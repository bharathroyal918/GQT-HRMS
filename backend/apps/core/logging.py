"""Logging filters for sensitive data redaction and correlation ID propagation."""
import logging
import re
import threading

# Thread-local storage for request correlation ID
_thread_locals = threading.local()


def get_current_correlation_id() -> str:
    """Retrieve the current request's correlation ID from thread-local storage."""
    return getattr(_thread_locals, "correlation_id", "SYS-INIT")


def set_current_correlation_id(correlation_id: str) -> None:
    """Set the current request's correlation ID in thread-local storage."""
    _thread_locals.correlation_id = correlation_id


def clear_current_correlation_id() -> None:
    """Clear thread-local correlation storage."""
    if hasattr(_thread_locals, "correlation_id"):
        del _thread_locals.correlation_id


class SensitiveDataFilter(logging.Filter):
    """Logging filter to inject correlation ID and redact passwords, tokens, and secrets."""

    SENSITIVE_PATTERNS = [
        (re.compile(r'(password["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1[REDACTED]\3'),
        (re.compile(r'(secret["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1[REDACTED]\3'),
        (re.compile(r'(token["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1[REDACTED]\3'),
        (re.compile(r'(Bearer\s+)([A-Za-z0-9\-._~+/]+=*)', re.IGNORECASE), r'\1[REDACTED_JWT]'),
        (re.compile(r'(api[_-]?key["\']?\s*[:=]\s*["\'])([^"\']+)(["\'])', re.IGNORECASE), r'\1[REDACTED]\3'),
        (re.compile(r'(postgresql:\/\/[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1[REDACTED_PASSWORD]\3'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        # Inject correlation_id if not present
        if not hasattr(record, "correlation_id"):
            record.correlation_id = get_current_correlation_id()

        # Sanitize log message string
        if isinstance(record.msg, str):
            sanitized = record.msg
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                sanitized = pattern.sub(replacement, sanitized)
            record.msg = sanitized

        return True
