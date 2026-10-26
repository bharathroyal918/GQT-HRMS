# GQT HRMS — Role-Based Access Control (RBAC) & Permission Matrix

> **Authoritative Source:** `HRMS - Complete Workflow` (13 Phases, 41 Steps, 19 CRM Modules, 8 AI Capabilities)  
> **Security Model:** Deny-by-default, Least-Privilege, Object-Level Ownership Scoping, Server-Side Authoritative  
> **Document Status:** Authoritative Initial Specification for Phase 1 Greenfield Development

---

## 1. Operational Role Catalogue

The following nine operational roles are derived directly from the operational workflow and responsibilities described in the authoritative specification:

| Role Code | Role Display Name | Primary Workflow Responsibility | Operational Scope |
| :--- | :--- | :--- | :--- |
| **`ADMIN`** | System Administrator | Platform administration, role provisioning, security settings, audit log inspection, system diagnostics. | Organization-wide platform operations. |
| **`PLACEMENT_HEAD`** | Placement Head / Director | Opportunity approvals, JD sign-offs, creative sign-offs, eligibility cohort overrides, final placement resume approval gate, offer acceptance sign-offs, executive analytics. | Departmental & organizational sign-off authority. |
| **`PLACEMENT_OFFICER`** | Placement Officer / Executive | Corporate intake, 12-point JD verification, student publication, student eligibility screening, candidate roster compilation, dispatching profiles to corporate HR, interview coordination, drive day execution, offer letters & joining verification. | Multi-company & multi-drive execution. |
| **`HR_RELATIONSHIP_MGR`** | Corporate CRM & HR Relationship Manager | Corporate discovery, domain classification, high-volume HR outreach (100+ HRs/day), contact directory management, nurturing queues, follow-up scheduling. | Company & HR Contact database. |
| **`CREATIVE_DESIGNER`** | Recruitment Creative Designer | Marketing asset design (flyers, banners, social media posts, QR codes, registration links), submitting design drafts for review. | Creative asset requests & draft revisions. |
| **`TRAINER`** | Placement & Technical Trainer | Student resume reviews, technical assessments, aptitude testing, corporate grooming, communication workshops, mock technical preparation, trainer feedback rubrics. | Student training cohorts & assessment rubrics. |
| **`EVALUATOR`** | Mock Interview Evaluator | Conducting 1-on-1 mock interviews, scoring rubrics (technical skills, problem-solving, communication), submitting readiness evaluations. | Assigned candidate mock interview sessions. |
| **`STUDENT`** | Enrolled Student / Candidate | Profile management, academic metrics, resume version uploads, drive registration, assessment completion, interview attendance confirmation, viewing offer letters, submitting drive feedback. | Self-record strictly (Object-level scoped). |
| **`AUDITOR`** | Compliance & Audit Officer | Inspection of immutable audit trails, credential events, placement verification checklists, and regulatory compliance reports. | Read-only organizational audit & compliance records. |

---

## 2. Module-Level Permission Matrix

Permissions: **R** = Read, **C** = Create, **U** = Update, **D** = Delete, **A** = Approve/Sign-off, **X** = Export, **ADM** = Full Administrative Control.

| # | CRM Module / Domain | `ADMIN` | `PLACEMENT_HEAD` | `PLACEMENT_OFFICER` | `HR_RELATIONSHIP_MGR` | `CREATIVE_DESIGNER` | `TRAINER` | `EVALUATOR` | `STUDENT` | `AUDITOR` |
| :-: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **User & Role Management** | `ADM` | `R` | - | - | - | - | - | - | `R` |
| **2** | **Audit Logs & Security** | `ADM` | `R` | - | - | - | - | - | - | `R` |
| **3** | **Company Directory** | `ADM` | `R, X` | `R, C, U` | `R, C, U, D, X` | - | - | - | - | `R` |
| **4** | **HR Contacts & Outreach** | `ADM` | `R, X` | `R, C, U` | `R, C, U, D, X` | - | - | - | - | `R` |
| **5** | **Follow-up Management** | `ADM` | `R` | `R, C, U` | `R, C, U, D` | - | - | - | - | `R` |
| **6** | **Job Requirements & JDs** | `ADM` | `R, U, A, X` | `R, C, U` | `R` | `R` | - | - | - | `R` |
| **7** | **12-Point JD Checklist** | `ADM` | `R, A` | `R, C, U` | - | - | - | - | - | `R` |
| **8** | **Creative Studio & Posters** | `ADM` | `R, A` | `R, C` | - | `R, C, U` | - | - | - | `R` |
| **9** | **Job Publications & Notices** | `ADM` | `R` | `R, C, U` | - | `R` | `R` | - | `R` (Active) | `R` |
| **10** | **Student Profiles** | `ADM` | `R, X` | `R, C, U, X` | - | - | `R` | `R` | `R, U` (Own) | `R` |
| **11** | **Resumes & ATS Versions** | `ADM` | `R, A, X` | `R, X` | - | - | `R, U` (Review) | `R` | `R, C, U` (Own) | `R` |
| **12** | **Eligibility Engine** | `ADM` | `R, A, U` | `R, C, U` | - | - | - | - | `R` (Own) | `R` |
| **13** | **Assessments & Tests** | `ADM` | `R, X` | `R` | - | - | `R, C, U` | `R` | `R, C` (Take) | `R` |
| **14** | **Mock Interviews & Rubrics** | `ADM` | `R, X` | `R` | - | - | `R, C, U` | `R, C, U` (Assigned)| `R` (Own Feedback)| `R` |
| **15** | **Candidate Submissions & Roster** | `ADM` | `R, A, X` | `R, C, U, X` | - | - | - | - | - | `R` |
| **16** | **Interview Drives & Rounds** | `ADM` | `R, X` | `R, C, U` | `R` | - | - | - | `R, U` (Confirm) | `R` |
| **17** | **Offers & Single-Job Policy** | `ADM` | `R, A, X` | `R, C, U` | - | - | - | - | `R, U` (Accept) | `R` |
| **18** | **360° Feedback Collection** | `ADM` | `R, X` | `R` | `R` (HR) | - | `R, C, U` (Trainer)| - | `R, C` (Student) | `R` |
| **19** | **Reports, Analytics & AI** | `ADM` | `R, X` | `R, X` | `R` | - | `R` | - | - | `R, X` |

---

## 3. Strict Approval Boundaries & Gating Rules

The following institutional sign-offs are strictly enforced at the backend service and API permission layer:

1. **Job Requirement Approval Gate (Step 7):**
   - *Authority:* `PLACEMENT_HEAD` or `ADMIN` only.
   - *Condition:* All 12 criteria in `JDVerificationChecklist` must evaluate to `PASSED`.
   - *Outcome:* JD is locked; transitions state to `APPROVED_FOR_CREATIVES`. Modifying an approved JD requires explicit revocation by the Placement Head.

2. **Creative Draft Approval Gate (Step 9):**
   - *Authority:* `PLACEMENT_HEAD` or authorized Senior `PLACEMENT_OFFICER`.
   - *Condition:* 4-point design verification passed (Flyer accuracy, official logo, registration QR code, valid contact info).
   - *Outcome:* Asset approved for student publication broadcast.

3. **Eligibility Cohort Override Gate (Step 14):**
   - *Authority:* `PLACEMENT_HEAD` or `PLACEMENT_OFFICER`.
   - *Condition:* Mandatory audit reason string (`override_reason`) must be supplied.
   - *Outcome:* Immutable audit log recorded with actor ID, timestamp, and justification.

4. **Final Placement Resume Certification Gate (Step 23):**
   - *Authority:* `PLACEMENT_HEAD` strictly.
   - *Condition:* Candidate must have completed required mock interview and resume iteration cycles.
   - *Rule:* Candidates whose `is_approved_for_placements` is `False` are strictly excluded by backend queryset selectors from company submission rosters (Step 24).

5. **Single-Job Placement Policy Enforcement (Step 40):**
   - *Authority:* Automated transactional service with `PLACEMENT_HEAD` override.
   - *Condition:* When a candidate accepts an official offer, competing active applications are automatically withdrawn under pessimistic database row locking (`select_for_update()`).

---

## 4. Object-Level Scoping & Data Ownership

To prevent broken object-level authorization (IDOR / BOLA):
- **Students (`STUDENT`):** Querysets are strictly scoped to `request.user.student_profile`. A student cannot read, submit, or manipulate any profile, resume, assessment score, or offer letter belonging to another student.
- **Mock Interview Evaluators (`EVALUATOR`):** Can view and submit rubrics only for student sessions specifically assigned to them.
- **Graphic Designers (`CREATIVE_DESIGNER`):** Can view and submit creative draft versions only for jobs assigned to their creative queue.
- **Placement Trainers (`TRAINER`):** Can view and grade student assessment cohorts and feedback forms for batches they instruct.
- **Corporate CRM Managers (`HR_RELATIONSHIP_MGR`):** Can view and manage corporate outreach queues, but cannot modify student placement records or trigger offer withdrawals.

### 4.1. Phase 2 Confirmed Corporate CRM Permissions (Implemented & Verified)
- **CRM Operational Roles:** `ADMIN`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, and `HR_RELATIONSHIP_MGR` hold complete operational read/write access to Companies, HR Contacts, Outreach Logs, Follow-ups, and Dashboard Metrics.
- **Compliance Auditor Role (`AUDITOR`):** Strictly restricted to `SAFE_METHODS` (`GET`, `HEAD`, `OPTIONS`). All mutating operations (`POST`, `PUT`, `PATCH`, `DELETE`) return `403 Forbidden: Auditors hold read-only privileges and cannot modify CRM records`.
- **Denied Roles (`STUDENT`, `CREATIVE_DESIGNER`, `TRAINER`, `EVALUATOR`):** Have zero access to CRM endpoints (`403 Forbidden: You do not have authorization to access Corporate CRM records`).
- **Configuration Management (`CRMConfiguration`):** Updating operational targets like `DAILY_OUTREACH_TARGET` is restricted to `ADMIN` and `PLACEMENT_HEAD` (`IsCRMManagerOrAdmin`).

### 4.2. Phase 3 Confirmed Job Intake & Verification Permissions (Implemented & Verified)
- **Job Intake Operational Roles:** `ADMIN`, `PLACEMENT_HEAD`, and `PLACEMENT_OFFICER` hold complete operational read/create/edit privileges on Job Requirements (`apps.jobs`).
- **Checklist Auditing (`CanVerifyJobChecklist`):** Restricted strictly to `ADMIN`, `PLACEMENT_HEAD`, and `PLACEMENT_OFFICER`. Mutating checklist item status (`VERIFIED`, `REJECTED`, `NOT_APPLICABLE`) and recording verifier remarks is enforced via service-level atomic transactions.
- **Step 7 Approval Gate (`CanApproveJobRequirement`):** Restricted strictly to `ADMIN` and `PLACEMENT_HEAD`. Final approval (`POST /approve/`), rejection (`POST /reject/`), and reopening (`POST /reopen/`) are strictly blocked for `PLACEMENT_OFFICER` (`403 Forbidden: Only Placement Head or Admin can sign off on job requirements`).
- **Checklist Completeness Gating:** Even for `ADMIN` or `PLACEMENT_HEAD`, approval transitions fail with `400 Bad Request` unless all 5 mandatory checklist items are marked `VERIFIED`.
- **Auditor Role (`AUDITOR`):** Strictly restricted to `SAFE_METHODS` (`GET`, `HEAD`, `OPTIONS`). All mutating lifecycle operations return `403 Forbidden`.
- **Downstream Read-Only Roles:** `HR_RELATIONSHIP_MGR` and `CREATIVE_DESIGNER` hold read-only access to Job Requirements for downstream collaboration.
- **Denied Roles (`STUDENT`, `TRAINER`, `EVALUATOR`):** Zero access to Job Intake endpoints (`403 Forbidden`). Students access job notices only after Step 10 official student publication.
- **Post-Approval Immutability:** Once approved, direct editing of job requirements is blocked (`is_editable=False`). Material modifications require explicit reopening by the Placement Head.

---

## 5. Explicitly Denied Actions

| Role | Explicitly Denied Operation | Enforcement Mechanism |
| :--- | :--- | :--- |
| `STUDENT` | Viewing assessment answer keys, evaluator rubric internals, other student profiles, raw company outreach notes. | Serializer field stripping + QuerySet filtering. |
| `STUDENT` | Altering placement readiness status (`is_approved_for_placements`) or eligibility override flags. | Model read-only fields; DRF serializer validation. |
| `CREATIVE_DESIGNER` | Approving job descriptions, publishing job notices, or accessing corporate HR contact directories. | DRF Permission class `HasRole(['PLACEMENT_HEAD', 'PLACEMENT_OFFICER'])`. |
| `EVALUATOR` / `TRAINER` | Generating official candidate submission rosters or dispatching packages to corporate HR. | Service-layer permission check. |
| `HR_RELATIONSHIP_MGR` | Overriding student eligibility cutoffs or certifying student placement resumes. | ViewSet permission classes. |
| `PLACEMENT_OFFICER` | Self-assigning superuser or administrative roles. | `IsSuperUserOrAdmin` permission on User Admin endpoints. |
| All Roles except `ADMIN` | Directly creating, modifying, or truncating `core_audit_log` records. | Immutable model configuration + DRF deny-all view permissions. |

---

## 6. Unresolved Business Decisions for GQT Stakeholders

The following items are not explicitly resolved in the workflow document and are tracked for confirmation:

1. **Student Self-Registration vs. Batch Roster Import:**  
   *Current Decision:* Self-registration is disabled by default; students are provisioned via administrative staff/batch upload or an invite-token link with institutional email verification.
2. **External Recruiter Portal Access:**  
   *Current Decision:* Corporate HR contacts interact via email/phone/submission packages. Direct portal access for external HR contacts is deferred to a future phase and not granted system credentials.
3. **Multi-Role Assignment Precedence:**  
   *Current Decision:* Users can hold multiple roles (e.g., `TRAINER` + `EVALUATOR`). Permissions are evaluated as a union of active role permissions, while approval gates require the specific authorizing role.
