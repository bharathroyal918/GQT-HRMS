"""DRF Serializers for Corporate CRM & HR Directory."""
from typing import Any, Dict
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.crm.models import (
    CaseEscalation,
    CaseEscalationStatus,
    Company,
    CompanyDomainCategory,
    CompanyRelationshipStatus,
    CompanyTier,
    CRMReconciliationRun,
    FollowUp,
    FollowUpCategory,
    FollowUpPriority,
    FollowUpReminderItem,
    FollowUpStatus,
    HRContact,
    OutreachChannel,
    OutreachLog,
    OutreachOutcome,
    ReminderChannel,
    StaffNotification,
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
    student_name = serializers.CharField(source="student.user.full_name", read_only=True, default=None)
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True, default=None)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True, default=None)
    reminders_count = serializers.IntegerField(source="reminder_items.count", read_only=True)

    class Meta:
        model = FollowUp
        fields = [
            "id",
            "company",
            "hr_contact",
            "assigned_to",
            "category",
            "student",
            "student_name",
            "student_roll_number",
            "job_requirement",
            "job_title",
            "interview_schedule",
            "placement_status",
            "due_date",
            "priority",
            "status",
            "purpose",
            "notes",
            "remind_at",
            "reminder_channel",
            "reminders_count",
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
            "category",
            "student",
            "job_requirement",
            "interview_schedule",
            "placement_status",
            "due_date",
            "priority",
            "purpose",
            "notes",
            "remind_at",
            "reminder_channel",
        ]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        company = attrs.get("company")
        contact = attrs.get("hr_contact")
        if contact and contact.company_id != company.id:
            raise serializers.ValidationError({
                "hr_contact": f"Contact '{contact.name}' does not belong to company '{company.name}'."
            })

        remind_at = attrs.get("remind_at")
        due_date = attrs.get("due_date")
        if remind_at and due_date and remind_at > due_date:
            raise serializers.ValidationError({
                "remind_at": "Reminder datetime cannot be scheduled after the follow-up due date."
            })

        return attrs


class FollowUpRescheduleSerializer(serializers.Serializer):
    """Input serializer for rescheduling a follow-up."""

    new_due_date = serializers.DateTimeField(required=True)
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")
    new_remind_at = serializers.DateTimeField(required=False, allow_null=True, default=None)


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


class FollowUpReminderItemSerializer(serializers.ModelSerializer):
    """Serializer for automated reminder queue records."""

    follow_up_purpose = serializers.CharField(source="follow_up.purpose", read_only=True)
    company_name = serializers.CharField(source="follow_up.company.name", read_only=True)

    class Meta:
        model = FollowUpReminderItem
        fields = [
            "id",
            "follow_up",
            "follow_up_purpose",
            "company_name",
            "channel",
            "recipient",
            "recipient_name",
            "scheduled_for",
            "status",
            "attempt_count",
            "max_attempts",
            "backoff_until",
            "sent_at",
            "delivered_at",
            "provider_message_id",
            "error_message",
            "is_simulated",
            "created_at",
            "updated_at",
        ]


class StaffNotificationSerializer(serializers.ModelSerializer):
    """Serializer for Placement Officer in-app alerts and notifications."""

    company_name = serializers.CharField(source="follow_up.company.name", read_only=True, default=None)

    class Meta:
        model = StaffNotification
        fields = [
            "id",
            "recipient",
            "notification_type",
            "title",
            "message",
            "link",
            "follow_up",
            "company_name",
            "is_read",
            "read_at",
            "created_at",
        ]


class CaseEscalationSerializer(serializers.ModelSerializer):
    """Serializer for pending and overdue case escalations."""

    company_name = serializers.CharField(source="follow_up.company.name", read_only=True, default=None)
    follow_up_purpose = serializers.CharField(source="follow_up.purpose", read_only=True, default=None)
    follow_up_due_date = serializers.DateTimeField(source="follow_up.due_date", read_only=True, default=None)
    escalated_to_name = serializers.CharField(source="escalated_to.full_name", read_only=True, default=None)
    escalated_to_email = serializers.CharField(source="escalated_to.email", read_only=True, default=None)
    previous_assigned_to_name = serializers.CharField(source="previous_assigned_to.full_name", read_only=True, default=None)
    acknowledged_by_name = serializers.CharField(source="acknowledged_by.full_name", read_only=True, default=None)
    resolved_by_name = serializers.CharField(source="resolved_by.full_name", read_only=True, default=None)

    class Meta:
        model = CaseEscalation
        fields = [
            "id",
            "case_type",
            "follow_up",
            "company_name",
            "follow_up_purpose",
            "follow_up_due_date",
            "escalated_to",
            "escalated_to_name",
            "escalated_to_email",
            "escalated_by",
            "previous_assigned_to",
            "previous_assigned_to_name",
            "reason",
            "escalation_level",
            "status",
            "acknowledged_at",
            "acknowledged_by",
            "acknowledged_by_name",
            "resolved_at",
            "resolved_by",
            "resolved_by_name",
            "resolution_notes",
            "created_at",
            "updated_at",
        ]


class CaseEscalationAcknowledgeSerializer(serializers.Serializer):
    """Input serializer for acknowledging an escalation."""

    notes = serializers.CharField(max_length=500, required=False, allow_blank=True, default="")


class CaseEscalationResolveSerializer(serializers.Serializer):
    """Input serializer for resolving an escalation."""

    resolution_notes = serializers.CharField(max_length=2000, required=True)

    def validate_resolution_notes(self, value: str) -> str:
        trimmed = value.strip()
        if len(trimmed) < 5:
            raise serializers.ValidationError("Resolution notes must be at least 5 characters.")
        return trimmed


class AutomationRunRequestSerializer(serializers.Serializer):
    """Input serializer for triggering an automated follow-up run."""

    dry_run = serializers.BooleanField(required=False, default=False)


# ==============================================================================
# Phase 10: CRM Database Integration Serializers
# ==============================================================================

class CRMReconciliationRunSerializer(serializers.ModelSerializer):
    """Audit serializer for CRM reconciliation history runs."""

    triggered_by_name = serializers.CharField(
        source="triggered_by.full_name", read_only=True, default="System"
    )
    triggered_by_email = serializers.CharField(
        source="triggered_by.email", read_only=True, default=""
    )

    class Meta:
        model = CRMReconciliationRun
        fields = [
            "id",
            "triggered_by",
            "triggered_by_name",
            "triggered_by_email",
            "status",
            "total_records_checked",
            "conflicts_detected",
            "records_synchronized",
            "diagnostic_details",
            "summary",
            "created_at",
        ]


class CRMReconciliationSyncRequestSerializer(serializers.Serializer):
    """Input parameters for triggering a database reconciliation run."""

    dry_run = serializers.BooleanField(
        default=False,
        required=False,
        help_text="If True, performs diagnostic audit and previews changes without persisting.",
    )


class CRMConflictSerializer(serializers.Serializer):
    """Structured representation of a cross-module data conflict."""

    area = serializers.CharField()
    severity = serializers.ChoiceField(choices=["CRITICAL", "WARNING", "INFO"])
    resource_type = serializers.CharField()
    resource_id = serializers.CharField()
    description = serializers.CharField()
    recommended_action = serializers.CharField()


class CRMDatabaseHealthSummarySerializer(serializers.Serializer):
    """Aggregate health score and high-level totals."""

    total_records_checked = serializers.IntegerField()
    total_consistent_records = serializers.IntegerField()
    total_conflicts = serializers.IntegerField()
    health_score_percentage = serializers.FloatField()
    status = serializers.CharField()
    as_of = serializers.CharField()


class CRMDatabaseHealthAreaSerializer(serializers.Serializer):
    """Per-area health diagnostic status."""

    name = serializers.CharField()
    total = serializers.IntegerField()
    consistent = serializers.IntegerField()
    conflicts = serializers.IntegerField()
    status = serializers.CharField()


class CRMDatabaseHealthSerializer(serializers.Serializer):
    """Complete 8-area database health diagnostic report."""

    summary = CRMDatabaseHealthSummarySerializer()
    areas = serializers.DictField(child=CRMDatabaseHealthAreaSerializer())
    conflicts = CRMConflictSerializer(many=True)


class CommunicationTimelineItemSerializer(serializers.Serializer):
    """Unified representation of a communication event across channels."""

    id = serializers.CharField()
    category = serializers.CharField()
    channel = serializers.CharField()
    channel_display = serializers.CharField(required=False, allow_null=True)
    direction = serializers.CharField()
    subject = serializers.CharField()
    summary = serializers.CharField()
    actor_name = serializers.CharField(allow_null=True)
    contact_name = serializers.CharField(required=False, allow_null=True)
    status = serializers.CharField()
    timestamp = serializers.CharField()

