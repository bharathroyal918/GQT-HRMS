"""Selectors for Reports & Analytics (Phase 11).

Pure, read-only analytical aggregations and statistics over authoritative domain records.
Enforces RBAC scoping, zero shadow tables, duplicate count prevention, and timezone correctness.
"""
from datetime import datetime, time
import calendar
from decimal import Decimal
from typing import Any, Dict, List, Optional
import zoneinfo

from django.conf import settings
from django.db.models import (
    Avg,
    Count,
    F,
    Max,
    Min,
    Q,
    Sum,
)
from django.utils import timezone

from apps.accounts.models import RoleCatalog
from apps.crm.models import Company, CompanyRelationshipStatus
from apps.feedback.models import HRFeedback, StudentFeedback, TrainerFeedback
from apps.interviews.models import ConductedStatus, InterviewSchedule, ShortlistedCandidate
from apps.jobs.models import JobRequirement
from apps.placements.models import (
    CandidateOfferLetter,
    CandidatePlacementStatus,
    CandidatePlacementStatusChoices,
    FinalResultIntake,
    JoiningStatus,
    OfferAcceptanceStatus,
)
from apps.preparation.models import PlacementReadinessCertification
from apps.students.models import EligibilityEvaluation, EligibilityStatus, StudentApplication, StudentProfile


def _get_tz():
    return zoneinfo.ZoneInfo(getattr(settings, "TIME_ZONE", "Asia/Kolkata"))


def _safe_percentage(numerator: int, denominator: int) -> float:
    if not denominator or denominator <= 0:
        return 0.0
    return round((float(numerator) / float(denominator)) * 100.0, 2)


def _safe_float(val: Optional[Any], default: float = 0.0) -> float:
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def is_hr_mgr_only(user: Optional[Any]) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    if getattr(user, "is_superuser", False):
        return False
    if hasattr(user, "has_role"):
        is_hr = user.has_role(RoleCatalog.HR_RELATIONSHIP_MGR)
        is_staff_or_auditor = user.has_any_role(
            RoleCatalog.ADMIN,
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.AUDITOR,
        )
        return is_hr and not is_staff_or_auditor
    return False


# -------------------------------------------------------------------------
# 1. Company Reports Selector
# -------------------------------------------------------------------------
def get_company_reports_dataset(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate aggregate corporate hiring and recruitment partner metrics."""
    filters = filters or {}
    companies_qs = Company.objects.filter(is_archived=False)

    # Scoping for HR Relationship Managers
    if is_hr_mgr_only(user):
        companies_qs = companies_qs.filter(owner=user)

    if filters.get("tier"):
        companies_qs = companies_qs.filter(tier=filters["tier"])
    if filters.get("domain_category"):
        companies_qs = companies_qs.filter(domain_category=filters["domain_category"])
    if filters.get("company_id"):
        companies_qs = companies_qs.filter(id=filters["company_id"])

    matched_company_ids = list(companies_qs.values_list("id", flat=True))

    total_companies = len(matched_company_ids)
    active_partners = companies_qs.filter(
        relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER
    ).count()

    # Drives posted
    drives_qs = JobRequirement.objects.filter(company_id__in=matched_company_ids)
    total_drives = drives_qs.count()

    # Distinct candidate submissions
    from apps.submissions.models import CandidateSubmission
    total_candidates_submitted = (
        CandidateSubmission.objects.filter(package__company_id__in=matched_company_ids)
        .values("student_id")
        .distinct()
        .count()
    )

    # Distinct candidates interviewed (conducted)
    total_candidates_interviewed = (
        InterviewSchedule.objects.filter(
            company_id__in=matched_company_ids,
            conducted_status=ConductedStatus.CONDUCTED,
        )
        .values("student_id")
        .distinct()
        .count()
    )

    # Distinct candidates selected
    selected_statuses = CandidatePlacementStatus.objects.filter(
        company_id__in=matched_company_ids,
        status=CandidatePlacementStatusChoices.SELECTED,
    )
    total_candidates_selected = selected_statuses.values("student_id").distinct().count()

    # Offers and Joinings
    offers_qs = CandidateOfferLetter.objects.filter(company_id__in=matched_company_ids)
    total_offers_issued = offers_qs.count()
    total_offers_accepted = offers_qs.filter(
        acceptance_status=OfferAcceptanceStatus.ACCEPTED
    ).count()
    total_candidates_joined = offers_qs.filter(
        joining_status=JoiningStatus.JOINED
    ).count()

    # Compensation aggregates
    ctc_aggs = selected_statuses.filter(offered_ctc__isnull=False).aggregate(
        avg_ctc=Avg("offered_ctc"),
        min_ctc=Min("offered_ctc"),
        max_ctc=Max("offered_ctc"),
    )
    overall_average_ctc = round(_safe_float(ctc_aggs["avg_ctc"]), 2)
    min_ctc = round(_safe_float(ctc_aggs["min_ctc"]), 2)
    max_ctc = round(_safe_float(ctc_aggs["max_ctc"]), 2)

    # Recruiter satisfaction rating (scale 1-5)
    recruiter_feedback_aggs = HRFeedback.objects.filter(
        company_id__in=matched_company_ids
    ).aggregate(
        avg_satisfaction=Avg("hiring_satisfaction_rating"),
        avg_tech_rating=Avg("technical_skills_rating"),
        avg_comm_rating=Avg("communication_skills_rating"),
    )
    avg_recruiter_satisfaction = round(
        _safe_float(recruiter_feedback_aggs["avg_satisfaction"]), 2
    )
    avg_tech_rating = round(_safe_float(recruiter_feedback_aggs["avg_tech_rating"]), 2)
    avg_comm_rating = round(_safe_float(recruiter_feedback_aggs["avg_comm_rating"]), 2)

    # Company breakdown table (limit to top 50 for performance)
    company_breakdown = []
    for comp in companies_qs.order_by("name")[:50]:
        comp_drives = drives_qs.filter(company_id=comp.id).count()
        comp_subs = (
            CandidateSubmission.objects.filter(package__company_id=comp.id)
            .values("student_id")
            .distinct()
            .count()
        )
        comp_interviewed = (
            InterviewSchedule.objects.filter(
                company_id=comp.id,
                conducted_status=ConductedStatus.CONDUCTED,
            )
            .values("student_id")
            .distinct()
            .count()
        )
        comp_selected = (
            CandidatePlacementStatus.objects.filter(
                company_id=comp.id,
                status=CandidatePlacementStatusChoices.SELECTED,
            )
            .values("student_id")
            .distinct()
            .count()
        )
        comp_offers = offers_qs.filter(company_id=comp.id)
        comp_offers_issued = comp_offers.count()
        comp_offers_accepted = comp_offers.filter(
            acceptance_status=OfferAcceptanceStatus.ACCEPTED
        ).count()
        comp_joined = comp_offers.filter(joining_status=JoiningStatus.JOINED).count()

        comp_ctc = (
            CandidatePlacementStatus.objects.filter(
                company_id=comp.id,
                status=CandidatePlacementStatusChoices.SELECTED,
                offered_ctc__isnull=False,
            ).aggregate(avg=Avg("offered_ctc"))["avg"]
        )
        comp_avg_ctc = round(_safe_float(comp_ctc), 2)

        comp_rating = (
            HRFeedback.objects.filter(company_id=comp.id).aggregate(
                avg=Avg("hiring_satisfaction_rating")
            )["avg"]
        )
        comp_avg_rating = round(_safe_float(comp_rating), 2)

        company_breakdown.append(
            {
                "company_id": comp.id,
                "company_name": comp.name,
                "domain_category": comp.get_domain_category_display() if hasattr(comp, "get_domain_category_display") else comp.domain_category,
                "tier": comp.get_tier_display() if hasattr(comp, "get_tier_display") else comp.tier,
                "relationship_status": comp.get_relationship_status_display() if hasattr(comp, "get_relationship_status_display") else comp.relationship_status,
                "drives_count": comp_drives,
                "submissions_count": comp_subs,
                "interviewed_count": comp_interviewed,
                "selected_count": comp_selected,
                "offers_issued_count": comp_offers_issued,
                "offers_accepted_count": comp_offers_accepted,
                "joined_count": comp_joined,
                "average_ctc": comp_avg_ctc,
                "recruiter_rating": comp_avg_rating,
            }
        )

    return {
        "summary": {
            "total_companies": total_companies,
            "active_hiring_partners": active_partners,
            "total_drives_posted": total_drives,
            "total_candidates_submitted": total_candidates_submitted,
            "total_candidates_interviewed": total_candidates_interviewed,
            "total_candidates_selected": total_candidates_selected,
            "total_offers_issued": total_offers_issued,
            "total_offers_accepted": total_offers_accepted,
            "total_candidates_joined": total_candidates_joined,
            "overall_average_ctc": overall_average_ctc,
            "min_ctc": min_ctc,
            "max_ctc": max_ctc,
            "average_recruiter_satisfaction": avg_recruiter_satisfaction,
            "average_technical_rating": avg_tech_rating,
            "average_communication_rating": avg_comm_rating,
        },
        "companies": company_breakdown,
    }


# -------------------------------------------------------------------------
# 2. Student Reports Selector
# -------------------------------------------------------------------------
def get_student_reports_dataset(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate aggregate student registration, verification, readiness, and outcomes."""
    filters = filters or {}
    students_qs = StudentProfile.objects.all()

    if filters.get("department"):
        students_qs = students_qs.filter(department=filters["department"])
    if filters.get("graduation_year"):
        students_qs = students_qs.filter(graduation_year=filters["graduation_year"])
    if filters.get("is_verified") is not None:
        students_qs = students_qs.filter(is_verified_by_placement=filters["is_verified"])

    matched_student_ids = list(students_qs.values_list("id", flat=True))
    total_students = len(matched_student_ids)

    # Verification count
    verified_count = students_qs.filter(is_verified_by_placement=True).count()
    verification_rate = _safe_percentage(verified_count, total_students)

    # Step 23 Gate Placement Readiness Certification
    certified_student_ids = set(
        PlacementReadinessCertification.objects.filter(
            student_id__in=matched_student_ids,
            is_approved_for_placements=True,
        ).values_list("student_id", flat=True)
    )
    readiness_certified_count = len(certified_student_ids)
    readiness_certification_rate = _safe_percentage(
        readiness_certified_count, total_students
    )

    # Application & Drive activity
    total_applications = StudentApplication.objects.filter(
        student_id__in=matched_student_ids
    ).count()
    distinct_students_applied = (
        StudentApplication.objects.filter(student_id__in=matched_student_ids)
        .values("student_id")
        .distinct()
        .count()
    )

    # Interview participation (conducted)
    distinct_students_interviewed = (
        InterviewSchedule.objects.filter(
            student_id__in=matched_student_ids,
            conducted_status=ConductedStatus.CONDUCTED,
        )
        .values("student_id")
        .distinct()
        .count()
    )

    # Selection & Placement outcomes
    selected_placements = CandidatePlacementStatus.objects.filter(
        student_id__in=matched_student_ids,
        status=CandidatePlacementStatusChoices.SELECTED,
    )
    distinct_students_selected = (
        selected_placements.values("student_id").distinct().count()
    )
    placement_rate = _safe_percentage(distinct_students_selected, total_students)

    # Joinings
    distinct_students_joined = (
        CandidateOfferLetter.objects.filter(
            student_id__in=matched_student_ids,
            joining_status=JoiningStatus.JOINED,
        )
        .values("student_id")
        .distinct()
        .count()
    )

    # Department breakdown
    dept_aggs = (
        students_qs.values("department")
        .annotate(
            total=Count("id"),
            verified=Count("id", filter=Q(is_verified_by_placement=True)),
            avg_cgpa=Avg("cgpa"),
        )
        .order_by("department")
    )
    department_breakdown = []
    for d in dept_aggs:
        dept_name = d["department"]
        dept_total = d["total"]
        dept_student_ids = students_qs.filter(department=dept_name).values_list("id", flat=True)
        dept_certified = len(certified_student_ids.intersection(set(dept_student_ids)))
        dept_selected = (
            selected_placements.filter(student__department=dept_name)
            .values("student_id")
            .distinct()
            .count()
        )
        department_breakdown.append(
            {
                "department": dept_name,
                "total_students": dept_total,
                "verified_count": d["verified"],
                "readiness_certified_count": dept_certified,
                "placed_count": dept_selected,
                "placement_rate": _safe_percentage(dept_selected, dept_total),
                "average_cgpa": round(_safe_float(d["avg_cgpa"]), 2),
            }
        )

    # Graduation Year breakdown
    year_aggs = (
        students_qs.values("graduation_year")
        .annotate(
            total=Count("id"),
            verified=Count("id", filter=Q(is_verified_by_placement=True)),
            avg_cgpa=Avg("cgpa"),
        )
        .order_by("-graduation_year")
    )
    graduation_year_breakdown = []
    for y in year_aggs:
        gy = y["graduation_year"]
        gy_total = y["total"]
        gy_placed = (
            selected_placements.filter(student__graduation_year=gy)
            .values("student_id")
            .distinct()
            .count()
        )
        graduation_year_breakdown.append(
            {
                "graduation_year": gy,
                "total_students": gy_total,
                "verified_count": y["verified"],
                "placed_count": gy_placed,
                "placement_rate": _safe_percentage(gy_placed, gy_total),
                "average_cgpa": round(_safe_float(y["avg_cgpa"]), 2),
            }
        )

    # Student feedback difficulty distribution
    difficulty_dist = (
        StudentFeedback.objects.filter(student_id__in=matched_student_ids)
        .values("difficulty")
        .annotate(count=Count("id"))
    )
    difficulty_map = {item["difficulty"]: item["count"] for item in difficulty_dist}

    return {
        "summary": {
            "total_students": total_students,
            "verified_profiles_count": verified_count,
            "verification_rate": verification_rate,
            "readiness_certified_count": readiness_certified_count,
            "readiness_certification_rate": readiness_certification_rate,
            "total_applications": total_applications,
            "distinct_students_applied": distinct_students_applied,
            "distinct_students_interviewed": distinct_students_interviewed,
            "distinct_students_selected": distinct_students_selected,
            "distinct_students_joined": distinct_students_joined,
            "overall_placement_rate": placement_rate,
        },
        "department_breakdown": department_breakdown,
        "graduation_year_breakdown": graduation_year_breakdown,
        "feedback_difficulty_distribution": difficulty_map,
    }


def get_single_student_report_summary(student_profile: StudentProfile) -> Dict[str, Any]:
    """Calculate strictly isolated metrics for a single student."""
    is_certified = PlacementReadinessCertification.objects.filter(
        student=student_profile,
        is_approved_for_placements=True,
    ).exists()

    applications_count = StudentApplication.objects.filter(student=student_profile).count()
    shortlists_count = ShortlistedCandidate.objects.filter(student=student_profile).count()
    interviews_count = InterviewSchedule.objects.filter(
        student=student_profile,
        conducted_status=ConductedStatus.CONDUCTED,
    ).count()

    placement_status = CandidatePlacementStatus.objects.filter(
        student=student_profile,
        status=CandidatePlacementStatusChoices.SELECTED,
    ).first()

    offer = CandidateOfferLetter.objects.filter(student=student_profile).first()

    # Profile completeness score
    completeness_score = 0
    if student_profile.roll_number:
        completeness_score += 15
    if student_profile.institutional_email:
        completeness_score += 15
    if student_profile.department and student_profile.degree:
        completeness_score += 15
    if student_profile.cgpa is not None:
        completeness_score += 15
    if student_profile.phone_number:
        completeness_score += 15
    if hasattr(student_profile, "resumes") and student_profile.resumes.filter(is_current=True).exists():
        completeness_score += 25

    return {
        "student_id": student_profile.id,
        "roll_number": student_profile.roll_number,
        "full_name": student_profile.user.full_name,
        "department": student_profile.department,
        "graduation_year": student_profile.graduation_year,
        "cgpa": float(student_profile.cgpa) if student_profile.cgpa is not None else 0.0,
        "is_verified_by_placement": student_profile.is_verified_by_placement,
        "is_placement_readiness_certified": is_certified,
        "profile_completeness_percent": completeness_score,
        "applications_count": applications_count,
        "shortlists_count": shortlists_count,
        "interviews_attended_count": interviews_count,
        "is_selected": placement_status is not None,
        "designation_offered": placement_status.designation_offered if placement_status else "",
        "offered_ctc": float(placement_status.offered_ctc) if placement_status and placement_status.offered_ctc else None,
        "offer_letter_issued": offer is not None,
        "offer_acceptance_status": offer.acceptance_status if offer else None,
        "joining_status": offer.joining_status if offer else None,
    }


# -------------------------------------------------------------------------
# 3. Placement Reports Selector
# -------------------------------------------------------------------------
def get_placement_reports_dataset(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate authoritative placement outcomes, offer lifecycle, and joining statistics."""
    filters = filters or {}
    results_qs = CandidatePlacementStatus.objects.all()

    if is_hr_mgr_only(user):
        results_qs = results_qs.filter(company__owner=user)

    if filters.get("company_id"):
        results_qs = results_qs.filter(company_id=filters["company_id"])
    if filters.get("job_requirement_id"):
        results_qs = results_qs.filter(job_requirement_id=filters["job_requirement_id"])
    if filters.get("department"):
        results_qs = results_qs.filter(student__department=filters["department"])
    if filters.get("status"):
        results_qs = results_qs.filter(status=filters["status"])
    if filters.get("start_date"):
        results_qs = results_qs.filter(created_at__date__gte=filters["start_date"])
    if filters.get("end_date"):
        results_qs = results_qs.filter(created_at__date__lte=filters["end_date"])

    total_results_evaluated = results_qs.count()

    # Step 37 Status Counts
    selected_count = results_qs.filter(status=CandidatePlacementStatusChoices.SELECTED).count()
    rejected_count = results_qs.filter(status=CandidatePlacementStatusChoices.REJECTED).count()
    waiting_list_count = results_qs.filter(status=CandidatePlacementStatusChoices.WAITING_LIST).count()
    hold_count = results_qs.filter(status=CandidatePlacementStatusChoices.HOLD).count()
    selection_rate = _safe_percentage(selected_count, total_results_evaluated)

    # Step 39-41 Offer & Joining Lifecycle
    matched_placement_ids = list(results_qs.values_list("id", flat=True))
    offers_qs = CandidateOfferLetter.objects.filter(placement_status_id__in=matched_placement_ids)

    total_offers_issued = offers_qs.count()
    offers_accepted = offers_qs.filter(acceptance_status=OfferAcceptanceStatus.ACCEPTED).count()
    offers_declined = offers_qs.filter(acceptance_status=OfferAcceptanceStatus.DECLINED).count()
    offers_pending = offers_qs.filter(acceptance_status=OfferAcceptanceStatus.PENDING_RESPONSE).count()
    offers_expired = offers_qs.filter(acceptance_status=OfferAcceptanceStatus.EXPIRED).count()
    offer_acceptance_rate = _safe_percentage(offers_accepted, total_offers_issued)

    # Joining outcomes
    joined_count = offers_qs.filter(joining_status=JoiningStatus.JOINED).count()
    not_joined_count = offers_qs.filter(joining_status=JoiningStatus.NOT_JOINED).count()
    deferred_count = offers_qs.filter(joining_status=JoiningStatus.DEFERRED).count()
    pending_joining_count = offers_qs.filter(joining_status=JoiningStatus.PENDING_JOINING).count()
    joining_rate = _safe_percentage(joined_count, offers_accepted)

    # Compensation statistics
    selected_with_ctc = results_qs.filter(
        status=CandidatePlacementStatusChoices.SELECTED,
        offered_ctc__isnull=False,
    )
    ctc_aggs = selected_with_ctc.aggregate(
        min_ctc=Min("offered_ctc"),
        max_ctc=Max("offered_ctc"),
        avg_ctc=Avg("offered_ctc"),
        sum_ctc=Sum("offered_ctc"),
    )
    min_ctc = round(_safe_float(ctc_aggs["min_ctc"]), 2)
    max_ctc = round(_safe_float(ctc_aggs["max_ctc"]), 2)
    avg_ctc = round(_safe_float(ctc_aggs["avg_ctc"]), 2)
    sum_ctc = round(_safe_float(ctc_aggs["sum_ctc"]), 2)

    # Safe median CTC calculation
    ctc_values = sorted([float(x) for x in selected_with_ctc.values_list("offered_ctc", flat=True)])
    median_ctc = 0.0
    if ctc_values:
        n = len(ctc_values)
        mid = n // 2
        if n % 2 == 1:
            median_ctc = round(ctc_values[mid], 2)
        else:
            median_ctc = round((ctc_values[mid - 1] + ctc_values[mid]) / 2.0, 2)

    # Company Placements summary breakdown
    company_placements = []
    comp_groups = (
        results_qs.values("company_id", "company__name")
        .annotate(
            total_eval=Count("id"),
            selected=Count("id", filter=Q(status=CandidatePlacementStatusChoices.SELECTED)),
            avg_ctc=Avg("offered_ctc", filter=Q(status=CandidatePlacementStatusChoices.SELECTED)),
        )
        .order_by("-selected")
    )
    for c in comp_groups[:30]:
        c_id = c["company_id"]
        c_offers = offers_qs.filter(company_id=c_id)
        c_issued = c_offers.count()
        c_accepted = c_offers.filter(acceptance_status=OfferAcceptanceStatus.ACCEPTED).count()
        c_joined = c_offers.filter(joining_status=JoiningStatus.JOINED).count()
        company_placements.append(
            {
                "company_id": c_id,
                "company_name": c["company__name"],
                "total_evaluated": c["total_eval"],
                "selected_count": c["selected"],
                "offers_issued": c_issued,
                "offers_accepted": c_accepted,
                "joined_count": c_joined,
                "average_ctc": round(_safe_float(c["avg_ctc"]), 2),
            }
        )

    return {
        "summary": {
            "total_results_evaluated": total_results_evaluated,
            "selected_count": selected_count,
            "rejected_count": rejected_count,
            "waiting_list_count": waiting_list_count,
            "hold_count": hold_count,
            "selection_rate": selection_rate,
            "total_offers_issued": total_offers_issued,
            "offers_accepted": offers_accepted,
            "offers_declined": offers_declined,
            "offers_pending_response": offers_pending,
            "offers_expired": offers_expired,
            "offer_acceptance_rate": offer_acceptance_rate,
            "joined_count": joined_count,
            "not_joined_count": not_joined_count,
            "deferred_count": deferred_count,
            "pending_joining_count": pending_joining_count,
            "joining_rate": joining_rate,
            "min_ctc": min_ctc,
            "max_ctc": max_ctc,
            "average_ctc": avg_ctc,
            "median_ctc": median_ctc,
            "total_package_value": sum_ctc,
        },
        "company_placements": company_placements,
    }


# -------------------------------------------------------------------------
# 4. Performance Reports & Conversion Funnel Selector
# -------------------------------------------------------------------------
def get_performance_reports_dataset(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate objective multi-stage conversion funnel across recruitment gates."""
    filters = filters or {}
    from apps.submissions.models import CandidateSubmission

    app_qs = StudentApplication.objects.all()
    sub_qs = CandidateSubmission.objects.all()
    shortlist_qs = ShortlistedCandidate.objects.all()
    interview_qs = InterviewSchedule.objects.all()
    placement_qs = CandidatePlacementStatus.objects.all()
    offer_qs = CandidateOfferLetter.objects.all()

    if is_hr_mgr_only(user):
        app_qs = app_qs.filter(job_requirement__company__owner=user)
        sub_qs = sub_qs.filter(package__company__owner=user)
        shortlist_qs = shortlist_qs.filter(shortlist__company__owner=user)
        interview_qs = interview_qs.filter(company__owner=user)
        placement_qs = placement_qs.filter(company__owner=user)
        offer_qs = offer_qs.filter(company__owner=user)

    if filters.get("company_id"):
        comp_id = filters["company_id"]
        app_qs = app_qs.filter(job_requirement__company_id=comp_id)
        sub_qs = sub_qs.filter(package__company_id=comp_id)
        shortlist_qs = shortlist_qs.filter(shortlist__company_id=comp_id)
        interview_qs = interview_qs.filter(company_id=comp_id)
        placement_qs = placement_qs.filter(company_id=comp_id)
        offer_qs = offer_qs.filter(company_id=comp_id)

    # 7 Objective Funnel Stages:
    # Stage 1: Applications Received
    stage1_applications = app_qs.count()

    # Stage 2: Applications Eligible
    stage2_eligible = (
        EligibilityEvaluation.objects.filter(
            application__in=app_qs,
            status=EligibilityStatus.ELIGIBLE,
        ).count()
    )

    # Stage 3: Readiness Certified (Candidates with active approved readiness)
    stage3_readiness_certified = (
        PlacementReadinessCertification.objects.filter(
            is_approved_for_placements=True,
        )
        .values("student_id")
        .distinct()
        .count()
    )

    # Stage 4: Profiles Submitted to Corporate HR
    stage4_submitted = sub_qs.values("student_id").distinct().count()

    # Stage 5: Shortlisted by HR
    stage5_shortlisted = shortlist_qs.values("student_id").distinct().count()

    # Stage 6: Interviews Attended / Conducted
    stage6_interviewed = (
        interview_qs.filter(conducted_status=ConductedStatus.CONDUCTED)
        .values("student_id")
        .distinct()
        .count()
    )

    # Stage 7: Selected by Recruiter
    stage7_selected = (
        placement_qs.filter(status=CandidatePlacementStatusChoices.SELECTED)
        .values("student_id")
        .distinct()
        .count()
    )

    # Stage 8: Offers Extended
    stage8_offers = offer_qs.count()

    # Stage 9: Offers Accepted
    stage9_accepted = offer_qs.filter(
        acceptance_status=OfferAcceptanceStatus.ACCEPTED
    ).count()

    # Stage 10: Candidates Joined
    stage10_joined = offer_qs.filter(joining_status=JoiningStatus.JOINED).count()

    # Funnel Stages list for clean visualization
    stages = [
        {
            "stage_number": 1,
            "stage_name": "Applications Received",
            "count": stage1_applications,
            "conversion_from_previous": 100.0,
        },
        {
            "stage_number": 2,
            "stage_name": "Eligible Applications",
            "count": stage2_eligible,
            "conversion_from_previous": _safe_percentage(stage2_eligible, stage1_applications),
        },
        {
            "stage_number": 3,
            "stage_name": "Readiness Certified (Step 23 Gate)",
            "count": stage3_readiness_certified,
            "conversion_from_previous": _safe_percentage(stage3_readiness_certified, stage2_eligible),
        },
        {
            "stage_number": 4,
            "stage_name": "Profiles Dispatched to Recruiter",
            "count": stage4_submitted,
            "conversion_from_previous": _safe_percentage(stage4_submitted, stage3_readiness_certified),
        },
        {
            "stage_number": 5,
            "stage_name": "Shortlisted by Recruiter",
            "count": stage5_shortlisted,
            "conversion_from_previous": _safe_percentage(stage5_shortlisted, stage4_submitted),
        },
        {
            "stage_number": 6,
            "stage_name": "Interviews Conducted",
            "count": stage6_interviewed,
            "conversion_from_previous": _safe_percentage(stage6_interviewed, stage5_shortlisted),
        },
        {
            "stage_number": 7,
            "stage_name": "Candidates Selected",
            "count": stage7_selected,
            "conversion_from_previous": _safe_percentage(stage7_selected, stage6_interviewed),
        },
        {
            "stage_number": 8,
            "stage_name": "Offers Issued",
            "count": stage8_offers,
            "conversion_from_previous": _safe_percentage(stage8_offers, stage7_selected),
        },
        {
            "stage_number": 9,
            "stage_name": "Offers Accepted",
            "count": stage9_accepted,
            "conversion_from_previous": _safe_percentage(stage9_accepted, stage8_offers),
        },
        {
            "stage_number": 10,
            "stage_name": "Candidates Joined",
            "count": stage10_joined,
            "conversion_from_previous": _safe_percentage(stage10_joined, stage9_accepted),
        },
    ]

    overall_pipeline_yield = _safe_percentage(stage10_joined, stage1_applications)

    return {
        "funnel_stages": stages,
        "metrics": {
            "applications_to_eligible_rate": _safe_percentage(stage2_eligible, stage1_applications),
            "submission_to_shortlist_rate": _safe_percentage(stage5_shortlisted, stage4_submitted),
            "interview_to_selection_rate": _safe_percentage(stage7_selected, stage6_interviewed),
            "selection_to_offer_rate": _safe_percentage(stage8_offers, stage7_selected),
            "offer_to_acceptance_rate": _safe_percentage(stage9_accepted, stage8_offers),
            "acceptance_to_joining_rate": _safe_percentage(stage10_joined, stage9_accepted),
            "overall_pipeline_yield": overall_pipeline_yield,
        },
    }


# -------------------------------------------------------------------------
# 5. Monthly Statistics Selector
# -------------------------------------------------------------------------
def get_monthly_statistics_dataset(
    year: int,
    month: Optional[int] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate deterministic month-based statistics using event-specific timestamps in configured timezone."""
    tz = _get_tz()
    from apps.submissions.models import CandidateSubmission

    def _calc_month_metrics(y: int, m: int) -> Dict[str, Any]:
        num_days = calendar.monthrange(y, m)[1]
        start_dt = datetime(y, m, 1, 0, 0, 0, tzinfo=tz)
        end_dt = datetime(y, m, num_days, 23, 59, 59, 999999, tzinfo=tz)
        start_date = start_dt.date()
        end_date = end_dt.date()

        # Job requirements created in this month
        jobs_qs = JobRequirement.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        if is_hr_mgr_only(user):
            jobs_qs = jobs_qs.filter(company__owner=user)
        jobs_posted = jobs_qs.count()

        # Submissions created in this month
        subs_qs = CandidateSubmission.objects.filter(created_at__gte=start_dt, created_at__lte=end_dt)
        if is_hr_mgr_only(user):
            subs_qs = subs_qs.filter(package__company__owner=user)
        profiles_submitted = subs_qs.values("student_id").distinct().count()

        # Interviews scheduled on date falling in this month
        interview_qs = InterviewSchedule.objects.filter(
            interview_date__gte=start_date,
            interview_date__lte=end_date,
            conducted_status=ConductedStatus.CONDUCTED,
        )
        if is_hr_mgr_only(user):
            interview_qs = interview_qs.filter(company__owner=user)
        interviews_conducted = interview_qs.count()

        # Results intake received in this month
        intakes_qs = FinalResultIntake.objects.filter(
            received_at__gte=start_dt,
            received_at__lte=end_dt,
        )
        if is_hr_mgr_only(user):
            intakes_qs = intakes_qs.filter(company__owner=user)
        results_received = intakes_qs.aggregate(total=Sum("total_results"))["total"] or 0

        # Selections received in this month
        sel_qs = CandidatePlacementStatus.objects.filter(
            intake__received_at__gte=start_dt,
            intake__received_at__lte=end_dt,
            status=CandidatePlacementStatusChoices.SELECTED,
        )
        if is_hr_mgr_only(user):
            sel_qs = sel_qs.filter(company__owner=user)
        selections_count = sel_qs.values("student_id").distinct().count()

        # Offers issued in this month
        offers_issued_qs = CandidateOfferLetter.objects.filter(
            issued_at__gte=start_dt,
            issued_at__lte=end_dt,
        )
        if is_hr_mgr_only(user):
            offers_issued_qs = offers_issued_qs.filter(company__owner=user)
        offers_issued = offers_issued_qs.count()

        # Offers accepted in this month (accepted_at)
        offers_accepted_qs = CandidateOfferLetter.objects.filter(
            accepted_at__gte=start_dt,
            accepted_at__lte=end_dt,
            acceptance_status=OfferAcceptanceStatus.ACCEPTED,
        )
        if is_hr_mgr_only(user):
            offers_accepted_qs = offers_accepted_qs.filter(company__owner=user)
        offers_accepted = offers_accepted_qs.count()

        # Joinings verified in this month (actual_joining_date)
        joining_qs = CandidateOfferLetter.objects.filter(
            actual_joining_date__gte=start_date,
            actual_joining_date__lte=end_date,
            joining_status=JoiningStatus.JOINED,
        )
        if is_hr_mgr_only(user):
            joining_qs = joining_qs.filter(company__owner=user)
        candidates_joined = joining_qs.count()

        # Average CTC offered for selections in this month
        ctc_aggs = sel_qs.filter(offered_ctc__isnull=False).aggregate(
            avg_ctc=Avg("offered_ctc"),
            sum_ctc=Sum("offered_ctc"),
        )
        avg_ctc = round(_safe_float(ctc_aggs["avg_ctc"]), 2)
        total_salary_offered = round(_safe_float(ctc_aggs["sum_ctc"]), 2)

        return {
            "year": y,
            "month": m,
            "month_name": f"{calendar.month_name[m]} {y}",
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "jobs_posted": jobs_posted,
            "profiles_submitted": profiles_submitted,
            "interviews_conducted": interviews_conducted,
            "results_received": results_received,
            "selections_count": selections_count,
            "offers_issued": offers_issued,
            "offers_accepted": offers_accepted,
            "candidates_joined": candidates_joined,
            "total_salary_offered": total_salary_offered,
            "average_ctc": avg_ctc,
        }

    if month:
        selected_month_data = _calc_month_metrics(year, month)
    else:
        now_dt = timezone.now().astimezone(tz)
        selected_month_data = _calc_month_metrics(year, now_dt.month if year == now_dt.year else 1)

    # Full 12-month series for annual trend chart
    monthly_series = []
    for m in range(1, 13):
        monthly_series.append(_calc_month_metrics(year, m))

    return {
        "selected_month": selected_month_data,
        "annual_trend": monthly_series,
    }
