"""DRF Serializers for Interview Management & Tracking (Phase 8 / Steps 29-35)."""
from rest_framework import serializers
from apps.interviews.models import (
    CandidateShortlist,
    ShortlistedCandidate,
    InterviewSchedule,
    InterviewNotificationLog,
    InterviewReminder,
    InterviewRound,
    HRInterviewFollowUp,
    ShortlistSource,
    InterviewMode,
    AttendanceStatus,
    ConductedStatus,
    RoundCategory,
    RoundStatus,
    FollowUpResponseStatus,
)


class ShortlistedCandidateItemSerializer(serializers.ModelSerializer):
    student_id = serializers.UUIDField(source="student.id", read_only=True)
    roll_number = serializers.CharField(source="student.roll_number", read_only=True)
    full_name = serializers.CharField(source="student.user.full_name", read_only=True)
    email = serializers.EmailField(source="student.user.email", read_only=True)
    phone_number = serializers.CharField(source="student.phone_number", read_only=True)
    department = serializers.CharField(source="student.department", read_only=True)
    degree = serializers.CharField(source="student.degree", read_only=True)
    cgpa = serializers.DecimalField(source="student.cgpa", max_digits=4, decimal_places=2, read_only=True)
    active_schedule_id = serializers.SerializerMethodField()

    class Meta:
        model = ShortlistedCandidate
        fields = [
            "id",
            "student_id",
            "roll_number",
            "full_name",
            "email",
            "phone_number",
            "department",
            "degree",
            "cgpa",
            "status",
            "recruiter_notes",
            "active_schedule_id",
            "created_at",
        ]

    def get_active_schedule_id(self, obj):
        active_sch = obj.schedules.filter(is_superseded=False).first()
        return str(active_sch.id) if active_sch else None


class CandidateShortlistSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    hr_contact_name = serializers.CharField(source="hr_contact.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    candidates = ShortlistedCandidateItemSerializer(many=True, read_only=True)

    class Meta:
        model = CandidateShortlist
        fields = [
            "id",
            "job_requirement",
            "company",
            "company_name",
            "job_title",
            "hr_contact",
            "hr_contact_name",
            "submission_package",
            "shortlist_reference_code",
            "source",
            "received_at",
            "candidate_count",
            "notes",
            "created_by",
            "created_by_name",
            "candidates",
            "created_at",
        ]


class CandidateShortlistCreateSerializer(serializers.Serializer):
    job_id = serializers.UUIDField(required=True)
    company_id = serializers.UUIDField(required=True)
    hr_contact_id = serializers.UUIDField(required=True)
    submission_package_id = serializers.UUIDField(required=False, allow_null=True)
    student_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False,
        required=True,
    )
    source = serializers.ChoiceField(choices=ShortlistSource.CHOICES, default=ShortlistSource.EMAIL)
    received_at = serializers.DateTimeField(required=False, allow_null=True)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class InterviewReminderSerializer(serializers.ModelSerializer):
    interval_display = serializers.CharField(source="get_interval_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = InterviewReminder
        fields = [
            "id",
            "interval",
            "interval_display",
            "scheduled_for",
            "status",
            "status_display",
            "sent_at",
            "channel",
            "provider_message_id",
            "error_message",
            "attempt_count",
        ]


class InterviewNotificationLogSerializer(serializers.ModelSerializer):
    sent_by_name = serializers.CharField(source="sent_by.full_name", read_only=True)

    class Meta:
        model = InterviewNotificationLog
        fields = [
            "id",
            "recipient_email",
            "recipient_phone",
            "channel",
            "status",
            "provider_message_id",
            "details_payload",
            "sent_at",
            "sent_by",
            "sent_by_name",
        ]


class InterviewScheduleSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    candidate_roll = serializers.CharField(source="student.roll_number", read_only=True)
    candidate_name = serializers.CharField(source="student.user.full_name", read_only=True)
    candidate_email = serializers.CharField(source="student.user.email", read_only=True)
    candidate_phone = serializers.CharField(source="student.phone_number", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    attendance_confirmed_by_name = serializers.CharField(
        source="attendance_confirmed_by.full_name", read_only=True
    )
    conducted_recorded_by_name = serializers.CharField(
        source="conducted_recorded_by.full_name", read_only=True
    )
    mode_display = serializers.CharField(source="get_mode_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    attendance_status_display = serializers.CharField(
        source="get_attendance_status_display", read_only=True
    )
    conducted_status_display = serializers.CharField(
        source="get_conducted_status_display", read_only=True
    )
    reminders = InterviewReminderSerializer(many=True, read_only=True)
    notification_logs = InterviewNotificationLogSerializer(many=True, read_only=True)

    class Meta:
        model = InterviewSchedule
        fields = [
            "id",
            "job_requirement",
            "company",
            "company_name",
            "job_title",
            "candidate",
            "student",
            "candidate_roll",
            "candidate_name",
            "candidate_email",
            "candidate_phone",
            "schedule_reference_code",
            "mode",
            "mode_display",
            "interview_date",
            "interview_time",
            "scheduled_start_time",
            "venue",
            "meeting_link",
            "required_documents",
            "status",
            "status_display",
            "rescheduled_from",
            "is_superseded",
            "notified_at",
            "notification_status",
            "attendance_status",
            "attendance_status_display",
            "attendance_confirmed_at",
            "attendance_confirmed_by",
            "attendance_confirmed_by_name",
            "attendance_source",
            "attendance_notes",
            "conducted_status",
            "conducted_status_display",
            "conducted_at",
            "conducted_recorded_by",
            "conducted_recorded_by_name",
            "conducted_notes",
            "created_by",
            "created_by_name",
            "reminders",
            "notification_logs",
            "created_at",
        ]


class InterviewScheduleCreateSerializer(serializers.Serializer):
    candidate_id = serializers.UUIDField(required=True)
    interview_date = serializers.DateField(required=True)
    interview_time = serializers.TimeField(required=True)
    mode = serializers.ChoiceField(choices=InterviewMode.CHOICES, default=InterviewMode.ONLINE)
    venue = serializers.CharField(required=False, allow_blank=True, default="")
    meeting_link = serializers.URLField(required=False, allow_blank=True, default="")
    required_documents = serializers.CharField(
        required=False,
        allow_blank=True,
        default="Resume copies (2), Government Photo ID, College ID, Academic Marksheets (original + photocopy)",
    )


class InterviewRescheduleSerializer(serializers.Serializer):
    new_date = serializers.DateField(required=True)
    new_time = serializers.TimeField(required=True)
    new_mode = serializers.ChoiceField(choices=InterviewMode.CHOICES, required=False)
    new_venue = serializers.CharField(required=False, allow_blank=True)
    new_meeting_link = serializers.URLField(required=False, allow_blank=True)
    new_required_documents = serializers.CharField(required=False, allow_blank=True)
    reschedule_reason = serializers.CharField(required=False, allow_blank=True, default="")


class AttendanceConfirmationSerializer(serializers.Serializer):
    attendance_status = serializers.ChoiceField(
        choices=[
            AttendanceStatus.CONFIRMED,
            AttendanceStatus.DECLINED,
            AttendanceStatus.TENTATIVE,
        ],
        required=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class InterviewConductedSerializer(serializers.Serializer):
    conducted_status = serializers.ChoiceField(
        choices=[
            ConductedStatus.CONDUCTED,
            ConductedStatus.NOT_CONDUCTED,
            ConductedStatus.CANDIDATE_ABSENT,
            ConductedStatus.INTERVIEWER_ABSENT,
            ConductedStatus.RESCHEDULED,
        ],
        required=True,
    )
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class InterviewRoundSerializer(serializers.ModelSerializer):
    candidate_roll = serializers.CharField(source="candidate.student.roll_number", read_only=True)
    candidate_name = serializers.CharField(source="candidate.student.user.full_name", read_only=True)
    company_name = serializers.CharField(source="company.name", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    category_display = serializers.CharField(source="get_category_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    evaluated_by_name = serializers.CharField(source="evaluated_by.full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = InterviewRound
        fields = [
            "id",
            "job_requirement",
            "company",
            "company_name",
            "job_title",
            "candidate",
            "candidate_roll",
            "candidate_name",
            "schedule",
            "round_number",
            "category",
            "category_display",
            "round_name",
            "status",
            "status_display",
            "scheduled_date",
            "scheduled_time",
            "interviewer_names",
            "internal_staff_notes",
            "evaluated_at",
            "evaluated_by",
            "evaluated_by_name",
            "created_by",
            "created_by_name",
            "created_at",
        ]

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # Strip confidential staff notes for student access
        request = self.context.get("request")
        if request and request.user and request.user.is_authenticated:
            user_roles = set(request.user.role_assignments.values_list("role__code", flat=True))
            if "STUDENT" in user_roles and not (request.user.is_staff or request.user.is_superuser):
                ret.pop("internal_staff_notes", None)
        return ret


class InterviewRoundCreateSerializer(serializers.Serializer):
    candidate_id = serializers.UUIDField(required=True)
    category = serializers.ChoiceField(choices=RoundCategory.CHOICES, required=True)
    round_name = serializers.CharField(required=False, allow_blank=True, default="")
    scheduled_date = serializers.DateField(required=False, allow_null=True)
    scheduled_time = serializers.TimeField(required=False, allow_null=True)
    interviewer_names = serializers.CharField(required=False, allow_blank=True, default="")
    internal_staff_notes = serializers.CharField(required=False, allow_blank=True, default="")
    schedule_id = serializers.UUIDField(required=False, allow_null=True)


class InterviewRoundEvaluateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=[RoundStatus.CLEARED, RoundStatus.NOT_CLEARED, RoundStatus.ON_HOLD],
        required=True,
    )
    internal_staff_notes = serializers.CharField(required=False, allow_blank=True, default="")


class HRInterviewFollowUpSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    job_title = serializers.CharField(source="job_requirement.title", read_only=True)
    hr_contact_name = serializers.CharField(source="hr_contact.name", read_only=True)
    conducted_by_name = serializers.CharField(source="conducted_by.full_name", read_only=True)
    channel_display = serializers.CharField(source="get_channel_display", read_only=True)
    response_status_display = serializers.CharField(source="get_response_status_display", read_only=True)

    class Meta:
        model = HRInterviewFollowUp
        fields = [
            "id",
            "job_requirement",
            "company",
            "company_name",
            "job_title",
            "hr_contact",
            "hr_contact_name",
            "follow_up_date",
            "channel",
            "channel_display",
            "conducted_by",
            "conducted_by_name",
            "candidate_status_reported",
            "pending_rounds",
            "expected_result_date",
            "is_date_confirmed",
            "next_follow_up_date",
            "response_status",
            "response_status_display",
            "hr_response_summary",
            "notes",
            "created_at",
        ]


class HRInterviewFollowUpCreateSerializer(serializers.Serializer):
    job_id = serializers.UUIDField(required=True)
    company_id = serializers.UUIDField(required=True)
    hr_contact_id = serializers.UUIDField(required=True)
    candidate_status_reported = serializers.CharField(required=True)
    pending_rounds = serializers.CharField(required=False, allow_blank=True, default="")
    expected_result_date = serializers.DateField(required=False, allow_null=True)
    is_date_confirmed = serializers.BooleanField(default=True)
    next_follow_up_date = serializers.DateField(required=False, allow_null=True)
    channel = serializers.CharField(default="PHONE_CALL")
    response_status = serializers.ChoiceField(
        choices=FollowUpResponseStatus.CHOICES,
        default=FollowUpResponseStatus.RESPONSE_RECEIVED,
    )
    hr_response_summary = serializers.CharField(required=False, allow_blank=True, default="")
    notes = serializers.CharField(required=False, allow_blank=True, default="")
