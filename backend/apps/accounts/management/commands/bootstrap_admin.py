"""Management command to securely provision or update the initial Platform Administrator."""
import getpass
import os
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from apps.accounts.models import Role, RoleCatalog, User
from apps.accounts.services import assign_roles_to_user, log_security_event


class Command(BaseCommand):
    help = "Safely bootstrap the initial GQT HRMS Administrator with zero default credentials."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            type=str,
            help="Administrator email address (or set via GQT_BOOTSTRAP_ADMIN_EMAIL).",
        )
        parser.add_argument(
            "--password",
            type=str,
            help="Administrator password (or set via GQT_BOOTSTRAP_ADMIN_PASSWORD).",
        )
        parser.add_argument(
            "--first-name",
            type=str,
            default="System",
            help="Administrator first name.",
        )
        parser.add_argument(
            "--last-name",
            type=str,
            default="Administrator",
            help="Administrator last name.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Do not prompt for missing arguments.",
        )

    def handle(self, *args, **options):
        # 1. First ensure all operational roles exist
        call_command("seed_roles")

        email = options.get("email") or os.environ.get("GQT_BOOTSTRAP_ADMIN_EMAIL")
        password = options.get("password") or os.environ.get("GQT_BOOTSTRAP_ADMIN_PASSWORD")
        first_name = options.get("first_name", "System")
        last_name = options.get("last_name", "Administrator")
        no_input = options.get("no_input", False)

        # Interactive prompts if arguments are absent
        if not email:
            if no_input:
                raise CommandError("Email must be provided via --email or GQT_BOOTSTRAP_ADMIN_EMAIL.")
            email = input("Enter Administrator Email: ").strip()

        if not email or "@" not in email:
            raise CommandError("A valid email address is required.")

        normalized_email = email.lower().strip()

        if not password:
            if no_input:
                raise CommandError("Password must be provided via --password or GQT_BOOTSTRAP_ADMIN_PASSWORD.")
            p1 = getpass.getpass("Enter Administrator Password: ")
            p2 = getpass.getpass("Confirm Administrator Password: ")
            if p1 != p2:
                raise CommandError("Passwords do not match.")
            password = p1

        if not password:
            raise CommandError("Password cannot be blank.")

        # Validate password strength against Django configured validators
        try:
            password_validation.validate_password(password)
        except ValidationError as exc:
            raise CommandError(f"Password does not satisfy security requirements: {'; '.join(exc.messages)}")

        # Create or update administrator account
        user, created = User.objects.get_or_create(
            email=normalized_email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        user.set_password(password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Assign ADMIN role
        assign_roles_to_user(
            target_user=user,
            role_codes=[RoleCatalog.ADMIN],
            assigned_by=user,
        )

        log_security_event(
            action="ADMIN_BOOTSTRAPPED",
            resource_id=str(user.id),
            user=user,
            changes={"email": normalized_email, "created": created},
        )

        action_desc = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully {action_desc} administrator account [{normalized_email}] with ADMIN role."
            )
        )
