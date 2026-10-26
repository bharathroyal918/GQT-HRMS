"""Job Requirements & Verification Domain Application (Phase 3)."""
from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.jobs"
    verbose_name = "Job Requirements & Verification Checklist"
