"""Serializers for Reports & Analytics (Phase 11).

Provides typed filter validation and response contracts for all 5 report categories.
"""
from datetime import date
from rest_framework import serializers

from apps.crm.models import CompanyDomainCategory, CompanyTier
from apps.placements.models import CandidatePlacementStatusChoices


class CompanyReportsFilterSerializer(serializers.Serializer):
    """Filter parameters for Company Reports."""

    tier = serializers.ChoiceField(
        choices=CompanyTier.CHOICES,
        required=False,
        allow_blank=True,
    )
    domain_category = serializers.ChoiceField(
        choices=CompanyDomainCategory.CHOICES,
        required=False,
        allow_blank=True,
    )
    company_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )


class StudentReportsFilterSerializer(serializers.Serializer):
    """Filter parameters for Student Reports."""

    department = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    graduation_year = serializers.IntegerField(
        required=False,
        min_value=2000,
        max_value=2100,
    )
    is_verified = serializers.BooleanField(
        required=False,
        allow_null=True,
        default=None,
    )


class PlacementReportsFilterSerializer(serializers.Serializer):
    """Filter parameters for Placement Reports."""

    company_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    job_requirement_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    department = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True,
    )
    status = serializers.ChoiceField(
        choices=CandidatePlacementStatusChoices.CHOICES,
        required=False,
        allow_blank=True,
    )
    start_date = serializers.DateField(
        required=False,
    )
    end_date = serializers.DateField(
        required=False,
    )

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({"end_date": "end_date must be greater than or equal to start_date."})
        return attrs


class PerformanceReportsFilterSerializer(serializers.Serializer):
    """Filter parameters for Performance Reports / Conversion Funnel."""

    company_id = serializers.IntegerField(
        required=False,
        min_value=1,
    )
    start_date = serializers.DateField(
        required=False,
    )
    end_date = serializers.DateField(
        required=False,
    )

    def validate(self, attrs):
        start = attrs.get("start_date")
        end = attrs.get("end_date")
        if start and end and start > end:
            raise serializers.ValidationError({"end_date": "end_date must be greater than or equal to start_date."})
        return attrs


class MonthlyStatisticsFilterSerializer(serializers.Serializer):
    """Filter parameters for Monthly Statistics."""

    year = serializers.IntegerField(
        required=False,
        default=date.today().year,
        min_value=2020,
        max_value=2100,
    )
    month = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        max_value=12,
    )
