"""Database query selectors for the Students and Eligibility Engine domain."""
from typing import Optional
from django.db.models import QuerySet, Q
from apps.students.models import (
    StudentProfile,
    StudentResume,
    JobPublication,
    StudentApplication,
    EligibilityEvaluation,
    CandidateCohort,
    CohortMember,
)


def get_student_profile_by_user(user) -> Optional[StudentProfile]:
    """Retrieve the student profile linked to a user account."""
    return StudentProfile.objects.filter(user=user).select_related("user").first()


def get_student_profile_by_id(profile_id: str) -> Optional[StudentProfile]:
    """Retrieve student profile by its UUID primary key."""
    return StudentProfile.objects.filter(id=profile_id).select_related("user").first()


def list_student_profiles(
    search: Optional[str] = None,
    department: Optional[str] = None,
    graduation_year: Optional[int] = None,
    min_cgpa: Optional[float] = None,
    is_verified: Optional[bool] = None,
) -> QuerySet[StudentProfile]:
    """List student profiles with optional filters."""
    qs = StudentProfile.objects.select_related("user").all()

    if search:
        search = search.strip()
        qs = qs.filter(
            Q(roll_number__icontains=search)
            | Q(institutional_email__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(college_name__icontains=search)
        )
    if department:
        qs = qs.filter(department__icontains=department.strip())
    if graduation_year:
        qs = qs.filter(graduation_year=graduation_year)
    if min_cgpa is not None:
        qs = qs.filter(cgpa__gte=min_cgpa)
    if is_verified is not None:
        qs = qs.filter(is_verified_by_placement=is_verified)

    return qs.order_by("-created_at")


def get_active_resume(student_profile: StudentProfile) -> Optional[StudentResume]:
    """Retrieve the active resume for a student profile."""
    return (
        StudentResume.objects.filter(student=student_profile, is_current=True)
        .order_by("-version_number")
        .first()
    )


def get_resume_by_id(resume_id: str) -> Optional[StudentResume]:
    """Retrieve a specific resume version by its ID."""
    return (
        StudentResume.objects.filter(id=resume_id)
        .select_related("student", "student__user")
        .first()
    )


def list_resumes_for_student(student_profile: StudentProfile) -> QuerySet[StudentResume]:
    """List all resume revisions uploaded by a student in descending version order."""
    return StudentResume.objects.filter(student=student_profile).order_by("-version_number")


def list_publications_for_job(job_id: str) -> QuerySet[JobPublication]:
    """List all broadcast publications for a given job requirement."""
    return (
        JobPublication.objects.filter(job_requirement_id=job_id)
        .select_related("job_requirement", "job_requirement__company", "creative_version", "published_by")
        .order_by("-created_at")
    )


def get_publication_by_id(pub_id: str) -> Optional[JobPublication]:
    """Retrieve a specific publication by its ID."""
    return (
        JobPublication.objects.filter(id=pub_id)
        .select_related("job_requirement", "job_requirement__company", "creative_version", "published_by")
        .first()
    )


def get_application_for_student_and_job(
    student_profile: StudentProfile, job_id: str
) -> Optional[StudentApplication]:
    """Retrieve an application for a specific student and job."""
    return (
        StudentApplication.objects.filter(student=student_profile, job_requirement_id=job_id)
        .select_related("student", "job_requirement", "resume", "eligibility_evaluation")
        .first()
    )


def list_applications_for_job(
    job_id: str, status: Optional[str] = None
) -> QuerySet[StudentApplication]:
    """List student applications for a job requirement."""
    qs = (
        StudentApplication.objects.filter(job_requirement_id=job_id)
        .select_related("student", "student__user", "resume", "eligibility_evaluation")
    )
    if status:
        qs = qs.filter(status=status)
    return qs.order_by("-applied_at")


def get_cohort_for_job(job_id: str) -> Optional[CandidateCohort]:
    """Retrieve the candidate cohort associated with an approved job."""
    return (
        CandidateCohort.objects.filter(job_requirement_id=job_id)
        .select_related("job_requirement", "finalized_by")
        .first()
    )


def list_cohort_members(
    cohort_id: str, is_eligible: Optional[bool] = None
) -> QuerySet[CohortMember]:
    """List members within a candidate cohort."""
    qs = (
        CohortMember.objects.filter(cohort_id=cohort_id)
        .select_related(
            "student",
            "student__user",
            "application",
            "application__resume",
            "override_by",
        )
    )
    if is_eligible is not None:
        qs = qs.filter(is_eligible=is_eligible)
    return qs.order_by("student__roll_number")
