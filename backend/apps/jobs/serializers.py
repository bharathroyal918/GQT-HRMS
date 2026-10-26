"""DRF Serializers for Job Requirements & Verification (Phase 3)."""
from rest_framework import serializers
from apps.crm.models import Company, HRContact
from apps.jobs.models import (
    ChecklistItemStatus,
    EmploymentType,
    JobApprovalDecision,
    JobChecklistItem,
    JobRequirement,
    JobRequirementStatus,
    WorkArrangement,
)


class JobChecklistItemSerializer(serializers.ModelSerializer):
    """Represents an individual verification checklist item."""

    verified_by_name = serializers.SerializerMethodField()

    class Meta:
        model = JobChecklistItem
        fields = [
            "id",
            "item_code",
            "title",
            "description",
            "is_mandatory",
            "status",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "remarks",
        ]
        read_only_fields = [
            "id",
            "item_code",
            "title",
            "description",
            "is_mandatory",
            "verified_by",
            "verified_by_name",
            "verified_at",
        ]

    def get_verified_by_name(self, obj: JobChecklistItem) -> str:
        return obj.verified_by.full_name if obj.verified_by else ""


class JobApprovalDecisionSerializer(serializers.ModelSerializer):
    """Represents historical audit log decisions (Submitted, Returned, Approved, Rejected)."""

    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = JobApprovalDecision
        fields = [
            "id",
            "decision",
            "actor",
            "actor_name",
            "actor_role",
            "comments",
            "created_at",
        ]
        read_only_fields = fields

    def get_actor_name(self, obj: JobApprovalDecision) -> str:
        return obj.actor.full_name if obj.actor else "System"


class JobRequirementListSerializer(serializers.ModelSerializer):
    """Compact summary serializer for directory and queue tables."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_tier = serializers.CharField(source="company.tier", read_only=True)
    hr_contact_name = serializers.CharField(
        source="hr_contact.name", read_only=True, default=""
    )
    checklist_progress = serializers.SerializerMethodField()

    class Meta:
        model = JobRequirement
        fields = [
            "id",
            "title",
            "company",
            "company_name",
            "company_tier",
            "hr_contact",
            "hr_contact_name",
            "location",
            "work_arrangement",
            "employment_type",
            "min_salary",
            "max_salary",
            "salary_currency",
            "status",
            "registration_deadline",
            "openings_count",
            "checklist_progress",
            "is_archived",
            "created_at",
        ]
        read_only_fields = fields

    def get_checklist_progress(self, obj: JobRequirement) -> dict:
        return obj.checklist_progress


class JobRequirementDetailSerializer(serializers.ModelSerializer):
    """Comprehensive representation with nested checklist items and decision logs."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    company_website = serializers.CharField(source="company.website", read_only=True)
    company_domain = serializers.CharField(source="company.domain", read_only=True)
    company_tier = serializers.CharField(source="company.tier", read_only=True)
    company_category = serializers.CharField(
        source="company.domain_category", read_only=True
    )
    hr_contact_name = serializers.CharField(
        source="hr_contact.name", read_only=True, default=""
    )
    hr_contact_email = serializers.CharField(
        source="hr_contact.email", read_only=True, default=""
    )
    hr_contact_phone = serializers.CharField(
        source="hr_contact.phone", read_only=True, default=""
    )
    created_by_name = serializers.CharField(
        source="created_by.full_name", read_only=True, default=""
    )
    assigned_verifier_name = serializers.CharField(
        source="assigned_verifier.full_name", read_only=True, default=""
    )
    verified_by_name = serializers.CharField(
        source="verified_by.full_name", read_only=True, default=""
    )
    approved_by_name = serializers.CharField(
        source="approved_by.full_name", read_only=True, default=""
    )
    checklist_items = JobChecklistItemSerializer(many=True, read_only=True)
    decisions = JobApprovalDecisionSerializer(many=True, read_only=True)
    checklist_progress = serializers.SerializerMethodField()
    is_locked = serializers.BooleanField(read_only=True)
    is_editable = serializers.BooleanField(read_only=True)

    class Meta:
        model = JobRequirement
        fields = [
            "id",
            "company",
            "company_name",
            "company_website",
            "company_domain",
            "company_tier",
            "company_category",
            "hr_contact",
            "hr_contact_name",
            "hr_contact_email",
            "hr_contact_phone",
            "title",
            "job_description",
            "skills_required",
            "min_salary",
            "max_salary",
            "salary_currency",
            "salary_breakup",
            "location",
            "work_arrangement",
            "employment_type",
            "has_bond",
            "bond_details",
            "eligibility_criteria",
            "min_cgpa",
            "hiring_process",
            "interview_date",
            "registration_deadline",
            "openings_count",
            "status",
            "created_by",
            "created_by_name",
            "assigned_verifier",
            "assigned_verifier_name",
            "verified_by",
            "verified_by_name",
            "verified_at",
            "approved_by",
            "approved_by_name",
            "approved_at",
            "rejection_reason",
            "return_reason",
            "notes",
            "is_archived",
            "checklist_items",
            "decisions",
            "checklist_progress",
            "is_locked",
            "is_editable",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_checklist_progress(self, obj: JobRequirement) -> dict:
        return obj.checklist_progress


class JobRequirementCreateUpdateSerializer(serializers.ModelSerializer):
    """Validates input for creating or updating a Job Requirement."""

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_archived=False)
    )
    hr_contact = serializers.PrimaryKeyRelatedField(
        queryset=HRContact.objects.filter(is_archived=False),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = JobRequirement
        fields = [
            "company",
            "hr_contact",
            "title",
            "job_description",
            "skills_required",
            "min_salary",
            "max_salary",
            "salary_currency",
            "salary_breakup",
            "location",
            "work_arrangement",
            "employment_type",
            "has_bond",
            "bond_details",
            "eligibility_criteria",
            "min_cgpa",
            "hiring_process",
            "interview_date",
            "registration_deadline",
            "openings_count",
            "notes",
        ]

    def validate(self, attrs):
        company = attrs.get("company", getattr(self.instance, "company", None))
        hr_contact = attrs.get("hr_contact", getattr(self.instance, "hr_contact", None))

        if hr_contact and company and hr_contact.company_id != company.id:
            raise serializers.ValidationError(
                {"hr_contact": f"HR Contact '{hr_contact.name}' does not belong to the selected company '{company.name}'."}
            )

        min_salary = attrs.get("min_salary", getattr(self.instance, "min_salary", None))
        max_salary = attrs.get("max_salary", getattr(self.instance, "max_salary", None))
        if min_salary is not None and max_salary is not None and min_salary > max_salary:
            raise serializers.ValidationError(
                {"min_salary": "Minimum salary cannot exceed maximum salary."}
            )

        return attrs


class ChecklistItemVerifySerializer(serializers.Serializer):
    """Validates verification decision on an individual checklist item."""

    status = serializers.ChoiceField(
        choices=[
            ChecklistItemStatus.VERIFIED,
            ChecklistItemStatus.REJECTED,
            ChecklistItemStatus.NOT_APPLICABLE,
            ChecklistItemStatus.PENDING,
        ]
    )
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class JobActionReasonSerializer(serializers.Serializer):
    """Validates comments or reason strings for return, approval, and rejection."""

    reason = serializers.CharField(min_length=3, max_length=2000)


class JobApprovalSerializer(serializers.Serializer):
    """Optional sign-off comments for approving an opportunity."""

    comments = serializers.CharField(required=False, allow_blank=True, default="")
