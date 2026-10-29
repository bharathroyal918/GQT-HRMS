"""Management command to provision the required GQT HRMS administrative and operational user accounts."""
from decimal import Decimal
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import RoleCatalog, User
from apps.accounts.services import assign_roles_to_user
from apps.students.models import StudentProfile


class Command(BaseCommand):
    help = "Idempotently provision the administrator (hrms@gqtech.in) and operational user (bharath@gmail.com)."

    @transaction.atomic
    def handle(self, *args, **options):
        # 1. Ensure all standard operational roles exist
        call_command("seed_roles")

        # 2. Provision / Update Administrator: hrms@gqtech.in
        admin_email = "hrms@gqtech.in"
        admin_password = "Adminhrms@123!"

        admin_user, admin_created = User.objects.get_or_create(
            email=admin_email,
            defaults={
                "first_name": "HRMS",
                "last_name": "Administrator",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )
        admin_user.set_password(admin_password)
        admin_user.first_name = "HRMS"
        admin_user.last_name = "Administrator"
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.is_active = True
        admin_user.save()

        assign_roles_to_user(admin_user, [RoleCatalog.ADMIN])
        self.stdout.write(
            self.style.SUCCESS(
                f"[{'CREATED' if admin_created else 'UPDATED'}] Administrator: {admin_email} (Roles: {RoleCatalog.ADMIN})"
            )
        )

        # 3. Provision / Update Remaining / Operational User: bharath@gmail.com
        user_email = "bharath@gmail.com"
        user_password = "Bharath@123"
        operational_roles = [
            RoleCatalog.PLACEMENT_HEAD,
            RoleCatalog.PLACEMENT_OFFICER,
            RoleCatalog.HR_RELATIONSHIP_MGR,
            RoleCatalog.CREATIVE_DESIGNER,
            RoleCatalog.TRAINER,
            RoleCatalog.EVALUATOR,
            RoleCatalog.STUDENT,
            RoleCatalog.AUDITOR,
        ]

        user, user_created = User.objects.get_or_create(
            email=user_email,
            defaults={
                "first_name": "Bharath",
                "last_name": "Kumar",
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
            },
        )
        user.set_password(user_password)
        user.first_name = "Bharath"
        user.last_name = "Kumar"
        user.is_staff = False
        user.is_superuser = False
        user.is_active = True
        user.save()

        assign_roles_to_user(user, operational_roles, assigned_by=admin_user)
        self.stdout.write(
            self.style.SUCCESS(
                f"[{'CREATED' if user_created else 'UPDATED'}] Operational User: {user_email} (Roles: {', '.join(operational_roles)})"
            )
        )

        # 4. Attach verified StudentProfile to bharath@gmail.com for student drives & placement self-service
        student_profile, prof_created = StudentProfile.objects.get_or_create(
            user=user,
            defaults={
                "roll_number": "1GQT22CS099",
                "institutional_email": "bharath.student@gqt.edu",
                "college_name": "GQT Institute of Technology",
                "degree": "B.Tech",
                "department": "Computer Science",
                "graduation_year": 2025,
                "cgpa": Decimal("8.50"),
                "active_backlogs": 0,
                "history_backlogs": 0,
                "phone_number": "+91 98765 43210",
                "is_verified_by_placement": True,
            },
        )
        if not prof_created:
            student_profile.is_verified_by_placement = True
            student_profile.save(update_fields=["is_verified_by_placement"])

        self.stdout.write(
            self.style.SUCCESS(
                f"[{'ATTACHED' if prof_created else 'VERIFIED'}] StudentProfile for: {user_email} (Roll: {student_profile.roll_number}, CGPA: {student_profile.cgpa})"
            )
        )
        self.stdout.write(self.style.SUCCESS("All user accounts successfully provisioned and ready for authentication."))

