"""Corporate CRM & HR Directory Domain Models.

Preserves the authoritative GQT HRMS workflow:
- Step 1: Identify Target Companies (Domain Categorization, Normalization, Duplicate Protection)
- Step 2: Contact HRs (Multi-channel logging, 100+ outreach/day target)
- Step 3: Record HR Information (Directory of HR Talent leads)
- Step 4: HR Response & Follow-up (Priority follow-up queue, Overdue calculations)
"""
import re
import uuid
from urllib.parse import urlparse
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel


def normalize_company_name(name: str) -> str:
    """Normalize company name by lowercasing, stripping punctuation, and compressing whitespace."""
    if not name:
        return ""
    # Strip common corporate suffixes for matching while preserving core brand
    cleaned = re.sub(r"[^\w\s]", "", name.lower())
    return " ".join(cleaned.split())


def extract_domain(website: str) -> str:
    """Safely extract canonical domain name from a URL."""
    if not website:
        return ""
    url = website.strip().lower()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.split(":")[0]
        # Remove leading www.
        if netloc.startswith("www."):
            netloc = netloc[4:]
        return netloc
    except Exception:
        return ""


class CompanyDomainCategory:
    IT_SERVICES = "IT_SERVICES"
    PRODUCT_TECH = "PRODUCT_TECH"
    CORE_ENGINEERING = "CORE_ENGINEERING"
    FINANCE_BANKING = "FINANCE_BANKING"
    BPO_ITES = "BPO_ITES"
    EDTECH = "EDTECH"
    HEALTHCARE = "HEALTHCARE"
    CONSULTING = "CONSULTING"
    OTHER = "OTHER"

    CHOICES = (
        (IT_SERVICES, "IT Services & Consulting"),
        (PRODUCT_TECH, "Product & SaaS Technology"),
        (CORE_ENGINEERING, "Core Engineering / Manufacturing"),
        (FINANCE_BANKING, "Banking, Financial Services & Insurance"),
        (BPO_ITES, "BPO / ITES / Operations"),
        (EDTECH, "Education & EdTech"),
        (HEALTHCARE, "Healthcare & Life Sciences"),
        (CONSULTING, "Management & Business Consulting"),
        (OTHER, "Other Domain"),
    )


class CompanyTier:
    TIER_1_ENTERPRISE = "TIER_1"
    TIER_2_MIDSIZE = "TIER_2"
    TIER_3_STARTUP = "TIER_3"

    CHOICES = (
        (TIER_1_ENTERPRISE, "Tier 1 — Enterprise / MNC"),
        (TIER_2_MIDSIZE, "Tier 2 — Mid-Market / Established"),
        (TIER_3_STARTUP, "Tier 3 — Startup / Growth Stage"),
    )


class CompanyRelationshipStatus:
    DISCOVERED = "DISCOVERED"
    OUTREACH_IN_PROGRESS = "OUTREACH_IN_PROGRESS"
    CONNECTED = "CONNECTED"
    INTERESTED = "INTERESTED"
    ACTIVE_HIRING_PARTNER = "ACTIVE_HIRING_PARTNER"
    NOT_INTERESTED = "NOT_INTERESTED"
    ON_HOLD = "ON_HOLD"

    CHOICES = (
        (DISCOVERED, "Discovered — Target Identified"),
        (OUTREACH_IN_PROGRESS, "Outreach in Progress"),
        (CONNECTED, "Connected — HR In Conversation"),
        (INTERESTED, "Interested — Fresher Hiring Opportunity"),
        (ACTIVE_HIRING_PARTNER, "Active Hiring Partner"),
        (NOT_INTERESTED, "Not Interested / No Fresher Hiring"),
        (ON_HOLD, "On Hold / Relationship Nurturing"),
    )


class CompanyDiscoverySource:
    MARKET_RESEARCH = "MARKET_RESEARCH"
    LINKEDIN = "LINKEDIN"
    REFERRAL = "REFERRAL"
    CAMPUS_INBOUND = "CAMPUS_INBOUND"
    COLD_OUTREACH = "COLD_OUTREACH"
    JOB_BOARD = "JOB_BOARD"
    OTHER = "OTHER"

    CHOICES = (
        (MARKET_RESEARCH, "Market Research"),
        (LINKEDIN, "LinkedIn Research"),
        (REFERRAL, "Employee / Corporate Referral"),
        (CAMPUS_INBOUND, "Campus Inbound Lead"),
        (COLD_OUTREACH, "Cold Outreach"),
        (JOB_BOARD, "Job Board / Portal Listing"),
        (OTHER, "Other Channel"),
    )


class OutreachChannel:
    CALL = "CALL"
    EMAIL = "EMAIL"
    LINKEDIN = "LINKEDIN"
    WHATSAPP = "WHATSAPP"
    IN_PERSON = "IN_PERSON"
    OTHER = "OTHER"

    CHOICES = (
        (CALL, "Phone Call"),
        (EMAIL, "Email Communication"),
        (LINKEDIN, "LinkedIn InMail / Message"),
        (WHATSAPP, "WhatsApp Business Outreach"),
        (IN_PERSON, "In-Person Corporate Visit"),
        (OTHER, "Other Channel"),
    )


class OutreachOutcome:
    CONNECTED_INTERESTED = "CONNECTED_INTERESTED"
    CONNECTED_NOT_INTERESTED = "CONNECTED_NOT_INTERESTED"
    CONNECTED_CALL_LATER = "CONNECTED_CALL_LATER"
    NO_ANSWER_BUSY = "NO_ANSWER_BUSY"
    INVALID_CONTACT_DETAILS = "INVALID_CONTACT_DETAILS"
    GATEKEEPER_BLOCKED = "GATEKEEPER_BLOCKED"
    FOLLOW_UP_SCHEDULED = "FOLLOW_UP_SCHEDULED"
    REQUIREMENT_COLLECTED = "REQUIREMENT_COLLECTED"

    CHOICES = (
        (CONNECTED_INTERESTED, "Connected — Interested in Hiring"),
        (CONNECTED_NOT_INTERESTED, "Connected — Not Hiring Freshers"),
        (CONNECTED_CALL_LATER, "Connected — Requested Callback"),
        (NO_ANSWER_BUSY, "No Answer / Line Busy"),
        (INVALID_CONTACT_DETAILS, "Invalid Email / Wrong Number"),
        (GATEKEEPER_BLOCKED, "Gatekeeper / Operator Blocked"),
        (FOLLOW_UP_SCHEDULED, "Follow-Up Scheduled"),
        (REQUIREMENT_COLLECTED, "Job Requirement / JD Collected"),
    )


class FollowUpPriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

    CHOICES = (
        (LOW, "Low Priority"),
        (MEDIUM, "Medium Priority"),
        (HIGH, "High Priority"),
        (URGENT, "Urgent — Immediate Action"),
    )


class FollowUpStatus:
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (OPEN, "Open / Scheduled"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    )


class FollowUpCategory:
    HR_OUTREACH = "HR_OUTREACH"
    STUDENT_RECONNECT = "STUDENT_RECONNECT"
    INTERVIEW_CONFIRMATION = "INTERVIEW_CONFIRMATION"
    OFFER_ACCEPTANCE = "OFFER_ACCEPTANCE"
    JOINING_CHECK = "JOINING_CHECK"
    GENERAL_RECONNECT = "GENERAL_RECONNECT"

    CHOICES = (
        (HR_OUTREACH, "Corporate HR Outreach"),
        (STUDENT_RECONNECT, "Candidate Reconnection"),
        (INTERVIEW_CONFIRMATION, "Interview Drive Confirmation"),
        (OFFER_ACCEPTANCE, "Offer Acceptance Tracking"),
        (JOINING_CHECK, "Pre-Joining Engagement Check"),
        (GENERAL_RECONNECT, "General Relationship Nurturing"),
    )


class ReminderChannel:
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    BOTH = "BOTH"
    NONE = "NONE"

    CHOICES = (
        (EMAIL, "Email Notification"),
        (WHATSAPP, "WhatsApp Message"),
        (BOTH, "Email & WhatsApp"),
        (NONE, "No Automated Reminder"),
    )


class ReminderDeliveryStatus:
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"
    RETRY_SCHEDULED = "RETRY_SCHEDULED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (PENDING, "Pending Queue"),
        (PROCESSING, "Processing Transmission"),
        (SENT, "Sent / Submitted to Provider"),
        (DELIVERED, "Delivered to Recipient"),
        (FAILED, "Failed Transmission"),
        (RETRY_SCHEDULED, "Retry Scheduled (Backoff)"),
        (CANCELLED, "Cancelled"),
    )


class StaffNotificationType:
    FOLLOW_UP_DUE = "FOLLOW_UP_DUE"
    FOLLOW_UP_OVERDUE = "FOLLOW_UP_OVERDUE"
    COMMUNICATION_FAILED = "COMMUNICATION_FAILED"
    CASE_ESCALATED = "CASE_ESCALATED"
    SYSTEM_ALERT = "SYSTEM_ALERT"

    CHOICES = (
        (FOLLOW_UP_DUE, "Follow-Up Due for Action"),
        (FOLLOW_UP_OVERDUE, "Follow-Up Overdue Notice"),
        (COMMUNICATION_FAILED, "Failed Communication Alert"),
        (CASE_ESCALATED, "Pending Case Escalation"),
        (SYSTEM_ALERT, "Operational System Alert"),
    )


class CaseEscalationType:
    OVERDUE_FOLLOW_UP = "OVERDUE_FOLLOW_UP"
    UNRESOLVED_COMMUNICATION_FAILURE = "UNRESOLVED_COMMUNICATION_FAILURE"

    CHOICES = (
        (OVERDUE_FOLLOW_UP, "Overdue Follow-Up SLA Breach"),
        (UNRESOLVED_COMMUNICATION_FAILURE, "Unresolved Communication Failure"),
    )


class CaseEscalationStatus:
    PENDING = "PENDING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"

    CHOICES = (
        (PENDING, "Pending Review"),
        (ACKNOWLEDGED, "Acknowledged by Officer"),
        (RESOLVED, "Resolved"),
        (DISMISSED, "Dismissed"),
    )


class CaseEscalationLevel:
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"

    CHOICES = (
        (LEVEL_1, "Level 1 — Placement Officer Alert"),
        (LEVEL_2, "Level 2 — Placement Head Escalation"),
    )


class Company(TimeStampedModel):
    """Corporate enterprise profile entity categorized by domain and hiring partner lifecycle."""

    name = models.CharField(max_length=255, db_index=True, help_text="Corporate legal or trading name.")
    normalized_name = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Canonical lowercase alphanumeric string for duplicate warnings.",
    )
    website = models.URLField(max_length=500, blank=True, default="", help_text="Corporate official website.")
    domain = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Normalized corporate root domain (e.g. google.com).",
    )
    domain_category = models.CharField(
        max_length=50,
        choices=CompanyDomainCategory.CHOICES,
        default=CompanyDomainCategory.IT_SERVICES,
        db_index=True,
        help_text="Industry domain categorization as required by Step 1.",
    )
    tier = models.CharField(
        max_length=20,
        choices=CompanyTier.CHOICES,
        default=CompanyTier.TIER_2_MIDSIZE,
    )
    relationship_status = models.CharField(
        max_length=50,
        choices=CompanyRelationshipStatus.CHOICES,
        default=CompanyRelationshipStatus.DISCOVERED,
        db_index=True,
    )
    source = models.CharField(
        max_length=50,
        choices=CompanyDiscoverySource.CHOICES,
        default=CompanyDiscoverySource.MARKET_RESEARCH,
    )
    city = models.CharField(max_length=100, blank=True, default="", db_index=True)
    state = models.CharField(max_length=100, blank=True, default="")
    country = models.CharField(max_length=100, blank=True, default="India")
    address = models.TextField(blank=True, default="")

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_companies",
        help_text="Assigned Relationship Manager or Placement Officer.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_companies",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_companies",
    )
    notes = models.TextField(blank=True, default="")
    is_archived = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "crm_company"
        ordering = ["name"]
        verbose_name = "Company"
        verbose_name_plural = "Companies"
        indexes = [
            models.Index(fields=["domain_category", "relationship_status"]),
            models.Index(fields=["normalized_name"]),
            models.Index(fields=["domain"]),
            models.Index(fields=["is_archived", "relationship_status"]),
        ]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        self.normalized_name = normalize_company_name(self.name)
        if self.website:
            self.domain = extract_domain(self.website)
        super().save(*args, **kwargs)


class HRContact(TimeStampedModel):
    """Directory of Corporate HR talent leads and recruitment relationship managers (Step 3)."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="hr_contacts",
        help_text="Corporate entity employing this contact.",
    )
    name = models.CharField(max_length=255, db_index=True, help_text="Contact full name.")
    designation = models.CharField(max_length=150, blank=True, default="", help_text="Job title or role in HR.")
    department = models.CharField(max_length=100, blank=True, default="Human Resources")
    email = models.EmailField(blank=True, default="", db_index=True, help_text="Corporate work email.")
    phone = models.CharField(max_length=30, blank=True, default="", db_index=True, help_text="Primary work phone.")
    alt_phone = models.CharField(max_length=30, blank=True, default="")
    linkedin_url = models.URLField(max_length=500, blank=True, default="")
    preferred_channel = models.CharField(
        max_length=20,
        choices=OutreachChannel.CHOICES,
        default=OutreachChannel.CALL,
    )
    status = models.CharField(
        max_length=30,
        choices=(
            ("ACTIVE", "Active"),
            ("PROSPECT", "Prospect"),
            ("INACTIVE", "Inactive"),
            ("BOUNCED_INVALID", "Bounced / Invalid Details"),
            ("LEFT_COMPANY", "Left Company"),
        ),
        default="ACTIVE",
        db_index=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="owned_contacts",
    )
    notes = models.TextField(blank=True, default="")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_contacts",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_contacts",
    )
    is_archived = models.BooleanField(default=False, db_index=True)

    class Meta:
        db_table = "crm_hr_contact"
        ordering = ["name"]
        verbose_name = "HR Contact"
        verbose_name_plural = "HR Contacts"
        indexes = [
            models.Index(fields=["company", "is_archived"]),
            models.Index(fields=["email"]),
            models.Index(fields=["phone"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.designation}) - {self.company.name}"


class OutreachLog(models.Model):
    """Append-only operational history recording multi-channel HR outreach activities (Step 2)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="outreach_logs",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="outreach_logs",
    )
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="outreach_activities",
        help_text="User who executed this outreach touchpoint.",
    )
    channel = models.CharField(
        max_length=20,
        choices=OutreachChannel.CHOICES,
        db_index=True,
    )
    direction = models.CharField(
        max_length=20,
        choices=(("OUTBOUND", "Outbound"), ("INBOUND", "Inbound")),
        default="OUTBOUND",
        db_index=True,
    )
    activity_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Timestamp when the outreach actually occurred.",
    )
    outcome = models.CharField(
        max_length=50,
        choices=OutreachOutcome.CHOICES,
        db_index=True,
    )
    subject = models.CharField(max_length=255, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    followup_required = models.BooleanField(default=False)
    correlation_id = models.CharField(max_length=64, blank=True, default="", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "crm_outreach_log"
        ordering = ["-activity_date"]
        verbose_name = "Outreach Log"
        verbose_name_plural = "Outreach Logs"
        indexes = [
            models.Index(fields=["activity_date", "channel"]),
            models.Index(fields=["company", "-activity_date"]),
            models.Index(fields=["performed_by", "activity_date"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel} to {self.company.name} on {self.activity_date.strftime('%Y-%m-%d %H:%M')} [{self.outcome}]"


class FollowUp(models.Model):
    """Scheduled corporate relationship nurturing tasks and callbacks (Step 4)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="follow_ups",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="follow_ups",
    )
    related_outreach = models.ForeignKey(
        OutreachLog,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_follow_ups",
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_follow_ups",
    )
    due_date = models.DateTimeField(db_index=True, help_text="Target date and time for this follow-up.")
    priority = models.CharField(
        max_length=20,
        choices=FollowUpPriority.CHOICES,
        default=FollowUpPriority.MEDIUM,
        db_index=True,
    )
    status = models.CharField(
        max_length=30,
        choices=FollowUpStatus.CHOICES,
        default=FollowUpStatus.OPEN,
        db_index=True,
    )
    category = models.CharField(
        max_length=40,
        choices=FollowUpCategory.CHOICES,
        default=FollowUpCategory.HR_OUTREACH,
        db_index=True,
        help_text="Operational classification of this follow-up task.",
    )
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_follow_ups",
        help_text="Optional candidate associated with student reconnection or placement follow-ups.",
    )
    job_requirement = models.ForeignKey(
        "jobs.JobRequirement",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_follow_ups",
        help_text="Optional job requirement associated with hiring follow-ups.",
    )
    interview_schedule = models.ForeignKey(
        "interviews.InterviewSchedule",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_follow_ups",
        help_text="Optional interview drive associated with attendance or outcome follow-ups.",
    )
    placement_status = models.ForeignKey(
        "placements.CandidatePlacementStatus",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_follow_ups",
        help_text="Optional placement status associated with offer acceptance or joining follow-ups.",
    )
    purpose = models.CharField(max_length=255, help_text="Objective of the follow-up.")
    notes = models.TextField(blank=True, default="", help_text="Detailed notes and historical context.")
    remind_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Target datetime to trigger automated reminder notification dispatch.",
    )
    reminder_channel = models.CharField(
        max_length=20,
        choices=ReminderChannel.CHOICES,
        default=ReminderChannel.EMAIL,
        help_text="Channel preference for automated follow-up reminder.",
    )
    completion_notes = models.TextField(blank=True, default="")
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="completed_follow_ups",
    )
    cancellation_reason = models.TextField(blank=True, default="")
    rescheduled_count = models.PositiveIntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_follow_ups",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_follow_ups",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crm_follow_up"
        ordering = ["due_date", "priority"]
        verbose_name = "Follow-Up"
        verbose_name_plural = "Follow-Ups"
        indexes = [
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["assigned_to", "status", "due_date"]),
            models.Index(fields=["company", "status"]),
            models.Index(fields=["category", "status"]),
            models.Index(fields=["remind_at", "status"]),
        ]

    def __str__(self) -> str:
        return f"Follow-up for {self.company.name} due {self.due_date.strftime('%Y-%m-%d')} [{self.status}]"

    @property
    def is_overdue(self) -> bool:
        """Dynamically evaluate whether this follow-up has breached its scheduled due date."""
        if self.status in [FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS]:
            return self.due_date < timezone.now()
        return False


class CRMConfiguration(models.Model):
    """Configurable system operational targets such as the 100+ outreach/day benchmark."""

    key = models.CharField(max_length=100, unique=True, db_index=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "crm_configuration"
        verbose_name = "CRM Configuration"
        verbose_name_plural = "CRM Configurations"

    def __str__(self) -> str:
        return f"{self.key} = {self.value}"


class CRMReconciliationRun(TimeStampedModel):
    """Immutable audit record of Phase 10 CRM database integration and reconciliation runs."""

    triggered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="crm_reconciliation_runs",
        help_text="User who initiated this reconciliation run.",
    )
    status = models.CharField(
        max_length=32,
        choices=(
            ("SUCCESS", "Success — All Records Consistent"),
            ("PARTIAL_WITH_CONFLICTS", "Completed — Conflicts Identified"),
            ("FAILED", "Reconciliation Failed"),
        ),
        default="SUCCESS",
        db_index=True,
    )
    total_records_checked = models.PositiveIntegerField(
        default=0,
        help_text="Total domain records evaluated across the 8 CRM data areas.",
    )
    conflicts_detected = models.PositiveIntegerField(
        default=0,
        help_text="Total integrity warnings or discrepancies flagged.",
    )
    records_synchronized = models.PositiveIntegerField(
        default=0,
        help_text="Total records reconciled or updated.",
    )
    diagnostic_details = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured breakdown of diagnostic findings across all 8 data areas.",
    )
    summary = models.TextField(
        blank=True,
        default="",
        help_text="Operational summary narrative of the reconciliation run.",
    )

    class Meta:
        db_table = "crm_reconciliation_run"
        ordering = ["-created_at"]
        verbose_name = "CRM Reconciliation Run"
        verbose_name_plural = "CRM Reconciliation Runs"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"CRM Reconciliation on {self.created_at.strftime('%Y-%m-%d %H:%M')} [{self.status}]"


class FollowUpReminderItem(TimeStampedModel):
    """Durable transactional queue and history for automated follow-up dispatches (Capability B & C)."""

    follow_up = models.ForeignKey(
        FollowUp,
        on_delete=models.CASCADE,
        related_name="reminder_items",
        help_text="The follow-up record triggering this communication.",
    )
    channel = models.CharField(
        max_length=20,
        choices=(
            (ReminderChannel.EMAIL, "Email Notification"),
            (ReminderChannel.WHATSAPP, "WhatsApp Message"),
        ),
        db_index=True,
    )
    recipient = models.CharField(
        max_length=255,
        help_text="Recipient email address or normalized E.164 phone number.",
    )
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Human-readable recipient name.",
    )
    scheduled_for = models.DateTimeField(
        db_index=True,
        help_text="Earliest timestamp when this reminder becomes eligible for dispatch.",
    )
    status = models.CharField(
        max_length=32,
        choices=ReminderDeliveryStatus.CHOICES,
        default=ReminderDeliveryStatus.PENDING,
        db_index=True,
    )
    attempt_count = models.PositiveIntegerField(default=0)
    max_attempts = models.PositiveIntegerField(default=3)
    backoff_until = models.DateTimeField(null=True, blank=True, db_index=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        db_index=True,
        help_text="Unique transmission identifier returned by provider adapter.",
    )
    error_message = models.TextField(blank=True, default="")
    is_simulated = models.BooleanField(
        default=True,
        help_text="Truthful flag indicating whether this delivery was local/simulated vs live provider.",
    )
    idempotency_key = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="Deterministic hash preventing duplicate queues for the same logical event.",
    )
    template_name = models.CharField(max_length=100, blank=True, default="")
    template_context = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "crm_follow_up_reminder_item"
        ordering = ["scheduled_for", "created_at"]
        verbose_name = "Follow-Up Reminder Item"
        verbose_name_plural = "Follow-Up Reminder Items"
        indexes = [
            models.Index(fields=["status", "scheduled_for"]),
            models.Index(fields=["follow_up", "status"]),
            models.Index(fields=["channel", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.channel} to {self.recipient} [{self.status}] (Follow-Up: {self.follow_up_id})"


class StaffNotification(TimeStampedModel):
    """In-app alert and inbox notifications for Placement Officers and staff (Capability D)."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="staff_notifications",
        help_text="Placement Officer or staff user receiving this notification.",
    )
    notification_type = models.CharField(
        max_length=40,
        choices=StaffNotificationType.CHOICES,
        default=StaffNotificationType.FOLLOW_UP_DUE,
        db_index=True,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Internal frontend route link to the relevant workspace.",
    )
    follow_up = models.ForeignKey(
        FollowUp,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staff_notifications",
    )
    is_read = models.BooleanField(default=False, db_index=True)
    read_at = models.DateTimeField(null=True, blank=True)
    idempotency_key = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="Deterministic event key preventing duplicate notifications.",
    )

    class Meta:
        db_table = "crm_staff_notification"
        ordering = ["-created_at"]
        verbose_name = "Staff Notification"
        verbose_name_plural = "Staff Notifications"
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"]),
            models.Index(fields=["notification_type", "-created_at"]),
        ]

    def __str__(self) -> str:
        return f"Notification for {self.recipient.email}: {self.title} [{'READ' if self.is_read else 'UNREAD'}]"


class CaseEscalation(TimeStampedModel):
    """Auditable escalation records for overdue follow-ups and unresolved failures (Capability E)."""

    case_type = models.CharField(
        max_length=40,
        choices=CaseEscalationType.CHOICES,
        default=CaseEscalationType.OVERDUE_FOLLOW_UP,
        db_index=True,
    )
    follow_up = models.ForeignKey(
        FollowUp,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="escalations",
        help_text="Follow-up case triggering escalation.",
    )
    reminder_item = models.ForeignKey(
        FollowUpReminderItem,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escalations",
        help_text="Optional failed communication item triggering escalation.",
    )
    escalated_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="received_escalations",
        help_text="Authorized supervisor or Placement Head receiving the escalation.",
    )
    escalated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="triggered_escalations",
        help_text="User who triggered the escalation, or null if automated background worker.",
    )
    previous_assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="prior_escalated_cases",
        help_text="Officer originally assigned to this case prior to escalation.",
    )
    reason = models.TextField(help_text="Explicit justification or condition triggering escalation.")
    escalation_level = models.CharField(
        max_length=20,
        choices=CaseEscalationLevel.CHOICES,
        default=CaseEscalationLevel.LEVEL_1,
        db_index=True,
    )
    status = models.CharField(
        max_length=30,
        choices=CaseEscalationStatus.CHOICES,
        default=CaseEscalationStatus.PENDING,
        db_index=True,
    )
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acknowledged_escalations",
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_escalations",
    )
    resolution_notes = models.TextField(blank=True, default="")
    idempotency_key = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="Deterministic event key preventing duplicate escalations for the same condition.",
    )

    class Meta:
        db_table = "crm_case_escalation"
        ordering = ["-created_at"]
        verbose_name = "Case Escalation"
        verbose_name_plural = "Case Escalations"
        indexes = [
            models.Index(fields=["status", "-created_at"]),
            models.Index(fields=["escalated_to", "status"]),
            models.Index(fields=["case_type", "status"]),
        ]

    def __str__(self) -> str:
        return f"Escalation [{self.case_type}] to {self.escalated_to.email} [{self.status}]"

