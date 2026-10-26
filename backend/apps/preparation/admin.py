"""Django Admin configuration for Student Preparation models."""
from django.contrib import admin
from apps.preparation.models import (
    ResumeReview,
    ResumeImprovementCycle,
    AssessmentTest,
    StudentAssessmentAttempt,
    TrainingSession,
    TrainingAttendance,
    MockInterview,
    MockInterviewEvaluation,
    PlacementReadinessCertification,
)


@admin.register(ResumeReview)
class ResumeReviewAdmin(admin.ModelAdmin):
    list_display = ("student", "resume", "reviewer", "status", "formatting_score", "technical_skills_score", "reviewed_at")
    list_filter = ("status", "reviewed_at")
    search_fields = ("student__roll_number", "student__user__first_name", "student__user__last_name", "reviewer__email")


@admin.register(ResumeImprovementCycle)
class ResumeImprovementCycleAdmin(admin.ModelAdmin):
    list_display = ("student", "initial_review", "status", "submitted_at")
    list_filter = ("status",)
    search_fields = ("student__roll_number", "student__user__first_name", "student__user__last_name")


@admin.register(AssessmentTest)
class AssessmentTestAdmin(admin.ModelAdmin):
    list_display = ("title", "test_type", "domain_track", "duration_minutes", "total_marks", "passing_marks", "is_active")
    list_filter = ("test_type", "is_active")
    search_fields = ("title", "domain_track")


@admin.register(StudentAssessmentAttempt)
class StudentAssessmentAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "test", "attempt_number", "score", "percentage", "passed", "status", "started_at")
    list_filter = ("passed", "status", "test__test_type")
    search_fields = ("student__roll_number", "test__title")


@admin.register(TrainingSession)
class TrainingSessionAdmin(admin.ModelAdmin):
    list_display = ("title", "session_type", "trainer", "scheduled_at", "venue_or_link", "is_completed")
    list_filter = ("session_type", "is_completed")
    search_fields = ("title", "trainer__email")


@admin.register(TrainingAttendance)
class TrainingAttendanceAdmin(admin.ModelAdmin):
    list_display = ("student", "session", "attendance_status", "presentation_score", "grooming_certified")
    list_filter = ("attendance_status", "grooming_certified", "session__session_type")
    search_fields = ("student__roll_number", "session__title")


@admin.register(MockInterview)
class MockInterviewAdmin(admin.ModelAdmin):
    list_display = ("student", "evaluator", "interview_type", "scheduled_at", "status")
    list_filter = ("interview_type", "status")
    search_fields = ("student__roll_number", "evaluator__email")


@admin.register(MockInterviewEvaluation)
class MockInterviewEvaluationAdmin(admin.ModelAdmin):
    list_display = ("mock_interview", "evaluator", "total_score", "readiness_recommendation", "evaluated_at")
    list_filter = ("readiness_recommendation",)
    search_fields = ("mock_interview__student__roll_number", "evaluator__email")


@admin.register(PlacementReadinessCertification)
class PlacementReadinessCertificationAdmin(admin.ModelAdmin):
    list_display = ("student", "approved_resume", "is_approved_for_placements", "status", "certified_by", "certified_at")
    list_filter = ("is_approved_for_placements", "status")
    search_fields = ("student__roll_number", "certified_by__email")
