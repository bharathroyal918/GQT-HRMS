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

    # Job requirement attributes for student drive visibility
    location = serializers.CharField(source="job_requirement.location", read_only=True)
    min_salary = serializers.DecimalField(source="job_requirement.min_salary", max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    max_salary = serializers.DecimalField(source="job_requirement.max_salary", max_digits=12, decimal_places=2, read_only=True, allow_null=True)
    salary_currency = serializers.CharField(source="job_requirement.salary_currency", read_only=True)
    employment_type = serializers.CharField(source="job_requirement.employment_type", read_only=True)
    employment_type_display = serializers.CharField(source="job_requirement.get_employment_type_display", read_only=True)
    work_arrangement = serializers.CharField(source="job_requirement.work_arrangement", read_only=True)
    work_arrangement_display = serializers.CharField(source="job_requirement.get_work_arrangement_display", read_only=True)
    registration_deadline = serializers.DateTimeField(source="job_requirement.registration_deadline", read_only=True)
    interview_date = serializers.DateField(source="job_requirement.interview_date", read_only=True, allow_null=True)
    eligibility_criteria = serializers.CharField(source="job_requirement.eligibility_criteria", read_only=True)
    min_cgpa = serializers.DecimalField(source="job_requirement.min_cgpa", max_digits=4, decimal_places=2, read_only=True, allow_null=True)
    skills_required = serializers.CharField(source="job_requirement.skills_required", read_only=True)
    job_description = serializers.CharField(source="job_requirement.job_description", read_only=True)
    openings_count = serializers.IntegerField(source="job_requirement.openings_count", read_only=True)
    has_bond = serializers.BooleanField(source="job_requirement.has_bond", read_only=True)
    bond_details = serializers.CharField(source="job_requirement.bond_details", read_only=True)
    job_status = serializers.CharField(source="job_requirement.status", read_only=True)
    job_is_archived = serializers.BooleanField(source="job_requirement.is_archived", read_only=True)
    eligibility_preview = serializers.SerializerMethodField()

    def get_eligibility_preview(self, obj):
        request = self.context.get("request")
        if not request or not getattr(request, "user", None) or not request.user.is_authenticated:
            return None
        if not hasattr(request, "_student_profile_cache"):
            from apps.students.selectors import get_student_profile_by_user
            request._student_profile_cache = get_student_profile_by_user(request.user)
        student_profile = request._student_profile_cache
        if not student_profile:
            return None

        from apps.students.services import evaluate_student_eligibility
        from apps.students.models import EligibilityStatus

        eval_result = evaluate_student_eligibility(obj.job_requirement, student_profile)
        status_display_map = {
            EligibilityStatus.ELIGIBLE: "Eligible",
            EligibilityStatus.INELIGIBLE: "Ineligible",
            EligibilityStatus.INCOMPLETE: "Profile Incomplete",
        }
        return {
            "status": eval_result["status"],
            "status_display": status_display_map.get(eval_result["status"], eval_result["status"]),
            "passed": eval_result["passed"],
            "details": eval_result["details"],
            "criteria_snapshot": eval_result["criteria_snapshot"],
        }

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
            "location",
            "min_salary",
            "max_salary",
            "salary_currency",
            "employment_type",
            "employment_type_display",
            "work_arrangement",
            "work_arrangement_display",
            "registration_deadline",
            "interview_date",
            "eligibility_criteria",
            "min_cgpa",
            "skills_required",
            "job_description",
            "openings_count",
            "has_bond",
            "bond_details",
            "job_status",
            "job_is_archived",
            "eligibility_preview",
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
