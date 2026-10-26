# GQT HRMS & Recruitment CRM Platform

> **Status:** Phase 3 (Job Intake & 5-Point Verification Checklist) Complete & Verified  
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
| **Database** | Supabase PostgreSQL 16 via `psycopg` (v3) | SSL connection (`sslmode=require`), UUIDv4 primary keys, normalized case-insensitive email uniqueness, transactional operations |
| **Security** | Argon2id, Fail-Closed Config, Log Redaction | Server-side validation, `SensitiveDataFilter` redacting secrets in logs, request correlation IDs (`X-Correlation-ID`) |
| **Testing** | pytest-django, Vitest | 86 backend unit/integration tests, 23 frontend component/route tests (109 total automated tests), strict TypeScript checks |



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
3. `pytest` &rarr; **61/61 automated backend tests pass (26 CRM + 35 Auth/Core)**
4. `tsc -b --noEmit` &rarr; Strict TypeScript compilation clean
5. `vitest run` &rarr; **19/19 frontend component & route tests pass (5 CRM + 14 Auth/Core)**
6. `npm run build` &rarr; Vite production build passes in `dist/` with 0 secret leaks

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
│   │   └── jobs/                  # Job Intake & Verification module (Phase 3)
│   │       ├── migrations/        # 0001_initial (JobRequirement, JobChecklistItem, JobApprovalDecision)
│   │       ├── models.py          # Relational entities, 5-point checklist specs, lifecycle status
│   │       ├── permissions.py     # IsJobStaffOrAuditor, CanVerifyJobChecklist, CanApproveJobRequirement
│   │       ├── selectors.py       # Query engine, queues, & metrics aggregations
│   │       ├── serializers.py     # DRF serializers with validation & nested checklist schemas
│   │       ├── services.py        # Atomic lifecycle transitions & approval gating
│   │       ├── urls.py            # /api/v1/jobs/ routes
│   │       └── views.py           # JobRequirementViewSet with verification & approval actions
│   ├── config/                    # Django configuration package
│   │   ├── asgi.py                # ASGI entrypoint
│   │   ├── urls.py                # Root URLs (/api/v1/ and admin)
│   │   ├── wsgi.py                # WSGI entrypoint
│   │   └── settings/              # Base, local, test, and production settings
│   ├── tests/                     # Automated pytest test suites (86 tests)
│   ├── manage.py                  # Django CLI management utility
│   ├── pytest.ini                 # Pytest runner configuration
│   └── requirements.txt           # Pinned backend dependencies
├── frontend/                      # React 19 TypeScript Vite frontend
│   ├── public/                    # Static brand assets (official GQT logos)
│   ├── src/
│   │   ├── api/                   # Typed API client (authApi.ts, crmApi.ts, jobsApi.ts)
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
│   │   │   ├── DashboardPage.tsx  # Interactive CRM roadmap & system dashboard
│   │   │   ├── DiagnosticsPage.tsx# Real-time infrastructure health inspector
│   │   │   └── NotFoundPage.tsx   # 404 handler
│   │   ├── test/                  # Vitest component & auth tests (23 tests)
│   │   ├── types/                 # TypeScript interfaces (auth.ts, api.ts, crm.ts, jobs.ts)
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
│   ├── deployment/                # Supabase PostgreSQL setup instructions
│   └── testing/                   # QA and automated testing strategy
└── scripts/                       # Automation scripts for Windows
    ├── setup_dev.ps1              # Full local bootstrap script
    ├── run_backend.ps1            # Start Django backend
    ├── run_frontend.ps1           # Start Vite frontend
    └── verify_dev.ps1             # Master 6-point verification suite
```

---

## 7. Next Phase: Creative Studio & Promotional Assets

Phase 3 (Job Intake & 5-Point Verification Checklist) is complete. The system is paused awaiting review before beginning:
* **Phase 4: Creative Studio & Promotional Assets (`apps.creatives` — Steps 8–9)**
  * Graphic Designer creative request dispatch from approved JDs.
  * Marketing flyers, banners, social media posts, and QR codes.
  * 4-Point design verification checklist.
  * Placement Head creative sign-off gate before student notification.



