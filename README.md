# GQT HRMS & Recruitment CRM Platform

> **Status:** Foundation Stage Verified  
> **Source of Truth:** `docs/requirements/workflow_traceability.md` (13 Business Phases, 41 Operational Steps, 19 CRM Modules, 8 AI Capabilities)  
> **Target Database:** Supabase-hosted PostgreSQL 16 Engine with SSL  
> **Frontend:** React 19, TypeScript (Strict), Vite, Tailwind CSS  
> **Backend:** Python 3.14, Django 5.1, Django REST Framework, drf-spectacular  

---

## 1. Technical Architecture Stack

| Layer | Technology | Standards & Conventions |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite, Tailwind CSS | Strict Mode (`strict: true`), TanStack Query v5, React Hook Form, Zod validation, Typed Axios API Client with CSRF & Correlation headers |
| **Backend** | Python 3.14, Django 5.1.x, Django REST Framework | Strict 5-Layer Pattern (`Views` &rarr; `Serializers` &rarr; `Services` &rarr; `Selectors` &rarr; `Models`), Versioned API under `/api/v1/`, OpenAPI 3.1 via drf-spectacular |
| **Database** | Supabase PostgreSQL 16 via `psycopg` (v3) | SSL connection (`sslmode=require`), UUIDv4 primary keys, DecimalField monetary precision, protected cascades, transactional operations |
| **Security** | Argon2id, Fail-Closed Config, Log Redaction | Server-side validation, `SensitiveDataFilter` redacting secrets in logs, request correlation IDs (`X-Correlation-ID`) |
| **Testing** | pytest-django, Vitest | Isolated in-memory backend testing, React Testing Library, strict compilation |

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
cd ..
```

#### Step 2: Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 3. Running Development Servers

* **Start Backend (Port 8000):**
  ```powershell
  powershell -File scripts\run_backend.ps1
  ```
  * Health Probe: `http://localhost:8000/api/v1/health/`
  * Readiness Probe: `http://localhost:8000/api/v1/ready/`
  * OpenAPI Swagger UI: `http://localhost:8000/api/v1/schema/swagger/`
  * OpenAPI Redoc UI: `http://localhost:8000/api/v1/schema/redoc/`

* **Start Frontend (Port 5173):**
  ```powershell
  powershell -File scripts\run_frontend.ps1
  ```
  * Web Dashboard: `http://localhost:5173`
  * System Diagnostics: `http://localhost:5173/diagnostics`

---

## 4. Master Verification Suite

To run all 6 backend and frontend automated checks:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_dev.ps1
```

Verification includes:
1. `manage.py check` &rarr; Django system checks (0 issues)
2. `manage.py makemigrations --check --dry-run` &rarr; 0 schema drift
3. `pytest` &rarr; 11/11 automated backend tests pass
4. `tsc -b --noEmit` &rarr; Strict TypeScript compilation clean
5. `vitest run` &rarr; 9/9 frontend component tests pass
6. `npm run build` &rarr; Vite production build passes in `dist/`

---

## 5. Directory Structure

```text
gqt-hrms/
├── .env.example                   # Master non-secret environment template
├── .gitignore                     # Git ignore rules for secrets, builds, and media
├── README.md                      # Project setup and documentation guide
├── backend/                       # Django 5.1 REST API backend
│   ├── .venv/                     # Python virtual environment (ignored)
│   ├── apps/
│   │   └── core/                  # Core logging, middleware, health, and base models
│   ├── config/                    # Django configuration package
│   │   ├── asgi.py                # ASGI entrypoint
│   │   ├── urls.py                # Root URLs (/api/v1/ and admin)
│   │   ├── wsgi.py                # WSGI entrypoint
│   │   └── settings/              # Base, local, test, and production settings
│   ├── tests/                     # Automated pytest test suites
│   ├── manage.py                  # Django CLI management utility
│   ├── pytest.ini                 # Pytest runner configuration
│   └── requirements.txt           # Pinned backend dependencies
├── frontend/                      # React 19 TypeScript Vite frontend
│   ├── public/                    # Static brand assets (official GQT logos)
│   ├── src/
│   │   ├── api/                   # Typed API service client
│   │   ├── components/
│   │   │   ├── brand/             # Official GQT Logo & Emblem components
│   │   │   ├── common/            # Accessible UI primitives (Button, Card, StatusBadge, Input)
│   │   │   └── layout/            # AppShell, Navbar, Footer
│   │   ├── lib/                   # apiClient.ts (Axios), queryClient.ts, utils.ts
│   │   ├── pages/                 # DashboardPage, DiagnosticsPage, NotFoundPage
│   │   ├── test/                  # Vitest test setup and component unit tests
│   │   ├── types/                 # TypeScript interfaces (API envelopes, health)
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
│   ├── security/                  # Security specifications & fail-closed runtime
│   ├── deployment/                # Supabase PostgreSQL setup instructions
│   └── testing/                   # QA and automated testing strategy
└── scripts/                       # Automation scripts for Windows
    ├── setup_dev.ps1              # Full local bootstrap script
    ├── run_backend.ps1            # Start Django backend
    ├── run_frontend.ps1           # Start Vite frontend
    └── verify_dev.ps1             # Master 6-point verification suite
```

---

## 6. Next Phase Implementation Plan

With the production-grade foundation verified, the system is ready for sequential domain implementation:
* **Phase 1:** Identity, User Models & Role-Based Authentication (`apps.accounts`).
* **Phase 2:** Corporate CRM & HR Directory Management (`apps.crm` — Steps 1–4).
* **Phase 3:** Job Intake & 12-Point Verification Checklist (`apps.jobs` — Steps 5–7).
* **Phase 4:** Recruitment Creative Studio (`apps.creatives` — Steps 8–9).
* **Phase 5:** Student Profiles, Resumes & Eligibility Engine (`apps.students`, `apps.registrations` — Steps 10–14).
* **Phase 6:** Student Preparation, Assessments & Mock Interviews (`apps.preparation` — Steps 15–23).
* **Phase 7:** Candidate Submission, Excel Rosters & Interview Drives (`apps.submissions`, `apps.interviews` — Steps 24–35).
* **Phase 8:** Placement Outcomes, Single-Job Policy & Joining (`apps.placements` — Steps 36–41).
* **Phase 9:** 360° Feedback, Analytics, and Continuous Improvement (`apps.feedback`, `apps.analytics` — Phases 9–13).
