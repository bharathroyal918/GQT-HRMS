"""Serializers for Student Preparation Domain (Phase 6 / Steps 15-23)."""
from rest_framework import serializers
from apps.accounts.models import RoleCatalog
from apps.preparation.models import (
    ResumeReview,
    ResumeImprovementCycle,
    AssessmentTest,
    StudentAssessmentAttempt,
    TrainingSession,
    TrainingAttendance,
    MockInterview,
    MockInterviewEvaluation,
    PlacementReadinessCertification,
)


class ResumeReviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    reviewer_name = serializers.CharField(source="reviewer.full_name", read_only=True)
    resume_version = serializers.IntegerField(source="resume.version_number", read_only=True)
    aggregate_score = serializers.IntegerField(read_only=True)

    class Meta:
        model = ResumeReview
        fields = [
            "id",
            "resume",
            "resume_version",
            "student",
            "student_name",
            "student_roll_number",
            "reviewer",
            "reviewer_name",
            "status",
            "formatting_score",
            "technical_skills_score",
            "projects_score",
            "achievements_score",
            "aggregate_score",
            "detailed_feedback",
            "suggested_improvements",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reviewer", "reviewed_at", "created_at", "updated_at"]


class ResumeReviewCreateSerializer(serializers.Serializer):
    resume_id = serializers.UUIDField()
    status = serializers.ChoiceField(choices=["APPROVED", "REVISION_REQUESTED"])
    formatting_score = serializers.IntegerField(min_value=1, max_value=10, default=7)
    technical_skills_score = serializers.IntegerField(min_value=1, max_value=10, default=7)
    projects_score = serializers.IntegerField(min_value=1, max_value=10, default=7)
    achievements_score = serializers.IntegerField(min_value=1, max_value=10, default=7)
    detailed_feedback = serializers.CharField()
    suggested_improvements = serializers.CharField(required=False, allow_blank=True, default="")


class ResumeImprovementCycleSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    prior_resume_version = serializers.IntegerField(source="prior_resume.version_number", read_only=True)
    improved_resume_version = serializers.IntegerField(source="improved_resume.version_number", read_only=True, allow_null=True)

    class Meta:
        model = ResumeImprovementCycle
        fields = [
            "id",
            "initial_review",
            "student",
            "student_name",
            "student_roll_number",
            "prior_resume",
            "prior_resume_version",
            "improved_resume",
            "improved_resume_version",
            "status",
            "student_notes",
            "submitted_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AssessmentTestListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentTest
        fields = [
            "id",
            "title",
            "test_type",
            "domain_track",
            "description",
            "duration_minutes",
            "total_marks",
            "passing_marks",
            "question_count",
            "is_active",
            "created_by_name",
            "created_at",
        ]

    def get_question_count(self, obj) -> int:
        return len(obj.questions or [])


class AssessmentTestDetailSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    questions = serializers.SerializerMethodField()

    class Meta:
        model = AssessmentTest
        fields = [
            "id",
            "title",
            "test_type",
            "domain_track",
            "description",
            "duration_minutes",
            "total_marks",
            "passing_marks",
            "questions",
            "is_active",
            "created_by_name",
            "created_at",
        ]

    def get_questions(self, obj) -> list:
        request = self.context.get("request")
        questions = obj.questions or []

        # If user is a student, STRICTLY STRIP answer keys and explanations
        if request and request.user and request.user.is_authenticated:
            user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
            if RoleCatalog.STUDENT in user_roles and not (request.user.is_staff or request.user.is_superuser):
                sanitized = []
                for q in questions:
                    clean_q = {
                        "id": q.get("id"),
                        "question_text": q.get("question_text"),
                        "options": q.get("options", []),
                        "marks": q.get("marks", 10),
                    }
                    sanitized.append(clean_q)
                return sanitized

        return questions


class StudentAssessmentAttemptSerializer(serializers.ModelSerializer):
    test_title = serializers.CharField(source="test.title", read_only=True)
    test_type = serializers.CharField(source="test.test_type", read_only=True)
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    total_marks = serializers.IntegerField(source="test.total_marks", read_only=True)
    passing_marks = serializers.IntegerField(source="test.passing_marks", read_only=True)

    class Meta:
        model = StudentAssessmentAttempt
        fields = [
            "id",
            "student",
            "student_name",
            "student_roll_number",
            "test",
            "test_title",
            "test_type",
            "attempt_number",
            "score",
            "total_marks",
            "passing_marks",
            "percentage",
            "passed",
            "status",
            "answers",
            "started_at",
            "completed_at",
            "created_at",
        ]
        read_only_fields = ["id", "attempt_number", "score", "percentage", "passed", "status", "started_at", "completed_at"]


class StartAssessmentAttemptSerializer(serializers.Serializer):
    test_id = serializers.UUIDField()


class SubmitAssessmentAttemptSerializer(serializers.Serializer):
    attempt_id = serializers.UUIDField()
    answers = serializers.DictField(child=serializers.CharField())


class TrainingSessionSerializer(serializers.ModelSerializer):
    trainer_name = serializers.CharField(source="trainer.full_name", read_only=True)
    attendee_count = serializers.SerializerMethodField()

    class Meta:
        model = TrainingSession
        fields = [
            "id",
            "title",
            "session_type",
            "trainer",
            "trainer_name",
            "scheduled_at",
            "venue_or_link",
            "description",
            "is_completed",
            "attendee_count",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def get_attendee_count(self, obj) -> int:
        return obj.attendances.count()


class TrainingAttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    session_title = serializers.CharField(source="session.title", read_only=True)
    session_type = serializers.CharField(source="session.session_type", read_only=True)

    class Meta:
        model = TrainingAttendance
        fields = [
            "id",
            "session",
            "session_title",
            "session_type",
            "student",
            "student_name",
            "student_roll_number",
            "attendance_status",
            "presentation_score",
            "professional_etiquette_verified",
            "corporate_communication_verified",
            "dress_code_verified",
            "hr_interview_ready",
            "grooming_certified",
            "trainer_remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecordAttendanceSerializer(serializers.Serializer):
    session_id = serializers.UUIDField()
    student_id = serializers.UUIDField()
    attendance_status = serializers.ChoiceField(choices=["ATTENDED", "ABSENT", "EXCUSED"])
    presentation_score = serializers.IntegerField(min_value=1, max_value=10, required=False, allow_null=True)
    professional_etiquette_verified = serializers.BooleanField(default=False)
    corporate_communication_verified = serializers.BooleanField(default=False)
    dress_code_verified = serializers.BooleanField(default=False)
    hr_interview_ready = serializers.BooleanField(default=False)
    grooming_certified = serializers.BooleanField(default=False)
    trainer_remarks = serializers.CharField(required=False, allow_blank=True, default="")


class MockInterviewEvaluationSerializer(serializers.ModelSerializer):
    evaluator_name = serializers.CharField(source="evaluator.full_name", read_only=True)

    class Meta:
        model = MockInterviewEvaluation
        fields = [
            "id",
            "mock_interview",
            "evaluator",
            "evaluator_name",
            "technical_competence_score",
            "problem_solving_score",
            "communication_clarity_score",
            "professional_readiness_score",
            "total_score",
            "technical_feedback",
            "communication_feedback",
            "improvement_suggestions",
            "readiness_recommendation",
            "evaluated_at",
        ]
        read_only_fields = ["id", "total_score", "evaluated_at"]


class MockInterviewSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    evaluator_name = serializers.CharField(source="evaluator.full_name", read_only=True)
    scheduled_by_name = serializers.CharField(source="scheduled_by.full_name", read_only=True)
    evaluation = MockInterviewEvaluationSerializer(read_only=True)

    class Meta:
        model = MockInterview
        fields = [
            "id",
            "student",
            "student_name",
            "student_roll_number",
            "evaluator",
            "evaluator_name",
            "scheduled_by",
            "scheduled_by_name",
            "interview_type",
            "scheduled_at",
            "meeting_link",
            "status",
            "notes",
            "evaluation",
            "created_at",
        ]
        read_only_fields = ["id", "scheduled_by", "created_at"]


class ScheduleMockInterviewSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    evaluator_id = serializers.UUIDField()
    scheduled_at = serializers.DateTimeField()
    interview_type = serializers.ChoiceField(choices=["TECHNICAL", "HR", "COMBINED"], default="COMBINED")
    meeting_link = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class SubmitMockEvaluationSerializer(serializers.Serializer):
    mock_interview_id = serializers.UUIDField()
    technical_competence_score = serializers.IntegerField(min_value=1, max_value=10)
    problem_solving_score = serializers.IntegerField(min_value=1, max_value=10)
    communication_clarity_score = serializers.IntegerField(min_value=1, max_value=10)
    professional_readiness_score = serializers.IntegerField(min_value=1, max_value=10)
    technical_feedback = serializers.CharField()
    communication_feedback = serializers.CharField()
    improvement_suggestions = serializers.CharField()
    readiness_recommendation = serializers.ChoiceField(
        choices=["READY_FOR_PLACEMENTS", "NEEDS_PRACTICE", "NOT_READY"]
    )


class PlacementReadinessCertificationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.user.full_name", read_only=True)
    student_roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    department = serializers.CharField(source="student.department", read_only=True)
    certified_by_name = serializers.CharField(source="certified_by.full_name", read_only=True)
    approved_resume_version = serializers.IntegerField(source="approved_resume.version_number", read_only=True)

    class Meta:
        model = PlacementReadinessCertification
        fields = [
            "id",
            "student",
            "student_name",
            "student_roll_number",
            "department",
            "approved_resume",
            "approved_resume_version",
            "is_approved_for_placements",
            "status",
            "certified_by",
            "certified_by_name",
            "certified_at",
            "readiness_summary",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "certified_by", "certified_at", "created_at"]


class CertifyPlacementReadinessRequestSerializer(serializers.Serializer):
    student_id = serializers.UUIDField()
    approved_resume_id = serializers.UUIDField()
    is_approved = serializers.BooleanField(default=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")
