# GQT HRMS — Supabase PostgreSQL 16 Configuration & Deployment Guide

## 1. Overview
GQT HRMS uses **Supabase-hosted PostgreSQL 16** as its primary production relational database engine. Django's ORM and migration engine serve as the single source of truth for the database schema.

---

## 2. Supabase Project Setup Instructions

1. **Create Supabase Organization & Project:**
   * Log into [supabase.com](https://supabase.com).
   * Create a new project (e.g. `gqt-hrms-production`).
   * Select the appropriate regional cluster (e.g. `ap-south-1` Mumbai for India latency optimization).
   * Set a strong, high-entropy database password (store securely in institutional password vault).

2. **Retrieve Connection Strings:**
   * Navigate to **Project Settings &rarr; Database &rarr; Connection Pooling**.
   * Note the two primary connection methods:

| Connection Method | Port | Purpose in GQT HRMS | Recommended Setting |
| :--- | :---: | :--- | :--- |
| **Direct Session Connection** | `5432` | Schema migrations (`migrate`), background workers, and Celery/cron daemons | `DATABASE_URL=postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:5432/postgres?sslmode=require` |
| **Supavisor Transaction Pooler** | `6543` | Stateless web requests under high concurrent load (Gunicorn WSGI workers) | `DATABASE_URL=postgresql://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require` |

> [!IMPORTANT]
> **Transaction Pooler Note:** When connecting through Supavisor port `6543` (Transaction mode), Django must be configured with `DISABLE_SERVER_SIDE_CURSORS = True` in database options to avoid prepared statement naming collisions across pooled connections. For initial migrations and admin commands, port `5432` is mandatory.

---

## 3. Environment Variable Configuration

In your server's `.env` file (never commit to Git):

```env
# Production Supabase PostgreSQL Connection
DATABASE_URL=postgresql://postgres.your-project-ref:YourStrongPassword999!@aws-0-ap-south-1.pooler.supabase.com:5432/postgres?sslmode=require
DB_SSLMODE=require
USE_SQLITE_FOR_LOCAL_DEV=False
```

---

## 4. Executing Safe, Non-Destructive Migrations

To apply schema migrations to Supabase without data destruction:

```bash
# Verify pending migrations without modifying database
python manage.py showmigrations

# Dry-run check for schema drift
python manage.py makemigrations --check --dry-run

# Apply migrations atomically
python manage.py migrate
```

---

## 5. Row-Level Security (RLS) & Access Boundaries
* Django connects to Supabase PostgreSQL using server-side credentials with schema ownership.
* For future public or student portal clients connecting directly via Supabase client libraries (if desired in later phases), RLS policies can be activated per table while preserving Django superuser bypass.
* All application queries enforce server-side object-level and role-based permissions in the Django service layer.
