# GQT HRMS — REST API Specification & Versioning

## 1. API Architecture
* **Base Namespace:** `/api/v1/`
* **Format:** JSON (`application/json`)
* **OpenAPI 3.1 Specification:**
  * Swagger UI: `http://localhost:8000/api/v1/schema/swagger/`
  * Redoc UI: `http://localhost:8000/api/v1/schema/redoc/`
  * Raw Schema: `http://localhost:8000/api/v1/schema/`

---

## 2. Standard Diagnostics Endpoints

### 2.1 Public Liveness Probe
* **Endpoint:** `GET /api/v1/health/`
* **Access:** Public (`AllowAny`), Rate limited (300/min)
* **Response Body (200 OK):**
```json
{
  "status": "UP",
  "service": "gqt-hrms-api",
  "version": "1.0.0",
  "environment": "development",
  "timestamp": "2026-10-26T12:00:00Z",
  "correlation_id": "c56a4180-65aa-42ec-a945-5fd21dec0538"
}
```

### 2.2 Infrastructure Readiness Probe
* **Endpoint:** `GET /api/v1/ready/`
* **Access:** Public (`AllowAny`), Rate limited (300/min)
* **Status Codes:**
  * `200 OK`: Database connected & media storage accessible.
  * `503 Service Unavailable`: Database query failed or storage unavailable.
* **Response Body:**
```json
{
  "status": "READY",
  "database": {
    "status": "UP"
  },
  "storage": {
    "status": "UP"
  },
  "timestamp": "2026-10-26T12:00:00Z",
  "correlation_id": "c56a4180-65aa-42ec-a945-5fd21dec0538"
}
```

---

## 3. Standard JSON Error Envelope
All error responses (400, 401, 403, 404, 500) follow a standardized format:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_FAILED",
    "message": "Human-readable summary of the error condition.",
    "details": {
      "field_name": ["Specific validation error string."]
    },
    "correlation_id": "c56a4180-65aa-42ec-a945-5fd21dec0538"
  }
}
```

---

## 4. Phase 1: Identity, Authentication & RBAC Endpoints

| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/auth/login/` | Public (Throttled) | Authenticate with normalized email & password; sets HttpOnly cookies. |
| `POST` | `/api/v1/auth/logout/` | Authenticated / Public | Blacklists refresh token and clears `gqt_access_token` / `gqt_refresh_token` cookies. |
| `GET` | `/api/v1/auth/me/` | Authenticated | Retrieve authenticated user profile, active roles, and metadata. |
| `POST` | `/api/v1/auth/refresh/` | Public (Throttled) | Rotate refresh token and set fresh access token cookie. |
| `POST` | `/api/v1/auth/password/change/` | Authenticated | Change password verifying current password and enforcing complexity. |
| `POST` | `/api/v1/auth/password/reset/request/` | Public (Throttled) | Request single-use password reset link; generic privacy response. |
| `POST` | `/api/v1/auth/password/reset/confirm/` | Public (Throttled) | Complete password reset using verified uidb64 and token. |
| `GET` | `/api/v1/auth/roles/` | Authenticated | List all active operational roles. |
| `GET` | `/api/v1/auth/users/` | Admin (`ADMIN`) | List paginated user accounts across the enterprise. |
| `POST` | `/api/v1/auth/users/` | Admin (`ADMIN`) | Provision a new user account with initial role assignments. |
| `PATCH` | `/api/v1/auth/users/{id}/status/` | Admin (`ADMIN`) | Activate or deactivate user account with self-deactivation prevention. |
| `POST` | `/api/v1/auth/users/{id}/roles/` | Admin (`ADMIN`) | Atomically assign or revoke operational roles for a user. |

---

## 5. Phase 2: Corporate CRM & HR Directory Endpoints

### 5.1 Corporate Companies
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/crm/companies/` | CRM Staff / Auditor | List and filter companies by domain category, status, tier, city, owner. |
| `POST` | `/api/v1/crm/companies/` | CRM Staff | Create corporate company with automatic name and domain normalization. |
| `GET` | `/api/v1/crm/companies/{id}/` | CRM Staff / Auditor | Retrieve full company profile with nested contacts and counts. |
| `PATCH` | `/api/v1/crm/companies/{id}/` | CRM Staff | Update corporate company profile with audit trail diff logging. |
| `GET` | `/api/v1/crm/companies/check-duplicate/` | CRM Staff / Auditor | Cautiously evaluate duplicate candidates by normalized name or canonical domain. |
| `POST` | `/api/v1/crm/companies/{id}/archive/` | CRM Staff | Safely archive company while preserving historical touchpoint integrity. |
| `POST` | `/api/v1/crm/companies/{id}/restore/` | CRM Staff | Restore an archived company profile. |
| `GET` | `/api/v1/crm/companies/{id}/contacts/` | CRM Staff / Auditor | Paginated list of HR contacts belonging to this company. |
| `GET` | `/api/v1/crm/companies/{id}/outreach/` | CRM Staff / Auditor | Paginated history of outreach touchpoints logged for this company. |
| `GET` | `/api/v1/crm/companies/{id}/follow-ups/` | CRM Staff / Auditor | Paginated list of scheduled follow-ups for this company. |

### 5.2 HR Contacts Directory
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/crm/contacts/` | CRM Staff / Auditor | Search and list corporate HR recruiters with filtering by status and company. |
| `POST` | `/api/v1/crm/contacts/` | CRM Staff | Register new HR recruiter associated with a valid company. |
| `GET` | `/api/v1/crm/contacts/{id}/` | CRM Staff / Auditor | Retrieve HR contact details and audit notes. |
| `PATCH` | `/api/v1/crm/contacts/{id}/` | CRM Staff | Update HR contact communication details. |
| `GET` | `/api/v1/crm/contacts/check-duplicate/` | CRM Staff / Auditor | Check for duplicate email or phone within the company. |
| `POST` | `/api/v1/crm/contacts/{id}/archive/` | CRM Staff | Archive HR contact. |
| `POST` | `/api/v1/crm/contacts/{id}/restore/` | CRM Staff | Restore archived HR contact. |

### 5.3 Multi-Channel Outreach Logging
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/crm/outreach/` | CRM Staff / Auditor | Retrieve append-only history of outreach touchpoints with filtering. |
| `POST` | `/api/v1/crm/outreach/` | CRM Staff | Record completed outreach touchpoint; enforces company/contact relationship. |
| `GET` | `/api/v1/crm/outreach/{id}/` | CRM Staff / Auditor | Retrieve single outreach activity record. |

### 5.4 Follow-Up Queue & Lifecycle
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/crm/follow-ups/` | CRM Staff / Auditor | List scheduled follow-ups with status, priority, and date range filters. |
| `GET` | `/api/v1/crm/follow-ups/overdue/` | CRM Staff / Auditor | List currently overdue follow-ups (`is_overdue=true`). |
| `POST` | `/api/v1/crm/follow-ups/` | CRM Staff | Schedule corporate follow-up task with assigned owner and due date. |
| `GET` | `/api/v1/crm/follow-ups/{id}/` | CRM Staff / Auditor | Retrieve follow-up details. |
| `POST` | `/api/v1/crm/follow-ups/{id}/reschedule/` | CRM Staff | Reschedule open/in-progress task with audit trail and incremented counter. |
| `POST` | `/api/v1/crm/follow-ups/{id}/complete/` | CRM Staff | Complete follow-up task with timestamp, actor, and completion notes. |
| `POST` | `/api/v1/crm/follow-ups/{id}/cancel/` | CRM Staff | Cancel follow-up task with mandatory cancellation reason. |
| `POST` | `/api/v1/crm/follow-ups/{id}/reopen/` | CRM Staff | Formally reopen completed or cancelled task with new due date. |

### 5.5 CRM Operational Metrics & Configurations
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/crm/dashboard/metrics/` | CRM Staff / Auditor | Retrieve KPI metrics, channel counts, and 100/day benchmark progress. |
| `GET` | `/api/v1/crm/config/` | CRM Staff / Auditor | Retrieve system operational configurations (e.g. `DAILY_OUTREACH_TARGET`). |
| `POST` | `/api/v1/crm/config/` | Admin / Head | Update operational target values. |

---

## 6. Phase 3: Job Intake & Verification Checklist Endpoints

### 6.1 Job Requirements Directory & Intake (Workflow Step 5)
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/jobs/requirements/` | Staff / Auditor | List and filter job opportunities by company, status, employment type, search. |
| `POST` | `/api/v1/jobs/requirements/` | Job Staff | Create job requirement draft with 10 structured fields; auto-generates 5 checklist items. |
| `GET` | `/api/v1/jobs/requirements/{id}/` | Staff / Auditor | Retrieve full job requirement, nested 5-point checklist items, and decision history. |
| `PATCH` | `/api/v1/jobs/requirements/{id}/` | Job Staff | Update editable draft (`DRAFT` or `CHANGES_REQUESTED`); blocked when locked/approved. |
| `POST` | `/api/v1/jobs/requirements/{id}/submit-verification/` | Job Staff | Submit draft for formal verification; advances status to `PENDING_VERIFICATION`. |
| `POST` | `/api/v1/jobs/requirements/{id}/archive/` | Job Staff | Archive requirement while preserving historical audit decisions. |
| `POST` | `/api/v1/jobs/requirements/{id}/restore/` | Job Staff | Restore an archived job requirement. |

### 6.2 5-Point Verification Checklist (Workflow Step 6)
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :---: |
| `POST` | `/api/v1/jobs/requirements/{id}/checklist/{item_id}/verify/` | Job Verifier | Audit verification point (`VERIFIED`, `REJECTED`, `NOT_APPLICABLE`) with remarks; auto-advances job to `UNDER_REVIEW` and `VERIFIED` when 100% complete. |
| `POST` | `/api/v1/jobs/requirements/{id}/return-correction/` | Job Verifier / Head | Return incomplete/incorrect job to draft state (`CHANGES_REQUESTED`) with mandatory feedback. |

### 6.3 Placement Head Sign-Off & Queues (Workflow Step 7)
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :---: |
| `POST` | `/api/v1/jobs/requirements/{id}/approve/` | Admin / Head | Final institutional sign-off gate; strictly enforces 100% checklist verification; locks JD for creative production. |
| `POST` | `/api/v1/jobs/requirements/{id}/reject/` | Admin / Head | Formally reject opportunity with mandatory audit justification. |
| `POST` | `/api/v1/jobs/requirements/{id}/reopen/` | Admin / Head | Formally reopen locked/rejected requirement back to `UNDER_REVIEW` for revisions. |
| `GET` | `/api/v1/jobs/requirements/pending-verification/` | Job Verifier / Head | Operational queue of jobs awaiting checklist verification. |
| `GET` | `/api/v1/jobs/requirements/pending-approval/` | Admin / Head | Operational queue of verified jobs awaiting Placement Head sign-off. |
| `GET` | `/api/v1/jobs/requirements/metrics/` | Staff / Auditor | Dashboard aggregations for active, pending, verified, approved jobs, and upcoming deadlines. |

---

## 7. Phase 4: Creative Studio & Promotional Assets Endpoints (Steps 8–9)

### 7.1 Creative Requests & Briefs (Workflow Step 8)
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `GET` | `/api/v1/creatives/requests/` | Staff / Auditor | List and search creative requests with multi-facet filtering. |
| `POST` | `/api/v1/creatives/requests/` | Creative Staff | Create production brief from approved job requirement (`status=APPROVED`). |
| `GET` | `/api/v1/creatives/requests/{id}/` | Staff / Auditor | Retrieve request detail with nested versions, active 4-point checklist, and decisions. |
| `PATCH` | `/api/v1/creatives/requests/{id}/` | Creative Staff | Update brief copy, audience, URLs, contact info, and production deadlines. |
| `POST` | `/api/v1/creatives/requests/{id}/assign/` | Creative Staff | Assign or reassign Graphic Designer; transitions state to `ASSIGNED`. |
| `POST` | `/api/v1/creatives/requests/{id}/archive/` | Admin / Head | Soft-archive creative request. |
| `POST` | `/api/v1/creatives/requests/{id}/restore/` | Admin / Head | Restore soft-archived creative request. |

### 7.2 Promotional Asset Versions & Uploads (Workflow Step 9)
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/creatives/requests/{id}/versions/` | Designer / Staff | Multipart upload (`file`, `designer_notes`). Enforces binary magic bytes (PNG, JPEG, WEBP, PDF), 10MB limit, SVG rejection, monotonic versioning, and auto-initializes 4 checklist items. Advances state to `REVIEW_PENDING`. |
| `GET` | `/api/v1/creatives/requests/{id}/versions/{version_id}/` | Staff / Auditor | Retrieve version detail with SHA-256 fingerprint, dimensions, and checklist status. |
| `GET` | `/api/v1/creatives/requests/{id}/versions/{version_id}/file/` | Staff / Auditor | Authenticated streaming binary file download via `FileResponse`. Raw private filesystem paths are never exposed. |

### 7.3 4-Point Design Verification & Placement Head Sign-Off Gate (Workflow Step 9 Gate)
| Method | Endpoint | Access | Description |
| :--- | :--- | :---: | :--- |
| `POST` | `/api/v1/creatives/requests/{id}/versions/{version_id}/checklist/{code}/verify/` | Creative Verifier | Audit checklist criterion (`FLYER_ACCURACY`, `OFFICIAL_LOGO`, `QR_CODE`, `REGISTRATION_LINK_AND_CONTACTS`) with status (`VERIFIED`, `REJECTED`, `WAIVED`) and remarks. Advances to `IN_REVIEW`. |
| `POST` | `/api/v1/creatives/requests/{id}/versions/{version_id}/return-correction/` | Creative Verifier | Return asset to designer (`CHANGES_REQUESTED`) with mandatory feedback notes. |
| `POST` | `/api/v1/creatives/requests/{id}/versions/{version_id}/approve/` | **Placement Head / Admin strictly** | Final institutional sign-off gate. Unlocks ONLY when all 4 checklist criteria evaluate to `VERIFIED`. Locks version and request as `APPROVED`. |
| `POST` | `/api/v1/creatives/requests/{id}/versions/{version_id}/reject/` | **Placement Head / Admin strictly** | Formally reject asset version with mandatory justification. |
| `GET` | `/api/v1/creatives/requests/pending-review/` | Staff / Auditor | Dual review queue (Checklist Audits vs Placement Head Sign-Offs). |
| `GET` | `/api/v1/creatives/requests/designer-queue/` | Graphic Designer / Admin | Workbench of creative deliverables assigned to current designer. |
| `GET` | `/api/v1/creatives/requests/metrics/` | Staff / Auditor | Studio KPIs: active, in production, review pending, approved, urgent deadlines. |

