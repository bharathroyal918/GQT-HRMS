"""Core architectural models: TimeStampedModel and immutable AuditLog."""
import uuid
from django.conf import settings
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base model supplying UUID primary key, timestamps, and soft deletion."""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Cryptographically secure, non-enumerable primary key.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="UTC timestamp when the record was initially created.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="UTC timestamp when the record was last modified.",
    )
    is_deleted = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Soft deletion flag to maintain historical referential integrity.",
    )

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class AuditLog(models.Model):
    """Immutable audit trail recording administrative and domain actions across the SaaS platform."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=128, db_index=True)
    resource_type = models.CharField(max_length=128, db_index=True)
    resource_id = models.CharField(max_length=128, db_index=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default="")
    changes = models.JSONField(default=dict, blank=True)
    correlation_id = models.CharField(max_length=64, db_index=True, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "core_audit_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["resource_type", "resource_id"]),
            models.Index(fields=["action", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.created_at.isoformat()} | {self.action} on {self.resource_type}:{self.resource_id}"


class NotificationCategory:
    SYSTEM = "SYSTEM"
    JOB_DRIVE = "JOB_DRIVE"
    APPLICATION = "APPLICATION"
    INTERVIEW = "INTERVIEW"
    PLACEMENT = "PLACEMENT"
    FOLLOW_UP = "FOLLOW_UP"

    CHOICES = (
        (SYSTEM, "System Notice"),
        (JOB_DRIVE, "Job & Recruitment Drive"),
        (APPLICATION, "Application Update"),
        (INTERVIEW, "Interview Update"),
        (PLACEMENT, "Placement Outcome"),
        (FOLLOW_UP, "CRM & Follow-Up Alert"),
    )


class Notification(TimeStampedModel):
    """Platform-wide in-app notification entity supporting recipient-isolated delivery and unread tracking."""

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
        help_text="User recipient of this in-app notification.",
        db_index=True,
    )
    category = models.CharField(
        max_length=40,
        choices=NotificationCategory.CHOICES,
        default=NotificationCategory.SYSTEM,
        db_index=True,
        help_text="Functional domain category of the notification.",
    )
    title = models.CharField(
        max_length=255,
        help_text="Concise summary header for the notification.",
    )
    message = models.TextField(
        help_text="Detailed explanatory notification body.",
    )
    link = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Internal application route link (e.g. /students/drives).",
    )
    is_read = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicates whether the recipient has acknowledged or viewed this notification.",
    )
    read_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="UTC timestamp when the notification was marked as read.",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Sanitized structured context payload. Strictly forbids secrets and credentials.",
    )
    idempotency_key = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        unique=True,
        db_index=True,
        help_text="Deterministic event key preventing duplicate notifications on retries.",
    )

    class Meta:
        db_table = "core_notification"
        ordering = ["-created_at"]
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        indexes = [
            models.Index(fields=["recipient", "is_read", "-created_at"], name="core_notif_recip_read_idx"),
            models.Index(fields=["recipient", "-created_at"], name="core_notif_recip_created_idx"),
            models.Index(fields=["category", "-created_at"], name="core_notif_cat_created_idx"),
        ]

    def __str__(self) -> str:
        status_str = "READ" if self.is_read else "UNREAD"
        return f"Notification for {self.recipient.email}: [{self.category}] {self.title} ({status_str})"

