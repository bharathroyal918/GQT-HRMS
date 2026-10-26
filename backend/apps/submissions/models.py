"""Candidate Submission & Profile Dispatch Domain Models (Phase 7 / Steps 24-28).

Authoritative GQT HRMS Workflow Steps:
- Step 24: Prepare Candidate List (Filter eligible cohort; strictly verify Placement Head readiness certification & approved resume)
- Step 25: Generate Candidate Roster Spreadsheet (Standardized Excel sheet with student metrics & SHA-256 integrity digest)
- Step 26: Attach Resumes (Bundle exact certified resume PDF versions corresponding to roster entries)
- Step 27: Send Candidate Profiles to HR (Dispatch package to corporate HR; track channel, provider ref, and update status)
- Step 28: Company Acknowledgement (Log recruiter receipt confirmation, feedback, drive dates, and callback timeline)
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.crm.models import Company, HRContact
from apps.jobs.models import JobRequirement
from apps.students.models import (
    StudentProfile,
    StudentApplication,
    StudentResume,
    CandidateCohort,
)
from apps.preparation.models import PlacementReadinessCertification


class SubmissionPackageStatus:
    DRAFT = "DRAFT"
    READY_FOR_DISPATCH = "READY_FOR_DISPATCH"
    DISPATCHED = "DISPATCHED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (DRAFT, "Draft Candidate Roster"),
        (READY_FOR_DISPATCH, "Packaged & Ready for Dispatch"),
        (DISPATCHED, "Dispatched to Corporate HR"),
        (ACKNOWLEDGED, "Receipt Acknowledged by Corporate HR"),
        (CANCELLED, "Submission Cancelled"),
    )


class DispatchChannel:
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    PORTAL_LINK = "PORTAL_LINK"
    DIRECT_HANDOFF = "DIRECT_HANDOFF"

    CHOICES = (
        (EMAIL, "Corporate Email Transmission"),
        (WHATSAPP, "WhatsApp Business Outreach"),
        (PORTAL_LINK, "Recruitment Portal Transmission"),
        (DIRECT_HANDOFF, "Direct Handoff / Campus Meeting"),
    )


class AcknowledgementChannel:
    EMAIL = "EMAIL"
    PHONE_CALL = "PHONE_CALL"
    WHATSAPP = "WHATSAPP"
    PORTAL = "PORTAL"
    IN_PERSON = "IN_PERSON"

    CHOICES = (
        (EMAIL, "Email Confirmation"),
        (PHONE_CALL, "Telephone Call"),
        (WHATSAPP, "WhatsApp Message"),
        (PORTAL, "Recruiter Portal Response"),
        (IN_PERSON, "In-Person Discussion"),
    )


class CandidateSubmissionStatus:
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"
    ON_HOLD = "ON_HOLD"

    CHOICES = (
        (PENDING, "Pending Corporate Dispatch"),
        (SUBMITTED, "Submitted to Corporate HR"),
        (ACKNOWLEDGED, "Receipt Acknowledged"),
        (SHORTLISTED, "Shortlisted by HR"),
        (REJECTED, "Not Shortlisted / Rejected by HR"),
        (ON_HOLD, "Under Recruiter Review / On Hold"),
    )


class SubmissionPackage(TimeStampedModel):
    """Authoritative corporate candidate submission package for an approved job requirement (Steps 24-28)."""

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="submission_packages",
        help_text="The approved job requirement linked to this corporate submission.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="submission_packages",
        help_text="The corporate enterprise partner receiving candidate profiles.",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.PROTECT,
        related_name="submission_packages",
        help_text="The primary corporate HR recipient for candidate dispatch.",
    )
    cohort = models.ForeignKey(
        CandidateCohort,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="submission_packages",
        help_text="Optional finalized candidate cohort source.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Descriptive title of the submission package (e.g. Batch 2026 - TCS ASE Profiles).",
    )
    status = models.CharField(
        max_length=32,
        choices=SubmissionPackageStatus.CHOICES,
        default=SubmissionPackageStatus.DRAFT,
        db_index=True,
        help_text="Authoritative lifecycle status of the corporate submission package.",
    )
    package_hash = models.CharField(
        max_length=64,
        blank=True,
        default="",
        db_index=True,
        help_text="Cryptographic SHA-256 digest of the generated candidate roster spreadsheet.",
    )
    roster_file = models.FileField(
        upload_to="rosters/%Y/%m/",
        null=True,
        blank=True,
        max_length=500,
        help_text="Standardized master XLSX spreadsheet file.",
    )
    roster_file_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Original generated filename of the roster spreadsheet.",
    )
    roster_generated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the master spreadsheet was generated (Step 25).",
    )
    resumes_attached_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when certified resumes were attached and verified (Step 26).",
    )
    candidate_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of candidates included in this submission package.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal notes or placement team directives.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_submission_packages",
        help_text="Placement staff user who assembled the submission package.",
    )

    # Step 27: Profile Dispatch Details
    dispatched_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp when profiles were transmitted to corporate HR.",
    )
    dispatched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="dispatched_submission_packages",
        help_text="Placement staff member who authorized and initiated profile dispatch.",
    )
    dispatch_channel = models.CharField(
        max_length=32,
        choices=DispatchChannel.CHOICES,
        default=DispatchChannel.EMAIL,
        help_text="Primary transmission channel used for dispatch.",
    )
    recipient_email = models.EmailField(
        blank=True,
        default="",
        help_text="Corporate recipient email address.",
    )
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Name of the HR contact receiving the submission.",
    )
    recipient_phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Contact telephone number used for dispatch coordination.",
    )
    provider_reference = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Email message ID or external dispatch tracking identifier.",
    )
    dispatch_notes = models.TextField(
        blank=True,
        default="",
        help_text="Dispatch communication remarks or transmission details.",
    )

    # Step 28: Recruiter Acknowledgment Details
    acknowledged_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Timestamp when corporate HR acknowledged receipt of candidate profiles.",
    )
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="recorded_acknowledgments",
        help_text="Placement officer who logged the recruiter acknowledgment.",
    )
    acknowledged_by_contact_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Name of recruiter or HR representative confirming profile receipt.",
    )
    acknowledgement_channel = models.CharField(
        max_length=32,
        choices=AcknowledgementChannel.CHOICES,
        default=AcknowledgementChannel.EMAIL,
        help_text="Communication channel used by recruiter to confirm receipt.",
    )
    recruiter_feedback = models.TextField(
        blank=True,
        default="",
        help_text="Preliminary recruiter impressions or candidate pool feedback.",
    )
    tentative_interview_date = models.DateField(
        null=True,
        blank=True,
        help_text="Proposed interview drive or assessment date provided by HR.",
    )
    follow_up_callback_date = models.DateField(
        null=True,
        blank=True,
        help_text="Agreed follow-up date for receiving recruiter shortlist.",
    )

    class Meta:
        db_table = "submissions_package"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["job_requirement", "status"]),
            models.Index(fields=["company", "status"]),
            models.Index(fields=["dispatched_at"]),
            models.Index(fields=["acknowledged_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} [{self.get_status_display()}] - {self.company.name}"


class CandidateSubmission(TimeStampedModel):
    """Individual candidate record included within a corporate submission package (Steps 24-28)."""

    package = models.ForeignKey(
        SubmissionPackage,
        on_delete=models.CASCADE,
        related_name="candidates",
        help_text="Parent submission package.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="candidate_submissions",
        help_text="Candidate student profile.",
    )
    application = models.ForeignKey(
        StudentApplication,
        on_delete=models.PROTECT,
        related_name="candidate_submissions",
        help_text="Underlying job application.",
    )
    readiness_certification = models.ForeignKey(
        PlacementReadinessCertification,
        on_delete=models.PROTECT,
        related_name="candidate_submissions",
        help_text="Authoritative Placement Head readiness certification (Step 23 Gate).",
    )
    submitted_resume = models.ForeignKey(
        StudentResume,
        on_delete=models.PROTECT,
        related_name="candidate_submissions",
        help_text="Exact certified resume version approved for placement submission.",
    )
    resume_version_number = models.PositiveIntegerField(
        help_text="Snapshot of the resume version number at time of submission.",
    )
    resume_sha256 = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 cryptographic hash of the submitted resume PDF.",
    )
    status = models.CharField(
        max_length=32,
        choices=CandidateSubmissionStatus.CHOICES,
        default=CandidateSubmissionStatus.PENDING,
        db_index=True,
        help_text="Individual candidate recruitment outcome for this submission.",
    )
    candidate_snapshot = models.JSONField(
        default=dict,
        help_text="Frozen academic and contact details at submission time (data minimization).",
    )

    class Meta:
        db_table = "submissions_candidate_submission"
        ordering = ["student__roll_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["package", "student"],
                name="unique_package_student_candidate",
            ),
        ]
        indexes = [
            models.Index(fields=["package", "status"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["resume_sha256"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} in {self.package.title} [{self.status}]"


class SubmissionDispatchLog(TimeStampedModel):
    """Audit and communication log tracking profile transmission attempts and delivery receipts."""

    package = models.ForeignKey(
        SubmissionPackage,
        on_delete=models.CASCADE,
        related_name="dispatch_logs",
        help_text="The submission package being dispatched.",
    )
    attempt_number = models.PositiveIntegerField(
        default=1,
        help_text="Sequential transmission attempt number.",
    )
    channel = models.CharField(
        max_length=32,
        choices=DispatchChannel.CHOICES,
        help_text="Transmission channel used.",
    )
    recipient = models.CharField(
        max_length=255,
        help_text="Recipient destination identifier (email or phone).",
    )
    status = models.CharField(
        max_length=32,
        choices=(
            ("QUEUED", "Queued for Transmission"),
            ("SENT", "Sent to Provider"),
            ("DELIVERED", "Delivered to Recipient"),
            ("FAILED", "Transmission Failed"),
        ),
        default="SENT",
        db_index=True,
    )
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="External provider message ID or delivery reference.",
    )
    response_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Provider transmission response or diagnostics.",
    )
    dispatched_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="submission_dispatch_logs",
    )
    timestamp = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        db_table = "submissions_dispatch_log"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["package", "status"]),
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self) -> str:
        return f"Dispatch #{self.attempt_number} for {self.package.title} [{self.status}]"
