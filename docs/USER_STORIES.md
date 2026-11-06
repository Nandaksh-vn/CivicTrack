# CivicTrack — User Stories and Acceptance Criteria

| Field | Value |
|---|---|
| Product | CivicTrack — Community Problem Reporting and Resolution Platform |
| Document | User Stories and Acceptance Criteria |
| Version | 1.0 |
| Date | 06 November 2026 |
| Status | Approved for 10-hour hackathon build |
| Companion documents | `PRD.md`, `SRS.md`, `TRD.md` |

---

## 1. How to Read This Document

Each story contains:

- **Story ID** — permanent identifier (`US-CIT`, `US-DEP`, `US-SUP`, `US-ADM`, `US-SYS`, `US-P1`, `US-E2E`).
- **Role, priority, and story** — in the form "As a …, I want …, so that …".
- **Preconditions** — what must be true before the story can be exercised.
- **Acceptance criteria** — Given/When/Then scenarios that determine pass or fail.
- **Expected system behavior** — the invariant the implementation must preserve.
- **Requirements** — the SRS functional requirement IDs implemented by the story.

Priority follows the PRD: **P0** is mandatory for the demo; **P1** is optional and must not block P0; **P2** is not implemented.

**Canonical facts** (roles, statuses, transitions, notification triggers, and the seven-day rule) are defined in PRD Appendix A and SRS §11–§14. If a story appears to conflict with those sections, the SRS wins and the story is a defect.

### 1.1 Canonical roles, statuses, and feature names

| Role code | Display name |
|---|---|
| `CITIZEN` | Citizen |
| `DEPARTMENT_OFFICER` | Department Officer |
| `SUPERINTENDENT_OFFICER` | Superintendent Officer |
| `PLATFORM_ADMIN` | Platform Administrator |

**Statuses:** `SUBMITTED`, `PENDING_DEPARTMENT_REVIEW`, `ACCEPTED`, `IN_PROGRESS`, `REJECTED`, `ESCALATED`, `RESOLVED`, `REOPENED` (P1).

**Feature names** (identical to PRD §10 and SRS §7.0): Authentication and Access Control; Complaint Submission; Photo Evidence; Location Capture; Category Routing; Department Review; Progress Tracking; Complaint Timeline; Automatic Escalation; Superintendent Oversight; Resolution Recording; In-App Notifications; Administration and Configuration; Audit Trail; AI Category and Priority Suggestions (P1); Duplicate Detection (P1); Issue Map (P1); Analytics Dashboard (P1); Citizen Feedback and Reopening (P1).

**Notification triggers:** NT-01 submitted; NT-02 accepted; NT-03 rejected; NT-04 progress; NT-05 escalated; NT-06 supervisory action; NT-07 resolved; NT-08 reopened (P1).

### Story index

| Area | IDs | Count |
|---|---|---|
| Citizen | US-CIT-01 – US-CIT-17 | 17 |
| Department Officer | US-DEP-01 – US-DEP-08 | 8 |
| Superintendent Officer | US-SUP-01 – US-SUP-05 | 5 |
| Platform Administrator | US-ADM-01 – US-ADM-06 | 6 |
| System and platform | US-SYS-01 – US-SYS-03 | 3 |
| P1 optional | US-P1-01 – US-P1-04 | 4 |
| End-to-end journey | US-E2E-01 | 1 |
| **Total** | | **44** |

---

## 2. Citizen Stories

### US-CIT-01 — Register a Citizen account

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to create a CivicTrack account with my name, email, and password, so that I can report civic problems and track them. |
| Requirements | FR-001, FR-003 |

**Preconditions**
- The visitor is not authenticated.
- The email address is not already registered.

**Acceptance criteria**
1. **Given** a valid name, unique email, and a password of 8–72 characters containing a letter and a digit, **when** the visitor submits the registration form, **then** the system creates an active account with role `CITIZEN`, returns HTTP 201, and signs the user in.
2. **Given** an email that already exists in any letter case, **when** the visitor submits registration, **then** the system returns HTTP 409 `EMAIL_ALREADY_REGISTERED` and creates no account.
3. **Given** a password shorter than 8 characters or missing a digit, **when** the visitor submits, **then** the system returns HTTP 422 with a field-level message and creates no account.
4. **Given** a completed registration, **when** the account is inspected in the database, **then** only a bcrypt hash (cost ≥ 12) is stored and no plaintext password exists.

**Expected system behavior**
Registration always produces the `CITIZEN` role; role is never accepted from the client. Duplicate emails are rejected case-insensitively. The API response contains a JWT and the public user object but no password fields.

---

### US-CIT-02 — Log in and log out

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a registered user, I want to log in and log out securely, so that my complaints and personal data remain private. |
| Requirements | FR-002, FR-003 |

**Preconditions**
- An active account exists.

**Acceptance criteria**
1. **Given** valid credentials, **when** the user submits the login form, **then** the system returns HTTP 200 with an 8-hour JWT and the user's role, and redirects to the correct dashboard.
2. **Given** an invalid password or unknown email, **when** the user submits login, **then** the system returns HTTP 401 with the generic message `Invalid email or password` and reveals which field was wrong only through a generic form error.
3. **Given** a deactivated account, **when** the user attempts login, **then** the system returns HTTP 401 and does not issue a token.
4. **Given** a logged-in user, **when** the user logs out, **then** the client discards the token, the system returns HTTP 204, and protected pages redirect to login.

**Expected system behavior**
The role returned at login determines the landing route: Citizen → My Complaints, Department Officer → Department Queue, Superintendent → Escalation Queue, Administrator → Administration. The UI never decides authorization; every request is re-checked by the API.

---

### US-CIT-03 — Submit a complaint

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to report a civic problem with a title, description, and category, so that the responsible department receives a clear, actionable complaint. |
| Requirements | FR-007, FR-008, FR-013, FR-042 |

**Preconditions**
- The user is authenticated as `CITIZEN`.
- At least one active category with a mapped department exists.

**Acceptance criteria**
1. **Given** an authenticated Citizen and an active category, **when** they submit a title of 5–150 characters and a description of 20–2,000 characters, **then** the system creates the complaint, sets `submitted_at`, returns HTTP 201 with status `PENDING_DEPARTMENT_REVIEW` and the tracking number, and creates the NT-01 notification.
2. **Given** a title shorter than 5 characters or a description shorter than 20 characters, **when** the user submits, **then** the system returns HTTP 422 and persists nothing.
3. **Given** a valid submission, **when** the complaint is inspected, **then** it belongs to the authenticated Citizen and no department other than the mapped one is associated.
4. **Given** a successful submission, **when** the timeline is read, **then** it contains `null → SUBMITTED` attributed to the Citizen and `SUBMITTED → PENDING_DEPARTMENT_REVIEW` attributed to `SYSTEM`, in that order.

**Expected system behavior**
The form exposes a single category selector and never a department selector. Submission is not verification; the UI labels the report as unverified until an officer acts. A failed validation or upload never leaves a partial complaint.

---

### US-CIT-04 — Attach photographs to a complaint

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to attach up to three photographs, so that the department can see the problem without visiting the site first. |
| Requirements | FR-010, FR-023 |

**Preconditions**
- The complaint form is open.

**Acceptance criteria**
1. **Given** the form, **when** the user selects one to three JPEG, PNG, or WebP images each at most 5 MiB, **then** the images are previewed and submitted with the complaint.
2. **Given** an image larger than 5 MiB, **when** the user selects it, **then** the client rejects it before upload with a readable message and the form remains usable.
3. **Given** a file with an image extension but a non-image signature, **when** it is uploaded, **then** the API returns HTTP 422 and no image row or file is persisted.
4. **Given** a valid complaint with images, **when** the complaint detail is read, **then** image metadata is returned and each image is retrievable through an authorized endpoint.

**Expected system behavior**
Images are optional. Stored files use randomized names and are never directly public. The maximum is three files per submission and ten images per complaint over its lifetime; progress and resolution evidence use the same limits and validation.

---

### US-CIT-05 — Add an optional location

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to add a location description and optionally share coordinates, so that the department can find the problem without me giving more personal information than necessary. |
| Requirements | FR-011, NFR-007 |

**Preconditions**
- The complaint form is open.

**Acceptance criteria**
1. **Given** the form, **when** the user enters only "Near Gate 2, Market Road", **then** the complaint is accepted with location text and no coordinates.
2. **Given** the user supplies latitude without longitude, **when** they submit, **then** the system returns HTTP 422 and explains that both coordinates are required.
3. **Given** latitude 91 or longitude 181, **when** the user submits, **then** the system returns HTTP 422.
4. **Given** a saved location, **when** a different citizen or an officer of another department requests the complaint, **then** the location is not returned.

**Expected system behavior**
Location is optional. The UI states that sharing an exact location is optional and visible only to authorized staff. Coordinates are stored as decimals and are never placed in URLs or logs.

---

### US-CIT-06 — Receive a tracking number and the correct department

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want a unique tracking number and to know which department owns my complaint, so that I can follow up with confidence. |
| Requirements | FR-009, FR-012, FR-015 |

**Preconditions**
- The complaint was submitted successfully.

**Acceptance criteria**
1. **Given** a successful submission, **when** the confirmation screen appears, **then** it shows a tracking number matching `CT-YYYY-NNNNNN`, the category, the department name, and status "Pending Department Review".
2. **Given** the category "Broken Streetlight", **when** routing completes, **then** the complaint is assigned to the Electrical Department as defined by the active mapping.
3. **Given** an inactive or unmapped category, **when** a citizen attempts submission, **then** the system returns HTTP 422 `CATEGORY_NOT_MAPPED` and creates no complaint.
4. **Given** two complaints submitted in sequence, **when** their tracking numbers are compared, **then** they are different and both satisfy the format.

**Expected system behavior**
Routing uses the mapping at submission time. Later mapping changes never move existing complaints. The citizen cannot choose or override the department.

---

### US-CIT-07 — View my complaints

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want a list of my complaints with their current status, so that I can see everything I have reported in one place. |
| Requirements | FR-014 |

**Preconditions**
- The user is authenticated and has at least one complaint.

**Acceptance criteria**
1. **Given** a Citizen with complaints, **when** they open "My Complaints", **then** only their complaints are returned, newest first, 20 per page.
2. **Given** another Citizen's complaint exists, **when** the first Citizen lists complaints, **then** the other complaint is absent.
3. **Given** a status filter of `ESCALATED`, **when** applied, **then** only escalated complaints owned by the Citizen are returned.
4. **Given** no complaints, **when** the list loads, **then** an empty state explains how to report a problem.

**Expected system behavior**
List items show tracking number, title, category, department, status, submitted date, and deadline when accepted. The list never exposes another user's data or precise location.

---

### US-CIT-08 — View status and the complete timeline

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to see the current status, department, dates, and a dated history of my complaint, so that I know whether it is being handled. |
| Requirements | FR-015, FR-016 |

**Preconditions**
- The Citizen owns the complaint.

**Acceptance criteria**
1. **Given** an owned complaint, **when** the detail page opens, **then** it shows tracking number, title, description, category, department, status, submitted time, acceptance time (if any), deadline (if accepted), resolution time (if resolved), and images.
2. **Given** status changes and progress notes, **when** the timeline is viewed, **then** events are ordered oldest-first and each shows the event type, actor display name or `SYSTEM`, and timestamp.
3. **Given** an internal officer note marked non-visible to citizens, **when** the Citizen views the timeline, **then** that note is absent.
4. **Given** a non-owner or another role outside scope, **when** the detail is requested, **then** the API returns HTTP 404 or 403 without leaking complaint fields.

**Expected system behavior**
The timeline is append-only. The UI shows the acceptance target date and a plain-language escalation explanation when applicable. `SUBMITTED` is never rendered as "verified".

---

### US-CIT-09 — Receive an acknowledgement when my complaint is accepted

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want an acknowledgement when the department accepts my complaint, so that I know it has not been ignored. |
| Requirements | FR-019, FR-042, FR-045 (NT-02) |

**Preconditions**
- The complaint is `PENDING_DEPARTMENT_REVIEW`.
- A Department Officer accepts it.

**Acceptance criteria**
1. **Given** a department acceptance, **when** the transaction commits, **then** a notification exists for the owning Citizen containing the tracking number, department name, accepting officer, acceptance time, and resolution deadline.
2. **Given** the Citizen is logged in, **when** the notification poller runs within 30 seconds, **then** the unread badge increases and the notification appears in the list.
3. **Given** the acceptance and the notification, **when** the database is inspected, **then** both were written in the same transaction and no acceptance exists without its notification.
4. **Given** the complaint detail, **when** the Citizen opens it after acceptance, **then** the status is `ACCEPTED` and the department is shown.

**Expected system behavior**
The deadline shown equals `accepted_at + configured window`; in production this is seven calendar days. Notification content is derived from stored data, not from client input.

---

### US-CIT-10 — Receive a rejection with a reason

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to know if my complaint was rejected and why, so that I can correct the report or use another channel. |
| Requirements | FR-020, FR-042, FR-045 (NT-03) |

**Preconditions**
- The complaint is `PENDING_DEPARTMENT_REVIEW`.

**Acceptance criteria**
1. **Given** a Department Officer rejects with a reason of 10–1,000 characters, **when** the transaction commits, **then** the status is `REJECTED` and the rejection reason, officer, and timestamp are stored.
2. **Given** the rejection, **when** the Citizen reads the notification, **then** it contains the tracking number and the full rejection reason.
3. **Given** a rejection with an empty or 9-character reason, **when** the officer submits, **then** the system returns HTTP 422 and no state changes.
4. **Given** a rejected complaint, **when** the Citizen views it, **then** no resolution deadline is displayed and the complaint cannot be accepted later in P0.

**Expected system behavior**
Rejection is terminal in P0. The reason is citizen-visible and also appears in the timeline. Rejection does not start or stop any escalation clock because no clock exists.

---

### US-CIT-11 — Receive progress updates

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to see progress notes and status changes, so that I know work is actually happening. |
| Requirements | FR-022, FR-023, FR-042, FR-045 (NT-04) |

**Preconditions**
- The complaint is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED`.
- An officer of the assigned department posts an update.

**Acceptance criteria**
1. **Given** an officer adds a progress note, **when** it commits, **then** a citizen-visible timeline entry and an NT-04 notification are created with the note and new status.
2. **Given** the first progress update on an `ACCEPTED` complaint, **when** the officer marks it as started, **then** the status becomes `IN_PROGRESS` and history records the transition.
3. **Given** an update on an `ESCALATED` complaint, **when** the officer adds a note, **then** the status remains `ESCALATED` and the update is visible to both the Citizen and the Superintendent.
4. **Given** an evidence image uploaded with a progress update, **when** the Citizen views the timeline, **then** the image is accessible through the authorized endpoint.

**Expected system behavior**
Progress notes are append-only and attributed. Internal notes are excluded from the citizen view. Updates never change the acceptance timestamp or deadline.

---

### US-CIT-12 — Receive an escalation update

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to be told when my complaint is escalated, so that I know a senior officer is now aware of the delay. |
| Requirements | FR-032, FR-042, FR-045 (NT-05) |

**Preconditions**
- The complaint is accepted, overdue, unresolved, and has no escalation record.

**Acceptance criteria**
1. **Given** the scheduler escalates the complaint, **when** the transaction commits, **then** the Citizen receives an NT-05 notification with the tracking number, department, deadline, and overdue duration.
2. **Given** the escalation, **when** the Citizen opens the complaint, **then** the status is `ESCALATED` and the timeline contains an escalation event attributed to `SYSTEM` with its timestamp.
3. **Given** the escalation event, **when** the Citizen reads it, **then** the text explains that a Superintendent Officer has been notified, without exposing internal officer contact details.
4. **Given** repeated scheduler runs, **when** the Citizen's notifications are listed, **then** exactly one NT-05 exists for that complaint.

**Expected system behavior**
Escalation is automatic and never requires the citizen to request it. The complaint remains with the original department; escalation adds supervision rather than replacing ownership.

---

### US-CIT-13 — Receive the resolution update

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want to see when and how my complaint was resolved, so that I can verify the fix and decide whether to give feedback. |
| Requirements | FR-024, FR-041, FR-042, FR-045 (NT-07) |

**Preconditions**
- The complaint is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED`.

**Acceptance criteria**
1. **Given** an authorized officer records a resolution with a note of 10–2,000 characters, **when** it commits, **then** the status is `RESOLVED`, the resolver and resolution time are stored, and the Citizen receives NT-07.
2. **Given** a resolution, **when** the Citizen opens the complaint, **then** the resolution note, resolver display name, resolution time, and any after-image are visible.
3. **Given** a deadline that passed without a resolution record, **when** the Citizen views the complaint, **then** it is shown as `ESCALATED` or another non-resolved status, never `RESOLVED`.
4. **Given** an attempt to resolve from `PENDING_DEPARTMENT_REVIEW` or `REJECTED`, **when** submitted, **then** the API returns HTTP 409 and no resolution fields are written.

**Expected system behavior**
Resolution is the only path to `RESOLVED`. An automated job can never write a resolution. After resolution the complaint leaves the escalation queue and stops being an escalation candidate.

---

### US-CIT-14 — Manage my notifications

| Field | Value |
|---|---|
| Role | Citizen (also used by every role) |
| Priority | P0 |
| Story | As a user, I want an unread badge and a notification list I can mark as read, so that I do not miss status changes. |
| Requirements | FR-043, FR-044, FR-045 |

**Preconditions**
- The user is authenticated.

**Acceptance criteria**
1. **Given** unread notifications, **when** the user opens the notification panel, **then** the list shows them newest first with trigger type, title, body, complaint tracking number, and time.
2. **Given** three unread notifications, **when** the header loads, **then** the unread count is 3.
3. **Given** an unread notification, **when** the user marks it read, **then** `read_at` is stored and the count decreases by one; repeating the call is idempotent.
4. **Given** another user's notification ID, **when** the user attempts to mark it read, **then** the API returns HTTP 404 and changes nothing.

**Expected system behavior**
Notifications are owner-only. Polling every 30 seconds keeps the badge current without websockets. A missing notification for a committed trigger is a defect, because notifications are written in the same transaction.

---

### US-CIT-15 — See only my own data

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P0 |
| Story | As a resident, I want my personal details and complaint data to be visible only to me and authorized staff, so that my privacy is protected. |
| Requirements | FR-004, NFR-005, NFR-007 |

**Preconditions**
- The user is authenticated as `CITIZEN`.

**Acceptance criteria**
1. **Given** a Citizen, **when** they request `/api/v1/department/complaints`, **then** the API returns HTTP 403.
2. **Given** a Citizen, **when** they call `POST /api/v1/complaints/{id}/accept` for any complaint, **then** the API returns HTTP 403 and no state changes.
3. **Given** another Citizen's complaint ID, **when** the first Citizen requests its detail or images, **then** the API returns HTTP 404 or 403 without returning fields.
4. **Given** the Citizen UI, **when** the navigation is rendered, **then** no department, Superintendent, or administration links are present.

**Expected system behavior**
Client-side hiding is cosmetic. Every API operation re-checks the token, role, and object scope. Denied attempts are audit-logged.

---

### US-CIT-16 — Give feedback or request reopening after resolution (P1)

| Field | Value |
|---|---|
| Role | Citizen |
| Priority | P1 |
| Story | As a resident whose issue is not actually fixed, I want to rate the resolution and request reopening, so that the complaint is not closed incorrectly. |
| Requirements | FR-056, FR-057 |

**Preconditions**
- The complaint is `RESOLVED` and belongs to the Citizen.
- No feedback or reopening request already exists for the complaint.

**Acceptance criteria**
1. **Given** a resolved complaint, **when** the Citizen submits a rating from 1 to 5 and an optional comment, **then** the feedback is stored once and displayed to authorized staff.
2. **Given** a resolved complaint, **when** the Citizen submits a reopening request with a reason, **then** the request is stored and the department officers receive a notification.
3. **Given** a Department Officer accepts the reopening request, **when** the action commits, **then** the status becomes `REOPENED` and NT-08 is created.
4. **Given** a reopening is accepted and work restarts, **when** the officer re-accepts, **then** a new acceptance timestamp and a new deadline are recorded.

**Expected system behavior**
Feedback and reopening never mutate the original resolution history. This story is optional and must not be started before all P0 acceptance criteria pass.

---

### US-CIT-17 — View my profile

| Field | Value |
|---|---|
| Role | Citizen (shared by all roles) |
| Priority | P0 |
| Story | As a signed-in user, I want to see my name, email, role, and department, so that I can confirm I am using the correct account. |
| Requirements | FR-005 |

**Preconditions**
- The user is authenticated.

**Acceptance criteria**
1. **Given** an authenticated session, **when** the profile page loads, **then** it shows full name, email, phone (if set), role display name, and department name for department officers.
2. **Given** the profile response, **when** it is inspected, **then** it contains no password hash and no other user's data.
3. **Given** a deactivated account with a still-valid token, **when** it calls the profile endpoint, **then** the API returns HTTP 401.

**Expected system behavior**
The profile endpoint is the canonical way for the frontend to restore a session and route the user after reload.

---

## 3. Department Officer Stories

### US-DEP-01 — Work from a department-scoped queue

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want a queue of only my department's complaints with status counts, so that I can triage pending work quickly. |
| Requirements | FR-017, FR-025 |

**Preconditions**
- The officer is authenticated and assigned to an active department.

**Acceptance criteria**
1. **Given** an officer in the Electrical Department, **when** the queue loads, **then** it contains only complaints routed to Electrical.
2. **Given** pending, accepted, and escalated complaints in the department, **when** the summary is read, **then** counts per status match the queue.
3. **Given** status and category filters, **when** applied, **then** the list narrows accordingly and pagination remains correct.
4. **Given** a complaint from another department, **when** the officer manipulates the query string, **then** it does not appear.

**Expected system behavior**
Department scoping is derived from the authenticated officer's user record, never from a client-supplied department id. The queue defaults to `PENDING_DEPARTMENT_REVIEW` first for triage.

---

### US-DEP-02 — Open a complaint in my department

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want to see the full complaint, photos, location, and history, so that I can make an informed accept or reject decision. |
| Requirements | FR-018, FR-015 |

**Preconditions**
- The complaint belongs to the officer's department.

**Acceptance criteria**
1. **Given** an in-scope complaint, **when** the officer opens it, **then** the description, category, location, images, status, and timeline are shown.
2. **Given** an out-of-scope complaint id, **when** the officer requests it, **then** the API returns HTTP 403 and no fields are leaked.
3. **Given** a complaint with images, **when** the officer opens an image, **then** it loads through the authorized image endpoint.
4. **Given** a complaint submitted by a citizen, **when** the officer views it, **then** the page labels it as an unverified citizen report, not a confirmed defect.

**Expected system behavior**
The officer can see the citizen's display name for contact context but not unrelated PII. Location and coordinates are visible because the officer is authorized for the responsible department.

---

### US-DEP-03 — Accept a complaint and start the seven-day clock

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want to accept a valid complaint, so that the citizen is acknowledged and the resolution clock starts. |
| Requirements | FR-019, FR-027, FR-050 |

**Preconditions**
- The complaint is `PENDING_DEPARTMENT_REVIEW` and belongs to the officer's department.

**Acceptance criteria**
1. **Given** a pending in-scope complaint, **when** the officer accepts, **then** the status becomes `ACCEPTED`, `accepted_at` and `accepted_by_user_id` are stored, `sla_seconds` is set, and `resolution_due_at = accepted_at + sla_seconds`.
2. **Given** the production configuration, **when** acceptance completes, **then** the deadline is exactly 10,080 minutes after the acceptance timestamp, not after submission.
3. **Given** the acceptance, **when** the citizen notification is checked, **then** NT-02 contains the department, acceptance time, and deadline.
4. **Given** a second acceptance attempt, **when** it is submitted, **then** the API returns HTTP 409 `INVALID_TRANSITION` and the original deadline is unchanged.
5. **Given** the acceptance, **when** history is read, **then** one row records `PENDING_DEPARTMENT_REVIEW → ACCEPTED`, the officer, the timestamp, and the resulting deadline.

**Expected system behavior**
The acceptance update is conditional on the current status, so two officers cannot accept simultaneously. The deadline is stored, not recomputed from current configuration on every read.

---

### US-DEP-04 — Reject a complaint with a reason

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want to reject an invalid or out-of-scope complaint with a mandatory reason, so that the citizen understands the decision. |
| Requirements | FR-020, FR-045 |

**Preconditions**
- The complaint is `PENDING_DEPARTMENT_REVIEW` and in scope.

**Acceptance criteria**
1. **Given** a pending complaint, **when** the officer rejects with a 10–1,000 character reason, **then** the status becomes `REJECTED` and the reason, officer, and timestamp are stored.
2. **Given** an empty or 9-character reason, **when** the officer submits, **then** the API returns HTTP 422 and the complaint remains pending.
3. **Given** a successful rejection, **when** the citizen reads the notification, **then** it contains the tracking number and the exact reason.
4. **Given** a rejected complaint, **when** the officer attempts to accept it, **then** the API returns HTTP 409.

**Expected system behavior**
Rejection is terminal in P0. No escalation clock exists for rejected complaints, and the reason is never hidden from the complainant.

---

### US-DEP-05 — Assign a complaint to staff

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want to assign a complaint to a staff member in my department, so that responsibility is explicit. |
| Requirements | FR-021 |

**Preconditions**
- The complaint is accepted or in progress and in scope.
- The assignee is an active user in the same department.

**Acceptance criteria**
1. **Given** an accepted complaint, **when** the officer assigns it to an active department colleague, **then** `assigned_to_user_id` and `assigned_at` are stored.
2. **Given** an assignee from another department or an inactive account, **when** the officer submits, **then** the API returns HTTP 422.
3. **Given** a successful assignment, **when** the queue is filtered by assignee, **then** the complaint appears under that assignee.
4. **Given** an assignment only, **when** the citizen checks notifications, **then** no progress notification is created because no status changed.

**Expected system behavior**
Assignment is internal coordination. It does not alter the complaint status, the deadline, or the citizen-visible lifecycle, and it does not bypass department scoping.

---

### US-DEP-06 — Post progress and upload evidence

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want to record progress notes and evidence, so that the citizen and Superintendent can see what has been done. |
| Requirements | FR-022, FR-023 |

**Preconditions**
- The complaint is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` and in scope.

**Acceptance criteria**
1. **Given** an accepted complaint, **when** the officer posts a 5–2,000 character note and marks work started, **then** the status becomes `IN_PROGRESS`, the note is stored, history records the transition, and NT-04 is created.
2. **Given** an in-progress complaint, **when** the officer uploads one to three valid images as progress evidence, **then** the images are stored and linked to the complaint.
3. **Given** an invalid file or a fourth image, **when** the officer uploads, **then** the API returns HTTP 422 or 413 and stores nothing.
4. **Given** a progress update, **when** the citizen views the timeline, **then** the note, actor, timestamp, and evidence are visible.

**Expected system behavior**
Progress is append-only. An officer cannot rewrite earlier notes. Uploads are limited to ten images per complaint across all kinds.

---

### US-DEP-07 — Resolve a complaint

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want to record a resolution with a note and optional after-photo, so that the citizen knows the work is complete and can verify it. |
| Requirements | FR-024, FR-042 |

**Preconditions**
- The complaint is `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED` and in scope.

**Acceptance criteria**
1. **Given** an in-scope accepted complaint, **when** the officer submits a 10–2,000 character resolution note, **then** the status becomes `RESOLVED`, the resolver and resolution time are stored, and NT-07 is created.
2. **Given** an optional after-image, **when** the resolution is submitted with it, **then** the image is linked as `RESOLUTION` evidence and shown to the citizen.
3. **Given** a 9-character note, **when** submitted, **then** the API returns HTTP 422 and the status is unchanged.
4. **Given** a resolved complaint, **when** the department queue is viewed, **then** it no longer counts as pending or escalated.

**Expected system behavior**
Resolution is the only writer of `RESOLVED`. The action is atomic with its history and notification. After resolution, the complaint cannot be escalated, and the original acceptance and department remain visible.

---

### US-DEP-08 — Continue work after escalation

| Field | Value |
|---|---|
| Role | Department Officer |
| Priority | P0 |
| Story | As a department officer, I want to keep posting progress on an escalated complaint, so that supervision does not stop the actual work. |
| Requirements | FR-026, FR-018 |

**Preconditions**
- The complaint is `ESCALATED` and belongs to the officer's department.

**Acceptance criteria**
1. **Given** an escalated complaint, **when** the officer posts a progress note, **then** the note is stored and the status remains `ESCALATED`.
2. **Given** the progress update, **when** the Superintendent opens the complaint, **then** the new note and evidence are visible in the timeline.
3. **Given** the update, **when** the citizen checks notifications, **then** NT-04 is created.
4. **Given** an escalated complaint from another department, **when** the officer attempts the update, **then** the API returns HTTP 403.

**Expected system behavior**
Escalation adds oversight; it does not transfer ownership or lock the department out. Only a resolution ends the escalated state.

---

## 4. Superintendent Officer Stories

### US-SUP-01 — Review the escalation queue

| Field | Value |
|---|---|
| Role | Superintendent Officer |
| Priority | P0 |
| Story | As a Superintendent Officer, I want a queue of automatically escalated complaints sorted by overdue duration, so that I can focus on the most delayed cases first. |
| Requirements | FR-035, FR-032 |

**Preconditions**
- The officer is authenticated as `SUPERINTENDENT_OFFICER`.
- At least one complaint has been escalated.

**Acceptance criteria**
1. **Given** escalated complaints, **when** the dashboard loads, **then** only `ESCALATED` complaints appear, sorted by overdue duration descending.
2. **Given** each row, **when** displayed, **then** it shows tracking number, department, acceptance time, deadline, overdue duration, and status.
3. **Given** a complaint escalated moments ago, **when** the queue is refreshed, **then** it appears without manual data entry.
4. **Given** a resolved complaint, **when** the queue loads, **then** it is absent.

**Expected system behavior**
The queue is populated only by the scheduler; there is no "escalate" button for the Superintendent. Sorting is computed from `now - deadline` (or from stored `overdue_seconds` at escalation where displayed as the initial delay).

---

### US-SUP-02 — Review the full history and delay

| Field | Value |
|---|---|
| Role | Superintendent Officer |
| Priority | P0 |
| Story | As a Superintendent Officer, I want to see the complaint, responsible department, acceptance date, delay, and complete timeline, so that I can judge what went wrong. |
| Requirements | FR-036, FR-037 |

**Preconditions**
- The complaint is `ESCALATED`.

**Acceptance criteria**
1. **Given** an escalated complaint, **when** the detail opens, **then** it shows the responsible department, `accepted_at`, `resolution_due_at`, current overdue duration, and current status.
2. **Given** the complaint's history, **when** the timeline renders, **then** submission, routing, acceptance, every progress note, evidence, escalation, and supervisory actions appear in chronological order.
3. **Given** a departmental progress note, **when** the Superintendent reads it, **then** the author and timestamp are visible.
4. **Given** an escalated complaint with no departmental progress beyond acceptance, **when** reviewed, **then** the page clearly states that no progress has been recorded.

**Expected system behavior**
The Superintendent sees the original department and all actions without needing the department to forward anything. The timeline is read-only.

---

### US-SUP-03 — Record an instruction or supervisory action

| Field | Value |
|---|---|
| Role | Superintendent Officer |
| Priority | P0 |
| Story | As a Superintendent Officer, I want to record an instruction or action against an escalated complaint, so that there is an attributable supervisory decision. |
| Requirements | FR-038, FR-050 |

**Preconditions**
- The complaint is `ESCALATED`.

**Acceptance criteria**
1. **Given** an escalated complaint, **when** the Superintendent records an `INSTRUCTION` with a 5–2,000 character note, **then** the action is stored with officer identity and timestamp and appears in the timeline.
2. **Given** the action, **when** department officers and the citizen check notifications, **then** NT-06 contains the action type, note summary, and Superintendent identity.
3. **Given** an empty note, **when** submitted, **then** the API returns HTTP 422.
4. **Given** a non-escalated complaint, **when** the Superintendent attempts a supervisory action, **then** the API returns HTTP 409.

**Expected system behavior**
Supervisory actions are append-only and cannot be edited or deleted. The complaint status remains `ESCALATED` until a resolution is recorded.

---

### US-SUP-04 — Direct follow-up to the responsible department

| Field | Value |
|---|---|
| Role | Superintendent Officer |
| Priority | P0 |
| Story | As a Superintendent Officer, I want to direct a follow-up or reassignment instruction to the responsible department, so that the department knows what is expected and by when. |
| Requirements | FR-039, FR-042 |

**Preconditions**
- The complaint is `ESCALATED`.
- The target department is active.

**Acceptance criteria**
1. **Given** an escalated complaint, **when** the Superintendent records a `FOLLOW_UP` with `directed_department_id` set to the responsible department, **then** the action is stored and the department officers receive NT-06.
2. **Given** the directive, **when** the timeline is viewed, **then** the target department and instruction are visible with actor and timestamp.
3. **Given** a directive, **when** the complaint is inspected, **then** the original `department_id` is unchanged and the complaint remains assigned to the responsible department.
4. **Given** an inactive target department, **when** submitted, **then** the API returns HTTP 422.

**Expected system behavior**
In P0, "reassign" is recorded as a directive, not an automatic ownership transfer. This prevents history loss and keeps accountability with the original department.

---

### US-SUP-05 — Monitor and resolve escalated complaints

| Field | Value |
|---|---|
| Role | Superintendent Officer |
| Priority | P0 |
| Story | As a Superintendent Officer, I want to monitor the case until it is resolved and record the resolution when appropriate, so that escalation ends only with a real outcome. |
| Requirements | FR-040, FR-041, FR-024 |

**Preconditions**
- The complaint is `ESCALATED`.

**Acceptance criteria**
1. **Given** an escalated complaint with new departmental progress, **when** the Superintendent refreshes the detail, **then** the new events appear and the complaint remains in the queue.
2. **Given** the Superintendent resolves the complaint with a 10–2,000 character note, **when** it commits, **then** the status becomes `RESOLVED`, the Superintendent is recorded as resolver, and NT-07 is created.
3. **Given** the resolution, **when** the escalation queue reloads, **then** the complaint is absent.
4. **Given** a complaint that is still escalated, **when** the Superintendent attempts to close without a resolution note, **then** the API returns HTTP 422.

**Expected system behavior**
The Superintendent's resolution uses the same rules as a departmental resolution and is fully attributed. Silence never closes a complaint.

---

## 5. Platform Administrator Stories

### US-ADM-01 — Manage users and roles

| Field | Value |
|---|---|
| Role | Platform Administrator |
| Priority | P0 |
| Story | As a platform administrator, I want to create and manage users and assign roles, so that the right people have the right access. |
| Requirements | FR-006 |

**Preconditions**
- The administrator is authenticated as `PLATFORM_ADMIN`.

**Acceptance criteria**
1. **Given** the user administration page, **when** the administrator changes a Citizen to Department Officer and assigns an active department, **then** the change is stored and takes effect on that user's next request.
2. **Given** a Department Officer role without a department, **when** saved, **then** the API returns HTTP 422.
3. **Given** the last active Platform Administrator, **when** the administrator attempts to demote or deactivate that account, **then** the API returns HTTP 409 and the account remains active.
4. **Given** a role change, **when** the audit log is read, **then** the actor, target, old role, new role, and timestamp are recorded.
5. **Given** the administrator creates a Department Officer with a unique email and an active department, **when** they save, **then** the account is created with role `DEPARTMENT_OFFICER`, can log in, and the creation is audited; omitting the department returns HTTP 422.

**Expected system behavior**
Only an Administrator can create and manage users and roles. A user has one role. Administrators do not gain operational complaint permissions by virtue of being administrators.

---

### US-ADM-02 — Manage departments

| Field | Value |
|---|---|
| Role | Platform Administrator |
| Priority | P0 |
| Story | As a platform administrator, I want to create and deactivate departments, so that the organizational structure matches the municipality. |
| Requirements | FR-046 |

**Preconditions**
- The administrator is authenticated.

**Acceptance criteria**
1. **Given** the department form, **when** the administrator creates a department with a unique name and code, **then** it is stored and available for category mapping.
2. **Given** a department with active categories, **when** the administrator attempts deactivation, **then** the API returns HTTP 409 and explains the dependency.
3. **Given** a department with active officers, **when** the administrator attempts deactivation, **then** the API returns HTTP 409.
4. **Given** a successful deactivation, **when** new complaints are submitted, **then** no category can route to the inactive department.

**Expected system behavior**
Departments are never hard-deleted because historical complaints reference them. Deactivation is a visibility and configuration change only.

---

### US-ADM-03 — Manage categories and routing mappings

| Field | Value |
|---|---|
| Role | Platform Administrator |
| Priority | P0 |
| Story | As a platform administrator, I want to manage complaint categories and map each to a department, so that new complaints route correctly without code changes. |
| Requirements | FR-047, FR-012 |

**Preconditions**
- At least one active department exists.

**Acceptance criteria**
1. **Given** the category form, **when** the administrator creates "Broken Streetlight" and maps it to the Electrical Department, **then** the category appears in the citizen catalogue and routes new complaints to Electrical.
2. **Given** a mapping change from Electrical to Public Works, **when** an existing Electrical complaint is read, **then** its department is unchanged; only new complaints use Public Works.
3. **Given** a category mapped to an inactive department, **when** the administrator saves, **then** the API returns HTTP 422.
4. **Given** an inactive category, **when** a citizen attempts to submit with it, **then** the API returns HTTP 422 `CATEGORY_NOT_MAPPED`.

**Expected system behavior**
Every active category has exactly one active mapped department. Mapping changes are audited with old and new values and never rewrite historical complaints.

---

### US-ADM-04 — Monitor platform activity

| Field | Value |
|---|---|
| Role | Platform Administrator |
| Priority | P0 |
| Story | As a platform administrator, I want to see counts by status and department plus recent events, so that I can detect operational problems. |
| Requirements | FR-048 |

**Preconditions**
- The administrator is authenticated.

**Acceptance criteria**
1. **Given** seeded complaints, **when** the activity page loads, **then** counts by status and department match the database.
2. **Given** at least one escalation, **when** the page loads, **then** the escalation count is shown separately.
3. **Given** recent activity, **when** the page loads, **then** the 20 most recent timeline events are listed with complaint, event, actor, and time.
4. **Given** a Citizen token, **when** the activity endpoint is called, **then** the API returns HTTP 403.

**Expected system behavior**
Activity is read-only. It does not expose PII beyond tracking numbers and actor display names needed for operations.

---

### US-ADM-05 — Review audit logs

| Field | Value |
|---|---|
| Role | Platform Administrator |
| Priority | P0 |
| Story | As a platform administrator, I want to review audit logs with filters, so that I can investigate access and configuration changes. |
| Requirements | FR-049, FR-050, NFR-008 |

**Preconditions**
- The administrator is authenticated.
- Audit events exist.

**Acceptance criteria**
1. **Given** authentication failures, denied access, role changes, mapping changes, and status transitions, **when** the audit page loads, **then** matching entries show actor, action, entity, timestamp, and metadata.
2. **Given** a filter by actor and date range, **when** applied, **then** only matching entries are returned, newest first.
3. **Given** an audit entry, **when** any client attempts update or delete through the API, **then** no such route exists and the record remains unchanged.
4. **Given** a Citizen token, **when** the audit endpoint is called, **then** the API returns HTTP 403.

**Expected system behavior**
Audit logs are append-only. Sensitive values such as passwords and tokens are never written to them.

---

### US-ADM-06 — Configure and test the escalation window

| Field | Value |
|---|---|
| Role | Platform Administrator (operator) |
| Priority | P0 |
| Story | As a demo operator, I want an explicit, guarded demo escalation window and a manual check trigger, so that I can prove automatic escalation in minutes without changing the production rule. |
| Requirements | FR-033, FR-034 |

**Preconditions**
- The environment is configured with `ALLOW_DEMO_ESCALATION=true` for the demo.
- The operator holds the internal trigger token.

**Acceptance criteria**
1. **Given** the default configuration, **when** the worker starts, **then** it logs an effective window of 10,080 minutes and no demo banner appears.
2. **Given** a 2-minute window and the demo guard enabled, **when** the worker starts, **then** it logs a clearly labeled demo banner and uses 120 seconds.
3. **Given** a shortened window without the guard, **when** the worker starts, **then** it refuses to continue with the shortened value and falls back to 10,080 minutes with an error log.
4. **Given** an overdue complaint, **when** the operator calls the internal trigger with a valid token, **then** the response reports `{evaluated, escalated, skipped}` and a second call escalates zero.
5. **Given** an invalid or missing internal token, **when** the trigger is called, **then** the API returns HTTP 401 or 403.

**Expected system behavior**
The production default is never stored as a hard-coded demo value. The manual trigger calls the same function as the scheduler and provides no bypass of the uniqueness and transition guarantees.

---

## 6. System and Platform Stories

### US-SYS-01 — Enforce role-based access on every operation

| Field | Value |
|---|---|
| Role | System |
| Priority | P0 |
| Story | As the platform, I want every API operation to check role and object scope, so that no user can perform another role's actions by calling the API directly. |
| Requirements | FR-004, NFR-005, RBAC-01–RBAC-08 |

**Preconditions**
- The API is running with authentication configured.

**Acceptance criteria**
1. **Given** the 12-case role matrix in SRS §12, **when** each unauthorized case is executed with a valid token, **then** every response is HTTP 403 and no state changes.
2. **Given** a request with no token or an expired token, **when** it targets a protected route, **then** the API returns HTTP 401.
3. **Given** a Department Officer, **when** they request a complaint from another department, **then** the API returns 403 even if they know the complaint ID.
4. **Given** a denied request, **when** the audit log is read, **then** an entry records actor, method, path, and timestamp.

**Expected system behavior**
Authorization is declarative per route and re-checked at the service layer for object scope. Client route guards exist for usability only and are never the security boundary.

---

### US-SYS-02 — Escalate overdue complaints automatically

| Field | Value |
|---|---|
| Role | System (scheduler) |
| Priority | P0 |
| Story | As the platform, I want to escalate every accepted complaint whose deadline passed without resolution, so that supervisory attention never depends on a person forwarding it. |
| Requirements | FR-028, FR-030, FR-031, FR-032, FR-050 |

**Preconditions**
- The worker process is running.
- A complaint has `accepted_at`, status `ACCEPTED` or `IN_PROGRESS`, `resolution_due_at <= now`, and no escalation record.

**Acceptance criteria**
1. **Given** an overdue accepted complaint and no escalation record, **when** the scheduler runs, **then** the status becomes `ESCALATED`, `escalated_at` is recorded, and a history row with actor `SYSTEM` and reason `SLA_BREACH` is appended.
2. **Given** the same complaint, **when** the escalation commits, **then** one escalation row exists with `deadline_at`, `escalated_at`, `overdue_seconds`, and `trigger_source`.
3. **Given** the escalation, **when** notifications are read, **then** NT-05 exists for every active Superintendent, every active officer of the department, and the citizen.
4. **Given** a complaint resolved before the run, **when** the scheduler evaluates it, **then** it is skipped and no escalation row is created.
5. **Given** a complaint accepted 6 days and 23 hours ago with the production window, **when** the scheduler runs, **then** no escalation occurs until the deadline.

**Expected system behavior**
The worker uses timestamps, not in-memory timers, so a restart cannot lose a pending escalation. The department remains unchanged and the complaint stays visible to the department for further progress.

---

### US-SYS-03 — Guarantee exactly-once escalation and reliable notifications

| Field | Value |
|---|---|
| Role | System |
| Priority | P0 |
| Story | As the platform, I want escalation and its notifications to be idempotent and atomic, so that repeated or concurrent runs cannot duplicate records or lose messages. |
| Requirements | FR-029, FR-042–FR-045, NFR-003, NFR-012 |

**Preconditions**
- The escalation function is invoked by the scheduler, a retry, or the manual trigger.

**Acceptance criteria**
1. **Given** one complaint, **when** the escalation check runs 20 consecutive times, **then** exactly one escalation row, one `ESCALATED` transition, and one NT-05 per recipient exist.
2. **Given** two worker instances or a manual trigger overlapping a scheduled run, **when** both attempt escalation, **then** the database lock and conditional update allow exactly one to succeed and the other to skip.
3. **Given** a failure while writing notifications, **when** the escalation transaction rolls back, **then** the status is not `ESCALATED` and no partial escalation row exists; the next run retries.
4. **Given** a duplicate-key error on `escalations.complaint_id`, **when** it is caught, **then** the run logs a skip and continues with other candidates rather than failing the batch.
5. **Given** the manual trigger, **when** it is called after a successful scheduled run, **then** it returns `escalated: 0` and creates nothing.

**Expected system behavior**
Idempotency is enforced at three layers: unique database constraint, conditional status update, and an advisory lock. Application-level "check then insert" alone is not sufficient.

---

## 7. P1 Optional Stories

### US-P1-01 — Get AI category and priority suggestions

| Field | Value |
|---|---|
| Role | Citizen (and Department Officer for priority confirmation) |
| Priority | P1 |
| Story | As a citizen, I want the system to suggest a category and priority from my description, so that I can submit faster and route correctly. |
| Requirements | FR-051, FR-054 |

**Preconditions**
- The P0 lifecycle is complete and stable.
- A Gemini API key is configured server-side.

**Acceptance criteria**
1. **Given** a description longer than 20 characters, **when** the user requests a suggestion, **then** the UI shows a suggested category and priority with a confidence label and requires confirmation.
2. **Given** no confirmation, **when** the user submits, **then** the manually selected category is used.
3. **Given** a Gemini timeout or error, **when** the user submits, **then** submission proceeds with manual selection within 5 seconds and no error blocks the form.
4. **Given** a suggestion, **when** an officer reviews the complaint, **then** the officer's category and priority override is recorded.

**Expected system behavior**
AI output is advisory. It never changes routing, status, deadlines, or resolution. The API key stays server-side, and the feature can be disabled by configuration without affecting P0.

---

### US-P1-02 — See possible duplicate complaints

| Field | Value |
|---|---|
| Role | Citizen (visible to Department Officer) |
| Priority | P1 |
| Story | As a citizen, I want to see nearby complaints similar to mine before submitting, so that I can avoid duplicating an existing report. |
| Requirements | FR-052 |

**Preconditions**
- The user has entered a category and coordinates.

**Acceptance criteria**
1. **Given** at least one same-category complaint within 500 metres and 7 days, **when** the user pauses on the form, **then** up to three candidates with tracking numbers and statuses are shown.
2. **Given** the candidates, **when** the user chooses to continue, **then** the complaint is submitted normally and no automatic merge occurs.
3. **Given** no coordinates, **when** duplicate detection runs, **then** it returns no candidates without blocking submission.
4. **Given** a candidate, **when** a Department Officer views it, **then** the officer may record a link note but both complaints retain their own history.

**Expected system behavior**
Duplicate detection is a suggestion only. It never hides, merges, rejects, or re-routes a complaint automatically.

---

### US-P1-03 — View complaints on a map

| Field | Value |
|---|---|
| Role | All authenticated roles (scope-filtered) |
| Priority | P1 |
| Story | As an officer, I want to see geolocated complaints on a map, so that I can understand local clusters and plan work. |
| Requirements | FR-053 |

**Preconditions**
- Complaints with coordinates exist.

**Acceptance criteria**
1. **Given** geolocated complaints in scope, **when** the map loads, **then** Leaflet/OpenStreetMap shows one marker per complaint with a popup linking to detail.
2. **Given** a Citizen, **when** the map loads, **then** only their own complaints appear.
3. **Given** a Department Officer, **when** the map loads, **then** only their department's complaints appear.
4. **Given** the map, **when** tiles fail to load, **then** the rest of the application remains usable and no P0 workflow is blocked.

**Expected system behavior**
The map is optional and lazy-loaded. It never becomes a dependency for submission, review, escalation, or resolution.

---

### US-P1-04 — View the analytics dashboard

| Field | Value |
|---|---|
| Role | Platform Administrator (read-only for Superintendent) |
| Priority | P1 |
| Story | As an administrator, I want charts of complaints by status, department, category, and age, so that I can spot backlog and routing problems. |
| Requirements | FR-055 |

**Preconditions**
- The P0 activity endpoint is implemented.

**Acceptance criteria**
1. **Given** seeded complaints, **when** the analytics page loads, **then** Recharts displays counts by status, department, category, and age bucket.
2. **Given** active filters, **when** a filter changes, **then** all charts reflect the filtered data.
3. **Given** an empty dataset, **when** the page loads, **then** each chart shows a zero-state instead of an error.
4. **Given** a Citizen token, **when** the analytics endpoint is called, **then** the API returns HTTP 403.

**Expected system behavior**
Analytics is read-only and derived from existing tables. No new operational writes, no data warehouse, and no export in P1.

---

## 8. End-to-End Journey

### US-E2E-01 — Complete complaint lifecycle from report to resolution

| Field | Value |
|---|---|
| Role | Citizen, Department Officer, Superintendent Officer, System, Administrator (setup) |
| Priority | P0 (demo gate) |
| Story | As a hackathon demonstrator, I want one uninterrupted journey from submission to resolution, including automatic escalation and supervisory intervention, so that the complete value proposition is proven. |
| Requirements | FR-001–FR-050 |

**Preconditions**
- The stack is running via Docker Compose.
- Seed data includes departments, categories, a Citizen, a Department Officer for Road Maintenance, a Superintendent, and an Administrator.
- The demo escalation window is 2 minutes with `ALLOW_DEMO_ESCALATION=true`, or a pre-seeded complaint has an acceptance time older than the window.

**Given/When/Then scenario**

1. **Given** the Citizen is on the login page, **when** they log in, **then** they land on "My Complaints" with no department or administration navigation.
2. **Given** the Citizen opens "Report a problem", **when** they select "Pothole / Damaged Road", enter "Large pothole near the school gate" with a 20+ character description, upload one photo, and add "Near Gate 2, Market Road", **then** they receive a tracking number such as `CT-2026-000042`, the Road Maintenance Department, and status "Pending Department Review".
3. **Given** the complaint exists, **when** the Road Maintenance officer logs in, **then** the complaint appears only in that department's queue, and it is absent from every other department's queue and every other citizen's list.
4. **Given** the officer opens the complaint, **when** they click Accept, **then** the status becomes `ACCEPTED`, the acceptance timestamp is recorded, the deadline is acceptance + 2 minutes in the demo (or 7 days in production), and the Citizen receives an acknowledgement with the department and target date.
5. **Given** the officer adds a progress note and marks the work started, **when** the citizen refreshes, **then** the status is `IN_PROGRESS` and the note, actor, and timestamp appear in the timeline.
6. **Given** the deadline passes without a resolution, **when** the scheduler or the guarded manual trigger runs, **then** the complaint becomes `ESCALATED`, exactly one escalation row exists, and the Superintendent, department, and Citizen receive NT-05.
7. **Given** the Superintendent logs in, **when** they open the escalation queue, **then** the complaint is listed with its department, acceptance time, deadline, overdue duration, and complete history.
8. **Given** the Superintendent records a follow-up instruction, **when** the department and Citizen refresh, **then** the instruction is visible in the timeline with the Superintendent's identity and timestamp, and NT-06 exists.
9. **Given** the department completes the work, **when** the officer records a resolution note and uploads an after-photo, **then** the status becomes `RESOLVED`, the Citizen receives NT-07, and the complaint leaves the escalation queue.
10. **Given** the resolved complaint, **when** the Citizen opens it, **then** the full timeline from submission to resolution is present, and no event was silently skipped.
11. **Given** a logged-in Citizen, **when** they call a department endpoint or navigate to `/department`, **then** the UI blocks the route and the API returns HTTP 403.
12. **Given** the Administrator logs in, **when** they open activity and audit views, **then** the counts and recent events include the demonstrated complaint, and the status transitions are attributable.

**Expected system behavior**
The journey completes without manual database edits after seeding. Escalation is triggered by time and the scheduler, not by a hidden button. The demo window is visibly labeled. The complaint is never shown as resolved before step 9.

**Demo rehearsal notes**
- Run the journey once with a pre-seeded overdue complaint for a guaranteed escalation, then once with the live 2-minute window if time permits.
- Keep the Administrator logged in on a second browser profile to show counts without disturbing role sessions.
- If the scheduler is unavailable, use the token-protected internal trigger and state clearly that it calls the same function as the background job.

---

## 9. Traceability Summary

| Story | Primary requirements |
|---|---|
| US-CIT-01 | FR-001, FR-003 |
| US-CIT-02 | FR-002, FR-003 |
| US-CIT-03 | FR-007, FR-008, FR-013, FR-042 |
| US-CIT-04 | FR-010, FR-023 |
| US-CIT-05 | FR-011, NFR-007 |
| US-CIT-06 | FR-009, FR-012, FR-015 |
| US-CIT-07 | FR-014 |
| US-CIT-08 | FR-015, FR-016 |
| US-CIT-09 | FR-019, FR-042, FR-045 |
| US-CIT-10 | FR-020, FR-042, FR-045 |
| US-CIT-11 | FR-022, FR-023, FR-042, FR-045 |
| US-CIT-12 | FR-032, FR-042, FR-045 |
| US-CIT-13 | FR-024, FR-041, FR-042, FR-045 |
| US-CIT-14 | FR-043, FR-044, FR-045 |
| US-CIT-15 | FR-004, NFR-005, NFR-007 |
| US-CIT-16 | FR-056, FR-057 |
| US-CIT-17 | FR-005 |
| US-DEP-01 | FR-017, FR-025 |
| US-DEP-02 | FR-018, FR-015 |
| US-DEP-03 | FR-019, FR-027, FR-050 |
| US-DEP-04 | FR-020, FR-045 |
| US-DEP-05 | FR-021 |
| US-DEP-06 | FR-022, FR-023 |
| US-DEP-07 | FR-024, FR-042 |
| US-DEP-08 | FR-026, FR-018 |
| US-SUP-01 | FR-035, FR-032 |
| US-SUP-02 | FR-036, FR-037 |
| US-SUP-03 | FR-038, FR-050 |
| US-SUP-04 | FR-039, FR-042 |
| US-SUP-05 | FR-040, FR-041, FR-024 |
| US-ADM-01 | FR-006 |
| US-ADM-02 | FR-046 |
| US-ADM-03 | FR-047, FR-012 |
| US-ADM-04 | FR-048 |
| US-ADM-05 | FR-049, FR-050, NFR-008 |
| US-ADM-06 | FR-033, FR-034 |
| US-SYS-01 | FR-004, NFR-005 |
| US-SYS-02 | FR-028, FR-030, FR-031, FR-032, FR-050 |
| US-SYS-03 | FR-029, FR-042–FR-045, NFR-003, NFR-012 |
| US-P1-01 | FR-051, FR-054 |
| US-P1-02 | FR-052 |
| US-P1-03 | FR-053 |
| US-P1-04 | FR-055 |
| US-E2E-01 | FR-001–FR-050 |

**Coverage assertion:** all P0 requirements FR-001–FR-050 appear in at least one story above. P1 requirements FR-051–FR-057 appear in `US-P1-01`–`US-P1-04` and `US-CIT-16`. P2 requirements FR-058–FR-064 intentionally have no MVP stories.

---

*End of User Stories.*
