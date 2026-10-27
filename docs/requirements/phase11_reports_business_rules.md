# GQT HRMS & Recruitment CRM — Phase 11: Reports & Analytics Business Rules & Traceability Matrix

## 1. Executive Summary & Authoritative Alignment

Phase 11 implements the **Reports & Analytics** layer over the authoritative GQT HRMS & Recruitment CRM platform as specified in `HRMS Work-Flow.pdf` and its companion DOCX.

### Exact Phase 11 Scope
1. **Company Reports**
2. **Student Reports**
3. **Placement Reports**
4. **Performance Reports**
5. **Monthly Statistics**

### Strict Scope Boundary
- **Phase 12 (Automated Follow-up Worker)** is NOT implemented (no daemon task, no email/WhatsApp workers).
- **Phase 13 (Continuous Improvement)** is NOT implemented (no automated curriculum changes, no skill gap action planners).
- **Zero AI / Speculative Ratings**: No machine learning placement predictions, arbitrary employee productivity scores, or automated candidate rankings.
- **Zero Shadow Tables**: All reporting queries operate directly over persisted, authoritative business records (`crm_company`, `jobs_jobrequirement`, `students_profile`, `preparation_placement_readiness`, `submissions_candidate_submission`, `interviews_schedule`, `placements_candidate_placement_status`, `placements_candidate_offer_letter`, and `feedback_*`).

---

## 2. Traceability Matrix

| Report Category | Business Metric | Source Model & Fields | Exact Calculation / Formula | Authorized Roles | Automated Test |
|---|---|---|---|---|---|
| **Company Reports** | Total Partner Companies | `crm.Company` | `COUNT(DISTINCT id)` with optional tier/domain filter | `ADMIN`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `HR_RELATIONSHIP_MGR`, `AUDITOR` | `test_company_reports_aggregation` |
| **Company Reports** | Active Hiring Partners | `crm.Company` | `COUNT(DISTINCT id) WHERE relationship_status='ACTIVE_HIRING_PARTNER'` | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Total Job Drives Posted | `jobs.JobRequirement` | `COUNT(DISTINCT id) WHERE company_id IN (...)` | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Total Profiles Submitted | `submissions.CandidateSubmission` | `COUNT(DISTINCT student_id)` across company submission packages | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Total Candidates Interviewed | `interviews.InterviewSchedule` | `COUNT(DISTINCT student_id) WHERE conducted_status='CONDUCTED'` | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Total Candidates Selected | `placements.CandidatePlacementStatus` | `COUNT(DISTINCT student_id) WHERE status='SELECTED'` | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Total Offers Issued | `placements.CandidateOfferLetter` | `COUNT(DISTINCT id)` | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Total Offers Accepted | `placements.CandidateOfferLetter` | `COUNT(DISTINCT id) WHERE acceptance_status='ACCEPTED'` | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Total Candidates Joined | `placements.CandidateOfferLetter` | `COUNT(DISTINCT id) WHERE joining_status='JOINED'` | Staff, HR Manager, Auditor | `test_company_reports_aggregation` |
| **Company Reports** | Average CTC Offered (INR Lakhs) | `placements.CandidatePlacementStatus` | `AVG(offered_ctc) WHERE status='SELECTED' AND offered_ctc IS NOT NULL` | Staff, HR Manager, Auditor | `test_company_reports_ctc_metrics` |
| **Company Reports** | Recruiter Hiring Satisfaction | `feedback.HRFeedback` | `AVG(hiring_satisfaction_rating)` (Scale 1–5) | Staff, HR Manager, Auditor | `test_company_reports_feedback_summary` |
| **Student Reports** | Total Registered Students | `students.StudentProfile` | `COUNT(DISTINCT id)` | Staff, Auditor | `test_student_reports_metrics` |
| **Student Reports** | Placement-Verified Profiles | `students.StudentProfile` | `COUNT(DISTINCT id) WHERE is_verified_by_placement=True` | Staff, Auditor | `test_student_reports_metrics` |
| **Student Reports** | Placement Readiness Certified (Step 23 Gate) | `preparation.PlacementReadinessCertification` | `COUNT(DISTINCT student_id) WHERE is_approved_for_placements=True` | Staff, Auditor | `test_student_reports_metrics` |
| **Student Reports** | Department Breakdown | `students.StudentProfile` | Group by `department`, count total and placed | Staff, Auditor | `test_student_reports_department_breakdown` |
| **Student Reports** | Individual Student Summary | Personal Student Profile & Applications | Isolated to authenticated student's own records | `STUDENT` (Self Only) | `test_student_isolation_in_reports` |
| **Placement Reports** | Final Result Status Breakdown | `placements.CandidatePlacementStatus` | `COUNT(*)` grouped by `status` (`SELECTED`, `REJECTED`, `WAITING_LIST`, `HOLD`) | Staff, HR Manager, Auditor | `test_placement_reports_status_breakdown` |
| **Placement Reports** | Offer Acceptance Breakdown | `placements.CandidateOfferLetter` | `COUNT(*)` grouped by `acceptance_status` (`ACCEPTED`, `DECLINED`, `PENDING_RESPONSE`, `EXPIRED`) | Staff, HR Manager, Auditor | `test_placement_reports_offer_breakdown` |
| **Placement Reports** | Joining Outcome Breakdown | `placements.CandidateOfferLetter` | `COUNT(*)` grouped by `joining_status` (`JOINED`, `NOT_JOINED`, `DEFERRED`, `PENDING_JOINING`) | Staff, HR Manager, Auditor | `test_placement_reports_joining_breakdown` |
| **Placement Reports** | Compensation Metrics (Min, Max, Avg, Median) | `placements.CandidatePlacementStatus` | `MIN(offered_ctc)`, `MAX(offered_ctc)`, `AVG(offered_ctc)` | Staff, HR Manager, Auditor | `test_placement_reports_ctc_statistics` |
| **Performance Reports** | 7-Stage Objective Conversion Funnel | Cross-Domain Aggregation | Distinct student counts across 7 lifecycle gates | Staff, Auditor | `test_performance_funnel_calculations` |
| **Performance Reports** | Conversion Percentages | Funnel Aggregation | `(Stage[N] / Stage[N-1]) * 100` (safe zero-division) | Staff, Auditor | `test_performance_funnel_calculations` |
| **Monthly Statistics** | Monthly Activity by Event Date | Event-specific timestamps | Partitioned counts based on exact event dates | Staff, Auditor | `test_monthly_statistics_boundaries` |
| **Reports Export** | Sanitized CSV Exports | All 5 Report Datasets | CSV output with formula injection prefix escaping | Staff, Auditor | `test_export_csv_formula_injection_protection` |

---

## 3. Detailed Metric Definitions & Mathematical Formulas

### 3.1 Company Reports Metrics
1. **Total Partner Companies**: Count of active `crm_company` records matching filters.
2. **Active Hiring Partners**: Count of companies with `relationship_status = 'ACTIVE_HIRING_PARTNER'`.
3. **Total Job Drives**: Count of `jobs_jobrequirement` linked to the company.
4. **Distinct Candidates Submitted**:
   $$\text{Submitted Candidates} = \left| \{ s \in \text{StudentProfile} \mid \exists c \in \text{CandidateSubmission}: c.package.company = C \land c.student = s \} \right|$$
   *Double counting prevention:* Distinct student count avoids duplicates if submitted to multiple packages.
5. **Distinct Candidates Interviewed**:
   $$\text{Interviewed Candidates} = \left| \{ s \in \text{StudentProfile} \mid \exists i \in \text{InterviewSchedule}: i.company = C \land i.student = s \land i.conducted\_status = \text{'CONDUCTED'} \} \right|$$
6. **Distinct Candidates Selected**:
   $$\text{Selected Candidates} = \left| \{ s \in \text{StudentProfile} \mid \exists p \in \text{CandidatePlacementStatus}: p.company = C \land p.student = s \land p.status = \text{'SELECTED'} \} \right|$$
7. **Offers Issued**: Count of `CandidateOfferLetter` where `company = C`.
8. **Offers Accepted**: Count of `CandidateOfferLetter` where `company = C \land acceptance_status = 'ACCEPTED'`.
9. **Candidates Joined**: Count of `CandidateOfferLetter` where `company = C \land joining_status = 'JOINED'`.
10. **Average CTC**:
    $$\text{Average CTC} = \frac{\sum_{p \in \text{Selected}} p.offered\_ctc}{\text{Count}(p \in \text{Selected with valid } offered\_ctc)}$$
    Excludes null CTCs; returns `None` if no selected candidates have recorded compensation.

### 3.2 Student Reports Metrics
1. **Profile Completeness Score**: Deterministic evaluation based on required profile attributes:
   - Roll number present (15%)
   - Institutional email verified (15%)
   - Department & degree filled (15%)
   - CGPA recorded (15%)
   - Mobile contact filled (15%)
   - Current active resume uploaded (25%)
2. **Placement Verification Rate**:
   $$\text{Verification Rate} = \frac{\text{Count}(is\_verified\_by\_placement = \text{True})}{\text{Total Registered Students}} \times 100$$
3. **Readiness Certification Rate (Step 23 Gate)**:
   $$\text{Readiness Rate} = \frac{\left| \{ s \mid \exists r \in \text{PlacementReadinessCertification}: r.student = s \land r.is\_approved\_for\_placements = \text{True} \} \right|}{\text{Total Registered Students}} \times 100$$
4. **Student Privacy & Isolation**:
   - `STUDENT` role can ONLY query their personal statistics (`/api/v1/reports/students/my-summary/`).
   - Requests from `STUDENT` to aggregate company or peer reports are HTTP 403 Forbidden.
   - Recruiter feedback on individual students is restricted to staff only.
   - Student interview feedback marked `is_anonymous = True` has candidate attribution redacted.

### 3.3 Placement Reports Metrics
Authoritative Step 36–41 lifecycle distinctions:
- **Selected**: Candidate passed interview rounds and recorded as `SELECTED` in result intake.
- **Offer Issued**: Official PDF offer letter uploaded with SHA-256 hash.
- **Offer Accepted**: Candidate or placement staff confirmed acceptance (`ACCEPTED`).
- **Joined**: Candidate physically or virtually onboarded (`JOINED`), verified by placement staff.
- **Deferred**: Candidate joining deferred to an approved future date (`DEFERRED`).
- **Waiting List / Hold**: Decision pending or standby; NEVER treated as rejection.

### 3.4 Performance Reports & 7-Stage Objective Conversion Funnel
1. **Stage 1 (Applications)**: Total student applications submitted for jobs (`StudentApplication`).
2. **Stage 2 (Eligible)**: Applications passing deterministic criteria (`EligibilityEvaluation.status = 'ELIGIBLE'`).
3. **Stage 3 (Readiness Certified)**: Candidates certified by Placement Head (`PlacementReadinessCertification`).
4. **Stage 4 (Submitted to Corporate HR)**: Profiles dispatched in submission packages (`CandidateSubmission`).
5. **Stage 5 (Shortlisted by HR)**: Candidates included in recruiter shortlist intake (`ShortlistedCandidate`).
6. **Stage 6 (Selected)**: Candidates receiving positive selection outcome (`CandidatePlacementStatus.status = 'SELECTED'`).
7. **Stage 7 (Joined)**: Candidates verified as joined (`CandidateOfferLetter.joining_status = 'JOINED'`).

**Conversion Rates:**
- $\text{Eligibility Rate} = \frac{\text{Stage 2}}{\text{Stage 1}} \times 100$
- $\text{Readiness Rate} = \frac{\text{Stage 3}}{\text{Stage 2}} \times 100$
- $\text{Submission-to-Shortlist Rate} = \frac{\text{Stage 5}}{\text{Stage 4}} \times 100$
- $\text{Shortlist-to-Selection Rate} = \frac{\text{Stage 6}}{\text{Stage 5}} \times 100$
- $\text{Offer-to-Join Rate} = \frac{\text{Stage 7}}{\text{Stage 6}} \times 100$

Zero-division safety: If denominator is 0, conversion rate is reported as `0.00%`.

### 3.5 Monthly Statistics Date Semantics
Events are partitioned strictly by their specific event dates in the configured timezone (`Asia/Kolkata`):
- **Jobs Created**: `JobRequirement.created_at`
- **Interviews Scheduled & Conducted**: `InterviewSchedule.interview_date`
- **Results Received**: `FinalResultIntake.received_at`
- **Offers Accepted**: `CandidateOfferLetter.accepted_at`
- **Candidate Joinings**: `CandidateOfferLetter.actual_joining_date`

Boundary handling:
- Months with 0 activity return clean dictionaries with zeroes for all counters.
- Date ranges strictly adhere to $[Start\ 00:00:00,\ End\ 23:59:59.999999]$.

---

## 4. Security, Authorization & Export Integrity

### Role-Based Access Control (RBAC) Matrix
| Endpoint / Resource | `ADMIN` / `PLACEMENT_HEAD` / `PLACEMENT_OFFICER` | `HR_RELATIONSHIP_MGR` | `AUDITOR` | `TRAINER` / `EVALUATOR` | `STUDENT` |
|---|---|---|---|---|---|
| `GET /api/v1/reports/companies/` | Full Access | Scoped to Assigned Companies | Read-Only | Denied | Denied (403) |
| `GET /api/v1/reports/students/` | Full Access | Denied | Read-Only | Aggregate Only | Denied (403) |
| `GET /api/v1/reports/students/my-summary/` | Full Access | Denied | Read-Only | Denied | Self Only (200) |
| `GET /api/v1/reports/placements/` | Full Access | Scoped to Assigned Companies | Read-Only | Denied | Denied (403) |
| `GET /api/v1/reports/performance/` | Full Access | Denied | Read-Only | Aggregate Only | Denied (403) |
| `GET /api/v1/reports/monthly-stats/` | Full Access | Scoped to Assigned Companies | Read-Only | Denied | Denied (403) |
| `GET /api/v1/reports/*/export/` | Full CSV Export | Scoped CSV Export | Read-Only CSV | Denied | Denied (403) |

### CSV Export Injection Protection
To prevent Formula Injection / CSV Injection attacks in spreadsheet software (Microsoft Excel, LibreOffice Calc, Google Sheets), all string cells starting with dangerous trigger characters (`=`, `+`, `-`, `@`, `\t`, `\r`) are automatically escaped by prepending an apostrophe (`'`).
