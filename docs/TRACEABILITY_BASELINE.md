# CivicTrack — Requirements Traceability Baseline

> **Document type:** Phase 1 deliverable — requirements validation and scope baseline  
> **Status:** Approved baseline for all later phases  
> **Version:** 1.0  
> **Date:** 06 November 2026  
> **Owner:** Architecture & Documentation workstream (DOC)  
> **Sources of truth (read-only):** [`PRD.md`](./PRD.md), [`SRS.md`](./SRS.md), [`TRD.md`](./TRD.md), [`USER_STORIES.md`](./USER_STORIES.md), [`PHASES.md`](./PHASES.md), `CivicTrack_Problem_Statement_and_Objectives.pdf`  
> **Scope:** P0 mandatory; P1 gated and optional; P2 documented only and **not built**.

---

## 1. Purpose and authority

This baseline proves that the documented CivicTrack scope is complete, internally consistent, and testable **before any application code exists**. It is the reference used by every later phase for implementation and test traceability.

**Authority rules**

1. The four requirement documents (`PRD.md`, `SRS.md`, `TRD.md`, `USER_STORIES.md`) remain the source of truth; this file is a derived, additive baseline.
2. In a conflict, the SRS requirement text and permanent requirement ID win; this file records the resolution rather than changing scope.
3. An ID is never renumbered or reused. New requirements discovered later are appended under the owning phase and workstream with the next free ID.
4. No application code, schema, migration, or configuration is created in Phase 1.

---

## 2. Baseline at a glance

| ID family | Count | Included IDs |
|---|---:|---|
| Functional requirements (FR) | 64 | FR-001…FR-064 (50 P0, 7 P1, 7 P2) |
| Non-functional requirements (NFR) | 22 | NFR-001…NFR-022 |
| Business rules (BR) | 20 | BR-01…BR-20 |
| Notification triggers (NT) | 8 | NT-01…NT-08 (7 P0, 1 P1) |
| Acceptance criteria (AC) | 16 | AC-01…AC-16 |
| User stories | 44 | 17 CIT, 8 DEP, 5 SUP, 6 ADM, 3 SYS, 4 P1, 1 E2E |
| RBAC requirements | 8 | RBAC-01…RBAC-08 |
| Escalation timing requirements | 10 | ESC-01…ESC-10 |
| Escalation idempotency requirements | 6 | IDEM-01…IDEM-06 |
| Escalation edge cases | 17 | EC-01…EC-17 |
| SRS database integrity requirements | 10 | DB-01…DB-10 |
| Security and privacy requirements | 16 | SEC-01…SEC-16 |
| System constraints | 10 | CON-01…CON-10 |
| Use cases | 7 | UC-01…UC-07 |
| PRD assumptions | 13 | A-01…A-13 |

**Priority split:** P0 = 50 FRs (mandatory), P1 = 7 FRs (optional, gated to Phase 21), P2 = 7 FRs (future, not built).

**Story split:** `US-CIT-01…17` (17), `US-DEP-01…08` (8), `US-SUP-01…05` (5), `US-ADM-01…06` (6), `US-SYS-01…03` (3), `US-P1-01…04` (4), `US-E2E-01` (1) = **44**.

---

## 3. Canonical glossary and invariants

### 3.1 Canonical roles

| Role (display) | Role code | Scope | Source |
|---|---|---|---|
| Citizen | `CITIZEN` | Own complaints and notifications | SRS §5, PRD §7 |
| Department Officer | `DEPARTMENT_OFFICER` | Exactly one active department | SRS §5, PRD §7 |
| Superintendent Officer | `SUPERINTENDENT_OFFICER` | Escalated complaints; oversight read | SRS §5, PRD §7 |
| Platform Administrator | `PLATFORM_ADMIN` | Configuration, users, audit; read-only complaint detail | SRS §5, PRD §7 |

**Invariants:** exactly one role per account; an officer must have exactly one active department; deactivated users are rejected on the next request even with an unexpired token.

### 3.2 Canonical statuses

`SUBMITTED`, `PENDING_DEPARTMENT_REVIEW`, `ACCEPTED`, `IN_PROGRESS`, `REJECTED`, `ESCALATED`, `RESOLVED`, `REOPENED` (P1).

`REOPENED` is not exercised in P0. No other status value is legal.

### 3.3 Authoritative transition table (SRS §11.1)

| From | To | Actor | Guard | Scope |
|---|---|---|---|---|
| `SUBMITTED` | `PENDING_DEPARTMENT_REVIEW` | System | Routing succeeded | P0 |
| `PENDING_DEPARTMENT_REVIEW` | `ACCEPTED` | Department Officer | Same department; status matches | P0 |
| `PENDING_DEPARTMENT_REVIEW` | `REJECTED` | Department Officer | Same department; reason 10–1,000 | P0 |
| `ACCEPTED` | `IN_PROGRESS` | Department Officer | Progress note 5–2,000 | P0 |
| `ACCEPTED` | `RESOLVED` | Department Officer | Resolution note 10–2,000 | P0 |
| `IN_PROGRESS` | `RESOLVED` | Department Officer | Resolution note 10–2,000 | P0 |
| `ACCEPTED` | `ESCALATED` | System | Deadline reached; no escalation row | P0 |
| `IN_PROGRESS` | `ESCALATED` | System | Deadline reached; no escalation row | P0 |
| `ESCALATED` | `RESOLVED` | Department Officer or Superintendent | Resolution note 10–2,000 | P0 |
| `RESOLVED` | `REOPENED` | System | Reopening accepted | P1 |
| `REOPENED` | `IN_PROGRESS` | Department Officer | New note and new deadline | P1 |

**Illegal transition:** HTTP `409 INVALID_TRANSITION`, no state change. Superintendent write actions are limited to `ESCALATED` complaints; administrative accounts have no operational complaint actions.

### 3.4 SLA and escalation invariants

| Invariant | Canonical value | Sources |
|---|---|---|
| Production window | 10,080 minutes = 604,800 seconds = 7 calendar days (168 hours) | PRD §13, SRS §14.1, TRD §13 |
| Clock start | `accepted_at`, never `submitted_at` | SRS FR-027, BR-05, ESC-01 |
| Deadline | `resolution_due_at = accepted_at + sla_seconds` | SRS §14.1 |
| Deadline boundary | Inclusive: eligible when `now_utc >= resolution_due_at` | SRS ESC-02, EC-11 |
| Per-complaint storage | `sla_seconds` and `resolution_due_at` immutable after acceptance | SRS ESC-06, EC-09 |
| Demo override | Non-default window accepted only with `ALLOW_DEMO_ESCALATION=true`; otherwise refuse to start or fall back to 10,080 with an error log | SRS FR-033, §14.5; TRD §13 |
| Escalation cardinality | At most one escalation row per complaint for its lifetime; `escalations.complaint_id` is unique | SRS FR-029, IDEM-01 |
| Concurrency | DB advisory lock plus conditional status update and candidate exclusion | SRS IDEM-03…IDEM-05 |
| Sticky status | `ESCALATED` remains until `RESOLVED`; departmental progress does not revert it | SRS ESC-09, EC-14 |

### 3.5 Tracking number

- Format: `^CT-[0-9]{4}-[0-9]{6}$` (example `CT-2026-000042`).
- Unique per complaint; returned in every complaint representation.
- Generated under a uniqueness constraint with retry on collision.
- Domain term is **tracking number**; the persisted column is `complaints.complaint_number`.

### 3.6 Pagination

- Default **20** items per page; maximum **100**.
- Response envelope: `{items, page, page_size, total, total_pages}`.
- Applies to citizen complaints, department queue, notifications, audit logs, and other list endpoints.

### 3.7 Session and time

- JWT HS256, **8-hour** expiry, secret **≥32 bytes**, stored in `sessionStorage` as `civictrack.token`, sent as `Authorization: Bearer`.
- All persisted timestamps are UTC `DATETIME(6)` (microsecond precision); display uses `APP_TIMEZONE`.
- Malformed, expired, or inactive-user tokens return 401; authorization failures return 403.

### 3.8 Upload invariants

- JPEG, PNG, or WebP only; magic-byte validation; maximum **5 MiB** per file.
- Maximum **3** images per submission/request; maximum **10** images per complaint lifetime.
- Randomized storage names under `UPLOAD_DIR`; private streaming through an authorized endpoint only.

### 3.9 Terminology reconciliation (DOC-009)

| Concept | Canonical term | Canonical code/format | Permitted variants | Resolution |
|---|---|---|---|---|
| Reported issue | **Complaint** | `complaints` | “ticket” appears only as a terminology task in `PHASES.md`/tracker, never as a domain object | Use “complaint”; no rename needed |
| Citizen | **Citizen** | `CITIZEN` | “resident” in story prose | Role code is authoritative |
| Department officer | **Department Officer** | `DEPARTMENT_OFFICER` | “officer”, “dept officer” in prose | Role code is authoritative |
| Superintendent | **Superintendent Officer** | `SUPERINTENDENT_OFFICER` | “Superintendent”, “supervisor” in prose | Role code is authoritative |
| Administrator | **Platform Administrator** | `PLATFORM_ADMIN` | “Administrator”, “Platform Admin” | Role code is authoritative |
| Issue reference | **Tracking number** | `^CT-[0-9]{4}-[0-9]{6}$` | “tracking ID”, DB column `complaint_number` | Display “tracking number”; column name is an implementation detail |
| Resolution window | **Escalation window / SLA window** | `ESCALATION_WINDOW_MINUTES`, per-complaint `sla_seconds` | “resolution window”, “deadline window” | Config variable plus stored `sla_seconds` |

No unresolved terminology conflict remains.

---

## 4. Requirement inventory

> **Inventory rule:** every SRS requirement ID is a primary key in exactly one row below. Cross-references inside matrix columns are expected and are not duplicate inventory keys. IDs are listed explicitly, not only as ranges.

### 4.1 Functional requirements (64)

| ID | Priority | Feature area | Requirement (verbatim SRS §7) | Test group | Delivery phase |
|---|---|---|---|---|---|
| FR-001 | P0 | Authentication and Access Control | The system **shall** allow an unauthenticated visitor to register a Citizen account with full name (2–120 characters), valid unique email (case-insensitive, ≤190 characters), password (8–72 characters containing at least one letter and one digit), and optional phone (7–20 characters from digits, `+`, spaces, `-`). On success it shall create an active user with role `CITIZEN` and return HTTP 201 with a JWT and the public user object. | T-AUTH | 6 |
| FR-002 | P0 | Authentication and Access Control | The system **shall** authenticate an active user by email and password, return a signed JWT valid for 8 hours, and return HTTP 401 with the generic message `Invalid email or password` for invalid credentials or an inactive account. Logout **shall** return HTTP 204 and require the client to discard the token. | T-AUTH | 6 |
| FR-003 | P0 | Authentication and Access Control | The system **shall** store only a bcrypt hash (cost ≥ 12) of each password, **shall not** return or log password fields, and **shall** verify credentials using a constant-time comparison. | T-AUTH | 6 |
| FR-004 | P0 | Authentication and Access Control | The system **shall** enforce role-based authorization on every protected API operation and every client route. A request whose authenticated role lacks permission **shall** return HTTP 403 and **shall not** change state. | T-RBAC | 6 |
| FR-005 | P0 | Authentication and Access Control | The system **shall** allow an authenticated user to retrieve their own profile: full name, email, phone, role code, active flag, and department name when applicable. It **shall not** expose password hashes or other users' PII. | T-AUTH | 6 |
| FR-006 | P0 | Authentication and Access Control | The system **shall** allow a Platform Administrator to list users; create Department Officer or Platform Administrator accounts with a unique email, role, and exactly one active department for Department Officers; change a user's role; activate or deactivate an account. It **shall** prevent deactivating or demoting the last active Platform Administrator. | T-ADMIN | 6 |
| FR-007 | P0 | Complaint Submission and Citizen Tracking | The system **shall** return the active category catalogue (id, name, code, mapped department id and name) to any authenticated user. | T-COMP | 8 |
| FR-008 | P0 | Complaint Submission and Citizen Tracking | The system **shall** create a complaint from a title (5–150 characters), description (20–2,000 characters), active category id, optional location text (≤255 characters), optional latitude and longitude, and zero to three images, associating it with the authenticated Citizen. | T-COMP | 8 |
| FR-009 | P0 | Complaint Submission and Citizen Tracking | The system **shall** assign each complaint a unique tracking number matching `^CT-[0-9]{4}-[0-9]{6}$` and **shall** return it in every complaint representation. | T-COMP | 8 |
| FR-010 | P0 | Complaint Submission and Citizen Tracking | The system **shall** accept only JPEG, PNG, or WebP images, maximum 5 MiB each and maximum three per submission; it **shall** verify file signatures, store files under randomized names, and reject invalid uploads with HTTP 422 **without** creating a complaint or partial image rows. | T-UPLOAD | 8 |
| FR-011 | P0 | Complaint Submission and Citizen Tracking | The system **shall** accept optional free-text location and optional coordinates. If either coordinate is supplied, both **shall** be required and **shall** satisfy latitude −90 to 90 and longitude −180 to 180; invalid combinations **shall** return HTTP 422. | T-COMP | 8 |
| FR-012 | P0 | Complaint Submission and Citizen Tracking | The system **shall** route every complaint at submission to exactly one active department using the category's current mapping. A category that is inactive or has no mapped department **shall** be rejected with HTTP 422, and no complaint **shall** be persisted. | T-COMP | 8 |
| FR-013 | P0 | Complaint Submission and Citizen Tracking | Within the submission transaction, the system **shall** persist status `SUBMITTED`, then `PENDING_DEPARTMENT_REVIEW`, and **shall** append two status-history rows: `null → SUBMITTED` attributed to the Citizen and `SUBMITTED → PENDING_DEPARTMENT_REVIEW` attributed to `SYSTEM`. | T-COMP | 8 |
| FR-014 | P0 | Complaint Submission and Citizen Tracking | The system **shall** list only the authenticated Citizen's complaints, newest first, paginated at 20 per page, filterable by status and category. | T-COMP | 9 |
| FR-015 | P0 | Complaint Submission and Citizen Tracking | The system **shall** return complaint details to its owner, including tracking number, title, description, category, department, status, submitted time, acceptance time, deadline, resolution time, location, images, and resolution summary when present. | T-COMP | 9 |
| FR-016 | P0 | Complaint Submission and Citizen Tracking | The system **shall** return a complaint timeline ordered by event timestamp ascending and then event id ascending, containing status changes, progress notes, supervisory actions, escalation events, and image additions, filtered by the viewer's visibility permissions. | T-COMP | 9 |
| FR-017 | P0 | Department Review, Progress, and Resolution | The system **shall** provide a Department Officer with a review queue limited to their assigned department, newest first, paginated at 20, filterable by status, category, and assignee, with per-status counts. | T-DEPT | 10 |
| FR-018 | P0 | Department Review, Progress, and Resolution | The system **shall** allow a Department Officer to read a complaint only when it exists and its `department_id` equals the officer's department. An existing complaint in another department **shall** return HTTP 403; an unknown id **shall** return HTTP 404. | T-RBAC | 10 |
| FR-019 | P0 | Department Review, Progress, and Resolution | The system **shall** allow a Department Officer of the assigned department to accept a complaint only while its status is `PENDING_DEPARTMENT_REVIEW`. In one transaction it **shall** set status `ACCEPTED`, `accepted_at` to the current UTC time, `accepted_by_user_id`, `sla_seconds` to the configured window, `resolution_due_at = accepted_at + sla_seconds`, append a history row, and create the citizen acceptance notification (NT-02). | T-DEPT, T-ESC | 10 |
| FR-020 | P0 | Department Review, Progress, and Resolution | The system **shall** allow a Department Officer of the assigned department to reject a `PENDING_DEPARTMENT_REVIEW` complaint only with a reason of 10–1,000 characters. It **shall** set status `REJECTED`, record `rejected_at`, `rejected_by_user_id`, and `rejection_reason`, append history, create the citizen rejection notification (NT-03), and treat rejection as terminal in P0. | T-DEPT | 10 |
| FR-021 | P0 | Department Review, Progress, and Resolution | The system **shall** allow an officer of the assigned department to assign a complaint to an active user of the same department, recording `assigned_to_user_id` and `assigned_at`. Assignment alone **shall not** change status or notify the citizen. | T-DEPT | 10 |
| FR-022 | P0 | Department Review, Progress, and Resolution | The system **shall** allow an officer of the assigned department to add a progress note (5–2,000 characters) to an `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` complaint, optionally transitioning `ACCEPTED → IN_PROGRESS`. Each change **shall** record actor and timestamp, append history when the status changes, and create the citizen progress notification (NT-04). | T-DEPT | 10 |
| FR-023 | P0 | Department Review, Progress, and Resolution | The system **shall** allow an officer of the assigned department to attach 1–3 JPEG/PNG/WebP images (≤5 MiB each, maximum 10 per complaint) as `PROGRESS` or `RESOLUTION` evidence while the status is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED`, storing uploader and timestamp. | T-UPLOAD | 10 |
| FR-024 | P0 | Department Review, Progress, and Resolution | The system **shall** allow an officer of the assigned department to resolve a complaint from `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` with a resolution note (10–2,000 characters). It **shall** set status `RESOLVED`, `resolved_at`, `resolved_by_user_id`, and `resolution_note`, append history, and create the citizen resolution notification (NT-07). Resolution from any other status **shall** return HTTP 409. | T-DEPT, T-SUP | 10 |
| FR-025 | P0 | Department Review, Progress, and Resolution | The system **shall** provide a Department Officer with a summary of their department's complaints counted by status and escalation state. | T-DEPT | 10 |
| FR-026 | P0 | Department Review, Progress, and Resolution | The system **shall** allow an officer of the assigned department to add progress notes and evidence to an `ESCALATED` complaint without changing its status; such updates **shall** create NT-04 and remain visible to the Superintendent. | T-DEPT | 10 |
| FR-027 | P0 | Automatic Escalation | At acceptance the system **shall** compute `resolution_due_at` as `accepted_at + sla_seconds`, where `sla_seconds` is the configured escalation window at that moment. It **shall never** compute the deadline from `submitted_at`. | T-ESC | 10 |
| FR-028 | P0 | Automatic Escalation | The system **shall** run an automatic escalation check at startup and then at a configurable interval (default 60 seconds) without any human action. | T-ESC | 11 |
| FR-029 | P0 | Automatic Escalation | The system **shall** create at most one escalation record per complaint for the lifetime of the complaint, including under repeated runs, retries, manual triggers, and concurrent worker instances. | T-ESC | 11 |
| FR-030 | P0 | Automatic Escalation | When a candidate satisfies all escalation conditions, the system **shall** change its status to `ESCALATED`, set `escalated_at`, and append a history row with actor `SYSTEM`, previous status, new status, and reason `SLA_BREACH`. | T-ESC | 11 |
| FR-031 | P0 | Automatic Escalation | The system **shall** create an escalation record containing `complaint_id` (unique), `escalation_number`, `previous_status`, `deadline_at`, `escalated_at`, `overdue_seconds`, `trigger_source`, and `reason_code`. | T-ESC | 11 |
| FR-032 | P0 | Automatic Escalation | In the same transaction as escalation, the system **shall** create NT-05 notifications for every active Superintendent, every active officer of the responsible department, and the complaint's Citizen. | T-ESC, T-NOTIF | 11 |
| FR-033 | P0 | Automatic Escalation | The system **shall** read the escalation window from configuration with a production default of 10,080 minutes (seven calendar days). A non-default window **shall** be accepted only when `ALLOW_DEMO_ESCALATION=true`; otherwise the system **shall** refuse to start or fall back to 10,080 minutes and log an error. | T-ESC | 11 |
| FR-034 | P0 | Automatic Escalation | The system **shall** expose a token-protected internal endpoint that executes the same escalation function on demand for demonstration and tests, returning `{evaluated, escalated, skipped}` and creating no duplicates. | T-ESC | 11 |
| FR-035 | P0 | Superintendent Oversight | The system **shall** provide a Superintendent queue of `ESCALATED` complaints sorted by overdue duration descending, showing tracking number, department, acceptance time, deadline, overdue duration, and current status. | T-SUP | 12 |
| FR-036 | P0 | Superintendent Oversight | The system **shall** show the Superintendent the complaint detail, responsible department, acceptance date, deadline, overdue duration computed at request time, and resolution information when present. | T-SUP | 12 |
| FR-037 | P0 | Superintendent Oversight | The system **shall** allow the Superintendent to read the complete timeline, progress notes, and evidence of escalated complaints. Read access to other complaints for oversight is permitted; operational actions remain restricted to escalated complaints, including their resolution. | T-SUP | 12 |
| FR-038 | P0 | Superintendent Oversight | The system **shall** allow the Superintendent to record an append-only action of type `INSTRUCTION`, `FOLLOW_UP`, `REASSIGN`, or `NOTE`, with a note of 5–2,000 characters, optional `directed_department_id`, actor identity, and UTC timestamp; the action **shall** appear in the timeline and create NT-06 for the department and citizen. | T-SUP | 12 |
| FR-039 | P0 | Superintendent Oversight | The system **shall** support directing a follow-up to the responsible department by recording `directed_department_id` and notifying that department. In P0 this is a directive; it **shall not** silently change the complaint's original `department_id`. | T-SUP | 12 |
| FR-040 | P0 | Superintendent Oversight | The system **shall** keep escalated complaints in the Superintendent queue and allow monitoring of subsequent departmental updates until the complaint becomes `RESOLVED`. | T-SUP | 12 |
| FR-041 | P0 | Superintendent Oversight | The system **shall** allow the Superintendent to resolve an `ESCALATED` complaint using the same resolution rules and notification as FR-024, recording the Superintendent as the resolving actor. | T-SUP | 12 |
| FR-042 | P0 | In-App Notifications | The system **shall** create notification rows for triggers NT-01 through NT-07 inside the same database transaction as the triggering state change, so a committed status change cannot lack its notification records. | T-NOTIF | 7 |
| FR-043 | P0 | In-App Notifications | The system **shall** list only the authenticated user's notifications, newest first, paginated at 20, and **shall** return an unread count. | T-NOTIF | 7 |
| FR-044 | P0 | In-App Notifications | The system **shall** allow a user to mark one or all of their own notifications as read, idempotently, recording `read_at`; marking another user's notification **shall** return HTTP 404 (not 403, to avoid disclosure). | T-NOTIF | 7 |
| FR-045 | P0 | In-App Notifications | Notification content **shall** include the complaint tracking number and resulting status, plus trigger-specific fields: department and target date for NT-02, rejection reason for NT-03, progress note for NT-04, overdue duration for NT-05, action summary for NT-06, and resolution note for NT-07. | T-NOTIF | 7 |
| FR-046 | P0 | Administration and Configuration | The system **shall** allow a Platform Administrator to create, update, list, and deactivate departments. Deactivation **shall** be blocked while active categories or active Department Officers reference the department. | T-ADMIN | 13 |
| FR-047 | P0 | Administration and Configuration | The system **shall** allow a Platform Administrator to create, update, list, and deactivate complaint categories and to change the mapped department. A mapping **shall** reference an active department, and changes **shall** affect only complaints submitted afterwards. | T-ADMIN | 13 |
| FR-048 | P0 | Administration and Configuration | The system **shall** provide a Platform Administrator with activity counts by complaint status and department, the number of escalations, and the 20 most recent timeline events across the platform. | T-ADMIN | 13 |
| FR-049 | P0 | Administration and Configuration | The system **shall** allow a Platform Administrator to read audit logs filtered by actor, action, entity type, and date range. The audit log **shall** be read-only through the API; no update or delete operation **shall** be exposed. | T-ADMIN | 13 |
| FR-050 | P0 | Audit Trail | The system **shall** append a status-history row for every status change, containing `complaint_id`, `from_status`, `to_status`, `actor_user_id` or null for system, `actor_role`, optional note, and a UTC timestamp. History rows **shall** never be updated or deleted through the API. | T-ESC, T-DEPT, T-SUP | 8–12 |
| FR-051 | P1 | AI Category and Priority Suggestions | The system **should** request a category suggestion from the Gemini API using the complaint title and description, display it with a confidence label, require explicit confirmation, and fall back to manual selection within 5 seconds on any error. | T-P1 | 21 (P1) |
| FR-052 | P1 | Duplicate Detection | The system **should** show up to three same-category complaints within 500 metres and seven days of a new complaint as possible duplicates. The citizen **should** be able to submit anyway; no automatic merge **should** occur. | T-P1 | 21 (P1) |
| FR-053 | P1 | Issue Map | The system **should** display a Leaflet/OpenStreetMap view of complaints with coordinates, restricted to the viewer's permitted scope, with marker popups linking to complaint detail. | T-P1 | 21 (P1) |
| FR-054 | P1 | AI Category and Priority Suggestions | The system **should** suggest a priority (`LOW`, `MEDIUM`, `HIGH`) from the complaint text, require officer confirmation, and never block submission or routing on the suggestion. | T-P1 | 21 (P1) |
| FR-055 | P1 | Analytics Dashboard | The system **should** provide an Administrator analytics view of complaint counts by status, department, category, and age using Recharts. | T-P1 | 21 (P1) |
| FR-056 | P1 | Citizen Feedback and Reopening | The system **should** allow a Citizen to submit a rating (1–5) and optional comment (≤1,000 characters) for a `RESOLVED` complaint, once per complaint. | T-P1 | 21 (P1) |
| FR-057 | P1 | Citizen Feedback and Reopening | The system **should** allow a Citizen to request reopening of a `RESOLVED` complaint with a reason; a Department Officer **should** accept or decline. Acceptance **should** set `REOPENED` and, on re-acceptance, a new deadline. | T-P1 | 21 (P1) |
| FR-058 | P2 | Future Work (P2) | The system may add email, SMS, WhatsApp, or push notification adapters through an outbox pattern. | Not built | Not built (P2) |
| FR-059 | P2 | Future Work (P2) | The system may support multiple municipalities with tenant isolation. | Not built | Not built (P2) |
| FR-060 | P2 | Future Work (P2) | The system may support working-day, holiday, and paused SLA calendars. | Not built | Not built (P2) |
| FR-061 | P2 | Future Work (P2) | The system may verify or classify evidence images automatically. | Not built | Not built (P2) |
| FR-062 | P2 | Future Work (P2) | The system may expose a privacy-reviewed public transparency portal. | Not built | Not built (P2) |
| FR-063 | P2 | Future Work (P2) | The system may provide native mobile applications. | Not built | Not built (P2) |
| FR-064 | P2 | Future Work (P2) | The system may integrate with external municipal work-order systems. | Not built | Not built (P2) |

### 4.2 Non-functional requirements (22)

| ID | Category | Requirement (verbatim SRS §8) | Measurable target / verification | Tracker verification | Delivery phase |
|---|---|---|---|---|---|
| NFR-001 | Performance | List endpoints **shall** respond within 1 second p95 and detail endpoints within 2 seconds p95 at demo volume (500 complaints, 50 concurrent users) | Load test at Hour 9; T-PERF | TEST-054 | 18 |
| NFR-002 | Timeliness | The escalation worker **shall** detect a due complaint within one scheduler interval (default ≤60 seconds) of its deadline | Integration test with 2-minute window; T-ESC | TEST-019, TEST-020 | 11, 17 |
| NFR-003 | Concurrency | Concurrent escalation runs **shall** produce exactly one escalation record and one `ESCALATED` transition per complaint | 20-run and parallel-run test; T-ESC | TEST-020, TEST-021 | 11, 17 |
| NFR-004 | Credential security | Passwords **shall** be hashed with bcrypt cost ≥12 and never persisted, returned, or logged in plaintext | Code review + test; T-AUTH | TEST-001 | 6 |
| NFR-005 | Authorization | 100% of protected API operations **shall** enforce role and object-scope checks server-side; UI hiding alone is insufficient | 12-case RBAC matrix; T-RBAC | TEST-003, TEST-050 | 6, 18 |
| NFR-006 | Session security | JWTs **shall** expire after 8 hours, be signed with a secret of at least 32 bytes, and be rejected when malformed, expired, or belonging to an inactive user | T-AUTH | TEST-001 | 6 |
| NFR-007 | Privacy | Email, phone, location text, and coordinates **shall** be readable only by the owner, officers of the responsible department, the Superintendent, and Administrators | Field-level tests; T-RBAC | TEST-012, TEST-050 | 6, 9, 18 |
| NFR-008 | Audit immutability | Status history, escalations, officer actions, and audit logs **shall** be append-only through the API | Attempt update/delete; T-ADMIN | TEST-029 | 13, 17 |
| NFR-009 | Time handling | All timestamps **shall** be stored in UTC with microsecond precision and displayed in `APP_TIMEZONE` | Boundary tests; T-ESC | TEST-019, TEST-039 | 5, 11 |
| NFR-010 | Usability | The complaint form **shall** be usable at 360 px width, expose at most five required inputs, and allow a first-time user to submit in ≤60 seconds | Timed usability run; T-E2E | TEST-033 | 15, 17 |
| NFR-011 | Reliability | A scheduler failure **shall** not lose data; the next successful run **shall** escalate all overdue complaints; records **shall** survive container restarts | Restart test; T-ESC | TEST-022, DEP-013 | 11, 19 |
| NFR-012 | Transactional integrity | Complaint creation, acceptance, escalation, resolution, and their notifications **shall** be atomic; a failure **shall** roll back all writes in the unit of work | Fault-injection test; T-ESC | TEST-006, TEST-008, TEST-017 | 7, 8, 10, 11 |
| NFR-013 | Upload safety | Uploads **shall** be limited to 5 MiB and three files per request, validated by magic bytes, stored with random names, and served only through an authorized endpoint | T-UPLOAD | TEST-009, TEST-051 | 8, 18 |
| NFR-014 | Compatibility | The UI **shall** function on the latest two major versions of Chrome, Edge, Firefox, and Safari | Manual matrix; T-E2E | TEST-046 | 17 |
| NFR-015 | Accessibility | Forms **shall** have associated labels, keyboard-operable controls, visible focus, and text contrast ≥4.5:1 | Manual audit; T-E2E | TEST-032, TEST-045, TEST-056 | 14, 18 |
| NFR-016 | Maintainability | TypeScript strict mode, ESLint, Python `ruff`, typed Pydantic schemas, and `.env.example` **shall** be present | Review at Hour 9 | DEP-001, DOC-030 | 3, 20 |
| NFR-017 | Portability | After the documented `.env` setup, `docker compose up` **shall** start database, API, worker, and web with one command on a clean machine | Fresh-clone test | DEP-012 | 3, 19 |
| NFR-018 | Observability | Every escalation run **shall** log evaluated, escalated, skipped, duration, and errors; `/health` and `/health/ready` **shall** report API and database status, and worker liveness **shall** be visible through its container status and structured logs | Log inspection; T-ESC | BE-012, BE-077, DEP-011 | 5, 11, 19 |
| NFR-019 | Retention | Complaints, history, escalations, actions, and audit logs **shall** not be hard-deleted; users and configuration use deactivation | API surface review | DB-023, TEST-029 | 4, 13 |
| NFR-020 | Testability | Deadline calculation, routing, idempotency, and RBAC **shall** have automated unit/integration tests; the critical lifecycle **shall** have an end-to-end test | Test run at Hour 9 | TEST-039–TEST-049 | 17 |
| NFR-021 | Log hygiene | Passwords, tokens, emails, phone numbers, location text, and coordinates **shall** not appear in application logs or URLs | Log review | TEST-052 | 5, 18 |
| NFR-022 | Capacity | The system **shall** support 500 complaints, 100 users, and 50 concurrent demo users with 2 GB image storage | Seeded-volume test | TEST-057 | 18, 19 |

### 4.3 Business rules (20)

| ID | Rule (verbatim SRS §11) | Enforced by |
|---|---|---|
| BR-01 | Every complaint has a unique tracking number and internal ID. | Unique DB constraint; FR-009 |
| BR-02 | Every complaint belongs to exactly one Citizen account. | Non-null FK; FR-008 |
| BR-03 | Every complaint is routed at submission to exactly one active department. | Non-null FK; FR-012 |
| BR-04 | Only an authorized officer of the assigned department may accept or reject. | Role + department checks; FR-004, FR-018, FR-019, FR-020 |
| BR-05 | The resolution clock starts at acceptance, never at submission. | FR-027; service-level invariant |
| BR-06 | Seven days means 168 hours / 10,080 minutes, not working days. | Configuration default; FR-033 |
| BR-07 | An unresolved accepted complaint past its deadline must be escalated automatically. | FR-028–FR-030 |
| BR-08 | Escalation happens at most once per complaint in P0. | Unique index; FR-029 |
| BR-09 | The Superintendent can view the full history of escalated complaints. | FR-037 |
| BR-10 | Every status change records actor (or `SYSTEM`), timestamp, previous and new status. | FR-050 |
| BR-11 | Only a Department Officer or the Superintendent may resolve. | FR-024, FR-041 |
| BR-12 | Submission does not verify the issue; UI must not claim verification. | Copy review; FR-008, FR-015 |
| BR-13 | Rejection requires a recorded reason shown to the citizen. | FR-020, FR-045 |
| BR-14 | Citizens receive notifications for submission, acceptance, rejection, progress, escalation, and resolution. | FR-042 |
| BR-15 | PII and precise location are restricted to authorized roles and never exposed publicly. | FR-004, NFR-007 |
| BR-16 | Only transitions in §11.1 are legal; others return 409 and change nothing. | State machine; §11.1 |
| BR-17 | Resolution requires a note and an authorized actor; evidence is optional. | FR-024 |
| BR-18 | Escalation preserves the original department and allows continued departmental updates. | FR-026, FR-039 |
| BR-19 | The production window is 10,080 minutes; demo overrides are explicit and guarded. | FR-033 |
| BR-20 | The system never infers `RESOLVED` from silence or elapsed time. | FR-024, FR-041; no other writer |

### 4.4 Notification triggers (8)

| ID | Trigger | Recipients | Required content | Timing | FR | Priority |
|---|---|---|---|---|---|---|
| NT-01 | Complaint submitted | Citizen | Tracking number, category, department, submitted time | Same transaction as submission | FR-042 | P0 |
| NT-02 | Complaint accepted | Citizen | Tracking number, department name, accepting officer, acceptance time, deadline | Same transaction as acceptance | FR-019, FR-042 | P0 |
| NT-03 | Complaint rejected | Citizen | Tracking number, department, rejection reason | Same transaction as rejection | FR-020, FR-042 | P0 |
| NT-04 | Progress update or status change | Citizen | Tracking number, new status, progress note | Same transaction as update | FR-022, FR-026 | P0 |
| NT-05 | Automatic escalation | Every active Superintendent, every active officer of the responsible department, Citizen | Tracking number, department, deadline, overdue duration, escalation time | Same transaction as escalation | FR-032 | P0 |
| NT-06 | Supervisory action recorded | Officers of the responsible department, Citizen | Tracking number, action type, note summary, Superintendent identity, timestamp | Same transaction as action | FR-038 | P0 |
| NT-07 | Complaint resolved | Citizen | Tracking number, resolution note, resolving officer, resolution time | Same transaction as resolution | FR-024, FR-041 | P0 |
| NT-08 | Reopening accepted (P1) | Department officers, Citizen | Tracking number, reopened status, reason | Same transaction as reopening | FR-057 | P1 |

### 4.5 Acceptance criteria (16) and reproducible test steps

| ID | Criterion (verbatim SRS §19) | Requirements | Reproducible verification steps | Evidence |
|---|---|---|---|---|
| AC-01 | A new Citizen can register, log in, and view their own profile. | FR-001–FR-005 | 1) Register with a unique email and a 12-character password containing a letter and a digit. 2) Assert HTTP 201, a JWT, and role `CITIZEN`. 3) Log in and call `GET /auth/me`. 4) Assert own profile fields and no password hash. | T-AUTH, T-E2E |
| AC-02 | A Citizen can submit a complaint with title, description, active category, optional images, and optional location, and receives a unique tracking number. | FR-007–FR-013 | 1) Log in as a Citizen and read `GET /categories`; choose an active category. 2) Submit multipart `POST /complaints` with title 5–150, description 20–2,000, category, a 1-byte-valid JPEG ≤5 MiB, and location text. 3) Assert HTTP 201, tracking number matches the regex, status `PENDING_DEPARTMENT_REVIEW`, one image row, and the mapped department. | T-COMP, T-E2E |
| AC-03 | The complaint appears only in the mapped department's queue and in the owning Citizen's list; another department and another citizen cannot see it. | FR-012, FR-014, FR-018, FR-004 | 1) Seed departments A and B, one officer each, and two citizens. 2) Submit a complaint mapped to A. 3) Assert it appears in A's queue and not B's. 4) Assert officer B gets 403 on detail and the other citizen gets 404 and no list entry. | T-RBAC, T-COMP |
| AC-04 | A Department Officer accepts the complaint; `accepted_at` is recorded; the Citizen receives NT-02 with the department and target date; the deadline equals acceptance plus the configured window. | FR-019, FR-027, FR-042 | 1) Accept the complaint as officer A with `POST /complaints/{id}/accept`. 2) Assert `ACCEPTED`, non-null `accepted_at`, and `resolution_due_at − accepted_at = sla_seconds`. 3) Assert an NT-02 row for the Citizen containing department and target date. | T-DEPT, T-NOTIF |
| AC-05 | A Department Officer rejects a different complaint with a reason; the Citizen receives NT-03 containing that reason; no deadline exists. | FR-020, FR-045 | 1) Submit a second complaint to department A. 2) Reject with `POST /complaints/{id}/reject` and a 10–1,000 character reason. 3) Assert `REJECTED`, rejection fields stored, `resolution_due_at` null, and NT-03 body contains the reason. | T-DEPT, T-NOTIF |
| AC-06 | Department progress updates appear in the Citizen timeline with status, note, actor, and timestamp. | FR-016, FR-022, FR-050 | 1) Accept the complaint, then post a 5–2,000 character progress note with `ACCEPTED → IN_PROGRESS`. 2) Read `GET /complaints/{id}/timeline`. 3) Assert the entry contains status, note, actor, and UTC timestamp, ordered ascending by timestamp then id. | T-COMP, T-DEPT |
| AC-07 | An accepted complaint past its deadline is escalated automatically without human action, and the status becomes `ESCALATED`. | FR-028–FR-031 | 1) Accept with `ESCALATION_WINDOW_MINUTES=2` and `ALLOW_DEMO_ESCALATION=true`. 2) Advance past the deadline or call `POST /internal/escalations/run`. 3) Assert `ESCALATED`, exactly one `escalations` row, a `SYSTEM/SLA_BREACH` history row, and NT-05 recipients. | T-ESC |
| AC-08 | Repeating the escalation check 20 times produces exactly one escalation row and one escalation transition. | FR-029, NFR-003 | 1) Prepare one overdue accepted complaint. 2) Call the escalation function/endpoint 20 times. 3) Assert one `escalations` row, one `ESCALATED` transition, and subsequent runs report skipped. | T-ESC |
| AC-09 | The Superintendent sees the escalated complaint with department, acceptance time, deadline, overdue duration, and full timeline. | FR-035–FR-037 | 1) Log in as Superintendent and call `GET /superintendent/escalations`. 2) Assert the complaint is listed with department, acceptance time, deadline, `overdue_seconds > 0`, sorted descending. 3) Read detail/timeline and assert full history. | T-SUP |
| AC-10 | The Superintendent records an instruction; it appears in the timeline with officer identity and timestamp, and the department and Citizen receive NT-06. | FR-038, FR-045, FR-050 | 1) Post `POST /complaints/{id}/superintendent-actions` with `INSTRUCTION` and a 5–2,000 character note. 2) Assert one append-only `officer_actions` row and a timeline entry with Superintendent identity and timestamp. 3) Assert NT-06 rows for department officers and the Citizen. | T-SUP, T-NOTIF |
| AC-11 | An authorized officer resolves the escalated complaint with a note; the Citizen receives NT-07; the complaint leaves the escalation queue. | FR-024, FR-041, FR-042 | 1) Resolve the escalated complaint as an officer or the Superintendent with a 10–2,000 character note. 2) Assert `RESOLVED`, resolution actor/time/note, a history row, and NT-07 for the Citizen. 3) Assert it is absent from the escalation queue. | T-SUP, T-DEPT, T-NOTIF |
| AC-12 | A complaint is never displayed as resolved without a recorded resolution row and status history. | FR-024, BR-20 | 1) Resolve a complaint and read its detail. 2) Assert `RESOLVED` appears only with `resolved_at`, `resolved_by_user_id`, `resolution_note`, and a matching status-history row. 3) Attempt resolution without a note and assert 422; assert no API route writes status directly. | T-DEPT, T-SUP |
| AC-13 | A Citizen receives 403 on department and Superintendent endpoints and sees no department navigation. | FR-004, RBAC-01–RBAC-08 | 1) Log in as a Citizen. 2) Call `GET /department/complaints` and `GET /superintendent/escalations`. 3) Assert 403 on both. 4) Assert no department/superintendent navigation and a direct URL renders `/forbidden`. | T-RBAC |
| AC-14 | A Department Officer cannot read or act on another department's complaint (403). | FR-018, RBAC-02 | 1) As officer B, read and mutate a department-A complaint (accept, reject, assign, progress, upload, resolve). 2) Assert 403 on every operation and no state change. 3) Assert an unknown id returns 404. | T-RBAC |
| AC-15 | Notifications are owner-only, show unread counts, and can be marked read. | FR-043, FR-044 | 1) Trigger notifications for Citizen A and create Citizen B. 2) As A, list notifications and unread count; mark one and all read; repeat. 3) Assert owner-only rows, `read_at` set, idempotent repeats, and 404 when B marks A's notification. | T-NOTIF |
| AC-16 | The production default window is 10,080 minutes and a shortened demo window is visibly labeled and guarded by `ALLOW_DEMO_ESCALATION`. | FR-033, FR-034 | 1) Start with default configuration and read `GET /internal/escalation-status`; assert effective window 10,080 minutes and demo mode false. 2) Set a 2-minute window without `ALLOW_DEMO_ESCALATION`; assert startup refusal or fallback to 10,080 with an error log. 3) Set `ALLOW_DEMO_ESCALATION=true`; assert 2 minutes accepted and visibly labeled in logs/UI. | T-ESC, T-ADMIN |

### 4.6 RBAC requirements (8)

| ID | Requirement (verbatim SRS §12.2) | Owner phase |
|---|---|---|
| RBAC-01 | Every protected endpoint **shall** declare its allowed roles and enforce them server-side. | 6 |
| RBAC-02 | Department Officers **shall** be scoped by `department_id` on every read and write; client-supplied department ids **shall** be ignored or rejected. | 6 |
| RBAC-03 | Citizens **shall** never receive another user's PII, coordinates, notifications, or complaint details. | 6 |
| RBAC-04 | Administrators **shall not** inherit operational accept/reject/progress/resolve permissions. | 6 |
| RBAC-05 | The Superintendent **shall** perform write actions only on `ESCALATED` complaints; reading other complaints for oversight is permitted. | 6 |
| RBAC-06 | Deactivated users **shall** be rejected on the next request even if their JWT has not expired. | 6 |
| RBAC-07 | UI route guards **shall** be advisory only; API enforcement is authoritative. | 6 |
| RBAC-08 | Denied attempts **shall** produce an audit entry with actor, route, method, and timestamp. | 6 |

### 4.7 Escalation timing requirements (10)

| ID | Requirement (verbatim SRS §14.2) | Owner phase |
|---|---|---|
| ESC-01 | The timer starts at `accepted_at`, recorded in UTC, and never at `submitted_at`. | 11 |
| ESC-02 | The deadline is inclusive: at `now == resolution_due_at`, the complaint is eligible for escalation. | 11 |
| ESC-03 | Calendar days are consecutive 24-hour periods; weekends and holidays count. | 11 |
| ESC-04 | The check runs at startup and every `ESCALATION_CHECK_SECONDS` (default 60). | 11 |
| ESC-05 | A scheduler outage delays but does not cancel escalation; the next successful run escalates every due complaint and records actual `escalated_at` and computed `overdue_seconds`. | 11 |
| ESC-06 | Changing the configured window affects only complaints accepted after the change; stored `sla_seconds` and `resolution_due_at` are immutable after acceptance. | 11 |
| ESC-07 | A complaint resolved before the escalation transaction commits is not escalated, even if the scheduler run started earlier. | 11 |
| ESC-08 | Escalation does not alter `department_id`, `accepted_at`, `accepted_by_user_id`, or the original deadline. | 11 |
| ESC-09 | The escalation status is sticky until `RESOLVED`; departmental progress does not revert it. | 11 |
| ESC-10 | There is no re-escalation in P0; a second escalation requires a future authorized workflow and schema change. | 11 |

### 4.8 Escalation idempotency requirements (6)

| ID | Requirement (verbatim SRS §14.3) | Owner phase |
|---|---|---|
| IDEM-01 | `escalations.complaint_id` **shall** have a unique constraint. | 11 |
| IDEM-02 | The status update **shall** be conditional on the current status being `ACCEPTED` or `IN_PROGRESS`. | 11 |
| IDEM-03 | The worker **shall** hold a database advisory lock (for example `GET_LOCK`) so that only one scheduler instance processes candidates at a time. | 11 |
| IDEM-04 | Candidate selection **shall** exclude complaints that already have an escalation row. | 11 |
| IDEM-05 | Duplicate-key or zero-row-update outcomes **shall** be treated as a skip, not an error. | 11 |
| IDEM-06 | A manual trigger and the scheduled run **shall** use the same function and the same guarantees. | 11 |

### 4.9 Escalation edge cases (17)

| ID | Scenario | Expected behavior |
|---|---|---|
| EC-01 | Complaint resolved 1 minute before deadline | No escalation; status `RESOLVED` |
| EC-02 | Complaint rejected | No escalation (rejection has no clock) |
| EC-03 | Complaint never accepted | No escalation in P0; remains `PENDING_DEPARTMENT_REVIEW` |
| EC-04 | Worker stopped for two days, then restarted | All due complaints escalate on the first run; `overdue_seconds` reflects actual delay |
| EC-05 | Resolution recorded after deadline but before the worker runs | No escalation; `RESOLVED` wins |
| EC-06 | Two worker instances run concurrently | Advisory lock serializes; one escalation row |
| EC-07 | Manual trigger fires during a scheduled run | Lock prevents overlap; one escalation row |
| EC-08 | Duplicate acceptance request | HTTP 409; no second deadline |
| EC-09 | Configuration changed after acceptance | Stored `sla_seconds` and deadline remain unchanged |
| EC-10 | Daylight saving transition | No effect; UTC arithmetic |
| EC-11 | Exactly at the deadline | Escalate (`>=`) |
| EC-12 | No active Superintendent | Escalate; notify administrators; audit `ESCALATION_FALLBACK_NO_SUPERINTENDENT` |
| EC-13 | Department has no active officers | Escalate; notify citizen and Superintendent; no department notification |
| EC-14 | Complaint escalated, then department posts progress | Status remains `ESCALATED`; progress is visible to Superintendent and citizen |
| EC-15 | Complaint escalated, then resolved by Superintendent | Allowed; resolution actor recorded; no further escalation |
| EC-16 | Database unavailable during a run | Job logs the error, releases the lock if acquired, retries next interval |
| EC-17 | Complaint accepted with `ALLOW_DEMO_ESCALATION` and a 2-minute window | Deadline is 2 minutes after acceptance; demo only; production default unchanged |

### 4.10 SRS database integrity requirements (10)

| ID | Requirement (verbatim SRS §15.2) | Owner phase |
|---|---|---|
| DB-01 | InnoDB, `utf8mb4`, UTC session timezone, `DATETIME(6)` timestamps. | 4 |
| DB-02 | `complaints.citizen_id` references `users.id`; `complaints.department_id` references `departments.id`; both non-null. | 4 |
| DB-03 | `complaint_categories.department_id` is non-null and references an active department at creation. | 4 |
| DB-04 | `escalations.complaint_id` is unique and references `complaints.id`. | 4 |
| DB-05 | History, escalations, officer actions, notifications, and audit logs are append-only through the API. | 4 |
| DB-06 | Status, role, image kind, and action type values are constrained to the documented enumerations. | 4 |
| DB-07 | Indexes support queue queries: `(department_id, status, submitted_at)`, escalation candidates `(status, resolution_due_at)`, notifications `(recipient_user_id, is_read, created_at)`, and timeline `(complaint_id, created_at)`. | 4 |
| DB-08 | Foreign keys use `RESTRICT` for core entities so records cannot be orphaned by deletion. | 4 |
| DB-09 | A single initial migration and a repeatable seed script exist; seeded data is idempotent. | 4 |
| DB-10 | Tracking numbers are generated under a uniqueness constraint with retry on collision. | 4 |

### 4.11 Security and privacy requirements (16)

| ID | Requirement (verbatim SRS §16) | Owner phases |
|---|---|---|
| SEC-01 | All production traffic uses HTTPS; the API sets HSTS at the proxy. | 5, 6, 8, 11, 13, 18 |
| SEC-02 | Passwords use bcrypt with cost ≥12; no reversible storage. | 5, 6, 8, 11, 13, 18 |
| SEC-03 | JWT secrets come from environment variables, are at least 32 bytes, and are never committed. | 5, 6, 8, 11, 13, 18 |
| SEC-04 | JWTs expire after 8 hours; malformed, expired, or inactive-user tokens return 401. | 5, 6, 8, 11, 13, 18 |
| SEC-05 | CORS allows only configured frontend origins and required methods/headers. | 5, 6, 8, 11, 13, 18 |
| SEC-06 | Login is rate-limited to 5 attempts per minute per IP+email pair; responses are generic. | 5, 6, 8, 11, 13, 18 |
| SEC-07 | All SQL uses parameterized queries or the ORM; no string interpolation of user input. | 5, 6, 8, 11, 13, 18 |
| SEC-08 | React escapes output by default; no `dangerouslySetInnerHTML` with user content. | 5, 6, 8, 11, 13, 18 |
| SEC-09 | File uploads are validated by signature, renamed randomly, stored outside the web root, and served through an authorized endpoint with `Content-Disposition` and a safe content type. | 5, 6, 8, 11, 13, 18 |
| SEC-10 | Object-level authorization prevents IDOR: every complaint, image, notification, and action is checked against the caller's scope. | 5, 6, 8, 11, 13, 18 |
| SEC-11 | PII and coordinates are excluded from logs, URLs, and error messages. | 5, 6, 8, 11, 13, 18 |
| SEC-12 | Audit logs record authentication failures, denied access, role changes, configuration changes, and status transitions. | 5, 6, 8, 11, 13, 18 |
| SEC-13 | Server errors return a generic message and request id; stack traces are logged server-side only. | 5, 6, 8, 11, 13, 18 |
| SEC-14 | Database credentials and API keys are environment-scoped; the demo Gemini key is not shipped in the frontend. | 5, 6, 8, 11, 13, 18 |
| SEC-15 | The UI displays a persistent "prototype, not an official municipal service" notice. | 5, 6, 8, 11, 13, 18 |
| SEC-16 | Privacy: email/phone are visible to the owner and administrators only; location and coordinates to the owner, responsible department officers, Superintendent, and administrators. | 5, 6, 8, 11, 13, 18 |

### 4.12 System constraints (10)

| ID | Constraint (verbatim SRS §18) | Owner phases |
|---|---|---|
| CON-01 | The implementation must be completable by a small team in ten hours; P0 is the priority. | 2–3, all |
| CON-02 | The stack is fixed: React + Vite + TypeScript + Tailwind + shadcn/ui + React Router + Recharts; FastAPI + SQLAlchemy + MySQL 8.4; APScheduler; Docker Compose; JWT. | 2–3, all |
| CON-03 | Notifications are in-app only in P0. | 2–3, all |
| CON-04 | The scheduler runs in a long-lived process, not in a serverless function. | 2–3, all |
| CON-05 | The frontend must be a responsive web app, not a native app. | 2–3, all |
| CON-06 | The system serves one municipality and one timezone configuration. | 2–3, all |
| CON-07 | AI (Gemini) and the map (Leaflet/OSM) are P1 and must not gate submission, routing, acceptance, escalation, or resolution. | 2–3, all |
| CON-08 | No real municipal data, credentials, or partnerships are assumed. | 2–3, all |
| CON-09 | Uploads are limited to images and a persistent local volume in P0. | 2–3, all |
| CON-10 | Demo data and the demo escalation window must be clearly separated from production defaults. | 2–3, all |

### 4.13 Use cases (7)

| ID | Owner phase |
|---|---|
| UC-01 | 8 |
| UC-02 | 10 |
| UC-03 | 10 |
| UC-04 | 10 |
| UC-05 | 11 |
| UC-06 | 12 |
| UC-07 | 6 |

### 4.14 Assumptions (PRD A-01…A-13; SRS references A-13)

| ID | Assumption (verbatim PRD §18.1) | Impact if violated |
|---|---|---|
| A-01 | The prototype serves one municipality; no tenant isolation is required. | Schema and auth would need redesign |
| A-02 | Accounts for officers and administrators are provisioned by seed data or an administrator; only citizens self-register. | Public officer signup would create a security hole |
| A-03 | Six sample departments and seven seeded categories cover the demo; Water Leakage maps to Water Supply, Other/Infrastructure to Public Works. | Routing demo would misrepresent ownership |
| A-04 | "Seven days" means 168 hours from acceptance; weekends and holidays count. | A calendar engine would be required |
| A-05 | Notifications are in-app only; no email/SMS provider is configured. | Additional integration work and credentials |
| A-06 | Location is optional and may be free text without coordinates. | Map coverage would be incomplete |
| A-07 | Images are optional; a complaint without a photo is valid. | Submission validation would need change |
| A-08 | The Administrator role is administrative only and has no operational complaint actions. | Separation of duties would be weakened |
| A-09 | The Superintendent may read complaint details beyond the escalated queue for oversight, but may act only on escalated complaints and resolutions. | Scope creep in supervisory powers |
| A-10 | Reopening and feedback are P1; `REOPENED` is not exercised in the P0 demo. | Demo script and status model change |
| A-11 | A moderately sized VM/container can run the frontend, API, worker, and MySQL for the demo. | Serverless-only deployment would break the scheduler and uploads |
| A-12 | The demo is conducted in a trusted environment with seeded users; no adversarial penetration testing is performed. | Security claims would exceed evidence |
| A-13 | Each user account has exactly one role; role separation is achieved with separate accounts. | A user needing both administration and operational access would require two accounts |

## 5. PRD feature cross-check (DOC-002)

### 5.1 PRD §10 → FR

| PRD §10 feature | Priority | FR IDs | PRD→FR check |
|---|---|---|---|
| Authentication and Access Control | P0 | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006 | Mapped |
| Complaint Submission | P0 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013 | Mapped |
| Photo Evidence | P0 | FR-010, FR-023 | Mapped |
| Location Capture | P0 | FR-011 | Mapped |
| Category Routing | P0 | FR-012, FR-046, FR-047 | Mapped |
| Department Review | P0 | FR-017, FR-018, FR-019, FR-020 | Mapped |
| Progress Tracking | P0 | FR-021, FR-022, FR-026 | Mapped |
| Complaint Timeline | P0 | FR-016, FR-050 | Mapped |
| Automatic Escalation | P0 | FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034 | Mapped |
| Superintendent Oversight | P0 | FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041 | Mapped |
| Resolution Recording | P0 | FR-024, FR-041 | Mapped |
| In-App Notifications | P0 | FR-042, FR-043, FR-044, FR-045 | Mapped |
| Administration and Configuration | P0 | FR-046, FR-047, FR-048, FR-049, FR-006 | Mapped |
| Audit Trail | P0 | FR-050 | Mapped |
| AI Category and Priority Suggestions | P1 | FR-051, FR-054 | Mapped |
| Duplicate Detection | P1 | FR-052 | Mapped |
| Issue Map | P1 | FR-053 | Mapped |
| Analytics Dashboard | P1 | FR-055 | Mapped |
| Citizen Feedback and Reopening | P1 | FR-056, FR-057 | Mapped |

**Result:** 19/19 normative PRD features map to at least one FR. No PRD feature lacks a requirement ID.

### 5.2 SRS §7.0 feature catalogue (independent check)

| SRS §7.0 feature | Priority | FR IDs |
|---|---|---|
| Authentication and Access Control | P0 | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006 |
| Complaint Submission | P0 | FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013 |
| Photo Evidence | P0 | FR-010, FR-023 |
| Location Capture | P0 | FR-011 |
| Category Routing | P0 | FR-012, FR-046, FR-047 |
| Department Review | P0 | FR-017, FR-018, FR-019, FR-020 |
| Progress Tracking | P0 | FR-021, FR-022, FR-026 |
| Complaint Timeline | P0 | FR-016, FR-050 |
| Automatic Escalation | P0 | FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034 |
| Superintendent Oversight | P0 | FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041 |
| Resolution Recording | P0 | FR-024, FR-041 |
| In-App Notifications | P0 | FR-042, FR-043, FR-044, FR-045 |
| Administration and Configuration | P0 | FR-046, FR-047, FR-048, FR-049, FR-006 |
| Audit Trail | P0 | FR-050 |
| AI Category and Priority Suggestions | P1 | FR-051, FR-054 |
| Duplicate Detection | P1 | FR-052 |
| Issue Map | P1 | FR-053 |
| Analytics Dashboard | P1 | FR-055 |
| Citizen Feedback and Reopening | P1 | FR-056, FR-057 |

**Result:** the SRS catalogue uses the same feature names as PRD §10. FR sets are identical; PRD adds NFR references (`NFR-004…006`, `NFR-007`, `NFR-008`, `NFR-013`) to the same features, which is additive and not a contradiction.

### 5.3 Inverse check: FRs not named in PRD §10

FR-014, FR-015, FR-025 are not named in the PRD §10 feature table. They are **not orphaned**:

| FR | Why it is not a PRD feature row | Authoritative trace |
|---|---|---|
| FR-014 | Citizen list is part of the “Complaint Submission / tracking” journey, not a separate feature | Story US-CIT-07; SRS §7.2 |
| FR-015 | Complaint detail is the read side of the same journey | Stories US-CIT-08, US-DEP-02; SRS §7.2 |
| FR-025 | Department status summary is an aggregate over the Department Review feature | Story US-DEP-01; SRS §7.3 |

**Resolution:** accept as documented. PRD §10 is a feature-level catalogue; SRS §7 and `USER_STORIES.md` provide the FR-level trace. No requirement is orphaned.

## 6. Story → FR matrix (DOC-003)

**Total stories: 44** — 17 CIT, 8 DEP, 5 SUP, 6 ADM, 3 SYS, 4 P1, 1 E2E.

| Story | Role | Priority | Title | FR IDs | Additional IDs | Phase(s) |
|---|---|---|---|---|---|---|
| US-CIT-01 | Citizen | P0 | Register a Citizen account | FR-001, FR-003 | — | 6 / 15 |
| US-CIT-02 | Citizen | P0 | Log in and log out | FR-002, FR-003 | — | 6 / 15 |
| US-CIT-03 | Citizen | P0 | Submit a complaint | FR-007, FR-008, FR-013, FR-042 | — | 8 / 15 |
| US-CIT-04 | Citizen | P0 | Attach photographs to a complaint | FR-010, FR-023 | — | 8 / 15 |
| US-CIT-05 | Citizen | P0 | Add an optional location | FR-011 | NFR-007 | 8 / 15 |
| US-CIT-06 | Citizen | P0 | Receive a tracking number and the correct department | FR-009, FR-012, FR-015 | — | 8 / 15 |
| US-CIT-07 | Citizen | P0 | View my complaints | FR-014 | — | 9 / 15 |
| US-CIT-08 | Citizen | P0 | View status and the complete timeline | FR-015, FR-016 | — | 9 / 15 |
| US-CIT-09 | Citizen | P0 | Receive an acknowledgement when my complaint is accepted | FR-019, FR-042, FR-045 | NT-02 | 7 / 15 |
| US-CIT-10 | Citizen | P0 | Receive a rejection with a reason | FR-020, FR-042, FR-045 | NT-03 | 7 / 15 |
| US-CIT-11 | Citizen | P0 | Receive progress updates | FR-022, FR-023, FR-042, FR-045 | NT-04 | 7 / 15 |
| US-CIT-12 | Citizen | P0 | Receive an escalation update | FR-032, FR-042, FR-045 | NT-05 | 7 / 15 |
| US-CIT-13 | Citizen | P0 | Receive the resolution update | FR-024, FR-041, FR-042, FR-045 | NT-07 | 7 / 15 |
| US-CIT-14 | Citizen (also used by every role) | P0 | Manage my notifications | FR-043, FR-044, FR-045 | — | 7 / 15 |
| US-CIT-15 | Citizen | P0 | See only my own data | FR-004 | NFR-005, NFR-007 | 6 / 14 |
| US-CIT-16 | Citizen | P1 | Give feedback or request reopening after resolution (P1) | FR-056, FR-057 | — | 21 (P1) |
| US-CIT-17 | Citizen (shared by all roles) | P0 | View my profile | FR-005 | — | 6 / 15 |
| US-DEP-01 | Department Officer | P0 | Work from a department-scoped queue | FR-017, FR-025 | — | 10 / 15 |
| US-DEP-02 | Department Officer | P0 | Open a complaint in my department | FR-018, FR-015 | — | 10 / 15 |
| US-DEP-03 | Department Officer | P0 | Accept a complaint and start the seven-day clock | FR-019, FR-027, FR-050 | — | 10 / 15 |
| US-DEP-04 | Department Officer | P0 | Reject a complaint with a reason | FR-020, FR-045 | — | 10 / 15 |
| US-DEP-05 | Department Officer | P0 | Assign a complaint to staff | FR-021 | — | 10 / 15 |
| US-DEP-06 | Department Officer | P0 | Post progress and upload evidence | FR-022, FR-023 | — | 10 / 15 |
| US-DEP-07 | Department Officer | P0 | Resolve a complaint | FR-024, FR-042 | — | 10 / 15 |
| US-DEP-08 | Department Officer | P0 | Continue work after escalation | FR-026, FR-018 | — | 10 / 15 |
| US-SUP-01 | Superintendent Officer | P0 | Review the escalation queue | FR-035, FR-032 | — | 12 / 15 |
| US-SUP-02 | Superintendent Officer | P0 | Review the full history and delay | FR-036, FR-037 | — | 12 / 15 |
| US-SUP-03 | Superintendent Officer | P0 | Record an instruction or supervisory action | FR-038, FR-050 | — | 12 / 15 |
| US-SUP-04 | Superintendent Officer | P0 | Direct follow-up to the responsible department | FR-039, FR-042 | — | 12 / 15 |
| US-SUP-05 | Superintendent Officer | P0 | Monitor and resolve escalated complaints | FR-040, FR-041, FR-024 | — | 12 / 15 |
| US-ADM-01 | Platform Administrator | P0 | Manage users and roles | FR-006 | — | 6 / 15 |
| US-ADM-02 | Platform Administrator | P0 | Manage departments | FR-046 | — | 13 / 15 |
| US-ADM-03 | Platform Administrator | P0 | Manage categories and routing mappings | FR-047, FR-012 | — | 13 / 15 |
| US-ADM-04 | Platform Administrator | P0 | Monitor platform activity | FR-048 | — | 13 / 15 |
| US-ADM-05 | Platform Administrator | P0 | Review audit logs | FR-049, FR-050 | NFR-008 | 13 / 15 |
| US-ADM-06 | Platform Administrator (operator) | P0 | Configure and test the escalation window | FR-033, FR-034 | — | 11 / 15 |
| US-SYS-01 | System | P0 | Enforce role-based access on every operation | FR-004 | RBAC-01, RBAC-02, RBAC-03, RBAC-04, RBAC-05, RBAC-06, RBAC-07, RBAC-08, NFR-005 | 6 |
| US-SYS-02 | System (scheduler) | P0 | Escalate overdue complaints automatically | FR-028, FR-030, FR-031, FR-032, FR-050 | — | 11 |
| US-SYS-03 | System | P0 | Guarantee exactly-once escalation and reliable notifications | FR-042, FR-043, FR-044, FR-045, FR-029 | NFR-003, NFR-012 | 11 |
| US-P1-01 | Citizen (and Department Officer for priority confirmation) | P1 | Get AI category and priority suggestions | FR-051, FR-054 | — | 21 (P1) |
| US-P1-02 | Citizen (visible to Department Officer) | P1 | See possible duplicate complaints | FR-052 | — | 21 (P1) |
| US-P1-03 | All authenticated roles (scope-filtered) | P1 | View complaints on a map | FR-053 | — | 21 (P1) |
| US-P1-04 | Platform Administrator (read-only for Superintendent) | P1 | View the analytics dashboard | FR-055 | — | 21 (P1) |
| US-E2E-01 | Citizen, Department Officer, Superintendent Officer, System, Administrator (setup) | P0 (demo gate) | Complete complaint lifecycle from report to resolution | FR-001, FR-002, FR-003, FR-004, FR-005, FR-006, FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013, FR-014, FR-015, FR-016, FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027, FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034, FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041, FR-042, FR-043, FR-044, FR-045, FR-046, FR-047, FR-048, FR-049, FR-050 | — | 17 |

**Notes**

1. The per-story `Requirements` row is authoritative for implementation; the `USER_STORIES.md` §9 summary is a primary-requirement view. FR-only sets match for all 44 stories. Six stories additionally name NT/RBAC IDs in their block (US-CIT-09…13 name their NT trigger; US-SYS-01 names RBAC-01…08). These are additive and correct.
2. `US-E2E-01` deliberately spans FR-001…FR-050 and is excluded from per-FR story lists to avoid implying it is the only story for those requirements.
3. P2 requirements FR-058…FR-064 intentionally have no MVP story (see §9).

## 7. FR → story / AC / test matrix

| FR | Priority | Primary story (SRS §20.1) | All mapped stories (excl. E2E-01) | Direct AC | Test group | Delivery phase |
|---|---|---|---|---|---|---|
| FR-001 | P0 | US-CIT-01 | US-CIT-01 | AC-01 | T-AUTH | 6 |
| FR-002 | P0 | US-CIT-02 | US-CIT-02 | AC-01 | T-AUTH | 6 |
| FR-003 | P0 | US-CIT-01, US-CIT-02 | US-CIT-01, US-CIT-02 | AC-01 | T-AUTH | 6 |
| FR-004 | P0 | US-SYS-01, US-CIT-15 | US-CIT-15, US-SYS-01 | AC-01, AC-03, AC-13 | T-RBAC | 6 |
| FR-005 | P0 | US-CIT-17 | US-CIT-17 | AC-01 | T-AUTH | 6 |
| FR-006 | P0 | US-ADM-01 | US-ADM-01 | — (covered by test) | T-ADMIN | 6 |
| FR-007 | P0 | US-CIT-03 | US-CIT-03 | AC-02 | T-COMP | 8 |
| FR-008 | P0 | US-CIT-03 | US-CIT-03 | AC-02 | T-COMP | 8 |
| FR-009 | P0 | US-CIT-06 | US-CIT-06 | AC-02 | T-COMP | 8 |
| FR-010 | P0 | US-CIT-04 | US-CIT-04 | AC-02 | T-UPLOAD | 8 |
| FR-011 | P0 | US-CIT-05 | US-CIT-05 | AC-02 | T-COMP | 8 |
| FR-012 | P0 | US-CIT-06 | US-CIT-06, US-ADM-03 | AC-02, AC-03 | T-COMP | 8 |
| FR-013 | P0 | US-CIT-03 | US-CIT-03 | AC-02 | T-COMP | 8 |
| FR-014 | P0 | US-CIT-07 | US-CIT-07 | AC-03 | T-COMP | 9 |
| FR-015 | P0 | US-CIT-08 | US-CIT-06, US-CIT-08, US-DEP-02 | — (covered by test) | T-COMP | 9 |
| FR-016 | P0 | US-CIT-08 | US-CIT-08 | AC-06 | T-COMP | 9 |
| FR-017 | P0 | US-DEP-01 | US-DEP-01 | — (covered by test) | T-DEPT | 10 |
| FR-018 | P0 | US-DEP-02 | US-DEP-02, US-DEP-08 | AC-03, AC-14 | T-RBAC | 10 |
| FR-019 | P0 | US-DEP-03 | US-CIT-09, US-DEP-03 | AC-04 | T-DEPT, T-ESC | 10 |
| FR-020 | P0 | US-DEP-04 | US-CIT-10, US-DEP-04 | AC-05 | T-DEPT | 10 |
| FR-021 | P0 | US-DEP-05 | US-DEP-05 | — (covered by test) | T-DEPT | 10 |
| FR-022 | P0 | US-DEP-06 | US-CIT-11, US-DEP-06 | AC-06 | T-DEPT | 10 |
| FR-023 | P0 | US-DEP-06 | US-CIT-04, US-CIT-11, US-DEP-06 | — (covered by test) | T-UPLOAD | 10 |
| FR-024 | P0 | US-DEP-07, US-SUP-05 | US-CIT-13, US-DEP-07, US-SUP-05 | AC-11, AC-12 | T-DEPT, T-SUP | 10 |
| FR-025 | P0 | US-DEP-01 | US-DEP-01 | — (covered by test) | T-DEPT | 10 |
| FR-026 | P0 | US-DEP-08 | US-DEP-08 | — (covered by test) | T-DEPT | 10 |
| FR-027 | P0 | US-DEP-03 | US-DEP-03 | AC-04 | T-ESC | 10 |
| FR-028 | P0 | US-SYS-02 | US-SYS-02 | AC-07 | T-ESC | 11 |
| FR-029 | P0 | US-SYS-03 | US-SYS-03 | AC-07, AC-08 | T-ESC | 11 |
| FR-030 | P0 | US-SYS-02 | US-SYS-02 | AC-07 | T-ESC | 11 |
| FR-031 | P0 | US-SYS-02 | US-SYS-02 | AC-07 | T-ESC | 11 |
| FR-032 | P0 | US-SYS-02, US-SUP-01 | US-CIT-12, US-SUP-01, US-SYS-02 | — (covered by test) | T-ESC, T-NOTIF | 11 |
| FR-033 | P0 | US-ADM-06 | US-ADM-06 | AC-16 | T-ESC | 11 |
| FR-034 | P0 | US-ADM-06 | US-ADM-06 | AC-16 | T-ESC | 11 |
| FR-035 | P0 | US-SUP-01 | US-SUP-01 | AC-09 | T-SUP | 12 |
| FR-036 | P0 | US-SUP-02 | US-SUP-02 | AC-09 | T-SUP | 12 |
| FR-037 | P0 | US-SUP-02 | US-SUP-02 | AC-09 | T-SUP | 12 |
| FR-038 | P0 | US-SUP-03 | US-SUP-03 | AC-10 | T-SUP | 12 |
| FR-039 | P0 | US-SUP-04 | US-SUP-04 | — (covered by test) | T-SUP | 12 |
| FR-040 | P0 | US-SUP-05 | US-SUP-05 | — (covered by test) | T-SUP | 12 |
| FR-041 | P0 | US-SUP-05 | US-CIT-13, US-SUP-05 | AC-11 | T-SUP | 12 |
| FR-042 | P0 | US-SYS-03 | US-CIT-03, US-CIT-09, US-CIT-10, US-CIT-11, US-CIT-12, US-CIT-13, US-DEP-07, US-SUP-04, US-SYS-03 | AC-04, AC-11 | T-NOTIF | 7 |
| FR-043 | P0 | US-CIT-14 | US-CIT-14, US-SYS-03 | AC-15 | T-NOTIF | 7 |
| FR-044 | P0 | US-CIT-14 | US-CIT-14, US-SYS-03 | AC-15 | T-NOTIF | 7 |
| FR-045 | P0 | US-CIT-09, US-CIT-10, US-CIT-11, US-CIT-12, US-CIT-13 | US-CIT-09, US-CIT-10, US-CIT-11, US-CIT-12, US-CIT-13, US-CIT-14, US-DEP-04, US-SYS-03 | AC-05, AC-10 | T-NOTIF | 7 |
| FR-046 | P0 | US-ADM-02 | US-ADM-02 | — (covered by test) | T-ADMIN | 13 |
| FR-047 | P0 | US-ADM-03 | US-ADM-03 | — (covered by test) | T-ADMIN | 13 |
| FR-048 | P0 | US-ADM-04 | US-ADM-04 | — (covered by test) | T-ADMIN | 13 |
| FR-049 | P0 | US-ADM-05 | US-ADM-05 | — (covered by test) | T-ADMIN | 13 |
| FR-050 | P0 | US-DEP-03, US-SUP-03, US-SYS-02 | US-DEP-03, US-SUP-03, US-ADM-05, US-SYS-02 | AC-06, AC-10 | T-ESC, T-DEPT, T-SUP | 8–12 |
| FR-051 | P1 | US-P1-01 | US-P1-01 | — (covered by test) | T-P1 | 21 (P1) |
| FR-052 | P1 | US-P1-02 | US-P1-02 | — (covered by test) | T-P1 | 21 (P1) |
| FR-053 | P1 | US-P1-03 | US-P1-03 | — (covered by test) | T-P1 | 21 (P1) |
| FR-054 | P1 | US-P1-01 | US-P1-01 | — (covered by test) | T-P1 | 21 (P1) |
| FR-055 | P1 | US-P1-04 | US-P1-04 | — (covered by test) | T-P1 | 21 (P1) |
| FR-056 | P1 | US-CIT-16 | US-CIT-16 | — (covered by test) | T-P1 | 21 (P1) |
| FR-057 | P1 | US-CIT-16 | US-CIT-16 | — (covered by test) | T-P1 | 21 (P1) |
| FR-058 | P2 | — | — (future) | — (covered by test) | Not built | Not built (P2) |
| FR-059 | P2 | — | — (future) | — (covered by test) | Not built | Not built (P2) |
| FR-060 | P2 | — | — (future) | — (covered by test) | Not built | Not built (P2) |
| FR-061 | P2 | — | — (future) | — (covered by test) | Not built | Not built (P2) |
| FR-062 | P2 | — | — (future) | — (covered by test) | Not built | Not built (P2) |
| FR-063 | P2 | — | — (future) | — (covered by test) | Not built | Not built (P2) |
| FR-064 | P2 | — | — (future) | — (covered by test) | Not built | Not built (P2) |

**Coverage assertions**

- Every P0 FR (50/50) maps to at least one non-E2E story.
- Every P0 FR (50/50) maps to at least one test group in SRS §20.1/TRD §20.
- 36 P0 FRs have a direct AC reference; the other 14 (`FR-006, FR-015, FR-017, FR-021, FR-023, FR-025, FR-026, FR-032, FR-039, FR-040, FR-046, FR-047, FR-048, FR-049`) are verified by their named test group. SRS §19 states that AC-01…AC-16 are release gates, not an exhaustive FR-to-AC list, so the “AC **or** test” criterion is met for all 50.
- P1 FRs map to P1 stories and `T-P1`; P2 FRs map to no story and are marked not built.

## 8. NFR measurability audit (DOC-007)

| NFR | Category | Numeric / observable target | Tracker verification | Verdict |
|---|---|---|---|---|
| NFR-001 | Performance | Load test at Hour 9; T-PERF | TEST-054 | Measurable |
| NFR-002 | Timeliness | Integration test with 2-minute window; T-ESC | TEST-019, TEST-020 | Measurable |
| NFR-003 | Concurrency | 20-run and parallel-run test; T-ESC | TEST-020, TEST-021 | Measurable |
| NFR-004 | Credential security | Code review + test; T-AUTH | TEST-001 | Measurable |
| NFR-005 | Authorization | 12-case RBAC matrix; T-RBAC | TEST-003, TEST-050 | Measurable |
| NFR-006 | Session security | T-AUTH | TEST-001 | Measurable |
| NFR-007 | Privacy | Field-level tests; T-RBAC | TEST-012, TEST-050 | Measurable |
| NFR-008 | Audit immutability | Attempt update/delete; T-ADMIN | TEST-029 | Measurable |
| NFR-009 | Time handling | Boundary tests; T-ESC | TEST-019, TEST-039 | Measurable |
| NFR-010 | Usability | Timed usability run; T-E2E | TEST-033 | Measurable |
| NFR-011 | Reliability | Restart test; T-ESC | TEST-022, DEP-013 | Measurable |
| NFR-012 | Transactional integrity | Fault-injection test; T-ESC | TEST-006, TEST-008, TEST-017 | Measurable |
| NFR-013 | Upload safety | T-UPLOAD | TEST-009, TEST-051 | Measurable |
| NFR-014 | Compatibility | Manual matrix; T-E2E | TEST-046 | Measurable |
| NFR-015 | Accessibility | Manual audit; T-E2E | TEST-032, TEST-045, TEST-056 | Measurable |
| NFR-016 | Maintainability | Review at Hour 9 | DEP-001, DOC-030 | Measurable |
| NFR-017 | Portability | Fresh-clone test | DEP-012 | Measurable |
| NFR-018 | Observability | Log inspection; T-ESC | BE-012, BE-077, DEP-011 | Measurable |
| NFR-019 | Retention | API surface review | DB-023, TEST-029 | Measurable |
| NFR-020 | Testability | Test run at Hour 9 | TEST-039–TEST-049 | Measurable |
| NFR-021 | Log hygiene | Log review | TEST-052 | Measurable |
| NFR-022 | Capacity | Seeded-volume test | TEST-057 | Measurable |

**Result:** 22/22 NFRs contain a numeric or directly observable target. Key thresholds: p95 1 s / 2 s at 500 complaints and 50 concurrent users; escalation detection ≤60 s; 8-hour JWT; 10,080-minute default window; 5 MiB per file; 3 files per request; 10 per complaint; 360 px width; ≤60-second first submission; contrast ≥4.5:1; 500 complaints / 100 users / 50 concurrent users / 2 GB image storage.

## 9. P2 exclusion register (DOC-005)

| FR | Requirement (verbatim) | Status | Authority |
|---|---|---|---|
| FR-058 | The system may add email, SMS, WhatsApp, or push notification adapters through an outbox pattern. | **Not built** | P2 future work — SRS §7.10, SRS §20.2, TRD Appendix A.2 |
| FR-059 | The system may support multiple municipalities with tenant isolation. | **Not built** | P2 future work — SRS §7.10, SRS §20.2, TRD Appendix A.2 |
| FR-060 | The system may support working-day, holiday, and paused SLA calendars. | **Not built** | P2 future work — SRS §7.10, SRS §20.2, TRD Appendix A.2 |
| FR-061 | The system may verify or classify evidence images automatically. | **Not built** | P2 future work — SRS §7.10, SRS §20.2, TRD Appendix A.2 |
| FR-062 | The system may expose a privacy-reviewed public transparency portal. | **Not built** | P2 future work — SRS §7.10, SRS §20.2, TRD Appendix A.2 |
| FR-063 | The system may provide native mobile applications. | **Not built** | P2 future work — SRS §7.10, SRS §20.2, TRD Appendix A.2 |
| FR-064 | The system may integrate with external municipal work-order systems. | **Not built** | P2 future work — SRS §7.10, SRS §20.2, TRD Appendix A.2 |

**Resolution:** FR-058…FR-064 are explicitly labeled future work in SRS §7.10 and excluded from P0 acceptance. They create no story, endpoint, table, dependency, or acceptance test in this delivery. `USER_STORIES.md` §9 states that P2 requirements intentionally have no MVP stories.

## 10. Open-question log (DOC-006)

| ID | Question | Source | Resolution | Status |
|---|---|---|---|---|
| Q-01 | `PHASES.md` says “18 CIT … minus overlaps = 44”, but `USER_STORIES.md` lists 17 CIT and 44 total IDs. | PHASES §Phase 1 | The 44 explicit story IDs are authoritative. 17 CIT + 8 DEP + 5 SUP + 6 ADM + 3 SYS + 4 P1 + 1 E2E = 44. The “18 CIT” phrase is an arithmetic wording defect, not a scope change. | Resolved — accept as documented |
| Q-02 | 14 P0 FRs have no direct AC reference. Are they untested? | SRS §19/§20.1 | They map to story-level acceptance criteria and named test groups (FR-006, FR-015, FR-017, FR-021, FR-023, FR-025, FR-026, FR-032, FR-039, FR-040, FR-046, FR-047, FR-048, FR-049). SRS §19 ACs are release gates, not an exhaustive per-FR list; the Phase 1 criterion is “AC or test”. | Resolved — accept as documented |
| Q-03 | PRD §10 does not name FR-014, FR-015, or FR-025. Are they orphaned? | PRD §10 vs SRS §7 | They are FR-level reads/aggregates inside documented journeys and map to US-CIT-07, US-CIT-08, US-DEP-02, and US-DEP-01. PRD §10 is feature-level. | Resolved — accept as documented |
| Q-04 | FR-032 lists test groups `T-ESC, T-NOTIF` in the FR table but only `T-NOTIF` in the trace table. | SRS §7.4 vs §20.1 | Use the union: escalation path `T-ESC` and notification delivery `T-NOTIF` are both required. No requirement change. | Resolved — accept as documented |
| Q-05 | “Superintendent”, “Superintendent Officer”, “Administrator”, “Platform Admin” appear in prose. | PRD/SRS/TRD/USER_STORIES | Canonical role codes are `SUPERINTENDENT_OFFICER` and `PLATFORM_ADMIN`; short display names are permitted in prose. See §3.9. | Resolved — accept as documented |
| Q-06 | “ticket” appears in the terminology task. Is it a second domain object? | PHASES DOC-009 task text | “ticket” is not used as a domain object in PRD/SRS/TRD/USER_STORIES. “Complaint” is canonical. | Resolved — accept as documented |
| Q-07 | P2 FR-058…FR-064 are absent from §20.1. Is traceability incomplete? | SRS §20.2, TRD A.2 | They are explicitly future/not built in SRS §7.10, SRS §20.2, and TRD Appendix A.2. Exclusion is intentional and recorded in §9. | Resolved — accept as documented |
| Q-08 | PRD’s Photo Evidence row adds NFR-013 while SRS §7.0 lists only FR-010 and FR-023. | PRD §10 vs SRS §7.0 | The FR set is identical; the PRD adds an applicable NFR. Additive, not contradictory. | Resolved — accept as documented |
| Q-09 | “Seven days”, “168 hours”, and “10,080 minutes” are used interchangeably. | PRD/SRS/TRD | They are identical: 7 × 24 × 60 = 10,080 minutes; calendar days include weekends and holidays (SRS ESC-03). Canonical stored unit is seconds: 604,800. | Resolved — accept as documented |
| Q-10 | AC-13 references `RBAC-01…RBAC-08`, and AC-12 references BR-20, not only FRs. | SRS §19 | Acceptance criteria may reference FR/NFR/BR/RBAC/NT. Cross-family references are valid traceability. | Resolved — accept as documented |
| Q-11 | Per-story `Requirements` rows name NT/RBAC IDs that the §9 summary omits. | USER_STORIES §2–8 vs §9 | Per-story rows are more specific and additive; FR-only sets match the summary for all 44 stories. No contradiction. | Resolved — accept as documented |
| Q-12 | SRS references only assumption A-13, while PRD defines A-01…A-13. | SRS §5 vs PRD §18.1 | PRD §18.1 is the full assumption register; A-13 is the only one cited by an SRS requirement. All 13 are inventoried in §4.14. | Resolved — accept as documented |
| Q-13 | NT-08 reopening is defined but belongs to P1. | SRS §13, PRD §16.2 | NT-08 is P1 and gated to Phase 21; it is excluded from P0 notification acceptance. No P0 dependency. | Resolved — accept as documented |
| Q-14 | Demo escalation values (2 minutes / 30-second check) could be mistaken for production defaults. | SRS §14.5, TRD §19 | Production default is 10,080 minutes; non-default requires `ALLOW_DEMO_ESCALATION=true` and must be visibly labeled. The guard is an acceptance criterion (AC-16). | Resolved — accept as documented |

**Open P0 questions: 0. Blocked items: 0. Silent assumptions: 0.** Every question above is resolved by accepting the documented requirement; none changes scope.

## 11. Scripted ID diff (DOC-011)

**Method:** a Python validator extracted every requirement ID family from `SRS.md` by its normative section tables, extracted every primary-key ID from §4 of this baseline, and compared the two sets. It separately extracted the 44 story IDs from `USER_STORIES.md` and compared them with §6. Duplicate detection counts primary-key occurrences, not cross-references inside matrix columns.

| Family | SRS IDs | Baseline inventory | Missing | Duplicates |
|---|---|---|---|---|
| FR-001…FR-064 | 64 | 64 | 0 | 0 |
| NFR-001…NFR-022 | 22 | 22 | 0 | 0 |
| BR-01…BR-20 | 20 | 20 | 0 | 0 |
| NT-01…NT-08 | 8 | 8 | 0 | 0 |
| AC-01…AC-16 | 16 | 16 | 0 | 0 |
| RBAC-01…RBAC-08 | 8 | 8 | 0 | 0 |
| ESC-01…ESC-10 | 10 | 10 | 0 | 0 |
| IDEM-01…IDEM-06 | 6 | 6 | 0 | 0 |
| EC-01…EC-17 | 17 | 17 | 0 | 0 |
| DB-01…DB-10 (SRS integrity) | 10 | 10 | 0 | 0 |
| SEC-01…SEC-16 | 16 | 16 | 0 | 0 |
| CON-01…CON-10 | 10 | 10 | 0 | 0 |
| UC-01…UC-07 | 7 | 7 | 0 | 0 |
| A-13 (SRS-referenced assumption) | 1 | 1 | 0 | 0 |
| **SRS total** | **215** | **215** | **0** | **0** |
| US-CIT-01…17, US-DEP-01…08, US-SUP-01…05, US-ADM-01…06, US-SYS-01…03, US-P1-01…04, US-E2E-01 | 44 | 44 | 0 | 0 |

**Result: 215/215 SRS requirement IDs present, 0 missing, 0 duplicates. 44/44 story IDs present, 0 missing, 0 duplicates.**

**Additional non-SRS context rows:** A-01…A-12 (PRD assumptions not individually cited by SRS) are inventoried in §4.14 for completeness. They are additive context rows, not SRS requirements, and do not affect the diff.

**Original-brief namespace:** `FR-01…FR-12` in SRS §1.5 and Appendix C are identifiers from the original problem brief, not SRS requirement IDs. Appendix C maps them to `FR-001…FR-050`; they are excluded from the diff by design.

**Reproduction:** the validator is documented in the Phase 1 validation record and was run against this exact file. Expected output: `missing=0 duplicates=0`.

## 12. Phase 1 acceptance criteria and Definition of Done

| Phase 1 acceptance criterion | Evidence | Verdict |
|---|---|---|
| Every ID in SRS appears exactly once in the inventory | §4 primary keys; §11 diff 215/215, 0 missing, 0 duplicates | **PASS** |
| Every P0 FR maps to at least one story and one AC or test | §7: 50/50 stories; 50/50 test groups; 36 direct ACs + 14 test-covered | **PASS** |
| No contradictions among roles, statuses, SLA, or tracking format | §3 canonical invariants and §3.9 terminology reconciliation | **PASS** |
| P2 scope explicitly marked “not built” | §9 exclusion register FR-058…FR-064 | **PASS** |
| Open questions resolved with zero unresolved P0 items | §10: 14 questions, 0 open P0, 0 blocked | **PASS** |
| Story count is 44 and every story maps to FRs | §6: 44/44, all with FR mappings | **PASS** |
| NFR targets measurable | §8: 22/22 measurable | **PASS** |
| Each AC has concrete reproducible steps | §4.5: 16/16 steps | **PASS** |
| PRD feature has a requirement ID | §5: 19/19 features mapped | **PASS** |
| No application code written in Phase 1 | This document and tracker update only | **PASS** |

**Definition of Done:** baseline approved; all later phases reference this file; no code written yet. **Status: COMPLETE.**

## 13. Change control

- This baseline is additive. Do not edit `PRD.md`, `SRS.md`, `TRD.md`, or `PHASES.md` to make the baseline pass.
- If a new requirement is discovered, add it under the owning phase and workstream in `tracker-checklist.md` with the next free ID, then append it here with its story/test trace.
- If a source document changes, re-run the scripted ID diff and record the new counts before starting the next phase.
- Requirement IDs are permanent. Never reuse or renumber an ID.

---

*End of baseline — Phase 1, CivicTrack.*
