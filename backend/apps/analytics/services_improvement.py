"""Services for Continuous Improvement & Strategic Planning (Phase 13).

Encapsulates business operations, transactional state machines, permission-guarded approvals,
and formula-injection-safe CSV exports.
"""
from datetime import date, datetime
import io
import csv
from typing import Any, Dict, Optional

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.accounts.models import RoleCatalog, User
from apps.analytics.models import (
    CycleActionCategory,
    CycleActionStatus,
    CycleImprovementAction,
    RecruitmentCycleReview,
    RecruitmentCycleStatus,
    TrainingPlan,
    TrainingPlanStatus,
)
from apps.analytics.selectors_improvement import get_placement_rate_analytics
from apps.core.models import AuditLog


# Safe CSV sanitization (Formula Injection Prevention: =, +, -, @, \t, \r)
DANGEROUS_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _sanitize_csv_cell(val: Any) -> str:
    s = str(val if val is not None else "")
    if s.startswith(DANGEROUS_PREFIXES):
        return f"'{s}"
    return s


# =========================================================================
# 1. Training Plan Services (Capability D)
# =========================================================================
@transaction.atomic
def create_training_plan(data: Dict[str, Any], user: User) -> TrainingPlan:
    """Create a new remedial training plan motivated by skill gaps and feedback."""
    title = data.get("title", "").strip()
    target_skill = data.get("target_skill", "").strip()
    motivation = data.get("motivation_evidence", "").strip()
    target_cohort = data.get("target_cohort", "").strip()
    objectives = data.get("proposed_objectives", "").strip()
    expected_outcome = data.get("expected_outcome", "").strip()
    planned_sessions = int(data.get("planned_sessions_count", 1))

    if not title or not target_skill or not motivation or not target_cohort:
        raise ValidationError("Title, target skill, motivation evidence, and target cohort are required.")

    start_date = data.get("planned_start_date")
    end_date = data.get("planned_end_date")
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    if start_date and end_date and start_date > end_date:
        raise ValidationError("Planned start date cannot be after planned end date.")

    responsible_trainer_id = data.get("responsible_trainer_id")
    if not responsible_trainer_id:
        # Default to current user if they are a trainer/staff, or raise
        responsible_trainer = user
    else:
        try:
            responsible_trainer = User.objects.get(id=responsible_trainer_id)
        except User.DoesNotExist:
            raise ValidationError(f"Responsible trainer with ID {responsible_trainer_id} does not exist.")

    initial_status = data.get("status", TrainingPlanStatus.DRAFT)
    if initial_status not in [TrainingPlanStatus.DRAFT, TrainingPlanStatus.PROPOSED]:
        initial_status = TrainingPlanStatus.DRAFT

    plan = TrainingPlan.objects.create(
        title=title,
        target_skill=target_skill,
        motivation_evidence=motivation,
        target_cohort=target_cohort,
        proposed_objectives=objectives,
        planned_sessions_count=planned_sessions,
        responsible_trainer=responsible_trainer,
        planned_start_date=start_date,
        planned_end_date=end_date,
        status=initial_status,
        expected_outcome=expected_outcome,
        created_by=user,
    )

    AuditLog.objects.create(
        user=user,
        action="TRAINING_PLAN_CREATED",
        resource_type="TrainingPlan",
        resource_id=str(plan.id),
        changes={"title": plan.title, "target_skill": plan.target_skill, "status": plan.status},
    )

    return plan


@transaction.atomic
def update_training_plan_status(
    plan: TrainingPlan,
    new_status: str,
    user: User,
    notes: str = "",
    actual_results: str = "",
    cancellation_reason: str = "",
) -> TrainingPlan:
    """Transition a training plan through its authorized lifecycle."""
    valid_transitions = {
        TrainingPlanStatus.DRAFT: [TrainingPlanStatus.PROPOSED, TrainingPlanStatus.CANCELLED],
        TrainingPlanStatus.PROPOSED: [TrainingPlanStatus.APPROVED, TrainingPlanStatus.DRAFT, TrainingPlanStatus.CANCELLED],
        TrainingPlanStatus.APPROVED: [TrainingPlanStatus.SCHEDULED, TrainingPlanStatus.IN_PROGRESS, TrainingPlanStatus.CANCELLED],
        TrainingPlanStatus.SCHEDULED: [TrainingPlanStatus.IN_PROGRESS, TrainingPlanStatus.CANCELLED],
        TrainingPlanStatus.IN_PROGRESS: [TrainingPlanStatus.COMPLETED, TrainingPlanStatus.CANCELLED],
        TrainingPlanStatus.COMPLETED: [],
        TrainingPlanStatus.CANCELLED: [],
    }

    allowed = valid_transitions.get(plan.status, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Invalid status transition from {plan.status} to {new_status}. Allowed transitions: {allowed}"
        )

    # Permission Gate: Only Placement Head or Admin can approve plans
    if new_status == TrainingPlanStatus.APPROVED:
        is_authorized = user.is_superuser or user.has_any_role(
            RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD
        )
        if not is_authorized:
            raise PermissionDenied("Only Placement Head or Admin can formally approve a training plan.")
        plan.approved_by = user
        plan.approved_at = timezone.now()

    if new_status == TrainingPlanStatus.COMPLETED:
        if not actual_results and not plan.actual_completion_results:
            raise ValidationError("Actual completion results must be documented when completing a plan.")
        if actual_results:
            plan.actual_completion_results = actual_results.strip()

    if new_status == TrainingPlanStatus.CANCELLED:
        if not cancellation_reason:
            raise ValidationError("A cancellation reason must be provided when revoking a training plan.")
        plan.cancellation_reason = cancellation_reason.strip()

    old_status = plan.status
    plan.status = new_status
    plan.save()

    AuditLog.objects.create(
        user=user,
        action="TRAINING_PLAN_STATUS_UPDATED",
        resource_type="TrainingPlan",
        resource_id=str(plan.id),
        changes={"old_status": old_status, "new_status": new_status, "notes": notes},
    )

    return plan


# =========================================================================
# 2. Recruitment Cycle Review Services (Capability E)
# =========================================================================
@transaction.atomic
def create_recruitment_cycle_review(data: Dict[str, Any], user: User) -> RecruitmentCycleReview:
    """Initiate a recruitment cycle review with an immutable baseline metric snapshot."""
    title = data.get("title", "").strip()
    cohort_year = int(data.get("cohort_year", timezone.now().year))
    start_date = data.get("review_period_start")
    end_date = data.get("review_period_end")

    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

    if not title:
        raise ValidationError("Title is required for a recruitment cycle review.")

    # Automatically capture empirical baseline metrics snapshot for the cohort
    baseline_analytics = get_placement_rate_analytics(filters={"cohort_year": cohort_year}, user=user)
    baseline_summary = baseline_analytics.get("summary", {})

    target_goals = data.get("target_goals", {})
    if not isinstance(target_goals, dict):
        target_goals = {}

    review = RecruitmentCycleReview.objects.create(
        title=title,
        cohort_year=cohort_year,
        review_period_start=start_date,
        review_period_end=end_date,
        status=RecruitmentCycleStatus.DRAFT,
        baseline_metrics=baseline_summary,
        target_goals=target_goals,
        placement_outcomes_summary=data.get("placement_outcomes_summary", "").strip(),
        feedback_summary=data.get("feedback_summary", "").strip(),
        skill_gaps_identified=data.get("skill_gaps_identified", "").strip(),
        created_by=user,
    )

    AuditLog.objects.create(
        user=user,
        action="RECRUITMENT_CYCLE_REVIEW_CREATED",
        resource_type="RecruitmentCycleReview",
        resource_id=str(review.id),
        changes={"title": review.title, "cohort_year": review.cohort_year},
    )

    return review


@transaction.atomic
def update_recruitment_cycle_status(
    review: RecruitmentCycleReview,
    new_status: str,
    user: User,
) -> RecruitmentCycleReview:
    """Transition a recruitment cycle review through its review cycle."""
    valid_transitions = {
        RecruitmentCycleStatus.DRAFT: [RecruitmentCycleStatus.IN_REVIEW],
        RecruitmentCycleStatus.IN_REVIEW: [RecruitmentCycleStatus.APPROVED, RecruitmentCycleStatus.DRAFT],
        RecruitmentCycleStatus.APPROVED: [RecruitmentCycleStatus.CLOSED],
        RecruitmentCycleStatus.CLOSED: [],
    }

    allowed = valid_transitions.get(review.status, [])
    if new_status not in allowed:
        raise ValidationError(
            f"Invalid cycle review transition from {review.status} to {new_status}. Allowed: {allowed}"
        )

    if new_status == RecruitmentCycleStatus.APPROVED:
        is_authorized = user.is_superuser or user.has_any_role(
            RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD
        )
        if not is_authorized:
            raise PermissionDenied("Only Placement Head or Admin can approve a recruitment cycle review.")
        review.approved_by = user
        review.approved_at = timezone.now()

    old_status = review.status
    review.status = new_status
    review.save()

    AuditLog.objects.create(
        user=user,
        action="RECRUITMENT_CYCLE_STATUS_UPDATED",
        resource_type="RecruitmentCycleReview",
        resource_id=str(review.id),
        changes={"old_status": old_status, "new_status": new_status},
    )

    return review


@transaction.atomic
def create_cycle_improvement_action(
    review: RecruitmentCycleReview,
    data: Dict[str, Any],
    user: User,
) -> CycleImprovementAction:
    """Create a trackable improvement action item linked to a cycle review."""
    title = data.get("action_title", "").strip()
    category = data.get("category", CycleActionCategory.REMEDIAL_TRAINING)
    description = data.get("description", "").strip()
    target_date = data.get("target_completion_date")

    if not title or not description or not target_date:
        raise ValidationError("Action title, description, and target completion date are required.")

    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

    assigned_to = None
    if data.get("assigned_to_id"):
        assigned_to = User.objects.filter(id=data["assigned_to_id"]).first()

    linked_plan = None
    if data.get("linked_training_plan_id"):
        linked_plan = TrainingPlan.objects.filter(id=data["linked_training_plan_id"]).first()

    action = CycleImprovementAction.objects.create(
        cycle_review=review,
        action_title=title,
        category=category,
        description=description,
        target_completion_date=target_date,
        assigned_to=assigned_to,
        status=CycleActionStatus.PENDING,
        linked_training_plan=linked_plan,
        created_by=user,
    )

    AuditLog.objects.create(
        user=user,
        action="CYCLE_ACTION_CREATED",
        resource_type="CycleImprovementAction",
        resource_id=str(action.id),
        changes={"action_title": action.action_title, "category": action.category},
    )

    return action


@transaction.atomic
def update_cycle_improvement_action_status(
    action: CycleImprovementAction,
    new_status: str,
    user: User,
    resolution_notes: str = "",
) -> CycleImprovementAction:
    """Update action status and document resolution evidence."""
    if new_status not in [c[0] for c in CycleActionStatus.CHOICES]:
        raise ValidationError(f"Invalid status {new_status}.")

    action.status = new_status
    if resolution_notes:
        action.resolution_notes = resolution_notes.strip()
    action.save()

    AuditLog.objects.create(
        user=user,
        action="CYCLE_ACTION_STATUS_UPDATED",
        resource_type="CycleImprovementAction",
        resource_id=str(action.id),
        changes={"new_status": new_status, "notes": resolution_notes},
    )

    return action


# =========================================================================
# 3. Safe Sanitized CSV Export Services
# =========================================================================
def export_placement_rate_csv(dataset: Dict[str, Any]) -> str:
    """Generate safe, injection-sanitized CSV for Placement Rate Analytics."""
    output = io.StringIO()
    writer = csv.writer(output)

    # 1. KPI Summary Block
    writer.writerow([_sanitize_csv_cell("GQT HRMS — Continuous Improvement: Placement Rate Analytics")])
    writer.writerow([_sanitize_csv_cell(f"Generated At: {dataset.get('generated_at', '')}")])
    writer.writerow([])

    summary = dataset.get("summary", {})
    writer.writerow([_sanitize_csv_cell("Metric Name"), _sanitize_csv_cell("Value"), _sanitize_csv_cell("Unit / Formula")])
    writer.writerow([_sanitize_csv_cell("Total Cohort Students"), _sanitize_csv_cell(summary.get("total_cohort_students", 0)), _sanitize_csv_cell("Headcount")])
    writer.writerow([_sanitize_csv_cell("Total Eligible Students"), _sanitize_csv_cell(summary.get("total_eligible_students", 0)), _sanitize_csv_cell("Verified Headcount")])
    writer.writerow([_sanitize_csv_cell("Distinct Students Applied"), _sanitize_csv_cell(summary.get("distinct_students_applied", 0)), _sanitize_csv_cell("Applicants")])
    writer.writerow([_sanitize_csv_cell("Distinct Students Interviewed"), _sanitize_csv_cell(summary.get("distinct_students_interviewed", 0)), _sanitize_csv_cell("Conducted")])
    writer.writerow([_sanitize_csv_cell("Distinct Students Selected"), _sanitize_csv_cell(summary.get("distinct_students_selected", 0)), _sanitize_csv_cell("Selected Candidates")])
    writer.writerow([_sanitize_csv_cell("Eligible Cohort Placement Rate"), _sanitize_csv_cell(f"{summary.get('placement_rate_eligible', 0.0)}%"), _sanitize_csv_cell("(Selected / Eligible) * 100")])
    writer.writerow([_sanitize_csv_cell("Applicant Placement Rate"), _sanitize_csv_cell(f"{summary.get('placement_rate_applicants', 0.0)}%"), _sanitize_csv_cell("(Selected / Applied) * 100")])
    writer.writerow([_sanitize_csv_cell("Interview Selection Rate"), _sanitize_csv_cell(f"{summary.get('interview_selection_rate', 0.0)}%"), _sanitize_csv_cell("(Selected / Interviewed) * 100")])
    writer.writerow([_sanitize_csv_cell("Offer Acceptance Rate"), _sanitize_csv_cell(f"{summary.get('offer_acceptance_rate', 0.0)}%"), _sanitize_csv_cell("(Accepted Offers / Resolved) * 100")])
    writer.writerow([_sanitize_csv_cell("Joining Rate"), _sanitize_csv_cell(f"{summary.get('joining_rate', 0.0)}%"), _sanitize_csv_cell("(Joined / Accepted) * 100")])
    writer.writerow([_sanitize_csv_cell("Overall Pipeline Yield"), _sanitize_csv_cell(f"{summary.get('overall_pipeline_yield', 0.0)}%"), _sanitize_csv_cell("(Joined / Eligible Base) * 100")])
    writer.writerow([])

    # 2. Department Breakdown
    writer.writerow([_sanitize_csv_cell("Department Breakdown")])
    writer.writerow([
        _sanitize_csv_cell("Department"),
        _sanitize_csv_cell("Total Students"),
        _sanitize_csv_cell("Applied"),
        _sanitize_csv_cell("Selected"),
        _sanitize_csv_cell("Joined"),
        _sanitize_csv_cell("Placement Rate (%)"),
    ])
    for row in dataset.get("department_breakdown", []):
        writer.writerow([
            _sanitize_csv_cell(row.get("department", "")),
            _sanitize_csv_cell(row.get("total_students", 0)),
            _sanitize_csv_cell(row.get("applied_students", 0)),
            _sanitize_csv_cell(row.get("selected_students", 0)),
            _sanitize_csv_cell(row.get("joined_students", 0)),
            _sanitize_csv_cell(f"{row.get('placement_rate', 0.0)}%"),
        ])

    return output.getvalue()


def export_skill_gaps_csv(dataset: Dict[str, Any]) -> str:
    """Generate safe, injection-sanitized CSV for Skill Gap Matrix."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([_sanitize_csv_cell("GQT HRMS — Continuous Improvement: Evidence-Based Skill Gap Matrix")])
    writer.writerow([_sanitize_csv_cell(f"Generated At: {dataset.get('generated_at', '')}")])
    writer.writerow([])

    writer.writerow([
        _sanitize_csv_cell("Skill / Competency"),
        _sanitize_csv_cell("Market Demand (Jobs)"),
        _sanitize_csv_cell("Assessment Attempts"),
        _sanitize_csv_cell("Pass Rate (%)"),
        _sanitize_csv_cell("Average Score (%)"),
        _sanitize_csv_cell("Data Coverage"),
        _sanitize_csv_cell("Gap Status"),
        _sanitize_csv_cell("Severity"),
        _sanitize_csv_cell("Actionable Recommendation"),
    ])

    for row in dataset.get("skill_matrix", []):
        pr = f"{row['assessment_pass_rate']}%" if row.get("assessment_pass_rate") is not None else "N/A (Unassessed)"
        sc = f"{row['average_assessment_score']}%" if row.get("average_assessment_score") is not None else "N/A"
        writer.writerow([
            _sanitize_csv_cell(row.get("skill_name", "")),
            _sanitize_csv_cell(row.get("market_demand_jobs_count", 0)),
            _sanitize_csv_cell(row.get("assessment_attempts_count", 0)),
            _sanitize_csv_cell(pr),
            _sanitize_csv_cell(sc),
            _sanitize_csv_cell(row.get("data_coverage_level", "")),
            _sanitize_csv_cell(row.get("gap_status", "")),
            _sanitize_csv_cell(row.get("severity", "")),
            _sanitize_csv_cell(row.get("evidence_based_recommendation", "")),
        ])

    return output.getvalue()


def export_training_plans_csv(dataset: Dict[str, Any]) -> str:
    """Generate safe, injection-sanitized CSV for Training Plans."""
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([_sanitize_csv_cell("GQT HRMS — Continuous Improvement: Remedial Training Plans")])
    writer.writerow([_sanitize_csv_cell(f"Generated At: {dataset.get('generated_at', '')}")])
    writer.writerow([])

    writer.writerow([
        _sanitize_csv_cell("Plan Title"),
        _sanitize_csv_cell("Target Skill"),
        _sanitize_csv_cell("Target Cohort"),
        _sanitize_csv_cell("Responsible Trainer"),
        _sanitize_csv_cell("Start Date"),
        _sanitize_csv_cell("End Date"),
        _sanitize_csv_cell("Status"),
        _sanitize_csv_cell("Approved By"),
        _sanitize_csv_cell("Expected Outcome"),
        _sanitize_csv_cell("Actual Results"),
    ])

    for row in dataset.get("training_plans", []):
        writer.writerow([
            _sanitize_csv_cell(row.get("title", "")),
            _sanitize_csv_cell(row.get("target_skill", "")),
            _sanitize_csv_cell(row.get("target_cohort", "")),
            _sanitize_csv_cell(row.get("responsible_trainer_name", "")),
            _sanitize_csv_cell(row.get("planned_start_date", "")),
            _sanitize_csv_cell(row.get("planned_end_date", "")),
            _sanitize_csv_cell(row.get("status_display", "")),
            _sanitize_csv_cell(row.get("approved_by_name", "Pending Approval")),
            _sanitize_csv_cell(row.get("expected_outcome", "")),
            _sanitize_csv_cell(row.get("actual_completion_results", "")),
        ])

    return output.getvalue()
