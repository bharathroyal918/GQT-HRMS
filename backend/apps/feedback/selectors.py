"""Optimized queries and permission-scoped selectors for Feedback Collection."""
from typing import Any, Dict, Optional
from django.db.models import Avg, Count, Q, QuerySet
from apps.accounts.models import RoleCatalog
from apps.crm.models import Company
from apps.feedback.models import HRFeedback, StudentFeedback, TrainerFeedback
from apps.feedback.permissions import HR_FEEDBACK_MANAGE_ROLES, STAFF_VIEW_ROLES, TRAINER_FEEDBACK_MANAGE_ROLES, get_user_roles
from apps.interviews.models import InterviewSchedule
from apps.students.models import StudentProfile


def get_student_feedback_queryset(user, filters: Optional[Dict[str, Any]] = None) -> QuerySet[StudentFeedback]:
    """Retrieve StudentFeedback queryset scoped by user role with optimized relation loading."""
    qs = StudentFeedback.objects.select_related(
        "student__user",
        "company",
        "job_requirement",
        "interview_schedule",
        "interview_round",
        "submitted_by",
    ).all()

    if user.is_superuser:
        pass
    else:
        roles = get_user_roles(user)
        if RoleCatalog.STUDENT in roles and not bool(roles & STAFF_VIEW_ROLES):
            qs = qs.filter(student__user=user)
        elif not bool(roles & STAFF_VIEW_ROLES):
            return StudentFeedback.objects.none()

    if filters:
        if filters.get("company"):
            qs = qs.filter(company_id=filters["company"])
        if filters.get("difficulty"):
            qs = qs.filter(difficulty=filters["difficulty"])
        if filters.get("job_requirement"):
            qs = qs.filter(job_requirement_id=filters["job_requirement"])
        if filters.get("search"):
            query = filters["search"]
            qs = qs.filter(
                Q(company__name__icontains=query)
                | Q(technical_questions__icontains=query)
                | Q(interview_experience__icontains=query)
            )

    return qs


def get_hr_feedback_queryset(user, filters: Optional[Dict[str, Any]] = None) -> QuerySet[HRFeedback]:
    """Retrieve HRFeedback queryset scoped by user role with optimized relation loading."""
    qs = HRFeedback.objects.select_related(
        "company",
        "hr_contact",
        "job_requirement",
        "candidate__user",
        "submitted_by",
    ).all()

    if user.is_superuser:
        pass
    else:
        roles = get_user_roles(user)
        if RoleCatalog.STUDENT in roles and not bool(roles & STAFF_VIEW_ROLES):
            # Students are strictly denied viewing HR feedback
            return HRFeedback.objects.none()
        if RoleCatalog.HR_RELATIONSHIP_MGR in roles and not bool(roles & STAFF_VIEW_ROLES):
            # Scoped to assigned companies / contacts
            qs = qs.filter(
                Q(company__owner=user)
                | Q(hr_contact__owner=user)
                | Q(submitted_by=user)
            )
        elif not bool(roles & (STAFF_VIEW_ROLES | HR_FEEDBACK_MANAGE_ROLES)):
            return HRFeedback.objects.none()

    if filters:
        if filters.get("company"):
            qs = qs.filter(company_id=filters["company"])
        if filters.get("candidate_quality"):
            qs = qs.filter(candidate_quality=filters["candidate_quality"])
        if filters.get("job_requirement"):
            qs = qs.filter(job_requirement_id=filters["job_requirement"])
        if filters.get("candidate"):
            qs = qs.filter(candidate_id=filters["candidate"])
        if filters.get("search"):
            query = filters["search"]
            qs = qs.filter(
                Q(company__name__icontains=query)
                | Q(candidate_quality_remarks__icontains=query)
                | Q(hiring_satisfaction_remarks__icontains=query)
            )

    return qs


def get_trainer_feedback_queryset(user, filters: Optional[Dict[str, Any]] = None) -> QuerySet[TrainerFeedback]:
    """Retrieve TrainerFeedback queryset scoped by user role with optimized relation loading."""
    qs = TrainerFeedback.objects.select_related(
        "student__user",
        "training_session",
        "trainer",
    ).all()

    if user.is_superuser:
        pass
    else:
        roles = get_user_roles(user)
        if RoleCatalog.STUDENT in roles and not bool(roles & STAFF_VIEW_ROLES):
            return TrainerFeedback.objects.none()
        if (RoleCatalog.TRAINER in roles or RoleCatalog.EVALUATOR in roles) and not bool(roles & STAFF_VIEW_ROLES):
            qs = qs.filter(trainer=user)
        elif not bool(roles & (STAFF_VIEW_ROLES | TRAINER_FEEDBACK_MANAGE_ROLES)):
            return TrainerFeedback.objects.none()

    if filters:
        if filters.get("student"):
            qs = qs.filter(student_id=filters["student"])
        if filters.get("student_readiness"):
            qs = qs.filter(student_readiness=filters["student_readiness"])
        if filters.get("training_session"):
            qs = qs.filter(training_session_id=filters["training_session"])
        if filters.get("search"):
            query = filters["search"]
            qs = qs.filter(
                Q(student__user__first_name__icontains=query)
                | Q(student__user__last_name__icontains=query)
                | Q(student__roll_number__icontains=query)
                | Q(areas_for_improvement__icontains=query)
            )

    return qs


def get_feedback_kpis(user) -> Dict[str, Any]:
    """Aggregate high-level KPIs across feedback categories visible to the authenticated user."""
    student_qs = get_student_feedback_queryset(user)
    hr_qs = get_hr_feedback_queryset(user)
    trainer_qs = get_trainer_feedback_queryset(user)

    hr_aggregates = hr_qs.aggregate(
        avg_technical=Avg("technical_skills_rating"),
        avg_communication=Avg("communication_skills_rating"),
        avg_satisfaction=Avg("hiring_satisfaction_rating"),
    )

    trainer_aggregates = trainer_qs.aggregate(
        avg_effectiveness=Avg("training_effectiveness_rating")
    )

    difficulty_counts = dict(
        student_qs.values("difficulty").annotate(count=Count("id")).values_list("difficulty", "count")
    )

    readiness_counts = dict(
        trainer_qs.values("student_readiness").annotate(count=Count("id")).values_list("student_readiness", "count")
    )

    return {
        "total_student_feedback": student_qs.count(),
        "total_hr_feedback": hr_qs.count(),
        "total_trainer_feedback": trainer_qs.count(),
        "avg_technical_skills_rating": round(hr_aggregates["avg_technical"] or 0.0, 2),
        "avg_communication_skills_rating": round(hr_aggregates["avg_communication"] or 0.0, 2),
        "avg_hiring_satisfaction_rating": round(hr_aggregates["avg_satisfaction"] or 0.0, 2),
        "avg_training_effectiveness_rating": round(trainer_aggregates["avg_effectiveness"] or 0.0, 2),
        "difficulty_breakdown": difficulty_counts,
        "readiness_breakdown": readiness_counts,
    }


def get_student_eligible_interview_drives(user) -> QuerySet[InterviewSchedule]:
    """Retrieve distinct scheduled interview drives for the authenticated student candidate."""
    if not hasattr(user, "student_profile"):
        return InterviewSchedule.objects.none()

    return (
        InterviewSchedule.objects.filter(student=user.student_profile)
        .select_related("job_requirement__company", "job_requirement")
        .order_by("-interview_date")
    )
