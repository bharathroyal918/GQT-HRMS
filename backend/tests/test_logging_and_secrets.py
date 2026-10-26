"""Tests for log redaction filter and correlation tracking."""
import logging
import pytest
from apps.core.logging import (
    SensitiveDataFilter,
    set_current_correlation_id,
    clear_current_correlation_id,
)


def test_sensitive_data_filter_redacts_credentials():
    """Verify SensitiveDataFilter redacts passwords, tokens, and database connection strings."""
    filter_instance = SensitiveDataFilter()
    set_current_correlation_id("test-corr-abc-123")

    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname=__file__,
        lineno=20,
        msg="Connecting with password='super_secret_password' and token=\"jwt_token_123\" to postgresql://user:mypassword@db.supabase.com:5432/db",
        args=(),
        exc_info=None,
    )

    filter_instance.filter(record)

    assert record.correlation_id == "test-corr-abc-123"
    assert "super_secret_password" not in record.msg
    assert "[REDACTED]" in record.msg
    assert "mypassword" not in record.msg
    assert "[REDACTED_PASSWORD]" in record.msg

    clear_current_correlation_id()
