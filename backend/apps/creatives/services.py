"""Creative Studio & Promotional Assets Business Services (Phase 4).

Follows strict 5-layer architecture.
All business state mutations, 4-point verification checklist updates,
and Placement Head sign-offs are executed atomically within @transaction.atomic blocks.
"""
from typing import Optional, Dict, Any, List
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models, transaction
from django.utils import timezone
from django.core.files.uploadedfile import UploadedFile
from apps.accounts.models import User, RoleCatalog
from apps.core.models import AuditLog
from apps.jobs.models import JobRequirement, JobRequirementStatus
from apps.creatives.models import (
    CreativeRequest,
    CreativeRequestStatus,
    CreativeDeliverableType,
    CreativePriority,
    CreativeAssetVersion,
    AssetVersionStatus,
    CreativeChecklistItem,
    ChecklistItemStatus,
    ChecklistItemCode,
    DEFAULT_4POINT_CHECKLIST_SPECS,
    CreativeDecision,
)
from apps.creatives.validators import validate_and_sanitize_creative_file


def _log_audit_event(
    user: Optional[User],
    action: str,
    resource_id: str,
    changes: Optional[Dict[str, Any]] = None,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> None:
    """Helper to record immutable audit log entries."""
    AuditLog.objects.create(
        user=user,
        action=action,
        resource_type="CreativeRequest",
        resource_id=resource_id,
        changes=changes or {},
        correlation_id=correlation_id or "",
        ip_address=ip_address,
    )


@transaction.atomic
def create_creative_request(
    job_requirement: JobRequirement,
    user: User,
    title: str,
    deliverable_type: str = CreativeDeliverableType.COMBINED_PACK,
    priority: str = CreativePriority.MEDIUM,
    brief: str = "",
    target_audience: str = "",
    registration_link: str = "",
    qr_code_target_url: str = "",
    contact_email: str = "",
    contact_phone: str = "",
    production_deadline=None,
    assigned_designer: Optional[User] = None,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeRequest:
    """Create a new promotional creative request from an approved Job Requirement (Step 8).

    Validations:
    1. JobRequirement must be APPROVED and not archived.
    2. Prevents duplicate active requests for the exact same job and deliverable type.
    3. Auto-populates brief from approved JD attributes if not fully specified.
    4. Validates designer role if pre-assigned.
    """
    # 1. Validate Job Requirement state
    if job_requirement.status != JobRequirementStatus.APPROVED or job_requirement.is_archived:
        raise ValidationError(
            f"Creative requests can only be initiated for approved job requirements. "
            f"Current job status: '{job_requirement.status}'."
        )

    # 2. Check for duplicate active requests
    existing = CreativeRequest.objects.filter(
        job_requirement=job_requirement,
        deliverable_type=deliverable_type,
        is_archived=False,
    ).exclude(status=CreativeRequestStatus.CANCELLED).first()

    if existing:
        raise ValidationError(
            f"An active creative request already exists for this job requirement with deliverable type "
            f"'{existing.get_deliverable_type_display()}' (ID: {existing.id})."
        )

    # 3. Default brief generation from approved JD details if empty
    if not brief or not brief.strip():
        salary_str = f"{job_requirement.min_salary} - {job_requirement.max_salary} LPA" if job_requirement.min_salary and job_requirement.max_salary else "Disclosed during interview"
        brief = (
            f"Recruitment Drive Announcement for {job_requirement.company.name}\n"
            f"Role: {job_requirement.title}\n"
            f"Location: {job_requirement.location} ({job_requirement.get_work_arrangement_display()})\n"
            f"Package: {salary_str}\n"
            f"Eligibility: {job_requirement.eligibility_criteria}\n"
            f"Drive Date: {job_requirement.interview_date.strftime('%d %B %Y') if job_requirement.interview_date else 'TBA'}\n"
            f"Registration Deadline: {job_requirement.registration_deadline.strftime('%d %B %Y %I:%M %p')}\n"
            f"Instructions: Ensure official company logo and high-contrast QR code pointing to registration link."
        )

    # 4. Designer assignment validation
    initial_status = CreativeRequestStatus.DRAFT
    if assigned_designer:
        if not (assigned_designer.is_superuser or assigned_designer.has_any_role(RoleCatalog.CREATIVE_DESIGNER, RoleCatalog.ADMIN)):
            raise ValidationError(
                f"Assigned user '{assigned_designer.email}' does not hold the CREATIVE_DESIGNER role."
            )
        initial_status = CreativeRequestStatus.ASSIGNED

    # Fallback contact info from job if available
    if not contact_email and job_requirement.hr_contact and job_requirement.hr_contact.email:
        contact_email = job_requirement.hr_contact.email

    creative_req = CreativeRequest.objects.create(
        job_requirement=job_requirement,
        title=title.strip(),
        deliverable_type=deliverable_type,
        status=initial_status,
        priority=priority,
        brief=brief.strip(),
        target_audience=target_audience.strip(),
        registration_link=registration_link.strip(),
        qr_code_target_url=qr_code_target_url.strip(),
        contact_email=contact_email.strip(),
        contact_phone=contact_phone.strip(),
        production_deadline=production_deadline,
        assigned_designer=assigned_designer,
        created_by=user,
    )

    CreativeDecision.objects.create(
        request=creative_req,
        decision="CREATED",
        actor=user,
        actor_role=", ".join(user.get_active_roles()),
        comments=f"Creative request created for {creative_req.get_deliverable_type_display()}",
        snapshot_request_status=creative_req.status,
    )

    _log_audit_event(
        user=user,
        action="CREATIVE_REQUEST_CREATED",
        resource_id=str(creative_req.id),
        changes={"title": creative_req.title, "deliverable_type": deliverable_type, "status": creative_req.status},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    return creative_req


@transaction.atomic
def update_creative_brief(
    creative_req: CreativeRequest,
    user: User,
    data: Dict[str, Any],
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeRequest:
    """Update editable parameters of a creative brief."""
    if not creative_req.is_editable:
        raise ValidationError(
            f"Cannot update creative request in status '{creative_req.status}'. Approved or archived requests are locked."
        )

    editable_fields = {
        "title", "priority", "brief", "target_audience",
        "registration_link", "qr_code_target_url",
        "contact_email", "contact_phone", "production_deadline",
    }

    changes = {}
    for field in editable_fields:
        if field in data:
            old_val = getattr(creative_req, field)
            new_val = data[field]
            if old_val != new_val:
                changes[field] = {"old": str(old_val), "new": str(new_val)}
                setattr(creative_req, field, new_val)

    if changes:
        creative_req.save()
        _log_audit_event(
            user=user,
            action="CREATIVE_BRIEF_UPDATED",
            resource_id=str(creative_req.id),
            changes=changes,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )

    return creative_req


@transaction.atomic
def assign_designer(
    creative_req: CreativeRequest,
    designer: User,
    assigned_by: User,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeRequest:
    """Assign or reassign a Graphic Designer to a creative request (Step 8)."""
    if creative_req.is_locked:
        raise ValidationError("Cannot reassign designer on an already approved creative request.")

    if not (
        assigned_by.is_superuser
        or assigned_by.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER)
    ):
        raise PermissionDenied("Only Placement Officers, Placement Heads, or Admins can assign graphic designers.")

    if not (designer.is_superuser or designer.has_any_role(RoleCatalog.CREATIVE_DESIGNER, RoleCatalog.ADMIN)):
        raise ValidationError(f"User '{designer.email}' does not hold the CREATIVE_DESIGNER role.")

    old_designer = creative_req.assigned_designer
    creative_req.assigned_designer = designer

    # Advance status if in DRAFT
    if creative_req.status == CreativeRequestStatus.DRAFT:
        creative_req.status = CreativeRequestStatus.ASSIGNED

    creative_req.save(update_fields=["assigned_designer", "status", "updated_at"])

    CreativeDecision.objects.create(
        request=creative_req,
        decision="ASSIGNED",
        actor=assigned_by,
        actor_role=", ".join(assigned_by.get_active_roles()),
        comments=f"Assigned to {designer.full_name or designer.email}",
        snapshot_request_status=creative_req.status,
    )

    _log_audit_event(
        user=assigned_by,
        action="CREATIVE_DESIGNER_ASSIGNED",
        resource_id=str(creative_req.id),
        changes={
            "old_designer": old_designer.email if old_designer else None,
            "new_designer": designer.email,
        },
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    return creative_req


@transaction.atomic
def upload_asset_version(
    creative_req: CreativeRequest,
    uploaded_file: UploadedFile,
    designer_user: User,
    deliverable_type: Optional[str] = None,
    designer_notes: str = "",
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeAssetVersion:
    """Upload a new promotional asset revision with cryptographic verification (Steps 8 & 9).

    Validations & Actions:
    1. Validates request is editable.
    2. Validates uploaded file signature, magic bytes, dimensions, and size (<=10MB).
    3. Auto-increments version number monotonically (1, 2, 3...).
    4. Automatically initializes the authoritative 4-point design verification checklist in PENDING state.
    5. Advances request status to REVIEW_PENDING.
    """
    if not creative_req.is_editable:
        raise ValidationError(
            f"Cannot upload asset version to creative request in status '{creative_req.status}'. Request is locked."
        )

    # Permission check for designer
    user_roles = set(designer_user.get_active_roles())
    is_staff = designer_user.is_superuser or bool(user_roles & {RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER})
    if not is_staff:
        if creative_req.assigned_designer_id and creative_req.assigned_designer_id != designer_user.id:
            raise PermissionDenied("You can only upload asset versions to creative requests assigned to you.")

    # Validate file integrity and security
    meta = validate_and_sanitize_creative_file(uploaded_file)

    # Compute next monotonic version number
    max_ver = creative_req.versions.aggregate(m=models.Max("version_number"))["m"] or 0
    next_ver = max_ver + 1

    actual_deliverable = deliverable_type or creative_req.deliverable_type

    # Create Asset Version record
    version = CreativeAssetVersion.objects.create(
        request=creative_req,
        version_number=next_ver,
        deliverable_type=actual_deliverable,
        file=uploaded_file,
        file_name=meta["original_filename"],
        file_size_bytes=meta["file_size_bytes"],
        mime_type=meta["mime_type"],
        sha256_hash=meta["sha256_hash"],
        width_px=meta["width_px"],
        height_px=meta["height_px"],
        designer_notes=designer_notes.strip(),
        status=AssetVersionStatus.SUBMITTED,
        uploaded_by=designer_user,
    )

    # Auto-initialize the authoritative 4-Point Design Verification Checklist
    checklist_entities = [
        CreativeChecklistItem(
            version=version,
            item_code=spec["item_code"],
            title=spec["title"],
            description=spec["description"],
            is_mandatory=spec["is_mandatory"],
            status=ChecklistItemStatus.PENDING,
        )
        for spec in DEFAULT_4POINT_CHECKLIST_SPECS
    ]
    CreativeChecklistItem.objects.bulk_create(checklist_entities)

    # Advance request status to REVIEW_PENDING
    creative_req.status = CreativeRequestStatus.REVIEW_PENDING
    creative_req.save(update_fields=["status", "updated_at"])

    CreativeDecision.objects.create(
        request=creative_req,
        version=version,
        decision="SUBMITTED",
        actor=designer_user,
        actor_role=", ".join(designer_user.get_active_roles()),
        comments=designer_notes.strip() or f"Asset version v{next_ver} uploaded",
        snapshot_version_number=next_ver,
        snapshot_request_status=creative_req.status,
    )

    _log_audit_event(
        user=designer_user,
        action="CREATIVE_VERSION_UPLOADED",
        resource_id=str(creative_req.id),
        changes={
            "version_number": next_ver,
            "file_name": meta["original_filename"],
            "sha256_hash": meta["sha256_hash"],
            "file_size": meta["file_size_bytes"],
        },
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    return version


@transaction.atomic
def verify_checklist_item(
    version: CreativeAssetVersion,
    item_code: str,
    status: str,
    reviewer: User,
    remarks: str = "",
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeChecklistItem:
    """Verify an individual design checklist point for an asset version (Step 9)."""
    if version.is_approved:
        raise ValidationError("Cannot modify verification checklist of an already approved asset version.")

    if not (
        reviewer.is_superuser
        or reviewer.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER)
    ):
        raise PermissionDenied("Only Placement Officers, Placement Heads, or Admins can verify design checklist items.")

    item = version.checklist_items.filter(item_code=item_code).first()
    if not item:
        raise ValidationError(f"Checklist item '{item_code}' does not exist on this asset version.")

    if status not in (
        ChecklistItemStatus.VERIFIED,
        ChecklistItemStatus.REJECTED,
        ChecklistItemStatus.NOT_APPLICABLE,
        ChecklistItemStatus.PENDING,
    ):
        raise ValidationError(f"Invalid checklist status: {status}")

    old_status = item.status
    item.status = status
    item.verified_by = reviewer
    item.verified_at = timezone.now()
    item.remarks = remarks.strip()
    item.save(update_fields=["status", "verified_by", "verified_at", "remarks", "updated_at"])

    # If version was SUBMITTED, transition to IN_REVIEW
    if version.status == AssetVersionStatus.SUBMITTED:
        version.status = AssetVersionStatus.IN_REVIEW
        version.save(update_fields=["status", "updated_at"])

    _log_audit_event(
        user=reviewer,
        action="CREATIVE_CHECKLIST_VERIFIED",
        resource_id=str(version.request.id),
        changes={
            "version_number": version.version_number,
            "item_code": item_code,
            "old_status": old_status,
            "new_status": status,
            "remarks": remarks,
        },
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    return item


@transaction.atomic
def return_for_correction(
    version: CreativeAssetVersion,
    reviewer: User,
    feedback: str,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeAssetVersion:
    """Return an asset version to the designer for correction with mandatory feedback (Step 9)."""
    if version.is_approved:
        raise ValidationError("Cannot return an approved asset version for correction.")

    if not (
        reviewer.is_superuser
        or reviewer.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER)
    ):
        raise PermissionDenied("Only Placement Officers, Placement Heads, or Admins can return assets for correction.")

    if not feedback or not feedback.strip():
        raise ValidationError("Mandatory feedback comments are required when requesting revisions.")

    version.status = AssetVersionStatus.CHANGES_REQUESTED
    version.rejection_reason = feedback.strip()
    version.save(update_fields=["status", "rejection_reason", "updated_at"])

    request = version.request
    request.status = CreativeRequestStatus.CHANGES_REQUESTED
    request.save(update_fields=["status", "updated_at"])

    CreativeDecision.objects.create(
        request=request,
        version=version,
        decision="CHANGES_REQUESTED",
        actor=reviewer,
        actor_role=", ".join(reviewer.get_active_roles()),
        comments=feedback.strip(),
        snapshot_version_number=version.version_number,
        snapshot_request_status=request.status,
    )

    _log_audit_event(
        user=reviewer,
        action="CREATIVE_CHANGES_REQUESTED",
        resource_id=str(request.id),
        changes={"version_number": version.version_number, "feedback": feedback},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    return version


@transaction.atomic
def approve_asset_version(
    version: CreativeAssetVersion,
    approver: User,
    comments: str = "",
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeAssetVersion:
    """Formal Step 9 Creative Approval Gate by Placement Head or System Administrator.

    Strictly enforced gating:
    All 4 mandatory checklist criteria must evaluate to VERIFIED before approval.
    """
    if not (
        approver.is_superuser
        or approver.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
    ):
        raise PermissionDenied("Only the Placement Head or System Administrator can approve creative promotional assets.")

    # 4-Point Checklist Gating
    if not version.all_mandatory_verified:
        unverified = list(
            version.checklist_items.filter(is_mandatory=True)
            .exclude(status=ChecklistItemStatus.VERIFIED)
            .values_list("title", flat=True)
        )
        raise ValidationError(
            f"Cannot approve creative asset: All 4 mandatory verification checklist criteria must evaluate to VERIFIED. "
            f"Pending items: {', '.join(unverified)}"
        )

    # Approve this version
    version.is_approved = True
    version.status = AssetVersionStatus.APPROVED
    version.approved_by = approver
    version.approved_at = timezone.now()
    version.save(update_fields=["is_approved", "status", "approved_by", "approved_at", "updated_at"])

    # Update parent request
    request = version.request
    request.status = CreativeRequestStatus.APPROVED
    request.save(update_fields=["status", "updated_at"])

    CreativeDecision.objects.create(
        request=request,
        version=version,
        decision="APPROVED",
        actor=approver,
        actor_role=", ".join(approver.get_active_roles()),
        comments=comments.strip() or "4-point checklist verified; signed off for student publication broadcast.",
        snapshot_version_number=version.version_number,
        snapshot_request_status=request.status,
    )

    _log_audit_event(
        user=approver,
        action="CREATIVE_VERSION_APPROVED",
        resource_id=str(request.id),
        changes={
            "version_number": version.version_number,
            "status": "APPROVED",
            "comments": comments,
        },
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    return version


@transaction.atomic
def reject_asset_version(
    version: CreativeAssetVersion,
    user: User,
    rejection_reason: str,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeAssetVersion:
    """Formally reject an asset version with mandatory justification."""
    if not (
        user.is_superuser
        or user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
    ):
        raise PermissionDenied("Only the Placement Head or System Administrator can reject creative assets.")

    if not rejection_reason or not rejection_reason.strip():
        raise ValidationError("Mandatory justification comments required when rejecting a creative asset.")

    version.status = AssetVersionStatus.REJECTED
    version.rejection_reason = rejection_reason.strip()
    version.save(update_fields=["status", "rejection_reason", "updated_at"])

    request = version.request
    request.status = CreativeRequestStatus.REJECTED
    request.save(update_fields=["status", "updated_at"])

    CreativeDecision.objects.create(
        request=request,
        version=version,
        decision="REJECTED",
        actor=user,
        actor_role=", ".join(user.get_active_roles()),
        comments=rejection_reason.strip(),
        snapshot_version_number=version.version_number,
        snapshot_request_status=request.status,
    )

    _log_audit_event(
        user=user,
        action="CREATIVE_VERSION_REJECTED",
        resource_id=str(request.id),
        changes={"version_number": version.version_number, "reason": rejection_reason},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    return version


@transaction.atomic
def archive_creative_request(
    request: CreativeRequest,
    user: User,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeRequest:
    """Archive a completed or deprecated creative request."""
    if not (
        user.is_superuser
        or user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER)
    ):
        raise PermissionDenied("Only Placement Staff or Admins can archive creative requests.")

    request.is_archived = True
    request.save(update_fields=["is_archived", "updated_at"])

    _log_audit_event(
        user=user,
        action="CREATIVE_REQUEST_ARCHIVED",
        resource_id=str(request.id),
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return request


@transaction.atomic
def restore_creative_request(
    request: CreativeRequest,
    user: User,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> CreativeRequest:
    """Restore an archived creative request."""
    if not (
        user.is_superuser
        or user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD, RoleCatalog.PLACEMENT_OFFICER)
    ):
        raise PermissionDenied("Only Placement Staff or Admins can restore creative requests.")

    request.is_archived = False
    request.save(update_fields=["is_archived", "updated_at"])

    _log_audit_event(
        user=user,
        action="CREATIVE_REQUEST_RESTORED",
        resource_id=str(request.id),
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return request
