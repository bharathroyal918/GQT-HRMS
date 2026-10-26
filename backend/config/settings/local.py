"""Local development settings for GQT HRMS platform."""
from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)

# Allow local dev loopbacks
ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=["localhost", "127.0.0.1", "0.0.0.0"],
)

# Cookies do not require Secure flag when testing locally over HTTP
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=False)
JWT_COOKIE_SECURE = env.bool("JWT_COOKIE_SECURE", default=False)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
