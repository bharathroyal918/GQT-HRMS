"""Placement Management Serializers.

Validates inputs and formats responses for:
- Step 36: Final Result Ingestion
- Step 37: Candidate Placement Statuses & Transitions
- Step 38: Student Notification Dispatches
- Step 39: Offer Letter Uploads & Downloads
- Step 40: Offer Acceptance Tracking
- Step 41: Candidate Joining Verification
"""
from rest_framework import serializers
from apps.placements.models import (
    FinalResultIntake,
    CandidatePlacementStatus,
    PlacementStatusHistory,
    PlacementNotificationLog,
    CandidateOfferLetter,
    OfferLetterVersion,
    JoiningStatusHistory,
    ResultIntakeSource,
    CandidatePlacementStatusChoices,
    OfferAcceptanceStatus,
    JoiningStatus,
)


class CandidatePlacementResultItemInputSerializer(serializers.Serializer):
    """Input serializer for an individual candidate result within an intake batch."""

    student_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=CandidatePlacementStatusChoices.CHOICES)
    designation_offered = serializers.CharField(required=False, allow_blank=True, default="")
    offered_ctc = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    work_location = serializers.CharField(required=False, allow_blank=True, default="")
    remarks = serializers.CharField(required=False, allow_blank=True, default="")


class FinalResultIntakeCreateSerializer(serializers.Serializer):
    """Payload for ingesting corporate HR final results (Step 36)."""

    job_requirement_id = serializers.UUIDField()
    company_id = serializers.UUIDField()
    hr_contact_id = serializers.UUIDField(required=False, allow_null=True)
    source = serializers.ChoiceField(choices=ResultIntakeSource.CHOICES, default=ResultIntakeSource.EMAIL)
    received_at = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    candidate_results = serializers.ListField(
        child=CandidatePlacementResultItemInputSerializer(),
        min_length=1,
    )


class PlacementStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.CharField(source="changed_by.full_name", read_only=True)

    class Meta:
        models_class = PlacementStatusHistory
        model = PlacementStatusHistory
        fields = [
            "id",
            "previous_status",
            "new_status",
            "reason",
            "changed_by_name",
            "created_at",
        ]


class PlacementNotificationLogSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source="sent_by.full_name", read_only=True)

    class Meta:
        model = PlacementNotificationLog
        fields = [
            "id",
            "recipient_email",
            "recipient_phone",
            "channel",
            "status",
            "status_announced",
            "provider_message_id",
            "details_payload",
            "sent_at",
            "sent_by_name",
        ]


class CandidateOfferLetterSerializer(serializers.ModelSerializer):
    """Offer letter document metadata and response/joining states."""

    issued_by_name = serializers.CharField(source="issued_by.full_name", read_only=True)
    acceptance_status_display = serializers.CharField(source="get_acceptance_status_display", read_only=True)
    joining_status_display = serializers.CharField(source="get_joining_status_display", read_only=True)
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = CandidateOfferLetter
        fields = [
            "id",
            "file_name",
            "file_size_bytes",
            "sha256_hash",
            "version_number",
            "is_active",
            "issued_at",
            "issued_by_name",
            "acceptance_deadline",
            "acceptance_status",
            "acceptance_status_display",
            "accepted_at",
            "acceptance_source",
            "student_decision_notes",
            "joining_status",
            "joining_status_display",
            "expected_joining_date",
            "actual_joining_date",
            "deferred_joining_date",
            "joining_location",
            "employee_id_assigned",
            "joining_notes",
            "joining_verified_at",
            "download_url",
            "created_at",
        ]

    def get_download_url(self, obj: CandidateOfferLetter) -> str:
        return f"/api/v1/placements/offers/{obj.id}/download/"


class CandidatePlacementStatusSerializer(serializers.ModelSerializer):
    """List serializer for candidate placement status entries."""

    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_email = serializers.CharField(source="student.institutional_email", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    status_updated_by_name = serializers.CharField(source="status_updated_by.full_name", read_only=True)
    has_offer_letter = serializers.SerializerMethodField()
    offer_letter_id = serializers.SerializerMethodField()
    acceptance_status = serializers.SerializerMethodField()
    joining_status = serializers.SerializerMethodField()

    class Meta:
        model = CandidatePlacementStatus
        fields = [
            "id",
            "job_requirement",
            "job_title",
            "company",
            "company_name",
            "student",
            "student_roll",
            "student_name",
            "student_email",
            "status",
            "status_display",
            "designation_offered",
            "offered_ctc",
            "work_location",
            "remarks",
            "has_offer_letter",
            "offer_letter_id",
            "acceptance_status",
            "joining_status",
            "status_updated_at",
            "status_updated_by_name",
            "created_at",
        ]

    def get_has_offer_letter(self, obj: CandidatePlacementStatus) -> bool:
        return hasattr(obj, "offer_letter") and obj.offer_letter is not None

    def get_offer_letter_id(self, obj: CandidatePlacementStatus) -> str | None:
        if hasattr(obj, "offer_letter") and obj.offer_letter is not None:
            return str(obj.offer_letter.id)
        return None

    def get_acceptance_status(self, obj: CandidatePlacementStatus) -> str | None:
        if hasattr(obj, "offer_letter") and obj.offer_letter is not None:
            return obj.offer_letter.acceptance_status
        return None

    def get_joining_status(self, obj: CandidatePlacementStatus) -> str | None:
        if hasattr(obj, "offer_letter") and obj.offer_letter is not None:
            return obj.offer_letter.joining_status
        return None


class CandidatePlacementStatusDetailSerializer(CandidatePlacementStatusSerializer):
    """Detailed candidate placement serializer with audit history and offer letter payload."""

    history = PlacementStatusHistorySerializer(many=True, read_only=True)
    offer_letter = CandidateOfferLetterSerializer(read_only=True)

    class Meta(CandidatePlacementStatusSerializer.Meta):
        fields = CandidatePlacementStatusSerializer.Meta.fields + [
            "history",
            "offer_letter",
        ]


class FinalResultIntakeSerializer(serializers.ModelSerializer):
    """Summary serializer for a final result intake batch."""

    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    hr_contact_name = serializers.CharField(source="hr_contact.name", default="", read_only=True)
    source_display = serializers.CharField(source="get_source_display", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = FinalResultIntake
        fields = [
            "id",
            "job_requirement",
            "job_title",
            "company",
            "company_name",
            "hr_contact",
            "hr_contact_name",
            "result_reference_code",
            "source",
            "source_display",
            "received_at",
            "total_results",
            "selected_count",
            "rejected_count",
            "waiting_list_count",
            "hold_count",
            "notes",
            "created_at",
            "created_by_name",
        ]


class UpdatePlacementStatusPayloadSerializer(serializers.Serializer):
    """Payload for updating candidate status (Step 37)."""

    status = serializers.ChoiceField(choices=CandidatePlacementStatusChoices.CHOICES)
    reason = serializers.CharField(required=False, allow_blank=True, default="")
    designation_offered = serializers.CharField(required=False, allow_blank=True)
    offered_ctc = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True)
    work_location = serializers.CharField(required=False, allow_blank=True)
    remarks = serializers.CharField(required=False, allow_blank=True)


class OfferLetterUploadPayloadSerializer(serializers.Serializer):
    """Payload for uploading or revising an offer letter (Step 39)."""

    placement_id = serializers.UUIDField()
    file = serializers.FileField()
    acceptance_deadline = serializers.DateField(required=False, allow_null=True)
    expected_joining_date = serializers.DateField(required=False, allow_null=True)
    joining_location = serializers.CharField(required=False, allow_blank=True, default="")


class OfferAcceptancePayloadSerializer(serializers.Serializer):
    """Payload for candidate offer response (Step 40)."""

    decision = serializers.ChoiceField(choices=[OfferAcceptanceStatus.ACCEPTED, OfferAcceptanceStatus.DECLINED])
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    source = serializers.ChoiceField(
        choices=["STUDENT_PORTAL", "PLACEMENT_OFFICE"],
        default="STUDENT_PORTAL",
        required=False,
    )


class JoiningStatusUpdatePayloadSerializer(serializers.Serializer):
    """Payload for verifying onboarding and joining status (Step 41)."""

    joining_status = serializers.ChoiceField(
        choices=[JoiningStatus.JOINED, JoiningStatus.NOT_JOINED, JoiningStatus.DEFERRED]
    )
    actual_joining_date = serializers.DateField(required=False, allow_null=True)
    deferred_joining_date = serializers.DateField(required=False, allow_null=True)
    joining_location = serializers.CharField(required=False, allow_blank=True, default="")
    employee_id_assigned = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class StudentPlacementViewSerializer(serializers.ModelSerializer):
    """Sanitized student-facing serializer. Strips internal staff notes and recruiter remarks."""

    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    offer_letter = CandidateOfferLetterSerializer(read_only=True)

    class Meta:
        model = CandidatePlacementStatus
        fields = [
            "id",
            "job_requirement",
            "job_title",
            "company",
            "company_name",
            "status",
            "status_display",
            "designation_offered",
            "offered_ctc",
            "work_location",
            "offer_letter",
            "status_updated_at",
            "created_at",
        ]
