"""DRF Serializers for Corporate CRM & HR Directory."""
from typing import Any, Dict
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.crm.models import (
    Company,
    CompanyDomainCategory,
    CompanyRelationshipStatus,
    CompanyTier,
    FollowUp,
    FollowUpPriority,
    FollowUpStatus,
    HRContact,
    OutreachChannel,
    OutreachLog,
    OutreachOutcome,
)

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """Compact user representation for ownership and audit assignments."""

    full_name = serializers.CharField(source="get_full_name", read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "full_name"]


class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for company directory tables and filters."""

    owner = UserMinimalSerializer(read_only=True)
    hr_contacts_count = serializers.IntegerField(source="hr_contacts.count", read_only=True)

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "normalized_name",
            "website",
            "domain",
            "domain_category",
            "tier",
            "relationship_status",
            "source",
            "city",
            "state",
            "country",
            "owner",
            "hr_contacts_count",
            "is_archived",
            "created_at",
            "updated_at",
        ]


class HRContactSummarySerializer(serializers.ModelSerializer):
    """Brief contact summary nested in company details."""

    class Meta:
        model = HRContact
        fields = ["id", "name", "designation", "email", "phone", "status", "is_archived"]


class CompanyDetailSerializer(serializers.ModelSerializer):
    """Comprehensive company profile including contacts, recent outreach, and follow-ups."""

    owner = UserMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    updated_by = UserMinimalSerializer(read_only=True)
    hr_contacts = serializers.SerializerMethodField()
    recent_outreach_count = serializers.IntegerField(source="outreach_logs.count", read_only=True)
    open_follow_ups_count = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = [
            "id",
            "name",
            "normalized_name",
            "website",
            "domain",
            "domain_category",
            "tier",
            "relationship_status",
            "source",
            "city",
            "state",
            "country",
            "address",
            "notes",
            "owner",
            "created_by",
            "updated_by",
            "hr_contacts",
            "recent_outreach_count",
            "open_follow_ups_count",
            "is_archived",
            "created_at",
            "updated_at",
        ]

    def get_hr_contacts(self, obj: Company):
        contacts = obj.hr_contacts.filter(is_deleted=False).order_by("name")
        return HRContactSummarySerializer(contacts, many=True).data

    def get_open_follow_ups_count(self, obj: Company) -> int:
        return obj.follow_ups.filter(
            status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS]
        ).count()


class CompanyCreateUpdateSerializer(serializers.ModelSerializer):
    """Input serializer for creating and updating company records."""

    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True), required=False, allow_null=True
    )

    class Meta:
        model = Company
        fields = [
            "name",
            "website",
            "domain_category",
            "tier",
            "relationship_status",
            "source",
            "city",
            "state",
            "country",
            "address",
            "owner",
            "notes",
        ]

    def validate_name(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("Company legal/trading name is required.")
        return trimmed


class CompanyDuplicateCheckSerializer(serializers.Serializer):
    """Validation for pre-submission duplicate warning query."""

    name = serializers.CharField(max_length=255, required=True)
    website = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class CompanyMinimalSerializer(serializers.ModelSerializer):
    """Minimal company reference for contacts, outreach, and follow-ups."""

    class Meta:
        model = Company
        fields = ["id", "name", "domain_category", "relationship_status"]


class HRContactListSerializer(serializers.ModelSerializer):
    """Serializer for HR contact directory table."""

    company = CompanyMinimalSerializer(read_only=True)
    owner = UserMinimalSerializer(read_only=True)

    class Meta:
        model = HRContact
        fields = [
            "id",
            "company",
            "name",
            "designation",
            "department",
            "email",
            "phone",
            "alt_phone",
            "linkedin_url",
            "preferred_channel",
            "status",
            "owner",
            "is_archived",
            "created_at",
            "updated_at",
        ]


class HRContactDetailSerializer(serializers.ModelSerializer):
    """Full HR contact profile including notes and audit information."""

    company = CompanyMinimalSerializer(read_only=True)
    owner = UserMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    updated_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = HRContact
        fields = [
            "id",
            "company",
            "name",
            "designation",
            "department",
            "email",
            "phone",
            "alt_phone",
            "linkedin_url",
            "preferred_channel",
            "status",
            "owner",
            "notes",
            "created_by",
            "updated_by",
            "is_archived",
            "created_at",
            "updated_at",
        ]


class HRContactCreateUpdateSerializer(serializers.ModelSerializer):
    """Input serializer for HR contact creation and editing."""

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_deleted=False)
    )
    owner = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True), required=False, allow_null=True
    )

    class Meta:
        model = HRContact
        fields = [
            "company",
            "name",
            "designation",
            "department",
            "email",
            "phone",
            "alt_phone",
            "linkedin_url",
            "preferred_channel",
            "status",
            "owner",
            "notes",
        ]

    def validate_name(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("Contact full name is required.")
        return trimmed


class OutreachLogSerializer(serializers.ModelSerializer):
    """Output representation for completed outreach touchpoints."""

    company = CompanyMinimalSerializer(read_only=True)
    hr_contact = HRContactSummarySerializer(read_only=True)
    performed_by = UserMinimalSerializer(read_only=True)

    class Meta:
        model = OutreachLog
        fields = [
            "id",
            "company",
            "hr_contact",
            "performed_by",
            "channel",
            "direction",
            "activity_date",
            "outcome",
            "subject",
            "notes",
            "followup_required",
            "correlation_id",
            "created_at",
        ]


class OutreachLogCreateSerializer(serializers.ModelSerializer):
    """Input serializer for recording an outreach touchpoint."""

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_deleted=False)
    )
    hr_contact = serializers.PrimaryKeyRelatedField(
        queryset=HRContact.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = OutreachLog
        fields = [
            "company",
            "hr_contact",
            "channel",
            "direction",
            "activity_date",
            "outcome",
            "subject",
            "notes",
            "followup_required",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        company = attrs.get("company")
        contact = attrs.get("hr_contact")
        if contact and contact.company_id != company.id:
            raise serializers.ValidationError({
                "hr_contact": f"Contact '{contact.name}' does not belong to company '{company.name}'."
            })
        return attrs


class FollowUpSerializer(serializers.ModelSerializer):
    """Output representation for scheduled corporate follow-ups."""

    company = CompanyMinimalSerializer(read_only=True)
    hr_contact = HRContactSummarySerializer(read_only=True)
    assigned_to = UserMinimalSerializer(read_only=True)
    completed_by = UserMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)

    class Meta:
        model = FollowUp
        fields = [
            "id",
            "company",
            "hr_contact",
            "assigned_to",
            "due_date",
            "priority",
            "status",
            "purpose",
            "is_overdue",
            "rescheduled_count",
            "completion_notes",
            "completed_at",
            "completed_by",
            "cancellation_reason",
            "created_by",
            "created_at",
            "updated_at",
        ]


class FollowUpCreateSerializer(serializers.ModelSerializer):
    """Input serializer for scheduling a follow-up."""

    company = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.filter(is_deleted=False)
    )
    hr_contact = serializers.PrimaryKeyRelatedField(
        queryset=HRContact.objects.filter(is_deleted=False),
        required=False,
        allow_null=True,
    )
    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )

    class Meta:
        model = FollowUp
        fields = [
            "company",
            "hr_contact",
            "assigned_to",
            "due_date",
            "priority",
            "purpose",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        company = attrs.get("company")
        contact = attrs.get("hr_contact")
        if contact and contact.company_id != company.id:
            raise serializers.ValidationError({
                "hr_contact": f"Contact '{contact.name}' does not belong to company '{company.name}'."
            })
        return attrs


class FollowUpRescheduleSerializer(serializers.Serializer):
    """Input serializer for rescheduling a follow-up."""

    new_due_date = serializers.DateTimeField(required=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class FollowUpCompleteSerializer(serializers.Serializer):
    """Input serializer for completing a follow-up."""

    completion_notes = serializers.CharField(
        max_length=2000, required=False, allow_blank=True, default=""
    )


class FollowUpCancelSerializer(serializers.Serializer):
    """Input serializer for cancelling a follow-up."""

    cancellation_reason = serializers.CharField(max_length=1000, required=True)

    def validate_cancellation_reason(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError("An explicit cancellation reason is required.")
        return trimmed


class FollowUpReopenSerializer(serializers.Serializer):
    """Input serializer for reopening a completed or cancelled follow-up."""

    new_due_date = serializers.DateTimeField(required=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
