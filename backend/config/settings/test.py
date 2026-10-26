"""Automated test settings for GQT HRMS platform.

Optimized for:
- 100% Isolated in-memory/test SQLite execution
- Fast password hashing (MD5 instead of Argon2id)
- Zero external network dependencies
"""
from .base import *  # noqa: F403
import os

DEBUG = False
ENVIRONMENT = "testing"

SECRET_KEY = "django-insecure-test-environment-isolated-secret-key-for-pytest-runs"
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use fast hasher for automated unit/integration tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Disable throttles in automated test runs
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []  # noqa: F405
