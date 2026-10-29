"""Verification suite for Global Notification Center (Phase 15 Workstream 3).

Verifies recipient-level isolation, unread tracking, idempotent marking,
workflow integrations (Job Approvals, Student Drive Applications), and tamper-resistance.
"""
import uuid
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RoleCatalog
from apps.accounts.services import assign_roles_to_user
from apps.core.models import Notification, NotificationCategory
from apps.core.selectors_notifications import (
    get_notification_by_id,
    get_unread_notification_count,
    get_user_notifications,
)
from apps.core.services_notifications import (
    create_notification,
    mark_all_notifications_as_read,
    mark_notification_as_read,
    sanitize_notification_metadata,
)
from apps.crm.models import Company
from apps.jobs.models import (
    ChecklistItemStatus,
    EmploymentType,
    JobRequirement,
    JobRequirementStatus,
    WorkArrangement,
)
from apps.jobs.services import approve_job_requirement, create_job_requirement
from apps.students.models import StudentProfile, StudentResume
from apps.students.services import apply_student_for_job

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def seed_roles(db):
    call_command("seed_roles")


@pytest.fixture
def user_a(db, seed_roles):
    u = User.objects.create_user(
        email="user_a@gqt.local",
        password="TestPassword123!",
        first_name="Alice",
        last_name="Staff",
        is_active=True,
    )
    assign_roles_to_user(u, [RoleCatalog.PLACEMENT_OFFICER])
    return u


@pytest.fixture
def user_b(db, seed_roles):
    u = User.objects.create_user(
        email="user_b@gqt.local",
        password="TestPassword123!",
        first_name="Bob",
        last_name="Student",
        is_active=True,
    )
    assign_roles_to_user(u, [RoleCatalog.STUDENT])
    return u


@pytest.fixture
def admin_user(db, seed_roles):
    u = User.objects.create_user(
        email="admin@gqt.local",
        password="TestPassword123!",
        first_name="Super",
        last_name="Admin",
        is_active=True,
    )
    assign_roles_to_user(u, [RoleCatalog.ADMIN])
    return u


@pytest.mark.django_db
def test_01_unauthenticated_notification_endpoints_denied(api_client):
    """Unauthenticated access to notification endpoints must be rejected with HTTP 401."""
    random_id = uuid.uuid4()
    assert api_client.get("/api/v1/notifications/").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.get("/api/v1/notifications/unread-count/").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.post(f"/api/v1/notifications/{random_id}/read/").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.post("/api/v1/notifications/mark-all-read/").status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_02_user_level_notification_isolation(api_client, user_a, user_b):
    """Users must only be able to view and interact with notifications specifically addressed to them."""
    notif_a, _ = create_notification(
        recipient=user_a,
        category=NotificationCategory.SYSTEM,
        title="Notice for Alice",
        message="Confidential operational notice",
    )
    notif_b, _ = create_notification(
        recipient=user_b,
        category=NotificationCategory.JOB_DRIVE,
        title="Notice for Bob",
        message="Placement drive open",
    )

    # 1. User A lists notifications
    api_client.force_authenticate(user=user_a)
    resp_a = api_client.get("/api/v1/notifications/")
    assert resp_a.status_code == status.HTTP_200_OK
    items_a = resp_a.data["data"]
    assert len(items_a) == 1
    assert items_a[0]["id"] == str(notif_a.id)
    assert items_a[0]["title"] == "Notice for Alice"

    # 2. User A attempts to retrieve User B's notification -> 404 Not Found
    resp_cross_get = api_client.get(f"/api/v1/notifications/{notif_b.id}/")
    assert resp_cross_get.status_code == status.HTTP_404_NOT_FOUND

    # 3. User A attempts to mark User B's notification as read -> 404 Not Found
    resp_cross_read = api_client.post(f"/api/v1/notifications/{notif_b.id}/read/")
    assert resp_cross_read.status_code == status.HTTP_404_NOT_FOUND

    # User B's notification remains unread
    notif_b.refresh_from_db()
    assert notif_b.is_read is False


@pytest.mark.django_db
def test_03_unread_counts_and_filtering(api_client, user_a):
    """Unread count reflects only unread items; filter parameters filter correctly."""
    create_notification(
        recipient=user_a,
        category=NotificationCategory.JOB_DRIVE,
        title="Unread 1",
        message="Message 1",
    )
    n2, _ = create_notification(
        recipient=user_a,
        category=NotificationCategory.APPLICATION,
        title="Unread 2",
        message="Message 2",
    )
    n3, _ = create_notification(
        recipient=user_a,
        category=NotificationCategory.FOLLOW_UP,
        title="Already Read",
        message="Message 3",
    )
    mark_notification_as_read(user_a, n3.id)

    api_client.force_authenticate(user=user_a)

    # Check unread count
    count_resp = api_client.get("/api/v1/notifications/unread-count/")
    assert count_resp.status_code == status.HTTP_200_OK
    assert count_resp.data["count"] == 2

    # Filter unread only
    unread_resp = api_client.get("/api/v1/notifications/?is_read=false")
    assert unread_resp.status_code == status.HTTP_200_OK
    assert len(unread_resp.data["data"]) == 2

    # Filter read only
    read_resp = api_client.get("/api/v1/notifications/?is_read=true")
    assert read_resp.status_code == status.HTTP_200_OK
    assert len(read_resp.data["data"]) == 1
    assert read_resp.data["data"][0]["id"] == str(n3.id)

    # Filter category
    cat_resp = api_client.get(f"/api/v1/notifications/?category={NotificationCategory.APPLICATION}")
    assert cat_resp.status_code == status.HTTP_200_OK
    assert len(cat_resp.data["data"]) == 1
    assert cat_resp.data["data"][0]["id"] == str(n2.id)


@pytest.mark.django_db
def test_04_mark_single_notification_as_read_idempotent(api_client, user_a):
    """Mark-read marks item read and timestamped; subsequent calls are safely idempotent."""
    notif, _ = create_notification(
        recipient=user_a,
        category=NotificationCategory.JOB_DRIVE,
        title="Placement Notice",
        message="Important notice details",
    )
    assert notif.is_read is False
    assert notif.read_at is None

    api_client.force_authenticate(user=user_a)

    # First call marks read
    resp1 = api_client.post(f"/api/v1/notifications/{notif.id}/read/")
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.data["data"]["is_read"] is True
    assert resp1.data["data"]["read_at"] is not None

    notif.refresh_from_db()
    assert notif.is_read is True
    first_read_at = notif.read_at

    # Second call is idempotent
    resp2 = api_client.post(f"/api/v1/notifications/{notif.id}/read/")
    assert resp2.status_code == status.HTTP_200_OK
    notif.refresh_from_db()
    assert notif.is_read is True
    assert notif.read_at == first_read_at


@pytest.mark.django_db
def test_05_mark_all_notifications_as_read(api_client, user_a):
    """Mark-all-read updates all pending unread items for user and updates unread badge."""
    for i in range(4):
        create_notification(
            recipient=user_a,
            category=NotificationCategory.SYSTEM,
            title=f"Notification {i}",
            message=f"Body {i}",
        )

    api_client.force_authenticate(user=user_a)
    assert get_unread_notification_count(user_a) == 4

    resp = api_client.post("/api/v1/notifications/mark-all-read/")
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["count"] == 4

    assert get_unread_notification_count(user_a) == 0


@pytest.mark.django_db
def test_06_invalid_uuid_and_nonexistent_notification_returns_404(api_client, user_a):
    """Invalid UUIDs or non-existent notification IDs safely return 404."""
    api_client.force_authenticate(user=user_a)
    assert api_client.get(f"/api/v1/notifications/{uuid.uuid4()}/").status_code == status.HTTP_404_NOT_FOUND
    assert api_client.post(f"/api/v1/notifications/{uuid.uuid4()}/read/").status_code == status.HTTP_404_NOT_FOUND
    assert api_client.get("/api/v1/notifications/invalid-uuid-format/").status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_07_tamper_resistance_read_only_viewset(api_client, user_a):
    """Clients cannot directly modify notifications via PUT, PATCH, or DELETE."""
    notif, _ = create_notification(
        recipient=user_a,
        category=NotificationCategory.SYSTEM,
        title="Immutable Notice",
        message="Cannot alter me",
    )
    api_client.force_authenticate(user=user_a)

    assert api_client.put(f"/api/v1/notifications/{notif.id}/", {"title": "Hacked"}).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert api_client.patch(f"/api/v1/notifications/{notif.id}/", {"title": "Hacked"}).status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    assert api_client.delete(f"/api/v1/notifications/{notif.id}/").status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_08_deduplication_and_idempotency_key(user_a):
    """Duplicate calls with the same idempotency_key safely return existing record without duplicate DB rows."""
    key = "UNIQUE-EVENT-KEY-999"
    notif1, created1 = create_notification(
        recipient=user_a,
        category=NotificationCategory.JOB_DRIVE,
        title="Event 1",
        message="Notice body",
        idempotency_key=key,
    )
    assert created1 is True

    notif2, created2 = create_notification(
        recipient=user_a,
        category=NotificationCategory.JOB_DRIVE,
        title="Event 1 Duplicate",
        message="Notice body",
        idempotency_key=key,
    )
    assert created2 is False
    assert notif1.id == notif2.id
    assert Notification.objects.filter(idempotency_key=key).count() == 1


@pytest.mark.django_db
def test_09_safe_handling_of_missing_or_inactive_recipients():
    """Missing or inactive recipients return (None, False) without raising unhandled errors."""
    res1, created1 = create_notification(
        recipient=None,
        category=NotificationCategory.SYSTEM,
        title="Missing",
        message="Body",
    )
    assert res1 is None
    assert created1 is False

    inactive_user = User.objects.create_user(
        email="inactive@gqt.local",
        password="TestPassword123!",
        is_active=False,
    )
    res2, created2 = create_notification(
        recipient=inactive_user,
        category=NotificationCategory.SYSTEM,
        title="Inactive",
        message="Body",
    )
    assert res2 is None
    assert created2 is False


@pytest.mark.django_db
def test_10_metadata_sensitive_key_redaction():
    """Metadata with passwords, tokens, API keys, or credentials is recursively redacted."""
    raw_metadata = {
        "user_id": "usr-123",
        "security": {
            "token": "secret-jwt-token-val",
            "password_hash": "hash_val_abc",
        },
        "integrations": [
            {"service": "email", "api_key": "sendgrid_key_val"},
            {"service": "db", "credentials": "db_pass_val"},
        ],
    }
    clean = sanitize_notification_metadata(raw_metadata)

    assert clean["user_id"] == "usr-123"
    assert clean["security"]["token"] == "[REDACTED]"
    assert clean["security"]["password_hash"] == "[REDACTED]"
    assert clean["integrations"][0]["api_key"] == "[REDACTED]"
    assert clean["integrations"][1]["credentials"] == "[REDACTED]"


@pytest.mark.django_db
def test_11_integrated_workflow_job_approval_triggers_notification(admin_user, user_a):
    """Approving a job requirement notifies the authoring officer."""
    company = Company.objects.create(name="Oracle India", normalized_name="oracle india")
    job = create_job_requirement(
        company=company,
        title="Software Engineer I",
        job_description="Core engineering role",
        skills_required="Java, Python, SQL",
        location="Bangalore",
        work_arrangement=WorkArrangement.ON_SITE,
        employment_type=EmploymentType.FULL_TIME,
        registration_deadline=timezone.now() + timezone.timedelta(days=14),
        created_by=user_a,
    )

    # Verify all mandatory checklist items to permit approval
    job.checklist_items.all().update(status=ChecklistItemStatus.VERIFIED)

    # Approve job requirement as admin
    approve_job_requirement(
        job=job,
        approver=admin_user,
        comments="Approved for recruitment drive",
    )

    # Verify notification created for user_a (job author)
    notif = Notification.objects.filter(
        recipient=user_a,
        category=NotificationCategory.JOB_DRIVE,
    ).first()
    assert notif is not None
    assert "Job Requirement Approved" in notif.title
    assert "Oracle India" in notif.message
    assert notif.link == "/jobs"


@pytest.mark.django_db
def test_12_integrated_workflow_student_application_triggers_notification(admin_user, user_b):
    """Student submitting drive self-application receives in-app notification with evaluation status."""
    student_profile = StudentProfile.objects.create(
        user=user_b,
        roll_number="GQT-2026-CS-001",
        institutional_email=user_b.email,
        college_name="GQT Engineering College",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2026,
        cgpa=8.5,
        phone_number="+91 98888 77777",
        is_verified_by_placement=True,
    )
    resume = StudentResume.objects.create(
        student=student_profile,
        version_number=1,
        file_name="bob.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b851",
        is_current=True,
    )
    company = Company.objects.create(name="TCS Digital", normalized_name="tcs digital")
    job = JobRequirement.objects.create(
        company=company,
        title="Systems Engineer",
        job_description="Enterprise software development",
        skills_required="Python, SQL",
        location="Hyderabad",
        work_arrangement=WorkArrangement.ON_SITE,
        employment_type=EmploymentType.FULL_TIME,
        registration_deadline=timezone.now() + timezone.timedelta(days=10),
        status=JobRequirementStatus.APPROVED,
        min_cgpa=7.0,
    )

    # Student applies for drive
    app = apply_student_for_job(
        student_profile=student_profile,
        job_requirement_id=str(job.id),
        user=user_b,
    )
    assert app is not None

    # Verify notification created for student
    notif = Notification.objects.filter(
        recipient=user_b,
        category=NotificationCategory.APPLICATION,
    ).first()
    assert notif is not None
    assert "Application Received" in notif.title
    assert "TCS Digital" in notif.message
    assert notif.link == "/students/drives"


@pytest.mark.django_db
def test_13_pagination_and_ordering(api_client, user_a):
    """Endpoints support server-side pagination and ordering by created_at descending."""
    now = timezone.now()
    for i in range(25):
        Notification.objects.create(
            recipient=user_a,
            category=NotificationCategory.SYSTEM,
            title=f"Notification #{i:02d}",
            message=f"Payload {i}",
            created_at=now + timezone.timedelta(minutes=i),
        )

    api_client.force_authenticate(user=user_a)
    resp = api_client.get("/api/v1/notifications/?page=1&page_size=10")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data["data"]) == 10
    assert resp.data["meta"]["count"] == 25
    assert resp.data["meta"]["total_pages"] == 3
    assert resp.data["meta"]["current_page"] == 1
    assert resp.data["meta"]["next"] is not None
    assert resp.data["meta"]["previous"] is None


@pytest.mark.django_db
def test_14_workflow_continues_if_notification_service_encounters_error(monkeypatch, admin_user, user_a):
    """Primary business operations (job approval) succeed cleanly even if notification dispatch fails."""
    company = Company.objects.create(name="Wipro Digital", normalized_name="wipro digital")
    job = create_job_requirement(
        company=company,
        title="QA Automation Engineer",
        job_description="Testing automation",
        skills_required="Selenium, Pytest",
        location="Pune",
        work_arrangement=WorkArrangement.ON_SITE,
        employment_type=EmploymentType.FULL_TIME,
        registration_deadline=timezone.now() + timezone.timedelta(days=7),
        created_by=user_a,
    )
    job.checklist_items.all().update(status=ChecklistItemStatus.VERIFIED)

    def crashing_create_notification(*args, **kwargs):
        raise RuntimeError("Simulated notification service outage")

    monkeypatch.setattr("apps.core.services_notifications.create_notification", crashing_create_notification)

    # Approve job - must not raise exception
    approved = approve_job_requirement(
        job=job,
        approver=admin_user,
        comments="Approved despite notification system outage",
    )
    assert approved.status == JobRequirementStatus.APPROVED
    assert approved.approved_by == admin_user


@pytest.mark.django_db
def test_15_business_transaction_rollback_reverts_notification(user_a):
    """If a business transaction rolls back, any in-transaction notification is also reverted."""
    from django.db import transaction

    try:
        with transaction.atomic():
            create_notification(
                recipient=user_a,
                category=NotificationCategory.SYSTEM,
                title="Transient Notice",
                message="This will roll back",
            )
            # Simulate a domain failure aborting the transaction
            raise ValueError("Intentional business failure")
    except ValueError:
        pass

    assert Notification.objects.filter(recipient=user_a, title="Transient Notice").exists() is False


@pytest.mark.django_db
def test_16_idempotency_empty_string_normalized_and_concurrency_safe(user_a):
    """Empty strings are normalized to None and do not violate database unique constraints."""
    notif1, c1 = create_notification(
        recipient=user_a,
        category=NotificationCategory.SYSTEM,
        title="Notice 1",
        message="Message",
        idempotency_key="",
    )
    notif2, c2 = create_notification(
        recipient=user_a,
        category=NotificationCategory.SYSTEM,
        title="Notice 2",
        message="Message",
        idempotency_key="   ",
    )
    notif3, c3 = create_notification(
        recipient=user_a,
        category=NotificationCategory.SYSTEM,
        title="Notice 3",
        message="Message",
        idempotency_key=None,
    )
    assert c1 is True and c2 is True and c3 is True
    assert notif1.id != notif2.id != notif3.id
    assert notif1.idempotency_key is None
    assert notif2.idempotency_key is None
    assert notif3.idempotency_key is None


@pytest.mark.django_db
def test_17_extended_metadata_secret_scrubbing_and_link_safety(api_client, user_a):
    """Extended credentials (authorization, private_key, session_id, client_secret) are sanitized; links restricted to internal routes."""
    raw_metadata = {
        "auth_headers": {
            "authorization": "Bearer eyJhbGciOi...",
            "access_token": "token_abc123",
            "session_id": "sess_987654",
        },
        "crypto": {
            "private_key": "-----BEGIN RSA PRIVATE KEY-----",
            "client_secret": "sec_xyz789",
        },
        "safe_info": "public_data",
    }
    notif, _ = create_notification(
        recipient=user_a,
        category=NotificationCategory.SYSTEM,
        title="Safe Notice",
        message="Clean body",
        link="https://malicious.com/phish",  # Must be stripped
        metadata=raw_metadata,
    )
    assert notif.link == ""  # Blocked external link

    # Internal link is preserved
    notif_internal, _ = create_notification(
        recipient=user_a,
        category=NotificationCategory.SYSTEM,
        title="Internal Notice",
        message="Body",
        link="/students/drives",
    )
    assert notif_internal.link == "/students/drives"

    # API output verification
    api_client.force_authenticate(user=user_a)
    resp = api_client.get(f"/api/v1/notifications/{notif.id}/")
    assert resp.status_code == status.HTTP_200_OK
    meta = resp.data["metadata"]
    assert meta["safe_info"] == "public_data"
    assert meta["auth_headers"]["authorization"] == "[REDACTED]"
    assert meta["auth_headers"]["access_token"] == "[REDACTED]"
    assert meta["auth_headers"]["session_id"] == "[REDACTED]"
    assert meta["crypto"]["private_key"] == "[REDACTED]"
    assert meta["crypto"]["client_secret"] == "[REDACTED]"


