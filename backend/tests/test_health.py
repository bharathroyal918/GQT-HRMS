"""Tests for public health check endpoint and secret non-disclosure."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_health_check_endpoint_returns_up_and_safe_metadata():
    """Verify /api/v1/health/ returns HTTP 200, status UP, and does not leak secrets."""
    client = APIClient()
    url = reverse("core:health")
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "gqt-hrms-api"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "correlation_id" in data

    # Verify no secret keywords leaked in response body
    body_text = response.content.decode("utf-8").lower()
    for sensitive_word in ("password", "secret", "token", "supabase", "postgres://", "key"):
        assert sensitive_word not in body_text, f"Potential sensitive word '{sensitive_word}' leaked in health check!"


@pytest.mark.django_db
def test_health_check_correlation_id_header_injected():
    """Verify X-Correlation-ID header is propagated in response."""
    client = APIClient()
    url = reverse("core:health")
    custom_id = "test-corr-id-999"
    response = client.get(url, HTTP_X_CORRELATION_ID=custom_id)

    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == custom_id
    assert response.json()["correlation_id"] == custom_id
