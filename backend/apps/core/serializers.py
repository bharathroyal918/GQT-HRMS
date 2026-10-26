"""Serializers for system diagnostics, health checks, and readiness."""
from rest_framework import serializers


class HealthCheckResponseSerializer(serializers.Serializer):
    """Response serializer for public liveness probe. Strictly zero secrets leaked."""

    status = serializers.CharField(default="UP")
    service = serializers.CharField(default="gqt-hrms-api")
    version = serializers.CharField(default="1.0.0")
    environment = serializers.CharField()
    timestamp = serializers.DateTimeField()
    correlation_id = serializers.CharField()


class ReadinessCheckResponseSerializer(serializers.Serializer):
    """Response serializer for infrastructure readiness probe (DB & Storage)."""

    status = serializers.CharField()
    database = serializers.DictField()
    storage = serializers.DictField()
    timestamp = serializers.DateTimeField()
    correlation_id = serializers.CharField()
