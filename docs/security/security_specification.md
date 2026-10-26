# GQT HRMS — Security Specification & Invariant Auditing

## 1. Zero Secret Disclosure Principle
* **Strict Invariant:** No secret keys, API tokens, database passwords, or private keys are ever stored in source code, Git commits, frontend environment files, or client-delivered JavaScript bundles.
* **Bundle Auditing:** Automated tests scan `frontend/dist` to ensure zero presence of database URLs, server passwords, or service-role keys.

---

## 2. Fail-Closed Production Runtime
In `backend/config/settings/production.py`:
1. `DJANGO_SECRET_KEY`: Must be provided, $\ge 40$ characters, and contain no "insecure" dev placeholder.
2. `DJANGO_ALLOWED_HOSTS`: Must be provided and cannot be wildcard `*` or only localhost.
3. Database Credentials: Password cannot be default/empty.
4. Cookie Security: `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, and `JWT_COOKIE_SECURE` must be `True`.
5. HTTPS Enforcement: `SECURE_SSL_REDIRECT = True`, `SECURE_HSTS_SECONDS = 31536000`.

---

## 3. Log Stream Sanitization
`SensitiveDataFilter` intercepts all log records across Django, Gunicorn, and application loggers to automatically redact:
* Passwords (`password: [REDACTED]`)
* Tokens and Bearer headers (`Bearer [REDACTED_JWT]`)
* Database connection URLs (`postgresql://user:[REDACTED_PASSWORD]@host...`)
* API keys and secret values.

---

## 4. Request Correlation ID Tracing
`CorrelationIdMiddleware` extracts incoming `X-Correlation-ID` or generates a unique UUIDv4. This ID is:
1. Injected into `request.correlation_id`.
2. Stored in thread-local context for log messages: `[req:UUID]`.
3. Injected into all outbound response headers as `X-Correlation-ID`.
4. Attached to standardized JSON error responses for rapid support debugging.

---

## 5. Identity, Authentication & RBAC Architecture (Phase 1)
* **Custom User Model:** Primary key is cryptographically random UUIDv4; email is normalized (lowercased, stripped) with database-level uniqueness constraint (`Lower('email')`).
* **Cryptographic Password Hashing:** Production utilizes `Argon2id` as the primary hasher with `PBKDF2` fallback.
* **Dual-Transport JWT Authentication:**
  * First-party web frontend communicates exclusively via secure `HttpOnly`, `SameSite=Lax` cookies (`gqt_access_token` with 15m lifetime and `gqt_refresh_token` with 7d lifetime). Zero tokens or credentials are stored in localStorage or sessionStorage.
  * Programmatic API clients can supply `Authorization: Bearer <token>`.
* **Refresh Token Rotation & Replay Prevention:** `rest_framework_simplejwt.token_blacklist` rotates refresh tokens on every refresh call and blacklists used tokens immediately. Replay of spent tokens triggers rejection and security alerts.
* **CSRF & Origin Protection:** Mutating requests require valid `X-CSRFToken` header matching the `gqt_csrftoken` cookie.
* **Brute-Force & Enumeration Defense:**
  * Login and password recovery endpoints are rate-limited (`AuthRateThrottle`: 10 req/min).
  * Login returns generic `Invalid email or password.` errors for nonexistent users and invalid passwords.
  * Password reset returns identical generic confirmations regardless of whether the email address exists.
* **Immutable Security Event Audit Trail:** Every authentication event (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`, `PASSWORD_CHANGED`, `PASSWORD_RESET_REQUESTED`, `PASSWORD_RESET_COMPLETED`, `ROLES_UPDATED`, `ACCOUNT_STATUS_CHANGED`, `ADMIN_BOOTSTRAPPED`) is recorded into `core_audit_log` with remote IP, correlation ID, and zero password/token disclosure.
* **Role-Based & Object-Level Authorization:** Governed by `docs/security/role_permission_matrix.md` with deny-by-default endpoints and server-side object ownership verification.
