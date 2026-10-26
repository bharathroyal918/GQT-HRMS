"""Serializers for Creative Studio & Promotional Assets Management (Phase 4)."""
from rest_framework import serializers
from apps.accounts.models import User
from apps.creatives.models import (
    CreativeRequest,
    CreativeAssetVersion,
    CreativeChecklistItem,
    CreativeDecision,
    CreativeDeliverableType,
    CreativePriority,
    ChecklistItemStatus,
)


class UserMinimalSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "full_name"]

    def get_full_name(self, obj: User) -> str:
        return obj.full_name or obj.email


class CreativeChecklistItemSerializer(serializers.ModelSerializer):
    verified_by = UserMinimalSerializer(read_only=True)
    item_code_display = serializers.CharField(source="get_item_code_display", read_only=True)

    class Meta:
        model = CreativeChecklistItem
        fields = [
            "id",
            "item_code",
            "item_code_display",
            "title",
            "description",
            "is_mandatory",
            "status",
            "verified_by",
            "verified_at",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CreativeDecisionSerializer(serializers.ModelSerializer):
    actor = UserMinimalSerializer(read_only=True)

    class Meta:
        model = CreativeDecision
        fields = [
            "id",
            "decision",
            "actor",
            "actor_role",
            "comments",
            "snapshot_version_number",
            "snapshot_request_status",
            "created_at",
        ]
        read_only_fields = fields


class CreativeAssetVersionSerializer(serializers.ModelSerializer):
    uploaded_by = UserMinimalSerializer(read_only=True)
    approved_by = UserMinimalSerializer(read_only=True)
    checklist_items = CreativeChecklistItemSerializer(many=True, read_only=True)
    checklist_progress = serializers.SerializerMethodField()
    deliverable_type_display = serializers.CharField(source="get_deliverable_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = CreativeAssetVersion
        fields = [
            "id",
            "version_number",
            "deliverable_type",
            "deliverable_type_display",
            "file_name",
            "file_size_bytes",
            "mime_type",
            "sha256_hash",
            "width_px",
            "height_px",
            "designer_notes",
            "status",
            "status_display",
            "uploaded_by",
            "is_approved",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "checklist_items",
            "checklist_progress",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_checklist_progress(self, obj: CreativeAssetVersion) -> dict:
        return obj.checklist_progress


class CreativeRequestListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="job_requirement.company.name", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    assigned_designer = UserMinimalSerializer(read_only=True)
    deliverable_type_display = serializers.CharField(source="get_deliverable_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    active_version_number = serializers.SerializerMethodField()
    active_version_status = serializers.SerializerMethodField()
    active_version_checklist_progress = serializers.SerializerMethodField()

    class Meta:
        model = CreativeRequest
        fields = [
            "id",
            "title",
            "deliverable_type",
            "deliverable_type_display",
            "status",
            "status_display",
            "priority",
            "job_requirement_id",
            "job_title",
            "company_name",
            "assigned_designer",
            "production_deadline",
            "versions_count",
            "active_version_number",
            "active_version_status",
            "active_version_checklist_progress",
            "is_archived",
            "created_at",
        ]
        read_only_fields = fields

    def get_active_version_number(self, obj: CreativeRequest) -> int | None:
        v = obj.active_version
        return v.version_number if v else None

    def get_active_version_status(self, obj: CreativeRequest) -> str | None:
        v = obj.active_version
        return v.status if v else None

    def get_active_version_checklist_progress(self, obj: CreativeRequest) -> dict | None:
        v = obj.active_version
        return v.checklist_progress if v else None


class CreativeRequestDetailSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="job_requirement.company.name", read_only=True)
    company_id = serializers.UUIDField(source="job_requirement.company.id", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    job_location = serializers.CharField(source="job_requirement.location", read_only=True)
    job_min_salary = serializers.DecimalField(source="job_requirement.min_salary", max_digits=10, decimal_places=2, read_only=True)
    job_max_salary = serializers.DecimalField(source="job_requirement.max_salary", max_digits=10, decimal_places=2, read_only=True)
    job_eligibility = serializers.CharField(source="job_requirement.eligibility_criteria", read_only=True)
    job_deadline = serializers.DateTimeField(source="job_requirement.registration_deadline", read_only=True)
    job_interview_date = serializers.DateField(source="job_requirement.interview_date", read_only=True)
    assigned_designer = UserMinimalSerializer(read_only=True)
    created_by = UserMinimalSerializer(read_only=True)
    deliverable_type_display = serializers.CharField(source="get_deliverable_type_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    versions = CreativeAssetVersionSerializer(many=True, read_only=True)
    decisions = CreativeDecisionSerializer(many=True, read_only=True)
    is_editable = serializers.BooleanField(read_only=True)
    is_locked = serializers.BooleanField(read_only=True)

    class Meta:
        model = CreativeRequest
        fields = [
            "id",
            "title",
            "deliverable_type",
            "deliverable_type_display",
            "status",
            "status_display",
            "priority",
            "brief",
            "target_audience",
            "registration_link",
            "qr_code_target_url",
            "contact_email",
            "contact_phone",
            "production_deadline",
            "job_requirement_id",
            "job_title",
            "company_id",
            "company_name",
            "job_location",
            "job_min_salary",
            "job_max_salary",
            "job_eligibility",
            "job_deadline",
            "job_interview_date",
            "assigned_designer",
            "created_by",
            "versions",
            "decisions",
            "is_editable",
            "is_locked",
            "is_archived",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CreativeRequestCreateSerializer(serializers.Serializer):
    job_requirement_id = serializers.UUIDField(required=True)
    title = serializers.CharField(max_length=255, required=True)
    deliverable_type = serializers.ChoiceField(
        choices=CreativeDeliverableType.CHOICES,
        default=CreativeDeliverableType.COMBINED_PACK,
    )
    priority = serializers.ChoiceField(
        choices=CreativePriority.CHOICES,
        default=CreativePriority.MEDIUM,
    )
    brief = serializers.CharField(required=False, allow_blank=True, default="")
    target_audience = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    registration_link = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    qr_code_target_url = serializers.URLField(max_length=500, required=False, allow_blank=True, default="")
    contact_email = serializers.EmailField(required=False, allow_blank=True, default="")
    contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    production_deadline = serializers.DateTimeField(required=False, allow_null=True, default=None)
    assigned_designer_id = serializers.UUIDField(required=False, allow_null=True, default=None)


class CreativeBriefUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False)
    priority = serializers.ChoiceField(choices=CreativePriority.CHOICES, required=False)
    brief = serializers.CharField(required=False)
    target_audience = serializers.CharField(max_length=255, required=False, allow_blank=True)
    registration_link = serializers.URLField(max_length=500, required=False, allow_blank=True)
    qr_code_target_url = serializers.URLField(max_length=500, required=False, allow_blank=True)
    contact_email = serializers.EmailField(required=False, allow_blank=True)
    contact_phone = serializers.CharField(max_length=32, required=False, allow_blank=True)
    production_deadline = serializers.DateTimeField(required=False, allow_null=True)


class AssignDesignerSerializer(serializers.Serializer):
    designer_id = serializers.UUIDField(required=True)


class UploadAssetVersionSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)
    deliverable_type = serializers.ChoiceField(
        choices=CreativeDeliverableType.CHOICES,
        required=False,
    )
    designer_notes = serializers.CharField(required=False, allow_blank=True, default="")


class VerifyChecklistItemSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=ChecklistItemStatus.CHOICES,
        required=True,
    )
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class ReturnCorrectionSerializer(serializers.Serializer):
    feedback = serializers.CharField(required=True, min_length=5)


class ApproveAssetVersionSerializer(serializers.Serializer):
    comments = serializers.CharField(required=False, allow_blank=True, default="")


class RejectAssetVersionSerializer(serializers.Serializer):
    rejection_reason = serializers.CharField(required=True, min_length=5)
