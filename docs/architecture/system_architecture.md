# GQT HRMS & Recruitment CRM — System Architecture Specification

## 1. Executive Architecture Summary
GQT HRMS is an enterprise single-organization SaaS platform automating institutional recruitment, student placement training, interview drives, and corporate relationship CRM.

---

## 2. 5-Layer Backend Architecture Pattern
Every business domain follows a strict 5-layer separation of concerns:

```
┌────────────────────────────────────────────────────────┐
│ 1. VIEWS & VIEWSETS                                    │
│    - HTTP parsing, status codes, standard envelopes    │
│    - Role & Object-level permission guards             │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. SERIALIZERS                                         │
│    - Input validation, sanitization, schema generation │
└──────────────────────────┬─────────────────────────────┘
                           │ Validated Data
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. SERVICES (Atomic Mutation Engine)                   │
│    - @transaction.atomic boundaries                    │
│    - Pessimistic row locking: select_for_update()      │
│    - File magic bytes validation & SHA-256 hashing     │
│    - Audit trail logging                               │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 4. SELECTORS (Query Engine)                            │
│    - Read queries, select_related, prefetch_related    │
│    - Aggregations, metrics, and funnel calculations    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 5. MODELS (Relational Entities)                        │
│    - UUIDv4 primary keys (non-enumerable)              │
│    - DecimalField for currency & CTC precision         │
│    - Protected deletion: on_delete=models.PROTECT      │
│    - Composite unique constraints                      │
└────────────────────────────────────────────────────────┘
```

---

## 3. Frontend Architecture
* **Framework:** React 19 + TypeScript (strict compiler options).
* **Styling:** Tailwind CSS with official Global Quest Technologies brand tokens:
  * Primary Deep Navy: `#001B4D`
  * Vivid Blue Accent: `#005BBB`
  * Charcoal Gray: `#1E293B`
  * Neutral Gray: `#64748B` / `#F1F5F9`
* **State & Server Cache:** TanStack Query v5 with normalized keys and optimistic mutations.
* **Form Validation:** React Hook Form with Zod runtime validation schemas.
* **API Client:** Axios with CSRF cookie auto-injection, Correlation ID propagation, and standard error extraction.
* **Bundle Optimization:** Route-level code splitting and manual vendor chunking (`vendor-react`, `vendor-query`, `vendor-forms`, `vendor-icons`).

---

## 4. Identity, Authentication & RBAC Domain (`apps.accounts`)
* **Custom User Model (`accounts_user`):**
  * `id`: UUIDv4 primary key.
  * `email`: Normalized, case-insensitive unique authentication identity (`Lower('email')`).
  * Account status flags: `is_active`, `is_staff`, `is_superuser`.
* **Role-Based Access Control (`accounts_role`, `accounts_user_role_assignment`):**
  * Normalized relational assignment model with active status flags and assignment audit references (`assigned_by`, `assigned_at`).
  * 9 operational roles: `ADMIN`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `HR_RELATIONSHIP_MGR`, `CREATIVE_DESIGNER`, `TRAINER`, `EVALUATOR`, `STUDENT`, `AUDITOR`.
* **Authentication Subsystem:**
  * Dual-transport JWT authentication via `HttpOnlyCookieJWTAuthentication` (SameSite cookies `gqt_access_token` and `gqt_refresh_token` for browser; Bearer header fallback for API consumers).
  * Refresh token rotation and replay prevention backed by `rest_framework_simplejwt.token_blacklist`.
  * Centralized `AuthContext` on frontend with `ProtectedRoute` guards and role-aware navigation. Zero credentials stored in web storage.

---

## 5. Corporate CRM & HR Directory Domain (`apps.crm`)
* **Company Model (`crm_company`):**
  * `id`: UUIDv4 primary key.
  * `name`, `normalized_name`: Indexed normalized corporate name for cautious duplicate identification.
  * `website`, `canonical_domain`: Extracted root domain (`google.com`, `infosys.com`) with validation.
  * `domain_category`: 9 industry classifications (`IT_SERVICES`, `PRODUCT_SAAS`, `CORE_ENGINEERING`, `BFSI`, `BPO_ITES`, `EDTECH`, `HEALTHCARE`, `CONSULTING`, `OTHER`).
  * `tier`: Tier 1 (Product/MNC/FAANG), Tier 2 (Mid-market/Service), Tier 3 (Startup/Boutique).
  * `relationship_status`: Discovered, Outreach in Progress, Connected, Interested, Active Hiring Partner, Not Interested, On Hold.
  * Relationship ownership, location, internal notes, archival flags, audit timestamps.
* **HR Contact Model (`crm_hr_contact`):**
  * `company_id`: Foreign key with `on_delete=models.PROTECT`.
  * `name`, `designation`, `department`, `email`, `phone`, `linkedin_url`, `preferred_channel`.
  * `status`: Active, Inactive, Left Company, Do Not Contact.
  * Last contacted and next follow-up dates (derived from real outreach & tasks).
* **Outreach Log Model (`crm_outreach_log`):**
  * Append-only activity touchpoint journal.
  * `company_id`, `hr_contact_id` (validated: contact must belong to company).
  * `channel`: Phone Call, Email, LinkedIn InMail, WhatsApp, Campus Visit, In-Person Meeting, Virtual Meeting, Other.
  * `direction`: Outbound vs. Inbound.
  * `outcome`: Connected - Positive, Connected - Neutral, Connected - Gatekeeper Block, No Answer, Left Voicemail, Email Replied, LinkedIn Accepted, Meeting Scheduled, Job Shared, Not Interested, Other.
  * Automatic status advancement: First outreach advances `DISCOVERED` company to `OUTREACH_IN_PROGRESS`.
* **Follow-Up Model (`crm_follow_up`):**
  * Priority follow-up task engine with explicit status lifecycle: `OPEN`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`.
  * Dynamic `is_overdue` state: `due_date < timezone.now()` while in `OPEN` or `IN_PROGRESS`.
  * Audited operations: scheduling, reassignment, completion, cancellation (reason required), and explicit reopening.
* **Duplicate Detection Engine:**
  * Exact and normalized name matching with case and special character stripping.
  * Canonical corporate domain matching.
  * HR contact duplicate detection within company by email and normalized phone number.
* **Daily Outreach Targets & Operational Metrics:**
  * System-wide configurable daily target (default: 100+ outreach/day) managed via `crm_configuration`.
  * Permission-aware metrics calculation aggregated across timezones for today's outreach, channel distributions, overdue follow-ups, and active partner counts.

---

## 6. Job Intake & Verification Domain (`apps.jobs`)
* **Job Requirement Model (`jobs_job_requirement`):**
  * `id`: UUIDv4 primary key.
  * Relational integrity: Foreign key to `crm.Company` with `on_delete=models.PROTECT`; optional foreign key to `crm.HRContact` with `on_delete=models.SET_NULL`. Service layer validates that contact belongs to the associated company.
  * 10 structured Step 5 fields: `title`, `description`, `skills_required`, `min_salary`/`max_salary`/`salary_negotiable`, `location`, `bond_details`, `eligibility_criteria`, `hiring_process_rounds`, `interview_date`, `registration_deadline`.
  * Explicit 7-stage lifecycle status: `DRAFT`, `PENDING_VERIFICATION`, `UNDER_REVIEW`, `CHANGES_REQUESTED`, `VERIFIED`, `APPROVED`, `REJECTED`.
  * Locking mechanism: `is_locked` / `is_editable` properties; approved JDs cannot be mutated without Placement Head reopening.
* **Checklist Entity Model (`jobs_checklist_item`):**
  * Relational normalization: Foreign key to `JobRequirement` with `on_delete=models.CASCADE`.
  * 5 workflow-derived verification points:
    1. `ELIGIBILITY`: Academic eligibility, backlogs, percentage/CGPA criteria.
    2. `SALARY_AUTHENTICITY`: CTC authenticity, stipends, deductions, bonds.
    3. `COMPANY_AUTHENTICITY`: Corporate credibility, registration, blacklist status.
    4. `INTERVIEW_PROCESS`: Rounds, mode, venue, assessment platforms.
    5. `REGISTRATION_DEADLINE`: Valid date before drive day allowing student prep.
  * Verification metadata: `status` (`PENDING`, `VERIFIED`, `REJECTED`, `NOT_APPLICABLE`), `verified_by`, `verified_at`, `remarks`.
  * Composite uniqueness: `UniqueConstraint(fields=['job_requirement', 'item_code'])`.
* **Decision Audit Log (`jobs_approval_decision`):**
  * Append-only decision record: `job_requirement_id`, `actor_id`, `decision` (`SUBMITTED`, `CHANGES_REQUESTED`, `APPROVED`, `REJECTED`, `REOPENED`), `reason`, `snapshot_status`, `created_at`.
* **State Machine & Atomic Services:**
  * `@transaction.atomic` mutations with optimistic and pessimistic locking.
  * Separation of duties: Placement Officers verify checklist items; only Placement Head or Admin can sign off on final approval.
  * Strict gate: `all_mandatory_verified` check prevents approval when any mandatory item is pending or rejected.
