"""Job Requirements & Verification Checklist Domain Models (Phase 3).

Preserves the authoritative GQT HRMS workflow:
- Step 5: Collect Job Description (Role, JD, Skills, Salary, Location, Bond, Eligibility, Hiring Process, Deadlines)
- Step 6: Verify Job Details (5 Core Points: Eligibility, Salary, Company Authenticity, Interview Process, Deadline)
- Step 7: Internal Approval (Placement Head sign-off locks JD before Phase 4 design creatives)
"""
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.crm.models import Company, HRContact


class JobRequirementStatus:
    DRAFT = "DRAFT"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    UNDER_REVIEW = "UNDER_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

    CHOICES = (
        (DRAFT, "Draft — Requirement Incomplete"),
        (PENDING_VERIFICATION, "Pending Verification"),
        (UNDER_REVIEW, "Under Review — Verification in Progress"),
        (CHANGES_REQUESTED, "Changes Requested — Returned for Correction"),
        (VERIFIED, "Verified — Ready for Placement Head Approval"),
        (APPROVED, "Approved — Locked for Creative Design & Drives"),
        (REJECTED, "Rejected — Opportunity Declined"),
    )


class EmploymentType:
    FULL_TIME = "FULL_TIME"
    INTERNSHIP = "INTERNSHIP"
    INTERNSHIP_PPO = "INTERNSHIP_PPO"
    CONTRACT = "CONTRACT"

    CHOICES = (
        (FULL_TIME, "Full-Time Employment"),
        (INTERNSHIP, "Internship Only"),
        (INTERNSHIP_PPO, "Internship with PPO / FTE Conversion"),
        (CONTRACT, "Fixed-Term Contract"),
    )


class WorkArrangement:
    ON_SITE = "ON_SITE"
    HYBRID = "HYBRID"
    REMOTE = "REMOTE"

    CHOICES = (
        (ON_SITE, "On-Site Office / Campus"),
        (HYBRID, "Hybrid (Office & Remote)"),
        (REMOTE, "100% Remote / Work from Home"),
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


class ChecklistItemCode:
    ELIGIBILITY = "ELIGIBILITY"
    SALARY_AUTHENTICITY = "SALARY_AUTHENTICITY"
    COMPANY_AUTHENTICITY = "COMPANY_AUTHENTICITY"
    INTERVIEW_PROCESS = "INTERVIEW_PROCESS"
    REGISTRATION_DEADLINE = "REGISTRATION_DEADLINE"

    CHOICES = (
        (ELIGIBILITY, "Candidate Academic & Degree Eligibility"),
        (SALARY_AUTHENTICITY, "Salary Package & CTC Authenticity"),
        (COMPANY_AUTHENTICITY, "Company Authenticity & Hiring Legitimacy"),
        (INTERVIEW_PROCESS, "Interview & Selection Process Clarity"),
        (REGISTRATION_DEADLINE, "Registration Deadline & Drive Timelines"),
    )


# Authoritative 5-Point Verification Specification (Workflow Step 6)
DEFAULT_CHECKLIST_SPECS = [
    {
        "item_code": ChecklistItemCode.ELIGIBILITY,
        "title": "Candidate Academic & Degree Eligibility",
        "description": "Verify eligible academic branches, minimum CGPA/percentage cutoff, maximum allowable active backlogs, and passing-out batches.",
        "is_mandatory": True,
    },
    {
        "item_code": ChecklistItemCode.SALARY_AUTHENTICITY,
        "title": "Salary Package & CTC Authenticity",
        "description": "Verify gross vs. net CTC breakdown, fixed vs. variable components, training/probation stipend, and any service agreement deductions.",
        "is_mandatory": True,
    },
    {
        "item_code": ChecklistItemCode.COMPANY_AUTHENTICITY,
        "title": "Company Authenticity & Hiring Legitimacy",
        "description": "Confirm legitimate corporate entity registration, active corporate domain/website, legitimate HR contact authority, and genuine hiring intent.",
        "is_mandatory": True,
    },
    {
        "item_code": ChecklistItemCode.INTERVIEW_PROCESS,
        "title": "Interview & Selection Process Clarity",
        "description": "Verify the complete sequence of evaluation stages (Online Aptitude, Technical Rounds, HR Interview), evaluation modes, and test platforms.",
        "is_mandatory": True,
    },
    {
        "item_code": ChecklistItemCode.REGISTRATION_DEADLINE,
        "title": "Registration Deadline & Drive Timelines",
        "description": "Verify reasonable student application turnaround time, drive dates feasibility, and schedule alignment with academic calendar.",
        "is_mandatory": True,
    },
]


class JobRequirement(TimeStampedModel):
    """Institutional hiring requirement collected from corporate partners (Workflow Steps 5–7)."""

    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="job_requirements",
        help_text="Corporate entity offering this employment opportunity.",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_requirements",
        help_text="Corporate HR lead who provided the job description.",
    )
    title = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Role or job designation title (e.g. Associate Software Engineer).",
    )
    job_description = models.TextField(
        help_text="Detailed job description, responsibilities, and role overview.",
    )
    skills_required = models.TextField(
        help_text="Mandatory and preferred technical and professional competencies.",
    )

    # Compensation attributes (Step 5)
    min_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum annual CTC or monthly stipend in currency units.",
    )
    max_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum annual CTC or monthly stipend in currency units.",
    )
    salary_currency = models.CharField(
        max_length=10,
        default="INR",
        help_text="Currency code (e.g. INR, USD).",
    )
    salary_breakup = models.TextField(
        blank=True,
        default="",
        help_text="Breakdown of fixed pay, performance variable, benefits, and probation terms.",
    )

    # Work terms (Step 5)
    location = models.CharField(
        max_length=255,
        help_text="Primary work location(s) or base branch (e.g. Bangalore, Hyderabad).",
    )
    work_arrangement = models.CharField(
        max_length=30,
        choices=WorkArrangement.CHOICES,
        default=WorkArrangement.ON_SITE,
        db_index=True,
    )
    employment_type = models.CharField(
        max_length=30,
        choices=EmploymentType.CHOICES,
        default=EmploymentType.FULL_TIME,
        db_index=True,
    )
    has_bond = models.BooleanField(
        default=False,
        help_text="Indicates whether a service agreement or bond is required.",
    )
    bond_details = models.TextField(
        blank=True,
        default="",
        help_text="Duration and penalty clauses of the service agreement, if applicable.",
    )

    # Candidate qualifications (Step 5)
    eligibility_criteria = models.TextField(
        blank=True,
        default="",
        help_text="Academic criteria, degree branches, minimum CGPA, and backlog thresholds.",
    )
    min_cgpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum required academic CGPA on a 10.0 scale.",
    )

    # Hiring process and drive timeline (Step 5)
    hiring_process = models.TextField(
        blank=True,
        default="",
        help_text="Sequential stages of the recruitment drive (e.g. Aptitude -> Technical -> HR).",
    )
    interview_date = models.DateField(
        null=True,
        blank=True,
        help_text="Tentative or confirmed drive date.",
    )
    registration_deadline = models.DateTimeField(
        db_index=True,
        help_text="Strict cutoff timestamp for student registrations.",
    )
    openings_count = models.PositiveIntegerField(
        default=1,
        help_text="Estimated or confirmed number of available vacancies.",
    )

    # Lifecycle state machine (Steps 5–7)
    status = models.CharField(
        max_length=30,
        choices=JobRequirementStatus.CHOICES,
        default=JobRequirementStatus.DRAFT,
        db_index=True,
    )

    # Ownership & Attribution
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_jobs",
    )
    assigned_verifier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_job_verifications",
        help_text="Placement Officer or Head assigned to verify checklist items.",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_jobs",
        help_text="User who completed the mandatory verification checklist.",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_jobs",
        help_text="Placement Head or Admin who signed off on the opportunity.",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    # Decision metadata
    rejection_reason = models.TextField(blank=True, default="")
    return_reason = models.TextField(blank=True, default="")
    notes = models.TextField(blank=True, default="")
    is_archived = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "jobs_requirement"
        ordering = ["-created_at"]
        verbose_name = "Job Requirement"
        verbose_name_plural = "Job Requirements"
        indexes = [
            models.Index(fields=["company", "status"]),
            models.Index(fields=["status", "registration_deadline"]),
            models.Index(fields=["is_archived", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} at {self.company.name} ({self.status})"

    @property
    def is_locked(self) -> bool:
        """Approved opportunities are locked against arbitrary changes to protect downstream creatives."""
        return self.status == JobRequirementStatus.APPROVED

    @property
    def is_editable(self) -> bool:
        """Requirements in draft or return-for-correction status may be updated by authorized staff."""
        return self.status in (JobRequirementStatus.DRAFT, JobRequirementStatus.CHANGES_REQUESTED)

    @property
    def all_mandatory_verified(self) -> bool:
        """Check whether every mandatory checklist item has been verified."""
        mandatory_items = self.checklist_items.filter(is_mandatory=True)
        if not mandatory_items.exists():
            return False
        return not mandatory_items.exclude(status=ChecklistItemStatus.VERIFIED).exists()

    @property
    def checklist_progress(self) -> dict:
        """Summary of verified vs total mandatory checklist items."""
        total = self.checklist_items.filter(is_mandatory=True).count()
        verified = self.checklist_items.filter(
            is_mandatory=True, status=ChecklistItemStatus.VERIFIED
        ).count()
        return {
            "total_mandatory": total,
            "verified_mandatory": verified,
            "percentage": int((verified / total) * 100) if total > 0 else 0,
            "is_complete": (total > 0 and verified == total),
        }


class JobChecklistItem(TimeStampedModel):
    """Individual verification checklist audit item for a Job Requirement (Step 6)."""

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name="checklist_items",
    )
    item_code = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Canonical code for verification item (e.g. ELIGIBILITY, SALARY_AUTHENTICITY).",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    is_mandatory = models.BooleanField(
        default=True,
        help_text="Mandatory items must evaluate to VERIFIED before approval is unlocked.",
    )
    status = models.CharField(
        max_length=30,
        choices=ChecklistItemStatus.CHOICES,
        default=ChecklistItemStatus.PENDING,
        db_index=True,
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_checklist_items",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(
        blank=True,
        default="",
        help_text="Auditor notes, verification findings, or correction instructions.",
    )

    class Meta:
        db_table = "jobs_checklist_item"
        ordering = ["created_at"]
        verbose_name = "Job Verification Checklist Item"
        verbose_name_plural = "Job Verification Checklist Items"
        constraints = [
            models.UniqueConstraint(
                fields=["job_requirement", "item_code"],
                name="unique_job_checklist_item",
            ),
        ]

    def __str__(self) -> str:
        return f"[{self.item_code}] {self.title} — {self.status}"


class JobApprovalDecision(models.Model):
    """Immutable audit log of verification, review, and approval lifecycle events (Steps 5–7)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.CASCADE,
        related_name="decisions",
    )
    decision = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Action performed: SUBMITTED, CHANGES_REQUESTED, VERIFIED, APPROVED, REJECTED, REOPENED.",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="job_decisions",
    )
    actor_role = models.CharField(max_length=50, blank=True, default="")
    comments = models.TextField(
        blank=True,
        default="",
        help_text="Mandatory or contextual comments accompanying the decision.",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "jobs_approval_decision"
        ordering = ["-created_at"]
        verbose_name = "Job Approval Decision"
        verbose_name_plural = "Job Approval Decisions"

    def __str__(self) -> str:
        return f"{self.decision} on {self.job_requirement.title} by {self.actor} at {self.created_at}"
