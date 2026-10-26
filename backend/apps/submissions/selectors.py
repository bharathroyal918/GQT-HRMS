"""Reusable Query Selectors for Candidate Submissions & Profile Dispatch (Phase 7)."""
from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from apps.jobs.models import JobRequirement
from apps.students.models import StudentProfile, StudentApplication, StudentApplicationStatus, CandidateCohort
from apps.preparation.models import PlacementReadinessCertification, PlacementReadinessStatus
from apps.submissions.models import SubmissionPackage, CandidateSubmission, SubmissionPackageStatus


def get_eligible_candidates_for_job(job_requirement_id: str) -> Dict[str, Any]:
    """Retrieve candidate pool for an approved job requirement, evaluating eligibility and Step 23 readiness certification.

    Returns:
        Dict containing job details and candidate readiness list.
    """
    try:
        job = JobRequirement.objects.select_related("company", "hr_contact").get(id=job_requirement_id)
    except JobRequirement.DoesNotExist:
        return {"job": None, "candidates": [], "total_eligible": 0, "total_certified": 0}

    # Query active applications for this job
    applications = StudentApplication.objects.filter(
        job_requirement=job,
        status__in=[
            StudentApplicationStatus.ELIGIBLE,
            StudentApplicationStatus.OVERRIDDEN,
        ],
    ).select_related("student__user", "resume")

    # If cohort exists, query eligible cohort members
    cohort = CandidateCohort.objects.filter(job_requirement=job, is_locked=True).first()
    cohort_student_ids = set()
    if cohort:
        cohort_student_ids = set(
            cohort.members.filter(is_eligible=True).values_list("student_id", flat=True)
        )

    # Already submitted candidate IDs for this job requirement (in active non-cancelled packages)
    submitted_student_ids = set(
        CandidateSubmission.objects.filter(
            package__job_requirement=job,
        ).exclude(
            package__status=SubmissionPackageStatus.CANCELLED,
        ).values_list("student_id", flat=True)
    )

    candidates_list = []
    total_eligible = 0
    total_certified = 0

    for app in applications:
        student = app.student
        total_eligible += 1

        # Check Step 23 Placement Readiness Certification Gate
        cert = PlacementReadinessCertification.objects.filter(
            student=student,
            is_approved_for_placements=True,
            status=PlacementReadinessStatus.CERTIFIED,
        ).select_related("approved_resume").order_by("-certified_at").first()

        has_certification = cert is not None and cert.approved_resume is not None
        if has_certification:
            total_certified += 1

        is_already_submitted = student.id in submitted_student_ids
        is_in_locked_cohort = student.id in cohort_student_ids

        candidates_list.append({
            "student_id": str(student.id),
            "student_name": student.user.full_name or student.user.email,
            "roll_number": student.roll_number,
            "institutional_email": student.institutional_email,
            "phone_number": student.phone_number,
            "college_name": student.college_name,
            "department": student.department,
            "graduation_year": student.graduation_year,
            "cgpa": float(student.cgpa) if student.cgpa else None,
            "technical_skills": getattr(student, "technical_skills", "") or "",
            "application_id": str(app.id),
            "application_status": app.status,
            "is_in_locked_cohort": is_in_locked_cohort,
            "has_readiness_certification": has_certification,
            "certification_id": str(cert.id) if cert else None,
            "approved_resume_id": str(cert.approved_resume.id) if (cert and cert.approved_resume) else None,
            "approved_resume_version": cert.approved_resume.version_number if (cert and cert.approved_resume) else None,
            "approved_resume_file_name": cert.approved_resume.file_name if (cert and cert.approved_resume) else None,
            "approved_resume_sha256": cert.approved_resume.sha256_hash if (cert and cert.approved_resume) else None,
            "is_already_submitted": is_already_submitted,
            "can_be_submitted": has_certification and not is_already_submitted,
        })

    return {
        "job_id": str(job.id),
        "job_title": job.title,
        "company_name": job.company.name,
        "hr_contact_name": job.hr_contact.name if job.hr_contact else "",
        "hr_contact_email": job.hr_contact.email if job.hr_contact else "",
        "candidates": candidates_list,
        "total_eligible": total_eligible,
        "total_certified": total_certified,
    }


def get_submission_packages(
    job_requirement_id: Optional[str] = None,
    company_id: Optional[str] = None,
    status: Optional[str] = None,
) -> QuerySet[SubmissionPackage]:
    """Retrieve filtered submission packages with prefetched relationships."""
    qs = SubmissionPackage.objects.select_related(
        "job_requirement",
        "company",
        "hr_contact",
        "created_by",
        "dispatched_by",
        "acknowledged_by",
    ).prefetch_related(
        "candidates__student__user",
        "candidates__submitted_resume",
    ).all()

    if job_requirement_id:
        qs = qs.filter(job_requirement_id=job_requirement_id)
    if company_id:
        qs = qs.filter(company_id=company_id)
    if status:
        qs = qs.filter(status=status)

    return qs


def get_submission_package_by_id(package_id: str) -> Optional[SubmissionPackage]:
    """Retrieve a single submission package by UUID with all related records."""
    try:
        return SubmissionPackage.objects.select_related(
            "job_requirement",
            "company",
            "hr_contact",
            "cohort",
            "created_by",
            "dispatched_by",
            "acknowledged_by",
        ).prefetch_related(
            "candidates__student__user",
            "candidates__application",
            "candidates__readiness_certification",
            "candidates__submitted_resume",
            "dispatch_logs__dispatched_by",
        ).get(id=package_id)
    except SubmissionPackage.DoesNotExist:
        return None


def get_student_submissions(student_user) -> QuerySet[CandidateSubmission]:
    """Retrieve submission records for an individual student (strictly object-level isolated)."""
    return CandidateSubmission.objects.filter(
        student__user=student_user,
    ).select_related(
        "package__job_requirement",
        "package__company",
        "submitted_resume",
    ).order_by("-created_at")
