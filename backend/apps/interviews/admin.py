"""Django Admin registration for Interview Management & Tracking models."""
from django.contrib import admin
from apps.interviews.models import (
    CandidateShortlist,
    ShortlistedCandidate,
    InterviewSchedule,
    InterviewNotificationLog,
    InterviewReminder,
    InterviewRound,
    HRInterviewFollowUp,
)


class ShortlistedCandidateInline(admin.TabularInline):
    model = ShortlistedCandidate
    extra = 0
    raw_id_fields = ("student", "submission")


@admin.register(CandidateShortlist)
class CandidateShortlistAdmin(admin.ModelAdmin):
    list_display = (
        "shortlist_reference_code",
        "company",
        "job_requirement",
        "candidate_count",
        "source",
        "received_at",
    )
    list_filter = ("source", "company", "received_at")
    search_fields = ("shortlist_reference_code", "company__name", "job_requirement__title")
    inlines = [ShortlistedCandidateInline]


class InterviewReminderInline(admin.TabularInline):
    model = InterviewReminder
    extra = 0


class InterviewNotificationLogInline(admin.TabularInline):
    model = InterviewNotificationLog
    extra = 0
    readonly_fields = ("sent_at", "provider_message_id")


@admin.register(InterviewSchedule)
class InterviewScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "schedule_reference_code",
        "student",
        "company",
        "interview_date",
        "interview_time",
        "mode",
        "status",
        "attendance_status",
        "conducted_status",
    )
    list_filter = (
        "status",
        "mode",
        "attendance_status",
        "conducted_status",
        "interview_date",
        "company",
    )
    search_fields = (
        "schedule_reference_code",
        "student__roll_number",
        "student__user__email",
        "company__name",
    )
    inlines = [InterviewReminderInline, InterviewNotificationLogInline]


@admin.register(InterviewRound)
class InterviewRoundAdmin(admin.ModelAdmin):
    list_display = (
        "candidate",
        "round_number",
        "category",
        "status",
        "scheduled_date",
        "evaluated_at",
    )
    list_filter = ("category", "status", "scheduled_date")
    search_fields = ("candidate__student__roll_number", "interviewer_names")


@admin.register(HRInterviewFollowUp)
class HRInterviewFollowUpAdmin(admin.ModelAdmin):
    list_display = (
        "company",
        "job_requirement",
        "candidate_status_reported",
        "expected_result_date",
        "next_follow_up_date",
        "response_status",
        "follow_up_date",
    )
    list_filter = ("response_status", "channel", "follow_up_date", "company")
    search_fields = ("company__name", "job_requirement__title", "candidate_status_reported")
