"""URL routing for Interview Management & Tracking (Phase 8 / Steps 29-35)."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.interviews.views import (
    CandidateShortlistViewSet,
    InterviewScheduleViewSet,
    InterviewRoundViewSet,
    HRInterviewFollowUpViewSet,
    ProcessDueRemindersView,
    StudentMyInterviewsView,
    InterviewKPIView,
)

app_name = "interviews"

router = DefaultRouter()
router.register(r"shortlists", CandidateShortlistViewSet, basename="shortlist")
router.register(r"schedules", InterviewScheduleViewSet, basename="schedule")
router.register(r"rounds", InterviewRoundViewSet, basename="round")
router.register(r"follow-ups", HRInterviewFollowUpViewSet, basename="follow-up")

urlpatterns = [
    path("kpis/", InterviewKPIView.as_view(), name="interview-kpis"),
    path("my-interviews/", StudentMyInterviewsView.as_view(), name="my-interviews"),
    path("reminders/process-due/", ProcessDueRemindersView.as_view(), name="reminders-process-due"),
    path("", include(router.urls)),
]
