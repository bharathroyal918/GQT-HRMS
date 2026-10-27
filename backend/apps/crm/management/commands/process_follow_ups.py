"""Django management command to execute automated follow-up processing (Phase 12).

Usage:
    python manage.py process_follow_ups --once
    python manage.py process_follow_ups --dry-run
    python manage.py process_follow_ups --interval=30
"""
import time
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.crm.scheduler import run_automated_followup_cycle


class Command(BaseCommand):
    help = "Execute Phase 12 Automated Follow-Up and Escalation cycle (Idempotent worker)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--once",
            action="store_true",
            help="Run a single automation cycle and exit immediately.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Inspect eligible follow-ups and reminders without making state mutations.",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=60,
            help="Poll interval in seconds when running as a continuous background daemon (default: 60s).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Maximum reminder items to process per batch (default: 50).",
        )

    def handle(self, *args, **options):
        once = options["once"]
        dry_run = options["dry_run"]
        interval = max(options["interval"], 5)

        self.stdout.write(
            self.style.NOTICE(
                f"Starting GQT HRMS Automated Follow-Up Worker "
                f"[once={once}, dry_run={dry_run}, interval={interval}s]..."
            )
        )

        if once or dry_run:
            results = run_automated_followup_cycle(dry_run=dry_run)
            self.stdout.write(self.style.SUCCESS(f"Cycle completed successfully: {results}"))
            return

        # Continuous execution mode
        self.stdout.write(self.style.SUCCESS(f"Worker running. Press Ctrl+C to terminate."))
        try:
            while True:
                results = run_automated_followup_cycle(dry_run=False)
                self.stdout.write(f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] Cycle summary: {results}")
                time.sleep(interval)
        except KeyboardInterrupt:
            self.stdout.write(self.style.NOTICE("Automated follow-up worker received shutdown signal. Exiting."))
