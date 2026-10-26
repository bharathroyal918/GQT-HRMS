# GQT HRMS — Phase 5: Student Registration & Eligibility Engine Business Rules

> **Domain:** Student Onboarding, Academic Profiles, Resume Ingestion & Eligibility Engine (Workflow Steps 10–14)  
> **Source Document:** `HRMS - Complete Workflow` (Authoritative Business Truth)  
> **Backend Implementation:** `apps.students`  
> **Frontend Implementation:** `src/pages/students/`  

---

## 1. Authoritative Workflow Mapping (Steps 10–14)

### Step 10: Publish Job Notification
* **Authority Gate:** Only requirements certified and locked in `APPROVED` status (`JobRequirement.status == 'APPROVED'`) by the Placement Head or System Administrator can be broadcasted to students.
* **Channels Supported:**
  1. `WHATSAPP`: WhatsApp Community Broadcast.
  2. `TELEGRAM`: Telegram Placement Channel.
  3. `EMAIL`: Direct institutional email broadcast.
  4. `PORTAL`: Student Career Portal Noticeboard (instantly transitions to `DELIVERED`).
* **Approved Creative Asset Linkage:**
  * When promotional assets are attached, the system enforces that the referenced `CreativeAssetVersion` has passed the authoritative 4-point design verification checklist with `is_approved == True` and belongs to the parent job requirement.
* **Safety & Provider State:**
  * External deliveries record unique gateway IDs (`provider_message_id`) and timestamp dispatches.
  * Internal publication records are decoupled from gateway delivery confirmations.
  * Incomplete or failed dispatches record diagnostic error details and support manual retries (`/retry/`) without creating duplicate broadcasts.

---

### Step 11: Student Registration
* **Identity Architecture:** Reuses the centralized `accounts.User` model and authentication infrastructure.
* **Role Boundary:** Every newly onboarded student account is strictly assigned `RoleCatalog.STUDENT`. Self-escalation to privileged roles is blocked.
* **Uniqueness Safeguards:**
  * Institutional Email: Normalized, case-insensitive uniqueness (`Lower("institutional_email")`).
  * University Roll Number: Normalized, case-insensitive uniqueness (`Upper("roll_number")`).
  * Double-registration requests return predictable validation responses (`400 Bad Request`) without disclosing unrelated account existence.

---

### Step 12: Collect Student Profile & Resume
* **Academic Metrics Collected:**
  * Roll Number (unique enrollment identifier)
  * Institutional Email (official university email)
  * College Name, Degree Program, Academic Department / Discipline
  * Graduation Year (passing out batch)
  * CGPA (stored as `Decimal(4,2)` on a 10.0 scale)
  * Standing Arrears / Active Backlogs Count
  * Historical Backlogs Count
  * Contact & Alternate Phone Numbers
* **Resume Document Security & Ingestion:**
  * **Magic Bytes Validation:** Every uploaded resume must begin with the `%PDF-` binary signature (`b"%PDF-"`). Non-PDF files, even if named with `.pdf` extensions, are rejected immediately.
  * **File Size Boundary:** Uploads are strictly capped at `5MB` (`MAX_RESUME_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024`).
  * **Path Isolation:** Stored in isolated user directories (`student_resumes/user_<id>/...`) using cryptographically randomized storage filenames.
  * **Cryptographic Digest:** A complete SHA-256 hash is computed and recorded for every upload.
  * **Monotonic Versioning:** Every new upload increments the version number (`v1`, `v2`, ...) and marks preceding versions as non-current (`is_current = False`).
  * **Authenticated Private Streaming:** Resumes are never exposed via public static URLs. They are streamed strictly through `/api/v1/students/resumes/<id>/download/` using Django `FileResponse`. Object-level permissions enforce that students can only download their own resumes (unauthorized students receive `403 Forbidden`).

---

### Step 13: Eligibility Verification Engine
* **Deterministic Rule Evaluation:** Evaluates four independent criteria based on the approved job requirement's criteria and student profile:
  1. **Discipline / Branch Matching:** Matches candidate branch against eligible disciplines specified in the job criteria.
  2. **CGPA Threshold:** Compares candidate CGPA against `job.min_cgpa` using exact Python `Decimal` arithmetic. Floating-point comparisons are prohibited.
  3. **Arrears Cutoff:** Compares candidate active backlogs against the allowable limit (default: 0 active arrears unless higher allowance explicitly defined).
  4. **Passing Batch:** Compares candidate graduation year against targeted recruitment batch.
* **Auditable Explanations:**
  * Returns criterion-by-criterion breakdown cards documenting `criterion`, `student_value`, `required_value`, `passed`, and descriptive evaluation rationale.
  * Overall outcome evaluated to `ELIGIBLE`, `INELIGIBLE`, or `INCOMPLETE` (when required marks/department are missing).
  * Stores immutable snapshot of criteria at evaluation time.

---

### Step 14: Eligible Candidate Cohort Finalization
* **Cohort Formation:** Compiles verified applicants into `CandidateCohort` linked 1-to-1 to the approved `JobRequirement`.
* **Authorized Manual Overrides:**
  * Placement Officers, Placement Heads, and Administrators can manually override candidate qualification.
  * Overrides require a mandatory business explanation of at least 10 characters.
  * Preserves automated engine result alongside override metadata (`override_reason`, `override_by`, `override_at`).
* **Finalization Gate:**
  * Only Placement Heads or System Administrators can lock a candidate cohort.
  * Executes database row locking (`select_for_update`) to prevent concurrent finalization races.
  * Formally seals the candidate roster (`is_locked = True`, `finalized_by`, `finalized_at`, `finalization_notes`).
  * Post-finalization mutations are strictly blocked to protect downstream Phase 6 candidate submission spreadsheets.

---

## 2. API Endpoints Reference

| Endpoint | Method | Permission | Description |
|---|---|---|---|
| `/api/v1/students/publications/` | GET | Authenticated | List broadcast notices for a job |
| `/api/v1/students/publications/` | POST | Placement Staff | Dispatch multi-channel job announcement |
| `/api/v1/students/publications/<id>/retry/` | POST | Placement Staff | Retry failed notification transmission |
| `/api/v1/students/register/` | POST | AllowAny | Register student user and profile |
| `/api/v1/students/profile/me/` | GET, PATCH | Authenticated Student | Retrieve/update personal profile |
| `/api/v1/students/profiles/` | GET | Placement Staff | Search and filter student talent directory |
| `/api/v1/students/resumes/upload/` | POST | Authenticated Student | Ingest PDF resume with %PDF- check |
| `/api/v1/students/resumes/<id>/download/` | GET | Owner or Staff | Authenticated streaming resume download |
| `/api/v1/students/applications/apply/` | POST | Authenticated Student | Submit job application & run eligibility engine |
| `/api/v1/students/applications/` | GET | Authenticated | List applications for job or my applications |
| `/api/v1/students/eligibility/<id>/` | GET | Owner or Staff | Criterion-by-criterion evaluation details |
| `/api/v1/students/eligibility/<id>/override/` | POST | Placement Staff | Authorize manual eligibility override |
| `/api/v1/students/cohorts/<job_id>/` | GET | Placement Staff | Retrieve cohort roster and members |
| `/api/v1/students/cohorts/<job_id>/finalize/` | POST | Placement Head / Admin | Formally lock candidate cohort |
