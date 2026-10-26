"""Transactional Domain Services for Student Preparation Workflow (Phase 6 / Steps 15-23)."""
import logging
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import RoleCatalog, User
from apps.core.models import AuditLog
from apps.students.models import StudentProfile, StudentResume
from apps.students.services import upload_student_resume
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

logger = logging.getLogger("apps.preparation")


# ==============================================================================
# Step 15: Resume Review Services
# ==============================================================================

@transaction.atomic
def review_resume_rubric(
    resume_id: str,
    reviewer: User,
    status: str,
    formatting_score: int,
    technical_skills_score: int,
    projects_score: int,
    achievements_score: int,
    detailed_feedback: str,
    suggested_improvements: str = "",
    request=None,
) -> ResumeReview:
    """Submit an authoritative trainer evaluation for a student resume against institutional rubrics."""
    try:
        resume = StudentResume.objects.select_related("student__user").get(id=resume_id)
    except StudentResume.DoesNotExist:
        raise ValidationError(f"Resume with ID {resume_id} does not exist.")

    if status not in [ResumeReviewStatus.APPROVED, ResumeReviewStatus.REVISION_REQUESTED]:
        raise ValidationError(f"Invalid review decision: {status}. Must be APPROVED or REVISION_REQUESTED.")

    for name, val in [
        ("formatting_score", formatting_score),
        ("technical_skills_score", technical_skills_score),
        ("projects_score", projects_score),
        ("achievements_score", achievements_score),
    ]:
        if not (1 <= int(val) <= 10):
            raise ValidationError({name: f"{name} must be an integer between 1 and 10."})

    if not detailed_feedback or not detailed_feedback.strip():
        raise ValidationError({"detailed_feedback": "Detailed feedback is required for institutional audit."})

    review = ResumeReview.objects.create(
        resume=resume,
        student=resume.student,
        reviewer=reviewer,
        status=status,
        formatting_score=int(formatting_score),
        technical_skills_score=int(technical_skills_score),
        projects_score=int(projects_score),
        achievements_score=int(achievements_score),
        detailed_feedback=detailed_feedback.strip(),
        suggested_improvements=suggested_improvements.strip(),
        reviewed_at=timezone.now(),
    )

    # If revision requested, initialize a resume improvement cycle (Step 16)
    if status == ResumeReviewStatus.REVISION_REQUESTED:
        ResumeImprovementCycle.objects.create(
            initial_review=review,
            student=resume.student,
            prior_resume=resume,
            status=ImprovementCycleStatus.REVISION_PENDING,
        )

    AuditLog.objects.create(
        user=reviewer,
        action="RESUME_REVIEW_SUBMITTED",
        resource_type="preparation.ResumeReview",
        resource_id=str(review.id),
        changes={
            "resume_id": str(resume.id),
            "student_id": str(resume.student.id),
            "status": review.status,
            "aggregate_score": review.aggregate_score,
        },
    )

    return review


# ==============================================================================
# Step 16: Resume Improvement Cycle Services
# ==============================================================================

@transaction.atomic
def submit_improved_resume(
    student_profile: StudentProfile,
    file_obj,
    student_notes: str = "",
    user: Optional[User] = None,
    request=None,
) -> Tuple[StudentResume, Optional[ResumeImprovementCycle]]:
    """Student re-uploads improved resume PDF with monotonic versioning linking to pending cycle."""
    # Validate and save resume using existing students service
    new_resume = upload_student_resume(
        student_profile=student_profile,
        file_obj=file_obj,
        user=user or student_profile.user,
        request=request,
    )

    # Link to pending improvement cycle if one exists
    cycle = (
        ResumeImprovementCycle.objects.filter(
            student=student_profile,
            status=ImprovementCycleStatus.REVISION_PENDING,
        )
        .order_by("-created_at")
        .first()
    )

    if cycle:
        cycle.improved_resume = new_resume
        cycle.status = ImprovementCycleStatus.REVISED_UPLOADED
        cycle.student_notes = student_notes.strip()
        cycle.submitted_at = timezone.now()
        cycle.save(update_fields=["improved_resume", "status", "student_notes", "submitted_at", "updated_at"])

        AuditLog.objects.create(
            user=user or student_profile.user,
            action="RESUME_IMPROVEMENT_SUBMITTED",
            resource_type="preparation.ResumeImprovementCycle",
            resource_id=str(cycle.id),
            changes={
                "prior_resume_id": str(cycle.prior_resume_id),
                "improved_resume_id": str(new_resume.id),
                "version_number": new_resume.version_number,
            },
        )

    return new_resume, cycle


# ==============================================================================
# Steps 17 & 18: Aptitude & Technical Assessment Services
# ==============================================================================

@transaction.atomic
def start_assessment_attempt(
    student_profile: StudentProfile,
    test_id: str,
) -> StudentAssessmentAttempt:
    """Initiate a timed attempt on an assessment test for the student."""
    try:
        test = AssessmentTest.objects.get(id=test_id, is_active=True)
    except AssessmentTest.DoesNotExist:
        raise ValidationError(f"Active assessment test with ID {test_id} not found.")

    # Check for unsubmitted in-progress attempt
    existing_in_progress = StudentAssessmentAttempt.objects.filter(
        student=student_profile,
        test=test,
        status=AssessmentAttemptStatus.IN_PROGRESS,
    ).first()

    if existing_in_progress:
        return existing_in_progress

    # Calculate next attempt number
    highest_attempt = (
        StudentAssessmentAttempt.objects.filter(student=student_profile, test=test)
        .order_by("-attempt_number")
        .first()
    )
    attempt_num = (highest_attempt.attempt_number + 1) if highest_attempt else 1

    attempt = StudentAssessmentAttempt.objects.create(
        student=student_profile,
        test=test,
        attempt_number=attempt_num,
        status=AssessmentAttemptStatus.IN_PROGRESS,
        started_at=timezone.now(),
    )

    return attempt


@transaction.atomic
def submit_assessment_attempt(
    attempt_id: str,
    answers: Dict[str, Any],
    user: Optional[User] = None,
) -> StudentAssessmentAttempt:
    """Grade answers deterministically against answer key and finalize attempt outcome."""
    try:
        attempt = StudentAssessmentAttempt.objects.select_related("test", "student__user").get(id=attempt_id)
    except StudentAssessmentAttempt.DoesNotExist:
        raise ValidationError(f"Assessment attempt {attempt_id} not found.")

    if attempt.status == AssessmentAttemptStatus.COMPLETED:
        raise ValidationError("This assessment attempt has already been submitted and finalized.")

    # Score against question bank
    test = attempt.test
    questions = test.questions or []
    total_score = 0
    total_possible = test.total_marks or 100

    for q in questions:
        q_id = str(q.get("id"))
        correct_opt = str(q.get("correct_option_id", "")).strip().upper()
        marks = int(q.get("marks", 10))

        student_opt = str(answers.get(q_id, "")).strip().upper()
        if student_opt and student_opt == correct_opt:
            total_score += marks

    pct = Decimal(str(round((total_score / total_possible) * 100, 2))) if total_possible > 0 else Decimal("0.00")
    passed = total_score >= test.passing_marks

    attempt.answers = answers
    attempt.score = total_score
    attempt.percentage = pct
    attempt.passed = passed
    attempt.status = AssessmentAttemptStatus.COMPLETED
    attempt.completed_at = timezone.now()
    attempt.save()

    AuditLog.objects.create(
        user=user or attempt.student.user,
        action="ASSESSMENT_ATTEMPT_SUBMITTED",
        resource_type="preparation.StudentAssessmentAttempt",
        resource_id=str(attempt.id),
        changes={
            "test_id": str(test.id),
            "test_type": test.test_type,
            "score": total_score,
            "percentage": float(pct),
            "passed": passed,
        },
    )

    return attempt


# ==============================================================================
# Steps 19 & 20: Communication & Grooming Training Services
# ==============================================================================

@transaction.atomic
def record_training_attendance(
    session_id: str,
    student_id: str,
    attendance_status: str,
    presentation_score: Optional[int] = None,
    professional_etiquette_verified: bool = False,
    corporate_communication_verified: bool = False,
    dress_code_verified: bool = False,
    hr_interview_ready: bool = False,
    grooming_certified: bool = False,
    trainer_remarks: str = "",
    trainer: Optional[User] = None,
) -> TrainingAttendance:
    """Record student attendance and corporate grooming criteria for institutional workshops."""
    try:
        session = TrainingSession.objects.get(id=session_id)
    except TrainingSession.DoesNotExist:
        raise ValidationError(f"Training session with ID {session_id} not found.")

    try:
        student = StudentProfile.objects.select_related("user").get(id=student_id)
    except StudentProfile.DoesNotExist:
        raise ValidationError(f"Student profile with ID {student_id} not found.")

    if attendance_status not in [AttendanceStatus.ATTENDED, AttendanceStatus.ABSENT, AttendanceStatus.EXCUSED]:
        raise ValidationError(f"Invalid attendance status: {attendance_status}.")

    if presentation_score is not None:
        if not (1 <= int(presentation_score) <= 10):
            raise ValidationError({"presentation_score": "Presentation score must be between 1 and 10."})

    attendance, created = TrainingAttendance.objects.update_or_create(
        session=session,
        student=student,
        defaults={
            "attendance_status": attendance_status,
            "presentation_score": presentation_score,
            "professional_etiquette_verified": professional_etiquette_verified,
            "corporate_communication_verified": corporate_communication_verified,
            "dress_code_verified": dress_code_verified,
            "hr_interview_ready": hr_interview_ready,
            "grooming_certified": grooming_certified,
            "trainer_remarks": trainer_remarks.strip(),
        },
    )

    AuditLog.objects.create(
        user=trainer,
        action="TRAINING_ATTENDANCE_RECORDED",
        resource_type="preparation.TrainingAttendance",
        resource_id=str(attendance.id),
        changes={
            "session_id": str(session.id),
            "student_id": str(student.id),
            "session_type": session.session_type,
            "attendance_status": attendance_status,
            "grooming_certified": grooming_certified,
        },
    )

    return attendance


# ==============================================================================
# Steps 21 & 22: Mock Interview & Rubric Evaluation Services
# ==============================================================================

@transaction.atomic
def schedule_mock_interview(
    student_id: str,
    evaluator_id: str,
    scheduled_by: User,
    scheduled_at,
    interview_type: str = MockInterviewType.COMBINED,
    meeting_link: str = "",
    notes: str = "",
) -> MockInterview:
    """Schedule a simulated one-on-one interview between candidate and evaluator."""
    try:
        student = StudentProfile.objects.select_related("user").get(id=student_id)
    except StudentProfile.DoesNotExist:
        raise ValidationError(f"Student profile with ID {student_id} not found.")

    try:
        evaluator = User.objects.get(id=evaluator_id)
    except User.DoesNotExist:
        raise ValidationError(f"Evaluator user with ID {evaluator_id} not found.")

    mock = MockInterview.objects.create(
        student=student,
        evaluator=evaluator,
        scheduled_by=scheduled_by,
        interview_type=interview_type,
        scheduled_at=scheduled_at,
        meeting_link=meeting_link.strip(),
        notes=notes.strip(),
        status=MockInterviewStatus.SCHEDULED,
    )

    AuditLog.objects.create(
        user=scheduled_by,
        action="MOCK_INTERVIEW_SCHEDULED",
        resource_type="preparation.MockInterview",
        resource_id=str(mock.id),
        changes={
            "student_id": str(student.id),
            "evaluator_id": str(evaluator.id),
            "interview_type": interview_type,
            "scheduled_at": str(scheduled_at),
        },
    )

    return mock


@transaction.atomic
def evaluate_mock_interview(
    mock_interview_id: str,
    evaluator: User,
    technical_competence_score: int,
    problem_solving_score: int,
    communication_clarity_score: int,
    professional_readiness_score: int,
    technical_feedback: str,
    communication_feedback: str,
    improvement_suggestions: str,
    readiness_recommendation: str,
) -> MockInterviewEvaluation:
    """Submit comprehensive rubric scorecard and candidate readiness recommendation."""
    try:
        mock = MockInterview.objects.select_related("student__user").get(id=mock_interview_id)
    except MockInterview.DoesNotExist:
        raise ValidationError(f"Mock interview {mock_interview_id} not found.")

    for name, val in [
        ("technical_competence_score", technical_competence_score),
        ("problem_solving_score", problem_solving_score),
        ("communication_clarity_score", communication_clarity_score),
        ("professional_readiness_score", professional_readiness_score),
    ]:
        if not (1 <= int(val) <= 10):
            raise ValidationError({name: f"{name} must be between 1 and 10."})

    if readiness_recommendation not in [
        MockReadinessRecommendation.READY_FOR_PLACEMENTS,
        MockReadinessRecommendation.NEEDS_PRACTICE,
        MockReadinessRecommendation.NOT_READY,
    ]:
        raise ValidationError(f"Invalid readiness recommendation: {readiness_recommendation}.")

    if not technical_feedback.strip() or not communication_feedback.strip() or not improvement_suggestions.strip():
        raise ValidationError("Technical feedback, communication feedback, and improvement suggestions are all mandatory.")

    evaluation, created = MockInterviewEvaluation.objects.update_or_create(
        mock_interview=mock,
        defaults={
            "evaluator": evaluator,
            "technical_competence_score": int(technical_competence_score),
            "problem_solving_score": int(problem_solving_score),
            "communication_clarity_score": int(communication_clarity_score),
            "professional_readiness_score": int(professional_readiness_score),
            "technical_feedback": technical_feedback.strip(),
            "communication_feedback": communication_feedback.strip(),
            "improvement_suggestions": improvement_suggestions.strip(),
            "readiness_recommendation": readiness_recommendation,
            "evaluated_at": timezone.now(),
        },
    )

    # Transition mock interview status to COMPLETED
    mock.status = MockInterviewStatus.COMPLETED
    mock.save(update_fields=["status", "updated_at"])

    AuditLog.objects.create(
        user=evaluator,
        action="MOCK_INTERVIEW_EVALUATED",
        resource_type="preparation.MockInterviewEvaluation",
        resource_id=str(evaluation.id),
        changes={
            "mock_interview_id": str(mock.id),
            "total_score": evaluation.total_score,
            "readiness_recommendation": readiness_recommendation,
        },
    )

    return evaluation


# ==============================================================================
# Step 23: Final Placement Resume Approval Gate
# ==============================================================================

@transaction.atomic
def certify_placement_readiness(
    student_id: str,
    approved_resume_id: str,
    certified_by: User,
    is_approved: bool = True,
    notes: str = "",
) -> PlacementReadinessCertification:
    """Certify candidate readiness and lock approved resume for placement drives (Step 23 Gate).

    Mandatory Role Policy: Restricted to Placement Head or Administrator.
    """
    try:
        student = StudentProfile.objects.select_related("user").get(id=student_id)
    except StudentProfile.DoesNotExist:
        raise ValidationError(f"Student profile {student_id} not found.")

    try:
        resume = StudentResume.objects.get(id=approved_resume_id, student=student)
    except StudentResume.DoesNotExist:
        raise ValidationError(f"Resume {approved_resume_id} does not belong to student {student_id}.")

    # Snapshot current preparation criteria state
    readiness_snapshot = get_student_readiness_snapshot(str(student.id))

    status = (
        PlacementReadinessStatus.CERTIFIED
        if is_approved
        else PlacementReadinessStatus.REJECTED
    )

    cert, created = PlacementReadinessCertification.objects.update_or_create(
        student=student,
        approved_resume=resume,
        defaults={
            "is_approved_for_placements": is_approved,
            "status": status,
            "certified_by": certified_by,
            "certified_at": timezone.now(),
            "readiness_summary": readiness_snapshot.get("criteria", {}),
            "notes": notes.strip(),
        },
    )

    AuditLog.objects.create(
        user=certified_by,
        action="PLACEMENT_READINESS_CERTIFIED" if is_approved else "PLACEMENT_READINESS_REJECTED",
        resource_type="preparation.PlacementReadinessCertification",
        resource_id=str(cert.id),
        changes={
            "student_id": str(student.id),
            "approved_resume_id": str(resume.id),
            "resume_version": resume.version_number,
            "is_approved_for_placements": is_approved,
            "status": status,
            "notes": notes.strip(),
        },
    )

    return cert
