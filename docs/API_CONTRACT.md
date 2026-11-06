# CivicTrack ΓÇö API Contract (P0, frozen)

> **Document type:** Phase 2 deliverable ΓÇö frozen endpoint catalogue  
> **Status:** Approved for implementation (Phases 5ΓÇô13)  
> **Version:** 1.0  
> **Date:** 06 November 2026  
> **Base path:** `/api/v1` (health endpoints are unversioned)  
> **Authority:** TRD ┬º8, ┬º9, ┬º16; SRS FR-001ΓÇôFR-050, RBAC-01ΓÇô08, SEC-01ΓÇô16  
> **Companion:** [`ARCHITECTURE.md`](./ARCHITECTURE.md), [`STATE_MACHINE.md`](./STATE_MACHINE.md)

---

## 1. Conventions

| Convention | Value |
|---|---|
| Transport | HTTPS in production; JSON except multipart upload and image streaming |
| Auth | `Authorization: Bearer <jwt>` (HS256, 8 h) |
| Timestamps | ISO 8601 UTC, e.g. `2026-11-06T10:00:00Z` |
| IDs | integers in JSON; tracking numbers are strings |
| Pagination | `?page=1&page_size=20`; `page_size` 1ΓÇô100, default 20 |
| List envelope | `{items, page, page_size, total, total_pages}` (+ list-specific extras) |
| Sorting | server-defined, newest first unless documented |
| Error envelope | `{"error":{"code","message","details?"},"request_id"}` |
| Request ID | `X-Request-ID` read or generated, always echoed |
| Idempotency | transitions guarded by status ΓåÆ 409; escalation is naturally idempotent |
| OpenAPI | `/docs` in non-production; schema export committed |

**Scope rule:** role gates are enforced by route dependencies; ownership and department scope are enforced in services using the authenticated user, never a client-supplied scope parameter.

---

## 2. Shared schemas

### 2.1 Error envelope

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Complaint has already been decided or resolved.",
    "details": { "current_status": "ACCEPTED" }
  },
  "request_id": "req-8f2a1c"
}
```

### 2.2 Pagination

```json
{ "items": [], "page": 1, "page_size": 20, "total": 0, "total_pages": 0 }
```

### 2.3 `UserProfile`

| Field | Type | Notes |
|---|---|---|
| `id` | integer | |
| `full_name` | string | 2ΓÇô120 |
| `email` | string | never returned with password fields |
| `phone` | string \| null | optional |
| `role` | enum | `CITIZEN`, `DEPARTMENT_OFFICER`, `SUPERINTENDENT_OFFICER`, `PLATFORM_ADMIN` |
| `department` | `DepartmentRef` \| null | required for Department Officer |
| `is_active` | boolean | |

`DepartmentRef`: `{id, name, code}`. `UserSummary`: `{id, full_name}` (or with `role` in timeline actors).

### 2.4 `ComplaintSummary`

| Field | Type | Notes |
|---|---|---|
| `id` | integer | |
| `complaint_number` | string | `^CT-[0-9]{4}-[0-9]{6}$` |
| `title` | string | |
| `status` | enum | canonical status |
| `category` | string | category name in list responses |
| `department` | string | department name in list responses |
| `submitted_at` | timestamp | |
| `accepted_at` | timestamp \| null | |
| `resolution_due_at` | timestamp \| null | |
| `overdue` / `is_overdue` | boolean | computed at request time |
| `assigned_to` | `UserSummary` \| null | department queue only |

### 2.5 `ComplaintDetail`

Create response and detail response share this shape:

| Field | Type | Notes |
|---|---|---|
| `id`, `complaint_number`, `title`, `description` | | description 20ΓÇô2,000 |
| `status`, `priority` | enum | `LOW`, `MEDIUM`, `HIGH` |
| `category` | `CategoryRef` | `{id, name, code}` |
| `department` | `DepartmentRef` | |
| `location` | `{text, latitude, longitude}` | any member may be null |
| `images` | `ImageMeta[]` | `{id, kind, mime_type, size_bytes, url}` |
| `submitted_at`, `accepted_at`, `resolution_due_at`, `escalated_at`, `resolved_at` | timestamps \| null | |
| `resolution_note` | string \| null | |
| `is_verified` | boolean | always `false` for a citizen report; display metadata only |
| `resolution` | object \| null | detail only: `{note, resolved_at, resolved_by, evidence[]}` |
| `timeline_url` | string | detail only |

### 2.6 `TimelineEvent`

| Field | Type | Notes |
|---|---|---|
| `id` | string | namespaced: `hist-`, `comment-`, `esc-`, `action-`, `image-` |
| `event_type` | enum | `STATUS_CHANGE`, `PROGRESS_NOTE`, `ESCALATION`, `SUPERINTENDENT_ACTION`, `IMAGE` |
| `from_status`, `to_status` | enum \| null | status events only |
| `actor` | `{id, display_name, role}` | system actor: `{id:null, display_name:"SYSTEM", role:"SYSTEM"}` |
| `note` | string \| null | |
| `created_at` | timestamp | ascending order, then event id |

### 2.7 `Notification`

| Field | Type | Notes |
|---|---|---|
| `id` | integer | |
| `trigger_code` | string | `NT-01`ΓÇª`NT-07` (NT-08 is P1) |
| `title`, `body` | string | plain text; includes tracking number and status |
| `complaint_id`, `complaint_number` | integer, string | |
| `is_read` | boolean | |
| `created_at` | timestamp | |

### 2.8 Admin resource shapes

- `Department`: `{id, name, code, description, is_active, created_at, updated_at}`
- `Category`: `{id, name, code, description, department, default_priority, is_active, created_at, updated_at}`
- `AdminUser`: `UserProfile` + `{created_at, updated_at}`
- `OfficerAction`: `{id, complaint_id, action_type, note, directed_department, officer, created_at}`
- `AuditLog`: `{id, actor_user_id, actor_role, action, entity_type, entity_id, created_at, metadata}`

---

## 3. Authorization and scope matrix

| Endpoint group | Public | Citizen | Dept Officer | Superintendent | Admin | Internal token |
|---|---|---|---|---|---|---|
| `POST /auth/register`, `POST /auth/login` | yes | ΓÇö | ΓÇö | ΓÇö | ΓÇö | ΓÇö |
| `POST /auth/logout`, `GET /auth/me` | ΓÇö | own | own | own | own | ΓÇö |
| `GET /categories` | ΓÇö | yes | yes | yes | yes | ΓÇö |
| `POST /complaints` | ΓÇö | yes | ΓÇö | ΓÇö | ΓÇö | ΓÇö |
| `GET /complaints` | ΓÇö | own only | ΓÇö | ΓÇö | ΓÇö | ΓÇö |
| `GET /complaints/{id}` | ΓÇö | owner only | same dept | escalated/read | read-only | ΓÇö |
| `GET /complaints/{id}/timeline` | ΓÇö | owner only | same dept | escalated/read | read-only | ΓÇö |
| `POST /complaints/{id}/images` | ΓÇö | ΓÇö | same dept | ΓÇö | ΓÇö | ΓÇö |
| `GET /complaints/{id}/images/{image_id}/file` | ΓÇö | owner | same dept | escalated/read | read-only | ΓÇö |
| `/department/*` | ΓÇö | ΓÇö | yes | ΓÇö | ΓÇö | ΓÇö |
| `POST /complaints/{id}/accept|reject|assign|progress` | ΓÇö | ΓÇö | same dept | ΓÇö | ΓÇö | ΓÇö |
| `POST /complaints/{id}/resolve` | ΓÇö | ΓÇö | same dept | escalated only | ΓÇö | ΓÇö |
| `/superintendent/*` | ΓÇö | ΓÇö | ΓÇö | yes | ΓÇö | ΓÇö |
| `POST /complaints/{id}/superintendent-actions` | ΓÇö | ΓÇö | ΓÇö | escalated only | ΓÇö | ΓÇö |
| `/notifications/*` | ΓÇö | own | own | own | own | ΓÇö |
| `/admin/*` | ΓÇö | ΓÇö | ΓÇö | ΓÇö | yes | ΓÇö |
| `/internal/*` | ΓÇö | ΓÇö | ΓÇö | ΓÇö | ΓÇö | yes |
| `/health*` | yes | ΓÇö | ΓÇö | ΓÇö | ΓÇö | ΓÇö |

**Status codes:** `401` missing/expired/invalid token or inactive user; `403` wrong role or wrong department; `404` absent resource or citizen scope violation; `409` illegal transition.

---

## 4. Endpoint catalogue ΓÇö P0

> **Coverage:** 40 P0 endpoints. Every row declares method, path, allowed role, object scope, request, success response, and error codes.

### 4.1 Authentication

#### 4.1.1 `POST /api/v1/auth/register`

| Item | Contract |
|---|---|
| Role / scope | Public |
| Request | `{full_name: string (2ΓÇô120), email: string, password: string (8ΓÇô72, letter+digit), phone?: string}` |
| Success | `201 {token, token_type:"bearer", expires_in:28800, user: UserProfile}` |
| Errors | `409 EMAIL_ALREADY_REGISTERED`, `422 VALIDATION_ERROR`, `429 RATE_LIMITED` |

Registration always assigns `CITIZEN`; a client-supplied `role` is ignored.

#### 4.1.2 `POST /api/v1/auth/login`

| Item | Contract |
|---|---|
| Role / scope | Public |
| Request | `{email, password}` |
| Success | `200 {token, token_type:"bearer", expires_in:28800, user: UserProfile}` |
| Errors | `401 INVALID_CREDENTIALS`, `422 VALIDATION_ERROR`, `429 RATE_LIMITED` |

#### 4.1.3 `POST /api/v1/auth/logout`

| Item | Contract |
|---|---|
| Role / scope | Any authenticated user |
| Request | none |
| Success | `204 No Content` |
| Errors | `401 TOKEN_INVALID` |

Revocation is client-side (sessionStorage disposal); a future denylist is out of scope.

#### 4.1.4 `GET /api/v1/auth/me`

| Item | Contract |
|---|---|
| Role / scope | Any authenticated user; own profile only |
| Success | `200 UserProfile` |
| Errors | `401 TOKEN_INVALID` |

### 4.2 Category catalogue

#### 4.2.1 `GET /api/v1/categories`

| Item | Contract |
|---|---|
| Role / scope | Any authenticated user |
| Request | none (active categories only) |
| Success | `200 {items: CategoryRef[]}` where `CategoryRef = {id, name, code, department:{id,name,code}}` |
| Errors | `401 TOKEN_INVALID` |

### 4.3 Complaints

#### 4.3.1 `POST /api/v1/complaints`

| Item | Contract |
|---|---|
| Role / scope | `CITIZEN`; complaint owned by the authenticated user |
| Request | `multipart/form-data`: `title` (5ΓÇô150), `description` (20ΓÇô2,000), `category_id` (int, active), `location_text?`, `latitude?`, `longitude?` (both-or-neither), `images?` 0ΓÇô3 (JPEG/PNG/WebP Γëñ5 MiB each) |
| Success | `201 ComplaintDetail`; status `PENDING_DEPARTMENT_REVIEW`; tracking number returned |
| Errors | `413 UPLOAD_TOO_LARGE`, `422 UNSUPPORTED_MEDIA_TYPE`, `422 CATEGORY_NOT_MAPPED`, `422 VALIDATION_ERROR`, `401`, `403` |

#### 4.3.2 `GET /api/v1/complaints`

| Item | Contract |
|---|---|
| Role / scope | `CITIZEN`; own complaints only |
| Request | query: `status?`, `category_id?`, `page?`, `page_size?` |
| Success | `200 Paginated<ComplaintSummary>` |
| Errors | `401`, `422 VALIDATION_ERROR` (bad query) |

#### 4.3.3 `GET /api/v1/complaints/{id}`

| Item | Contract |
|---|---|
| Role / scope | Owner; officer of responsible department; Superintendent (escalated/read); Administrator read-only |
| Success | `200 ComplaintDetail` + `resolution` + `timeline_url` |
| Errors | `401`, `403 FORBIDDEN` (officer other department), `404 NOT_FOUND` (absent or citizen scope) |

#### 4.3.4 `GET /api/v1/complaints/{id}/timeline`

| Item | Contract |
|---|---|
| Role / scope | Same as detail |
| Success | `200 {items: TimelineEvent[]}` ascending by `created_at`, then id |
| Errors | `401`, `403`, `404` |

#### 4.3.5 `POST /api/v1/complaints/{id}/images`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER` of the responsible department; status `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` |
| Request | `multipart/form-data`: `kind` = `PROGRESS` \| `RESOLUTION`; `images` 1ΓÇô3 (JPEG/PNG/WebP Γëñ5 MiB each; max 10 per complaint lifetime) |
| Success | `201 {items: ImageMeta[]}` |
| Errors | `403`, `404`, `409 INVALID_TRANSITION` (wrong status), `413 UPLOAD_TOO_LARGE`, `422 UNSUPPORTED_MEDIA_TYPE`, `422 VALIDATION_ERROR` (limit exceeded) |

#### 4.3.6 `GET /api/v1/complaints/{id}/images/{image_id}/file`

| Item | Contract |
|---|---|
| Role / scope | Same as complaint detail; image must belong to the complaint |
| Success | `200` binary stream, stored MIME type, `Content-Disposition: inline`, `Cache-Control: private, max-age=300` |
| Errors | `401`, `403`, `404` |

No image is served publicly or from a predictable unauthenticated URL.

### 4.4 Department operations

#### 4.4.1 `GET /api/v1/department/complaints`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER`; own department only |
| Request | query: `status?`, `assigned_to?`, `overdue?`, `page?`, `page_size?` |
| Success | `200 {items: ComplaintSummary[], counts: {status: int}, page, page_size, total, total_pages}` |
| Errors | `401`, `403` |

#### 4.4.2 `GET /api/v1/department/summary`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER`; own department |
| Success | `200 {counts: {status: int}, escalated: int, overdue: int}` |
| Errors | `401`, `403` |

#### 4.4.3 `POST /api/v1/complaints/{id}/accept`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER` of the responsible department; status `PENDING_DEPARTMENT_REVIEW` |
| Request | none |
| Success | `200 {id, complaint_number, status:"ACCEPTED", department, accepted_at, accepted_by:{id,full_name}, sla_seconds, resolution_due_at, notifications_created:["NT-02"]}` |
| Errors | `401`, `403`, `404`, `409 INVALID_TRANSITION` (with current status) |

#### 4.4.4 `POST /api/v1/complaints/{id}/reject`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER` of the responsible department; status `PENDING_DEPARTMENT_REVIEW` |
| Request | `{reason: string (10ΓÇô1,000)}` |
| Success | `200 {id, status:"REJECTED", rejected_at, rejected_by, rejection_reason, notifications_created:["NT-03"]}` |
| Errors | `401`, `403`, `404`, `409 INVALID_TRANSITION`, `422 VALIDATION_ERROR` |

#### 4.4.5 `POST /api/v1/complaints/{id}/assign`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER` of the responsible department; status `PENDING_DEPARTMENT_REVIEW`, `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` |
| Request | `{assignee_user_id: integer}` (active same-department user) |
| Success | `200 {id, assigned_to:{id,full_name}, assigned_at}`; status unchanged; no citizen notification |
| Errors | `401`, `403`, `404`, `422 VALIDATION_ERROR` (inactive/other department) |

#### 4.4.6 `POST /api/v1/complaints/{id}/progress`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER` of the responsible department; status `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` |
| Request | `{note: string (5ΓÇô2,000), set_status?: "IN_PROGRESS"}` |
| Success | `200 {id, status, timeline_event: TimelineEvent, notifications_created:["NT-04"]}` |
| Errors | `401`, `403`, `404`, `409 INVALID_TRANSITION` (wrong status or disallowed change), `422 VALIDATION_ERROR` |

`set_status` is optional. On `ESCALATED`, the status remains `ESCALATED`; a request implying another status returns `409`.

#### 4.4.7 `POST /api/v1/complaints/{id}/resolve`

| Item | Contract |
|---|---|
| Role / scope | `DEPARTMENT_OFFICER` of the responsible department (`ACCEPTED`, `IN_PROGRESS`, `ESCALATED`) or `SUPERINTENDENT_OFFICER` (`ESCALATED` only) |
| Request | `{resolution_note: string (10ΓÇô2,000), evidence_image_ids?: integer[]}` |
| Success | `200 {id, status:"RESOLVED", resolved_at, resolved_by:{id,full_name,role}, resolution_note, resolution_due_at, was_escalated, notifications_created:["NT-07"]}` |
| Errors | `401`, `403`, `404`, `409 INVALID_TRANSITION`, `422 VALIDATION_ERROR` |

### 4.5 Superintendent operations

#### 4.5.1 `GET /api/v1/superintendent/escalations`

| Item | Contract |
|---|---|
| Role / scope | `SUPERINTENDENT_OFFICER` |
| Request | query: `page?`, `page_size?` |
| Success | `200 {items: [{id, complaint_number, title, department, accepted_at, resolution_due_at, escalated_at, overdue_seconds, current_overdue_seconds, status, last_action_at}], summary:{open, oldest_overdue_seconds}, page, page_size, total, total_pages}` sorted by overdue descending |
| Errors | `401`, `403` |

#### 4.5.2 `GET /api/v1/superintendent/summary`

| Item | Contract |
|---|---|
| Role / scope | `SUPERINTENDENT_OFFICER` |
| Success | `200 {open: int, oldest_overdue_seconds: int, by_department:[{id, name, open: int}]}` |
| Errors | `401`, `403` |

#### 4.5.3 `POST /api/v1/complaints/{id}/superintendent-actions`

| Item | Contract |
|---|---|
| Role / scope | `SUPERINTENDENT_OFFICER`; status `ESCALATED` only |
| Request | `{action_type: "INSTRUCTION"\|"FOLLOW_UP"\|"REASSIGN"\|"NOTE", note: string (5ΓÇô2,000), directed_department_id?: integer}` |
| Success | `201 OfficerAction {id, complaint_id, action_type, note, directed_department, officer, created_at, notifications_created:["NT-06"]}` |
| Errors | `401`, `403`, `404`, `409 INVALID_TRANSITION`, `422 VALIDATION_ERROR` |

### 4.6 Notifications

#### 4.6.1 `GET /api/v1/notifications`

| Item | Contract |
|---|---|
| Role / scope | Any authenticated user; own rows only |
| Request | query: `unread_only?` (default false), `page?`, `page_size?` |
| Success | `200 {items: Notification[], unread_count: int, page, page_size, total, total_pages}` |
| Errors | `401` |

#### 4.6.2 `GET /api/v1/notifications/unread-count`

| Item | Contract |
|---|---|
| Role / scope | Any authenticated user; own rows only |
| Success | `200 {unread_count: int}` |
| Errors | `401` |

#### 4.6.3 `POST /api/v1/notifications/{id}/read`

| Item | Contract |
|---|---|
| Role / scope | Any authenticated user; own notification only |
| Success | `200 {id, is_read:true, read_at}`; repeat call is idempotent |
| Errors | `401`, `404 NOT_FOUND` (another user's notification or absent; no disclosure) |

#### 4.6.4 `POST /api/v1/notifications/read-all`

| Item | Contract |
|---|---|
| Role / scope | Any authenticated user; own rows only |
| Success | `200 {updated: int}`; idempotent |
| Errors | `401` |

### 4.7 Administration

#### 4.7.1 `GET /api/v1/admin/users`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Request | query: `role?`, `department_id?`, `is_active?`, `page?`, `page_size?` |
| Success | `200 Paginated<AdminUser>` |
| Errors | `401`, `403` |

#### 4.7.2 `POST /api/v1/admin/users`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Request | `{full_name, email, password, phone?, role, department_id?}`; `department_id` required for `DEPARTMENT_OFFICER`, forbidden for `SUPERINTENDENT_OFFICER`/`PLATFORM_ADMIN` |
| Success | `201 AdminUser` |
| Errors | `409 EMAIL_ALREADY_REGISTERED`, `422 VALIDATION_ERROR`, `401`, `403` |

#### 4.7.3 `PATCH /api/v1/admin/users/{id}`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN`; last-active-admin protection |
| Request | any of `{role?, department_id?, is_active?}` |
| Success | `200 AdminUser` |
| Errors | `401`, `403`, `404`, `409 LAST_ADMIN_PROTECTED`, `422 VALIDATION_ERROR` |

#### 4.7.4 `GET /api/v1/admin/departments`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Success | `200 {items: Department[]}` |
| Errors | `401`, `403` |

#### 4.7.5 `POST /api/v1/admin/departments`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Request | `{name: string, code: string, description?: string}` |
| Success | `201 Department` |
| Errors | `401`, `403`, `409 DUPLICATE_DEPARTMENT`, `422 VALIDATION_ERROR` |

#### 4.7.6 `PATCH /api/v1/admin/departments/{id}`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Request | any of `{name?, code?, description?, is_active?}` |
| Success | `200 Department` |
| Errors | `401`, `403`, `404`, `409 DEPARTMENT_IN_USE` (deactivation blocked while active categories or officers reference it), `422 VALIDATION_ERROR` |

#### 4.7.7 `GET /api/v1/admin/categories`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Success | `200 {items: Category[]}` |
| Errors | `401`, `403` |

#### 4.7.8 `POST /api/v1/admin/categories`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Request | `{name, code, description?, department_id, default_priority?: "LOW"\|"MEDIUM"\|"HIGH", is_active?}` |
| Success | `201 Category` |
| Errors | `401`, `403`, `409 DUPLICATE_CATEGORY`, `422 VALIDATION_ERROR` (inactive/absent department) |

#### 4.7.9 `PATCH /api/v1/admin/categories/{id}`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Request | any of `{name?, code?, description?, department_id?, default_priority?, is_active?}` |
| Success | `200 Category` + `note:"Affects new complaints only."` |
| Errors | `401`, `403`, `404`, `422 VALIDATION_ERROR` |

#### 4.7.10 `GET /api/v1/admin/activity`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN` |
| Success | `200 {by_status:{status:int}, by_department:[{id,name,open,escalated}], escalations_total:int, escalation_window_minutes:int, demo_mode:boolean, recent_events: TimelineEvent[]}` |
| Errors | `401`, `403` |

#### 4.7.11 `GET /api/v1/admin/audit-logs`

| Item | Contract |
|---|---|
| Role / scope | `PLATFORM_ADMIN`; read-only |
| Request | query: `actor_user_id?`, `action?`, `entity_type?`, `from?`, `to?`, `page?`, `page_size?` |
| Success | `200 Paginated<AuditLog>` |
| Errors | `401`, `403`, `422 VALIDATION_ERROR` |

No update or delete operation is exposed.

### 4.8 Internal operations

#### 4.8.1 `POST /api/v1/internal/escalations/run`

| Item | Contract |
|---|---|
| Role / scope | `X-Internal-Token` (constant-time compare, 10 calls/min/token) |
| Request | none; token header |
| Success | `200 {evaluated, escalated, skipped, duration_ms, trigger_source:"MANUAL_TRIGGER", window_minutes, demo_mode, lock_skipped?}`; second call naturally returns zeros |
| Errors | `401 TOKEN_INVALID`, `403 FORBIDDEN`, `429 RATE_LIMITED`, `503 SERVICE_UNAVAILABLE` |

#### 4.8.2 `GET /api/v1/internal/escalation-status`

| Item | Contract |
|---|---|
| Role / scope | `X-Internal-Token` |
| Success | `200 {effective_window_minutes, demo_mode, last_run: {evaluated, escalated, skipped, duration_ms, at} \| null}` |
| Errors | `401`, `403` |

### 4.9 Health

#### 4.9.1 `GET /health`

| Item | Contract |
|---|---|
| Role / scope | Public |
| Success | `200 {"status":"ok","version":"1.0.0"}` |

#### 4.9.2 `GET /health/ready`

| Item | Contract |
|---|---|
| Role / scope | Public |
| Success | `200 {"status":"ready","database":"ok"}` |
| Errors | `503 {"status":"not_ready","database":"unavailable"}` |

---

## 5. Error taxonomy

| HTTP | Code | When | Client behavior |
|---|---|---|---|
| 400 | `INVALID_REQUEST` | malformed JSON/body that cannot be parsed | show generic error |
| 401 | `TOKEN_INVALID` | missing/expired/invalid token, inactive user | clear session, redirect to login |
| 401 | `INVALID_CREDENTIALS` | wrong email/password | inline login error |
| 403 | `FORBIDDEN` | wrong role or wrong department | show forbidden page/banner |
| 404 | `NOT_FOUND` | absent resource or citizen scope violation | show not found |
| 409 | `INVALID_TRANSITION` | illegal status transition | refresh complaint, conflict banner |
| 409 | `EMAIL_ALREADY_REGISTERED` | duplicate email | link to login |
| 409 | `LAST_ADMIN_PROTECTED` | deactivate/demote last active admin | inline admin error |
| 409 | `DEPARTMENT_IN_USE` | deactivate referenced department | inline admin error |
| 409 | `DUPLICATE_DEPARTMENT` / `DUPLICATE_CATEGORY` | duplicate name/code | inline admin error |
| 413 | `UPLOAD_TOO_LARGE` | file > 5 MiB | inline upload error |
| 422 | `VALIDATION_ERROR` | Pydantic/field/business validation | map `details` to fields |
| 422 | `CATEGORY_NOT_MAPPED` | inactive or unmapped category | ask for another category |
| 422 | `UNSUPPORTED_MEDIA_TYPE` | bad image signature/format | inline upload error |
| 429 | `RATE_LIMITED` | login/internal trigger limit | show retry hint + `Retry-After` |
| 500 | `INTERNAL_ERROR` | unhandled exception | show reference `request_id` |
| 503 | `SERVICE_UNAVAILABLE` | database unavailable/readiness failure | retry later |

**Unhandled exceptions:** log the stack trace with `request_id`; return `INTERNAL_ERROR` with `request_id`; never expose SQL, paths, or secrets.

---

## 6. P1 endpoints (documented, not built)

| Method | Path | Role | Status |
|---|---|---|---|
| POST | `/ai/suggest-category` | Citizen | P1 ΓÇö not built |
| GET | `/complaints/{id}/duplicates` | Citizen/Dept | P1 ΓÇö not built |
| GET | `/map/complaints` | Scoped | P1 ΓÇö not built |
| POST | `/complaints/{id}/feedback` | Citizen | P1 ΓÇö not built |
| POST | `/complaints/{id}/reopen-requests` | Citizen | P1 ΓÇö not built |

These endpoints must not be implemented, seeded, or imported in P0 code paths.

---

## 7. Contract validation

| Check | Result |
|---|---|
| P0 endpoints catalogued | 40/40 |
| Every endpoint declares allowed role and object scope | PASS |
| Every endpoint declares request fields and success shape | PASS |
| Every endpoint declares error codes | PASS |
| List endpoints use the common pagination envelope | PASS |
| Error envelope consistent with TRD ┬º8.1/┬º16.1 | PASS |
| P1 endpoints separated and marked not built | PASS |

---

*End of API contract ΓÇö Phase 2, CivicTrack.*

---

## P1 — not built

The P1 endpoints below are intentionally absent from P0 and must not be implemented behind the P0 rollout:

- `POST /api/v1/ai/suggest-category` (FR-051) â€” feature-flagged, server-side Gemini call, silent fallback
- `POST /api/v1/ai/suggest-priority` (FR-054) â€” advisory only
- `POST /api/v1/complaints/{id}/feedback` (FR-056) â€” rating after resolution
- `POST /api/v1/complaints/{id}/reopen` (FR-057) â€” NT-08 trigger
- `GET /api/v1/analytics/overview` (FR-055) â€” Recharts dashboard
- Duplicate scan endpoints (FR-052), issue map feed (FR-053)

Any client hitting an unregistered P1 path receives the standard `404 NOT_FOUND` envelope. P1 may ship only after Phase 20 sign-off, behind per-feature flags, and never on P0 acceptance paths.
