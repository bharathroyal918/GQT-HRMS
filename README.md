# GQT HRMS & Recruitment CRM Platform

> **Status:** Phase 10 (CRM Database Update — 8-Area Integration & Safe Reconciliation) Complete & Verified<br>
> **Source of Truth:** `docs/requirements/workflow_traceability.md` (13 Business Phases, 41 Operational Steps, 19 CRM Modules, 8 AI Capabilities)  
> **Role & Permission Matrix:** `docs/security/role_permission_matrix.md` (9 Operational Roles, Deny-by-Default, Object-Level Ownership)  
> **Target Database:** Supabase-hosted PostgreSQL 16 Engine with SSL  
> **Frontend:** React 19, TypeScript (Strict), Vite, Tailwind CSS  
> **Backend:** Python 3.14, Django 5.1, Django REST Framework, drf-spectacular  

---

## 1. Technical Architecture Stack

| Layer | Technology | Standards & Conventions |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS | Strict Mode (`strict: true`), TanStack Query v5, React Hook Form, Zod validation, Typed Axios API Client with CSRF & Correlation headers, Zero web storage of auth tokens |
| **Backend** | Python 3.14, Django 5.1.x, Django REST Framework | Strict 5-Layer Pattern (`Views` &rarr; `Serializers` &rarr; `Services` &rarr; `Selectors` &rarr; `Models`), Versioned API under `/api/v1/`, OpenAPI 3.1 via drf-spectacular |
| **Identity & Auth** | Argon2id, SimpleJWT Blacklist, HttpOnly Cookies | Dual-transport JWT (SameSite Lax HttpOnly cookies + Bearer header fallback), Token family rotation & replay detection, Rate-limited login (10 req/min) |
| **CRM Subsystem** | Corporate Directory, HR Contacts, Outreach, Tasks | `apps.crm` module with dynamic overdue evaluation, 100+ outreach/day target tracking, duplicate candidate detection, and audit trail logging |
| **Job Intake Subsystem** | Requirements, 5-Point Verification Checklist, Head Sign-off | `apps.jobs` module with relational checklist entities, gated Placement Head approval, draft immutability post-approval, and operational queues |
| **Creative Studio Subsystem** | Promotional Assets, 4-Point Checklist, Versioning, Sign-off | `apps.creatives` module with monotonic versioning, SVG/magic bytes file security, 4-point design verification checklist, and gated Placement Head sign-off |
| **Students & Eligibility Subsystem** | Broadcast, Registration, Resume Vault, Engine, Cohorts | `apps.students` module with multi-channel broadcast (WhatsApp/Telegram/Email/Portal), PDF `%PDF-` binary magic bytes verification, deterministic eligibility engine (Decimal CGPA), and cohort locking |
| **Student Preparation Subsystem** | Rubric Reviews, Iteration Cycles, Timed Tests, Mocks, Gate | `apps.preparation` module covering Steps 15–23 with institutional rubric scoring, monotonic resume improvement cycles, aptitude/technical tests (answer-key security), grooming certification, mock scorecards, and Placement Head final readiness approval gate |
| **Submissions & Dispatch Subsystem** | Candidate List, Master Excel, Resume Bundles, Dispatch, Ack | `apps.submissions` module covering Steps 24–28 with candidate roster assembly, master Excel spreadsheet generation with SHA-256 fingerprint, certified PDF resume attachments, corporate HR transmission logging, and recruiter receipt acknowledgment |
| **Interview Management Subsystem** | Shortlists, Schedules, Notifications, Reminders, Rounds, Follow-ups | `apps.interviews` module covering Steps 29–35 with corporate HR shortlist intake, multi-channel scheduling (Online/In-person/Hybrid), 5 authoritative notification fields, idempotent automatic reminders (24h, 2h, 30m), attendance confirmation, interview execution outcomes, 5-category round tracking (Aptitude, Coding, Technical, HR, Managerial) with student notes isolation, and corporate HR follow-up metrics |
| **Placement Management Subsystem** | Final Results, Status Transitions, Notifications, Offer Letters, Acceptance, Joining | `apps.placements` module covering Steps 36–41 with corporate final result intake, 4 candidate statuses (Selected, Rejected, Waiting List, Hold), student notifications, secure private PDF offer letter upload with magic-bytes & SHA-256 validation, offer acceptance lifecycle (Pending, Accepted, Declined, Expired), and joining verification (Joined, Not Joined, Deferred) |
| **Feedback Collection Subsystem** | Student Experiences, Corporate HR Evaluations, Trainer Readiness Rubrics | `apps.feedback` module covering Student Interview Experiences (narrative, questions, difficulty, suggestions, anonymity), Corporate HR Evaluations (candidate quality, 1–5 star ratings for tech, comms, satisfaction, remarks), and Trainer Feedback (readiness levels, training effectiveness, and actionable improvement areas) |
| **CRM Integration & Reconciliation Subsystem** | 8-Domain Consistency Scan, Idempotent Reconciliation, 360° Profiles, Unified Timelines | `apps.crm` module covering 8 domain areas (Companies, HR Contacts, Candidates, Resumes, Interviews, Placements, Feedback, and Timelines), non-destructive conflict detection, active hiring partner promotion, and immutable reconciliation audit runs |
| **Database** | Supabase PostgreSQL 16 via `psycopg` (v3) | SSL connection (`sslmode=require`), UUIDv4 primary keys, normalized case-insensitive email uniqueness, transactional operations |
| **Security** | Argon2id, Fail-Closed Config, Log Redaction | Server-side validation, `SensitiveDataFilter` redacting secrets in logs, request correlation IDs (`X-Correlation-ID`) |
| **Testing** | pytest-django, Vitest | 262 backend automated tests (including 16 Phase 10 tests), 78 frontend component/route tests (340 total automated tests), strict TypeScript checks |



---

## 2. Windows Local Development Setup

### 2.1 One-Click Setup
In PowerShell from the repository root:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
```

### 2.2 Manual Setup

#### Step 1: Backend Environment & Virtualenv
```powershell
# Copy environment template
Copy-Item .env.example .env

# Create virtual environment and install pinned dependencies
python -m venv backend\.venv
& "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "backend\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt

# Run database migrations
cd backend
& ".\.venv\Scripts\python.exe" manage.py migrate

# Seed the 9 official operational roles
& ".\.venv\Scripts\python.exe" manage.py seed_roles

# Provision the initial Platform Administrator
& ".\.venv\Scripts\python.exe" manage.py bootstrap_admin
cd ..
```

#### Step 2: Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 3. Administrator Provisioning & Account Recovery

### 3.1 Initial Administrator Bootstrap
The platform features zero default production passwords. To provision the initial Platform Administrator:
```powershell
# Interactive mode (prompts for email and hidden password)
& "backend\.venv\Scripts\python.exe" backend\manage.py bootstrap_admin

# Non-interactive / CI automation mode
& "backend\.venv\Scripts\python.exe" backend\manage.py bootstrap_admin --email admin@gqt.local --password "StrongAdminPass123!" --no-input
```

### 3.2 Account Recovery Procedure
If an administrator loses access:
1. An operator with server-side console access runs `manage.py bootstrap_admin --email <admin_email>` to safely reset the password and re-verify the `ADMIN` role.
2. Every administrative bootstrap and password change generates an immutable `core_audit_log` event with remote IP, timestamp, and correlation ID.

---

## 4. Running Development Servers

* **Start Backend (Port 8000):**
  ```powershell
  powershell -File scripts\run_backend.ps1
  ```
  * Health Probe: `http://localhost:8000/api/v1/health/`
  * Readiness Probe: `http://localhost:8000/api/v1/ready/`
  * Current User: `http://localhost:8000/api/v1/auth/me/`
  * CRM Companies: `http://localhost:8000/api/v1/crm/companies/`
  * CRM HR Contacts: `http://localhost:8000/api/v1/crm/contacts/`
  * CRM Outreach Logs: `http://localhost:8000/api/v1/crm/outreach/`
  * CRM Follow-ups: `http://localhost:8000/api/v1/crm/follow-ups/`
  * CRM Dashboard Metrics: `http://localhost:8000/api/v1/crm/dashboard/metrics/`
  * Job Requirements: `http://localhost:8000/api/v1/jobs/requirements/`
  * Creative Requests: `http://localhost:8000/api/v1/creatives/requests/`
  * OpenAPI Swagger UI: `http://localhost:8000/api/v1/schema/swagger/`
  * OpenAPI Redoc UI: `http://localhost:8000/api/v1/schema/redoc/`

* **Start Frontend (Port 5173):**
  ```powershell
  powershell -File scripts\run_frontend.ps1
  ```
  * Web Dashboard: `http://localhost:5173`
  * Login Screen: `http://localhost:5173/login`
  * Password Recovery: `http://localhost:5173/auth/forgot-password`
  * CRM Dashboard: `http://localhost:5173/crm`
  * Company Directory: `http://localhost:5173/crm/companies`
  * Add Company: `http://localhost:5173/crm/companies/new`
  * HR Contacts Directory: `http://localhost:5173/crm/contacts`
  * Outreach Activity Feed: `http://localhost:5173/crm/outreach`
  * Log Outreach Activity: `http://localhost:5173/crm/outreach/new`
  * Follow-up Workspace: `http://localhost:5173/crm/follow-ups`
  * Job Requirements Directory: `http://localhost:5173/jobs`
  * Job Intake Form (Step 5): `http://localhost:5173/jobs/new`
  * Job Approvals Queue: `http://localhost:5173/jobs/approvals`
  * Creative Studio Directory (Step 8): `http://localhost:5173/creatives`
  * Creative Request Intake: `http://localhost:5173/creatives/new`
  * Creative Review Queues (Step 9): `http://localhost:5173/creatives/queue`
  * Graphic Designer Workbench: `http://localhost:5173/creatives/my-tasks`
  * System Diagnostics (Admin only): `http://localhost:5173/diagnostics`

---

## 5. Master Verification Suite

To run all 6 backend and frontend automated checks:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_dev.ps1
```

Verification includes:
1. `manage.py check` &rarr; Django system checks (0 issues)
2. `manage.py makemigrations --check --dry-run` &rarr; 0 schema drift
3. `pytest` &rarr; **111/111 automated backend tests pass (25 Creatives + 25 Jobs + 26 CRM + 35 Auth/Core)**
4. `tsc -b --noEmit` &rarr; Strict TypeScript compilation clean
5. `vitest run` &rarr; **29/29 frontend component & route tests pass across 7 test suites**
6. `npm run build` &rarr; Vite production build passes in `dist/` (1752 modules bundled) with 0 secret leaks

---

## 6. Directory Structure

```text
gqt-hrms/
├── .env.example                   # Master non-secret environment template
├── .gitignore                     # Git ignore rules for secrets, builds, and media
├── README.md                      # Project setup and documentation guide
├── backend/                       # Django 5.1 REST API backend
│   ├── .venv/                     # Python virtual environment (ignored)
│   ├── apps/
│   │   ├── accounts/              # Identity, custom User, Role, RBAC, and Auth APIs
│   │   │   ├── management/        # seed_roles, bootstrap_admin commands
│   │   │   ├── migrations/        # 0001_initial (User, Role, UserRoleAssignment)
│   │   │   ├── authentication.py  # HttpOnlyCookieJWTAuthentication
│   │   │   ├── models.py          # User (UUIDv4, Lower email), Role, UserRoleAssignment
│   │   │   ├── permissions.py     # IsAdminOrSuperUser, role_required, IsSelfOrAdmin
│   │   │   ├── serializers.py     # Login, User, Role, PasswordChange, Reset serializers
│   │   │   ├── services.py        # Atomic auth mutations & AuditLog integrations
│   │   │   ├── throttles.py       # AuthRateThrottle (10 req/min)
│   │   │   ├── urls.py            # /api/v1/auth/ routing
│   │   │   └── views.py           # LoginView, LogoutView, Me, Refresh, Admin viewset
│   │   ├── core/                  # Core logging, middleware, health, and base models
│   │   ├── crm/                   # Corporate CRM & HR Directory module (Phase 2)
│   │   │   ├── migrations/        # 0001_initial (Company, HRContact, OutreachLog, FollowUp)
│   │   │   ├── models.py          # Relational entities & integrity constraints
│   │   │   ├── permissions.py     # IsCRMStaffOrAuditor, IsCRMManagerOrAdmin
│   │   │   ├── selectors.py       # Query engine, duplicate detection, & metrics aggregations
│   │   │   ├── serializers.py     # DRF serializers with validation & nested schemas
│   │   │   ├── services.py        # Atomic business logic & audit logging
│   │   │   ├── urls.py            # /api/v1/crm/ routes
│   │   │   └── views.py           # ViewSets for companies, contacts, outreach, tasks, dashboard
│   │   ├── jobs/                  # Job Intake & Verification module (Phase 3)
│   │   │   ├── migrations/        # 0001_initial (JobRequirement, JobChecklistItem, JobApprovalDecision)
│   │   │   ├── models.py          # Relational entities, 5-point checklist specs, lifecycle status
│   │   │   ├── permissions.py     # IsJobStaffOrAuditor, CanVerifyJobChecklist, CanApproveJobRequirement
│   │   │   ├── selectors.py       # Query engine, queues, & metrics aggregations
│   │   │   ├── serializers.py     # DRF serializers with validation & nested checklist schemas
│   │   │   ├── services.py        # Atomic lifecycle transitions & approval gating
│   │   │   ├── urls.py            # /api/v1/jobs/ routes
│   │   │   └── views.py           # JobRequirementViewSet with verification & approval actions
│   │   └── creatives/             # Creative Studio & Promotional Assets module (Phase 4 / Steps 8-9)
│   │       ├── migrations/        # 0001_initial (CreativeRequest, AssetVersion, ChecklistItem, Decision)
│   │       ├── models.py          # Relational models, 4-point design checklist, priority, deliverable types
│   │       ├── permissions.py     # IsCreativeStaffOrAuditor, CanAssignDesigner, CanApproveCreative
│   │       ├── selectors.py       # Query engine, designer queues, review queues, metrics
│   │       ├── serializers.py     # DRF serializers with version history & nested audit items
│   │       ├── services.py        # Request lifecycle, upload with magic bytes, checklist verification, Head approval
│   │       ├── urls.py            # /api/v1/creatives/ routes
│   │       ├── validators.py      # Binary magic bytes, pure-Python dimensions, SHA-256, SVG rejection
│   │       └── views.py           # CreativeRequestViewSet with authenticated streaming download action
│   ├── config/                    # Django configuration package
│   │   ├── asgi.py                # ASGI entrypoint
│   │   ├── urls.py                # Root URLs (/api/v1/ and admin)
│   │   ├── wsgi.py                # WSGI entrypoint
│   │   └── settings/              # Base, local, test, and production settings
│   ├── tests/                     # Automated pytest test suites (111 tests)
│   ├── manage.py                  # Django CLI management utility
│   ├── pytest.ini                 # Pytest runner configuration
│   └── requirements.txt           # Pinned backend dependencies
├── frontend/                      # React 19 TypeScript Vite frontend
│   ├── public/                    # Static brand assets (official GQT logos)
│   ├── src/
│   │   ├── api/                   # Typed API client (authApi.ts, crmApi.ts, jobsApi.ts, creativesApi.ts)
│   │   ├── components/
│   │   │   ├── auth/              # ProtectedRoute route guard
│   │   │   ├── brand/             # Official GQT Logo & Emblem components
│   │   │   ├── common/            # Accessible UI primitives (Button, Card, Input, Modal, Badge)
│   │   │   └── layout/            # AppShell, Navbar, Footer
│   │   ├── context/               # AuthContext & AuthProvider (zero web storage of tokens)
│   │   ├── lib/                   # apiClient.ts (Axios), queryClient.ts, utils.ts
│   │   ├── pages/
│   │   │   ├── auth/              # LoginPage, ForgotPasswordPage, ResetPasswordPage, AccessDeniedPage
│   │   │   ├── crm/               # Corporate CRM workspace (Phase 2)
│   │   │   │   ├── CrmDashboardPage.tsx  # KPI cards, daily target progress, overdue queue
│   │   │   │   ├── CompaniesPage.tsx     # Company directory with search & filters
│   │   │   │   ├── CompanyFormPage.tsx   # Company create/edit with duplicate detection
│   │   │   │   ├── CompanyDetailPage.tsx # Company detail view with tabbed contacts/outreach
│   │   │   │   ├── ContactsPage.tsx      # HR Contact directory
│   │   │   │   ├── ContactFormPage.tsx   # HR Contact create/edit
│   │   │   │   ├── OutreachPage.tsx      # Outreach activity journal & filter view
│   │   │   │   ├── OutreachFormPage.tsx  # Log new outreach touchpoint
│   │   │   │   └── FollowUpsPage.tsx     # Follow-up workspace with reschedule/complete modals
│   │   │   ├── jobs/              # Job Intake & Verification workspace (Phase 3)
│   │   │   │   ├── JobDirectoryPage.tsx      # Opportunities directory with filters & progress bars
│   │   │   │   ├── JobFormPage.tsx           # Step 5 intake form with company/contact linkage
│   │   │   │   ├── JobDetailPage.tsx         # 3-tab workspace: 5-point checklist, overview, decisions
│   │   │   │   └── JobApprovalsQueuePage.tsx # Dual queues: checklist audits & Head approvals
│   │   │   ├── creatives/         # Creative Studio & Promotional Assets workspace (Phase 4 / Steps 8-9)
│   │   │   │   ├── CreativeDirectoryPage.tsx   # Deliverables directory with format badges & KPIs
│   │   │   │   ├── CreativeRequestFormPage.tsx # Step 8 intake from approved jobs with copy brief
│   │   │   │   ├── CreativeDetailPage.tsx      # Workspace: 4-point checklist, file download, Head approval
│   │   │   │   ├── CreativeReviewQueuePage.tsx # Dual queues: checklist audits & Placement Head approvals
│   │   │   │   └── DesignerWorkQueuePage.tsx   # Graphic designer assigned task workbench
│   │   │   ├── DashboardPage.tsx  # Interactive CRM roadmap & system dashboard
│   │   │   ├── DiagnosticsPage.tsx# Real-time infrastructure health inspector
│   │   │   └── NotFoundPage.tsx   # 404 handler
│   │   ├── test/                  # Vitest component & suite tests (29 tests across 7 test files)
│   │   ├── types/                 # TypeScript interfaces (auth.ts, api.ts, crm.ts, jobs.ts, creatives.ts)
│   │   ├── App.tsx                # React Router & QueryClient routing
│   │   ├── index.css              # Tailwind CSS directives & scrollbar styles
│   │   └── main.tsx               # Application root entry
│   ├── package.json               # Frontend dependencies and build scripts
│   ├── tailwind.config.js         # GQT brand design tokens & color palette
│   ├── tsconfig.json              # TypeScript root configuration
│   ├── tsconfig.app.json          # Strict TypeScript compiler options
│   └── vite.config.ts             # Vite + React + Vitest bundler configuration
├── docs/                          # Architecture & specifications
│   ├── architecture/              # 5-Layer backend & system design
│   ├── requirements/              # 41-Step workflow traceability matrix
│   ├── api/                       # API design and OpenAPI documentation
│   ├── security/                  # Security specifications & role_permission_matrix.md
│   ├── crm/                       # Phase 2 Corporate CRM documentation
│   │   ├── corporate_crm_data_model.md     # CRM entity relationship design
│   │   ├── corporate_crm_business_rules.md # Duplicate detection, follow-up rules, targets
│   │   └── corporate_crm_api.md            # CRM endpoint specifications
│   ├── jobs/                      # Phase 3 Job Intake documentation
│   │   ├── job_intake_data_model.md        # Job requirement, checklist, and decision schema
│   │   ├── job_intake_business_rules.md    # 5-point checklist, lifecycle states, transitions
│   │   └── job_intake_api.md               # Job intake REST API documentation
│   ├── creatives/                 # Phase 4 Creative Studio documentation
│   │   ├── creative_assets_data_model.md     # Relational assets, versions, 4-point checklist schema
│   │   ├── creative_assets_business_rules.md # 4-point checklist, magic bytes security, gate rules
│   │   └── creative_assets_api.md            # Creative Studio REST API documentation
│   ├── deployment/                # Supabase PostgreSQL setup instructions
│   └── testing/                   # QA and automated testing strategy
└── scripts/                       # Automation scripts for Windows
    ├── setup_dev.ps1              # Full local bootstrap script
    ├── run_backend.ps1            # Start Django backend
    ├── run_frontend.ps1           # Start Vite frontend
    └── verify_dev.ps1             # Master 6-point verification suite
```

---
 
## 7. Next Phase: Interview Management & Drive Day Tracking (Steps 29–35)

Phase 7 (Candidate Submission & Profile Dispatch — Steps 24–28) is complete and verified with 100% green automated tests across all 6 quality gates (180 backend tests, 46 frontend tests, 226 total tests). The system is strictly paused awaiting explicit authorization before beginning:
* **Phase 8: Interview Management & Drive Day Tracking (Steps 29–35)**
  * Step 29: Receive Shortlisted Candidates (ingest recruiter shortlist and match against submission roster).
  * Step 30: Notify Students (dispatch interview drive invitations with venue, reporting time, and documents).
  * Step 31: Automatic Reminders (scheduled idempotent reminders at 24h, 2h, and 30m before drive).
  * Step 32: Attendance Confirmation (capture candidate RSVP status prior to drive day).
  * Step 33: Drive Day Attendance & Conduct (record physical/virtual check-in and attendance).
  * Step 34: Track Interview Rounds (sequential multi-round evaluation: Aptitude, Coding, Technical, HR, Managerial).
  * Step 35: HR Follow-up During Drives (maintain recruiter communication on pending rounds and result dates).

