# GQT HRMS & Recruitment CRM — Authoritative Workflow Traceability Matrix

> **Authoritative Source of Truth:** `HRMS - Complete Workflow` (Preserving 13 Business Phases, 41 Operational Steps, 19 CRM Modules, 8 AI Capabilities)  
> **System Scope:** Single-Organization Internal Enterprise HRMS & Corporate Recruitment CRM SaaS  
> **Backend Architecture:** Python 3.14 + Django 5.1 + DRF (Strict 5-Layer Architecture)  
> **Frontend Architecture:** React 19 + TypeScript Strict + Vite + Tailwind CSS  
> **Database:** Supabase-hosted PostgreSQL 16 Engine with SSL  

---

## 1. 13-Phase Workflow Overview

| Phase # | Authoritative Workflow Phase | Operational Steps Covered | Target Domain App |
| :--- | :--- | :--- | :--- |
| **Phase 1** | **Company Acquisition** | Steps 1, 2, 3, 4 | `apps.crm` |
| **Phase 2** | **Job Requirement Management** | Steps 5, 6, 7, 8, 9 | `apps.jobs`, `apps.creatives` |
| **Phase 3** | **Student Registration** | Steps 10, 11, 12, 13, 14 | `apps.registrations`, `apps.students` |
| **Phase 4** | **Student Preparation** | Steps 15, 16, 17, 18, 19, 20, 21, 22, 23 | `apps.preparation` |
| **Phase 5** | **Company Submission** | Steps 24, 25, 26, 27, 28 | `apps.submissions` |
| **Phase 6** | **Interview Management** | Steps 29, 30, 31, 32, 33 | `apps.interviews` |
| **Phase 7** | **Interview Tracking** | Steps 34, 35 | `apps.interviews` |
| **Phase 8** | **Placement Management** | Steps 36, 37, 38, 39, 40, 41 | `apps.placements` |
| **Phase 9** | **Feedback Collection** | Student, HR, and Trainer 360° Rubrics | `apps.feedback` |
| **Phase 10** | **CRM Database Update** | Candidate History & Corporate Timelines | `apps.crm.sync` |
| **Phase 11** | **Reports & Analytics** | 13-Stage Conversion Funnel & CTC Stats | `apps.analytics` |
| **Phase 12** | **Automated Follow-Up** | Overdue Escalations & Candidate Reconnection | `apps.crm.scheduler` |
| **Phase 13** | **Continuous Improvement** | Recruiter Curriculum Gaps & Cutoff Optimization | `apps.analytics.improvement` |

---

## 2. 41-Step End-to-End Operational Traceability Matrix

### Phase 1: Company Acquisition (Steps 1–4) — [STATUS: IMPLEMENTED & TESTED IN PHASE 2]
* **Step 1: Identify Target Companies**  
  * *Business Requirement:* Market research on fresher hiring companies categorized by domain (IT, Core, BPO, Finance, etc.).  
  * *Implemented Entity:* `apps.crm.models.Company` (name, normalized_name, domain_category, website, domain, tier, relationship_status, city, state, country, owner).  
  * *Validation:* Normalized lowercase alphanumeric duplicate detection and canonical root domain collision checking (`check_company_duplicates`).
  * *Status:* ✅ Implemented, 26 backend tests + 5 frontend tests verified.
* **Step 2: Contact HRs**  
  * *Business Requirement:* Multi-channel outreach (Calls, Emails, LinkedIn, WhatsApp, In-Person) targeting 100+ HRs/day.  
  * *Implemented Entity:* `apps.crm.models.OutreachLog` (company, hr_contact, performed_by, channel, direction, activity_date, outcome, subject, notes, followup_required).  
  * *Validation:* Append-only history; contact-company relationship verification; daily quota aggregation against configurable target.
  * *Status:* ✅ Implemented & verified.
* **Step 3: Record HR Information**  
  * *Business Requirement:* Maintain directory of HR talent leads with email, phone, LinkedIn, and callback dates.  
  * *Implemented Entity:* `apps.crm.models.HRContact` (company, name, designation, department, email, phone, alt_phone, linkedin_url, preferred_channel, status, owner).  
  * *Validation:* Contact duplicate checking within company; safe archival with historical preservation.
  * *Status:* ✅ Implemented & verified.
* **Step 4: HR Response & Follow-up**  
  * *Business Requirement:* If interested, trigger JD intake; if not interested, schedule relationship nurturing follow-up.  
  * *Implemented Entity:* `apps.crm.models.FollowUp` (company, hr_contact, assigned_to, due_date, priority, status, purpose, completion_notes, completed_at, completed_by, cancellation_reason, rescheduled_count).  
  * *Validation:* Dynamic `is_overdue` evaluation; strict state transition lifecycle (OPEN/IN_PROGRESS -> COMPLETED/CANCELLED); authorized reopening workflow.
  * *Status:* ✅ Implemented & verified.

### Phase 2: Job Requirement Management (Steps 5–9) — [STEPS 5–7 IMPLEMENTED & TESTED IN PHASE 3]
* **Step 5: Collect Job Description**  
  * *Business Requirement:* Intake formal corporate hiring requirements across 10 structured fields (role, description, skills, CTC range, location, work arrangement, bond, eligibility criteria, hiring process stages, and deadlines).  
  * *Implemented Entity:* `apps.jobs.models.JobRequirement` (company, hr_contact, title, job_description, skills_required, min_salary, max_salary, salary_currency, salary_breakup, location, work_arrangement, employment_type, has_bond, bond_details, eligibility_criteria, min_cgpa, hiring_process, interview_date, registration_deadline, openings_count, status).  
  * *Validation:* Server-side salary range check (`min_salary <= max_salary`), contact-to-company relationship integrity check (`hr_contact.company_id == company.id`), deadline validation.  
  * *Status:* ✅ Implemented & verified.
* **Step 6: Verify Job Details**  
  * *Business Requirement:* Institutional review against the 5 authoritative Step 6 verification criteria (`ELIGIBILITY`, `SALARY_AUTHENTICITY`, `COMPANY_AUTHENTICITY`, `INTERVIEW_PROCESS`, `REGISTRATION_DEADLINE`).  
  * *Implemented Entity:* `apps.jobs.models.JobChecklistItem` (job_requirement, item_code, title, description, is_mandatory, status, verified_by, verified_at, remarks).  
  * *Validation:* Extensible checklist model; composite uniqueness per requirement; automated state advancement to `UNDER_REVIEW` and `VERIFIED`.  
  * *Status:* ✅ Implemented & verified.
* **Step 7: Internal Approval Gate**  
  * *Business Requirement:* Placement Head or Admin formally signs off on opportunity; strictly locks JD against unauthorized modifications.  
  * *Implemented Entity:* `apps.jobs.models.JobApprovalDecision` (job_requirement, decision, actor, actor_role, comments, created_at).  
  * *Gating Rule:* All 5 mandatory checklist criteria must evaluate to `VERIFIED` before approval can proceed. Premature approval attempts are rejected with `400 Bad Request`. Non-authorized roles receive `403 Forbidden`. Reopening requires explicit business justification and clears previous approval timestamps.  
  * *Status:* ✅ Implemented & verified.
* **Step 8: Send to Design Team**  
  * *Business Requirement:* Trigger creative asset requests (Flyer, Banner, Social Post, Combined Pack) from approved job requirements and assign graphic designer.  
  * *Required Entity:* `apps.creatives.models.CreativeRequest`.
  * *Status:* ✅ Implemented & verified (Phase 4).
* **Step 9: Review & Approve Design**  
  * *Business Requirement:* Designer submits asset revision; reviewer validates authoritative 4-point design verification checklist (Flyer accuracy, Official logo, QR code, Registration link/contacts). Final sign-off restricted to Placement Head.  
  * *Required Entity:* `apps.creatives.models.CreativeAssetVersion`, `apps.creatives.models.CreativeChecklistItem`, `apps.creatives.models.CreativeDecision`.  
  * *Security Rule:* Uploaded files validated with binary magic bytes; SVG rejected (XSS defense); monotonic version numbering; authenticated streaming delivery.
  * *Status:* ✅ Implemented & verified (Phase 4).

### Phase 5: Student Registration & Eligibility Engine (Steps 10–14) [IMPLEMENTED & VERIFIED]
* **Step 10: Publish Job Notification**  
  * *Business Requirement:* Broadcast approved opportunity to student channels (WhatsApp, Telegram, Email, Portal noticeboard).  
  * *Gate Rule:* Strictly gated on Step 7 sign-off (`JobRequirement.status == 'APPROVED'`). Fails closed on draft, returned, or unapproved jobs.
  * *Creative Linkage:* Connects approved Step 9 promotional assets (`CreativeAssetVersion.is_approved == True`).
  * *Implementation:* `apps.students.models.JobPublication(job_requirement, creative_version, channel, status, target_audience, dispatched_at, delivered_at, provider_message_id)`.
* **Step 11: Student Registration**  
  * *Business Requirement:* Onboard student candidates via CRM portal with strict uniqueness on normalized institutional email (case-insensitive lowercase) and roll number (case-insensitive uppercase).  
  * *Role Isolation:* Automatically assigns `RoleCatalog.STUDENT`; zero capability for self-escalation.
  * *Implementation:* `apps.students.models.StudentProfile(user, roll_number, institutional_email, college_name, degree, department, graduation_year, cgpa, active_backlogs)`.
* **Step 12: Collect Student Profile & Resume**  
  * *Business Requirement:* Ingest student academic metrics and resume PDF documents in private isolated storage.  
  * *Security Enforcement:* Validates binary signature `%PDF-` (`b"%PDF-"`), rejects spoofed extensions, enforces 5MB limit (`MAX_RESUME_UPLOAD_SIZE_BYTES`), computes cryptographic SHA-256 fingerprint, and provisions monotonic version numbers (`v1`, `v2`, ...).  
  * *Private Streaming:* Resumes served exclusively via authenticated `FileResponse` behind `IsStudentOwnerOrStaff` object-level permissions (student-to-student data isolation enforced; 403 Forbidden).
  * *Implementation:* `apps.students.models.StudentResume(student, version_number, file, file_name, file_size_bytes, sha256_hash, is_current)`.
* **Step 13: Eligibility Verification Engine**  
  * *Business Requirement:* Deterministic, auditable rule evaluation evaluating 4 core criteria (Branch/Discipline matching, Decimal CGPA threshold comparison, standing arrears cutoff, and graduation passing batch).  
  * *Explainability:* Produces structured criterion-level breakdown cards with exact required vs. actual values.  
  * *Implementation:* `apps.students.models.StudentApplication(student, job_requirement, resume, status)` and `apps.students.models.EligibilityEvaluation(application, status, criteria_snapshot, evaluation_details)`.
* **Step 14: Eligible Candidate Cohort Finalization**  
  * *Business Requirement:* Formally assemble verified candidate roster. Allows Placement Officers and Placement Heads to authorize manual eligibility overrides with mandatory justification (>= 10 characters) and verifier attribution.  
  * *Finalization Gate:* Strictly gated to Placement Head or System Administrator. Finalization executes row locking (`select_for_update`), sets `is_locked = True`, and protects downstream candidate rosters against post-finalization mutations.  
  * *Implementation:* `apps.students.models.CandidateCohort(job_requirement, title, is_locked, finalized_by, finalized_at)` and `apps.students.models.CohortMember(cohort, student, application, is_eligible, is_override, override_reason, override_by)`.

### Phase 6: Student Preparation (Steps 15–23) [IMPLEMENTED & VERIFIED]
* **Step 15: Resume Review**  
  * *Business Requirement:* Placement trainers evaluate student resumes against institutional standards/rubric (formatting, technical skills, project descriptions, achievements) before corporate drive submissions.  
  * *Implementation:* `apps.preparation.models.ResumeReview(resume, student, reviewer, status, formatting_score, technical_skills_score, projects_score, achievements_score, detailed_feedback, suggested_improvements)`.  
  * *Validation:* Rubric scores strictly bounded between 1 and 10; mandatory constructive feedback; status transitions to `APPROVED` or `REVISION_REQUESTED`.
* **Step 16: Resume Improvement Cycle**  
  * *Business Requirement:* Student iterates and improves resume addressing trainer rubric feedback, re-uploading an updated version (`v2`, `v3`, ...) with monotonic versioning.  
  * *Implementation:* `apps.preparation.models.ResumeImprovementCycle(initial_review, student, prior_resume, improved_resume, status, student_notes, submitted_at)`.  
  * *Validation:* Preserves previous resume versions in immutable private storage; transitions cycle from `REVISION_PENDING` to `REVISED_UPLOADED`.
* **Step 17: Aptitude Assessment**  
  * *Business Requirement:* Timed quantitative, logical, and verbal aptitude tests evaluating freshers with instant deterministic server-side scoring.  
  * *Implementation:* `apps.preparation.models.AssessmentTest` (type `APTITUDE`) and `apps.preparation.models.StudentAssessmentAttempt(student, test, attempt_number, score, percentage, passed, status, answers)`.  
  * *Validation:* Enforces duration limits, computes marks deterministically, tracks monotonic attempt counts, and evaluates `passed = score >= test.passing_marks`.
* **Step 18: Technical Assessment**  
  * *Business Requirement:* Domain-specific technical assessments (Java, Python, SQL, Web fundamentals) with strict anti-tampering answer key stripping.  
  * *Security Enforcement:* Question serialization for candidates strictly strips `correct_option_id` and internal explanations; grading performed exclusively server-side.  
  * *Implementation:* `apps.preparation.models.AssessmentTest` (type `TECHNICAL`) and `apps.preparation.models.StudentAssessmentAttempt`.
* **Step 19: Communication Skills Training**  
  * *Business Requirement:* Track student participation, attendance, and presentation evaluation scores in institutional communication workshops.  
  * *Implementation:* `apps.preparation.models.TrainingSession` (type `COMMUNICATION`) and `apps.preparation.models.TrainingAttendance(session, student, attendance_status, presentation_score)`.
* **Step 20: Corporate Grooming Session**  
  * *Business Requirement:* Professional etiquette, corporate communication, and formal dress code verification, certifying interview decorum.  
  * *Implementation:* `apps.preparation.models.TrainingAttendance(session, student, professional_etiquette_verified, corporate_communication_verified, dress_code_verified, hr_interview_ready, grooming_certified, trainer_remarks)`.  
  * *Validation:* Requires explicit trainer verification across etiquette, communication, and formal attire.
* **Step 21: One-on-One Mock Interview**  
  * *Business Requirement:* Simulated one-on-one technical and HR interviews scheduled with industry evaluators and trainers.  
  * *Implementation:* `apps.preparation.models.MockInterview(student, evaluator, scheduled_by, interview_type, scheduled_at, meeting_link, status, notes)`.
* **Step 22: Mock Interview Rubric Evaluation**  
  * *Business Requirement:* Detailed scorecard evaluation recording scores for technical competence, problem solving, communication clarity, and professional readiness (out of 40), plus actionable feedback and readiness recommendation (`READY_FOR_PLACEMENTS`, `NEEDS_PRACTICE`, `NOT_READY`).  
  * *Implementation:* `apps.preparation.models.MockInterviewEvaluation(mock_interview, evaluator, technical_competence_score, problem_solving_score, communication_clarity_score, professional_readiness_score, total_score, technical_feedback, communication_feedback, improvement_suggestions, readiness_recommendation)`.
* **Step 23: Final Placement Resume Approval Gate**  
  * *Business Requirement:* Placement Head formal readiness certification gate. Verifies candidate preparation across all milestones (Steps 15-22) and approves a specific resume version with `is_approved_for_placements = True`.  
  * *Gate Rule:* Mandatory Gate before Phase 7 (Steps 24-28: Company Submission & Profile Dispatch). Only `PLACEMENT_HEAD` or `ADMIN` can authorize clearance.  
  * *Implementation:* `apps.preparation.models.PlacementReadinessCertification(student, approved_resume, is_approved_for_placements, status, certified_by, certified_at, readiness_summary, notes)`.

### Phase 5: Company Submission (Steps 24–28)
* **Step 24: Prepare Candidate List:** Filter eligible cohort; strictly exclude candidates without placement-approved resumes.
* **Step 25: Generate Candidate Roster Spreadsheet:** Compile standardized master spreadsheet with verified candidate academic/contact data and cryptographic SHA-256 digest.
* **Step 26: Attach Resumes:** Bundle exact approved resume PDF versions corresponding to candidate roster entries.
* **Step 27: Send Candidate Profiles to HR:** Dispatch package to corporate HR; record timestamp, dispatch provider ref, and update state to `SUBMITTED_TO_COMPANY`.
* **Step 28: Company Acknowledgement:** Log HR confirmation of receipt, preliminary feedback, and next follow-up callback date.

### Phases 6 & 7: Interview Management & Tracking (Steps 29–35)
* **Step 29: Receive Shortlisted Candidates:** Ingest recruiter candidate shortlist; match against submission roster; advance to `SHORTLISTED`.
* **Step 30: Notify Students:** Send drive invitations with venue / video link, reporting time, and mandatory documents.
* **Step 31: Automatic Reminders:** Schedule and dispatch idempotent reminders at 24h, 2h, and 30m before drive via automated background worker.
* **Step 32: Attendance Confirmation:** Capture candidate confirmation (`CONFIRMED`, `TENTATIVE`, `DECLINED`) prior to drive day.
* **Step 33: Drive Day Attendance & Conduct:** Record physical/virtual attendance (`PRESENT`, `NO_SHOW`) and conduct (`CONDUCTED`, `MISSED`).
* **Step 34: Track Interview Rounds:** Sequential round evaluation (Aptitude, Coding, Technical, HR, Managerial) with no skipping.
* **Step 35: HR Follow-up During Drives:** Maintain communication with HR during evaluation; track pending rounds and expected result dates.

### Phase 8: Placement Management (Steps 36–41)
* **Step 36: Receive Final Results:** Ingest hiring outcomes from HR (`SELECTED`, `REJECTED`, `WAITING_LIST`, `ON_HOLD`).
* **Step 37: Update Candidate Status:** Atomically update student application status and student profile placement state.
* **Step 38: Notify Students:** Notify placed and unselected candidates with official congratulatory / rejection advisories.
* **Step 39: Upload Offer Letter:** Upload official offer letter with magic-bytes validation (`%PDF-`, SHA-256, 5MB limit).
* **Step 40: Track Offer Acceptance & Single-Job Policy:** Enforce Single-Job Placement Policy: accepting offer auto-withdraws competing applications using `select_for_update()` row locking.
* **Step 41: Track Joining Status:** Verify physical/virtual joining date, employee ID, and location; capture reason if non-joining.

### Phases 9–13: Continuous Feedback, Sync & Analytics
* **Phase 9: Feedback Collection:** Collect 360-degree feedback across students (difficulty, questions asked), HR recruiters, and trainers.
* **Phase 10: CRM Database Update:** Automatically sync candidate placement state into CRM profiles, compute company lifetime hiring metrics, maintain chronological interaction timelines, and archive completed drives.
* **Phase 11: Reports & Analytics:** Generate 13-stage placement conversion funnels, department average/median CTC statistics, corporate partner trends, and export authorized CSV reports.
* **Phase 12: Automated Follow-Up Worker:** Run automated background jobs to escalate overdue follow-ups, trigger annual hiring cycle outreach, reconnect unselected candidates, and engage placed students before joining.
* **Phase 13: Continuous Improvement:** Analyze recruiter feedback to identify syllabus gaps, detect recurring interview elimination rounds, refine cutoff criteria based on placement success, and compile executive annual reports.

---

## 3. Recommended CRM Modules (19 Modules)
1. Dashboard
2. Company Management
3. HR Management
4. Follow-up Management
5. Job Description Management
6. Design Team Module
7. Student Management
8. Registration Module
9. Resume Builder & Versions
10. Eligibility Engine
11. Training Module
12. Mock Interview Module
13. Company Submissions
14. Interview Management
15. Placement Management
16. Feedback Module
17. Notification Center
18. Reports & Analytics
19. User & Role Management

## 4. Recommended AI Features (8 Capabilities)
1. **AI HR Assistant:** Automated email generation and follow-up conversation summaries.
2. **Resume Analyzer:** ATS scoring, keyword gap extraction, and formatting analysis.
3. **Student Job Matching:** Vector similarity search between student skills and verified JDs.
4. **AI Mock Interviewer:** Speech-to-text / LLM simulated technical and behavioral Q&A.
5. **JD Parser:** Extraction of skills, CTC, bond, and eligibility criteria from raw text or PDFs.
6. **Follow-up Prediction:** Classification predicting HR response likelihood and optimal outreach timing.
7. **Placement Analytics:** Predictive modeling of batch placement conversion rates and department risks.
8. **Automated Reports:** LLM compilation of executive placement summaries for academic leadership.
