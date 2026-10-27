"""Serializers for Phase 9 Feedback Collection."""
from rest_framework import serializers
from apps.accounts.models import RoleCatalog
from apps.feedback.models import CandidateQuality, DifficultyLevel, HRFeedback, StudentFeedback, StudentReadiness, TrainerFeedback
from apps.feedback.permissions import STAFF_VIEW_ROLES, get_user_roles


class StudentFeedbackSerializer(serializers.ModelSerializer):
    """Detailed representation of student interview experience feedback."""

    student_name = serializers.SerializerMethodField()
    student_roll_number = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="company.name", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True, default=None)
    interview_date = serializers.DateTimeField(source="interview_schedule.interview_date", read_only=True, default=None)
    difficulty_display = serializers.CharField(source="get_difficulty_display", read_only=True)
    submitted_by_name = serializers.CharField(source="submitted_by.full_name", read_only=True)

    class Meta:
        model = StudentFeedback
        fields = [
            "id",
            "student",
            "student_name",
            "student_roll_number",
            "company",
            "company_name",
            "job_requirement",
            "job_title",
            "interview_schedule",
            "interview_date",
            "interview_round",
            "interview_experience",
            "technical_questions",
            "difficulty",
            "difficulty_display",
            "suggestions",
            "is_anonymous",
            "submitted_by",
            "submitted_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "student", "submitted_by", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        request = self.context.get("request")
        if obj.is_anonymous and request:
            user = request.user
            roles = get_user_roles(user)
            # Only staff with admin permissions or the author themselves can view identity
            if obj.student.user != user and not (user.is_superuser or RoleCatalog.ADMIN in roles):
                return "Anonymous Candidate"
        return obj.student.user.full_name or obj.student.roll_number

    def get_student_roll_number(self, obj) -> str:
        request = self.context.get("request")
        if obj.is_anonymous and request:
            user = request.user
            roles = get_user_roles(user)
            if obj.student.user != user and not (user.is_superuser or RoleCatalog.ADMIN in roles):
                return "ANONYMOUS"
        return obj.student.roll_number


class StudentFeedbackCreateSerializer(serializers.Serializer):
    """Input serializer for submitting student interview feedback."""

    company = serializers.UUIDField(required=True)
    job_requirement = serializers.UUIDField(required=False, allow_null=True)
    interview_schedule = serializers.UUIDField(required=False, allow_null=True)
    interview_round = serializers.UUIDField(required=False, allow_null=True)
    interview_experience = serializers.CharField(required=True, min_length=10)
    technical_questions = serializers.CharField(required=False, allow_blank=True, default="")
    difficulty = serializers.ChoiceField(choices=[c[0] for c in DifficultyLevel.CHOICES], default=DifficultyLevel.MEDIUM)
    suggestions = serializers.CharField(required=False, allow_blank=True, default="")
    is_anonymous = serializers.BooleanField(required=False, default=False)
    student_id = serializers.UUIDField(required=False, allow_null=True, help_text="Admin only: target student")


class StudentFeedbackUpdateSerializer(serializers.Serializer):
    """Input serializer for correcting student interview feedback."""

    interview_experience = serializers.CharField(required=False, min_length=10)
    technical_questions = serializers.CharField(required=False, allow_blank=True)
    difficulty = serializers.ChoiceField(choices=[c[0] for c in DifficultyLevel.CHOICES], required=False)
    suggestions = serializers.CharField(required=False, allow_blank=True)
    is_anonymous = serializers.BooleanField(required=False)


class HRFeedbackSerializer(serializers.ModelSerializer):
    """Detailed representation of corporate recruiter feedback."""

    company_name = serializers.CharField(source="company.name", read_only=True)
    hr_contact_name = serializers.CharField(source="hr_contact.name", read_only=True, default=None)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True, default=None)
    candidate_name = serializers.SerializerMethodField()
    candidate_roll_number = serializers.CharField(source="candidate.roll_number", read_only=True, default=None)
    candidate_quality_display = serializers.CharField(source="get_candidate_quality_display", read_only=True)
    submitted_by_name = serializers.CharField(source="submitted_by.full_name", read_only=True)

    class Meta:
        model = HRFeedback
        fields = [
            "id",
            "company",
            "company_name",
            "hr_contact",
            "hr_contact_name",
            "job_requirement",
            "job_title",
            "candidate",
            "candidate_name",
            "candidate_roll_number",
            "candidate_quality",
            "candidate_quality_display",
            "candidate_quality_remarks",
            "technical_skills_rating",
            "technical_skills_remarks",
            "communication_skills_rating",
            "communication_skills_remarks",
            "hiring_satisfaction_rating",
            "hiring_satisfaction_remarks",
            "submitted_by",
            "submitted_by_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "submitted_by", "created_at", "updated_at"]

    def get_candidate_name(self, obj) -> str | None:
        if obj.candidate:
            return obj.candidate.user.full_name or obj.candidate.roll_number
        return None


class HRFeedbackCreateSerializer(serializers.Serializer):
    """Input serializer for logging corporate HR recruiter feedback."""

    company = serializers.UUIDField(required=True)
    hr_contact = serializers.UUIDField(required=False, allow_null=True)
    job_requirement = serializers.UUIDField(required=False, allow_null=True)
    candidate = serializers.UUIDField(required=False, allow_null=True)
    candidate_quality = serializers.ChoiceField(choices=[c[0] for c in CandidateQuality.CHOICES], default=CandidateQuality.GOOD)
    candidate_quality_remarks = serializers.CharField(required=False, allow_blank=True, default="")
    technical_skills_rating = serializers.IntegerField(required=False, min_value=1, max_value=5, default=3)
    technical_skills_remarks = serializers.CharField(required=False, allow_blank=True, default="")
    communication_skills_rating = serializers.IntegerField(required=False, min_value=1, max_value=5, default=3)
    communication_skills_remarks = serializers.CharField(required=False, allow_blank=True, default="")
    hiring_satisfaction_rating = serializers.IntegerField(required=False, min_value=1, max_value=5, default=4)
    hiring_satisfaction_remarks = serializers.CharField(required=False, allow_blank=True, default="")


class HRFeedbackUpdateSerializer(serializers.Serializer):
    """Input serializer for updating corporate HR feedback."""

    candidate_quality = serializers.ChoiceField(choices=[c[0] for c in CandidateQuality.CHOICES], required=False)
    candidate_quality_remarks = serializers.CharField(required=False, allow_blank=True)
    technical_skills_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    technical_skills_remarks = serializers.CharField(required=False, allow_blank=True)
    communication_skills_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    communication_skills_remarks = serializers.CharField(required=False, allow_blank=True)
    hiring_satisfaction_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    hiring_satisfaction_remarks = serializers.CharField(required=False, allow_blank=True)


class TrainerFeedbackSerializer(serializers.ModelSerializer):
    """Detailed representation of placement trainer evaluation feedback."""

    student_name = serializers.SerializerMethodField()
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    session_title = serializers.CharField(source="training_session.title", read_only=True, default=None)
    student_readiness_display = serializers.CharField(source="get_student_readiness_display", read_only=True)
    trainer_name = serializers.CharField(source="trainer.full_name", read_only=True)

    class Meta:
        model = TrainerFeedback
        fields = [
            "id",
            "student",
            "student_name",
            "student_roll_number",
            "training_session",
            "session_title",
            "student_readiness",
            "student_readiness_display",
            "student_readiness_remarks",
            "training_effectiveness_rating",
            "training_effectiveness_remarks",
            "areas_for_improvement",
            "trainer",
            "trainer_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "trainer", "created_at", "updated_at"]

    def get_student_name(self, obj) -> str:
        return obj.student.user.full_name or obj.student.roll_number


class TrainerFeedbackCreateSerializer(serializers.Serializer):
    """Input serializer for recording trainer student evaluation feedback."""

    student = serializers.UUIDField(required=True)
    training_session = serializers.UUIDField(required=False, allow_null=True)
    student_readiness = serializers.ChoiceField(choices=[c[0] for c in StudentReadiness.CHOICES], default=StudentReadiness.READY)
    student_readiness_remarks = serializers.CharField(required=False, allow_blank=True, default="")
    training_effectiveness_rating = serializers.IntegerField(required=False, min_value=1, max_value=5, default=4)
    training_effectiveness_remarks = serializers.CharField(required=False, allow_blank=True, default="")
    areas_for_improvement = serializers.CharField(required=True, min_length=10)


class TrainerFeedbackUpdateSerializer(serializers.Serializer):
    """Input serializer for updating trainer evaluation feedback."""

    student_readiness = serializers.ChoiceField(choices=[c[0] for c in StudentReadiness.CHOICES], required=False)
    student_readiness_remarks = serializers.CharField(required=False, allow_blank=True)
    training_effectiveness_rating = serializers.IntegerField(required=False, min_value=1, max_value=5)
    training_effectiveness_remarks = serializers.CharField(required=False, allow_blank=True)
    areas_for_improvement = serializers.CharField(required=False, min_length=10)


class FeedbackKPISerializer(serializers.Serializer):
    """Summary dashboard KPI metric response."""

    total_student_feedback = serializers.IntegerField()
    total_hr_feedback = serializers.IntegerField()
    total_trainer_feedback = serializers.IntegerField()
    avg_technical_skills_rating = serializers.FloatField()
    avg_communication_skills_rating = serializers.FloatField()
    avg_hiring_satisfaction_rating = serializers.FloatField()
    avg_training_effectiveness_rating = serializers.FloatField()
    difficulty_breakdown = serializers.DictField(child=serializers.IntegerField())
    readiness_breakdown = serializers.DictField(child=serializers.IntegerField())
