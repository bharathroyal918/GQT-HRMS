"""Selectors for Continuous Improvement & Strategic Planning (Phase 13).

Provides pure, read-only analytics for:
- Capability A: Granular Placement Rate Analytics
- Capability B: Cross-Category Feedback Intelligence
- Capability C: Evidence-Based Skill Gap Analysis
- Capability D: Strategic Training Plans
- Capability E: Recruitment Cycle Reviews & Continuous Action Tracking
- Diagnostics: Continuous Improvement Data Quality Integrity Check
"""
from datetime import datetime, date
from decimal import Decimal
import re
from typing import Any, Dict, List, Optional, Set
import zoneinfo

from django.conf import settings
from django.db.models import Avg, Count, Max, Min, Q, Sum
from django.utils import timezone

from apps.accounts.models import RoleCatalog
from apps.analytics.models import (
    CycleActionCategory,
    CycleActionStatus,
    CycleImprovementAction,
    RecruitmentCycleReview,
    RecruitmentCycleStatus,
    TrainingPlan,
    TrainingPlanStatus,
)
from apps.crm.models import Company
from apps.feedback.models import CandidateQuality, DifficultyLevel, HRFeedback, StudentFeedback, StudentReadiness, TrainerFeedback
from apps.interviews.models import ConductedStatus, InterviewSchedule, ShortlistedCandidate
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.placements.models import (
    CandidateOfferLetter,
    CandidatePlacementStatus,
    CandidatePlacementStatusChoices,
    JoiningStatus,
    OfferAcceptanceStatus,
)
from apps.preparation.models import (
    AssessmentTest,
    AssessmentTestType,
    MockInterview,
    MockInterviewEvaluation,
    MockInterviewStatus,
    MockReadinessRecommendation,
    PlacementReadinessCertification,
    StudentAssessmentAttempt,
)
from apps.students.models import StudentApplication, StudentProfile
from apps.submissions.models import CandidateSubmission


def _get_tz():
    return zoneinfo.ZoneInfo(getattr(settings, "TIME_ZONE", "Asia/Kolkata"))


def _safe_pct(num: int, den: int) -> float:
    if not den or den <= 0:
        return 0.0
    return round((float(num) / float(den)) * 100.0, 2)


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


# =========================================================================
# CAPABILITY A: Granular Placement Rate Analytics
# =========================================================================
def get_placement_rate_analytics(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Calculate granular cohort placement funnel metrics with explicit numerators and denominators."""
    filters = filters or {}
    students_qs = StudentProfile.objects.all()

    if filters.get("cohort_year"):
        students_qs = students_qs.filter(graduation_year=filters["cohort_year"])
    if filters.get("department"):
        students_qs = students_qs.filter(department=filters["department"])
    if filters.get("college_name"):
        students_qs = students_qs.filter(college_name__icontains=filters["college_name"])

    matched_student_ids = set(students_qs.values_list("id", flat=True))
    total_cohort_students = len(matched_student_ids)

    # 1. Eligible Students Population (Placement Office Verified)
    eligible_students_count = students_qs.filter(is_verified_by_placement=True).count()
    # Baseline denominator defaults to verified students; if none verified, fallback to all cohort students
    baseline_population = eligible_students_count if eligible_students_count > 0 else total_cohort_students

    # 2. Applications (Registered / Applied)
    apps_qs = StudentApplication.objects.filter(student_id__in=matched_student_ids)
    if filters.get("start_date"):
        apps_qs = apps_qs.filter(applied_at__date__gte=filters["start_date"])
    if filters.get("end_date"):
        apps_qs = apps_qs.filter(applied_at__date__lte=filters["end_date"])
    if filters.get("job_requirement_id"):
        apps_qs = apps_qs.filter(job_requirement_id=filters["job_requirement_id"])
    if filters.get("company_id"):
        apps_qs = apps_qs.filter(job_requirement__company_id=filters["company_id"])

    students_applied_ids = set(apps_qs.values_list("student_id", flat=True))
    total_applications_count = apps_qs.count()
    distinct_students_applied_count = len(students_applied_ids)

    # 3. Submissions to Companies
    subs_qs = CandidateSubmission.objects.filter(student_id__in=matched_student_ids)
    if filters.get("company_id"):
        subs_qs = subs_qs.filter(company_id=filters["company_id"])
    if filters.get("job_requirement_id"):
        subs_qs = subs_qs.filter(job_requirement_id=filters["job_requirement_id"])
    students_submitted_ids = set(subs_qs.values_list("student_id", flat=True))
    distinct_students_submitted_count = len(students_submitted_ids)

    # 4. Shortlisted Students
    shortlists_qs = ShortlistedCandidate.objects.filter(student_id__in=matched_student_ids)
    if filters.get("job_requirement_id"):
        shortlists_qs = shortlists_qs.filter(shortlist__job_requirement_id=filters["job_requirement_id"])
    students_shortlisted_ids = set(shortlists_qs.values_list("student_id", flat=True))
    distinct_students_shortlisted_count = len(students_shortlisted_ids)

    # 5. Attended Interviews (Conducted)
    interviews_qs = InterviewSchedule.objects.filter(
        student_id__in=matched_student_ids,
        conducted_status=ConductedStatus.CONDUCTED,
    )
    if filters.get("start_date"):
        interviews_qs = interviews_qs.filter(interview_date__gte=filters["start_date"])
    if filters.get("end_date"):
        interviews_qs = interviews_qs.filter(interview_date__lte=filters["end_date"])
    if filters.get("company_id"):
        interviews_qs = interviews_qs.filter(company_id=filters["company_id"])
    if filters.get("job_requirement_id"):
        interviews_qs = interviews_qs.filter(job_requirement_id=filters["job_requirement_id"])
    students_interviewed_ids = set(interviews_qs.values_list("student_id", flat=True))
    distinct_students_interviewed_count = len(students_interviewed_ids)

    # 6. Placement Results (Selected)
    results_qs = CandidatePlacementStatus.objects.filter(student_id__in=matched_student_ids)
    if is_hr_mgr_only(user):
        results_qs = results_qs.filter(company__owner=user)
    if filters.get("company_id"):
        results_qs = results_qs.filter(company_id=filters["company_id"])
    if filters.get("job_requirement_id"):
        results_qs = results_qs.filter(job_requirement_id=filters["job_requirement_id"])
    if filters.get("start_date"):
        results_qs = results_qs.filter(status_updated_at__date__gte=filters["start_date"])
    if filters.get("end_date"):
        results_qs = results_qs.filter(status_updated_at__date__lte=filters["end_date"])

    selected_results_qs = results_qs.filter(status=CandidatePlacementStatusChoices.SELECTED)
    total_selections_count = selected_results_qs.count()
    students_selected_ids = set(selected_results_qs.values_list("student_id", flat=True))
    distinct_students_selected_count = len(students_selected_ids)

    # 7. Offer Letters & Acceptance (Step 39-40)
    matched_placement_ids = set(results_qs.values_list("id", flat=True))
    offers_qs = CandidateOfferLetter.objects.filter(
        student_id__in=matched_student_ids,
        placement_status_id__in=matched_placement_ids,
    )
    total_offers_issued_count = offers_qs.count()
    distinct_students_offers_issued_ids = set(offers_qs.values_list("student_id", flat=True))

    offers_accepted_qs = offers_qs.filter(acceptance_status=OfferAcceptanceStatus.ACCEPTED)
    total_offers_accepted_count = offers_accepted_qs.count()
    students_accepted_ids = set(offers_accepted_qs.values_list("student_id", flat=True))
    distinct_students_accepted_count = len(students_accepted_ids)

    offers_declined_qs = offers_qs.filter(acceptance_status=OfferAcceptanceStatus.DECLINED)
    total_offers_declined_count = offers_declined_qs.count()

    offers_pending_qs = offers_qs.filter(acceptance_status=OfferAcceptanceStatus.PENDING_RESPONSE)
    total_offers_pending_count = offers_pending_qs.count()

    resolved_offers_count = total_offers_accepted_count + total_offers_declined_count

    # 8. Joining Outcomes (Step 41)
    joined_qs = offers_qs.filter(joining_status=JoiningStatus.JOINED)
    total_joined_count = joined_qs.count()
    students_joined_ids = set(joined_qs.values_list("student_id", flat=True))
    distinct_students_joined_count = len(students_joined_ids)

    not_joined_qs = offers_qs.filter(joining_status=JoiningStatus.NOT_JOINED)
    total_not_joined_count = not_joined_qs.count()
    students_not_joined_ids = set(not_joined_qs.values_list("student_id", flat=True)) - students_joined_ids
    distinct_students_not_joined_count = len(students_not_joined_ids)

    pending_joining_qs = offers_qs.filter(joining_status=JoiningStatus.PENDING_JOINING)
    total_pending_joining_count = pending_joining_qs.count()

    # Final outcomes pending: selected students without resolved joining outcome
    pending_outcome_student_ids = students_selected_ids - students_joined_ids - students_not_joined_ids
    distinct_students_pending_outcomes_count = len(pending_outcome_student_ids)

    # 9. Multi-Offer Distribution
    # Count how many offers each student received
    student_offer_counts = (
        offers_qs.values("student_id")
        .annotate(offer_count=Count("id"))
        .values_list("offer_count", flat=True)
    )
    single_offer_students = sum(1 for c in student_offer_counts if c == 1)
    dual_offer_students = sum(1 for c in student_offer_counts if c == 2)
    multi_offer_students = sum(1 for c in student_offer_counts if c >= 3)

    # 10. Rate Metrics with Explicit Formulas & Denominators
    placement_rate_eligible = _safe_pct(distinct_students_selected_count, baseline_population)
    placement_rate_applicants = _safe_pct(distinct_students_selected_count, distinct_students_applied_count)
    interview_selection_rate = _safe_pct(distinct_students_selected_count, distinct_students_interviewed_count)
    offer_acceptance_rate = _safe_pct(total_offers_accepted_count, resolved_offers_count if resolved_offers_count > 0 else total_offers_issued_count)
    joining_rate = _safe_pct(distinct_students_joined_count, distinct_students_accepted_count)
    overall_pipeline_yield = _safe_pct(distinct_students_joined_count, baseline_population)

    # 11. Department Breakdown Table
    department_breakdown = []
    dept_names = students_qs.values_list("department", flat=True).distinct().order_by("department")
    for dept in dept_names:
        if not dept:
            continue
        dept_studs = students_qs.filter(department=dept)
        dept_total = dept_studs.count()
        dept_stud_ids = set(dept_studs.values_list("id", flat=True))
        dept_applied = len(set(apps_qs.filter(student_id__in=dept_stud_ids).values_list("student_id", flat=True)))
        dept_selected = len(set(selected_results_qs.filter(student_id__in=dept_stud_ids).values_list("student_id", flat=True)))
        dept_joined = len(set(joined_qs.filter(student_id__in=dept_stud_ids).values_list("student_id", flat=True)))
        dept_rate = _safe_pct(dept_selected, dept_total)

        department_breakdown.append({
            "department": dept,
            "total_students": dept_total,
            "applied_students": dept_applied,
            "selected_students": dept_selected,
            "joined_students": dept_joined,
            "placement_rate": dept_rate,
        })

    # 12. Metric Definitions & Traceability Explanations
    metric_definitions = [
        {
            "metric_name": "Eligible Cohort Placement Rate",
            "percentage": placement_rate_eligible,
            "numerator": distinct_students_selected_count,
            "numerator_label": "Distinct Students Selected",
            "denominator": baseline_population,
            "denominator_label": "Eligible Students in Cohort",
            "formula": "(Distinct Students Selected / Verified Eligible Cohort) * 100",
            "records_count": total_selections_count,
            "notes": "Measures institutional placement conversion against all certified eligible students. Prevents double-counting students with multiple offers.",
        },
        {
            "metric_name": "Applicant Placement Rate",
            "percentage": placement_rate_applicants,
            "numerator": distinct_students_selected_count,
            "numerator_label": "Distinct Students Selected",
            "denominator": distinct_students_applied_count,
            "denominator_label": "Distinct Students Who Applied",
            "formula": "(Distinct Students Selected / Distinct Students Applied) * 100",
            "records_count": total_applications_count,
            "notes": "Measures drive conversion specifically for active student job seekers.",
        },
        {
            "metric_name": "Interview-to-Selection Rate",
            "percentage": interview_selection_rate,
            "numerator": distinct_students_selected_count,
            "numerator_label": "Distinct Students Selected",
            "denominator": distinct_students_interviewed_count,
            "denominator_label": "Distinct Students Interviewed",
            "formula": "(Distinct Students Selected / Distinct Students Interviewed) * 100",
            "records_count": interviews_qs.count(),
            "notes": "Measures candidate interview clearance efficiency across all recruitment rounds.",
        },
        {
            "metric_name": "Offer Acceptance Rate",
            "percentage": offer_acceptance_rate,
            "numerator": total_offers_accepted_count,
            "numerator_label": "Total Offers Accepted",
            "denominator": resolved_offers_count if resolved_offers_count > 0 else total_offers_issued_count,
            "denominator_label": "Resolved Offers (Accepted + Declined)",
            "formula": "(Accepted Offers / Resolved Offer Decisions) * 100",
            "records_count": total_offers_issued_count,
            "notes": "Event-level metric measuring corporate offer appeal among candidates.",
        },
        {
            "metric_name": "Joining Rate",
            "percentage": joining_rate,
            "numerator": distinct_students_joined_count,
            "numerator_label": "Distinct Students Joined",
            "denominator": distinct_students_accepted_count,
            "denominator_label": "Distinct Students with Accepted Offers",
            "formula": "(Students Joined / Students Accepted Offers) * 100",
            "records_count": total_joined_count,
            "notes": "Measures onboarding realization and candidate renege containment.",
        },
        {
            "metric_name": "Overall Pipeline Yield",
            "percentage": overall_pipeline_yield,
            "numerator": distinct_students_joined_count,
            "numerator_label": "Distinct Students Joined",
            "denominator": baseline_population,
            "denominator_label": "Eligible Cohort Base",
            "formula": "(Students Joined / Eligible Cohort Base) * 100",
            "records_count": total_joined_count,
            "notes": "End-to-end institutional yield from eligible registration to verified employer onboarding.",
        },
    ]

    return {
        "summary": {
            "total_cohort_students": total_cohort_students,
            "total_eligible_students": baseline_population,
            "distinct_students_applied": distinct_students_applied_count,
            "total_applications": total_applications_count,
            "distinct_students_submitted": distinct_students_submitted_count,
            "distinct_students_shortlisted": distinct_students_shortlisted_count,
            "distinct_students_interviewed": distinct_students_interviewed_count,
            "distinct_students_selected": distinct_students_selected_count,
            "total_selections": total_selections_count,
            "total_offers_issued": total_offers_issued_count,
            "total_offers_accepted": total_offers_accepted_count,
            "total_offers_declined": total_offers_declined_count,
            "total_offers_pending": total_offers_pending_count,
            "distinct_students_joined": distinct_students_joined_count,
            "distinct_students_not_joined": distinct_students_not_joined_count,
            "distinct_students_pending_outcomes": distinct_students_pending_outcomes_count,
            "single_offer_students": single_offer_students,
            "dual_offer_students": dual_offer_students,
            "multi_offer_students": multi_offer_students,
            "placement_rate_eligible": placement_rate_eligible,
            "placement_rate_applicants": placement_rate_applicants,
            "interview_selection_rate": interview_selection_rate,
            "offer_acceptance_rate": offer_acceptance_rate,
            "joining_rate": joining_rate,
            "overall_pipeline_yield": overall_pipeline_yield,
        },
        "metric_definitions": metric_definitions,
        "department_breakdown": department_breakdown,
        "filters_applied": {k: str(v) for k, v in filters.items() if v is not None},
        "generated_at": timezone.now().isoformat(),
    }


# =========================================================================
# CAPABILITY B: Cross-Category Feedback Intelligence
# =========================================================================
MINIMUM_GROUP_ANONYMITY_THRESHOLD = 3


def get_feedback_intelligence(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Aggregate feedback across Student (Cat A), Recruiter HR (Cat B), and Trainer (Cat C)."""
    filters = filters or {}

    # Scoping
    raw_company_id = filters.get("company_id")
    scoped_company_id = str(raw_company_id) if raw_company_id else None
    if is_hr_mgr_only(user):
        owned_company_ids = [str(c) for c in Company.objects.filter(owner=user).values_list("id", flat=True)]
        if scoped_company_id and scoped_company_id not in owned_company_ids:
            return {"error": "Unauthorized access to company feedback."}
        hr_companies_filter = Q(company_id=scoped_company_id) if scoped_company_id else Q(company_id__in=owned_company_ids)
    else:
        hr_companies_filter = Q(company_id=scoped_company_id) if scoped_company_id else Q()

    # 1. HR Recruiter Feedback (Category B)
    hr_qs = HRFeedback.objects.filter(hr_companies_filter)
    if filters.get("start_date"):
        hr_qs = hr_qs.filter(created_at__date__gte=filters["start_date"])
    if filters.get("end_date"):
        hr_qs = hr_qs.filter(created_at__date__lte=filters["end_date"])
    if filters.get("job_requirement_id"):
        hr_qs = hr_qs.filter(job_requirement_id=filters["job_requirement_id"])

    hr_total = hr_qs.count()
    hr_aggs = hr_qs.aggregate(
        avg_tech=Avg("technical_skills_rating"),
        avg_comm=Avg("communication_skills_rating"),
        avg_sat=Avg("hiring_satisfaction_rating"),
    )
    avg_technical_rating = round(_safe_float(hr_aggs["avg_tech"]), 2)
    avg_communication_rating = round(_safe_float(hr_aggs["avg_comm"]), 2)
    avg_hiring_satisfaction = round(_safe_float(hr_aggs["avg_sat"]), 2)

    quality_counts = {
        CandidateQuality.EXCELLENT: hr_qs.filter(candidate_quality=CandidateQuality.EXCELLENT).count(),
        CandidateQuality.GOOD: hr_qs.filter(candidate_quality=CandidateQuality.GOOD).count(),
        CandidateQuality.FAIR: hr_qs.filter(candidate_quality=CandidateQuality.FAIR).count(),
        CandidateQuality.POOR: hr_qs.filter(candidate_quality=CandidateQuality.POOR).count(),
    }

    # Extract non-empty recruiter observations (sanitized)
    hr_remarks_list = []
    recruiter_remarks_sample = []
    for f in hr_qs.select_related("company", "job_requirement").order_by("-created_at")[:10]:
        remarks = (f.technical_skills_remarks or f.communication_skills_remarks or f.hiring_satisfaction_remarks or "").strip()
        if remarks:
            item_entry = {
                "company_name": f.company.name,
                "candidate_quality": f.get_candidate_quality_display(),
                "technical_rating": f.technical_skills_rating,
                "communication_rating": f.communication_skills_rating,
                "satisfaction_rating": f.hiring_satisfaction_rating,
                "remarks": remarks[:300],
                "date": f.created_at.date().isoformat(),
            }
            hr_remarks_list.append(item_entry)
            recruiter_remarks_sample.append({
                "id": str(f.id),
                "company_name": f.company.name,
                "role_title": f.job_requirement.title if f.job_requirement else "General Recruitment",
                "category": f.get_candidate_quality_display(),
                "remark": remarks[:300],
                "rating": f.technical_skills_rating,
                "date": f.created_at.date().isoformat(),
            })

    # 2. Student Interview Feedback (Category A)
    student_qs = StudentFeedback.objects.all()
    if scoped_company_id:
        student_qs = student_qs.filter(company_id=scoped_company_id)
    if filters.get("job_requirement_id"):
        student_qs = student_qs.filter(job_requirement_id=filters["job_requirement_id"])
    if filters.get("start_date"):
        student_qs = student_qs.filter(created_at__date__gte=filters["start_date"])
    if filters.get("end_date"):
        student_qs = student_qs.filter(created_at__date__lte=filters["end_date"])

    student_total = student_qs.count()
    difficulty_counts = {
        DifficultyLevel.EASY: student_qs.filter(difficulty=DifficultyLevel.EASY).count(),
        DifficultyLevel.MEDIUM: student_qs.filter(difficulty=DifficultyLevel.MEDIUM).count(),
        DifficultyLevel.HARD: student_qs.filter(difficulty=DifficultyLevel.HARD).count(),
        DifficultyLevel.VERY_HARD: student_qs.filter(difficulty=DifficultyLevel.VERY_HARD).count(),
    }

    student_difficulty_breakdown = [
        {"difficulty": "EASY", "count": difficulty_counts[DifficultyLevel.EASY], "percentage": _safe_pct(difficulty_counts[DifficultyLevel.EASY], student_total)},
        {"difficulty": "MEDIUM", "count": difficulty_counts[DifficultyLevel.MEDIUM], "percentage": _safe_pct(difficulty_counts[DifficultyLevel.MEDIUM], student_total)},
        {"difficulty": "HARD", "count": difficulty_counts[DifficultyLevel.HARD], "percentage": _safe_pct(difficulty_counts[DifficultyLevel.HARD], student_total)},
        {"difficulty": "VERY_HARD", "count": difficulty_counts[DifficultyLevel.VERY_HARD], "percentage": _safe_pct(difficulty_counts[DifficultyLevel.VERY_HARD], student_total)},
    ]

    # Strict Anonymity & Small Group Masking Policy
    is_small_group = student_total < MINIMUM_GROUP_ANONYMITY_THRESHOLD
    student_feedback_extracts = []
    student_suggestions_sample = []
    for sf in student_qs.select_related("company", "student").order_by("-created_at")[:10]:
        # Enforce student anonymity if flagged OR if small group threshold applies
        should_mask = sf.is_anonymous or is_small_group
        author_display = "Candidate (Anonymized)" if should_mask else sf.student.roll_number
        experience = sf.interview_experience[:250] if sf.interview_experience else ""
        suggestion_text = sf.suggestions[:200] if sf.suggestions else (experience[:200] or "No specific suggestion provided.")
        student_feedback_extracts.append({
            "company_name": sf.company.name,
            "difficulty": sf.get_difficulty_display(),
            "interview_experience": experience,
            "technical_questions": sf.technical_questions[:200] if sf.technical_questions else "",
            "suggestions": sf.suggestions[:200] if sf.suggestions else "",
            "submitted_by": author_display,
            "is_anonymous": should_mask,
            "date": sf.created_at.date().isoformat(),
        })
        student_suggestions_sample.append({
            "id": str(sf.id),
            "company_name": sf.company.name,
            "difficulty": sf.get_difficulty_display(),
            "suggestion": suggestion_text,
            "interview_experience": experience,
            "date": sf.created_at.date().isoformat(),
            "is_anonymous": should_mask,
        })

    # 3. Trainer Readiness Feedback (Category C)
    trainer_qs = TrainerFeedback.objects.all()
    if filters.get("start_date"):
        trainer_qs = trainer_qs.filter(created_at__date__gte=filters["start_date"])
    if filters.get("end_date"):
        trainer_qs = trainer_qs.filter(created_at__date__lte=filters["end_date"])

    trainer_total = trainer_qs.count()
    trainer_aggs = trainer_qs.aggregate(avg_eff=Avg("training_effectiveness_rating"))
    avg_training_effectiveness = round(_safe_float(trainer_aggs["avg_eff"]), 2)

    readiness_counts = {
        StudentReadiness.HIGHLY_READY: trainer_qs.filter(student_readiness=StudentReadiness.HIGHLY_READY).count(),
        StudentReadiness.READY: trainer_qs.filter(student_readiness=StudentReadiness.READY).count(),
        StudentReadiness.NEEDS_PRACTICE: trainer_qs.filter(student_readiness=StudentReadiness.NEEDS_PRACTICE).count(),
        StudentReadiness.NOT_READY: trainer_qs.filter(student_readiness=StudentReadiness.NOT_READY).count(),
    }

    trainer_readiness_breakdown = [
        {"readiness": "HIGHLY_READY", "count": readiness_counts[StudentReadiness.HIGHLY_READY], "percentage": _safe_pct(readiness_counts[StudentReadiness.HIGHLY_READY], trainer_total)},
        {"readiness": "READY", "count": readiness_counts[StudentReadiness.READY], "percentage": _safe_pct(readiness_counts[StudentReadiness.READY], trainer_total)},
        {"readiness": "NEEDS_PRACTICE", "count": readiness_counts[StudentReadiness.NEEDS_PRACTICE], "percentage": _safe_pct(readiness_counts[StudentReadiness.NEEDS_PRACTICE], trainer_total)},
        {"readiness": "NOT_READY", "count": readiness_counts[StudentReadiness.NOT_READY], "percentage": _safe_pct(readiness_counts[StudentReadiness.NOT_READY], trainer_total)},
    ]

    # Recurring areas for improvement from trainers
    trainer_improvements = []
    trainer_improvement_areas_sample = []
    for tf in trainer_qs.select_related("student", "student__user").order_by("-created_at")[:10]:
        if tf.areas_for_improvement and tf.areas_for_improvement.strip():
            student_display = "Candidate (Anonymized)" if is_small_group else (
                getattr(tf.student.user, "full_name", None) or getattr(tf.student, "roll_number", "Candidate")
                if hasattr(tf, "student") and tf.student else "Candidate"
            )
            trainer_improvements.append({
                "student_readiness": tf.get_student_readiness_display(),
                "training_effectiveness": tf.training_effectiveness_rating,
                "areas_for_improvement": tf.areas_for_improvement[:250],
                "date": tf.created_at.date().isoformat(),
            })
            trainer_improvement_areas_sample.append({
                "id": str(tf.id),
                "student_name": student_display,
                "readiness": tf.get_student_readiness_display(),
                "areas_for_improvement": tf.areas_for_improvement[:250],
                "effectiveness_rating": tf.training_effectiveness_rating,
                "date": tf.created_at.date().isoformat(),
            })

    return {
        "anonymity_rule_enforced": True,
        "minimum_group_threshold": MINIMUM_GROUP_ANONYMITY_THRESHOLD,
        "is_small_group_masked": is_small_group,
        "anonymity_notice": "Minimum group threshold applied to protect student privacy." if is_small_group else None,
        "kpi_summary": {
            "total_recruiter_evaluations": hr_total,
            "total_student_experiences": student_total,
            "total_trainer_assessments": trainer_total,
            "avg_recruiter_tech_rating": avg_technical_rating,
            "avg_recruiter_comm_rating": avg_communication_rating,
            "avg_recruiter_satisfaction": avg_hiring_satisfaction,
            "avg_trainer_effectiveness": avg_training_effectiveness,
        },
        "recruiter_ratings": {
            "avg_technical": avg_technical_rating,
            "avg_communication": avg_communication_rating,
            "avg_satisfaction": avg_hiring_satisfaction,
            "distribution_quality": quality_counts,
        },
        "student_difficulty_breakdown": student_difficulty_breakdown,
        "trainer_readiness_breakdown": trainer_readiness_breakdown,
        "recruiter_remarks_sample": recruiter_remarks_sample,
        "student_suggestions_sample": student_suggestions_sample,
        "trainer_improvement_areas_sample": trainer_improvement_areas_sample,
        "hr_feedback": {
            "total_responses": hr_total,
            "avg_technical_rating": avg_technical_rating,
            "avg_communication_rating": avg_communication_rating,
            "avg_hiring_satisfaction": avg_hiring_satisfaction,
            "candidate_quality_distribution": quality_counts,
            "recent_observations": hr_remarks_list,
        },
        "student_feedback": {
            "total_responses": student_total,
            "difficulty_distribution": difficulty_counts,
            "is_small_group_masked": is_small_group,
            "anonymity_threshold": MINIMUM_GROUP_ANONYMITY_THRESHOLD,
            "recent_experiences": student_feedback_extracts,
        },
        "trainer_feedback": {
            "total_evaluations": trainer_total,
            "avg_training_effectiveness": avg_training_effectiveness,
            "readiness_distribution": readiness_counts,
            "recurring_improvement_areas": trainer_improvements,
        },
        "generated_at": timezone.now().isoformat(),
    }


# =========================================================================
# CAPABILITY C: Evidence-Based Skill Gap Analysis
# =========================================================================
CANONICAL_SKILL_PATTERNS = [
    (r"\b(python|python3|py)\b", "Python"),
    (r"\b(django|drf|django rest)\b", "Django"),
    (r"\b(react|reactjs|react\.js)\b", "React"),
    (r"\b(javascript|js|es6)\b", "JavaScript"),
    (r"\b(typescript|ts)\b", "TypeScript"),
    (r"\b(java|core java|advanced java)\b", "Java"),
    (r"\b(spring|springboot|spring boot)\b", "Spring Boot"),
    (r"\b(sql|mysql|postgresql|postgres|database)\b", "SQL / Database"),
    (r"\b(dsa|data structures|algorithms|problem solving)\b", "Data Structures & Algorithms"),
    (r"\b(aptitude|quantitative|reasoning|logical)\b", "Aptitude & Quantitative"),
    (r"\b(communication|verbal|soft skills|english)\b", "Communication & Soft Skills"),
    (r"\b(html|css|web dev|frontend)\b", "Web Technologies"),
    (r"\b(git|github|version control)\b", "Git & Version Control"),
    (r"\b(c\+\+|cpp)\b", "C++"),
    (r"\b(node|nodejs|node\.js|express)\b", "Node.js"),
    (r"\b(aws|cloud|docker|devops)\b", "Cloud & DevOps"),
]


def normalize_skill(raw_skill: str) -> Optional[str]:
    """Map raw skill string or keyword to canonical institutional skill name."""
    cleaned = raw_skill.strip().lower()
    for pattern, canonical in CANONICAL_SKILL_PATTERNS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            return canonical
    # If no pattern matches and cleaned has reasonable length, capitalize
    if len(cleaned) >= 2:
        return cleaned.title()
    return None


def get_skill_gap_analysis(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Analyze empirical skill supply and demand using JobRequirements, Assessments, Mocks, and Feedback."""
    filters = filters or {}

    # 1. Market Demand: Extract skills required from approved/active Job Requirements
    jobs_qs = JobRequirement.objects.filter(
        status__in=[
            JobRequirementStatus.APPROVED,
            JobRequirementStatus.VERIFIED,
            JobRequirementStatus.UNDER_REVIEW,
        ]
    )
    if filters.get("company_id"):
        jobs_qs = jobs_qs.filter(company_id=filters["company_id"])

    skill_demand_counts: Dict[str, int] = {}
    skill_job_references: Dict[str, List[str]] = {}
    skill_company_references: Dict[str, Set[str]] = {}

    for job in jobs_qs:
        raw_text = f"{job.skills_required} {job.title} {job.job_description}"
        detected_in_job: Set[str] = set()
        for token in re.split(r"[,;\n/]+", job.skills_required):
            norm = normalize_skill(token)
            if norm:
                detected_in_job.add(norm)

        # Fallback check against canonical patterns on the full skills_required string
        for pattern, canonical in CANONICAL_SKILL_PATTERNS:
            if re.search(pattern, raw_text, re.IGNORECASE):
                detected_in_job.add(canonical)

        for skill in detected_in_job:
            skill_demand_counts[skill] = skill_demand_counts.get(skill, 0) + 1
            if skill not in skill_job_references:
                skill_job_references[skill] = []
            if job.title not in skill_job_references[skill]:
                skill_job_references[skill].append(job.title)
            if skill not in skill_company_references:
                skill_company_references[skill] = set()
            skill_company_references[skill].add(str(job.company_id))

    # 2. Institutional Assessments Evidence (Aptitude & Technical)
    attempts_qs = StudentAssessmentAttempt.objects.filter(status="COMPLETED")
    if filters.get("cohort_year"):
        attempts_qs = attempts_qs.filter(student__graduation_year=filters["cohort_year"])
    if filters.get("department"):
        attempts_qs = attempts_qs.filter(student__department=filters["department"])

    skill_assessment_stats: Dict[str, Dict[str, Any]] = {}
    for test in AssessmentTest.objects.all():
        # Map test title / domain track to skill
        test_skill = normalize_skill(f"{test.domain_track} {test.title}")
        if not test_skill:
            test_skill = "Aptitude & Quantitative" if test.test_type == AssessmentTestType.APTITUDE else "Technical Assessment"

        test_attempts = attempts_qs.filter(test=test)
        total_att = test_attempts.count()
        passed_att = test_attempts.filter(passed=True).count()
        avg_score = test_attempts.aggregate(avg=Avg("percentage"))["avg"] or 0.0

        if test_skill not in skill_assessment_stats:
            skill_assessment_stats[test_skill] = {
                "total_attempts": 0,
                "passed_attempts": 0,
                "score_sum": 0.0,
                "tests_count": 0,
            }

        skill_assessment_stats[test_skill]["total_attempts"] += total_att
        skill_assessment_stats[test_skill]["passed_attempts"] += passed_att
        skill_assessment_stats[test_skill]["score_sum"] += float(avg_score) * total_att
        skill_assessment_stats[test_skill]["tests_count"] += 1

    # 3. Mock Interview Rubric Baseline
    mock_evals_qs = MockInterviewEvaluation.objects.all()
    if filters.get("cohort_year"):
        mock_evals_qs = mock_evals_qs.filter(mock_interview__student__graduation_year=filters["cohort_year"])

    mock_total = mock_evals_qs.count()
    mock_aggs = mock_evals_qs.aggregate(
        avg_tech=Avg("technical_competence_score"),
        avg_prob=Avg("problem_solving_score"),
        avg_comm=Avg("communication_clarity_score"),
        avg_prof=Avg("professional_readiness_score"),
    )
    mock_avg_technical = round(_safe_float(mock_aggs["avg_tech"]), 2)
    mock_avg_problem_solving = round(_safe_float(mock_aggs["avg_prob"]), 2)
    mock_avg_communication = round(_safe_float(mock_aggs["avg_comm"]), 2)

    # 4. Synthesize Combined Skill Matrix
    all_skills = set(skill_demand_counts.keys()) | set(skill_assessment_stats.keys())
    # Ensure standard baseline competencies are always included
    all_skills.update(["Data Structures & Algorithms", "Aptitude & Quantitative", "Communication & Soft Skills", "Python", "Java", "SQL / Database"])

    skill_matrix = []
    for skill in sorted(all_skills):
        demand = skill_demand_counts.get(skill, 0)
        ass_data = skill_assessment_stats.get(skill)

        if ass_data and ass_data["total_attempts"] > 0:
            total_att = ass_data["total_attempts"]
            passed_att = ass_data["passed_attempts"]
            pass_rate = _safe_pct(passed_att, total_att)
            avg_score = round(ass_data["score_sum"] / total_att, 2)
        else:
            total_att = 0
            passed_att = 0
            pass_rate = None
            avg_score = None

        # Data Coverage Level
        if total_att >= 10:
            coverage = "HIGH"
        elif total_att >= 3:
            coverage = "MODERATE"
        elif total_att >= 1:
            coverage = "LOW"
        else:
            coverage = "INSUFFICIENT_DATA"

        # Categorize Gap Status deterministically (Zero AI)
        if demand >= 2 and (pass_rate is None or total_att == 0):
            gap_status = "UNASSESSED_DEMAND"
            status_label = "Unassessed Market Demand"
            severity = "HIGH"
            recommendation = f"Urgent: Create institutional assessment test and verify student baseline for {skill}."
        elif pass_rate is not None and pass_rate < 60.0:
            gap_status = "CRITICAL_GAP"
            status_label = "Demonstrated Skill Gap (<60% Pass Rate)"
            severity = "CRITICAL"
            recommendation = f"Conduct remedial workshop and syllabus coaching on {skill} before campus drives."
        elif pass_rate is not None and pass_rate < 75.0:
            gap_status = "MODERATE_GAP"
            status_label = "Moderate Gap (60–74% Pass Rate)"
            severity = "MEDIUM"
            recommendation = f"Provide mock drills and practice assignments on {skill}."
        elif demand >= 1 and pass_rate is not None and pass_rate >= 75.0:
            gap_status = "STRENGTH"
            status_label = "Demonstrated Strength (>=75% Pass Rate)"
            severity = "LOW"
            recommendation = f"Maintain curriculum excellence; candidate cohort demonstrates strong proficiency."
        elif demand == 0 and pass_rate is not None and pass_rate >= 75.0:
            gap_status = "STRENGTH"
            status_label = "Adequate Proficiency"
            severity = "LOW"
            recommendation = f"Proficiency verified; monitor for future employer hiring demand."
        else:
            gap_status = "MONITORING"
            status_label = "Monitoring Required"
            severity = "MEDIUM"
            recommendation = f"Gather additional test attempts and mock interview evaluations for {skill}."

        if gap_status == "STRENGTH":
            coverage_category = "EVALUATED_WELL"
        else:
            coverage_category = gap_status

        companies_count = len(skill_company_references.get(skill, set()))

        skill_matrix.append({
            "skill": skill,
            "skill_name": skill,
            "jobs_requiring": demand,
            "market_demand_jobs_count": demand,
            "companies_requiring": companies_count,
            "jobs_referencing": skill_job_references.get(skill, [])[:3],
            "assessment_tests_count": skill_assessment_stats.get(skill, {}).get("tests_count", 0),
            "total_attempts": total_att,
            "assessment_attempts_count": total_att,
            "passed_attempts": passed_att,
            "pass_percentage": round(pass_rate, 2) if pass_rate is not None else 0.0,
            "assessment_pass_rate": pass_rate,
            "average_assessment_score": avg_score,
            "data_coverage_level": coverage,
            "gap_status": gap_status,
            "coverage_category": coverage_category,
            "status_label": status_label,
            "severity": severity,
            "recommendation": recommendation,
            "evidence_based_recommendation": recommendation,
        })

    # Summary Statistics
    critical_count = sum(1 for s in skill_matrix if s["gap_status"] == "CRITICAL_GAP")
    unassessed_count = sum(1 for s in skill_matrix if s["gap_status"] == "UNASSESSED_DEMAND")
    moderate_count = sum(1 for s in skill_matrix if s["gap_status"] == "MODERATE_GAP")
    strength_count = sum(1 for s in skill_matrix if s["gap_status"] == "STRENGTH")

    return {
        "summary": {
            "total_skills_evaluated": len(skill_matrix),
            "critical_gaps_count": critical_count,
            "unassessed_demand_count": unassessed_count,
            "moderate_gaps_count": moderate_count,
            "strengths_count": strength_count,
            "total_jobs_analyzed": jobs_qs.count(),
            "total_assessment_attempts_analyzed": attempts_qs.count(),
            "total_mock_evaluations_analyzed": mock_total,
            "mock_benchmarks": {
                "avg_technical_competence": mock_avg_technical,
                "avg_problem_solving": mock_avg_problem_solving,
                "avg_communication_clarity": mock_avg_communication,
            },
        },
        "total_market_demand_skills": sum(1 for s in skill_matrix if s["jobs_requiring"] > 0),
        "total_assessed_skills": sum(1 for s in skill_matrix if s["total_attempts"] > 0),
        "unassessed_high_demand_skills": unassessed_count,
        "critical_gap_skills": critical_count,
        "ai_disclaimer": "All skill gaps derived deterministically from authoritative job requirements, student assessment attempts, and mock interview scorecards. No predictive AI or probabilistic candidate ranking applied.",
        "methodology_disclaimer": "All skill gaps derived deterministically from authoritative job requirements, student assessment attempts, and mock interview scorecards. No predictive AI or probabilistic candidate ranking applied.",
        "skill_matrix": skill_matrix,
        "generated_at": timezone.now().isoformat(),
    }


# =========================================================================
# CAPABILITY D: Strategic Training Plans
# =========================================================================
def get_training_plans_dataset(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Retrieve structured continuous improvement training plans and status."""
    filters = filters or {}
    plans_qs = TrainingPlan.objects.select_related(
        "responsible_trainer",
        "approved_by",
        "created_by",
    ).prefetch_related("linked_cycle_actions")

    if filters.get("status"):
        plans_qs = plans_qs.filter(status=filters["status"])
    if filters.get("target_skill"):
        plans_qs = plans_qs.filter(target_skill__icontains=filters["target_skill"])
    if filters.get("responsible_trainer_id"):
        plans_qs = plans_qs.filter(responsible_trainer_id=filters["responsible_trainer_id"])

    plans_list = []
    for p in plans_qs:
        plan_code = f"TRP-{str(p.id)[:8].upper()}"
        plans_list.append({
            "id": str(p.id),
            "plan_code": plan_code,
            "title": p.title,
            "target_skill": p.target_skill,
            "motivation_evidence": p.motivation_evidence,
            "evidence_rationale": p.motivation_evidence,
            "target_cohort": p.target_cohort,
            "proposed_objectives": p.proposed_objectives,
            "planned_sessions_count": p.planned_sessions_count,
            "responsible_trainer_id": str(p.responsible_trainer.id),
            "responsible_trainer_name": p.responsible_trainer.full_name or p.responsible_trainer.username,
            "planned_start_date": p.planned_start_date.isoformat(),
            "planned_end_date": p.planned_end_date.isoformat(),
            "start_date": p.planned_start_date.isoformat(),
            "end_date": p.planned_end_date.isoformat(),
            "status": p.status,
            "status_display": p.get_status_display(),
            "expected_outcome": p.expected_outcome,
            "actual_completion_results": p.actual_completion_results,
            "cancellation_reason": p.cancellation_reason,
            "approval_notes": p.cancellation_reason,
            "approved_by_name": p.approved_by.full_name if p.approved_by else None,
            "approved_at": p.approved_at.isoformat() if p.approved_at else None,
            "created_by_name": p.created_by.full_name or p.created_by.username,
            "created_at": p.created_at.isoformat(),
            "updated_at": p.updated_at.isoformat(),
            "linked_actions_count": p.linked_cycle_actions.count(),
        })

    status_counts = {
        TrainingPlanStatus.DRAFT: plans_qs.filter(status=TrainingPlanStatus.DRAFT).count(),
        TrainingPlanStatus.PROPOSED: plans_qs.filter(status=TrainingPlanStatus.PROPOSED).count(),
        TrainingPlanStatus.APPROVED: plans_qs.filter(status=TrainingPlanStatus.APPROVED).count(),
        TrainingPlanStatus.SCHEDULED: plans_qs.filter(status=TrainingPlanStatus.SCHEDULED).count(),
        TrainingPlanStatus.IN_PROGRESS: plans_qs.filter(status=TrainingPlanStatus.IN_PROGRESS).count(),
        TrainingPlanStatus.COMPLETED: plans_qs.filter(status=TrainingPlanStatus.COMPLETED).count(),
        TrainingPlanStatus.CANCELLED: plans_qs.filter(status=TrainingPlanStatus.CANCELLED).count(),
    }

    return {
        "summary": {
            "total_plans": plans_qs.count(),
            "status_counts": status_counts,
        },
        "training_plans": plans_list,
        "generated_at": timezone.now().isoformat(),
    }


# =========================================================================
# CAPABILITY E: Recruitment Cycle Reviews & Actions
# =========================================================================
def get_recruitment_cycle_reviews_dataset(
    filters: Optional[Dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> Dict[str, Any]:
    """Retrieve recruitment cycle reviews, baseline metric snapshots, and improvement action items."""
    filters = filters or {}
    reviews_qs = RecruitmentCycleReview.objects.select_related(
        "approved_by",
        "created_by",
    ).prefetch_related("actions__assigned_to", "actions__linked_training_plan")

    if filters.get("cohort_year"):
        reviews_qs = reviews_qs.filter(cohort_year=filters["cohort_year"])
    if filters.get("status"):
        reviews_qs = reviews_qs.filter(status=filters["status"])

    reviews_list = []
    for r in reviews_qs:
        actions_list = []
        for a in r.actions.all():
            actions_list.append({
                "id": a.id,
                "action_title": a.action_title,
                "category": a.category,
                "category_display": a.get_category_display(),
                "description": a.description,
                "target_completion_date": a.target_completion_date.isoformat(),
                "assigned_to_id": a.assigned_to.id if a.assigned_to else None,
                "assigned_to_name": a.assigned_to.full_name if a.assigned_to else "Unassigned",
                "status": a.status,
                "status_display": a.get_status_display(),
                "linked_training_plan_id": a.linked_training_plan_id,
                "linked_training_plan_title": a.linked_training_plan.title if a.linked_training_plan else None,
                "resolution_notes": a.resolution_notes,
                "created_at": a.created_at.isoformat(),
            })

        reviews_list.append({
            "id": r.id,
            "title": r.title,
            "cohort_year": r.cohort_year,
            "review_period_start": r.review_period_start.isoformat(),
            "review_period_end": r.review_period_end.isoformat(),
            "status": r.status,
            "status_display": r.get_status_display(),
            "baseline_metrics": r.baseline_metrics,
            "target_goals": r.target_goals,
            "placement_outcomes_summary": r.placement_outcomes_summary,
            "feedback_summary": r.feedback_summary,
            "skill_gaps_identified": r.skill_gaps_identified,
            "approved_by_name": r.approved_by.full_name if r.approved_by else None,
            "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            "created_by_name": r.created_by.full_name or r.created_by.username,
            "created_at": r.created_at.isoformat(),
            "actions": actions_list,
            "total_actions": len(actions_list),
            "completed_actions": sum(1 for act in actions_list if act["status"] == CycleActionStatus.COMPLETED),
        })

    return {
        "summary": {
            "total_cycle_reviews": reviews_qs.count(),
            "total_action_items": CycleImprovementAction.objects.count(),
            "completed_actions": CycleImprovementAction.objects.filter(status=CycleActionStatus.COMPLETED).count(),
            "pending_actions": CycleImprovementAction.objects.filter(status=CycleActionStatus.PENDING).count(),
        },
        "cycle_reviews": reviews_list,
        "generated_at": timezone.now().isoformat(),
    }


# =========================================================================
# DATA QUALITY & INTEGRITY DIAGNOSTICS
# =========================================================================
def get_continuous_improvement_diagnostics() -> Dict[str, Any]:
    """Execute 6-point data quality and continuous improvement diagnostics scan."""
    now = timezone.now()
    today = now.date()

    # 1. Unresolved Placement Outcomes (Selected > 14 days without active offer letter)
    selected_status_without_offer = CandidatePlacementStatus.objects.filter(
        status=CandidatePlacementStatusChoices.SELECTED,
        offer_letter__isnull=True,
    ).count()

    # 2. Completed Interviews Lacking Feedback
    conducted_interviews_no_student_fb = InterviewSchedule.objects.filter(
        conducted_status=ConductedStatus.CONDUCTED,
        student_feedback__isnull=True,
    ).count()

    # 3. High Demand Job Requirements Lacking Detailed Skills Required
    jobs_missing_skills = JobRequirement.objects.filter(
        Q(skills_required="") | Q(skills_required__isnull=True)
    ).count()

    # 4. Completed Mock Interviews Lacking Scorecards
    mocks_completed_no_eval = MockInterview.objects.filter(
        status=MockInterviewStatus.COMPLETED,
        evaluation__isnull=True,
    ).count()

    # 5. Overdue Training Plans
    overdue_training_plans = TrainingPlan.objects.filter(
        planned_end_date__lt=today,
        status__in=[TrainingPlanStatus.SCHEDULED, TrainingPlanStatus.IN_PROGRESS],
    ).count()

    # 6. Overdue Cycle Improvement Actions
    overdue_cycle_actions = CycleImprovementAction.objects.filter(
        target_completion_date__lt=today,
        status__in=[CycleActionStatus.PENDING, CycleActionStatus.IN_PROGRESS],
    ).count()

    total_violations = (
        selected_status_without_offer
        + conducted_interviews_no_student_fb
        + jobs_missing_skills
        + mocks_completed_no_eval
        + overdue_training_plans
        + overdue_cycle_actions
    )

    # Health Score (0 - 100%)
    health_score = max(0, 100 - (total_violations * 5))

    checks = [
        {
            "code": "UNRESOLVED_OFFERS",
            "title": "Selected Candidates Lacking Uploaded Offer Letters",
            "violations_count": selected_status_without_offer,
            "status": "PASS" if selected_status_without_offer == 0 else "WARNING",
            "description": "Selected candidates should have verified offer letters uploaded in private storage (Step 39).",
        },
        {
            "code": "MISSING_STUDENT_FEEDBACK",
            "title": "Conducted Interviews Missing Student Feedback",
            "violations_count": conducted_interviews_no_student_fb,
            "status": "PASS" if conducted_interviews_no_student_fb == 0 else "INFO",
            "description": "Candidates who attended interviews should record their interview difficulty and technical questions.",
        },
        {
            "code": "JOBS_MISSING_SKILLS",
            "title": "Job Requirements Lacking Detailed Skills Required",
            "violations_count": jobs_missing_skills,
            "status": "PASS" if jobs_missing_skills == 0 else "WARNING",
            "description": "Every job requirement must record explicit technical skills for curriculum and gap alignment.",
        },
        {
            "code": "MOCKS_MISSING_EVALUATION",
            "title": "Concluded Mock Interviews Lacking Rubric Scorecards",
            "violations_count": mocks_completed_no_eval,
            "status": "PASS" if mocks_completed_no_eval == 0 else "WARNING",
            "description": "Evaluators must submit mock scorecards with domain and communication rubrics (Step 22).",
        },
        {
            "code": "OVERDUE_TRAINING_PLANS",
            "title": "Training Plans Past Target Completion Date",
            "violations_count": overdue_training_plans,
            "status": "PASS" if overdue_training_plans == 0 else "WARNING",
            "description": "Training plans past their end date should have empirical completion results recorded.",
        },
        {
            "code": "OVERDUE_CYCLE_ACTIONS",
            "title": "Cycle Improvement Actions Overdue",
            "violations_count": overdue_cycle_actions,
            "status": "PASS" if overdue_cycle_actions == 0 else "WARNING",
            "description": "Action items arising from recruitment reviews must be executed by assigned owners.",
        },
    ]

    return {
        "health_score": health_score,
        "total_anomalies": total_violations,
        "checks": checks,
        "scanned_at": now.isoformat(),
    }
