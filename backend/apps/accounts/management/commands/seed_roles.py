"""Management command to idempotently seed the 9 operational roles from the authoritative workflow."""
from django.core.management.base import BaseCommand
from apps.accounts.models import Role, RoleCatalog

ROLE_DEFINITIONS = [
    {
        "code": RoleCatalog.ADMIN,
        "name": "System Administrator",
        "description": "Full administrative governance, security configuration, role assignments, and audit log inspection.",
    },
    {
        "code": RoleCatalog.PLACEMENT_HEAD,
        "name": "Placement Head / Director",
        "description": "Institutional sign-offs for JDs, creative banners, student eligibility overrides, and placement resume approvals.",
    },
    {
        "code": RoleCatalog.PLACEMENT_OFFICER,
        "name": "Placement Officer / Executive",
        "description": "Corporate outreach, 12-point JD verification, student publication, roster compilation, and interview tracking.",
    },
    {
        "code": RoleCatalog.HR_RELATIONSHIP_MGR,
        "name": "Corporate CRM & HR Relationship Manager",
        "description": "Corporate database management, HR talent directory, high-volume contact outreach, and follow-up nurturing.",
    },
    {
        "code": RoleCatalog.CREATIVE_DESIGNER,
        "name": "Recruitment Creative Designer",
        "description": "Production of recruitment marketing flyers, social media banners, QR registration posters, and versioned drafts.",
    },
    {
        "code": RoleCatalog.TRAINER,
        "name": "Placement & Technical Trainer",
        "description": "Student resume review, aptitude assessment, technical test administration, communication coaching, and feedback.",
    },
    {
        "code": RoleCatalog.EVALUATOR,
        "name": "Mock Interview Evaluator",
        "description": "1-on-1 mock interviews, technical & communication rubric evaluation, and candidate readiness scoring.",
    },
    {
        "code": RoleCatalog.STUDENT,
        "name": "Enrolled Student / Candidate",
        "description": "Student profile, academic details, resume upload, drive registration, attendance confirmation, and drive feedback.",
    },
    {
        "code": RoleCatalog.AUDITOR,
        "name": "Compliance & Audit Officer",
        "description": "Read-only inspection of immutable security audit logs, credential histories, and placement verification records.",
    },
]


class Command(BaseCommand):
    help = "Idempotently seed the official 9 operational roles into the database."

    def handle(self, *args, **options):
        created_count = 0
        updated_count = 0

        for rdef in ROLE_DEFINITIONS:
            role, created = Role.objects.get_or_create(
                code=rdef["code"],
                defaults={
                    "name": rdef["name"],
                    "description": rdef["description"],
                    "is_active": True,
                },
            )
            if created:
                created_count += 1
            else:
                role.name = rdef["name"]
                role.description = rdef["description"]
                role.is_active = True
                role.save(update_fields=["name", "description", "is_active"])
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded operational roles: {created_count} created, {updated_count} verified/updated."
            )
        )
