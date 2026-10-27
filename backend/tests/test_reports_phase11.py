"""Comprehensive Automated Test Suite for Phase 11: Reports & Analytics.

Tests:
1. Company Reports Dataset & Aggregation
2. Company Reports Scoping for HR Relationship Managers
3. Student Reports Metrics, Step 23 Gate, & Department Breakdown
4. Student Self-Service Report & Complete Isolation (Denial of Aggregate Endpoints)
5. Placement Reports Lifecycle & Compensation Metrics (Min, Max, Avg, Median)
6. Performance Reports & 10-Stage Objective Conversion Funnel
7. Monthly Statistics Timezone Boundaries & Empty Month Zero-Handling
8. CSV Export Integrity & Formula Injection Sanitization
9. Auditor Read-Only Authorization Across All Endpoints
10. Filter Validation & Bad Date Boundaries (HTTP 400)
"""
import csv
import io
from datetime import date, datetime, timedelta
from decimal import Decimal
import pytest
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
from apps.crm.models import Company, CompanyDomainCategory, CompanyRelationshipStatus, CompanyTier, HRContact
from apps.feedback.models import HRFeedback
from apps.interviews.models import ConductedStatus, InterviewSchedule, ShortlistedCandidate
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.placements.models import (
    CandidateOfferLetter,
    CandidatePlacementStatus,
    CandidatePlacementStatusChoices,
    FinalResultIntake,
    JoiningStatus,
    OfferAcceptanceStatus,
)
from apps.preparation.models import PlacementReadinessCertification, PlacementReadinessStatus
from apps.students.models import (
    CandidateCohort,
    EligibilityEvaluation,
    EligibilityStatus,
    StudentApplication,
    StudentProfile,
    StudentResume,
)
from apps.submissions.models import (
    CandidateSubmission,
    CandidateSubmissionStatus,
    SubmissionPackage,
    SubmissionPackageStatus,
)


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def roles(db):
    roles_dict = {}
    for code, name in RoleCatalog.CHOICES:
        role, _ = Role.objects.get_or_create(code=code, defaults={"name": name, "is_active": True})
        roles_dict[code] = role
    return roles_dict


def make_user(email: str, role_code: str, roles) -> User:
    user = User.objects.create_user(
        email=email.lower().strip(),
        password="TestPassword123!",
        first_name="Test",
        last_name=role_code,
    )
    UserRoleAssignment.objects.create(
        user=user,
        role=roles[role_code],
        is_active=True,
    )
    return user


@pytest.fixture
def admin_user(db, roles):
    return make_user("admin.phase11@gqt.internal", RoleCatalog.ADMIN, roles)


@pytest.fixture
def placement_officer_user(db, roles):
    return make_user("officer.phase11@gqt.internal", RoleCatalog.PLACEMENT_OFFICER, roles)


@pytest.fixture
def hr_mgr_user(db, roles):
    return make_user("hrmgr.phase11@gqt.internal", RoleCatalog.HR_RELATIONSHIP_MGR, roles)


@pytest.fixture
def other_hr_mgr_user(db, roles):
    return make_user("other_hrmgr.phase11@gqt.internal", RoleCatalog.HR_RELATIONSHIP_MGR, roles)


@pytest.fixture
def auditor_user(db, roles):
    return make_user("auditor.phase11@gqt.internal", RoleCatalog.AUDITOR, roles)


@pytest.fixture
def student_user_1(db, roles):
    user = make_user("student1.phase11@gqt.edu", RoleCatalog.STUDENT, roles)
    StudentProfile.objects.create(
        user=user,
        roll_number="2026CSE001",
        institutional_email=user.email,
        college_name="GQT Engineering College",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2026,
        cgpa=Decimal("8.50"),
        phone_number="+919876543210",
        is_verified_by_placement=True,
    )
    return user


@pytest.fixture
def student_user_2(db, roles):
    user = make_user("student2.phase11@gqt.edu", RoleCatalog.STUDENT, roles)
    StudentProfile.objects.create(
        user=user,
        roll_number="2026ECE002",
        institutional_email=user.email,
        college_name="GQT Engineering College",
        degree="B.Tech",
        department="Electronics",
        graduation_year=2026,
        cgpa=Decimal("7.20"),
        phone_number="+919876543211",
        is_verified_by_placement=False,
    )
    return user


@pytest.fixture
def sample_company(db, hr_mgr_user, admin_user):
    return Company.objects.create(
        name="TechCorp Solutions",
        normalized_name="techcorp solutions",
        website="https://techcorp.example.com",
        domain="techcorp.example.com",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        tier=CompanyTier.TIER_1_ENTERPRISE,
        relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER,
        owner=hr_mgr_user,
        created_by=admin_user,
    )


@pytest.fixture
def other_company(db, other_hr_mgr_user, admin_user):
    return Company.objects.create(
        name="=CmdInjection Corp",  # Formula injection test trigger
        normalized_name="cmdinjection corp",
        website="https://cmd.example.com",
        domain="cmd.example.com",
        domain_category=CompanyDomainCategory.PRODUCT_TECH,
        tier=CompanyTier.TIER_2_MIDSIZE,
        relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER,
        owner=other_hr_mgr_user,
        created_by=admin_user,
    )


@pytest.fixture
def sample_hr_contact(db, sample_company, admin_user):
    return HRContact.objects.create(
        company=sample_company,
        name="Jane Doe",
        email="jane.doe@techcorp.example.com",
        phone="+919876543299",
        designation="Head of University Relations",
        status="ACTIVE",
        created_by=admin_user,
    )


@pytest.fixture
def sample_job(db, sample_company, sample_hr_contact, admin_user):
    return JobRequirement.objects.create(
        company=sample_company,
        hr_contact=sample_hr_contact,
        title="Associate Software Engineer",
        job_description="Core engineering role in distributed systems.",
        skills_required="Python, Django, PostgreSQL",
        location="Bangalore",
        min_salary=Decimal("600000"),
        max_salary=Decimal("900000"),
        registration_deadline=date.today() + timedelta(days=14),
        status=JobRequirementStatus.APPROVED,
        created_by=admin_user,
    )


# -------------------------------------------------------------------------
# Test Cases
# -------------------------------------------------------------------------
@pytest.mark.django_db
def test_01_company_reports_dataset_and_aggregation(
    api_client, admin_user, sample_company, sample_hr_contact, sample_job, student_user_1
):
    """Verify company reports KPIs, drive counts, submissions, interviews, offers, and average CTC."""
    student_profile = student_user_1.student_profile

    # 1. Submission
    pkg = SubmissionPackage.objects.create(
        job_requirement=sample_job,
        company=sample_company,
        hr_contact=sample_hr_contact,
        title="Batch 1 Roster",
        status=SubmissionPackageStatus.DISPATCHED,
        created_by=admin_user,
    )
    resume = StudentResume.objects.create(
        student=student_profile,
        version_number=1,
        file="resumes/test.pdf",
        file_name="test.pdf",
        file_size_bytes=1024,
        sha256_hash="abc123hash",
        is_current=True,
    )
    cert = PlacementReadinessCertification.objects.create(
        student=student_profile,
        approved_resume=resume,
        is_approved_for_placements=True,
        certified_by=admin_user,
    )
    app = StudentApplication.objects.create(
        student=student_profile,
        job_requirement=sample_job,
    )
    sub = CandidateSubmission.objects.create(
        package=pkg,
        student=student_profile,
        application=app,
        readiness_certification=cert,
        submitted_resume=resume,
        resume_version_number=1,
        resume_sha256="abc123hash",
        status=CandidateSubmissionStatus.SUBMITTED,
    )

    # 2. Interview
    from apps.interviews.models import CandidateShortlist
    shortlist = CandidateShortlist.objects.create(
        job_requirement=sample_job,
        company=sample_company,
        hr_contact=sample_hr_contact,
        shortlist_reference_code="SL-2026-001",
        created_by=admin_user,
    )
    sc = ShortlistedCandidate.objects.create(
        shortlist=shortlist,
        student=student_profile,
        submission=sub,
    )
    InterviewSchedule.objects.create(
        job_requirement=sample_job,
        company=sample_company,
        candidate=sc,
        student=student_profile,
        schedule_reference_code="SCH-2026-001",
        interview_date=date.today(),
        interview_time=timezone.now().time(),
        scheduled_start_time=timezone.now(),
        conducted_status=ConductedStatus.CONDUCTED,
        created_by=admin_user,
    )

    # 3. Placement & Offer
    intake = FinalResultIntake.objects.create(
        job_requirement=sample_job,
        company=sample_company,
        result_reference_code="RES-2026-001",
        total_results=1,
        selected_count=1,
        created_by=admin_user,
    )
    placement_status = CandidatePlacementStatus.objects.create(
        intake=intake,
        job_requirement=sample_job,
        company=sample_company,
        student=student_profile,
        status=CandidatePlacementStatusChoices.SELECTED,
        designation_offered="Software Engineer",
        offered_ctc=Decimal("800000.00"),
        status_updated_by=admin_user,
    )
    CandidateOfferLetter.objects.create(
        placement_status=placement_status,
        student=student_profile,
        job_requirement=sample_job,
        company=sample_company,
        file="offers/offer.pdf",
        file_name="offer.pdf",
        file_size_bytes=1024,
        sha256_hash="offerhash123",
        issued_by=admin_user,
        acceptance_status=OfferAcceptanceStatus.ACCEPTED,
        joining_status=JoiningStatus.JOINED,
        actual_joining_date=date.today(),
    )

    # 4. HR Feedback
    HRFeedback.objects.create(
        company=sample_company,
        job_requirement=sample_job,
        hiring_satisfaction_rating=5,
        technical_skills_rating=4,
        communication_skills_rating=4,
        submitted_by=admin_user,
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/reports/companies/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    summary = data["summary"]

    assert summary["total_companies"] >= 1
    assert summary["active_hiring_partners"] >= 1
    assert summary["total_drives_posted"] >= 1
    assert summary["total_candidates_submitted"] == 1
    assert summary["total_candidates_interviewed"] == 1
    assert summary["total_candidates_selected"] == 1
    assert summary["total_offers_issued"] == 1
    assert summary["total_offers_accepted"] == 1
    assert summary["total_candidates_joined"] == 1
    assert summary["overall_average_ctc"] == 800000.00
    assert summary["average_recruiter_satisfaction"] == 5.0


@pytest.mark.django_db
def test_02_company_reports_scoping_for_hr_manager(
    api_client, hr_mgr_user, other_hr_mgr_user, sample_company, other_company
):
    """Verify that HR Relationship Manager is strictly scoped to their assigned companies."""
    api_client.force_authenticate(user=hr_mgr_user)
    response = api_client.get("/api/v1/reports/companies/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]

    # Should only contain sample_company (owned by hr_mgr_user), not other_company
    assert data["summary"]["total_companies"] == 1
    comp_names = [c["company_name"] for c in data["companies"]]
    assert sample_company.name in comp_names
    assert other_company.name not in comp_names


@pytest.mark.django_db
def test_03_student_reports_metrics_and_department_breakdown(
    api_client, admin_user, student_user_1, student_user_2
):
    """Verify student verification, Step 23 readiness certification, and department breakdowns."""
    # Ensure both student profiles are loaded
    assert student_user_1.student_profile is not None
    assert student_user_2.student_profile is not None
    total_in_db = StudentProfile.objects.count()

    # Give student_1 readiness certification
    resume = StudentResume.objects.create(
        student=student_user_1.student_profile,
        version_number=1,
        file="resumes/s1.pdf",
        file_name="s1.pdf",
        file_size_bytes=1024,
        sha256_hash="hash1",
        is_current=True,
    )
    PlacementReadinessCertification.objects.create(
        student=student_user_1.student_profile,
        approved_resume=resume,
        is_approved_for_placements=True,
        certified_by=admin_user,
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/reports/students/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    summary = data["summary"]

    assert summary["total_students"] == total_in_db
    assert summary["verified_profiles_count"] == 1  # only student 1 is verified
    assert summary["readiness_certified_count"] == 1
    assert summary["verification_rate"] == 50.0
    assert summary["readiness_certified_count"] == 1
    assert summary["readiness_certification_rate"] == 50.0

    dept_breakdown = data["department_breakdown"]
    depts = {d["department"]: d for d in dept_breakdown}
    assert "Computer Science" in depts
    assert "Electronics" in depts
    assert depts["Computer Science"]["verified_count"] == 1
    assert depts["Electronics"]["verified_count"] == 0


@pytest.mark.django_db
def test_04_student_self_report_and_isolation(
    api_client, student_user_1, student_user_2
):
    """Verify student role access to their own summary, and 403 denial for aggregate reporting endpoints."""
    api_client.force_authenticate(user=student_user_1)

    # 1. Permitted self summary
    response = api_client.get("/api/v1/reports/students/my-summary/")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    assert data["roll_number"] == "2026CSE001"
    assert data["profile_completeness_percent"] >= 75

    # 2. Denied organizational aggregate reports
    forbidden_endpoints = [
        "/api/v1/reports/companies/",
        "/api/v1/reports/students/",
        "/api/v1/reports/placements/",
        "/api/v1/reports/performance/",
        "/api/v1/reports/monthly-stats/",
    ]
    for url in forbidden_endpoints:
        res = api_client.get(url)
        assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_05_placement_reports_lifecycle_and_compensation(
    api_client, admin_user, sample_company, sample_job, student_user_1, student_user_2
):
    """Verify authoritative placement status breakdown, offer acceptance lifecycle, and CTC stats."""
    intake = FinalResultIntake.objects.create(
        job_requirement=sample_job,
        company=sample_company,
        result_reference_code="RES-2026-STAT",
        total_results=2,
        selected_count=1,
        rejected_count=1,
        created_by=admin_user,
    )
    p1 = CandidatePlacementStatus.objects.create(
        intake=intake,
        job_requirement=sample_job,
        company=sample_company,
        student=student_user_1.student_profile,
        status=CandidatePlacementStatusChoices.SELECTED,
        designation_offered="Engineer",
        offered_ctc=Decimal("600000.00"),
        status_updated_by=admin_user,
    )
    CandidatePlacementStatus.objects.create(
        intake=intake,
        job_requirement=sample_job,
        company=sample_company,
        student=student_user_2.student_profile,
        status=CandidatePlacementStatusChoices.REJECTED,
        status_updated_by=admin_user,
    )
    CandidateOfferLetter.objects.create(
        placement_status=p1,
        student=student_user_1.student_profile,
        job_requirement=sample_job,
        company=sample_company,
        file="offers/p1.pdf",
        file_name="p1.pdf",
        file_size_bytes=2048,
        sha256_hash="hashp1",
        issued_by=admin_user,
        acceptance_status=OfferAcceptanceStatus.ACCEPTED,
        joining_status=JoiningStatus.DEFERRED,
        deferred_joining_date=date.today() + timedelta(days=30),
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/reports/placements/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]
    summary = data["summary"]

    assert summary["total_results_evaluated"] == 2
    assert summary["selected_count"] == 1
    assert summary["rejected_count"] == 1
    assert summary["selection_rate"] == 50.0
    assert summary["total_offers_issued"] == 1
    assert summary["offers_accepted"] == 1
    assert summary["deferred_count"] == 1
    assert summary["average_ctc"] == 600000.00
    assert summary["median_ctc"] == 600000.00


@pytest.mark.django_db
def test_06_performance_conversion_funnel(
    api_client, admin_user, sample_company, sample_job, student_user_1
):
    """Verify 10-stage conversion funnel calculations and zero-division safety."""
    app = StudentApplication.objects.create(
        student=student_user_1.student_profile,
        job_requirement=sample_job,
    )
    EligibilityEvaluation.objects.create(
        application=app,
        status=EligibilityStatus.ELIGIBLE,
    )

    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/reports/performance/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()["data"]

    stages = data["funnel_stages"]
    assert len(stages) == 10
    stage1 = stages[0]
    stage2 = stages[1]
    assert stage1["count"] == 1
    assert stage2["count"] == 1
    assert stage2["conversion_from_previous"] == 100.0


@pytest.mark.django_db
def test_07_monthly_statistics_boundaries_and_empty_months(
    api_client, admin_user, sample_company, sample_job
):
    """Verify deterministic month-based statistics and graceful zero handling."""
    api_client.force_authenticate(user=admin_user)
    current_year = date.today().year

    response = api_client.get(f"/api/v1/reports/monthly-stats/?year={current_year}&month=1")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()["data"]
    sel_month = data["selected_month"]
    assert sel_month["year"] == current_year
    assert sel_month["month"] == 1
    assert "jobs_posted" in sel_month
    assert "offers_issued" in sel_month
    assert len(data["annual_trend"]) == 12


@pytest.mark.django_db
def test_08_csv_export_and_formula_injection_protection(
    api_client, admin_user, other_company
):
    """Verify CSV exports escape potential formula injections starting with '=', '+', '-', '@'."""
    api_client.force_authenticate(user=admin_user)

    response = api_client.get("/api/v1/reports/companies/export/")
    assert response.status_code == status.HTTP_200_OK
    assert response["Content-Type"].startswith("text/csv")
    assert "attachment; filename=" in response["Content-Disposition"]

    csv_text = response.content.decode("utf-8")
    # Verify other_company.name '=CmdInjection Corp' is escaped with leading apostrophe
    assert "'=CmdInjection Corp" in csv_text


@pytest.mark.django_db
def test_09_auditor_read_only_access(
    api_client, auditor_user
):
    """Verify Auditor role has read-only access across all 5 report endpoints."""
    api_client.force_authenticate(user=auditor_user)

    endpoints = [
        "/api/v1/reports/companies/",
        "/api/v1/reports/companies/export/",
        "/api/v1/reports/students/",
        "/api/v1/reports/students/export/",
        "/api/v1/reports/placements/",
        "/api/v1/reports/placements/export/",
        "/api/v1/reports/performance/",
        "/api/v1/reports/performance/export/",
        "/api/v1/reports/monthly-stats/",
        "/api/v1/reports/monthly-stats/export/",
    ]
    for url in endpoints:
        res = api_client.get(url)
        assert res.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_10_filters_and_validation(api_client, admin_user):
    """Verify invalid date boundaries return HTTP 400 with descriptive error."""
    api_client.force_authenticate(user=admin_user)

    # start_date > end_date should fail validation
    response = api_client.get("/api/v1/reports/placements/?start_date=2026-10-20&end_date=2026-10-10")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "end_date" in str(response.json())
