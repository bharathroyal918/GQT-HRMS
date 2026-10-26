"""Reusable Query Selectors for Student Preparation Domain (Phase 6)."""
from typing import Dict, Any, List, Optional
from django.db.models import QuerySet, Q
from apps.students.models import StudentProfile, StudentResume
from apps.preparation.models import (
    ResumeReview,
    ResumeReviewStatus,
    ResumeImprovementCycle,
    AssessmentTest,
    AssessmentTestType,
    StudentAssessmentAttempt,
    AssessmentAttemptStatus,
    TrainingSession,
    TrainingAttendance,
    AttendanceStatus,
    MockInterview,
    MockInterviewEvaluation,
    MockReadinessRecommendation,
    PlacementReadinessCertification,
)


def get_resume_reviews(
    student_id: Optional[str] = None,
    resume_id: Optional[str] = None,
    status: Optional[str] = None,
) -> QuerySet[ResumeReview]:
    """Retrieve resume review records with filtering."""
    qs = ResumeReview.objects.select_related("student__user", "resume", "reviewer").all()
    if student_id:
        qs = qs.filter(student_id=student_id)
    if resume_id:
        qs = qs.filter(resume_id=resume_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def get_active_assessment_tests(test_type: Optional[str] = None) -> QuerySet[AssessmentTest]:
    """Retrieve available assessment tests."""
    qs = AssessmentTest.objects.filter(is_active=True).select_related("created_by")
    if test_type:
        qs = qs.filter(test_type=test_type)
    return qs


def get_student_attempts(
    student_id: Optional[str] = None,
    test_id: Optional[str] = None,
) -> QuerySet[StudentAssessmentAttempt]:
    """Retrieve student assessment attempt records."""
    qs = StudentAssessmentAttempt.objects.select_related("student__user", "test").all()
    if student_id:
        qs = qs.filter(student_id=student_id)
    if test_id:
        qs = qs.filter(test_id=test_id)
    return qs


def get_training_sessions(
    session_type: Optional[str] = None,
    is_completed: Optional[bool] = None,
) -> QuerySet[TrainingSession]:
    """Retrieve training and corporate grooming workshop sessions."""
    qs = TrainingSession.objects.select_related("trainer").all()
    if session_type:
        qs = qs.filter(session_type=session_type)
    if is_completed is not None:
        qs = qs.filter(is_completed=is_completed)
    return qs


def get_mock_interviews(
    student_id: Optional[str] = None,
    evaluator_id: Optional[str] = None,
    status: Optional[str] = None,
) -> QuerySet[MockInterview]:
    """Retrieve mock interview schedules."""
    qs = MockInterview.objects.select_related("student__user", "evaluator", "scheduled_by", "evaluation").all()
    if student_id:
        qs = qs.filter(student_id=student_id)
    if evaluator_id:
        qs = qs.filter(evaluator_id=evaluator_id)
    if status:
        qs = qs.filter(status=status)
    return qs


def get_placement_certifications(
    student_id: Optional[str] = None,
    is_approved: Optional[bool] = None,
) -> QuerySet[PlacementReadinessCertification]:
    """Retrieve placement readiness certification records."""
    qs = PlacementReadinessCertification.objects.select_related("student__user", "approved_resume", "certified_by").all()
    if student_id:
        qs = qs.filter(student_id=student_id)
    if is_approved is not None:
        qs = qs.filter(is_approved_for_placements=is_approved)
    return qs


def get_student_readiness_snapshot(student_id: str) -> Dict[str, Any]:
    """Compile comprehensive readiness snapshot across Steps 15-23 for Placement Head review."""
    student = StudentProfile.objects.select_related("user").get(id=student_id)
    latest_resume = student.current_resume

    # 1. Resume Review Status (Step 15/16)
    latest_review = ResumeReview.objects.filter(student=student).order_by("-reviewed_at").first()
    has_approved_review = latest_review is not None and latest_review.status == ResumeReviewStatus.APPROVED

    # 2. Aptitude Assessment Status (Step 17)
    aptitude_attempt = (
        StudentAssessmentAttempt.objects.filter(
            student=student,
            test__test_type=AssessmentTestType.APTITUDE,
            status=AssessmentAttemptStatus.COMPLETED,
        )
        .order_by("-percentage")
        .first()
    )
    passed_aptitude = aptitude_attempt is not None and aptitude_attempt.passed

    # 3. Technical Assessment Status (Step 18)
    technical_attempt = (
        StudentAssessmentAttempt.objects.filter(
            student=student,
            test__test_type=AssessmentTestType.TECHNICAL,
            status=AssessmentAttemptStatus.COMPLETED,
        )
        .order_by("-percentage")
        .first()
    )
    passed_technical = technical_attempt is not None and technical_attempt.passed

    # 4. Communication Skills Attendance (Step 19)
    comm_attendance = TrainingAttendance.objects.filter(
        student=student,
        session__session_type="COMMUNICATION",
        attendance_status=AttendanceStatus.ATTENDED,
    ).first()
    attended_communication = comm_attendance is not None

    # 5. Corporate Grooming Certification (Step 20)
    grooming_attendance = TrainingAttendance.objects.filter(
        student=student,
        grooming_certified=True,
    ).first()
    grooming_certified = grooming_attendance is not None

    # 6. Mock Interview & Scorecard (Steps 21 & 22)
    mock_eval = (
        MockInterviewEvaluation.objects.filter(mock_interview__student=student)
        .select_related("mock_interview")
        .order_by("-evaluated_at")
        .first()
    )
    mock_completed = mock_eval is not None
    mock_ready = mock_eval is not None and mock_eval.readiness_recommendation == MockReadinessRecommendation.READY_FOR_PLACEMENTS

    # 7. Final Placement Readiness Certification Gate (Step 23)
    latest_cert = (
        PlacementReadinessCertification.objects.filter(student=student)
        .order_by("-certified_at")
        .first()
    )
    is_placement_certified = latest_cert is not None and latest_cert.is_approved_for_placements

    all_criteria_met = (
        has_approved_review
        and passed_aptitude
        and passed_technical
        and attended_communication
        and grooming_certified
        and mock_ready
    )

    return {
        "student_id": str(student.id),
        "student_name": student.user.full_name,
        "roll_number": student.roll_number,
        "department": student.department,
        "current_resume_id": str(latest_resume.id) if latest_resume else None,
        "current_resume_version": latest_resume.version_number if latest_resume else None,
        "criteria": {
            "resume_review_approved": has_approved_review,
            "resume_review_id": str(latest_review.id) if latest_review else None,
            "aptitude_assessment_passed": passed_aptitude,
            "aptitude_score": aptitude_attempt.score if aptitude_attempt else None,
            "technical_assessment_passed": passed_technical,
            "technical_score": technical_attempt.score if technical_attempt else None,
            "communication_attended": attended_communication,
            "grooming_certified": grooming_certified,
            "mock_interview_completed": mock_completed,
            "mock_interview_ready": mock_ready,
            "mock_total_score": mock_eval.total_score if mock_eval else None,
        },
        "all_criteria_met": all_criteria_met,
        "is_placement_certified": is_placement_certified,
        "current_certification": {
            "is_approved_for_placements": latest_cert.is_approved_for_placements,
            "status": latest_cert.status,
            "certified_by": latest_cert.certified_by.full_name,
            "certified_at": latest_cert.certified_at.isoformat(),
            "notes": latest_cert.notes,
        } if latest_cert else None,
    }
