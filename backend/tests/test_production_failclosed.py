"""Tests verifying fail-closed security invariants in production settings."""
import os
import importlib
import pytest
from django.core.exceptions import ImproperlyConfigured


@pytest.fixture
def clean_env(monkeypatch):
    """Fixture ensuring isolation from external environment variables."""
    monkeypatch.setenv("SKIP_DOTENV", "true")
    # Clean relevant env vars
    for key in (
        "DJANGO_SECRET_KEY",
        "DJANGO_ALLOWED_HOSTS",
        "DB_PASSWORD",
        "DATABASE_URL",
        "SESSION_COOKIE_SECURE",
        "CSRF_COOKIE_SECURE",
    ):
        monkeypatch.delenv(key, raising=False)


def test_production_fails_when_secret_key_missing(clean_env, monkeypatch):
    """Production settings must raise ImproperlyConfigured if secret key is omitted."""
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.edu.in")
    monkeypatch.setenv("DB_PASSWORD", "A_Secure_NonDefault_Password_999!")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        import config.settings.production as prod
        importlib.reload(prod)


def test_production_fails_when_secret_key_too_short(clean_env, monkeypatch):
    """Production settings must raise ImproperlyConfigured if secret key is shorter than 40 chars."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "too-short-secret-key")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.edu.in")
    monkeypatch.setenv("DB_PASSWORD", "A_Secure_NonDefault_Password_999!")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        import config.settings.production as prod
        importlib.reload(prod)


def test_production_fails_when_secret_key_contains_insecure(clean_env, monkeypatch):
    """Production settings must raise ImproperlyConfigured if secret key contains 'insecure'."""
    monkeypatch.setenv("DJANGO_SECRET_KEY", "django-insecure-this-is-a-placeholder-that-exceeds-40-characters-in-length")
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.edu.in")
    monkeypatch.setenv("DB_PASSWORD", "A_Secure_NonDefault_Password_999!")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")

    with pytest.raises(ImproperlyConfigured, match="DJANGO_SECRET_KEY"):
        import config.settings.production as prod
        importlib.reload(prod)


def test_production_fails_when_allowed_hosts_is_wildcard(clean_env, monkeypatch):
    """Production settings must raise ImproperlyConfigured if ALLOWED_HOSTS is wildcard."""
    valid_key = "a" * 64
    monkeypatch.setenv("DJANGO_SECRET_KEY", valid_key)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "*")
    monkeypatch.setenv("DB_PASSWORD", "A_Secure_NonDefault_Password_999!")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")

    with pytest.raises(ImproperlyConfigured, match="DJANGO_ALLOWED_HOSTS"):
        import config.settings.production as prod
        importlib.reload(prod)


def test_production_fails_when_db_password_is_weak(clean_env, monkeypatch):
    """Production settings must raise ImproperlyConfigured if database password is weak/default."""
    valid_key = "b" * 64
    monkeypatch.setenv("DJANGO_SECRET_KEY", valid_key)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.edu.in")
    monkeypatch.setenv("DB_PASSWORD", "postgres")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")

    with pytest.raises(ImproperlyConfigured, match="Production database password"):
        import config.settings.production as prod
        importlib.reload(prod)


def test_production_fails_when_db_engine_is_not_postgresql(clean_env, monkeypatch):
    """Production settings must raise ImproperlyConfigured if database engine is not PostgreSQL."""
    valid_key = "b" * 64
    monkeypatch.setenv("DJANGO_SECRET_KEY", valid_key)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.edu.in")
    monkeypatch.setenv("DB_PASSWORD", "StrongProductionPassword2026!#$")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")
    monkeypatch.setenv("JWT_COOKIE_SECURE", "True")
    monkeypatch.setenv("USE_SQLITE_FOR_LOCAL_DEV", "True")
    monkeypatch.delenv("DATABASE_URL", raising=False)

    with pytest.raises(ImproperlyConfigured, match="Production database ENGINE must be 'django.db.backends.postgresql'"):
        import config.settings.production as prod
        importlib.reload(prod)


def test_production_fails_when_jwt_cookie_secure_is_disabled(clean_env, monkeypatch):
    """Production settings must raise ImproperlyConfigured if JWT_COOKIE_SECURE is False."""
    valid_key = "b" * 64
    monkeypatch.setenv("DJANGO_SECRET_KEY", valid_key)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.edu.in")
    monkeypatch.setenv("DB_PASSWORD", "StrongProductionPassword2026!#$")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")
    monkeypatch.setenv("JWT_COOKIE_SECURE", "False")
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:StrongProductionPassword2026!#$@localhost:5432/gqt_hrms")
    monkeypatch.setenv("USE_SQLITE_FOR_LOCAL_DEV", "False")

    with pytest.raises(ImproperlyConfigured, match="JWT_COOKIE_SECURE must be enabled in production"):
        import config.settings.production as prod
        importlib.reload(prod)


def test_production_succeeds_with_valid_configuration(clean_env, monkeypatch):
    """Production settings must load without errors when valid configuration is injected."""
    valid_key = "c" * 64
    monkeypatch.setenv("DJANGO_SECRET_KEY", valid_key)
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "hrms.gqt.edu.in")
    monkeypatch.setenv("DB_PASSWORD", "StrongProductionPassword2026!#$")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "True")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "True")
    monkeypatch.setenv("JWT_COOKIE_SECURE", "True")
    monkeypatch.setenv("DATABASE_URL", "postgresql://postgres:StrongProductionPassword2026!#$@localhost:5432/gqt_hrms")
    monkeypatch.setenv("USE_SQLITE_FOR_LOCAL_DEV", "False")

    import config.settings.production as prod
    importlib.reload(prod)
    assert prod.DEBUG is False
    assert prod.ENVIRONMENT == "production"
