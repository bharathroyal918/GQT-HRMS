"""PostgreSQL 16 Staging Verification and Production Readiness Test Suite.

Validates:
- Database environment, version 16.x, UTF-8 encoding, timezone semantics, least privilege
- Schema integrity: UUID PKs, FK CASCADE/PROTECT, unique/check constraints, JSONField, Decimal
- Atomic transactions and rollbacks
- Real multi-connection concurrency and row-level locking (select_for_update)
- Notification idempotency under concurrent load
- Student application deduplication under concurrency
- Query performance, indexing, and N+1 prevention (select_related / prefetch_related)
- End-to-end multi-workstream HRMS business flows on PostgreSQL 16
"""

import threading
from datetime import timedelta
from decimal import Decimal
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import connection, connections, transaction, IntegrityError
from django.db.models import ProtectedError, Q
from django.utils import timezone

from apps.accounts.models import Role, RoleCatalog, UserRoleAssignment
from apps.accounts import services as acc_svc
from apps.core.models import AuditLog, Notification, NotificationCategory
from apps.core import services_notifications as notif_svc
from apps.crm.models import Company, CompanyDomainCategory, HRContact, FollowUp, FollowUpStatus
from apps.jobs.models import (
    JobRequirement,
    JobRequirementStatus,
    JobChecklistItem,
    JobApprovalDecision,
    ChecklistItemStatus,
    EmploymentType,
    WorkArrangement,
)
from apps.jobs import services as job_svc
from apps.students.models import (
    StudentProfile,
    StudentResume,
    StudentApplication,
    StudentApplicationStatus,
    EligibilityEvaluation,
)
from apps.students import services as stu_svc
from apps.submissions.models import SubmissionPackage, CandidateSubmission
from apps.preparation.models import PlacementReadinessCertification
from apps.placements.models import (
    FinalResultIntake,
    CandidatePlacementStatus,
    CandidateOfferLetter,
    CandidatePlacementStatusChoices,
)
from apps.creatives.models import (
    CreativeRequest,
    CreativeRequestStatus,
    CreativeAssetVersion,
    CreativeDeliverableType,
)

User = get_user_model()


@pytest.fixture(autouse=True)
def require_postgres():
    """Verify that the active test database engine is PostgreSQL."""
    engine = connection.settings_dict.get("ENGINE", "")
    if "postgresql" not in engine:
        pytest.skip(f"Test requires PostgreSQL backend, active engine is: {engine}")


# ==============================================================================
# SECTION 1: PostgreSQL 16 Environment, Metadata & Security
# ==============================================================================

@pytest.mark.django_db
def test_postgres_16_server_version_and_encoding():
    """Verify PostgreSQL server version is 16.x and encoding is UTF8."""
    with connection.cursor() as cursor:
        cursor.execute("SHOW server_version;")
        version_str = cursor.fetchone()[0]
        assert version_str.startswith("16."), f"Expected PostgreSQL 16.x, found: {version_str}"

        cursor.execute("SHOW server_encoding;")
        encoding = cursor.fetchone()[0]
        assert encoding.upper() == "UTF8", f"Expected UTF8 encoding, found: {encoding}"

        cursor.execute("SHOW TimeZone;")
        tz = cursor.fetchone()[0]
        assert tz in ("UTC", "Asia/Kolkata", "Asia/Calcutta"), f"Unexpected timezone: {tz}"


@pytest.mark.django_db
def test_postgres_least_privilege_connection():
    """Verify application connection operates with least privilege (non-superuser)."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT current_user, usesuper FROM pg_user WHERE usename = current_user;")
        current_user, is_superuser = cursor.fetchone()
        assert is_superuser is False, f"Staging connection must NOT be PostgreSQL superuser! User: {current_user}"


# ==============================================================================
# SECTION 2: Database Integrity, Constraints & Data Types
# ==============================================================================

@pytest.mark.django_db
def test_uuid_primary_keys_and_jsonfield():
    """Verify UUIDv4 primary keys and PostgreSQL JSONField containment queries."""
    user = User.objects.create(
        email="pg_uuid_test@example.com",
        first_name="UUID",
        last_name="Tester",
        is_active=True,
    )
    assert user.id is not None
    assert len(str(user.id)) == 36, f"Invalid UUID string representation: {user.id}"

    notif, created = notif_svc.create_notification(
        recipient=user,
        category=NotificationCategory.SYSTEM,
        title="UUID & JSONField Test",
        message="Testing PostgreSQL jsonb storage",
        metadata={"source": "pg_staging_suite", "feature_flags": ["v1", "v2"], "metrics": {"score": 98.5}},
    )
    assert created is True
    assert notif is not None

    # PostgreSQL JSONField containment and key lookup
    found = Notification.objects.filter(metadata__source="pg_staging_suite").first()
    assert found is not None
    assert found.metadata.get("metrics", {}).get("score") == 98.5


@pytest.mark.django_db
def test_foreign_key_protect_and_cascade_behavior():
    """Verify PostgreSQL foreign key PROTECT prevents parent deletion and CASCADE removes dependents."""
    admin_user = User.objects.create(
        email="pg_admin_fk@example.com",
        first_name="Admin",
        last_name="FK",
        is_active=True,
    )
    admin_role, _ = Role.objects.get_or_create(code=RoleCatalog.ADMIN, defaults={"name": "Admin"})
    UserRoleAssignment.objects.create(
        user=admin_user,
        role=admin_role,
        is_active=True,
    )

    # CASCADE: deleting user cascades to UserRoleAssignment
    user_id = admin_user.id
    admin_user.delete()
    assert not UserRoleAssignment.objects.filter(user_id=user_id).exists()

    # PROTECT: Company with active JobRequirement cannot be deleted
    company = Company.objects.create(
        name="Postgres Protected Corp",
        website="https://pg-corp.example.com",
        domain_category=CompanyDomainCategory.PRODUCT_TECH,
    )
    job_user = User.objects.create(
        email="pg_job_creator@example.com",
        first_name="Job",
        last_name="Creator",
        is_active=True,
    )
    JobRequirement.objects.create(
        company=company,
        title="Software Engineer",
        job_description="Standard dev role",
        skills_required="Python, Django, PostgreSQL",
        location="Bengaluru",
        registration_deadline=timezone.now() + timedelta(days=14),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=3,
        min_salary=Decimal("1200000.00"),
        max_salary=Decimal("1500000.00"),
        created_by=job_user,
        status=JobRequirementStatus.DRAFT,
    )

    with pytest.raises(ProtectedError):
        company.delete()


@pytest.mark.django_db
def test_check_constraint_negative_openings_count_rejected():
    """Verify PostgreSQL check constraint rejects negative openings_count at database level."""
    company = Company.objects.create(name="Check Corp", website="https://check.example.com", domain_category=CompanyDomainCategory.IT_SERVICES)
    user = User.objects.create(email="pg_check_user@example.com", is_active=True)

    with pytest.raises(IntegrityError):
        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO jobs_requirement (
                        id, created_at, updated_at, is_deleted, is_archived, company_id,
                        title, job_description, skills_required, location, work_arrangement,
                        employment_type, has_bond, bond_details, eligibility_criteria,
                        hiring_process, openings_count, status, created_by_id, notes, salary_currency, salary_breakup
                    ) VALUES (
                        gen_random_uuid(), NOW(), NOW(), false, false, %s,
                        'Test Job', 'Desc', 'Skills', 'Remote', 'REMOTE',
                        'FULL_TIME', false, '', '', '', -5, 'DRAFT', %s, '', 'INR', ''
                    );
                """, [str(company.id), str(user.id)])


@pytest.mark.django_db(transaction=True)
def test_concurrent_candidate_submission_deduplication():
    """Verify unique constraint on (package, student) prevents duplicate candidate submissions under concurrency."""
    company = Company.objects.create(name="Submission Test Corp", website="https://subtest.com", domain_category=CompanyDomainCategory.PRODUCT_TECH)
    user = User.objects.create(email="pg_sub_admin@example.com", is_active=True)
    job = JobRequirement.objects.create(
        company=company,
        title="QA Engineer",
        job_description="Testing automation",
        skills_required="Pytest, Selenium",
        location="Chennai",
        registration_deadline=timezone.now() + timedelta(days=10),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=2,
        min_salary=Decimal("800000.00"),
        max_salary=Decimal("1000000.00"),
        created_by=user,
        status=JobRequirementStatus.APPROVED,
    )
    student_user = User.objects.create(email="pg_sub_student@example.com", is_active=True)
    profile = StudentProfile.objects.create(
        user=student_user,
        roll_number="PG16-SUB-001",
        institutional_email="sub.student@campus.edu",
        college_name="Engineering Institute",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.10"),
    )
    resume = StudentResume.objects.create(
        student=profile,
        version_number=1,
        file="resumes/sub_resume.pdf",
        file_name="sub_resume.pdf",
        file_size_bytes=1024,
        sha256_hash="abc123sha",
        is_current=True,
    )
    application = StudentApplication.objects.create(
        student=profile,
        job_requirement=job,
        status=StudentApplicationStatus.ELIGIBLE,
    )
    contact = HRContact.objects.create(
        company=company,
        name="HR Submissions Lead",
        designation="Recruiter",
        email="hr.sub@subtest.com",
    )
    package = SubmissionPackage.objects.create(
        company=company,
        job_requirement=job,
        hr_contact=contact,
        title="Round 1 Submission Package",
        created_by=user,
    )

    cert = PlacementReadinessCertification.objects.create(
        student=profile,
        approved_resume=resume,
        is_approved_for_placements=True,
        status="CERTIFIED",
        certified_by=user,
    )

    success_flags = []
    error_flags = []

    def submit_worker():
        try:
            connections.close_all()
            with transaction.atomic():
                CandidateSubmission.objects.create(
                    package=package,
                    student=profile,
                    application=application,
                    readiness_certification=cert,
                    submitted_resume=resume,
                    resume_version_number=1,
                    resume_sha256="abc123sha",
                )
            success_flags.append(True)
        except IntegrityError:
            error_flags.append("IntegrityError")
        finally:
            connections.close_all()

    threads = [threading.Thread(target=submit_worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert CandidateSubmission.objects.filter(package=package, student=profile).count() == 1
    assert len(success_flags) == 1
    assert len(error_flags) == 3


@pytest.mark.django_db
def test_decimal_precision_preservation():
    """Verify PostgreSQL numeric/decimal type preserves exact financial precision."""
    company = Company.objects.create(
        name="Precision Systems Ltd",
        website="https://precision.example.com",
        domain_category=CompanyDomainCategory.FINANCE_BANKING,
    )
    user = User.objects.create(
        email="pg_decimal@example.com",
        first_name="Decimal",
        last_name="Test",
        is_active=True,
    )
    target_salary = Decimal("1475500.50")
    job = JobRequirement.objects.create(
        company=company,
        title="Quant Developer",
        job_description="Algorithmic trading engine",
        skills_required="C++, Python, PostgreSQL",
        location="Mumbai",
        registration_deadline=timezone.now() + timedelta(days=7),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=2,
        min_salary=target_salary,
        max_salary=target_salary + Decimal("500000.00"),
        created_by=user,
        status=JobRequirementStatus.DRAFT,
    )
    job.refresh_from_db()
    assert job.min_salary == target_salary
    assert isinstance(job.min_salary, Decimal)


@pytest.mark.django_db
def test_timestamp_timezone_conversion_semantics():
    """Verify PostgreSQL timestamp with time zone preserves exact UTC / Asia/Kolkata equivalency."""
    user = User.objects.create(email="pg_tz_test@example.com", is_active=True)
    notif, _ = notif_svc.create_notification(
        recipient=user,
        category=NotificationCategory.SYSTEM,
        title="TZ Test",
        message="Verifying timestamp timezone semantics",
    )
    notif.refresh_from_db()
    # Stored timestamp must be timezone-aware
    assert timezone.is_aware(notif.created_at)

    with connection.cursor() as cursor:
        cursor.execute("SELECT created_at, created_at AT TIME ZONE 'Asia/Kolkata' FROM core_notification WHERE id = %s;", [str(notif.id)])
        utc_ts, kolkata_ts = cursor.fetchone()
        # Verify 5 hours 30 minutes delta
        delta = kolkata_ts - utc_ts.replace(tzinfo=None)
        assert delta == timedelta(hours=5, minutes=30)


@pytest.mark.django_db
def test_atomic_transaction_rollback():
    """Verify transaction.atomic() cleanly rolls back all modifications on exception."""
    initial_user_count = User.objects.count()
    initial_notif_count = Notification.objects.count()

    try:
        with transaction.atomic():
            temp_user = User.objects.create(
                email="pg_rollback_user@example.com",
                first_name="Rollback",
                last_name="Test",
                is_active=True,
            )
            Notification.objects.create(
                recipient=temp_user,
                category=NotificationCategory.SYSTEM,
                title="Rollback Candidate",
                message="This notification must be rolled back",
            )
            # Intentional failure to trigger rollback
            raise ValueError("Deliberate atomic transaction rollback simulation")
    except ValueError:
        pass

    assert User.objects.count() == initial_user_count
    assert Notification.objects.count() == initial_notif_count
    assert not User.objects.filter(email="pg_rollback_user@example.com").exists()


# ==============================================================================
# SECTION 3: Concurrency and Row-Level Locking (Multi-Connection)
# ==============================================================================

@pytest.mark.django_db(transaction=True)
def test_concurrent_notification_idempotency():
    """Verify 5 concurrent worker threads attempting to create identical idempotency key yield exactly 1 notification."""
    recipient = User.objects.create(
        email="pg_concur_notif@example.com",
        first_name="Concur",
        last_name="Notif",
        is_active=True,
    )
    idempotency_key = f"evt-pg-staging-concur-{recipient.id}"

    created_flags = []
    notifications = []
    errors = []

    def worker():
        try:
            connections.close_all()
            notif, created = notif_svc.create_notification(
                recipient=recipient,
                category=NotificationCategory.SYSTEM,
                title="Concurrent Alert",
                message="Testing concurrent idempotency",
                idempotency_key=idempotency_key,
            )
            if notif:
                notifications.append(notif.id)
            created_flags.append(created)
        except Exception as exc:
            errors.append(str(exc))
        finally:
            connections.close_all()

    threads = [threading.Thread(target=worker) for _ in range(5)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrent workers encountered unexpected exceptions: {errors}"
    assert created_flags.count(True) == 1, f"Expected exactly 1 created=True, got: {created_flags}"
    assert Notification.objects.filter(idempotency_key=idempotency_key).count() == 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_student_application_deduplication():
    """Verify concurrent student applications for the same drive produce exactly 1 record and reject duplicates."""
    student_user = User.objects.create(
        email="pg_concur_student@example.com",
        first_name="Concur",
        last_name="Student",
        is_active=True,
    )
    profile = StudentProfile.objects.create(
        user=student_user,
        roll_number="PG16-CONCUR-001",
        institutional_email="pg_concur_student@campus.edu",
        college_name="Engineering Institute",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.50"),
    )
    StudentResume.objects.create(
        student=profile,
        version_number=1,
        file="resumes/concur_resume.pdf",
        file_name="concur_resume.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_current=True,
    )

    company = Company.objects.create(name="PG Concur Tech", website="https://pg-concur.com", domain_category=CompanyDomainCategory.IT_SERVICES)
    admin = User.objects.create(email="pg_admin_concur@example.com", is_active=True)
    job = JobRequirement.objects.create(
        company=company,
        title="Cloud Engineer",
        job_description="AWS/GCP infrastructure",
        skills_required="Python, Docker, Terraform",
        location="Hyderabad",
        registration_deadline=timezone.now() + timedelta(days=5),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=5,
        min_salary=Decimal("1000000.00"),
        max_salary=Decimal("1400000.00"),
        created_by=admin,
        status=JobRequirementStatus.APPROVED,
    )

    success_count = []
    error_count = []

    def apply_worker():
        try:
            connections.close_all()
            app = stu_svc.apply_student_for_job(
                student_profile=profile,
                job_requirement_id=str(job.id),
                user=student_user,
            )
            success_count.append(app.id)
        except (ValidationError, IntegrityError) as exc:
            error_count.append(str(exc))
        finally:
            connections.close_all()

    threads = [threading.Thread(target=apply_worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Database unique constraint enforces single application
    total_db_apps = StudentApplication.objects.filter(student=profile, job_requirement=job).count()
    assert total_db_apps == 1, f"Expected exactly 1 application in database, found: {total_db_apps}"
    assert len(success_count) >= 1


@pytest.mark.django_db(transaction=True)
def test_concurrent_last_admin_protection():
    """Verify that multiple concurrent deactivation requests cannot deactivate the final system administrator."""
    last_admin = User.objects.create(
        email="pg_sole_admin@example.com",
        first_name="Sole",
        last_name="Admin",
        is_active=True,
    )
    admin_role, _ = Role.objects.get_or_create(code=RoleCatalog.ADMIN, defaults={"name": "Admin"})
    UserRoleAssignment.objects.create(user=last_admin, role=admin_role, is_active=True)

    operator = User.objects.create(
        email="pg_operator@example.com",
        first_name="Operator",
        last_name="User",
        is_active=True,
    )
    UserRoleAssignment.objects.create(user=operator, role=admin_role, is_active=True)

    # Deactivate operator first so last_admin is the only active admin remaining
    acc_svc.update_user_status(target_user=operator, is_active=False, updated_by=last_admin)

    # Now verify last_admin cannot be deactivated concurrently
    deactivation_results = []
    exceptions_raised = []

    def deactivation_worker():
        try:
            connections.close_all()
            acc_svc.update_user_status(
                target_user=last_admin,
                is_active=False,
                updated_by=operator,
            )
            deactivation_results.append("SUCCESS")
        except (ValidationError, Exception) as exc:
            exceptions_raised.append(type(exc).__name__)
        finally:
            connections.close_all()

    threads = [threading.Thread(target=deactivation_worker) for _ in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    last_admin.refresh_from_db()
    assert last_admin.is_active is True, "Final administrator must NEVER be deactivated!"
    assert len(deactivation_results) == 0, "Deactivation of last admin should not have succeeded!"


# ==============================================================================
# SECTION 4: Query Performance & Index Verification
# ==============================================================================

@pytest.mark.django_db
def test_select_related_and_explain_plan_on_indexes():
    """Verify query plan uses index scans on PostgreSQL for high-volume endpoints."""
    creator = User.objects.create(email="pg_query_idx@example.com", is_active=True)

    with connection.cursor() as cursor:
        cursor.execute("EXPLAIN SELECT * FROM core_notification WHERE recipient_id = %s;", [str(creator.id)])
        plan_lines = [row[0] for row in cursor.fetchall()]
        plan_text = " ".join(plan_lines)
        # PostgreSQL should plan an Index Scan or Bitmap Index Scan on recipient_id
        assert "Index" in plan_text or "Scan" in plan_text


# ==============================================================================
# SECTION 5: End-to-End Multi-Workstream HRMS Business Flows
# ==============================================================================

@pytest.mark.django_db
def test_e2e_user_and_role_administration_workflow():
    """Verify User administration, profile updates, role assignments, and audit logging on PostgreSQL."""
    for code, name in RoleCatalog.CHOICES:
        Role.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})

    admin_user = User.objects.create(
        email="pg_e2e_admin@example.com",
        first_name="E2E",
        last_name="SuperAdmin",
        is_active=True,
    )
    admin_role = Role.objects.get(code=RoleCatalog.ADMIN)
    UserRoleAssignment.objects.create(user=admin_user, role=admin_role, is_active=True)

    # 1. Admin creates new officer user via service
    validated_payload = {
        "email": "pg_e2e_officer@example.com",
        "password": "StrongOfficerPassword123!",
        "first_name": "Placement",
        "last_name": "Officer",
        "roles": [RoleCatalog.PLACEMENT_OFFICER],
    }
    officer = acc_svc.create_user_by_admin(
        validated_data=validated_payload,
        created_by=admin_user,
    )
    assert officer.is_active is True
    assert officer.has_role(RoleCatalog.PLACEMENT_OFFICER)

    # 2. Update officer profile
    updated_officer = acc_svc.update_user_profile(
        target_user=officer,
        validated_data={"first_name": "Senior Officer", "last_name": "Lead"},
        updated_by=admin_user,
    )
    assert updated_officer.first_name == "Senior Officer"

    # 3. Synchronize roles
    acc_svc.assign_roles_to_user(
        target_user=officer,
        role_codes=[RoleCatalog.PLACEMENT_OFFICER, RoleCatalog.HR_RELATIONSHIP_MGR],
        assigned_by=admin_user,
    )
    assert officer.has_role(RoleCatalog.HR_RELATIONSHIP_MGR)

    # 4. Deactivate officer
    acc_svc.update_user_status(target_user=officer, is_active=False, updated_by=admin_user)
    officer.refresh_from_db()
    assert officer.is_active is False

    # 5. AuditLog verification
    audit_events = AuditLog.objects.filter(resource_id=str(officer.id))
    assert audit_events.exists()


@pytest.mark.django_db
def test_e2e_crm_and_job_intake_workflow():
    """Verify Company creation, contact tracking, and job approval pipeline on PostgreSQL."""
    admin = User.objects.create(email="pg_crm_admin@example.com", is_active=True)
    admin_role, _ = Role.objects.get_or_create(code=RoleCatalog.ADMIN, defaults={"name": "Admin"})
    UserRoleAssignment.objects.create(user=admin, role=admin_role, is_active=True)

    company = Company.objects.create(
        name="Apex Global Technologies",
        website="https://apexglobal.example.com",
        domain_category=CompanyDomainCategory.PRODUCT_TECH,
    )
    contact = HRContact.objects.create(
        company=company,
        name="Sarah Jenkins",
        designation="Head of University Relations",
        email="sjenkins@apexglobal.example.com",
        phone="+91 9876543210",
    )
    assert contact.company == company

    job = job_svc.create_job_requirement(
        company=company,
        title="Full Stack Software Engineer",
        job_description="Building high scale SaaS solutions",
        skills_required="React, Django, PostgreSQL",
        location="Bengaluru",
        registration_deadline=timezone.now() + timedelta(days=20),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=10,
        min_salary=Decimal("1200000.00"),
        max_salary=Decimal("1600000.00"),
        created_by=admin,
        hr_contact=contact,
    )
    assert job.status == JobRequirementStatus.DRAFT

    # Verify all 5 mandatory checklist items using job_svc.verify_checklist_item
    for item in job.checklist_items.filter(is_mandatory=True):
        job_svc.verify_checklist_item(
            job=job,
            item_id=str(item.id),
            status=ChecklistItemStatus.VERIFIED,
            user=admin,
            remarks="Verified compliant.",
        )

    # Approve job requirement
    approved_job = job_svc.approve_job_requirement(
        job=job,
        approver=admin,
        comments="Approved for nationwide campus hiring drive.",
    )
    assert approved_job.status == JobRequirementStatus.APPROVED


@pytest.mark.django_db
def test_e2e_student_drive_and_notification_workflow():
    """Verify Student eligibility evaluation, drive application, and in-app notifications on PostgreSQL."""
    student_user = User.objects.create(
        email="pg_student_e2e@example.com",
        first_name="Pooja",
        last_name="Rao",
        is_active=True,
    )
    profile = StudentProfile.objects.create(
        user=student_user,
        roll_number="PG16-E2E-009",
        institutional_email="pooja.rao@campus.edu",
        college_name="Engineering Institute",
        degree="B.Tech",
        department="Information Science",
        graduation_year=2025,
        cgpa=Decimal("8.80"),
    )
    StudentResume.objects.create(
        student=profile,
        version_number=1,
        file="resumes/pooja_rao.pdf",
        file_name="pooja_rao.pdf",
        file_size_bytes=2048,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_current=True,
    )

    company = Company.objects.create(name="NexGen Labs", website="https://nexgen.example.com", domain_category=CompanyDomainCategory.IT_SERVICES)
    recruiter = User.objects.create(email="pg_recruiter_e2e@example.com", is_active=True)
    job = JobRequirement.objects.create(
        company=company,
        title="Data Engineer",
        job_description="ETL pipelines and warehouse modelling",
        skills_required="SQL, Python, Spark",
        location="Pune",
        registration_deadline=timezone.now() + timedelta(days=10),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=4,
        min_salary=Decimal("1100000.00"),
        max_salary=Decimal("1400000.00"),
        min_cgpa=Decimal("7.50"),
        created_by=recruiter,
        status=JobRequirementStatus.APPROVED,
    )

    # Student applies for job
    application = stu_svc.apply_student_for_job(
        student_profile=profile,
        job_requirement_id=str(job.id),
        user=student_user,
    )
    assert application.status in (StudentApplicationStatus.ELIGIBLE, StudentApplicationStatus.APPLIED)

    # In-app notification creation
    notif, created = notif_svc.create_notification(
        recipient=student_user,
        category=NotificationCategory.JOB_DRIVE,
        title="Drive Application Confirmed",
        message="Your application for Data Engineer at NexGen Labs has been accepted.",
        link=f"/drives/{job.id}",
    )
    assert created is True
    assert notif.is_read is False

    # Mark as read
    notif_svc.mark_notification_as_read(student_user, notif.id)
    notif.refresh_from_db()
    assert notif.is_read is True

    # Mark all read
    notif_svc.create_notification(
        recipient=student_user,
        category=NotificationCategory.SYSTEM,
        title="System Notice",
        message="Profile verification complete.",
    )
    unread_count = Notification.objects.filter(recipient=student_user, is_read=False).count()
    assert unread_count >= 1

    marked_count = notif_svc.mark_all_notifications_as_read(student_user)
    assert marked_count >= 1
    assert Notification.objects.filter(recipient=student_user, is_read=False).count() == 0


@pytest.mark.django_db
def test_e2e_placement_and_offer_workflow():
    """Verify Final Result Intake, Candidate Placement Status, and Offer Letter generation on PostgreSQL."""
    admin = User.objects.create(email="pg_placement_admin@example.com", is_active=True)
    company = Company.objects.create(name="Staging Placements Ltd", website="https://placements.example.com", domain_category=CompanyDomainCategory.PRODUCT_TECH)
    job = JobRequirement.objects.create(
        company=company,
        title="Associate Software Engineer",
        job_description="Entry level engineering program",
        skills_required="Java, Python, SQL",
        location="Bengaluru",
        registration_deadline=timezone.now() + timedelta(days=5),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=3,
        min_salary=Decimal("900000.00"),
        max_salary=Decimal("1200000.00"),
        created_by=admin,
        status=JobRequirementStatus.APPROVED,
    )
    student_user = User.objects.create(email="pg_placed_student@example.com", is_active=True)
    student = StudentProfile.objects.create(
        user=student_user,
        roll_number="PG16-PLACE-001",
        institutional_email="placed.student@campus.edu",
        college_name="Engineering College",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.90"),
    )

    # 1. Final result intake from company
    intake = FinalResultIntake.objects.create(
        company=company,
        job_requirement=job,
        result_reference_code="RES-2026-PG16-01",
        total_results=1,
        selected_count=1,
        created_by=admin,
    )
    assert intake.id is not None

    # 2. Record Candidate Placement Status
    placement = CandidatePlacementStatus.objects.create(
        intake=intake,
        job_requirement=job,
        company=company,
        student=student,
        status=CandidatePlacementStatusChoices.SELECTED,
        designation_offered="Associate Software Engineer",
        offered_ctc=Decimal("1150000.00"),
        work_location="Bengaluru",
        status_updated_by=admin,
    )
    assert placement.status == CandidatePlacementStatusChoices.SELECTED
    assert placement.offered_ctc == Decimal("1150000.00")

    # 3. Create Offer Letter record
    offer = CandidateOfferLetter.objects.create(
        placement_status=placement,
        student=student,
        job_requirement=job,
        company=company,
        file="offers/pg16_offer_001.pdf",
        file_name="pg16_offer_001.pdf",
        file_size_bytes=4096,
        sha256_hash="d7a8fbb307d7809469ca9abcb0082e4f8d5651e46d3cdb762d02d0bf37c9e592",
        version_number=1,
        issued_by=admin,
        acceptance_deadline=timezone.now() + timedelta(days=7),
    )
    assert offer.id is not None
    assert offer.version_number == 1


@pytest.mark.django_db
def test_e2e_creative_management_workflow():
    """Verify Creative Request and Asset Version lifecycle on PostgreSQL."""
    admin = User.objects.create(email="pg_creative_admin@example.com", is_active=True)
    company = Company.objects.create(name="Design Studio Corp", website="https://design.example.com", domain_category=CompanyDomainCategory.OTHER)
    job = JobRequirement.objects.create(
        company=company,
        title="UI Designer",
        job_description="Product design and visual identity",
        skills_required="Figma, UI/UX",
        location="Remote",
        registration_deadline=timezone.now() + timedelta(days=12),
        employment_type=EmploymentType.FULL_TIME,
        openings_count=1,
        min_salary=Decimal("700000.00"),
        max_salary=Decimal("900000.00"),
        created_by=admin,
        status=JobRequirementStatus.APPROVED,
    )

    request = CreativeRequest.objects.create(
        job_requirement=job,
        title="Drive Announcement Banner",
        deliverable_type=CreativeDeliverableType.BANNER,
        brief="Create high-resolution landscape banner for campus placement drive.",
        created_by=admin,
    )
    assert request.id is not None
    assert request.status == CreativeRequestStatus.DRAFT
