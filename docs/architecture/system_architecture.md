# GQT HRMS & Recruitment CRM — System Architecture Specification

## 1. Executive Architecture Summary
GQT HRMS is an enterprise single-organization SaaS platform automating institutional recruitment, student placement training, interview drives, and corporate relationship CRM.

---

## 2. 5-Layer Backend Architecture Pattern
Every business domain follows a strict 5-layer separation of concerns:

```
┌────────────────────────────────────────────────────────┐
│ 1. VIEWS & VIEWSETS                                    │
│    - HTTP parsing, status codes, standard envelopes    │
│    - Role & Object-level permission guards             │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 2. SERIALIZERS                                         │
│    - Input validation, sanitization, schema generation │
└──────────────────────────┬─────────────────────────────┘
                           │ Validated Data
                           ▼
┌────────────────────────────────────────────────────────┐
│ 3. SERVICES (Atomic Mutation Engine)                   │
│    - @transaction.atomic boundaries                    │
│    - Pessimistic row locking: select_for_update()      │
│    - File magic bytes validation & SHA-256 hashing     │
│    - Audit trail logging                               │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 4. SELECTORS (Query Engine)                            │
│    - Read queries, select_related, prefetch_related    │
│    - Aggregations, metrics, and funnel calculations    │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│ 5. MODELS (Relational Entities)                        │
│    - UUIDv4 primary keys (non-enumerable)              │
│    - DecimalField for currency & CTC precision         │
│    - Protected deletion: on_delete=models.PROTECT      │
│    - Composite unique constraints                      │
└────────────────────────────────────────────────────────┘
```

---

## 3. Frontend Architecture
* **Framework:** React 19 + TypeScript (strict compiler options).
* **Styling:** Tailwind CSS with official Global Quest Technologies brand tokens:
  * Primary Deep Navy: `#001B4D`
  * Vivid Blue Accent: `#005BBB`
  * Charcoal Gray: `#1E293B`
  * Neutral Gray: `#64748B` / `#F1F5F9`
* **State & Server Cache:** TanStack Query v5 with normalized keys and optimistic mutations.
* **Form Validation:** React Hook Form with Zod runtime validation schemas.
* **API Client:** Axios with CSRF cookie auto-injection, Correlation ID propagation, and standard error extraction.
* **Bundle Optimization:** Route-level code splitting and manual vendor chunking (`vendor-react`, `vendor-query`, `vendor-forms`, `vendor-icons`).

---

## 4. Identity, Authentication & RBAC Domain (`apps.accounts`)
* **Custom User Model (`accounts_user`):**
  * `id`: UUIDv4 primary key.
  * `email`: Normalized, case-insensitive unique authentication identity (`Lower('email')`).
  * Account status flags: `is_active`, `is_staff`, `is_superuser`.
* **Role-Based Access Control (`accounts_role`, `accounts_user_role_assignment`):**
  * Normalized relational assignment model with active status flags and assignment audit references (`assigned_by`, `assigned_at`).
  * 9 operational roles: `ADMIN`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `HR_RELATIONSHIP_MGR`, `CREATIVE_DESIGNER`, `TRAINER`, `EVALUATOR`, `STUDENT`, `AUDITOR`.
* **Authentication Subsystem:**
  * Dual-transport JWT authentication via `HttpOnlyCookieJWTAuthentication` (SameSite cookies `gqt_access_token` and `gqt_refresh_token` for browser; Bearer header fallback for API consumers).
  * Refresh token rotation and replay prevention backed by `rest_framework_simplejwt.token_blacklist`.
  * Centralized `AuthContext` on frontend with `ProtectedRoute` guards and role-aware navigation. Zero credentials stored in web storage.
