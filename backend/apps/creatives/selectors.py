"""Read/Query Selectors for Creative Studio (Phase 4).

Follows strict 5-layer architecture. Zero mutations occur in selectors.
"""
from datetime import timedelta
from typing import Optional, Dict, Any
from django.db.models import QuerySet, Q, Count
from django.utils import timezone
from apps.accounts.models import User, RoleCatalog
from apps.creatives.models import (
    CreativeRequest,
    CreativeRequestStatus,
    CreativeAssetVersion,
)


def get_creative_requests_queryset(
    user: Optional[User] = None,
    company_id: Optional[str] = None,
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    deliverable_type: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_designer_id: Optional[str] = None,
    search: Optional[str] = None,
    include_archived: bool = False,
    ordering: str = "-created_at",
) -> QuerySet[CreativeRequest]:
    """Retrieve filtered, prefetched creative production requests."""
    qs = CreativeRequest.objects.select_related(
        "job_requirement",
        "job_requirement__company",
        "assigned_designer",
        "created_by",
    ).prefetch_related(
        "versions",
        "versions__checklist_items",
        "decisions",
    )

    if not include_archived:
        qs = qs.filter(is_archived=False)

    # Role-based scoping: If user only has CREATIVE_DESIGNER role, limit to requests assigned to them
    if user and not user.is_superuser:
        user_roles = set(user.get_active_roles())
        staff_supervisors = {RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER, RoleCatalog.AUDITOR}
        if RoleCatalog.CREATIVE_DESIGNER in user_roles and not (user_roles & staff_supervisors):
            qs = qs.filter(Q(assigned_designer=user) | Q(assigned_designer__isnull=True))

    if company_id:
        qs = qs.filter(job_requirement__company_id=company_id)

    if job_id:
        qs = qs.filter(job_requirement_id=job_id)

    if status:
        qs = qs.filter(status=status)

    if deliverable_type:
        qs = qs.filter(deliverable_type=deliverable_type)

    if priority:
        qs = qs.filter(priority=priority)

    if assigned_designer_id:
        qs = qs.filter(assigned_designer_id=assigned_designer_id)

    if search:
        search_terms = search.strip().split()
        for term in search_terms:
            qs = qs.filter(
                Q(title__icontains=term)
                | Q(brief__icontains=term)
                | Q(job_requirement__title__icontains=term)
                | Q(job_requirement__company__name__icontains=term)
            )

    valid_orderings = {
        "-created_at", "created_at",
        "-production_deadline", "production_deadline",
        "-priority", "priority",
        "status", "-status",
        "title", "-title",
    }
    safe_order = ordering if ordering in valid_orderings else "-created_at"
    return qs.order_by(safe_order)


def get_creative_request_by_id(request_id: str) -> Optional[CreativeRequest]:
    """Fetch single creative request with complete prefetching."""
    return (
        CreativeRequest.objects.select_related(
            "job_requirement",
            "job_requirement__company",
            "job_requirement__hr_contact",
            "assigned_designer",
            "created_by",
        )
        .prefetch_related(
            "versions",
            "versions__checklist_items",
            "versions__checklist_items__verified_by",
            "versions__uploaded_by",
            "versions__approved_by",
            "decisions",
            "decisions__actor",
        )
        .filter(id=request_id)
        .first()
    )


def get_asset_version_by_id(request_id: str, version_id: str) -> Optional[CreativeAssetVersion]:
    """Fetch single asset version with complete checklist prefetching."""
    return (
        CreativeAssetVersion.objects.select_related(
            "request",
            "request__job_requirement",
            "request__job_requirement__company",
            "uploaded_by",
            "approved_by",
        )
        .prefetch_related(
            "checklist_items",
            "checklist_items__verified_by",
            "decisions",
            "decisions__actor",
        )
        .filter(request_id=request_id, id=version_id)
        .first()
    )


def get_designer_queue_queryset(designer_user: User) -> QuerySet[CreativeRequest]:
    """Operational queue for a specific designer of their open and pending requests."""
    return (
        CreativeRequest.objects.select_related(
            "job_requirement",
            "job_requirement__company",
            "assigned_designer",
            "created_by",
        )
        .prefetch_related("versions", "versions__checklist_items")
        .filter(
            assigned_designer=designer_user,
            is_archived=False,
            status__in=[
                CreativeRequestStatus.ASSIGNED,
                CreativeRequestStatus.IN_PRODUCTION,
                CreativeRequestStatus.CHANGES_REQUESTED,
                CreativeRequestStatus.REVIEW_PENDING,
            ],
        )
        .order_by("production_deadline", "-created_at")
    )


def get_pending_review_queue_queryset() -> QuerySet[CreativeRequest]:
    """Operational queue of creative requests awaiting verification or Placement Head approval (Step 9)."""
    return (
        CreativeRequest.objects.select_related(
            "job_requirement",
            "job_requirement__company",
            "assigned_designer",
            "created_by",
        )
        .prefetch_related("versions", "versions__checklist_items")
        .filter(
            is_archived=False,
            status__in=[
                CreativeRequestStatus.REVIEW_PENDING,
                CreativeRequestStatus.IN_PRODUCTION,
                CreativeRequestStatus.CHANGES_REQUESTED,
            ],
        )
        .order_by("production_deadline", "-created_at")
    )


def get_creative_metrics() -> Dict[str, Any]:
    """Calculate aggregate KPI metrics for Creative Studio."""
    now = timezone.now()
    seven_days = now + timedelta(days=7)

    base = CreativeRequest.objects.filter(is_archived=False)

    total_active = base.exclude(status=CreativeRequestStatus.CANCELLED).count()
    draft = base.filter(status=CreativeRequestStatus.DRAFT).count()
    assigned = base.filter(status=CreativeRequestStatus.ASSIGNED).count()
    in_production = base.filter(status=CreativeRequestStatus.IN_PRODUCTION).count()
    review_pending = base.filter(status=CreativeRequestStatus.REVIEW_PENDING).count()
    changes_requested = base.filter(status=CreativeRequestStatus.CHANGES_REQUESTED).count()
    approved = base.filter(status=CreativeRequestStatus.APPROVED).count()
    urgent_deadlines = base.filter(
        production_deadline__isnull=False,
        production_deadline__lte=seven_days,
        production_deadline__gte=now,
    ).exclude(status__in=[CreativeRequestStatus.APPROVED, CreativeRequestStatus.CANCELLED]).count()

    return {
        "total_active": total_active,
        "draft": draft,
        "assigned": assigned,
        "in_production": in_production,
        "review_pending": review_pending,
        "changes_requested": changes_requested,
        "approved": approved,
        "urgent_deadlines_7_days": urgent_deadlines,
    }
