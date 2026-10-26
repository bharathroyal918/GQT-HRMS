# Phase 6: Student Preparation — Domain Architecture & Business Rules
## Workflow Steps 15–23 Specification

> **Authoritative Baseline:** `HRMS - Complete Workflow` (Phase 4: Student Preparation)  
> **Target Django Application:** `backend/apps/preparation` (`apps.preparation.apps.PreparationConfig`)  
> **API Root Namespace:** `/api/v1/preparation/`  
> **Frontend Module:** `frontend/src/pages/preparation/` (`ResumeReviewWorkspacePage`, `StudentAssessmentsPage`, `MockInterviewWorkspacePage`, `PlacementReadinessGatePage`)  
> **Quality Gate Status:** 100% Passing (160 backend pytest tests, 41 frontend vitest tests, 0 migration drift, strict TypeScript clean, production Vite bundle clean)

---

## 1. Domain Overview & Workflow Mapping

| Step # | Authoritative Workflow Step | Business Purpose & Operational Gate | Authorized Roles | Primary Model & Service |
| :--- | :--- | :--- | :--- | :--- |
| **Step 15** | **Resume Review** | Placement trainers evaluate student resumes against institutional standards/rubric (formatting, technical skills, projects, achievements 1-10 scale). | `TRAINER`, `PLACEMENT_OFFICER`, `PLACEMENT_HEAD`, `ADMIN` | `ResumeReview`, `review_resume_rubric()` |
| **Step 16** | **Resume Improvement Cycle** | Candidate iterates based on trainer feedback, submitting revisions with monotonic versioning (`v2`, `v3`, ...). | `STUDENT`, `ADMIN` | `ResumeImprovementCycle`, `submit_improved_resume()` |
| **Step 17** | **Aptitude Assessment** | Timed quantitative, logical, and verbal aptitude evaluations with automated deterministic scoring. | `STUDENT` (take), `TRAINER` / Staff (inspect) | `AssessmentTest` (`APTITUDE`), `StudentAssessmentAttempt` |
| **Step 18** | **Technical Assessment** | Domain-specific technical test (Java, Python, SQL, DSA); question answer keys strictly stripped from student view. | `STUDENT` (take), `TRAINER` / Staff (inspect) | `AssessmentTest` (`TECHNICAL`), `StudentAssessmentAttempt` |
| **Step 19** | **Communication Skills Training** | Workshop attendance and presentation skills evaluation scoring (1-10). | `TRAINER`, `PLACEMENT_OFFICER`, `ADMIN` | `TrainingSession` (`COMMUNICATION`), `TrainingAttendance` |
| **Step 20** | **Corporate Grooming Session** | Verification of professional etiquette, corporate communication, and formal dress code compliance. | `TRAINER`, `PLACEMENT_OFFICER`, `ADMIN` | `TrainingAttendance` (`grooming_certified = True`) |
| **Step 21** | **One-on-One Mock Interview** | Simulated technical and HR interviews scheduled with industry evaluators and trainers. | `PLACEMENT_OFFICER`, `PLACEMENT_HEAD`, `TRAINER`, `ADMIN` | `MockInterview`, `schedule_mock_interview()` |
| **Step 22** | **Mock Interview Feedback** | Evaluator submits 4-pillar rubric scorecard (out of 40), technical & communication feedback, and readiness recommendation. | `EVALUATOR`, `TRAINER`, `ADMIN` | `MockInterviewEvaluation`, `evaluate_mock_interview()` |
| **Step 23** | **Final Placement Resume Approval Gate** | Placement Head formally certifies resume readiness (`is_approved_for_placements = True`). Mandatory gate before Phase 7. | `PLACEMENT_HEAD`, `ADMIN` (Privileged Gate) | `PlacementReadinessCertification`, `certify_placement_readiness()` |

---

## 2. State Transitions & Lifecycle Rules

### 2.1. Resume Review Lifecycle (Steps 15 & 16)
```
[Uploaded Resume v1] ──(Trainer Review)──┬──► [APPROVED] (Proceeds toward Gate)
                                          │
                                          └──► [REVISION_REQUESTED]
                                                    │
                                                    ▼
                                          [ResumeImprovementCycle: REVISION_PENDING]
                                                    │
                                                    ▼ (Student re-uploads PDF)
                                          [Monotonic Resume v2 Uploaded]
                                                    │
                                                    ▼
                                          [Cycle: REVISED_UPLOADED] ──► (Re-reviewed by Trainer)
```

### 2.2. Assessment Attempt Lifecycle (Steps 17 & 18)
```
[AssessmentTest: Active] ──(Student Initiates)──► [Attempt: IN_PROGRESS]
                                                          │
                                                          ▼ (Student Submits Answers)
                                                  (Server Deterministically Scores)
                                                          │
                                                          ▼
                                                  [Attempt: COMPLETED]
                                                  ├─ score / total_marks
                                                  ├─ percentage (0.00% to 100.00%)
                                                  └─ passed: bool (score >= test.passing_marks)
```

### 2.3. Mock Interview Lifecycle (Steps 21 & 22)
```
[Schedule Request] ──(Staff Schedules)──► [MockInterview: SCHEDULED]
                                                   │
                                                   ▼ (Interview Conducted)
                                           [MockInterview: IN_PROGRESS]
                                                   │
                                                   ▼ (Evaluator Submits Rubric)
                                           [MockInterview: COMPLETED]
                                           └─ [MockInterviewEvaluation: Scorecard /40]
                                              ├─ READY_FOR_PLACEMENTS
                                              ├─ NEEDS_PRACTICE
                                              └─ NOT_READY
```

### 2.4. Final Placement Resume Approval Gate (Step 23)
```
[Candidate Readiness Snapshot Compiled (Steps 15-22)]
  ├─ 1. Trainer Resume Review: APPROVED
  ├─ 2. Aptitude Test: PASSED
  ├─ 3. Technical Test: PASSED
  ├─ 4. Communication Workshop: ATTENDED
  ├─ 5. Corporate Grooming: CERTIFIED
  └─ 6. Mock Interview: READY_FOR_PLACEMENTS
             │
             ▼ (Placement Head Authorization Gate)
  ┌────────────────────────────────────────────────────────┐
  │  PLACEMENT HEAD / ADMIN EXCLUSIVE DECISION GATE        │
  │  POST /api/v1/preparation/certifications/certify/      │
  └────────────────────────────────────────────────────────┘
             │
             ├──► [CERTIFIED: is_approved_for_placements = True]  ──► UNLOCKS PHASE 7 DRIVE SUBMISSIONS
             │
             └──► [REJECTED: is_approved_for_placements = False]  ──► BLOCKS DRIVE SUBMISSIONS (Remedial Action)
```

---

## 3. Role-Based Access Control (RBAC) Matrix

| Workflow Endpoint | `STUDENT` | `TRAINER` | `EVALUATOR` | `PLACEMENT_OFFICER` | `PLACEMENT_HEAD` | `ADMIN` |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `GET /api/v1/preparation/resume-reviews/` | Own Only | Full | Full | Full | Full | Full |
| `POST /api/v1/preparation/resume-reviews/` | ❌ 403 | ✅ Permitted | ❌ 403 | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| `POST /api/v1/preparation/improvement-cycles/submit/` | ✅ Own | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ✅ Permitted |
| `GET /api/v1/preparation/tests/<id>/` | Stripped (No Answers) | Full | Full | Full | Full | Full |
| `POST /api/v1/preparation/attempts/start/` | ✅ Permitted | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ✅ Permitted |
| `POST /api/v1/preparation/attempts/submit/` | ✅ Permitted | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ✅ Permitted |
| `POST /api/v1/preparation/sessions/` | ❌ 403 | ✅ Permitted | ❌ 403 | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| `POST /api/v1/preparation/attendances/record/` | ❌ 403 | ✅ Permitted | ❌ 403 | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| `POST /api/v1/preparation/mock-interviews/` | ❌ 403 | ✅ Permitted | ❌ 403 | ✅ Permitted | ✅ Permitted | ✅ Permitted |
| `POST /api/v1/preparation/mock-interviews/evaluate/` | ❌ 403 | ✅ Permitted | ✅ Permitted | ❌ 403 | ✅ Permitted | ✅ Permitted |
| `GET /api/v1/preparation/readiness-snapshot/<id>/` | Own Only | Full | Full | Full | Full | Full |
| `POST /api/v1/preparation/certifications/certify/` | ❌ 403 | ❌ 403 | ❌ 403 | ❌ 403 | ✅ Permitted | ✅ Permitted |

---

## 4. Security, Isolation & Audit Logging

1. **Student Data Isolation:**
   - Candidate endpoints automatically filter querysets to `student=request.user.student_profile`.
   - Any attempt by Student A to inspect Student B's reviews, scorecards, attempts, or readiness snapshots returns `403 Forbidden`.
2. **Assessment Anti-Tampering:**
   - Client views for candidates strictly omit `correct_option_id` and internal explanations.
   - Grading is performed entirely on the backend against immutable test question keys.
   - Resubmission of an already-finalized attempt is prevented with transactional validation.
3. **Audit Trail Compliance:**
   - Every state transition across Steps 15-23 writes an immutable record to `core_audit_log`:
     - `RESUME_REVIEW_SUBMITTED`
     - `RESUME_IMPROVEMENT_SUBMITTED`
     - `ASSESSMENT_ATTEMPT_SUBMITTED`
     - `TRAINING_ATTENDANCE_RECORDED`
     - `MOCK_INTERVIEW_SCHEDULED`
     - `MOCK_INTERVIEW_EVALUATED`
     - `PLACEMENT_READINESS_CERTIFIED` / `PLACEMENT_READINESS_REJECTED`

---

## 5. Unresolved GQT Business Decisions (Open Governance Items)

In strict accordance with project requirements, the following business items are documented as open organizational decisions rather than fabricated defaults:

1. **Assessment Minimum Pass Threshold:**
   - *Current Implementation:* Configurable per assessment (`passing_marks`, default 60%).
   - *Open Decision:* Does GQT mandate an institutional-wide minimum passing percentage (e.g. 60% vs 70%) across all affiliated engineering colleges, or does each department head configure passing marks per drive?
2. **Maximum Assessment Re-attempt Policy:**
   - *Current Implementation:* Students can undertake multiple tracked monotonic attempts (`attempt_number = 1, 2, ...`).
   - *Open Decision:* Does GQT impose a hard limit on re-attempts (e.g., maximum 3 attempts per test), or are remedial attempts unlimited upon trainer recommendation?
3. **Soft Gating vs. Hard Gating on Step 23 Certification:**
   - *Current Implementation:* Placement Head has full administrative discretion to certify readiness (`is_approved = True`) or return candidate (`is_approved = False`), with an informative 6-point criteria checklist displayed.
   - *Open Decision:* Should the system enforce an automated hard block preventing the Placement Head from certifying readiness if any of the 6 criteria are incomplete, or does the Placement Head retain executive waiver authority?
