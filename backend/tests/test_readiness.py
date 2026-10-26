"""Tests for infrastructure readiness probe."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_readiness_probe_success():
    """Verify readiness probe verifies database and storage execution."""
    client = APIClient()
    url = reverse("core:readiness")
    response = client.get(url)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "READY"
    assert data["database"]["status"] == "UP"
    assert data["storage"]["status"] == "UP"
    assert "timestamp" in data
    assert "correlation_id" in data
