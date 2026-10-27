"""URL routing configuration for Placement Management & Tracking (Phase 8 / Steps 36-41)."""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.placements.views import (
    FinalResultIntakeViewSet,
    CandidatePlacementStatusViewSet,
    CandidateOfferLetterViewSet,
    OfferLetterDownloadAPIView,
    StudentPlacementAPIView,
    PlacementKPIAPIView,
    JobParticipatingCandidatesAPIView,
)

router = DefaultRouter()
router.register(r"intakes", FinalResultIntakeViewSet, basename="placement-intakes")
router.register(r"statuses", CandidatePlacementStatusViewSet, basename="placement-statuses")
router.register(r"offers", CandidateOfferLetterViewSet, basename="placement-offers")

urlpatterns = [
    # KPIs
    path("kpis/", PlacementKPIAPIView.as_view(), name="placement-kpis"),

    # Student portal self-service
    path("my-placements/", StudentPlacementAPIView.as_view(), name="my-placements"),

    # Candidates eligible for final result intake
    path(
        "jobs/<uuid:job_id>/candidates/",
        JobParticipatingCandidatesAPIView.as_view(),
        name="job-participating-candidates",
    ),

    # Secure authenticated streaming download for offer letter
    path(
        "offers/<uuid:pk>/download/",
        OfferLetterDownloadAPIView.as_view(),
        name="offer-download",
    ),

    # Router endpoints
    path("", include(router.urls)),
]
