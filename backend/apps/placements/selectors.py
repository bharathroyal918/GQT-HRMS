"""Placement Management Selectors.

Encapsulates permission-filtered, optimized read operations for final results, candidate placement statuses,
offer letters, acceptance states, and joining verifications.
"""
from typing import Optional, List, Dict, Any
from django.db.models import QuerySet, Q, Count
from django.contrib.auth import get_user_model
from apps.placements.models import (
    FinalResultIntake,
    CandidatePlacementStatus,
    CandidateOfferLetter,
    CandidatePlacementStatusChoices,
    OfferAcceptanceStatus,
    JoiningStatus,
)
from apps.students.models import StudentProfile
from apps.jobs.models import JobRequirement
from apps.submissions.models import CandidateSubmission
from apps.interviews.models import ShortlistedCandidate

User = get_user_model()


def get_final_result_intakes(
    job_id: Optional[str] = None,
    company_id: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[FinalResultIntake]:
    """Return filtered query set of final result intake batches."""
    qs = FinalResultIntake.objects.select_related(
        "job_requirement", "company", "hr_contact", "created_by"
    ).all()

    if job_id:
        qs = qs.filter(job_requirement_id=job_id)
    if company_id:
        qs = qs.filter(company_id=company_id)
    if search:
        search = search.strip()
        qs = qs.filter(
            Q(result_reference_code__icontains=search)
            | Q(company__name__icontains=search)
            | Q(job_requirement__title__icontains=search)
        )
    return qs


def get_final_result_intake_by_id(intake_id: str) -> Optional[FinalResultIntake]:
    """Retrieve a single final result intake batch with all related objects."""
    return (
        FinalResultIntake.objects.select_related(
            "job_requirement", "company", "hr_contact", "created_by"
        )
        .prefetch_related("candidate_results__student__user")
        .filter(id=intake_id)
        .first()
    )


def get_candidate_placement_statuses(
    job_id: Optional[str] = None,
    company_id: Optional[str] = None,
    student_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[CandidatePlacementStatus]:
    """Return filtered candidate placement decision statuses."""
    qs = (
        CandidatePlacementStatus.objects.select_related(
            "intake",
            "job_requirement",
            "company",
            "student",
            "student__user",
            "status_updated_by",
        )
        .prefetch_related("history", "offer_letter")
        .all()
    )

    if job_id:
        qs = qs.filter(job_requirement_id=job_id)
    if company_id:
        qs = qs.filter(company_id=company_id)
    if student_id:
        qs = qs.filter(student_id=student_id)
    if status:
        qs = qs.filter(status=status)
    if search:
        search = search.strip()
        qs = qs.filter(
            Q(student__roll_number__icontains=search)
            | Q(student__user__full_name__icontains=search)
            | Q(student__institutional_email__icontains=search)
            | Q(company__name__icontains=search)
            | Q(job_requirement__title__icontains=search)
        )
    return qs


def get_candidate_placement_status_by_id(placement_id: str) -> Optional[CandidatePlacementStatus]:
    """Retrieve an individual candidate placement record with history and offer letter."""
    return (
        CandidatePlacementStatus.objects.select_related(
            "intake",
            "job_requirement",
            "company",
            "student",
            "student__user",
            "status_updated_by",
        )
        .prefetch_related("history__changed_by", "offer_letter", "notification_logs__sent_by")
        .filter(id=placement_id)
        .first()
    )


def get_candidate_offer_letters(
    job_id: Optional[str] = None,
    company_id: Optional[str] = None,
    student_id: Optional[str] = None,
    acceptance_status: Optional[str] = None,
    joining_status: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[CandidateOfferLetter]:
    """Return filtered candidate offer letters."""
    qs = (
        CandidateOfferLetter.objects.select_related(
            "placement_status",
            "student",
            "student__user",
            "job_requirement",
            "company",
            "issued_by",
            "acceptance_recorded_by",
            "joining_verified_by",
        )
        .prefetch_related("versions", "joining_history")
        .filter(is_active=True)
    )

    if job_id:
        qs = qs.filter(job_requirement_id=job_id)
    if company_id:
        qs = qs.filter(company_id=company_id)
    if student_id:
        qs = qs.filter(student_id=student_id)
    if acceptance_status:
        qs = qs.filter(acceptance_status=acceptance_status)
    if joining_status:
        qs = qs.filter(joining_status=joining_status)
    if search:
        search = search.strip()
        qs = qs.filter(
            Q(student__roll_number__icontains=search)
            | Q(student__user__full_name__icontains=search)
            | Q(student__institutional_email__icontains=search)
            | Q(company__name__icontains=search)
            | Q(job_requirement__title__icontains=search)
        )
    return qs


def get_offer_letter_by_id(offer_id: str) -> Optional[CandidateOfferLetter]:
    """Retrieve a single candidate offer letter by ID."""
    return (
        CandidateOfferLetter.objects.select_related(
            "placement_status",
            "student",
            "student__user",
            "job_requirement",
            "company",
            "issued_by",
            "acceptance_recorded_by",
            "joining_verified_by",
        )
        .prefetch_related("versions__superseded_by", "joining_history__changed_by")
        .filter(id=offer_id)
        .first()
    )


def get_student_placement_records(user: User) -> List[Dict[str, Any]]:
    """Return placement decision records and active offers belonging to the authenticated student."""
    profile = getattr(user, "student_profile", None)
    if not profile:
        return []

    return (
        CandidatePlacementStatus.objects.select_related(
            "job_requirement", "company", "intake", "offer_letter"
        )
        .prefetch_related("notification_logs")
        .filter(student=profile)
        .order_by("-created_at")
    )


def get_participated_candidates_for_job(job_requirement_id: str) -> List[Dict[str, Any]]:
    """Return distinct candidates who participated in the drive (submitted or shortlisted)."""
    # 1. Candidates submitted
    submitted_students = StudentProfile.objects.filter(
        candidate_submissions__package__job_requirement_id=job_requirement_id
    ).select_related("user")

    # 2. Candidates shortlisted
    shortlisted_students = StudentProfile.objects.filter(
        interview_schedules__job_requirement_id=job_requirement_id
    ).select_related("user")

    all_students = (submitted_students | shortlisted_students).distinct()

    results = []
    # Check if placement status already exists for this job
    existing_statuses = {
        ps.student_id: ps.status
        for ps in CandidatePlacementStatus.objects.filter(job_requirement_id=job_requirement_id)
    }

    for s in all_students:
        results.append({
            "student_id": str(s.id),
            "roll_number": s.roll_number,
            "student_name": s.user.full_name,
            "institutional_email": s.institutional_email,
            "department": s.department,
            "degree": s.degree,
            "cgpa": float(s.cgpa) if s.cgpa else None,
            "existing_placement_status": existing_statuses.get(s.id),
        })
    return results


def get_placement_kpis() -> Dict[str, int]:
    """Compute high-level KPIs for placement management workspace."""
    results = CandidatePlacementStatus.objects.all()
    offers = CandidateOfferLetter.objects.filter(is_active=True)

    total_results = results.count()
    selected_count = results.filter(status=CandidatePlacementStatusChoices.SELECTED).count()
    rejected_count = results.filter(status=CandidatePlacementStatusChoices.REJECTED).count()
    waiting_list_count = results.filter(status=CandidatePlacementStatusChoices.WAITING_LIST).count()
    hold_count = results.filter(status=CandidatePlacementStatusChoices.HOLD).count()

    total_offers = offers.count()
    offers_accepted = offers.filter(acceptance_status=OfferAcceptanceStatus.ACCEPTED).count()
    offers_declined = offers.filter(acceptance_status=OfferAcceptanceStatus.DECLINED).count()
    offers_pending = offers.filter(acceptance_status=OfferAcceptanceStatus.PENDING_RESPONSE).count()

    total_joined = offers.filter(joining_status=JoiningStatus.JOINED).count()
    total_deferred = offers.filter(joining_status=JoiningStatus.DEFERRED).count()
    total_not_joined = offers.filter(joining_status=JoiningStatus.NOT_JOINED).count()

    return {
        "total_results": total_results,
        "selected_count": selected_count,
        "rejected_count": rejected_count,
        "waiting_list_count": waiting_list_count,
        "hold_count": hold_count,
        "total_offers": total_offers,
        "offers_accepted": offers_accepted,
        "offers_declined": offers_declined,
        "offers_pending": offers_pending,
        "total_joined": total_joined,
        "total_deferred": total_deferred,
        "total_not_joined": total_not_joined,
    }
