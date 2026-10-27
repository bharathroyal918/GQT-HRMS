# GQT HRMS — Phase 12: Automated Follow-Up Specification & Implementation Manual

**Document Version:** 1.0.0  
**Status:** Approved & Verified (Step Zero Audit to Final Quality Gates)  
**Milestone:** Phase 12 — Automated Follow-Up  
**Baseline Reference:** Phase 11 (`8f91e28`)  
**Target Environment:** Django 5.1.15 + React 19 + TypeScript Strict + PostgreSQL 16 (Hosted on Supabase)

---

## 1. Executive Summary

Phase 12 implements the production-grade **Automated Follow-Up** system for the GQT HRMS & Recruitment CRM Platform. Built directly upon the authoritative workflow defined in `HRMS Work-Flow.pdf` (Workflow Step 4 and Stage 5 Corporate Retention), this system automates multi-channel notifications and corporate relationship nurturing through five core capabilities:

1. **Schedule Follow-ups:** Enriched corporate and candidate follow-up entity supporting categories (`HR_OUTREACH`, `STUDENT_RECONNECT`, `INTERVIEW_CONFIRMATION`, `OFFER_ACCEPTANCE`, `JOINING_CHECK`, `GENERAL_RECONNECT`), multi-channel reminder preferences (`EMAIL`, `WHATSAPP`, `BOTH`, `NONE`), target `remind_at` triggers, and notes.
2. **Automated Reminder Emails:** Transactional outbox queuing with template rendering, bounded backoff retry, idempotent dispatch, and provider abstraction.
3. **WhatsApp Messages:** Vendor-neutral adapter abstraction supporting phone number normalization (Indian E.164 standard), template context preparation, simulated local execution, and Meta WhatsApp Cloud API webhooks with HMAC-SHA256 signature verification.
4. **Placement Officer Notifications:** Authoritative in-app alerts for assigned officers when corporate follow-ups are due today or become overdue, with deduplicated generation and unread tracking.
5. **Escalation for Pending Cases:** Configurable SLA detection escalating unresolved corporate commitments (default: 3 days overdue) to Placement Heads/Directors, with full audit trail, acknowledgment, and mandatory resolution outcomes.

---

## 2. Architecture & Design Decisions

### 2.1 The 5-Layer Pattern
Adhering to the project's strict architecture:
`Models` → `Selectors` → `Services` → `Serializers` → `Views`

- **Business Logic Boundary:** Views contain zero scheduling or workflow logic. All mutations flow through `apps.crm.services` (`schedule_follow_up`, `reschedule_follow_up`, `complete_follow_up`, `cancel_follow_up`, `acknowledge_case_escalation`, `resolve_case_escalation`).
- **Data Access:** All filtering and aggregations live in `apps.crm.selectors` (`get_follow_up_reminders_queryset`, `get_staff_notifications_queryset`, `get_case_escalations_queryset`).

### 2.2 Transactional Outbox Pattern
To prevent distributed transaction failures and avoid blocking web requests during slow external network calls (SMTP or Meta WhatsApp API):
- When a user schedules or reschedules a follow-up, `FollowUpReminderItem` records are committed transactionally to the database in `PENDING` status.
- Background execution claims pending items using database row locking (`select_for_update(skip_locked=True)` on PostgreSQL) and atomic state transitions to `PROCESSING` before invoking provider adapters.
- Outbox processing happens completely out-of-process.

### 2.3 Provider Abstraction & Truthful Reporting
- External communications are isolated behind `BaseEmailAdapter` and `BaseWhatsAppAdapter`.
- **Truthful Status:** In development and test environments where live credentials are not provisioned, `SimulatedEmailAdapter` and `SimulatedWhatsAppAdapter` record `is_simulated = True` and status `SIMULATED` or `DELIVERED`. Local mock execution is **never reported as real external delivery**.
- **HMAC Signature Verification:** Meta WhatsApp callbacks verify `X-Hub-Signature-256` HMAC-SHA256 signatures before parsing status payloads.

---

## 3. Database Schema & Migration

### 3.1 Migration Record
- **Migration File:** `backend/apps/crm/migrations/0003_caseescalation_followupreminderitem_and_more.py`
- **Drift Detection:** Verified clean (`manage.py makemigrations --check --dry-run` reports 0 pending changes).

### 3.2 Extended & New Models

#### `apps.crm.FollowUp` (Extended)
- `category`: `VARCHAR(32)` (`HR_OUTREACH`, `STUDENT_RECONNECT`, `INTERVIEW_CONFIRMATION`, `OFFER_ACCEPTANCE`, `JOINING_CHECK`, `GENERAL_RECONNECT`).
- `student`: Foreign key to `StudentProfile` (optional, for candidate-specific follow-ups).
- `job_requirement`: Foreign key to `JobRequirement` (optional, for drive-specific follow-ups).
- `interview_schedule`: Foreign key to `InterviewSchedule` (optional, for interview attendance follow-ups).
- `placement_status`: Foreign key to `CandidatePlacementStatus` (optional, for offer follow-ups).
- `remind_at`: `TIMESTAMPTZ` (the exact trigger timestamp; defaults to `due_date` if omitted).
- `reminder_channel`: `VARCHAR(16)` (`NONE`, `EMAIL`, `WHATSAPP`, `BOTH`).
- `notes`: `TEXT` (instructional notes and talking points).
- **Indexes:** `['due_date', 'status']`, `['assigned_to', 'status']`, `['remind_at', 'status']`, `['category', 'status']`.

#### `apps.crm.FollowUpReminderItem` (New Transactional Outbox)
- `id`: `UUID` (Primary Key).
- `follow_up`: Foreign key to `FollowUp` (cascade delete).
- `channel`: `VARCHAR(16)` (`EMAIL`, `WHATSAPP`).
- `recipient`: `VARCHAR(254)` (email address or normalized E.164 phone number).
- `recipient_name`: `VARCHAR(255)`.
- `scheduled_for`: `TIMESTAMPTZ`.
- `status`: `VARCHAR(20)` (`PENDING`, `PROCESSING`, `SENT`, `DELIVERED`, `FAILED`, `RETRY_SCHEDULED`, `CANCELLED`).
- `attempt_count`: `INTEGER` (bounded retry counter).
- `max_attempts`: `INTEGER` (default: 3).
- `backoff_until`: `TIMESTAMPTZ` (exponential backoff window: 5m, 15m, 45m).
- `sent_at`: `TIMESTAMPTZ`.
- `delivered_at`: `TIMESTAMPTZ`.
- `provider_message_id`: `VARCHAR(255)` (SMTP message ID or Meta WhatsApp `wamid`).
- `error_message`: `TEXT`.
- `is_simulated`: `BOOLEAN` (flags local simulated delivery).
- **Constraint:** Unique index on `['follow_up', 'channel', 'scheduled_for']` prevents duplicate outbox items.

#### `apps.crm.StaffNotification` (New Placement Officer In-App Alerts)
- `id`: `UUID` (Primary Key).
- `recipient`: Foreign key to `User` (assigned officer).
- `notification_type`: `VARCHAR(32)` (`FOLLOW_UP_DUE`, `FOLLOW_UP_OVERDUE`, `COMMUNICATION_FAILED`, `CASE_ESCALATED`, `SYSTEM_ALERT`).
- `title`: `VARCHAR(255)`.
- `message`: `TEXT`.
- `link`: `VARCHAR(500)` (action URL within HRMS).
- `follow_up`: Foreign key to `FollowUp` (optional).
- `is_read`: `BOOLEAN` (default: `False`).
- `read_at`: `TIMESTAMPTZ`.
- **Constraint:** Unique index on `['recipient', 'follow_up', 'notification_type', 'is_read']` prevents duplicate alert spam for the same event.

#### `apps.crm.CaseEscalation` (New SLA Escalations)
- `id`: `UUID` (Primary Key).
- `case_type`: `VARCHAR(32)` (`OVERDUE_FOLLOW_UP`, `UNRESOLVED_COMMUNICATION_FAILURE`).
- `follow_up`: Foreign key to `FollowUp`.
- `escalated_to`: Foreign key to `User` (Supervisor / Placement Head).
- `escalated_by`: Foreign key to `User` (system or user).
- `previous_assigned_to`: Foreign key to `User` (officer who owned the task).
- `reason`: `TEXT`.
- `escalation_level`: `VARCHAR(16)` (`LEVEL_1`, `LEVEL_2`).
- `status`: `VARCHAR(20)` (`PENDING`, `ACKNOWLEDGED`, `RESOLVED`, `DISMISSED`).
- `acknowledged_at`: `TIMESTAMPTZ`.
- `acknowledged_by`: Foreign key to `User`.
- `resolved_at`: `TIMESTAMPTZ`.
- `resolved_by`: Foreign key to `User`.
- `resolution_notes`: `TEXT` (mandatory for resolution).
- **Constraint:** Unique index on `['follow_up', 'case_type', 'status']` prevents duplicate active escalations for the same underlying follow-up.

---

## 4. Background Execution & Reliability

### 4.1 Windows-Compatible Background Worker
Because Celery/Redis are not installed on this local Windows development machine, background processing is provided via:
1. **Django Management Command:**
   ```powershell
   # Run once and exit
   python manage.py process_follow_ups --once

   # Dry-run inspection without mutations
   python manage.py process_follow_ups --dry-run --once

   # Continuous local background worker loop (e.g. interval 60s)
   python manage.py process_follow_ups --interval 60 --limit 100
   ```
2. **Automated Scheduled Tasks:**
   - In production on Windows Server: Schedule via Windows Task Scheduler every 5 minutes.
   - In production on Linux/container: Add a cron job or Kubernetes CronJob calling `python manage.py process_follow_ups --once`.

### 4.2 Idempotency & Concurrency Protections
- **Atomic Claims:** Outbox items are fetched inside `transaction.atomic()` using `select_for_update(skip_locked=True)` on PostgreSQL.
- **Double-Send Prevention:** State transitions from `PENDING` to `PROCESSING` happen before provider adapters are called.
- **Bounded Exponential Backoff:**
  - Attempt 1 failure: `backoff_until = now + 5 minutes`.
  - Attempt 2 failure: `backoff_until = now + 15 minutes`.
  - Attempt 3 failure: `status = FAILED`, marked permanently for manual staff intervention or retry via UI.

---

## 5. Security & Role-Based Access Control (RBAC)

All endpoints strictly enforce server-side authorization:

| Endpoint | Permitted Roles | Description |
|---|---|---|
| `GET /api/v1/crm/follow-ups/` | Staff, Directors, Officers, Coordinators, Auditors (read-only) | List filterable follow-ups |
| `POST /api/v1/crm/follow-ups/` | Admin, Placement Director, Placement Officer | Schedule new follow-up |
| `POST /api/v1/crm/follow-ups/{id}/reschedule/` | Admin, Placement Director, Placement Officer | Reschedule follow-up |
| `POST /api/v1/crm/follow-ups/{id}/complete/` | Admin, Placement Director, Placement Officer | Complete follow-up |
| `GET /api/v1/crm/follow-ups/{id}/reminders/` | Staff, Admin, Placement Officers | View outbox items for task |
| `POST /api/v1/crm/follow-ups/{id}/reminders/{rem_id}/retry/` | Admin, Placement Director, Placement Officer | Reschedule retry for failed reminder |
| `GET /api/v1/crm/escalations/` | Admin, Placement Director, Placement Officer | View SLA case escalations |
| `POST /api/v1/crm/escalations/{id}/acknowledge/` | Admin, Placement Director, Placement Officer | Acknowledge pending escalation |
| `POST /api/v1/crm/escalations/{id}/resolve/` | Admin, Placement Director, Placement Officer | Resolve escalation with notes |
| `GET /api/v1/crm/notifications/` | Authenticated Officer / Staff | View own activity alerts |
| `POST /api/v1/crm/notifications/{id}/read/` | Recipient Officer | Mark alert as read |
| `POST /api/v1/crm/automation/run/` | Admin, Placement Director, Placement Officer | Trigger automation cycle |
| `GET /api/v1/crm/webhooks/whatsapp/` | External Webhook (Public with verify token) | Meta Webhook Challenge verification |
| `POST /api/v1/crm/webhooks/whatsapp/` | External Webhook (HMAC-SHA256 signature verified) | Meta Webhook Status callbacks |

*Note: Students and external HR contacts are strictly denied access (`403 Forbidden`) to all CRM, follow-up, reminder, and escalation endpoints.*

---

## 6. Environment Configuration

The following environment variables configure Phase 12 providers and policies:

```ini
# ==============================================================================
# Phase 12: Automated Follow-Up & Provider Configuration
# ==============================================================================

# Email Provider Settings
EMAIL_PROVIDER_BACKEND=simulated          # Options: simulated, smtp
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=apikey
EMAIL_HOST_PASSWORD=your-smtp-secret-key
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=placements@gqt.local

# WhatsApp Provider Settings
WHATSAPP_PROVIDER_BACKEND=simulated       # Options: simulated, meta
WHATSAPP_PHONE_NUMBER_ID=109876543210987
WHATSAPP_ACCESS_TOKEN=your-meta-access-token
WHATSAPP_API_SECRET=your-meta-app-secret
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-custom-webhook-verify-token

# SLA & Escalation Policies (Also configurable via CRMConfiguration model)
CRM_FOLLOW_UP_ESCALATION_OVERDUE_DAYS=3   # Default: 3 business days overdue
CRM_ESCALATION_TARGET_ROLE=PLACEMENT_HEAD # Default: PLACEMENT_HEAD
```

---

## 7. Quality Gates Verification Results

Executed via `powershell -ExecutionPolicy Bypass -File scripts/verify_dev.ps1` on 2026-10-27:

```
==========================================================
 GQT HRMS — Master Foundation Verification Suite (Windows)
==========================================================

[Check 1/6] Running Django System Checks...
System check identified no issues (0 silenced).
PASS: Django system checks clean.

[Check 2/6] Verifying Migration Consistency...
No changes detected
PASS: Zero migration drift detected.

[Check 3/6] Running Backend Pytest Suite...
================= 288 passed, 4 warnings in 76.43s (0:01:16) ==================
PASS: All backend automated tests passed.

[Check 4/6] Running Frontend TypeScript Type Check...
PASS: Frontend TypeScript compilation clean.

[Check 5/6] Running Frontend Vitest Component Tests...
Test Files  16 passed (16)
Tests       90 passed (90)
PASS: All frontend Vitest tests passed.

[Check 6/6] Verifying Frontend Production Build...
✓ built in 20.57s
PASS: Frontend production build generated successfully in dist/.

==========================================================
 ALL CHECKS PASSED: GQT HRMS Phase 12 (Automated Follow-up) Verified!
==========================================================
```

### Metrics Summary
- **Backend Tests:** 288 passed (272 baseline + 16 new Phase 12 tests).
- **Frontend Tests:** 90 passed (86 baseline + 4 new Phase 12 tests).
- **Migration Drift:** 0 drift detected.
- **TypeScript Errors:** 0 errors in strict mode.
- **Production Build:** Successfully generated clean chunk bundles in `dist/`.

---

## 8. Unresolved Business Decisions & Known Limitations

1. **Escalation Threshold & Hierarchy:** The official `HRMS Work-Flow.pdf` specifies that overdue/pending cases must be escalated to supervisors, but does not dictate a static day count or multi-tier managerial tree. We implemented the configurable parameter `FOLLOW_UP_ESCALATION_OVERDUE_DAYS` (defaulting to 3 days) and assigned escalations to `PLACEMENT_HEAD`. An enterprise organizational chart hierarchy can be plugged into `get_escalation_supervisor_for_user` once defined by university leadership.
2. **PostgreSQL / Supabase Status:** Local automated verification was executed against SQLite/in-memory SQLite. Production target PostgreSQL 16 on Supabase is fully configured in settings (`DATABASE_URL`), and row-level locks (`select_for_update(skip_locked=True)`) are dynamically enabled when running against PostgreSQL, but live Supabase connectivity has not been executed on this offline Windows development workstation.
3. **Live WhatsApp Meta Cloud API Account:** A Meta Business Manager account with approved template IDs (`followup_reminder_notice`) must be provisioned before switching `WHATSAPP_PROVIDER_BACKEND=meta`. The simulated adapter verified all template context formatting, phone normalization, and webhook HMAC signature processing.
