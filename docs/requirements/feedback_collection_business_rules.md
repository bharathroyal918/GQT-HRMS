# GQT HRMS & Recruitment CRM — Phase 9: Feedback Collection Business Rules & Decision Register

> **Status:** Approved Baseline for Phase 9 Implementation  
> **Authoritative Source:** `HRMS Work-Flow.pdf` — Phase 9: Feedback Collection  
> **Target Subsystem:** `apps.feedback` (Django/DRF) + `/feedback` Workspace (React/TypeScript)  
> **Scope Boundary:** Phase 9 (Feedback Collection) ONLY. Phase 10 (CRM Database Update) and subsequent phases are strictly excluded.

---

## 1. Authoritative Workflow Requirements vs. Policy Decisions

| Area | Authoritative Source Requirement | Implemented Baseline Choice | Policy Status / GQT Approval Needed |
| :--- | :--- | :--- | :--- |
| **A. Student Feedback Topics** | 1. Interview Experience<br/>2. Technical Questions<br/>3. Difficulty<br/>4. Suggestions | Structured fields: `interview_experience` (text), `technical_questions` (text/list), `difficulty` (EASY, MEDIUM, HARD, VERY_HARD), `suggestions` (text). | **CONFIRMED** — Exact source terminology preserved. |
| **B. HR Feedback Topics** | 1. Candidate Quality<br/>2. Technical Skills<br/>3. Communication Skills<br/>4. Hiring Satisfaction | Structured fields: `candidate_quality` (POOR, FAIR, GOOD, EXCELLENT), `candidate_quality_remarks`, `technical_skills_rating` (1–5), `technical_skills_remarks`, `communication_skills_rating` (1–5), `communication_skills_remarks`, `hiring_satisfaction_rating` (1–5), `hiring_satisfaction_remarks`. | **CONFIRMED** — Core 4 topics enforced. 1–5 rating scales used for skills/satisfaction with optional remarks. |
| **C. Trainer Feedback Topics** | 1. Student Readiness<br/>2. Training Effectiveness<br/>3. Areas for Improvement | Structured fields: `student_readiness` (NOT_READY, NEEDS_PRACTICE, READY, HIGHLY_READY), `student_readiness_remarks`, `training_effectiveness_rating` (1–5), `training_effectiveness_remarks`, `areas_for_improvement` (text). | **CONFIRMED** — Source topics implemented. |
| **Eligible Submitters** | Students, HR Contacts / Relationship Managers, Trainers. | - Student Feedback: Authenticated `STUDENT` role (self-submitted only).<br/>- HR Feedback: Authenticated `HR_RELATIONSHIP_MGR`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, or `ADMIN` (recording for/with authorized corporate partner).<br/>- Trainer Feedback: Authenticated `TRAINER`, `EVALUATOR`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, or `ADMIN`. | **CONFIRMED** — Role catalog integration enforced. |
| **Anonymity Policy** | Not defined in source workflow. | Student feedback includes `is_anonymous` boolean flag (default `False`). When `is_anonymous=True`, student identity is hidden from aggregated/staff views except Platform `ADMIN` for moderation safety. | **POLICY DECISION** — Awaiting GQT formal policy on whether candidate anonymity is mandatory or optional. Safe optional implementation chosen. |
| **Feedback Editability & Corrections** | Not defined in source workflow. | Submitters may update their feedback within a configurable grace window (or before drive closure). Every update generates an immutable `AuditLog` entry detailing changed fields and actor attribution. | **POLICY DECISION** — Revisions are logged via audit trail. No destructive overwrites without audit tracking. |
| **Access Isolation & Privacy** | Source requires 360° feedback without cross-contamination. | - Students can view ONLY their own student feedback. (Cannot view other students' feedback or confidential HR feedback).<br/>- HR users/managers view only their company/drive feedback.<br/>- Trainers view only feedback for students/sessions they conducted.<br/>- Placement Head & Admin have supervisory access.<br/>- Auditor has read-only access. | **CONFIRMED** — Strict zero cross-user leakage enforced server-side. |
| **Submission Deadlines** | Not defined in source workflow. | No arbitrary expiration or deadline locks are invented. Submissions remain open post-interview / post-training. | **POLICY DECISION** — Awaiting GQT policy on whether automated deadline enforcement (e.g., within 72 hours of interview) should be mandated. |
| **Review & Moderation Workflow** | Not defined in source workflow. | Direct submission into active state (`status = SUBMITTED`). Flagging/moderation can be added if GQT authorizes a review committee. | **CONFIRMED** — Avoided invented multi-stage approval bureaucracy. |
| **Notification Triggers** | Not defined in source workflow. | No automated emails or SMS are sent upon feedback submission to prevent spam/unauthorized communications. | **CONFIRMED** — Preserves fail-safe communication discipline. |
| **CRM Update Integration (Phase 10)** | Source defines Phase 10 as separate phase. | Feedback models are cleanly indexed and relational to `Company`, `StudentProfile`, `JobRequirement`, and `InterviewSchedule`, preparing for Phase 10 synchronization without implementing premature triggers. | **CONFIRMED** — Phase 10 boundaries strictly preserved. |

---

## 2. Feedback Category Specifications

### 2.1 Student Feedback (`StudentFeedback`)
- **Target Actor:** Candidate (`RoleCatalog.STUDENT`).
- **Prerequisites:** Student must have participated in an interview or drive with the target `Company` / `JobRequirement`.
- **Fields:**
  - `student`: Foreign key to `StudentProfile` (derived from `request.user.student_profile`).
  - `company`: Foreign key to `Company` (the interviewing company).
  - `job_requirement`: Nullable foreign key to `JobRequirement`.
  - `interview_schedule`: Nullable foreign key to `InterviewSchedule`.
  - `interview_round`: Nullable foreign key to `InterviewRound`.
  - `interview_experience`: Text description of the overall interview process, interviewer demeanor, venue/connectivity, and organization.
  - `technical_questions`: Text description / list of specific technical, coding, or algorithmic questions asked during rounds.
  - `difficulty`: Choice field: `EASY`, `MEDIUM`, `HARD`, `VERY_HARD`.
  - `suggestions`: Text suggestions for peer students, syllabus training, or future campus drives.
  - `is_anonymous`: Boolean flag indicating whether student requests anonymity in department summaries.
  - `submitted_by`: User foreign key.
- **Invariants:**
  - `student` must equal the authenticated user's profile unless submitter is `ADMIN` performing administrative entry.
  - Duplicate submission guard: A student cannot submit duplicate feedback for the exact same `interview_schedule` (or `job_requirement` if interview is not linked).

### 2.2 Corporate HR Feedback (`HRFeedback`)
- **Target Actor:** Corporate Recruiter / HR Relationship Manager (`HR_RELATIONSHIP_MGR`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `ADMIN`).
- **Fields:**
  - `company`: Foreign key to `Company`.
  - `hr_contact`: Nullable foreign key to `HRContact`.
  - `job_requirement`: Nullable foreign key to `JobRequirement`.
  - `candidate`: Nullable foreign key to `StudentProfile` (supports individual candidate evaluations or overall drive cohorts).
  - `candidate_quality`: Choice field: `POOR`, `FAIR`, `GOOD`, `EXCELLENT`.
  - `candidate_quality_remarks`: Text remarks on candidate caliber, problem-solving, and foundational knowledge.
  - `technical_skills_rating`: Rating integer (1–5 stars).
  - `technical_skills_remarks`: Text remarks on coding proficiency, system knowledge, and tools.
  - `communication_skills_rating`: Rating integer (1–5 stars).
  - `communication_skills_remarks`: Text remarks on articulation, confidence, and language proficiency.
  - `hiring_satisfaction_rating`: Rating integer (1–5 stars).
  - `hiring_satisfaction_remarks`: Text remarks on overall drive satisfaction, institutional support, and future hiring intent.
  - `submitted_by`: User foreign key.
- **Invariants:**
  - Ratings must be bounded between 1 and 5.
  - `company` must match the `job_requirement.company` if job requirement is specified.
  - `candidate` must belong to the drive if specified.

### 2.3 Trainer Feedback (`TrainerFeedback`)
- **Target Actor:** Placement Trainer / Mock Evaluator (`TRAINER`, `EVALUATOR`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `ADMIN`).
- **Fields:**
  - `student`: Foreign key to `StudentProfile`.
  - `training_session`: Nullable foreign key to `TrainingSession`.
  - `student_readiness`: Choice field: `NOT_READY`, `NEEDS_PRACTICE`, `READY`, `HIGHLY_READY`.
  - `student_readiness_remarks`: Text remarks on interview readiness and demeanor.
  - `training_effectiveness_rating`: Rating integer (1–5 stars).
  - `training_effectiveness_remarks`: Text remarks on student absorption of curriculum concepts.
  - `areas_for_improvement`: Text remarks detailing specific gaps (e.g. Data Structures, System Design, Communication, Quantitative Aptitude).
  - `trainer`: User foreign key.
- **Invariants:**
  - `trainer` must be authenticated user.
  - Rating must be bounded between 1 and 5.

---

## 3. Security and RBAC Matrix

| Role | Student Feedback | HR Feedback | Trainer Feedback | Feedback Summaries |
| :--- | :---: | :---: | :---: | :---: |
| **STUDENT** | Create (Own), Read (Own) | Denied | Denied | Denied |
| **TRAINER** / **EVALUATOR** | Denied | Denied | Create, Read (Assigned) | Read (Trainer aggregates) |
| **HR_RELATIONSHIP_MGR** | Denied | Create (Assigned Co.), Read (Assigned Co.) | Denied | Read (HR aggregates) |
| **PLACEMENT_OFFICER** | Read-Only | Create, Read | Create, Read | Read (Full) |
| **PLACEMENT_HEAD** | Read-Only | Create, Read | Create, Read | Read (Full) |
| **ADMIN** | Full (Audit Attributed) | Full | Full | Read (Full) |
| **AUDITOR** | Read-Only (Audited) | Read-Only | Read-Only | Read (Full) |

---

## 4. Unresolved Policy Decisions Awaiting GQT Approval
1. **Mandatory vs. Optional Anonymity:** Should students be allowed to submit anonymous feedback, or must all academic evaluations be identifiable? (Implemented as configurable boolean).
2. **Post-Submission Edit Window:** What is the maximum duration a submitter may edit their feedback before it is permanently locked? (Implemented with audit tracking).
3. **Escalation Rules:** Should low ratings (e.g. Hiring Satisfaction <= 2 or Candidate Quality = POOR) automatically create an alert for the Placement Head? (Deferred to Phase 12 Automated Follow-up).
