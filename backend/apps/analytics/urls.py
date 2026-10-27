"""URL Configuration for Reports & Analytics App (Phase 11).

Endpoints mounted under /api/v1/reports/:
- /api/v1/reports/companies/ & /export/
- /api/v1/reports/students/ & /export/ & /my-summary/
- /api/v1/reports/placements/ & /export/
- /api/v1/reports/performance/ & /export/
- /api/v1/reports/monthly-stats/ & /export/
"""
from django.urls import path

from apps.analytics.views import (
    CompanyReportsExportView,
    CompanyReportsView,
    MonthlyStatisticsExportView,
    MonthlyStatisticsView,
    PerformanceReportsExportView,
    PerformanceReportsView,
    PlacementReportsExportView,
    PlacementReportsView,
    StudentReportsExportView,
    StudentReportsView,
    StudentSelfReportSummaryView,
)

app_name = "analytics"

urlpatterns = [
    # 1. Company Reports
    path("companies/", CompanyReportsView.as_view(), name="company-reports"),
    path("companies/export/", CompanyReportsExportView.as_view(), name="company-reports-export"),

    # 2. Student Reports
    path("students/", StudentReportsView.as_view(), name="student-reports"),
    path("students/export/", StudentReportsExportView.as_view(), name="student-reports-export"),
    path("students/my-summary/", StudentSelfReportSummaryView.as_view(), name="student-reports-my-summary"),

    # 3. Placement Reports
    path("placements/", PlacementReportsView.as_view(), name="placement-reports"),
    path("placements/export/", PlacementReportsExportView.as_view(), name="placement-reports-export"),

    # 4. Performance Reports
    path("performance/", PerformanceReportsView.as_view(), name="performance-reports"),
    path("performance/export/", PerformanceReportsExportView.as_view(), name="performance-reports-export"),

    # 5. Monthly Statistics
    path("monthly-stats/", MonthlyStatisticsView.as_view(), name="monthly-statistics"),
    path("monthly-stats/export/", MonthlyStatisticsExportView.as_view(), name="monthly-statistics-export"),
]
