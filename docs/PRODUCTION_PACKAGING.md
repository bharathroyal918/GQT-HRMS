# GQT HRMS — Production Packaging & Deployment Guide
## Phase 15 Workstream 5 & 5.1: Docker, Nginx & CI Foundation

**Platform:** GQT HRMS & Recruitment CRM
**Target Architecture:** Multi-container production deployment with Docker Compose, Nginx Reverse Proxy, Django REST WSGI (Gunicorn), and Supabase PostgreSQL 16.

---

## 1. Prerequisites

Before building or running the production container topology, ensure your host environment meets the following requirements:

- **Docker Engine:** Version 24.0.0 or higher.
- **Docker Compose:** Version 2.20.0 or higher (Docker Compose v2 CLI).
- **System Resources:**
  - Minimum 2 vCPUs.
  - Minimum 4 GB RAM.
  - Minimum 20 GB free disk space for container images, static assets, and media volume mounts.
- **Network Ports:** Port 80 (and 443 if terminating TLS directly at Nginx) available on the host machine.
- **Target Database:** PostgreSQL 16 instance (Supabase PostgreSQL 16 recommended) accessible from the Docker container network.

---

## 2. Environment Variables & Secret Configuration

The application enforces **fail-closed security invariants**. Missing, short, or placeholder secrets will prevent the Django backend from booting.

### 2.1 Initialization
Copy the template to create a local `.env` file:
```bash
cp .env.example .env
```

### 2.2 Critical Environment Variables Matrix

| Variable Name | Classification | Required In Prod? | Description & Constraints |
| :--- | :---: | :---: | :--- |
| `ENVIRONMENT` | Configuration | Yes | Must be set to `production`. |
| `DEBUG` | Security | Yes | Must be set to `False`. |
| `DJANGO_SETTINGS_MODULE` | Configuration | Yes | Set to `config.settings.production`. |
| `DJANGO_SECRET_KEY` | **CRITICAL SECRET** | Yes | Minimum 50 characters, high-entropy random string. Rejects weak or "insecure" strings. |
| `DJANGO_ALLOWED_HOSTS` | Security | Yes | Comma-separated list of FQDNs (e.g. `hrms.gqtech.in,backend`). Localhost-only rejected. |
| `DATABASE_URL` | **CRITICAL SECRET** | Yes | PostgreSQL 16 connection string with `?sslmode=require`. |
| `DB_PASSWORD` | **CRITICAL SECRET** | Yes | Non-default, complex database password. |
| `CORS_ALLOWED_ORIGINS` | Security | Yes | Origins permitted for cross-origin API calls (e.g. `https://hrms.gqtech.in`). |
| `CSRF_TRUSTED_ORIGINS` | Security | Yes | Trusted origins for CSRF header injection. |
| `SESSION_COOKIE_SECURE` | Security | Yes | Enforced `True` in production (cookies require HTTPS). |
| `CSRF_COOKIE_SECURE` | Security | Yes | Enforced `True` in production (CSRF token requires HTTPS). |
| `JWT_COOKIE_SECURE` | Security | Yes | Enforced `True` in production (JWT token requires HTTPS). |
| `JWT_SIGNING_KEY` | **CRITICAL SECRET** | Yes | Dedicated high-entropy secret key for HS256 JWT tokens. |
| `VITE_API_BASE_URL` | Build-time Arg | Yes | Set to `/api/v1` for single-origin reverse proxying via Nginx. |
| `PORT` | Networking | No | Host port mapped to Nginx (default: `80`). |

> [!CAUTION]
> Never commit `.env` or paste real secrets into Git, Dockerfiles, or CI workflow definitions. The repository `.gitignore` and `.dockerignore` files prevent local `.env` files from being tracked or bundled into images.

---

## 3. Container Topology & Architecture

The production foundation uses a decoupled, dual-tier container architecture orchestrated by Docker Compose:

```
                  +----------------------------------------------+
                  |                 Client Browser               |
                  +----------------------------------------------+
                                         |
                                         | HTTP / HTTPS (Port 80/443)
                                         v
+------------------------------------------------------------------------------------+
| Docker Network: gqt_internal                                                       |
|                                                                                    |
|  +------------------------------------------------------------------------------+  |
|  | Frontend Edge Service: gqt-hrms-frontend (Nginx 1.27 Alpine)                 |  |
|  | - Serves React 19 SPA static assets (/usr/share/nginx/html)                 |  |
|  | - Long-term caching for fingerprinted assets (/assets/*: 1y immutable)       |  |
|  | - Direct high-speed static delivery (/static/* -> static_data volume :ro)    |  |
|  | - Zero-cache for index.html (immediate deploy propagation)                   |  |
|  | - SPA fallback (try_files $uri $uri/ /index.html)                            |  |
|  | - Security headers (X-Frame-Options, X-Content-Type-Options, nosniff)       |  |
|  | - Blocks direct /media/* access (all documents require authenticated API)    |  |
|  | - Blocks hidden files (.env, .git, .sqlite3) & source maps (*.map)           |  |
|  +------------------------------------------------------------------------------+  |
|                          |                                                         |
|                          | /api/* & /admin/* Proxying (Internal: 8000)             |
|                          v                                                         |
|  +------------------------------------------------------------------------------+  |
|  | Backend WSGI Service: gqt-hrms-backend (Python 3.12 Slim + Gunicorn)         |  |
|  | - Runs unprivileged as non-root appuser (UID 10001)                          |  |
|  | - Gunicorn 3 workers, 2 threads, 60s timeout                                 |  |
|  | - Pre-collects static assets during container build stage                    |  |
|  | - Manages authenticated streaming file downloads (FileResponse)              |  |
|  | - Zero-secret liveness (/api/v1/health/) & readiness (/api/v1/ready/)        |  |
|  +------------------------------------------------------------------------------+  |
|                          |                               |                         |
|    Media Volume (/app/media)            Static Volume (/app/staticfiles)           |
|                          v                               v                         |
|               [gqt_hrms_media_data]            [gqt_hrms_static_data]              |
|                                                (Mounted read-only to Nginx)        |
+------------------------------------------------------------------------------------+
                                         |
                                         | TLS encrypted connection (Port 5432/6543)
                                         v
                  +----------------------------------------------+
                  |         Supabase PostgreSQL 16 DB            |
                  +----------------------------------------------+
```

---

## 4. Static-File Delivery Architecture

Django with `DEBUG=False` does not serve static files via WSGI. Nginx is configured to serve all static assets directly:

1. **Build-Time Pre-Collection:** `backend/Dockerfile` executes `python manage.py collectstatic --noinput --settings=config.settings.test` during the image build, ensuring all Django admin and DRF static assets are embedded in `/app/staticfiles`.
2. **Volume Sharing:** In `docker-compose.yml`, the named volume `static_data` is mounted to:
   - `backend`: `/app/staticfiles` (read-write)
   - `frontend` (Nginx): `/usr/share/nginx/static:ro` (read-only)
3. **Nginx Direct Delivery:** Nginx serves `/static/` via `alias /usr/share/nginx/static/;` with a 30-day cache header and `try_files $uri =404;`.
4. **Maintenance & Updates:** Running `docker compose exec backend python manage.py collectstatic --noinput` updates the volume in-place, and Nginx immediately serves the updated assets without downtime.

---

## 5. Uploaded-Media Security Architecture

User uploads in GQT HRMS consist of sensitive documents:
- Student resumes (`student_resumes/user_<id>/...`)
- Candidate submission rosters (`submissions/rosters/...`)
- Placement offer letters and verification proofs
- Promotional creative assets

### Security Invariants:
1. **No Public Static Alias:** Nginx explicitly denies all direct requests to `/media/` using `location ^~ /media/ { deny all; return 404; }`.
2. **Authenticated Streaming Endpoints:** All file downloads are routed through Django DRF endpoints:
   - Student Resumes: `GET /api/v1/students/resumes/<id>/download/`
   - Creative Assets: `GET /api/v1/creatives/assets/<id>/versions/<v_id>/download/`
   - Submissions: `GET /api/v1/submissions/<id>/download-roster/`
3. **Object-Level Authorization:** Each endpoint verifies user authentication (`IsAuthenticated`), role membership (`AUDIT_ROLES`, `CREATIVE_ROLES`, `PLACEMENT_ROLES`), and candidate ownership before streaming the binary payload via `FileResponse`.
4. **Volume Isolation:** The `media_data` volume is mounted exclusively into the `backend` container. The `frontend` (Nginx) container has no access to candidate resumes, enforcing least-privilege boundary separation.

---

## 6. Nginx Configuration Hierarchy

Two configuration files exist in the repository to support both standalone and bundled container workflows:
- `frontend/nginx.conf`: Copied by `frontend/Dockerfile` into `/etc/nginx/conf.d/default.conf` inside the frontend image. **This is the actual file loaded by the running container.**
- `nginx/conf.d/default.conf`: Mirror file loaded by standalone Nginx reverse proxies using `nginx/nginx.conf`.

Both configurations are kept in strict synchronization, ensuring consistent routing, caching, and security headers.

---

## 7. Local Build & Startup Procedures

### 7.1 Validate Compose Configuration
Before launching, validate the Docker Compose specification:
```bash
docker compose config
```

### 7.2 Build Container Images
Build both backend and frontend images using clean Docker cache:
```bash
docker compose build --no-cache
```

### 7.3 Start Application Services
Start the container stack in detached mode:
```bash
docker compose up -d
```

### 7.4 Verify Service Status & Health
Inspect the container health states:
```bash
docker compose ps
```
Both services should transition from `starting` to `healthy`.

---

## 8. Health Verification & Log Inspection

### 8.1 Endpoint Health Checks
Verify the Nginx edge and backend proxy via curl or browser:
```bash
# 1. Frontend SPA Root
curl -I http://localhost/

# 2. Backend API Liveness Probe (via Nginx reverse proxy)
curl -s http://localhost/api/v1/health/ | jq .

# 3. Backend Infrastructure Readiness Probe
curl -s http://localhost/api/v1/ready/ | jq .

# 4. Django Admin Static Asset Verification
curl -I http://localhost/static/admin/css/base.css
```

Expected health response (`HTTP 200 OK`):
```json
{
  "status": "UP",
  "service": "gqt-hrms-api",
  "version": "1.0.0",
  "environment": "production"
}
```

### 8.2 Log Inspection
Tail live container logs:
```bash
# All services
docker compose logs -f

# Backend WSGI logs only
docker compose logs -f backend

# Nginx edge access & error logs only
docker compose logs -f frontend
```

---

## 9. Safe Shutdown & Restart

### 9.1 Graceful Shutdown
To stop the services without losing persistent volumes:
```bash
docker compose down
```

### 9.2 Restart Services
```bash
docker compose restart
```

### 9.3 Complete Teardown (Volumes Preserved)
```bash
docker compose down --remove-orphans
```
> [!WARNING]
> Do NOT pass `-v` or `--volumes` to `docker compose down` unless you intend to permanently delete uploaded student resumes and media files stored in `gqt_hrms_media_data`.

---

## 10. Database Migrations & Administrative Procedures

The Docker container **deliberately does not run migrations automatically on container restart**. This prevents accidental schema race conditions when scaling out multiple backend replicas.

### 10.1 Execute Database Migrations
Run migrations as a one-off task using the existing backend container:
```bash
docker compose exec -it backend python manage.py migrate
```

### 10.2 Collect Static Files (if updated)
```bash
docker compose exec -it backend python manage.py collectstatic --noinput
```

### 10.3 Database Backups (Supabase PostgreSQL 16)
- **Automated Point-in-Time Recovery (PITR):** Handled continuously by Supabase.
- **Manual Logical Dump:**
  ```bash
  pg_dump -h [DB_HOST] -U postgres -d postgres -F c -b -v -f gqt_hrms_backup_$(date +%Y%m%d_%H%M%S).dump
  ```

---

## 11. Reverse Proxy & TLS/HTTPS Architecture

### 11.1 SSL/TLS Termination
In typical enterprise production, TLS is terminated at:
1. **Cloud Load Balancer / CDN (Cloudflare, AWS ALB, GCP Load Balancer), OR**
2. **Host-level Nginx / Caddy with Let's Encrypt certificates.**

The internal Nginx edge container is configured to receive `X-Forwarded-Proto` and `X-Forwarded-For` from the upstream terminator and pass them to Gunicorn:
```nginx
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```
Django's `SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")` validates this header to enforce HTTPS redirect logic safely.

---

## 12. Continuous Integration (CI) Workflow

The GitHub Actions CI pipeline (`.github/workflows/ci.yml`) triggers on every push and pull request targeting `master`.

### Quality Gates Enforced in CI:
1. **Django System Checks:** `python manage.py check --settings=config.settings.test`
2. **Migration Consistency:** `python manage.py makemigrations --check --dry-run`
3. **Backend Pytest Suite:** All 354 automated backend tests executed against clean test database.
4. **Frontend TypeScript Check:** `tsc -b --noEmit` strict type checking.
5. **Frontend Vitest Suite:** All 147 component, hook, and route unit tests.
6. **Frontend Production Build:** Vite build bundle optimization and chunk verification.
7. **Docker Packaging Validation:** Docker Compose configuration check and Dockerfile syntax builds.

Any failure in any gate immediately halts the pipeline and blocks pull request merging.

---

## 13. Troubleshooting Common Issues

### Issue 1: Backend Fails Boot with `ImproperlyConfigured: Production Security Violation: DJANGO_SECRET_KEY...`
- **Cause:** `DJANGO_SECRET_KEY` in `.env` is omitted, shorter than 40 characters, contains "insecure", or matches development fallbacks.
- **Remedy:** Generate a secure random key (e.g. `python -c "import secrets; print(secrets.token_urlsafe(50))"`) and assign it in `.env`.

### Issue 2: CSRF Verification Failed (`403 Forbidden` on POST/PUT requests)
- **Cause:** `CSRF_TRUSTED_ORIGINS` does not match the exact scheme and domain used by the browser (e.g. missing `https://`).
- **Remedy:** Ensure `CSRF_TRUSTED_ORIGINS=https://hrms.gqtech.in` matches the client's origin header.

### Issue 3: Django Admin Styling Missing (`/static/admin/css/base.css` 404)
- **Cause:** Static volume was not populated or Nginx is not mounting `static_data`.
- **Remedy:** Ensure `docker-compose.yml` mounts `static_data:/usr/share/nginx/static:ro` on `frontend`, and execute `docker compose exec backend python manage.py collectstatic --noinput`.

### Issue 4: Direct Access to Student Resumes Forbidden (`404` or `403`)
- **Cause:** Expected behavior. Direct access to `/media/` is denied by Nginx for candidate privacy.
- **Remedy:** Access resumes through the authenticated API: `/api/v1/students/resumes/<id>/download/`.

---

## 14. Environment Separation Boundaries

| Environment | Database Engine | `DEBUG` | Container Packaging |
| :--- | :--- | :---: | :--- |
| **Local Dev** | SQLite / Supabase Dev | `True` | Direct run (`manage.py runserver`, `vite dev`) |
| **Local Test** | SQLite in-memory | `False` | Pytest / Vitest runners |
| **Workstream 5 CI** | SQLite in-memory | `False` | GitHub Actions Linux runners |
| **Staging / Prod (WS6)** | Supabase PostgreSQL 16 | `False` | Docker Compose (`gqt-hrms-backend` + `gqt-hrms-frontend`) |
