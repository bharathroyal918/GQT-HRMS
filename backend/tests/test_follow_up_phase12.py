"""Comprehensive test suite for Phase 12: Automated Follow-Up Workflows.

Covers:
1. Schedule Follow-ups (categories, channels, remind_at validation, outbox queueing).
2. Reminder Emails (simulated adapter, retry logic, bounded backoff, failure exhaustion).
3. WhatsApp Messages (E.164 normalization, simulated adapter, webhook challenge & signature verification).
4. Placement Officer Notifications (due/overdue detection, deduplication, read-receipts).
5. Escalation for Pending Cases (overdue SLA detection, deduplication, supervisor assignment, acknowledge, resolve).
6. Management Command (process_follow_ups with --once and --dry-run).
7. Automation Run API endpoint and RBAC permissions.
"""
from datetime import timedelta
import hashlib
import hmac
import json
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RoleCatalog
from apps.accounts.services import assign_roles_to_user
from apps.crm.adapters.email import SimulatedEmailAdapter, get_email_adapter
from apps.crm.adapters.whatsapp import (
    MetaWhatsAppAdapter,
    SimulatedWhatsAppAdapter,
    get_whatsapp_adapter,
)
from apps.crm.models import (
    CaseEscalation,
    CaseEscalationLevel,
    CaseEscalationStatus,
    CaseEscalationType,
    Company,
    CompanyDomainCategory,
    CompanyRelationshipStatus,
    FollowUp,
    FollowUpCategory,
    FollowUpPriority,
    FollowUpReminderItem,
    FollowUpStatus,
    HRContact,
    ReminderChannel,
    ReminderDeliveryStatus,
    StaffNotification,
    StaffNotificationType,
)
from apps.crm.scheduler import (
    generate_due_followup_officer_notifications,
    generate_overdue_followup_escalations,
    process_due_reminder_items,
    run_automated_followup_cycle,
)
from apps.crm.services import (
    acknowledge_case_escalation,
    cancel_follow_up,
    complete_follow_up,
    reschedule_follow_up,
    resolve_case_escalation,
    schedule_follow_up,
)

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seed_roles(db):
    call_command("seed_roles")


@pytest.fixture
def test_password():
    return "P@ssw0rd12345!"


@pytest.fixture
def admin_user(db, seed_roles, test_password):
    user = User.objects.create_superuser(
        email="admin@gqt.local", password=test_password, first_name="Admin", last_name="User"
    )
    assign_roles_to_user(user, [RoleCatalog.ADMIN])
    return user


@pytest.fixture
def placement_head_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="head@gqt.local", password=test_password, first_name="Placement", last_name="Head"
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_HEAD])
    return user


@pytest.fixture
def placement_officer_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="officer@gqt.local", password=test_password, first_name="Placement", last_name="Officer"
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_OFFICER])
    return user


@pytest.fixture
def auditor_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="auditor@gqt.local", password=test_password, first_name="Audit", last_name="Inspector"
    )
    assign_roles_to_user(user, [RoleCatalog.AUDITOR])
    return user


@pytest.fixture
def student_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="student@gqt.local", password=test_password, first_name="Rahul", last_name="Sharma"
    )
    assign_roles_to_user(user, [RoleCatalog.STUDENT])
    return user


@pytest.fixture
def company(db, placement_officer_user):
    return Company.objects.create(
        name="Cognizant Technology Solutions",
        domain="cognizant.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER,
        owner=placement_officer_user,
    )


@pytest.fixture
def hr_contact(db, company):
    return HRContact.objects.create(
        company=company,
        name="Anjali Rao",
        designation="Lead Talent Acquisition",
        email="anjali.rao@cognizant.com",
        phone="+919876543210",
    )


# ==============================================================================
# CAPABILITY A: SCHEDULE FOLLOW-UPS & REMINDER OUTBOX
# ==============================================================================


@pytest.mark.django_db
def test_schedule_follow_up_with_reminders_and_category(company, hr_contact, placement_officer_user):
    """Scheduling a follow-up with reminder_channel=BOTH queues email and whatsapp outbox items."""
    now = timezone.now()
    due_date = now + timedelta(days=2)
    remind_at = now + timedelta(days=1)

    follow_up = schedule_follow_up(
        company=company,
        due_date=due_date,
        purpose="Finalize 2026 Batch campus interview schedule",
        priority=FollowUpPriority.HIGH,
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
        hr_contact=hr_contact,
        category=FollowUpCategory.INTERVIEW_CONFIRMATION,
        reminder_channel=ReminderChannel.BOTH,
        remind_at=remind_at,
        notes="Anjali requested early morning follow-up call.",
    )

    assert follow_up.category == FollowUpCategory.INTERVIEW_CONFIRMATION
    assert follow_up.reminder_channel == ReminderChannel.BOTH
    assert follow_up.remind_at == remind_at
    assert follow_up.notes == "Anjali requested early morning follow-up call."

    reminders = FollowUpReminderItem.objects.filter(follow_up=follow_up)
    assert reminders.count() == 2

    email_rem = reminders.filter(channel=ReminderChannel.EMAIL).first()
    assert email_rem is not None
    assert email_rem.recipient == "anjali.rao@cognizant.com"
    assert email_rem.status == ReminderDeliveryStatus.PENDING
    assert email_rem.scheduled_for == remind_at

    wa_rem = reminders.filter(channel=ReminderChannel.WHATSAPP).first()
    assert wa_rem is not None
    assert wa_rem.recipient == "+919876543210"
    assert wa_rem.status == ReminderDeliveryStatus.PENDING


@pytest.mark.django_db
def test_schedule_follow_up_validation_remind_at_after_due_date(api_client, company, placement_officer_user):
    """API rejects follow-up scheduling when remind_at is after due_date."""
    api_client.force_authenticate(user=placement_officer_user)
    now = timezone.now()

    payload = {
        "company": str(company.id),
        "due_date": (now + timedelta(days=1)).isoformat(),
        "remind_at": (now + timedelta(days=2)).isoformat(),  # Invalid: remind_at > due_date
        "purpose": "Check offer letters release",
        "category": "OFFER_ACCEPTANCE",
        "reminder_channel": "EMAIL",
    }

    response = api_client.post("/api/v1/crm/follow-ups/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "remind_at" in str(response.data)


@pytest.mark.django_db
def test_reschedule_follow_up_updates_reminders(company, hr_contact, placement_officer_user):
    """Rescheduling a follow-up cancels obsolete reminder outbox items and schedules new ones."""
    now = timezone.now()
    follow_up = schedule_follow_up(
        company=company,
        due_date=now + timedelta(days=1),
        purpose="Initial outreach",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
        hr_contact=hr_contact,
        reminder_channel=ReminderChannel.EMAIL,
        remind_at=now + timedelta(hours=12),
    )

    old_reminder = FollowUpReminderItem.objects.get(follow_up=follow_up)
    assert old_reminder.status == ReminderDeliveryStatus.PENDING

    new_due = now + timedelta(days=4)
    rescheduled = reschedule_follow_up(
        follow_up=follow_up,
        new_due_date=new_due,
        actor=placement_officer_user,
        reason="Recruiter postponed review",
    )

    assert rescheduled.rescheduled_count == 1
    old_reminder.refresh_from_db()
    assert old_reminder.status == ReminderDeliveryStatus.CANCELLED

    new_reminders = FollowUpReminderItem.objects.filter(
        follow_up=rescheduled, status=ReminderDeliveryStatus.PENDING
    )
    assert new_reminders.count() == 1
    assert new_reminders.first().id != old_reminder.id


@pytest.mark.django_db
def test_complete_and_cancel_follow_up_cancels_pending_reminders(company, hr_contact, placement_officer_user):
    """Completing or cancelling a follow-up cleanly cancels any pending reminders."""
    now = timezone.now()
    fu1 = schedule_follow_up(
        company=company,
        due_date=now + timedelta(days=1),
        purpose="Task 1",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
        hr_contact=hr_contact,
        reminder_channel=ReminderChannel.EMAIL,
    )
    fu2 = schedule_follow_up(
        company=company,
        due_date=now + timedelta(days=1),
        purpose="Task 2",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
        hr_contact=hr_contact,
        reminder_channel=ReminderChannel.WHATSAPP,
    )

    complete_follow_up(fu1, actor=placement_officer_user, notes="Completed successfully")
    cancel_follow_up(fu2, actor=placement_officer_user, reason="Cancelled by client")

    assert FollowUpReminderItem.objects.get(follow_up=fu1).status == ReminderDeliveryStatus.CANCELLED
    assert FollowUpReminderItem.objects.get(follow_up=fu2).status == ReminderDeliveryStatus.CANCELLED


# ==============================================================================
# CAPABILITY B & C: ADAPTERS & SCHEDULER OUTBOX PROCESSING
# ==============================================================================


@pytest.mark.django_db
def test_simulated_email_and_whatsapp_adapters(company, hr_contact, placement_officer_user):
    """Adapters truthfully record is_simulated=True in local development mode without fake live claims."""
    email_adapter = get_email_adapter()
    wa_adapter = get_whatsapp_adapter()

    assert isinstance(email_adapter, SimulatedEmailAdapter)
    assert isinstance(wa_adapter, SimulatedWhatsAppAdapter)

    email_res = email_adapter.send_email(
        recipient="hr@example.com",
        subject="Interview Drive Reminder",
        body_text="Reminder for interview round tomorrow.",
    )
    assert email_res.success is True
    assert email_res.is_simulated is True
    assert email_res.status == "SIMULATED"

    wa_res = wa_adapter.send_message(
        phone_number="+919876543210",
        template_name="follow_up_reminder_v1",
        template_context={"company_name": "Cognizant", "due_date": "2026-10-30"},
    )
    assert wa_res.success is True
    assert wa_res.is_simulated is True
    assert wa_res.status == "SIMULATED"


@pytest.mark.django_db
def test_whatsapp_phone_normalization():
    """WhatsApp adapter correctly normalizes Indian phone numbers into valid E.164 format."""
    adapter = SimulatedWhatsAppAdapter()
    assert adapter.normalize_phone_number("9876543210") == "+919876543210"
    assert adapter.normalize_phone_number("+91 98765 43210") == "+919876543210"
    assert adapter.normalize_phone_number("09876543210") == "+919876543210"
    assert adapter.normalize_phone_number("+1 415 555 2671") == "+14155552671"


@pytest.mark.django_db
def test_scheduler_process_due_reminder_items(company, hr_contact, placement_officer_user):
    """Scheduler processes due reminders and records attempt count, sent_at, and delivery status."""
    past = timezone.now() - timedelta(minutes=5)
    follow_up = schedule_follow_up(
        company=company,
        due_date=timezone.now() + timedelta(days=1),
        purpose="Send Brochure",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
        hr_contact=hr_contact,
        reminder_channel=ReminderChannel.BOTH,
        remind_at=past,
    )

    items = FollowUpReminderItem.objects.filter(follow_up=follow_up)
    assert items.count() == 2

    processed = process_due_reminder_items(batch_size=10)
    assert processed >= 2

    for item in FollowUpReminderItem.objects.filter(follow_up=follow_up):
        assert item.status in [ReminderDeliveryStatus.SENT, ReminderDeliveryStatus.DELIVERED]
        assert item.attempt_count == 1
        assert item.sent_at is not None
        assert item.is_simulated is True


@pytest.mark.django_db
def test_scheduler_bounded_backoff_and_retry_exhaustion(company, hr_contact, placement_officer_user, monkeypatch):
    """When a provider fails, the scheduler retries with bounded backoff until max_attempts, then marks FAILED."""
    past = timezone.now() - timedelta(minutes=5)
    follow_up = schedule_follow_up(
        company=company,
        due_date=timezone.now() + timedelta(days=1),
        purpose="Test failure retry",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
        hr_contact=hr_contact,
        reminder_channel=ReminderChannel.EMAIL,
        remind_at=past,
    )

    from apps.crm.adapters.base import ProviderDeliveryResult

    def mock_failing_send(*args, **kwargs):
        return ProviderDeliveryResult(
            success=False,
            error_message="Simulated connection timeout to mail server",
            is_transient=True,
        )

    monkeypatch.setattr(SimulatedEmailAdapter, "send_email", mock_failing_send)

    # First attempt -> RETRY_SCHEDULED with backoff_until in future
    process_due_reminder_items(batch_size=10)
    item = FollowUpReminderItem.objects.get(follow_up=follow_up)
    assert item.status == ReminderDeliveryStatus.RETRY_SCHEDULED
    assert item.attempt_count == 1
    assert item.backoff_until is not None

    # Fast forward backoff to simulate time passage
    item.backoff_until = timezone.now() - timedelta(seconds=1)
    item.save()

    # Second attempt
    process_due_reminder_items(batch_size=10)
    item.refresh_from_db()
    assert item.status == ReminderDeliveryStatus.RETRY_SCHEDULED
    assert item.attempt_count == 2

    # Fast forward again for final attempt (max_attempts is 3)
    item.backoff_until = timezone.now() - timedelta(seconds=1)
    item.save()

    process_due_reminder_items(batch_size=10)
    item.refresh_from_db()
    assert item.status == ReminderDeliveryStatus.FAILED
    assert item.attempt_count == 3
    assert "timeout" in item.error_message


# ==============================================================================
# CAPABILITY D: PLACEMENT OFFICER NOTIFICATIONS
# ==============================================================================


@pytest.mark.django_db
def test_placement_officer_notification_generation_and_deduplication(
    company, placement_officer_user
):
    """Follow-ups due today generate staff notifications and do not produce duplicate notifications on repeated cycles."""
    now = timezone.now()
    # Create follow-up due in 2 hours
    fu = schedule_follow_up(
        company=company,
        due_date=now + timedelta(hours=2),
        purpose="Verify student shortlisting with HR",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
    )

    created_count = generate_due_followup_officer_notifications()
    assert created_count >= 1

    notifs = StaffNotification.objects.filter(
        follow_up=fu, recipient=placement_officer_user, notification_type=StaffNotificationType.FOLLOW_UP_DUE
    )
    assert notifs.count() == 1
    assert notifs.first().is_read is False

    # Run cycle again: deduplication should ensure count remains 1
    second_count = generate_due_followup_officer_notifications()
    assert second_count == 0
    assert notifs.count() == 1


@pytest.mark.django_db
def test_staff_notification_mark_read_and_unread_count_api(
    api_client, company, placement_officer_user
):
    """Officer can read notification count, mark single notification as read, and mark all as read."""
    api_client.force_authenticate(user=placement_officer_user)

    notif = StaffNotification.objects.create(
        recipient=placement_officer_user,
        notification_type=StaffNotificationType.FOLLOW_UP_DUE,
        title="Due Follow-Up",
        message="Follow-up due today",
    )

    # Check unread count endpoint
    res_count = api_client.get("/api/v1/crm/notifications/unread-count/")
    assert res_count.status_code == status.HTTP_200_OK
    assert res_count.data["count"] == 1

    # Mark as read
    res_read = api_client.post(f"/api/v1/crm/notifications/{notif.id}/read/")
    assert res_read.status_code == status.HTTP_200_OK
    notif.refresh_from_db()
    assert notif.is_read is True

    # Count is now 0
    res_count2 = api_client.get("/api/v1/crm/notifications/unread-count/")
    assert res_count2.data["count"] == 0


# ==============================================================================
# CAPABILITY E: ESCALATION FOR PENDING CASES
# ==============================================================================


@pytest.mark.django_db
def test_generate_overdue_followup_escalations_and_deduplication(
    company, placement_officer_user, placement_head_user
):
    """Overdue follow-ups past threshold trigger CaseEscalation to supervisor with zero duplicate spam."""
    now = timezone.now()
    overdue_fu = schedule_follow_up(
        company=company,
        due_date=now - timedelta(days=4),  # 4 days overdue (> threshold 3)
        purpose="Stalled conversation regarding brochure",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
    )

    created_count = generate_overdue_followup_escalations()
    assert created_count >= 1

    escalations = CaseEscalation.objects.filter(follow_up=overdue_fu)
    assert escalations.count() == 1
    esc = escalations.first()
    assert esc.case_type == CaseEscalationType.OVERDUE_FOLLOW_UP
    assert esc.status == CaseEscalationStatus.PENDING
    assert esc.escalated_to == placement_head_user
    assert "overdue for 4 day(s)" in esc.reason

    # Re-running generation does not create duplicates
    second_count = generate_overdue_followup_escalations()
    assert second_count == 0
    assert escalations.count() == 1


@pytest.mark.django_db
def test_escalation_acknowledge_and_resolve_lifecycle(
    api_client, company, placement_officer_user, placement_head_user
):
    """Authorized placement head can acknowledge and resolve an escalation with mandatory resolution notes."""
    overdue_fu = schedule_follow_up(
        company=company,
        due_date=timezone.now() - timedelta(days=5),
        purpose="Urgent follow-up",
        assigned_to=placement_officer_user,
        created_by=placement_officer_user,
    )
    esc = CaseEscalation.objects.create(
        case_type=CaseEscalationType.OVERDUE_FOLLOW_UP,
        follow_up=overdue_fu,
        escalated_to=placement_head_user,
        previous_assigned_to=placement_officer_user,
        reason="Overdue 5 days",
    )

    api_client.force_authenticate(user=placement_head_user)

    # 1. Acknowledge
    ack_res = api_client.post(f"/api/v1/crm/escalations/{esc.id}/acknowledge/")
    assert ack_res.status_code == status.HTTP_200_OK
    esc.refresh_from_db()
    assert esc.status == CaseEscalationStatus.ACKNOWLEDGED
    assert esc.acknowledged_by == placement_head_user

    # 2. Resolve without notes -> fails validation
    res_fail = api_client.post(f"/api/v1/crm/escalations/{esc.id}/resolve/", {"resolution_notes": ""})
    assert res_fail.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Resolve with notes -> succeeds
    res_ok = api_client.post(
        f"/api/v1/crm/escalations/{esc.id}/resolve/",
        {"resolution_notes": "Contacted VP of HR directly and rescheduled drive."},
    )
    assert res_ok.status_code == status.HTTP_200_OK
    esc.refresh_from_db()
    assert esc.status == CaseEscalationStatus.RESOLVED
    assert esc.resolved_by == placement_head_user
    assert "VP of HR" in esc.resolution_notes


# ==============================================================================
# WHATSAPP WEBHOOK VERIFICATION & CALLBACK PROCESSING
# ==============================================================================


@pytest.mark.django_db
def test_whatsapp_webhook_challenge_verification(api_client, monkeypatch):
    """WhatsApp webhook GET challenge responds with hub.challenge when token matches."""
    monkeypatch.setenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "secret-test-token-123")

    # Correct token
    res = api_client.get(
        "/api/v1/crm/webhooks/whatsapp/",
        {"hub.mode": "subscribe", "hub.verify_token": "secret-test-token-123", "hub.challenge": "115599"},
    )
    assert res.status_code == status.HTTP_200_OK
    assert res.content.decode() == "115599"

    # Incorrect token
    res_bad = api_client.get(
        "/api/v1/crm/webhooks/whatsapp/",
        {"hub.mode": "subscribe", "hub.verify_token": "wrong-token", "hub.challenge": "115599"},
    )
    assert res_bad.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_whatsapp_webhook_delivery_status_callback(
    api_client, company, hr_contact, placement_officer_user, monkeypatch
):
    """WhatsApp webhook POST callback updates FollowUpReminderItem delivery status securely."""
    secret = "test-webhook-app-secret"
    monkeypatch.setenv("WHATSAPP_API_SECRET", secret)

    reminder = FollowUpReminderItem.objects.create(
        follow_up=schedule_follow_up(
            company=company,
            due_date=timezone.now() + timedelta(days=1),
            purpose="WA test",
            assigned_to=placement_officer_user,
            created_by=placement_officer_user,
        ),
        channel=ReminderChannel.WHATSAPP,
        recipient="+919876543210",
        scheduled_for=timezone.now(),
        provider_message_id="wamid.HBgLMjA",
        status=ReminderDeliveryStatus.PROCESSING,
    )

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid.HBgLMjA",
                                    "status": "delivered",
                                    "timestamp": "1730000000",
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    payload_bytes = json.dumps(payload).encode("utf-8")
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    response = api_client.post(
        "/api/v1/crm/webhooks/whatsapp/",
        data=payload_bytes,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=signature,
    )
    assert response.status_code == status.HTTP_200_OK
    reminder.refresh_from_db()
    assert reminder.status == ReminderDeliveryStatus.DELIVERED
    assert reminder.delivered_at is not None


# ==============================================================================
# MANAGEMENT COMMAND & AUTOMATION RUN API
# ==============================================================================


@pytest.mark.django_db
def test_management_command_process_follow_ups():
    """Management command `process_follow_ups` runs with --dry-run and --once cleanly."""
    # Test --dry-run
    call_command("process_follow_ups", once=True, dry_run=True)
    # Test live execution
    call_command("process_follow_ups", once=True, dry_run=False)


@pytest.mark.django_db
def test_automation_run_api_endpoint_rbac(
    api_client, student_user, auditor_user, placement_officer_user
):
    """Students and auditors are forbidden from executing the automation cycle; authorized staff can run dry_run."""
    # 1. Student forbidden
    api_client.force_authenticate(user=student_user)
    res_student = api_client.post("/api/v1/crm/automation/run/", {"dry_run": True})
    assert res_student.status_code == status.HTTP_403_FORBIDDEN

    # 2. Auditor forbidden
    api_client.force_authenticate(user=auditor_user)
    res_auditor = api_client.post("/api/v1/crm/automation/run/", {"dry_run": True})
    assert res_auditor.status_code == status.HTTP_403_FORBIDDEN

    # 3. Placement Officer authorized
    api_client.force_authenticate(user=placement_officer_user)
    res_officer = api_client.post("/api/v1/crm/automation/run/", {"dry_run": True})
    assert res_officer.status_code == status.HTTP_200_OK
    assert res_officer.data["success"] is True
    assert res_officer.data["data"]["dry_run"] is True
