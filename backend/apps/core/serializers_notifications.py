"""Serializers for Global Notification Center (Phase 15 Workstream 3).

Exposes strictly read-only notification attributes, preventing any tampering with protected fields.
"""
from rest_framework import serializers
from apps.core.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Read-only presentation serializer for notification records."""

    metadata = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "category",
            "title",
            "message",
            "link",
            "is_read",
            "read_at",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields

    def get_metadata(self, obj: Notification) -> dict:
        from apps.core.services_notifications import sanitize_notification_metadata
        return sanitize_notification_metadata(obj.metadata or {})


class NotificationUnreadCountSerializer(serializers.Serializer):
    """Response envelope for unread badge count."""

    count = serializers.IntegerField(read_only=True)

