"""Student Preparation Domain Models (Phase 6 / Steps 15-23).

Authoritative GQT HRMS Workflow:
- Step 15: Resume Review (Trainer evaluation against institutional rubric)
- Step 16: Resume Improvement (Student revision cycle and monotonic re-upload)
- Step 17: Aptitude Test (Timed quantitative, logical & verbal evaluations)
- Step 18: Technical Assessment (Domain-specific coding & technical evaluations)
- Step 19: Communication Skills Training (Presentation skills & workshop attendance)
- Step 20: Grooming Session (Professional etiquette, corporate communication & dress code certification)
- Step 21: One-on-One Mock Interview (Technical, HR, and combined mock scheduling)
- Step 22: Mock Interview Feedback (Rubric scorecard, technical/communication notes & readiness recommendation)
- Step 23: Final Resume Approval Gate (Placement Head readiness certification: is_approved_for_placements=True)
"""
import uuid
from decimal import Decimal
from typing import Optional
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone
from apps.core.models import TimeStampedModel
from apps.students.models import StudentProfile, StudentResume


class ResumeReviewStatus:
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REVISION_REQUESTED = "REVISION_REQUESTED"

    CHOICES = (
        (PENDING, "Pending Review"),
        (APPROVED, "Approved by Trainer"),
        (REVISION_REQUESTED, "Revision Requested"),
    )


class ResumeReview(TimeStampedModel):
    """Institutional resume rubric review conducted by placement trainers (Step 15)."""

    resume = models.ForeignKey(
        StudentResume,
        on_delete=models.CASCADE,
        related_name="reviews",
        help_text="The specific resume version evaluated by the trainer.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="resume_reviews",
        help_text="The candidate student owning the resume.",
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conducted_resume_reviews",
        help_text="The trainer or placement officer who evaluated the resume.",
    )
    status = models.CharField(
        max_length=32,
        choices=ResumeReviewStatus.CHOICES,
        default=ResumeReviewStatus.PENDING,
        db_index=True,
        help_text="Trainer evaluation decision.",
    )
    formatting_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Visual presentation, hierarchy, and professional layout (1-10).",
    )
    technical_skills_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Technical stack accuracy, categorization, and domain relevance (1-10).",
    )
    projects_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Project descriptions, technologies used, impact, and links (1-10).",
    )
    achievements_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Academic honours, certifications, and extracurricular achievements (1-10).",
    )
    detailed_feedback = models.TextField(
        help_text="Specific, constructive feedback explaining strengths and areas for improvement.",
    )
    suggested_improvements = models.TextField(
        blank=True,
        default="",
        help_text="Actionable bullet points for the candidate to address in the next revision.",
    )
    reviewed_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
        help_text="Timestamp when the review was submitted.",
    )

    class Meta:
        db_table = "preparation_resume_review"
        ordering = ["-reviewed_at"]
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["resume", "status"]),
            models.Index(fields=["reviewed_at"]),
        ]

    def __str__(self) -> str:
        return f"Review for {self.student.roll_number} v{self.resume.version_number} [{self.status}]"

    @property
    def aggregate_score(self) -> int:
        return (
            self.formatting_score
            + self.technical_skills_score
            + self.projects_score
            + self.achievements_score
        )


class ImprovementCycleStatus:
    REVISION_PENDING = "REVISION_PENDING"
    REVISED_UPLOADED = "REVISED_UPLOADED"
    RE_REVIEWED = "RE_REVIEWED"

    CHOICES = (
        (REVISION_PENDING, "Revision Pending from Student"),
        (REVISED_UPLOADED, "Revised Resume Uploaded"),
        (RE_REVIEWED, "Re-reviewed and Verified"),
    )


class ResumeImprovementCycle(TimeStampedModel):
    """Tracks candidate iterations, student notes, and revision history (Step 16)."""

    initial_review = models.ForeignKey(
        ResumeReview,
        on_delete=models.CASCADE,
        related_name="improvement_cycles",
        help_text="The feedback review that triggered this improvement cycle.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="resume_improvement_cycles",
        help_text="The candidate student working on resume revisions.",
    )
    prior_resume = models.ForeignKey(
        StudentResume,
        on_delete=models.CASCADE,
        related_name="prior_in_cycles",
        help_text="The prior resume version that required improvement.",
    )
    improved_resume = models.ForeignKey(
        StudentResume,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="improved_in_cycles",
        help_text="The newly uploaded revision addressing the feedback.",
    )
    status = models.CharField(
        max_length=32,
        choices=ImprovementCycleStatus.CHOICES,
        default=ImprovementCycleStatus.REVISION_PENDING,
        db_index=True,
    )
    student_notes = models.TextField(
        blank=True,
        default="",
        help_text="Student's summary of changes made in the revised version.",
    )
    submitted_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when revised resume was submitted.",
    )

    class Meta:
        db_table = "preparation_resume_improvement_cycle"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "status"]),
        ]

    def __str__(self) -> str:
        return f"Cycle for {self.student.roll_number} (Review #{self.initial_review.id}) [{self.status}]"


class AssessmentTestType:
    APTITUDE = "APTITUDE"
    TECHNICAL = "TECHNICAL"

    CHOICES = (
        (APTITUDE, "Aptitude Assessment"),
        (TECHNICAL, "Technical Assessment"),
    )


class AssessmentTest(TimeStampedModel):
    """Timed aptitude and domain-specific technical assessment definitions (Steps 17 & 18)."""

    title = models.CharField(
        max_length=255,
        help_text="Title of the test (e.g. Quantitative & Logical Reasoning, Core Java Assessment).",
    )
    test_type = models.CharField(
        max_length=32,
        choices=AssessmentTestType.CHOICES,
        db_index=True,
        help_text="Category of assessment.",
    )
    domain_track = models.CharField(
        max_length=100,
        default="General",
        help_text="Sub-specialization (e.g. Quantitative, Logical, Verbal, Java, Python, SQL).",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Test overview, instructions, and syllabus coverage.",
    )
    duration_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Maximum allowed time to complete the test in minutes.",
    )
    total_marks = models.PositiveIntegerField(
        default=100,
        help_text="Maximum possible score.",
    )
    passing_marks = models.PositiveIntegerField(
        default=60,
        help_text="Minimum score required to qualify as PASSED.",
    )
    questions = models.JSONField(
        default=list,
        help_text=(
            "Structured question bank: [{'id': 1, 'question_text': '...', "
            "'options': [{'id': 'A', 'text': '...'}, ...], "
            "'correct_option_id': 'A', 'marks': 10, 'explanation': '...'}]"
        ),
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Active tests available for student scheduling/taking.",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="created_assessments",
    )

    class Meta:
        db_table = "preparation_assessment_test"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["test_type", "is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_test_type_display()}) [{self.total_marks} Marks]"


class AssessmentAttemptStatus:
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"

    CHOICES = (
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (EXPIRED, "Time Expired"),
    )


class StudentAssessmentAttempt(TimeStampedModel):
    """Candidate attempt record for aptitude and technical assessments (Steps 17 & 18)."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="assessment_attempts",
        help_text="The candidate student who took the assessment.",
    )
    test = models.ForeignKey(
        AssessmentTest,
        on_delete=models.CASCADE,
        related_name="student_attempts",
        help_text="The specific assessment test taken.",
    )
    attempt_number = models.PositiveIntegerField(
        default=1,
        help_text="Monotonic attempt counter for this student on this test.",
    )
    score = models.PositiveIntegerField(
        default=0,
        help_text="Authoritative marks obtained.",
    )
    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Percentage score obtained (0.00 to 100.00).",
    )
    passed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if score >= test.passing_marks.",
    )
    status = models.CharField(
        max_length=32,
        choices=AssessmentAttemptStatus.CHOICES,
        default=AssessmentAttemptStatus.IN_PROGRESS,
        db_index=True,
    )
    answers = models.JSONField(
        default=dict,
        help_text="Mapping of question id (as string) to student selected option id.",
    )
    started_at = models.DateTimeField(
        default=timezone.now,
        help_text="Timestamp when candidate began the assessment.",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when candidate submitted the assessment.",
    )

    class Meta:
        db_table = "preparation_assessment_attempt"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["student", "test"]),
            models.Index(fields=["test", "passed"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        res = "PASSED" if self.passed else "FAILED"
        return f"{self.student.roll_number} - {self.test.title} (Attempt #{self.attempt_number}): {self.score}/{self.test.total_marks} [{res}]"


class TrainingSessionType:
    COMMUNICATION = "COMMUNICATION"
    CORPORATE_GROOMING = "CORPORATE_GROOMING"

    CHOICES = (
        (COMMUNICATION, "Communication Skills Training"),
        (CORPORATE_GROOMING, "Corporate Grooming Session"),
    )


class TrainingSession(TimeStampedModel):
    """Institutional training workshops and corporate grooming sessions (Steps 19 & 20)."""

    title = models.CharField(
        max_length=255,
        help_text="Session title (e.g. Professional Etiquette & Dress Code, Technical Presentation).",
    )
    session_type = models.CharField(
        max_length=32,
        choices=TrainingSessionType.CHOICES,
        db_index=True,
        help_text="Type of preparation workshop.",
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conducted_training_sessions",
        help_text="The trainer leading this session.",
    )
    scheduled_at = models.DateTimeField(
        help_text="Date and time when the session is scheduled.",
    )
    venue_or_link = models.CharField(
        max_length=255,
        help_text="Physical classroom/auditorium venue or virtual meeting URL.",
    )
    description = models.TextField(
        blank=True,
        default="",
        help_text="Workshop curriculum, goals, and required materials.",
    )
    is_completed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="True if the workshop has concluded.",
    )

    class Meta:
        db_table = "preparation_training_session"
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["session_type", "is_completed"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.get_session_type_display()}) on {self.scheduled_at:%Y-%m-%d}"


class AttendanceStatus:
    ATTENDED = "ATTENDED"
    ABSENT = "ABSENT"
    EXCUSED = "EXCUSED"

    CHOICES = (
        (ATTENDED, "Attended"),
        (ABSENT, "Absent"),
        (EXCUSED, "Excused Absence"),
    )


class TrainingAttendance(TimeStampedModel):
    """Student attendance, communication scoring, and grooming certification (Steps 19 & 20)."""

    session = models.ForeignKey(
        TrainingSession,
        on_delete=models.CASCADE,
        related_name="attendances",
        help_text="The training workshop attended.",
    )
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="training_attendances",
        help_text="The student participant.",
    )
    attendance_status = models.CharField(
        max_length=32,
        choices=AttendanceStatus.CHOICES,
        default=AttendanceStatus.ATTENDED,
        db_index=True,
    )
    presentation_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="Communication and presentation evaluation score (1-10) for Step 19.",
    )
    # Step 20 Corporate Grooming Specific Criteria:
    professional_etiquette_verified = models.BooleanField(
        default=False,
        help_text="Demonstrates polite conduct, handshake, posture, and active listening.",
    )
    corporate_communication_verified = models.BooleanField(
        default=False,
        help_text="Clear articulation, email/business decorum, and professional tone.",
    )
    dress_code_verified = models.BooleanField(
        default=False,
        help_text="Conforms strictly to formal institutional interview attire.",
    )
    hr_interview_ready = models.BooleanField(
        default=False,
        help_text="Shows structured responses to standard behavioral HR questions.",
    )
    grooming_certified = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Overall corporate grooming certification granted by trainer.",
    )
    trainer_remarks = models.TextField(
        blank=True,
        default="",
        help_text="Qualitative observations and feedback from the trainer.",
    )

    class Meta:
        db_table = "preparation_training_attendance"
        ordering = ["session__scheduled_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "student"],
                name="unique_session_student_attendance",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "grooming_certified"]),
            models.Index(fields=["attendance_status"]),
        ]

    def __str__(self) -> str:
        groom_flag = " [Grooming Certified]" if self.grooming_certified else ""
        return f"{self.student.roll_number} @ {self.session.title}: {self.attendance_status}{groom_flag}"


class MockInterviewType:
    TECHNICAL = "TECHNICAL"
    HR = "HR"
    COMBINED = "COMBINED"

    CHOICES = (
        (TECHNICAL, "Technical Mock Interview"),
        (HR, "HR / Behavioral Mock Interview"),
        (COMBINED, "Combined Technical & HR Interview"),
    )


class MockInterviewStatus:
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    NO_SHOW = "NO_SHOW"

    CHOICES = (
        (SCHEDULED, "Scheduled"),
        (IN_PROGRESS, "In Progress"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
        (NO_SHOW, "Candidate No-Show"),
    )


class MockInterview(TimeStampedModel):
    """One-on-one simulated interview scheduled with industry evaluators or trainers (Step 21)."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="mock_interviews",
        help_text="The candidate student being interviewed.",
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="assigned_mock_interviews",
        help_text="The evaluator or trainer conducting the mock interview.",
    )
    scheduled_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="scheduled_mock_interviews",
        help_text="The placement staff member who scheduled the mock.",
    )
    interview_type = models.CharField(
        max_length=32,
        choices=MockInterviewType.CHOICES,
        default=MockInterviewType.COMBINED,
        db_index=True,
    )
    scheduled_at = models.DateTimeField(
        db_index=True,
        help_text="Date and time of the interview.",
    )
    meeting_link = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Video conference link or physical room number.",
    )
    status = models.CharField(
        max_length=32,
        choices=MockInterviewStatus.CHOICES,
        default=MockInterviewStatus.SCHEDULED,
        db_index=True,
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Internal scheduling notes or candidate instructions.",
    )

    class Meta:
        db_table = "preparation_mock_interview"
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["student", "status"]),
            models.Index(fields=["evaluator", "status"]),
            models.Index(fields=["scheduled_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.get_interview_type_display()} for {self.student.roll_number} with {self.evaluator.full_name} [{self.status}]"


class MockReadinessRecommendation:
    READY_FOR_PLACEMENTS = "READY_FOR_PLACEMENTS"
    NEEDS_PRACTICE = "NEEDS_PRACTICE"
    NOT_READY = "NOT_READY"

    CHOICES = (
        (READY_FOR_PLACEMENTS, "Ready for Placement Drives"),
        (NEEDS_PRACTICE, "Needs Additional Practice / Minor Improvements"),
        (NOT_READY, "Not Ready — Requires Remedial Training"),
    )


class MockInterviewEvaluation(TimeStampedModel):
    """Detailed rubric scorecard and qualitative feedback from the mock interview (Step 22)."""

    mock_interview = models.OneToOneField(
        MockInterview,
        on_delete=models.CASCADE,
        related_name="evaluation",
        help_text="The mock interview session evaluated.",
    )
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_mock_evaluations",
        help_text="The evaluator who submitted this scorecard.",
    )
    technical_competence_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Depth of domain knowledge, coding accuracy, and system fundamentals (1-10).",
    )
    problem_solving_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Analytical thinking, approach to edge cases, and algorithmic clarity (1-10).",
    )
    communication_clarity_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Verbal fluency, active listening, and structured explanation (1-10).",
    )
    professional_readiness_score = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        default=7,
        help_text="Professional composure, demeanor, body language, and confidence (1-10).",
    )
    total_score = models.PositiveIntegerField(
        default=28,
        help_text="Aggregate scorecard total (out of 40).",
    )
    technical_feedback = models.TextField(
        help_text="Detailed assessment of domain knowledge, strengths, and concept gaps.",
    )
    communication_feedback = models.TextField(
        help_text="Assessment of verbal fluency, voice modulation, and listening skills.",
    )
    improvement_suggestions = models.TextField(
        help_text="Actionable steps the candidate must undertake before company interviews.",
    )
    readiness_recommendation = models.CharField(
        max_length=32,
        choices=MockReadinessRecommendation.CHOICES,
        default=MockReadinessRecommendation.READY_FOR_PLACEMENTS,
        db_index=True,
    )
    evaluated_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    class Meta:
        db_table = "preparation_mock_interview_evaluation"
        ordering = ["-evaluated_at"]
        indexes = [
            models.Index(fields=["readiness_recommendation"]),
            models.Index(fields=["total_score"]),
        ]

    def __str__(self) -> str:
        return f"Scorecard for Mock #{self.mock_interview_id}: {self.total_score}/40 [{self.readiness_recommendation}]"

    def save(self, *args, **kwargs):
        self.total_score = (
            self.technical_competence_score
            + self.problem_solving_score
            + self.communication_clarity_score
            + self.professional_readiness_score
        )
        super().save(*args, **kwargs)


class PlacementReadinessStatus:
    CERTIFIED = "CERTIFIED"
    REJECTED = "REJECTED"

    CHOICES = (
        (CERTIFIED, "Certified Ready for Placement Drives"),
        (REJECTED, "Returned for Further Preparation"),
    )


class PlacementReadinessCertification(TimeStampedModel):
    """Authoritative gate certifying that a candidate and resume are ready for company drives (Step 23).

    Mandatory Gate: Phase 7 (Workflow Steps 24-28: Candidate Submission & Profile Dispatch)
    is strictly blocked unless a student has an active certified readiness record
    with is_approved_for_placements = True.
    """

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="placement_certifications",
        help_text="The candidate student receiving readiness certification.",
    )
    approved_resume = models.ForeignKey(
        StudentResume,
        on_delete=models.PROTECT,
        related_name="certified_placements",
        help_text="The specific, certified resume version locked for company submissions.",
    )
    is_approved_for_placements = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Crucial gate flag unlocking Phase 7 company profile dispatch.",
    )
    status = models.CharField(
        max_length=32,
        choices=PlacementReadinessStatus.CHOICES,
        default=PlacementReadinessStatus.CERTIFIED,
        db_index=True,
    )
    certified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="certified_placement_readinesses",
        help_text="Placement Head or Admin authorizing readiness certification.",
    )
    certified_at = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )
    readiness_summary = models.JSONField(
        default=dict,
        help_text="Snapshot of readiness checks: resume review, assessments, grooming, mock evaluation.",
    )
    notes = models.TextField(
        blank=True,
        default="",
        help_text="Placement Head certification justification or directive.",
    )

    class Meta:
        db_table = "preparation_placement_readiness"
        ordering = ["-certified_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "approved_resume"],
                name="unique_student_resume_placement_cert",
            ),
        ]
        indexes = [
            models.Index(fields=["student", "is_approved_for_placements"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self) -> str:
        cert_label = "APPROVED" if self.is_approved_for_placements else "REJECTED"
        return f"{self.student.roll_number} Resume v{self.approved_resume.version_number} [{cert_label}] by {self.certified_by.full_name}"
