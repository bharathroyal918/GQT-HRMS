# GQT HRMS — Phase 3: Job Intake & Verification REST API Specification

> **Base Route:** `/api/v1/jobs/requirements/`  
> **Authentication:** Dual-Transport JWT (SameSite HttpOnly Cookies or `Authorization: Bearer <token>`)  
> **Pagination Envelope:** Standard Results Envelope (`success`, `meta`, `data`)  

---

## 1. Endpoints Overview

| Method | Endpoint | Description | Permissions Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/jobs/requirements/` | List and search job requirements | `IsJobStaffOrAuditor` |
| `POST` | `/api/v1/jobs/requirements/` | Create a new job requirement draft | `IsJobStaffOrAuditor` (Intake Staff) |
| `GET` | `/api/v1/jobs/requirements/{id}/` | Retrieve full job details with checklist and decisions | `IsJobStaffOrAuditor` |
| `PATCH` | `/api/v1/jobs/requirements/{id}/` | Update an editable draft or returned requirement | `IsJobStaffOrAuditor` (Intake Staff) |
| `POST` | `/api/v1/jobs/requirements/{id}/submit-verification/` | Submit requirement for 5-point checklist verification | `IsJobStaffOrAuditor` (Intake Staff) |
| `POST` | `/api/v1/jobs/requirements/{id}/checklist/{item_id}/verify/` | Verify or reject an individual checklist criterion | `CanVerifyJobChecklist` |
| `POST` | `/api/v1/jobs/requirements/{id}/return-correction/` | Return requirement to creator with mandatory feedback | `CanVerifyJobChecklist` |
| `POST` | `/api/v1/jobs/requirements/{id}/approve/` | Sign off and lock opportunity (gated on all 5 items verified) | `CanApproveJobRequirement` |
| `POST` | `/api/v1/jobs/requirements/{id}/reject/` | Formally decline opportunity with documented reason | `CanApproveJobRequirement` |
| `POST` | `/api/v1/jobs/requirements/{id}/reopen/` | Reopen locked or rejected requirement for re-audit | `CanApproveJobRequirement` |
| `POST` | `/api/v1/jobs/requirements/{id}/archive/` | Soft-archive a job requirement | `CanApproveJobRequirement` |
| `POST` | `/api/v1/jobs/requirements/{id}/restore/` | Restore an archived job requirement | `CanApproveJobRequirement` |
| `GET` | `/api/v1/jobs/requirements/pending-verification/` | Operational queue of jobs awaiting checklist audit | `IsJobStaffOrAuditor` |
| `GET` | `/api/v1/jobs/requirements/pending-approval/` | Operational queue of verified jobs awaiting Head sign-off | `IsJobStaffOrAuditor` |
| `GET` | `/api/v1/jobs/requirements/metrics/` | Aggregated metrics across job requirement lifecycle | `IsJobStaffOrAuditor` |

---

## 2. Request and Response Schemas

### 2.1 Create Job Requirement
`POST /api/v1/jobs/requirements/`

**Request Payload:**
```json
{
  "company": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
  "hr_contact": "2c9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bee",
  "title": "Associate Software Engineer — Backend",
  "job_description": "Join our core platform engineering team...",
  "skills_required": "Python, Django, PostgreSQL, Docker",
  "min_salary": "600000.00",
  "max_salary": "850000.00",
  "salary_currency": "INR",
  "salary_breakup": "Fixed: ₹6.0 LPA, Performance Incentive: ₹2.5 LPA",
  "location": "Bangalore",
  "work_arrangement": "HYBRID",
  "employment_type": "FULL_TIME",
  "has_bond": false,
  "bond_details": "",
  "eligibility_criteria": "B.Tech/BE (CS, IT, ECE) with 60%+ or 6.5+ CGPA, 0 backlogs",
  "min_cgpa": "6.50",
  "hiring_process": "Stage 1: Aptitude & Coding, Stage 2: Technical Interview, Stage 3: HR Discussion",
  "interview_date": "2026-11-20",
  "registration_deadline": "2026-11-10T23:59:59+05:30",
  "openings_count": 15,
  "notes": "Fast-track drive for immediate joiners"
}
```

**Response (`201 Created`):**
Returns full `JobRequirementDetail` with 5 initialized `checklist_items` in `PENDING` state:
```json
{
  "id": "3d9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bef",
  "title": "Associate Software Engineer — Backend",
  "company": "1b9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bed",
  "company_name": "Infosys BPM",
  "company_tier": "TIER_1",
  "status": "DRAFT",
  "checklist_progress": {
    "total_mandatory": 5,
    "verified_mandatory": 0,
    "percentage": 0,
    "is_complete": false
  },
  "checklist_items": [
    {
      "id": "item-1",
      "item_code": "ELIGIBILITY",
      "title": "Candidate Academic & Degree Eligibility",
      "status": "PENDING",
      "is_mandatory": true
    },
    {
      "id": "item-2",
      "item_code": "SALARY_AUTHENTICITY",
      "title": "Salary Package & CTC Authenticity",
      "status": "PENDING",
      "is_mandatory": true
    },
    {
      "id": "item-3",
      "item_code": "COMPANY_AUTHENTICITY",
      "title": "Company Authenticity & Hiring Legitimacy",
      "status": "PENDING",
      "is_mandatory": true
    },
    {
      "id": "item-4",
      "item_code": "INTERVIEW_PROCESS",
      "title": "Interview & Selection Process Clarity",
      "status": "PENDING",
      "is_mandatory": true
    },
    {
      "id": "item-5",
      "item_code": "REGISTRATION_DEADLINE",
      "title": "Registration Deadline & Drive Timelines",
      "status": "PENDING",
      "is_mandatory": true
    }
  ],
  "decisions": [],
  "is_locked": false,
  "is_editable": true,
  "created_at": "2026-10-26T14:00:00Z"
}
```

---

### 2.2 Verify Individual Checklist Item
`POST /api/v1/jobs/requirements/{id}/checklist/{item_id}/verify/`

**Request Payload:**
```json
{
  "status": "VERIFIED",
  "remarks": "Verified corporate domain and verified 60% cutoff against university rules."
}
```

**Response (`200 OK`):**
Returns refreshed `JobRequirementDetail`. If all 5 items are verified, status automatically updates to `VERIFIED`.

---

### 2.3 Approve Job Requirement (Placement Head Sign-Off)
`POST /api/v1/jobs/requirements/{id}/approve/`

**Request Payload:**
```json
{
  "comments": "Opportunity verified and approved for campus drive broadcast."
}
```

**Conditions Enforced:**
* Caller must be `PLACEMENT_HEAD` or `ADMIN` (else `403 Forbidden`).
* All 5 mandatory checklist items must be `VERIFIED` (else `400 Bad Request`).

**Success Response (`200 OK`):**
```json
{
  "id": "3d9d6bcd-bbfd-4b2d-9b5d-ab8dfbbd4bef",
  "status": "APPROVED",
  "approved_by_name": "Dr. Ramesh Rao",
  "approved_at": "2026-10-26T14:30:00Z",
  "is_locked": true,
  "is_editable": false
}
```

---

### 2.4 Return for Correction
`POST /api/v1/jobs/requirements/{id}/return-correction/`

**Request Payload:**
```json
{
  "reason": "Variable salary components are not clearly distinguished from fixed pay; please clarify with HR."
}
```

**Response (`200 OK`):**
Status transitions to `CHANGES_REQUESTED`. The creator can now update the draft and re-submit.

---

### 2.5 Operational Metrics
`GET /api/v1/jobs/requirements/metrics/`

**Response (`200 OK`):**
```json
{
  "total_active": 24,
  "draft_count": 5,
  "pending_verification_count": 8,
  "under_review_count": 4,
  "changes_requested_count": 2,
  "verified_count": 3,
  "approved_count": 10,
  "rejected_count": 1,
  "deadlines_approaching_count": 6
}
```
