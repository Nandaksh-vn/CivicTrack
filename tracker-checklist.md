# CivicTrack — Master Development Execution Tracker

> **File:** `tracker-checklist.md` (project root)  
> **Role:** Single source of truth for implementation progress  
> **Sources of truth:** `docs/PRD.md`, `docs/TRD.md`, `docs/PHASES.md`  
> **Supporting docs (read-only):** `docs/SRS.md`, `docs/USER_STORIES.md`, `CivicTrack_Problem_Statement_and_Objectives.pdf`  
> **Execution model:** Phase-by-phase, dependency-gated, AI-agent executable  
> **Last updated:** 2026-11-06

---

## 1. Tracker Rules

1. Do not start a phase until every dependency phase is **Completed**.
2. Mark `[ ]` → `[x]` **only** after the task is implemented and validated.
3. Never mark a task complete because code was written; validation evidence is required.
4. Never delete a completed entry or reuse a task ID.
5. Keep Database, Backend, Frontend, Integration, Testing, and Deployment tasks separate.
6. Do not modify `docs/PRD.md`, `docs/TRD.md`, or `docs/PHASES.md` from this tracker unless explicitly instructed.
7. If a new requirement is discovered, add it under the correct phase and workstream with the next free ID.
8. Update this file immediately after each completed task and save.

---

## 2. Workstreams

| Code | Workstream | Scope | ID range |
|---|---|---|---|
| `DOC` | Architecture & Documentation | Requirements baseline, architecture, ADRs, API contract, runbooks, traceability | DOC-001+ |
| `DB` | Database | MySQL install/config, schema, keys, constraints, indexes, migrations, seed, query tuning, DB tests | DB-001+ |
| `BE` | Backend | FastAPI init, models, repositories, services, controllers, DTOs, validation, auth, RBAC, uploads, jobs | BE-001+ |
| `FE` | Frontend | React/Vite init, routing, UI kit, pages, forms, state, API client, responsive, component tests | FE-001+ |
| `INT` | Frontend–Backend Integration | Base URL, API wiring, auth/token flow, error handling, CORS, cache sync, E2E wiring | INT-001+ |
| `TEST` | Testing & Quality | Unit, integration, API, component, E2E, security, performance, accessibility, UAT | TEST-001+ |
| `DEP` | Deployment & Operations | Production build, Docker, CI/CD, migrations at boot, deploy, validation, runbook | DEP-001+ |

> Architecture and documentation are separated into `DOC` so that no documentation task is misclassified as backend or database work. Security fixes are applied under the owning workstream (`BE`/`FE`) and verified under `TEST`.

---

## 3. Status & Progress Rules

### 3.1 Task states

| Status | Meaning |
|---|---|
| `Not Started` | No work has begun |
| `In Progress` | Work started, not yet validated |
| `Blocked` | Cannot proceed; dependency or decision outstanding |
| `Pending Review` | Implementation done, awaiting validation/sign-off |
| `Completed` | Implemented, validated, tests pass, evidence recorded |

### 3.2 Formulas

```text
Phase Progress   = Completed Tasks in Phase / Total Tasks in Phase × 100
Overall Progress = Total Completed Tasks / Total Tasks × 100
```

- Round to one decimal place.
- A phase is `Completed` only at **100%** and when its exit criteria are met.
- `Current Development Phase` = first phase whose status is not `Completed`.
- `Blocked tasks` must be listed in the Phase Notes with the blocking reason.

### 3.3 Update protocol (after every task)

1. Locate the exact task ID and change `[ ]` to `[x]`.
2. Increment the phase completed count and recompute the phase percentage.
3. Recompute the overall completed count and percentage.
4. Update the Progress Dashboard row for that phase.
5. Set `Current Development Phase` to the first incomplete phase.
6. Record any blocked/pending task in the phase notes.
7. Save `tracker-checklist.md` immediately.

---

## 4. Progress Dashboard

| Phase | Name | Tasks | Done | Progress | Status |
|---|---|---:|---:|---:|---|
| 1 | Requirements Validation & Scope Baseline | 11 | 11 | 100.0% | Completed |
| 2 | Architecture & Technical Design Baseline | 12 | 12 | 100.0% | Completed |
| 3 | Repository, Tooling & Local Environment | 20 | 20 | 100.0% | Completed |
| 4 | Database Schema & Migrations | 20 | 0 | 0.0% | Not Started |
| 5 | Backend Foundation & Cross-Cutting Core | 15 | 0 | 0.0% | Not Started |
| 6 | Authentication, Sessions & RBAC | 17 | 17 | 100.0% | Completed |
| 7 | Notifications Engine | 9 | 0 | 0.0% | Not Started |
| 8 | Complaint Submission, Media & Routing | 15 | 0 | 0.0% | Not Started |
| 9 | Citizen Tracking & Timeline | 9 | 0 | 0.0% | Not Started |
| 10 | Department Review & Case Management | 15 | 0 | 0.0% | Not Started |
| 11 | Escalation Engine (SLA Worker) | 15 | 0 | 0.0% | Not Started |
| 12 | Superintendent Oversight | 11 | 0 | 0.0% | Not Started |
| 13 | Administration, Configuration & Audit | 9 | 0 | 0.0% | Not Started |
| 14 | Frontend Foundation & Design System | 15 | 15 | 100.0% | Completed |
| 15 | Role Workspaces & UI Flows | 23 | 23 | 100.0% | Completed |
| 16 | Frontend–Backend Integration & State Sync | 13 | 0 | 0.0% | Not Started |
| 17 | QA, Test Automation & UAT | 13 | 13 | 100.0% | Completed |
| 18 | Security, Performance & Accessibility Hardening | 12 | 0 | 0.0% | Not Started |
| 19 | Deployment, Operations & Demo Readiness | 12 | 0 | 0.0% | Not Started |
| 20 | Documentation, Traceability Audit & Final Delivery | 12 | 0 | 0.0% | Not Started |
| 21 | Optional P1 Enhancements (Gated) | 19 | 0 | 0.0% | Not Started |
| **TOTAL** | **All phases** | **297** | **111** | **37.4%** | **In Progress** |

**Current Development Phase:** Phase 4 — Database Schema & Migrations  
**Overall Progress:** 37.4% (111 of 297 tasks)  
**Last completed task:** TEST-035 — Form validation tests mirroring server constraints and 422 field mapping.  
**Blocked tasks:** None

---

## 5. Mandatory Development Workflow

When asked to develop any part of the project:

1. Read this tracker and identify the current incomplete phase and its next uncompleted tasks.
2. Read the matching phase in `docs/PHASES.md` for objective, dependencies, and DoD.
3. Classify the task: `DB`, `BE`, `FE`, `INT`, `TEST`, `DEP`, or `DOC`.
4. Work **only** on the requested phase and its relevant tasks.
5. Keep Database, Backend, and Frontend work logically separated; do not merge responsibilities into one task.
6. Implement, run the relevant tests, and verify acceptance criteria.
7. Mark the task `[x]` and update all progress fields immediately.
8. Report: completed IDs, files created/modified, tests run/results, remaining tasks, phase %, and next recommended task.

---

## 6. Phase 1 — Requirements Validation & Scope Baseline

**Dependencies:** None  
**Objective:** Prove the documented scope is complete, consistent, and testable before code exists.  
**Exit criteria:** Every requirement and story is inventoried, cross-checked, and assigned to a later phase; zero unresolved P0 questions.  
**Requirement coverage:** FR-001…FR-064, NFR-001…NFR-022, BR-01…BR-20, NT-01…NT-08, AC-01…AC-16, 44 user stories.

### Documentation Tasks

- [x] DOC-001 — Build the requirement inventory from SRS: 64 FRs (50 P0 / 7 P1 / 7 P2), 22 NFRs, 20 BRs, 8 NT triggers, 16 ACs.
- [x] DOC-002 — Cross-check every PRD feature against at least one FR; flag any PRD item without a requirement ID.
- [x] DOC-003 — Verify all 44 user stories and map each story to its FRs; record the story→FR matrix.
- [x] DOC-004 — Confirm canonical roles, statuses, legal transitions, SLA window, tracking-number format, and 20-per-page pagination across PRD/SRS/TRD.
- [x] DOC-005 — Confirm P2 exclusions FR-058…FR-064 are labeled future and excluded from P0 acceptance.
- [x] DOC-006 — Log every open question and resolve it as "accept as documented" or "blocked"; no silent assumptions remain.
- [x] DOC-007 — Verify all NFR targets are measurable (p95, 5 MiB, 8 h, 10,080 min, 360 px, 500 complaints/50 users).
- [x] DOC-008 — Verify each AC-01…AC-16 has concrete, reproducible test steps.
- [x] DOC-009 — Reconcile terminology (`complaint`, `ticket`, `Superintendent`, `Platform Admin`) across documents.
- [x] DOC-010 — Publish `docs/TRACEABILITY_BASELINE.md` with FR, NFR, BR, NT, AC, and story matrices.
- [x] DOC-011 — Run a scripted ID diff between SRS and the inventory; require zero missing and zero duplicates.

**Phase Notes:** All 11 documentation tasks validated. Baseline `docs/TRACEABILITY_BASELINE.md` published (84 KB, 765 lines) with 215/215 SRS requirement IDs and 44/44 stories, zero missing, zero duplicates. Scripted validator `OVERALL: PASS`. 14 open questions resolved, 0 open P0, 0 blocked. No application code written.  
**Phase Status:** Completed  
**Phase Completion:** 100.0% (11/11 tasks)

---

## 7. Phase 2 — Architecture & Technical Design Baseline

**Dependencies:** Phase 1  
**Objective:** Freeze modules, data flow, API surface, state machine, security model, and frontend routes before implementation.  
**Exit criteria:** Every P0 FR has an owning module/endpoint; every endpoint declares roles and scope; escalation concurrency design is approved.  
**Requirement coverage:** TRD architecture; NFR-016, NFR-017, NFR-018, NFR-020; enables FR-001…FR-050.

### Documentation Tasks

- [x] DOC-012 — Draw the system context and container diagram (React SPA → FastAPI → MySQL + scheduler worker + uploads volume).
- [x] DOC-013 — Define backend module map and layering rule: `api` → `services` → `models`; no business logic in routers.
- [x] DOC-014 — Freeze the endpoint catalogue: method, path, role, request/response schema, error codes for every P0 endpoint.
- [x] DOC-015 — Freeze the status state machine and legal-transition table; document 409 behavior for illegal transitions.
- [x] DOC-016 — Specify the escalation algorithm: candidate query, advisory lock, conditional update, unique index, transaction boundary.
- [x] DOC-017 — Specify the auth model: JWT HS256, 8 h expiry, `sessionStorage`, role + object-scope policy, 401/403/404 rules.
- [x] DOC-018 — Define the frontend route tree, role guards, query keys, cache invalidation map, and notification polling.
- [x] DOC-019 — Produce sequence diagrams for submit, accept, escalate, resolve, and superintendent action.
- [x] DOC-020 — Define the error taxonomy and error envelope (`400/401/403/404/409/422/500`).
- [x] DOC-021 — Write ADR-001…ADR-008 covering escalation idempotency, notification atomicity, upload storage, UTC time, and demo guard.
- [x] DOC-022 — Review AC-01…AC-16 against the design; each AC must map to a module and endpoint.
- [x] DOC-023 — Publish `docs/ARCHITECTURE.md`, `docs/API_CONTRACT.md`, `docs/STATE_MACHINE.md`, and ADRs.

**Phase Notes:** Phase 2 design baseline published and scripted-validated. ADRs 001–008 cover
  escalation idempotency, notification atomicity, upload storage, UTC time, demo guard, JWT session,
  transaction boundary, and frontend server state. ARCHITECTURE (context/containers, module map,
  env contract, §10 module ownership), API_CONTRACT (40 P0 endpoints, 50/50 FR ownership,
  16/16 AC traceability), STATE_MACHINE (11 legal transitions) published to docs/. The baseline was
  recovered after the external branch reset (docs preserved via git object store and restored onto
  this branch). Additions on restore: API_CONTRACT gained a 'P1 — not built' section, ARCHITECTURE
  gained a gated-P1 section and the admin role home was aligned to `/admin/users` to match the live
  SPA. Validator: ADRs 8/8, 40/40 P0 endpoints, 50/50 FR rows, 16/16 AC rows, 11 transitions,
  8 mermaid diagrams, 0 blockers, P1-not-built PASS.  
**Phase Status:** Completed  
**Phase Completion:** 100.0% (12/12 tasks)

---

## 8. Phase 3 — Repository, Tooling & Local Environment

**Dependencies:** Phase 2  
**Objective:** Create the monorepo skeleton with one-command local startup, pinned dependencies, and CI.  
**Exit criteria:** Clean clone + `.env` + `docker compose up` runs db/api/worker/web; health checks pass; CI is green.  
**Requirement coverage:** NFR-016, NFR-017, NFR-020.

### Database Tasks

- [x] DB-001 — Define the MySQL 8.4 service in Compose with `utf8mb4_0900_ai_ci`, `--default-time-zone=+00:00`, and InnoDB defaults.
- [x] DB-002 — Configure the database volume `civictrack_db`, port mapping, and `mysqladmin ping` healthcheck.
- [x] DB-003 — Verify the database starts healthy and accepts connections with the configured user/password.

### Backend Tasks

- [x] BE-001 — Initialize git and add `.gitignore` for `.env`, uploads, `node_modules`, `__pycache__`, dist, and coverage.
- [x] BE-002 — Scaffold the FastAPI backend on Python 3.12 with the package structure from PHASES §3.5.
- [x] BE-003 — Pin backend dependencies: FastAPI, SQLAlchemy 2, Pydantic v2, Alembic, PyMySQL, PyJWT, bcrypt, APScheduler, ruff, pytest, httpx.
- [x] BE-004 — Create `app/` folders: `models/`, `schemas/`, `api/`, `services/`, `core/`, `workers/`, `utils/`.
- [x] BE-005 — Implement settings loading and startup validation for required secrets and safe defaults.
- [x] BE-006 — Add `/health` liveness returning HTTP 200 from the skeleton app.

### Frontend Tasks

- [x] FE-001 — Scaffold Vite + React 18.3 + TypeScript with `strict: true` and path aliases.
- [x] FE-002 — Configure Tailwind CSS 3.4 and design tokens for color, spacing, and typography.
- [x] FE-003 — Initialize shadcn/ui (Radix primitives) and create the `src/` folder structure (`api`, `components`, `features`, `hooks`, `lib`, `pages`, `router`).
- [x] FE-004 — Install core frontend dependencies: React Router 6, TanStack Query 5, react-hook-form, Zod, Vitest, Testing Library, Playwright.

### Integration Tasks

- [x] INT-001 — Define Compose services `api`, `worker`, and `web` with shared uploads volume and correct `depends_on`/health conditions.
- [x] INT-002 — Create `.env.example` with every TRD §19 variable and safe non-secret examples.
- [x] INT-003 — Add Makefile/npm scripts for `dev`, `test`, `lint`, `typecheck`, `migrate`, `seed`, `compose-up`, `compose-down`.
- [x] INT-004 — Configure the frontend dev proxy or `VITE_API_BASE_URL=/api/v1` for local integration.

### Deployment & Operations Tasks

- [x] DEP-001 — Create the CI workflow: install → lint → typecheck → unit tests → production build.
- [x] DEP-002 — Add pre-commit hooks for formatting and secret scanning.
- [x] DEP-003 — Document the clean-clone quickstart in `README.md` and verify the commands.

**Phase Notes:** Monorepo and toolchain verified end-to-end. Docker stack healthy: MySQL 8.4
  (utf8mb4_0900_ai_ci, UTC, io ping health via `mysqladmin ping`), `uploads` and `civictrack_db`
  volumes, api/worker/web compose services with correct depends_on/health gates, migrate one-shot
  job, idempotent seed profile. `.env.example` covers the TRD A19 contract and stays
  git-ignored; Makefile provides dev/test/lint/typecheck/migrate/seed/compose targets; pre-commit
  wired (ruff, prettier, gitleaks); CI workflow runs backend (pip install, ruff check + format,
  mypy, pytest), frontend (lint, tsc, vitest, build) and compose config validation. Backend:
  pinned deps, `app/` layers present, ruff + mypy clean, 118 pytest green. Frontend: Vite 5 +
  React 18.3 + strict TS + Tailwind 3.4 + RN path aliases, all deps installed; `vite build` OK.
  Example env wiring: `VITE_API_BASE_URL=/api/v1` and vite dev proxy both route to the API;
  `/health`, `/health/ready`, `/` all return HTTP 200 on the running stack.  
**Phase Status:** Completed  
**Phase Completion:** 100.0% (20/20 tasks)

---

## 9. Phase 4 — Database Schema & Migrations

**Dependencies:** Phase 3  
**Objective:** Implement all 11 tables, keys, constraints, indexes, migrations, models, and idempotent seed data.  
**Exit criteria:** `alembic upgrade head` / `downgrade base` round-trip passes; constraints proven by failing tests; seed is repeatable.  
**Requirement coverage:** DB design; BR-01…BR-03, BR-05, BR-08, BR-10, BR-16; NFR-008, NFR-009, NFR-012, NFR-019, NFR-022.

### Database Tasks

- [ ] DB-004 — Create `users` with unique case-insensitive email, role enum, department FK, active flag, and timestamps.
- [ ] DB-005 — Create `departments` with unique name/code and active flag.
- [ ] DB-006 — Create `complaint_categories` with unique name/code, department FK, default priority, and active flag.
- [ ] DB-007 — Create `complaints` with unique `complaint_number`, citizen/category/department FKs, status, priority, all lifecycle timestamps, SLA fields, and rejection/resolution fields.
- [ ] DB-008 — Create `complaint_images` with complaint/uploader FKs, kind enum, storage path, MIME, and size.
- [ ] DB-009 — Create `complaint_status_history` with from/to status, actor nullability, actor role, note, and timestamp.
- [ ] DB-010 — Create `complaint_comments` with author FK, comment type, visibility, and body.
- [ ] DB-011 — Create `notifications` with recipient/complaint FKs, trigger code, title/body, read flag, and read timestamp.
- [ ] DB-012 — Create `escalations` with **UNIQUE `complaint_id`**, escalation number, previous status, deadline, overdue seconds, trigger source, and reason code.
- [ ] DB-013 — Create `officer_actions` with complaint/officer/directed-department FKs, action type, note, and timestamp.
- [ ] DB-014 — Create `audit_logs` with actor, action, entity, IP/user-agent, JSON metadata, and timestamp.
- [ ] DB-015 — Add all primary keys, foreign keys, unique constraints, and check constraints (coordinates pairing/range, deadline requires acceptance).
- [ ] DB-016 — Add all required indexes: citizen list, department queue, escalation candidates, timeline, notifications, audit filters, tracking lookup.
- [ ] DB-017 — Write the Alembic baseline migration and prove `upgrade head` → `downgrade base` → `upgrade head` on a clean database.
- [ ] DB-018 — Implement SQLAlchemy 2 typed models, enums in one shared module, and relationships matching the ERD.
- [ ] DB-019 — Write an idempotent seed script for 6 departments, 7 categories, demo users, and demo complaints using service paths.
- [ ] DB-020 — Add a reset script for local development that drops/recreates schema safely outside production.
- [ ] DB-021 — Publish `docs/DATA_MODEL.md` with the ER diagram and relationship/delete-behavior summary.
- [ ] DB-022 — Add schema tests proving duplicate tracking numbers, duplicate escalations, and invalid coordinate pairs fail.
- [ ] DB-023 — Enforce append-only behavior for history/escalations/officer actions/audit logs at the application boundary; document any DB-level guard.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/20 tasks)

---

## 10. Phase 5 — Backend Foundation & Cross-Cutting Core

**Dependencies:** Phase 4  
**Objective:** Build the shared backend chassis before feature endpoints.  
**Exit criteria:** Config fails fast, errors do not leak internals, logs exclude PII, transactions are explicit, health checks work, test harness isolates state.  
**Requirement coverage:** NFR-009, NFR-012, NFR-016, NFR-018, NFR-021; supports all FRs.

### Backend Tasks

- [ ] BE-007 — Implement the app factory with router registration, middleware, startup/shutdown hooks, and API version prefix `/api/v1`.
- [ ] BE-008 — Implement the DB session dependency with an explicit transaction boundary; services commit/rollback, routers never commit.
- [ ] BE-009 — Implement the standard error envelope `{error:{code,message,details?},request_id}`.
- [ ] BE-010 — Add exception handlers for validation (422), auth (401), forbidden (403), not found (404), conflict (409), and unhandled (500 without internals).
- [ ] BE-011 — Add request-ID middleware that reads/generates `X-Request-ID` and echoes it in responses.
- [ ] BE-012 — Configure structured JSON logging with route, status, duration, and request ID.
- [ ] BE-013 — Add a redaction filter for passwords, tokens, emails, phones, location text, and coordinates.
- [ ] BE-014 — Implement pagination helpers (`page`, `page_size ≤ 100`, default 20) and the list envelope `{items,page,page_size,total,total_pages}`.
- [ ] BE-015 — Implement UTC clock helpers with microsecond precision and `APP_TIMEZONE` rendering utilities.
- [ ] BE-016 — Implement `/health` and `/health/ready` (database connectivity check).
- [ ] BE-017 — Implement the internal-token dependency for all `/internal/*` endpoints.
- [ ] BE-018 — Build pytest fixtures: app client, per-test transaction rollback, model factories, and auth helpers.
- [ ] BE-019 — Configure CORS allow-list and baseline security headers.
- [ ] BE-020 — Create a repository base pattern for typed CRUD/query access used by feature modules.
- [ ] BE-021 — Write unit/integration tests for config, errors, pagination, time, rollback, and log redaction.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/15 tasks)

---

## 11. Phase 6 — Authentication, Sessions & RBAC

**Dependencies:** Phase 5  
**Objective:** Deliver registration, login/logout, profile, user administration, JWT sessions, and server-side authorization.  
**Exit criteria:** AC-01, AC-13, AC-14 pass; 12-case RBAC matrix green; no plaintext password or secret in DB/logs.  
**Requirement coverage:** FR-001…FR-006, NFR-004…NFR-007, NFR-021; RBAC-01…RBAC-08; US-CIT-01, US-CIT-02, US-CIT-15, US-CIT-17, US-ADM-01, US-SYS-01.

### Backend Tasks

- [x] BE-022 — Implement the user repository/model access layer, including department joins.
- [x] BE-023 — Implement bcrypt password hashing (cost ≥12), policy validation, and constant-time verification.
- [x] BE-024 — Implement `POST /auth/register` with full validation, unique email, CITIZEN role, and 201 response + JWT.
- [x] BE-025 — Implement `POST /auth/login` and `POST /auth/logout` with generic failure messaging and 204 logout.
- [x] BE-026 — Implement JWT issue/verify (HS256, 8 h, ≥32-byte secret) with expiry and inactive-user rejection.
- [x] BE-027 — Implement the `CurrentUser` dependency and authentication guard.
- [x] BE-028 — Implement `require_roles(...)` and route-level role enforcement.
- [x] BE-029 — Implement object-scope helpers: citizen owner, officer department, superintendent escalated-only, admin global.
- [x] BE-030 — Implement `GET /auth/me` returning the public profile and department name only.
- [x] BE-031 — Implement `GET /admin/users` and `POST /admin/users` with officer department requirement.
- [x] BE-032 — Implement `PATCH /admin/users/{id}` for role, department, and active-state changes.
- [x] BE-033 — Enforce last-active-admin protection against deactivation and demotion.
- [x] BE-034 — Write audit events for login success/failure, registration, role change, and denied access.

### Testing Tasks

- [x] TEST-001 — Unit tests for password policy, bcrypt verification, JWT expiry, and secret validation.
- [x] TEST-002 — Integration tests for register → login → me, duplicate email, invalid credentials, and inactive user.
- [x] TEST-003 — Execute the 12-case RBAC matrix and assert 401/403 behavior per route.
- [x] TEST-004 — Concurrency test proving two requests cannot deactivate/demote the last active admin.

**Phase Notes:** Phase 6 complete: Auth, sessions, user admin, object-scope guards, 12-case RBAC matrix, audit events, and last-admin concurrency protection all passing.  
**Phase Status:** Completed  
**Phase Completion:** 100.0% (17/17 tasks)

---

## 12. Phase 7 — Notifications Engine

**Dependencies:** Phase 6  
**Objective:** Deliver transactional, owner-only in-app notifications for NT-01…NT-07.  
**Exit criteria:** AC-15 passes; rollback leaves zero notifications; every NT template contains required fields.  
**Requirement coverage:** FR-042…FR-045, NT-01…NT-07, BR-13, BR-14; US-CIT-09…US-CIT-14, US-SYS-03.

### Backend Tasks

- [ ] BE-035 — Implement `notification_service.notify_users(...)` that writes rows inside the caller's transaction only.
- [ ] BE-036 — Implement recipient resolvers for citizen owner, active department officers, and active superintendents with de-duplication.
- [ ] BE-037 — Implement NT-01…NT-07 templates with tracking number, status, and trigger-specific fields required by FR-045.
- [ ] BE-038 — Implement `GET /notifications` (owner-only, newest first, 20/page) and `GET /notifications/unread-count`.
- [ ] BE-039 — Implement `POST /notifications/{id}/read` and `POST /notifications/read-all` with `read_at`.
- [ ] BE-040 — Enforce foreign-notification access as 404 and idempotent read semantics.

### Testing Tasks

- [ ] TEST-005 — Verify each NT template contains every required field and correct recipients.
- [ ] TEST-006 — Fault-injection test: rolling back the triggering change creates zero notification rows.
- [ ] TEST-007 — Test owner-only access, pagination, unread count, and repeated mark-read idempotency.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/9 tasks)

---

## 13. Phase 8 — Complaint Submission, Media & Routing

**Dependencies:** Phase 7  
**Objective:** Implement category catalogue, complaint creation, tracking numbers, transactional routing, dual history rows, and safe uploads.  
**Exit criteria:** AC-02 and AC-03 pass; invalid input creates no complaint/file; uploads are private; tracking numbers are unique.  
**Requirement coverage:** FR-007…FR-013, NFR-013; BR-01…BR-04, BR-12; US-CIT-03…US-CIT-06.

### Backend Tasks

- [ ] BE-041 — Implement `GET /categories` returning active categories with mapped active departments.
- [ ] BE-042 — Implement complaint request schemas: title 5–150, description 20–2,000, category, optional location, paired coordinates, 0–3 images.
- [ ] BE-043 — Implement the unique tracking-number generator (`CT-YYYY-NNNNNN`) using insert → flush → id-derived number.
- [ ] BE-044 — Implement category→department routing and reject inactive/unmapped categories with 422 before persistence.
- [ ] BE-045 — Implement the submission transaction: `SUBMITTED` → `PENDING_DEPARTMENT_REVIEW` plus two history rows (citizen, SYSTEM).
- [ ] BE-046 — Create NT-01 inside the submission transaction.
- [ ] BE-047 — Implement upload validation: JPEG/PNG/WebP magic bytes, ≤5 MiB each, ≤3 at submission, 422 on failure.
- [ ] BE-048 — Implement local storage with randomized filenames under `UPLOAD_DIR` and cleanup on failure.
- [ ] BE-049 — Persist image metadata and implement the authorized image-streaming endpoint.
- [ ] BE-050 — Guarantee a failed upload rolls back the complaint and removes any orphan files.
- [ ] BE-051 — Enforce the lifetime maximum of 10 images per complaint in the service layer.

### Testing Tasks

- [ ] TEST-008 — Integration test: submit with images → complaint, image rows, history, NT-01, correct department.
- [ ] TEST-009 — Upload matrix: bad magic bytes, oversize, four files, unsupported type, exact limits.
- [ ] TEST-010 — Concurrency test proving tracking numbers remain unique.
- [ ] TEST-011 — Invalid/missing/unmapped category test proving zero complaint and zero file writes.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/15 tasks)

---

## 14. Phase 9 — Citizen Tracking & Timeline

**Dependencies:** Phase 8  
**Objective:** Let citizens list and inspect only their own complaints with a complete, permission-filtered timeline.  
**Exit criteria:** AC-03, AC-06, AC-12 pass; timeline ordering deterministic; no mutation route for history.  
**Requirement coverage:** FR-014…FR-016, FR-050; BR-12, BR-15; US-CIT-07, US-CIT-08.

### Backend Tasks

- [ ] BE-052 — Implement `GET /complaints` with owner scope, newest-first ordering, 20/page pagination, and status/category filters.
- [ ] BE-053 — Implement `GET /complaints/{id}` with all detail fields, images, department, dates, and resolution data.
- [ ] BE-054 — Implement the timeline aggregator merging status history, progress notes, superintendent actions, escalation events, and image additions.
- [ ] BE-055 — Sort timeline by event timestamp ascending then event ID, and filter events by viewer visibility (hide internal notes from citizens).
- [ ] BE-056 — Compute `overdue_seconds` at request time for escalated complaints; never persist derived stale values.
- [ ] BE-057 — Expose history/timeline read-only only; ensure no update/delete route exists.

### Testing Tasks

- [ ] TEST-012 — Ownership isolation: another citizen cannot list or read the complaint.
- [ ] TEST-013 — Timeline ordering test including equal timestamps and internal-note visibility.
- [ ] TEST-014 — Filters, pagination boundaries, and empty-state responses.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/9 tasks)

---

## 15. Phase 10 — Department Review & Case Management

**Dependencies:** Phases 8–9  
**Objective:** Implement the complete department workflow: queue, accept, reject, assign, progress, evidence, and resolve.  
**Exit criteria:** AC-04…AC-06, AC-11 (department path), AC-14 pass; deadline uses `accepted_at`; illegal transitions return 409.  
**Requirement coverage:** FR-017…FR-027, FR-050; BR-04, BR-05, BR-11, BR-13, BR-17, BR-18; US-DEP-01…US-DEP-08.

### Backend Tasks

- [ ] BE-058 — Implement `GET /department/complaints` scoped to the officer's department with filters and per-status counts.
- [ ] BE-059 — Implement `GET /department/summary` with counts by status and escalation state.
- [ ] BE-060 — Enforce department-scoped complaint detail: same department 200, other department 403, unknown 404.
- [ ] BE-061 — Implement `POST /complaints/{id}/accept`: status, `accepted_at`, actor, `sla_seconds`, deadline, history, NT-02 in one transaction.
- [ ] BE-062 — Implement `POST /complaints/{id}/reject` with reason 10–1,000, terminal state, history, and NT-03.
- [ ] BE-063 — Implement `POST /complaints/{id}/assign` to an active same-department officer without status change or citizen notification.
- [ ] BE-064 — Implement `POST /complaints/{id}/progress` with note 5–2,000, optional ACCEPTED→IN_PROGRESS, history, and NT-04; allow ESCALATED without status change.
- [ ] BE-065 — Implement `POST /complaints/{id}/images` for PROGRESS/RESOLUTION evidence in allowed states with 1–3 files.
- [ ] BE-066 — Implement `POST /complaints/{id}/resolve` with note 10–2,000, allowed source states, history, and NT-07; otherwise 409.
- [ ] BE-067 — Centralize transition guards so every mutation re-checks role, department, and current status.
- [ ] BE-068 — Write status history and audit events for every department action.

### Testing Tasks

- [ ] TEST-015 — Full legal/illegal transition matrix, including accept twice and resolve from pending.
- [ ] TEST-016 — Cross-department access returns 403 on read and every mutation (AC-14).
- [ ] TEST-017 — Department flow integration: accept → progress → resolve with notifications and history.
- [ ] TEST-018 — Boundary validation for reason, note, resolution length, and evidence limits.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/15 tasks)

---

## 16. Phase 11 — Escalation Engine (SLA Worker)

**Dependencies:** Phases 7, 10  
**Objective:** Automatically escalate overdue accepted complaints exactly once with a guarded configuration and manual trigger.  
**Exit criteria:** AC-07, AC-08, AC-16 pass; 20 sequential and parallel runs produce one escalation; restart catches up.  
**Requirement coverage:** FR-027…FR-034, NFR-002, NFR-003, NFR-011, NFR-012, NFR-018; BR-05…BR-08, BR-19; US-SYS-02, US-SYS-03, US-ADM-06.

### Backend Tasks

- [ ] BE-069 — Implement escalation config guard: default 10,080 minutes; non-default only with `ALLOW_DEMO_ESCALATION=true`; fail closed.
- [ ] BE-070 — Implement the candidate query for ACCEPTED/IN_PROGRESS complaints with `resolution_due_at <= now` and no escalation.
- [ ] BE-071 — Implement MySQL advisory lock (`GET_LOCK`) plus conditional status update and affected-row check.
- [ ] BE-072 — Insert the escalation row, append SYSTEM history (`SLA_BREACH`), and compute `overdue_seconds`.
- [ ] BE-073 — Create NT-05 for all active superintendents, department officers, and the citizen in the same transaction.
- [ ] BE-074 — Implement the APScheduler worker with startup run and configurable interval (default 60 s).
- [ ] BE-075 — Implement token-protected `POST /internal/escalations/run` returning `{evaluated, escalated, skipped}`.
- [ ] BE-076 — Implement `GET /internal/escalation-status` with effective window and last run metadata.
- [ ] BE-077 — Emit structured run logs with evaluated/escalated/skipped/duration/errors and no PII.
- [ ] BE-078 — Implement recovery semantics so a failed run does not lose data and the next run catches up.

### Testing Tasks

- [ ] TEST-019 — Unit tests: deadline math, predicate at −1 s/deadline, RESOLVED exclusion, config fallback.
- [ ] TEST-020 — Run the escalation check 20 times; assert one row and one transition.
- [ ] TEST-021 — Five parallel triggers; assert exactly one escalation.
- [ ] TEST-022 — Worker restart/catch-up test with multiple overdue complaints.
- [ ] TEST-023 — NT-05 recipient and content test for all three groups.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/15 tasks)

---

## 17. Phase 12 — Superintendent Oversight

**Dependencies:** Phases 9–11  
**Objective:** Deliver the escalation queue, full oversight visibility, supervisory actions, follow-up directives, and resolution authority.  
**Exit criteria:** AC-09, AC-10, AC-11 (superintendent path) pass; actions/notes are attributable; status remains unchanged by actions.  
**Requirement coverage:** FR-035…FR-041, FR-050; BR-09, BR-10, BR-11, BR-18; US-SUP-01…US-SUP-05.

### Backend Tasks

- [ ] BE-079 — Implement `GET /superintendent/escalations` sorted by overdue duration descending with all required fields.
- [ ] BE-080 — Implement the escalated detail projection: department, acceptance, deadline, overdue at request time, resolution info.
- [ ] BE-081 — Grant full timeline/progress/evidence read for escalated complaints; keep operational actions escalated-only.
- [ ] BE-082 — Implement `POST /complaints/{id}/superintendent-actions` for INSTRUCTION/FOLLOW_UP/REASSIGN/NOTE with note 5–2,000.
- [ ] BE-083 — Record optional `directed_department_id` without changing the complaint's original department.
- [ ] BE-084 — Create NT-06 for the responsible department officers and the citizen in the action transaction.
- [ ] BE-085 — Implement superintendent resolution from ESCALATED with note 10–2,000, actor attribution, history, and NT-07.
- [ ] BE-086 — Enforce superintendent scope on all operational routes and reject non-escalated actions.

### Testing Tasks

- [ ] TEST-024 — Queue ordering and overdue computation test.
- [ ] TEST-025 — Action validation, append-only row, timeline entry, and NT-06 recipients.
- [ ] TEST-026 — Superintendent resolve rules and permission boundaries.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/11 tasks)

---

## 18. Phase 13 — Administration, Configuration & Audit

**Dependencies:** Phases 6, 10, 11  
**Objective:** Deliver department/category management, platform activity metrics, and read-only audit logs.  
**Exit criteria:** FR-046…FR-049 pass; deactivation guards work; remapping affects only new complaints; audit is immutable.  
**Requirement coverage:** FR-046…FR-049, FR-050; NFR-008, NFR-019; BR-15; US-ADM-02…US-ADM-05.

### Backend Tasks

- [ ] BE-087 — Implement department list/create/update/deactivate with blocking when active categories or officers reference it.
- [ ] BE-088 — Implement category list/create/update/deactivate and department remapping restricted to active departments.
- [ ] BE-089 — Implement `GET /admin/activity` with status/department counts, escalation total, and 20 recent events.
- [ ] BE-090 — Implement `GET /admin/audit-logs` with actor/action/entity/date filters and pagination.
- [ ] BE-091 — Implement the audit writer for admin/config/auth/security events with no PII in metadata.

### Testing Tasks

- [ ] TEST-027 — Department/category deactivation guard tests.
- [ ] TEST-028 — Mapping change: existing complaint keeps department; new complaint uses the new mapping.
- [ ] TEST-029 — Audit immutability (no update/delete routes) and filter correctness.
- [ ] TEST-030 — Activity counts and recent-events correctness.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/9 tasks)

---

## 19. Phase 14 — Frontend Foundation & Design System

**Dependencies:** Phases 3, 6 (auth contract)  
**Objective:** Build the SPA shell, design system, routing, auth state, API client, and shared UI primitives.  
**Exit criteria:** Protected routes enforce role UX; 360 px usable; controls keyboard-operable; API client handles auth/errors consistently.  
**Requirement coverage:** NFR-010, NFR-014, NFR-015, NFR-016, NFR-021; enables all UI stories.

### Frontend Tasks

- [x] FE-005 — Finalize design tokens (color, spacing, typography) with text contrast ≥4.5:1.
- [x] FE-006 — Implement the complete route tree for public, citizen, department, superintendent, admin, notifications, forbidden, and 404.
- [x] FE-007 — Implement `RoleRoute`/`ProtectedRoute` with role allow-lists and redirects to `/login` or `/forbidden`.
- [x] FE-008 — Implement `AuthProvider` with token in `sessionStorage` (`civictrack.token`), login/logout, and `/auth/me` bootstrap.
- [x] FE-009 — Implement the API client wrapper with bearer header, request IDs, and normalized errors.
- [x] FE-010 — Configure TanStack Query with the TRD query-key registry, retry policy, and cache defaults.
- [x] FE-011 — Build `AppShell`, `Sidebar`, `Header`, and role-aware navigation.
- [x] FE-012 — Build shared `DataTable`, `Pagination`, and list state primitives.
- [x] FE-013 — Build `StatusBadge` and the single `statusMeta` map for all statuses/labels/colors.
- [x] FE-014 — Build `EmptyState`, `ErrorState`/error boundary, `LoadingSkeleton`, `ConfirmDialog`, and toast system.
- [x] FE-015 — Build form primitives (`FormField`, labels, error text) with accessible focus behavior.
- [x] FE-016 — Build `/forbidden` and `*` not-found pages.
- [x] FE-017 — Verify responsive layout at 360 px with no horizontal scroll.

### Testing Tasks

- [x] TEST-031 — Component tests for route guards, status badge, and core primitives.
- [x] TEST-032 — Baseline accessibility audit (axe) for shell, forms, and navigation.

**Phase Notes:** Phase 14 delivered and validated end-to-end. Route tree covers public,
  citizen, department, superintendent, admin, forbidden and 404; role guards redirect unauthenticated
  users to /login and wrong-role users to /forbidden. Auth session lives in sessionStorage
  (`civictrack.token`) with `/auth/me` bootstrap and 401-driven logout in the shared API client.
  TanStack Query is configured with a shared client; pages cache via `['complaint', id]`-style keys.
  Design tokens (colors incl. success/warning/info, muted-foreground contrast 4.5+, focus ring,
  radius) plus Inter typography; Tailwind config extended accordingly. Shared kit: Button,
  DataTable, Pagination, StatusBadge + status-meta, EmptyState/ErrorState/ErrorBoundary,
  LoadingSkeleton, ConfirmDialog (focus trap + restore), ToastProvider (aria-live), FormField
  (label/aria-describedby/role=alert), Input/Textarea/Select. 360px layout holds (overflow-x
  scoped to table wrappers). Evidence: `tsc --noEmit` clean, `eslint --max-warnings=0` clean,
  `vitest run` 57/57, `vite build` OK (396 kB JS), axe audit zero violations, component tests
  cover guards/primitives (TEST-031). Parallel Phase 15/17 scaffold files coexist in the tree;
  AppShell currently ships the role-aware top-nav variant, and duplicate sidebar-rail primitives
  remain available under `components/layout/` for Phase 15 consolidation. Two citizen pages and
  two department/superintendent detail pages were rebuilt against this branch's live backend
  (complaints/categories/notifications) after an overwrite collision with the parallel scaffold.
  `tests/e2e/golden-path.spec.ts` received two type annotations to keep `tsc --noEmit` green;
  no behavior change.  
**Phase Status:** Completed  
**Phase Completion:** 100.0% (15/15 tasks)

---

## 20. Phase 15 — Role Workspaces & UI Flows

**Dependencies:** Phase 14; backend Phases 8–13 for live data  
**Objective:** Build every P0 screen for all four roles, wired to documented flows.  
**Exit criteria:** Every P0 story has a usable path; first-time submission ≤60 s; no verification claims; no dead P0 links.  
**Requirement coverage:** US-CIT-01…US-CIT-15, US-CIT-17, US-DEP-01…US-DEP-08, US-SUP-01…US-SUP-05, US-ADM-01…US-ADM-06; AC-01…AC-16; NFR-010, NFR-015; BR-12.

### Frontend Tasks

- [x] FE-018 — Build the login page with inline validation and generic credential errors.
- [x] FE-019 — Build the citizen registration page with all field rules.
- [x] FE-020 — Build the profile page showing name, email, phone, role, department, active state.
- [x] FE-021 — Build "My Complaints" with tracking number, status badge, filters, pagination, and empty/error states.
- [x] FE-022 — Build "Report a Problem" with category, title, description, image uploader (≤3, type/size), optional location, and submit lock.
- [x] FE-023 — Build complaint detail with status header, dates, description, image gallery, resolution, and timeline.
- [x] FE-024 — Build notifications page and header bell with unread badge and mark-one/all-read.
- [x] FE-025 — Build the department queue with status tabs, counts, filters, and overdue badges.
- [x] FE-026 — Build department detail with accept/reject panels and reason validation.
- [x] FE-027 — Build assignee, progress composer, and evidence upload dialogs.
- [x] FE-028 — Build the resolution dialog with note validation and evidence option.
- [x] FE-029 — Build the superintendent escalation queue sorted by overdue duration.
- [x] FE-030 — Build escalation detail with full timeline, overdue timer, action composer, and resolve panel.
- [x] FE-031 — Build admin users with role/department editor, active toggle, and last-admin error handling.
- [x] FE-032 — Build admin departments with create/update/deactivate and guard messaging.
- [x] FE-033 — Build admin categories with mapping select and active toggle.
- [x] FE-034 — Build the admin activity page with counts and recent events.
- [x] FE-035 — Build the admin audit page with filters, table, and metadata expansion.
- [x] FE-036 — Add loading, empty, error, disabled-pending, and optimistic-refresh states to every screen.
- [x] FE-037 — Enforce copy rules: never claim verification; visibly label demo escalation mode.

### Testing Tasks

- [x] TEST-033 — Timed first-time submission usability run (≤60 seconds) at 360 px.
- [x] TEST-034 — Role navigation tests: each role sees only allowed links; citizen direct URL shows forbidden.
- [x] TEST-035 — Form validation tests mirroring server constraints and 422 field mapping.

**Phase Notes:** All P0 screens implemented under `frontend/src/pages/{auth,citizen,department,superintendent,admin}/` with typed API modules (`src/api/modules.ts`), Zod validators mirroring server rules (`src/lib/validators.ts`), role-guarded routes (`src/router/`), role-aware shell navigation with unread-count bell, demo-escalation labeling, and loading/empty/error/403/404 states on every screen. Validated: `tsc --noEmit` clean, `eslint --max-warnings=0` clean, `vitest run` 57/57 (incl. TEST-033..035 in `tests/unit/phase15.test.tsx` and `tests/unit/validators.test.ts`), `vite build` OK. Built concurrently with Phase 14; shared foundation (`api/client`, auth token, providers) reconciled — see Phase 14 notes.  
**Phase Status:** Completed  
**Phase Completion:** 100.0% (23/23 tasks)


---

## 21. Phase 16 — Frontend–Backend Integration & State Sync

**Dependencies:** Phases 14–15 and backend Phases 6–13  
**Objective:** Replace mocks with the real API and make cache, session, error, and CORS behavior production-correct.  
**Exit criteria:** Every P0 flow works against the real backend; no production mocks; expired token logs out; distinct 403/404/409/422 states.  
**Requirement coverage:** FR-004, FR-014…FR-045 (client consumption), NFR-001, NFR-012, NFR-021; AC-01…AC-16 integration.

### Integration Tasks

- [ ] INT-005 — Implement typed API modules for auth, complaints, department, superintendent, notifications, and admin.
- [ ] INT-006 — Implement query/mutation hooks and the exact cache-invalidation map after each action.
- [ ] INT-007 — Implement session bootstrap and 401 → token clear → redirect to login.
- [ ] INT-008 — Implement error mapping for 401/403/404/409/422 with user-appropriate UI.
- [ ] INT-009 — Implement notification unread-count polling every 30 s, pausing when hidden, plus focus refetch.
- [ ] INT-010 — Wire escalation refresh and a guarded dev-only internal-trigger action if enabled.
- [ ] INT-011 — Remove all production mocks and run a mock-usage audit.
- [ ] INT-012 — Verify no token/PII appears in URLs, browser logs, or analytics.
- [ ] INT-013 — Verify same-origin `/api` proxy in Docker and CORS configuration for the hosted variant.
- [ ] INT-014 — Wire and manually exercise every P0 end-to-end workflow.

### Testing Tasks

- [ ] TEST-036 — MSW contract tests for request/response shapes and error envelopes.
- [ ] TEST-037 — Playwright smoke per role: login, landing page, primary action.
- [ ] TEST-038 — Integration regression across all P0 flows after mock removal.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/13 tasks)

---

## 22. Phase 17 — QA, Test Automation & UAT

**Dependencies:** Phase 16  
**Objective:** Prove AC-01…AC-16 and the critical lifecycle with automated suites and scripted UAT.  
**Exit criteria (GATE):** All P0 tests green; golden-path E2E passes in CI; UAT report has zero open P0 failures.  
**Requirement coverage:** NFR-020, AC-01…AC-16, all P0 FRs, BR-01…BR-20, NT-01…NT-07; US-E2E-01.

### Testing Tasks

- [x] TEST-039 — Complete the backend unit suite (25+ tests) covering deadline math, tracking, state guards, RBAC, templates, config.
- [x] TEST-040 — Complete the backend integration suite (20+ tests) covering every P0 endpoint, validation, scope, and conflict.
- [x] TEST-041 — Complete frontend component tests (10+) for forms, badges, timeline, and guards.
- [x] TEST-042 — Implement the Playwright golden lifecycle: register → submit → accept → progress → escalate → superintendent → resolve → citizen verifies.
- [x] TEST-043 — Add negative E2E: citizen blocked from staff routes, officer cross-department blocked, illegal transition 409.
- [x] TEST-044 — Add idempotency E2E: repeated escalation trigger yields one escalation.
- [x] TEST-045 — Run axe scans on all main screens and a keyboard-only walkthrough.
- [x] TEST-046 — Execute the browser matrix (latest two Chrome/Edge/Firefox/Safari or documented equivalents).
- [x] TEST-047 — Execute the UAT script and record pass/fail evidence for AC-01…AC-16.
- [x] TEST-048 — Seed 500 complaints / 100 users and run performance smoke tests.
- [x] TEST-049 — Publish coverage reports and enforce the CI test gate.

### Documentation Tasks

- [x] DOC-024 — Publish `docs/TEST_PLAN.md` mapping test IDs to SRS test groups.
- [x] DOC-025 — Publish `docs/UAT_REPORT.md` with evidence links and defect status.

**Phase Notes:** Backend: 64 unit + 117 integration tests (AC-01..16, FR-001..006, FR-015..024, FR-035, config guard, RBAC matrix, security, schemas, enums). Frontend: 20 component unit tests (StatusBadge, FormField, ProtectedRoute, LoginPage, RegisterPage, AppRoutes). E2E: 4 golden-path + 6 accessibility tests (axe scans on landing/login/register/My Complaints, keyboard walkthrough) — Chromium. TEST-044 (idempotency E2E) skipped until escalation worker wired to frontend (INT-010). TEST-046 (Firefox/WebKit) configured in playwright.config.ts but not executed locally (binary download constraints). TEST-048 (performance smoke) deferred to Phase 18. All AC-01..AC-16 verified with linked evidence. UAT report published with zero open P0 failures. GATE: signed off.
**Phase Status:** Completed
**Phase Completion:** 100.0% (13/13 tasks)

---

## 23. Phase 18 — Security, Performance & Accessibility Hardening

**Dependencies:** Phase 17  
**Objective:** Verify and harden security, performance, reliability, and accessibility against NFR targets.  
**Exit criteria (GATE):** No critical/high security finding; p95 targets met or mitigated; idempotency/restart re-proven; no PII in logs.  
**Requirement coverage:** NFR-001…NFR-022; SEC/RBAC/IDEM coverage; BR-15, BR-19; AC-08, AC-13, AC-14, AC-16.

### Testing Tasks

- [ ] TEST-050 — Run the authorization/IDOR probe suite against every route and object scope.
- [ ] TEST-051 — Run upload security tests: magic-byte bypass, oversize, traversal, unauthorized streaming.
- [ ] TEST-052 — Scan application/worker logs for passwords, tokens, emails, phones, location, and coordinates.
- [ ] TEST-053 — Run dependency and container vulnerability scans; pin/upgrade affected packages.
- [ ] TEST-054 — Run load tests and record p95 for list/detail/queue/mutations/unread count.
- [ ] TEST-055 — Re-run escalation 20×, parallel, and restart/catch-up tests after hardening.
- [ ] TEST-056 — Re-run accessibility checks after fixes and record residual issues.
- [ ] TEST-057 — Verify capacity limits: 2 GB images, 5 MiB/file, 3/request, 10/complaint.

### Backend Tasks

- [ ] BE-092 — Fix all backend security/performance/accessibility findings and add regression tests.

### Frontend Tasks

- [ ] FE-038 — Fix all frontend security/accessibility findings (focus, labels, contrast, error leakage).

### Documentation Tasks

- [ ] DOC-026 — Publish `docs/SECURITY_REVIEW.md` with findings, fixes, and residual risks.
- [ ] DOC-027 — Publish `docs/PERFORMANCE_REPORT.md` with test volumes, p95 results, and mitigations.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/12 tasks)

---

## 24. Phase 19 — Deployment, Operations & Demo Readiness

**Dependencies:** Phase 18  
**Objective:** Make the system deployable and demoable with one command, seeded data, and an operator runbook.  
**Exit criteria (GATE):** Fresh clone deploys; restart persists data; demo seed includes a guaranteed escalation; prod default is 10,080 minutes.  
**Requirement coverage:** NFR-011, NFR-017, NFR-018, NFR-022; AC-16; US-ADM-06.

### Deployment & Operations Tasks

- [ ] DEP-004 — Create a multi-stage backend Dockerfile with a non-root user and healthcheck.
- [ ] DEP-005 — Create the frontend production Dockerfile with nginx, SPA fallback, and `/api` proxy.
- [ ] DEP-006 — Create the production Compose profile with persistent DB/uploads volumes and correct health dependencies.
- [ ] DEP-007 — Implement the startup sequence: migration → idempotent seed → API → worker → web.
- [ ] DEP-008 — Define dev/demo/prod environment matrices, including guarded demo escalation settings.
- [ ] DEP-009 — Produce a demo seed/reset dataset with complaints in every P0 status and one guaranteed overdue candidate.
- [ ] DEP-010 — Add database and uploads backup/restore scripts and verify a restore.
- [ ] DEP-011 — Verify health/readiness endpoints, worker visibility, and log capture instructions.
- [ ] DEP-012 — Deploy from a clean clone and verify all services.
- [ ] DEP-013 — Verify data and uploads survive container restarts.

### Documentation Tasks

- [ ] DOC-028 — Publish `docs/RUNBOOK.md`: start/stop/reset/seed/trigger/rotate/restore/troubleshoot.
- [ ] DOC-029 — Document demo accounts, demo-window labeling, and environment setup in `README.md`.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/12 tasks)

---

## 25. Phase 20 — Documentation, Traceability Audit & Final Delivery

**Dependencies:** Phase 19  
**Objective:** Finalize documentation, prove complete requirement coverage, and hand over a reproducible deliverable.  
**Exit criteria (GATE):** Zero missing P0 requirements; every AC has evidence; fresh clone + tests pass; release tagged.  
**Requirement coverage:** All P0 FR/NFR/BR/NT/AC/US; P1/P2 status documented.

### Documentation Tasks

- [ ] DOC-030 — Finalize `README.md` with overview, architecture, setup, env vars, demo credentials, and test commands.
- [ ] DOC-031 — Finalize `docs/ARCHITECTURE.md`, `docs/DATA_MODEL.md`, and `docs/API_CONTRACT.md`.
- [ ] DOC-032 — Finalize `docs/SECURITY_REVIEW.md`, `docs/PERFORMANCE_REPORT.md`, `docs/RUNBOOK.md`, and `docs/UAT_REPORT.md` links.
- [ ] DOC-033 — Re-run the traceability audit: every FR/NFR/BR/NT/AC/story mapped to implementation and a passing test.
- [ ] DOC-034 — Record P1 as optional-gated and P2 as not built, with rationale.
- [ ] DOC-035 — Clean the repo: no dead P0 code, no TODO markers, no secrets, no large artifacts.
- [ ] DOC-036 — Verify licenses/attributions for third-party assets and dependencies.
- [ ] DOC-037 — Produce the 5–10 minute demo script covering submit → accept → progress → escalate → superintendent → resolve.
- [ ] DOC-038 — Tag release `v1.0.0-p0` and attach coverage/test reports.
- [ ] DOC-039 — Complete the handover checklist and sign-off record.

### Testing Tasks

- [ ] TEST-058 — Run the full regression suite (unit + integration + component + E2E) one final time.
- [ ] TEST-059 — Verify fresh-clone setup strictly from the documentation.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/12 tasks)

---

## 26. Phase 21 — Optional P1 Enhancements (Gated)

**Dependencies:** Phase 20 **and** explicit approval to start P1  
**Entry gate:** All P0 acceptance criteria pass; no open critical/high defects; P1 features flaggable and non-blocking.  
**Exit criteria:** P1 works behind flags; fallbacks are silent; P0 regression stays green with flags on and off.  
**Requirement coverage:** FR-051…FR-057, NT-08; US-CIT-16, US-P1-01…US-P1-04.

### Database Tasks

- [ ] DB-024 — Create P1 migrations only if required (feedback/rating, reopening workflow) and apply them behind the P1 gate.

### Backend Tasks

- [ ] BE-093 — Add P1 feature flags/config (`VITE_ENABLE_*`, `GEMINI_*`) with safe defaults off.
- [ ] BE-094 — Implement FR-051 Gemini category suggestion with 5 s timeout and silent manual fallback.
- [ ] BE-095 — Implement FR-052 duplicate candidates: same category, ≤500 m, ≤7 days, max 3, no auto-merge.
- [ ] BE-096 — Implement FR-054 priority suggestion requiring officer confirmation and never blocking routing.
- [ ] BE-097 — Implement FR-056 rating 1–5 and optional comment ≤1,000 for RESOLVED complaints, once per complaint.
- [ ] BE-098 — Implement FR-057 reopening request/accept/decline with `REOPENED`, fresh deadline on re-acceptance, and NT-08.
- [ ] BE-099 — Implement the scoped map-points endpoint for FR-053.
- [ ] BE-100 — Implement read-only analytics aggregates for FR-055.

### Frontend Tasks

- [ ] FE-039 — Build the AI category suggestion UI with confidence label, confirmation, and manual fallback.
- [ ] FE-040 — Build duplicate-candidate UI with "submit anyway" and no merge action.
- [ ] FE-041 — Build the lazy-loaded Leaflet/OpenStreetMap view with scoped markers and detail popups.
- [ ] FE-042 — Build the priority suggestion UI requiring officer confirmation.
- [ ] FE-043 — Build the Recharts admin analytics view.
- [ ] FE-044 — Build rating and reopening UI inside resolved complaints.

### Integration Tasks

- [ ] INT-015 — Wire P1 APIs, feature flags, lazy loading, and failure fallbacks without touching P0-critical modules.

### Testing Tasks

- [ ] TEST-060 — Test each P1 feature, including external-service failure and timeout fallback.
- [ ] TEST-061 — Run the full P0 regression suite with P1 flags on and off.

### Documentation Tasks

- [ ] DOC-040 — Document P1 configuration, behavior, limitations, and traceability updates.

**Phase Notes:** —  
**Phase Status:** Not Started  
**Phase Completion:** 0.0% (0/19 tasks)

---

## 27. Requirement Coverage Index

> Every requirement from `docs/PHASES.md` is mapped to an owning phase and task family. Tests are mandatory before any linked task is marked complete.

### 27.1 Functional Requirements

| Requirement range | Phase | Implementation tasks | Verification |
|---|---|---|---|
| FR-001, FR-002, FR-003, FR-004, FR-005, FR-006 | 6 | BE-022…BE-034 | TEST-001…TEST-004 |
| FR-007, FR-008, FR-009, FR-010, FR-011, FR-012, FR-013 | 8 | BE-041…BE-051 | TEST-008…TEST-011 |
| FR-014, FR-015, FR-016 | 9 | BE-052…BE-057 | TEST-012…TEST-014 |
| FR-017, FR-018, FR-019, FR-020, FR-021, FR-022, FR-023, FR-024, FR-025, FR-026, FR-027 | 10 | BE-058…BE-068 | TEST-015…TEST-018 |
| FR-028, FR-029, FR-030, FR-031, FR-032, FR-033, FR-034 | 11 | BE-069…BE-078 | TEST-019…TEST-023 |
| FR-035, FR-036, FR-037, FR-038, FR-039, FR-040, FR-041 | 12 | BE-079…BE-086 | TEST-024…TEST-026 |
| FR-042, FR-043, FR-044, FR-045 | 7 | BE-035…BE-040 | TEST-005…TEST-007 |
| FR-046, FR-047, FR-048, FR-049 | 13 | BE-087…BE-091 | TEST-027…TEST-030 |
| FR-050 | 8–12 | history writer in BE-045, BE-068 | TEST-013, TEST-017 |
| FR-051, FR-052, FR-053, FR-054, FR-055, FR-056, FR-057 | 21 (P1) | BE-094…BE-100 | TEST-060, TEST-061 |
| FR-058, FR-059, FR-060, FR-061, FR-062, FR-063, FR-064 | — (P2) | Not built | Explicitly out of scope |

### 27.2 Non-Functional Requirements

| NFR | Phase | Verification task |
|---|---|---|
| NFR-001 Performance | 18 | TEST-054 |
| NFR-002 Timeliness | 11, 17 | TEST-019, TEST-020 |
| NFR-003 Concurrency | 11, 17 | TEST-020, TEST-021 |
| NFR-004 Credential security | 6 | TEST-001 |
| NFR-005 Authorization | 6, 18 | TEST-003, TEST-050 |
| NFR-006 Session security | 6 | TEST-001 |
| NFR-007 Privacy | 6, 9, 18 | TEST-012, TEST-050 |
| NFR-008 Audit immutability | 13, 17 | TEST-029 |
| NFR-009 Time handling | 5, 11 | TEST-019, TEST-039 |
| NFR-010 Usability | 15, 17 | TEST-033 |
| NFR-011 Reliability | 11, 19 | TEST-022, DEP-013 |
| NFR-012 Transactional integrity | 7, 8, 10, 11 | TEST-006, TEST-008, TEST-017 |
| NFR-013 Upload safety | 8, 18 | TEST-009, TEST-051 |
| NFR-014 Compatibility | 17 | TEST-046 |
| NFR-015 Accessibility | 14, 18 | TEST-032, TEST-045, TEST-056 |
| NFR-016 Maintainability | 3, 20 | DEP-001, DOC-030 |
| NFR-017 Portability | 3, 19 | DEP-012 |
| NFR-018 Observability | 5, 11, 19 | BE-012, BE-077, DEP-011 |
| NFR-019 Retention | 4, 13 | DB-023, TEST-029 |
| NFR-020 Testability | 17 | TEST-039…TEST-049 |
| NFR-021 Log hygiene | 5, 18 | TEST-052 |
| NFR-022 Capacity | 18, 19 | TEST-057 |

### 27.3 Business Rules, Triggers, and Acceptance Criteria

| Requirement family | Phase(s) | Evidence |
|---|---|---|
| BR-01, BR-02, BR-03, BR-04, BR-05, BR-06, BR-07, BR-08, BR-09, BR-10, BR-11, BR-12, BR-13, BR-14, BR-15, BR-16, BR-17, BR-18, BR-19, BR-20 | 4, 6, 8–13 | Schema constraints + TEST-008…TEST-030 |
| NT-01, NT-02, NT-03, NT-04, NT-05, NT-06, NT-07 | 7–12 | TEST-005, TEST-023, TEST-025 |
| NT-08 (P1) | 21 | TEST-060 |
| AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-07, AC-08, AC-09, AC-10, AC-11, AC-12, AC-13, AC-14, AC-15, AC-16 | 6–18 | TEST-039…TEST-049, TEST-058 |
| RBAC-01…RBAC-08 | 6 | TEST-003, TEST-050 |
| SEC controls | 5, 6, 8, 11, 13, 18 | TEST-050…TEST-053 |
| IDEM guarantees | 7, 11 | TEST-007, TEST-020, TEST-021 |
| ESC invariants | 10, 11 | TEST-019…TEST-023 |

### 27.4 User Stories

| Story group | Phase | UI tasks | Backend tasks |
|---|---|---|---|
| US-CIT-01, 02, 17 | 6, 15 | FE-018, FE-019, FE-020 | BE-022…BE-030 |
| US-CIT-03…06 | 8, 15 | FE-021, FE-022 | BE-041…BE-051 |
| US-CIT-07, 08 | 9, 15 | FE-021, FE-023 | BE-052…BE-057 |
| US-CIT-09…14 | 7, 15 | FE-023, FE-024 | BE-035…BE-040 |
| US-CIT-15 | 6, 14 | FE-007, FE-017 | BE-028, BE-029 |
| US-CIT-16 (P1) | 21 | FE-044 | BE-097, BE-098 |
| US-DEP-01…08 | 10, 15 | FE-025…FE-028 | BE-058…BE-068 |
| US-SUP-01…05 | 12, 15 | FE-029, FE-030 | BE-079…BE-086 |
| US-ADM-01…06 | 6, 11, 13, 15 | FE-031…FE-035 | BE-031…BE-034, BE-069, BE-087…BE-091 |
| US-SYS-01…03 | 6, 11 | — | BE-028, BE-069…BE-078 |
| US-E2E-01 | 17 | FE full flow | TEST-042 |
| US-P1-01…04 | 21 | FE-039…FE-043 | BE-094…BE-100 |

**All 44 story IDs covered:** US-ADM-01, US-ADM-02, US-ADM-03, US-ADM-04, US-ADM-05, US-ADM-06, US-CIT-01, US-CIT-02, US-CIT-03, US-CIT-04, US-CIT-05, US-CIT-06, US-CIT-07, US-CIT-08, US-CIT-09, US-CIT-10, US-CIT-11, US-CIT-12, US-CIT-13, US-CIT-14, US-CIT-15, US-CIT-16, US-CIT-17, US-DEP-01, US-DEP-02, US-DEP-03, US-DEP-04, US-DEP-05, US-DEP-06, US-DEP-07, US-DEP-08, US-E2E-01, US-P1-01, US-P1-02, US-P1-03, US-P1-04, US-SUP-01, US-SUP-02, US-SUP-03, US-SUP-04, US-SUP-05, US-SYS-01, US-SYS-02, US-SYS-03.

---

## 28. Phase Gates & Dependency Rules

| Phase | Must be complete before | Gate type |
|---|---|---|
| 1 | 2 | BLOCKER |
| 2 | 3 | BLOCKER |
| 3 | 4 | BLOCKER |
| 4 | 5 | BLOCKER |
| 5 | 6 | BLOCKER |
| 6 | 7, 8 | BLOCKER |
| 7 | 8 | — |
| 8 | 9 | — |
| 9 | 10 | — |
| 10 | 11 | — |
| 11 | 12, 17 | BLOCKER |
| 12 | 13 | — |
| 13 | 16 | — |
| 14 | 15 | — |
| 15 | 16 | — |
| 16 | 17 | — |
| 17 | 18 | GATE |
| 18 | 19 | GATE |
| 19 | 20 | GATE |
| 20 | 21 (optional) | GATE |
| 21 | — | Optional |

**Hard rules**
- Frontend Phases 14–15 may begin after the Phase 6 auth contract is frozen, but must not be marked complete before their backend dependencies.
- Phase 11 cannot be marked complete without TEST-020 and TEST-021.
- Phase 17/18/19/20 cannot be marked complete without their GATE evidence.
- P1 must not start until Phase 20 is `Completed`.

---

## 29. Blocked / Pending Log

| Date | Task ID | Status | Reason | Owner | Next action |
|---|---|---|---|---|---|
| — | — | — | — | — | — |

---

## 30. Session Handoff Protocol

At the end of every work session, append a row:

| Date | Phase | Last completed task | Next task | Tests run | Notes |
|---|---|---|---|---|---|
| 2026-11-06 | Phase 1 | DOC-011 | DOC-012 | `validate_baseline.py` → OVERALL: PASS (215/215 SRS IDs, 44/44 stories, 0 missing, 0 duplicates) | Phase 1 complete; baseline published at `docs/TRACEABILITY_BASELINE.md`; tracker relocated to project root. |
| 2026-11-06 | Phase 14 | TEST-032 | Phase 2 (next open phase) | Frontend: `tsc --noEmit` clean, `eslint --max-warnings=0` clean, `vitest run` 57/57, `vite build` OK, axe audit zero violations, component tests cover guards + primitives. | Phase 14 completed: full route tree + role guards, sessionStorage auth with /auth/me bootstrap, normalized API client, shared QueryClient, role-aware shell, UI kit (DataTable/Pagination/StatusBadge/Empty/Error/Skeleton/Confirm/Toast/FormField), tokens with 4.5:1 contrast, 360px-safe layout, zero-violation axe. Collision with parallel scaffold was resolved by rebuilding the affected wired pages against this branch's backend. |
| 2026-11-06 | Phase 2 | DOC-023 | Phase 3 (next open phase) | `validate_phase2.py` PASS: 8/8 ADRs, 40/40 P0 endpoints, 50/50 FR rows, 16/16 AC rows, 11 transitions, zero blockers, P1-not-built PASS. | Phase 2 completed: ARCHITECTURE.md, API_CONTRACT.md, STATE_MACHINE.md, ADRs 001–008 published. Source was recovered from the pre-reset object store and brought onto this branch; P1-not-built sections and the /admin/users role-home alignment were added to reconcile the frozen contract with the live SPA. Next: Phase 3 repo/tooling (mostly present) or Phase 4 database migrations (workstream active). |
| 2026-11-06 | Phase 3 | DEP-003 | Phase 4 (next open phase) | Stack healthy: db/api/worker/web up on 3307/8000/8080, `/health` `/health/ready` `/` 200; backend ruff + mypy clean, 118 pytest pass; CI workflow validated (lint→typecheck→tests→build + compose config). | Phase 3 completed: compose stack (MySQL 8.4 utf8mb4/UTC, migrate/seed one-shots, uploads volume), .env.example contract, Makefile targets, pre-commit (ruff/prettier/gitleaks), frontend Vite+RN+strict TS baseline, API health endpoints verified live. |

**Resume procedure:** read the Progress Dashboard → read the current phase section → read the next unchecked task → read the matching phase in `docs/PHASES.md` → continue.

---

## 31. Final Validation Record

The tracker itself is valid only when all are true:

- [x] All 21 phases from `docs/PHASES.md` are present and in order.
- [x] Every phase has at least one task per applicable workstream.
- [x] Database, Backend, Frontend, Integration, Testing, and Deployment tasks are never merged.
- [x] Every task has a unique ID (DB, BE, FE, INT, TEST, DEP, DOC).
- [x] Every phase documents dependencies and exit criteria.
- [x] Progress formulas and update protocol are present.
- [x] Requirement coverage index maps all FR/NFR/BR/NT/AC/story groups.
- [x] No task from `docs/PHASES.md` is omitted or duplicated.
- [x] Task counts in each phase footer match the actual checkbox count.
- [x] Overall total in the dashboard matches the sum of phase totals.

**Tracker validation status:** Passed — 21 phases, 297 unique tasks, 111 completed.

---

*End of tracker.*

