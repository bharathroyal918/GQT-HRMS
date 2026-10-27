"""Views for Reports & Analytics (Phase 11).

Provides versioned, read-only REST endpoints and safe CSV downloads under /api/v1/reports/.
"""
from django.http import HttpResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.analytics.permissions import (
    CanAccessCompanyReports,
    CanAccessMonthlyStatistics,
    CanAccessPerformanceReports,
    CanAccessPlacementReports,
    CanAccessStudentReports,
    CanAccessStudentSelfReport,
)
from apps.analytics.selectors import (
    get_company_reports_dataset,
    get_monthly_statistics_dataset,
    get_performance_reports_dataset,
    get_placement_reports_dataset,
    get_single_student_report_summary,
    get_student_reports_dataset,
)
from apps.analytics.serializers import (
    CompanyReportsFilterSerializer,
    MonthlyStatisticsFilterSerializer,
    PerformanceReportsFilterSerializer,
    PlacementReportsFilterSerializer,
    StudentReportsFilterSerializer,
)
from apps.analytics.services import (
    generate_company_reports_csv,
    generate_monthly_statistics_csv,
    generate_performance_reports_csv,
    generate_placement_reports_csv,
    generate_student_reports_csv,
)
from apps.students.models import StudentProfile


# -------------------------------------------------------------------------
# 1. Company Reports Views
# -------------------------------------------------------------------------
class CompanyReportsView(APIView):
    """Retrieve aggregate corporate hiring activity, drive counts, and recruiter satisfaction."""

    permission_classes = [IsAuthenticated, CanAccessCompanyReports]

    @extend_schema(
        summary="Retrieve Company Reports Dataset",
        parameters=[
            OpenApiParameter("tier", str, required=False, description="Filter by Company Tier (TIER_1, TIER_2, TIER_3)"),
            OpenApiParameter("domain_category", str, required=False, description="Filter by Industry Domain Category"),
            OpenApiParameter("company_id", int, required=False, description="Filter by specific Company ID"),
        ],
        responses={200: dict},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = CompanyReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        data = get_company_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


class CompanyReportsExportView(APIView):
    """Export Company Reports as a sanitized, formula-injection safe CSV."""

    permission_classes = [IsAuthenticated, CanAccessCompanyReports]

    @extend_schema(
        summary="Export Company Reports as CSV",
        responses={200: str},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = CompanyReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        dataset = get_company_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        csv_content = generate_company_reports_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="gqt_company_reports.csv"'
        return response


# -------------------------------------------------------------------------
# 2. Student Reports Views
# -------------------------------------------------------------------------
class StudentReportsView(APIView):
    """Retrieve aggregate student verification, readiness certification, and placement rates."""

    permission_classes = [IsAuthenticated, CanAccessStudentReports]

    @extend_schema(
        summary="Retrieve Student Reports Dataset",
        parameters=[
            OpenApiParameter("department", str, required=False, description="Filter by Academic Department"),
            OpenApiParameter("graduation_year", int, required=False, description="Filter by Passing Out Year"),
            OpenApiParameter("is_verified", bool, required=False, description="Filter by Placement Verification status"),
        ],
        responses={200: dict},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = StudentReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        data = get_student_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


class StudentReportsExportView(APIView):
    """Export Student Reports as a sanitized, formula-injection safe CSV."""

    permission_classes = [IsAuthenticated, CanAccessStudentReports]

    @extend_schema(
        summary="Export Student Reports as CSV",
        responses={200: str},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = StudentReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        dataset = get_student_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        csv_content = generate_student_reports_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="gqt_student_reports.csv"'
        return response


class StudentSelfReportSummaryView(APIView):
    """Retrieve strictly isolated personal metrics for the authenticated student candidate."""

    permission_classes = [IsAuthenticated, CanAccessStudentSelfReport]

    @extend_schema(
        summary="Retrieve Student Personal Placement Summary",
        responses={200: dict},
    )
    def get(self, request, *args, **kwargs):
        try:
            profile = request.user.student_profile
        except (AttributeError, StudentProfile.DoesNotExist):
            return Response(
                {"success": False, "error": "No student profile found for authenticated user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        data = get_single_student_report_summary(profile)
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


# -------------------------------------------------------------------------
# 3. Placement Reports Views
# -------------------------------------------------------------------------
class PlacementReportsView(APIView):
    """Retrieve authoritative placement results, offer letter lifecycle, and joining statistics."""

    permission_classes = [IsAuthenticated, CanAccessPlacementReports]

    @extend_schema(
        summary="Retrieve Placement Reports Dataset",
        parameters=[
            OpenApiParameter("company_id", int, required=False),
            OpenApiParameter("job_requirement_id", int, required=False),
            OpenApiParameter("department", str, required=False),
            OpenApiParameter("status", str, required=False),
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
        ],
        responses={200: dict},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = PlacementReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        data = get_placement_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


class PlacementReportsExportView(APIView):
    """Export Placement Reports as a sanitized, formula-injection safe CSV."""

    permission_classes = [IsAuthenticated, CanAccessPlacementReports]

    @extend_schema(
        summary="Export Placement Reports as CSV",
        responses={200: str},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = PlacementReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        dataset = get_placement_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        csv_content = generate_placement_reports_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="gqt_placement_reports.csv"'
        return response


# -------------------------------------------------------------------------
# 4. Performance Reports Views
# -------------------------------------------------------------------------
class PerformanceReportsView(APIView):
    """Retrieve 10-stage objective recruitment conversion funnel and pipeline yields."""

    permission_classes = [IsAuthenticated, CanAccessPerformanceReports]

    @extend_schema(
        summary="Retrieve Performance & Conversion Funnel Reports",
        parameters=[
            OpenApiParameter("company_id", int, required=False),
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
        ],
        responses={200: dict},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = PerformanceReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        data = get_performance_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


class PerformanceReportsExportView(APIView):
    """Export Performance Reports as a sanitized, formula-injection safe CSV."""

    permission_classes = [IsAuthenticated, CanAccessPerformanceReports]

    @extend_schema(
        summary="Export Performance Reports as CSV",
        responses={200: str},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = PerformanceReportsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        dataset = get_performance_reports_dataset(
            filters=filter_serializer.validated_data,
            user=request.user,
        )
        csv_content = generate_performance_reports_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="gqt_performance_reports.csv"'
        return response


# -------------------------------------------------------------------------
# 5. Monthly Statistics Views
# -------------------------------------------------------------------------
class MonthlyStatisticsView(APIView):
    """Retrieve month-based statistics partitioned strictly by event-specific dates in configured timezone."""

    permission_classes = [IsAuthenticated, CanAccessMonthlyStatistics]

    @extend_schema(
        summary="Retrieve Monthly Statistics",
        parameters=[
            OpenApiParameter("year", int, required=False, description="Target Calendar Year (default current year)"),
            OpenApiParameter("month", int, required=False, description="Target Month (1-12)"),
        ],
        responses={200: dict},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = MonthlyStatisticsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        year = filter_serializer.validated_data.get("year")
        month = filter_serializer.validated_data.get("month")
        data = get_monthly_statistics_dataset(
            year=year,
            month=month,
            user=request.user,
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


class MonthlyStatisticsExportView(APIView):
    """Export Monthly Statistics as a sanitized, formula-injection safe CSV."""

    permission_classes = [IsAuthenticated, CanAccessMonthlyStatistics]

    @extend_schema(
        summary="Export Monthly Statistics as CSV",
        responses={200: str},
    )
    def get(self, request, *args, **kwargs):
        filter_serializer = MonthlyStatisticsFilterSerializer(data=request.query_params)
        filter_serializer.is_valid(raise_exception=True)
        year = filter_serializer.validated_data.get("year")
        month = filter_serializer.validated_data.get("month")
        dataset = get_monthly_statistics_dataset(
            year=year,
            month=month,
            user=request.user,
        )
        csv_content = generate_monthly_statistics_csv(dataset)
        response = HttpResponse(csv_content, content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = f'attachment; filename="gqt_monthly_statistics_{year}.csv"'
        return response
