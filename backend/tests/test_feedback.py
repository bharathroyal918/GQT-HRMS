"""Comprehensive Automated Test Suite for Phase 9: Feedback Collection.

Covers Authoritative Workflow Phase 9 Categories:
- A. Student Feedback (Interview Experience, Technical Questions, Difficulty, Suggestions)
- B. HR Feedback (Candidate Quality, Technical Skills, Communication Skills, Hiring Satisfaction)
- C. Trainer Feedback (Student Readiness, Training Effectiveness, Areas for Improvement)
- Security: Role-Based Access Controls, Data Isolation, Cross-User Access Prevention, Audit Logging
"""
import uuid
from datetime import datetime, time, timedelta
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
from apps.core.models import AuditLog
from apps.crm.models import Company, CompanyDomainCategory, HRContact
from apps.feedback.models import (
    CandidateQuality,
    DifficultyLevel,
    HRFeedback,
    StudentFeedback,
    StudentReadiness,
    TrainerFeedback,
)
from apps.feedback import selectors, services
from apps.interviews.models import (
    CandidateShortlist,
    InterviewMode,
    InterviewSchedule,
    ScheduleStatus,
    ShortlistedCandidate,
)
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.preparation.models import (
    PlacementReadinessCertification,
    PlacementReadinessStatus,
    TrainingSession,
    TrainingSessionType,
)
from apps.students.models import (
    StudentApplication,
    StudentApplicationStatus,
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
    return make_user("admin.phase9@gqt.internal", RoleCatalog.ADMIN, roles)


@pytest.fixture
def placement_head_user(db, roles):
    return make_user("head.phase9@gqt.internal", RoleCatalog.PLACEMENT_HEAD, roles)


@pytest.fixture
def placement_officer_user(db, roles):
    return make_user("officer.phase9@gqt.internal", RoleCatalog.PLACEMENT_OFFICER, roles)


@pytest.fixture
def hr_mgr_user(db, roles):
    return make_user("hrmgr.phase9@gqt.internal", RoleCatalog.HR_RELATIONSHIP_MGR, roles)


@pytest.fixture
def trainer_user(db, roles):
    return make_user("trainer.phase9@gqt.internal", RoleCatalog.TRAINER, roles)


@pytest.fixture
def auditor_user(db, roles):
    return make_user("auditor.phase9@gqt.internal", RoleCatalog.AUDITOR, roles)


@pytest.fixture
def student_user_a(db, roles):
    user = make_user("student.a@gqt.edu", RoleCatalog.STUDENT, roles)
    StudentProfile.objects.create(
        user=user,
        roll_number="2026-CS-001",
        institutional_email=user.email,
        phone_number="+919876543210",
        department="Computer Science",
        degree="B.Tech",
        graduation_year=2026,
        cgpa="8.50",
    )
    return user


@pytest.fixture
def student_user_b(db, roles):
    user = make_user("student.b@gqt.edu", RoleCatalog.STUDENT, roles)
    StudentProfile.objects.create(
        user=user,
        roll_number="2026-CS-002",
        institutional_email=user.email,
        phone_number="+919876543211",
        department="Information Technology",
        degree="B.Tech",
        graduation_year=2026,
        cgpa="7.80",
    )
    return user


@pytest.fixture
def company(db, hr_mgr_user):
    return Company.objects.create(
        name="Apex Cloud Technologies",
        domain_category=CompanyDomainCategory.IT_SERVICES,
        website="https://apexcloud.io",
        owner=hr_mgr_user,
    )


@pytest.fixture
def other_company(db, admin_user):
    return Company.objects.create(
        name="Global FinTech Solutions",
        domain_category=CompanyDomainCategory.FINANCE_BANKING,
        website="https://globalfintech.io",
        owner=admin_user,
    )


@pytest.fixture
def hr_contact(db, company):
    return HRContact.objects.create(
        company=company,
        name="Jessica Pearson",
        email="jessica.p@apexcloud.io",
        phone="+919876500001",
    )


@pytest.fixture
def job_requirement(db, company, hr_contact, admin_user):
    return JobRequirement.objects.create(
        company=company,
        hr_contact=hr_contact,
        title="Associate Cloud Engineer",
        job_description="Fresh graduate cloud deployment role.",
        skills_required="Python, AWS, Linux, SQL",
        min_salary=600000,
        max_salary=900000,
        location="Bengaluru",
        registration_deadline=timezone.now() + timedelta(days=14),
        status=JobRequirementStatus.APPROVED,
        created_by=admin_user,
        approved_by=admin_user,
    )


@pytest.fixture
def interview_schedule_a(db, student_user_a, job_requirement, company, hr_contact, admin_user):
    prof = student_user_a.student_profile
    resume = StudentResume.objects.create(
        student=prof,
        version_number=1,
        file_name="resume_v1.pdf",
        file_size_bytes=1024,
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_current=True,
    )
    cert = PlacementReadinessCertification.objects.create(
        student=prof,
        approved_resume=resume,
        is_approved_for_placements=True,
        status=PlacementReadinessStatus.CERTIFIED,
        certified_by=admin_user,
    )
    app = StudentApplication.objects.create(
        student=prof,
        job_requirement=job_requirement,
        status=StudentApplicationStatus.APPLIED,
    )
    pkg = SubmissionPackage.objects.create(
        title="Submission Batch A",
        job_requirement=job_requirement,
        company=company,
        hr_contact=hr_contact,
        status=SubmissionPackageStatus.DISPATCHED,
        created_by=admin_user,
    )
    sub = CandidateSubmission.objects.create(
        package=pkg,
        student=prof,
        application=app,
        readiness_certification=cert,
        submitted_resume=resume,
        resume_version_number=1,
        resume_sha256=resume.sha256_hash,
        status=CandidateSubmissionStatus.SUBMITTED,
    )
    shortlist = CandidateShortlist.objects.create(
        job_requirement=job_requirement,
        company=company,
        hr_contact=hr_contact,
        shortlist_reference_code=f"SL-{uuid.uuid4().hex[:8].upper()}",
        candidate_count=1,
        created_by=admin_user,
    )
    sl_cand = ShortlistedCandidate.objects.create(
        shortlist=shortlist,
        student=prof,
        submission=sub,
    )

    target_date = timezone.localdate() + timedelta(days=1)
    target_time = time(10, 0)
    scheduled_start = timezone.make_aware(datetime.combine(target_date, target_time))

    return InterviewSchedule.objects.create(
        student=prof,
        candidate=sl_cand,
        job_requirement=job_requirement,
        company=company,
        schedule_reference_code=f"SCH-FB-{uuid.uuid4().hex[:8].upper()}",
        interview_date=target_date,
        interview_time=target_time,
        scheduled_start_time=scheduled_start,
        mode=InterviewMode.ONLINE,
        meeting_link="https://meet.google.com/abc-def-ghi",
        status=ScheduleStatus.CONDUCTED,
        created_by=admin_user,
    )


@pytest.fixture
def training_session(db, trainer_user):
    return TrainingSession.objects.create(
        title="Advanced System Design & Coding Prep",
        session_type=TrainingSessionType.COMMUNICATION,
        trainer=trainer_user,
        scheduled_at=timezone.now() - timedelta(days=2),
        venue_or_link="Auditorium B",
        is_completed=True,
    )


# ==============================================================================
# SECTION A: Student Feedback Tests (Category A)
# ==============================================================================

@pytest.mark.django_db
def test_01_submit_student_feedback_success(student_user_a, company, job_requirement, interview_schedule_a):
    """Step 9 Category A: Student can submit structured interview feedback."""
    data = {
        "company_id": str(company.id),
        "job_requirement_id": str(job_requirement.id),
        "interview_schedule_id": str(interview_schedule_a.id),
        "interview_experience": "The technical panel was very supportive. Round 1 covered system design and data structures.",
        "technical_questions": "1. Implement an LRU Cache.\n2. Explain ACID properties in PostgreSQL.",
        "difficulty": DifficultyLevel.HARD,
        "suggestions": "Practice graph algorithms and dynamic programming before the drive.",
        "is_anonymous": False,
    }

    feedback = services.submit_student_feedback(student_user_a, data)

    assert feedback.student == student_user_a.student_profile
    assert feedback.company == company
    assert feedback.job_requirement == job_requirement
    assert feedback.interview_schedule == interview_schedule_a
    assert feedback.difficulty == DifficultyLevel.HARD
    assert "LRU Cache" in feedback.technical_questions
    assert feedback.is_anonymous is False
    assert feedback.submitted_by == student_user_a


@pytest.mark.django_db
def test_02_student_feedback_derived_from_authenticated_user(student_user_a, company):
    """Student feedback derives candidate identity from request.user, not arbitrary input."""
    data = {
        "company_id": str(company.id),
        "interview_experience": "General campus recruitment drive with multiple aptitude rounds.",
        "difficulty": DifficultyLevel.MEDIUM,
    }

    feedback = services.submit_student_feedback(student_user_a, data)
    assert feedback.student == student_user_a.student_profile


@pytest.mark.django_db
def test_03_student_feedback_duplicate_prevention(student_user_a, company, interview_schedule_a):
    """Submitting duplicate feedback for the same interview schedule is rejected."""
    data = {
        "company_id": str(company.id),
        "interview_schedule_id": str(interview_schedule_a.id),
        "interview_experience": "First submission experience.",
        "difficulty": DifficultyLevel.EASY,
    }
    services.submit_student_feedback(student_user_a, data)

    with pytest.raises(ValidationError) as exc:
        services.submit_student_feedback(student_user_a, data)
    assert "already submitted feedback" in str(exc.value)


@pytest.mark.django_db
def test_04_student_feedback_min_length_validation(student_user_a, company):
    """Interview experience must be at least 10 characters."""
    data = {
        "company_id": str(company.id),
        "interview_experience": "Good",  # too short
        "difficulty": DifficultyLevel.EASY,
    }
    with pytest.raises(ValidationError) as exc:
        services.submit_student_feedback(student_user_a, data)
    assert "at least 10 characters" in str(exc.value)


@pytest.mark.django_db
def test_05_student_feedback_invalid_difficulty(student_user_a, company):
    """Invalid difficulty choice is rejected."""
    data = {
        "company_id": str(company.id),
        "interview_experience": "Great interview experience overall.",
        "difficulty": "SUPER_HARD",
    }
    with pytest.raises(ValidationError) as exc:
        services.submit_student_feedback(student_user_a, data)
    assert "Invalid difficulty level" in str(exc.value)


@pytest.mark.django_db
def test_06_student_cannot_submit_feedback_for_another_student_interview(student_user_b, company, interview_schedule_a):
    """Student B cannot link their feedback to Student A's interview schedule."""
    data = {
        "company_id": str(company.id),
        "interview_schedule_id": str(interview_schedule_a.id),  # Belongs to student A
        "interview_experience": "Sneaking into someone else's interview.",
        "difficulty": DifficultyLevel.MEDIUM,
    }
    with pytest.raises(ValidationError) as exc:
        services.submit_student_feedback(student_user_b, data)
    assert "scheduled for another student" in str(exc.value)


@pytest.mark.django_db
def test_07_student_feedback_anonymity_masking(api_client, student_user_a, student_user_b, company):
    """When is_anonymous=True, identity is masked for other users viewing serialized output."""
    data = {
        "company_id": str(company.id),
        "interview_experience": "Confidential honest feedback on interview atmosphere.",
        "difficulty": DifficultyLevel.HARD,
        "is_anonymous": True,
    }
    feedback = services.submit_student_feedback(student_user_a, data)

    # When viewed by author Student A: identity is visible
    api_client.force_authenticate(user=student_user_a)
    res_a = api_client.get(f"/api/v1/feedback/student/{feedback.id}/")
    assert res_a.status_code == status.HTTP_200_OK
    assert res_a.data["student_name"] == student_user_a.full_name

    # When viewed by another student: denied via object permissions (404/403)
    api_client.force_authenticate(user=student_user_b)
    res_b = api_client.get(f"/api/v1/feedback/student/{feedback.id}/")
    assert res_b.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


# ==============================================================================
# SECTION B: Corporate HR Feedback Tests (Category B)
# ==============================================================================

@pytest.mark.django_db
def test_08_submit_hr_feedback_success(placement_officer_user, company, hr_contact, job_requirement, student_user_a):
    """Step 9 Category B: Placement officer or HR relationship manager can record corporate HR feedback."""
    data = {
        "company_id": str(company.id),
        "hr_contact_id": str(hr_contact.id),
        "job_requirement_id": str(job_requirement.id),
        "candidate_id": str(student_user_a.student_profile.id),
        "candidate_quality": CandidateQuality.EXCELLENT,
        "candidate_quality_remarks": "Demonstrated outstanding problem-solving and clean coding discipline.",
        "technical_skills_rating": 5,
        "technical_skills_remarks": "Strong grasp of algorithmic complexity and distributed data stores.",
        "communication_skills_rating": 4,
        "communication_skills_remarks": "Clear articulation and confident presentation.",
        "hiring_satisfaction_rating": 5,
        "hiring_satisfaction_remarks": "Extremely satisfied with the campus drive coordination and candidate caliber.",
    }

    feedback = services.submit_hr_feedback(placement_officer_user, data)

    assert feedback.company == company
    assert feedback.hr_contact == hr_contact
    assert feedback.candidate == student_user_a.student_profile
    assert feedback.candidate_quality == CandidateQuality.EXCELLENT
    assert feedback.technical_skills_rating == 5
    assert feedback.hiring_satisfaction_rating == 5
    assert feedback.submitted_by == placement_officer_user


@pytest.mark.django_db
def test_09_hr_feedback_ratings_range_validation(placement_officer_user, company):
    """Numerical ratings must be strictly bounded between 1 and 5."""
    data = {
        "company_id": str(company.id),
        "candidate_quality": CandidateQuality.GOOD,
        "technical_skills_rating": 6,  # Invalid: > 5
        "communication_skills_rating": 3,
        "hiring_satisfaction_rating": 4,
    }
    with pytest.raises(ValidationError) as exc:
        services.submit_hr_feedback(placement_officer_user, data)
    assert "between 1 and 5" in str(exc.value)


@pytest.mark.django_db
def test_10_hr_relationship_manager_scope_enforcement(hr_mgr_user, other_company):
    """HR Relationship Manager cannot submit feedback for an unassigned company."""
    data = {
        "company_id": str(other_company.id),
        "candidate_quality": CandidateQuality.GOOD,
        "technical_skills_rating": 4,
        "communication_skills_rating": 4,
        "hiring_satisfaction_rating": 4,
    }
    with pytest.raises(ValidationError) as exc:
        services.submit_hr_feedback(hr_mgr_user, data)
    assert "not assigned to manage recruitment" in str(exc.value)


@pytest.mark.django_db
def test_11_hr_feedback_duplicate_prevention(placement_officer_user, company, job_requirement, student_user_a):
    """Duplicate HR feedback for the same candidate and job requirement is rejected."""
    data = {
        "company_id": str(company.id),
        "job_requirement_id": str(job_requirement.id),
        "candidate_id": str(student_user_a.student_profile.id),
        "candidate_quality": CandidateQuality.GOOD,
        "technical_skills_rating": 4,
        "communication_skills_rating": 4,
        "hiring_satisfaction_rating": 4,
    }
    services.submit_hr_feedback(placement_officer_user, data)

    with pytest.raises(ValidationError) as exc:
        services.submit_hr_feedback(placement_officer_user, data)
    assert "already been submitted for this candidate" in str(exc.value)


# ==============================================================================
# SECTION C: Trainer Feedback Tests (Category C)
# ==============================================================================

@pytest.mark.django_db
def test_12_submit_trainer_feedback_success(trainer_user, student_user_a, training_session):
    """Step 9 Category C: Placement trainer can submit candidate evaluation feedback."""
    data = {
        "student_id": str(student_user_a.student_profile.id),
        "training_session_id": str(training_session.id),
        "student_readiness": StudentReadiness.READY,
        "student_readiness_remarks": "Candidate exhibits strong conceptual clarity and high interview focus.",
        "training_effectiveness_rating": 5,
        "training_effectiveness_remarks": "Mastered graph traversals and relational schema design efficiently.",
        "areas_for_improvement": "Needs minor practice with rapid-fire behavioral questions under tight time limits.",
    }

    feedback = services.submit_trainer_feedback(trainer_user, data)

    assert feedback.student == student_user_a.student_profile
    assert feedback.training_session == training_session
    assert feedback.student_readiness == StudentReadiness.READY
    assert feedback.training_effectiveness_rating == 5
    assert feedback.trainer == trainer_user


@pytest.mark.django_db
def test_13_trainer_feedback_areas_for_improvement_min_length(trainer_user, student_user_a):
    """Areas for improvement must be at least 10 characters."""
    data = {
        "student_id": str(student_user_a.student_profile.id),
        "student_readiness": StudentReadiness.NEEDS_PRACTICE,
        "training_effectiveness_rating": 3,
        "areas_for_improvement": "None",  # too short
    }
    with pytest.raises(ValidationError) as exc:
        services.submit_trainer_feedback(trainer_user, data)
    assert "at least 10 characters" in str(exc.value)


@pytest.mark.django_db
def test_14_trainer_feedback_duplicate_prevention(trainer_user, student_user_a, training_session):
    """Duplicate trainer feedback for the same session and student is rejected."""
    data = {
        "student_id": str(student_user_a.student_profile.id),
        "training_session_id": str(training_session.id),
        "student_readiness": StudentReadiness.READY,
        "training_effectiveness_rating": 4,
        "areas_for_improvement": "Focus on database concurrency and indexing fundamentals.",
    }
    services.submit_trainer_feedback(trainer_user, data)

    with pytest.raises(ValidationError) as exc:
        services.submit_trainer_feedback(trainer_user, data)
    assert "already submitted feedback" in str(exc.value)


# ==============================================================================
# SECTION D: API Endpoints, RBAC, and Privacy Isolation Tests
# ==============================================================================

@pytest.mark.django_db
def test_15_api_student_feedback_crud_and_isolation(api_client, student_user_a, student_user_b, company):
    """Student can create and read own feedback; Student B cannot access Student A's submission."""
    api_client.force_authenticate(user=student_user_a)

    post_res = api_client.post(
        "/api/v1/feedback/student/",
        {
            "company": str(company.id),
            "interview_experience": "Friendly panel, technical round was comprehensive and fair.",
            "difficulty": DifficultyLevel.MEDIUM,
            "suggestions": "Review operating system basics.",
        },
        format="json",
    )
    assert post_res.status_code == status.HTTP_201_CREATED
    feedback_id = post_res.data["id"]

    # Student A can view their feedback
    get_res = api_client.get(f"/api/v1/feedback/student/{feedback_id}/")
    assert get_res.status_code == status.HTTP_200_OK

    # Student B cannot access Student A's feedback
    api_client.force_authenticate(user=student_user_b)
    b_res = api_client.get(f"/api/v1/feedback/student/{feedback_id}/")
    assert b_res.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND]


@pytest.mark.django_db
def test_16_api_student_denied_from_hr_and_trainer_feedback(api_client, student_user_a, company):
    """Students are strictly forbidden from HR and Trainer feedback endpoints."""
    api_client.force_authenticate(user=student_user_a)

    # Denied from HR feedback
    hr_res = api_client.get("/api/v1/feedback/hr/")
    assert hr_res.status_code == status.HTTP_403_FORBIDDEN

    # Denied from Trainer feedback
    trainer_res = api_client.get("/api/v1/feedback/trainer/")
    assert trainer_res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_17_api_trainer_denied_from_hr_feedback(api_client, trainer_user):
    """Trainers cannot view confidential HR feedback."""
    api_client.force_authenticate(user=trainer_user)
    res = api_client.get("/api/v1/feedback/hr/")
    assert res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_18_api_auditor_read_only_access(api_client, auditor_user, company):
    """Auditors have read-only access and are denied write operations."""
    api_client.force_authenticate(user=auditor_user)

    # Read allowed
    get_res = api_client.get("/api/v1/feedback/hr/")
    assert get_res.status_code == status.HTTP_200_OK

    # Write denied
    post_res = api_client.post(
        "/api/v1/feedback/hr/",
        {
            "company": str(company.id),
            "candidate_quality": CandidateQuality.GOOD,
            "technical_skills_rating": 4,
            "communication_skills_rating": 4,
            "hiring_satisfaction_rating": 4,
        },
        format="json",
    )
    assert post_res.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_19_api_unauthenticated_request_denied(api_client):
    """Unauthenticated requests return 401 Unauthorized across all feedback endpoints."""
    assert api_client.get("/api/v1/feedback/student/").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.get("/api/v1/feedback/hr/").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.get("/api/v1/feedback/trainer/").status_code == status.HTTP_401_UNAUTHORIZED
    assert api_client.get("/api/v1/feedback/summary/").status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_20_api_feedback_summary_kpis(api_client, placement_officer_user, student_user_a, company, trainer_user):
    """Feedback KPI summary endpoint computes correct totals and averages."""
    # Seed 1 student feedback
    services.submit_student_feedback(
        student_user_a,
        {
            "company_id": str(company.id),
            "interview_experience": "Excellent drive coordination.",
            "difficulty": DifficultyLevel.HARD,
        },
    )

    # Seed 1 HR feedback
    services.submit_hr_feedback(
        placement_officer_user,
        {
            "company_id": str(company.id),
            "candidate_quality": CandidateQuality.GOOD,
            "technical_skills_rating": 4,
            "communication_skills_rating": 5,
            "hiring_satisfaction_rating": 5,
        },
    )

    # Seed 1 Trainer feedback
    services.submit_trainer_feedback(
        trainer_user,
        {
            "student_id": str(student_user_a.student_profile.id),
            "student_readiness": StudentReadiness.READY,
            "training_effectiveness_rating": 4,
            "areas_for_improvement": "Keep polishing mock technical interview answers.",
        },
    )

    api_client.force_authenticate(user=placement_officer_user)
    res = api_client.get("/api/v1/feedback/summary/")

    assert res.status_code == status.HTTP_200_OK
    data = res.data
    assert data["total_student_feedback"] == 1
    assert data["total_hr_feedback"] == 1
    assert data["total_trainer_feedback"] == 1
    assert data["avg_technical_skills_rating"] == 4.0
    assert data["avg_communication_skills_rating"] == 5.0
    assert data["avg_hiring_satisfaction_rating"] == 5.0
    assert data["avg_training_effectiveness_rating"] == 4.0
    assert data["difficulty_breakdown"].get(DifficultyLevel.HARD) == 1
    assert data["readiness_breakdown"].get(StudentReadiness.READY) == 1


@pytest.mark.django_db
def test_21_audit_log_recorded_for_feedback_actions(student_user_a, company):
    """Feedback operations persist immutable AuditLog entries without logging confidential text."""
    feedback = services.submit_student_feedback(
        student_user_a,
        {
            "company_id": str(company.id),
            "interview_experience": "Solid multi-round interview format.",
            "difficulty": DifficultyLevel.MEDIUM,
        },
    )

    log = AuditLog.objects.filter(resource_type="STUDENT_FEEDBACK", resource_id=str(feedback.id)).first()
    assert log is not None
    assert log.action == "SUBMIT_STUDENT_FEEDBACK"
    assert log.user == student_user_a
    # Confidential text should not be leaked in changes JSON
    assert "interview_experience" not in log.changes


@pytest.mark.django_db
def test_22_feedback_filtering(api_client, placement_officer_user, student_user_a, student_user_b, company, other_company):
    """Feedback listings can be safely filtered by company and difficulty."""
    services.submit_student_feedback(
        student_user_a,
        {
            "company_id": str(company.id),
            "interview_experience": "Feedback on Apex Cloud drive.",
            "difficulty": DifficultyLevel.HARD,
        },
    )
    services.submit_student_feedback(
        student_user_b,
        {
            "company_id": str(other_company.id),
            "interview_experience": "Feedback on Global FinTech drive.",
            "difficulty": DifficultyLevel.EASY,
        },
    )

    api_client.force_authenticate(user=placement_officer_user)

    # Filter by company
    res_company = api_client.get(f"/api/v1/feedback/student/?company={company.id}")
    assert res_company.status_code == status.HTTP_200_OK
    items_company = res_company.data.get("data", res_company.data.get("results", res_company.data))
    assert len(items_company) == 1

    # Filter by difficulty
    res_diff = api_client.get("/api/v1/feedback/student/?difficulty=EASY")
    assert res_diff.status_code == status.HTTP_200_OK
    items_diff = res_diff.data.get("data", res_diff.data.get("results", res_diff.data))
    assert len(items_diff) == 1
    assert items_diff[0]["difficulty"] == DifficultyLevel.EASY
