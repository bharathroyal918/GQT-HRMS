"""Comprehensive test suite for Phase 10: CRM Database Update & Cross-Module Integration."""
from datetime import timedelta
import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import RoleCatalog
from apps.accounts.services import assign_roles_to_user
from apps.core.models import AuditLog
from apps.crm.models import (
    Company,
    CompanyDomainCategory,
    CompanyRelationshipStatus,
    CRMReconciliationRun,
    HRContact,
    OutreachChannel,
    OutreachLog,
    OutreachOutcome,
)
from apps.crm.selectors import (
    get_company_360_profile,
    get_company_communication_timeline,
    get_crm_database_health_diagnostics,
    get_student_360_profile,
    get_student_communication_timeline,
)
from apps.crm.services import run_crm_database_reconciliation
from apps.feedback.models import HRFeedback, StudentFeedback, TrainerFeedback
from apps.interviews.models import (
    InterviewNotificationLog,
    InterviewRound,
    InterviewSchedule,
)
from apps.jobs.models import JobRequirement
from apps.placements.models import (
    CandidateOfferLetter,
    CandidatePlacementStatus,
    FinalResultIntake,
    PlacementNotificationLog,
)
from apps.preparation.models import PlacementReadinessCertification
from apps.students.models import JobPublication, StudentProfile, StudentResume
from apps.submissions.models import (
    CandidateSubmission,
    SubmissionDispatchLog,
    SubmissionPackage,
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
def student_user_1(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="student1@gqt.local", password=test_password, first_name="Aarav", last_name="Sharma"
    )
    assign_roles_to_user(user, [RoleCatalog.STUDENT])
    return user


@pytest.fixture
def student_user_2(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="student2@gqt.local", password=test_password, first_name="Diya", last_name="Patel"
    )
    assign_roles_to_user(user, [RoleCatalog.STUDENT])
    return user


@pytest.fixture
def trainer_user(db, seed_roles, test_password):
    user = User.objects.create_user(
        email="trainer@gqt.local", password=test_password, first_name="Ravi", last_name="Kumar"
    )
    assign_roles_to_user(user, [RoleCatalog.TRAINER])
    return user


@pytest.fixture
def sample_company(db, admin_user):
    return Company.objects.create(
        name="Tata Consultancy Services",
        website="https://www.tcs.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        relationship_status=CompanyRelationshipStatus.DISCOVERED,
        city="Mumbai",
        created_by=admin_user,
    )


@pytest.fixture
def sample_hr_contact(db, sample_company, admin_user):
    return HRContact.objects.create(
        company=sample_company,
        name="Pooja Mehta",
        designation="Lead Campus Recruiter",
        email="pooja.m@tcs.example.com",
        phone="+919876543210",
        created_by=admin_user,
    )


@pytest.fixture
def sample_student_profile(db, student_user_1):
    return StudentProfile.objects.create(
        user=student_user_1,
        roll_number="GQT-2026-CS-001",
        institutional_email="aarav.s@campus.gqt.edu",
        department="Computer Science",
        degree="B.Tech",
        college_name="GQT Engineering Institute",
        cgpa=8.75,
        graduation_year=2026,
        is_verified_by_placement=True,
    )


@pytest.fixture
def sample_student_profile_2(db, student_user_2):
    return StudentProfile.objects.create(
        user=student_user_2,
        roll_number="GQT-2026-CS-002",
        institutional_email="diya.p@campus.gqt.edu",
        department="Information Technology",
        degree="B.Tech",
        college_name="GQT Engineering Institute",
        cgpa=9.10,
        graduation_year=2026,
        is_verified_by_placement=True,
    )


@pytest.fixture
def sample_job_requirement(db, sample_company, sample_hr_contact, admin_user):
    return JobRequirement.objects.create(
        company=sample_company,
        hr_contact=sample_hr_contact,
        title="Associate Software Engineer",
        job_description="Standard software engineer role.",
        skills_required="Python, Django, React",
        location="Bengaluru",
        registration_deadline=timezone.now() + timedelta(days=7),
        openings_count=10,
        created_by=admin_user,
    )


@pytest.fixture
def sample_result_intake(db, sample_company, sample_job_requirement, admin_user):
    return FinalResultIntake.objects.create(
        company=sample_company,
        job_requirement=sample_job_requirement,
        result_reference_code="INTAKE-2026-001",
        total_results=1,
        selected_count=1,
        created_by=admin_user,
    )


# ==============================================================================
# Health Diagnostics Across the 8 Recruitment Workflow Areas
# ==============================================================================

@pytest.mark.django_db
def test_crm_health_diagnostics_clean_state(sample_company, sample_hr_contact, sample_student_profile):
    """Clean state diagnostic yields 100% health score and status HEALTHY."""
    report = get_crm_database_health_diagnostics()
    assert report["summary"]["total_conflicts"] == 0
    assert report["summary"]["status"] == "HEALTHY"
    assert report["summary"]["health_score_percentage"] == 100.0
    assert report["areas"]["company"]["status"] == "CLEAN"
    assert report["areas"]["hr"]["status"] == "CLEAN"
    assert report["areas"]["students"]["status"] == "CLEAN"


@pytest.mark.django_db
def test_crm_health_diagnostics_company_unpromoted_conflict(
    sample_company, sample_student_profile, sample_job_requirement, sample_result_intake, admin_user
):
    """Company with verified selected candidate but DISCOVERED status triggers INFO conflict."""
    CandidatePlacementStatus.objects.create(
        intake=sample_result_intake,
        student=sample_student_profile,
        job_requirement=sample_job_requirement,
        company=sample_company,
        status="SELECTED",
        offered_ctc=750000.00,
        designation_offered="Software Engineer",
        status_updated_by=admin_user,
    )

    report = get_crm_database_health_diagnostics()
    assert report["summary"]["total_conflicts"] >= 1
    assert report["areas"]["company"]["conflicts"] >= 1
    company_conflicts = [c for c in report["conflicts"] if c["area"] == "Company"]
    assert len(company_conflicts) == 1
    assert company_conflicts[0]["severity"] == "INFO"
    assert "ACTIVE_HIRING_PARTNER" in company_conflicts[0]["recommended_action"]


@pytest.mark.django_db
def test_crm_health_diagnostics_hr_contact_mismatch(
    sample_company, sample_hr_contact, admin_user
):
    """JobRequirement referencing HRContact from another company triggers CRITICAL conflict."""
    other_company = Company.objects.create(
        name="Wipro Enterprises",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        created_by=admin_user,
    )
    JobRequirement.objects.create(
        company=other_company,
        hr_contact=sample_hr_contact,  # Belongs to sample_company, NOT other_company
        title="Associate Software Engineer",
        job_description="Mismatch test role.",
        skills_required="Java, Spring",
        location="Hyderabad",
        registration_deadline=timezone.now() + timedelta(days=5),
        openings_count=5,
        created_by=admin_user,
    )

    report = get_crm_database_health_diagnostics()
    assert report["summary"]["status"] == "CRITICAL"
    hr_conflicts = [c for c in report["conflicts"] if c["area"] == "HR"]
    assert len(hr_conflicts) == 1
    assert hr_conflicts[0]["severity"] == "CRITICAL"


@pytest.mark.django_db
def test_crm_health_diagnostics_cgpa_out_of_bounds(student_user_1):
    """Student with CGPA > 10.0 triggers WARNING conflict."""
    StudentProfile.objects.create(
        user=student_user_1,
        roll_number="GQT-INVALID-CGPA",
        cgpa=11.5,  # Out of range
        graduation_year=2026,
    )

    report = get_crm_database_health_diagnostics()
    student_conflicts = [c for c in report["conflicts"] if c["area"] == "Students"]
    assert len(student_conflicts) == 1
    assert student_conflicts[0]["severity"] == "WARNING"


@pytest.mark.django_db
def test_crm_health_diagnostics_multiple_active_resumes(sample_student_profile, admin_user):
    """Student with multiple is_current=True resumes triggers WARNING conflict."""
    StudentResume.objects.create(
        student=sample_student_profile,
        version_number=1,
        file="resumes/resume_v1.pdf",
        file_name="resume_v1.pdf",
        file_size_bytes=1024,
        sha256_hash="a" * 64,
        is_current=True,
    )
    StudentResume.objects.create(
        student=sample_student_profile,
        version_number=2,
        file="resumes/resume_v2.pdf",
        file_name="resume_v2.pdf",
        file_size_bytes=2048,
        sha256_hash="b" * 64,
        is_current=True,
    )

    report = get_crm_database_health_diagnostics()
    resume_conflicts = [c for c in report["conflicts"] if c["area"] == "Resume Versions"]
    assert len(resume_conflicts) == 1
    assert resume_conflicts[0]["severity"] == "WARNING"


@pytest.mark.django_db
def test_crm_health_diagnostics_invalid_offer_letter(
    sample_company, sample_student_profile, sample_job_requirement, sample_result_intake, admin_user
):
    """Offer letter for candidate with status REJECTED triggers CRITICAL conflict."""
    status_record = CandidatePlacementStatus.objects.create(
        intake=sample_result_intake,
        student=sample_student_profile,
        job_requirement=sample_job_requirement,
        company=sample_company,
        status="REJECTED",  # Not SELECTED
        status_updated_by=admin_user,
    )
    CandidateOfferLetter.objects.create(
        placement_status=status_record,
        student=sample_student_profile,
        job_requirement=sample_job_requirement,
        company=sample_company,
        file="offers/letter.pdf",
        file_name="letter.pdf",
        file_size_bytes=10240,
        sha256_hash="d" * 64,
        issued_by=admin_user,
    )

    report = get_crm_database_health_diagnostics()
    placement_conflicts = [c for c in report["conflicts"] if c["area"] == "Placement Status"]
    assert any(c["severity"] == "CRITICAL" for c in placement_conflicts)


# ==============================================================================
# 360-Degree Profile & Timeline Aggregations
# ==============================================================================

@pytest.mark.django_db
def test_company_360_profile_aggregation(
    sample_company, sample_hr_contact, sample_student_profile, sample_job_requirement, sample_result_intake, admin_user
):
    """get_company_360_profile aggregates jobs, placements, CTC metrics, and feedback."""
    ps = CandidatePlacementStatus.objects.create(
        intake=sample_result_intake,
        student=sample_student_profile,
        company=sample_company,
        job_requirement=sample_job_requirement,
        status="SELECTED",
        offered_ctc=800000.00,
        designation_offered="Software Engineer",
        status_updated_by=admin_user,
    )

    CandidateOfferLetter.objects.create(
        placement_status=ps,
        student=sample_student_profile,
        job_requirement=sample_job_requirement,
        company=sample_company,
        file="offers/tcs_offer.pdf",
        file_name="tcs_offer.pdf",
        file_size_bytes=2048,
        sha256_hash="e" * 64,
        acceptance_status="ACCEPTED",
        joining_status="JOINED",
        issued_by=admin_user,
    )

    HRFeedback.objects.create(
        company=sample_company,
        hr_contact=sample_hr_contact,
        candidate=sample_student_profile,
        job_requirement=sample_job_requirement,
        technical_skills_rating=5,
        communication_skills_rating=4,
        hiring_satisfaction_rating=5,
        submitted_by=admin_user,
    )

    profile = get_company_360_profile(sample_company.id)
    assert profile["company"]["name"] == sample_company.name
    assert profile["lifetime_metrics"]["total_jobs"] == 1
    assert profile["lifetime_metrics"]["total_placed"] == 1
    assert profile["lifetime_metrics"]["total_joined"] == 1
    assert profile["lifetime_metrics"]["avg_offered_ctc"] == 800000.00
    assert profile["feedback_summary"]["total_hr_evaluations"] == 1
    assert profile["feedback_summary"]["avg_technical_skills_rating"] == 5.0
    assert len(profile["placed_candidates"]) == 1
    assert profile["placed_candidates"][0]["joining_status"] == "JOINED"


@pytest.mark.django_db
def test_student_360_profile_aggregation(
    sample_company, sample_student_profile, sample_job_requirement, sample_result_intake, trainer_user, admin_user
):
    """get_student_360_profile aggregates academic, certification, resume, and placement status."""
    resume = StudentResume.objects.create(
        student=sample_student_profile,
        version_number=1,
        file="resumes/aarav_resume_v1.pdf",
        file_name="aarav_resume_v1.pdf",
        file_size_bytes=5120,
        sha256_hash="c" * 64,
        is_current=True,
    )

    PlacementReadinessCertification.objects.create(
        student=sample_student_profile,
        approved_resume=resume,
        is_approved_for_placements=True,
        certified_by=admin_user,
        notes="Candidate certified with distinction.",
    )

    ps = CandidatePlacementStatus.objects.create(
        intake=sample_result_intake,
        student=sample_student_profile,
        company=sample_company,
        job_requirement=sample_job_requirement,
        status="SELECTED",
        offered_ctc=650000.00,
        status_updated_by=admin_user,
    )

    CandidateOfferLetter.objects.create(
        placement_status=ps,
        student=sample_student_profile,
        job_requirement=sample_job_requirement,
        company=sample_company,
        file="offers/tcs_offer.pdf",
        file_name="tcs_offer.pdf",
        file_size_bytes=2048,
        sha256_hash="f" * 64,
        acceptance_status="ACCEPTED",
        joining_status="JOINED",
        issued_by=admin_user,
    )

    TrainerFeedback.objects.create(
        student=sample_student_profile,
        trainer=trainer_user,
        student_readiness="READY",
        training_effectiveness_rating=5,
        areas_for_improvement="Technical concepts",
    )

    profile = get_student_360_profile(sample_student_profile.id)
    assert profile["student"]["roll_number"] == "GQT-2026-CS-001"
    assert profile["readiness_gate"]["is_certified"] is True
    assert len(profile["resumes"]) == 1
    assert profile["overall_placement_outcome"] == "JOINED"
    assert len(profile["placement_history"]) == 1
    assert len(profile["trainer_evaluations"]) == 1


@pytest.mark.django_db
def test_company_and_student_communication_timelines(
    sample_company, sample_hr_contact, sample_student_profile, sample_job_requirement, sample_result_intake, admin_user
):
    """Timelines assemble communication records in reverse chronological order."""
    # 1. Company outreach log
    OutreachLog.objects.create(
        company=sample_company,
        hr_contact=sample_hr_contact,
        channel=OutreachChannel.CALL,
        outcome=OutreachOutcome.CONNECTED_INTERESTED,
        subject="Introductory drive alignment",
        performed_by=admin_user,
    )

    # 2. Student placement notification
    ps = CandidatePlacementStatus.objects.create(
        intake=sample_result_intake,
        student=sample_student_profile,
        company=sample_company,
        job_requirement=sample_job_requirement,
        status="SELECTED",
        status_updated_by=admin_user,
    )
    PlacementNotificationLog.objects.create(
        placement_status=ps,
        student=sample_student_profile,
        channel="EMAIL",
        recipient_email=sample_student_profile.institutional_email,
        status="SENT",
        sent_by=admin_user,
    )

    # Verify Company timeline
    company_timeline = get_company_communication_timeline(sample_company.id)
    assert len(company_timeline) >= 2
    categories = [event["category"] for event in company_timeline]
    assert "OUTREACH" in categories
    assert "PLACEMENT_NOTIFICATION" in categories

    # Verify Student timeline
    student_timeline = get_student_communication_timeline(sample_student_profile.id)
    assert len(student_timeline) >= 1
    assert student_timeline[0]["category"] == "PLACEMENT_ADVISORY"


# ==============================================================================
# Reconciliation Services & Idempotence
# ==============================================================================

@pytest.mark.django_db
def test_reconciliation_service_dry_run(
    sample_company, sample_student_profile, sample_job_requirement, sample_result_intake, admin_user
):
    """Dry run identifies discrepancy and creates CRMReconciliationRun without mutating company."""
    CandidatePlacementStatus.objects.create(
        intake=sample_result_intake,
        student=sample_student_profile,
        company=sample_company,
        job_requirement=sample_job_requirement,
        status="SELECTED",
        status_updated_by=admin_user,
    )

    result = run_crm_database_reconciliation(user=admin_user, dry_run=True)

    assert result["dry_run"] is True
    assert result["records_synchronized"] == 0
    assert result["conflicts_detected"] >= 1

    sample_company.refresh_from_db()
    # Company status remains DISCOVERED (unchanged in dry run)
    assert sample_company.relationship_status == CompanyRelationshipStatus.DISCOVERED

    run_record = CRMReconciliationRun.objects.get(id=result["run_id"])
    assert run_record.triggered_by == admin_user
    assert "DRY-RUN" in run_record.summary


@pytest.mark.django_db
def test_reconciliation_service_live_execution_and_idempotence(
    sample_company, sample_student_profile, sample_job_requirement, sample_result_intake, admin_user
):
    """Live reconciliation promotes company to ACTIVE_HIRING_PARTNER, and repeated runs are idempotent."""
    CandidatePlacementStatus.objects.create(
        intake=sample_result_intake,
        student=sample_student_profile,
        company=sample_company,
        job_requirement=sample_job_requirement,
        status="SELECTED",
        status_updated_by=admin_user,
    )

    # Run 1: Live sync
    result1 = run_crm_database_reconciliation(user=admin_user, dry_run=False)
    assert result1["records_synchronized"] == 1
    assert result1["status"] == "SUCCESS"

    sample_company.refresh_from_db()
    assert sample_company.relationship_status == CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER

    # Audit log check
    audit = AuditLog.objects.filter(action="CRM_RECONCILIATION_EXECUTED").first()
    assert audit is not None
    assert audit.user == admin_user

    # Run 2: Repeated live sync (idempotent, 0 new updates needed)
    result2 = run_crm_database_reconciliation(user=admin_user, dry_run=False)
    assert result2["records_synchronized"] == 0
    assert result2["status"] == "SUCCESS"
    assert result2["conflicts_detected"] == 0

    sample_company.refresh_from_db()
    assert sample_company.relationship_status == CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER


# ==============================================================================
# REST API Endpoints & Role-Based Access Control
# ==============================================================================

@pytest.mark.django_db
def test_api_reconciliation_diagnostics_staff_and_auditor(
    api_client, placement_officer_user, auditor_user, student_user_1
):
    """Diagnostics endpoint allows Placement Officer and Auditor, but denies Student."""
    # 1. Placement Officer -> 200 OK
    api_client.force_authenticate(user=placement_officer_user)
    resp = api_client.get("/api/v1/crm/reconciliation/diagnostics/")
    assert resp.status_code == status.HTTP_200_OK
    assert "summary" in resp.data["data"]
    assert "areas" in resp.data["data"]

    # 2. Auditor -> 200 OK (Auditors have read-only diagnostic visibility)
    api_client.force_authenticate(user=auditor_user)
    resp_audit = api_client.get("/api/v1/crm/reconciliation/diagnostics/")
    assert resp_audit.status_code == status.HTTP_200_OK

    # 3. Student -> 403 Forbidden
    api_client.force_authenticate(user=student_user_1)
    resp_student = api_client.get("/api/v1/crm/reconciliation/diagnostics/")
    assert resp_student.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_api_reconciliation_sync_staff_vs_auditor(
    api_client, placement_head_user, auditor_user
):
    """Sync endpoint allows Placement Head to mutate, but rejects Auditor with 403."""
    # 1. Placement Head -> 200 OK
    api_client.force_authenticate(user=placement_head_user)
    resp = api_client.post("/api/v1/crm/reconciliation/sync/", {"dry_run": False})
    assert resp.status_code == status.HTTP_200_OK
    assert resp.data["data"]["status"] in ["SUCCESS", "PARTIAL_WITH_CONFLICTS"]

    # 2. Auditor -> 403 Forbidden (Auditor cannot mutate)
    api_client.force_authenticate(user=auditor_user)
    resp_audit = api_client.post("/api/v1/crm/reconciliation/sync/", {"dry_run": False})
    assert resp_audit.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_api_reconciliation_history_endpoint(
    api_client, placement_officer_user, admin_user
):
    """Reconciliation history endpoint returns audit log of runs."""
    run_crm_database_reconciliation(user=admin_user, dry_run=False)

    api_client.force_authenticate(user=placement_officer_user)
    resp = api_client.get("/api/v1/crm/reconciliation/history/")
    assert resp.status_code == status.HTTP_200_OK
    assert len(resp.data["data"]) >= 1
    assert "total_records_checked" in resp.data["data"][0]


@pytest.mark.django_db
def test_api_company_360_and_timeline_endpoints(
    api_client, placement_officer_user, sample_company
):
    """Company 360 and timeline action endpoints return 200 OK."""
    api_client.force_authenticate(user=placement_officer_user)

    # 360 endpoint
    resp_360 = api_client.get(f"/api/v1/crm/companies/{sample_company.id}/360/")
    assert resp_360.status_code == status.HTTP_200_OK
    assert resp_360.data["data"]["company"]["name"] == sample_company.name

    # Timeline endpoint
    resp_timeline = api_client.get(f"/api/v1/crm/companies/{sample_company.id}/timeline/")
    assert resp_timeline.status_code == status.HTTP_200_OK
    assert isinstance(resp_timeline.data["data"], list)


@pytest.mark.django_db
def test_api_student_360_privacy_isolation(
    api_client, student_user_1, student_user_2, sample_student_profile, sample_student_profile_2, placement_officer_user
):
    """Students can only view their own 360 profile; accessing another student yields 403."""
    # 1. Student 1 views their own profile -> 200 OK
    api_client.force_authenticate(user=student_user_1)
    resp_own = api_client.get(f"/api/v1/crm/students/{sample_student_profile.id}/360/")
    assert resp_own.status_code == status.HTTP_200_OK
    assert resp_own.data["data"]["student"]["roll_number"] == sample_student_profile.roll_number

    # 2. Student 1 attempts to view Student 2 profile -> 403 Forbidden
    resp_other = api_client.get(f"/api/v1/crm/students/{sample_student_profile_2.id}/360/")
    assert resp_other.status_code == status.HTTP_403_FORBIDDEN

    # 3. Placement Officer views Student 2 profile -> 200 OK (Staff access)
    api_client.force_authenticate(user=placement_officer_user)
    resp_staff = api_client.get(f"/api/v1/crm/students/{sample_student_profile_2.id}/360/")
    assert resp_staff.status_code == status.HTTP_200_OK
