"""Automated Follow-Up Background Scheduler and Execution Engine (Phase 12).

Implements the five official workflow capabilities:
1. Schedule Follow-ups (Trigger processing)
2. Reminder Emails (Safe background queue & delivery)
3. WhatsApp Messages (Provider abstraction & templates)
4. Placement Officer Notifications (In-app alerts for due/overdue/failed events)
5. Escalation for Pending Cases (Auditable SLA breach & failed delivery escalations)
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connection, transaction
from django.utils import timezone

from apps.accounts.models import RoleCatalog
from apps.core.models import AuditLog
from apps.crm.adapters.email import get_email_adapter
from apps.crm.adapters.whatsapp import get_whatsapp_adapter
from apps.crm.models import (
    CaseEscalation,
    CaseEscalationLevel,
    CaseEscalationStatus,
    CaseEscalationType,
    CRMConfiguration,
    FollowUp,
    FollowUpPriority,
    FollowUpReminderItem,
    FollowUpStatus,
    ReminderDeliveryStatus,
    StaffNotification,
    StaffNotificationType,
)

logger = logging.getLogger("apps.crm.scheduler")
User = get_user_model()


def _log_automation_audit(
    *,
    user: Any,
    action: str,
    resource_type: str,
    resource_id: Any,
    changes: Optional[Dict[str, Any]] = None,
    correlation_id: str = "",
) -> None:
    """Helper to record immutable audit trail entries for automation actions."""
    try:
        AuditLog.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            changes=changes or {},
            correlation_id=correlation_id,
        )
    except Exception as exc:
        logger.warning(f"Failed to record automation audit log: {exc}")


def _get_config_value(key: str, default: str) -> str:
    """Read a CRMConfiguration key safely with fallback."""
    try:
        conf = CRMConfiguration.objects.filter(key=key).first()
        if conf and conf.value:
            return conf.value
    except Exception:
        pass
    return default


def _resolve_escalation_target_officer(fallback_user: Optional[Any] = None) -> Optional[Any]:
    """Resolve supervisory officer (Placement Head or Administrator) for case escalations."""
    # 1. Check if configured target role exists
    target_role_code = _get_config_value("ESCALATION_TARGET_ROLE", RoleCatalog.PLACEMENT_HEAD)

    officer = (
        User.objects.filter(
            is_active=True,
            role_assignments__role__code=target_role_code,
            role_assignments__is_active=True,
        )
        .order_by("created_at")
        .first()
    )
    if officer:
        return officer

    # 2. Fallback to any active Administrator
    admin_user = (
        User.objects.filter(
            is_active=True,
            role_assignments__role__code=RoleCatalog.ADMIN,
            role_assignments__is_active=True,
        )
        .order_by("created_at")
        .first()
    )
    if admin_user:
        return admin_user

    # 3. Superuser or fallback
    superuser = User.objects.filter(is_active=True, is_superuser=True).first()
    if superuser:
        return superuser

    return fallback_user


# ==============================================================================
# Capability B & C: Process Due Reminder Items (Emails & WhatsApp)
# ==============================================================================

def recover_stale_processing_reminders(
    reference_time: Optional[datetime] = None,
    stale_threshold_minutes: int = 10,
    correlation_id: str = "",
    batch_size: int = 100,
) -> int:
    """Recover reminder items trapped in PROCESSING state after worker interruptions.

    If an item has been in PROCESSING for longer than stale_threshold_minutes:
    - If attempt_count < max_attempts, return it to RETRY_SCHEDULED so a worker can pick it up.
    - If attempt_count >= max_attempts, mark it as FAILED and record an audit log.

    Bounded recovery batches:
    - Bounded to at most `batch_size` items ordered deterministically by updated_at ascending.
    """
    if batch_size <= 0:
        raise ValueError("batch_size must be a positive integer greater than zero.")

    now = reference_time or timezone.now()
    stale_cutoff = now - timedelta(minutes=stale_threshold_minutes)
    is_postgres = connection.vendor == "postgresql"

    with transaction.atomic():
        stale_items = (
            FollowUpReminderItem.objects.filter(
                status=ReminderDeliveryStatus.PROCESSING,
                updated_at__lte=stale_cutoff,
            )
            .select_related("follow_up")
            .order_by("updated_at")
        )
        if is_postgres:
            try:
                stale_items = stale_items.select_for_update(skip_locked=True)
            except Exception:
                stale_items = stale_items.select_for_update()

        items_list = list(stale_items[:batch_size])
        recovered_count = 0
        for item in items_list:
            recovered_count += 1
            if item.attempt_count < item.max_attempts:
                item.status = ReminderDeliveryStatus.RETRY_SCHEDULED
                item.backoff_until = now
                item.error_message = (
                    f"Recovered from stalled PROCESSING state (exceeded {stale_threshold_minutes}m timeout)."
                )
                item.save(update_fields=["status", "backoff_until", "error_message", "updated_at"])
                _log_automation_audit(
                    user=None,
                    action="FOLLOW_UP_REMINDER_RECOVERED",
                    resource_type="FollowUpReminderItem",
                    resource_id=item.id,
                    changes={
                        "previous_status": "PROCESSING",
                        "new_status": "RETRY_SCHEDULED",
                        "reason": "stale_timeout",
                    },
                    correlation_id=correlation_id,
                )
            else:
                item.status = ReminderDeliveryStatus.FAILED
                item.error_message = (
                    f"Permanent failure: trapped in PROCESSING after {item.attempt_count} attempts."
                )
                item.save(update_fields=["status", "error_message", "updated_at"])
                _log_automation_audit(
                    user=None,
                    action="FOLLOW_UP_REMINDER_STALE_FAILED",
                    resource_type="FollowUpReminderItem",
                    resource_id=item.id,
                    changes={
                        "previous_status": "PROCESSING",
                        "new_status": "FAILED",
                        "reason": "max_attempts_exceeded",
                    },
                    correlation_id=correlation_id,
                )
        return recovered_count


def process_due_reminder_items(
    reference_time: Optional[datetime] = None,
    limit: int = 50,
    correlation_id: str = "",
    batch_size: Optional[int] = None,
) -> int:
    """Idempotently process and dispatch due automated reminder items with bounded retry.

    Uses atomic database locking to prevent duplicate concurrent worker dispatches.
    """
    limit = batch_size if batch_size is not None else limit
    now = reference_time or timezone.now()
    is_postgres = connection.vendor == "postgresql"

    # Recover any orphaned items stuck in PROCESSING due to earlier worker crash (bounded batch)
    recover_stale_processing_reminders(
        reference_time=now,
        correlation_id=correlation_id,
        batch_size=limit or 100,
    )

    from django.db.models import Q

    # Eligible items: PENDING or RETRY_SCHEDULED where scheduled_for <= now and backoff_until <= now
    with transaction.atomic():
        eligible_items = (
            FollowUpReminderItem.objects.filter(
                status__in=[
                    ReminderDeliveryStatus.PENDING,
                    ReminderDeliveryStatus.RETRY_SCHEDULED,
                ],
                scheduled_for__lte=now,
            )
            .filter(Q(backoff_until__isnull=True) | Q(backoff_until__lte=now))
            .select_related(
                "follow_up",
                "follow_up__company",
                "follow_up__hr_contact",
                "follow_up__assigned_to",
            )
            .order_by("scheduled_for")
        )

        if is_postgres:
            try:
                eligible_items = eligible_items.select_for_update(skip_locked=True)
            except Exception:
                eligible_items = eligible_items.select_for_update()

        items_to_process = list(eligible_items[:limit])

        # Atomically mark as PROCESSING
        for item in items_to_process:
            item.status = ReminderDeliveryStatus.PROCESSING
            item.save(update_fields=["status", "updated_at"])

    processed_count = 0
    email_adapter = get_email_adapter()
    whatsapp_adapter = get_whatsapp_adapter()

    for item in items_to_process:
        follow_up = item.follow_up
        # If the parent follow-up has been completed or cancelled, cancel the reminder item
        if follow_up.status in [FollowUpStatus.COMPLETED, FollowUpStatus.CANCELLED]:
            item.status = ReminderDeliveryStatus.CANCELLED
            item.error_message = f"Cancelled because follow-up status is {follow_up.status}."
            item.save(update_fields=["status", "error_message", "updated_at"])
            continue

        item.attempt_count += 1
        item_correlation = correlation_id or f"REM-{item.id.hex[:8]}"

        try:
            if item.channel == "EMAIL":
                subject = (
                    f"Reminder: Follow-up for {follow_up.company.name} "
                    f"due {follow_up.due_date.strftime('%Y-%m-%d %H:%M')}"
                )
                body_text = (
                    f"Dear {item.recipient_name or 'Partner'},\n\n"
                    f"This is an automated follow-up reminder regarding {follow_up.company.name}.\n"
                    f"Purpose: {follow_up.purpose}\n"
                    f"Due Date: {follow_up.due_date.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"Best regards,\nGQT HR & Placement Team"
                )
                result = email_adapter.send_email(
                    recipient=item.recipient,
                    subject=subject,
                    body_text=body_text,
                    correlation_id=item_correlation,
                )
            elif item.channel == "WHATSAPP":
                template_name = item.template_name or "followup_reminder_notice"
                context = {
                    "company_name": follow_up.company.name,
                    "due_date": follow_up.due_date.strftime("%Y-%m-%d %H:%M"),
                    "purpose": follow_up.purpose,
                    **(item.template_context or {}),
                }
                result = whatsapp_adapter.send_message(
                    phone_number=item.recipient,
                    template_name=template_name,
                    template_context=context,
                    correlation_id=item_correlation,
                )
            else:
                result = None

            if result and result.success:
                item.status = ReminderDeliveryStatus.SENT
                item.sent_at = timezone.now()
                item.provider_message_id = result.provider_message_id
                item.is_simulated = result.is_simulated
                item.error_message = ""
                item.save(
                    update_fields=[
                        "status",
                        "sent_at",
                        "provider_message_id",
                        "is_simulated",
                        "error_message",
                        "attempt_count",
                        "updated_at",
                    ]
                )
                processed_count += 1

                _log_automation_audit(
                    user=None,
                    action="FOLLOW_UP_REMINDER_SENT",
                    resource_type="FollowUpReminderItem",
                    resource_id=item.id,
                    changes={
                        "channel": item.channel,
                        "recipient": item.recipient,
                        "provider_message_id": result.provider_message_id,
                        "is_simulated": result.is_simulated,
                    },
                    correlation_id=item_correlation,
                )
            else:
                # Failure path
                err_msg = result.error_message if result else "Unsupported channel"
                item.error_message = err_msg

                if item.attempt_count < item.max_attempts:
                    item.status = ReminderDeliveryStatus.RETRY_SCHEDULED
                    # Bounded exponential backoff: 5m, 15m, 45m
                    backoff_delay_minutes = min(5 * (3 ** (item.attempt_count - 1)), 120)
                    item.backoff_until = now + timedelta(minutes=backoff_delay_minutes)
                    item.save(
                        update_fields=[
                            "status",
                            "error_message",
                            "attempt_count",
                            "backoff_until",
                            "updated_at",
                        ]
                    )
                else:
                    item.status = ReminderDeliveryStatus.FAILED
                    item.save(
                        update_fields=[
                            "status",
                            "error_message",
                            "attempt_count",
                            "updated_at",
                        ]
                    )
                    # Notify responsible officer of communication failure
                    _create_communication_failure_notification(item)

                _log_automation_audit(
                    user=None,
                    action="FOLLOW_UP_REMINDER_FAILED",
                    resource_type="FollowUpReminderItem",
                    resource_id=item.id,
                    changes={
                        "channel": item.channel,
                        "attempt_count": item.attempt_count,
                        "error": err_msg,
                        "status": item.status,
                    },
                    correlation_id=item_correlation,
                )

        except Exception as exc:
            logger.error(f"Unexpected error processing reminder item {item.id}: {exc}")
            item.status = (
                ReminderDeliveryStatus.RETRY_SCHEDULED
                if item.attempt_count < item.max_attempts
                else ReminderDeliveryStatus.FAILED
            )
            item.error_message = f"Worker runtime exception: {exc}"
            item.save(update_fields=["status", "error_message", "attempt_count", "updated_at"])

    return processed_count


def _create_communication_failure_notification(reminder_item: FollowUpReminderItem) -> None:
    """Generate in-app alert for responsible officer when communication exhausts retries."""
    follow_up = reminder_item.follow_up
    recipient = follow_up.assigned_to
    idempotency_key = f"NOTIF-FAIL-{reminder_item.id}-{reminder_item.attempt_count}"

    if StaffNotification.objects.filter(idempotency_key=idempotency_key).exists():
        return

    StaffNotification.objects.create(
        recipient=recipient,
        notification_type=StaffNotificationType.COMMUNICATION_FAILED,
        title=f"Delivery Failed: {reminder_item.channel} to {reminder_item.recipient}",
        message=(
            f"Automated reminder via {reminder_item.channel} for {follow_up.company.name} "
            f"failed after {reminder_item.attempt_count} attempts. Reason: {reminder_item.error_message}"
        ),
        link=f"/crm/follow-ups?tab=overdue",
        follow_up=follow_up,
        idempotency_key=idempotency_key,
    )


# ==============================================================================
# Capability D: Placement Officer Notifications
# ==============================================================================

def generate_due_followup_officer_notifications(
    reference_time: Optional[datetime] = None,
    window_hours: int = 24,
) -> int:
    """Detect follow-ups becoming due within configured window and notify responsible officer.

    Deduplicated using deterministic idempotency keys per follow-up due event.
    """
    now = reference_time or timezone.now()
    window_end = now + timedelta(hours=window_hours)

    due_follow_ups = (
        FollowUp.objects.filter(
            status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS],
            due_date__gte=now,
            due_date__lte=window_end,
        )
        .select_related("company", "assigned_to")
        .order_by("due_date")
    )

    created_count = 0
    for follow_up in due_follow_ups:
        # Deterministic key for this due date window
        key = f"NOTIF-DUE-{follow_up.id}-{follow_up.due_date.strftime('%Y%m%d%H')}"
        if StaffNotification.objects.filter(idempotency_key=key).exists():
            continue

        hours_left = max(int((follow_up.due_date - now).total_seconds() / 3600), 0)
        StaffNotification.objects.create(
            recipient=follow_up.assigned_to,
            notification_type=StaffNotificationType.FOLLOW_UP_DUE,
            title=f"Upcoming Follow-Up: {follow_up.company.name}",
            message=(
                f"Follow-up for {follow_up.company.name} is due in ~{hours_left} hour(s) "
                f"({follow_up.due_date.strftime('%Y-%m-%d %H:%M')}). Purpose: {follow_up.purpose}"
            ),
            link="/crm/follow-ups?tab=today",
            follow_up=follow_up,
            idempotency_key=key,
        )
        created_count += 1

    return created_count


# ==============================================================================
# Capability E: Escalation for Pending / Overdue Cases
# ==============================================================================

def generate_overdue_followup_escalations(
    reference_time: Optional[datetime] = None,
    overdue_days: Optional[int] = None,
) -> int:
    """Detect follow-ups breaching overdue threshold and trigger auditable supervisory escalations.

    Respects configurable thresholds from CRMConfiguration.
    Deduplicates escalations to prevent repetitive re-escalation of unchanged cases.
    """
    now = reference_time or timezone.now()

    if overdue_days is None:
        raw_days = _get_config_value("FOLLOW_UP_ESCALATION_OVERDUE_DAYS", "3")
        try:
            overdue_days = max(int(raw_days), 1)
        except ValueError:
            overdue_days = 3

    cutoff = now - timedelta(days=overdue_days)

    breached_follow_ups = (
        FollowUp.objects.filter(
            status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS],
            due_date__lte=cutoff,
        )
        .select_related("company", "assigned_to")
        .order_by("due_date")
    )

    escalations_created = 0

    for follow_up in breached_follow_ups:
        # Prevent duplicate escalations for the same follow-up while an escalation is active
        existing_active = CaseEscalation.objects.filter(
            follow_up=follow_up,
            status__in=[CaseEscalationStatus.PENDING, CaseEscalationStatus.ACKNOWLEDGED],
        ).exists()
        if existing_active:
            continue

        # Deterministic key: unique per follow-up due date cycle
        idempotency_key = f"ESC-OVERDUE-{follow_up.id}-{follow_up.due_date.strftime('%Y%m%d')}"
        if CaseEscalation.objects.filter(idempotency_key=idempotency_key).exists():
            continue

        supervisor = _resolve_escalation_target_officer(fallback_user=follow_up.assigned_to)
        if not supervisor:
            logger.warning(f"No supervisory officer found to receive escalation for follow-up {follow_up.id}")
            continue

        days_overdue = max(int((now - follow_up.due_date).total_seconds() / 86400), overdue_days)
        reason = (
            f"Follow-up for company '{follow_up.company.name}' has been overdue for {days_overdue} day(s) "
            f"(scheduled due date was {follow_up.due_date.strftime('%Y-%m-%d')}). "
            f"Assigned officer: {follow_up.assigned_to.full_name} ({follow_up.assigned_to.email})."
        )

        escalation = CaseEscalation.objects.create(
            case_type=CaseEscalationType.OVERDUE_FOLLOW_UP,
            follow_up=follow_up,
            escalated_to=supervisor,
            escalated_by=None,  # Automated background engine
            previous_assigned_to=follow_up.assigned_to,
            reason=reason,
            escalation_level=CaseEscalationLevel.LEVEL_1,
            status=CaseEscalationStatus.PENDING,
            idempotency_key=idempotency_key,
        )
        escalations_created += 1

        # In-app alert for the supervisor
        StaffNotification.objects.create(
            recipient=supervisor,
            notification_type=StaffNotificationType.CASE_ESCALATED,
            title=f"Case Escalated: Overdue Follow-Up for {follow_up.company.name}",
            message=reason,
            link=f"/crm/follow-ups?tab=escalations",
            follow_up=follow_up,
            idempotency_key=f"NOTIF-ESC-{escalation.id}",
        )

        _log_automation_audit(
            user=None,
            action="CASE_ESCALATED",
            resource_type="CaseEscalation",
            resource_id=escalation.id,
            changes={
                "follow_up_id": str(follow_up.id),
                "company": follow_up.company.name,
                "escalated_to": supervisor.email,
                "previous_assigned_to": follow_up.assigned_to.email,
                "days_overdue": days_overdue,
            },
        )

    return escalations_created


# ==============================================================================
# Master Automation Orchestration Cycle
# ==============================================================================

def run_automated_followup_cycle(
    reference_time: Optional[datetime] = None,
    dry_run: bool = False,
    triggered_by: Optional[Any] = None,
    correlation_id: str = "",
) -> Dict[str, Any]:
    """Execute complete automated follow-up operational cycle across all Phase 12 capabilities.

    Safe, transactional, and idempotent. Supports dry-run inspection.
    """
    now = reference_time or timezone.now()
    corr_id = correlation_id or f"AUTO-{uuid.uuid4().hex[:8].upper()}"

    logger.info(
        f"[AUTOMATION_CYCLE_START] [req:{corr_id}] dry_run={dry_run} "
        f"triggered_by={getattr(triggered_by, 'email', 'System')}"
    )

    if dry_run:
        # Read-only counts
        from django.db.models import Q
        pending_reminders = FollowUpReminderItem.objects.filter(
            status__in=[
                ReminderDeliveryStatus.PENDING,
                ReminderDeliveryStatus.RETRY_SCHEDULED,
            ],
            scheduled_for__lte=now,
        ).filter(Q(backoff_until__isnull=True) | Q(backoff_until__lte=now)).count()

        window_end = now + timedelta(hours=24)
        due_follow_ups = FollowUp.objects.filter(
            status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS],
            due_date__gte=now,
            due_date__lte=window_end,
        ).count()

        overdue_days = 3
        cutoff = now - timedelta(days=overdue_days)
        overdue_follow_ups = FollowUp.objects.filter(
            status__in=[FollowUpStatus.OPEN, FollowUpStatus.IN_PROGRESS],
            due_date__lte=cutoff,
        ).count()

        return {
            "success": True,
            "dry_run": True,
            "correlation_id": corr_id,
            "executed_at": now.isoformat(),
            "reminders_eligible": pending_reminders,
            "due_notifications_eligible": due_follow_ups,
            "overdue_escalations_eligible": overdue_follow_ups,
        }

    # 1. Process due reminders
    reminders_count = process_due_reminder_items(reference_time=now, correlation_id=corr_id)

    # 2. Generate placement officer upcoming due notifications
    notifications_count = generate_due_followup_officer_notifications(reference_time=now)

    # 3. Generate overdue escalations
    escalations_count = generate_overdue_followup_escalations(reference_time=now)

    summary = {
        "success": True,
        "dry_run": False,
        "correlation_id": corr_id,
        "executed_at": now.isoformat(),
        "reminders_processed": reminders_count,
        "notifications_created": notifications_count,
        "escalations_created": escalations_count,
    }

    _log_automation_audit(
        user=triggered_by,
        action="AUTOMATION_CYCLE_COMPLETED",
        resource_type="CRMAutomation",
        resource_id=corr_id,
        changes=summary,
        correlation_id=corr_id,
    )

    logger.info(f"[AUTOMATION_CYCLE_COMPLETE] [req:{corr_id}] {summary}")
    return summary
