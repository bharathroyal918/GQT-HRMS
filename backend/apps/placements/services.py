"""Placement Management Services.

Encapsulates transactional business logic for:
- Step 36: Receive Final Results from Corporate HR
- Step 37: Update Candidate Placement Status & Audit History
- Step 38: Notify Students of Outcome Advisories
- Step 39: Secure Offer Letter Upload, Integrity Verification, & Versioning
- Step 40: Track Offer Acceptance (Student Self-Service & Staff Offline Entry)
- Step 41: Track Joining Status, Deferrals, & Onboarding Verification
"""
import uuid
from decimal import Decimal
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.placements.models import (
    FinalResultIntake,
    CandidatePlacementStatus,
    PlacementStatusHistory,
    PlacementNotificationLog,
    CandidateOfferLetter,
    OfferLetterVersion,
    JoiningStatusHistory,
    ResultIntakeSource,
    CandidatePlacementStatusChoices,
    OfferAcceptanceStatus,
    JoiningStatus,
)
from apps.placements.validators import validate_offer_letter_pdf
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.crm.models import Company, HRContact
from apps.students.models import StudentProfile
from apps.submissions.models import CandidateSubmission
from apps.interviews.models import ShortlistedCandidate


def generate_result_reference_code() -> str:
    """Generate institutional reference code for final result intake: RES-YYYYMMDD-XXXX."""
    date_str = timezone.now().strftime("%Y%m%d")
    random_hex = uuid.uuid4().hex[:4].upper()
    return f"RES-{date_str}-{random_hex}"


def receive_final_results(
    *,
    job_requirement_id: Optional[str] = None,
    job_id: Optional[str] = None,
    company_id: str,
    hr_contact_id: Optional[str] = None,
    source: str = ResultIntakeSource.EMAIL,
    received_at: Optional[Any] = None,
    notes: str = "",
    candidate_results: List[Dict[str, Any]],
    user: Any,
) -> FinalResultIntake:
    """Receive and record final recruitment results from corporate HR (Step 36).

    Validates:
    1. JobRequirement exists and is in APPROVED status.
    2. Company matches job requirement.
    3. Each student exists and participated in this drive (either submitted or shortlisted).
    4. Each candidate status is one of SELECTED, REJECTED, WAITING_LIST, HOLD.
    5. Prevents duplicate candidate submissions in the same intake batch.
    """
    target_job_id = job_requirement_id or job_id
    if not target_job_id:
        raise ValidationError("job_requirement_id is required.")

    if not candidate_results:
        raise ValidationError("At least one candidate result must be provided.")

    try:
        job = JobRequirement.objects.get(id=target_job_id)
    except JobRequirement.DoesNotExist:
        raise ValidationError("Job requirement not found.")

    if job.status != JobRequirementStatus.APPROVED:
        raise ValidationError("Final results can only be recorded for approved job requirements.")

    try:
        company = Company.objects.get(id=company_id)
    except Company.DoesNotExist:
        raise ValidationError("Company not found.")

    if job.company_id != company.id:
        raise ValidationError("Company does not match the job requirement corporate sponsor.")

    hr_contact = None
    if hr_contact_id:
        try:
            hr_contact = HRContact.objects.get(id=hr_contact_id, company=company)
        except HRContact.DoesNotExist:
            raise ValidationError("HR Contact does not belong to the specified company.")

    # Deduplicate student IDs in payload
    student_ids = [c["student_id"] for c in candidate_results]
    if len(student_ids) != len(set(student_ids)):
        raise ValidationError("Duplicate candidate entries detected in result payload.")

    # Validate that all students participated in this job drive
    participated_student_ids = set(
        CandidateSubmission.objects.filter(
            package__job_requirement=job
        ).values_list("student_id", flat=True)
    ) | set(
        ShortlistedCandidate.objects.filter(
            shortlist__job_requirement=job
        ).values_list("student_id", flat=True)
    )

    with transaction.atomic():
        ref_code = generate_result_reference_code()
        while FinalResultIntake.objects.filter(result_reference_code=ref_code).exists():
            ref_code = generate_result_reference_code()

        intake = FinalResultIntake.objects.create(
            job_requirement=job,
            company=company,
            hr_contact=hr_contact,
            result_reference_code=ref_code,
            source=source,
            received_at=received_at or timezone.now(),
            notes=notes,
            created_by=user,
        )

        selected_c = 0
        rejected_c = 0
        waiting_c = 0
        hold_c = 0

        for item in candidate_results:
            s_id = item["student_id"]
            c_status = item.get("status", CandidatePlacementStatusChoices.HOLD)

            if c_status not in [c[0] for c in CandidatePlacementStatusChoices.CHOICES]:
                raise ValidationError(f"Invalid candidate placement status: {c_status}")

            try:
                student = StudentProfile.objects.get(id=s_id)
            except StudentProfile.DoesNotExist:
                raise ValidationError(f"Student profile with ID '{s_id}' not found.")

            # Cross-job validation: Verify candidate actually participated in this drive
            if participated_student_ids and student.id not in participated_student_ids:
                raise ValidationError(
                    f"Candidate {student.roll_number} did not participate in recruitment drive for '{job.title}'."
                )

            # Tally counts
            if c_status == CandidatePlacementStatusChoices.SELECTED:
                selected_c += 1
            elif c_status == CandidatePlacementStatusChoices.REJECTED:
                rejected_c += 1
            elif c_status == CandidatePlacementStatusChoices.WAITING_LIST:
                waiting_c += 1
            elif c_status == CandidatePlacementStatusChoices.HOLD:
                hold_c += 1

            # Update or create candidate placement status
            placement_status, created = CandidatePlacementStatus.objects.update_or_create(
                job_requirement=job,
                student=student,
                defaults={
                    "intake": intake,
                    "company": company,
                    "status": c_status,
                    "designation_offered": item.get("designation_offered", ""),
                    "offered_ctc": Decimal(str(item["offered_ctc"])) if item.get("offered_ctc") else None,
                    "work_location": item.get("work_location", ""),
                    "remarks": item.get("remarks", ""),
                    "status_updated_at": timezone.now(),
                    "status_updated_by": user,
                },
            )

            # Record audit history
            PlacementStatusHistory.objects.create(
                placement_status=placement_status,
                previous_status="NEW_RECORD" if created else "PREVIOUS_INTAKE",
                new_status=c_status,
                reason=f"Initial intake under {ref_code}. {item.get('remarks', '')}".strip(),
                changed_by=user,
            )

        intake.total_results = len(candidate_results)
        intake.selected_count = selected_c
        intake.rejected_count = rejected_c
        intake.waiting_list_count = waiting_c
        intake.hold_count = hold_c
        intake.save()

    return intake


def update_candidate_placement_status(
    *,
    placement_id: str,
    new_status: str,
    reason: str = "",
    designation_offered: Optional[str] = None,
    offered_ctc: Optional[Any] = None,
    work_location: Optional[str] = None,
    remarks: Optional[str] = None,
    user: Any,
) -> CandidatePlacementStatus:
    """Transition candidate placement status with server-side validation and audit log (Step 37)."""
    if new_status not in [c[0] for c in CandidatePlacementStatusChoices.CHOICES]:
        raise ValidationError(f"Invalid status: {new_status}")

    try:
        placement = CandidatePlacementStatus.objects.select_related("student", "job_requirement").get(id=placement_id)
    except CandidatePlacementStatus.DoesNotExist:
        raise ValidationError("Candidate placement record not found.")

    previous_status = placement.status
    if previous_status == new_status:
        # Idempotent return if no status change
        return placement

    # Enforce mandatory documented reason when revoking selection
    if previous_status == CandidatePlacementStatusChoices.SELECTED and new_status != CandidatePlacementStatusChoices.SELECTED:
        if not reason.strip():
            raise ValidationError("A documented reason is mandatory when revoking candidate selection.")

    with transaction.atomic():
        placement.status = new_status
        if designation_offered is not None:
            placement.designation_offered = designation_offered
        if offered_ctc is not None:
            placement.offered_ctc = Decimal(str(offered_ctc)) if offered_ctc else None
        if work_location is not None:
            placement.work_location = work_location
        if remarks is not None:
            placement.remarks = remarks

        placement.status_updated_at = timezone.now()
        placement.status_updated_by = user
        placement.save()

        PlacementStatusHistory.objects.create(
            placement_status=placement,
            previous_status=previous_status,
            new_status=new_status,
            reason=reason.strip() or "Standard placement status update.",
            changed_by=user,
        )

    return placement


def notify_candidate_placement_status(
    *,
    placement_id: str,
    channel: str = "EMAIL",
    user: Any,
) -> PlacementNotificationLog:
    """Dispatch truthful candidate notification for their placement outcome (Step 38)."""
    try:
        placement = CandidatePlacementStatus.objects.select_related(
            "student", "student__user", "job_requirement", "company"
        ).get(id=placement_id)
    except CandidatePlacementStatus.DoesNotExist:
        raise ValidationError("Candidate placement record not found.")

    student = placement.student
    recipient_email = student.institutional_email or student.user.email
    recipient_phone = getattr(student.user, "phone_number", "") or ""

    status_labels = {
        CandidatePlacementStatusChoices.SELECTED: "Congratulations! You have been Selected",
        CandidatePlacementStatusChoices.REJECTED: "Update on your Recruitment Drive Application",
        CandidatePlacementStatusChoices.WAITING_LIST: "You have been placed on the Waiting List",
        CandidatePlacementStatusChoices.HOLD: "Your Recruitment Drive Decision is on Hold",
    }
    headline = status_labels.get(placement.status, "Placement Decision Advisory")

    details = {
        "candidate_name": student.user.full_name,
        "roll_number": student.roll_number,
        "job_title": placement.job_requirement.title,
        "company_name": placement.company.name,
        "status": placement.status,
        "designation": placement.designation_offered,
        "ctc": str(placement.offered_ctc) if placement.offered_ctc else "As per drive policy",
        "work_location": placement.work_location,
        "headline": headline,
    }

    simulated_message_id = f"MSG-PLACE-{uuid.uuid4().hex[:12].upper()}"

    log = PlacementNotificationLog.objects.create(
        placement_status=placement,
        student=student,
        recipient_email=recipient_email,
        recipient_phone=recipient_phone,
        channel=channel,
        status="SENT",
        status_announced=placement.status,
        provider_message_id=simulated_message_id,
        details_payload=details,
        sent_at=timezone.now(),
        sent_by=user,
    )

    return log


def upload_offer_letter(
    *,
    placement_id: str,
    file_obj: Any,
    acceptance_deadline: Optional[Any] = None,
    expected_joining_date: Optional[Any] = None,
    joining_location: str = "",
    user: Any,
) -> CandidateOfferLetter:
    """Upload official corporate offer letter PDF for selected candidate (Step 39).

    Validates:
    1. Candidate must be in SELECTED status.
    2. File must be valid PDF (b'%PDF-' magic bytes, <= 5MB).
    3. Computes cryptographic SHA-256 hash.
    4. If previous offer exists, archives it in OfferLetterVersion before updating.
    """
    try:
        placement = CandidatePlacementStatus.objects.select_related(
            "student", "job_requirement", "company"
        ).get(id=placement_id)
    except CandidatePlacementStatus.DoesNotExist:
        raise ValidationError("Candidate placement status not found.")

    if placement.status != CandidatePlacementStatusChoices.SELECTED:
        raise ValidationError(
            f"Offer letter can only be uploaded for SELECTED candidates. Current status is {placement.status}."
        )

    # Validates size limit, %PDF- magic bytes, and computes SHA-256
    sha256 = validate_offer_letter_pdf(file_obj)

    with transaction.atomic():
        existing_offer = CandidateOfferLetter.objects.filter(placement_status=placement).first()

        if existing_offer:
            # Monotonic archival: supersede prior version
            archived_version = existing_offer.version_number
            OfferLetterVersion.objects.create(
                offer=existing_offer,
                version_number=archived_version,
                file=existing_offer.file,
                file_name=existing_offer.file_name,
                file_size_bytes=existing_offer.file_size_bytes,
                sha256_hash=existing_offer.sha256_hash,
                superseded_at=timezone.now(),
                superseded_by=user,
                superseded_reason="Revised offer letter issued by placement office.",
            )

            existing_offer.file = file_obj
            existing_offer.file_name = file_obj.name
            existing_offer.file_size_bytes = file_obj.size
            existing_offer.sha256_hash = sha256
            existing_offer.version_number = archived_version + 1
            existing_offer.is_active = True
            existing_offer.issued_at = timezone.now()
            existing_offer.issued_by = user
            if acceptance_deadline is not None:
                existing_offer.acceptance_deadline = acceptance_deadline
            if expected_joining_date is not None:
                existing_offer.expected_joining_date = expected_joining_date
            if joining_location:
                existing_offer.joining_location = joining_location
            # Reset acceptance state to pending on new version release
            existing_offer.acceptance_status = OfferAcceptanceStatus.PENDING_RESPONSE
            existing_offer.accepted_at = None
            existing_offer.save()
            return existing_offer

        else:
            offer = CandidateOfferLetter.objects.create(
                placement_status=placement,
                student=placement.student,
                job_requirement=placement.job_requirement,
                company=placement.company,
                file=file_obj,
                file_name=file_obj.name,
                file_size_bytes=file_obj.size,
                sha256_hash=sha256,
                version_number=1,
                is_active=True,
                issued_at=timezone.now(),
                issued_by=user,
                acceptance_deadline=acceptance_deadline,
                expected_joining_date=expected_joining_date,
                joining_location=joining_location,
                acceptance_status=OfferAcceptanceStatus.PENDING_RESPONSE,
            )
            return offer


def record_offer_acceptance(
    *,
    offer_id: str,
    decision: str,
    notes: str = "",
    source: str = "STUDENT_PORTAL",
    user: Any,
) -> CandidateOfferLetter:
    """Track candidate decision to accept or decline the offer letter (Step 40)."""
    if decision not in [OfferAcceptanceStatus.ACCEPTED, OfferAcceptanceStatus.DECLINED]:
        raise ValidationError("Decision must be either ACCEPTED or DECLINED.")

    try:
        offer = CandidateOfferLetter.objects.select_related(
            "student", "student__user", "placement_status"
        ).get(id=offer_id)
    except CandidateOfferLetter.DoesNotExist:
        raise ValidationError("Offer letter record not found.")

    if not offer.is_active:
        raise ValidationError("Cannot respond to an inactive or superseded offer letter.")

    if offer.acceptance_status != OfferAcceptanceStatus.PENDING_RESPONSE:
        raise ValidationError(
            f"Offer letter is already in {offer.get_acceptance_status_display()} state; cannot record a new decision."
        )

    # Student ownership check: if source is student portal, ensure user is the candidate
    if source == "STUDENT_PORTAL":
        if offer.student.user != user and not user.is_superuser:
            raise ValidationError("You may only submit an acceptance decision for your own offer letter.")

    with transaction.atomic():
        offer.acceptance_status = decision
        offer.accepted_at = timezone.now()
        offer.acceptance_source = source
        offer.student_decision_notes = notes.strip()
        offer.acceptance_recorded_by = user

        # Step 41 bridge: If accepted, mark joining status as PENDING_JOINING; if declined, mark NOT_APPLICABLE
        if decision == OfferAcceptanceStatus.ACCEPTED:
            offer.joining_status = JoiningStatus.PENDING_JOINING
        else:
            offer.joining_status = JoiningStatus.NOT_APPLICABLE

        offer.save()

    return offer


def record_joining_status(
    *,
    offer_id: str,
    joining_status: str,
    actual_joining_date: Optional[Any] = None,
    deferred_joining_date: Optional[Any] = None,
    joining_location: Optional[str] = None,
    employee_id_assigned: Optional[str] = None,
    notes: str = "",
    user: Any,
) -> CandidateOfferLetter:
    """Track and verify candidate onboarding reporting status: JOINED, NOT_JOINED, DEFERRED (Step 41)."""
    valid_statuses = [
        JoiningStatus.JOINED,
        JoiningStatus.NOT_JOINED,
        JoiningStatus.DEFERRED,
    ]
    if joining_status not in valid_statuses:
        raise ValidationError(f"Invalid joining status: {joining_status}. Expected one of {valid_statuses}.")

    try:
        offer = CandidateOfferLetter.objects.select_related(
            "student", "student__user", "company", "job_requirement"
        ).get(id=offer_id)
    except CandidateOfferLetter.DoesNotExist:
        raise ValidationError("Offer letter record not found.")

    if offer.acceptance_status != OfferAcceptanceStatus.ACCEPTED:
        raise ValidationError("Joining status can only be tracked for offers that have been ACCEPTED by the candidate.")

    if joining_status == JoiningStatus.DEFERRED:
        if not deferred_joining_date and not notes.strip():
            raise ValidationError("A deferred joining date or explanatory reason is required when deferring joining.")

    if joining_status == JoiningStatus.NOT_JOINED and not notes.strip():
        raise ValidationError("Documented remarks are required when marking a candidate as NOT JOINED.")

    with transaction.atomic():
        previous_status = offer.joining_status
        offer.joining_status = joining_status

        if actual_joining_date is not None:
            offer.actual_joining_date = actual_joining_date
        elif joining_status == JoiningStatus.JOINED and not offer.actual_joining_date:
            offer.actual_joining_date = timezone.now().date()

        if deferred_joining_date is not None:
            offer.deferred_joining_date = deferred_joining_date

        if joining_location is not None:
            offer.joining_location = joining_location

        if employee_id_assigned is not None:
            offer.employee_id_assigned = employee_id_assigned

        if notes:
            offer.joining_notes = notes.strip()

        offer.joining_verified_at = timezone.now()
        offer.joining_verified_by = user
        offer.save()

        JoiningStatusHistory.objects.create(
            offer=offer,
            previous_status=previous_status,
            new_status=joining_status,
            reason=notes.strip() or "Joining status updated.",
            changed_by=user,
        )

    return offer
