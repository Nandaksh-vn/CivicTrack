# CivicTrack — REST API Contract Specification

> **Document:** `docs/API_CONTRACT.md`  
> **Target Release:** v1.0.0-p0  
> **Base URL:** `/api/v1`  
> **Source Documents:** `docs/TRD.md` (§8), `docs/SRS.md`  

---

## 1. Global Conventions & Standards

### 1.1 Content Negotiation & Serialization
- All requests containing a body must use `Content-Type: application/json` (except image upload endpoints which use `multipart/form-data`).
- All responses serialize using `application/json` with UTF-8 encoding.
- Date and time fields adhere strictly to ISO 8601 UTC format (`YYYY-MM-DDTHH:MM:SSZ` or with timezone offset).

### 1.2 Error Envelope
All error responses (4xx and 5xx) follow a consistent error structure:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Complaint with id 42 does not exist.",
    "details": null
  }
}
```

### 1.3 Pagination Standard
List endpoints support `limit` (default: 20, max: 100) and `offset` (default: 0) query parameters. Responses return:
```json
{
  "items": [ ... ],
  "total": 128,
  "limit": 20,
  "offset": 0
}
```

---

## 2. Authentication & Profile (`/auth`)

### 2.1 Register Citizen
- **Method / Path:** `POST /api/v1/auth/register`
- **Access:** Public
- **Request Body:**
  ```json
  {
    "full_name": "Jane Citizen",
    "email": "jane@example.com",
    "password": "Password123",
    "phone": "+91 98765 43210"
  }
  ```
- **Response (201 Created):**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "jane@example.com",
      "full_name": "Jane Citizen",
      "role": "CITIZEN",
      "department_id": null
    }
  }
  ```

### 2.2 Login
- **Method / Path:** `POST /api/v1/auth/login`
- **Access:** Public
- **Request Body:**
  ```json
  {
    "email": "admin@civictrack.local",
    "password": "Admin@12345"
  }
  ```
- **Response (200 OK):** Bearer token + User profile. Constant-time hash verification.

### 2.3 Logout
- **Method / Path:** `POST /api/v1/auth/logout`
- **Access:** Authenticated
- **Response (204 No Content)**

### 2.4 Profile (`me`)
- **Method / Path:** `GET /api/v1/auth/me`
- **Access:** Authenticated
- **Response (200 OK):** Current user object with department metadata if assigned.

---

## 3. Complaint Submission & Citizen Management (`/complaints`)

### 3.1 Submit Complaint
- **Method / Path:** `POST /api/v1/complaints`
- **Access:** `CITIZEN` only
- **Request Body:**
  ```json
  {
    "category_id": 1,
    "title": "Broken water main flooding sidewalk",
    "description": "Continuous leak at corner of 4th cross street.",
    "location_text": "Corner of 4th Cross",
    "latitude": 12.9716,
    "longitude": 77.5946
  }
  ```
- **Response (201 Created):** Complaint object with unique `complaint_number` (e.g., `CT-20261106-9041`) and status `SUBMITTED`.

### 3.2 List My Complaints
- **Method / Path:** `GET /api/v1/complaints`
- **Access:** `CITIZEN` only (returns only caller's complaints)
- **Parameters:** `status`, `limit`, `offset`

### 3.3 Complaint Detail
- **Method / Path:** `GET /api/v1/complaints/{id}`
- **Access:** Citizen owner, Officer of assigned department, Superintendent.

### 3.4 Image Upload
- **Method / Path:** `POST /api/v1/complaints/{id}/images`
- **Access:** Citizen owner (while not RESOLVED/REJECTED), Officer of assigned dept, Superintendent.
- **Form Data:** `file` (binary, max 5 MiB, JPEG/PNG/WebP), `image_kind` (`SUBMISSION|PROGRESS|RESOLUTION`).

### 3.5 Authorized Image Streaming
- **Method / Path:** `GET /api/v1/complaints/{id}/images/{image_id}/file`
- **Access:** Same authorization as Complaint Detail. Streams binary bytes with `X-Content-Type-Options: nosniff`.

---

## 4. Department Officer Operations (`/department`, `/complaints`)

### 4.1 Department Queue
- **Method / Path:** `GET /api/v1/department/queue`
- **Access:** `DEPARTMENT_OFFICER`
- **Query Params:** `status` (`SUBMITTED|IN_PROGRESS|ESCALATED|RESOLVED|REJECTED`), `limit`, `offset`.

### 4.2 Accept Complaint
- **Method / Path:** `POST /api/v1/complaints/{id}/accept`
- **Access:** `DEPARTMENT_OFFICER` (matching department)
- **Transition:** `SUBMITTED -> IN_PROGRESS`. Sets `accepted_at = now()`, derives `resolution_due_at = accepted_at + SLA`. Sends `NT-02`.

### 4.3 Reject Complaint
- **Method / Path:** `POST /api/v1/complaints/{id}/reject`
- **Access:** `DEPARTMENT_OFFICER` (matching department)
- **Transition:** `SUBMITTED -> REJECTED`. Requires `rejection_reason` (min 5 chars). Sends `NT-03`.

### 4.4 Resolve Complaint
- **Method / Path:** `POST /api/v1/complaints/{id}/resolve`
- **Access:** `DEPARTMENT_OFFICER` (matching department) or `SUPERINTENDENT_OFFICER` (if ESCALATED)
- **Transition:** `IN_PROGRESS|ESCALATED -> RESOLVED`. Requires `resolution_note`. Sends `NT-04`.

---

## 5. Superintendent Oversight (`/superintendent`, `/complaints`)

### 5.1 Escalation Queue
- **Method / Path:** `GET /api/v1/superintendent/escalations`
- **Access:** `SUPERINTENDENT_OFFICER`
- **Ordering:** Sorted by overdue duration descending.

### 5.2 Record Action / Directive
- **Method / Path:** `POST /api/v1/complaints/{id}/superintendent-actions`
- **Access:** `SUPERINTENDENT_OFFICER`
- **Request Body:**
  ```json
  {
    "action_type": "INSTRUCTION",
    "directed_department_id": 2,
    "note": "Immediate patch required before tomorrow morning commute."
  }
  ```
- **Response (201 Created):** Creates immutable `officer_actions` row, triggers `NT-06` notification to citizen and department officers.

---

## 6. Administration & Governance (`/admin`)

- `POST/GET/PATCH /api/v1/admin/departments`: Department CRUD. Deactivation blocked if active categories or officers exist.
- `POST/GET/PATCH /api/v1/admin/categories`: Category CRUD and department remapping.
- `GET/POST/PATCH /api/v1/admin/users`: User management. Enforces single active department for officers, protects last active admin.
- `GET /api/v1/admin/activity`: System-wide counts by status, department, and 20 recent timeline events.
- `GET /api/v1/admin/audit-logs`: Filterable, paginated, read-only audit records.

---

## 7. Internal & Diagnostic (`/internal`, `/health`)

- `POST /api/v1/internal/escalations/run` (alias: `/trigger`): Token-protected endpoint (`X-Internal-Token`). Scans and escalates all overdue complaints and returns `{evaluated, escalated, skipped}`.
- `GET /api/v1/internal/escalation-status`: Token-protected effective SLA window and last escalation metadata.
- `GET /api/v1/health`: Liveness probe (HTTP 200).
- `GET /api/v1/health/live`: Worker & API process liveness.
- `GET /api/v1/health/ready`: Database connectivity check.

