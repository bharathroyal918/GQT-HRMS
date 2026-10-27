# GQT HRMS — Phase 10: CRM Database Update
## Business Rules, Architectural Specification & Decision Register

> **Authoritative Source:** `HRMS Work-Flow.pdf` (Phase 10: CRM Database Update)  
> **Status:** Implementation Specification (Phase 10 Scope Only)  
> **Target Subsystems:** Company, HR, Students, Resume Versions, Interview Status, Placement Status, Feedback, Communication History  

---

## 1. Executive Summary & Architecture Principles

Phase 10 provides a unified, reliable, traceable integration and reconciliation layer over the 8 recruitment workflow data areas established across Phases 1 through 9.

### Core Architectural Principles
1. **Zero Shadow Redundancy:** No speculative "master CRM duplicate table" is introduced. Domain models created in Phases 1–9 (`apps.crm`, `apps.jobs`, `apps.students`, `apps.preparation`, `apps.submissions`, `apps.interviews`, `apps.placements`, `apps.feedback`) remain the single authoritative sources of truth for their respective domain entities.
2. **Deterministic Reconciliation:** Synchronization between modules is idempotent, transactionally atomic, and safe to execute repeatedly without duplicating records or corrupting historical timelines.
3. **Preservation of History & Anonymity:** Historical decisions (e.g. revoked offers, past resume versions, interview rounds, previous placement statuses) are never overwritten or deleted. Candidate anonymity options (`is_anonymous`) established in Phase 9 are strictly enforced across all CRM aggregations.
4. **Deny-by-Default Cross-Module Access:** Students cannot view other students' CRM profiles or confidential corporate feedback; corporate HR managers cannot view cross-company candidate submissions; trainers retain assignment-scoped visibility; auditors are strictly read-only.
5. **Conflict Identification Over Destructive Merging:** When contradictory or orphaned records are detected (e.g., conflicting placement outcomes, unapproved resume versions, mismatched HR contacts), they are flagged as structured conflicts for authorized staff review rather than silently picking an arbitrary winner or deleting data.

---

## 2. Authoritative Source Models & Cross-Module Relationships

The eight workflow-mandated areas map to authoritative domain models as follows:

| Area | Authoritative Source Model | Primary Key & Stable Identifiers | Related Domain Models Linked | Authoritative Data Stored | Derived / Aggregated Data |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1. Company** | `apps.crm.models.Company` | UUID `id`, `name`, `normalized_name`, `domain` | `HRContact`, `JobRequirement`, `SubmissionPackage`, `InterviewSchedule`, `CandidatePlacementStatus`, `StudentFeedback`, `HRFeedback`, `OutreachLog`, `FollowUp` | Corporate profile, domain category, tier, ownership, address | Total drives, total submitted, total placed, total joined, average CTC, recruiter satisfaction score, last interaction timestamp |
| **2. HR** | `apps.crm.models.HRContact` | UUID `id`, `company_id`, `email`, `phone` | `Company`, `OutreachLog`, `FollowUp`, `JobRequirement`, `HRFeedback`, `HRInterviewFollowUp` | Recruiter contact profile, designation, direct phone, work email, status | Total drives coordinated, active hiring status, last contact timestamp |
| **3. Students** | `apps.students.models.StudentProfile` | UUID `id`, `user_id`, `roll_number`, `institutional_email` | `User`, `StudentResume`, `StudentApplication`, `PlacementReadinessCertification`, `CandidateSubmission`, `ShortlistedCandidate`, `CandidatePlacementStatus`, `CandidateOfferLetter`, `TrainerFeedback` | Academic identity, college, department, CGPA, graduation batch, verification flag | Current placement status, active offer details, total drives applied, interview attendance rate, trainer readiness evaluation |
| **4. Resume Versions** | `apps.students.models.StudentResume` | UUID `id`, `student_id`, `version_number` | `ResumeReview`, `CandidateSubmission` | Monotonic version number, binary magic bytes (`%PDF-`), SHA-256 hash, private file path | Approval flag (`is_approved_for_submissions`), review score, drives where submitted |
| **5. Interview Status** | `apps.interviews.models.InterviewSchedule` | UUID `id`, `company_id`, `job_requirement_id` | `ShortlistedCandidate`, `InterviewRound`, `HRInterviewFollowUp`, `InterviewReminderLog` | Schedule time, mode (Online/In-person), venue, attendance confirmation, conducted outcome | Round progression count, current round status, recruiter feedback notes |
| **6. Placement Status** | `apps.placements.models.CandidatePlacementStatus` | UUID `id`, `company_id`, `job_requirement_id`, `student_id` | `PlacementStatusHistory`, `CandidateOfferLetter`, `JoiningStatusHistory`, `FinalResultIntake` | Authoritative placement outcome (`SELECTED`, `REJECTED`, `WAITING_LIST`, `HOLD`), designation, offered CTC | Offer acceptance lifecycle (`PENDING`, `ACCEPTED`, `DECLINED`), joining outcome (`JOINED`, `NOT_JOINED`, `DEFERRED`) |
| **7. Feedback** | `apps.feedback.models.StudentFeedback`, `HRFeedback`, `TrainerFeedback` | UUID `id`, submission timestamps | `Company`, `StudentProfile`, `JobRequirement`, `InterviewSchedule` | Interview questions, difficulty, suggestions, anonymity flag; HR ratings (Tech, Comm, Satisfaction); Trainer readiness rubrics | Company aggregate difficulty, recruiter satisfaction average, student readiness status |
| **8. Communication History** | Multi-channel communication records across modules | Unique log UUIDs, timestamps, correlation IDs | `OutreachLog`, `JobPublication`, `ProfileTransmissionLog`, `InterviewReminderLog`, `PlacementNotificationLog`, `AuditLog` | Message timestamp, channel, subject, recipient, dispatch outcome (`SIMULATED`, `SENT`, `FAILED`, `PENDING`), correlation ID | Unified chronological company communication timeline, unified student notification history |

---

## 3. Reconciliation & Health Diagnostic Rules

The Phase 10 synchronization engine evaluates the health of the 8 areas using non-destructive diagnostic rules:

### Area 1: Company & HR Contact Integrity
* **Rule 1.1:** An `HRContact` must be linked to an active, non-deleted `Company`.
* **Rule 1.2:** A `JobRequirement` referencing both `company` and `hr_contact` must ensure `hr_contact.company_id == job_requirement.company_id`. Any mismatch is flagged as `CRITICAL_MISMATCH`.
* **Rule 1.3:** If a company has verified `CandidatePlacementStatus(status='SELECTED')` or `FinalResultIntake` records, its `relationship_status` should be reconciled to `ACTIVE_HIRING_PARTNER`.

### Area 2: Student Identity & Academic Profile Integrity
* **Rule 2.1:** Each `StudentProfile` must have exactly one linked `User` with role `STUDENT`.
* **Rule 2.2:** Normalized institutional email and roll number must be unique across all active student profiles.
* **Rule 2.3:** CGPA must fall within standard bounds ($0.00 \le \text{CGPA} \le 10.00$).

### Area 3: Resume Versions & Submission Linkage
* **Rule 3.1:** Each student must have monotonic resume version numbers ($v1, v2, \dots$) with exactly one marked `is_current=True` (or none if unuploaded).
* **Rule 3.2:** Every `CandidateSubmission` must reference a valid `StudentResume` belonging to that specific student. Cross-student resume linkage is strictly prohibited.
* **Rule 3.3:** Flag submissions referencing unapproved or non-current resume versions as `RESUME_VERSION_WARNING`.

### Area 4: Interview Scheduling & Outcome Consistency
* **Rule 4.1:** An `InterviewSchedule` must link to a valid `ShortlistedCandidate` from the corresponding `SubmissionPackage` and `Company`.
* **Rule 4.2:** If `schedule_status == 'CONDUCTED'`, the interview should have at least one corresponding `InterviewRound` or explicit outcome.
* **Rule 4.3:** Flag schedules where attendance was marked `CONFIRMED` but conducted outcome remains `SCHEDULED` past the scheduled time.

### Area 5: Placement & Offer Letter Integrity
* **Rule 5.1:** A `CandidateOfferLetter` must link exclusively to a `CandidatePlacementStatus` with status `SELECTED`. Offer letters for non-selected candidates are flagged as `INVALID_OFFER_LINKAGE`.
* **Rule 5.2:** `JoiningStatus.JOINED` or `DEFERRED` is only permitted if `OfferAcceptanceStatus == 'ACCEPTED'`. A joined status with pending or declined offer is flagged as `CONTRADICTORY_JOINING_STATUS`.
* **Rule 5.3:** Each status modification must be recorded in `PlacementStatusHistory`.

### Area 6: Feedback & Anonymity Safeguards
* **Rule 6.1:** `StudentFeedback` must belong to the submitting candidate's `StudentProfile` and reference a company/drive they participated in.
* **Rule 6.2:** If `is_anonymous == True`, student identity (name, roll number) must be masked in all aggregated CRM views and API responses for non-admin viewers.
* **Rule 6.3:** `HRFeedback` must be linked to a company authorized for the authenticated HR Relationship Manager.

### Area 7: Unified Communication History
* **Rule 7.1:** Multi-channel communication events (`OutreachLog`, `JobPublication`, `ProfileTransmissionLog`, `InterviewReminderLog`, `PlacementNotificationLog`) are aggregated into a unified, chronological timeline.
* **Rule 7.2:** Delivery statuses must be truthful (`SIMULATED`, `SENT`, `FAILED`, `PENDING`). No simulated or local event may claim live external delivery.
* **Rule 7.3:** No passwords, OTPs, or authentication tokens may be logged in communication history.

---

## 4. Database Changes & Model Addition

To track reconciliation runs and diagnostic audits without duplicating domain records, a single lightweight audit entity is introduced in `apps.crm.models`:

```python
class CRMReconciliationRun(TimeStampedModel):
    """Immutable audit record of Phase 10 CRM database integration and reconciliation runs."""
    triggered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=32, choices=(("SUCCESS", "Success"), ("PARTIAL_WITH_CONFLICTS", "Completed with Conflicts"), ("FAILED", "Failed")), default="SUCCESS")
    total_records_checked = models.PositiveIntegerField(default=0)
    conflicts_detected = models.PositiveIntegerField(default=0)
    records_synchronized = models.PositiveIntegerField(default=0)
    diagnostic_details = models.JSONField(default=dict, blank=True)
    summary = models.TextField(blank=True, default="")
```

---

## 5. Decision Register & GQT Leadership Review

| Decision Item | Confirmed Implementation | Deferred to GQT Approval | Decision Status |
| :--- | :--- | :--- | :--- |
| **Automatic Company Status Promotion** | When verified candidate selections exist, company status upgrades to `ACTIVE_HIRING_PARTNER`. | Whether companies with past hiring that paused for >12 months should automatically degrade to `ON_HOLD`. | **CONFIRMED** (upgrade only; degradation deferred). |
| **Multiple Conflicting Job Selections** | If a candidate is selected in two concurrent recruitment drives, both placement records remain intact and are surfaced in CRM. | Whether GQT enforces an automatic "Single Offer Lock" policy that auto-declines subsequent offers once one offer is accepted. | **DEFERRED** (requires academic leadership sign-off; both offers remain visible). |
| **Orphaned Record Cleanup** | Flagged in diagnostic scan; never deleted automatically. | Whether administrative staff should have a bulk "hard delete" or "soft-archive" button for test records. | **CONFIRMED** (safe archival / flag only; zero silent deletions). |
| **Cross-Module Communication Timeline** | Unified timeline aggregating 6 log sources into a coherent chronological feed. | Whether outgoing emails should support live webhook tracking for read-receipts. | **DEFERRED** (requires external provider configuration in Phase 12). |
