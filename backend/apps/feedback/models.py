"""Feedback Collection Domain Models (Phase 9).

Authoritative GQT HRMS Workflow Phase 9 Categories:
- A. Student Feedback: Interview Experience, Technical Questions, Difficulty, Suggestions
- B. HR Feedback: Candidate Quality, Technical Skills, Communication Skills, Hiring Satisfaction
- C. Trainer Feedback: Student Readiness, Training Effectiveness, Areas for Improvement
"""
import uuid
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from apps.core.models import TimeStampedModel
from apps.crm.models import Company, HRContact
from apps.interviews.models import InterviewRound, InterviewSchedule
from apps.jobs.models import JobRequirement
from apps.preparation.models import TrainingSession
from apps.students.models import StudentProfile


class DifficultyLevel:
    """Difficulty rating choices for student interview feedback."""

    EASY = "EASY"
    MEDIUM = "MEDIUM"
    HARD = "HARD"
    VERY_HARD = "VERY_HARD"

    CHOICES = (
        (EASY, "Easy — Straightforward questions"),
        (MEDIUM, "Medium — Balanced conceptual & practical"),
        (HARD, "Hard — Advanced problem solving & in-depth"),
        (VERY_HARD, "Very Hard — Highly challenging / competitive"),
    )


class CandidateQuality:
    """Candidate caliber rating choices for corporate HR feedback."""

    POOR = "POOR"
    FAIR = "FAIR"
    GOOD = "GOOD"
    EXCELLENT = "EXCELLENT"

    CHOICES = (
        (POOR, "Poor — Below hiring expectations"),
        (FAIR, "Fair — Meets basic criteria but lacks depth"),
        (GOOD, "Good — Competent and well-prepared"),
        (EXCELLENT, "Excellent — Exceeds hiring benchmark"),
    )


class StudentReadiness:
    """Candidate placement readiness choices for trainer feedback."""

    NOT_READY = "NOT_READY"
    NEEDS_PRACTICE = "NEEDS_PRACTICE"
    READY = "READY"
    HIGHLY_READY = "HIGHLY_READY"

    CHOICES = (
        (NOT_READY, "Not Ready — Requires significant foundational coaching"),
        (NEEDS_PRACTICE, "Needs Practice — Solid fundamentals, needs mock polish"),
        (READY, "Ready — Fully qualified for campus placement drives"),
        (HIGHLY_READY, "Highly Ready — Top performer / Day-1 offer candidate"),
    )


class StudentFeedback(TimeStampedModel):
    """Student candidate feedback on corporate interview experience (Phase 9 Category A)."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="student_feedback",
        help_text="The student submitting the interview feedback.",
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="student_feedback",
        help_text="The corporate hiring partner conducting the interview.",
    )
    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_feedback",
        help_text="The recruitment job requirement drive linked to the interview.",
    )
    interview_schedule = models.ForeignKey(
        InterviewSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_feedback",
        help_text="The specific scheduled interview instance.",
    )
    interview_round = models.ForeignKey(
        InterviewRound,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="student_feedback",
        help_text="The specific interview round evaluated (optional).",
    )
    interview_experience = models.TextField(
        help_text="Candidate description of the overall interview experience, atmosphere, and organization.",
    )
    technical_questions = models.TextField(
        blank=True,
        default="",
        help_text="Specific technical, algorithmic, system design, or problem-solving questions asked.",
    )
    difficulty = models.CharField(
        max_length=20,
        choices=DifficultyLevel.CHOICES,
        default=DifficultyLevel.MEDIUM,
        db_index=True,
        help_text="Candidate assessment of the drive's difficulty level.",
    )
    suggestions = models.TextField(
        blank=True,
        default="",
        help_text="Actionable suggestions for future candidates, curriculum updates, or drive coordination.",
    )
    is_anonymous = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether candidate identity should be suppressed in aggregate reporting.",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_student_feedback",
        help_text="The authenticated user who recorded this submission.",
    )

    class Meta:
        db_table = "feedback_student_feedback"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "company"]),
            models.Index(fields=["company", "difficulty"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "interview_schedule"],
                name="unique_student_feedback_per_schedule",
                condition=models.Q(interview_schedule__isnull=False),
            )
        ]

    def __str__(self) -> str:
        return f"StudentFeedback({self.student.user.full_name or self.student.roll_number} -> {self.company.name})"


class HRFeedback(TimeStampedModel):
    """Corporate HR recruiter feedback on candidate cohort and hiring satisfaction (Phase 9 Category B)."""

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="hr_feedback",
        help_text="The corporate hiring entity providing the feedback.",
    )
    hr_contact = models.ForeignKey(
        HRContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_feedback",
        help_text="The corporate HR recruiter lead communicating feedback.",
    )
    job_requirement = models.ForeignKey(
        JobRequirement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_feedback",
        help_text="The recruitment job requirement evaluated.",
    )
    candidate = models.ForeignKey(
        StudentProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="hr_candidate_feedback",
        help_text="Specific evaluated candidate (null indicates overall drive / cohort feedback).",
    )
    candidate_quality = models.CharField(
        max_length=20,
        choices=CandidateQuality.CHOICES,
        default=CandidateQuality.GOOD,
        db_index=True,
        help_text="Assessment of student caliber, domain foundation, and problem solving.",
    )
    candidate_quality_remarks = models.TextField(
        blank=True,
        default="",
        help_text="Qualitative observations regarding candidate caliber.",
    )
    technical_skills_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Numerical rating (1-5) of technical proficiency, code quality, and engineering concepts.",
    )
    technical_skills_remarks = models.TextField(
        blank=True,
        default="",
        help_text="Recruiter remarks on technical gaps, strengths, and stack proficiency.",
    )
    communication_skills_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,
        help_text="Numerical rating (1-5) of verbal articulation, confidence, and professional conduct.",
    )
    communication_skills_remarks = models.TextField(
        blank=True,
        default="",
        help_text="Recruiter remarks on candidate communication and presentation.",
    )
    hiring_satisfaction_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=4,
        help_text="Overall recruiter satisfaction with the campus drive process and hiring outcome (1-5).",
    )
    hiring_satisfaction_remarks = models.TextField(
        blank=True,
        default="",
        help_text="Institutional feedback, drive coordination remarks, and future hiring intent.",
    )
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_hr_feedback",
        help_text="The authenticated user who logged this HR feedback entry.",
    )

    class Meta:
        db_table = "feedback_hr_feedback"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "candidate_quality"]),
            models.Index(fields=["hiring_satisfaction_rating"]),
            models.Index(fields=["created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company", "job_requirement", "candidate"],
                name="unique_hr_feedback_per_candidate_job",
                condition=models.Q(candidate__isnull=False, job_requirement__isnull=False),
            )
        ]

    def __str__(self) -> str:
        cand = f" - {self.candidate.user.full_name}" if self.candidate else " (Cohort)"
        return f"HRFeedback({self.company.name}{cand})"


class TrainerFeedback(TimeStampedModel):
    """Placement & technical trainer feedback on student preparation and areas for improvement (Phase 9 Category C)."""

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="trainer_feedback",
        help_text="The evaluated candidate student.",
    )
    training_session = models.ForeignKey(
        TrainingSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="trainer_feedback",
        help_text="The specific workshop or grooming session evaluated.",
    )
    student_readiness = models.CharField(
        max_length=20,
        choices=StudentReadiness.CHOICES,
        default=StudentReadiness.READY,
        db_index=True,
        help_text="Trainer assessment of candidate placement readiness.",
    )
    student_readiness_remarks = models.TextField(
        blank=True,
        default="",
        help_text="Detailed observations on technical preparedness and mock performance.",
    )
    training_effectiveness_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=4,
        help_text="Trainer assessment of student curriculum absorption and responsiveness (1-5).",
    )
    training_effectiveness_remarks = models.TextField(
        blank=True,
        default="",
        help_text="Observations on topic mastery and engagement.",
    )
    areas_for_improvement = models.TextField(
        help_text="Concrete areas for student improvement (e.g. Data Structures, Communication, Aptitude speed).",
    )
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="submitted_trainer_feedback",
        help_text="The trainer or mock evaluator providing this assessment.",
    )

    class Meta:
        db_table = "feedback_trainer_feedback"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["student", "student_readiness"]),
            models.Index(fields=["trainer", "created_at"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "training_session", "trainer"],
                name="unique_trainer_feedback_per_session",
                condition=models.Q(training_session__isnull=False),
            )
        ]

    def __str__(self) -> str:
        return f"TrainerFeedback({self.trainer.full_name} -> {self.student.user.full_name or self.student.roll_number})"
