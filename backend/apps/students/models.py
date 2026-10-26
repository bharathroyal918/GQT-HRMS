"""Student Registration, Academic Profiles, and Eligibility Engine Domain Models.

Preserves the authoritative GQT HRMS workflow:
- Step 10: Publish Job Notification (Multi-channel notification dispatch of approved jobs)
- Step 11: Student Registration (Onboard student identity with roll number & email uniqueness)
- Step 12: Collect Student Profile & Resume (Academic records and PDF resume with magic bytes validation)
- Step 13: Eligibility Verification Engine (Deterministic multi-factor rule evaluation)
- Step 14: Eligible Candidate Cohort Finalization (Cohort locking & manual override audit)
"""
import uuid
from decimal import Decimal
from typing import Optional
from django.conf import settings
from django.db import models
from django.db.models.functions import Lower, Upper
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.jobs.models import JobRequirement
from apps.creatives.models import CreativeAssetVersion
from apps.students.validators import student_resume_upload_path


class JobPublicationChannel:
    WHATSAPP = "WHATSAPP"
    TELEGRAM = "TELEGRAM"
    EMAIL = "EMAIL"
    PORTAL = "PORTAL"

    CHOICES = (
        (WHATSAPP, "WhatsApp Community Broadcast"),
        (TELEGRAM, "Telegram Placement Channel"),
        (EMAIL, "Direct Institutional Email Broadcast"),
        (PORTAL, "Student Career Portal Noticeboard"),
    )


class JobPublicationStatus:
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    DISPATCHED = "DISPATCHED"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (PENDING, "Pending Dispatch"),
        (QUEUED, "Queued with Communication Gateway"),
        (DISPATCHED, "Dispatched to Gateway / Network"),
        (DELIVERED, "Delivered Successfully to Recipients"),
        (FAILED, "Delivery Failed"),
        (CANCELLED, "Publication Cancelled"),
    )


class JobPublication(TimeStampedModel):
    """Internal publication and multi-channel broadcast record for approved opportunities (Step 10)."""

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name="publications",
        help_text="The approved job requirement being broadcasted.",
    )
    creative_version = models.ForeignKey(
        CreativeAssetVersion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="publications",
        help_text="Optional approved promotional creative asset (Step 9 sign-off) attached to this notice.",
    )
    channel = models.CharField(
        max_length=32,
        choices=JobPublicationChannel.CHOICES,
        db_index=True,
        help_text="Distribution channel for the placement announcement.",
    )
    status = models.CharField(
        max_length=32,
        choices=JobPublicationStatus.CHOICES,
        default=JobPublicationStatus.PENDING,
        db_index=True,
        help_text="Current state of publication and external delivery.",
    )
    target_audience = models.CharField(
        max_length=255,
        help_text="Description of targeted student cohort (e.g. 2025 Passing Out Batch - Circuit Branches).",
    )
    subject = models.CharField(
        max_length=255,
        help_text="Notice headline or subject line for students.",
    )
    message_body = models.TextField(
        help_text="Complete announcement text including role, salary, drive date, and registration instructions.",
    )
    dispatched_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the notification was transmitted to the delivery provider.",
    )
    delivered_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when delivery was verified by the provider.",
    )
    failure_reason = models.TextField(
        blank=True,
        default="",
        help_text="Diagnostic failure explanation if transmission failed.",
    )
    retry_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of retry attempts executed.",
    )
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="External message identifier or receipt from SMS/Email/Messaging provider.",
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="job_publications",
        help_text="Placement staff member who initiated this announcement.",
    )

    class Meta:
        db_table = "students_job_publication"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["job_requirement", "channel"]),
            models.Index(fields=["status", "channel"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.job_requirement.title} via {self.get_channel_display()} [{self.status}]"


class StudentProfile(TimeStampedModel):
    """Institutional student profile with verified academic metrics and identity records (Steps 11 & 12)."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
        help_text="The linked user account with STUDENT role.",
    )
    roll_number = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Institutional enrollment or university register number (normalized uppercase).",
    )
    institutional_email = models.EmailField(
        unique=True,
        db_index=True,
        help_text="Official college or university email address (normalized lowercase).",
    )
    college_name = models.CharField(
        max_length=255,
        help_text="Name of the affiliated university or engineering college.",
    )
    degree = models.CharField(
        max_length=100,
        help_text="Degree program (e.g. B.Tech, B.E., M.Tech, MCA, BCA).",
    )
    department = models.CharField(
        max_length=100,
        help_text="Academic discipline or branch (e.g. Computer Science, Information Science, Electronics).",
    )
    graduation_year = models.PositiveIntegerField(
        db_index=True,
        help_text="Year of course completion / passing out batch (e.g. 2025).",
    )
    cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        help_text="Cumulative Grade Point Average (CGPA) on a 10.0 scale.",
    )
    active_backlogs = models.PositiveIntegerField(
        default=0,
        help_text="Current number of uncleared backlogs / standing arrears.",
    )
    history_backlogs = models.PositiveIntegerField(
        default=0,
        help_text="Historical total count of arrears ever recorded throughout degree.",
    )
    phone_number = models.CharField(
        max_length=30,
        help_text="Primary mobile contact number.",
    )
    alternate_phone = models.CharField(
        max_length=30,
        blank=True,
        default="",
        help_text="Alternate emergency contact phone number.",
    )
    is_verified_by_placement = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Flag certified by placement office confirming marks and enrollment validity.",
    )

    class Meta:
        db_table = "students_profile"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                Lower("institutional_email"),
                name="unique_lower_institutional_email",
            ),
            models.UniqueConstraint(
                Upper("roll_number"),
                name="unique_upper_roll_number",
            ),
        ]
        indexes = [
            models.Index(fields=["graduation_year", "department"]),
            models.Index(fields=["cgpa", "active_backlogs"]),
        ]

    def __str__(self) -> str:
        return f"{self.user.full_name} ({self.roll_number}) - {self.department} {self.graduation_year}"

    def clean(self) -> None:
        super().clean()
        if self.roll_number:
            self.roll_number = self.roll_number.strip().upper()
        if self.institutional_email:
            self.institutional_email = self.institutional_email.strip().lower()

    @property
    def current_resume(self) -> Optional["StudentResume"]:
        """Return the active, latest approved resume version for this candidate."""
        return self.resumes.filter(is_current=True).order_by("-version_number").first()


class StudentResume(TimeStampedModel):
    """Ingested student resume document with binary magic bytes validation and version tracking (Step 12)."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="resumes",
        help_text="The student profile owning this resume.",
    )
    version_number = models.PositiveIntegerField(
        help_text="Monotonically incrementing version number (v1, v2, ...).",
    )
    file = models.FileField(
        upload_to=student_resume_upload_path,
        max_length=500,
        help_text="The resume PDF document file in isolated private storage.",
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Original client filename when uploaded.",
    )
    file_size_bytes = models.PositiveIntegerField(
        help_text="Exact file size in bytes.",
    )
    sha256_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Cryptographic SHA-256 digest of the binary payload.",
    )
    is_current = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indicates whether this is the candidate's active current resume version.",
    )

    class Meta:
        db_table = "students_resume"
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "version_number"],
                name="unique_student_resume_version",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "is_current"]),
            models.Index(fields=["sha256_hash"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} Resume v{self.version_number}"


class StudentApplicationStatus:
    APPLIED = "APPLIED"
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    OVERRIDDEN = "OVERRIDDEN"
    WITHDRAWN = "WITHDRAWN"

    CHOICES = (
        (APPLIED, "Applied — Verification Pending"),
        (ELIGIBLE, "Eligible — Meets Criteria"),
        (INELIGIBLE, "Ineligible — Criteria Not Satisfied"),
        (OVERRIDDEN, "Overridden — Manually Certified by Placement Officer"),
        (WITHDRAWN, "Withdrawn by Student"),
    )


class StudentApplication(TimeStampedModel):
    """Application record submitted by a student for an approved job requirement."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="applications",
        help_text="The student submitting this drive application.",
    )
    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name="student_applications",
        help_text="The approved job requirement being applied for.",
    )
    resume = models.ForeignKey(
        StudentResume,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="applications",
        help_text="The specific resume version attached at application time.",
    )
    status = models.CharField(
        max_length=32,
        choices=StudentApplicationStatus.CHOICES,
        default=StudentApplicationStatus.APPLIED,
        db_index=True,
        help_text="Current qualification and drive state.",
    )
    applied_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        db_table = "students_application"
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "job_requirement"],
                name="unique_student_job_application",
            ),
        ]
        indexes = [
            models.Index(fields=["job_requirement", "status"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} -> {self.job_requirement.title} [{self.status}]"


class EligibilityStatus:
    ELIGIBLE = "ELIGIBLE"
    INELIGIBLE = "INELIGIBLE"
    INCOMPLETE = "INCOMPLETE"

    CHOICES = (
        (ELIGIBLE, "Eligible"),
        (INELIGIBLE, "Ineligible"),
        (INCOMPLETE, "Incomplete / Insufficient Academic Data"),
    )


class EligibilityEvaluation(TimeStampedModel):
    """Auditable result of deterministic rule evaluation for a student application (Step 13 & 14)."""

    application = models.OneToOneField(
        StudentApplication,
        on_delete=models.CASCADE,
        related_name="eligibility_evaluation",
        help_text="The student application evaluated by the engine.",
    )
    status = models.CharField(
        max_length=32,
        choices=EligibilityStatus.CHOICES,
        db_index=True,
        help_text="Authoritative eligibility status evaluated by the rule engine.",
    )
    criteria_snapshot = models.JSONField(
        default=dict,
        help_text="Snapshot of the job requirement criteria at the time of evaluation.",
    )
    evaluation_details = models.JSONField(
        default=dict,
        help_text="Criterion-by-criterion evaluation breakdown (Branch, CGPA, Backlogs, Passing Year).",
    )
    is_overridden = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates whether an authorized placement officer manually overrode this result.",
    )
    override_reason = models.TextField(
        blank=True,
        default="",
        help_text="Mandatory business justification provided by the overriding officer.",
    )
    override_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="overridden_eligibilities",
        help_text="The authorized placement officer who executed the override.",
    )
    override_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the manual override was recorded.",
    )
    evaluated_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp of automated rule evaluation.",
    )

    class Meta:
        db_table = "students_eligibility_evaluation"
        ordering = ["-evaluated_at"]
        indexes = [
            models.Index(fields=["status", "is_overridden"]),
        ]

    def __str__(self) -> str:
        flag = " [OVERRIDDEN]" if self.is_overridden else ""
        return f"Eligibility for {self.application} -> {self.status}{flag}"


class CandidateCohort(TimeStampedModel):
    """Finalized and locked cohort of verified candidates for an approved job drive (Step 14)."""

    job_requirement = models.OneToOneField(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name="candidate_cohort",
        help_text="The approved job requirement linked to this candidate cohort.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Descriptive title of the final candidate cohort.",
    )
    is_locked = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Lock flag preventing further candidate additions once finalized by Placement Head.",
    )
    finalized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="finalized_cohorts",
        help_text="Placement Head or Admin who certified and locked this cohort.",
    )
    finalized_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when cohort was formally locked.",
    )
    finalization_notes = models.TextField(
        blank=True,
        default="",
        help_text="Operational notes or drive instructions recorded at cohort sign-off.",
    )

    class Meta:
        db_table = "students_candidate_cohort"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_locked"]),
        ]

    def __str__(self) -> str:
        status_label = "LOCKED" if self.is_locked else "OPEN"
        return f"{self.title} ({status_label})"

    @property
    def member_count(self) -> int:
        return self.members.count()

    @property
    def eligible_member_count(self) -> int:
        return self.members.filter(is_eligible=True).count()


class CohortMember(TimeStampedModel):
    """Individual candidate record included within a job candidate cohort (Step 14)."""

    cohort = models.ForeignKey(
        CandidateCohort,
        on_delete=models.CASCADE,
        related_name="members",
        help_text="The parent candidate cohort.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="cohort_memberships",
        help_text="The candidate student profile.",
    )
    application = models.ForeignKey(
        StudentApplication,
        on_delete=models.CASCADE,
        related_name="cohort_memberships",
        help_text="The underlying job drive application.",
    )
    is_eligible = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Final eligibility indicator for this cohort inclusion.",
    )
    is_override = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates whether this candidate was included via manual override.",
    )
    override_reason = models.TextField(
        blank=True,
        default="",
        help_text="Mandatory reason if candidate inclusion was overridden.",
    )
    override_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cohort_overrides",
        help_text="Staff user who authorized the candidate override.",
    )
    override_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of override authorization.",
    )

    class Meta:
        db_table = "students_cohort_member"
        ordering = ["student__roll_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["cohort", "student"],
                name="unique_cohort_student_member",
            ),
        ]
        indexes = [
            models.Index(fields=["cohort", "is_eligible"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} in {self.cohort.title}"
