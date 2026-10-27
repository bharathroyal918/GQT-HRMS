"""Interview Management & Tracking Domain Models (Steps 29-35).

Authoritative GQT HRMS Workflow Steps:
- Step 29: Receive Shortlisted Candidates (Shortlist intake from corporate HR, associate with submissions)
- Step 30: Notify Students (Interview date, time, venue, meeting link, required documents)
- Step 31: Automatic Reminders (24 hours, 2 hours, 30 minutes before interview)
- Step 32: Attendance Confirmation (Candidate confirmation vs staff-recorded attendance)
- Step 33: Interview Conducted (Track whether scheduled interview was conducted)
- Step 34: Track Interview Rounds (Aptitude, Coding, Technical, HR, Managerial)
- Step 35: HR Follow-up (Candidate status, pending rounds, expected result date)
"""
import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.crm.models import Company, HRContact
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile
from apps.submissions.models import SubmissionPackage, CandidateSubmission


class ShortlistSource:
    EMAIL = "EMAIL"
    PORTAL = "PORTAL"
    FILE_IMPORT = "FILE_IMPORT"
    DIRECT_HANDOFF = "DIRECT_HANDOFF"

    CHOICES = (
        (EMAIL, "Corporate Email Shortlist"),
        (PORTAL, "Recruiter Portal Export"),
        (FILE_IMPORT, "Spreadsheet Import"),
        (DIRECT_HANDOFF, "Direct Handoff / Meeting"),
    )


class ShortlistedCandidateStatus:
    PENDING_SCHEDULE = "PENDING_SCHEDULE"
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    WITHDRAWN = "WITHDRAWN"

    CHOICES = (
        (PENDING_SCHEDULE, "Pending Interview Scheduling"),
        (SCHEDULED, "Interview Scheduled"),
        (IN_PROGRESS, "Interview Rounds In Progress"),
        (COMPLETED, "All Rounds Completed"),
        (WITHDRAWN, "Withdrawn by Candidate"),
    )


class InterviewMode:
    IN_PERSON = "IN_PERSON"
    ONLINE = "ONLINE"
    HYBRID = "HYBRID"

    CHOICES = (
        (IN_PERSON, "In-Person (On-Campus / Corporate Office)"),
        (ONLINE, "Virtual / Online (Teams / Zoom / Meet)"),
        (HYBRID, "Hybrid Drive"),
    )


class ScheduleStatus:
    SCHEDULED = "SCHEDULED"
    RESCHEDULED = "RESCHEDULED"
    CONDUCTED = "CONDUCTED"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (SCHEDULED, "Interview Scheduled"),
        (RESCHEDULED, "Interview Rescheduled"),
        (CONDUCTED, "Interview Conducted"),
        (CANCELLED, "Interview Cancelled"),
    )


class AttendanceStatus:
    NO_RESPONSE = "NO_RESPONSE"
    CONFIRMED = "CONFIRMED"
    DECLINED = "DECLINED"
    TENTATIVE = "TENTATIVE"

    CHOICES = (
        (NO_RESPONSE, "No Response Yet"),
        (CONFIRMED, "Confirmed / Attending"),
        (DECLINED, "Declined / Unable to Attend"),
        (TENTATIVE, "Tentative / Clarification Requested"),
    )


class AttendanceSource:
    STUDENT_SELF_CONFIRMED = "STUDENT_SELF_CONFIRMED"
    STAFF_RECORDED = "STAFF_RECORDED"

    CHOICES = (
        (STUDENT_SELF_CONFIRMED, "Student Self-Confirmation"),
        (STAFF_RECORDED, "Placement Staff Recorded"),
    )


class ConductedStatus:
    PENDING = "PENDING"
    CONDUCTED = "CONDUCTED"
    NOT_CONDUCTED = "NOT_CONDUCTED"
    CANDIDATE_ABSENT = "CANDIDATE_ABSENT"
    INTERVIEWER_ABSENT = "INTERVIEWER_ABSENT"
    RESCHEDULED = "RESCHEDULED"

    CHOICES = (
        (PENDING, "Pending Conduct"),
        (CONDUCTED, "Interview Conducted"),
        (NOT_CONDUCTED, "Not Conducted"),
        (CANDIDATE_ABSENT, "Candidate Absent"),
        (INTERVIEWER_ABSENT, "Interviewer Absent / Unavailable"),
        (RESCHEDULED, "Session Rescheduled"),
    )


class ReminderInterval:
    HOURS_24 = "HOURS_24"
    HOURS_2 = "HOURS_2"
    MINUTES_30 = "MINUTES_30"

    CHOICES = (
        (HOURS_24, "24 Hours Before Interview"),
        (HOURS_2, "2 Hours Before Interview"),
        (MINUTES_30, "30 Minutes Before Interview"),
    )


class ReminderStatus:
    SCHEDULED = "SCHEDULED"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    SKIPPED = "SKIPPED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"

    CHOICES = (
        (SCHEDULED, "Scheduled"),
        (PROCESSING, "Processing Delivery"),
        (SENT, "Reminder Sent"),
        (SKIPPED, "Skipped (Short-Notice Scheduling)"),
        (CANCELLED, "Cancelled (Schedule Superseded)"),
        (FAILED, "Delivery Attempt Failed"),
    )


class RoundCategory:
    APTITUDE = "APTITUDE"
    CODING = "CODING"
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    MANAGERIAL = "MANAGERIAL"

    CHOICES = (
        (APTITUDE, "Aptitude Round"),
        (CODING, "Coding / Programming Test"),
        (TECHNICAL, "Technical Interview"),
        (HR, "HR Interview"),
        (MANAGERIAL, "Managerial / Leadership Round"),
    )


class RoundStatus:
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    CLEARED = "CLEARED"
    NOT_CLEARED = "NOT_CLEARED"
    ON_HOLD = "ON_HOLD"
    CANCELLED = "CANCELLED"

    CHOICES = (
        (SCHEDULED, "Scheduled"),
        (IN_PROGRESS, "In Progress"),
        (CLEARED, "Cleared Round / Advanced"),
        (NOT_CLEARED, "Not Cleared / Eliminated"),
        (ON_HOLD, "On Hold / Decision Awaited"),
        (CANCELLED, "Round Cancelled"),
    )


class FollowUpResponseStatus:
    RESPONSE_RECEIVED = "RESPONSE_RECEIVED"
    AWAITING_RESPONSE = "AWAITING_RESPONSE"
    CALLBACK_REQUESTED = "CALLBACK_REQUESTED"

    CHOICES = (
        (RESPONSE_RECEIVED, "HR Response Received"),
        (AWAITING_RESPONSE, "Awaiting HR Response"),
        (CALLBACK_REQUESTED, "Callback Requested by Recruiter"),
    )


class CandidateShortlist(TimeStampedModel):
    """Institutional record for corporate HR shortlist intake (Step 29)."""

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="interview_shortlists",
        help_text="The approved job requirement linked to this shortlist.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="interview_shortlists",
        help_text="The corporate enterprise partner providing the shortlist.",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.PROTECT,
        related_name="interview_shortlists",
        help_text="The corporate HR contact who communicated the shortlist.",
    )
    submission_package = models.ForeignKey(
        SubmissionPackage,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="interview_shortlists",
        help_text="Optional submission package source for candidate verification.",
    )
    shortlist_reference_code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique institutional tracking reference (e.g. SL-202610-ABCD).",
    )
    source = models.CharField(
        max_length=32,
        choices=ShortlistSource.CHOICES,
        default=ShortlistSource.EMAIL,
        help_text="Channel through which the corporate shortlist was received.",
    )
    received_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Timestamp when the corporate shortlist was officially received.",
    )
    candidate_count = models.PositiveIntegerField(
        default=0,
        help_text="Total number of candidates included in this shortlist intake.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Recruiter remarks, special instructions, or intake notes.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_shortlists",
        help_text="Placement staff user who recorded the shortlist intake.",
    )

    class Meta:
        db_table = "interviews_candidate_shortlist"
        ordering = ["-received_at"]
        indexes = [
            models.Index(fields=["job_requirement", "received_at"]),
            models.Index(fields=["company", "received_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.shortlist_reference_code} - {self.company.name} ({self.candidate_count} candidates)"


class ShortlistedCandidate(TimeStampedModel):
    """Relational candidate entry in an HR shortlist (Step 29)."""

    shortlist = models.ForeignKey(
        CandidateShortlist,
        on_delete=models.CASCADE,
        related_name="candidates",
        help_text="Parent shortlist intake record.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="shortlisted_interviews",
        help_text="Shortlisted student profile.",
    )
    submission = models.ForeignKey(
        CandidateSubmission,
        on_delete=models.PROTECT,
        related_name="shortlist_entries",
        help_text="Underlying submission record for traceability.",
    )
    status = models.CharField(
        max_length=32,
        choices=ShortlistedCandidateStatus.CHOICES,
        default=ShortlistedCandidateStatus.PENDING_SCHEDULE,
        db_index=True,
        help_text="Interview progression lifecycle status for this shortlisted candidate.",
    )
    recruiter_notes = models.TextField(
        blank=True,
        default="",
        help_text="Candidate-specific notes provided by the recruiter.",
    )

    class Meta:
        db_table = "interviews_shortlisted_candidate"
        ordering = ["student__roll_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["shortlist", "student"],
                name="unique_shortlist_student",
            ),
        ]
        indexes = [
            models.Index(fields=["shortlist", "status"]),
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.student.roll_number} in {self.shortlist.shortlist_reference_code} [{self.status}]"


class InterviewSchedule(TimeStampedModel):
    """Scheduled interview event for a shortlisted candidate (Steps 30, 32, 33)."""

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="interview_schedules",
        help_text="Job requirement linked to this interview session.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="interview_schedules",
        help_text="Corporate entity conducting the interview.",
    )
    candidate = models.ForeignKey(
        ShortlistedCandidate,
        on_delete=models.PROTECT,
        related_name="schedules",
        help_text="Shortlisted candidate entry.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="interview_schedules",
        help_text="Student profile attending the interview.",
    )
    schedule_reference_code = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text="Unique schedule reference code (e.g. SCH-202610-001).",
    )
    mode = models.CharField(
        max_length=32,
        choices=InterviewMode.CHOICES,
        default=InterviewMode.ONLINE,
        help_text="Interview mode (In-person, Online, Hybrid).",
    )

    # Authoritative Step 30 Notification Fields
    interview_date = models.DateField(
        db_index=True,
        help_text="Date on which the interview is scheduled to take place.",
    )
    interview_time = models.TimeField(
        help_text="Time of day when the interview begins.",
    )
    scheduled_start_time = models.DateTimeField(
        db_index=True,
        help_text="Timezone-aware start timestamp calculated for reminder window processing.",
    )
    venue = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Physical venue, hall, or room for in-person drives.",
    )
    meeting_link = models.URLField(
        max_length=500,
        blank=True,
        default="",
        help_text="Virtual meeting link (e.g. Microsoft Teams, Google Meet, Zoom).",
    )
    required_documents = models.TextField(
        blank=True,
        default="Resume copies (2), Government Photo ID, College ID, Academic Marksheets (original + photocopy)",
        help_text="Mandatory documents candidate must bring or have ready for the interview.",
    )

    # Lifecycle & Rescheduling
    status = models.CharField(
        max_length=32,
        choices=ScheduleStatus.CHOICES,
        default=ScheduleStatus.SCHEDULED,
        db_index=True,
        help_text="Status of the interview schedule.",
    )
    rescheduled_from = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rescheduled_to",
        help_text="Previous schedule if this session was rescheduled.",
    )
    is_superseded = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if this schedule has been superseded by a reschedule.",
    )

    # Step 30: Student Notification Details
    notified_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when candidate was notified of interview schedule.",
    )
    notification_status = models.CharField(
        max_length=32,
        choices=(
            ("NOT_SENT", "Not Sent"),
            ("SENT", "Notification Dispatched"),
            ("FAILED", "Dispatch Failed"),
        ),
        default="NOT_SENT",
        db_index=True,
    )

    # Step 32: Attendance Confirmation Details
    attendance_status = models.CharField(
        max_length=32,
        choices=AttendanceStatus.CHOICES,
        default=AttendanceStatus.NO_RESPONSE,
        db_index=True,
        help_text="Candidate attendance confirmation state.",
    )
    attendance_confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when attendance confirmation was recorded.",
    )
    attendance_confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="confirmed_interview_attendances",
        help_text="User who recorded attendance (student self-confirmation or placement staff).",
    )
    attendance_source = models.CharField(
        max_length=32,
        choices=AttendanceSource.CHOICES,
        default=AttendanceSource.STUDENT_SELF_CONFIRMED,
        help_text="Source of attendance confirmation.",
    )
    attendance_notes = models.TextField(
        blank=True,
        default="",
        help_text="Notes, reasons if declining, or remarks regarding attendance.",
    )

    # Step 33: Interview Conducted Details
    conducted_status = models.CharField(
        max_length=32,
        choices=ConductedStatus.CHOICES,
        default=ConductedStatus.PENDING,
        db_index=True,
        help_text="Authoritative recording of whether the scheduled interview was conducted.",
    )
    conducted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when interview was conducted or marked conducted.",
    )
    conducted_recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorded_interview_conducts",
        help_text="Placement staff user who recorded the interview conducted outcome.",
    )
    conducted_notes = models.TextField(
        blank=True,
        default="",
        help_text="Operational observations regarding the conduct of the interview session.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_interview_schedules",
        help_text="Placement officer who created the schedule.",
    )

    class Meta:
        db_table = "interviews_schedule"
        ordering = ["scheduled_start_time"]
        indexes = [
            models.Index(fields=["job_requirement", "status"]),
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["student", "status"]),
            models.Index(fields=["scheduled_start_time"]),
            models.Index(fields=["attendance_status"]),
            models.Index(fields=["conducted_status"]),
        ]

    def __str__(self) -> str:
        return f"{self.schedule_reference_code} for {self.student.roll_number} on {self.interview_date} [{self.status}]"


class InterviewNotificationLog(TimeStampedModel):
    """Audit log tracking student interview notification dispatches (Step 30)."""

    schedule = models.ForeignKey(
        InterviewSchedule,
        on_delete=models.CASCADE,
        related_name="notification_logs",
        help_text="Interview schedule being communicated.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="interview_notifications",
    )
    recipient_email = models.EmailField(
        help_text="Student email address notified.",
    )
    recipient_phone = models.CharField(
        max_length=32,
        blank=True,
        default="",
        help_text="Student phone number for multi-channel notification.",
    )
    channel = models.CharField(
        max_length=32,
        choices=(
            ("EMAIL", "Email Notification"),
            ("WHATSAPP", "WhatsApp Message"),
            ("SMS", "SMS Message"),
            ("PORTAL", "Student Portal Alert"),
        ),
        default="EMAIL",
    )
    status = models.CharField(
        max_length=32,
        choices=(
            ("QUEUED", "Queued"),
            ("SENT", "Dispatched to Recipient"),
            ("DELIVERED", "Delivered"),
            ("FAILED", "Dispatch Failed"),
        ),
        default="SENT",
        db_index=True,
    )
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="External message ID or dispatch reference.",
    )
    details_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Snapshot of date, time, venue, meeting link, and required documents dispatched.",
    )
    sent_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    sent_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dispatched_interview_notifications",
    )

    class Meta:
        db_table = "interviews_notification_log"
        ordering = ["-sent_at"]
        indexes = [
            models.Index(fields=["schedule", "status"]),
            models.Index(fields=["student", "sent_at"]),
        ]

    def __str__(self) -> str:
        return f"Notification for {self.schedule.schedule_reference_code} -> {self.recipient_email} [{self.status}]"


class InterviewReminder(TimeStampedModel):
    """Authoritative automatic reminder intervals for interview schedules (Step 31).

    Intervals defined by authoritative workflow:
    - 24 Hours Before
    - 2 Hours Before
    - 30 Minutes Before
    """

    schedule = models.ForeignKey(
        InterviewSchedule,
        on_delete=models.CASCADE,
        related_name="reminders",
        help_text="The interview schedule this reminder belongs to.",
    )
    interval = models.CharField(
        max_length=32,
        choices=ReminderInterval.CHOICES,
        help_text="Authoritative reminder window.",
    )
    scheduled_for = models.DateTimeField(
        db_index=True,
        help_text="Exact calculated datetime when this reminder must be dispatched.",
    )
    status = models.CharField(
        max_length=32,
        choices=ReminderStatus.CHOICES,
        default=ReminderStatus.SCHEDULED,
        db_index=True,
        help_text="Delivery and processing state of the reminder.",
    )
    sent_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when reminder was successfully dispatched.",
    )
    channel = models.CharField(
        max_length=32,
        choices=(
            ("EMAIL", "Email"),
            ("WHATSAPP", "WhatsApp"),
            ("SMS", "SMS"),
        ),
        default="EMAIL",
    )
    provider_message_id = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Simulated or provider transmission identifier.",
    )
    error_message = models.TextField(
        blank=True,
        default="",
        help_text="Diagnostic message if reminder dispatch failed.",
    )
    attempt_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of processing attempts.",
    )

    class Meta:
        db_table = "interviews_reminder"
        ordering = ["scheduled_for"]
        constraints = [
            models.UniqueConstraint(
                fields=["schedule", "interval"],
                name="unique_schedule_reminder_interval",
            ),
        ]
        indexes = [
            models.Index(fields=["scheduled_for", "status"]),
            models.Index(fields=["schedule", "status"]),
        ]

    def __str__(self) -> str:
        return f"Reminder {self.interval} for {self.schedule.schedule_reference_code} at {self.scheduled_for} [{self.status}]"


class InterviewRound(TimeStampedModel):
    """Categorized interview round tracking for a candidate (Step 34).

    Authoritative Workflow Categories:
    - Aptitude
    - Coding
    - Technical
    - HR
    - Managerial
    """

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="interview_rounds",
        help_text="Associated job requirement.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="interview_rounds",
        help_text="Company conducting the round.",
    )
    candidate = models.ForeignKey(
        ShortlistedCandidate,
        on_delete=models.PROTECT,
        related_name="interview_rounds",
        help_text="Shortlisted candidate being evaluated.",
    )
    schedule = models.ForeignKey(
        InterviewSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="rounds",
        help_text="Optional linked interview schedule session.",
    )
    round_number = models.PositiveIntegerField(
        default=1,
        help_text="Sequential round progression number (1, 2, 3...).",
    )
    category = models.CharField(
        max_length=32,
        choices=RoundCategory.CHOICES,
        db_index=True,
        help_text="Authoritative interview round category.",
    )
    round_name = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Human-friendly round label (e.g. Round 1: Coding & Data Structures).",
    )
    status = models.CharField(
        max_length=32,
        choices=RoundStatus.CHOICES,
        default=RoundStatus.SCHEDULED,
        db_index=True,
        help_text="Lifecycle and evaluation outcome for this round.",
    )
    scheduled_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date scheduled for this round.",
    )
    scheduled_time = models.TimeField(
        null=True,
        blank=True,
        help_text="Time scheduled for this round.",
    )
    interviewer_names = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Interviewer names or panel description.",
    )
    internal_staff_notes = models.TextField(
        blank=True,
        default="",
        help_text="Confidential placement staff / interviewer notes. Excluded from student responses.",
    )
    evaluated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when round evaluation was recorded.",
    )
    evaluated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evaluated_interview_rounds",
        help_text="Staff user who recorded the round outcome.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_interview_rounds",
        help_text="Placement staff user who created the round.",
    )

    class Meta:
        db_table = "interviews_round"
        ordering = ["candidate", "round_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["candidate", "round_number"],
                name="unique_candidate_round_number",
            ),
        ]
        indexes = [
            models.Index(fields=["candidate", "status"]),
            models.Index(fields=["job_requirement", "category"]),
            models.Index(fields=["category", "status"]),
        ]

    def __str__(self) -> str:
        return f"{self.candidate.student.roll_number} - Round {self.round_number} ({self.get_category_display()}) [{self.status}]"


class HRInterviewFollowUp(TimeStampedModel):
    """Corporate HR follow-up tracking for interview status and results (Step 35).

    Authoritative workflow metrics:
    - Candidate status
    - Pending rounds
    - Expected result date
    """

    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.PROTECT,
        related_name="interview_follow_ups",
        help_text="Job requirement this follow-up relates to.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.PROTECT,
        related_name="interview_follow_ups",
        help_text="Corporate partner involved in the interview process.",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.PROTECT,
        related_name="interview_follow_ups",
        help_text="Corporate HR contact who provided the update.",
    )
    follow_up_date = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Date and time when this follow-up outreach occurred.",
    )
    channel = models.CharField(
        max_length=32,
        choices=(
            ("PHONE_CALL", "Phone Call"),
            ("EMAIL", "Email Communication"),
            ("WHATSAPP", "WhatsApp Discussion"),
            ("IN_PERSON", "In-Person Discussion"),
        ),
        default="PHONE_CALL",
        help_text="Communication channel used for the follow-up.",
    )
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conducted_interview_follow_ups",
        help_text="Placement officer or relationship manager who conducted the follow-up.",
    )

    # Authoritative Step 35 Metrics
    candidate_status_reported = models.CharField(
        max_length=255,
        help_text="Interim candidate pool status reported by HR (e.g. Technical Round Evaluation in Progress).",
    )
    pending_rounds = models.CharField(
        max_length=500,
        blank=True,
        default="",
        help_text="Pending rounds reported by HR (e.g. Managerial round pending for 5 students).",
    )
    expected_result_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Expected result date confirmed or estimated by HR.",
    )
    is_date_confirmed = models.BooleanField(
        default=True,
        help_text="True if HR confirmed a firm expected date; False if tentative estimate.",
    )
    next_follow_up_date = models.DateField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Agreed next follow-up callback date.",
    )
    response_status = models.CharField(
        max_length=32,
        choices=FollowUpResponseStatus.CHOICES,
        default=FollowUpResponseStatus.RESPONSE_RECEIVED,
        db_index=True,
        help_text="Status of the HR response.",
    )
    hr_response_summary = models.TextField(
        blank=True,
        default="",
        help_text="Detailed summary of the feedback or discussion with corporate HR.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal placement team notes and action items.",
    )

    class Meta:
        db_table = "interviews_hr_follow_up"
        ordering = ["-follow_up_date"]
        indexes = [
            models.Index(fields=["job_requirement", "follow_up_date"]),
            models.Index(fields=["company", "follow_up_date"]),
            models.Index(fields=["expected_result_date"]),
            models.Index(fields=["next_follow_up_date"]),
        ]

    def __str__(self) -> str:
        return f"HR Follow-up for {self.company.name} on {self.job_requirement.title} ({self.follow_up_date.strftime('%Y-%m-%d')})"
