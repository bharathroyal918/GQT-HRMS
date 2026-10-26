# GQT HRMS — Phase 3: Job Intake & Verification Business Rules

> **Domain:** Job Requirement Management (Steps 5–7)  
> **Source Document:** `HRMS - Complete Workflow` (Authoritative Business Truth)  

---

## 1. Authoritative Workflow Mapping (Steps 5–7)

### Step 5: Collect Job Description
The corporate relationship lead or placement officer ingests the following 10 mandatory and structured attributes from the corporate hiring partner:
1. **Role Title:** Explicit corporate designation.
2. **Job Description:** Complete operational scope and day-to-day responsibilities.
3. **Required Skills:** Mandatory and preferred technical languages, frameworks, and proficiencies.
4. **Salary / Compensation:** Annual gross CTC, monthly training/probation stipend, and breakdown of fixed vs. variable components.
5. **Location & Work Arrangement:** Base office, campus location, or hybrid/remote classification.
6. **Bond / Service Agreement:** Exact duration and financial penalty clauses, if applicable.
7. **Eligibility Criteria:** Permitted degree streams, passing-out batches, minimum percentage/CGPA cutoff, and maximum allowable active backlogs.
8. **Hiring Process:** Number and sequence of evaluation stages (e.g., Online Aptitude &rarr; Technical Coding &rarr; HR Interview).
9. **Interview Date:** Confirmed or tentative drive day schedule.
10. **Registration Deadline:** Strict application cutoff timestamp for candidate registrations.

---

### Step 6: Verify Job Details (5-Point Institutional Checklist)

#### Discrepancy Analysis & Confirmed Specification
* **Source Workflow Ground Truth (`HRMS - Complete Workflow`):** Step 6 specifies exactly **5 explicit verification criteria**:
  1. *Eligibility*
  2. *Salary*
  3. *Company authenticity*
  4. *Interview process*
  5. *Deadline*
* **Previous Documentation Discrepancy:** Initial exploratory drafts (`docs/security/role_permission_matrix.md` and `docs/requirements/workflow_traceability.md`) made references to a "12-Point JD Checklist", while an early README preview referred to a "15-point checklist". Neither of those documents enumerated all items beyond illustrative examples.
* **Confirmed Architectural Decision:** Phase 3 strictly implements the **authoritative 5-point verification checklist** derived directly from Step 6 of the business source document, implemented via an extensible relational model (`JobChecklistItem`) supporting future expansion without schema alterations.

#### The 5 Default Verification Specifications:
1. **`ELIGIBILITY` — Candidate Academic & Degree Eligibility:**  
   *Reviewer Audit:* Verify that degree branches, graduation batches, minimum CGPA/percentage, and backlog allowances align with GQT institutional academic policies and student enrollment records.
2. **`SALARY_AUTHENTICITY` — Salary Package & CTC Authenticity:**  
   *Reviewer Audit:* Confirm that gross CTC, net in-hand estimates, probation stipends, performance variables, and any service agreement deductions are documented accurately and do not mislead candidates.
3. **`COMPANY_AUTHENTICITY` — Company Authenticity & Hiring Legitimacy:**  
   *Reviewer Audit:* Validate corporate registration, corporate root domain (`website`), active corporate email authority of the HR contact, and verify genuine hiring partner track record.
4. **`INTERVIEW_PROCESS` — Interview & Selection Process Clarity:**  
   *Reviewer Audit:* Ensure complete transparency regarding evaluation stages (online tests, technical coding rounds, managerial/HR interviews), test platforms, and infrastructure requirements.
5. **`REGISTRATION_DEADLINE` — Registration Deadline & Drive Timelines:**  
   *Reviewer Audit:* Verify that the application deadline provides students reasonable lead time to register and prepare, and aligns with institutional academic drive calendars.

---

### Step 7: Internal Approval Gate
* **Approving Authority:** `PLACEMENT_HEAD` or `ADMIN` exclusively.
* **Pre-condition Gate:** **All 5 mandatory checklist items must evaluate to `VERIFIED` (`is_complete == True`).**  
  If any mandatory checklist item remains in `PENDING` or `REJECTED`, the backend service strictly raises a `ValidationError` and refuses approval.
* **Post-condition:** The job requirement is marked `APPROVED`, `approved_by` and `approved_at` are stamped, and the opportunity is **locked** against arbitrary edits. It is immediately unlocked for Phase 4 (Creative Design Studio).

---

## 2. Complete Lifecycle State Machine

The requirement advances through seven explicit operational states:

```
                  ┌───────────────┐
                  │     DRAFT     │◄──────────────────────────┐
                  └───────┬───────┘                           │
                          │ submit_for_verification()         │
                          ▼                                   │
             ┌─────────────────────────┐                      │
             │  PENDING_VERIFICATION   │                      │
             └────────────┬────────────┘                      │
                          │ verify_checklist_item()           │
                          ▼                                   │
             ┌─────────────────────────┐   return_for_        │
             │      UNDER_REVIEW       │   correction()       │
             └────────────┬────────────┴──────────────────────┤
                          │                                   │
                          ├───────────────────────────────────┼──────────┐
                          │ (all 5 items VERIFIED)            │          │
                          ▼                                   │          │
             ┌─────────────────────────┐                      │          │
             │        VERIFIED         │──────────────────────┘          │
             └────────────┬────────────┘                                 │
                          │                                              │
        ┌─────────────────┴─────────────────┐                            │
        │ approve()                         │ reject()                   │
        ▼                                   ▼                            │
┌───────────────┐                   ┌───────────────┐                    │
│   APPROVED    │                   │   REJECTED    │                    │
│ (JD Locked)   │                   │ (Documented)  │                    │
└───────┬───────┘                   └───────┬───────┘                    │
        │                                   │                            │
        └─────────────────┬─────────────────┘                            │
                          │ reopen_job_requirement()                     │
                          ▼                                              │
             ┌─────────────────────────┐                                 │
             │      UNDER_REVIEW       │◄────────────────────────────────┘
             └─────────────────────────┘
```

### State Transition Matrix

| Source State | Destination State | Permitted Roles | Required Pre-conditions & Inputs | Audit Event | Error on Violation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DRAFT` | `PENDING_VERIFICATION` | `PLACEMENT_OFFICER`, `PLACEMENT_HEAD`, `ADMIN` | Title, description, location, deadline present. | `JOB_SUBMITTED_FOR_VERIFICATION` | `400 Bad Request` |
| `CHANGES_REQUESTED` | `PENDING_VERIFICATION` | `PLACEMENT_OFFICER`, `PLACEMENT_HEAD`, `ADMIN` | Updated fields saved. | `JOB_SUBMITTED_FOR_VERIFICATION` | `400 Bad Request` |
| `PENDING_VERIFICATION` | `UNDER_REVIEW` | `PLACEMENT_OFFICER`, `PLACEMENT_HEAD`, `ADMIN` | First checklist item audited. | `JOB_CHECKLIST_ITEM_VERIFIED` | `400 Bad Request` |
| `UNDER_REVIEW` | `VERIFIED` | Automatic Service Transition | All 5 mandatory checklist items evaluated to `VERIFIED`. | `JOB_CHECKLIST_ITEM_VERIFIED` | N/A |
| `PENDING_VERIFICATION` / `UNDER_REVIEW` / `VERIFIED` | `CHANGES_REQUESTED` | `PLACEMENT_OFFICER`, `PLACEMENT_HEAD`, `ADMIN` | Mandatory non-empty `reason` string explaining needed changes. | `JOB_RETURNED_FOR_CORRECTION` | `400 Bad Request` ("Reason mandatory") |
| `VERIFIED` / `UNDER_REVIEW` | `APPROVED` | `PLACEMENT_HEAD`, `ADMIN` | **All 5 checklist items must be `VERIFIED`.** | `JOB_REQUIREMENT_APPROVED` | `400 Bad Request` ("All mandatory items must be VERIFIED") / `403 Forbidden` |
| `PENDING_VERIFICATION` / `UNDER_REVIEW` / `VERIFIED` | `REJECTED` | `PLACEMENT_HEAD`, `ADMIN` | Mandatory non-empty `rejection_reason` string. | `JOB_REQUIREMENT_REJECTED` | `400 Bad Request` / `403 Forbidden` |
| `APPROVED` / `REJECTED` | `UNDER_REVIEW` | `PLACEMENT_HEAD`, `ADMIN` | Mandatory `comments` justifying the reopening of locked opportunity. Clears previous approval timestamp. | `JOB_REQUIREMENT_REOPENED` | `403 Forbidden` / `400 Bad Request` |

---

## 3. Separation of Duties & Security Guardrails

1. **Intake vs. Approval Separation:**
   * `PLACEMENT_OFFICER` can collect requirements, create drafts, and audit checklist items.
   * `PLACEMENT_OFFICER` cannot execute `approve()` or `reject()`. Attempts return `403 Forbidden`.
   * Only `PLACEMENT_HEAD` and `ADMIN` hold executive sign-off authority.
2. **Locked Opportunity Protection:**
   * Once a requirement transitions to `APPROVED`, direct mutation via `PATCH /api/v1/jobs/requirements/{id}/` is strictly rejected by the service layer (`is_editable == False`).
   * To revise an approved opportunity, the Placement Head must explicitly invoke `reopen()`, documenting the business justification.
3. **Auditor Read-Only Boundary:**
   * The `AUDITOR` role has full read access across all requirements, verification items, and decision history logs (`SAFE_METHODS`).
   * Any mutating attempt (`POST`, `PATCH`, `DELETE`) by an auditor triggers an explicit `403 Forbidden` ("Auditors hold read-only privileges").
4. **Student & Unrelated Role Isolation:**
   * Roles `STUDENT`, `TRAINER`, and `EVALUATOR` receive `403 Forbidden` across all internal `/api/v1/jobs/` endpoints.
