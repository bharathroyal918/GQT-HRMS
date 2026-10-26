"""Serializers for Candidate Submissions & Profile Dispatch API (Phase 7)."""
from rest_framework import serializers
from apps.submissions.models import (
    SubmissionPackage,
    SubmissionPackageStatus,
    CandidateSubmission,
    CandidateSubmissionStatus,
    SubmissionDispatchLog,
    DispatchChannel,
    AcknowledgementChannel,
)


class CandidateEligibilityReadinessSerializer(serializers.Serializer):
    """Candidate readiness item indicating eligibility and Step 23 Placement Head certification."""

    student_id = serializers.UUIDField()
    student_name = serializers.CharField()
    roll_number = serializers.CharField()
    institutional_email = serializers.EmailField()
    phone_number = serializers.CharField()
    college_name = serializers.CharField()
    department = serializers.CharField()
    graduation_year = serializers.IntegerField()
    cgpa = serializers.FloatField(allow_null=True)
    technical_skills = serializers.CharField(allow_blank=True)
    application_id = serializers.UUIDField()
    application_status = serializers.CharField()
    is_in_locked_cohort = serializers.BooleanField()
    has_readiness_certification = serializers.BooleanField()
    certification_id = serializers.UUIDField(allow_null=True)
    approved_resume_id = serializers.UUIDField(allow_null=True)
    approved_resume_version = serializers.IntegerField(allow_null=True)
    approved_resume_file_name = serializers.CharField(allow_null=True)
    approved_resume_sha256 = serializers.CharField(allow_null=True)
    is_already_submitted = serializers.BooleanField()
    can_be_submitted = serializers.BooleanField()


class CandidateSubmissionSerializer(serializers.ModelSerializer):
    """Individual candidate record inside a corporate submission package."""

    student_id = serializers.UUIDField(source="student.id", read_only=True)
    roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    institutional_email = serializers.EmailField(source="student.institutional_email", read_only=True)
    phone_number = serializers.CharField(source="student.phone_number", read_only=True)
    department = serializers.CharField(source="student.department", read_only=True)
    graduation_year = serializers.IntegerField(source="student.graduation_year", read_only=True)
    cgpa = serializers.DecimalField(source="student.cgpa", max_digits=4, decimal_places=2, read_only=True)
    resume_id = serializers.UUIDField(source="submitted_resume.id", read_only=True)
    resume_file_url = serializers.SerializerMethodField()

    class Meta:
        model = CandidateSubmission
        fields = [
            "id",
            "student_id",
            "roll_number",
            "student_name",
            "institutional_email",
            "phone_number",
            "department",
            "graduation_year",
            "cgpa",
            "resume_id",
            "resume_version_number",
            "resume_sha256",
            "resume_file_url",
            "status",
            "candidate_snapshot",
            "created_at",
            "updated_at",
        ]

    def get_resume_file_url(self, obj) -> str:
        if obj.submitted_resume and obj.submitted_resume.file:
            return f"/api/v1/students/resumes/{obj.submitted_resume.id}/download/"
        return ""


class SubmissionDispatchLogSerializer(serializers.ModelSerializer):
    """Audit log record of profile transmission attempt."""

    dispatched_by_name = serializers.CharField(source="dispatched_by.full_name", read_only=True)

    class Meta:
        model = SubmissionDispatchLog
        fields = [
            "id",
            "attempt_number",
            "channel",
            "recipient",
            "status",
            "provider_message_id",
            "response_payload",
            "dispatched_by_name",
            "timestamp",
        ]


class SubmissionPackageListSerializer(serializers.ModelSerializer):
    """Summary representation for submission package directory and queues."""

    job_id = serializers.UUIDField(source="job_requirement.id", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_id = serializers.UUIDField(source="company.id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    hr_contact_id = serializers.UUIDField(source="hr_contact.id", read_only=True)
    hr_contact_name = serializers.CharField(source="hr_contact.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    dispatched_by_name = serializers.CharField(source="dispatched_by.full_name", read_only=True)

    class Meta:
        model = SubmissionPackage
        fields = [
            "id",
            "title",
            "job_id",
            "job_title",
            "company_id",
            "company_name",
            "hr_contact_id",
            "hr_contact_name",
            "status",
            "candidate_count",
            "package_hash",
            "roster_file_name",
            "has_roster_file",
            "created_at",
            "dispatched_at",
            "acknowledged_at",
            "created_by_name",
            "dispatched_by_name",
        ]

    has_roster_file = serializers.SerializerMethodField()

    def get_has_roster_file(self, obj) -> bool:
        return bool(obj.roster_file)


class SubmissionPackageDetailSerializer(serializers.ModelSerializer):
    """Complete detail representation of candidate submission package with roster and logs."""

    job_id = serializers.UUIDField(source="job_requirement.id", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    company_id = serializers.UUIDField(source="company.id", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    hr_contact_id = serializers.UUIDField(source="hr_contact.id", read_only=True)
    hr_contact_name = serializers.CharField(source="hr_contact.name", read_only=True)
    hr_contact_email = serializers.EmailField(source="hr_contact.email", read_only=True)
    hr_contact_phone = serializers.CharField(source="hr_contact.phone", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    dispatched_by_name = serializers.CharField(source="dispatched_by.full_name", read_only=True)
    acknowledged_by_name = serializers.CharField(source="acknowledged_by.full_name", read_only=True)

    candidates = CandidateSubmissionSerializer(many=True, read_only=True)
    dispatch_logs = SubmissionDispatchLogSerializer(many=True, read_only=True)
    roster_download_url = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionPackage
        fields = [
            "id",
            "title",
            "job_id",
            "job_title",
            "company_id",
            "company_name",
            "hr_contact_id",
            "hr_contact_name",
            "hr_contact_email",
            "hr_contact_phone",
            "status",
            "candidate_count",
            "package_hash",
            "roster_file_name",
            "roster_download_url",
            "roster_generated_at",
            "resumes_attached_at",
            "notes",
            "created_at",
            "created_by_name",
            # Dispatch
            "dispatched_at",
            "dispatched_by_name",
            "dispatch_channel",
            "recipient_email",
            "recipient_name",
            "recipient_phone",
            "provider_reference",
            "dispatch_notes",
            # Acknowledgment
            "acknowledged_at",
            "acknowledged_by_name",
            "acknowledged_by_contact_name",
            "acknowledgement_channel",
            "recruiter_feedback",
            "tentative_interview_date",
            "follow_up_callback_date",
            # Nested
            "candidates",
            "dispatch_logs",
        ]

    def get_roster_download_url(self, obj) -> str:
        if obj.roster_file:
            return f"/api/v1/submissions/packages/{obj.id}/roster/download/"
        return ""


class CreateSubmissionPackageSerializer(serializers.Serializer):
    """Payload for Step 24: Prepare Candidate List and initialize submission package."""

    job_requirement_id = serializers.UUIDField(required=True)
    candidate_student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        required=True,
    )
    title = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class DispatchPackageSerializer(serializers.Serializer):
    """Payload for Step 27: Profile Dispatch to Corporate HR."""

    channel = serializers.ChoiceField(
        choices=DispatchChannel.CHOICES,
        default=DispatchChannel.EMAIL,
    )
    recipient_email = serializers.EmailField(required=False, allow_blank=True, default="")
    recipient_name = serializers.CharField(max_length=255, required=False, allow_blank=True, default="")
    recipient_phone = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    dispatch_notes = serializers.CharField(required=False, allow_blank=True, default="")


class RecordAcknowledgementSerializer(serializers.Serializer):
    """Payload for Step 28: Log Corporate Recruiter Acknowledgment."""

    acknowledged_by_contact_name = serializers.CharField(max_length=255, required=True)
    acknowledgement_channel = serializers.ChoiceField(
        choices=AcknowledgementChannel.CHOICES,
        default=AcknowledgementChannel.EMAIL,
    )
    recruiter_feedback = serializers.CharField(required=False, allow_blank=True, default="")
    tentative_interview_date = serializers.DateField(required=False, allow_null=True)
    follow_up_callback_date = serializers.DateField(required=False, allow_null=True)


class StudentSubmissionSerializer(serializers.ModelSerializer):
    """Student-facing submission card (strict candidate privacy isolation)."""

    package_id = serializers.UUIDField(source="package.id", read_only=True)
    job_title = serializers.CharField(source="package.job_requirement.title", read_only=True)
    company_name = serializers.CharField(source="package.company.name", read_only=True)
    dispatched_at = serializers.DateTimeField(source="package.dispatched_at", read_only=True)
    resume_version = serializers.IntegerField(source="resume_version_number", read_only=True)

    class Meta:
        model = CandidateSubmission
        fields = [
            "id",
            "package_id",
            "job_title",
            "company_name",
            "status",
            "resume_version",
            "dispatched_at",
            "created_at",
        ]
