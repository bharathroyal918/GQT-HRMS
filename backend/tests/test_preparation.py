"""Comprehensive Automated Test Suite for Phase 6: Student Preparation (Steps 15-23).

Authoritative Workflow Coverage:
- Step 15: Resume Review (Trainer evaluation against institutional rubric)
- Step 16: Resume Improvement Cycle (Candidate revisions, monotonic PDF re-upload)
- Step 17: Aptitude Assessment (Timed quantitative & logical tests, deterministic scoring)
- Step 18: Technical Assessment (Domain assessments, answer-key stripping on student queries)
- Step 19: Communication Skills Training (Workshop scheduling, presentation scores)
- Step 20: Corporate Grooming Session (Etiquette, communication, dress code certification)
- Step 21: One-on-One Mock Interview (Technical, HR, and combined mock scheduling)
- Step 22: Mock Interview Evaluation (Rubric scorecards, feedback, readiness recommendations)
- Step 23: Final Placement Resume Approval Gate (Placement Head readiness certification)
- Candidate Data Isolation & Role-Based Access Controls
- Audit Trail Logging for Consequential Decisions
"""
import io
import uuid
from decimal import Decimal
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import Role, RoleCatalog, User, UserRoleAssignment
from apps.core.models import AuditLog
from apps.students.models import StudentProfile, StudentResume
from apps.preparation.models import (
    ResumeReview,
    ResumeReviewStatus,
    ResumeImprovementCycle,
    ImprovementCycleStatus,
    AssessmentTest,
    AssessmentTestType,
    StudentAssessmentAttempt,
    AssessmentAttemptStatus,
    TrainingSession,
    TrainingSessionType,
    TrainingAttendance,
    AttendanceStatus,
    MockInterview,
    MockInterviewType,
    MockInterviewStatus,
    MockInterviewEvaluation,
    MockReadinessRecommendation,
    PlacementReadinessCertification,
    PlacementReadinessStatus,
)
from apps.preparation.selectors import get_student_readiness_snapshot
from apps.preparation.services import (
    review_resume_rubric,
    submit_improved_resume,
    start_assessment_attempt,
    submit_assessment_attempt,
    record_training_attendance,
    schedule_mock_interview,
    evaluate_mock_interview,
    certify_placement_readiness,
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
    return make_user("admin.phase6@gqt.internal", RoleCatalog.ADMIN, roles)


@pytest.fixture
def placement_head(db, roles):
    return make_user("head.phase6@gqt.internal", RoleCatalog.PLACEMENT_HEAD, roles)


@pytest.fixture
def placement_officer(db, roles):
    return make_user("officer.phase6@gqt.internal", RoleCatalog.PLACEMENT_OFFICER, roles)


@pytest.fixture
def trainer_user(db, roles):
    return make_user("trainer.phase6@gqt.internal", RoleCatalog.TRAINER, roles)


@pytest.fixture
def evaluator_user(db, roles):
    return make_user("evaluator.phase6@gqt.internal", RoleCatalog.EVALUATOR, roles)


@pytest.fixture
def student_user_a(db, roles):
    user = make_user("student.a@gqt.edu", RoleCatalog.STUDENT, roles)
    user.first_name = "Candidate"
    user.last_name = "Alpha"
    user.save()
    return user


@pytest.fixture
def student_profile_a(db, student_user_a):
    return StudentProfile.objects.create(
        user=student_user_a,
        roll_number="1GQ21CS001",
        institutional_email=student_user_a.email,
        college_name="GQT Engineering College",
        degree="B.E.",
        department="Computer Science",
        graduation_year=2025,
        cgpa=Decimal("8.50"),
        active_backlogs=0,
        phone_number="+919876543210",
    )


@pytest.fixture
def student_user_b(db, roles):
    user = make_user("student.b@gqt.edu", RoleCatalog.STUDENT, roles)
    user.first_name = "Candidate"
    user.last_name = "Beta"
    user.save()
    return user


@pytest.fixture
def student_profile_b(db, student_user_b):
    return StudentProfile.objects.create(
        user=student_user_b,
        roll_number="1GQ21CS002",
        institutional_email=student_user_b.email,
        college_name="GQT Engineering College",
        degree="B.E.",
        department="Information Science",
        graduation_year=2025,
        cgpa=Decimal("7.80"),
        active_backlogs=0,
        phone_number="+919876543211",
    )


@pytest.fixture
def sample_pdf_content():
    return b"%PDF-1.4\n1 0 obj\n<< /Title (Student Resume) >>\nendobj\ntrailer\n<< /Root 1 0 R >>\n%%EOF\n"


@pytest.fixture
def student_resume_v1(db, student_profile_a, sample_pdf_content):
    file_obj = SimpleUploadedFile("candidate_resume_v1.pdf", sample_pdf_content, content_type="application/pdf")
    return StudentResume.objects.create(
        student=student_profile_a,
        version_number=1,
        file=file_obj,
        file_name="candidate_resume_v1.pdf",
        file_size_bytes=len(sample_pdf_content),
        sha256_hash="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        is_current=True,
    )


@pytest.fixture
def sample_aptitude_test(db, trainer_user):
    questions = [
        {
            "id": 1,
            "question_text": "If a train runs at 60 km/h, how far does it travel in 45 minutes?",
            "options": [
                {"id": "A", "text": "40 km"},
                {"id": "B", "text": "45 km"},
                {"id": "C", "text": "50 km"},
            ],
            "correct_option_id": "B",
            "marks": 50,
            "explanation": "Distance = speed * time = 60 * (45/60) = 45 km",
        },
        {
            "id": 2,
            "question_text": "Find the next number in series: 2, 4, 8, 16, ...",
            "options": [
                {"id": "A", "text": "24"},
                {"id": "B", "text": "30"},
                {"id": "C", "text": "32"},
            ],
            "correct_option_id": "C",
            "marks": 50,
            "explanation": "Each term is multiplied by 2. 16 * 2 = 32.",
        },
    ]
    return AssessmentTest.objects.create(
        title="General Aptitude & Reasoning Benchmark",
        test_type=AssessmentTestType.APTITUDE,
        domain_track="Quantitative & Logical",
        description="Core quantitative and reasoning assessment for freshers.",
        duration_minutes=30,
        total_marks=100,
        passing_marks=60,
        questions=questions,
        created_by=trainer_user,
    )


@pytest.fixture
def sample_technical_test(db, trainer_user):
    questions = [
        {
            "id": 1,
            "question_text": "What is the time complexity of searching in a balanced BST?",
            "options": [
                {"id": "A", "text": "O(1)"},
                {"id": "B", "text": "O(log n)"},
                {"id": "C", "text": "O(n)"},
            ],
            "correct_option_id": "B",
            "marks": 50,
            "explanation": "Binary search on balanced tree halves search space each level, O(log n).",
        },
        {
            "id": 2,
            "question_text": "Which ACID property guarantees transactional persistence?",
            "options": [
                {"id": "A", "text": "Atomicity"},
                {"id": "B", "text": "Isolation"},
                {"id": "C", "text": "Durability"},
            ],
            "correct_option_id": "C",
            "marks": 50,
            "explanation": "Durability guarantees committed transactions survive system crashes.",
        },
    ]
    return AssessmentTest.objects.create(
        title="Core Computer Science & Coding Test",
        test_type=AssessmentTestType.TECHNICAL,
        domain_track="Data Structures & Databases",
        description="Evaluates algorithmic fundamentals and database systems.",
        duration_minutes=45,
        total_marks=100,
        passing_marks=60,
        questions=questions,
        created_by=trainer_user,
    )


# ==============================================================================
# Step 15 Tests: Resume Review
# ==============================================================================

def test_01_resume_review_by_trainer_success(db, student_resume_v1, trainer_user):
    """Step 15: Placement trainer evaluates student resume against institutional rubric."""
    review = review_resume_rubric(
        resume_id=str(student_resume_v1.id),
        reviewer=trainer_user,
        status=ResumeReviewStatus.APPROVED,
        formatting_score=9,
        technical_skills_score=8,
        projects_score=9,
        achievements_score=8,
        detailed_feedback="Clean formatting, relevant full-stack projects, and verified GitHub links.",
        suggested_improvements="Add cloud deployment badges to project section.",
    )
    assert review.id is not None
    assert review.status == ResumeReviewStatus.APPROVED
    assert review.aggregate_score == 34
    assert review.reviewer == trainer_user
    assert review.student == student_resume_v1.student


def test_02_resume_review_revision_requested_creates_improvement_cycle(db, student_resume_v1, trainer_user):
    """Step 15 -> Step 16: Revision requested automatically triggers ResumeImprovementCycle."""
    review = review_resume_rubric(
        resume_id=str(student_resume_v1.id),
        reviewer=trainer_user,
        status=ResumeReviewStatus.REVISION_REQUESTED,
        formatting_score=5,
        technical_skills_score=6,
        projects_score=4,
        achievements_score=5,
        detailed_feedback="Projects lack measurable impact metrics. Format is inconsistent.",
        suggested_improvements="Quantify outcomes and standardize date headers.",
    )
    assert review.status == ResumeReviewStatus.REVISION_REQUESTED

    cycle = ResumeImprovementCycle.objects.filter(initial_review=review).first()
    assert cycle is not None
    assert cycle.student == student_resume_v1.student
    assert cycle.prior_resume == student_resume_v1
    assert cycle.status == ImprovementCycleStatus.REVISION_PENDING


def test_03_resume_review_invalid_score_boundary_rejected(db, student_resume_v1, trainer_user):
    """Rubric scores outside 1-10 are strictly rejected."""
    with pytest.raises(ValidationError):
        review_resume_rubric(
            resume_id=str(student_resume_v1.id),
            reviewer=trainer_user,
            status=ResumeReviewStatus.APPROVED,
            formatting_score=11,  # Invalid: > 10
            technical_skills_score=8,
            projects_score=8,
            achievements_score=8,
            detailed_feedback="Valid comments",
        )


def test_04_api_resume_review_role_gate(api_client, student_resume_v1, student_user_a, trainer_user):
    """Students cannot review resumes; only trainers and staff are permitted."""
    api_client.force_authenticate(user=student_user_a)
    payload = {
        "resume_id": str(student_resume_v1.id),
        "status": "APPROVED",
        "formatting_score": 8,
        "technical_skills_score": 8,
        "projects_score": 8,
        "achievements_score": 8,
        "detailed_feedback": "Self-review attempt",
    }
    resp = api_client.post("/api/v1/preparation/resume-reviews/", payload, format="json")
    assert resp.status_code == 403

    # Trainer succeeds
    api_client.force_authenticate(user=trainer_user)
    resp_trainer = api_client.post("/api/v1/preparation/resume-reviews/", payload, format="json")
    assert resp_trainer.status_code == 201
    assert resp_trainer.data["status"] == "APPROVED"


# ==============================================================================
# Step 16 Tests: Resume Improvement Cycle
# ==============================================================================

def test_05_resume_improvement_reupload_success(db, student_profile_a, student_resume_v1, trainer_user):
    """Step 16: Student iterates and re-uploads improved resume with monotonic versioning."""
    # Step 15: Request revision
    review = review_resume_rubric(
        resume_id=str(student_resume_v1.id),
        reviewer=trainer_user,
        status=ResumeReviewStatus.REVISION_REQUESTED,
        formatting_score=5,
        technical_skills_score=6,
        projects_score=5,
        achievements_score=5,
        detailed_feedback="Revise formatting and project descriptions.",
    )

    # Step 16: Student submits revised resume
    revised_pdf = b"%PDF-1.4\nRevised content with quantified metrics\n%%EOF\n"
    file_obj = SimpleUploadedFile("candidate_resume_v2.pdf", revised_pdf, content_type="application/pdf")

    new_resume, cycle = submit_improved_resume(
        student_profile=student_profile_a,
        file_obj=file_obj,
        student_notes="Added metrics and aligned typography per trainer instructions.",
        user=student_profile_a.user,
    )

    assert new_resume.version_number == 2
    assert new_resume.is_current is True
    assert cycle is not None
    assert cycle.status == ImprovementCycleStatus.REVISED_UPLOADED
    assert cycle.improved_resume == new_resume


# ==============================================================================
# Steps 17 & 18 Tests: Aptitude & Technical Assessments
# ==============================================================================

def test_06_aptitude_test_start_and_deterministic_grading_pass(db, student_profile_a, sample_aptitude_test):
    """Step 17: Timed aptitude assessment submission and deterministic passing score."""
    attempt = start_assessment_attempt(
        student_profile=student_profile_a,
        test_id=str(sample_aptitude_test.id),
    )
    assert attempt.status == AssessmentAttemptStatus.IN_PROGRESS
    assert attempt.attempt_number == 1

    # Student answers both correctly: 1: 'B', 2: 'C' -> 100/100 marks
    answers = {"1": "B", "2": "C"}
    final_attempt = submit_assessment_attempt(
        attempt_id=str(attempt.id),
        answers=answers,
        user=student_profile_a.user,
    )

    assert final_attempt.status == AssessmentAttemptStatus.COMPLETED
    assert final_attempt.score == 100
    assert final_attempt.percentage == Decimal("100.00")
    assert final_attempt.passed is True


def test_07_aptitude_test_score_below_passing_marks_fails(db, student_profile_a, sample_aptitude_test):
    """Score below passing_marks evaluates to passed=False."""
    attempt = start_assessment_attempt(
        student_profile=student_profile_a,
        test_id=str(sample_aptitude_test.id),
    )
    # Answers 1 wrong, 1 correct: score = 50 / 100 (< 60 passing marks)
    answers = {"1": "A", "2": "C"}
    final_attempt = submit_assessment_attempt(
        attempt_id=str(attempt.id),
        answers=answers,
        user=student_profile_a.user,
    )
    assert final_attempt.score == 50
    assert final_attempt.passed is False


def test_08_technical_assessment_student_view_strips_answer_keys(api_client, student_user_a, sample_technical_test):
    """Step 18 Security: Questions retrieved by a student strictly omit correct_option_id and explanation."""
    api_client.force_authenticate(user=student_user_a)
    resp = api_client.get(f"/api/v1/preparation/tests/{sample_technical_test.id}/")
    assert resp.status_code == 200

    questions = resp.data["questions"]
    assert len(questions) == 2
    for q in questions:
        assert "correct_option_id" not in q
        assert "explanation" not in q
        assert "question_text" in q
        assert "options" in q


def test_09_technical_assessment_staff_view_preserves_answer_keys(api_client, trainer_user, sample_technical_test):
    """Staff / Trainers can view answer keys and explanations."""
    api_client.force_authenticate(user=trainer_user)
    resp = api_client.get(f"/api/v1/preparation/tests/{sample_technical_test.id}/")
    assert resp.status_code == 200

    questions = resp.data["questions"]
    for q in questions:
        assert "correct_option_id" in q
        assert "explanation" in q


def test_10_duplicate_assessment_attempt_submission_blocked(db, student_profile_a, sample_aptitude_test):
    """Cannot submit a finalized attempt twice."""
    attempt = start_assessment_attempt(
        student_profile=student_profile_a,
        test_id=str(sample_aptitude_test.id),
    )
    submit_assessment_attempt(attempt_id=str(attempt.id), answers={"1": "B"})

    with pytest.raises(ValidationError, match="already been submitted"):
        submit_assessment_attempt(attempt_id=str(attempt.id), answers={"1": "B"})


# ==============================================================================
# Steps 19 & 20 Tests: Communication & Corporate Grooming
# ==============================================================================

def test_11_communication_training_session_and_attendance(db, student_profile_a, trainer_user):
    """Step 19: Workshop scheduling and presentation evaluation scoring."""
    session = TrainingSession.objects.create(
        title="Corporate Presentation & Communication Skills Workshop",
        session_type=TrainingSessionType.COMMUNICATION,
        trainer=trainer_user,
        scheduled_at=timezone.now(),
        venue_or_link="Auditorium A / Seminar Hall 2",
    )

    attendance = record_training_attendance(
        session_id=str(session.id),
        student_id=str(student_profile_a.id),
        attendance_status=AttendanceStatus.ATTENDED,
        presentation_score=9,
        trainer_remarks="Excellent delivery and confident articulation.",
        trainer=trainer_user,
    )
    assert attendance.attendance_status == AttendanceStatus.ATTENDED
    assert attendance.presentation_score == 9


def test_12_corporate_grooming_session_verification_and_certification(db, student_profile_a, trainer_user):
    """Step 20: Corporate grooming certification verifying etiquette, decorum, and dress code."""
    session = TrainingSession.objects.create(
        title="Corporate Grooming & Professional Etiquette Intensive",
        session_type=TrainingSessionType.CORPORATE_GROOMING,
        trainer=trainer_user,
        scheduled_at=timezone.now(),
        venue_or_link="Placement Conference Room",
    )

    attendance = record_training_attendance(
        session_id=str(session.id),
        student_id=str(student_profile_a.id),
        attendance_status=AttendanceStatus.ATTENDED,
        professional_etiquette_verified=True,
        corporate_communication_verified=True,
        dress_code_verified=True,
        hr_interview_ready=True,
        grooming_certified=True,
        trainer_remarks="Meets all institutional corporate grooming and attire standards.",
        trainer=trainer_user,
    )
    assert attendance.grooming_certified is True
    assert attendance.dress_code_verified is True
    assert attendance.hr_interview_ready is True


# ==============================================================================
# Steps 21 & 22 Tests: Mock Interview & Rubric Scorecard
# ==============================================================================

def test_13_mock_interview_scheduling_success(db, student_profile_a, evaluator_user, placement_officer):
    """Step 21: Placement staff schedules one-on-one mock interview with industry evaluator."""
    scheduled_time = timezone.now() + timezone.timedelta(days=2)
    mock = schedule_mock_interview(
        student_id=str(student_profile_a.id),
        evaluator_id=str(evaluator_user.id),
        scheduled_by=placement_officer,
        scheduled_at=scheduled_time,
        interview_type=MockInterviewType.COMBINED,
        meeting_link="https://meet.google.com/gqt-mock-123",
        notes="Assess data structures, system design, and communication fluency.",
    )
    assert mock.id is not None
    assert mock.status == MockInterviewStatus.SCHEDULED
    assert mock.evaluator == evaluator_user
    assert mock.student == student_profile_a


def test_14_mock_interview_evaluation_rubric_and_readiness_recommendation(
    db, student_profile_a, evaluator_user, placement_officer
):
    """Step 22: Evaluator submits comprehensive scorecard and readiness recommendation."""
    mock = schedule_mock_interview(
        student_id=str(student_profile_a.id),
        evaluator_id=str(evaluator_user.id),
        scheduled_by=placement_officer,
        scheduled_at=timezone.now(),
    )

    evaluation = evaluate_mock_interview(
        mock_interview_id=str(mock.id),
        evaluator=evaluator_user,
        technical_competence_score=8,
        problem_solving_score=9,
        communication_clarity_score=8,
        professional_readiness_score=9,
        technical_feedback="Demonstrates strong coding intuition and understanding of time complexity.",
        communication_feedback="Crisp explanations, pauses to organize thoughts effectively.",
        improvement_suggestions="Review SQL window functions before target company drive.",
        readiness_recommendation=MockReadinessRecommendation.READY_FOR_PLACEMENTS,
    )

    assert evaluation.total_score == 34
    assert evaluation.readiness_recommendation == MockReadinessRecommendation.READY_FOR_PLACEMENTS

    # Interview status transitions to COMPLETED
    mock.refresh_from_db()
    assert mock.status == MockInterviewStatus.COMPLETED


def test_15_mock_interview_evaluation_requires_mandatory_feedback(db, student_profile_a, evaluator_user, placement_officer):
    """Missing qualitative feedback raises ValidationError."""
    mock = schedule_mock_interview(
        student_id=str(student_profile_a.id),
        evaluator_id=str(evaluator_user.id),
        scheduled_by=placement_officer,
        scheduled_at=timezone.now(),
    )

    with pytest.raises(ValidationError):
        evaluate_mock_interview(
            mock_interview_id=str(mock.id),
            evaluator=evaluator_user,
            technical_competence_score=8,
            problem_solving_score=8,
            communication_clarity_score=8,
            professional_readiness_score=8,
            technical_feedback="",  # Empty
            communication_feedback="Good",
            improvement_suggestions="Practice",
            readiness_recommendation=MockReadinessRecommendation.READY_FOR_PLACEMENTS,
        )


# ==============================================================================
# Step 23 Tests: Final Placement Readiness Certification Gate
# ==============================================================================

def test_16_readiness_snapshot_compiles_steps_15_to_22_correctly(
    db, student_profile_a, student_resume_v1, trainer_user, evaluator_user, placement_officer, sample_aptitude_test, sample_technical_test
):
    """Readiness selector aggregates progress across all preparation steps."""
    # Step 15: Review
    review_resume_rubric(
        resume_id=str(student_resume_v1.id),
        reviewer=trainer_user,
        status=ResumeReviewStatus.APPROVED,
        formatting_score=9,
        technical_skills_score=9,
        projects_score=9,
        achievements_score=9,
        detailed_feedback="All rubric points verified.",
    )

    # Step 17: Aptitude
    att_apt = start_assessment_attempt(student_profile=student_profile_a, test_id=str(sample_aptitude_test.id))
    submit_assessment_attempt(attempt_id=str(att_apt.id), answers={"1": "B", "2": "C"})

    # Step 18: Technical
    att_tech = start_assessment_attempt(student_profile=student_profile_a, test_id=str(sample_technical_test.id))
    submit_assessment_attempt(attempt_id=str(att_tech.id), answers={"1": "B", "2": "C"})

    # Step 19: Comm
    comm_sess = TrainingSession.objects.create(
        title="Communication", session_type=TrainingSessionType.COMMUNICATION, trainer=trainer_user, scheduled_at=timezone.now(), venue_or_link="Auditorium"
    )
    record_training_attendance(session_id=str(comm_sess.id), student_id=str(student_profile_a.id), attendance_status=AttendanceStatus.ATTENDED)

    # Step 20: Grooming
    groom_sess = TrainingSession.objects.create(
        title="Grooming", session_type=TrainingSessionType.CORPORATE_GROOMING, trainer=trainer_user, scheduled_at=timezone.now(), venue_or_link="Room 101"
    )
    record_training_attendance(session_id=str(groom_sess.id), student_id=str(student_profile_a.id), attendance_status=AttendanceStatus.ATTENDED, grooming_certified=True)

    # Steps 21 & 22: Mock
    mock = schedule_mock_interview(student_id=str(student_profile_a.id), evaluator_id=str(evaluator_user.id), scheduled_by=placement_officer, scheduled_at=timezone.now())
    evaluate_mock_interview(
        mock_interview_id=str(mock.id),
        evaluator=evaluator_user,
        technical_competence_score=8,
        problem_solving_score=8,
        communication_clarity_score=8,
        professional_readiness_score=8,
        technical_feedback="Solid",
        communication_feedback="Fluent",
        improvement_suggestions="Keep it up",
        readiness_recommendation=MockReadinessRecommendation.READY_FOR_PLACEMENTS,
    )

    snapshot = get_student_readiness_snapshot(str(student_profile_a.id))
    assert snapshot["all_criteria_met"] is True
    assert snapshot["criteria"]["resume_review_approved"] is True
    assert snapshot["criteria"]["aptitude_assessment_passed"] is True
    assert snapshot["criteria"]["technical_assessment_passed"] is True
    assert snapshot["criteria"]["communication_attended"] is True
    assert snapshot["criteria"]["grooming_certified"] is True
    assert snapshot["criteria"]["mock_interview_ready"] is True


def test_17_placement_readiness_certification_gate_placement_head_success(
    db, student_profile_a, student_resume_v1, placement_head
):
    """Step 23 Gate: Placement Head authorizes readiness certification locking resume for drives."""
    cert = certify_placement_readiness(
        student_id=str(student_profile_a.id),
        approved_resume_id=str(student_resume_v1.id),
        certified_by=placement_head,
        is_approved=True,
        notes="Candidate verified across all preparation criteria. Certified ready for company dispatch.",
    )
    assert cert.is_approved_for_placements is True
    assert cert.status == PlacementReadinessStatus.CERTIFIED
    assert cert.certified_by == placement_head
    assert cert.approved_resume == student_resume_v1


def test_18_placement_readiness_certification_role_gate_denies_officer(
    api_client, student_profile_a, student_resume_v1, placement_officer, placement_head
):
    """Step 23 Gate: Placement Officer cannot certify readiness; only Placement Head / Admin can."""
    payload = {
        "student_id": str(student_profile_a.id),
        "approved_resume_id": str(student_resume_v1.id),
        "is_approved": True,
        "notes": "Officer certification attempt",
    }
    api_client.force_authenticate(user=placement_officer)
    resp = api_client.post("/api/v1/preparation/certifications/certify/", payload, format="json")
    assert resp.status_code == 403

    # Placement Head succeeds
    api_client.force_authenticate(user=placement_head)
    resp_head = api_client.post("/api/v1/preparation/certifications/certify/", payload, format="json")
    assert resp_head.status_code == 200
    assert resp_head.data["is_approved_for_placements"] is True


def test_19_placement_readiness_certification_rejection_path(db, student_profile_a, student_resume_v1, placement_head):
    """Step 23 Gate: Candidate returned for remedial preparation with is_approved_for_placements = False."""
    cert = certify_placement_readiness(
        student_id=str(student_profile_a.id),
        approved_resume_id=str(student_resume_v1.id),
        certified_by=placement_head,
        is_approved=False,
        notes="Returned: Candidate needs another mock interview iteration before corporate dispatch.",
    )
    assert cert.is_approved_for_placements is False
    assert cert.status == PlacementReadinessStatus.REJECTED


def test_20_api_student_data_isolation(api_client, student_profile_a, student_profile_b, student_user_a, student_user_b):
    """Security: Student A cannot inspect Student B's readiness snapshot or review records."""
    api_client.force_authenticate(user=student_user_a)
    resp = api_client.get(f"/api/v1/preparation/readiness-snapshot/{student_profile_b.id}/")
    assert resp.status_code == 403

    # Can inspect own snapshot
    resp_own = api_client.get(f"/api/v1/preparation/readiness-snapshot/{student_profile_a.id}/")
    assert resp_own.status_code == 200


def test_21_api_unauthenticated_requests_denied(api_client, student_profile_a):
    """Unauthenticated access returns 401 across endpoints."""
    assert api_client.get("/api/v1/preparation/resume-reviews/").status_code == 401
    assert api_client.get("/api/v1/preparation/tests/").status_code == 401
    assert api_client.get("/api/v1/preparation/mock-interviews/").status_code == 401
    assert api_client.get(f"/api/v1/preparation/readiness-snapshot/{student_profile_a.id}/").status_code == 401


def test_22_audit_trail_recorded_for_preparation_milestones(
    db, student_profile_a, student_resume_v1, trainer_user, evaluator_user, placement_head, placement_officer
):
    """AuditLog records actor, action, and changes across preparation lifecycle."""
    # Review
    review_resume_rubric(
        resume_id=str(student_resume_v1.id),
        reviewer=trainer_user,
        status=ResumeReviewStatus.APPROVED,
        formatting_score=8,
        technical_skills_score=8,
        projects_score=8,
        achievements_score=8,
        detailed_feedback="Approved",
    )
    assert AuditLog.objects.filter(action="RESUME_REVIEW_SUBMITTED", user=trainer_user).exists()

    # Certification
    certify_placement_readiness(
        student_id=str(student_profile_a.id),
        approved_resume_id=str(student_resume_v1.id),
        certified_by=placement_head,
        is_approved=True,
    )
    assert AuditLog.objects.filter(action="PLACEMENT_READINESS_CERTIFIED", user=placement_head).exists()
