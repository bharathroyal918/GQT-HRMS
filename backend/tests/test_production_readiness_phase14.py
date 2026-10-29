"""Phase 14: Production Hardening, Concurrency & Security Regression Tests.

Verifies:
1. Concurrency: Stale PROCESSING reminder recovery after worker termination.
2. Concurrency: ProcessLock mutual exclusion for background follow-up worker.
3. File Security: Magic bytes validation, script rejection, and extension enforcement.
4. Communication Adapters: Simulation mode truthfulness, fail-closed live credentials, and webhook HMAC validation.
"""
import hashlib
import hmac
import io
import json
import os
import subprocess
import sys
import time
from datetime import timedelta
from decimal import Decimal
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Role, RoleCatalog, UserRoleAssignment
from apps.accounts.services import assign_roles_to_user
from apps.core.models import AuditLog
from apps.creatives.models import (
    CreativeDeliverableType,
    CreativeRequest,
    CreativeRequestStatus,
    AssetVersionStatus,
)
from apps.creatives.services import create_creative_request, upload_asset_version
from apps.creatives.validators import validate_and_sanitize_creative_file
from apps.crm.adapters.email import SimulatedEmailAdapter
from apps.crm.adapters.whatsapp import MetaWhatsAppAdapter, SimulatedWhatsAppAdapter
from apps.crm.management.commands.process_follow_ups import ProcessLock
from apps.crm.models import (
    Company,
    CompanyDomainCategory,
    CompanyTier,
    FollowUp,
    FollowUpPriority,
    FollowUpReminderItem,
    FollowUpStatus,
    HRContact,
    ReminderChannel,
    ReminderDeliveryStatus,
)
from apps.crm.scheduler import recover_stale_processing_reminders
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.placements.validators import validate_offer_letter_pdf
from apps.students.validators import validate_resume_pdf

User = get_user_model()


@pytest.fixture
def phase14_dataset(db):
    """Fixture providing base entities for Phase 14 concurrency and outbox tests."""
    officer_user = User.objects.create_user(
        email="officer14@gqt.internal",
        password="ValidStrongPassword123!@#",
        first_name="Placement",
        last_name="Officer",
        is_active=True,
    )
    po_role, _ = Role.objects.get_or_create(
        code=RoleCatalog.PLACEMENT_OFFICER, defaults={"name": "Placement Officer"}
    )
    UserRoleAssignment.objects.create(user=officer_user, role=po_role, is_active=True)

    company = Company.objects.create(
        name="Phase14 Tech Corp",
        website="https://p14tech.example.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        tier=CompanyTier.TIER_1_ENTERPRISE,
        created_by=officer_user,
    )
    hr_contact = HRContact.objects.create(
        company=company,
        name="HR Manager",
        designation="Senior Talent Lead",
        email="hrmgr@p14tech.example.com",
        phone="+919876543210",
        created_by=officer_user,
    )
    follow_up = FollowUp.objects.create(
        company=company,
        hr_contact=hr_contact,
        assigned_to=officer_user,
        created_by=officer_user,
        due_date=timezone.now() + timedelta(days=1),
        priority=FollowUpPriority.HIGH,
        status=FollowUpStatus.OPEN,
        purpose="Phase 14 Readiness Testing",
    )
    return {
        "officer": officer_user,
        "company": company,
        "hr_contact": hr_contact,
        "follow_up": follow_up,
    }


# ==============================================================================
# Workstream B & F: Concurrency & Stale Processing Recovery
# ==============================================================================

@pytest.mark.django_db
def test_recover_stale_processing_reminders_recovers_to_retry_scheduled(phase14_dataset):
    """Items stuck in PROCESSING longer than threshold must be recovered to RETRY_SCHEDULED."""
    follow_up = phase14_dataset["follow_up"]
    now = timezone.now()
    twenty_mins_ago = now - timedelta(minutes=20)

    item = FollowUpReminderItem.objects.create(
        follow_up=follow_up,
        channel=ReminderChannel.EMAIL,
        recipient="test@example.com",
        scheduled_for=twenty_mins_ago,
        status=ReminderDeliveryStatus.PROCESSING,
        attempt_count=1,
        max_attempts=3,
        idempotency_key="TEST-STALE-RECOVERY-1",
    )
    # Manually backdate updated_at to simulate a crashed worker
    FollowUpReminderItem.objects.filter(id=item.id).update(updated_at=twenty_mins_ago)

    recovered = recover_stale_processing_reminders(reference_time=now, stale_threshold_minutes=10)
    assert recovered == 1

    item.refresh_from_db()
    assert item.status == ReminderDeliveryStatus.RETRY_SCHEDULED
    assert item.backoff_until is not None
    assert "Recovered from stalled PROCESSING" in item.error_message

    # Audit log check
    audit = AuditLog.objects.filter(
        resource_id=str(item.id), action="FOLLOW_UP_REMINDER_RECOVERED"
    ).first()
    assert audit is not None
    assert audit.changes["new_status"] == "RETRY_SCHEDULED"


@pytest.mark.django_db
def test_recover_stale_processing_reminders_marks_exhausted_items_as_failed(phase14_dataset):
    """Items stuck in PROCESSING that have reached max_attempts must be marked FAILED."""
    follow_up = phase14_dataset["follow_up"]
    now = timezone.now()
    twenty_mins_ago = now - timedelta(minutes=20)

    item = FollowUpReminderItem.objects.create(
        follow_up=follow_up,
        channel=ReminderChannel.WHATSAPP,
        recipient="+919876543210",
        scheduled_for=twenty_mins_ago,
        status=ReminderDeliveryStatus.PROCESSING,
        attempt_count=3,
        max_attempts=3,
        idempotency_key="TEST-STALE-EXHAUSTED-1",
    )
    FollowUpReminderItem.objects.filter(id=item.id).update(updated_at=twenty_mins_ago)

    recovered = recover_stale_processing_reminders(reference_time=now, stale_threshold_minutes=10)
    assert recovered == 1

    item.refresh_from_db()
    assert item.status == ReminderDeliveryStatus.FAILED
    assert "Permanent failure" in item.error_message

    audit = AuditLog.objects.filter(
        resource_id=str(item.id), action="FOLLOW_UP_REMINDER_STALE_FAILED"
    ).first()
    assert audit is not None
    assert audit.changes["new_status"] == "FAILED"


def test_process_lock_mutual_exclusion():
    """ProcessLock must prevent overlapping process runs and release cleanly."""
    lock1 = ProcessLock(lock_name="test_worker_p14.lock")
    lock2 = ProcessLock(lock_name="test_worker_p14.lock")

    assert lock1.acquire() is True
    try:
        # A second lock instance for the same file should see the active process and reject
        assert lock2.acquire() is False
    finally:
        lock1.release()

    # After release, acquire should succeed
    assert lock2.acquire() is True
    lock2.release()


# ==============================================================================
# Workstream E: File Security & Magic Bytes
# ==============================================================================

def test_creative_validator_rejects_spoofed_file_and_active_scripts():
    """Creative validator must reject non-image payloads disguised with image extensions."""
    # 1. Spoofed HTML file with .png extension
    spoofed_file = SimpleUploadedFile(
        "malicious.png",
        b"<script>alert('xss')</script>",
        content_type="image/png",
    )
    with pytest.raises(ValidationError, match="File content contains prohibited markup"):
        validate_and_sanitize_creative_file(spoofed_file)

    # 2. SVG file explicitly prohibited
    svg_file = SimpleUploadedFile(
        "vector.svg",
        b"<svg xmlns='http://www.w3.org/2000/svg'><circle r='10'/></svg>",
        content_type="image/svg+xml",
    )
    with pytest.raises(ValidationError, match="strictly prohibited for security reasons"):
        validate_and_sanitize_creative_file(svg_file)

    # 3. Valid PNG header accepted
    # 8-byte PNG signature + minimal chunk
    valid_png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x0a\x00\x00\x00\x0a\x08\x06\x00\x00\x00"
    valid_file = SimpleUploadedFile("clean.png", valid_png_content, content_type="image/png")
    meta = validate_and_sanitize_creative_file(valid_file)
    assert meta["mime_type"] == "image/png"
    assert meta["width_px"] == 10
    assert meta["height_px"] == 10


def test_pdf_validators_enforce_magic_bytes():
    """Resume and Offer Letter validators must reject files lacking '%PDF-' signature."""
    invalid_file = SimpleUploadedFile("fake.pdf", b"This is plain text disguised as PDF.", content_type="application/pdf")

    with pytest.raises(ValidationError, match="Binary magic bytes signature mismatch"):
        validate_resume_pdf(invalid_file)

    with pytest.raises(ValidationError, match="Binary magic bytes signature mismatch"):
        validate_offer_letter_pdf(invalid_file)

    # Valid PDF magic header
    valid_pdf_file = SimpleUploadedFile("real.pdf", b"%PDF-1.4 sample content", content_type="application/pdf")
    resume_hash = validate_resume_pdf(valid_pdf_file)
    assert len(resume_hash) == 64

    offer_hash = validate_offer_letter_pdf(valid_pdf_file)
    assert len(offer_hash) == 64


# ==============================================================================
# Workstream G: Communication Adapters & Simulation Truthfulness
# ==============================================================================

def test_communication_adapters_simulation_mode_and_fail_closed():
    """Simulated adapters must truthfully declare simulation, and unconfigured live adapters fail closed."""
    # 1. Simulated Email Adapter
    email_sim = SimulatedEmailAdapter()
    res = email_sim.send_email(
        recipient="test@example.com",
        subject="Test Subject",
        body_text="Test Body",
    )
    assert res.success is True
    assert res.is_simulated is True
    assert res.status == "SIMULATED"
    assert res.provider_message_id.startswith("SIM-EMAIL-")

    # 2. Simulated WhatsApp Adapter
    wa_sim = SimulatedWhatsAppAdapter()
    res_wa = wa_sim.send_message(
        phone_number="9876543210",
        template_name="test_template",
        template_context={"var": "val"},
    )
    assert res_wa.success is True
    assert res_wa.is_simulated is True
    assert res_wa.status == "SIMULATED"
    assert res_wa.provider_message_id.startswith("SIM-WA-")

    # 3. Meta WhatsApp Adapter without credentials fails closed
    meta_adapter = MetaWhatsAppAdapter(api_token="", phone_number_id="")
    res_meta = meta_adapter.send_message(
        phone_number="9876543210",
        template_name="test_template",
        template_context={},
    )
    assert res_meta.success is False
    assert res_meta.is_simulated is False
    assert res_meta.status == "FAILED"
    assert "not configured" in res_meta.error_message


def test_whatsapp_webhook_signature_verification():
    """WhatsApp webhook signature validator must correctly verify HMAC-SHA256 signatures."""
    import hashlib
    import hmac

    adapter = SimulatedWhatsAppAdapter()
    payload = b'{"object":"whatsapp_business_account","entry":[]}'
    secret = "test_webhook_secret_key_123"

    # Compute genuine signature
    mac = hmac.new(secret.encode("utf-8"), msg=payload, digestmod=hashlib.sha256)
    expected_hex = mac.hexdigest()
    valid_header = f"sha256={expected_hex}"

    # Valid signature
    assert adapter.verify_webhook_signature(payload, valid_header, secret) is True

    # Tampered signature
    assert adapter.verify_webhook_signature(payload, "sha256=invalidhexsignature", secret) is False

    # Tampered payload
    assert adapter.verify_webhook_signature(b'{"tampered":true}', valid_header, secret) is False


# ==============================================================================
# Phase 14.1 Acceptance Remediation Regression Tests
# ==============================================================================

@pytest.mark.django_db
def test_whatsapp_webhook_post_fail_closed_missing_and_invalid_signature(phase14_dataset, monkeypatch):
    """WhatsApp POST webhook must reject missing/invalid signatures without mutating state."""
    client = APIClient()
    secret = "phase14-test-webhook-secret-999"
    monkeypatch.setenv("WHATSAPP_WEBHOOK_APP_SECRET", secret)

    follow_up = phase14_dataset["follow_up"]
    item = FollowUpReminderItem.objects.create(
        follow_up=follow_up,
        channel=ReminderChannel.WHATSAPP,
        recipient="+919876543210",
        scheduled_for=timezone.now(),
        provider_message_id="wamid.P141_TEST_MSG_1",
        status=ReminderDeliveryStatus.PROCESSING,
        idempotency_key="TEST-WA-POST-FC-1",
    )

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid.P141_TEST_MSG_1",
                                    "status": "delivered",
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    raw_body = json.dumps(payload).encode("utf-8")

    # 1. Missing signature header -> 401 Unauthorized
    res_no_sig = client.post(
        "/api/v1/crm/webhooks/whatsapp/",
        data=raw_body,
        content_type="application/json",
    )
    assert res_no_sig.status_code == status.HTTP_401_UNAUTHORIZED
    item.refresh_from_db()
    assert item.status == ReminderDeliveryStatus.PROCESSING  # State NOT mutated!

    # 2. Invalid signature header -> 401 Unauthorized
    res_bad_sig = client.post(
        "/api/v1/crm/webhooks/whatsapp/",
        data=raw_body,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256="sha256=0000000000000000000000000000000000000000000000000000000000000000",
    )
    assert res_bad_sig.status_code == status.HTTP_401_UNAUTHORIZED
    item.refresh_from_db()
    assert item.status == ReminderDeliveryStatus.PROCESSING  # State NOT mutated!

    # 3. Valid signature header -> 200 OK and updates delivery status
    valid_digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    res_valid = client.post(
        "/api/v1/crm/webhooks/whatsapp/",
        data=raw_body,
        content_type="application/json",
        HTTP_X_HUB_SIGNATURE_256=f"sha256={valid_digest}",
    )
    assert res_valid.status_code == status.HTTP_200_OK
    item.refresh_from_db()
    assert item.status == ReminderDeliveryStatus.DELIVERED
    assert item.delivered_at is not None


def test_whatsapp_webhook_get_fail_closed_production_token(monkeypatch):
    """WhatsApp GET webhook in production rejects fallback token and requires valid configured token."""
    client = APIClient()

    # Simulate production environment
    from django.conf import settings
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "DEBUG", False)

    # 1. Production with no token configured -> rejects dev fallback token
    monkeypatch.delenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", raising=False)
    res_no_token = client.get(
        "/api/v1/crm/webhooks/whatsapp/",
        {"hub.mode": "subscribe", "hub.verify_token": "gqt-hrms-wa-verify", "hub.challenge": "ch123"},
    )
    assert res_no_token.status_code == status.HTTP_403_FORBIDDEN

    # 2. Production with valid configured token -> accepts challenge
    monkeypatch.setenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "prod-strict-verify-token")
    res_valid = client.get(
        "/api/v1/crm/webhooks/whatsapp/",
        {"hub.mode": "subscribe", "hub.verify_token": "prod-strict-verify-token", "hub.challenge": "ch999"},
    )
    assert res_valid.status_code == status.HTTP_200_OK
    assert res_valid.content.decode() == "ch999"

    # 3. Production with mismatched token -> 403 Forbidden
    res_bad = client.get(
        "/api/v1/crm/webhooks/whatsapp/",
        {"hub.mode": "subscribe", "hub.verify_token": "invalid-token", "hub.challenge": "ch999"},
    )
    assert res_bad.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_recover_stale_processing_reminders_batch_bounded(phase14_dataset):
    """Stale reminder recovery must respect the batch_size limit and reject non-positive batch sizes."""
    follow_up = phase14_dataset["follow_up"]
    now = timezone.now()
    twenty_mins_ago = now - timedelta(minutes=20)

    # Create 5 stale items
    for i in range(5):
        item = FollowUpReminderItem.objects.create(
            follow_up=follow_up,
            channel=ReminderChannel.EMAIL,
            recipient=f"batch_{i}@example.com",
            scheduled_for=twenty_mins_ago,
            status=ReminderDeliveryStatus.PROCESSING,
            attempt_count=1,
            max_attempts=3,
            idempotency_key=f"TEST-BOUNDED-BATCH-{i}",
        )
        FollowUpReminderItem.objects.filter(id=item.id).update(updated_at=twenty_mins_ago)

    # Validate non-positive batch_size raises ValueError
    with pytest.raises(ValueError, match="batch_size must be a positive integer"):
        recover_stale_processing_reminders(batch_size=0)

    with pytest.raises(ValueError, match="batch_size must be a positive integer"):
        recover_stale_processing_reminders(batch_size=-5)

    # Invocation with batch_size=2 recovers exactly 2 items
    recovered_count = recover_stale_processing_reminders(
        reference_time=now,
        stale_threshold_minutes=10,
        batch_size=2,
    )
    assert recovered_count == 2

    # 3 items remain in PROCESSING, 2 transitioned to RETRY_SCHEDULED
    processing_count = FollowUpReminderItem.objects.filter(
        status=ReminderDeliveryStatus.PROCESSING,
        idempotency_key__startswith="TEST-BOUNDED-BATCH-",
    ).count()
    assert processing_count == 3

    retry_count = FollowUpReminderItem.objects.filter(
        status=ReminderDeliveryStatus.RETRY_SCHEDULED,
        idempotency_key__startswith="TEST-BOUNDED-BATCH-",
    ).count()
    assert retry_count == 2


def test_process_lock_atomic_stale_recovery_and_release():
    """ProcessLock uses persistent advisory locking, immune to stale file artifacts and PID recycling."""
    lock_name = "test_atomic_p14_worker.lock"
    lock1 = ProcessLock(lock_name=lock_name)
    lock2 = ProcessLock(lock_name=lock_name)

    assert lock1.acquire() is True
    try:
        # Second acquire fails atomically via OS advisory lock
        assert lock2.acquire() is False
    finally:
        lock1.release()

    # In advisory lock model, lock file persists safely without competing inodes
    assert lock1.lock_path.exists()

    # Simulate dead process by manually writing an arbitrary PID to lock file
    lock1.lock_path.write_text("99999999\n1730000000\n", encoding="utf-8")
    assert lock1.lock_path.exists()

    # A new lock instance acquires because the OS lock is free, regardless of file content
    lock3 = ProcessLock(lock_name=lock_name)
    assert lock3.acquire() is True
    try:
        assert lock3.lock_path.exists()
    finally:
        lock3.release()


def test_process_lock_simultaneous_startup():
    """Two or more workers starting at nearly the same time cannot both enter protected work."""
    lock_name = "test_concurrent_startup_p14.lock"
    lock = ProcessLock(lock_name=lock_name)
    if lock.lock_path.exists():
        try:
            lock.lock_path.unlink()
        except OSError:
            pass

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    worker_script = f"""
import os, sys, time
sys.path.insert(0, r"{backend_dir}")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
import django
django.setup()
from apps.crm.management.commands.process_follow_ups import ProcessLock

l = ProcessLock(lock_name="{lock_name}")
if l.acquire():
    sys.stdout.write("ACQUIRED\\n")
    sys.stdout.flush()
    time.sleep(1.0)
    l.release()
else:
    sys.stdout.write("DENIED\\n")
    sys.stdout.flush()
"""
    procs = []
    try:
        for _ in range(4):
            p = subprocess.Popen(
                [sys.executable, "-c", worker_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            procs.append(p)

        results = []
        for p in procs:
            out, err = p.communicate(timeout=15)
            results.append(out.strip())

        assert results.count("ACQUIRED") == 1, f"Expected exactly 1 ACQUIRED, got: {results}"
        assert results.count("DENIED") == 3, f"Expected 3 DENIED, got: {results}"
    finally:
        for p in procs:
            if p.poll() is None:
                p.kill()
                p.wait()
        if lock.lock_path.exists():
            try:
                lock.lock_path.unlink()
            except OSError:
                pass


def test_process_lock_crash_recovery():
    """After a lock-holding process terminates unexpectedly, another process can acquire."""
    lock_name = "test_crash_recovery_p14.lock"
    lock = ProcessLock(lock_name=lock_name)
    if lock.lock_path.exists():
        try:
            lock.lock_path.unlink()
        except OSError:
            pass

    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    child_script = f"""
import os, sys, time
sys.path.insert(0, r"{backend_dir}")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.test")
import django
django.setup()
from apps.crm.management.commands.process_follow_ups import ProcessLock

l = ProcessLock(lock_name="{lock_name}")
if l.acquire():
    sys.stdout.write("HELD\\n")
    sys.stdout.flush()
    time.sleep(30)
"""
    p = subprocess.Popen(
        [sys.executable, "-c", child_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        status_line = p.stdout.readline().strip()
        assert status_line == "HELD"

        # Active lock check: second process must be denied while child lives
        l2 = ProcessLock(lock_name=lock_name)
        assert l2.acquire() is False

        # Simulate crash/SIGKILL
        p.kill()
        p.wait()

        # The OS kernel frees the lock automatically; new process acquires immediately
        assert l2.acquire() is True
        l2.release()
    finally:
        if p.poll() is None:
            p.kill()
            p.wait()
        if lock.lock_path.exists():
            try:
                lock.lock_path.unlink()
            except OSError:
                pass


def test_process_lock_pid_recycling_resilience():
    """A stale PID record alone cannot prevent recovery when the OS lock is not held."""
    lock_name = "test_pid_recycling_p14.lock"
    lock = ProcessLock(lock_name=lock_name)
    lock.lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock.lock_path.write_text(f"{os.getpid()}\n1700000000\n", encoding="utf-8")

    # Even though file contains an active PID, no descriptor holds the OS advisory lock
    new_lock = ProcessLock(lock_name=lock_name)
    assert new_lock.acquire() is True
    try:
        assert new_lock._acquired is True
    finally:
        new_lock.release()


def test_process_lock_safe_release():
    """One process/instance cannot release another process's lock."""
    lock_name = "test_safe_release_p14.lock"
    lock_owner = ProcessLock(lock_name=lock_name)
    lock_rogue = ProcessLock(lock_name=lock_name)

    assert lock_owner.acquire() is True
    lock_third = ProcessLock(lock_name=lock_name)
    try:
        # Rogue instance attempts to release without holding the lock
        lock_rogue.release()

        # lock_owner must still hold the lock; third instance cannot acquire
        assert lock_third.acquire() is False
    finally:
        lock_owner.release()

    # After owner releases, third instance can acquire
    assert lock_third.acquire() is True
    lock_third.release()


def test_process_lock_exception_cleanup():
    """Exceptions during protected work release the lock via context manager."""
    lock_name = "test_exception_cleanup_p14.lock"
    with pytest.raises(RuntimeError, match="critical section failure"):
        with ProcessLock(lock_name=lock_name):
            raise RuntimeError("critical section failure")

    # Lock must be free for reacquisition
    lock2 = ProcessLock(lock_name=lock_name)
    assert lock2.acquire() is True
    lock2.release()


def test_process_lock_repeated_lifecycle():
    """Acquire, idempotent acquire, and release work reliably across repeated cycles."""
    lock_name = "test_lifecycle_p14.lock"
    lock = ProcessLock(lock_name=lock_name)
    for _ in range(5):
        assert lock.acquire() is True
        assert lock.acquire() is True  # Idempotent re-acquisition
        lock.release()


@pytest.mark.django_db
def test_process_follow_ups_command_lock_integration():
    """Management command respects active ProcessLock and exits gracefully."""
    out = io.StringIO()
    # 1. Run with --dry-run and --once when lock is free
    call_command("process_follow_ups", once=True, dry_run=True, stdout=out)
    assert "Cycle completed successfully" in out.getvalue()

    # 2. Acquire default lock in another instance, then invoke command
    held_lock = ProcessLock()
    assert held_lock.acquire() is True
    try:
        out_blocked = io.StringIO()
        call_command("process_follow_ups", once=True, dry_run=True, stdout=out_blocked)
        assert "Another instance of process_follow_ups is already active" in out_blocked.getvalue()
    finally:
        held_lock.release()


@pytest.mark.django_db
def test_creative_asset_download_storage_agnostic(phase14_dataset):
    """Creative asset download must stream via file.open() without relying on local .path."""
    client = APIClient()
    officer = phase14_dataset["officer"]
    company = phase14_dataset["company"]
    client.force_authenticate(user=officer)

    job = JobRequirement.objects.create(
        company=company,
        title="Software Engineer 2026",
        job_description="Core engineering role",
        skills_required="Python, Django",
        min_salary=Decimal("6.00"),
        max_salary=Decimal("9.00"),
        location="Bengaluru",
        eligibility_criteria="BE/B.Tech with 60%+",
        interview_date=timezone.now() + timedelta(days=15),
        registration_deadline=timezone.now() + timedelta(days=5),
        status=JobRequirementStatus.APPROVED,
        created_by=officer,
    )

    req = create_creative_request(
        job_requirement=job,
        user=officer,
        title="Campus Drive Banner",
        deliverable_type=CreativeDeliverableType.BANNER,
    )

    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x08\x00\x00\x00\x08\x08\x06\x00\x00\x00"
    upload_file = SimpleUploadedFile("banner.png", png_bytes, content_type="image/png")

    version = upload_asset_version(
        creative_req=req,
        uploaded_file=upload_file,
        designer_user=officer,
        designer_notes="Storage-agnostic test asset",
    )

    url = f"/api/v1/creatives/requests/{req.id}/versions/{version.id}/file/"
    res = client.get(url)
    assert res.status_code == status.HTTP_200_OK
    assert res["Content-Type"] == "image/png"

    # Verify streamed payload matches uploaded bytes
    streamed_bytes = b"".join(res.streaming_content) if hasattr(res, "streaming_content") else res.content
    assert streamed_bytes == png_bytes
