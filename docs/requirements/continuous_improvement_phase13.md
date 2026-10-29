# GQT HRMS — PHASE 13: CONTINUOUS IMPROVEMENT
## Evidence-Based Recruitment, Training & Placement Quality Loop
**Specification, Business Rules & Operational Blueprint**

---

### 1. Architectural Summary & System Context

Phase 13 establishes the **Continuous Improvement** feedback loop for the GQT HRMS platform. It turns disparate transactional records (applications, shortlists, interview attendance, final selections, multi-offer letters, joining confirmations, recruiter remarks, student reviews, and trainer assessments) into an auditable, evidence-based improvement system.

#### Core Principles:
- **Zero AI / Deterministic Analytics:** No predictive machine learning, synthetic resume scoring, or automated AI text generation is used. All metrics and matrices derive deterministically from stored PostgreSQL records.
- **Strict Role-Based Authorization:** Placement Head authorization is required for approving remedial training plans and committing recruitment cycle reviews. Students remain strictly isolated from aggregate organizational reports and recruiter feedback.
- **Data Provenance & Mathematical Proof:** Every rate metric documents its exact numerator, denominator, formula, and source population. Division-by-zero errors are mathematically guarded.
- **Institutional Anonymity Protection:** Student feedback aggregations enforce a minimum cohort threshold (minimum 3 responses) to prevent deanonymization of individual candidates.

---

### 2. The Five Phase 13 Responsibilities

```
                                +-----------------------------+
                                | 1. Analyze Placement Rate   |
                                | Distinct Student Funnel &   |
                                | Multi-Offer Yield           |
                                +--------------+--------------+
                                               |
                                               v
+-----------------------------+ <--------------+------------> +-----------------------------+
| 2. Analyze Feedback         |                               | 3. Identify Skill Gaps      |
| Anonymized Recruiter,       |                               | Industry Demand vs Internal |
| Student & Trainer Insights  |                               | Assessment Pass Rates       |
+--------------+--------------+                               +--------------+--------------+
               |                                                             |
               +-----------------------+     +-------------------------------+
                                       |     |
                                       v     v
                                +-----------------------------+
                                | 4. Plan New Training        |
                                | Remedial Plans with         |
                                | Placement Head Approval     |
                                +--------------+--------------+
                                               |
                                               v
                                +-----------------------------+
                                | 5. Repeat Recruitment Cycle |
                                | Frozen Baseline Snapshots & |
                                | Traceable Action Items      |
                                +-----------------------------+
```

---

### 3. Capability A — Placement Rate Analytics

#### Multi-Offer & Distinct Candidate Model:
Institutional placement must distinguish between **events** (applications, interviews, selections, offer letters) and **distinct candidates**. A single candidate selected by 3 companies represents 3 selection events and 3 offer letters, but only **1 placed student**.

#### Documented Metric Formulas:

| Metric Name | Numerator | Denominator | Formula | Provenance |
| :--- | :--- | :--- | :--- | :--- |
| **Eligible Cohort Placement Rate** | Distinct verified students selected (≥1 offer) | Total placement-verified eligible cohort students | `(Selected Distinct / Eligible Verified) * 100` | Step 36 (Intake) vs Step 20 (Profile) |
| **Applicant Placement Rate** | Distinct verified students selected (≥1 offer) | Distinct students who submitted ≥1 job application | `(Selected Distinct / Applicants Distinct) * 100` | Step 36 vs Step 24 (Applications) |
| **Interview Selection Rate** | Distinct verified students selected | Distinct students who attended ≥1 interview session | `(Selected Distinct / Interviewed Distinct) * 100` | Step 36 vs Step 32 (Schedules) |
| **Offer Acceptance Rate** | Total accepted offer letters | Total resolved offers (Accepted + Declined) | `(Accepted Offers / Resolved Offers) * 100` | Step 40 (Offer Letters) |
| **Confirmed Joining Rate** | Distinct students confirmed joined | Distinct students who accepted offers | `(Joined Distinct / Accepted Distinct) * 100` | Step 41 (Joining Status) |
| **Overall Pipeline Yield** | Distinct students confirmed joined | Total placement-verified eligible cohort students | `(Joined Distinct / Eligible Verified) * 100` | Step 41 vs Step 20 |

#### Multi-Offer Distribution:
The analytics engine classifies placed candidates into:
- Single-offer recipients
- Dual-offer recipients
- Multi-offer recipients (3+ offers)
- Pending outcome candidates (selected candidates awaiting final offer decision or joining confirmation)

---

### 4. Capability B — Cross-Category Feedback Intelligence

#### Aggregated Categories:
1. **Corporate Recruiter Feedback (HR):**
   - Candidate Technical Skills Rating (1–5 scale)
   - Candidate Professional Communication Rating (1–5 scale)
   - Hiring Satisfaction Rating (1–5 scale)
   - Candidate Quality distribution (`EXCELLENT`, `GOOD`, `AVERAGE`, `BELOW_AVERAGE`, `UNSATISFACTORY`)
   - Qualitative Recruiter Remarks
2. **Candidate Interview Experiences (Student):**
   - Perceived Interview Difficulty (`EASY`, `MEDIUM`, `HARD`)
   - Qualitative Interview Questions & Observations
   - Candidate Suggestions for Pre-Placement Training
3. **Trainer Readiness Assessments (Trainer):**
   - Student Placement Readiness (`HIGHLY_READY`, `READY`, `NEEDS_PRACTICE`, `NOT_READY`)
   - Training Effectiveness Rating (1–5 scale)
   - Qualitative Areas for Remedial Improvement

#### Privacy & Anonymity Safeguards:
- **Minimum-Group Threshold (k-Anonymity = 3):** If a filtered cohort yields fewer than 3 student feedback records, individual qualitative suggestions and difficulty counts are suppressed with a prominent privacy notice to prevent deanonymization.
- **Untrusted User Content Sanitization:** All free-text suggestions, remarks, and interview questions are treated strictly as untrusted text, escaping HTML and stripping executable formula prefixes (`=`, `+`, `-`, `@`) during CSV exports.
- **Scoping for HR Relationship Managers:** HR Relationship Managers are scoped strictly to feedback records originating from corporate accounts assigned under their management.

---

### 5. Capability C — Evidence-Based Skill Gap Matrix

#### Canonical Skill Resolution:
Market skills declared in `JobRequirement.skills_required` and student test tracks in `AssessmentTest.domain_track` are normalized against canonical technology taxonomies (e.g. `Python`, `Django`, `React`, `Data Structures`, `SQL`, `AWS Cloud`).

#### Evidence Coverage Categories:
- **`EVALUATED_WELL`:** In-demand skill with internal assessment tests having a cohort pass rate ≥ 60%.
- **`CRITICAL_GAP`:** In-demand skill with internal assessment tests having a cohort pass rate < 60%. Requires prioritized remedial intervention.
- **`UNASSESSED_DEMAND`:** Skill required across multiple enterprise job descriptions with zero internal assessment attempts. Requires curriculum creation.
- **`SUFFICIENT_EVIDENCE`:** Assessed skill with healthy student profile coverage.

---

### 6. Capability D — Strategic Remedial Training Plans

#### Safe Lifecycle Workflow:
```
[DRAFT]  --->  [PROPOSED]  --->  [APPROVED]  --->  [SCHEDULED]  --->  [IN_PROGRESS]  --->  [COMPLETED]
   |                |                 |                                                      |
   +----------------+-----------------+------------------------------------------------------+---> [CANCELLED]
```

#### Authorization & Safety Invariants:
1. **Placement Head Authorization:** A training plan can only be approved by users holding the `ADMIN` or `PLACEMENT_HEAD` role.
2. **Immutable Placement Readiness:** Creating, approving, or completing a training plan **cannot** automatically alter a student's `PlacementReadinessCertification` (Step 23) or modify historical placement records.
3. **Audit Logging:** Every state transition (`PROPOSED`, `APPROVED`, `IN_PROGRESS`, `COMPLETED`, `CANCELLED`) writes an immutable record to `core.AuditLog` with user ID, timestamps, and transition notes.

---

### 7. Capability E — Recruitment Cycle Reviews

#### Continuous Cycle Improvement:
1. **Frozen Baseline Metrics Snapshot:** Captures the institutional placement rate, verified eligible population count, and selection totals at the moment of cycle initiation. These frozen metrics prevent historical revisionism when subsequent placement records arrive.
2. **Trackable Improvement Action Items:** Each cycle review binds measurable action items across categories:
   - `CURRICULUM_TRAINING`
   - `INTERVIEW_PREP`
   - `CORPORATE_OUTREACH`
   - `STUDENT_POLICY`
   - `ASSESSMENT_UPGRADE`
3. **Explicit Operational Controls:** Cycle closures or rollovers never trigger automated bulk job republications, student profile dispatches, or external candidate notifications.

---

### 8. Data Quality Diagnostics (6-Point Audit)

The continuous improvement engine includes 6 automated diagnostics:
1. **`CHK_ORPHAN_PLACEMENTS`:** Identifies placement results lacking verified intake records.
2. **`CHK_DUPLICATE_SUBMISSIONS`:** Detects duplicate candidate submissions for the same job.
3. **`CHK_UNRESOLVED_OFFERS`:** Flags offers lingering in `PENDING_RESPONSE` or candidates pending joining for >30 days.
4. **`CHK_UNASSESSED_DEMAND`:** Flags high-demand market skills lacking internal assessment evaluations.
5. **`CHK_ANONYMITY_THRESHOLD`:** Warns when cohort filters produce <3 responses.
6. **`CHK_OVERDUE_ACTIONS`:** Audits incomplete improvement action items past due date.

---

### 9. API Reference & Endpoint Catalog

All endpoints mounted under `/api/v1/continuous-improvement/`:

| Method | Endpoint | Description | Permitted Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/placement-rate/` | Distinct funnel analytics, rates, & definitions | Staff, Auditor, HR Mgr |
| `GET` | `/placement-rate/export/` | Sanitized CSV export of placement rates | Staff, Auditor |
| `GET` | `/feedback-intelligence/` | Aggregated 3-category feedback & ratings | Staff, Auditor, Trainer, HR Mgr |
| `GET` | `/skill-gap-matrix/` | Evidence-based skill demand vs pass rates | Staff, Auditor, Trainer, Evaluator |
| `GET` | `/skill-gap-matrix/export/`| Sanitized CSV export of skill matrix | Staff, Auditor |
| `GET` | `/training-plans/` | List remedial training plans | Staff, Auditor, Trainer |
| `POST` | `/training-plans/` | Create draft remedial training plan | Placement Head, Admin, Officer |
| `POST` | `/training-plans/<id>/transition/` | State transition with approval/completion notes | Placement Head (for approval) |
| `GET` | `/training-plans/export/`| Sanitized CSV export of training plans | Staff, Auditor |
| `GET` | `/recruitment-cycles/` | List cycle reviews & action items | Staff, Auditor |
| `POST` | `/recruitment-cycles/` | Initiate cycle review & freeze baseline | Placement Head, Admin |
| `POST` | `/cycle-actions/` | Bind improvement action item | Placement Head, Admin, Officer |
| `PATCH`| `/cycle-actions/<id>/` | Update action item progress or status | Placement Head, Admin, Owner |
| `GET` | `/diagnostics/` | 6-point continuous improvement diagnostic scan | Staff, Auditor |
