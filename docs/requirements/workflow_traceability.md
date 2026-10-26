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

### Phase 1: Company Acquisition (Steps 1–4)
* **Step 1: Identify Target Companies**  
  * *Business Requirement:* Market research on fresher hiring companies categorized by domain (IT, Core, BPO, Finance, etc.).  
  * *Required Entity:* `Company(name, domain_category, website, city, lifecycle_status)`.  
  * *Validation:* Normalized lowercase duplicate detection on corporate legal name and website URL.
* **Step 2: Contact HRs**  
  * *Business Requirement:* Multi-channel outreach (Calls, Emails, LinkedIn, WhatsApp) targeting 100+ HRs/day.  
  * *Required Entity:* `OutreachLog(company, hr_contact, channel, state, outcome, notes)`.  
  * *Validation:* Channel enum enforcement; daily quota aggregator.
* **Step 3: Record HR Information**  
  * *Business Requirement:* Maintain directory of HR talent leads with email, phone, LinkedIn, and callback dates.  
  * *Required Entity:* `HRContact(company, name, designation, email, phone, next_followup_date)`.  
  * *Validation:* Unique email per corporate entity; international phone format.
* **Step 4: HR Response & Follow-up**  
  * *Business Requirement:* If interested, trigger JD intake; if not interested, schedule relationship nurturing follow-up.  
  * *Required Entity:* `FollowUp(company, hr_contact, due_at, priority, status, outcome)`.

### Phase 2: Job Requirement Management (Steps 5–9)
* **Step 5: Collect Job Description**  
  * *Business Requirement:* Intake formal hiring requirements (role, CTC range, bond, eligibility, deadlines).  
  * *Required Entity:* `JobRequirement`, `JobDescription(version_number, required_skills, eligibility_criteria)`.
* **Step 6: Verify Job Details**  
  * *Business Requirement:* Review against 12-point institutional verification checklist (salary authenticity, bond, test formats).  
  * *Required Entity:* `JDVerificationChecklist`, `JDChecklistItem(item_code, status, reviewer_notes)`.  
  * *Rule:* All 12 items must be `PASSED` before approval is unlocked.
* **Step 7: Internal Approval**  
  * *Business Requirement:* Placement Head formally signs off on opportunity; locks JD against unauthorized modifications.  
  * *Required Entity:* `JobApprovalLog(job_requirement, actor, action, comments)`.
* **Step 8: Send to Design Team**  
  * *Business Requirement:* Trigger creative asset requests (Flyer, Banner, Social Post) and assign graphic designer.  
  * *Required Entity:* `CreativeRequest(job_requirement, creative_type, assigned_designer)`.
* **Step 9: Review & Approve Design**  
  * *Business Requirement:* Designer submits draft; reviewer validates 4-point design checklist (flyer, logo, QR code, registration link).  
  * *Required Entity:* `CreativeDraftVersion`, `CreativeReviewChecklist`.  
  * *Security Rule:* Uploaded files validated with binary magic bytes; SVG rejected (XSS defense).

### Phase 3: Student Registration (Steps 10–14)
* **Step 10: Publish Job Notification**  
  * *Business Requirement:* Broadcast approved opportunity to student channels (WhatsApp, Telegram, Email, Portal).  
  * *Required Entity:* `JobPublication(job_requirement, channel, published_at)`.
* **Step 11: Student Registration**  
  * *Business Requirement:* Onboard students via CRM portal/Google form with roll number & email uniqueness.  
  * *Required Entity:* `StudentProfile(user, roll_number, college, department, graduation_year, cgpa)`.
* **Step 12: Collect Student Profile & Resume**  
  * *Business Requirement:* Ingest student academic metrics and resume PDF.  
  * *Required Entity:* `StudentResume(student, version_number, file, sha256_hash)`.  
  * *Security Rule:* Binary magic bytes check (`%PDF-`), SHA-256 fingerprinting, 5MB limit.
* **Step 13: Eligibility Verification Engine**  
  * *Business Requirement:* Multi-factor rule evaluation (branch, CGPA, backlogs, graduation year).  
  * *Required Entity:* `EligibilityRule`, `StudentApplication(student, job_requirement, status)`.
* **Step 14: Eligible Students Cohort**  
  * *Business Requirement:* Finalize eligible candidate cohort; allow Placement Officer manual override with mandatory audit reason.  
  * *Required Entity:* `EligibilityEvaluation(application, is_eligible, override_reason, override_by)`.

### Phase 4: Student Preparation (Steps 15–23)
* **Step 15: Resume Review:** Placement trainers evaluate formatting, technical skills, and project summaries against rubric.
* **Step 16: Resume Improvement Cycle:** Student iterates on resume feedback, uploads new version with monotonic versioning.
* **Step 17: Aptitude Assessment:** Timed quantitative, logical, and verbal aptitude tests with instant automated scoring.
* **Step 18: Technical Assessment:** Domain-specific technical test; client receives questions with answer keys strictly stripped.
* **Step 19: Communication Training:** Workshop tracking for group discussions, corporate presentation, and communication skills.
* **Step 20: Corporate Grooming Session:** Verification of professional etiquette, interview dress code, and corporate conduct.
* **Step 21: One-on-One Mock Interview:** Schedule individual simulated technical and HR interviews with evaluators.
* **Step 22: Mock Interview Rubric Evaluation:** Record scores for technical knowledge, problem solving, communication, and readiness.
* **Step 23: Final Placement Resume Approval Gate:** Placement Head formally certifies resume readiness (`is_approved_for_placements = True`). Mandatory gate before candidate submission.

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
