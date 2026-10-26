"""Query selectors for Job Requirements & Verification (Phase 3)."""
from typing import Any, Dict, Optional
from django.db.models import Count, Q, QuerySet
from django.utils import timezone
from apps.jobs.models import (
    ChecklistItemStatus,
    JobChecklistItem,
    JobRequirement,
    JobRequirementStatus,
)

SAFE_ORDERING_FIELDS = {
    "-created_at": "-created_at",
    "created_at": "created_at",
    "-registration_deadline": "-registration_deadline",
    "registration_deadline": "registration_deadline",
    "title": "title",
    "-title": "-title",
    "company__name": "company__name",
    "-company__name": "-company__name",
    "status": "status",
    "-status": "-status",
}


def get_jobs_queryset(
    filters: Optional[Dict[str, Any]] = None,
    ordering: str = "-created_at",
    include_archived: bool = False,
) -> QuerySet[JobRequirement]:
    """Retrieve filtered, ordered, and optimized queryset of job requirements."""
    filters = filters or {}
    qs = JobRequirement.objects.select_related(
        "company",
        "hr_contact",
        "created_by",
        "assigned_verifier",
        "verified_by",
        "approved_by",
    ).prefetch_related("checklist_items")

    if not include_archived:
        qs = qs.filter(is_archived=False)

    company_id = filters.get("company_id")
    if company_id:
        qs = qs.filter(company_id=company_id)

    status = filters.get("status")
    if status:
        qs = qs.filter(status=status)

    employment_type = filters.get("employment_type")
    if employment_type:
        qs = qs.filter(employment_type=employment_type)

    work_arrangement = filters.get("work_arrangement")
    if work_arrangement:
        qs = qs.filter(work_arrangement=work_arrangement)

    search = filters.get("search")
    if search:
        search = search.strip()
        qs = qs.filter(
            Q(title__icontains=search)
            | Q(skills_required__icontains=search)
            | Q(location__icontains=search)
            | Q(company__name__icontains=search)
        )

    assigned_verifier_id = filters.get("assigned_verifier_id")
    if assigned_verifier_id:
        qs = qs.filter(assigned_verifier_id=assigned_verifier_id)

    created_by_id = filters.get("created_by_id")
    if created_by_id:
        qs = qs.filter(created_by_id=created_by_id)

    safe_order = SAFE_ORDERING_FIELDS.get(ordering, "-created_at")
    return qs.order_by(safe_order)


def get_job_by_id(job_id: str, include_archived: bool = True) -> Optional[JobRequirement]:
    """Fetch single job requirement with related entities, checklist, and decisions."""
    qs = JobRequirement.objects.select_related(
        "company",
        "hr_contact",
        "created_by",
        "assigned_verifier",
        "verified_by",
        "approved_by",
    ).prefetch_related(
        "checklist_items",
        "decisions__actor",
    )
    if not include_archived:
        qs = qs.filter(is_archived=False)
    return qs.filter(id=job_id).first()


def get_pending_verifications_queryset() -> QuerySet[JobRequirement]:
    """Retrieve jobs requiring checklist review (Step 6)."""
    return get_jobs_queryset(
        filters={"status__in": [JobRequirementStatus.PENDING_VERIFICATION, JobRequirementStatus.UNDER_REVIEW]},
        ordering="registration_deadline",
    ).filter(
        status__in=[JobRequirementStatus.PENDING_VERIFICATION, JobRequirementStatus.UNDER_REVIEW]
    )


def get_pending_approvals_queryset() -> QuerySet[JobRequirement]:
    """Retrieve verified opportunities awaiting Placement Head sign-off (Step 7)."""
    return get_jobs_queryset(
        filters={"status": JobRequirementStatus.VERIFIED},
        ordering="registration_deadline",
    )


def get_job_metrics() -> Dict[str, Any]:
    """Aggregate permission-safe operational metrics across job requirement lifecycle."""
    now = timezone.now()
    seven_days = now + timezone.timedelta(days=7)

    base = JobRequirement.objects.filter(is_archived=False)
    counts = base.aggregate(
        total_active=Count("id"),
        draft_count=Count("id", filter=Q(status=JobRequirementStatus.DRAFT)),
        pending_verification_count=Count(
            "id", filter=Q(status=JobRequirementStatus.PENDING_VERIFICATION)
        ),
        under_review_count=Count("id", filter=Q(status=JobRequirementStatus.UNDER_REVIEW)),
        changes_requested_count=Count(
            "id", filter=Q(status=JobRequirementStatus.CHANGES_REQUESTED)
        ),
        verified_count=Count("id", filter=Q(status=JobRequirementStatus.VERIFIED)),
        approved_count=Count("id", filter=Q(status=JobRequirementStatus.APPROVED)),
        rejected_count=Count("id", filter=Q(status=JobRequirementStatus.REJECTED)),
        deadlines_approaching_count=Count(
            "id",
            filter=Q(
                registration_deadline__gte=now,
                registration_deadline__lte=seven_days,
                status__in=[
                    JobRequirementStatus.VERIFIED,
                    JobRequirementStatus.APPROVED,
                ],
            ),
        ),
    )
    return counts
