"""Django Admin registration for Placement Management models."""
from django.contrib import admin
from apps.placements.models import (
    FinalResultIntake,
    CandidatePlacementStatus,
    PlacementStatusHistory,
    PlacementNotificationLog,
    CandidateOfferLetter,
    OfferLetterVersion,
    JoiningStatusHistory,
)


class PlacementStatusHistoryInline(admin.TabularInline):
    model = PlacementStatusHistory
    extra = 0
    readonly_fields = ("previous_status", "new_status", "reason", "changed_by", "created_at")


class PlacementNotificationLogInline(admin.TabularInline):
    model = PlacementNotificationLog
    extra = 0
    readonly_fields = (
        "recipient_email",
        "recipient_phone",
        "channel",
        "status",
        "status_announced",
        "provider_message_id",
        "sent_at",
        "sent_by",
    )


class OfferLetterVersionInline(admin.TabularInline):
    model = OfferLetterVersion
    extra = 0
    readonly_fields = (
        "version_number",
        "file_name",
        "file_size_bytes",
        "sha256_hash",
        "superseded_at",
        "superseded_by",
    )


class JoiningStatusHistoryInline(admin.TabularInline):
    model = JoiningStatusHistory
    extra = 0
    readonly_fields = (
        "previous_status",
        "new_status",
        "reason",
        "changed_by",
        "created_at",
    )


@admin.register(FinalResultIntake)
class FinalResultIntakeAdmin(admin.ModelAdmin):
    list_display = (
        "result_reference_code",
        "job_requirement",
        "company",
        "source",
        "total_results",
        "selected_count",
        "rejected_count",
        "received_at",
        "created_at",
    )
    search_fields = ("result_reference_code", "company__name", "job_requirement__title")
    list_filter = ("source", "created_at")


@admin.register(CandidatePlacementStatus)
class CandidatePlacementStatusAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "job_requirement",
        "company",
        "status",
        "offered_ctc",
        "designation_offered",
        "status_updated_at",
    )
    search_fields = (
        "student__roll_number",
        "student__user__full_name",
        "student__user__email",
        "company__name",
        "job_requirement__title",
    )
    list_filter = ("status", "created_at")
    inlines = [PlacementStatusHistoryInline, PlacementNotificationLogInline]


@admin.register(CandidateOfferLetter)
class CandidateOfferLetterAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "job_requirement",
        "company",
        "version_number",
        "acceptance_status",
        "joining_status",
        "acceptance_deadline",
        "is_active",
    )
    search_fields = (
        "student__roll_number",
        "student__user__full_name",
        "company__name",
        "file_name",
    )
    list_filter = ("acceptance_status", "joining_status", "is_active")
    inlines = [OfferLetterVersionInline, JoiningStatusHistoryInline]


@admin.register(PlacementNotificationLog)
class PlacementNotificationLogAdmin(admin.ModelAdmin):
    list_display = (
        "recipient_email",
        "channel",
        "status",
        "status_announced",
        "provider_message_id",
        "sent_at",
    )
    search_fields = ("recipient_email", "provider_message_id")
    list_filter = ("channel", "status", "status_announced")
