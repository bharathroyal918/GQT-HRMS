"""Creative Studio & Promotional Assets Domain Models (Phase 4).

Preserves the authoritative GQT HRMS workflow:
- Step 8: Send to Design Team (Request Flyer, Banner, Social Media Post from approved Job Requirements)
- Step 9: Review & Approve Design (4-Point Checklist: Flyer accuracy, Logo, QR code, Registration link & contacts)
"""
import uuid
from typing import Dict, Any, List
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.jobs.models import JobRequirement, JobRequirementStatus


class CreativeDeliverableType:
    FLYER = "FLYER"
    BANNER = "BANNER"
    SOCIAL_POST = "SOCIAL_POST"
    COMBINED_PACK = "COMBINED_PACK"

    CHOICES = (
        (FLYER, "Placement Announcement Flyer (A4 / Document)"),
        (BANNER, "Display Banner (Web / Portal / Header)"),
        (SOCIAL_POST, "Social Media Post (Square / WhatsApp / LinkedIn)"),
        (COMBINED_PACK, "Combined Creative Pack (All Formats)"),
    )


class CreativeRequestStatus:
    DRAFT = "DRAFT"
    ASSIGNED = "ASSIGNED"
    IN_PRODUCTION = "IN_PRODUCTION"
    REVIEW_PENDING = "REVIEW_PENDING"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (DRAFT, "Draft — Brief Under Construction"),
        (ASSIGNED, "Assigned — Graphic Designer Assigned"),
        (IN_PRODUCTION, "In Production — Asset Drafting in Progress"),
        (REVIEW_PENDING, "Review Pending — Asset Uploaded for Step 9 Audit"),
        (CHANGES_REQUESTED, "Changes Requested — Returned for Revision"),
        (APPROVED, "Approved — Certified by Placement Head for Step 10"),
        (REJECTED, "Rejected — Asset Ineligible"),
        (CANCELLED, "Cancelled — Creative Request Terminated"),
    )


class CreativePriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

    CHOICES = (
        (LOW, "Low Priority"),
        (MEDIUM, "Medium Priority (Standard)"),
        (HIGH, "High Priority"),
        (URGENT, "Urgent — Immediate Drive Date"),
    )


class AssetVersionStatus:
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    CHOICES = (
        (DRAFT, "Draft Asset"),
        (SUBMITTED, "Submitted for Verification"),
        (IN_REVIEW, "In Review — 4-Point Checklist Audit Active"),
        (CHANGES_REQUESTED, "Changes Requested"),
        (APPROVED, "Approved — Placement Head Certified"),
        (REJECTED, "Rejected"),
    )


class ChecklistItemCode:
    FLYER_ACCURACY = "FLYER_ACCURACY"
    OFFICIAL_LOGO = "OFFICIAL_LOGO"
    QR_CODE = "QR_CODE"
    REGISTRATION_LINK_AND_CONTACTS = "REGISTRATION_LINK_AND_CONTACTS"

    CHOICES = (
        (FLYER_ACCURACY, "Flyer Content & Job Details Accuracy"),
        (OFFICIAL_LOGO, "Official Corporate & GQT Brand Logos"),
        (QR_CODE, "QR Code Scannability & URL Destination"),
        (REGISTRATION_LINK_AND_CONTACTS, "Registration Link & Placement Contact Info"),
    )


class ChecklistItemStatus:
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"

    CHOICES = (
        (PENDING, "Pending Verification"),
        (VERIFIED, "Verified & Passed"),
        (REJECTED, "Rejected / Fails Criteria"),
        (NOT_APPLICABLE, "Not Applicable / Waived"),
    )


# Authoritative 4-Point Design Verification Checklist specifications
DEFAULT_4POINT_CHECKLIST_SPECS: List[Dict[str, Any]] = [
    {
        "item_code": ChecklistItemCode.FLYER_ACCURACY,
        "title": "Flyer Content & Job Details Accuracy",
        "description": (
            "Verify role title, eligibility criteria (degrees, branches, CGPA, backlogs), "
            "salary/CTC package, drive date, venue, and hiring process rounds match the approved Job Requirement."
        ),
        "is_mandatory": True,
    },
    {
        "item_code": ChecklistItemCode.OFFICIAL_LOGO,
        "title": "Official Corporate & GQT Brand Logos",
        "description": (
            "Verify official high-resolution corporate employer logo is authentic, correctly placed, "
            "and compliant with GQT institutional brand guidelines and visual identity tokens."
        ),
        "is_mandatory": True,
    },
    {
        "item_code": ChecklistItemCode.QR_CODE,
        "title": "QR Code Scannability & URL Destination",
        "description": (
            "Verify the embedded QR code is scannable via camera/lens, has high contrast, and resolves "
            "strictly to the official drive registration URL."
        ),
        "is_mandatory": True,
    },
    {
        "item_code": ChecklistItemCode.REGISTRATION_LINK_AND_CONTACTS,
        "title": "Registration Link & Placement Contact Info",
        "description": (
            "Verify explicit text registration URL is legible and accurate, registration deadline is displayed, "
            "and official placement cell contact email and phone numbers are prominently shown."
        ),
        "is_mandatory": True,
    },
]


def creative_upload_path(instance: "CreativeAssetVersion", filename: str) -> str:
    """Generate dynamic upload path for promotional creative assets."""
    now = timezone.now()
    ext = filename.split(".")[-1].lower() if "." in filename else "bin"
    return f"creatives/{now.year}/{now.month:02d}/{uuid.uuid4().hex}.{ext}"


class CreativeRequest(TimeStampedModel):
    """Creative production request linking an approved Job Requirement to promotional assets (Step 8)."""

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="creative_requests",
        help_text="The approved JobRequirement backing this creative request.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Descriptive title of the promotional asset or campaign.",
    )
    deliverable_type = models.CharField(
        max_length=32,
        choices=CreativeDeliverableType.CHOICES,
        default=CreativeDeliverableType.COMBINED_PACK,
        db_index=True,
    )
    status = models.CharField(
        max_length=32,
        choices=CreativeRequestStatus.CHOICES,
        default=CreativeRequestStatus.DRAFT,
        db_index=True,
    )
    priority = models.CharField(
        max_length=16,
        choices=CreativePriority.CHOICES,
        default=CreativePriority.MEDIUM,
        db_index=True,
    )
    brief = models.TextField(
        help_text="Detailed creative brief, copy highlights, design instructions, and specifications.",
    )
    target_audience = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Target batches, departments, branches, or eligible student cohorts.",
    )
    registration_link = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Official drive registration URL to embed on the flyer and copy.",
    )
    qr_code_target_url = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Destination URL encoded inside the promotional QR code.",
    )
    contact_email = models.EmailField(
        blank=True,
        default="",
        help_text="Placement cell support email printed on promotional material.",
    )
    contact_phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Placement coordinator contact phone printed on promotional material.",
    )
    production_deadline = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Deadline by which promotional assets must be approved for broadcast.",
    )
    assigned_designer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_creative_requests",
        help_text="The Graphic Designer assigned to produce this creative deliverable.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_creative_requests",
        help_text="Placement Officer or Admin who created this request.",
    )
    is_archived = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Safe archival flag for completed or deprecated requests.",
    )

    class Meta:
        db_table = "creatives_request"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["job_requirement", "status"]),
            models.Index(fields=["assigned_designer", "status"]),
            models.Index(fields=["production_deadline"]),
        ]
        constraints = [
            # Prevent duplicate active requests for the exact same job and deliverable
            models.UniqueConstraint(
                fields=["job_requirement", "deliverable_type"],
                condition=models.Q(is_archived=False) & ~models.Q(status=CreativeRequestStatus.CANCELLED),
                name="unique_active_job_deliverable_request",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_deliverable_type_display()}) [{self.status}]"

    @property
    def company(self):
        return self.job_requirement.company

    @property
    def is_editable(self) -> bool:
        """Determines if the brief or new versions can be submitted."""
        return self.status in (
            CreativeRequestStatus.DRAFT,
            CreativeRequestStatus.ASSIGNED,
            CreativeRequestStatus.IN_PRODUCTION,
            CreativeRequestStatus.CHANGES_REQUESTED,
            CreativeRequestStatus.REVIEW_PENDING,
        ) and not self.is_archived

    @property
    def is_locked(self) -> bool:
        """Determines if the creative request has received final approval."""
        return self.status == CreativeRequestStatus.APPROVED

    @property
    def active_version(self) -> "CreativeAssetVersion | None":
        """Return the latest version or approved version."""
        approved = self.versions.filter(is_approved=True).order_by("-version_number").first()
        if approved:
            return approved
        return self.versions.order_by("-version_number").first()

    @property
    def versions_count(self) -> int:
        return self.versions.count()


class CreativeAssetVersion(TimeStampedModel):
    """Promotional creative asset file version with cryptographic integrity (Step 8 & 9)."""

    request = models.ForeignKey(
        CreativeRequest,
        on_delete=models.CASCADE,
        related_name="versions",
        help_text="The parent creative production request.",
    )
    version_number = models.PositiveIntegerField(
        help_text="Monotonically increasing version number (1, 2, 3...).",
    )
    deliverable_type = models.CharField(
        max_length=32,
        choices=CreativeDeliverableType.CHOICES,
        default=CreativeDeliverableType.FLYER,
    )
    file = models.FileField(
        upload_to=creative_upload_path,
        max_length=500,
        help_text="The promotional asset file (PNG, JPEG, WEBP, or PDF).",
    )
    file_name = models.CharField(
        max_length=255,
        help_text="Original uploaded filename.",
    )
    file_size_bytes = models.PositiveIntegerField(
        help_text="Exact file size in bytes.",
    )
    mime_type = models.CharField(
        max_length=128,
        help_text="Validated MIME type (image/png, image/jpeg, image/webp, application/pdf).",
    )
    sha256_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Cryptographic SHA-256 digest of the uploaded binary.",
    )
    width_px = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Image width in pixels (where applicable).",
    )
    height_px = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Image height in pixels (where applicable).",
    )
    designer_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes from the designer detailing changes or instructions in this version.",
    )
    status = models.CharField(
        max_length=32,
        choices=AssetVersionStatus.CHOICES,
        default=AssetVersionStatus.SUBMITTED,
        db_index=True,
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_creative_versions",
        help_text="The designer or staff member who uploaded this revision.",
    )
    is_approved = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates whether this specific version has passed final Step 9 sign-off.",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="approved_creative_versions",
        help_text="Placement Head who formally certified this asset version.",
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of final Placement Head approval.",
    )
    rejection_reason = models.TextField(
        blank=True,
        default="",
        help_text="Reason recorded if this version was rejected or returned for changes.",
    )

    class Meta:
        db_table = "creatives_asset_version"
        ordering = ["-version_number"]
        indexes = [
            models.Index(fields=["request", "version_number"]),
            models.Index(fields=["status", "is_approved"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "version_number"],
                name="unique_request_version_number",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.request.title} v{self.version_number} [{self.status}]"

    @property
    def all_mandatory_verified(self) -> bool:
        """Returns True strictly when all 4 mandatory checklist items evaluate to VERIFIED."""
        mandatory = self.checklist_items.filter(is_mandatory=True)
        if not mandatory.exists():
            return False
        return not mandatory.exclude(status=ChecklistItemStatus.VERIFIED).exists()

    @property
    def checklist_progress(self) -> Dict[str, Any]:
        """Calculates checklist completion metrics."""
        total = self.checklist_items.filter(is_mandatory=True).count()
        verified = self.checklist_items.filter(
            is_mandatory=True,
            status=ChecklistItemStatus.VERIFIED,
        ).count()
        percent = int((verified / total * 100)) if total > 0 else 0
        return {
            "total": total,
            "verified": verified,
            "percent": percent,
            "all_verified": total > 0 and verified == total,
        }


class CreativeChecklistItem(TimeStampedModel):
    """Individual 4-point design verification criterion audited per asset version (Step 9)."""

    version = models.ForeignKey(
        CreativeAssetVersion,
        on_delete=models.CASCADE,
        related_name="checklist_items",
        help_text="The asset version being verified.",
    )
    item_code = models.CharField(
        max_length=64,
        choices=ChecklistItemCode.CHOICES,
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        help_text="Human-readable title of the verification point.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Detailed evaluation instructions for the reviewer.",
    )
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Whether this verification check is strictly required for approval.",
    )
    status = models.CharField(
        max_length=32,
        choices=ChecklistItemStatus.CHOICES,
        default=ChecklistItemStatus.PENDING,
        db_index=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="verified_creative_checklist_items",
        help_text="Reviewer who verified this design point.",
    )
    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when verification was recorded.",
    )
    remarks = models.TextField(
        blank=True,
        default="",
        help_text="Reviewer remarks, feedback, or verification notes.",
    )

    class Meta:
        db_table = "creatives_checklist_item"
        ordering = ["item_code"]
        indexes = [
            models.Index(fields=["version", "item_code"]),
            models.Index(fields=["status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["version", "item_code"],
                name="unique_version_checklist_item",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.version} — {self.get_item_code_display()}: {self.status}"


class CreativeDecision(TimeStampedModel):
    """Append-only audit record of creative reviews, assignments, and approval decisions."""

    request = models.ForeignKey(
        CreativeRequest,
        on_delete=models.CASCADE,
        related_name="decisions",
    )
    version = models.ForeignKey(
        CreativeAssetVersion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="decisions",
    )
    decision = models.CharField(
        max_length=32,
        db_index=True,
        help_text="Decision action: ASSIGNED, SUBMITTED, CHANGES_REQUESTED, APPROVED, REJECTED, REOPENED.",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        help_text="The user who recorded this decision.",
    )
    actor_role = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Role under which the actor authorized this decision.",
    )
    comments = models.TextField(
        blank=True,
        default="",
        help_text="Comments, revision feedback, or justification for the decision.",
    )
    snapshot_version_number = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Version number active at the time of this decision.",
    )
    snapshot_request_status = models.CharField(
        max_length=32,
        help_text="Status of the creative request at the time of this decision.",
    )

    class Meta:
        db_table = "creatives_decision"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["request", "created_at"]),
            models.Index(fields=["decision"]),
        ]

    def __str__(self) -> str:
        return f"{self.created_at.isoformat()} | {self.decision} by {self.actor} on {self.request.title}"
