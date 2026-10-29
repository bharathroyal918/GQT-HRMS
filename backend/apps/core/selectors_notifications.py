"""Selectors for Global Notification Center (Phase 15 Workstream 3).

Strict recipient-level query isolation enforcing that users can only ever access their own notifications.
"""
import uuid
from typing import Optional, Union
from django.contrib.auth import get_user_model
from django.db.models import QuerySet
from apps.core.models import Notification

User = get_user_model()


def get_user_notifications(
    user: User,
    is_read: Optional[bool] = None,
    category: Optional[str] = None,
) -> QuerySet[Notification]:
    """Retrieve notifications scoped strictly to the authenticated recipient."""
    if not user or not user.is_authenticated:
        return Notification.objects.none()

    qs = Notification.objects.filter(recipient=user, is_deleted=False)

    if is_read is not None:
        qs = qs.filter(is_read=is_read)

    if category:
        qs = qs.filter(category=category)

    return qs.order_by("-created_at")


def get_unread_notification_count(user: User) -> int:
    """Return count of unread, non-deleted notifications for the authenticated user."""
    if not user or not user.is_authenticated:
        return 0
    return Notification.objects.filter(
        recipient=user,
        is_deleted=False,
        is_read=False,
    ).count()


def get_notification_by_id(
    user: User,
    notification_id: Union[str, uuid.UUID],
) -> Optional[Notification]:
    """Retrieve a single notification ensuring it strictly belongs to the requesting recipient."""
    if not user or not user.is_authenticated:
        return None
    try:
        return Notification.objects.get(
            id=notification_id,
            recipient=user,
            is_deleted=False,
        )
    except (Notification.DoesNotExist, ValueError):
        return None

