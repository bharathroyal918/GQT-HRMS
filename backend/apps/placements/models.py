"""Placement Management Domain Models (Steps 36–41).

Authoritative GQT HRMS Workflow Steps:
- Step 36: Receive Final Results (Corporate HR result intake linked to job & company)
- Step 37: Update Candidate Status (Selected, Rejected, Waiting List, Hold)
- Step 38: Notify Students (Truthful status notification advisories)
- Step 39: Upload Offer Letter (%PDF- magic bytes, SHA-256 integrity, private storage)
- Step 40: Track Offer Acceptance (Accepted, Declined, Pending, student self-service vs staff)
- Step 41: Track Joining Status (Joined, Not Joined, Deferred, verification history)
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.crm.models import Company, HRContact
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile
from apps.placements.validators import offer_letter_upload_path


class ResultIntakeSource:
    EMAIL = "EMAIL"
    PORTAL = "PORTAL"
    FILE_IMPORT = "FILE_IMPORT"
    DIRECT_HANDOFF = "DIRECT_HANDOFF"

    CHOICES = (
        (EMAIL, "Corporate Email Shortlist/Result"),
        (PORTAL, "Recruiter Portal Export"),
        (FILE_IMPORT, "Spreadsheet Import"),
        (DIRECT_HANDOFF, "Direct Handoff / Meeting"),
    )


class CandidatePlacementStatusChoices:
    """Authoritative Step 37 candidate placement outcome statuses."""

    SELECTED = "SELECTED"
    REJECTED = "REJECTED"
    WAITING_LIST = "WAITING_LIST"
    HOLD = "HOLD"

    CHOICES = (
        (SELECTED, "Selected — Eligible for Offer Letter"),
        (REJECTED, "Rejected — Not Selected"),
        (WAITING_LIST, "Waiting List — Standby Status"),
        (HOLD, "Hold — Decision Awaited"),
    )


class OfferAcceptanceStatus:
    """Authoritative Step 40 offer acceptance lifecycle statuses."""

    PENDING_RESPONSE = "PENDING_RESPONSE"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"

    CHOICES = (
        (PENDING_RESPONSE, "Pending Candidate Response"),
        (ACCEPTED, "Offer Accepted"),
        (DECLINED, "Offer Declined"),
        (EXPIRED, "Offer Expired"),
    )


class JoiningStatus:
    """Authoritative Step 41 candidate onboarding and reporting statuses."""

    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING_JOINING = "PENDING_JOINING"
    JOINED = "JOINED"
    NOT_JOINED = "NOT_JOINED"
    DEFERRED = "DEFERRED"

    CHOICES = (
        (NOT_APPLICABLE, "Not Applicable (Offer Pending/Declined)"),
        (PENDING_JOINING, "Pending Joining Date"),
        (JOINED, "Joined Company"),
        (NOT_JOINED, "Not Joined / Renege"),
        (DEFERRED, "Deferred Joining Date"),
    )


class FinalResultIntake(TimeStampedModel):
    """Batch record for final candidate recruitment results from corporate HR (Step 36)."""

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="placement_intakes",
        help_text="Job requirement for which final results were shared.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="placement_intakes",
        help_text="Corporate employer providing final results.",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="placement_intakes",
        help_text="Corporate recruiter or HR contact communicating results.",
    )
    result_reference_code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Institutional reference identifier (e.g. RES-20261027-0001).",
    )
    source = models.CharField(
        max_length=32,
        choices=ResultIntakeSource.CHOICES,
        default=ResultIntakeSource.EMAIL,
        help_text="Channel through which final results were ingested.",
    )
    received_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when final results were officially received from HR.",
    )
    total_results = models.PositiveIntegerField(
        default=0,
        help_text="Total number of candidate outcomes recorded in this intake.",
    )
    selected_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of selected candidates.",
    )
    rejected_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of rejected candidates.",
    )
    waiting_list_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of waitlisted candidates.",
    )
    hold_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of candidates on hold.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="General recruiter remarks or evaluation summary notes.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_placement_intakes",
        help_text="Placement staff user who recorded the results.",
    )

    class Meta:
        db_table = "placements_final_result_intake"
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["job_requirement", "received_at"]),
            models.Index(fields=["company", "received_at"]),
            models.Index(fields=["result_reference_code"]),
        ]

    def __str__(self) -> str:
        return f"{self.result_reference_code} - {self.company.name} ({self.total_results} candidates)"


class CandidatePlacementStatus(TimeStampedModel):
    """Authoritative placement outcome status for an individual candidate on a job drive (Step 37)."""

    intake = models.ForeignKey(
        FinalResultIntake,
        on_delete=models.CASCADE,
        related_name="candidate_results",
        help_text="Associated result intake batch.",
    )
    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="placement_results",
        help_text="The job requirement for this placement decision.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="placement_results",
        help_text="Corporate employer.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="placement_results",
        help_text="Student profile.",
    )
    status = models.CharField(
        max_length=32,
        choices=CandidatePlacementStatusChoices.CHOICES,
        default=CandidatePlacementStatusChoices.HOLD,
        db_index=True,
        help_text="Authoritative candidate result: Selected, Rejected, Waiting List, Hold.",
    )
    designation_offered = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Corporate job designation or title offered by the recruiter.",
    )
    offered_ctc = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual Cost to Company (CTC) package in INR.",
    )
    work_location = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Designated work base or posting city.",
    )
    remarks = models.TextField(
        blank=True,
        default="",
        help_text="Specific recruiter remarks or selection feedback.",
    )
    status_updated_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp of latest status transition or correction.",
    )
    status_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_candidate_placement_statuses",
        help_text="User who enacted the latest status update.",
    )

    class Meta:
        db_table = "placements_candidate_status"
        ordering = ["-status_updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["job_requirement", "student"],
                name="unique_job_student_placement_result",
            ),
        ]
        indexes = [
            models.Index(fields=["status", "job_requirement"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["company", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} - {self.job_requirement.title} [{self.get_status_display()}]"


class PlacementStatusHistory(TimeStampedModel):
    """Immutable audit record tracking status transitions and corrections (Step 37)."""

    placement_status = models.ForeignKey(
        CandidatePlacementStatus,
        on_delete=models.CASCADE,
        related_name="history",
        help_text="Candidate placement record being transitioned.",
    )
    previous_status = models.CharField(
        max_length=32,
        choices=CandidatePlacementStatusChoices.CHOICES,
        help_text="Prior status before update.",
    )
    new_status = models.CharField(
        max_length=32,
        choices=CandidatePlacementStatusChoices.CHOICES,
        help_text="New updated status.",
    )
    reason = models.TextField(
        blank=True,
        default="",
        help_text="Documented rationale for status update or correction.",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="placement_status_changes",
        help_text="Actor who authorized the status transition.",
    )

    class Meta:
        db_table = "placements_status_history"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["placement_status", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.placement_status.student.roll_number}: {self.previous_status} -> {self.new_status}"


class PlacementNotificationLog(TimeStampedModel):
    """Immutable log of candidate status outcome notifications (Step 38)."""

    placement_status = models.ForeignKey(
        CandidatePlacementStatus,
        on_delete=models.CASCADE,
        related_name="notification_logs",
        help_text="Placement status record being announced.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="placement_notifications",
        help_text="Student recipient.",
    )
    recipient_email = models.EmailField(
        help_text="Destination email address used.",
    )
    recipient_phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Destination mobile number used.",
    )
    channel = models.CharField(
        max_length=32,
        choices=(
            ("EMAIL", "Email"),
            ("WHATSAPP", "WhatsApp"),
            ("SMS", "SMS"),
            ("PORTAL", "Student Portal Advisory"),
        ),
        default="EMAIL",
    )
    status = models.CharField(
        max_length=32,
        choices=(
            ("PENDING", "Pending"),
            ("SENT", "Dispatched"),
            ("FAILED", "Failed"),
        ),
        default="SENT",
    )
    status_announced = models.CharField(
        max_length=32,
        choices=CandidatePlacementStatusChoices.CHOICES,
        help_text="The placement status conveyed in this notification.",
    )
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Simulated or provider transmission identifier.",
    )
    details_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Rendered message snapshot (subject, body, parameters).",
    )
    sent_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp of dispatch attempt.",
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="sent_placement_notifications",
        help_text="Staff member who triggered the notification.",
    )

    class Meta:
        db_table = "placements_notification_log"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["placement_status", "sent_at"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self) -> str:
        return f"Notification to {self.student.roll_number} for {self.status_announced} [{self.status}]"


class CandidateOfferLetter(TimeStampedModel):
    """Official corporate offer letter document, acceptance, and joining tracking (Steps 39–41)."""

    placement_status = models.OneToOneField(
        CandidatePlacementStatus,
        on_delete=models.CASCADE,
        related_name="offer_letter",
        help_text="Placement status record for selected candidate.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="offer_letters",
        help_text="Student recipient of this offer.",
    )
    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="offer_letters",
        help_text="Job requirement offering employment.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="offer_letters",
        help_text="Company extending the offer.",
    )

    # Step 39: Offer Document File & Integrity
    file = models.FileField(
        upload_to=offer_letter_upload_path,
        max_length=500,
        help_text="The official PDF offer letter document in private storage.",
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
        help_text="Cryptographic SHA-256 digest of the PDF payload.",
    )
    version_number = models.PositiveIntegerField(
        default=1,
        help_text="Monotonically incrementing offer version (v1, v2...).",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Indicates whether this is the active current offer letter.",
    )
    issued_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when offer letter was uploaded and issued.",
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="issued_offer_letters",
        help_text="Placement officer who uploaded the offer letter.",
    )

    # Step 40: Acceptance Tracking Fields
    acceptance_deadline = models.DateField(
        null=True,
        blank=True,
        help_text="Explicit candidate response deadline if provided by recruiter (optional, non-invented).",
    )
    acceptance_status = models.CharField(
        max_length=32,
        choices=OfferAcceptanceStatus.CHOICES,
        default=OfferAcceptanceStatus.PENDING_RESPONSE,
        db_index=True,
        help_text="Offer acceptance response state: Pending, Accepted, Declined, Expired.",
    )
    accepted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when acceptance or declination was recorded.",
    )
    acceptance_source = models.CharField(
        max_length=32,
        choices=(
            ("STUDENT_PORTAL", "Student Self-Service via Portal"),
            ("PLACEMENT_OFFICE", "Placement Office Offline Entry"),
        ),
        default="STUDENT_PORTAL",
        help_text="Origin of the acceptance decision record.",
    )
    student_decision_notes = models.TextField(
        blank=True,
        default="",
        help_text="Candidate remarks, terms acceptance note, or reason if declined.",
    )
    acceptance_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_offer_acceptances",
        help_text="User who recorded the decision (student themselves or staff member).",
    )

    # Step 41: Joining Status Fields
    joining_status = models.CharField(
        max_length=32,
        choices=JoiningStatus.CHOICES,
        default=JoiningStatus.NOT_APPLICABLE,
        db_index=True,
        help_text="Candidate reporting status: Joined, Not Joined, Deferred.",
    )
    expected_joining_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected joining date specified in the offer letter.",
    )
    actual_joining_date = models.DateField(
        null=True,
        blank=True,
        help_text="Verified actual date candidate reported to work.",
    )
    deferred_joining_date = models.DateField(
        null=True,
        blank=True,
        help_text="Approved new reporting date if joining was deferred.",
    )
    joining_location = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Reporting office, campus, or onboarding center location.",
    )
    employee_id_assigned = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Corporate employee code or badge ID assigned upon onboarding.",
    )
    joining_notes = models.TextField(
        blank=True,
        default="",
        help_text="Verification remarks, deferral reasons, or non-joining explanations.",
    )
    joining_verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when joining status was verified by placement office.",
    )
    joining_verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_joinings",
        help_text="Placement staff officer who verified candidate onboarding.",
    )

    class Meta:
        db_table = "placements_candidate_offer_letter"
        ordering = ["-issued_at"]
        indexes = [
            models.Index(fields=["student", "acceptance_status"]),
            models.Index(fields=["job_requirement", "acceptance_status"]),
            models.Index(fields=["joining_status"]),
            models.Index(fields=["sha256_hash"]),
        ]

    def __str__(self) -> str:
        return f"Offer v{self.version_number} for {self.student.roll_number} - {self.company.name} [{self.acceptance_status}]"


class OfferLetterVersion(TimeStampedModel):
    """Archival record of superseded offer letter document versions (Step 39)."""

    offer = models.ForeignKey(
        CandidateOfferLetter,
        on_delete=models.CASCADE,
        related_name="versions",
        help_text="Parent offer letter record.",
    )
    version_number = models.PositiveIntegerField(
        help_text="Archived version number.",
    )
    file = models.FileField(
        upload_to="offer_letters/archive/%Y/%m/",
        max_length=500,
        help_text="Archived offer letter PDF.",
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Original filename of this version.",
    )
    file_size_bytes = models.PositiveIntegerField(
        help_text="File size in bytes.",
    )
    sha256_hash = models.CharField(
        max_length=64,
        help_text="SHA-256 hash digest of this archived version.",
    )
    superseded_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when this version was replaced by a newer version.",
    )
    superseded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="superseded_offer_versions",
        help_text="Placement officer who uploaded the replacement version.",
    )
    superseded_reason = models.TextField(
        blank=True,
        default="",
        help_text="Documented reason for offer revision or re-issuance.",
    )

    class Meta:
        db_table = "placements_offer_version"
        ordering = ["-version_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["offer", "version_number"],
                name="unique_offer_letter_version",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.offer.student.roll_number} Offer v{self.version_number} (Archived)"


class JoiningStatusHistory(TimeStampedModel):
    """Immutable audit trail for candidate joining status updates and deferrals (Step 41)."""

    offer = models.ForeignKey(
        CandidateOfferLetter,
        on_delete=models.CASCADE,
        related_name="joining_history",
        help_text="Offer letter record whose joining status was updated.",
    )
    previous_status = models.CharField(
        max_length=32,
        choices=JoiningStatus.CHOICES,
        help_text="Prior joining status.",
    )
    new_status = models.CharField(
        max_length=32,
        choices=JoiningStatus.CHOICES,
        help_text="New updated joining status.",
    )
    reason = models.TextField(
        blank=True,
        default="",
        help_text="Documented reason or deferral justification.",
    )
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="joining_status_changes",
        help_text="Actor who recorded the joining update.",
    )

    class Meta:
        db_table = "placements_joining_history"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["offer", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.offer.student.roll_number} Joining: {self.previous_status} -> {self.new_status}"
