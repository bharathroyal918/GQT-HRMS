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

