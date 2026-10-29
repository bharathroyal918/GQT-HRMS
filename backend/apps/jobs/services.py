"""Transactional Service Layer for Job Requirements & Verification (Phase 3)."""
import logging
from typing import Any, Dict, List, Optional
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from apps.accounts.models import RoleCatalog, User
from apps.core.models import AuditLog
from apps.crm.models import Company, HRContact
from apps.jobs.models import (
    DEFAULT_CHECKLIST_SPECS,
    ChecklistItemCode,
    ChecklistItemStatus,
    JobApprovalDecision,
    JobChecklistItem,
    JobRequirement,
    JobRequirementStatus,
)

logger = logging.getLogger(__name__)


def _log_audit_event(
    user: Optional[User],
    action: str,
    resource_id: str,
    changes: Dict[str, Any],
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> None:
    """Record immutable audit event in core_audit_log."""
    AuditLog.objects.create(
        user=user,
        action=action,
        resource_type="JobRequirement",
        resource_id=str(resource_id),
        changes=changes,
        correlation_id=correlation_id,
        ip_address=ip_address,
    )


@transaction.atomic
def create_job_requirement(
    company: Company,
    title: str,
    job_description: str,
    skills_required: str,
    location: str,
    registration_deadline: Any,
    created_by: Optional[User] = None,
    hr_contact: Optional[HRContact] = None,
    min_salary: Optional[Any] = None,
    max_salary: Optional[Any] = None,
    salary_currency: str = "INR",
    salary_breakup: str = "",
    work_arrangement: str = "ON_SITE",
    employment_type: str = "FULL_TIME",
    has_bond: bool = False,
    bond_details: str = "",
    eligibility_criteria: str = "",
    min_cgpa: Optional[Any] = None,
    hiring_process: str = "",
    interview_date: Optional[Any] = None,
    openings_count: int = 1,
    notes: str = "",
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Create a new Job Requirement draft and initialize its 5-point verification checklist."""
    # Validate company-contact relationship
    if hr_contact and hr_contact.company_id != company.id:
        raise ValidationError(
            f"HR Contact '{hr_contact.name}' does not belong to Company '{company.name}'."
        )

    # Validate salary range
    if min_salary is not None and max_salary is not None:
        if min_salary > max_salary:
            raise ValidationError("Minimum salary cannot exceed maximum salary.")

    job = JobRequirement.objects.create(
        company=company,
        hr_contact=hr_contact,
        title=title.strip(),
        job_description=job_description.strip(),
        skills_required=skills_required.strip(),
        min_salary=min_salary,
        max_salary=max_salary,
        salary_currency=salary_currency,
        salary_breakup=salary_breakup.strip(),
        location=location.strip(),
        work_arrangement=work_arrangement,
        employment_type=employment_type,
        has_bond=has_bond,
        bond_details=bond_details.strip(),
        eligibility_criteria=eligibility_criteria.strip(),
        min_cgpa=min_cgpa,
        hiring_process=hiring_process.strip(),
        interview_date=interview_date,
        registration_deadline=registration_deadline,
        openings_count=openings_count,
        status=JobRequirementStatus.DRAFT,
        created_by=created_by,
        notes=notes.strip(),
    )

    # Initialize the authoritative 5-point verification checklist (Step 6)
    checklist_objs = [
        JobChecklistItem(
            job_requirement=job,
            item_code=spec["item_code"],
            title=spec["title"],
            description=spec["description"],
            is_mandatory=spec["is_mandatory"],
            status=ChecklistItemStatus.PENDING,
        )
        for spec in DEFAULT_CHECKLIST_SPECS
    ]
    JobChecklistItem.objects.bulk_create(checklist_objs)

    _log_audit_event(
        user=created_by,
        action="JOB_REQUIREMENT_CREATED",
        resource_id=str(job.id),
        changes={
            "title": job.title,
            "company": str(company.name),
            "status": job.status,
            "checklist_items_initialized": len(checklist_objs),
        },
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return job


@transaction.atomic
def update_job_requirement(
    job: JobRequirement,
    updated_by: Optional[User],
    data: Dict[str, Any],
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Update editable fields of a draft or returned requirement."""
    if not job.is_editable:
        raise ValidationError(
            f"Job Requirement is in '{job.status}' status and cannot be modified. "
            "Only DRAFT or CHANGES_REQUESTED requirements can be edited."
        )

    # Validate company/contact relationship if updated
    company = data.get("company", job.company)
    hr_contact = data.get("hr_contact", job.hr_contact)
    if hr_contact and hr_contact.company_id != company.id:
        raise ValidationError(
            f"HR Contact does not belong to Company '{company.name}'."
        )

    # Validate salary range
    min_salary = data.get("min_salary", job.min_salary)
    max_salary = data.get("max_salary", job.max_salary)
    if min_salary is not None and max_salary is not None:
        if min_salary > max_salary:
            raise ValidationError("Minimum salary cannot exceed maximum salary.")

    changes = {}
    editable_fields = [
        "title",
        "job_description",
        "skills_required",
        "min_salary",
        "max_salary",
        "salary_currency",
        "salary_breakup",
        "location",
        "work_arrangement",
        "employment_type",
        "has_bond",
        "bond_details",
        "eligibility_criteria",
        "min_cgpa",
        "hiring_process",
        "interview_date",
        "registration_deadline",
        "openings_count",
        "notes",
        "hr_contact",
    ]

    for field in editable_fields:
        if field in data:
            old_val = getattr(job, field)
            new_val = data[field]
            if old_val != new_val:
                changes[field] = {"old": str(old_val), "new": str(new_val)}
                setattr(job, field, new_val)

    if changes:
        job.save()
        _log_audit_event(
            user=updated_by,
            action="JOB_REQUIREMENT_UPDATED",
            resource_id=str(job.id),
            changes=changes,
            correlation_id=correlation_id,
            ip_address=ip_address,
        )

    return job


@transaction.atomic
def submit_for_verification(
    job: JobRequirement,
    user: User,
    comments: str = "",
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Submit a draft or corrected job requirement for checklist verification (Step 6)."""
    if job.status not in (JobRequirementStatus.DRAFT, JobRequirementStatus.CHANGES_REQUESTED):
        raise ValidationError(
            f"Cannot submit job in status '{job.status}'. Only DRAFT or CHANGES_REQUESTED can be submitted."
        )

    if not job.title or not job.job_description or not job.location or not job.registration_deadline:
        raise ValidationError("Title, description, location, and registration deadline are mandatory for submission.")

    old_status = job.status
    job.status = JobRequirementStatus.PENDING_VERIFICATION
    job.save(update_fields=["status", "updated_at"])

    # Record decision log
    JobApprovalDecision.objects.create(
        job_requirement=job,
        decision="SUBMITTED",
        actor=user,
        actor_role=", ".join(user.get_active_roles()),
        comments=comments.strip(),
    )

    _log_audit_event(
        user=user,
        action="JOB_SUBMITTED_FOR_VERIFICATION",
        resource_id=str(job.id),
        changes={"old_status": old_status, "new_status": job.status, "comments": comments},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return job


@transaction.atomic
def verify_checklist_item(
    job: JobRequirement,
    item_id: str,
    status: str,
    user: User,
    remarks: str = "",
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobChecklistItem:
    """Verify an individual checklist item (Step 6) and advance job status if criteria met."""
    if job.status == JobRequirementStatus.APPROVED:
        raise ValidationError("Cannot modify verification checklist of an already approved job.")

    item = job.checklist_items.filter(id=item_id).first()
    if not item:
        raise ValidationError("Checklist item does not exist on this job requirement.")

    if status not in (
        ChecklistItemStatus.VERIFIED,
        ChecklistItemStatus.REJECTED,
        ChecklistItemStatus.NOT_APPLICABLE,
        ChecklistItemStatus.PENDING,
    ):
        raise ValidationError(f"Invalid checklist item status: {status}")

    old_status = item.status
    item.status = status
    item.verified_by = user
    item.verified_at = timezone.now()
    item.remarks = remarks.strip()
    item.save(update_fields=["status", "verified_by", "verified_at", "remarks", "updated_at"])

    # Advance job status:
    # 1. If currently in PENDING_VERIFICATION, transition to UNDER_REVIEW
    if job.status == JobRequirementStatus.PENDING_VERIFICATION:
        job.status = JobRequirementStatus.UNDER_REVIEW
        job.save(update_fields=["status", "updated_at"])

    # 2. If all mandatory items are now VERIFIED, transition job status to VERIFIED
    if job.all_mandatory_verified:
        job.status = JobRequirementStatus.VERIFIED
        job.verified_by = user
        job.verified_at = timezone.now()
        job.save(update_fields=["status", "verified_by", "verified_at", "updated_at"])
    elif job.status == JobRequirementStatus.VERIFIED:
        # A previously verified item was reverted/rejected; regress back to UNDER_REVIEW
        job.status = JobRequirementStatus.UNDER_REVIEW
        job.save(update_fields=["status", "updated_at"])

    _log_audit_event(
        user=user,
        action="JOB_CHECKLIST_ITEM_VERIFIED",
        resource_id=str(job.id),
        changes={
            "item_code": item.item_code,
            "old_status": old_status,
            "new_status": status,
            "remarks": remarks,
            "job_status": job.status,
        },
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return item


@transaction.atomic
def return_for_correction(
    job: JobRequirement,
    user: User,
    reason: str,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Return requirement back to Placement Officer for correction (Step 6/7)."""
    if not reason or not reason.strip():
        raise ValidationError("A mandatory reason must be provided when requesting changes.")

    if job.status == JobRequirementStatus.APPROVED:
        raise ValidationError("Cannot return an already approved job. Use reopen instead.")

    old_status = job.status
    job.status = JobRequirementStatus.CHANGES_REQUESTED
    job.return_reason = reason.strip()
    job.save(update_fields=["status", "return_reason", "updated_at"])

    JobApprovalDecision.objects.create(
        job_requirement=job,
        decision="CHANGES_REQUESTED",
        actor=user,
        actor_role=", ".join(user.get_active_roles()),
        comments=reason.strip(),
    )

    _log_audit_event(
        user=user,
        action="JOB_RETURNED_FOR_CORRECTION",
        resource_id=str(job.id),
        changes={"old_status": old_status, "new_status": job.status, "reason": reason},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return job


@transaction.atomic
def approve_job_requirement(
    job: JobRequirement,
    approver: User,
    comments: str = "",
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Placement Head or Admin formal sign-off (Step 7). Locks requirement for creatives."""
    # Authorization check
    if not (
        approver.is_superuser
        or approver.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
    ):
        raise PermissionDenied("Only the Placement Head or System Administrator can approve job opportunities.")

    # Condition: All 5 mandatory checklist criteria must evaluate to VERIFIED
    if not job.all_mandatory_verified:
        unverified = list(
            job.checklist_items.filter(is_mandatory=True)
            .exclude(status=ChecklistItemStatus.VERIFIED)
            .values_list("title", flat=True)
        )
        raise ValidationError(
            f"Cannot approve job requirement: All mandatory verification checklist items must evaluate to VERIFIED. "
            f"Pending items: {', '.join(unverified)}"
        )

    old_status = job.status
    job.status = JobRequirementStatus.APPROVED
    job.approved_by = approver
    job.approved_at = timezone.now()
    job.save(update_fields=["status", "approved_by", "approved_at", "updated_at"])

    JobApprovalDecision.objects.create(
        job_requirement=job,
        decision="APPROVED",
        actor=approver,
        actor_role=", ".join(approver.get_active_roles()),
        comments=comments.strip(),
    )

    _log_audit_event(
        user=approver,
        action="JOB_REQUIREMENT_APPROVED",
        resource_id=str(job.id),
        changes={"old_status": old_status, "new_status": job.status, "comments": comments},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )

    # Phase 15 WS3: In-app notification to job author if distinct
    try:
        if job.created_by and getattr(job.created_by, "is_active", False) and job.created_by != approver:
            from apps.core.models import NotificationCategory
            from apps.core.services_notifications import create_notification
            create_notification(
                recipient=job.created_by,
                category=NotificationCategory.JOB_DRIVE,
                title=f"Job Requirement Approved: {job.title}",
                message=f"Job requirement '{job.title}' for {job.company.name} was approved by {approver.full_name or approver.email}.",
                link="/jobs",
                metadata={"job_id": str(job.id), "company_id": str(job.company_id)},
                idempotency_key=f"NOTIF-JOB-APPROVE-{job.id}",
            )
    except Exception as exc:
        logger.warning("Failed to dispatch in-app notification for job %s: %s", job.id, exc)

    return job


@transaction.atomic
def reject_job_requirement(
    job: JobRequirement,
    user: User,
    rejection_reason: str,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Formally reject a job requirement (Step 7)."""
    if not (
        user.is_superuser
        or user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
    ):
        raise PermissionDenied("Only the Placement Head or System Administrator can reject job opportunities.")

    if not rejection_reason or not rejection_reason.strip():
        raise ValidationError("A documented rejection reason is mandatory.")

    old_status = job.status
    job.status = JobRequirementStatus.REJECTED
    job.rejection_reason = rejection_reason.strip()
    job.save(update_fields=["status", "rejection_reason", "updated_at"])

    JobApprovalDecision.objects.create(
        job_requirement=job,
        decision="REJECTED",
        actor=user,
        actor_role=", ".join(user.get_active_roles()),
        comments=rejection_reason.strip(),
    )

    _log_audit_event(
        user=user,
        action="JOB_REQUIREMENT_REJECTED",
        resource_id=str(job.id),
        changes={"old_status": old_status, "new_status": job.status, "reason": rejection_reason},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return job


@transaction.atomic
def reopen_job_requirement(
    job: JobRequirement,
    user: User,
    comments: str,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Explicit authorized reopening of an approved or rejected job for re-verification."""
    if not (
        user.is_superuser
        or user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
    ):
        raise PermissionDenied("Only the Placement Head or Admin can reopen locked or finalized requirements.")

    if not comments or not comments.strip():
        raise ValidationError("Mandatory justification comments required when reopening a requirement.")

    old_status = job.status
    # Reopen into UNDER_REVIEW so checklist can be audited or corrected
    job.status = JobRequirementStatus.UNDER_REVIEW
    job.approved_at = None
    job.approved_by = None
    job.save(update_fields=["status", "approved_at", "approved_by", "updated_at"])

    JobApprovalDecision.objects.create(
        job_requirement=job,
        decision="REOPENED",
        actor=user,
        actor_role=", ".join(user.get_active_roles()),
        comments=comments.strip(),
    )

    _log_audit_event(
        user=user,
        action="JOB_REQUIREMENT_REOPENED",
        resource_id=str(job.id),
        changes={"old_status": old_status, "new_status": job.status, "comments": comments},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return job


@transaction.atomic
def archive_job_requirement(
    job: JobRequirement,
    user: User,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Soft-archive a job requirement."""
    if not (
        user.is_superuser
        or user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
    ):
        raise PermissionDenied("Only Placement Head or Admin can archive job requirements.")

    job.is_archived = True
    job.save(update_fields=["is_archived", "updated_at"])

    _log_audit_event(
        user=user,
        action="JOB_REQUIREMENT_ARCHIVED",
        resource_id=str(job.id),
        changes={"is_archived": True},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return job


@transaction.atomic
def restore_job_requirement(
    job: JobRequirement,
    user: User,
    correlation_id: str = "",
    ip_address: Optional[str] = None,
) -> JobRequirement:
    """Restore a previously archived job requirement."""
    if not (
        user.is_superuser
        or user.has_any_role(RoleCatalog.ADMIN, RoleCatalog.PLACEMENT_HEAD)
    ):
        raise PermissionDenied("Only Placement Head or Admin can restore job requirements.")

    job.is_archived = False
    job.save(update_fields=["is_archived", "updated_at"])

    _log_audit_event(
        user=user,
        action="JOB_REQUIREMENT_RESTORED",
        resource_id=str(job.id),
        changes={"is_archived": False},
        correlation_id=correlation_id,
        ip_address=ip_address,
    )
    return job
