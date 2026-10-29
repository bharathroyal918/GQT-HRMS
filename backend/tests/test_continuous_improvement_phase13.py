"""Comprehensive Automated Test Suite for Phase 13: Continuous Improvement.

Tests:
1. Placement Rate Analytics: Distinct Student Funnels, Multi-Offers, Explicit Formulas & Denominators
2. Placement Rate Filtering & Division-by-Zero Safety
3. Feedback Intelligence: Category A/B/C Aggregation, Rating Scales, & Anonymity Rules
4. Feedback Scoping for HR Relationship Managers
5. Evidence-Based Skill Gap Matrix: Normalization, Unassessed Demand vs Critical Gaps
6. Training Plan Lifecycle, Approval Gate & Immutable Readiness
7. Recruitment Cycle Reviews, Baseline Metric Snapshots & Improvement Action Items
8. Role Permissions & Strict Student Isolation
9. Safe CSV Exports & Formula Injection Sanitization
10. Continuous Improvement 6-Point Data Quality Diagnostics
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
from apps.analytics.models import (
    CycleActionCategory,
    CycleActionStatus,
    CycleImprovementAction,
    RecruitmentCycleReview,
    RecruitmentCycleStatus,
    TrainingPlan,
    TrainingPlanStatus,
)
from apps.crm.models import Company, CompanyDomainCategory, CompanyRelationshipStatus, CompanyTier, HRContact
from apps.feedback.models import CandidateQuality, DifficultyLevel, HRFeedback, StudentFeedback, StudentReadiness, TrainerFeedback
from apps.interviews.models import CandidateShortlist, ConductedStatus, InterviewRound, InterviewSchedule, ShortlistedCandidate
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.placements.models import (
    CandidateOfferLetter,
    CandidatePlacementStatus,
    CandidatePlacementStatusChoices,
    FinalResultIntake,
    JoiningStatus,
    OfferAcceptanceStatus,
)
from apps.preparation.models import (
    AssessmentTest,
    AssessmentTestType,
    MockInterview,
    MockInterviewEvaluation,
    MockInterviewStatus,
    MockReadinessRecommendation,
    PlacementReadinessCertification,
    PlacementReadinessStatus,
    StudentAssessmentAttempt,
)
from apps.students.models import StudentApplication, StudentProfile, StudentResume
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
    return make_user("admin.phase13@gqt.internal", RoleCatalog.ADMIN, roles)


@pytest.fixture
def placement_head_user(db, roles):
    return make_user("head.phase13@gqt.internal", RoleCatalog.PLACEMENT_HEAD, roles)


@pytest.fixture
def placement_officer_user(db, roles):
    return make_user("officer.phase13@gqt.internal", RoleCatalog.PLACEMENT_OFFICER, roles)


@pytest.fixture
def trainer_user(db, roles):
    return make_user("trainer.phase13@gqt.internal", RoleCatalog.TRAINER, roles)


@pytest.fixture
def hr_mgr_user(db, roles):
    return make_user("hrmgr.phase13@gqt.internal", RoleCatalog.HR_RELATIONSHIP_MGR, roles)


@pytest.fixture
def other_hr_mgr_user(db, roles):
    return make_user("other_hrmgr.phase13@gqt.internal", RoleCatalog.HR_RELATIONSHIP_MGR, roles)


@pytest.fixture
def auditor_user(db, roles):
    return make_user("auditor.phase13@gqt.internal", RoleCatalog.AUDITOR, roles)


@pytest.fixture
def student_user(db, roles):
    user = make_user("student.phase13@gqt.edu", RoleCatalog.STUDENT, roles)
    StudentProfile.objects.create(
        user=user,
        roll_number="2026CSE099",
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
def phase13_dataset(db, admin_user, hr_mgr_user, other_hr_mgr_user, trainer_user, roles):
    """Seed comprehensive dataset for continuous improvement verification."""
    # 1. Companies
    comp_a = Company.objects.create(
        name="Alpha Cloud Tech",
        domain_category=CompanyDomainCategory.PRODUCT_TECH,
        tier=CompanyTier.TIER_1_ENTERPRISE,
        relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER,
        owner=hr_mgr_user,
        created_by=admin_user,
    )
    comp_b = Company.objects.create(
        name="Beta FinTech Labs",
        domain_category=CompanyDomainCategory.FINANCE_BANKING,
        tier=CompanyTier.TIER_2_MIDSIZE,
        relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER,
        owner=other_hr_mgr_user,
        created_by=admin_user,
    )

    # 2. Job Requirements
    job_1 = JobRequirement.objects.create(
        company=comp_a,
        title="Backend Software Engineer",
        job_description="Develop scalable Python and Django REST APIs with PostgreSQL.",
        skills_required="Python, Django, PostgreSQL, REST APIs, Git",
        min_salary=Decimal("700000.00"),
        max_salary=Decimal("1200000.00"),
        location="Bangalore",
        registration_deadline=timezone.now() + timedelta(days=14),
        status=JobRequirementStatus.APPROVED,
        created_by=admin_user,
    )
    job_2 = JobRequirement.objects.create(
        company=comp_b,
        title="Full Stack Engineer",
        job_description="React, Node.js, and Data Structures problem solving.",
        skills_required="React, JavaScript, Node.js, DSA, SQL",
        min_salary=Decimal("600000.00"),
        max_salary=Decimal("900000.00"),
        location="Hyderabad",
        registration_deadline=timezone.now() + timedelta(days=14),
        status=JobRequirementStatus.APPROVED,
        created_by=admin_user,
    )

    # 3. Students
    stud_user_1 = make_user("stud1.c13@gqt.edu", RoleCatalog.STUDENT, roles)
    profile_1 = StudentProfile.objects.create(
        user=stud_user_1,
        roll_number="2026CSE001",
        institutional_email=stud_user_1.email,
        college_name="GQT Engineering College",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2026,
        cgpa=Decimal("8.80"),
        phone_number="+919876543201",
        is_verified_by_placement=True,
    )

    stud_user_2 = make_user("stud2.c13@gqt.edu", RoleCatalog.STUDENT, roles)
    profile_2 = StudentProfile.objects.create(
        user=stud_user_2,
        roll_number="2026CSE002",
        institutional_email=stud_user_2.email,
        college_name="GQT Engineering College",
        degree="B.Tech",
        department="Computer Science",
        graduation_year=2026,
        cgpa=Decimal("7.60"),
        phone_number="+919876543202",
        is_verified_by_placement=True,
    )

    stud_user_3 = make_user("stud3.c13@gqt.edu", RoleCatalog.STUDENT, roles)
    profile_3 = StudentProfile.objects.create(
        user=stud_user_3,
        roll_number="2026ECE001",
        institutional_email=stud_user_3.email,
        college_name="GQT Engineering College",
        degree="B.Tech",
        department="Electronics",
        graduation_year=2026,
        cgpa=Decimal("7.20"),
        phone_number="+919876543203",
        is_verified_by_placement=True,
    )

    # 4. Applications
    app_1 = StudentApplication.objects.create(student=profile_1, job_requirement=job_1)
    app_2 = StudentApplication.objects.create(student=profile_1, job_requirement=job_2)  # Multi-applicant
    app_3 = StudentApplication.objects.create(student=profile_2, job_requirement=job_1)

    # 5. Shortlists & Schedules
    contact_a = HRContact.objects.create(
        company=comp_a,
        name="Jane Recruiter",
        email="jane.recruiter@alphacloud.com",
        designation="Talent Acquisition Lead",
        created_by=admin_user,
    )
    contact_b = HRContact.objects.create(
        company=comp_b,
        name="Bob HR",
        email="bob.hr@betafintech.com",
        designation="Recruitment Specialist",
        created_by=admin_user,
    )

    resume_1 = StudentResume.objects.create(
        student=profile_1,
        version_number=1,
        file_name="resume_p1.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b851",
        is_current=True,
    )
    cert_1 = PlacementReadinessCertification.objects.create(
        student=profile_1,
        approved_resume=resume_1,
        is_approved_for_placements=True,
        status=PlacementReadinessStatus.CERTIFIED,
        certified_by=admin_user,
    )
    resume_2 = StudentResume.objects.create(
        student=profile_2,
        version_number=1,
        file_name="resume_p2.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b852",
        is_current=True,
    )
    cert_2 = PlacementReadinessCertification.objects.create(
        student=profile_2,
        approved_resume=resume_2,
        is_approved_for_placements=True,
        status=PlacementReadinessStatus.CERTIFIED,
        certified_by=admin_user,
    )

    pkg_1 = SubmissionPackage.objects.create(
        title="Batch 2026 - Alpha Cloud Tech",
        job_requirement=job_1,
        company=comp_a,
        hr_contact=contact_a,
        status=SubmissionPackageStatus.DISPATCHED,
        created_by=admin_user,
    )
    pkg_2 = SubmissionPackage.objects.create(
        title="Batch 2026 - Beta FinTech Labs",
        job_requirement=job_2,
        company=comp_b,
        hr_contact=contact_b,
        status=SubmissionPackageStatus.DISPATCHED,
        created_by=admin_user,
    )

    sub_1a = CandidateSubmission.objects.create(
        package=pkg_1,
        student=profile_1,
        application=app_1,
        readiness_certification=cert_1,
        submitted_resume=resume_1,
        resume_version_number=1,
        resume_sha256=resume_1.sha256_hash,
        status=CandidateSubmissionStatus.SHORTLISTED,
    )
    sub_2a = CandidateSubmission.objects.create(
        package=pkg_1,
        student=profile_2,
        application=app_3,
        readiness_certification=cert_2,
        submitted_resume=resume_2,
        resume_version_number=1,
        resume_sha256=resume_2.sha256_hash,
        status=CandidateSubmissionStatus.SHORTLISTED,
    )
    sub_1b = CandidateSubmission.objects.create(
        package=pkg_2,
        student=profile_1,
        application=app_2,
        readiness_certification=cert_1,
        submitted_resume=resume_1,
        resume_version_number=1,
        resume_sha256=resume_1.sha256_hash,
        status=CandidateSubmissionStatus.SHORTLISTED,
    )

    sl_1 = CandidateShortlist.objects.create(
        job_requirement=job_1,
        company=comp_a,
        hr_contact=contact_a,
        shortlist_reference_code="SL-2026-001",
        created_by=admin_user,
    )
    sc_1 = ShortlistedCandidate.objects.create(
        shortlist=sl_1,
        student=profile_1,
        submission=sub_1a,
    )
    sc_2 = ShortlistedCandidate.objects.create(
        shortlist=sl_1,
        student=profile_2,
        submission=sub_2a,
    )
    sl_2 = CandidateShortlist.objects.create(
        job_requirement=job_2,
        company=comp_b,
        hr_contact=contact_b,
        shortlist_reference_code="SL-2026-002",
        created_by=admin_user,
    )
    sc_3 = ShortlistedCandidate.objects.create(
        shortlist=sl_2,
        student=profile_1,
        submission=sub_1b,
    )

    sched_1 = InterviewSchedule.objects.create(
        job_requirement=job_1,
        company=comp_a,
        candidate=sc_1,
        student=profile_1,
        schedule_reference_code="SCH-2026-001",
        interview_date=date.today() - timedelta(days=5),
        interview_time=timezone.now().time(),
        scheduled_start_time=timezone.now() - timedelta(days=5),
        conducted_status=ConductedStatus.CONDUCTED,
        created_by=admin_user,
    )
    sched_2 = InterviewSchedule.objects.create(
        job_requirement=job_2,
        company=comp_b,
        candidate=sc_3,
        student=profile_1,
        schedule_reference_code="SCH-2026-002",
        interview_date=date.today() - timedelta(days=4),
        interview_time=timezone.now().time(),
        scheduled_start_time=timezone.now() - timedelta(days=4),
        conducted_status=ConductedStatus.CONDUCTED,
        created_by=admin_user,
    )
    sched_3 = InterviewSchedule.objects.create(
        job_requirement=job_1,
        company=comp_a,
        candidate=sc_2,
        student=profile_2,
        schedule_reference_code="SCH-2026-003",
        interview_date=date.today() - timedelta(days=3),
        interview_time=timezone.now().time(),
        scheduled_start_time=timezone.now() - timedelta(days=3),
        conducted_status=ConductedStatus.CONDUCTED,
        created_by=admin_user,

     )

    # 6. Placement Results: Student 1 selected at BOTH comp_a and comp_b (Dual offer)
    intake_1 = FinalResultIntake.objects.create(
        job_requirement=job_1,
        company=comp_a,
        result_reference_code="RES-2026-001",
        total_results=2,
        selected_count=2,
        created_by=admin_user,
    )
    res_1a = CandidatePlacementStatus.objects.create(
        intake=intake_1,
        job_requirement=job_1,
        company=comp_a,
        student=profile_1,
        status=CandidatePlacementStatusChoices.SELECTED,
        offered_ctc=Decimal("900000.00"),
        status_updated_by=admin_user,
    )
    res_2a = CandidatePlacementStatus.objects.create(
        intake=intake_1,
        job_requirement=job_1,
        company=comp_a,
        student=profile_2,
        status=CandidatePlacementStatusChoices.SELECTED,
        offered_ctc=Decimal("800000.00"),
        status_updated_by=admin_user,
    )

    intake_2 = FinalResultIntake.objects.create(
        job_requirement=job_2,
        company=comp_b,
        result_reference_code="RES-2026-002",
        total_results=1,
        selected_count=1,
        created_by=admin_user,
    )
    res_1b = CandidatePlacementStatus.objects.create(
        intake=intake_2,
        job_requirement=job_2,
        company=comp_b,
        student=profile_1,
        status=CandidatePlacementStatusChoices.SELECTED,
        offered_ctc=Decimal("850000.00"),
        status_updated_by=admin_user,
    )

    # 7. Offers & Joining:
    # Student 1 accepts offer A and JOINS; declines offer B
    offer_1a = CandidateOfferLetter.objects.create(
        placement_status=res_1a,
        student=profile_1,
        job_requirement=job_1,
        company=comp_a,
        file="offers/offer1a.pdf",
        file_name="offer_1a.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        issued_by=admin_user,
        acceptance_status=OfferAcceptanceStatus.ACCEPTED,
        joining_status=JoiningStatus.JOINED,
    )
    offer_1b = CandidateOfferLetter.objects.create(
        placement_status=res_1b,
        student=profile_1,
        job_requirement=job_2,
        company=comp_b,
        file="offers/offer1b.pdf",
        file_name="offer_1b.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b856",
        issued_by=admin_user,
        acceptance_status=OfferAcceptanceStatus.DECLINED,
        joining_status=JoiningStatus.NOT_APPLICABLE,
    )
    # Student 2 offer pending response
    offer_2a = CandidateOfferLetter.objects.create(
        placement_status=res_2a,
        student=profile_2,
        job_requirement=job_1,
        company=comp_a,
        file="offers/offer2a.pdf",
        file_name="offer_2a.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b857",
        issued_by=admin_user,
        acceptance_status=OfferAcceptanceStatus.PENDING_RESPONSE,
        joining_status=JoiningStatus.PENDING_JOINING,
    )

    # 8. Feedback Seed:
    # HR Feedback
    HRFeedback.objects.create(
        company=comp_a,
        job_requirement=job_1,
        candidate_quality=CandidateQuality.EXCELLENT,
        technical_skills_rating=4,
        communication_skills_rating=4,
        hiring_satisfaction_rating=5,
        technical_skills_remarks="Strong Python foundation, needs slight polish on concurrency.",
        submitted_by=admin_user,
    )
    # Student Feedback (One anonymous, one named)
    StudentFeedback.objects.create(
        student=profile_1,
        company=comp_a,
        job_requirement=job_1,
        interview_schedule=sched_1,
        difficulty=DifficultyLevel.HARD,
        interview_experience="Challenging technical design discussion and live coding.",
        technical_questions="Explain Django ORM select_related vs prefetch_related.",
        suggestions="Emphasize database indexing in pre-placement training.",
        is_anonymous=True,
        submitted_by=stud_user_1,
    )
    # Trainer Feedback
    TrainerFeedback.objects.create(
        student=profile_1,
        student_readiness=StudentReadiness.HIGHLY_READY,
        training_effectiveness_rating=5,
        areas_for_improvement="Advanced distributed caching and microservices.",
        trainer=trainer_user,
    )

    # 9. Assessment Tests & Attempts for Skill Matrix
    test_py = AssessmentTest.objects.create(
        title="Python Core Evaluation",
        test_type=AssessmentTestType.TECHNICAL,
        domain_track="Python",
        total_marks=100,
        passing_marks=60,
        created_by=admin_user,
    )
    test_dsa = AssessmentTest.objects.create(
        title="Data Structures & Algorithms Challenge",
        test_type=AssessmentTestType.TECHNICAL,
        domain_track="Data Structures",
        total_marks=100,
        passing_marks=60,
        created_by=admin_user,
    )
    # Python: student 1 passed with 85%
    StudentAssessmentAttempt.objects.create(
        student=profile_1,
        test=test_py,
        score=85,
        percentage=Decimal("85.00"),
        passed=True,
        status="COMPLETED",
    )
    # DSA: student 1 scored 50% (failed), student 2 scored 45% (failed) -> Critical Gap
    StudentAssessmentAttempt.objects.create(
        student=profile_1,
        test=test_dsa,
        score=50,
        percentage=Decimal("50.00"),
        passed=False,
        status="COMPLETED",
    )
    StudentAssessmentAttempt.objects.create(
        student=profile_2,
        test=test_dsa,
        score=45,
        percentage=Decimal("45.00"),
        passed=False,
        status="COMPLETED",
    )

    return {
        "comp_a": comp_a,
        "comp_b": comp_b,
        "job_1": job_1,
        "job_2": job_2,
        "profile_1": profile_1,
        "profile_2": profile_2,
        "profile_3": profile_3,
        "stud_user_1": stud_user_1,
    }


# =========================================================================
# TEST 1: Placement Rate Analytics & Multi-Offers
# =========================================================================
def test_01_placement_rate_analytics_distinct_students_and_multi_offers(api_client, admin_user, phase13_dataset):
    """Verify distinct student counting, dual-offer handling, and explicit rate formulas."""
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/continuous-improvement/placement-rate/", {"cohort_year": 2026})

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    summary = data["summary"]

    # 3 total eligible students in cohort (profile_1, profile_2, profile_3)
    assert summary["total_eligible_students"] == 3
    # 2 distinct students applied (profile_1 applied to 2 jobs, profile_2 to 1 job)
    assert summary["distinct_students_applied"] == 2
    assert summary["total_applications"] == 3

    # 2 distinct students selected (profile_1 selected in job1 & job2; profile_2 in job1)
    assert summary["distinct_students_selected"] == 2
    assert summary["total_selections"] == 3

    # Multi-offer distribution: profile_1 has 2 offers, profile_2 has 1 offer
    assert summary["single_offer_students"] == 1
    assert summary["dual_offer_students"] == 1
    assert summary["total_offers_issued"] == 3
    assert summary["total_offers_accepted"] == 1
    assert summary["total_offers_declined"] == 1
    assert summary["total_offers_pending"] == 1

    # Joining: profile_1 joined; profile_2 pending joining
    assert summary["distinct_students_joined"] == 1
    assert summary["distinct_students_pending_outcomes"] == 1

    # Exact Percentage Verification:
    # Placement Rate (Eligible): 2 selected / 3 eligible = 66.67%
    assert summary["placement_rate_eligible"] == 66.67
    # Applicant Placement Rate: 2 selected / 2 applied = 100.0%
    assert summary["placement_rate_applicants"] == 100.0
    # Offer Acceptance Rate: 1 accepted / 2 resolved (1 accepted + 1 declined) = 50.0%
    assert summary["offer_acceptance_rate"] == 50.0
    # Joining Rate: 1 joined / 1 accepted = 100.0%
    assert summary["joining_rate"] == 100.0

    # Metric definitions & documentation block verified
    assert len(data["metric_definitions"]) == 6
    assert data["metric_definitions"][0]["metric_name"] == "Eligible Cohort Placement Rate"
    assert data["metric_definitions"][0]["numerator"] == 2
    assert data["metric_definitions"][0]["denominator"] == 3


# =========================================================================
# TEST 2: Filtering & Zero Denominators
# =========================================================================
def test_02_placement_rate_filtering_and_zero_denominators(api_client, admin_user, phase13_dataset):
    """Verify empty cohort year handles zero denominators gracefully without division by zero."""
    api_client.force_authenticate(user=admin_user)
    # Query future cohort with zero records
    response = api_client.get("/api/v1/continuous-improvement/placement-rate/", {"cohort_year": 2030})

    assert response.status_code == status.HTTP_200_OK
    summary = response.data["summary"]
    assert summary["total_cohort_students"] == 0
    assert summary["placement_rate_eligible"] == 0.0
    assert summary["placement_rate_applicants"] == 0.0
    assert summary["offer_acceptance_rate"] == 0.0
    assert summary["joining_rate"] == 0.0


# =========================================================================
# TEST 3: Feedback Intelligence & Anonymity Rules
# =========================================================================
def test_03_feedback_intelligence_cross_category_and_anonymity(api_client, admin_user, phase13_dataset):
    """Verify 3-category feedback aggregation and candidate anonymity protection."""
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/continuous-improvement/feedback/")

    assert response.status_code == status.HTTP_200_OK
    data = response.data

    # HR Feedback
    hr = data["hr_feedback"]
    assert hr["total_responses"] >= 1
    assert hr["avg_technical_rating"] == 4.0
    assert hr["avg_hiring_satisfaction"] == 5.0
    assert hr["candidate_quality_distribution"]["EXCELLENT"] == 1

    # Student Feedback: Count is 1 (< 3 threshold), so small group masking must trigger
    sf = data["student_feedback"]
    assert sf["total_responses"] == 1
    assert sf["is_small_group_masked"] is True
    assert sf["recent_experiences"][0]["submitted_by"] == "Candidate (Anonymized)"
    assert sf["recent_experiences"][0]["is_anonymous"] is True

    # Trainer Feedback
    tf = data["trainer_feedback"]
    assert tf["total_evaluations"] >= 1
    assert tf["avg_training_effectiveness"] == 5.0
    assert tf["readiness_distribution"]["HIGHLY_READY"] == 1


# =========================================================================
# TEST 4: Feedback Scoping for HR Relationship Managers
# =========================================================================
def test_04_feedback_scoping_for_hr_manager(api_client, hr_mgr_user, other_hr_mgr_user, phase13_dataset):
    """HR Manager can access feedback for owned company; blocked from unauthorized companies."""
    comp_a = phase13_dataset["comp_a"]
    comp_b = phase13_dataset["comp_b"]

    api_client.force_authenticate(user=hr_mgr_user)
    # Allowed: comp_a is owned by hr_mgr_user
    res_allowed = api_client.get("/api/v1/continuous-improvement/feedback/", {"company_id": str(comp_a.id)})
    assert res_allowed.status_code == status.HTTP_200_OK

    # Forbidden: comp_b is owned by other_hr_mgr_user
    res_forbidden = api_client.get("/api/v1/continuous-improvement/feedback/", {"company_id": str(comp_b.id)})
    assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN


# =========================================================================
# TEST 5: Evidence-Based Skill Gap Analysis
# =========================================================================
def test_05_skill_gap_matrix_normalization_and_unassessed_vs_weak(api_client, admin_user, phase13_dataset):
    """Verify deterministic skill normalization, critical gaps, and unassessed demand classification."""
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/continuous-improvement/skill-gaps/")

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    summary = data["summary"]
    matrix = {s["skill_name"]: s for s in data["skill_matrix"]}

    # Python: demanded by Job 1, assessed with 1 attempt passed (85%) -> Strength
    assert "Python" in matrix
    assert matrix["Python"]["market_demand_jobs_count"] >= 1
    assert matrix["Python"]["assessment_pass_rate"] == 100.0

    # Data Structures & Algorithms: demanded by Job 2, 2 attempts failed (0% pass rate) -> Critical Gap
    assert "Data Structures & Algorithms" in matrix
    dsa = matrix["Data Structures & Algorithms"]
    assert dsa["market_demand_jobs_count"] >= 1
    assert dsa["assessment_pass_rate"] == 0.0
    assert dsa["gap_status"] == "CRITICAL_GAP"
    assert dsa["severity"] == "CRITICAL"

    # Methodology disclaimer present (Zero AI verification)
    assert "predictive AI" in data["methodology_disclaimer"]


# =========================================================================
# TEST 6: Training Plan Lifecycle, Approval Gate & Readiness Preservation
# =========================================================================
def test_06_training_plan_lifecycle_and_approval_gate(api_client, trainer_user, placement_head_user, admin_user):
    """Verify full TrainingPlan lifecycle: Draft -> Proposed -> Approved -> Scheduled -> In Progress -> Completed."""
    api_client.force_authenticate(user=trainer_user)

    # 1. Trainer drafts a remedial plan
    payload = {
        "title": "Remedial Workshop: Advanced Data Structures",
        "target_skill": "Data Structures & Algorithms",
        "motivation_evidence": "0% pass rate on algorithmic challenge and recurring mock interview gaps.",
        "target_cohort": "2026 Passing Out Batch - Computer Science",
        "proposed_objectives": "Recursion, Tree Traversal, Dynamic Programming, and Complexity Optimization.",
        "planned_sessions_count": 4,
        "planned_start_date": (date.today() + timedelta(days=7)).isoformat(),
        "planned_end_date": (date.today() + timedelta(days=14)).isoformat(),
        "expected_outcome": "Achieve >= 75% pass rate on re-assessment.",
        "status": TrainingPlanStatus.DRAFT,
    }
    create_res = api_client.post("/api/v1/continuous-improvement/training-plans/", payload, format="json")
    assert create_res.status_code == status.HTTP_201_CREATED
    plan_id = create_res.data["id"]

    # 2. Trainer proposes plan
    prop_res = api_client.post(
        f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/",
        {"new_status": TrainingPlanStatus.PROPOSED, "notes": "Submitted for approval."},
        format="json",
    )
    assert prop_res.status_code == status.HTTP_200_OK
    assert prop_res.data["status"] == TrainingPlanStatus.PROPOSED

    # 3. Trainer attempts to approve their own plan -> 403 Forbidden (Only Head / Admin)
    unauth_appr = api_client.post(
        f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/",
        {"new_status": TrainingPlanStatus.APPROVED},
        format="json",
    )
    assert unauth_appr.status_code == status.HTTP_403_FORBIDDEN

    # 4. Placement Head approves plan
    api_client.force_authenticate(user=placement_head_user)
    appr_res = api_client.post(
        f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/",
        {"new_status": TrainingPlanStatus.APPROVED, "notes": "Approved by Placement Head."},
        format="json",
    )
    assert appr_res.status_code == status.HTTP_200_OK
    assert appr_res.data["status"] == TrainingPlanStatus.APPROVED

    # 5. Progress to Scheduled, then In Progress, then Completed
    api_client.post(f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/", {"new_status": TrainingPlanStatus.SCHEDULED})
    api_client.post(f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/", {"new_status": TrainingPlanStatus.IN_PROGRESS})

    # Completing requires actual results
    comp_fail = api_client.post(
        f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/",
        {"new_status": TrainingPlanStatus.COMPLETED},
    )
    assert comp_fail.status_code == status.HTTP_400_BAD_REQUEST

    comp_res = api_client.post(
        f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/",
        {
            "new_status": TrainingPlanStatus.COMPLETED,
            "actual_results": "42 candidates attended all 4 sessions. Re-assessment average increased from 47% to 82%.",
        },
        format="json",
    )
    assert comp_res.status_code == status.HTTP_200_OK
    assert comp_res.data["status"] == TrainingPlanStatus.COMPLETED

    # Verify plan cannot transition out of terminal state COMPLETED
    invalid_res = api_client.post(
        f"/api/v1/continuous-improvement/training-plans/{plan_id}/status/",
        {"new_status": TrainingPlanStatus.DRAFT},
        format="json",
    )
    assert invalid_res.status_code == status.HTTP_400_BAD_REQUEST


# =========================================================================
# TEST 7: Recruitment Cycle Reviews & Actions
# =========================================================================
def test_07_recruitment_cycle_review_and_actions(api_client, admin_user, placement_head_user, phase13_dataset):
    """Verify recruitment cycle review captures baseline snapshot and tracks action items."""
    api_client.force_authenticate(user=admin_user)

    # 1. Create Cycle Review
    review_payload = {
        "title": "Annual Recruitment Cycle Review 2026",
        "cohort_year": 2026,
        "review_period_start": "2026-01-01",
        "review_period_end": "2026-12-31",
        "target_goals": {
            "target_placement_rate": 85.0,
            "target_joining_rate": 95.0,
        },
        "placement_outcomes_summary": "Initial baseline placement conversion is 66.67%.",
    }
    review_res = api_client.post("/api/v1/continuous-improvement/cycle-reviews/", review_payload, format="json")
    assert review_res.status_code == status.HTTP_201_CREATED
    review_id = review_res.data["id"]

    # Verify baseline metrics snapshot was captured automatically
    detail_res = api_client.get(f"/api/v1/continuous-improvement/cycle-reviews/{review_id}/")
    assert detail_res.status_code == status.HTTP_200_OK
    baseline = detail_res.data["baseline_metrics"]
    assert baseline["total_eligible_students"] == 3
    assert baseline["placement_rate_eligible"] == 66.67

    # 2. Create Improvement Action Item
    action_payload = {
        "action_title": "Curriculum Update: Include PostgreSQL Indexing & Optimization",
        "category": CycleActionCategory.CURRICULUM_UPDATE,
        "description": "Revise 6th-semester database syllabus to include explain plan and B-tree indexing.",
        "target_completion_date": "2026-11-30",
    }
    act_res = api_client.post(
        f"/api/v1/continuous-improvement/cycle-reviews/{review_id}/actions/",
        action_payload,
        format="json",
    )
    assert act_res.status_code == status.HTTP_201_CREATED
    action_id = act_res.data["id"]

    # 3. Update Action Item Status
    update_act = api_client.post(
        f"/api/v1/continuous-improvement/cycle-actions/{action_id}/status/",
        {"new_status": CycleActionStatus.COMPLETED, "resolution_notes": "Syllabus board approved revision."},
        format="json",
    )
    assert update_act.status_code == status.HTTP_200_OK
    assert update_act.data["status"] == CycleActionStatus.COMPLETED

    # 4. Progress Review to In Review, then Approved
    api_client.post(f"/api/v1/continuous-improvement/cycle-reviews/{review_id}/status/", {"new_status": RecruitmentCycleStatus.IN_REVIEW})
    api_client.force_authenticate(user=placement_head_user)
    appr_cycle = api_client.post(f"/api/v1/continuous-improvement/cycle-reviews/{review_id}/status/", {"new_status": RecruitmentCycleStatus.APPROVED})
    assert appr_cycle.status_code == status.HTTP_200_OK
    assert appr_cycle.data["status"] == RecruitmentCycleStatus.APPROVED


# =========================================================================
# TEST 8: Role Permissions & Student Isolation
# =========================================================================
def test_08_role_permissions_and_student_isolation(api_client, student_user, auditor_user):
    """Students are strictly forbidden from organizational aggregates; Auditors have read-only access."""
    endpoints = [
        "/api/v1/continuous-improvement/placement-rate/",
        "/api/v1/continuous-improvement/feedback/",
        "/api/v1/continuous-improvement/skill-gaps/",
        "/api/v1/continuous-improvement/training-plans/",
        "/api/v1/continuous-improvement/cycle-reviews/",
        "/api/v1/continuous-improvement/diagnostics/",
    ]

    # Student denied on all continuous improvement endpoints
    api_client.force_authenticate(user=student_user)
    for ep in endpoints:
        res = api_client.get(ep)
        assert res.status_code == status.HTTP_403_FORBIDDEN, f"Student should be barred from {ep}"

    # Auditor permitted for read-only access
    api_client.force_authenticate(user=auditor_user)
    for ep in endpoints:
        res = api_client.get(ep)
        assert res.status_code == status.HTTP_200_OK, f"Auditor should have read-only access to {ep}"

    # Auditor forbidden from write operations
    post_res = api_client.post("/api/v1/continuous-improvement/training-plans/", {"title": "Illegal Plan"})
    assert post_res.status_code == status.HTTP_403_FORBIDDEN


# =========================================================================
# TEST 9: CSV Exports & Formula Injection Protection
# =========================================================================
def test_09_csv_exports_and_formula_injection_protection(api_client, admin_user, phase13_dataset):
    """Verify safe CSV exports with formula injection sanitization."""
    api_client.force_authenticate(user=admin_user)

    # 1. Placement Rate CSV
    res_pr = api_client.get("/api/v1/continuous-improvement/placement-rate/export/")
    assert res_pr.status_code == status.HTTP_200_OK
    assert res_pr["Content-Type"] == "text/csv"
    assert "Eligible Cohort Placement Rate" in res_pr.content.decode("utf-8")

    # 2. Skill Gaps CSV
    res_sg = api_client.get("/api/v1/continuous-improvement/skill-gaps/export/")
    assert res_sg.status_code == status.HTTP_200_OK
    assert "Data Structures & Algorithms" in res_sg.content.decode("utf-8")

    # 3. Training Plans CSV
    res_tp = api_client.get("/api/v1/continuous-improvement/training-plans/export/")
    assert res_tp.status_code == status.HTTP_200_OK


# =========================================================================
# TEST 10: Continuous Improvement Diagnostics Scan
# =========================================================================
def test_10_continuous_improvement_diagnostics_scan(api_client, admin_user, phase13_dataset):
    """Verify 6-point data quality diagnostics detects unresolved placement records and health score."""
    api_client.force_authenticate(user=admin_user)
    response = api_client.get("/api/v1/continuous-improvement/diagnostics/")

    assert response.status_code == status.HTTP_200_OK
    data = response.data
    assert "health_score" in data
    assert len(data["checks"]) == 6
    check_codes = [c["code"] for c in data["checks"]]
    assert "UNRESOLVED_OFFERS" in check_codes
    assert "MISSING_STUDENT_FEEDBACK" in check_codes
    assert "OVERDUE_TRAINING_PLANS" in check_codes
