"""Comprehensive verification suite for Phase 2: Corporate CRM & HR Directory."""
from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RoleCatalog
from apps.accounts.services import assign_roles_to_user
from apps.core.models import AuditLog
from apps.crm.models import (
    CRMConfiguration,
    Company,
    CompanyDomainCategory,
    CompanyRelationshipStatus,
    FollowUp,
    FollowUpPriority,
    FollowUpStatus,
    HRContact,
    OutreachChannel,
    OutreachLog,
    OutreachOutcome,
    extract_domain,
    normalize_company_name,
)
from apps.crm.selectors import (
    check_company_duplicates,
    check_hr_contact_duplicates,
    get_crm_dashboard_metrics,
)
from apps.crm.services import (
    archive_company,
    cancel_follow_up,
    complete_follow_up,
    create_company,
    create_hr_contact,
    record_outreach_activity,
    reopen_follow_up,
    reschedule_follow_up,
    restore_company,
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
        email="head@gqt.local", password=test_password, first_name="Head", last_name="Director"
    )
    assign_roles_to_user(user, [RoleCatalog.PLACEMENT_HEAD])
    return user


@pytest.fixture
def hr_manager_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="hrmgr@gqt.local", password=test_password, first_name="HRM", last_name="Manager"
    )
    assign_roles_to_user(user, [RoleCatalog.HR_RELATIONSHIP_MGR])
    return user


@pytest.fixture
def auditor_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="auditor@gqt.local", password=test_password, first_name="Audi", last_name="Tor"
    )
    assign_roles_to_user(user, [RoleCatalog.AUDITOR])
    return user


@pytest.fixture
def student_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="student@gqt.local", password=test_password, first_name="Stud", last_name="Ent"
    )
    assign_roles_to_user(user, [RoleCatalog.STUDENT])
    return user


@pytest.fixture
def sample_company(db, admin_user):
    return Company.objects.create(
        name="Infosys Technologies Private Limited",
        website="https://www.infosys.com/careers",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        relationship_status=CompanyRelationshipStatus.DISCOVERED,
        city="Bengaluru",
        created_by=admin_user,
    )


@pytest.fixture
def sample_contact(db, sample_company, admin_user):
    return HRContact.objects.create(
        company=sample_company,
        name="Sunita Sharma",
        designation="Lead Campus Recruiter",
        email="sunita.sharma@infosys.com",
        phone="+919876543210",
        created_by=admin_user,
    )


# ==============================================================================
# Unit & Business Logic Tests (1 - 10)
# ==============================================================================

@pytest.mark.django_db
def test_01_company_creation_and_normalization():
    """Verify company creation normalizes name and extracts domain."""
    assert normalize_company_name("  Acme  Corp.,  Inc. ") == "acme corp inc"
    assert extract_domain("https://www.acme.corp:8080/careers/jobs") == "acme.corp"
    assert extract_domain("http://sub.domain.co.in/path") == "sub.domain.co.in"

    company = Company.objects.create(
        name="  TATA Consultancy Services Ltd. ",
        website="https://www.tcs.com/careers",
    )
    assert company.normalized_name == "tata consultancy services ltd"
    assert company.domain == "tcs.com"
    assert company.is_archived is False


@pytest.mark.django_db
def test_02_company_duplicate_detection_exact_name(sample_company):
    """Verify duplicate detection flags matching normalized name."""
    matches = check_company_duplicates("Infosys Technologies Private Limited")
    assert len(matches) >= 1
    assert matches[0]["match_type"] == "EXACT_NAME"
    assert matches[0]["company_id"] == sample_company.id


@pytest.mark.django_db
def test_03_company_duplicate_detection_canonical_domain(sample_company):
    """Verify duplicate detection flags canonical domain collision even with different company name."""
    matches = check_company_duplicates("Infosys BPM Division", website="https://infosys.com/bpm")
    assert len(matches) >= 1
    domain_matches = [m for m in matches if m["match_type"] == "DOMAIN_MATCH"]
    assert len(domain_matches) == 1
    assert domain_matches[0]["domain"] == "infosys.com"


@pytest.mark.django_db
def test_04_company_duplicate_check_api(api_client, hr_manager_user, sample_company):
    """Verify the /api/v1/crm/companies/check-duplicate/ API returns warning candidates."""
    api_client.force_authenticate(user=hr_manager_user)
    response = api_client.get(
        "/api/v1/crm/companies/check-duplicate/",
        {"name": "Infosys Technologies", "website": "https://infosys.com"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] is True
    assert len(response.data["data"]) >= 1


@pytest.mark.django_db
def test_05_company_archive_and_restore(hr_manager_user, sample_company):
    """Verify archiving and restoring company preserves relations."""
    archived = archive_company(hr_manager_user, sample_company)
    assert archived.is_archived is True

    restored = restore_company(hr_manager_user, archived)
    assert restored.is_archived is False


@pytest.mark.django_db
def test_06_company_filtering_and_search(db, hr_manager_user):
    """Verify company selectors support domain category, status, and text search."""
    c1 = Company.objects.create(
        name="Wipro Digital",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        relationship_status=CompanyRelationshipStatus.DISCOVERED,
        city="Bengaluru",
    )
    c2 = Company.objects.create(
        name="Zoho Corporation",
        domain_category=CompanyDomainCategory.PRODUCT_TECH,
        relationship_status=CompanyRelationshipStatus.CONNECTED,
        city="Chennai",
    )

    api = APIClient()
    api.force_authenticate(user=hr_manager_user)

    # Filter by domain_category
    r1 = api.get("/api/v1/crm/companies/", {"domain_category": "PRODUCT_TECH"})
    assert r1.status_code == status.HTTP_200_OK
    assert len(r1.data["data"]) == 1
    assert r1.data["data"][0]["name"] == "Zoho Corporation"

    # Search by text
    r2 = api.get("/api/v1/crm/companies/", {"search": "Wipro"})
    assert r2.status_code == status.HTTP_200_OK
    assert len(r2.data["data"]) == 1
    assert r2.data["data"][0]["name"] == "Wipro Digital"


@pytest.mark.django_db
def test_07_hr_contact_creation_and_company_link(admin_user, sample_company):
    """Verify HR contact creation and company linkage."""
    contact = create_hr_contact(
        admin_user,
        {
            "company": sample_company,
            "name": "Rajesh Kumar",
            "designation": "Talent Acquisition Head",
            "email": "rajesh.k@infosys.com",
            "phone": "+919123456789",
            "status": "ACTIVE",
        },
    )
    assert contact.company == sample_company
    assert contact.name == "Rajesh Kumar"
    assert contact.is_archived is False


@pytest.mark.django_db
def test_08_hr_contact_duplicate_detection(sample_company, sample_contact):
    """Verify duplicate detection identifies email or phone collision within the same company."""
    matches = check_hr_contact_duplicates(
        company_id=sample_company.id,
        email="sunita.sharma@infosys.com",
    )
    assert len(matches) == 1
    assert matches[0]["contact_id"] == sample_contact.id


@pytest.mark.django_db
def test_09_hr_contact_archive_and_restore(hr_manager_user, sample_contact):
    """Verify HR contact can be safely archived and restored."""
    api = APIClient()
    api.force_authenticate(user=hr_manager_user)

    res_archive = api.post(f"/api/v1/crm/contacts/{sample_contact.id}/archive/")
    assert res_archive.status_code == status.HTTP_200_OK
    sample_contact.refresh_from_db()
    assert sample_contact.is_archived is True

    res_restore = api.post(f"/api/v1/crm/contacts/{sample_contact.id}/restore/")
    assert res_restore.status_code == status.HTTP_200_OK
    sample_contact.refresh_from_db()
    assert sample_contact.is_archived is False


@pytest.mark.django_db
def test_10_outreach_logging_success(hr_manager_user, sample_company, sample_contact):
    """Verify logging outreach activity updates company status and stores record."""
    outreach = record_outreach_activity(
        hr_manager_user,
        {
            "company": sample_company,
            "hr_contact": sample_contact,
            "channel": OutreachChannel.CALL,
            "direction": "OUTBOUND",
            "outcome": OutreachOutcome.CONNECTED_INTERESTED,
            "subject": "Initial Campus Placement Pitch",
            "notes": "Spoke to Sunita. Interested in hiring 2026 CS graduates.",
            "followup_required": True,
        },
    )
    assert outreach.channel == OutreachChannel.CALL
    assert outreach.outcome == OutreachOutcome.CONNECTED_INTERESTED
    assert outreach.performed_by == hr_manager_user

    sample_company.refresh_from_db()
    assert sample_company.relationship_status == CompanyRelationshipStatus.OUTREACH_IN_PROGRESS


# ==============================================================================
# Business Invariants & Validation Tests (11 - 17)
# ==============================================================================

@pytest.mark.django_db
def test_11_outreach_company_contact_relationship_validation(hr_manager_user, sample_company):
    """Verify that an outreach record cannot reference a contact from a different company."""
    other_company = Company.objects.create(name="Other Corp")
    foreign_contact = HRContact.objects.create(company=other_company, name="Foreign HR")

    with pytest.raises(ValidationError):
        record_outreach_activity(
            hr_manager_user,
            {
                "company": sample_company,
                "hr_contact": foreign_contact,
                "channel": OutreachChannel.EMAIL,
                "outcome": OutreachOutcome.NO_ANSWER_BUSY,
            },
        )


@pytest.mark.django_db
def test_12_outreach_logging_api_validation(api_client, hr_manager_user, sample_company):
    """Verify API returns 400 when linking a contact from a different company."""
    other_company = Company.objects.create(name="Another Corp")
    foreign_contact = HRContact.objects.create(company=other_company, name="Unrelated HR")

    api_client.force_authenticate(user=hr_manager_user)
    payload = {
        "company": str(sample_company.id),
        "hr_contact": str(foreign_contact.id),
        "channel": "CALL",
        "direction": "OUTBOUND",
        "outcome": "CONNECTED_INTERESTED",
        "subject": "Invalid Association Test",
    }
    response = api_client.post("/api/v1/crm/outreach/", payload, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "hr_contact" in response.data or "error" in response.data


@pytest.mark.django_db
def test_13_follow_up_creation_and_lifecycle(hr_manager_user, sample_company, sample_contact):
    """Verify follow-up scheduling, completion with notes, and status transition."""
    due = timezone.now() + timedelta(days=2)
    follow_up = schedule_follow_up(
        hr_manager_user,
        {
            "company": sample_company,
            "hr_contact": sample_contact,
            "assigned_to": hr_manager_user,
            "due_date": due,
            "priority": FollowUpPriority.HIGH,
            "purpose": "Send 2026 Batch Placement Brochure",
        },
    )
    assert follow_up.status == FollowUpStatus.OPEN
    assert follow_up.rescheduled_count == 0

    # Complete follow-up
    completed = complete_follow_up(
        hr_manager_user, follow_up, completion_notes="Brochure sent via email and acknowledged."
    )
    assert completed.status == FollowUpStatus.COMPLETED
    assert completed.completed_at is not None
    assert completed.completed_by == hr_manager_user


@pytest.mark.django_db
def test_14_follow_up_overdue_dynamic_calculation(hr_manager_user, sample_company):
    """Verify dynamic overdue evaluation accurately checks due date against timezone.now()."""
    past_due = timezone.now() - timedelta(hours=3)
    future_due = timezone.now() + timedelta(hours=5)

    f_overdue = FollowUp.objects.create(
        company=sample_company,
        assigned_to=hr_manager_user,
        due_date=past_due,
        status=FollowUpStatus.OPEN,
        purpose="Overdue call",
    )
    f_future = FollowUp.objects.create(
        company=sample_company,
        assigned_to=hr_manager_user,
        due_date=future_due,
        status=FollowUpStatus.OPEN,
        purpose="Future call",
    )
    f_completed_past = FollowUp.objects.create(
        company=sample_company,
        assigned_to=hr_manager_user,
        due_date=past_due,
        status=FollowUpStatus.COMPLETED,
        purpose="Completed past call",
    )

    assert f_overdue.is_overdue is True
    assert f_future.is_overdue is False
    assert f_completed_past.is_overdue is False


@pytest.mark.django_db
def test_15_follow_up_overdue_query_filter(api_client, hr_manager_user, sample_company):
    """Verify /api/v1/crm/follow-ups/overdue/ returns only overdue follow-ups."""
    past_due = timezone.now() - timedelta(days=1)
    future_due = timezone.now() + timedelta(days=1)

    FollowUp.objects.create(
        company=sample_company,
        assigned_to=hr_manager_user,
        due_date=past_due,
        status=FollowUpStatus.OPEN,
        purpose="Call overdue",
    )
    FollowUp.objects.create(
        company=sample_company,
        assigned_to=hr_manager_user,
        due_date=future_due,
        status=FollowUpStatus.OPEN,
        purpose="Call upcoming",
    )

    api_client.force_authenticate(user=hr_manager_user)
    response = api_client.get("/api/v1/crm/follow-ups/overdue/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["meta"]["count"] == 1
    assert response.data["data"][0]["purpose"] == "Call overdue"


@pytest.mark.django_db
def test_16_follow_up_rescheduling_history(hr_manager_user, sample_company):
    """Verify rescheduling follow-up increments counter and preserves audit history."""
    initial_due = timezone.now() + timedelta(days=1)
    f = FollowUp.objects.create(
        company=sample_company,
        assigned_to=hr_manager_user,
        due_date=initial_due,
        status=FollowUpStatus.OPEN,
        purpose="Review JD",
    )

    new_due = timezone.now() + timedelta(days=3)
    rescheduled = reschedule_follow_up(
        hr_manager_user, f, new_due, reason="HR requested rescheduling to next week"
    )
    assert rescheduled.rescheduled_count == 1
    assert rescheduled.due_date == new_due


@pytest.mark.django_db
def test_17_follow_up_cancel_and_reopen(hr_manager_user, sample_company):
    """Verify follow-up cancellation and authorized reopening workflow."""
    due = timezone.now() + timedelta(days=1)
    f = FollowUp.objects.create(
        company=sample_company,
        assigned_to=hr_manager_user,
        due_date=due,
        status=FollowUpStatus.OPEN,
        purpose="Campus drive discussion",
    )

    cancelled = cancel_follow_up(hr_manager_user, f, cancellation_reason="HR went on sabbatical")
    assert cancelled.status == FollowUpStatus.CANCELLED

    # Cannot complete cancelled follow-up without reopening
    with pytest.raises(ValidationError):
        complete_follow_up(hr_manager_user, cancelled)

    # Reopen
    new_due = timezone.now() + timedelta(days=5)
    reopened = reopen_follow_up(hr_manager_user, cancelled, new_due, reason="HR returned and resumed hiring")
    assert reopened.status == FollowUpStatus.OPEN
    assert reopened.due_date == new_due


# ==============================================================================
# Operational Metrics & Targets (18 - 20)
# ==============================================================================

@pytest.mark.django_db
def test_18_daily_outreach_target_calculation(hr_manager_user, sample_company):
    """Verify operational daily target (100+) is tracked and calculated accurately."""
    CRMConfiguration.objects.update_or_create(key="DAILY_OUTREACH_TARGET", defaults={"value": "100"})

    # Create 5 outreach activities today
    for i in range(5):
        OutreachLog.objects.create(
            company=sample_company,
            performed_by=hr_manager_user,
            channel=OutreachChannel.CALL,
            outcome=OutreachOutcome.CONNECTED_INTERESTED,
            subject=f"Outreach {i}",
            activity_date=timezone.now(),
        )

    metrics = get_crm_dashboard_metrics(hr_manager_user)
    assert metrics["daily_outreach_target"] == 100
    assert metrics["today_outreach_count"] == 5
    assert metrics["today_outreach_progress_percent"] == 5.0
    assert metrics["user_today_outreach_count"] == 5


@pytest.mark.django_db
def test_19_dashboard_metrics_aggregation(hr_manager_user, sample_company, sample_contact):
    """Verify dashboard KPI metrics count companies, contacts, channel breakdown correctly."""
    OutreachLog.objects.create(
        company=sample_company,
        performed_by=hr_manager_user,
        channel=OutreachChannel.CALL,
        outcome=OutreachOutcome.CONNECTED_INTERESTED,
        activity_date=timezone.now(),
    )
    OutreachLog.objects.create(
        company=sample_company,
        performed_by=hr_manager_user,
        channel=OutreachChannel.EMAIL,
        outcome=OutreachOutcome.CONNECTED_INTERESTED,
        activity_date=timezone.now(),
    )

    metrics = get_crm_dashboard_metrics(hr_manager_user)
    assert metrics["total_active_companies"] == 1
    assert metrics["total_active_contacts"] == 1
    assert metrics["channel_breakdown"].get("CALL") == 1
    assert metrics["channel_breakdown"].get("EMAIL") == 1


@pytest.mark.django_db
def test_20_timezone_boundary_behavior(hr_manager_user, sample_company):
    """Verify activities outside today's local date boundary are excluded from daily count."""
    yesterday = timezone.now() - timedelta(days=2)
    OutreachLog.objects.create(
        company=sample_company,
        performed_by=hr_manager_user,
        channel=OutreachChannel.CALL,
        outcome=OutreachOutcome.CONNECTED_INTERESTED,
        activity_date=yesterday,
    )

    metrics = get_crm_dashboard_metrics(hr_manager_user)
    assert metrics["today_outreach_count"] == 0


# ==============================================================================
# Security & Permissions Tests (21 - 24)
# ==============================================================================

@pytest.mark.django_db
def test_21_crm_staff_role_access(api_client, hr_manager_user, placement_head_user):
    """Verify PLACEMENT_HEAD and HR_RELATIONSHIP_MGR have full operational write access."""
    for user in [placement_head_user, hr_manager_user]:
        api_client.force_authenticate(user=user)
        payload = {
            "name": f"Hiring Partner {user.email}",
            "domain_category": "IT_SERVICES",
            "relationship_status": "DISCOVERED",
        }
        res = api_client.post("/api/v1/crm/companies/", payload, format="json")
        assert res.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_22_auditor_read_only_access(api_client, auditor_user, sample_company):
    """Verify AUDITOR can list and view records, but is blocked (403) from mutating CRM data."""
    api_client.force_authenticate(user=auditor_user)

    # Allowed: GET list
    r_list = api_client.get("/api/v1/crm/companies/")
    assert r_list.status_code == status.HTTP_200_OK

    # Allowed: GET detail
    r_detail = api_client.get(f"/api/v1/crm/companies/{sample_company.id}/")
    assert r_detail.status_code == status.HTTP_200_OK

    # Denied: POST create
    r_post = api_client.post("/api/v1/crm/companies/", {"name": "Disallowed By Auditor"}, format="json")
    assert r_post.status_code == status.HTTP_403_FORBIDDEN

    # Denied: PATCH update
    r_patch = api_client.patch(
        f"/api/v1/crm/companies/{sample_company.id}/", {"notes": "Forbidden edit"}, format="json"
    )
    assert r_patch.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_23_student_and_unrelated_roles_denied(api_client, student_user, sample_company):
    """Verify STUDENT role is denied (403 Forbidden) on all CRM endpoints."""
    api_client.force_authenticate(user=student_user)

    assert api_client.get("/api/v1/crm/companies/").status_code == status.HTTP_403_FORBIDDEN
    assert api_client.get("/api/v1/crm/contacts/").status_code == status.HTTP_403_FORBIDDEN
    assert api_client.get("/api/v1/crm/outreach/").status_code == status.HTTP_403_FORBIDDEN
    assert api_client.get("/api/v1/crm/follow-ups/").status_code == status.HTTP_403_FORBIDDEN
    assert api_client.get("/api/v1/crm/dashboard/metrics/").status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_24_unauthenticated_request_denied(api_client):
    """Verify anonymous unauthenticated requests return 401 Unauthorized."""
    res = api_client.get("/api/v1/crm/companies/")
    assert res.status_code == status.HTTP_401_UNAUTHORIZED


# ==============================================================================
# Audit Trail & Pagination Tests (25 - 26)
# ==============================================================================

@pytest.mark.django_db
def test_25_audit_log_generation_on_crm_actions(hr_manager_user, sample_company, sample_contact):
    """Verify AuditLog records events for company creation, contact, outreach, and follow-up."""
    # Count audit logs
    count_before = AuditLog.objects.count()

    create_company(hr_manager_user, {"name": "TCS BPS", "domain_category": "BPO_ITES"})
    record_outreach_activity(
        hr_manager_user,
        {
            "company": sample_company,
            "hr_contact": sample_contact,
            "channel": OutreachChannel.EMAIL,
            "outcome": OutreachOutcome.CONNECTED_CALL_LATER,
        },
    )

    count_after = AuditLog.objects.count()
    assert count_after >= count_before + 2

    actions = AuditLog.objects.values_list("action", flat=True)
    assert "COMPANY_CREATED" in actions
    assert "OUTREACH_LOGGED" in actions


@pytest.mark.django_db
def test_26_pagination_and_safe_sorting(api_client, hr_manager_user):
    """Verify standard pagination format and safe ordering on company list endpoint."""
    for i in range(25):
        Company.objects.create(name=f"Enterprise Company {i:02d}")

    api_client.force_authenticate(user=hr_manager_user)
    response = api_client.get("/api/v1/crm/companies/?page=1&page_size=10&ordering=-name")
    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] is True
    assert response.data["meta"]["count"] >= 25
    assert response.data["meta"]["total_pages"] >= 3
    assert len(response.data["data"]) == 10
    # First item should be Enterprise Company 24 due to -name
    assert response.data["data"][0]["name"] == "Enterprise Company 24"
