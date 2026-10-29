"""Domain service functions for Student Registration, Ingestion, and Eligibility Engine."""
import logging
import re
import uuid
from decimal import Decimal
from typing import Dict, Any, List, Optional, Tuple
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import RoleCatalog, User
from apps.accounts.services import assign_roles_to_user, log_security_event
from apps.core.models import AuditLog
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.creatives.models import CreativeAssetVersion
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
from apps.students.validators import validate_resume_pdf

logger = logging.getLogger("apps.students")


# ==============================================================================
# Step 10: Publish Job Notification Services
# ==============================================================================

def publish_job_notification(
    job_requirement_id: str,
    channel: str,
    target_audience: str,
    creative_version_id: Optional[str] = None,
    subject: Optional[str] = None,
    message_body: Optional[str] = None,
    published_by: Optional[User] = None,
    request=None,
) -> JobPublication:
    """Create and dispatch an internal broadcast notification for an approved job requirement."""
    try:
        job = JobRequirement.objects.select_related("company").get(id=job_requirement_id)
    except JobRequirement.DoesNotExist:
        raise ValidationError(f"Job requirement with ID {job_requirement_id} not found.")

    # Rule: Only APPROVED job requirements can be published (Workflow Step 10)
    if job.status != JobRequirementStatus.APPROVED:
        raise ValidationError(
            f"Cannot publish job opportunity in '{job.status}' status. "
            f"Only '{JobRequirementStatus.APPROVED}' requirements certified by the Placement Head can be broadcast."
        )

    if job.is_archived:
        raise ValidationError("Cannot broadcast an archived job requirement.")

    # Validate attached creative asset version if provided
    creative_version = None
    if creative_version_id:
        try:
            creative_version = CreativeAssetVersion.objects.select_related("request").get(
                id=creative_version_id
            )
            if str(creative_version.request.job_requirement_id) != str(job.id):
                raise ValidationError("Attached creative asset belongs to a different job requirement.")
            if not creative_version.is_approved:
                raise ValidationError(
                    "Attached creative asset has not received final Step 9 sign-off approval."
                )
        except CreativeAssetVersion.DoesNotExist:
            raise ValidationError(f"Creative asset version with ID {creative_version_id} not found.")

    # Build default subject and body if not provided
    final_subject = (
        subject.strip()
        if subject and subject.strip()
        else f"Campus Drive Notice: {job.title} at {job.company.name}"
    )

    if not message_body or not message_body.strip():
        salary_info = (
            f"CTC: {job.salary_currency} {job.min_salary} - {job.max_salary}"
            if job.min_salary and job.max_salary
            else "Compensation: As per corporate standards"
        )
        final_message = (
            f"Placement Opportunity Alert: {job.title} with {job.company.name}.\n"
            f"Location: {job.location} ({job.get_work_arrangement_display()})\n"
            f"{salary_info}\n"
            f"Registration Cutoff: {job.registration_deadline.strftime('%d-%b-%Y %H:%M')}\n"
            f"Eligible Candidates: Please register via student portal before deadline."
        )
    else:
        final_message = message_body.strip()

    # Create publication record
    pub = JobPublication.objects.create(
        job_requirement=job,
        creative_version=creative_version,
        channel=channel,
        status=JobPublicationStatus.DISPATCHED,
        target_audience=target_audience.strip(),
        subject=final_subject,
        message_body=final_message,
        dispatched_at=timezone.now(),
        provider_message_id=f"gqt_{channel.lower()}_{uuid.uuid4().hex[:12]}",
        published_by=published_by,
    )

    # In-portal announcements are immediately available
    if channel == JobPublicationChannel.PORTAL:
        pub.status = JobPublicationStatus.DELIVERED
        pub.delivered_at = timezone.now()
        pub.save(update_fields=["status", "delivered_at"])

    # Audit event
    AuditLog.objects.create(
        user=published_by,
        action="JOB_NOTIFICATION_PUBLISHED",
        resource_type="students.JobPublication",
        resource_id=str(pub.id),
        changes={
            "job_id": str(job.id),
            "job_title": job.title,
            "channel": channel,
            "status": pub.status,
            "target_audience": target_audience,
            "creative_version_id": str(creative_version.id) if creative_version else None,
        },
    )

    return pub


def retry_job_publication(
    publication_id: str,
    user: Optional[User] = None,
    request=None,
) -> JobPublication:
    """Re-attempt dispatch of a failed or pending publication."""
    try:
        pub = JobPublication.objects.select_related("job_requirement").get(id=publication_id)
    except JobPublication.DoesNotExist:
        raise ValidationError(f"Publication record {publication_id} not found.")

    pub.retry_count += 1
    pub.status = JobPublicationStatus.DISPATCHED
    pub.dispatched_at = timezone.now()
    pub.failure_reason = ""
    pub.provider_message_id = f"gqt_retry_{pub.channel.lower()}_{uuid.uuid4().hex[:12]}"
    pub.save(update_fields=["retry_count", "status", "dispatched_at", "failure_reason", "provider_message_id"])

    AuditLog.objects.create(
        user=user,
        action="JOB_PUBLICATION_RETRIED",
        resource_type="students.JobPublication",
        resource_id=str(pub.id),
        changes={"retry_count": pub.retry_count, "channel": pub.channel},
    )

    return pub


# ==============================================================================
# Step 11: Student Registration Services
# ==============================================================================

@transaction.atomic
def register_student(
    email: str,
    password: str,
    roll_number: str,
    first_name: str,
    last_name: str,
    college_name: str,
    degree: str,
    department: str,
    graduation_year: int,
    cgpa: Decimal,
    active_backlogs: int = 0,
    history_backlogs: int = 0,
    phone_number: str = "",
    alternate_phone: str = "",
    request=None,
) -> Tuple[User, StudentProfile]:
    """Register and onboard a new student account with normalized email & roll number uniqueness."""
    norm_email = email.lower().strip()
    norm_roll = roll_number.upper().strip()

    # Server-side validation of uniqueness
    if User.objects.filter(email=norm_email).exists():
        raise ValidationError({"email": "An account with this institutional email already exists."})

    if StudentProfile.objects.filter(roll_number__iexact=norm_roll).exists():
        raise ValidationError({"roll_number": "A student profile with this roll number already exists."})

    if StudentProfile.objects.filter(institutional_email__iexact=norm_email).exists():
        raise ValidationError({"institutional_email": "A student profile with this institutional email already exists."})

    # Validate CGPA boundary
    cgpa_dec = Decimal(str(cgpa))
    if cgpa_dec < Decimal("0.00") or cgpa_dec > Decimal("10.00"):
        raise ValidationError({"cgpa": "CGPA must be between 0.00 and 10.00 on a 10.0 scale."})

    # Create User account with STUDENT role
    user = User.objects.create_user(
        email=norm_email,
        password=password,
        first_name=first_name.strip(),
        last_name=last_name.strip(),
    )

    # Assign STUDENT role
    assign_roles_to_user(
        target_user=user,
        role_codes=[RoleCatalog.STUDENT],
        assigned_by=user,
        request=request,
    )

    # Create StudentProfile
    profile = StudentProfile.objects.create(
        user=user,
        roll_number=norm_roll,
        institutional_email=norm_email,
        college_name=college_name.strip(),
        degree=degree.strip(),
        department=department.strip(),
        graduation_year=int(graduation_year),
        cgpa=cgpa_dec,
        active_backlogs=max(0, int(active_backlogs)),
        history_backlogs=max(0, int(history_backlogs)),
        phone_number=phone_number.strip(),
        alternate_phone=alternate_phone.strip(),
    )

    AuditLog.objects.create(
        user=user,
        action="STUDENT_REGISTERED",
        resource_type="students.StudentProfile",
        resource_id=str(profile.id),
        changes={
            "user_id": str(user.id),
            "roll_number": norm_roll,
            "institutional_email": norm_email,
            "department": profile.department,
            "graduation_year": profile.graduation_year,
        },
    )

    return user, profile


# ==============================================================================
# Step 12: Collect Student Profile & Resume Services
# ==============================================================================

@transaction.atomic
def upload_student_resume(
    student_profile: StudentProfile,
    file_obj,
    user: Optional[User] = None,
    request=None,
) -> StudentResume:
    """Validate PDF magic bytes, compute cryptographic hash, and save with monotonic versioning."""
    # Enforces size limit and b'%PDF-' signature
    sha256_hash = validate_resume_pdf(file_obj)

    # Compute next monotonic version number
    current_highest = (
        student_profile.resumes.order_by("-version_number").first()
    )
    next_version = (current_highest.version_number + 1) if current_highest else 1

    # Mark existing resumes as non-current
    student_profile.resumes.filter(is_current=True).update(is_current=False)

    resume = StudentResume.objects.create(
        student=student_profile,
        version_number=next_version,
        file=file_obj,
        file_name=getattr(file_obj, "name", f"resume_v{next_version}.pdf"),
        file_size_bytes=file_obj.size,
        sha256_hash=sha256_hash,
        is_current=True,
    )

    AuditLog.objects.create(
        user=user or student_profile.user,
        action="STUDENT_RESUME_UPLOADED",
        resource_type="students.StudentResume",
        resource_id=str(resume.id),
        changes={
            "student_id": str(student_profile.id),
            "version_number": resume.version_number,
            "file_size_bytes": resume.file_size_bytes,
            "sha256_hash": resume.sha256_hash,
        },
    )

    return resume


def update_student_profile(
    student_profile: StudentProfile,
    data: Dict[str, Any],
    user: Optional[User] = None,
    request=None,
) -> StudentProfile:
    """Update student academic profile details with validation."""
    allowed_fields = [
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

    changes = {}
    for field in allowed_fields:
        if field in data:
            val = data[field]
            if field == "cgpa":
                val = Decimal(str(val))
                if val < Decimal("0.00") or val > Decimal("10.00"):
                    raise ValidationError("CGPA must be between 0.00 and 10.00.")
            elif field in ("active_backlogs", "history_backlogs", "graduation_year"):
                val = int(val)

            old_val = getattr(student_profile, field)
            if old_val != val:
                changes[field] = {"old": str(old_val), "new": str(val)}
                setattr(student_profile, field, val)

    if changes:
        student_profile.save()
        AuditLog.objects.create(
            user=user or student_profile.user,
            action="STUDENT_PROFILE_UPDATED",
            resource_type="students.StudentProfile",
            resource_id=str(student_profile.id),
            changes=changes,
        )

    return student_profile


# ==============================================================================
# Step 13: Eligibility Verification Engine Services
# ==============================================================================

def evaluate_student_eligibility(
    job_requirement: JobRequirement,
    student_profile: StudentProfile,
) -> Dict[str, Any]:
    """Deterministic, auditable evaluation of student academic profile against approved job criteria.

    Evaluates 4 factors:
    1. Branch / Discipline matching.
    2. CGPA threshold comparison using Decimal arithmetic.
    3. Active backlogs cutoff comparison.
    4. Passing out batch / Graduation year alignment.

    Returns:
        Structured evaluation dict with status, criterion-by-criterion explanations, and criteria snapshot.
    """
    criteria_text = (job_requirement.eligibility_criteria or "").lower()
    details: List[Dict[str, Any]] = []
    is_overall_eligible = True

    # 1. Branch / Discipline check
    # Check if criteria restricts departments
    student_dept = student_profile.department.strip()
    branch_check = {
        "criterion": "Discipline / Branch",
        "student_value": student_dept,
        "required_value": "Eligible branches specified in JD",
        "passed": True,
        "details": f"Discipline '{student_dept}' satisfies candidate intake requirements.",
    }

    # Inspect if specific branches are required in criteria_text
    known_branches = ["computer science", "information science", "electronics", "electrical", "mechanical", "civil"]
    mentioned_branches = [b for b in known_branches if b in criteria_text]
    if mentioned_branches:
        if any(b in student_dept.lower() for b in mentioned_branches):
            branch_check["passed"] = True
            branch_check["details"] = f"Discipline '{student_dept}' matches allowed branches ({', '.join(mentioned_branches)})."
        else:
            branch_check["passed"] = False
            branch_check["required_value"] = ", ".join(mentioned_branches).title()
            branch_check["details"] = f"Discipline '{student_dept}' is not in allowed branches ({', '.join(mentioned_branches)})."
            is_overall_eligible = False

    details.append(branch_check)

    # 2. CGPA Cutoff check (using exact Decimal comparison)
    min_cgpa_req = job_requirement.min_cgpa
    cgpa_check = {
        "criterion": "Minimum Academic CGPA",
        "student_value": str(student_profile.cgpa),
        "required_value": f">= {min_cgpa_req}" if min_cgpa_req else "No minimum threshold",
        "passed": True,
        "details": f"Student CGPA {student_profile.cgpa} meets requirement.",
    }

    if min_cgpa_req is not None:
        if student_profile.cgpa < min_cgpa_req:
            cgpa_check["passed"] = False
            cgpa_check["details"] = f"Student CGPA {student_profile.cgpa} is below minimum requirement of {min_cgpa_req}."
            is_overall_eligible = False

    details.append(cgpa_check)

    # 3. Active Backlogs Cutoff check
    # Parse backlogs allowance from criteria_text or default to 0
    max_backlogs_allowed = 0
    if "backlog" in criteria_text:
        match = re.search(r"(\d+)\s*(?:active\s*)?backlog", criteria_text)
        if match:
            max_backlogs_allowed = int(match.group(1))

    backlog_check = {
        "criterion": "Active Arrears / Backlogs",
        "student_value": str(student_profile.active_backlogs),
        "required_value": f"<= {max_backlogs_allowed} active backlog(s)",
        "passed": True,
        "details": f"Student has {student_profile.active_backlogs} standing backlog(s) (Limit: {max_backlogs_allowed}).",
    }

    if student_profile.active_backlogs > max_backlogs_allowed:
        backlog_check["passed"] = False
        backlog_check["details"] = (
            f"Student active backlogs ({student_profile.active_backlogs}) exceeds allowable limit of {max_backlogs_allowed}."
        )
        is_overall_eligible = False

    details.append(backlog_check)

    # 4. Graduation Year / Batch check
    # Check if a specific 4-digit year is specified in criteria or drive date
    target_year = None
    year_match = re.search(r"\b(202[0-9])\b", criteria_text)
    if year_match:
        target_year = int(year_match.group(1))
    elif job_requirement.interview_date:
        target_year = job_requirement.interview_date.year

    year_check = {
        "criterion": "Graduation Passing Batch",
        "student_value": str(student_profile.graduation_year),
        "required_value": str(target_year) if target_year else "Open to all passing batches",
        "passed": True,
        "details": f"Student graduation batch {student_profile.graduation_year} is eligible.",
    }

    if target_year and student_profile.graduation_year != target_year:
        year_check["passed"] = False
        year_check["details"] = (
            f"Graduation year {student_profile.graduation_year} does not match targeted passing batch {target_year}."
        )
        is_overall_eligible = False

    details.append(year_check)

    # Check for incomplete academic records
    if student_profile.cgpa == Decimal("0.00") or not student_profile.department:
        final_status = EligibilityStatus.INCOMPLETE
        is_overall_eligible = False
    elif is_overall_eligible:
        final_status = EligibilityStatus.ELIGIBLE
    else:
        final_status = EligibilityStatus.INELIGIBLE

    return {
        "status": final_status,
        "passed": is_overall_eligible,
        "details": details,
        "criteria_snapshot": {
            "job_title": job_requirement.title,
            "min_cgpa": str(job_requirement.min_cgpa) if job_requirement.min_cgpa else None,
            "eligibility_criteria": job_requirement.eligibility_criteria,
            "registration_deadline": job_requirement.registration_deadline.isoformat(),
            "target_year": target_year,
            "max_backlogs_allowed": max_backlogs_allowed,
        },
    }


@transaction.atomic
def apply_student_for_job(
    student_profile: StudentProfile,
    job_requirement_id: str,
    user: Optional[User] = None,
    request=None,
) -> StudentApplication:
    """Submit a student drive registration and immediately execute deterministic eligibility evaluation."""
    try:
        job = JobRequirement.objects.get(id=job_requirement_id)
    except JobRequirement.DoesNotExist:
        raise ValidationError(f"Job requirement {job_requirement_id} not found.")

    if job.status != JobRequirementStatus.APPROVED:
        raise ValidationError("Cannot apply for a job opportunity that is not in APPROVED status.")

    if job.registration_deadline and timezone.now() > job.registration_deadline:
        raise ValidationError("Registration deadline for this opportunity has passed.")

    # Require an active uploaded resume
    active_resume = student_profile.current_resume
    if not active_resume:
        raise ValidationError(
            "An uploaded PDF resume is mandatory before applying for placement drives. "
            "Please upload your resume in the Student Profile workspace."
        )

    # Get or create application
    application, created = StudentApplication.objects.get_or_create(
        student=student_profile,
        job_requirement=job,
        defaults={"resume": active_resume, "status": StudentApplicationStatus.APPLIED},
    )

    if not created and application.status == StudentApplicationStatus.WITHDRAWN:
        application.status = StudentApplicationStatus.APPLIED
        application.resume = active_resume
        application.save(update_fields=["status", "resume", "updated_at"])
    elif not created:
        raise ValidationError("You have already submitted an application for this placement opportunity.")

    # Run deterministic eligibility engine
    eval_result = evaluate_student_eligibility(job, student_profile)

    eval_status = eval_result["status"]
    app_status = (
        StudentApplicationStatus.ELIGIBLE
        if eval_status == EligibilityStatus.ELIGIBLE
        else StudentApplicationStatus.INELIGIBLE
    )
    application.status = app_status
    application.save(update_fields=["status", "updated_at"])

    # Create or update evaluation record
    EligibilityEvaluation.objects.update_or_create(
        application=application,
        defaults={
            "status": eval_status,
            "criteria_snapshot": eval_result["criteria_snapshot"],
            "evaluation_details": eval_result["details"],
            "evaluated_at": timezone.now(),
        },
    )

    AuditLog.objects.create(
        user=user or student_profile.user,
        action="STUDENT_APPLICATION_SUBMITTED",
        resource_type="students.StudentApplication",
        resource_id=str(application.id),
        changes={
            "student_roll": student_profile.roll_number,
            "job_id": str(job.id),
            "status": application.status,
            "eligibility_status": eval_status,
        },
    )

    # Phase 15 WS3: In-app notification to student
    try:
        if student_profile.user and getattr(student_profile.user, "is_active", False):
            from apps.core.models import NotificationCategory
            from apps.core.services_notifications import create_notification
            create_notification(
                recipient=student_profile.user,
                category=NotificationCategory.APPLICATION,
                title=f"Application Received: {job.title}",
                message=f"Your application for '{job.title}' at {job.company.name} has been received with status: {application.status}.",
                link="/students/drives",
                metadata={
                    "job_id": str(job.id),
                    "application_id": str(application.id),
                    "status": application.status,
                },
                idempotency_key=f"NOTIF-STUDENT-APP-{application.id}",
            )
    except Exception as exc:
        logger.warning("Failed to dispatch in-app notification for application %s: %s", application.id, exc)

    return application


# ==============================================================================
# Step 14: Eligible Candidate Cohort Finalization Services
# ==============================================================================

@transaction.atomic
def override_candidate_eligibility(
    evaluation_id: str,
    new_is_eligible: bool,
    override_reason: str,
    override_by: User,
    request=None,
) -> EligibilityEvaluation:
    """Authorize a manual override for candidate eligibility with mandatory business justification."""
    if not override_reason or len(override_reason.strip()) < 10:
        raise ValidationError(
            "A mandatory, comprehensive justification of at least 10 characters is required for manual eligibility overrides."
        )

    try:
        evaluation = EligibilityEvaluation.objects.select_related(
            "application", "application__student", "application__job_requirement"
        ).get(id=evaluation_id)
    except EligibilityEvaluation.DoesNotExist:
        raise ValidationError(f"Eligibility evaluation {evaluation_id} not found.")

    old_status = evaluation.status
    new_status = EligibilityStatus.ELIGIBLE if new_is_eligible else EligibilityStatus.INELIGIBLE

    evaluation.is_overridden = True
    evaluation.override_reason = override_reason.strip()
    evaluation.override_by = override_by
    evaluation.override_at = timezone.now()
    evaluation.status = new_status
    evaluation.save(
        update_fields=[
            "is_overridden",
            "override_reason",
            "override_by",
            "override_at",
            "status",
            "updated_at",
        ]
    )

    # Synchronize application status
    app = evaluation.application
    app.status = (
        StudentApplicationStatus.OVERRIDDEN
        if new_is_eligible
        else StudentApplicationStatus.INELIGIBLE
    )
    app.save(update_fields=["status", "updated_at"])

    # Update cohort member if present in an open cohort
    CohortMember.objects.filter(application=app).update(
        is_eligible=new_is_eligible,
        is_override=True,
        override_reason=override_reason.strip(),
        override_by=override_by,
        override_at=timezone.now(),
    )

    AuditLog.objects.create(
        user=override_by,
        action="ELIGIBILITY_OVERRIDDEN",
        resource_type="students.EligibilityEvaluation",
        resource_id=str(evaluation.id),
        changes={
            "student_roll": app.student.roll_number,
            "job_id": str(app.job_requirement_id),
            "old_status": old_status,
            "new_status": new_status,
            "reason": override_reason.strip(),
        },
    )

    # Phase 15 WS3: In-app notification to student on eligibility override
    try:
        if app.student.user and getattr(app.student.user, "is_active", False):
            from apps.core.models import NotificationCategory
            from apps.core.services_notifications import create_notification
            create_notification(
                recipient=app.student.user,
                category=NotificationCategory.APPLICATION,
                title=f"Application Status Updated: {app.job_requirement.title}",
                message=f"Your eligibility for '{app.job_requirement.title}' has been updated to {new_status} by {override_by.full_name or override_by.email}.",
                link="/students/drives",
                metadata={"evaluation_id": str(evaluation.id), "new_status": new_status},
                idempotency_key=f"NOTIF-APP-OVERRIDE-{evaluation.id}-{new_status}",
            )
    except Exception as exc:
        logger.warning("Failed to dispatch in-app notification for evaluation %s: %s", evaluation.id, exc)

    return evaluation


@transaction.atomic
def finalize_candidate_cohort(
    job_requirement_id: str,
    finalized_by: User,
    notes: str = "",
    request=None,
) -> CandidateCohort:
    """Compile, populate, and formally lock the verified candidate cohort for an approved job requirement."""
    # Use select_for_update to guard against race conditions
    try:
        job = JobRequirement.objects.select_for_update().get(id=job_requirement_id)
    except JobRequirement.DoesNotExist:
        raise ValidationError(f"Job requirement {job_requirement_id} not found.")

    if job.status != JobRequirementStatus.APPROVED:
        raise ValidationError("Only approved job opportunities can have finalized cohorts.")

    cohort, created = CandidateCohort.objects.select_for_update().get_or_create(
        job_requirement=job,
        defaults={
            "title": f"Candidate Cohort — {job.title} ({job.company.name})",
            "finalization_notes": notes.strip(),
        },
    )

    if cohort.is_locked:
        raise ValidationError(
            f"Candidate cohort for '{job.title}' is already finalized and locked. "
            "Modification of locked cohorts is prohibited to preserve downstream interview integrity."
        )

    # Collect all eligible and overridden applications
    eligible_apps = (
        StudentApplication.objects.filter(
            job_requirement=job,
            status__in=[
                StudentApplicationStatus.ELIGIBLE,
                StudentApplicationStatus.OVERRIDDEN,
            ],
        )
        .select_related("student", "eligibility_evaluation")
    )

    # Atomically populate or update cohort members
    for app in eligible_apps:
        is_override = False
        override_reason = ""
        override_by = None
        override_at = None

        if hasattr(app, "eligibility_evaluation"):
            ev = app.eligibility_evaluation
            if ev.is_overridden:
                is_override = True
                override_reason = ev.override_reason
                override_by = ev.override_by
                override_at = ev.override_at

        CohortMember.objects.update_or_create(
            cohort=cohort,
            student=app.student,
            defaults={
                "application": app,
                "is_eligible": True,
                "is_override": is_override,
                "override_reason": override_reason,
                "override_by": override_by,
                "override_at": override_at,
            },
        )

    # Lock the cohort
    cohort.is_locked = True
    cohort.finalized_by = finalized_by
    cohort.finalized_at = timezone.now()
    cohort.finalization_notes = notes.strip()
    cohort.save(
        update_fields=[
            "is_locked",
            "finalized_by",
            "finalized_at",
            "finalization_notes",
            "updated_at",
        ]
    )

    AuditLog.objects.create(
        user=finalized_by,
        action="CANDIDATE_COHORT_FINALIZED",
        resource_type="students.CandidateCohort",
        resource_id=str(cohort.id),
        changes={
            "job_id": str(job.id),
            "job_title": job.title,
            "cohort_title": cohort.title,
            "member_count": cohort.member_count,
            "finalized_at": cohort.finalized_at.isoformat(),
        },
    )

    return cohort
