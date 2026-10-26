"""REST API Serializers for Student Onboarding, Resumes, and Eligibility Engine."""
from decimal import Decimal
from rest_framework import serializers
from apps.accounts.models import User
from apps.students.models import (
    JobPublication,
    JobPublicationChannel,
    JobPublicationStatus,
    StudentProfile,
    StudentResume,
    StudentApplication,
    StudentApplicationStatus,
    EligibilityEvaluation,
    EligibilityStatus,
    CandidateCohort,
    CohortMember,
)


class JobPublicationSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_name = serializers.CharField(source="job_requirement.company.name", read_only=True)
    published_by_name = serializers.CharField(source="published_by.full_name", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = JobPublication
        fields = [
            "id",
            "job_requirement",
            "job_title",
            "company_name",
            "creative_version",
            "channel",
            "channel_display",
            "status",
            "status_display",
            "target_audience",
            "subject",
            "message_body",
            "dispatched_at",
            "delivered_at",
            "failure_reason",
            "retry_count",
            "provider_message_id",
            "published_by",
            "published_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class JobPublicationCreateSerializer(serializers.Serializer):
    job_requirement_id = serializers.UUIDField()
    channel = serializers.ChoiceField(choices=JobPublicationChannel.CHOICES)
    target_audience = serializers.CharField(max_length=255)
    creative_version_id = serializers.UUIDField(required=False, allow_null=True)
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True)
    message_body = serializers.CharField(required=False, allow_blank=True)


class StudentRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    roll_number = serializers.CharField(max_length=64)
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    college_name = serializers.CharField(max_length=255)
    degree = serializers.CharField(max_length=100)
    department = serializers.CharField(max_length=100)
    graduation_year = serializers.IntegerField(min_value=2000, max_value=2100)
    cgpa = serializers.DecimalField(max_digits=4, decimal_places=2, min_value=Decimal("0.00"), max_value=Decimal("10.00"))
    active_backlogs = serializers.IntegerField(required=False, default=0, min_value=0)
    history_backlogs = serializers.IntegerField(required=False, default=0, min_value=0)
    phone_number = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")
    alternate_phone = serializers.CharField(max_length=30, required=False, allow_blank=True, default="")


class StudentResumeSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    uploaded_at = serializers.DateTimeField(source="created_at", read_only=True)

    class Meta:
        model = StudentResume
        fields = [
            "id",
            "version_number",
            "file_name",
            "file_size_bytes",
            "sha256_hash",
            "is_current",
            "download_url",
            "uploaded_at",
        ]
        read_only_fields = fields

    def get_download_url(self, obj) -> str:
        return f"/api/v1/students/resumes/{obj.id}/download/"


class StudentResumeUploadSerializer(serializers.Serializer):
    file = serializers.FileField()


class StudentProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    current_resume = serializers.SerializerMethodField()
    resumes = StudentResumeSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user",
            "full_name",
            "email",
            "roll_number",
            "institutional_email",
            "college_name",
            "degree",
            "department",
            "graduation_year",
            "cgpa",
            "active_backlogs",
            "history_backlogs",
            "phone_number",
            "alternate_phone",
            "is_verified_by_placement",
            "current_resume",
            "resumes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "full_name",
            "email",
            "roll_number",
            "institutional_email",
            "is_verified_by_placement",
            "current_resume",
            "resumes",
            "created_at",
            "updated_at",
        ]

    def get_current_resume(self, obj) -> dict | None:
        active = obj.current_resume
        if active:
            return StudentResumeSerializer(active).data
        return None


class StudentProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = [
            "college_name",
            "degree",
            "department",
            "graduation_year",
            "cgpa",
            "active_backlogs",
            "history_backlogs",
            "phone_number",
            "alternate_phone",
        ]


class EligibilityEvaluationSerializer(serializers.ModelSerializer):
    override_by_name = serializers.CharField(source="override_by.full_name", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = EligibilityEvaluation
        fields = [
            "id",
            "status",
            "status_display",
            "criteria_snapshot",
            "evaluation_details",
            "is_overridden",
            "override_reason",
            "override_by",
            "override_by_name",
            "override_at",
            "evaluated_at",
        ]
        read_only_fields = fields


class StudentApplicationSerializer(serializers.ModelSerializer):
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_department = serializers.CharField(source="student.department", read_only=True)
    student_cgpa = serializers.DecimalField(source="student.cgpa", max_digits=4, decimal_places=2, read_only=True)
    student_active_backlogs = serializers.IntegerField(source="student.active_backlogs", read_only=True)
    student_graduation_year = serializers.IntegerField(source="student.graduation_year", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_name = serializers.CharField(source="job_requirement.company.name", read_only=True)
    resume_version = serializers.IntegerField(source="resume.version_number", read_only=True, default=None)
    resume_id = serializers.UUIDField(source="resume.id", read_only=True, default=None)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    eligibility_evaluation = EligibilityEvaluationSerializer(read_only=True)

    class Meta:
        model = StudentApplication
        fields = [
            "id",
            "student",
            "student_roll",
            "student_name",
            "student_department",
            "student_cgpa",
            "student_active_backlogs",
            "student_graduation_year",
            "job_requirement",
            "job_title",
            "company_name",
            "resume",
            "resume_id",
            "resume_version",
            "status",
            "status_display",
            "applied_at",
            "eligibility_evaluation",
        ]
        read_only_fields = fields


class EligibilityOverrideSerializer(serializers.Serializer):
    is_eligible = serializers.BooleanField()
    override_reason = serializers.CharField(min_length=10)


class CohortMemberSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="student.id", read_only=True)
    student_roll = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_email = serializers.EmailField(source="student.institutional_email", read_only=True)
    student_department = serializers.CharField(source="student.department", read_only=True)
    student_cgpa = serializers.DecimalField(source="student.cgpa", max_digits=4, decimal_places=2, read_only=True)
    student_active_backlogs = serializers.IntegerField(source="student.active_backlogs", read_only=True)
    student_graduation_year = serializers.IntegerField(source="student.graduation_year", read_only=True)
    resume_id = serializers.UUIDField(source="application.resume.id", read_only=True, default=None)
    resume_version = serializers.IntegerField(source="application.resume.version_number", read_only=True, default=None)
    override_by_name = serializers.CharField(source="override_by.full_name", read_only=True, default=None)

    class Meta:
        model = CohortMember
        fields = [
            "id",
            "student_id",
            "student_roll",
            "student_name",
            "student_email",
            "student_department",
            "student_cgpa",
            "student_active_backlogs",
            "student_graduation_year",
            "application",
            "resume_id",
            "resume_version",
            "is_eligible",
            "is_override",
            "override_reason",
            "override_by",
            "override_by_name",
            "override_at",
            "created_at",
        ]
        read_only_fields = fields


class CandidateCohortSerializer(serializers.ModelSerializer):
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_name = serializers.CharField(source="job_requirement.company.name", read_only=True)
    finalized_by_name = serializers.CharField(source="finalized_by.full_name", read_only=True, default=None)
    member_count = serializers.IntegerField(read_only=True)
    eligible_member_count = serializers.IntegerField(read_only=True)
    members = CohortMemberSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateCohort
        fields = [
            "id",
            "job_requirement",
            "job_title",
            "company_name",
            "title",
            "is_locked",
            "finalized_by",
            "finalized_by_name",
            "finalized_at",
            "finalization_notes",
            "member_count",
            "eligible_member_count",
            "members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CohortFinalizeSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")
