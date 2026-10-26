"""Transactional business services for Phase 2 Corporate CRM & HR Directory."""
from typing import Any, Dict, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.crm.models import (
    Company,
    CompanyRelationshipStatus,
    FollowUp,
    FollowUpStatus,
    HRContact,
    OutreachLog,
)


def log_crm_audit(
    *,
    user: Any,
    action: str,
    resource_type: str,
    resource_id: Any,
    changes: Optional[Dict[str, Any]] = None,
    correlation_id: str = "",
) -> None:
    """Helper to record immutable audit trail entries for CRM operations."""
    try:
        AuditLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            changes=changes or {},
            correlation_id=correlation_id,
        )
    except Exception:
        # Audit logging failure must never silently crash the critical business path
        pass


@transaction.atomic
def create_company(user: Any, validated_data: Dict[str, Any]) -> Company:
    """Create a new corporate company profile with normalization and audit trail."""
    owner = validated_data.pop("owner", None) or user
    company = Company.objects.create(
        owner=owner,
        created_by=user if getattr(user, "is_authenticated", False) else None,
        updated_by=user if getattr(user, "is_authenticated", False) else None,
        **validated_data,
    )
    log_crm_audit(
        user=user,
        action="COMPANY_CREATED",
        resource_type="Company",
        resource_id=company.id,
        changes={
            "name": company.name,
            "domain_category": company.domain_category,
            "relationship_status": company.relationship_status,
        },
    )
    return company


@transaction.atomic
def update_company(user: Any, company: Company, validated_data: Dict[str, Any]) -> Company:
    """Update company details and record field-level audit diff."""
    changes = {}
    for field, val in validated_data.items():
        old_val = getattr(company, field, None)
        if old_val != val:
            changes[field] = {"old": str(old_val), "new": str(val)}
            setattr(company, field, val)

    company.updated_by = user if getattr(user, "is_authenticated", False) else None
    company.save()

    if changes:
        log_crm_audit(
            user=user,
            action="COMPANY_UPDATED",
            resource_type="Company",
            resource_id=company.id,
            changes=changes,
        )
    return company


@transaction.atomic
def archive_company(user: Any, company: Company) -> Company:
    """Archive a company while preserving historical relationships."""
    company.is_archived = True
    company.updated_by = user if getattr(user, "is_authenticated", False) else None
    company.save()
    log_crm_audit(
        user=user,
        action="COMPANY_ARCHIVED",
        resource_type="Company",
        resource_id=company.id,
    )
    return company


@transaction.atomic
def restore_company(user: Any, company: Company) -> Company:
    """Restore an archived company."""
    company.is_archived = False
    company.updated_by = user if getattr(user, "is_authenticated", False) else None
    company.save()
    log_crm_audit(
        user=user,
        action="COMPANY_RESTORED",
        resource_type="Company",
        resource_id=company.id,
    )
    return company


@transaction.atomic
def create_hr_contact(user: Any, validated_data: Dict[str, Any]) -> HRContact:
    """Create a new HR contact associated with a valid corporate company."""
    company = validated_data.get("company")
    if not company:
        raise ValidationError({"company": "A contact must be associated with an existing company."})

    owner = validated_data.pop("owner", None) or user
    contact = HRContact.objects.create(
        owner=owner,
        created_by=user if getattr(user, "is_authenticated", False) else None,
        updated_by=user if getattr(user, "is_authenticated", False) else None,
        **validated_data,
    )
    log_crm_audit(
        user=user,
        action="HR_CONTACT_CREATED",
        resource_type="HRContact",
        resource_id=contact.id,
        changes={
            "name": contact.name,
            "company": str(contact.company.id),
            "designation": contact.designation,
            "email": contact.email,
        },
    )
    return contact


@transaction.atomic
def update_hr_contact(user: Any, contact: HRContact, validated_data: Dict[str, Any]) -> HRContact:
    """Update HR contact details and audit differences."""
    changes = {}
    for field, val in validated_data.items():
        old_val = getattr(contact, field, None)
        if old_val != val:
            changes[field] = {"old": str(old_val), "new": str(val)}
            setattr(contact, field, val)

    contact.updated_by = user if getattr(user, "is_authenticated", False) else None
    contact.save()

    if changes:
        log_crm_audit(
            user=user,
            action="HR_CONTACT_UPDATED",
            resource_type="HRContact",
            resource_id=contact.id,
            changes=changes,
        )
    return contact


@transaction.atomic
def archive_hr_contact(user: Any, contact: HRContact) -> HRContact:
    """Archive an HR contact."""
    contact.is_archived = True
    contact.updated_by = user if getattr(user, "is_authenticated", False) else None
    contact.save()
    log_crm_audit(
        user=user,
        action="HR_CONTACT_ARCHIVED",
        resource_type="HRContact",
        resource_id=contact.id,
    )
    return contact


@transaction.atomic
def restore_hr_contact(user: Any, contact: HRContact) -> HRContact:
    """Restore an archived HR contact."""
    contact.is_archived = False
    contact.updated_by = user if getattr(user, "is_authenticated", False) else None
    contact.save()
    log_crm_audit(
        user=user,
        action="HR_CONTACT_RESTORED",
        resource_type="HRContact",
        resource_id=contact.id,
    )
    return contact


@transaction.atomic
def record_outreach_activity(user: Any, validated_data: Dict[str, Any]) -> OutreachLog:
    """Record a completed multi-channel outreach touchpoint.

    Validates company and HR contact relationship integrity:
    if hr_contact is provided, it must belong to the selected company.
    """
    company = validated_data.get("company")
    contact = validated_data.get("hr_contact")

    if contact and contact.company_id != company.id:
        raise ValidationError(
            {"hr_contact": f"Contact '{contact.name}' does not belong to company '{company.name}'."}
        )

    outreach = OutreachLog.objects.create(
        performed_by=user,
        **validated_data,
    )

    # Optionally update company relationship status if newly connected
    if company.relationship_status == CompanyRelationshipStatus.DISCOVERED:
        company.relationship_status = CompanyRelationshipStatus.OUTREACH_IN_PROGRESS
        company.save(update_fields=["relationship_status", "updated_at"])

    log_crm_audit(
        user=user,
        action="OUTREACH_LOGGED",
        resource_type="OutreachLog",
        resource_id=outreach.id,
        changes={
            "company": str(company.id),
            "contact": str(contact.id) if contact else None,
            "channel": outreach.channel,
            "outcome": outreach.outcome,
        },
    )
    return outreach


@transaction.atomic
def schedule_follow_up(user: Any, validated_data: Dict[str, Any]) -> FollowUp:
    """Schedule a corporate follow-up task with relationship validation."""
    company = validated_data.get("company")
    contact = validated_data.get("hr_contact")

    if contact and contact.company_id != company.id:
        raise ValidationError(
            {"hr_contact": f"Contact '{contact.name}' does not belong to company '{company.name}'."}
        )

    assigned_to = validated_data.pop("assigned_to", None) or user

    follow_up = FollowUp.objects.create(
        assigned_to=assigned_to,
        created_by=user if getattr(user, "is_authenticated", False) else None,
        updated_by=user if getattr(user, "is_authenticated", False) else None,
        status=FollowUpStatus.OPEN,
        **validated_data,
    )
    log_crm_audit(
        user=user,
        action="FOLLOW_UP_SCHEDULED",
        resource_type="FollowUp",
        resource_id=follow_up.id,
        changes={
            "company": str(company.id),
            "due_date": follow_up.due_date.isoformat(),
            "priority": follow_up.priority,
            "assigned_to": str(assigned_to.id),
        },
    )
    return follow_up


@transaction.atomic
def reschedule_follow_up(
    user: Any, follow_up: FollowUp, new_due_date: Any, reason: str = ""
) -> FollowUp:
    """Reschedule an open or in-progress follow-up with incremented counter and audit log."""
    if follow_up.status in [FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED]:
        raise ValidationError(
            {"status": f"Cannot reschedule a follow-up with status '{follow_up.status}'."}
        )

    old_date = follow_up.due_date
    follow_up.due_date = new_due_date
    follow_up.rescheduled_count += 1
    follow_up.updated_by = user if getattr(user, "is_authenticated", False) else None
    follow_up.save()

    log_crm_audit(
        user=user,
        action="FOLLOW_UP_RESCHEDULED",
        resource_type="FollowUp",
        resource_id=follow_up.id,
        changes={
            "old_due_date": old_date.isoformat(),
            "new_due_date": new_due_date.isoformat() if hasattr(new_due_date, "isoformat") else str(new_due_date),
            "reason": reason,
            "rescheduled_count": follow_up.rescheduled_count,
        },
    )
    return follow_up


@transaction.atomic
def complete_follow_up(
    user: Any, follow_up: FollowUp, completion_notes: str = ""
) -> FollowUp:
    """Transition follow-up to COMPLETED status with completion timestamp and user reference."""
    if follow_up.status == FollowUpStatus.COMPLETED:
        raise ValidationError({"status": "This follow-up is already marked completed."})

    if follow_up.status == FollowUpStatus.CANCELLED:
        raise ValidationError({"status": "Cannot complete a cancelled follow-up."})

    follow_up.status = FollowUpStatus.COMPLETED
    follow_up.completed_at = timezone.now()
    follow_up.completed_by = user if getattr(user, "is_authenticated", False) else None
    follow_up.completion_notes = completion_notes
    follow_up.updated_by = user if getattr(user, "is_authenticated", False) else None
    follow_up.save()

    log_crm_audit(
        user=user,
        action="FOLLOW_UP_COMPLETED",
        resource_type="FollowUp",
        resource_id=follow_up.id,
        changes={
            "completed_by": str(user.id) if getattr(user, "id", None) else None,
            "completed_at": follow_up.completed_at.isoformat(),
        },
    )
    return follow_up


@transaction.atomic
def cancel_follow_up(
    user: Any, follow_up: FollowUp, cancellation_reason: str = ""
) -> FollowUp:
    """Cancel a follow-up with explicit cancellation reason."""
    if follow_up.status == FollowUpStatus.COMPLETED:
        raise ValidationError({"status": "Cannot cancel a completed follow-up without reopening."})

    follow_up.status = FollowUpStatus.CANCELLED
    follow_up.cancellation_reason = cancellation_reason
    follow_up.updated_by = user if getattr(user, "is_authenticated", False) else None
    follow_up.save()

    log_crm_audit(
        user=user,
        action="FOLLOW_UP_CANCELLED",
        resource_type="FollowUp",
        resource_id=follow_up.id,
        changes={"cancellation_reason": cancellation_reason},
    )
    return follow_up


@transaction.atomic
def reopen_follow_up(
    user: Any, follow_up: FollowUp, new_due_date: Any, reason: str = ""
) -> FollowUp:
    """Explicitly reopen a completed or cancelled follow-up as required by the business workflow."""
    follow_up.status = FollowUpStatus.OPEN
    follow_up.completed_at = None
    follow_up.completed_by = None
    follow_up.due_date = new_due_date
    follow_up.updated_by = user if getattr(user, "is_authenticated", False) else None
    follow_up.save()

    log_crm_audit(
        user=user,
        action="FOLLOW_UP_REOPENED",
        resource_type="FollowUp",
        resource_id=follow_up.id,
        changes={"reason": reason, "new_due_date": str(new_due_date)},
    )
    return follow_up
