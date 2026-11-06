# CivicTrack — Product Requirements Document (PRD)

| Field | Value |
|---|---|
| Product | CivicTrack — Community Problem Reporting and Resolution Platform |
| Document | Product Requirements Document |
| Version | 1.0 |
| Date | 06 November 2026 |
| Status | Approved for 10-hour hackathon build |
| Owner | Product Management |
| Audience | Hackathon team, reviewers, judges, future maintainers |
| Companion documents | `SRS.md`, `USER_STORIES.md`, `TRD.md` |

---

## 1. Document Purpose

This PRD defines **why** CivicTrack exists, **who** it serves, **what** the product must do, and **how success is judged** for the 10-hour hackathon build. It is the product-level agreement; it does not prescribe implementation.

- The **SRS** converts this scope into numbered, testable requirements.
- `USER_STORIES.md` converts the requirements into role-based deliverables with Given/When/Then acceptance criteria.
- `TRD.md` defines how the requirements will be built with the agreed stack.

**In scope of this document:** product vision, users, outcomes, feature scope, business rules, priorities, risks, and the canonical complaint lifecycle shared by all four documents.

**Out of scope of this document:** database schemas, endpoint contracts, framework choices, and code-level design (see TRD). This is a prototype specification, not a procurement document, and it does not claim any municipal partnership or legal authority.

**Decision rule for conflicts:** if this PRD and the SRS disagree, the SRS governs testable behavior and this PRD must be corrected. The canonical lifecycle in Appendix A is normative for all four documents.

---

## 2. Product Overview

CivicTrack is a transparent, role-based web platform that connects residents with the municipal department responsible for a local civic problem. A citizen submits a complaint with a title, description, category, optional photos, and an optional location. CivicTrack assigns a unique tracking number, routes the complaint to the mapped department, and exposes a dated timeline to the citizen.

The department reviews the complaint and either accepts it (starting a seven-calendar-day resolution clock) or rejects it with a mandatory reason. Accepted complaints can be assigned, updated with progress notes and evidence, and finally resolved with a resolution note. If an accepted complaint is not resolved before its deadline, a background job **automatically** escalates it to the Superintendent Officer and notifies the Superintendent, the department, and the citizen. The Superintendent can review the full history, record instructions or follow-up actions, and monitor the complaint until an authorized officer records a resolution.

**The product is not:** a general-purpose municipal ERP, a public social network, a verified-fact reporting system, or a replacement for a real municipal complaint process. A submitted complaint is an **unverified report** until an authorized officer acts on it.

---

## 3. Background and Problem Statement

### 3.1 Current situation

Residents encounter civic defects daily: broken streetlights, potholes and damaged roads, overflowing bins, blocked drains, water leakage, and damaged public infrastructure. Reporting is inconsistent. A resident may call an office, message an unofficial number, post on social media, or give up entirely. There is no shared record, no acknowledgement, and no way to know which department owns the issue.

Departments, in turn, receive reports through disconnected channels with missing details and no reliable prioritisation. Accepted work is tracked informally, if at all. When a case stalls, nothing forces supervisory attention; escalation depends on a citizen complaining again or an individual officer forwarding an email.

### 3.2 Problem statement

> Residents cannot reliably report local civic problems, cannot tell whether the responsible department has accepted the issue, and cannot see whether it is being worked on. Departments lack a structured intake and progress record, and overdue accepted complaints have no automatic path to supervisory attention.

### 3.3 Observed failure modes to design against

| # | Failure mode | Consequence | CivicTrack response |
|---|---|---|---|
| P-1 | Resident does not know the responsible department | Report is misdirected or abandoned | Category-to-department routing |
| P-2 | No acknowledgement after reporting | Resident assumes nothing happened | Acceptance notification with department and target date |
| P-3 | No shared status record | Duplicate calls, conflicting answers | Single status timeline per complaint |
| P-4 | Work stalls silently | Issue remains unresolved indefinitely | Seven-day automatic escalation |
| P-5 | Escalation depends on a person | Overdue cases are missed | Scheduler-driven, idempotent escalation |
| P-6 | Actions are unattributed | No accountability | Actor and timestamp on every status change |
| P-7 | "Resolved" is claimed without evidence | Trust erodes | Authorized resolution with mandatory note |
| P-8 | Personal details or exact location leak | Privacy harm | Role-scoped access to PII and coordinates |

### 3.4 Why this is a good hackathon problem

The core value is a complete, demonstrable state machine with a time-based automation. It can be built end-to-end in ten hours without external integrations, while still exercising authentication, authorization, file upload, relational modelling, background jobs, notifications, and auditability.

---

## 4. Product Vision

> **A civic complaint that cannot be ignored:** every report has an owner, a clock, a visible history, and a supervisory safety net.

CivicTrack should make the responsible department obvious, make progress visible, and make inaction expensive. The product succeeds when a resident can answer three questions at any moment: *Who has my complaint? What is happening? When should I expect action?*

---

## 5. Project Goals

| Goal | Description | Evidence of achievement |
|---|---|---|
| G-1 Accessible reporting | A first-time user can submit a complete complaint in under a minute on a phone-sized screen | Timed usability run of the demo flow |
| G-2 Correct ownership | Every complaint lands in exactly one mapped department queue | Routing test across all seeded categories |
| G-3 Visible accountability | Citizen sees status, department, dates, and a chronological timeline | Screenshot/walkthrough of timeline |
| G-4 Time-bound action | Acceptance starts a seven-calendar-day clock; breach triggers automatic escalation | Automated escalation test using demo window |
| G-5 Supervisory control | Superintendent can see overdue cases, full history, and record attributable instructions | Superintendent walkthrough |
| G-6 Truthful closure | Only an authorized officer can resolve, with a recorded note and optional evidence | Negative test: unresolved/timeout never shows "Resolved" |
| G-7 Safe by role | Citizens cannot reach department, Superintendent, or admin operations | RBAC test matrix |
| G-8 Demo reliability | One command boots the stack with seeded users and a reproducible escalation demo | Fresh-clone rehearsal |

---

## 6. Measurable Objectives

Targets are scoped to the hackathon prototype and its demo environment. They are deliberately conservative and measurable without production traffic.

| ID | Objective | Target | How measured |
|---|---|---|---|
| O-1 | End-to-end lifecycle demonstrable | All SRS §19 acceptance criteria (AC-01–AC-16) pass in one continuous run | Moderator checklist |
| O-2 | Submission effort | Median ≤ 60 seconds from opening the form to receiving a tracking number (5 trials) | Stopwatch during rehearsal |
| O-3 | Routing accuracy | 20/20 seeded complaints routed to the expected department | Automated routing test |
| O-4 | Escalation timeliness | Escalated within one scheduler cycle (≤ 60 s) after the configured deadline | Integration test with a 2-minute window |
| O-5 | Escalation idempotency | 0 duplicate escalation rows across 20 consecutive scheduler executions | Concurrency/idempotency test |
| O-6 | Timeline completeness | 100% of status transitions have actor, previous status, new status, and UTC timestamp | Database assertion after E2E run |
| O-7 | Access control | 0 successful unauthorized operations across the 12-case RBAC matrix | Automated negative tests |
| O-8 | Notification visibility | In-app notification visible within 30 s of the triggering action | Notification test with polling |
| O-9 | API responsiveness | p95 < 1 s for list endpoints, < 2 s for detail endpoints at demo data volume | Timed test run |
| O-10 | Reproducible setup | `docker compose up` + seed + first login in ≤ 10 minutes on a clean machine | Fresh-clone rehearsal |

---

## 7. Target Users and Personas

### 7.1 Persona summary

| Persona | Role | Context | Primary goal | What success looks like |
|---|---|---|---|---|
| **Priya, resident** | Citizen | Commutes daily, reports a dark streetlight from her phone | Get acknowledgement and a credible timeline | Knows the department, the target date, and every update without calling anyone |
| **Arjun, department officer** | Department Officer (Road Maintenance) | Manages a queue between site visits | Triage, accept, assign, and close complaints with minimal clicks | Queue is ordered and scoped; acceptance and resolution take under a minute each |
| **Meera, Superintendent Officer** | Superintendent Officer | Oversees multiple departments and overdue cases | See what is late and force follow-up | One queue shows every overdue accepted complaint with its full history and delay |
| **Ravi, platform administrator** | Platform Administrator | Maintains accounts and routing configuration | Keep the platform correct and auditable | Can fix a mapping or role in minutes and see who did what |

### 7.2 Persona detail

**Priya — Citizen.** Reports problems occasionally, not a power user. Uses a mid-range Android phone on a slow connection. Distrusts "we will look into it" and has no patience for forms longer than a few fields. Needs plain language, visible status, and a reference number she can keep.

**Arjun — Department Officer.** Works at a desk and in the field. Wants a short queue, the evidence photo, and a clear accept/reject decision. Needs to record why a complaint was rejected and to show progress without writing a report. Is not interested in administrative configuration.

**Meera — Superintendent Officer.** Accountable for delays she did not create. Needs an exception-based view: only escalated complaints, sorted by overdue duration, with the department, acceptance date, deadline, and every departmental action in one place. Her instructions must be attributable.

**Ravi — Platform Administrator.** Technical caretaker. Needs to create officer accounts, fix a wrong category mapping, and review suspicious activity. Should not be able to silently perform operational actions; administration is separate from service delivery.

### 7.3 Out-of-scope users

Not designed for: municipal elected officials, external auditors, journalists, anonymous public viewers, or multiple municipalities in one deployment. These are future personas (see §20).

---

## 8. User Pain Points

| ID | Pain point | Affected persona | Current workaround | Product response |
|---|---|---|---|---|
| PP-1 | "I don't know which department handles this" | Citizen | Calls the main switchboard | Category selection + automatic routing |
| PP-2 | "I never heard back" | Citizen | Calls again or gives up | Acknowledgement notification with department and target date |
| PP-3 | "I don't know if anyone is working on it" | Citizen | Social media complaints | Status timeline with dated progress notes |
| PP-4 | "Nothing happens for weeks" | Citizen, Superintendent | Informal escalation by phone | Automatic seven-day escalation |
| PP-5 | "Reports arrive with no photo or location" | Department Officer | Calls the resident back | Optional photo evidence and location at submission |
| PP-6 | "I can't tell which cases are late" | Superintendent | Manual spreadsheet review | Escalation queue sorted by overdue duration |
| PP-7 | "Nobody owns the decision" | All officers | Verbal instructions | Actor-attributed actions and status history |
| PP-8 | "The complaint was closed but the pothole is still there" | Citizen | Reports again | Authorized resolution note + P1 feedback/reopen |
| PP-9 | "I can see other people's addresses" | Citizen | None | Role-scoped access to PII and precise coordinates |
| PP-10 | "Changing a category breaks routing" | Administrator | Code change | Admin-managed category-to-department mapping |

---

## 9. Proposed Solution

CivicTrack is a single web application with four role-specific experiences over one shared complaint record.

| Pain | Capability | Why it works |
|---|---|---|
| PP-1, PP-5 | Structured submission with category, photos, optional location | Routing becomes deterministic; officers get evidence up front |
| PP-2, PP-3 | Acceptance acknowledgement + chronological timeline | The citizen receives a department name, a target date, and every update |
| PP-4, PP-6 | Deadline computed at acceptance + scheduled escalation | Delay is detected by the system, not by a person |
| PP-7 | Append-only status history and action records | Every decision has an actor and a timestamp |
| PP-8 | Authorized resolution with mandatory note and optional evidence | The product never infers closure from silence |
| PP-9 | Role-based access and field-level privacy | Only the owner, responsible department, Superintendent, and administrator see sensitive data |
| PP-10 | Admin configuration of departments and mappings | Routing can be corrected without a deployment |

**Deliberate simplifications for the hackathon**

- In-app notifications only. No email, SMS, WhatsApp, or push provider.
- One municipality per deployment. No multi-tenancy.
- Optional free-text location plus optional latitude/longitude. No geocoding, boundary lookup, or ward assignment.
- No AI in the critical path. AI categorization and priority are suggestions only (P1).
- No message broker, no microservices, no websockets. Polling is sufficient.
- Fixed seven-calendar-day rule. Working-day and holiday calendars are deferred.

**The differentiator:** escalation is computed from the acceptance timestamp and executed by an idempotent background job, so the demo (and the product) proves that overdue complaints reach supervision without human forwarding.

---

## 10. Core Features

Feature names below are normative and are used identically in the SRS, user stories, and TRD.

| Feature | Description | Priority | Requirements |
|---|---|---|---|
| Authentication and Access Control | Registration, login, JWT sessions, role guards, department scoping | P0 | FR-001–FR-006, NFR-004–NFR-006 |
| Complaint Submission | Title, description, category, optional photo and location, unique tracking number | P0 | FR-007–FR-013 |
| Photo Evidence | Up to three validated images attached to a complaint or update | P0 | FR-010, FR-023, NFR-013 |
| Location Capture | Optional free-text location plus optional coordinates | P0 | FR-011, NFR-007 |
| Category Routing | Configurable category-to-department mapping applied at submission | P0 | FR-012, FR-046, FR-047 |
| Department Review | Department-scoped queue, accept with timestamp, reject with reason | P0 | FR-017–FR-020 |
| Progress Tracking | Assignment, progress notes, status change to IN_PROGRESS | P0 | FR-021, FR-022, FR-026 |
| Complaint Timeline | Append-only, chronological history of every event | P0 | FR-016, FR-050, NFR-008 |
| Automatic Escalation | Seven-calendar-day deadline from acceptance, scheduled, idempotent escalation | P0 | FR-027–FR-034 |
| Superintendent Oversight | Escalation queue, delay view, full history, attributable instructions | P0 | FR-035–FR-041 |
| Resolution Recording | Authorized resolution with mandatory note and optional after-photo | P0 | FR-024, FR-041, BR-17 |
| In-App Notifications | Trigger-based notifications with unread counts | P0 | FR-042–FR-045 |
| Administration and Configuration | Users, roles, departments, categories, mappings, activity view | P0 | FR-006, FR-046–FR-049 |
| Audit Trail | Attributable status, action, and security events | P0 | FR-050, NFR-008 |
| AI Category and Priority Suggestions | Gemini-powered suggestions requiring human confirmation | P1 | FR-051, FR-054 |
| Duplicate Detection | Same-category, time-and-distance-based suggestions | P1 | FR-052 |
| Issue Map | Leaflet/OpenStreetMap view of geolocated complaints | P1 | FR-053 |
| Analytics Dashboard | Counts by status, department, and age (Recharts) | P1 | FR-055 |
| Citizen Feedback and Reopening | Rating and reopening request after resolution | P1 | FR-056, FR-057 |

---

## 11. Detailed Feature Descriptions

### 11.1 Authentication and Access Control

Citizens self-register with name, email, password, and optional phone. Officers, Superintendents, and Administrators are provisioned by an Administrator or by the seed script. Login returns a JWT; every protected request is authorized on the server against the user's current role and department. Citizens have no route, navigation item, or API permission for departmental or supervisory operations.

**Rules:** unique case-insensitive email; password at least 8 characters with a letter and a digit; hashed with bcrypt; inactive users cannot log in; role changes take effect on the next request; a Department Officer is always bound to exactly one department.
**Failure experience:** generic "invalid email or password" message; no account enumeration; 403 with a readable message on unauthorized access.

### 11.2 Complaint Submission

The citizen selects a category, enters a title (5–150 characters) and description (20–2,000 characters), optionally attaches up to three images and an optional location, and submits. The system validates the input, generates a unique tracking number in the form `CT-<YYYY>-<6-digit sequence>` (for example `CT-2026-000042`), creates the complaint, writes the initial history entries, routes it to the mapped department, and returns the tracking number.

**Rules:** every complaint belongs to exactly one citizen and one department; category must be active and mapped; submission is not verification; the citizen cannot choose a department; a failed image upload must not create a half-written complaint.
**Success experience:** a confirmation screen shows the tracking number, department, status "Pending Department Review", and a link to the timeline.

### 11.3 Photo Evidence and Location

Images are optional but recommended. Accepted formats are JPEG, PNG, and WebP, up to 5 MB each, maximum three per complaint at submission. Department officers can attach progress or resolution evidence later. Location is optional free text (for example "Near Gate 2, Market Road") plus optional latitude/longitude captured by the browser or entered manually. No map is required for P0; the coordinates are stored for the P1 issue map.

**Privacy:** precise coordinates and location text are visible only to the complainant, officers of the responsible department, the Superintendent, and the Administrator. They are never exposed on a public page.

### 11.4 Category Routing

Active categories each map to exactly one active department. Routing happens once, transactionally, at submission, and the assigned department is immutable for P0. If a mapping is changed later, existing complaints keep their original department; only new complaints use the new mapping. Administrators can change mappings without a code deployment.

**Seeded defaults (assumption A-03):**

| Category | Department |
|---|---|
| Pothole / Damaged Road | Road Maintenance Department |
| Broken Streetlight | Electrical Department |
| Garbage Overflow | Sanitation Department |
| Blocked Drainage | Drainage Department |
| Water Leakage | Water Supply Department |
| Damaged Public Infrastructure | Public Works Department |
| Other Community Issue | Public Works Department |

### 11.5 Department Review and Decision

Each Department Officer sees only their department's complaints. The default queue is sorted by submission time with status filters and counts. The officer opens the complaint, reviews evidence, and chooses:

- **Accept** — records `accepted_at` and the accepting officer, sets `resolution_due_at = accepted_at + 7 calendar days`, changes status to `ACCEPTED`, and notifies the citizen with the department name, acceptance time, and target date.
- **Reject** — requires a reason of 10–1,000 characters, changes status to `REJECTED`, records the reason, and notifies the citizen. Rejection is terminal for P0.

Acceptance and rejection are allowed only while the status is `PENDING_DEPARTMENT_REVIEW`; a second attempt returns a conflict error. The officer cannot accept a complaint assigned to another department.

### 11.6 Progress Tracking and Resolution

After acceptance, the officer can assign the complaint to a staff member, add progress notes, change the status to `IN_PROGRESS`, and upload evidence. Every update is timestamped and visible to the citizen, except notes explicitly marked internal. Resolution requires a resolution note (10–2,000 characters), changes the status to `RESOLVED`, records the resolving officer and time, optionally attaches an after-photo, and notifies the citizen. Resolution is allowed from `ACCEPTED`, `IN_PROGRESS`, or `ESCALATED`. It is never allowed from `SUBMITTED`, `PENDING_DEPARTMENT_REVIEW`, or `REJECTED`.

**Truthfulness rule:** the system never derives `RESOLVED` from inactivity, from a deadline passing, or from an automated process. Only an authorized officer action creates the resolution.

### 11.7 Automatic Escalation

When a complaint is accepted, the system stores `sla_seconds` (the window applied at that moment) and `resolution_due_at`. A background scheduler evaluates candidates every 60 seconds by default. A complaint is escalated when all of the following are true:

1. `accepted_at` is not null.
2. Status is `ACCEPTED` or `IN_PROGRESS`.
3. `resolution_due_at <= now (UTC)`.
4. No escalation record exists for the complaint.

The escalation transaction changes the status to `ESCALATED`, creates exactly one escalation row, writes a system-attributed history entry, and creates notifications for the Superintendent, the responsible department's officers, and the citizen. Departmental progress updates remain possible after escalation; the status stays `ESCALATED` until a resolution is recorded. There is no re-escalation in P0.

**Demo configuration:** the window defaults to 10,080 minutes (seven calendar days) and may be overridden only with an explicit `ALLOW_DEMO_ESCALATION=true` flag. A two-minute window is used for the live demo. The production default is never replaced in code or in documentation by the demo interval.

### 11.8 Superintendent Oversight

The Superintendent has a separate dashboard listing escalated complaints, sorted by overdue duration, with the responsible department, acceptance date, deadline, and current status. Opening a complaint shows the complete timeline, departmental progress, and escalation metadata. The Superintendent can record an instruction, follow-up, reassignment directive, or note; each record stores the officer identity, action type, note, optional target department, and timestamp, and notifies the department and the citizen. The Superintendent can also record the resolution of an escalated complaint after intervention.

### 11.9 In-App Notifications

Notifications are rows tied to a recipient and optionally a complaint. They are generated inside the same database transaction as the action that triggers them, so a status change cannot succeed without its notification record. The UI shows an unread badge and a notification list; polling every 30 seconds is sufficient. Content always includes the tracking number and the new status; rejection includes the reason; acceptance includes the department and target date; escalation includes the overdue duration.

### 11.10 Administration

Administrators manage users and roles, departments, categories, and mappings. They can view platform activity (counts by status, department, and escalation) and audit logs. Because the P1 analytics dashboard is optional, P0 exposes a simple activity table and counters. Administrative actions are themselves audited.

**Separation of duties:** having the Administrator role does not grant operational accept, reject, progress, or resolve actions. An Administrator who must act operationally needs a separate operational role account, which is out of scope for the hackathon (assumption A-08).

### 11.11 P1 Features (only if the P0 path is stable)

- **AI Category and Priority Suggestions (Gemini):** suggest a category and priority from the title and description. Suggestions are displayed with a confidence label and require citizen or officer confirmation. Failure or timeout falls back silently to manual selection.
- **Duplicate Detection:** when a new complaint is submitted, show up to three same-category complaints within 500 m and 7 days. The citizen may still submit; officers decide whether to link or ignore. No automatic merging.
- **Issue Map:** Leaflet + OpenStreetMap markers for complaints with coordinates, filtered by the viewer's scope. No clustering, heatmaps, or routing.
- **Analytics Dashboard:** Recharts views of complaints by status, department, category, and age. Read-only.
- **Citizen Feedback and Reopening:** a rating and comment on a resolved complaint, and a reopening request that the department can accept, moving the complaint to `REOPENED` and restarting a fresh deadline on re-acceptance. Optional; not required for the demo.

---

## 12. User Journeys

Status values in **bold** are persisted statuses. All timestamps are stored in UTC and displayed in the configured timezone.

### J-01 Citizen reports a problem (happy path)

| Step | Actor | Action | Resulting state |
|---|---|---|---|
| 1 | Citizen | Registers or logs in | Authenticated session |
| 2 | Citizen | Opens "Report a problem" | Submission form |
| 3 | Citizen | Selects category, enters title and description | Draft |
| 4 | Citizen | Attaches photos and optional location (optional) | Draft with evidence |
| 5 | System | Validates, generates tracking number, routes | **SUBMITTED** → **PENDING_DEPARTMENT_REVIEW** in one transaction |
| 6 | Citizen | Sees tracking number and department | Confirmation |
| 7 | Citizen | Receives in-app submission notification (NT-01) | Notification list updated |

### J-02 Department reviews and accepts

| Step | Actor | Action | Resulting state |
|---|---|---|---|
| 1 | Department Officer | Opens department queue and selects the complaint | **PENDING_DEPARTMENT_REVIEW** |
| 2 | Department Officer | Reviews description, photos, location | Unchanged |
| 3 | Department Officer | Clicks Accept | **ACCEPTED**, `accepted_at` recorded, deadline computed |
| 4 | System | Notifies citizen with department and target date (NT-02) | Notification created |
| 5 | Citizen | Sees acknowledgement and target date | Timeline updated |
| 6 | Department Officer | Assigns staff, adds progress note | **IN_PROGRESS** |
| 7 | System | Notifies citizen (NT-04) | Notification created |

### J-03 Department rejects a complaint

| Step | Actor | Action | Resulting state |
|---|---|---|---|
| 1 | Department Officer | Opens a pending complaint | **PENDING_DEPARTMENT_REVIEW** |
| 2 | Department Officer | Clicks Reject and enters a reason | Reason validated (10–1,000 chars) |
| 3 | System | Records rejection, actor, timestamp | **REJECTED** |
| 4 | System | Notifies citizen with the reason (NT-03) | Notification created |
| 5 | Citizen | Reads the reason in the timeline and notification | No resolution clock exists |

### J-04 Escalation after seven days

| Step | Actor | Action | Resulting state |
|---|---|---|---|
| 1 | System | Scheduler runs and evaluates accepted complaints | No change for in-window cases |
| 2 | System | Finds an accepted complaint past `resolution_due_at` with no escalation | Candidate |
| 3 | System | In one transaction: status change, escalation row, history, notifications | **ESCALATED** |
| 4 | System | Notifies Superintendent, department officers, and citizen (NT-05) | Three recipient groups |
| 5 | Superintendent | Opens escalation queue, sees overdue duration and full history | Queue updated |
| 6 | Superintendent | Records instruction directed at the department (NT-06) | Timeline and action log updated |
| 7 | Department Officer | Adds progress and resolves with note (NT-07) | **RESOLVED** |

### J-05 Overdue complaint resolved after intervention

| Step | Actor | Action | Resulting state |
|---|---|---|---|
| 1 | Superintendent | Reviews overdue complaint and departmental delay | **ESCALATED** |
| 2 | Superintendent | Records a follow-up action with a deadline instruction | **ESCALATED** |
| 3 | Department Officer | Completes work, uploads after-photo, records resolution note | **RESOLVED** |
| 4 | System | Notifies the citizen with the resolution summary (NT-07) | Notification created |
| 5 | Citizen | Views the complete history from submission to resolution | Timeline complete |

### J-06 Unauthorized access attempt

| Step | Actor | Action | Resulting state |
|---|---|---|---|
| 1 | Citizen | Manually navigates to `/department` | Route guard shows not-authorized |
| 2 | Citizen | Calls `POST /api/v1/complaints/{id}/accept` with a valid token | Server returns `403 FORBIDDEN` |
| 3 | System | Writes an audit log entry for the denied attempt | Unchanged complaint |
| 4 | Citizen | Can still view only their own complaints | Scoped data |

### J-07 P1 reopening (optional)

| Step | Actor | Action | Resulting state |
|---|---|---|---|
| 1 | Citizen | Opens a resolved complaint and requests reopening with a reason | Request recorded (P1) |
| 2 | Department Officer | Reviews and accepts the reopening | **REOPENED** |
| 3 | Department Officer | Re-accepts work | **IN_PROGRESS** with a new deadline |
| 4 | System | Notifies both parties (NT-08) | Timeline updated |

---

## 13. Business Rules

These rules are normative in all four documents. The SRS assigns each to testable requirements.

| ID | Rule |
|---|---|
| BR-01 | Every complaint has a unique, human-readable tracking number and an internal identifier. |
| BR-02 | Every complaint is associated with exactly one Citizen account. |
| BR-03 | Every complaint is routed at submission to exactly one active department via its category mapping. |
| BR-04 | Only an authorized officer of the assigned department may accept or reject a complaint. |
| BR-05 | The seven-calendar-day timer starts at `accepted_at`, never at submission time. |
| BR-06 | "Seven days" means seven calendar days (168 hours / 10,080 minutes), not working days. |
| BR-07 | An accepted complaint that remains unresolved after its deadline must be escalated automatically. |
| BR-08 | Escalation occurs exactly once per complaint in P0; re-escalation requires a future authorized workflow. |
| BR-09 | The Superintendent Officer can view the full history and all departmental actions for escalated complaints. |
| BR-10 | Every status change records the previous status, new status, actor identity (or `SYSTEM`), and UTC timestamp. |
| BR-11 | Only an authorized Department Officer or the Superintendent Officer may mark a complaint `RESOLVED`. |
| BR-12 | Submission does not verify the reported issue; the UI must not label a complaint as verified. |
| BR-13 | A rejection must include a recorded reason; the reason is shown to the citizen. |
| BR-14 | Citizens receive in-app notifications for submission, acceptance, rejection, progress, escalation, and resolution. |
| BR-15 | Personal information and precise location are visible only to authorized roles and are never exposed publicly. |
| BR-16 | Only the approved status transitions in Appendix A are legal; any other transition returns a conflict error and changes nothing. |
| BR-17 | Resolution requires a resolution note and an authorized actor; after-evidence is optional. |
| BR-18 | Escalation does not remove or change the original department assignment; the department may continue updating the complaint. |
| BR-19 | The production escalation window is 10,080 minutes; a demo override is an explicit, guarded configuration and never a code default. |
| BR-20 | The system never infers `RESOLVED` from silence, elapsed time, or an automated process. |

---

## 14. Functional Scope

### 14.1 In scope for P0 (must demo)

- Citizen registration, login, logout, and own-profile view.
- Role-based access for four roles, with server-side enforcement and department scoping.
- Complaint submission with category, title, description, up to three images, and optional location.
- Unique tracking number, initial history, and transactional routing.
- Citizen complaint list, detail, status, department, dates, images, and chronological timeline.
- Department queue, detail, accept, reject with reason, assign staff, progress notes, evidence, and resolution.
- Seven-calendar-day deadline from acceptance, background check, exactly-once escalation, and escalation metadata.
- Escalation notifications to Superintendent, department, and citizen.
- Superintendent escalation queue, delay view, full history, instruction/follow-up recording, and resolution.
- In-app notification list, unread count, and mark-as-read.
- Administrator management of users/roles, departments, categories/mappings, plus activity and audit views.
- Audit trail for status changes and administrative/security events.
- Seeded demo accounts and data, Dockerized local run.

### 14.2 In scope only if P0 is complete (P1)

AI category/priority suggestion, duplicate suggestions, issue map, analytics dashboard, citizen feedback/reopening.

### 14.3 Explicitly out of scope

See §15.

---

## 15. Out-of-Scope Features

| Out-of-scope item | Why excluded | Future |
|---|---|---|
| Email, SMS, WhatsApp, push notifications | External providers add setup, cost, and failure modes | P2 |
| Multi-city / multi-tenant operation | Requires tenancy model and isolation design | P2 |
| Working-day, holiday, or pause-aware SLAs | Calendar engine is disproportionate for 10 hours | P2 |
| AI-based verification of photo authenticity | Cannot be validated responsibly in the timebox | P2 |
| Public transparency portal or open data API | Privacy review required | P2 |
| Native mobile applications | Responsive web is sufficient for the demo | P2 |
| Integration with real municipal systems | No partnership, credentials, or authority | P2 |
| Payments, fines, or billing | Not part of the complaint lifecycle | Not planned |
| Live chat or social media ingestion | Undefined moderation and identity model | Not planned |
| GIS polygons, ward boundaries, routing directions | Map is optional and marker-only | P1/P2 |
| Predictive analytics or officer performance scoring | Insufficient data and high misuse risk | Not planned |
| Full offline/PWA support | Not needed for the demo environment | Not planned |

---

## 16. MVP Priorities (P0/P1/P2)

### 16.1 P0 — mandatory for a successful demonstration

Everything in §14.1. The end-to-end lifecycle and the automatic escalation are non-negotiable. P0 is defined by FR-001 through FR-050 and NFR-001 through NFR-022.

### 16.2 P1 — important only if P0 is stable

| Feature | Requirements | Minimal demo value |
|---|---|---|
| AI Category and Priority Suggestions | FR-051, FR-054 | Show a suggestion with manual confirmation |
| Duplicate Detection | FR-052 | Show candidate duplicates before submit |
| Issue Map | FR-053 | Plot seeded geolocated complaints |
| Analytics Dashboard | FR-055 | Three charts on admin screen |
| Citizen Feedback and Reopening | FR-056, FR-057 | Rate a resolved complaint; request reopening |

### 16.3 P2 — future enhancements

FR-058 through FR-064: external notification channels, multi-tenancy, SLA calendars, AI verification, public portal, native apps, municipal integrations.

### 16.4 Cut-line policy

1. Freeze P0 at Hour 1 and do not add scope later.
2. If a P0 item slips, reduce polish (animations, empty-state art, advanced filters), not the lifecycle.
3. Drop P1 features in reverse order: analytics, map, duplicates, AI.
4. Never disable or fake escalation to save time; use the guarded demo window instead.
5. A P1 feature must not introduce a new mandatory table, external dependency, or migration after Hour 7.

---

## 17. Success Metrics

### 17.1 Hackathon success (release gate)

The build is successful only when all of the following are true in one continuous demonstration:

| Metric | Target |
|---|---|
| Citizen submits a complaint and receives a tracking number | Pass |
| Complaint appears in the correct department queue | Pass |
| Department accepts; citizen sees acknowledgement with department and target date | Pass |
| Citizen sees current status and dated progress history | Pass |
| Deadline equals acceptance time + configured window (7 days in production, 2 minutes in demo) | Pass |
| An overdue unresolved complaint appears automatically in the Superintendent queue | Pass (no manual forwarding) |
| Repeated scheduler runs create no duplicate escalation | Pass (20 runs) |
| Superintendent records an instruction visible in the timeline with identity and timestamp | Pass |
| Authorized officer resolves; citizen sees the resolution update | Pass |
| Citizen cannot access department or Superintendent operations | Pass (12-case matrix) |
| No complaint can be shown as resolved without a recorded resolution | Pass |

### 17.2 Product success metrics for a future pilot (not measured in the hackathon)

These are targets to validate after adoption. They are not claims of current performance.

| Metric | Target | Instrumentation needed |
|---|---|---|
| Median time from submission to department decision | ≤ 48 hours | `accepted_at - submitted_at` |
| Share of accepted complaints resolved before deadline | ≥ 85% | Status history + escalation rows |
| Share of complaints escalated | ≤ 15% | Escalation count / accepted count |
| Median time from escalation to first supervisory action | ≤ 24 hours | `officer_actions` timestamps |
| Citizen notification coverage for defined triggers | 100% | Notification table reconciliation |
| Citizen-reported clarity of status | ≥ 4/5 | Post-resolution survey (future) |

### 17.3 Anti-metrics (must not happen)

- A complaint displayed as resolved without a resolution record.
- Two escalation rows for one complaint.
- A citizen seeing another citizen's contact details or coordinates.
- A department officer acting on another department's complaint.
- An escalation that requires a human to forward the case.

---

## 18. Assumptions and Dependencies

### 18.1 Assumptions

| ID | Assumption | Impact if wrong |
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

### 18.2 Dependencies

| ID | Dependency | Owner | Needed by |
|---|---|---|---|
| D-01 | MySQL 8.4 instance (Docker or managed) | Backend | Hour 2 |
| D-02 | Python 3.12 and Node.js 20+ toolchains | Team | Hour 1 |
| D-03 | JWT secret and environment configuration | Backend | Hour 2 |
| D-04 | Seed data for departments, categories, users, and a backdated complaint | Backend | Hour 3 |
| D-05 | A persistent process or container for the API and scheduler | DevOps | Hour 6 |
| D-06 | Google Gemini API key (P1 only) | P1 owner | Hour 8, optional |
| D-07 | OpenStreetMap tile access for Leaflet (P1 only) | P1 owner | Hour 8, optional |

---

## 19. Risks and Mitigations

| ID | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R-01 | Scheduler not running during the demo, so escalation never fires | Medium | High | Run scheduler in a dedicated worker; show last-run status; provide a guarded manual trigger and a pre-seeded overdue complaint | Backend |
| R-02 | Duplicate escalation under retries or overlapping runs | Medium | High | Unique constraint on `escalations.complaint_id`, conditional status update, scheduler lock, concurrency test | Backend |
| R-03 | Deadline computed from submission instead of acceptance | Low | High | Single service method; unit tests with explicit timestamps; UI shows accepted time and deadline | Backend |
| R-04 | Demo window leaks into production | Medium | High | Environment-scoped override plus `ALLOW_DEMO_ESCALATION` guard; fail-fast check; startup log banner | Backend |
| R-05 | Team merges conflict near the end | Medium | Medium | Freeze API contracts at Hour 1; separate feature branches; integrate at Hours 3, 5, 7 | All |
| R-06 | Role checks only in the UI | Medium | High | Server-side dependency on every route; 12-case negative test matrix | Backend |
| R-07 | Image upload failures or oversized files block submission | Medium | Medium | Client-side size check, 5 MB limit, clear errors, submission rollback on failure | Frontend |
| R-08 | MySQL not ready when the API starts | Medium | Medium | Healthcheck + retry on startup; documented compose ordering | DevOps |
| R-09 | Scope creep into AI/map/analytics | High | Medium | P1 gate requires all P0 acceptance criteria; explicit cut line | Product |
| R-10 | Free-tier cold starts slow the deploy demo | Medium | Medium | Rehearse on the target environment; keep a local Docker fallback; warm services before judging | DevOps |
| R-11 | PII exposed in logs or URLs | Low | High | Log allowlist, no coordinates in query strings, review before deploy | Backend |
| R-12 | Judges interpret the demo as a real municipal service | Low | Medium | Persistent "prototype" labeling; no government logos or claims | Product |

---

## 20. Future Enhancements

| Horizon | Enhancement | Rationale |
|---|---|---|
| Near (post-hackathon) | Email/SMS notification adapters with an outbox | Reach citizens who do not open the app |
| Near | Citizen feedback and reopening workflow | Close the loop on disputed resolutions |
| Near | Duplicate linking with officer merge decision | Reduce departmental noise |
| Mid | Working-day and holiday-aware SLAs, category-specific windows | Reflect real service policies |
| Mid | Interactive map with ward boundaries and clustering | Operational planning |
| Mid | Analytics for backlog age, department throughput, and repeat categories | Management oversight |
| Mid | Photo metadata checks and before/after comparison | Stronger evidence |
| Long | Multi-tenant deployment for multiple municipalities | Scale without forks |
| Long | Public transparency portal with privacy-preserving aggregates | Civic accountability |
| Long | Integration with municipal work-order systems | Avoid double entry |
| Long | Accessibility audit to WCAG 2.1 AA and localisation | Inclusive service delivery |

---

## Appendix A — Canonical Reference (normative)

All four documents must use these exact roles, statuses, transitions, triggers, and rules.

### A.1 Roles

| Role code | Display name | Scope |
|---|---|---|
| `CITIZEN` | Citizen | Own complaints and notifications |
| `DEPARTMENT_OFFICER` | Department Officer | Complaints of one assigned department |
| `SUPERINTENDENT_OFFICER` | Superintendent Officer | Escalated complaints and oversight read access |
| `PLATFORM_ADMIN` | Platform Administrator | Users, roles, departments, categories, mappings, activity, audit, read-only complaint detail |

### A.2 Complaint statuses

| Status | Meaning | Entered by | Priority |
|---|---|---|---|
| `SUBMITTED` | Record created; routing in progress within the same transaction | System | P0 |
| `PENDING_DEPARTMENT_REVIEW` | Routed to the mapped department; awaiting decision | System | P0 |
| `ACCEPTED` | Department accepted; `accepted_at` and `resolution_due_at` set | Department Officer | P0 |
| `IN_PROGRESS` | Work underway | Department Officer | P0 |
| `REJECTED` | Declined with a recorded reason; terminal in P0 | Department Officer | P0 |
| `ESCALATED` | Deadline breached; with the Superintendent; sticky until resolved | System (scheduler or guarded manual trigger) | P0 |
| `RESOLVED` | Authorized resolution recorded; terminal in P0 | Department Officer or Superintendent Officer | P0 |
| `REOPENED` | Citizen disputed a resolution; under departmental review | Citizen request + Department Officer acceptance | P1 |

### A.3 Legal transitions

| From | To | Actor | Conditions |
|---|---|---|---|
| `SUBMITTED` | `PENDING_DEPARTMENT_REVIEW` | System | Routing succeeded |
| `PENDING_DEPARTMENT_REVIEW` | `ACCEPTED` | Department Officer | Same department; sets acceptance fields and deadline |
| `PENDING_DEPARTMENT_REVIEW` | `REJECTED` | Department Officer | Same department; reason required |
| `ACCEPTED` | `IN_PROGRESS` | Department Officer | Progress note required |
| `ACCEPTED` | `RESOLVED` | Department Officer | Resolution note required |
| `IN_PROGRESS` | `RESOLVED` | Department Officer | Resolution note required |
| `ACCEPTED` | `ESCALATED` | System (scheduler or guarded manual trigger) | Deadline reached; no escalation exists |
| `IN_PROGRESS` | `ESCALATED` | System (scheduler or guarded manual trigger) | Deadline reached; no escalation exists |
| `ESCALATED` | `RESOLVED` | Department Officer or Superintendent | Resolution note required |
| `RESOLVED` | `REOPENED` | System on accepted citizen request | P1 only |
| `REOPENED` | `IN_PROGRESS` | Department Officer | P1 only; new deadline |

**Superintendent resolution is available only from `ESCALATED` (FR-041).** `ACCEPTED` and `IN_PROGRESS` complaints are resolved by an officer of the assigned department. Any other transition returns `409 INVALID_TRANSITION` and changes nothing.

### A.4 Notification triggers

| ID | Trigger | Recipients | Required content | Priority |
|---|---|---|---|---|
| NT-01 | Complaint submitted | Citizen | Tracking number, category, department, submitted time | P0 |
| NT-02 | Complaint accepted | Citizen | Tracking number, department, accepting officer, acceptance time, resolution deadline | P0 |
| NT-03 | Complaint rejected | Citizen | Tracking number, department, rejection reason | P0 |
| NT-04 | Progress or status update | Citizen | Tracking number, new status, progress note | P0 |
| NT-05 | Automatic escalation | Superintendent, all active officers of the department, Citizen | Tracking number, department, deadline, overdue duration | P0 |
| NT-06 | Supervisory action recorded | Department officers, Citizen | Tracking number, action type, instruction summary, officer identity | P0 |
| NT-07 | Complaint resolved | Citizen | Tracking number, resolution note, resolving officer, resolution time | P0 |
| NT-08 | Reopening accepted | Department officers, Citizen | Tracking number, reopened status | P1 |

**Recipient fallback:** if no active Superintendent exists, NT-05 is delivered to active Administrators, the escalation still proceeds, and an audit event is recorded.

### A.5 Escalation rule (one sentence)

A complaint is escalated **exactly once** when `accepted_at` exists, its status is `ACCEPTED` or `IN_PROGRESS`, `now >= accepted_at + configured window`, and no escalation record exists; the default window is **10,080 minutes (seven calendar days)**, and a demo override (for example, two minutes) is permitted only with an explicit environment guard.

### A.6 Priority definitions

- **P0** — required for the demo and for release; failure blocks the demonstration.
- **P1** — optional, only after all P0 acceptance criteria pass; may be shown if stable.
- **P2** — documented future work; not built during the hackathon.

---

## Appendix B — Glossary

| Term | Definition |
|---|---|
| Acceptance | Department decision that it owns the complaint; starts the resolution clock |
| Acknowledgement | In-app notification confirming acceptance with department and target date |
| Audit log | Append-only record of security-relevant and administrative events |
| Complaint | A citizen-submitted report of a civic problem; unverified until officer action |
| Deadline | `resolution_due_at`, computed at acceptance as `accepted_at + sla_seconds` |
| Department | Organizational unit responsible for a category of civic work |
| Escalation | Automatic transfer of an overdue accepted complaint to the Superintendent queue |
| Idempotent | Repeating the operation does not create a second escalation |
| Overdue duration | `now - deadline` at the time of escalation or review |
| Resolution | Authorized recorded closure with a mandatory note |
| SLA | Service-level window; for this MVP, seven calendar days from acceptance |
| Status history | Append-only record of every status transition with actor and timestamp |
| Timeline | Citizen-visible chronological combination of status changes and progress notes |
| Tracking number | Human-readable unique complaint identifier, `CT-YYYY-NNNNNN` |

---

*End of PRD.*
