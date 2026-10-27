"""Selectors (read & query layer) for Corporate CRM & HR Directory."""
from datetime import datetime, time
from typing import Any, Dict, List, Optional
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db import models
from django.db.models import Count, F, Q, QuerySet
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


# ==============================================================================
# Phase 10: CRM Database Update Selectors & Integration Layer
# ==============================================================================

def get_crm_database_health_diagnostics() -> Dict[str, Any]:
    """Execute non-destructive integrity audit across all 8 recruitment workflow areas.
    
    Evaluates:
    1. Company
    2. HR Contacts
    3. Students
    4. Resume Versions
    5. Interview Status
    6. Placement Status
    7. Feedback
    8. Communication History
    """
    from apps.jobs.models import JobRequirement
    from apps.students.models import StudentProfile, StudentResume, JobPublication
    from apps.submissions.models import SubmissionPackage, CandidateSubmission, SubmissionDispatchLog
    from apps.interviews.models import InterviewSchedule, InterviewNotificationLog
    from apps.placements.models import CandidatePlacementStatus, CandidateOfferLetter, PlacementNotificationLog, FinalResultIntake
    from apps.feedback.models import StudentFeedback, HRFeedback, TrainerFeedback

    conflicts: List[Dict[str, Any]] = []

    # 1. Company Integrity
    companies_qs = Company.objects.filter(is_deleted=False)
    total_companies = companies_qs.count()
    company_conflicts = 0

    # Check for companies with verified placements not marked as ACTIVE_HIRING_PARTNER
    placed_company_ids = set(
        CandidatePlacementStatus.objects.filter(status="SELECTED").values_list("company_id", flat=True)
    )
    unmarked_partners = companies_qs.filter(
        id__in=placed_company_ids
    ).exclude(relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER)
    for c in unmarked_partners:
        company_conflicts += 1
        conflicts.append({
            "area": "Company",
            "severity": "INFO",
            "resource_type": "Company",
            "resource_id": str(c.id),
            "description": f"Company '{c.name}' has verified candidate selections but relationship status is '{c.relationship_status}'.",
            "recommended_action": "Reconciliation will automatically promote relationship status to ACTIVE_HIRING_PARTNER.",
        })

    # 2. HR Contact Integrity
    contacts_qs = HRContact.objects.filter(is_deleted=False)
    total_contacts = contacts_qs.count()
    hr_conflicts = 0

    # Cross-check job requirements where hr_contact company does not match job company
    mismatched_jobs = JobRequirement.objects.filter(
        is_deleted=False, hr_contact__isnull=False
    ).exclude(hr_contact__company_id=models.F("company_id")).select_related("company", "hr_contact")
    for j in mismatched_jobs:
        hr_conflicts += 1
        conflicts.append({
            "area": "HR",
            "severity": "CRITICAL",
            "resource_type": "JobRequirement",
            "resource_id": str(j.id),
            "description": f"Job requirement '{j.title}' belongs to '{j.company.name}' but references HR Contact '{j.hr_contact.name}' from another company.",
            "recommended_action": "Review and reassign the job requirement to an authorized contact within the same company.",
        })

    # 3. Student Profile Integrity
    students_qs = StudentProfile.objects.filter(is_deleted=False).select_related("user")
    total_students = students_qs.count()
    student_conflicts = 0

    for s in students_qs:
        # Check CGPA bounds
        if s.cgpa is not None and (s.cgpa < 0 or s.cgpa > 10):
            student_conflicts += 1
            conflicts.append({
                "area": "Students",
                "severity": "WARNING",
                "resource_type": "StudentProfile",
                "resource_id": str(s.id),
                "description": f"Student '{s.user.full_name}' ({s.roll_number}) has an out-of-range CGPA: {s.cgpa}.",
                "recommended_action": "Verify academic transcript and correct CGPA to a 10.0 scale.",
            })

    # 4. Resume Versions Integrity
    resumes_qs = StudentResume.objects.filter(is_deleted=False)
    total_resumes = resumes_qs.count()
    resume_conflicts = 0

    # Check for students with multiple active current resumes
    multi_current = StudentProfile.objects.annotate(
        current_count=Count("resumes", filter=Q(resumes__is_current=True, resumes__is_deleted=False))
    ).filter(current_count__gt=1)
    for s in multi_current:
        resume_conflicts += 1
        conflicts.append({
            "area": "Resume Versions",
            "severity": "WARNING",
            "resource_type": "StudentProfile",
            "resource_id": str(s.id),
            "description": f"Student '{s.user.full_name}' ({s.roll_number}) has {s.current_count} resumes marked as active/current.",
            "recommended_action": "Mark only the latest approved version as active current resume.",
        })

    # Cross-check CandidateSubmissions referencing resumes not belonging to student
    mismatched_submissions = CandidateSubmission.objects.filter(
        submitted_resume__isnull=False
    ).exclude(submitted_resume__student_id=models.F("student_id")).select_related("student", "submitted_resume")
    for sub in mismatched_submissions:
        resume_conflicts += 1
        conflicts.append({
            "area": "Resume Versions",
            "severity": "CRITICAL",
            "resource_type": "CandidateSubmission",
            "resource_id": str(sub.id),
            "description": f"Candidate submission {sub.id} references a resume belonging to a different student profile.",
            "recommended_action": "Correct submission resume reference to candidate's own certified resume.",
        })

    # 5. Interview Status Integrity
    schedules_qs = InterviewSchedule.objects.all()
    total_schedules = schedules_qs.count()
    interview_conflicts = 0

    # Check for schedules conducted but without outcome/rounds
    empty_conducted = schedules_qs.filter(
        conducted_status="CONDUCTED"
    ).annotate(rounds_count=Count("rounds")).filter(rounds_count=0)
    for sch in empty_conducted:
        interview_conflicts += 1
        conflicts.append({
            "area": "Interview Status",
            "severity": "INFO",
            "resource_type": "InterviewSchedule",
            "resource_id": str(sch.id),
            "description": f"Interview schedule on {sch.interview_date} marked as CONDUCTED without recorded round outcomes.",
            "recommended_action": "Record round evaluation results or feedback notes for the conducted drive.",
        })

    # 6. Placement Status Integrity
    placements_qs = CandidatePlacementStatus.objects.all()
    total_placements = placements_qs.count()
    placement_conflicts = 0

    # Offer letters for non-SELECTED candidates
    invalid_offers = CandidateOfferLetter.objects.exclude(
        placement_status__status="SELECTED"
    ).select_related("placement_status", "student")
    for off in invalid_offers:
        placement_conflicts += 1
        conflicts.append({
            "area": "Placement Status",
            "severity": "CRITICAL",
            "resource_type": "CandidateOfferLetter",
            "resource_id": str(off.id),
            "description": f"Offer letter {off.id} exists for student {off.student.roll_number} whose placement status is '{off.placement_status.status}' (must be SELECTED).",
            "recommended_action": "Verify candidate hiring outcome or void invalid offer letter record.",
        })

    # Joined status with pending/declined offer
    contradictory_joining = CandidateOfferLetter.objects.filter(
        joining_status="JOINED"
    ).exclude(acceptance_status="ACCEPTED").select_related("student")
    for off in contradictory_joining:
        placement_conflicts += 1
        conflicts.append({
            "area": "Placement Status",
            "severity": "CRITICAL",
            "resource_type": "CandidateOfferLetter",
            "resource_id": str(off.id),
            "description": f"Offer letter for student {off.student.roll_number} has joining_status=JOINED but acceptance_status='{off.acceptance_status}'.",
            "recommended_action": "A candidate cannot have joined without formal offer acceptance.",
        })

    # 7. Feedback Integrity & Anonymity
    student_fb_count = StudentFeedback.objects.count()
    hr_fb_count = HRFeedback.objects.count()
    trainer_fb_count = TrainerFeedback.objects.count()
    total_feedback = student_fb_count + hr_fb_count + trainer_fb_count
    feedback_conflicts = 0

    # 8. Communication History Integrity
    outreach_logs_count = OutreachLog.objects.count()
    job_pubs_count = JobPublication.objects.filter(is_deleted=False).count()
    transmissions_count = SubmissionDispatchLog.objects.count()
    reminders_count = InterviewNotificationLog.objects.count()
    placement_notifs_count = PlacementNotificationLog.objects.count()
    total_communications = outreach_logs_count + job_pubs_count + transmissions_count + reminders_count + placement_notifs_count
    comm_conflicts = 0

    # Compute overall statistics
    total_checked = (
        total_companies
        + total_contacts
        + total_students
        + total_resumes
        + total_schedules
        + total_placements
        + total_feedback
        + total_communications
    )
    total_conflicts = len(conflicts)
    consistent_records = max(0, total_checked - total_conflicts)
    health_score = round((consistent_records / total_checked * 100), 1) if total_checked > 0 else 100.0

    overall_status = "HEALTHY"
    if any(c["severity"] == "CRITICAL" for c in conflicts):
        overall_status = "CRITICAL"
    elif total_conflicts > 0:
        overall_status = "NEEDS_ATTENTION"

    return {
        "summary": {
            "total_records_checked": total_checked,
            "total_consistent_records": consistent_records,
            "total_conflicts": total_conflicts,
            "health_score_percentage": health_score,
            "status": overall_status,
            "as_of": timezone.now().isoformat(),
        },
        "areas": {
            "company": {
                "name": "Company",
                "total": total_companies,
                "consistent": total_companies - company_conflicts,
                "conflicts": company_conflicts,
                "status": "WARNING" if company_conflicts > 0 else "CLEAN",
            },
            "hr": {
                "name": "HR Contacts",
                "total": total_contacts,
                "consistent": total_contacts - hr_conflicts,
                "conflicts": hr_conflicts,
                "status": "CRITICAL" if hr_conflicts > 0 else "CLEAN",
            },
            "students": {
                "name": "Students",
                "total": total_students,
                "consistent": total_students - student_conflicts,
                "conflicts": student_conflicts,
                "status": "WARNING" if student_conflicts > 0 else "CLEAN",
            },
            "resumes": {
                "name": "Resume Versions",
                "total": total_resumes,
                "consistent": total_resumes - resume_conflicts,
                "conflicts": resume_conflicts,
                "status": "WARNING" if resume_conflicts > 0 else "CLEAN",
            },
            "interviews": {
                "name": "Interview Status",
                "total": total_schedules,
                "consistent": total_schedules - interview_conflicts,
                "conflicts": interview_conflicts,
                "status": "INFO" if interview_conflicts > 0 else "CLEAN",
            },
            "placements": {
                "name": "Placement Status",
                "total": total_placements,
                "consistent": total_placements - placement_conflicts,
                "conflicts": placement_conflicts,
                "status": "CRITICAL" if placement_conflicts > 0 else "CLEAN",
            },
            "feedback": {
                "name": "Feedback",
                "total": total_feedback,
                "consistent": total_feedback,
                "conflicts": 0,
                "status": "CLEAN",
            },
            "communications": {
                "name": "Communication History",
                "total": total_communications,
                "consistent": total_communications,
                "conflicts": 0,
                "status": "CLEAN",
            },
        },
        "conflicts": conflicts,
    }


def get_company_360_profile(company_id: Any) -> Dict[str, Any]:
    """Compile comprehensive 360-degree recruitment integration profile for a Company."""
    from apps.jobs.models import JobRequirement
    from apps.submissions.models import SubmissionPackage, CandidateSubmission
    from apps.interviews.models import InterviewSchedule
    from apps.placements.models import CandidatePlacementStatus, CandidateOfferLetter
    from apps.feedback.models import HRFeedback, StudentFeedback

    company = Company.objects.filter(id=company_id, is_deleted=False).select_related("owner").first()
    if not company:
        return {}

    hr_contacts = list(
        company.hr_contacts.filter(is_deleted=False, is_archived=False).values(
            "id", "name", "designation", "department", "email", "phone", "status"
        )
    )

    jobs = JobRequirement.objects.filter(company=company, is_deleted=False).order_by("-created_at")
    total_jobs = jobs.count()

    # Submissions count
    total_submissions = CandidateSubmission.objects.filter(
        package__company=company
    ).count()

    # Interview count
    total_interviewed = InterviewSchedule.objects.filter(
        company=company, conducted_status="CONDUCTED"
    ).count()

    # Placements
    placement_statuses = CandidatePlacementStatus.objects.filter(
        company=company
    ).select_related("student", "student__user", "job_requirement")

    total_placed = placement_statuses.filter(status="SELECTED").count()

    placed_candidates_list = []
    total_ctc_sum = 0
    ctc_count = 0
    total_joined = 0

    for ps in placement_statuses.filter(status="SELECTED"):
        offer = getattr(ps, "offer_letter", None)
        joining_status = offer.joining_status if offer else "NOT_APPLICABLE"
        if joining_status == "JOINED":
            total_joined += 1

        ctc_val = float(ps.offered_ctc) if ps.offered_ctc else 0.0
        if ctc_val > 0:
            total_ctc_sum += ctc_val
            ctc_count += 1

        placed_candidates_list.append({
            "id": str(ps.id),
            "student_id": str(ps.student.id),
            "student_name": ps.student.user.full_name,
            "student_roll_number": ps.student.roll_number,
            "job_title": ps.job_requirement.title if ps.job_requirement else "General Drive",
            "designation_offered": ps.designation_offered or "Graduate Trainee",
            "offered_ctc": float(ps.offered_ctc) if ps.offered_ctc else None,
            "acceptance_status": offer.acceptance_status if offer else "PENDING_RESPONSE",
            "joining_status": joining_status,
            "status_updated_at": ps.updated_at.isoformat() if ps.updated_at else None,
        })

    avg_ctc = round(total_ctc_sum / ctc_count, 2) if ctc_count > 0 else 0.0

    # HR Feedbacks
    hr_feedbacks = HRFeedback.objects.filter(company=company)
    total_hr_fb = hr_feedbacks.count()
    avg_tech = 0.0
    avg_comm = 0.0
    avg_sat = 0.0
    if total_hr_fb > 0:
        avg_tech = round(sum(f.technical_skills_rating for f in hr_feedbacks) / total_hr_fb, 1)
        avg_comm = round(sum(f.communication_skills_rating for f in hr_feedbacks) / total_hr_fb, 1)
        avg_sat = round(sum(f.hiring_satisfaction_rating for f in hr_feedbacks) / total_hr_fb, 1)

    # Student Interview difficulty breakdown
    student_fbs = StudentFeedback.objects.filter(company=company)
    diff_counts = {"EASY": 0, "MEDIUM": 0, "HARD": 0, "VERY_HARD": 0}
    for sf in student_fbs:
        if sf.difficulty in diff_counts:
            diff_counts[sf.difficulty] += 1

    # Recruitment drives list
    drives_list = []
    for j in jobs[:10]:
        placed_in_job = placement_statuses.filter(job_requirement=j, status="SELECTED").count()
        drives_list.append({
            "id": str(j.id),
            "title": j.title,
            "status": j.status,
            "openings_count": j.openings_count,
            "interview_date": j.interview_date.isoformat() if j.interview_date else None,
            "placed_count": placed_in_job,
            "created_at": j.created_at.isoformat(),
        })

    return {
        "company": {
            "id": str(company.id),
            "name": company.name,
            "domain": company.domain,
            "domain_category": company.domain_category,
            "tier": company.tier,
            "relationship_status": company.relationship_status,
            "relationship_status_display": company.get_relationship_status_display(),
            "city": company.city,
            "state": company.state,
            "owner_name": company.owner.full_name if company.owner else None,
        },
        "hr_contacts": hr_contacts,
        "lifetime_metrics": {
            "total_jobs": total_jobs,
            "total_submissions": total_submissions,
            "total_interviewed": total_interviewed,
            "total_placed": total_placed,
            "total_joined": total_joined,
            "avg_offered_ctc": avg_ctc,
            "total_hr_feedbacks": total_hr_fb,
            "total_student_feedbacks": student_fbs.count(),
        },
        "feedback_summary": {
            "total_hr_evaluations": total_hr_fb,
            "avg_technical_skills_rating": avg_tech,
            "avg_communication_skills_rating": avg_comm,
            "avg_hiring_satisfaction_rating": avg_sat,
            "difficulty_breakdown": diff_counts,
        },
        "recruitment_drives": drives_list,
        "placed_candidates": placed_candidates_list,
    }


def get_student_360_profile(student_id_or_user_id: Any, viewer_user: Any = None) -> Dict[str, Any]:
    """Compile comprehensive 360-degree candidate recruitment history for a student."""
    from apps.students.models import StudentProfile, StudentApplication
    from apps.preparation.models import PlacementReadinessCertification
    from apps.submissions.models import CandidateSubmission
    from apps.interviews.models import InterviewSchedule
    from apps.placements.models import CandidatePlacementStatus, CandidateOfferLetter
    from apps.feedback.models import TrainerFeedback, StudentFeedback

    # Lookup by profile id or user id
    student = StudentProfile.objects.filter(
        Q(id=student_id_or_user_id) | Q(user_id=student_id_or_user_id),
        is_deleted=False
    ).select_related("user").first()

    if not student:
        return {}

    # Check permission: if viewer is student, they must be the owner
    is_owner = viewer_user and (viewer_user.id == student.user_id)
    is_staff = viewer_user and getattr(viewer_user, "is_staff", False)

    # Resumes
    resumes = list(
        student.resumes.filter(is_deleted=False).order_by("-version_number").values(
            "id", "version_number", "file_name", "file_size_bytes", "is_current", "created_at"
        )
    )

    # Readiness gate
    readiness_cert = PlacementReadinessCertification.objects.filter(
        student=student
    ).order_by("-certified_at").first()

    # Applications
    applications = list(
        StudentApplication.objects.filter(student=student).select_related("job_requirement", "job_requirement__company").order_by("-created_at")[:15]
    )
    applications_list = [
        {
            "id": str(app.id),
            "job_title": app.job_requirement.title,
            "company_name": app.job_requirement.company.name,
            "status": app.status,
            "created_at": app.created_at.isoformat(),
        }
        for app in applications
    ]

    # Submissions
    submissions = list(
        CandidateSubmission.objects.filter(student=student).select_related("package", "package__company", "package__job_requirement").order_by("-created_at")[:10]
    )
    submissions_list = [
        {
            "id": str(sub.id),
            "company_name": sub.package.company.name,
            "job_title": sub.package.job_requirement.title,
            "status": sub.status,
            "status_display": sub.get_status_display(),
            "created_at": sub.created_at.isoformat(),
        }
        for sub in submissions
    ]

    # Placements
    placement_statuses = CandidatePlacementStatus.objects.filter(
        student=student
    ).select_related("company", "job_requirement").order_by("-created_at")

    overall_placement_outcome = "UNPLACED"
    placed_offers = []

    for ps in placement_statuses:
        offer = getattr(ps, "offer_letter", None)
        joining_status = offer.joining_status if offer else "NOT_APPLICABLE"
        acceptance_status = offer.acceptance_status if offer else "PENDING_RESPONSE"

        if ps.status == "SELECTED":
            if joining_status == "JOINED":
                overall_placement_outcome = "JOINED"
            elif acceptance_status == "ACCEPTED" and overall_placement_outcome != "JOINED":
                overall_placement_outcome = "OFFER_ACCEPTED"
            elif overall_placement_outcome not in ["JOINED", "OFFER_ACCEPTED"]:
                overall_placement_outcome = "SELECTED"
        elif ps.status in ["HOLD", "WAITING_LIST"] and overall_placement_outcome == "UNPLACED":
            overall_placement_outcome = "IN_PROCESS"

        placed_offers.append({
            "id": str(ps.id),
            "company_name": ps.company.name,
            "job_title": ps.job_requirement.title if ps.job_requirement else "General Drive",
            "status": ps.status,
            "status_display": ps.get_status_display(),
            "designation_offered": ps.designation_offered or "N/A",
            "offered_ctc": float(ps.offered_ctc) if ps.offered_ctc else None,
            "acceptance_status": acceptance_status,
            "joining_status": joining_status,
            "status_updated_at": ps.updated_at.isoformat() if ps.updated_at else None,
        })

    # Trainer Feedback
    trainer_feedbacks = TrainerFeedback.objects.filter(
        student=student
    ).select_related("trainer").order_by("-created_at")
    trainer_evals = [
        {
            "id": str(tf.id),
            "trainer_name": tf.trainer.full_name,
            "student_readiness": tf.student_readiness,
            "student_readiness_display": tf.get_student_readiness_display(),
            "training_effectiveness_rating": tf.training_effectiveness_rating,
            "areas_for_improvement": tf.areas_for_improvement,
            "created_at": tf.created_at.isoformat(),
        }
        for tf in trainer_feedbacks
    ]

    return {
        "student": {
            "id": str(student.id),
            "roll_number": student.roll_number,
            "full_name": student.user.full_name,
            "institutional_email": student.institutional_email,
            "department": student.department,
            "degree": student.degree,
            "college_name": student.college_name,
            "cgpa": float(student.cgpa) if student.cgpa else None,
            "active_backlogs": student.active_backlogs,
            "graduation_year": student.graduation_year,
            "is_verified_by_placement": student.is_verified_by_placement,
        },
        "readiness_gate": {
            "is_certified": readiness_cert.is_approved_for_placements if readiness_cert else False,
            "certified_at": readiness_cert.certified_at.isoformat() if (readiness_cert and readiness_cert.certified_at) else None,
            "comments": readiness_cert.notes if readiness_cert else "",
        },
        "resumes": [
            {
                "id": str(r["id"]),
                "version_number": r["version_number"],
                "file_name": r["file_name"],
                "file_size_bytes": r["file_size_bytes"],
                "is_current": r["is_current"],
                "created_at": r["created_at"].isoformat(),
            }
            for r in resumes
        ],
        "overall_placement_outcome": overall_placement_outcome,
        "placement_history": placed_offers,
        "applications": applications_list,
        "submissions": submissions_list,
        "trainer_evaluations": trainer_evals,
    }


def get_company_communication_timeline(company_id: Any) -> List[Dict[str, Any]]:
    """Assemble chronological multi-channel communication history for a company."""
    from apps.submissions.models import SubmissionDispatchLog
    from apps.placements.models import PlacementNotificationLog

    events: List[Dict[str, Any]] = []

    # 1. Outreach logs
    outreaches = OutreachLog.objects.filter(company_id=company_id).select_related("performed_by", "hr_contact").order_by("-activity_date")[:50]
    for o in outreaches:
        events.append({
            "id": str(o.id),
            "category": "OUTREACH",
            "channel": o.channel,
            "channel_display": o.get_channel_display(),
            "direction": o.direction,
            "subject": o.subject or f"Outreach via {o.get_channel_display()}",
            "summary": o.notes or f"Outcome: {o.get_outcome_display()}",
            "actor_name": o.performed_by.full_name,
            "contact_name": o.hr_contact.name if o.hr_contact else None,
            "status": "SENT",
            "timestamp": o.activity_date.isoformat(),
        })

    # 2. Candidate Profile Dispatches (Submissions)
    transmissions = SubmissionDispatchLog.objects.filter(
        package__company_id=company_id
    ).select_related("package", "dispatched_by").order_by("-timestamp")[:25]
    for t in transmissions:
        events.append({
            "id": str(t.id),
            "category": "DISPATCH",
            "channel": t.channel,
            "channel_display": t.get_channel_display(),
            "direction": "OUTBOUND",
            "subject": f"Candidate Profiles Dispatched (Package #{str(t.package_id)[:8]})",
            "summary": f"Delivery Status: {t.status}. Recipient: {t.recipient}",
            "actor_name": t.dispatched_by.full_name if t.dispatched_by else "Placement System",
            "contact_name": None,
            "status": t.status,
            "timestamp": t.timestamp.isoformat(),
        })

    # 3. Placement Notifications for company
    placement_notifs = PlacementNotificationLog.objects.filter(
        placement_status__company_id=company_id
    ).select_related("placement_status", "placement_status__student__user").order_by("-sent_at")[:25]
    for pn in placement_notifs:
        events.append({
            "id": str(pn.id),
            "category": "PLACEMENT_NOTIFICATION",
            "channel": pn.channel,
            "channel_display": pn.channel,
            "direction": "OUTBOUND",
            "subject": f"Placement Outcome Advisory: {pn.placement_status.student.user.full_name} ({pn.placement_status.status})",
            "summary": f"Recipient: {pn.recipient_email}. Status: {pn.status}",
            "actor_name": "Placement System",
            "contact_name": None,
            "status": pn.status,
            "timestamp": pn.sent_at.isoformat(),
        })

    # Sort descending by timestamp
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    return events


def get_student_communication_timeline(student_id: Any) -> List[Dict[str, Any]]:
    """Assemble chronological multi-channel communication history for a student candidate."""
    from apps.students.models import StudentProfile, JobPublication
    from apps.interviews.models import InterviewNotificationLog
    from apps.placements.models import PlacementNotificationLog

    student = StudentProfile.objects.filter(Q(id=student_id) | Q(user_id=student_id)).first()
    if not student:
        return []

    events: List[Dict[str, Any]] = []

    # 1. Placement Outcome Notifications
    placement_notifs = PlacementNotificationLog.objects.filter(
        student=student
    ).select_related("placement_status", "placement_status__company").order_by("-sent_at")[:25]
    for pn in placement_notifs:
        events.append({
            "id": str(pn.id),
            "category": "PLACEMENT_ADVISORY",
            "channel": pn.channel,
            "subject": f"Placement Result: {pn.placement_status.company.name} [{pn.placement_status.status}]",
            "summary": f"Delivery status: {pn.status} to {pn.recipient_email}",
            "status": pn.status,
            "timestamp": pn.sent_at.isoformat(),
        })

    # 2. Interview Notifications & Reminders
    notifs = InterviewNotificationLog.objects.filter(
        student=student
    ).select_related("schedule").order_by("-sent_at")[:25]
    for n in notifs:
        events.append({
            "id": str(n.id),
            "category": "INTERVIEW_NOTIFICATION",
            "channel": n.channel,
            "subject": f"Interview Notification ({n.schedule.schedule_reference_code})",
            "summary": f"Dispatched via {n.channel}. Status: {n.status}",
            "status": n.status,
            "timestamp": n.sent_at.isoformat(),
        })

    # 3. Targeted Job Publications
    pubs = JobPublication.objects.filter(
        status="DELIVERED"
    ).select_related("job_requirement", "job_requirement__company").order_by("-dispatched_at")[:10]
    for pub in pubs:
        if pub.dispatched_at:
            events.append({
                "id": str(pub.id),
                "category": "JOB_ANNOUNCEMENT",
                "channel": pub.channel,
                "subject": pub.subject or f"Job Opening: {pub.job_requirement.title} at {pub.job_requirement.company.name}",
                "summary": f"Broadcast via {pub.get_channel_display()}",
                "status": pub.status,
                "timestamp": pub.dispatched_at.isoformat(),
            })

    # Sort descending by timestamp
    events.sort(key=lambda x: x["timestamp"], reverse=True)
    return events

