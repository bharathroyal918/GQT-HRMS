"""Tests verifying OpenAPI 3.1 schema generation."""
import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_openapi_schema_endpoint():
    """Verify OpenAPI 3.1 JSON schema generates cleanly without errors."""
    client = APIClient()
    url = reverse("schema")
    response = client.get(url, HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    schema = response.json()
    assert schema["openapi"].startswith("3.")
    assert schema["info"]["title"] == "GQT HRMS & Recruitment CRM API"
    assert "/api/v1/health/" in schema["paths"]
    assert "/api/v1/ready/" in schema["paths"]
