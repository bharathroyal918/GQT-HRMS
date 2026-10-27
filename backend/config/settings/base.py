"""Base Django settings for GQT HRMS & Recruitment CRM Platform.

Architectural Standards:
- Enterprise Modular 5-Layer Pattern
- Supabase-hosted PostgreSQL 16 Support with SSL
- Strict Secret Redaction & Audit Logging
- OpenAPI 3.1 Documentation via drf-spectacular
"""
from pathlib import Path
import os
from datetime import timedelta
import environ

# Build paths inside the project: BASE_DIR is the backend/ directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
REPO_ROOT = BASE_DIR.parent

env = environ.Env(
    ENVIRONMENT=(str, "development"),
    DEBUG=(bool, False),
    TIMEZONE=(str, "Asia/Kolkata"),
    LOG_LEVEL=(str, "INFO"),
    USE_SQLITE_FOR_LOCAL_DEV=(bool, True),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    CSRF_TRUSTED_ORIGINS=(list, ["http://localhost:5173", "http://127.0.0.1:5173"]),
    SESSION_COOKIE_SECURE=(bool, False),
    CSRF_COOKIE_SECURE=(bool, False),
    JWT_COOKIE_SECURE=(bool, False),
    JWT_ACCESS_TOKEN_LIFETIME_MINUTES=(int, 15),
    JWT_REFRESH_TOKEN_LIFETIME_DAYS=(int, 7),
)

# Load .env file from either backend/ or repo root (if not disabled by SKIP_DOTENV)
skip_dotenv = os.environ.get("SKIP_DOTENV", "").lower() in ("true", "1", "yes")
if not skip_dotenv:
    if (BASE_DIR / ".env").exists():
        environ.Env.read_env(str(BASE_DIR / ".env"))
    elif (REPO_ROOT / ".env").exists():
        environ.Env.read_env(str(REPO_ROOT / ".env"))

ENVIRONMENT = env("ENVIRONMENT")
DEBUG = env("DEBUG")

DEV_FALLBACK_SECRET_KEY = (
    "django-insecure-dev-only-secret-key-must-be-rotated-for-production-min-50-chars"
)

# Secret key evaluation: In production, never use fallback
if ENVIRONMENT == "production":
    SECRET_KEY = env("DJANGO_SECRET_KEY", default="")
else:
    SECRET_KEY = env("DJANGO_SECRET_KEY", default=DEV_FALLBACK_SECRET_KEY)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# Application definition
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.core.apps.CoreConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.crm.apps.CrmConfig",
    "apps.jobs.apps.JobsConfig",
    "apps.creatives.apps.CreativesConfig",
    "apps.students.apps.StudentsConfig",
    "apps.preparation.apps.PreparationConfig",
    "apps.submissions.apps.SubmissionsConfig",
    "apps.interviews.apps.InterviewsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Custom User Model
AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "apps.core.middleware.CorrelationIdMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# Database Configuration (Supabase PostgreSQL 16 via psycopg v3)
# Allows DATABASE_URL or individual connection parameters, with graceful local dev fallback
database_url = env.str("DATABASE_URL", default="")
use_sqlite = env.bool("USE_SQLITE_FOR_LOCAL_DEV", default=True)

if database_url and not (use_sqlite and "sqlite" in database_url.lower()):
    parsed_db = env.db_url("DATABASE_URL")
    # Ensure SSL is enforced for remote Supabase connections
    if "supabase.com" in parsed_db.get("HOST", "") or parsed_db.get("ENGINE") == "django.db.backends.postgresql":
        parsed_db.setdefault("OPTIONS", {})
        parsed_db["OPTIONS"]["sslmode"] = env.str("DB_SSLMODE", default="require")
        parsed_db["OPTIONS"]["connect_timeout"] = 10
    DATABASES = {"default": parsed_db}
elif env.str("DB_NAME", default="") and not use_sqlite:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("DB_NAME"),
            "USER": env("DB_USER", default="postgres"),
            "PASSWORD": env("DB_PASSWORD", default=""),
            "HOST": env("DB_HOST", default="localhost"),
            "PORT": env("DB_PORT", default="5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "sslmode": env("DB_SSLMODE", default="require"),
                "connect_timeout": 10,
            },
        }
    }
else:
    # Safe, isolated local development fallback when Supabase credentials are not yet injected
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev_local.sqlite3",
        }
    }

# Password Hashers (Argon2id primary, PBKDF2 fallback)
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
]

# Password Validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization & Timezone
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIMEZONE", default="Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# Static & Media Storage
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
PRIVATE_MEDIA_ROOT = BASE_DIR / "media" / "private"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework Configuration
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.accounts.authentication.HttpOnlyCookieJWTAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.core.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/minute",
        "user": "1000/minute",
        "health": "300/minute",
        "auth": "10/minute",
    },
}

# SimpleJWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": "gqt-hrms-auth",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# JWT Cookie Configuration for Web Frontend
JWT_AUTH_COOKIE = "gqt_access_token"
JWT_REFRESH_COOKIE = "gqt_refresh_token"
JWT_COOKIE_SECURE = env.bool("JWT_COOKIE_SECURE", default=False)
JWT_COOKIE_SAMESITE = "Lax"
JWT_COOKIE_PATH = "/"
JWT_REFRESH_COOKIE_PATH = "/api/v1/auth/"

# drf-spectacular OpenAPI 3.1 Settings
SPECTACULAR_SETTINGS = {
    "TITLE": "GQT HRMS & Recruitment CRM API",
    "DESCRIPTION": (
        "Production-grade, enterprise recruitment CRM and HRMS platform "
        "automating the 13 workflow phases and 41 operational steps for GQT."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": r"/api/v1/",
}

# CORS & CSRF Settings
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS")
CSRF_COOKIE_HTTPONLY = False  # Allows Axios client to read CSRF token for header injection
CSRF_COOKIE_NAME = "gqt_csrftoken"
CSRF_HEADER_NAME = "HTTP_X_CSRFTOKEN"

# Logging with Sensitive Data Redaction & Correlation Tracking
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "sensitive_data_filter": {
            "()": "apps.core.logging.SensitiveDataFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": (
                "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] "
                "[req:%(correlation_id)s] %(message)s"
            ),
        },
        "simple": {
            "format": "%(levelname)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["sensitive_data_filter"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}
