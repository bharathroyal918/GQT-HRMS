# GQT HRMS — Phase 3: Job Intake & Verification Data Model

> **Module:** `apps.jobs`  
> **Source of Truth:** `HRMS - Complete Workflow` (Phase 2: Job Requirement Management, Steps 5–7)  
> **Target Database Engine:** Supabase PostgreSQL 16 / SQLite 3 for local development  

---

## 1. Domain Entity-Relationship Overview

```
┌────────────────────────────────┐         ┌────────────────────────────────┐
│         crm_company            │         │         crm_hr_contact         │
│  (Parent Corporate Partner)    │         │  (Corporate Lead / Source)     │
└───────────────┬────────────────┘         └───────────────┬────────────────┘
                │ 1                                        │ 0..1
                │                                          │
                │ 1..* (PROTECT)                           │ 0..* (SET_NULL)
                ▼                                          ▼
┌───────────────────────────────────────────────────────────────────────────┐
│                             jobs_requirement                              │
│  - id: UUID (PK)                                                          │
│  - title: VARCHAR(255)                                                    │
│  - job_description: TEXT                                                  │
│  - skills_required: TEXT                                                  │
│  - min_salary / max_salary: NUMERIC(12, 2)                                │
│  - salary_currency: VARCHAR(10)                                           │
│  - salary_breakup: TEXT                                                   │
│  - location: VARCHAR(255)                                                 │
│  - work_arrangement: VARCHAR(30) (ON_SITE, HYBRID, REMOTE)                 │
│  - employment_type: VARCHAR(30) (FULL_TIME, INTERNSHIP, INTERNSHIP_PPO)   │
│  - has_bond: BOOLEAN                                                      │
│  - bond_details: TEXT                                                     │
│  - eligibility_criteria: TEXT                                             │
│  - min_cgpa: NUMERIC(4, 2)                                                │
│  - hiring_process: TEXT                                                   │
│  - interview_date: DATE (Nullable)                                       │
│  - registration_deadline: TIMESTAMPTZ                                     │
│  - openings_count: INTEGER                                                │
│  - status: VARCHAR(30) (DRAFT, PENDING_VERIFICATION, UNDER_REVIEW, etc.)  │
│  - created_by, assigned_verifier, verified_by, approved_by: FKs to User   │
│  - verified_at, approved_at: TIMESTAMPTZ                                  │
│  - rejection_reason, return_reason, notes: TEXT                           │
│  - is_archived, is_deleted: BOOLEAN                                       │
└─────────────────────┬───────────────────────────────┬─────────────────────┘
                      │ 1                             │ 1
                      │                               │
                      │ 1..* (CASCADE)                │ 0..* (CASCADE)
                      ▼                               ▼
┌──────────────────────────────────────────┐ ┌──────────────────────────────┐
│           jobs_checklist_item            │ │    jobs_approval_decision    │
│  - id: UUID (PK)                         │ │  - id: UUID (PK)             │
│  - job_requirement_id: UUID (FK)        │ │  - job_requirement_id: UUID  │
│  - item_code: VARCHAR(64)                │ │  - decision: VARCHAR(50)     │
│  - title: VARCHAR(255)                   │ │  - actor_id: UUID (FK User)  │
│  - description: TEXT                     │ │  - actor_role: VARCHAR(50)   │
│  - is_mandatory: BOOLEAN (True)          │ │  - comments: TEXT            │
│  - status: PENDING, VERIFIED, REJECTED   │ │  - created_at: TIMESTAMPTZ   │
│  - verified_by_id: UUID (FK User)        │ └──────────────────────────────┘
│  - verified_at: TIMESTAMPTZ              │
│  - remarks: TEXT                         │
│  - UNIQUE(job_requirement, item_code)    │
└──────────────────────────────────────────┘
```

---

## 2. Model Specifications

### 2.1 `JobRequirement` (`jobs_requirement`)
Implements Step 5 (Collect Job Description) and coordinates Steps 6–7 lifecycle transitions.

| Column | Data Type | Nullable | Constraints & Description |
| :--- | :--- | :---: | :--- |
| `id` | `UUID` | No | Primary key, UUIDv4 non-enumerable. |
| `company_id` | `UUID` | No | Foreign key to `crm_company`, `ON DELETE PROTECT`. |
| `hr_contact_id` | `UUID` | Yes | Foreign key to `crm_hr_contact`, `ON DELETE SET_NULL`. Enforced at service layer: `hr_contact.company_id == company.id`. |
| `title` | `VARCHAR(255)` | No | Role designation (e.g., "Associate Software Engineer"). Indexed. |
| `job_description` | `TEXT` | No | Full role overview, primary responsibilities, and team scope. |
| `skills_required` | `TEXT` | No | Required technical languages, frameworks, and proficiencies. |
| `min_salary` | `NUMERIC(12, 2)` | Yes | Minimum CTC in currency units. Must satisfy `min_salary <= max_salary`. |
| `max_salary` | `NUMERIC(12, 2)` | Yes | Maximum CTC in currency units. |
| `salary_currency` | `VARCHAR(10)` | No | Default: `"INR"`. Supported: `"INR"`, `"USD"`, `"EUR"`. |
| `salary_breakup` | `TEXT` | Yes | Fixed salary, variable incentives, probation stipend, training deductions. |
| `location` | `VARCHAR(255)` | No | Primary base office / campus drive location. |
| `work_arrangement` | `VARCHAR(30)` | No | `ON_SITE`, `HYBRID`, `REMOTE`. |
| `employment_type` | `VARCHAR(30)` | No | `FULL_TIME`, `INTERNSHIP`, `INTERNSHIP_PPO`, `CONTRACT`. |
| `has_bond` | `BOOLEAN` | No | Default `False`. Indicates mandatory service agreement. |
| `bond_details` | `TEXT` | Yes | Duration and penalty terms if bond required. |
| `eligibility_criteria` | `TEXT` | Yes | Branch cutoffs, backlogs, and academic qualifications. |
| `min_cgpa` | `NUMERIC(4, 2)` | Yes | Minimum academic CGPA cutoff on a 10.0 scale. |
| `hiring_process` | `TEXT` | Yes | Sequential stages (e.g., Aptitude &rarr; Technical &rarr; HR). |
| `interview_date` | `DATE` | Yes | Tentative or confirmed drive date. |
| `registration_deadline` | `TIMESTAMPTZ` | No | Strict cutoff for student applications. Indexed. |
| `openings_count` | `INTEGER` | No | Available hiring headcount (default: `1`). |
| `status` | `VARCHAR(30)` | No | Lifecycle state: `DRAFT`, `PENDING_VERIFICATION`, `UNDER_REVIEW`, `CHANGES_REQUESTED`, `VERIFIED`, `APPROVED`, `REJECTED`. Indexed. |
| `created_by_id` | `UUID` | Yes | FK to `accounts_user`, `SET_NULL`. Placement Officer who initiated intake. |
| `assigned_verifier_id`| `UUID` | Yes | FK to `accounts_user`, `SET_NULL`. Reviewer assigned to audit checklist. |
| `verified_by_id` | `UUID` | Yes | FK to `accounts_user`, `SET_NULL`. User completing checklist audit. |
| `verified_at` | `TIMESTAMPTZ` | Yes | Timestamp when all mandatory checklist items evaluated to `VERIFIED`. |
| `approved_by_id` | `UUID` | Yes | FK to `accounts_user`, `SET_NULL`. Placement Head signing off. |
| `approved_at` | `TIMESTAMPTZ` | Yes | Timestamp when opportunity was formally approved and locked. |
| `rejection_reason` | `TEXT` | Yes | Documented rationale if declined. |
| `return_reason` | `TEXT` | Yes | Required feedback when returned for correction. |
| `notes` | `TEXT` | Yes | Internal operational and audit remarks. |
| `is_archived` | `BOOLEAN` | No | Default `False`. Soft-archival flag. Indexed with status. |
| `is_deleted` | `BOOLEAN` | No | Soft-deletion flag from `TimeStampedModel`. |
| `created_at` | `TIMESTAMPTZ` | No | Auto-set creation timestamp (UTC). Indexed. |
| `updated_at` | `TIMESTAMPTZ` | No | Auto-set last modification timestamp (UTC). |

---

### 2.2 `JobChecklistItem` (`jobs_checklist_item`)
Implements Step 6 (Verify Job Details). Normalizes verification criteria with per-item reviewer attribution.

| Column | Data Type | Nullable | Constraints & Description |
| :--- | :--- | :---: | :--- |
| `id` | `UUID` | No | Primary key, UUIDv4 non-enumerable. |
| `job_requirement_id`| `UUID` | No | Foreign key to `jobs_requirement`, `ON DELETE CASCADE`. |
| `item_code` | `VARCHAR(64)` | No | Code matching authoritative Step 6 specs (`ELIGIBILITY`, `SALARY_AUTHENTICITY`, `COMPANY_AUTHENTICITY`, `INTERVIEW_PROCESS`, `REGISTRATION_DEADLINE`). |
| `title` | `VARCHAR(255)` | No | Human-readable criterion title. |
| `description` | `TEXT` | Yes | Audit instructions and guidance for the verifier. |
| `is_mandatory` | `BOOLEAN` | No | Default `True`. All mandatory items must evaluate to `VERIFIED` before approval is unlocked. |
| `status` | `VARCHAR(30)` | No | `PENDING`, `VERIFIED`, `REJECTED`, `NOT_APPLICABLE`. Default: `PENDING`. Indexed. |
| `verified_by_id` | `UUID` | Yes | FK to `accounts_user`, `SET_NULL`. Placement Officer who audited this item. |
| `verified_at` | `TIMESTAMPTZ` | Yes | UTC timestamp of decision. |
| `remarks` | `TEXT` | Yes | Audit notes, discrepancies found, or justification. |
| `created_at` | `TIMESTAMPTZ` | No | Creation timestamp. |
| `updated_at` | `TIMESTAMPTZ` | No | Update timestamp. |

**Database Constraints:**
* Composite unique constraint: `UniqueConstraint(fields=['job_requirement', 'item_code'], name='unique_job_checklist_item')`.

---

### 2.3 `JobApprovalDecision` (`jobs_approval_decision`)
Provides an immutable decision and audit log for review milestones (Step 7).

| Column | Data Type | Nullable | Description |
| :--- | :--- | :---: | :--- |
| `id` | `UUID` | No | Primary key, UUIDv4. |
| `job_requirement_id`| `UUID` | No | Foreign key to `jobs_requirement`, `ON DELETE CASCADE`. |
| `decision` | `VARCHAR(50)` | No | `SUBMITTED`, `CHANGES_REQUESTED`, `VERIFIED`, `APPROVED`, `REJECTED`, `REOPENED`. |
| `actor_id` | `UUID` | Yes | FK to `accounts_user`, `SET_NULL`. Operator executing action. |
| `actor_role` | `VARCHAR(50)` | Yes | Comma-delimited active roles held by the actor at decision time. |
| `comments` | `TEXT` | Yes | Mandatory or contextual comments explaining the decision. |
| `created_at` | `TIMESTAMPTZ` | No | Immutable timestamp when decision occurred. |

---

## 3. Database Indexes

To support production query patterns at scale:
1. `jobs_requir_company_baf94c_idx`: `(company_id, status)` for company-specific opportunity listings.
2. `jobs_requir_status_184884_idx`: `(status, registration_deadline)` for operational queues and expiring drive alerts.
3. `jobs_requir_is_arch_754679_idx`: `(is_archived, status)` for active vs archived directory filtering.
4. `jobs_checklist_item_status_idx`: `(status)` for quick verification status counting.
