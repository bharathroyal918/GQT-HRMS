"""Selectors (read & query layer) for Corporate CRM & HR Directory."""
from datetime import datetime, time
from typing import Any, Dict, List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db.models import Count, Q, QuerySet
from django.utils import timezone

from apps.crm.models import (
    CRMConfiguration,
    Company,
    CompanyDomainCategory,
    CompanyRelationshipStatus,
    FollowUp,
    FollowUpStatus,
    HRContact,
    OutreachLog,
    extract_domain,
    normalize_company_name,
)

DEFAULT_DAILY_TARGET = 100


def get_daily_outreach_target() -> int:
    """Retrieve operational daily outreach target from configuration or fallback to 100."""
    config = CRMConfiguration.objects.filter(key="DAILY_OUTREACH_TARGET").first()
    if config:
        try:
            return int(config.value)
        except (ValueError, TypeError):
            pass
    return DEFAULT_DAILY_TARGET


def get_companies_queryset(
    *,
    search: Optional[str] = None,
    domain_category: Optional[str] = None,
    relationship_status: Optional[str] = None,
    tier: Optional[str] = None,
    city: Optional[str] = None,
    owner_id: Optional[str] = None,
    is_archived: Optional[bool] = False,
    ordering: Optional[str] = "name",
) -> QuerySet[Company]:
    """Retrieve optimized queryset for Corporate Companies with filtering and validation."""
    qs = Company.objects.filter(is_deleted=False).select_related("owner", "created_by", "updated_by")

    if is_archived is not None:
        qs = qs.filter(is_archived=is_archived)

    if domain_category:
        qs = qs.filter(domain_category=domain_category)

    if relationship_status:
        qs = qs.filter(relationship_status=relationship_status)

    if tier:
        qs = qs.filter(tier=tier)

    if city:
        qs = qs.filter(city__icontains=city)

    if owner_id:
        qs = qs.filter(owner_id=owner_id)

    if search:
        search_term = search.strip()
        qs = qs.filter(
            Q(name__icontains=search_term)
            | Q(domain__icontains=search_term)
            | Q(city__icontains=search_term)
        )

    # Safe ordering validation
    allowed_orderings = {
        "name": "name",
        "-name": "-name",
        "created_at": "created_at",
        "-created_at": "-created_at",
        "updated_at": "updated_at",
        "-updated_at": "-updated_at",
        "domain_category": "domain_category",
        "-domain_category": "-domain_category",
        "relationship_status": "relationship_status",
        "-relationship_status": "-relationship_status",
    }
    order_field = allowed_orderings.get(ordering, "name")
    return qs.order_by(order_field)


def get_company_by_id(company_id: UUID | str) -> Optional[Company]:
    """Fetch single company with pre-fetched contacts and relationships."""
    return (
        Company.objects.filter(id=company_id, is_deleted=False)
        .select_related("owner", "created_by", "updated_by")
        .prefetch_related("hr_contacts", "outreach_logs", "follow_ups")
        .first()
    )


def check_company_duplicates(name: str, website: Optional[str] = None) -> List[Dict[str, Any]]:
    """Cautiously evaluate potential duplicates based on normalized name and canonical domain.

    Does not automatically merge or delete records. Returns flagged candidate matches with explanations.
    """
    matches: List[Dict[str, Any]] = []
    seen_ids = set()

    norm_name = normalize_company_name(name)
    canon_domain = extract_domain(website) if website else ""

    if norm_name:
        # Match exact normalized name
        name_qs = Company.objects.filter(
            is_deleted=False,
            normalized_name=norm_name,
        ).values("id", "name", "domain", "relationship_status", "is_archived")

        for item in name_qs:
            seen_ids.add(str(item["id"]))
            matches.append({
                "company_id": item["id"],
                "name": item["name"],
                "domain": item["domain"],
                "relationship_status": item["relationship_status"],
                "is_archived": item["is_archived"],
                "match_type": "EXACT_NAME",
                "reason": f"Existing record has matching normalized company name: '{norm_name}'",
            })

    if canon_domain:
        # Match canonical corporate domain
        domain_qs = (
            Company.objects.filter(is_deleted=False, domain=canon_domain)
            .exclude(id__in=seen_ids)
            .values("id", "name", "domain", "relationship_status", "is_archived")
        )

        for item in domain_qs:
            seen_ids.add(str(item["id"]))
            matches.append({
                "company_id": item["id"],
                "name": item["name"],
                "domain": item["domain"],
                "relationship_status": item["relationship_status"],
                "is_archived": item["is_archived"],
                "match_type": "DOMAIN_MATCH",
                "reason": f"Existing record shares corporate website domain: '{canon_domain}'",
            })

    return matches


def get_hr_contacts_queryset(
    *,
    company_id: Optional[str | UUID] = None,
    search: Optional[str] = None,
    status: Optional[str] = None,
    owner_id: Optional[str | UUID] = None,
    is_archived: Optional[bool] = False,
    ordering: Optional[str] = "name",
) -> QuerySet[HRContact]:
    """Retrieve filtered HR contact directory queryset."""
    qs = HRContact.objects.filter(is_deleted=False).select_related(
        "company", "owner", "created_by", "updated_by"
    )

    if company_id:
        qs = qs.filter(company_id=company_id)

    if is_archived is not None:
        qs = qs.filter(is_archived=is_archived)

    if status:
        qs = qs.filter(status=status)

    if owner_id:
        qs = qs.filter(owner_id=owner_id)

    if search:
        search_term = search.strip()
        qs = qs.filter(
            Q(name__icontains=search_term)
            | Q(email__icontains=search_term)
            | Q(phone__icontains=search_term)
            | Q(designation__icontains=search_term)
            | Q(company__name__icontains=search_term)
        )

    allowed_orderings = {
        "name": "name",
        "-name": "-name",
        "created_at": "created_at",
        "-created_at": "-created_at",
        "designation": "designation",
        "-designation": "-designation",
    }
    order_field = allowed_orderings.get(ordering, "name")
    return qs.order_by(order_field)


def check_hr_contact_duplicates(
    company_id: str | UUID, email: Optional[str] = None, phone: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Check for duplicate HR contacts within the same company by email or phone."""
    matches: List[Dict[str, Any]] = []
    if not company_id:
        return matches

    clean_email = email.strip().lower() if email else ""
    clean_phone = phone.strip() if phone else ""

    if clean_email:
        email_matches = HRContact.objects.filter(
            company_id=company_id, is_deleted=False, email__iexact=clean_email
        ).values("id", "name", "designation", "email", "phone")
        for m in email_matches:
            matches.append({
                "contact_id": m["id"],
                "name": m["name"],
                "designation": m["designation"],
                "match_field": "email",
                "reason": f"Existing contact in this company has matching email: {clean_email}",
            })

    if clean_phone:
        phone_matches = HRContact.objects.filter(
            company_id=company_id, is_deleted=False, phone=clean_phone
        ).values("id", "name", "designation", "email", "phone")
        for m in phone_matches:
            if not any(item.get("contact_id") == m["id"] for item in matches):
                matches.append({
                    "contact_id": m["id"],
                    "name": m["name"],
                    "designation": m["designation"],
                    "match_field": "phone",
                    "reason": f"Existing contact in this company has matching phone: {clean_phone}",
                })

    return matches


def get_outreach_logs_queryset(
    *,
    company_id: Optional[str | UUID] = None,
    hr_contact_id: Optional[str | UUID] = None,
    performed_by_id: Optional[str | UUID] = None,
    channel: Optional[str] = None,
    outcome: Optional[str] = None,
    direction: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[OutreachLog]:
    """Retrieve outreach log activity history."""
    qs = OutreachLog.objects.select_related("company", "hr_contact", "performed_by")

    if company_id:
        qs = qs.filter(company_id=company_id)

    if hr_contact_id:
        qs = qs.filter(hr_contact_id=hr_contact_id)

    if performed_by_id:
        qs = qs.filter(performed_by_id=performed_by_id)

    if channel:
        qs = qs.filter(channel=channel)

    if outcome:
        qs = qs.filter(outcome=outcome)

    if direction:
        qs = qs.filter(direction=direction)

    if date_from:
        qs = qs.filter(activity_date__gte=date_from)

    if date_to:
        qs = qs.filter(activity_date__lte=date_to)

    if search:
        search_term = search.strip()
        qs = qs.filter(
            Q(subject__icontains=search_term)
            | Q(notes__icontains=search_term)
            | Q(company__name__icontains=search_term)
            | Q(hr_contact__name__icontains=search_term)
        )

    return qs.order_by("-activity_date")


def get_follow_ups_queryset(
    *,
    company_id: Optional[str | UUID] = None,
    hr_contact_id: Optional[str | UUID] = None,
    assigned_to_id: Optional[str | UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    is_overdue: Optional[bool] = None,
    due_date_from: Optional[str] = None,
    due_date_to: Optional[str] = None,
    search: Optional[str] = None,
) -> QuerySet[FollowUp]:
    """Retrieve follow-ups with support for overdue state evaluation."""
    qs = FollowUp.objects.select_related(
        "company", "hr_contact", "assigned_to", "completed_by", "created_by"
    )

    if company_id:
        qs = qs.filter(company_id=company_id)

    if hr_contact_id:
        qs = qs.filter(hr_contact_id=hr_contact_id)

    if assigned_to_id:
        qs = qs.filter(assigned_to_id=assigned_to_id)

    if status:
        qs = qs.filter(status=status)

    if priority:
        qs = qs.filter(priority=priority)

    now = timezone.now()
    if is_overdue is True:
        # Overdue = Open/In-progress and due_date in past
        qs = qs.filter(
            status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS],
            due_date__lt=now,
        )
    elif is_overdue is False:
        qs = qs.filter(
            Q(status__in=[FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED])
            | Q(due_date__gte=now)
        )

    if due_date_from:
        qs = qs.filter(due_date__gte=due_date_from)

    if due_date_to:
        qs = qs.filter(due_date__lte=due_date_to)

    if search:
        search_term = search.strip()
        qs = qs.filter(
            Q(purpose__icontains=search_term)
            | Q(company__name__icontains=search_term)
            | Q(hr_contact__name__icontains=search_term)
        )

    return qs.order_by("due_date", "priority")


def get_crm_dashboard_metrics(user: Any, timezone_name: str = "Asia/Kolkata") -> Dict[str, Any]:
    """Calculate permission-aware metrics and operational targets.

    Calculates:
    - Total active companies and active HR contacts.
    - Outreach activity for today in the user's timezone boundary.
    - Outreach channel breakdown for today.
    - Progress toward configured daily outreach target (e.g., 100/day).
    - Follow-ups due today and overdue.
    - Current user's individual outreach count today.
    - Recent activity feed.
    """
    try:
        user_tz = ZoneInfo(timezone_name)
    except Exception:
        user_tz = ZoneInfo("Asia/Kolkata")

    now = timezone.now()
    now_local = now.astimezone(user_tz)
    start_of_day_local = datetime.combine(now_local.date(), time.min, tzinfo=user_tz)
    end_of_day_local = datetime.combine(now_local.date(), time.max, tzinfo=user_tz)

    total_companies = Company.objects.filter(is_archived=False, is_deleted=False).count()
    total_contacts = HRContact.objects.filter(
        is_archived=False, is_deleted=False, status="ACTIVE"
    ).count()

    daily_target = get_daily_outreach_target()

    today_outreach_qs = OutreachLog.objects.filter(
        activity_date__gte=start_of_day_local,
        activity_date__lte=end_of_day_local,
    )
    today_outreach_count = today_outreach_qs.count()

    channel_counts_raw = (
        today_outreach_qs.values("channel")
        .annotate(total=Count("id"))
        .order_by("-total")
    )
    channel_breakdown = {item["channel"]: item["total"] for item in channel_counts_raw}

    user_today_outreach = 0
    if user and user.is_authenticated:
        user_today_outreach = today_outreach_qs.filter(performed_by=user).count()

    due_today_count = FollowUp.objects.filter(
        status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS],
        due_date__gte=start_of_day_local,
        due_date__lte=end_of_day_local,
    ).count()

    overdue_count = FollowUp.objects.filter(
        status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS],
        due_date__lt=now,
    ).count()

    completed_follow_ups_count = FollowUp.objects.filter(
        status=FollowUpStatus.COMPLETED
    ).count()

    recent_activities = list(
        OutreachLog.objects.select_related("company", "hr_contact", "performed_by")
        .order_by("-activity_date")[:10]
        .values(
            "id",
            "channel",
            "direction",
            "activity_date",
            "outcome",
            "subject",
            "company__id",
            "company__name",
            "hr_contact__id",
            "hr_contact__name",
            "performed_by__email",
            "performed_by__first_name",
            "performed_by__last_name",
        )
    )

    return {
        "total_active_companies": total_companies,
        "total_active_contacts": total_contacts,
        "daily_outreach_target": daily_target,
        "today_outreach_count": today_outreach_count,
        "today_outreach_progress_percent": min(
            100.0, round((today_outreach_count / daily_target) * 100, 1)
        ) if daily_target > 0 else 0.0,
        "channel_breakdown": channel_breakdown,
        "user_today_outreach_count": user_today_outreach,
        "follow_ups_due_today": due_today_count,
        "follow_ups_overdue": overdue_count,
        "follow_ups_completed": completed_follow_ups_count,
        "timezone": timezone_name,
        "as_of": now.isoformat(),
        "recent_activities": recent_activities,
    }
