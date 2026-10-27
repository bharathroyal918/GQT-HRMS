"""Transactional business services for Phase 2 Corporate CRM & HR Directory."""
from typing import Any, Dict, Optional
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.core.models import AuditLog
from apps.crm.models import (
    CaseEscalation,
    CaseEscalationStatus,
    Company,
    CompanyRelationshipStatus,
    CRMReconciliationRun,
    FollowUp,
    FollowUpReminderItem,
    FollowUpStatus,
    HRContact,
    OutreachLog,
    ReminderChannel,
    ReminderDeliveryStatus,
    StaffNotification,
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


def queue_follow_up_reminders(
    follow_up: FollowUp, user: Any = None, correlation_id: str = ""
) -> List[FollowUpReminderItem]:
    """Idempotently queue automated reminder items for a scheduled follow-up."""
    if not follow_up.remind_at or follow_up.reminder_channel == ReminderChannel.NONE:
        return []

    queued: List[FollowUpReminderItem] = []
    remind_timestamp = int(follow_up.remind_at.timestamp())

    # Resolve email recipient
    email_recipient = ""
    email_name = ""
    if follow_up.hr_contact and follow_up.hr_contact.email:
        email_recipient = follow_up.hr_contact.email
        email_name = follow_up.hr_contact.name
    elif follow_up.student and getattr(follow_up.student, "institutional_email", None):
        email_recipient = follow_up.student.institutional_email
        email_name = getattr(getattr(follow_up.student, "user", None), "full_name", "")
    elif follow_up.assigned_to and follow_up.assigned_to.email:
        email_recipient = follow_up.assigned_to.email
        email_name = follow_up.assigned_to.full_name

    # Resolve phone recipient
    phone_recipient = ""
    phone_name = ""
    if follow_up.hr_contact and follow_up.hr_contact.phone:
        phone_recipient = follow_up.hr_contact.phone
        phone_name = follow_up.hr_contact.name
    elif follow_up.student and getattr(follow_up.student, "phone_number", None):
        phone_recipient = follow_up.student.phone_number
        phone_name = getattr(getattr(follow_up.student, "user", None), "full_name", "")
    elif follow_up.assigned_to and getattr(follow_up.assigned_to, "phone_number", None):
        phone_recipient = follow_up.assigned_to.phone_number
        phone_name = follow_up.assigned_to.full_name

    # 1. Email Reminder
    if follow_up.reminder_channel in [ReminderChannel.EMAIL, ReminderChannel.BOTH] and email_recipient:
        email_key = f"REM-{follow_up.id}-EMAIL-{remind_timestamp}"
        item, created = FollowUpReminderItem.objects.get_or_create(
            idempotency_key=email_key,
            defaults={
                "follow_up": follow_up,
                "channel": "EMAIL",
                "recipient": email_recipient,
                "recipient_name": email_name,
                "scheduled_for": follow_up.remind_at,
                "status": ReminderDeliveryStatus.PENDING,
            },
        )
        if created:
            queued.append(item)

    # 2. WhatsApp Reminder
    if follow_up.reminder_channel in [ReminderChannel.WHATSAPP, ReminderChannel.BOTH] and phone_recipient:
        wa_key = f"REM-{follow_up.id}-WA-{remind_timestamp}"
        item, created = FollowUpReminderItem.objects.get_or_create(
            idempotency_key=wa_key,
            defaults={
                "follow_up": follow_up,
                "channel": "WHATSAPP",
                "recipient": phone_recipient,
                "recipient_name": phone_name,
                "scheduled_for": follow_up.remind_at,
                "status": ReminderDeliveryStatus.PENDING,
            },
        )
        if created:
            queued.append(item)

    return queued


@transaction.atomic
def schedule_follow_up(
    user: Any = None, validated_data: Optional[Dict[str, Any]] = None, **kwargs: Any
) -> FollowUp:
    """Schedule a corporate follow-up task with relationship validation and reminder queueing."""
    data = dict(validated_data or {})
    data.update(kwargs)

    actor = user or data.pop("created_by", None) or data.get("assigned_to")

    company = data.get("company")
    contact = data.get("hr_contact")

    if contact and company and contact.company_id != getattr(company, "id", None):
        raise ValidationError(
            {"hr_contact": f"Contact '{contact.name}' does not belong to company '{company.name}'."}
        )

    if not data.get("remind_at") and data.get("reminder_channel") and data.get("reminder_channel") != ReminderChannel.NONE:
        data["remind_at"] = data.get("due_date")

    assigned_to = data.pop("assigned_to", None) or actor

    follow_up = FollowUp.objects.create(
        assigned_to=assigned_to,
        created_by=actor if getattr(actor, "is_authenticated", False) else None,
        updated_by=actor if getattr(actor, "is_authenticated", False) else None,
        status=FollowUpStatus.OPEN,
        **data,
    )

    # Queue automated reminders if requested
    queue_follow_up_reminders(follow_up, user=actor)

    log_crm_audit(
        user=actor,
        action="FOLLOW_UP_SCHEDULED",
        resource_type="FollowUp",
        resource_id=follow_up.id,
        changes={
            "company": str(getattr(company, "id", company)) if company else None,
            "due_date": follow_up.due_date.isoformat(),
            "priority": follow_up.priority,
            "assigned_to": str(getattr(assigned_to, "id", assigned_to)) if assigned_to else None,
            "category": follow_up.category,
            "reminder_channel": follow_up.reminder_channel,
        },
    )
    return follow_up


@transaction.atomic
def reschedule_follow_up(
    user: Any = None,
    follow_up: Optional[FollowUp] = None,
    new_due_date: Any = None,
    reason: str = "",
    new_remind_at: Optional[Any] = None,
    actor: Any = None,
    **kwargs: Any,
) -> FollowUp:
    """Reschedule an open or in-progress follow-up with incremented counter and audit log."""
    if isinstance(user, FollowUp):
        target_fu = user
        operator = actor or getattr(target_fu, "assigned_to", None)
    else:
        operator = user or actor
        target_fu = follow_up or kwargs.get("target")

    if not target_fu:
        raise ValidationError({"follow_up": "A valid follow_up instance is required."})

    if target_fu.status in [FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED]:
        raise ValidationError(
            {"status": f"Cannot reschedule a follow-up with status '{target_fu.status}'."}
        )

    old_date = target_fu.due_date
    target_fu.due_date = new_due_date
    target_fu.rescheduled_count += 1
    if new_remind_at is not None:
        target_fu.remind_at = new_remind_at
    elif target_fu.remind_at:
        target_fu.remind_at = new_due_date
    target_fu.updated_by = operator if getattr(operator, "is_authenticated", False) else None
    target_fu.save()

    # Cancel obsolete pending reminders and queue updated ones
    target_fu.reminder_items.filter(status=ReminderDeliveryStatus.PENDING).update(
        status=ReminderDeliveryStatus.CANCELLED,
        error_message="Obsolete due to rescheduling",
        updated_at=timezone.now(),
    )
    queue_follow_up_reminders(target_fu, user=operator)

    log_crm_audit(
        user=operator,
        action="FOLLOW_UP_RESCHEDULED",
        resource_type="FollowUp",
        resource_id=target_fu.id,
        changes={
            "old_due_date": old_date.isoformat(),
            "new_due_date": new_due_date.isoformat() if hasattr(new_due_date, "isoformat") else str(new_due_date),
            "reason": reason,
            "rescheduled_count": target_fu.rescheduled_count,
        },
    )
    return target_fu


@transaction.atomic
def complete_follow_up(
    user: Any = None,
    follow_up: Optional[FollowUp] = None,
    completion_notes: str = "",
    actor: Any = None,
    notes: str = "",
    **kwargs: Any,
) -> FollowUp:
    """Transition follow-up to COMPLETED status with completion timestamp and cancel pending reminders."""
    if isinstance(user, FollowUp):
        target_fu = user
        operator = actor or getattr(target_fu, "assigned_to", None)
    else:
        operator = user or actor
        target_fu = follow_up or kwargs.get("target")

    if not target_fu:
        raise ValidationError({"follow_up": "A valid follow_up instance is required."})

    notes_val = completion_notes or notes

    if target_fu.status == FollowUpStatus.COMPLETED:
        raise ValidationError({"status": "This follow-up is already marked completed."})

    if target_fu.status == FollowUpStatus.CANCELLED:
        raise ValidationError({"status": "Cannot complete a cancelled follow-up."})

    target_fu.status = FollowUpStatus.COMPLETED
    target_fu.completed_at = timezone.now()
    target_fu.completed_by = operator if getattr(operator, "is_authenticated", False) else None
    target_fu.completion_notes = notes_val
    target_fu.updated_by = operator if getattr(operator, "is_authenticated", False) else None
    target_fu.save()

    # Cancel any pending reminder items
    target_fu.reminder_items.filter(status=ReminderDeliveryStatus.PENDING).update(
        status=ReminderDeliveryStatus.CANCELLED,
        error_message="Cancelled on follow-up completion",
        updated_at=timezone.now(),
    )

    log_crm_audit(
        user=operator,
        action="FOLLOW_UP_COMPLETED",
        resource_type="FollowUp",
        resource_id=target_fu.id,
        changes={
            "completed_by": str(operator.id) if getattr(operator, "id", None) else None,
            "completed_at": target_fu.completed_at.isoformat(),
        },
    )
    return target_fu


@transaction.atomic
def cancel_follow_up(
    user: Any = None,
    follow_up: Optional[FollowUp] = None,
    cancellation_reason: str = "",
    actor: Any = None,
    reason: str = "",
    **kwargs: Any,
) -> FollowUp:
    """Cancel a follow-up with explicit cancellation reason and cancel pending reminders."""
    if isinstance(user, FollowUp):
        target_fu = user
        operator = actor or getattr(target_fu, "assigned_to", None)
    else:
        operator = user or actor
        target_fu = follow_up or kwargs.get("target")

    if not target_fu:
        raise ValidationError({"follow_up": "A valid follow_up instance is required."})

    reason_val = cancellation_reason or reason

    if target_fu.status == FollowUpStatus.COMPLETED:
        raise ValidationError({"status": "Cannot cancel a completed follow-up without reopening."})

    target_fu.status = FollowUpStatus.CANCELLED
    target_fu.cancellation_reason = reason_val
    target_fu.updated_by = operator if getattr(operator, "is_authenticated", False) else None
    target_fu.save()

    # Cancel any pending reminder items
    target_fu.reminder_items.filter(status=ReminderDeliveryStatus.PENDING).update(
        status=ReminderDeliveryStatus.CANCELLED,
        error_message="Cancelled on follow-up cancellation",
        updated_at=timezone.now(),
    )

    log_crm_audit(
        user=operator,
        action="FOLLOW_UP_CANCELLED",
        resource_type="FollowUp",
        resource_id=target_fu.id,
        changes={
            "cancellation_reason": reason_val,
        },
    )
    return target_fu


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


# ==============================================================================
# Phase 10: CRM Database Update & Reconciliation Services
# ==============================================================================

@transaction.atomic
def run_crm_database_reconciliation(
    user: Any = None,
    dry_run: bool = False,
    correlation_id: str = "",
) -> Dict[str, Any]:
    """Execute Phase 10 CRM database integration & reconciliation.

    1. Executes full health diagnostic across the 8 data areas.
    2. Identifies cross-module discrepancies without destructive merging or data loss.
    3. Safely synchronizes consistent states:
       - Promotes companies with verified candidate selections to ACTIVE_HIRING_PARTNER.
    4. Persists CRMReconciliationRun audit record.
    5. Emits immutable AuditLog entry.
    6. Returns structured summary and diagnostic payload.
    """
    from apps.placements.models import CandidatePlacementStatus
    from apps.crm.selectors import get_crm_database_health_diagnostics

    records_synchronized = 0
    synchronized_companies = []

    if not dry_run:
        # Safe reconciliation rule: promote companies with verified candidate selections
        placed_company_ids = set(
            CandidatePlacementStatus.objects.filter(
                status="SELECTED"
            ).values_list("company_id", flat=True)
        )
        companies_to_promote = Company.objects.filter(
            id__in=placed_company_ids,
            is_deleted=False,
        ).exclude(relationship_status=CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER)

        for comp in companies_to_promote:
            old_status = comp.relationship_status
            comp.relationship_status = CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER
            comp.updated_by = user if getattr(user, "is_authenticated", False) else None
            comp.save(update_fields=["relationship_status", "updated_by", "updated_at"])
            records_synchronized += 1
            synchronized_companies.append({
                "company_id": str(comp.id),
                "name": comp.name,
                "old_status": old_status,
                "new_status": CompanyRelationshipStatus.ACTIVE_HIRING_PARTNER,
            })

    diagnostics = get_crm_database_health_diagnostics()
    total_checked = diagnostics["summary"]["total_records_checked"]
    total_conflicts = diagnostics["summary"]["total_conflicts"]

    run_status = "SUCCESS" if total_conflicts == 0 else "PARTIAL_WITH_CONFLICTS"
    mode_str = "DRY-RUN" if dry_run else "LIVE"
    summary_text = (
        f"Phase 10 CRM Reconciliation [{mode_str}] completed. "
        f"Checked {total_checked} records across 8 areas. "
        f"Synchronized {records_synchronized} records. "
        f"Identified {total_conflicts} items requiring authorized review."
    )

    reconciliation_run = CRMReconciliationRun.objects.create(
        triggered_by=user if getattr(user, "is_authenticated", False) else None,
        status=run_status,
        total_records_checked=total_checked,
        conflicts_detected=total_conflicts,
        records_synchronized=records_synchronized,
        diagnostic_details={
            **diagnostics,
            "dry_run": dry_run,
            "synchronized_companies": synchronized_companies,
        },
        summary=summary_text,
    )

    log_crm_audit(
        user=user,
        action="CRM_RECONCILIATION_EXECUTED",
        resource_type="CRMReconciliationRun",
        resource_id=reconciliation_run.id,
        changes={
            "dry_run": dry_run,
            "status": run_status,
            "total_records_checked": total_checked,
            "conflicts_detected": total_conflicts,
            "records_synchronized": records_synchronized,
            "summary": summary_text,
        },
        correlation_id=correlation_id,
    )

    return {
        "run_id": str(reconciliation_run.id),
        "status": run_status,
        "dry_run": dry_run,
        "total_records_checked": total_checked,
        "conflicts_detected": total_conflicts,
        "records_synchronized": records_synchronized,
        "summary": summary_text,
        "created_at": reconciliation_run.created_at.isoformat(),
        "diagnostics": diagnostics,
    }


# ==============================================================================
# Phase 12: Automated Follow-Up & Escalation Services
# ==============================================================================

@transaction.atomic
def acknowledge_case_escalation(
    user: Any,
    escalation: CaseEscalation,
    notes: str = "",
) -> CaseEscalation:
    """Acknowledge a pending case escalation by an authorized officer."""
    if escalation.status != CaseEscalationStatus.PENDING:
        raise ValidationError(
            {"status": f"Cannot acknowledge an escalation in status '{escalation.status}'."}
        )

    escalation.status = CaseEscalationStatus.ACKNOWLEDGED
    escalation.acknowledged_at = timezone.now()
    escalation.acknowledged_by = user if getattr(user, "is_authenticated", False) else None
    if notes:
        escalation.resolution_notes = f"[Acknowledged Notes]: {notes}"
    escalation.save(update_fields=["status", "acknowledged_at", "acknowledged_by", "resolution_notes", "updated_at"])

    log_crm_audit(
        user=user,
        action="CASE_ESCALATION_ACKNOWLEDGED",
        resource_type="CaseEscalation",
        resource_id=escalation.id,
        changes={
            "status": CaseEscalationStatus.ACKNOWLEDGED,
            "acknowledged_by": str(user.id) if getattr(user, "id", None) else None,
            "notes": notes,
        },
    )
    return escalation


@transaction.atomic
def resolve_case_escalation(
    user: Any,
    escalation: CaseEscalation,
    resolution_notes: str,
) -> CaseEscalation:
    """Resolve an escalation with mandatory documented resolution notes."""
    if not resolution_notes or len(resolution_notes.strip()) < 5:
        raise ValidationError(
            {"resolution_notes": "Documented resolution notes (min 5 characters) are required."}
        )

    if escalation.status in [CaseEscalationStatus.RESOLVED, CaseEscalationStatus.DISMISSED]:
        raise ValidationError(
            {"status": f"This escalation is already '{escalation.status}'."}
        )

    escalation.status = CaseEscalationStatus.RESOLVED
    escalation.resolved_at = timezone.now()
    escalation.resolved_by = user if getattr(user, "is_authenticated", False) else None
    escalation.resolution_notes = resolution_notes.strip()
    escalation.save(update_fields=["status", "resolved_at", "resolved_by", "resolution_notes", "updated_at"])

    log_crm_audit(
        user=user,
        action="CASE_ESCALATION_RESOLVED",
        resource_type="CaseEscalation",
        resource_id=escalation.id,
        changes={
            "status": CaseEscalationStatus.RESOLVED,
            "resolved_by": str(user.id) if getattr(user, "id", None) else None,
            "resolution_notes": resolution_notes,
        },
    )
    return escalation


@transaction.atomic
def mark_notification_as_read(
    user: Any,
    notification: StaffNotification,
) -> StaffNotification:
    """Mark an individual staff notification as read for the recipient user."""
    if notification.recipient_id != getattr(user, "id", None) and not getattr(user, "is_superuser", False):
        raise ValidationError({"recipient": "Cannot modify notifications belonging to another user."})

    if not notification.is_read:
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save(update_fields=["is_read", "read_at", "updated_at"])

    return notification


@transaction.atomic
def mark_all_notifications_as_read(user: Any) -> int:
    """Mark all unread notifications for a user as read."""
    unread_qs = StaffNotification.objects.filter(recipient=user, is_read=False)
    now = timezone.now()
    updated_count = unread_qs.update(is_read=True, read_at=now, updated_at=now)
    return updated_count


@transaction.atomic
def retry_failed_reminder_item(
    user: Any,
    reminder_item: FollowUpReminderItem,
) -> FollowUpReminderItem:
    """Manually re-queue a failed automated follow-up reminder item."""
    if reminder_item.status not in [ReminderDeliveryStatus.FAILED, ReminderDeliveryStatus.CANCELLED]:
        raise ValidationError(
            {"status": f"Only failed or cancelled reminders can be re-queued (current: {reminder_item.status})."}
        )

    reminder_item.status = ReminderDeliveryStatus.PENDING
    reminder_item.attempt_count = 0
    reminder_item.backoff_until = None
    reminder_item.scheduled_for = timezone.now()
    reminder_item.error_message = f"Manually re-queued by {getattr(user, 'email', 'Staff')}."
    reminder_item.save(update_fields=["status", "attempt_count", "backoff_until", "scheduled_for", "error_message", "updated_at"])

    log_crm_audit(
        user=user,
        action="REMINDER_ITEM_RETRY_QUEUED",
        resource_type="FollowUpReminderItem",
        resource_id=reminder_item.id,
        changes={"scheduled_for": reminder_item.scheduled_for.isoformat()},
    )
    return reminder_item

