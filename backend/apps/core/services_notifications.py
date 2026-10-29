"""Service layer for Global Notification Center (Phase 15 Workstream 3).

Enforces business logic, recipient isolation, secret sanitization, and deterministic deduplication.
"""
import logging
import uuid
from typing import Any, Dict, Optional, Tuple, Union
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import exceptions
from apps.core.models import Notification, NotificationCategory
from apps.core.selectors_notifications import get_notification_by_id

logger = logging.getLogger(__name__)

User = get_user_model()

SENSITIVE_KEY_PATTERNS = (
    "password",
    "token",
    "secret",
    "refresh",
    "access",
    "authorization",
    "api_key",
    "client_secret",
    "private_key",
    "credentials",
    "credential",
    "session",
    "session_id",
    "otp",
    "hash",
)


def _is_sensitive_key(key: str) -> bool:
    k_lower = str(key).lower()
    return any(p in k_lower for p in SENSITIVE_KEY_PATTERNS)


def sanitize_notification_metadata(metadata: Any) -> Any:
    """Recursively scrub any sensitive credential keys or nested structures from notification metadata."""
    if not metadata:
        return {}
    if isinstance(metadata, dict):
        sanitized = {}
        for k, v in metadata.items():
            if _is_sensitive_key(k):
                sanitized[k] = "[REDACTED]"
            else:
                sanitized[k] = sanitize_notification_metadata(v)
        return sanitized
    if isinstance(metadata, (list, tuple, set)):
        return [sanitize_notification_metadata(item) for item in metadata]
    return metadata


def create_notification(
    recipient: Optional[User],
    category: str,
    title: str,
    message: str,
    link: str = "",
    metadata: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> Tuple[Optional[Notification], bool]:
    """Create a new in-app notification with deduplication and metadata secret scrubbing.

    Returns:
        (notification_instance, created_boolean)
        If recipient is missing or inactive, returns (None, False) without raising errors.
        Fail-safe: Catches any database or integrity error to prevent aborting primary business transactions.
    """
    if not recipient or not recipient.is_active:
        return None, False

    clean_key = str(idempotency_key).strip() if idempotency_key and str(idempotency_key).strip() else None

    if clean_key:
        existing = Notification.objects.filter(
            idempotency_key=clean_key,
        ).first()
        if existing:
            return existing, False

    # Ensure valid category
    valid_categories = {c[0] for c in NotificationCategory.CHOICES}
    cat = category if category in valid_categories else NotificationCategory.SYSTEM

    clean_metadata = sanitize_notification_metadata(metadata or {})

    # Constrain links to internal routes only (prevent open redirects or javascript: URIs)
    clean_link = str(link).strip()[:500] if link else ""
    if clean_link and not clean_link.startswith("/"):
        clean_link = ""

    try:
        with transaction.atomic():
            notification = Notification.objects.create(
                recipient=recipient,
                category=cat,
                title=title.strip()[:255],
                message=message.strip(),
                link=clean_link,
                metadata=clean_metadata,
                idempotency_key=clean_key,
            )
            return notification, True
    except IntegrityError:
        # Concurrent creation with identical clean_key
        if clean_key:
            existing = Notification.objects.filter(
                idempotency_key=clean_key,
            ).first()
            if existing:
                return existing, False
        logger.warning("Notification creation failed integrity check for recipient %s", recipient.id)
        return None, False
    except Exception as exc:
        logger.exception("Unexpected error during notification creation: %s", exc)
        return None, False


def mark_notification_as_read(
    user: User,
    notification_id: Union[str, uuid.UUID],
) -> Notification:
    """Mark a specific notification as read, enforcing strict recipient isolation.

    Raises:
        NotFound if notification does not exist or belongs to another user.
    """
    notification = get_notification_by_id(user, notification_id)
    if not notification:
        raise exceptions.NotFound("Notification not found.")

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at", "updated_at"])

    return notification


@transaction.atomic
def mark_all_notifications_as_read(user: User) -> int:
    """Mark all unread notifications for the authenticated user as read."""
    if not user or not user.is_authenticated:
        return 0

    now = timezone.now()
    count = Notification.objects.filter(
        recipient=user,
        is_deleted=False,
        is_read=False,
    ).update(
        is_read=True,
        read_at=now,
        updated_at=now,
    )
    return count

