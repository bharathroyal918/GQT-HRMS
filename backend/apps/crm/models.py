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
    purpose = models.CharField(max_length=255, help_text="Objective of the follow-up.")
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

