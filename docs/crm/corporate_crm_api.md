# GQT HRMS — Corporate CRM API Specification

## 1. Overview
Versioned endpoints under the `/api/v1/crm/` namespace providing Corporate CRM & HR Directory Management functionality. All responses adhere to the standard envelope format:

```json
{
  "success": true,
  "meta": { ... },
  "data": { ... }
}
```

---

## 2. Company Endpoints

### `GET /api/v1/crm/companies/`
- **Permissions**: `ADMIN`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `HR_RELATIONSHIP_MGR`, `AUDITOR`.
- **Query Parameters**:
  - `search`: Filter by name, domain, city.
  - `domain_category`: Filter by industry category (e.g. `IT_SERVICES`, `PRODUCT_TECH`).
  - `relationship_status`: Filter by relationship state.
  - `tier`: Filter by `TIER_1`, `TIER_2`, `TIER_3`.
  - `city`: Filter by city name.
  - `owner_id`: Filter by relationship owner UUID.
  - `is_archived`: Boolean (default `false`).
  - `page`, `page_size`: Standard pagination.
  - `ordering`: Safe sorting (`name`, `-name`, `created_at`, `-created_at`, `updated_at`, `-updated_at`).

### `POST /api/v1/crm/companies/`
- **Permissions**: `ADMIN`, `PLACEMENT_HEAD`, `PLACEMENT_OFFICER`, `HR_RELATIONSHIP_MGR`.
- **Payload**:
  ```json
  {
    "name": "Tata Consultancy Services Ltd.",
    "website": "https://www.tcs.com",
    "domain_category": "IT_SERVICES",
    "tier": "TIER_1",
    "relationship_status": "DISCOVERED",
    "source": "MARKET_RESEARCH",
    "city": "Mumbai",
    "state": "Maharashtra",
    "country": "India",
    "address": "TCS House, Raveline Street, Fort, Mumbai",
    "notes": "Major fresher recruiter across colleges"
  }
  ```

### `GET /api/v1/crm/companies/check-duplicate/`
- **Query Parameters**: `name` (required), `website` (optional).
- **Response**: List of candidate matches with `match_type` (`EXACT_NAME` or `DOMAIN_MATCH`) and `reason`.

### `POST /api/v1/crm/companies/{id}/archive/`
- Archives company while preserving historical outreach and contacts.

### `POST /api/v1/crm/companies/{id}/restore/`
- Restores an archived company profile.

---

## 3. HR Contact Endpoints

### `GET /api/v1/crm/contacts/`
- **Query Parameters**: `company_id`, `search`, `status`, `owner_id`, `is_archived`, `page`, `page_size`.

### `POST /api/v1/crm/contacts/`
- **Payload**:
  ```json
  {
    "company": "c8a411ec-4581-42e7-8fd2-9f323714f3da",
    "name": "Sunita Sharma",
    "designation": "Lead Campus Recruiter",
    "department": "Human Resources",
    "email": "sunita.sharma@infosys.com",
    "phone": "+919876543210",
    "preferred_channel": "CALL",
    "status": "ACTIVE"
  }
  ```

---

## 4. Corporate Outreach Endpoints

### `GET /api/v1/crm/outreach/`
- **Query Parameters**: `company_id`, `hr_contact_id`, `performed_by_id`, `channel`, `outcome`, `direction`, `date_from`, `date_to`, `search`.

### `POST /api/v1/crm/outreach/`
- **Payload**:
  ```json
  {
    "company": "c8a411ec-4581-42e7-8fd2-9f323714f3da",
    "hr_contact": "8f8b8e01-38ef-41fa-8fbc-3a677119e712",
    "channel": "CALL",
    "direction": "OUTBOUND",
    "outcome": "CONNECTED_INTERESTED",
    "subject": "Initial Campus Placement Pitch for 2026 Batch",
    "notes": "Discussed hiring numbers. Requested brochure via email.",
    "followup_required": true
  }
  ```

---

## 5. Follow-Up Endpoints

### `GET /api/v1/crm/follow-ups/`
- **Query Parameters**: `company_id`, `hr_contact_id`, `assigned_to_id`, `status`, `priority`, `is_overdue`, `due_date_from`, `due_date_to`, `search`.

### `GET /api/v1/crm/follow-ups/overdue/`
- Convenience endpoint returning all overdue tasks (`is_overdue=true`).

### `POST /api/v1/crm/follow-ups/`
- **Payload**:
  ```json
  {
    "company": "c8a411ec-4581-42e7-8fd2-9f323714f3da",
    "hr_contact": "8f8b8e01-38ef-41fa-8fbc-3a677119e712",
    "due_date": "2026-10-30T10:00:00Z",
    "priority": "HIGH",
    "purpose": "Send campus drive proposal and eligibility checklist"
  }
  ```

### `POST /api/v1/crm/follow-ups/{id}/reschedule/`
- **Payload**: `{"new_due_date": "2026-11-02T14:30:00Z", "reason": "HR requested call next week"}`.

### `POST /api/v1/crm/follow-ups/{id}/complete/`
- **Payload**: `{"completion_notes": "Proposal sent and acknowledged"}`.

### `POST /api/v1/crm/follow-ups/{id}/cancel/`
- **Payload**: `{"cancellation_reason": "HR confirmed no fresher intake this financial year"}`.

### `POST /api/v1/crm/follow-ups/{id}/reopen/`
- **Payload**: `{"new_due_date": "2026-11-10T10:00:00Z", "reason": "HR re-initiated fresher recruitment"}`.

---

## 6. Dashboard & Metrics Endpoints

### `GET /api/v1/crm/dashboard/metrics/`
- **Query Parameters**: `timezone` (default: `Asia/Kolkata`).
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "total_active_companies": 42,
      "total_active_contacts": 85,
      "daily_outreach_target": 100,
      "today_outreach_count": 24,
      "today_outreach_progress_percent": 24.0,
      "channel_breakdown": {
        "CALL": 12,
        "EMAIL": 8,
        "LINKEDIN": 4
      },
      "user_today_outreach_count": 15,
      "follow_ups_due_today": 7,
      "follow_ups_overdue": 3,
      "follow_ups_completed": 18,
      "timezone": "Asia/Kolkata",
      "as_of": "2026-10-26T13:30:00Z",
      "recent_activities": [ ... ]
    }
  }
  ```

### `GET /api/v1/crm/config/`
- Returns system operational configurations.

### `POST /api/v1/crm/config/`
- Restricted to `ADMIN` and `PLACEMENT_HEAD`. Updates configuration keys.
