# GQT HRMS — Creative Studio & Promotional Assets API Specification
## RESTful Endpoints: `/api/v1/creatives/` (Steps 8–9)

### 1. Base URL & Authentication

* **Base URL**: `/api/v1/creatives/`
* **Authentication**: Cookie session / Bearer Token with CSRF protection on mutations.
* **Deny-by-default**: Student, Trainer, Evaluator roles return `403 Forbidden`. Auditors have strictly read-only (`SAFE_METHODS`) access.

---

### 2. Endpoints Overview

| Method | Endpoint | Action | Authorized Roles |
| :--- | :--- | :--- | :--- |
| `GET` | `/requests/` | List and search creative requests | Admin, Placement Head/Officer, Designer, Auditor |
| `POST` | `/requests/` | Create creative request from approved job | Admin, Placement Head, Placement Officer |
| `GET` | `/requests/{id}/` | Retrieve full request with versions & checklist | Admin, Placement Head/Officer, Designer, Auditor |
| `PATCH` | `/requests/{id}/` | Update creative brief copy/deadlines | Admin, Placement Head, Placement Officer |
| `POST` | `/requests/{id}/assign/` | Assign graphic designer | Admin, Placement Head, Placement Officer |
| `POST` | `/requests/{id}/versions/` | Upload multipart promotional asset file | Designer, Admin, Placement Head/Officer |
| `GET` | `/requests/{id}/versions/{version_id}/` | Get asset version detail | Staff & Auditor |
| `GET` | `/requests/{id}/versions/{version_id}/file/` | Authenticated streaming file download | Staff & Auditor |
| `POST` | `/requests/{id}/versions/{version_id}/checklist/{code}/verify/` | Verify 4-point checklist item | Admin, Placement Head, Placement Officer |
| `POST` | `/requests/{id}/versions/{version_id}/return-correction/` | Return design with revision remarks | Admin, Placement Head, Placement Officer |
| `POST` | `/requests/{id}/versions/{version_id}/approve/` | Placement Head final sign-off | **Placement Head, Admin strictly** |
| `POST` | `/requests/{id}/versions/{version_id}/reject/` | Reject asset version with reason | **Placement Head, Admin strictly** |
| `GET` | `/requests/pending-review/` | Operational queue of assets in review | Staff & Auditor |
| `GET` | `/requests/designer-queue/` | Graphic Designer assigned workbench | Graphic Designer, Admin |
| `GET` | `/requests/metrics/` | Aggregated creative studio KPIs | Staff & Auditor |

---

### 3. Key Endpoint Payloads

#### 3.1 Create Creative Request (`POST /api/v1/creatives/requests/`)
```json
{
  "job_requirement_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "title": "Infosys Cloud Engineer Campus Flyer 2026",
  "deliverable_type": "FLYER",
  "priority": "HIGH",
  "brief": "Design a high-impact campus recruitment flyer targeting 2026 graduates.",
  "target_audience": "BE / B.Tech / MCA with 65%+ throughout",
  "registration_url": "https://gqt.edu/register/infosys-2026",
  "qr_code_target_url": "https://gqt.edu/register/infosys-2026?src=qr",
  "contact_email": "placement@gqt.edu",
  "contact_phone": "+91 9876543210",
  "production_deadline": "2026-11-15T18:00:00Z",
  "assigned_designer_id": "8fa85f64-5717-4562-b3fc-2c963f66afa7"
}
```

#### 3.2 Verify Checklist Item (`POST /api/v1/creatives/requests/{id}/versions/{ver_id}/checklist/{code}/verify/`)
```json
{
  "status": "VERIFIED",
  "remarks": "Official Infosys logo verified against corporate branding guidelines."
}
```

#### 3.3 Placement Head Sign-Off (`POST /api/v1/creatives/requests/{id}/versions/{ver_id}/approve/`)
```json
{
  "comments": "Flyer content, branding, QR code, and registration details verified. Approved for student broadcast."
}
```
*Note: Returns `400 Bad Request` if any of the 4 mandatory checklist items is not in `VERIFIED` status.*
