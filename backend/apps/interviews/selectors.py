"""Reusable, permission-aware query selectors for Interview Management & Tracking."""
from datetime import date
from typing import Optional, List
from django.db.models import QuerySet, Count, Q
from django.utils import timezone
from apps.interviews.models import (
    CandidateShortlist,
    ShortlistedCandidate,
    InterviewSchedule,
    InterviewRound,
    HRInterviewFollowUp,
    InterviewReminder,
    ScheduleStatus,
    AttendanceStatus,
    ConductedStatus,
    ReminderStatus,
)
from apps.submissions.models import CandidateSubmission, SubmissionPackageStatus
from apps.students.models import StudentProfile


def get_shortlists(
    job_id: Optional[str] = None,
    company_id: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[CandidateShortlist]:
    """Retrieve corporate HR candidate shortlists with selective filters."""
    qs = CandidateShortlist.objects.select_related(
        "job_requirement",
        "company",
        "hr_contact",
        "submission_package",
        "created_by",
    ).prefetch_related("candidates__student__user")

    if job_id:
        qs = qs.filter(job_requirement_id=job_id)
    if company_id:
        qs = qs.filter(company_id=company_id)
    if search:
        qs = qs.filter(
            Q(shortlist_reference_code__icontains=search)
            | Q(company__name__icontains=search)
            | Q(job_requirement__title__icontains=search)
            | Q(notes__icontains=search)
        )
    return qs.order_by("-received_at")


def get_shortlist_by_id(shortlist_id: str) -> Optional[CandidateShortlist]:
    """Retrieve a single CandidateShortlist with candidates and submissions loaded."""
    try:
        return (
            CandidateShortlist.objects.select_related(
                "job_requirement",
                "company",
                "hr_contact",
                "submission_package",
                "created_by",
            )
            .prefetch_related(
                "candidates__student__user",
                "candidates__submission",
                "candidates__schedules",
            )
            .get(id=shortlist_id)
        )
    except (CandidateShortlist.DoesNotExist, ValueError):
        return None


def get_eligible_submissions_for_shortlist(job_id: str) -> List[dict]:
    """Retrieve submitted candidates from dispatched submission packages for a job."""
    submissions = (
        CandidateSubmission.objects.filter(
            package__job_requirement_id=job_id,
            package__status__in=[
                SubmissionPackageStatus.DISPATCHED,
                SubmissionPackageStatus.ACKNOWLEDGED,
            ],
        )
        .select_related("student__user", "package")
        .order_by("student__roll_number")
    )

    already_shortlisted_ids = set(
        ShortlistedCandidate.objects.filter(
            shortlist__job_requirement_id=job_id
        ).values_list("student_id", flat=True)
    )

    results = []
    for sub in submissions:
        student = sub.student
        results.append({
            "submission_id": str(sub.id),
            "package_id": str(sub.package_id),
            "package_title": sub.package.title,
            "student_id": str(student.id),
            "roll_number": student.roll_number,
            "full_name": student.user.full_name,
            "email": student.user.email,
            "phone_number": student.phone_number,
            "department": student.department,
            "degree": student.degree,
            "cgpa": float(student.cgpa) if student.cgpa else 0.0,
            "submission_status": sub.status,
            "is_already_shortlisted": student.id in already_shortlisted_ids,
        })
    return results


def get_interview_schedules(
    job_id: Optional[str] = None,
    company_id: Optional[str] = None,
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    attendance_status: Optional[str] = None,
    conducted_status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    search: Optional[str] = None,
) -> QuerySet[InterviewSchedule]:
    """Retrieve interview schedules with comprehensive multi-criteria filtering."""
    qs = InterviewSchedule.objects.select_related(
        "job_requirement",
        "company",
        "candidate__shortlist",
        "student__user",
        "created_by",
        "attendance_confirmed_by",
        "conducted_recorded_by",
        "rescheduled_from",
    ).prefetch_related(
        "reminders",
        "notification_logs",
        "rounds",
    )

    if job_id:
        qs = qs.filter(job_requirement_id=job_id)
    if company_id:
        qs = qs.filter(company_id=company_id)
    if student_id:
        qs = qs.filter(student_id=student_id)
    if status:
        qs = qs.filter(status=status)
    if attendance_status:
        qs = qs.filter(attendance_status=attendance_status)
    if conducted_status:
        qs = qs.filter(conducted_status=conducted_status)
    if date_from:
        qs = qs.filter(interview_date__gte=date_from)
    if date_to:
        qs = qs.filter(interview_date__lte=date_to)
    if search:
        qs = qs.filter(
            Q(schedule_reference_code__icontains=search)
            | Q(student__roll_number__icontains=search)
            | Q(student__user__first_name__icontains=search)
            | Q(student__user__last_name__icontains=search)
            | Q(venue__icontains=search)
        )
    return qs.order_by("scheduled_start_time")


def get_interview_schedule_by_id(schedule_id: str) -> Optional[InterviewSchedule]:
    """Retrieve an InterviewSchedule by UUID with full relations."""
    try:
        return (
            InterviewSchedule.objects.select_related(
                "job_requirement",
                "company",
                "candidate__shortlist",
                "student__user",
                "created_by",
                "attendance_confirmed_by",
                "conducted_recorded_by",
                "rescheduled_from",
            )
            .prefetch_related(
                "reminders",
                "notification_logs",
                "rounds",
            )
            .get(id=schedule_id)
        )
    except (InterviewSchedule.DoesNotExist, ValueError):
        return None


def get_student_interview_schedules(student_profile: StudentProfile) -> QuerySet[InterviewSchedule]:
    """Retrieve student's personal interview schedules, hiding superseded versions."""
    return (
        InterviewSchedule.objects.filter(
            student=student_profile,
            is_superseded=False,
        )
        .select_related("job_requirement", "company")
        .prefetch_related("reminders")
        .order_by("scheduled_start_time")
    )


def get_due_reminders(reference_time: Optional[timezone.datetime] = None) -> QuerySet[InterviewReminder]:
    """Retrieve scheduled reminders ready for transmission."""
    now = reference_time or timezone.now()
    return (
        InterviewReminder.objects.filter(
            status=ReminderStatus.SCHEDULED,
            scheduled_for__lte=now,
            schedule__status=ScheduleStatus.SCHEDULED,
            schedule__is_superseded=False,
        )
        .select_related(
            "schedule__student__user",
            "schedule__job_requirement",
            "schedule__company",
        )
        .order_by("scheduled_for")
    )


def get_interview_rounds(
    candidate_id: Optional[str] = None,
    job_id: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
) -> QuerySet[InterviewRound]:
    """Retrieve interview rounds with filtering."""
    qs = InterviewRound.objects.select_related(
        "job_requirement",
        "company",
        "candidate__student__user",
        "schedule",
        "evaluated_by",
        "created_by",
    )

    if candidate_id:
        qs = qs.filter(candidate_id=candidate_id)
    if job_id:
        qs = qs.filter(job_requirement_id=job_id)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("candidate", "round_number")


def get_hr_follow_ups(
    job_id: Optional[str] = None,
    company_id: Optional[str] = None,
    overdue_only: bool = False,
    search: Optional[str] = None,
) -> QuerySet[HRInterviewFollowUp]:
    """Retrieve HR interview follow-up touchpoints."""
    qs = HRInterviewFollowUp.objects.select_related(
        "job_requirement",
        "company",
        "hr_contact",
        "conducted_by",
    )

    if job_id:
        qs = qs.filter(job_requirement_id=job_id)
    if company_id:
        qs = qs.filter(company_id=company_id)
    if overdue_only:
        today = timezone.localdate()
        qs = qs.filter(next_follow_up_date__lt=today)
    if search:
        qs = qs.filter(
            Q(candidate_status_reported__icontains=search)
            | Q(pending_rounds__icontains=search)
            | Q(hr_response_summary__icontains=search)
            | Q(company__name__icontains=search)
        )
    return qs.order_by("-follow_up_date")


def get_interview_kpis() -> dict:
    """Aggregate high-level operational metrics for the Interview Management workspace."""
    total_shortlists = CandidateShortlist.objects.count()
    total_shortlisted_candidates = ShortlistedCandidate.objects.count()
    total_schedules = InterviewSchedule.objects.filter(is_superseded=False).count()
    confirmed_attendance = InterviewSchedule.objects.filter(
        is_superseded=False, attendance_status=AttendanceStatus.CONFIRMED
    ).count()
    interviews_conducted = InterviewSchedule.objects.filter(
        is_superseded=False, conducted_status=ConductedStatus.CONDUCTED
    ).count()
    pending_hr_followups = HRInterviewFollowUp.objects.filter(
        next_follow_up_date__gte=timezone.localdate()
    ).count()

    return {
        "total_shortlists": total_shortlists,
        "total_shortlisted_candidates": total_shortlisted_candidates,
        "total_schedules": total_schedules,
        "confirmed_attendance": confirmed_attendance,
        "interviews_conducted": interviews_conducted,
        "pending_hr_followups": pending_hr_followups,
    }
