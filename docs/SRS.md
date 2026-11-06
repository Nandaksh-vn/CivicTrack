# CivicTrack — Software Requirements Specification (SRS)

| Field | Value |
|---|---|
| Product | CivicTrack — Community Problem Reporting and Resolution Platform |
| Document | Software Requirements Specification |
| Version | 1.0 |
| Date | 06 November 2026 |
| Status | Approved for 10-hour hackathon build |
| Standard | IEEE 830-style structure, adapted for a hackathon MVP |
| Companion documents | `PRD.md`, `USER_STORIES.md`, `TRD.md` |

---

## 1. Introduction

### 1.1 Purpose

This SRS specifies the functional and non-functional requirements of CivicTrack in a form that can be implemented, tested, and verified. Each requirement has a unique identifier and an observable acceptance condition. The document is the authority for **what the system shall do**; the TRD is the authority for **how**.

### 1.2 Scope

CivicTrack is a browser-based prototype for one municipality. It supports four roles over a shared complaint lifecycle: submission with optional photo and location, category-based routing, departmental acceptance or rejection, progress tracking, automatic escalation after a seven-calendar-day resolution window, supervisory intervention, authorized resolution, and in-app notifications.

The system includes a React/Vite frontend, a FastAPI backend, a MySQL database, and an APScheduler worker. It does not include SMS/email delivery, multi-tenancy, GIS boundary logic, AI verification, or integration with real municipal systems.

### 1.3 Intended audience

| Reader | Use |
|---|---|
| Frontend and backend developers | Implement requirements and API behavior |
| Testers and demo moderator | Derive test cases and verify acceptance criteria |
| Product owner and judges | Confirm scope and demo readiness |
| Future maintainers | Understand invariants and edge cases |

### 1.4 References

- `PRD.md` — product rationale, personas, scope, priorities.
- `USER_STORIES.md` — role-based stories and Given/When/Then criteria.
- `TRD.md` — architecture, schema, API contracts, escalation design.
- `CivicTrack_Problem_Statement_and_Objectives.pdf` — original hackathon brief.

### 1.5 Requirement conventions

- **Shall** indicates a mandatory, testable requirement.
- Requirement IDs are permanent: `FR-001`–`FR-064`, `NFR-001`–`NFR-022`, `BR-01`–`BR-20`, `NT-01`–`NT-08`.
- Priority: **P0** mandatory for the demo, **P1** optional if P0 passes, **P2** future work (not implemented).
- Every P0 requirement appears in `USER_STORIES.md` and has an implementation approach in `TRD.md` §22.
- Where the original brief uses `FR-01`–`FR-12`, Appendix C maps them to this document's identifiers.

### 1.6 Assumptions

Assumptions are listed in PRD §18 and repeated where they affect a requirement. The most important are: one municipality, seeded officer accounts, in-app notifications only, optional image/location, and a fixed calendar-day SLA.

---

## 2. Purpose and Scope

### 2.1 Product purpose

Give citizens a single, accountable channel to report civic problems; give departments a structured queue and progress record; and guarantee that accepted complaints which breach the resolution window reach a Superintendent automatically.

### 2.2 In scope

| Area | Included |
|---|---|
| Identity | Citizen self-registration; seeded officer/admin accounts; login; JWT; role and department scoping |
| Intake | Title, description, active category, 0–3 images, optional text location and coordinates, unique tracking number |
| Routing | Category-to-department mapping, transactional assignment at submission |
| Department | Queue, detail, accept, reject with reason, assign, progress notes, evidence, resolve |
| Time | `accepted_at`, `sla_seconds`, `resolution_due_at`, UTC storage |
| Escalation | Scheduled check, exactly-once escalation, history, three-party notification |
| Oversight | Superintendent queue, delay view, full history, attributable actions, resolution |
| Citizen | List, detail, timeline, notifications, own profile |
| Admin | Users/roles, departments, categories/mappings, activity, audit log |
| Audit | Append-only status history, officer actions, audit events |
| Demo | Seed data, guarded demo escalation window, manual trigger endpoint, Docker Compose |

### 2.3 Out of scope

Email/SMS/WhatsApp/push; multi-tenant operation; working-day/holiday calendars; AI verification; public portal; native apps; municipal integrations; payments; live chat; map clustering; officer performance scoring (see PRD §15).

---

## 3. Definitions and Abbreviations

| Term | Definition |
|---|---|
| API | Application Programming Interface, served under `/api/v1` |
| APScheduler | Python background scheduler used by the worker process |
| Citizen | Role `CITIZEN`; owner of complaints |
| Department | Organizational unit responsible for a category of work |
| Department Officer | Role `DEPARTMENT_OFFICER`; scoped to one department |
| Superintendent Officer | Role `SUPERINTENDENT_OFFICER`; oversees escalated complaints |
| Platform Administrator | Role `PLATFORM_ADMIN`; configures the platform |
| Complaint | A citizen report with a unique tracking number and a lifecycle status |
| Acceptance | Department decision to own the complaint; starts the resolution clock |
| Resolution / deadline | `resolution_due_at = accepted_at + sla_seconds` |
| SLA | Service-level window; 7 calendar days = 168 hours = 10,080 minutes in production |
| Escalation | Automatic transfer of an overdue unresolved complaint to the Superintendent |
| Escalation window | Configured number of seconds after acceptance before escalation |
| Idempotent | Repeating an operation yields the same state and at most one escalation row |
| Timeline | Ordered union of status changes, progress notes, supervisor actions, and escalation events |
| Tracking number | `CT-<YYYY>-<6 digits>`, unique and human-readable |
| UTC | Coordinated Universal Time; all persisted timestamps use it |
| PII | Personally identifiable information, including phone, email, and precise coordinates |

### 3.1 Status glossary

`SUBMITTED`, `PENDING_DEPARTMENT_REVIEW`, `ACCEPTED`, `IN_PROGRESS`, `REJECTED`, `ESCALATED`, `RESOLVED`, `REOPENED` (P1). Definitions and transitions are normatively defined in §11, §14, and PRD Appendix A.

### 3.2 Abbreviations

| Abbreviation | Meaning |
|---|---|
| AC | Acceptance criterion |
| BR | Business rule |
| FR | Functional requirement |
| JWT | JSON Web Token |
| NFR | Non-functional requirement |
| NT | Notification trigger |
| RBAC | Role-based access control |
| SLA | Service-level agreement/window |
| UC | Use case |

---

## 4. Overall System Description

### 4.1 Product perspective

CivicTrack is a standalone web application with four role-specific interfaces backed by one API and one relational database. A separate worker process runs the escalation check. The system does not depend on external services for P0; the only optional external services are Gemini (P1) and OpenStreetMap tiles (P1).

### 4.2 Major functions

1. Register, authenticate, and authorize users.
2. Submit and route complaints with evidence and optional location.
3. Review, accept or reject, assign, update, and resolve complaints.
4. Compute and enforce the resolution deadline.
5. Escalate overdue accepted complaints automatically and exactly once.
6. Notify affected parties in-app.
7. Provide supervisory review and attributable intervention.
8. Administer configuration and inspect audit information.

### 4.3 System context

```
Citizen (browser) ─┐
Dept Officer ──────┼── React SPA (Vite) ── HTTPS/JSON ── FastAPI /api/v1 ── MySQL 8.4
Superintendent ────┤                                          │
Administrator ─────┘                                          └── APScheduler worker
                                                                  (escalation check)
Optional P1: Gemini API (category/priority), OSM tiles (map)
```

### 4.4 User classes

See §5.

### 4.5 Operating constraints

- Ten-hour build by a small team; P0 must be demonstrable end-to-end.
- Browser-based, responsive down to 360 px width.
- Single municipality, single timezone configuration.
- The escalation worker must run in a long-lived process; serverless functions are not suitable.
- No dependency on AI for any P0 behavior.

### 4.6 Assumptions and dependencies

As in PRD §18. Key dependencies: MySQL 8.4, Python 3.12, Node.js 20+, a JWT secret, seed data, and a persistent process for the scheduler.

---

## 5. User Classes and Characteristics

| User class | Role code | Technical skill | Frequency | Scope | Key needs |
|---|---|---|---|---|---|
| Citizen | `CITIZEN` | Low to moderate; mobile-first | Occasional | Own complaints and notifications | Short form, plain language, visible status, reference number |
| Department Officer | `DEPARTMENT_OFFICER` | Moderate; desktop | Daily during a shift | Only own department's complaints | Scoped queue, accept/reject, fast progress and resolution updates |
| Superintendent Officer | `SUPERINTENDENT_OFFICER` | Moderate; desktop | Daily | Escalated complaints; oversight read | Exception queue, overdue duration, full history, attributable instructions |
| Platform Administrator | `PLATFORM_ADMIN` | High | Weekly / as needed | All configuration and audit data; read-only complaint detail | User/role management, routing configuration, activity and audit review |

**Constraints on user classes**

- A user has exactly one role (assumption A-13). Role switching requires a different account.
- A Department Officer must be assigned to exactly one active department.
- Citizens cannot be created by other citizens; officers and administrators are provisioned by a Platform Administrator or the seed script.
- Deactivated users cannot authenticate; existing tokens are rejected on the next request.

---

## 6. Operating Environment

| Element | Requirement |
|---|---|
| Client | Modern evergreen browser: Chrome, Edge, Firefox, Safari (latest two major versions); responsive 360–1920 px |
| Frontend hosting | Static build served by nginx in Docker, or Vercel |
| Backend | Python 3.12, FastAPI, Uvicorn, single worker process per container |
| Worker | Python 3.12, APScheduler, same codebase as backend, separate container |
| Database | MySQL 8.4, InnoDB, `utf8mb4`, UTC session timezone |
| Network | HTTPS in deployment; CORS restricted to configured frontend origins |
| Storage | Persistent volume mounted at `/app/uploads` for images |
| Time | Server clocks synchronized via NTP; all persistence in UTC; display timezone from `APP_TIMEZONE` |
| Containerization | Docker and Docker Compose for db, api, worker, web |
| Development | Windows, macOS, or Linux with Docker Desktop; Node.js 20+, Python 3.12 for non-Docker work |

---

## 7. Functional Requirements

Each requirement is mandatory at its priority and is verified by the test group named in the last column (test design in TRD §20). P0 requirements are numbered FR-001–FR-050; P1 FR-051–FR-057; P2 FR-058–FR-064 (documented, not built).

### 7.0 Feature catalogue

Feature names are normative and identical to PRD §10 and the TRD implementation map.

| Feature | Priority | Requirements |
|---|---|---|
| Authentication and Access Control | P0 | FR-001–FR-006 |
| Complaint Submission | P0 | FR-007–FR-013 |
| Photo Evidence | P0 | FR-010, FR-023 |
| Location Capture | P0 | FR-011 |
| Category Routing | P0 | FR-012, FR-046, FR-047 |
| Department Review | P0 | FR-017–FR-020 |
| Progress Tracking | P0 | FR-021, FR-022, FR-026 |
| Complaint Timeline | P0 | FR-016, FR-050 |
| Automatic Escalation | P0 | FR-027–FR-034 |
| Superintendent Oversight | P0 | FR-035–FR-041 |
| Resolution Recording | P0 | FR-024, FR-041 |
| In-App Notifications | P0 | FR-042–FR-045 |
| Administration and Configuration | P0 | FR-006, FR-046–FR-049 |
| Audit Trail | P0 | FR-050 |
| AI Category and Priority Suggestions | P1 | FR-051, FR-054 |
| Duplicate Detection | P1 | FR-052 |
| Issue Map | P1 | FR-053 |
| Analytics Dashboard | P1 | FR-055 |
| Citizen Feedback and Reopening | P1 | FR-056, FR-057 |

### 7.1 Authentication and access control

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-001 | The system **shall** allow an unauthenticated visitor to register a Citizen account with full name (2–120 characters), valid unique email (case-insensitive, ≤190 characters), password (8–72 characters containing at least one letter and one digit), and optional phone (7–20 characters from digits, `+`, spaces, `-`). On success it shall create an active user with role `CITIZEN` and return HTTP 201 with a JWT and the public user object. | P0 | T-AUTH |
| FR-002 | The system **shall** authenticate an active user by email and password, return a signed JWT valid for 8 hours, and return HTTP 401 with the generic message `Invalid email or password` for invalid credentials or an inactive account. Logout **shall** return HTTP 204 and require the client to discard the token. | P0 | T-AUTH |
| FR-003 | The system **shall** store only a bcrypt hash (cost ≥ 12) of each password, **shall not** return or log password fields, and **shall** verify credentials using a constant-time comparison. | P0 | T-AUTH |
| FR-004 | The system **shall** enforce role-based authorization on every protected API operation and every client route. A request whose authenticated role lacks permission **shall** return HTTP 403 and **shall not** change state. | P0 | T-RBAC |
| FR-005 | The system **shall** allow an authenticated user to retrieve their own profile: full name, email, phone, role code, active flag, and department name when applicable. It **shall not** expose password hashes or other users' PII. | P0 | T-AUTH |
| FR-006 | The system **shall** allow a Platform Administrator to list users; create Department Officer or Platform Administrator accounts with a unique email, role, and exactly one active department for Department Officers; change a user's role; activate or deactivate an account. It **shall** prevent deactivating or demoting the last active Platform Administrator. | P0 | T-ADMIN |

### 7.2 Complaint submission and citizen tracking

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-007 | The system **shall** return the active category catalogue (id, name, code, mapped department id and name) to any authenticated user. | P0 | T-COMP |
| FR-008 | The system **shall** create a complaint from a title (5–150 characters), description (20–2,000 characters), active category id, optional location text (≤255 characters), optional latitude and longitude, and zero to three images, associating it with the authenticated Citizen. | P0 | T-COMP |
| FR-009 | The system **shall** assign each complaint a unique tracking number matching `^CT-[0-9]{4}-[0-9]{6}$` and **shall** return it in every complaint representation. | P0 | T-COMP |
| FR-010 | The system **shall** accept only JPEG, PNG, or WebP images, maximum 5 MiB each and maximum three per submission; it **shall** verify file signatures, store files under randomized names, and reject invalid uploads with HTTP 422 **without** creating a complaint or partial image rows. | P0 | T-UPLOAD |
| FR-011 | The system **shall** accept optional free-text location and optional coordinates. If either coordinate is supplied, both **shall** be required and **shall** satisfy latitude −90 to 90 and longitude −180 to 180; invalid combinations **shall** return HTTP 422. | P0 | T-COMP |
| FR-012 | The system **shall** route every complaint at submission to exactly one active department using the category's current mapping. A category that is inactive or has no mapped department **shall** be rejected with HTTP 422, and no complaint **shall** be persisted. | P0 | T-COMP |
| FR-013 | Within the submission transaction, the system **shall** persist status `SUBMITTED`, then `PENDING_DEPARTMENT_REVIEW`, and **shall** append two status-history rows: `null → SUBMITTED` attributed to the Citizen and `SUBMITTED → PENDING_DEPARTMENT_REVIEW` attributed to `SYSTEM`. | P0 | T-COMP |
| FR-014 | The system **shall** list only the authenticated Citizen's complaints, newest first, paginated at 20 per page, filterable by status and category. | P0 | T-COMP |
| FR-015 | The system **shall** return complaint details to its owner, including tracking number, title, description, category, department, status, submitted time, acceptance time, deadline, resolution time, location, images, and resolution summary when present. | P0 | T-COMP |
| FR-016 | The system **shall** return a complaint timeline ordered by event timestamp ascending and then event id ascending, containing status changes, progress notes, supervisory actions, escalation events, and image additions, filtered by the viewer's visibility permissions. | P0 | T-COMP |

### 7.3 Department review, progress, and resolution

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-017 | The system **shall** provide a Department Officer with a review queue limited to their assigned department, newest first, paginated at 20, filterable by status, category, and assignee, with per-status counts. | P0 | T-DEPT |
| FR-018 | The system **shall** allow a Department Officer to read a complaint only when it exists and its `department_id` equals the officer's department. An existing complaint in another department **shall** return HTTP 403; an unknown id **shall** return HTTP 404. | P0 | T-RBAC |
| FR-019 | The system **shall** allow a Department Officer of the assigned department to accept a complaint only while its status is `PENDING_DEPARTMENT_REVIEW`. In one transaction it **shall** set status `ACCEPTED`, `accepted_at` to the current UTC time, `accepted_by_user_id`, `sla_seconds` to the configured window, `resolution_due_at = accepted_at + sla_seconds`, append a history row, and create the citizen acceptance notification (NT-02). | P0 | T-DEPT, T-ESC |
| FR-020 | The system **shall** allow a Department Officer of the assigned department to reject a `PENDING_DEPARTMENT_REVIEW` complaint only with a reason of 10–1,000 characters. It **shall** set status `REJECTED`, record `rejected_at`, `rejected_by_user_id`, and `rejection_reason`, append history, create the citizen rejection notification (NT-03), and treat rejection as terminal in P0. | P0 | T-DEPT |
| FR-021 | The system **shall** allow an officer of the assigned department to assign a complaint to an active user of the same department, recording `assigned_to_user_id` and `assigned_at`. Assignment alone **shall not** change status or notify the citizen. | P0 | T-DEPT |
| FR-022 | The system **shall** allow an officer of the assigned department to add a progress note (5–2,000 characters) to an `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` complaint, optionally transitioning `ACCEPTED → IN_PROGRESS`. Each change **shall** record actor and timestamp, append history when the status changes, and create the citizen progress notification (NT-04). | P0 | T-DEPT |
| FR-023 | The system **shall** allow an officer of the assigned department to attach 1–3 JPEG/PNG/WebP images (≤5 MiB each, maximum 10 per complaint) as `PROGRESS` or `RESOLUTION` evidence while the status is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED`, storing uploader and timestamp. | P0 | T-UPLOAD |
| FR-024 | The system **shall** allow an officer of the assigned department to resolve a complaint from `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` with a resolution note (10–2,000 characters). It **shall** set status `RESOLVED`, `resolved_at`, `resolved_by_user_id`, and `resolution_note`, append history, and create the citizen resolution notification (NT-07). Resolution from any other status **shall** return HTTP 409. | P0 | T-DEPT, T-SUP |
| FR-025 | The system **shall** provide a Department Officer with a summary of their department's complaints counted by status and escalation state. | P0 | T-DEPT |
| FR-026 | The system **shall** allow an officer of the assigned department to add progress notes and evidence to an `ESCALATED` complaint without changing its status; such updates **shall** create NT-04 and remain visible to the Superintendent. | P0 | T-DEPT |

### 7.4 Automatic escalation

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-027 | At acceptance the system **shall** compute `resolution_due_at` as `accepted_at + sla_seconds`, where `sla_seconds` is the configured escalation window at that moment. It **shall never** compute the deadline from `submitted_at`. | P0 | T-ESC |
| FR-028 | The system **shall** run an automatic escalation check at startup and then at a configurable interval (default 60 seconds) without any human action. | P0 | T-ESC |
| FR-029 | The system **shall** create at most one escalation record per complaint for the lifetime of the complaint, including under repeated runs, retries, manual triggers, and concurrent worker instances. | P0 | T-ESC |
| FR-030 | When a candidate satisfies all escalation conditions, the system **shall** change its status to `ESCALATED`, set `escalated_at`, and append a history row with actor `SYSTEM`, previous status, new status, and reason `SLA_BREACH`. | P0 | T-ESC |
| FR-031 | The system **shall** create an escalation record containing `complaint_id` (unique), `escalation_number`, `previous_status`, `deadline_at`, `escalated_at`, `overdue_seconds`, `trigger_source`, and `reason_code`. | P0 | T-ESC |
| FR-032 | In the same transaction as escalation, the system **shall** create NT-05 notifications for every active Superintendent, every active officer of the responsible department, and the complaint's Citizen. | P0 | T-ESC, T-NOTIF |
| FR-033 | The system **shall** read the escalation window from configuration with a production default of 10,080 minutes (seven calendar days). A non-default window **shall** be accepted only when `ALLOW_DEMO_ESCALATION=true`; otherwise the system **shall** refuse to start or fall back to 10,080 minutes and log an error. | P0 | T-ESC |
| FR-034 | The system **shall** expose a token-protected internal endpoint that executes the same escalation function on demand for demonstration and tests, returning `{evaluated, escalated, skipped}` and creating no duplicates. | P0 | T-ESC |

### 7.5 Superintendent oversight

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-035 | The system **shall** provide a Superintendent queue of `ESCALATED` complaints sorted by overdue duration descending, showing tracking number, department, acceptance time, deadline, overdue duration, and current status. | P0 | T-SUP |
| FR-036 | The system **shall** show the Superintendent the complaint detail, responsible department, acceptance date, deadline, overdue duration computed at request time, and resolution information when present. | P0 | T-SUP |
| FR-037 | The system **shall** allow the Superintendent to read the complete timeline, progress notes, and evidence of escalated complaints. Read access to other complaints for oversight is permitted; operational actions remain restricted to escalated complaints, including their resolution. | P0 | T-SUP |
| FR-038 | The system **shall** allow the Superintendent to record an append-only action of type `INSTRUCTION`, `FOLLOW_UP`, `REASSIGN`, or `NOTE`, with a note of 5–2,000 characters, optional `directed_department_id`, actor identity, and UTC timestamp; the action **shall** appear in the timeline and create NT-06 for the department and citizen. | P0 | T-SUP |
| FR-039 | The system **shall** support directing a follow-up to the responsible department by recording `directed_department_id` and notifying that department. In P0 this is a directive; it **shall not** silently change the complaint's original `department_id`. | P0 | T-SUP |
| FR-040 | The system **shall** keep escalated complaints in the Superintendent queue and allow monitoring of subsequent departmental updates until the complaint becomes `RESOLVED`. | P0 | T-SUP |
| FR-041 | The system **shall** allow the Superintendent to resolve an `ESCALATED` complaint using the same resolution rules and notification as FR-024, recording the Superintendent as the resolving actor. | P0 | T-SUP |

### 7.6 In-app notifications

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-042 | The system **shall** create notification rows for triggers NT-01 through NT-07 inside the same database transaction as the triggering state change, so a committed status change cannot lack its notification records. | P0 | T-NOTIF |
| FR-043 | The system **shall** list only the authenticated user's notifications, newest first, paginated at 20, and **shall** return an unread count. | P0 | T-NOTIF |
| FR-044 | The system **shall** allow a user to mark one or all of their own notifications as read, idempotently, recording `read_at`; marking another user's notification **shall** return HTTP 404 (not 403, to avoid disclosure). | P0 | T-NOTIF |
| FR-045 | Notification content **shall** include the complaint tracking number and resulting status, plus trigger-specific fields: department and target date for NT-02, rejection reason for NT-03, progress note for NT-04, overdue duration for NT-05, action summary for NT-06, and resolution note for NT-07. | P0 | T-NOTIF |

### 7.7 Administration and configuration

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-046 | The system **shall** allow a Platform Administrator to create, update, list, and deactivate departments. Deactivation **shall** be blocked while active categories or active Department Officers reference the department. | P0 | T-ADMIN |
| FR-047 | The system **shall** allow a Platform Administrator to create, update, list, and deactivate complaint categories and to change the mapped department. A mapping **shall** reference an active department, and changes **shall** affect only complaints submitted afterwards. | P0 | T-ADMIN |
| FR-048 | The system **shall** provide a Platform Administrator with activity counts by complaint status and department, the number of escalations, and the 20 most recent timeline events across the platform. | P0 | T-ADMIN |
| FR-049 | The system **shall** allow a Platform Administrator to read audit logs filtered by actor, action, entity type, and date range. The audit log **shall** be read-only through the API; no update or delete operation **shall** be exposed. | P0 | T-ADMIN |

### 7.8 Audit and history

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-050 | The system **shall** append a status-history row for every status change, containing `complaint_id`, `from_status`, `to_status`, `actor_user_id` or null for system, `actor_role`, optional note, and a UTC timestamp. History rows **shall** never be updated or deleted through the API. | P0 | T-ESC, T-DEPT, T-SUP |

### 7.9 P1 requirements (optional, only after all P0 acceptance criteria pass)

| ID | Requirement | Priority | Test |
|---|---|---|---|
| FR-051 | The system **should** request a category suggestion from the Gemini API using the complaint title and description, display it with a confidence label, require explicit confirmation, and fall back to manual selection within 5 seconds on any error. | P1 | T-P1 |
| FR-052 | The system **should** show up to three same-category complaints within 500 metres and seven days of a new complaint as possible duplicates. The citizen **should** be able to submit anyway; no automatic merge **should** occur. | P1 | T-P1 |
| FR-053 | The system **should** display a Leaflet/OpenStreetMap view of complaints with coordinates, restricted to the viewer's permitted scope, with marker popups linking to complaint detail. | P1 | T-P1 |
| FR-054 | The system **should** suggest a priority (`LOW`, `MEDIUM`, `HIGH`) from the complaint text, require officer confirmation, and never block submission or routing on the suggestion. | P1 | T-P1 |
| FR-055 | The system **should** provide an Administrator analytics view of complaint counts by status, department, category, and age using Recharts. | P1 | T-P1 |
| FR-056 | The system **should** allow a Citizen to submit a rating (1–5) and optional comment (≤1,000 characters) for a `RESOLVED` complaint, once per complaint. | P1 | T-P1 |
| FR-057 | The system **should** allow a Citizen to request reopening of a `RESOLVED` complaint with a reason; a Department Officer **should** accept or decline. Acceptance **should** set `REOPENED` and, on re-acceptance, a new deadline. | P1 | T-P1 |

### 7.10 P2 requirements (documented only; not implemented in the hackathon)

| ID | Requirement | Priority |
|---|---|---|
| FR-058 | The system may add email, SMS, WhatsApp, or push notification adapters through an outbox pattern. | P2 |
| FR-059 | The system may support multiple municipalities with tenant isolation. | P2 |
| FR-060 | The system may support working-day, holiday, and paused SLA calendars. | P2 |
| FR-061 | The system may verify or classify evidence images automatically. | P2 |
| FR-062 | The system may expose a privacy-reviewed public transparency portal. | P2 |
| FR-063 | The system may provide native mobile applications. | P2 |
| FR-064 | The system may integrate with external municipal work-order systems. | P2 |

---

## 8. Non-Functional Requirements

| ID | Category | Requirement | Target / verification |
|---|---|---|---|
| NFR-001 | Performance | List endpoints **shall** respond within 1 second p95 and detail endpoints within 2 seconds p95 at demo volume (500 complaints, 50 concurrent users) | Load test at Hour 9; T-PERF |
| NFR-002 | Timeliness | The escalation worker **shall** detect a due complaint within one scheduler interval (default ≤60 seconds) of its deadline | Integration test with 2-minute window; T-ESC |
| NFR-003 | Concurrency | Concurrent escalation runs **shall** produce exactly one escalation record and one `ESCALATED` transition per complaint | 20-run and parallel-run test; T-ESC |
| NFR-004 | Credential security | Passwords **shall** be hashed with bcrypt cost ≥12 and never persisted, returned, or logged in plaintext | Code review + test; T-AUTH |
| NFR-005 | Authorization | 100% of protected API operations **shall** enforce role and object-scope checks server-side; UI hiding alone is insufficient | 12-case RBAC matrix; T-RBAC |
| NFR-006 | Session security | JWTs **shall** expire after 8 hours, be signed with a secret of at least 32 bytes, and be rejected when malformed, expired, or belonging to an inactive user | T-AUTH |
| NFR-007 | Privacy | Email, phone, location text, and coordinates **shall** be readable only by the owner, officers of the responsible department, the Superintendent, and Administrators | Field-level tests; T-RBAC |
| NFR-008 | Audit immutability | Status history, escalations, officer actions, and audit logs **shall** be append-only through the API | Attempt update/delete; T-ADMIN |
| NFR-009 | Time handling | All timestamps **shall** be stored in UTC with microsecond precision and displayed in `APP_TIMEZONE` | Boundary tests; T-ESC |
| NFR-010 | Usability | The complaint form **shall** be usable at 360 px width, expose at most five required inputs, and allow a first-time user to submit in ≤60 seconds | Timed usability run; T-E2E |
| NFR-011 | Reliability | A scheduler failure **shall** not lose data; the next successful run **shall** escalate all overdue complaints; records **shall** survive container restarts | Restart test; T-ESC |
| NFR-012 | Transactional integrity | Complaint creation, acceptance, escalation, resolution, and their notifications **shall** be atomic; a failure **shall** roll back all writes in the unit of work | Fault-injection test; T-ESC |
| NFR-013 | Upload safety | Uploads **shall** be limited to 5 MiB and three files per request, validated by magic bytes, stored with random names, and served only through an authorized endpoint | T-UPLOAD |
| NFR-014 | Compatibility | The UI **shall** function on the latest two major versions of Chrome, Edge, Firefox, and Safari | Manual matrix; T-E2E |
| NFR-015 | Accessibility | Forms **shall** have associated labels, keyboard-operable controls, visible focus, and text contrast ≥4.5:1 | Manual audit; T-E2E |
| NFR-016 | Maintainability | TypeScript strict mode, ESLint, Python `ruff`, typed Pydantic schemas, and `.env.example` **shall** be present | Review at Hour 9 |
| NFR-017 | Portability | After the documented `.env` setup, `docker compose up` **shall** start database, API, worker, and web with one command on a clean machine | Fresh-clone test |
| NFR-018 | Observability | Every escalation run **shall** log evaluated, escalated, skipped, duration, and errors; `/health` and `/health/ready` **shall** report API and database status, and worker liveness **shall** be visible through its container status and structured logs | Log inspection; T-ESC |
| NFR-019 | Retention | Complaints, history, escalations, actions, and audit logs **shall** not be hard-deleted; users and configuration use deactivation | API surface review |
| NFR-020 | Testability | Deadline calculation, routing, idempotency, and RBAC **shall** have automated unit/integration tests; the critical lifecycle **shall** have an end-to-end test | Test run at Hour 9 |
| NFR-021 | Log hygiene | Passwords, tokens, emails, phone numbers, location text, and coordinates **shall** not appear in application logs or URLs | Log review |
| NFR-022 | Capacity | The system **shall** support 500 complaints, 100 users, and 50 concurrent demo users with 2 GB image storage | Seeded-volume test |

---

## 9. Detailed Use Cases

### UC-01 — Submit a complaint

| Field | Value |
|---|---|
| Actors | Citizen (primary), System |
| Preconditions | User is authenticated with role `CITIZEN`; at least one active mapped category exists |
| Trigger | Citizen selects "Report a problem" and submits the form |
| Related FRs | FR-007–FR-013, FR-016, FR-042, FR-045 |

**Main flow**

1. System returns the active category catalogue.
2. Citizen selects a category and enters title, description, optional location, and optional images.
3. System validates lengths, category state, coordinate pair, file count, file size, and file signatures.
4. System begins a transaction, generates a unique tracking number, and inserts the complaint with `submitted_at = now(UTC)`.
5. System routes the complaint to the category's mapped department.
6. System writes history `null → SUBMITTED` (Citizen) and `SUBMITTED → PENDING_DEPARTMENT_REVIEW` (System).
7. System writes the NT-01 notification for the Citizen.
8. System commits and returns HTTP 201 with the complaint, tracking number, status, department, and timeline link.

**Alternate flows**

- A1: No image is attached — complaint is still valid.
- A2: No location is supplied — complaint is still valid.
- A3: Category is inactive — HTTP 422, nothing persisted.

**Exceptions**

- E1: Image exceeds 5 MiB — HTTP 422 with the offending file name; nothing persisted.
- E2: Coordinates incomplete or out of range — HTTP 422.
- E3: Database error — transaction rolls back; HTTP 500 with a request ID; retry does not duplicate because the client has not received a tracking number.

**Postconditions:** Complaint exists in `PENDING_DEPARTMENT_REVIEW`; history and NT-01 exist; department queue now includes it.

### UC-02 — Accept a complaint

| Field | Value |
|---|---|
| Actors | Department Officer (primary), System |
| Preconditions | Authenticated officer belongs to the complaint's department; complaint status is `PENDING_DEPARTMENT_REVIEW` |
| Trigger | Officer clicks Accept |
| Related FRs | FR-018, FR-019, FR-027, FR-042, FR-045 |

**Main flow**

1. System re-reads the complaint and verifies department scope and status.
2. System sets `accepted_at = now(UTC)`, `accepted_by_user_id`, `sla_seconds = configured window`, `resolution_due_at = accepted_at + sla_seconds`, and status `ACCEPTED`.
3. System appends the status history row.
4. System creates NT-02 for the Citizen with department, acceptance time, and deadline.
5. System commits and returns the updated complaint.

**Alternate flows**

- A1: Another officer accepted first — the conditional update affects zero rows; HTTP 409 `INVALID_TRANSITION`.
- A2: Officer belongs to a different department — HTTP 403, no read of sensitive fields.

**Postconditions:** Deadline stored; citizen notified; complaint appears as `ACCEPTED` in the department queue.

### UC-03 — Reject a complaint

| Field | Value |
|---|---|
| Actors | Department Officer, System |
| Preconditions | Same department; status `PENDING_DEPARTMENT_REVIEW` |
| Trigger | Officer selects Reject and supplies a reason |
| Related FRs | FR-018, FR-020, FR-042 |

**Main flow**

1. System validates the reason length (10–1,000 characters).
2. System sets status `REJECTED`, `rejected_at`, `rejected_by_user_id`, `rejection_reason`.
3. System appends history and creates NT-03 with the reason.
4. System commits and returns the updated complaint.

**Exceptions:** Missing or short reason → HTTP 422, no state change. Already decided → HTTP 409.

**Postconditions:** Rejection is terminal in P0; no deadline exists; citizen can read the reason.

### UC-04 — Record progress and resolve

| Field | Value |
|---|---|
| Actors | Department Officer, System |
| Preconditions | Complaint status is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED`; officer is in the assigned department |
| Trigger | Officer posts a progress note, assigns staff, or records a resolution |
| Related FRs | FR-021–FR-024, FR-026, FR-042 |

**Main flow (progress)**

1. System validates note length and status.
2. System inserts a progress comment, optionally transitions `ACCEPTED → IN_PROGRESS`, appends history for the transition, and creates NT-04.
3. System commits and returns the timeline event.

**Main flow (resolution)**

1. Officer supplies a resolution note and optional after-image.
2. System verifies status is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED`.
3. System sets `RESOLVED`, `resolved_at`, `resolved_by_user_id`, `resolution_note`, and optionally links the evidence image.
4. System appends history and creates NT-07.
5. System commits; the complaint leaves the escalation queue and the deadline no longer applies.

**Exceptions:** Resolution from `PENDING_DEPARTMENT_REVIEW`, `REJECTED`, `SUBMITTED`, or `RESOLVED` → HTTP 409. Note shorter than 10 characters → HTTP 422.

**Postconditions:** Citizen can see the update; the complaint is closed only by an authorized record.

### UC-05 — Automatic escalation

| Field | Value |
|---|---|
| Actors | System (scheduler), System (database) |
| Preconditions | Worker running; complaint accepted; status `ACCEPTED` or `IN_PROGRESS`; deadline reached; no escalation row |
| Trigger | APScheduler interval job (default every 60 seconds) or guarded manual trigger |
| Related FRs | FR-027–FR-034, FR-042, FR-050 |

**Main flow**

1. Worker acquires the escalation lock; if unavailable, logs a skip and exits.
2. Worker selects up to 100 candidates satisfying all conditions, ordered by deadline.
3. For each candidate, in a transaction, worker conditionally updates status to `ESCALATED`; if zero rows change, it skips.
4. Worker inserts the escalation row with unique `complaint_id`, deadline, escalation time, overdue seconds, and source.
5. Worker appends the system history row and creates NT-05 for the Superintendent(s), department officers, and citizen.
6. Worker commits per complaint, releases the lock, and logs the summary.

**Alternate flows**

- A1: No active Superintendent - escalation still commits; department and citizen are notified; Administrators receive the escalation notification and an audit event `ESCALATION_FALLBACK_NO_SUPERINTENDENT` is logged.
- A2: Complaint was resolved after the deadline but before this run — it is not a candidate and is not escalated.

**Exceptions:** Duplicate key on `escalations.complaint_id` → rollback that complaint and continue. Database unavailable → job logs an error and retries on the next interval.

**Postconditions:** Exactly one escalation row; status `ESCALATED`; three recipient groups notified; full history preserved.

### UC-06 — Superintendent reviews and intervenes

| Field | Value |
|---|---|
| Actors | Superintendent Officer, System |
| Preconditions | Escalated complaints exist; officer authenticated with role `SUPERINTENDENT_OFFICER` |
| Trigger | Officer opens the escalation queue and a complaint |
| Related FRs | FR-035–FR-041, FR-042, FR-050 |

**Main flow**

1. System returns escalated complaints sorted by overdue duration.
2. Officer opens a complaint and reviews the department, acceptance date, deadline, overdue duration, timeline, progress notes, and evidence.
3. Officer records an action with type, note, and optional directed department.
4. System appends the action, writes a history event, and creates NT-06 for the department officers and the citizen.
5. Officer monitors further departmental updates until resolution.
6. Optionally, the officer records the resolution (FR-041).

**Exceptions:** Acting on a non-escalated complaint with a supervisory action → HTTP 409. Empty note → HTTP 422.

**Postconditions:** Every supervisory action is attributable and visible; escalation remains until resolution.

### UC-07 — Unauthorized access is denied

| Field | Value |
|---|---|
| Actors | Citizen (attacker), System |
| Preconditions | Authenticated Citizen with a valid JWT |
| Trigger | Citizen calls a departmental or supervisory endpoint, or navigates to a protected route |
| Related FRs | FR-004, NFR-005 |

**Main flow**

1. Server authenticates the token and loads the current user.
2. Role dependency rejects the operation with HTTP 403.
3. No state change occurs; an audit log entry records the denied attempt.
4. The client shows a not-authorized page and no sensitive data.

**Postconditions:** Role boundary intact; no data disclosure beyond the citizen's own records.

---

## 10. Input and Output Requirements

### 10.1 Authentication inputs

| Field | Type | Required | Validation | Error |
|---|---|---|---|---|
| full_name | string | Yes (register) | Trimmed, 2–120 characters | 422 |
| email | string | Yes | Valid email, ≤190 characters, unique case-insensitive | 409 if exists |
| password | string | Yes | 8–72 characters, ≥1 letter, ≥1 digit; never echoed | 422 |
| phone | string | No | 7–20 characters from digits, `+`, spaces, `-` | 422 |
| role | enum | No (admin only) | One of the four role codes | 422 |
| department_id | integer | Conditional | Required and active when role is `DEPARTMENT_OFFICER` | 422 |

### 10.2 Complaint submission inputs

| Field | Type | Required | Validation | Error |
|---|---|---|---|---|
| title | string | Yes | 5–150 characters after trim | 422 |
| description | string | Yes | 20–2,000 characters after trim | 422 |
| category_id | integer | Yes | Exists, active, mapped to an active department | 422 |
| location_text | string | No | ≤255 characters | 422 |
| latitude | decimal | No | −90 to 90; requires longitude | 422 |
| longitude | decimal | No | −180 to 180; requires latitude | 422 |
| images | file[] | No | 0–3 files; JPEG/PNG/WebP; ≤5 MiB each; signature verified | 422 |

### 10.3 Department action inputs

| Action | Fields | Validation |
|---|---|---|
| Accept | none | Status must be `PENDING_DEPARTMENT_REVIEW`; department must match |
| Reject | `reason` | 10–1,000 characters |
| Assign | `assignee_user_id` | Active user in the same department |
| Progress | `note`, optional `set_status=IN_PROGRESS` | 5–2,000 characters; status must allow the transition |
| Evidence | `kind` = `PROGRESS` or `RESOLUTION`, 1–3 images | Status `ACCEPTED`/`IN_PROGRESS`/`ESCALATED`; ≤10 images per complaint |
| Resolve | `resolution_note`, optional `evidence_image_ids` | 10–2,000 characters; status `ACCEPTED`/`IN_PROGRESS`/`ESCALATED` |

### 10.4 Superintendent action inputs

| Field | Type | Required | Validation |
|---|---|---|---|
| action_type | enum | Yes | `INSTRUCTION`, `FOLLOW_UP`, `REASSIGN`, `NOTE` |
| note | string | Yes | 5–2,000 characters |
| directed_department_id | integer | No | Active department; defaults to the complaint's department |

### 10.5 Output requirements

| Output | Content | Rules |
|---|---|---|
| Complaint summary | id, tracking number, title, category, department, status, submitted time, accepted time, deadline, overdue flag | No PII beyond the viewer's scope |
| Complaint detail | Summary plus description, location, images metadata, resolution summary | Coordinates only for authorized roles |
| Timeline event | event type, timestamp, actor display name or `SYSTEM`, from/to status, note | Sorted ascending; internal notes excluded from citizen view |
| Department queue | Paginated summaries plus per-status counts | Department-scoped only |
| Escalation queue | Summaries plus deadline and overdue duration | Sorted by overdue duration descending |
| Notification | id, trigger code, title, body, complaint id, read flag, created time | Owner-only |
| Error | HTTP status, `error.code`, `error.message`, optional `details`, `request_id` | No stack traces, SQL, or secrets |
| Pagination | `items`, `page`, `page_size`, `total`, `total_pages` | `page_size` default 20, maximum 100 |

### 10.6 Standard error envelope

```json
{
  "error": {
    "code": "INVALID_TRANSITION",
    "message": "Complaint cannot be accepted from status REJECTED.",
    "details": { "current_status": "REJECTED" }
  },
  "request_id": "7f3c2a1e-9a4b-4a5e-9f0d-1c2b3a4d5e6f"
}
```

---

## 11. Business Rules

| ID | Rule | Enforced by |
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

### 11.1 Authoritative transition table

| From | To | Actor | Guard | Side effects |
|---|---|---|---|---|
| `SUBMITTED` | `PENDING_DEPARTMENT_REVIEW` | System | Routing succeeded | History; NT-01 |
| `PENDING_DEPARTMENT_REVIEW` | `ACCEPTED` | Department Officer | Same department; status matches | `accepted_at`, `sla_seconds`, `resolution_due_at`; history; NT-02 |
| `PENDING_DEPARTMENT_REVIEW` | `REJECTED` | Department Officer | Same department; reason valid | Rejection fields; history; NT-03 |
| `ACCEPTED` | `IN_PROGRESS` | Department Officer | Progress note valid | Comment; history; NT-04 |
| `ACCEPTED` | `RESOLVED` | Department Officer | Resolution note valid | Resolution fields; history; NT-07 |
| `IN_PROGRESS` | `RESOLVED` | Department Officer | Resolution note valid | Resolution fields; history; NT-07 |
| `ACCEPTED` | `ESCALATED` | System | Deadline reached; no escalation | Escalation row; history; NT-05 |
| `IN_PROGRESS` | `ESCALATED` | System | Deadline reached; no escalation | Escalation row; history; NT-05 |
| `ESCALATED` | `RESOLVED` | Department Officer or Superintendent | Resolution note valid | Resolution fields; history; NT-07 |
| `RESOLVED` | `REOPENED` | System (P1) | Reopening accepted | Reopen fields; history; NT-08 |
| `REOPENED` | `IN_PROGRESS` | Department Officer (P1) | New note and new deadline | `accepted_at` refreshed; history |

**Superintendent resolution is available only from `ESCALATED` (FR-041).** `ACCEPTED` and `IN_PROGRESS` complaints are resolved by an officer of the assigned department. Any other transition returns `409 INVALID_TRANSITION` and changes nothing.

---

## 12. Role-Based Access Requirements

### 12.1 Permission matrix

Legend: **C** create, **R** read, **U** update, **A** operational action, **—** denied.

| Operation | Citizen | Department Officer | Superintendent | Administrator |
|---|---|---|---|---|
| Register (self) | C | — | — | — |
| Log in / log out | C | C | C | C |
| Read own profile | R | R | R | R |
| Submit complaint | C | — | — | — |
| Read own complaints | R | — | — | — |
| Read any complaint (oversight) | — | — | R (all; act only on escalated) | R (read-only) |
| Read department complaints | — | R (own department) | R (all) | — |
| Accept / reject | — | A (own department) | — | — |
| Assign staff | — | A (own department) | — | — |
| Add progress / evidence | — | A (own department) | — | — |
| Resolve | — | A (own department) | A (escalated) | — |
| View escalation queue | — | — | R | — |
| Record supervisory action | — | — | A | — |
| Read notifications | R (own) | R (own) | R (own) | R (own) |
| Mark notifications read | U (own) | U (own) | U (own) | U (own) |
| Manage users and roles | — | — | — | C/U |
| Manage departments/categories/mappings | — | — | — | C/U |
| View activity and audit logs | — | — | — | R |

### 12.2 Enforcement requirements

| ID | Requirement |
|---|---|
| RBAC-01 | Every protected endpoint **shall** declare its allowed roles and enforce them server-side. |
| RBAC-02 | Department Officers **shall** be scoped by `department_id` on every read and write; client-supplied department ids **shall** be ignored or rejected. |
| RBAC-03 | Citizens **shall** never receive another user's PII, coordinates, notifications, or complaint details. |
| RBAC-04 | Administrators **shall not** inherit operational accept/reject/progress/resolve permissions. |
| RBAC-05 | The Superintendent **shall** perform write actions only on `ESCALATED` complaints; reading other complaints for oversight is permitted. |
| RBAC-06 | Deactivated users **shall** be rejected on the next request even if their JWT has not expired. |
| RBAC-07 | UI route guards **shall** be advisory only; API enforcement is authoritative. |
| RBAC-08 | Denied attempts **shall** produce an audit entry with actor, route, method, and timestamp. |

---

## 13. Notification Requirements

| ID | Trigger | Recipients | Required content | Channel | Timing | FR |
|---|---|---|---|---|---|---|
| NT-01 | Complaint submitted | Citizen | Tracking number, category, department, submitted time | In-app | Same transaction as submission | FR-042 |
| NT-02 | Complaint accepted | Citizen | Tracking number, department name, accepting officer, acceptance time, deadline | In-app | Same transaction as acceptance | FR-019, FR-042 |
| NT-03 | Complaint rejected | Citizen | Tracking number, department, rejection reason | In-app | Same transaction as rejection | FR-020, FR-042 |
| NT-04 | Progress update or status change | Citizen | Tracking number, new status, progress note | In-app | Same transaction as update | FR-022, FR-026 |
| NT-05 | Automatic escalation | Every active Superintendent, every active officer of the responsible department, Citizen | Tracking number, department, deadline, overdue duration, escalation time | In-app | Same transaction as escalation | FR-032 |
| NT-06 | Supervisory action recorded | Officers of the responsible department, Citizen | Tracking number, action type, note summary, Superintendent identity, timestamp | In-app | Same transaction as action | FR-038 |
| NT-07 | Complaint resolved | Citizen | Tracking number, resolution note, resolving officer, resolution time | In-app | Same transaction as resolution | FR-024, FR-041 |
| NT-08 | Reopening accepted (P1) | Department officers, Citizen | Tracking number, reopened status, reason | In-app | Same transaction as reopening | FR-057 |

### 13.1 Notification rules

- Notifications are **persisted rows**, not transient UI toasts.
- A notification row stores recipient, trigger code, complaint reference, title, body, read flag, and creation time.
- The recipient set is resolved at trigger time; later role changes do not retroactively create notifications.
- When no active Superintendent exists, the escalation still proceeds; administrators receive the NT-05 content and an audit event is recorded.
- Citizens can read only their own notifications; marking another user's notification returns 404.
- Polling every 30 seconds is the P0 delivery mechanism; no websocket or push channel exists.

---

## 14. Escalation Requirements

### 14.1 Normative definition

A complaint is escalated when and only when:

```
accepted_at IS NOT NULL
AND status IN ('ACCEPTED', 'IN_PROGRESS')
AND resolution_due_at IS NOT NULL
AND now_utc >= resolution_due_at
AND NOT EXISTS (SELECT 1 FROM escalations WHERE complaint_id = complaint.id)
```

The default window is **10,080 minutes** (7 × 24 × 60), stored per complaint as `sla_seconds` at acceptance. `resolution_due_at = accepted_at + sla_seconds`.

### 14.2 Timing requirements

| ID | Requirement |
|---|---|
| ESC-01 | The timer starts at `accepted_at`, recorded in UTC, and never at `submitted_at`. |
| ESC-02 | The deadline is inclusive: at `now == resolution_due_at`, the complaint is eligible for escalation. |
| ESC-03 | Calendar days are consecutive 24-hour periods; weekends and holidays count. |
| ESC-04 | The check runs at startup and every `ESCALATION_CHECK_SECONDS` (default 60). |
| ESC-05 | A scheduler outage delays but does not cancel escalation; the next successful run escalates every due complaint and records actual `escalated_at` and computed `overdue_seconds`. |
| ESC-06 | Changing the configured window affects only complaints accepted after the change; stored `sla_seconds` and `resolution_due_at` are immutable after acceptance. |
| ESC-07 | A complaint resolved before the escalation transaction commits is not escalated, even if the scheduler run started earlier. |
| ESC-08 | Escalation does not alter `department_id`, `accepted_at`, `accepted_by_user_id`, or the original deadline. |
| ESC-09 | The escalation status is sticky until `RESOLVED`; departmental progress does not revert it. |
| ESC-10 | There is no re-escalation in P0; a second escalation requires a future authorized workflow and schema change. |

### 14.3 Idempotency requirements

| ID | Requirement |
|---|---|
| IDEM-01 | `escalations.complaint_id` **shall** have a unique constraint. |
| IDEM-02 | The status update **shall** be conditional on the current status being `ACCEPTED` or `IN_PROGRESS`. |
| IDEM-03 | The worker **shall** hold a database advisory lock (for example `GET_LOCK`) so that only one scheduler instance processes candidates at a time. |
| IDEM-04 | Candidate selection **shall** exclude complaints that already have an escalation row. |
| IDEM-05 | Duplicate-key or zero-row-update outcomes **shall** be treated as a skip, not an error. |
| IDEM-06 | A manual trigger and the scheduled run **shall** use the same function and the same guarantees. |

### 14.4 Edge cases

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

### 14.5 Demonstration configuration

| Variable | Production value | Demo value | Guard |
|---|---|---|---|
| `ESCALATION_WINDOW_MINUTES` | `10080` | `2` | Non-default requires `ALLOW_DEMO_ESCALATION=true` |
| `ALLOW_DEMO_ESCALATION` | `false` | `true` | Startup banner and log warning in demo mode |
| `ESCALATION_CHECK_SECONDS` | `60` | `30` | Minimum 5 seconds |

The worker **shall** log the effective window at startup. The documentation and UI **shall** label a shortened window as a demo configuration. Tests **shall** cover both the 10,080-minute default and a shortened window.

---

## 15. Database Requirements

### 15.1 Required entities

The system **shall** persist at least these eleven tables, named identically in the TRD:

`users`, `departments`, `complaint_categories`, `complaints`, `complaint_images`, `complaint_status_history`, `complaint_comments`, `notifications`, `escalations`, `officer_actions`, `audit_logs`.

### 15.2 Integrity requirements

| ID | Requirement |
|---|---|
| DB-01 | InnoDB, `utf8mb4`, UTC session timezone, `DATETIME(6)` timestamps. |
| DB-02 | `complaints.citizen_id` references `users.id`; `complaints.department_id` references `departments.id`; both non-null. |
| DB-03 | `complaint_categories.department_id` is non-null and references an active department at creation. |
| DB-04 | `escalations.complaint_id` is unique and references `complaints.id`. |
| DB-05 | History, escalations, officer actions, notifications, and audit logs are append-only through the API. |
| DB-06 | Status, role, image kind, and action type values are constrained to the documented enumerations. |
| DB-07 | Indexes support queue queries: `(department_id, status, submitted_at)`, escalation candidates `(status, resolution_due_at)`, notifications `(recipient_user_id, is_read, created_at)`, and timeline `(complaint_id, created_at)`. |
| DB-08 | Foreign keys use `RESTRICT` for core entities so records cannot be orphaned by deletion. |
| DB-09 | A single initial migration and a repeatable seed script exist; seeded data is idempotent. |
| DB-10 | Tracking numbers are generated under a uniqueness constraint with retry on collision. |

### 15.3 Transaction requirements

| Unit of work | Atomic writes |
|---|---|
| Submission | Complaint, routing fields, two history rows, image rows, NT-01 |
| Acceptance | Status, acceptance fields, history, NT-02 |
| Rejection | Status, rejection fields, history, NT-03 |
| Progress | Comment, optional status/fields, history, NT-04 |
| Escalation | Status, escalation row, history, three-recipient NT-05 |
| Resolution | Status, resolution fields, image link, history, NT-07 |
| Supervisory action | Officer action, history event, NT-06 |

---

## 16. Security and Privacy Requirements

| ID | Requirement |
|---|---|
| SEC-01 | All production traffic uses HTTPS; the API sets HSTS at the proxy. |
| SEC-02 | Passwords use bcrypt with cost ≥12; no reversible storage. |
| SEC-03 | JWT secrets come from environment variables, are at least 32 bytes, and are never committed. |
| SEC-04 | JWTs expire after 8 hours; malformed, expired, or inactive-user tokens return 401. |
| SEC-05 | CORS allows only configured frontend origins and required methods/headers. |
| SEC-06 | Login is rate-limited to 5 attempts per minute per IP+email pair; responses are generic. |
| SEC-07 | All SQL uses parameterized queries or the ORM; no string interpolation of user input. |
| SEC-08 | React escapes output by default; no `dangerouslySetInnerHTML` with user content. |
| SEC-09 | File uploads are validated by signature, renamed randomly, stored outside the web root, and served through an authorized endpoint with `Content-Disposition` and a safe content type. |
| SEC-10 | Object-level authorization prevents IDOR: every complaint, image, notification, and action is checked against the caller's scope. |
| SEC-11 | PII and coordinates are excluded from logs, URLs, and error messages. |
| SEC-12 | Audit logs record authentication failures, denied access, role changes, configuration changes, and status transitions. |
| SEC-13 | Server errors return a generic message and request id; stack traces are logged server-side only. |
| SEC-14 | Database credentials and API keys are environment-scoped; the demo Gemini key is not shipped in the frontend. |
| SEC-15 | The UI displays a persistent "prototype, not an official municipal service" notice. |
| SEC-16 | Privacy: email/phone are visible to the owner and administrators only; location and coordinates to the owner, responsible department officers, Superintendent, and administrators. |

**Token storage decision (documented tradeoff):** the frontend and API may be hosted on different origins (Vercel + API host), so the P0 implementation stores the JWT in `sessionStorage` and sends it in the `Authorization: Bearer` header. This avoids cross-site cookie failures during the demo. Mitigations: short 8-hour expiry, no token in URLs, strict CSP where hosting allows, React escaping, dependency audit, and a documented P2 upgrade to same-domain httpOnly cookies with CSRF protection.

---

## 17. Error Handling

### 17.1 HTTP status usage

| Status | Use |
|---|---|
| 200 | Successful read or update |
| 201 | Complaint or user created |
| 204 | Logout, delete-like acknowledgment, mark-all-read |
| 400 | Malformed JSON or invalid enum syntax |
| 401 | Missing, malformed, expired token, or invalid credentials |
| 403 | Authenticated but role/scope not permitted |
| 404 | Resource does not exist or is outside the caller's ownership scope (avoid disclosure); department-scope violations return 403 |
| 409 | State conflict: duplicate email, invalid transition, duplicate escalation |
| 413 | Upload exceeds size limit |
| 422 | Validation failure with field details |
| 429 | Rate limit exceeded |
| 500 | Unexpected server error, logged with a request id |
| 503 | Database or dependency unavailable |

### 17.2 Application error codes

| Code | HTTP | Meaning |
|---|---|---|
| `VALIDATION_ERROR` | 422 | One or more fields invalid; `details` maps fields to messages |
| `INVALID_CREDENTIALS` | 401 | Email/password mismatch or inactive account |
| `TOKEN_INVALID` | 401 | Missing, malformed, or expired token |
| `FORBIDDEN` | 403 | Role or department scope denies the operation |
| `NOT_FOUND` | 404 | Resource absent or out of scope |
| `EMAIL_ALREADY_REGISTERED` | 409 | Duplicate registration |
| `INVALID_TRANSITION` | 409 | Status does not allow the requested action |
| `DUPLICATE_ESCALATION` | 409 | Escalation record already exists (internal, typically skipped) |
| `CATEGORY_NOT_MAPPED` | 422 | Category inactive or lacks a department |
| `UPLOAD_TOO_LARGE` | 413 | File exceeds 5 MiB |
| `UNSUPPORTED_MEDIA_TYPE` | 422 | File signature is not JPEG/PNG/WebP |
| `RATE_LIMITED` | 429 | Too many login attempts |
| `INTERNAL_ERROR` | 500 | Unexpected failure |

### 17.3 Error behavior rules

1. Validation occurs before any write; a failed request changes nothing.
2. Multi-row operations use one transaction; any failure rolls back the unit of work.
3. A notification insert failure rolls back the associated action so the timeline and inbox cannot diverge.
4. A scheduler failure never corrupts a complaint; the next run retries from timestamps, not from a queue.
5. Errors never expose stack traces, SQL, secrets, or another user's data.
6. The frontend maps `INVALID_TRANSITION` to a readable message such as "This complaint has already been decided."

---

## 18. System Constraints

| ID | Constraint |
|---|---|
| CON-01 | The implementation must be completable by a small team in ten hours; P0 is the priority. |
| CON-02 | The stack is fixed: React + Vite + TypeScript + Tailwind + shadcn/ui + React Router + Recharts; FastAPI + SQLAlchemy + MySQL 8.4; APScheduler; Docker Compose; JWT. |
| CON-03 | Notifications are in-app only in P0. |
| CON-04 | The scheduler runs in a long-lived process, not in a serverless function. |
| CON-05 | The frontend must be a responsive web app, not a native app. |
| CON-06 | The system serves one municipality and one timezone configuration. |
| CON-07 | AI (Gemini) and the map (Leaflet/OSM) are P1 and must not gate submission, routing, acceptance, escalation, or resolution. |
| CON-08 | No real municipal data, credentials, or partnerships are assumed. |
| CON-09 | Uploads are limited to images and a persistent local volume in P0. |
| CON-10 | Demo data and the demo escalation window must be clearly separated from production defaults. |

---

## 19. Acceptance Criteria

These are the release gates for the hackathon. All must pass in one continuous run.

| ID | Criterion | Requirements |
|---|---|---|
| AC-01 | A new Citizen can register, log in, and view their own profile. | FR-001–FR-005 |
| AC-02 | A Citizen can submit a complaint with title, description, active category, optional images, and optional location, and receives a unique tracking number. | FR-007–FR-013 |
| AC-03 | The complaint appears only in the mapped department's queue and in the owning Citizen's list; another department and another citizen cannot see it. | FR-012, FR-014, FR-018, FR-004 |
| AC-04 | A Department Officer accepts the complaint; `accepted_at` is recorded; the Citizen receives NT-02 with the department and target date; the deadline equals acceptance plus the configured window. | FR-019, FR-027, FR-042 |
| AC-05 | A Department Officer rejects a different complaint with a reason; the Citizen receives NT-03 containing that reason; no deadline exists. | FR-020, FR-045 |
| AC-06 | Department progress updates appear in the Citizen timeline with status, note, actor, and timestamp. | FR-016, FR-022, FR-050 |
| AC-07 | An accepted complaint past its deadline is escalated automatically without human action, and the status becomes `ESCALATED`. | FR-028–FR-031 |
| AC-08 | Repeating the escalation check 20 times produces exactly one escalation row and one escalation transition. | FR-029, NFR-003 |
| AC-09 | The Superintendent sees the escalated complaint with department, acceptance time, deadline, overdue duration, and full timeline. | FR-035–FR-037 |
| AC-10 | The Superintendent records an instruction; it appears in the timeline with officer identity and timestamp, and the department and Citizen receive NT-06. | FR-038, FR-045, FR-050 |
| AC-11 | An authorized officer resolves the escalated complaint with a note; the Citizen receives NT-07; the complaint leaves the escalation queue. | FR-024, FR-041, FR-042 |
| AC-12 | A complaint is never displayed as resolved without a recorded resolution row and status history. | FR-024, BR-20 |
| AC-13 | A Citizen receives 403 on department and Superintendent endpoints and sees no department navigation. | FR-004, RBAC-01–RBAC-08 |
| AC-14 | A Department Officer cannot read or act on another department's complaint (403). | FR-018, RBAC-02 |
| AC-15 | Notifications are owner-only, show unread counts, and can be marked read. | FR-043, FR-044 |
| AC-16 | The production default window is 10,080 minutes and a shortened demo window is visibly labeled and guarded by `ALLOW_DEMO_ESCALATION`. | FR-033, FR-034 |

---

## 20. Traceability Matrix

Test groups are defined in TRD §20: `T-AUTH`, `T-RBAC`, `T-COMP`, `T-UPLOAD`, `T-DEPT`, `T-ESC`, `T-SUP`, `T-NOTIF`, `T-ADMIN`, `T-PERF`, `T-E2E`, `T-P1`.

### 20.1 P0 requirements

| FR | Story IDs | Use case | TRD section | API | Test |
|---|---|---|---|---|---|
| FR-001 | US-CIT-01 | UC-01 | §9 | `POST /auth/register` | T-AUTH |
| FR-002 | US-CIT-02 | — | §9 | `POST /auth/login`, `POST /auth/logout` | T-AUTH |
| FR-003 | US-CIT-01, US-CIT-02 | — | §9 | `POST /auth/register`, `POST /auth/login` | T-AUTH |
| FR-004 | US-SYS-01, US-CIT-15 | UC-07 | §9, §17 | All protected routes | T-RBAC |
| FR-005 | US-CIT-17 | — | §9 | `GET /auth/me` | T-AUTH |
| FR-006 | US-ADM-01 | — | §5, §9 | `/admin/users` | T-ADMIN |
| FR-007 | US-CIT-03 | UC-01 | §8 | `GET /categories` | T-COMP |
| FR-008 | US-CIT-03 | UC-01 | §8, §5 | `POST /complaints` | T-COMP |
| FR-009 | US-CIT-06 | UC-01 | §7, §13 | `POST /complaints` | T-COMP |
| FR-010 | US-CIT-04 | UC-01 | §10 | `POST /complaints` | T-UPLOAD |
| FR-011 | US-CIT-05 | UC-01 | §8 | `POST /complaints` | T-COMP |
| FR-012 | US-CIT-06 | UC-01 | §12 | `POST /complaints` | T-COMP |
| FR-013 | US-CIT-03 | UC-01 | §13, §15 | `POST /complaints` | T-COMP |
| FR-014 | US-CIT-07 | — | §8 | `GET /complaints` | T-COMP |
| FR-015 | US-CIT-08 | — | §8 | `GET /complaints/{id}` | T-COMP |
| FR-016 | US-CIT-08 | — | §8 | `GET /complaints/{id}/timeline` | T-COMP |
| FR-017 | US-DEP-01 | — | §8 | `GET /department/complaints` | T-DEPT |
| FR-018 | US-DEP-02 | UC-02 | §8, §9 | `GET /complaints/{id}` | T-RBAC |
| FR-019 | US-DEP-03 | UC-02 | §8, §13 | `POST /complaints/{id}/accept` | T-DEPT, T-ESC |
| FR-020 | US-DEP-04 | UC-03 | §8 | `POST /complaints/{id}/reject` | T-DEPT |
| FR-021 | US-DEP-05 | — | §8 | `POST /complaints/{id}/assign` | T-DEPT |
| FR-022 | US-DEP-06 | UC-04 | §8 | `POST /complaints/{id}/progress` | T-DEPT |
| FR-023 | US-DEP-06 | UC-04 | §10 | `POST /complaints/{id}/images` | T-UPLOAD |
| FR-024 | US-DEP-07, US-SUP-05 | UC-04 | §8 | `POST /complaints/{id}/resolve` | T-DEPT, T-SUP |
| FR-025 | US-DEP-01 | — | §8 | `GET /department/summary` | T-DEPT |
| FR-026 | US-DEP-08 | UC-04 | §8 | `POST /complaints/{id}/progress` | T-DEPT |
| FR-027 | US-DEP-03 | UC-02 | §13 | `POST /complaints/{id}/accept` | T-ESC |
| FR-028 | US-SYS-02 | UC-05 | §13, §14 | Worker + `POST /internal/escalations/run` | T-ESC |
| FR-029 | US-SYS-03 | UC-05 | §13, §14 | Worker | T-ESC |
| FR-030 | US-SYS-02 | UC-05 | §13 | Worker | T-ESC |
| FR-031 | US-SYS-02 | UC-05 | §7, §13 | Worker | T-ESC |
| FR-032 | US-SYS-02, US-SUP-01 | UC-05 | §11 | Worker | T-NOTIF |
| FR-033 | US-ADM-06 | — | §13, §19 | Worker config | T-ESC |
| FR-034 | US-ADM-06 | — | §8, §14 | `POST /internal/escalations/run` | T-ESC |
| FR-035 | US-SUP-01 | — | §8 | `GET /superintendent/escalations` | T-SUP |
| FR-036 | US-SUP-02 | UC-06 | §8, §13 | `GET /complaints/{id}` | T-SUP |
| FR-037 | US-SUP-02 | UC-06 | §8 | `GET /complaints/{id}/timeline` | T-SUP |
| FR-038 | US-SUP-03 | UC-06 | §8 | `POST /complaints/{id}/superintendent-actions` | T-SUP |
| FR-039 | US-SUP-04 | UC-06 | §8 | `POST /complaints/{id}/superintendent-actions` | T-SUP |
| FR-040 | US-SUP-05 | UC-06 | §8 | `GET /superintendent/escalations` | T-SUP |
| FR-041 | US-SUP-05 | UC-06 | §8 | `POST /complaints/{id}/resolve` | T-SUP |
| FR-042 | US-SYS-03 | UC-01–UC-06 | §11 | All action endpoints | T-NOTIF |
| FR-043 | US-CIT-14 | — | §8, §11 | `GET /notifications` | T-NOTIF |
| FR-044 | US-CIT-14 | — | §8 | `POST /notifications/{id}/read` | T-NOTIF |
| FR-045 | US-CIT-09, US-CIT-10, US-CIT-11, US-CIT-12, US-CIT-13 | — | §11 | All notification-producing actions | T-NOTIF |
| FR-046 | US-ADM-02 | — | §5, §8 | `/admin/departments` | T-ADMIN |
| FR-047 | US-ADM-03 | — | §12 | `/admin/categories` | T-ADMIN |
| FR-048 | US-ADM-04 | — | §8 | `/admin/activity` | T-ADMIN |
| FR-049 | US-ADM-05 | — | §15 | `/admin/audit-logs` | T-ADMIN |
| FR-050 | US-DEP-03, US-SUP-03, US-SYS-02 | UC-05, UC-06 | §15 | Read-only timeline | T-ESC, T-DEPT, T-SUP |

### 20.2 P1 and P2 requirements

| FR | Story | TRD section | Test |
|---|---|---|---|
| FR-051 | US-P1-01 | §5 | T-P1 |
| FR-052 | US-P1-02 | §12 | T-P1 |
| FR-053 | US-P1-03 | §4 | T-P1 |
| FR-054 | US-P1-01 | §5 | T-P1 |
| FR-055 | US-P1-04 | §4 | T-P1 |
| FR-056 | US-CIT-16 | §5, §8 | T-P1 |
| FR-057 | US-CIT-16 | §5, §8 | T-P1 |
| FR-058–FR-064 | — (future) | §22 roadmap | Not built |

### 20.3 Story coverage check

| Story range | Count | All mapped to FRs |
|---|---|---|
| US-CIT-01 – US-CIT-17 | 17 | Yes |
| US-DEP-01 – US-DEP-08 | 8 | Yes |
| US-SUP-01 – US-SUP-05 | 5 | Yes |
| US-ADM-01 – US-ADM-06 | 6 | Yes |
| US-SYS-01 – US-SYS-03 | 3 | Yes |
| US-P1-01 – US-P1-04 | 4 | Yes |
| US-E2E-01 | 1 | Yes (end-to-end) |

---

## Appendix A — Requirement summary by priority

| Priority | FR range | Count | Included in demo |
|---|---|---|---|
| P0 | FR-001–FR-050 | 50 | Mandatory |
| P1 | FR-051–FR-057 | 7 | Only if P0 complete |
| P2 | FR-058–FR-064 | 7 | Not built |

## Appendix B — Non-functional requirement summary

| Category | NFRs |
|---|---|
| Performance and capacity | NFR-001, NFR-002, NFR-022 |
| Concurrency and reliability | NFR-003, NFR-011, NFR-012 |
| Security | NFR-004, NFR-005, NFR-006, NFR-013, SEC-01–SEC-16 |
| Privacy and audit | NFR-007, NFR-008, NFR-019, NFR-021 |
| Time | NFR-009 |
| Usability and accessibility | NFR-010, NFR-014, NFR-015 |
| Maintainability and portability | NFR-016, NFR-017 |
| Observability and testability | NFR-018, NFR-020 |

## Appendix C — Mapping from the original brief

| Brief ID | Requirement | This SRS |
|---|---|---|
| FR-01 | Submit complaint with description, optional image/location | FR-008, FR-010, FR-011 |
| FR-02 | Unique tracking ID and submission timestamp | FR-009, FR-013 |
| FR-03 | Route to department by category mapping | FR-012 |
| FR-04 | Only assigned department officer may accept/reject | FR-004, FR-018, FR-019, FR-020 |
| FR-05 | Acceptance timestamp and citizen notification | FR-019, FR-042 |
| FR-06 | Status and chronological timeline | FR-015, FR-016 |
| FR-07 | Seven-calendar-day deadline from acceptance | FR-027, FR-033 |
| FR-08 | Automatic escalation after deadline | FR-028–FR-031 |
| FR-09 | Notify Superintendent, department, citizen | FR-032 |
| FR-10 | Superintendent intervention notes | FR-038, FR-039 |
| FR-11 | Audit/history of status, actor, timestamp | FR-050 |
| FR-12 | Authorized resolution with note and evidence | FR-024, FR-041 |

---

*End of SRS.*
