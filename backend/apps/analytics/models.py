"""Domain Models for Continuous Improvement & Strategic Planning (Phase 13).

Authoritative GQT HRMS Continuous Improvement Responsibilities:
1. Analyze placement rate (granular cohort outcomes, multi-offers, distinct student funnels).
2. Analyze feedback (cross-category ratings, difficulty perceptions, suggestions, anonymity preservation).
3. Identify skill gaps (market demand vs assessment performance, mock interview rubric gaps, trainer feedback).
4. Plan new training (structured remedial interventions, syllabus revisions, Placement Head approval gate).
5. Repeat the recruitment cycle (cycle reviews, baseline metric snapshots, actionable improvement items).
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


class TrainingPlanStatus:
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (DRAFT, "Draft — In Preparation"),
        (PROPOSED, "Proposed — Awaiting Placement Head Review"),
        (APPROVED, "Approved — Authorized by Placement Head"),
        (SCHEDULED, "Scheduled — Dates & Trainer Confirmed"),
        (IN_PROGRESS, "In Progress — Training Underway"),
        (COMPLETED, "Completed — Concluded & Results Recorded"),
        (CANCELLED, "Cancelled — Plan Revoked"),
    )


class RecruitmentCycleStatus:
    DRAFT = "DRAFT"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"

    CHOICES = (
        (DRAFT, "Draft — Review Being Compiled"),
        (IN_REVIEW, "In Review — Under Committee Review"),
        (APPROVED, "Approved — Actions Authorized"),
        (CLOSED, "Closed — Cycle Concluded"),
    )


class CycleActionCategory:
    CURRICULUM_UPDATE = "CURRICULUM_UPDATE"
    REMEDIAL_TRAINING = "REMEDIAL_TRAINING"
    CUTOFF_REFINEMENT = "CUTOFF_REFINEMENT"
    RECRUITER_ENGAGEMENT = "RECRUITER_ENGAGEMENT"
    PROCESS_OPTIMIZATION = "PROCESS_OPTIMIZATION"

    CHOICES = (
        (CURRICULUM_UPDATE, "Curriculum & Syllabus Update"),
        (REMEDIAL_TRAINING, "Remedial Skill Training"),
        (CUTOFF_REFINEMENT, "Eligibility & Cutoff Refinement"),
        (RECRUITER_ENGAGEMENT, "Recruiter Relationship Outreach"),
        (PROCESS_OPTIMIZATION, "Interview & Drive Process Optimization"),
    )


class CycleActionStatus:
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    DEFERRED = "DEFERRED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (PENDING, "Pending"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (DEFERRED, "Deferred"),
        (CANCELLED, "Cancelled"),
    )


class TrainingPlan(TimeStampedModel):
    """Structured training and syllabus intervention plan motivated by skill gap & feedback evidence (Capability D)."""

    title = models.CharField(
        max_length=255,
        help_text="Title of the training intervention (e.g. Remedial Workshop: Advanced Data Structures).",
    )
    target_skill = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Normalized skill or domain competency being addressed (e.g. Python, SQL, DSA).",
    )
    motivation_evidence = models.TextField(
        help_text="Defensible evidence or feedback motivating this plan (e.g. Low pass rate on technical test, recruiter remarks).",
    )
    target_cohort = models.CharField(
        max_length=255,
        help_text="Targeted student cohort (e.g. 2025 Passing Out Batch - Computer Science).",
    )
    proposed_objectives = models.TextField(
        help_text="Structured learning objectives, topics covered, and pedagogy.",
    )
    planned_sessions_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of planned sessions or workshops.",
    )
    responsible_trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="responsible_training_plans",
        help_text="Lead trainer or faculty member responsible for delivering the plan.",
    )
    planned_start_date = models.DateField(
        help_text="Planned start date for the training.",
    )
    planned_end_date = models.DateField(
        help_text="Planned completion date for the training.",
    )
    status = models.CharField(
        max_length=32,
        choices=TrainingPlanStatus.CHOICES,
        default=TrainingPlanStatus.DRAFT,
        db_index=True,
        help_text="Lifecycle state of the training plan.",
    )
    expected_outcome = models.TextField(
        help_text="Measurable expected outcome and target post-training assessment benchmark.",
    )
    actual_completion_results = models.TextField(
        blank=True,
        default="",
        help_text="Empirical results, attendance count, and evaluation scores recorded upon conclusion.",
    )
    cancellation_reason = models.TextField(
        blank=True,
        default="",
        help_text="Documented rationale if the training plan was cancelled.",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_training_plans",
        help_text="Placement Head or Admin who formally authorized this plan.",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of formal approval.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_training_plans",
        help_text="User who drafted this training plan.",
    )

    class Meta:
        db_table = "analytics_training_plan"
        ordering = ["-planned_start_date", "-created_at"]
        indexes = [
            models.Index(fields=["target_skill", "status"]),
            models.Index(fields=["status", "planned_start_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} [{self.target_skill}] ({self.get_status_display()})"


class RecruitmentCycleReview(TimeStampedModel):
    """Institutional review and continuous improvement assessment for a recruitment cycle (Capability E)."""

    title = models.CharField(
        max_length=255,
        help_text="Title of the recruitment cycle review (e.g. Annual Recruitment Cycle Review 2025-2026).",
    )
    cohort_year = models.PositiveIntegerField(
        db_index=True,
        help_text="Graduation year / passing out batch analyzed (e.g. 2025).",
    )
    review_period_start = models.DateField(
        help_text="Start date of the reviewed recruitment period.",
    )
    review_period_end = models.DateField(
        help_text="End date of the reviewed recruitment period.",
    )
    status = models.CharField(
        max_length=32,
        choices=RecruitmentCycleStatus.CHOICES,
        default=RecruitmentCycleStatus.DRAFT,
        db_index=True,
        help_text="Review lifecycle status.",
    )
    baseline_metrics = models.JSONField(
        default=dict,
        help_text="Immutable baseline metrics snapshot captured at review creation (placement rate, CTC, conversion rates).",
    )
    target_goals = models.JSONField(
        default=dict,
        help_text="Institutional target goals for the next cycle (e.g. target placement rate, CTC benchmark).",
    )
    placement_outcomes_summary = models.TextField(
        blank=True,
        default="",
        help_text="Analytical summary of placement rates, offers accepted, and joining metrics.",
    )
    feedback_summary = models.TextField(
        blank=True,
        default="",
        help_text="Summary of student, corporate HR, and trainer feedback observations.",
    )
    skill_gaps_identified = models.TextField(
        blank=True,
        default="",
        help_text="Primary technical, aptitude, or communication skill gaps identified across drives.",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_cycle_reviews",
        help_text="Placement Head or Admin who authorized the cycle review findings.",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of approval.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_cycle_reviews",
        help_text="Staff member who compiled the cycle review.",
    )

    class Meta:
        db_table = "analytics_cycle_review"
        ordering = ["-cohort_year", "-created_at"]
        indexes = [
            models.Index(fields=["cohort_year", "status"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} (Batch {self.cohort_year}) [{self.get_status_display()}]"


class CycleImprovementAction(TimeStampedModel):
    """Concrete, trackable action item arising from a recruitment cycle review (Capability E)."""

    cycle_review = models.ForeignKey(
        RecruitmentCycleReview,
        on_delete=models.CASCADE,
        related_name="actions",
        help_text="The cycle review that originated this action item.",
    )
    action_title = models.CharField(
        max_length=255,
        help_text="Concise description of the improvement action.",
    )
    category = models.CharField(
        max_length=32,
        choices=CycleActionCategory.CHOICES,
        default=CycleActionCategory.REMEDIAL_TRAINING,
        db_index=True,
        help_text="Category of continuous improvement intervention.",
    )
    description = models.TextField(
        help_text="Detailed scope, rationale, and execution steps for this action item.",
    )
    target_completion_date = models.DateField(
        help_text="Target deadline for completing this improvement action.",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_cycle_actions",
        help_text="Staff member or trainer assigned to drive this action.",
    )
    status = models.CharField(
        max_length=32,
        choices=CycleActionStatus.CHOICES,
        default=CycleActionStatus.PENDING,
        db_index=True,
        help_text="Current implementation state.",
    )
    linked_training_plan = models.ForeignKey(
        TrainingPlan,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="linked_cycle_actions",
        help_text="Optional training plan created to implement this remedial action.",
    )
    resolution_notes = models.TextField(
        blank=True,
        default="",
        help_text="Evidence of resolution or status update notes.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_cycle_actions",
        help_text="Staff member who recorded this action item.",
    )

    class Meta:
        db_table = "analytics_cycle_action"
        ordering = ["target_completion_date", "-created_at"]
        indexes = [
            models.Index(fields=["cycle_review", "status"]),
            models.Index(fields=["status", "target_completion_date"]),
        ]

    def __str__(self) -> str:
        return f"Action: {self.action_title} [{self.get_category_display()}] ({self.get_status_display()})"
