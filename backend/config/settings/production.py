"""Hardened production settings for GQT HRMS platform.

Fail-Closed Security Invariants:
- Rejects boot if DJANGO_SECRET_KEY is omitted, weak, or contains 'insecure'
- Rejects boot if DJANGO_ALLOWED_HOSTS is wildcard or only local
- Rejects boot if Database password is empty or default
- Enforces SSL/TLS redirects and Secure cookie flags
"""
from django.core.exceptions import ImproperlyConfigured
from .base import *  # noqa: F403
from .base import env, DATABASES, DEV_FALLBACK_SECRET_KEY

DEBUG = False
ENVIRONMENT = "production"

# Re-read production environment overrides directly
SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=[])

# Invariant 1: Fail-closed on missing, short, or placeholder SECRET_KEY
if (
    not SECRET_KEY
    or len(SECRET_KEY) < 40
    or "insecure" in SECRET_KEY.lower()
    or SECRET_KEY == DEV_FALLBACK_SECRET_KEY
):
    raise ImproperlyConfigured(
        "Production Security Violation: DJANGO_SECRET_KEY must be an explicit, "
        "high-entropy string of at least 40 characters without 'insecure' placeholders."
    )

# Invariant 2: Fail-closed on missing, wildcard, or only-localhost ALLOWED_HOSTS
if not ALLOWED_HOSTS or "*" in ALLOWED_HOSTS or set(ALLOWED_HOSTS) <= {"localhost", "127.0.0.1", "0.0.0.0"}:
    raise ImproperlyConfigured(
        "Production Security Violation: DJANGO_ALLOWED_HOSTS must contain valid production "
        "fully qualified domain names. Wildcards and localhost-only lists are prohibited."
    )

# Invariant 3: Fail-closed on missing or insecure database credentials
db_config = DATABASES.get("default", {})
db_pass = env.str("DB_PASSWORD", default=str(db_config.get("PASSWORD", "")))
if not db_pass or db_pass.lower() in ("change_me", "postgres", "password", "root", "admin", "123456"):
    raise ImproperlyConfigured(
        "Production Security Violation: Production database password must be configured "
        "with a strong, non-default credential."
    )

# Invariant 4: Mandatory HTTPS Cookie Security
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
JWT_COOKIE_SECURE = env.bool("JWT_COOKIE_SECURE", default=True)

if not SESSION_COOKIE_SECURE or not CSRF_COOKIE_SECURE:
    raise ImproperlyConfigured(
        "Production Security Violation: SESSION_COOKIE_SECURE and CSRF_COOKIE_SECURE "
        "must be enabled in production."
    )

# Invariant 5: Transport Layer Security & Hardening Headers
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = env.bool("SECURE_HSTS_PRELOAD", default=False)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
