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
