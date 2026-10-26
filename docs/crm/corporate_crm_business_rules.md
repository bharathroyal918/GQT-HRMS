# GQT HRMS — Corporate CRM Business Rules & Invariants

## 1. Company Duplicate Protection Workflow (Workflow Step 1)

### Principles
- **No Automatic Merging or Silent Deletion**: Similar corporate names do not guarantee identical legal entities. The platform never automatically overwrites or merges records.
- **Normalization Strategy**:
  - `name` is cleaned using `normalize_company_name()`: lowercased, special characters/punctuation stripped, whitespace collapsed to single spaces.
  - `website` is parsed using `extract_domain()`: scheme, port, `www.` prefix, and query paths are stripped to yield the canonical root domain.
- **Pre-Submission Warning**:
  - An interactive endpoint `GET /api/v1/crm/companies/check-duplicate/?name=...&website=...` returns candidate matches classified by:
    - `EXACT_NAME`: Existing active or archived entity has identical normalized name.
    - `DOMAIN_MATCH`: Existing entity shares canonical root domain.
  - Returns rationale explaining why the warning was raised.
  - Authorized users may review candidates and proceed if legitimate (e.g. distinct subsidiaries sharing a parent website).

---

## 2. HR Contact & Relationship Integrity (Workflow Steps 2 & 3)

### Company-to-Contact Invariants
- An HR contact must be bound to a valid, non-deleted `Company`.
- Multi-channel outreach activity (`OutreachLog`) and follow-ups (`FollowUp`) that specify both `company` and `hr_contact` must validate that:
  $$\text{hr\_contact.company\_id} == \text{company.id}$$
  If a mismatched contact is supplied, the service layer raises `ValidationError` and the API responds with HTTP 400 Bad Request.
- Company-level outreach is permitted when no individual HR recruiter has been assigned or identified yet (`hr_contact = None`).

---

## 3. Daily Outreach Benchmark (Workflow Step 2: 100+ Outreach/Day)

### Operational Target Rules
- The authoritative workflow defines an operational benchmark of **100 or more outreach touchpoints per day** for the corporate relationship team.
- **Configurability**: Target value is stored in `crm_configuration` under key `DAILY_OUTREACH_TARGET` (default: 100), avoiding hardcoded magic numbers.
- **Timezone Boundary Enforcement**:
  - Daily counts are computed relative to the operational timezone boundary (default: `Asia/Kolkata` / UTC+05:30).
  - Touchpoints occurring between 00:00:00 and 23:59:59 local time are aggregated.
  - Planned or cancelled tasks are **never** counted toward completed outreach.
- **Non-Punitive Rule**: Shortfalls against the daily target are displayed visually on the dashboard as operational progress indicators and do not automatically alter employee statuses or lock features.

---

## 4. Follow-up Lifecycle and Overdue Management (Workflow Step 4)

### State Transitions
- Lifecycle states: `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
- **Dynamic Overdue Evaluation**: Overdue is not a manually selected status; it is evaluated dynamically at query and serializer time:
  $$\text{is\_overdue} = \text{status} \in \{\text{OPEN}, \text{IN\_PROGRESS}\} \land \text{due\_date} < \text{now()}$$
- **Rescheduling**:
  - Can only be performed on `OPEN` or `IN_PROGRESS` tasks.
  - Automatically increments `rescheduled_count`.
  - Records previous due date, new due date, reason, and actor in `core_audit_log`.
- **Reopening**:
  - Completed or cancelled follow-ups cannot become active again through ordinary edit requests.
  - Reopening requires explicit POST to `/api/v1/crm/follow-ups/{id}/reopen/` with new due date and reason.

---

## 5. Role-Based Access Control (RBAC) Matrix

| Operation / Endpoint | ADMIN | PLACEMENT_HEAD | PLACEMENT_OFFICER | HR_RELATIONSHIP_MGR | AUDITOR | STUDENT / CREATIVE / EVALUATOR |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **List / Search Companies** | Read/Write | Read/Write | Read/Write | Read/Write | Read Only | 403 Forbidden |
| **Create / Update Company** | Read/Write | Read/Write | Read/Write | Read/Write | 403 Forbidden | 403 Forbidden |
| **Archive / Restore Company**| Read/Write | Read/Write | Read/Write | Read/Write | 403 Forbidden | 403 Forbidden |
| **List HR Contacts** | Read/Write | Read/Write | Read/Write | Read/Write | Read Only | 403 Forbidden |
| **Create / Update HR Contact** | Read/Write | Read/Write | Read/Write | Read/Write | 403 Forbidden | 403 Forbidden |
| **Log Outreach Touchpoint** | Read/Write | Read/Write | Read/Write | Read/Write | 403 Forbidden | 403 Forbidden |
| **Follow-Up Scheduling & Completion**| Read/Write | Read/Write | Read/Write | Read/Write | 403 Forbidden | 403 Forbidden |
| **CRM Dashboard Metrics** | Full Access | Full Access | Full Access | Full Access | Full Access | 403 Forbidden |
| **Update Target Configurations** | Full Access | Full Access | 403 Forbidden | 403 Forbidden | 403 Forbidden | 403 Forbidden |

---

## 6. Audit Trail Enforcement
All mutating corporate relationship events generate immutable records in `core_audit_log`:
- `COMPANY_CREATED`, `COMPANY_UPDATED`, `COMPANY_ARCHIVED`, `COMPANY_RESTORED`.
- `HR_CONTACT_CREATED`, `HR_CONTACT_UPDATED`, `HR_CONTACT_ARCHIVED`, `HR_CONTACT_RESTORED`.
- `OUTREACH_LOGGED`.
- `FOLLOW_UP_SCHEDULED`, `FOLLOW_UP_RESCHEDULED`, `FOLLOW_UP_COMPLETED`, `FOLLOW_UP_CANCELLED`, `FOLLOW_UP_REOPENED`.
