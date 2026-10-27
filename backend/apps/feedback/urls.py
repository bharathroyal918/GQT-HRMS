"""URL routing for Phase 9 Feedback Collection."""
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from apps.feedback import views

app_name = "feedback"

router = DefaultRouter()
router.register("student", views.StudentFeedbackViewSet, basename="student-feedback")
router.register("hr", views.HRFeedbackViewSet, basename="hr-feedback")
router.register("trainer", views.TrainerFeedbackViewSet, basename="trainer-feedback")

urlpatterns = [
    path("summary/", views.FeedbackSummaryAPIView.as_view(), name="feedback-summary"),
    path("student-drives/", views.StudentEligibleDrivesAPIView.as_view(), name="feedback-student-drives"),
    path("", include(router.urls)),
]
