"""Transactional Domain Services for Candidate Submissions & Profile Dispatch (Phase 7 / Steps 24-28)."""
import io
import hashlib
import logging
import uuid
from datetime import date
from typing import List, Dict, Any, Optional
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from django.conf import settings
from django.core.exceptions import ValidationError, PermissionDenied
from django.core.files.base import ContentFile
from django.db import transaction
from django.utils import timezone
from apps.core.models import AuditLog
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.students.models import StudentProfile, StudentApplication, StudentResume
from apps.preparation.models import PlacementReadinessCertification, PlacementReadinessStatus
from apps.submissions.models import (
    SubmissionPackage,
    SubmissionPackageStatus,
    CandidateSubmission,
    CandidateSubmissionStatus,
    SubmissionDispatchLog,
    DispatchChannel,
    AcknowledgementChannel,
)

logger = logging.getLogger("apps.submissions")


# ==============================================================================
# Step 24: Prepare Candidate List & Create Submission Package
# ==============================================================================

@transaction.atomic
def create_submission_package(
    job_requirement_id: str,
    candidate_student_ids: List[str],
    user,
    title: str = "",
    notes: str = "",
) -> SubmissionPackage:
    """Prepare candidate roster and assemble submission package for an approved job requirement (Step 24).

    Mandatory Gates & Business Invariants:
    1. JobRequirement must be APPROVED or PUBLISHED.
    2. At least one candidate must be provided.
    3. Each candidate must have an eligible job application for this requirement.
    4. Step 23 Gate: Candidate MUST have an active PlacementReadinessCertification with
       is_approved_for_placements = True and status = 'CERTIFIED'.
    5. Candidate must not already have an active submission for this same job requirement.
    """
    try:
        job = JobRequirement.objects.select_related("company", "hr_contact").get(id=job_requirement_id)
    except JobRequirement.DoesNotExist:
        raise ValidationError(f"Job requirement {job_requirement_id} does not exist.")

    if job.status not in [JobRequirementStatus.APPROVED, "PUBLISHED"]:
        raise ValidationError(
            f"Cannot create candidate submission for job in '{job.get_status_display()}' status. "
            f"Job must be verified and approved by Placement Head."
        )

    if not candidate_student_ids:
        raise ValidationError("At least one eligible candidate must be selected for corporate submission.")

    # Deduplicate requested student IDs while preserving order
    unique_student_ids = list(dict.fromkeys(candidate_student_ids))

    # Verify no active duplicate submissions for this job
    already_submitted = set(
        CandidateSubmission.objects.filter(
            package__job_requirement=job,
            student_id__in=unique_student_ids,
        ).exclude(
            package__status=SubmissionPackageStatus.CANCELLED,
        ).values_list("student__roll_number", flat=True)
    )
    if already_submitted:
        rolls = ", ".join(already_submitted)
        raise ValidationError(
            f"The following candidate(s) are already included in an active submission package for this job: {rolls}"
        )

    # Fetch and validate candidates
    students = StudentProfile.objects.filter(id__in=unique_student_ids).select_related("user")
    student_map = {str(s.id): s for s in students}

    if len(student_map) != len(unique_student_ids):
        missing = set(unique_student_ids) - set(student_map.keys())
        raise ValidationError(f"One or more student profiles not found: {missing}")

    validated_candidates = []

    for s_id in unique_student_ids:
        student = student_map[s_id]

        # Check job application exists
        app = StudentApplication.objects.filter(student=student, job_requirement=job).first()
        if not app:
            raise ValidationError(
                f"Candidate {student.roll_number} has not applied for job requirement '{job.title}'."
            )

        # Step 23 Placement Readiness Certification Gate:
        cert = PlacementReadinessCertification.objects.filter(
            student=student,
            is_approved_for_placements=True,
            status=PlacementReadinessStatus.CERTIFIED,
        ).select_related("approved_resume").order_by("-certified_at").first()

        if not cert or not cert.approved_resume:
            raise ValidationError(
                f"Candidate {student.roll_number} ({student.user.full_name}) lacks Placement Head "
                f"readiness certification (Workflow Step 23 Gate). Only candidates certified ready "
                f"for placement drives can be submitted to companies."
            )

        validated_candidates.append({
            "student": student,
            "application": app,
            "cert": cert,
            "resume": cert.approved_resume,
        })

    package_title = title.strip() or f"{job.company.name} - {job.title} Candidate Roster"

    package = SubmissionPackage.objects.create(
        job_requirement=job,
        company=job.company,
        hr_contact=job.hr_contact,
        title=package_title,
        status=SubmissionPackageStatus.DRAFT,
        candidate_count=len(validated_candidates),
        notes=notes.strip(),
        created_by=user,
    )

    # Create candidate submission records with frozen snapshots
    candidate_records = []
    for item in validated_candidates:
        s = item["student"]
        r = item["resume"]
        cert = item["cert"]
        app = item["application"]

        snapshot = {
            "student_name": s.user.full_name or s.user.email,
            "roll_number": s.roll_number,
            "institutional_email": s.institutional_email,
            "phone_number": s.phone_number,
            "college_name": s.college_name,
            "department": s.department,
            "graduation_year": s.graduation_year,
            "cgpa": float(s.cgpa) if s.cgpa else None,
            "technical_skills": getattr(s, "technical_skills", "") or "",
            "resume_version": r.version_number,
            "resume_sha256": r.sha256_hash,
            "certified_by": cert.certified_by.full_name or cert.certified_by.email,
            "certified_at": cert.certified_at.isoformat(),
        }

        cs = CandidateSubmission(
            package=package,
            student=s,
            application=app,
            readiness_certification=cert,
            submitted_resume=r,
            resume_version_number=r.version_number,
            resume_sha256=r.sha256_hash,
            status=CandidateSubmissionStatus.PENDING,
            candidate_snapshot=snapshot,
        )
        candidate_records.append(cs)

    CandidateSubmission.objects.bulk_create(candidate_records)

    AuditLog.objects.create(
        user=user,
        action="SUBMISSION_PACKAGE_CREATED",
        resource_type="submissions.SubmissionPackage",
        resource_id=str(package.id),
        changes={
            "job_id": str(job.id),
            "company_name": job.company.name,
            "candidate_count": len(candidate_records),
            "candidate_roll_numbers": [item["student"].roll_number for item in validated_candidates],
        },
    )

    logger.info(
        "Created submission package %s for %s with %d candidates by user %s",
        package.id,
        job.title,
        len(candidate_records),
        user.email,
    )

    return package


# ==============================================================================
# Step 25: Generate Candidate Roster Spreadsheet (Excel Sheet)
# ==============================================================================

@transaction.atomic
def generate_candidate_roster_spreadsheet(package_id: str, user) -> SubmissionPackage:
    """Generate standardized master XLSX spreadsheet with student metrics & cryptographic SHA-256 digest (Step 25)."""
    try:
        package = SubmissionPackage.objects.select_related("job_requirement__company", "hr_contact").get(id=package_id)
    except SubmissionPackage.DoesNotExist:
        raise ValidationError(f"Submission package {package_id} not found.")

    if package.status not in [SubmissionPackageStatus.DRAFT, SubmissionPackageStatus.READY_FOR_DISPATCH]:
        raise ValidationError(
            f"Cannot regenerate roster spreadsheet for package in '{package.get_status_display()}' status."
        )

    candidates = list(
        package.candidates.select_related("student__user", "submitted_resume").order_by("student__roll_number")
    )
    if not candidates:
        raise ValidationError("Cannot generate roster spreadsheet: submission package contains 0 candidates.")

    # Build Excel Workbook
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Candidate Roster"

    # Brand Colors & Styles
    navy_fill = PatternFill(start_color="1B365D", end_color="1B365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1B365D")
    meta_font = Font(name="Calibri", size=10, italic=True, color="4B5563")
    regular_font = Font(name="Calibri", size=10, color="000000")
    thin_border = Border(
        left=Side(style="thin", color="D1D5DB"),
        right=Side(style="thin", color="D1D5DB"),
        top=Side(style="thin", color="D1D5DB"),
        bottom=Side(style="thin", color="D1D5DB"),
    )
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")

    # Title block
    ws.merge_cells("A1:L1")
    ws["A1"] = "GQT HRMS — OFFICIAL PLACEMENT CANDIDATE ROSTER"
    ws["A1"].font = title_font
    ws["A1"].alignment = Alignment(horizontal="left", vertical="center")

    # Metadata block
    job = package.job_requirement
    ws["A2"] = f"Company: {package.company.name} | Role: {job.title} | Package: {package.title}"
    ws["A2"].font = meta_font
    ws["A3"] = f"Generated: {timezone.now():%Y-%m-%d %H:%M UTC} | Total Candidates: {len(candidates)}"
    ws["A3"].font = meta_font

    # Table Headers (Row 5)
    headers = [
        "Sl. No.",
        "Roll Number",
        "Candidate Name",
        "Email Address",
        "Contact Number",
        "College / Institution",
        "Branch / Department",
        "Graduation Year",
        "CGPA / %",
        "Key Technical Skills",
        "Approved Resume",
        "Resume SHA-256 Digest",
    ]

    header_row = 5
    for col_idx, header_text in enumerate(headers, start=1):
        cell = ws.cell(row=header_row, column=col_idx, value=header_text)
        cell.fill = navy_fill
        cell.font = header_font
        cell.alignment = center_align
        cell.border = thin_border

    # Data Rows
    current_row = header_row + 1
    for sl_no, cs in enumerate(candidates, start=1):
        snap = cs.candidate_snapshot or {}
        r = cs.submitted_resume
        resume_label = f"Resume v{cs.resume_version_number}"

        row_data = [
            sl_no,
            snap.get("roll_number", cs.student.roll_number),
            snap.get("student_name", cs.student.user.full_name),
            snap.get("institutional_email", cs.student.institutional_email),
            snap.get("phone_number", cs.student.phone_number),
            snap.get("college_name", cs.student.college_name),
            snap.get("department", cs.student.department),
            snap.get("graduation_year", cs.student.graduation_year),
            f"{snap.get('cgpa', cs.student.cgpa):.2f}" if snap.get("cgpa") else "N/A",
            snap.get("technical_skills") or getattr(cs.student, "technical_skills", "") or "N/A",
            resume_label,
            cs.resume_sha256[:16] + "...",
        ]

        for col_idx, val in enumerate(row_data, start=1):
            cell = ws.cell(row=current_row, column=col_idx, value=val)
            cell.font = regular_font
            cell.border = thin_border
            cell.alignment = center_align if col_idx in [1, 2, 8, 9, 11] else left_align

        current_row += 1

    # Adjust column widths dynamically
    from openpyxl.utils import get_column_letter

    for col_idx, col in enumerate(ws.iter_cols(min_row=5, max_row=current_row - 1), start=1):
        col_letter = get_column_letter(col_idx)
        max_len = max((len(str(cell.value or "")) for cell in col), default=10)
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Save to memory buffer
    buffer = io.BytesIO()
    wb.save(buffer)
    excel_bytes = buffer.getvalue()

    # Compute SHA-256 digest
    sha256_hash = hashlib.sha256(excel_bytes).hexdigest()

    clean_company = package.company.name.replace(" ", "_")
    clean_role = job.title.replace(" ", "_")
    file_name = f"GQT_{clean_company}_{clean_role}_Candidate_Roster.xlsx"

    # Persist file and update package
    package.roster_file.save(file_name, ContentFile(excel_bytes), save=False)
    package.roster_file_name = file_name
    package.package_hash = sha256_hash
    package.roster_generated_at = timezone.now()
    package.save(update_fields=["roster_file", "roster_file_name", "package_hash", "roster_generated_at", "updated_at"])

    AuditLog.objects.create(
        user=user,
        action="ROSTER_SPREADSHEET_GENERATED",
        resource_type="submissions.SubmissionPackage",
        resource_id=str(package.id),
        changes={
            "file_name": file_name,
            "candidate_count": len(candidates),
            "sha256_digest": sha256_hash,
        },
    )

    logger.info("Generated roster Excel for package %s (SHA-256: %s)", package.id, sha256_hash)
    return package


# ==============================================================================
# Step 26: Verify and Attach Resumes
# ==============================================================================

@transaction.atomic
def verify_and_attach_resumes(package_id: str, user) -> SubmissionPackage:
    """Verify and lock certified resume PDF attachments for all roster candidates (Step 26).

    Business Invariants:
    1. Every candidate must possess their exact approved resume PDF.
    2. Verifies SHA-256 digest of attached resume matches certification record.
    3. Moves package to READY_FOR_DISPATCH status once verified.
    """
    try:
        package = SubmissionPackage.objects.get(id=package_id)
    except SubmissionPackage.DoesNotExist:
        raise ValidationError(f"Submission package {package_id} not found.")

    if package.status not in [SubmissionPackageStatus.DRAFT, SubmissionPackageStatus.READY_FOR_DISPATCH]:
        raise ValidationError(f"Cannot attach resumes to package in '{package.get_status_display()}' status.")

    candidates = package.candidates.select_related("student", "submitted_resume").all()
    if not candidates:
        raise ValidationError("Package contains no candidates to attach resumes for.")

    verified_count = 0
    for cs in candidates:
        resume = cs.submitted_resume
        if not resume or not resume.file:
            raise ValidationError(
                f"Candidate {cs.student.roll_number} has no certified resume PDF attached."
            )

        # Check resume hash integrity
        if resume.sha256_hash != cs.resume_sha256:
            raise ValidationError(
                f"Integrity check failed: resume hash for {cs.student.roll_number} does not match certified snapshot."
            )
        verified_count += 1

    package.resumes_attached_at = timezone.now()
    package.status = SubmissionPackageStatus.READY_FOR_DISPATCH
    package.save(update_fields=["resumes_attached_at", "status", "updated_at"])

    AuditLog.objects.create(
        user=user,
        action="SUBMISSION_RESUMES_ATTACHED",
        resource_type="submissions.SubmissionPackage",
        resource_id=str(package.id),
        changes={
            "attached_resumes_count": verified_count,
            "status": package.status,
        },
    )

    logger.info("Verified and attached %d resumes for package %s", verified_count, package.id)
    return package


# ==============================================================================
# Step 27: Send Candidate Profiles to HR (Dispatch)
# ==============================================================================

@transaction.atomic
def dispatch_candidate_profiles_to_hr(
    package_id: str,
    user,
    channel: str = DispatchChannel.EMAIL,
    recipient_email: str = "",
    recipient_name: str = "",
    recipient_phone: str = "",
    dispatch_notes: str = "",
) -> SubmissionPackage:
    """Dispatch candidate submission package to corporate HR partner (Step 27).

    State Transition:
    - Moves package to DISPATCHED.
    - Updates candidate submissions to SUBMITTED.
    - Records immutable SubmissionDispatchLog with external provider ref.
    """
    try:
        # Row-lock package to prevent concurrent duplicate dispatch
        package = SubmissionPackage.objects.select_for_update().select_related(
            "job_requirement", "company", "hr_contact"
        ).get(id=package_id)
    except SubmissionPackage.DoesNotExist:
        raise ValidationError(f"Submission package {package_id} not found.")

    if package.status in [SubmissionPackageStatus.DISPATCHED, SubmissionPackageStatus.ACKNOWLEDGED]:
        raise ValidationError(
            f"Package has already been dispatched to corporate HR on {package.dispatched_at:%Y-%m-%d}."
        )

    if package.candidate_count == 0:
        raise ValidationError("Cannot dispatch empty candidate submission package.")

    # Resolve recipient contact information
    target_email = recipient_email.strip() or (package.hr_contact.email if package.hr_contact else "")
    target_name = recipient_name.strip() or (package.hr_contact.name if package.hr_contact else "")
    target_phone = recipient_phone.strip() or (package.hr_contact.phone if package.hr_contact else "")

    if channel == DispatchChannel.EMAIL and not target_email:
        raise ValidationError("Corporate recipient email address is required for email profile dispatch.")
    if channel == DispatchChannel.WHATSAPP and not target_phone:
        raise ValidationError("Recipient telephone number is required for WhatsApp profile dispatch.")

    # External Provider Dispatch Simulation / Interface Boundary
    provider_ref = f"MSG-DISP-{uuid.uuid4().hex[:12].upper()}"

    # Log dispatch attempt
    attempt_count = package.dispatch_logs.count() + 1
    dispatch_log = SubmissionDispatchLog.objects.create(
        package=package,
        attempt_number=attempt_count,
        channel=channel,
        recipient=target_email if channel == DispatchChannel.EMAIL else target_phone,
        status="SENT",
        provider_message_id=provider_ref,
        response_payload={
            "provider": "GQT Corporate Transmission Gateway (Simulated Provider)",
            "recipient_name": target_name,
            "recipient_email": target_email,
            "candidate_count": package.candidate_count,
            "has_roster_file": bool(package.roster_file),
            "dispatched_at": timezone.now().isoformat(),
        },
        dispatched_by=user,
    )

    # State Transitions
    now = timezone.now()
    package.status = SubmissionPackageStatus.DISPATCHED
    package.dispatched_at = now
    package.dispatched_by = user
    package.dispatch_channel = channel
    package.recipient_email = target_email
    package.recipient_name = target_name
    package.recipient_phone = target_phone
    package.provider_reference = provider_ref
    package.dispatch_notes = dispatch_notes.strip()
    package.save(update_fields=[
        "status",
        "dispatched_at",
        "dispatched_by",
        "dispatch_channel",
        "recipient_email",
        "recipient_name",
        "recipient_phone",
        "provider_reference",
        "dispatch_notes",
        "updated_at",
    ])

    # Atomically advance candidate submissions to SUBMITTED
    package.candidates.update(status=CandidateSubmissionStatus.SUBMITTED, updated_at=now)

    AuditLog.objects.create(
        user=user,
        action="CANDIDATE_PROFILES_DISPATCHED",
        resource_type="submissions.SubmissionPackage",
        resource_id=str(package.id),
        changes={
            "channel": channel,
            "recipient_email": target_email,
            "recipient_name": target_name,
            "candidate_count": package.candidate_count,
            "provider_reference": provider_ref,
            "status": package.status,
        },
    )

    logger.info(
        "Dispatched package %s (%d candidates) to %s via %s (Ref: %s)",
        package.id,
        package.candidate_count,
        target_email,
        channel,
        provider_ref,
    )

    return package


# ==============================================================================
# Step 28: Company Acknowledgement
# ==============================================================================

@transaction.atomic
def record_company_acknowledgement(
    package_id: str,
    user,
    acknowledged_by_contact_name: str,
    acknowledgement_channel: str = AcknowledgementChannel.EMAIL,
    recruiter_feedback: str = "",
    tentative_interview_date: Optional[date] = None,
    follow_up_callback_date: Optional[date] = None,
) -> SubmissionPackage:
    """Record recruiter acknowledgment confirming receipt of candidate profiles (Step 28).

    State Transition:
    - Moves package to ACKNOWLEDGED.
    - Updates candidate submissions to ACKNOWLEDGED.
    - Records follow-up dates and feedback.
    """
    try:
        package = SubmissionPackage.objects.select_for_update().get(id=package_id)
    except SubmissionPackage.DoesNotExist:
        raise ValidationError(f"Submission package {package_id} not found.")

    if package.status != SubmissionPackageStatus.DISPATCHED:
        raise ValidationError(
            f"Cannot record company acknowledgment for package in '{package.get_status_display()}' status. "
            f"Package must be DISPATCHED first."
        )

    contact_name = acknowledged_by_contact_name.strip()
    if not contact_name:
        raise ValidationError("Name of the corporate HR representative confirming receipt is required.")

    now = timezone.now()
    package.status = SubmissionPackageStatus.ACKNOWLEDGED
    package.acknowledged_at = now
    package.acknowledged_by = user
    package.acknowledged_by_contact_name = contact_name
    package.acknowledgement_channel = acknowledgement_channel
    package.recruiter_feedback = recruiter_feedback.strip()
    package.tentative_interview_date = tentative_interview_date
    package.follow_up_callback_date = follow_up_callback_date
    package.save(update_fields=[
        "status",
        "acknowledged_at",
        "acknowledged_by",
        "acknowledged_by_contact_name",
        "acknowledgement_channel",
        "recruiter_feedback",
        "tentative_interview_date",
        "follow_up_callback_date",
        "updated_at",
    ])

    # Advance candidate submissions to ACKNOWLEDGED
    package.candidates.update(status=CandidateSubmissionStatus.ACKNOWLEDGED, updated_at=now)

    AuditLog.objects.create(
        user=user,
        action="COMPANY_ACKNOWLEDGEMENT_RECORDED",
        resource_type="submissions.SubmissionPackage",
        resource_id=str(package.id),
        changes={
            "acknowledged_by_contact_name": contact_name,
            "channel": acknowledgement_channel,
            "tentative_interview_date": str(tentative_interview_date) if tentative_interview_date else None,
            "follow_up_callback_date": str(follow_up_callback_date) if follow_up_callback_date else None,
            "status": package.status,
        },
    )

    logger.info(
        "Recorded company acknowledgment for package %s from %s (Channel: %s)",
        package.id,
        contact_name,
        acknowledgement_channel,
    )

    return package
