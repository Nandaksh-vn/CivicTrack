# CivicTrack — Phase-Wise Execution Roadmap

> **Document type:** Executable delivery plan with full requirement traceability  
> **Source of truth:** [`PRD.md`](./PRD.md), [`SRS.md`](./SRS.md), [`TRD.md`](./TRD.md), [`USER_STORIES.md`](./USER_STORIES.md), and `CivicTrack_Problem_Statement_and_Objectives.pdf`  
> **Scope:** P0 (must ship), P1 (optional, gated), P2 (documented only, not built)  
> **Intended executor:** AI coding agent or small engineering team working sequentially  
> **Last updated:** 2026-11-06

---

## 1. How To Use This Document

1. Execute phases **in order**. A phase may start only when every dependency phase has passed its Definition of Done (DoD).
2. Work top-to-bottom inside a phase. Each task names its **files/folders**, **technologies**, and **verification** so an AI agent can execute it without guessing.
3. Never mark a requirement covered until its acceptance test exists and passes.
4. If a requirement conflicts with this plan, the requirement documents win. Update this plan, do not silently drop scope.
5. Only **P0** is required for delivery. **P1** starts only after Phase 20 sign-off and only if time remains. **P2** is explicitly out of scope.
6. Do not modify `PRD.md`, `SRS.md`, `TRD.md`, or `USER_STORIES.md`. This roadmap is additive.

### Status legend

| Symbol | Meaning |
|---|---|
| `P0` | Required for the graded/demo deliverable |
| `P1` | Optional enhancement, gated behind all P0 acceptance criteria |
| `P2` | Future scope, explicitly not implemented |
| `BLOCKER` | Later phases cannot start until complete |
| `GATE` | Requires explicit human sign-off |

---

## 2. Phase Map

| # | Phase | Primary requirement groups | Key output | Gate |
|---|---|---|---|---|
| 1 | Requirements Validation & Scope Baseline | All FR/NFR/BR/NT/AC/US | Validated scope + coverage baseline | BLOCKER |
| 2 | Architecture & Technical Design Baseline | TRD architecture, NFR-016/017 | ADR set + module map | BLOCKER |
| 3 | Repository, Tooling & Local Environment | NFR-016, NFR-017 | Runnable skeleton + CI | BLOCKER |
| 4 | Database Schema & Migrations | DB design, BR-01…BR-03, NFR-008/009/019 | 11 tables + Alembic baseline | BLOCKER |
| 5 | Backend Foundation & Cross-Cutting Core | NFR-009/012/018/021 | App factory, errors, logging, transactions | BLOCKER |
| 6 | Authentication, Sessions & RBAC | FR-001…FR-006, NFR-004…007, RBAC-01…08 | Auth + route guards | BLOCKER |
| 7 | Notifications Engine | FR-042…FR-045, NT-01…NT-07 | Transactional in-app notifications | — |
| 8 | Complaint Submission, Media & Routing | FR-007…FR-013, NFR-013 | Submission API + uploads | — |
| 9 | Citizen Tracking & Timeline | FR-014…FR-016, FR-050 | Citizen read APIs + timeline | — |
| 10 | Department Review & Case Management | FR-017…FR-026 | Department workflow APIs | — |
| 11 | Escalation Engine (SLA Worker) | FR-027…FR-034, NFR-002/003/011/012 | APScheduler worker + idempotency | BLOCKER |
| 12 | Superintendent Oversight | FR-035…FR-041 | Oversight queue + actions | — |
| 13 | Administration, Configuration & Audit | FR-046…FR-049, NFR-008/019 | Admin APIs + audit log | — |
| 14 | Frontend Foundation & Design System | NFR-010/014/015/016 | Vite app, routing, UI kit | — |
| 15 | Role Workspaces & UI Flows | All role stories, AC-01…AC-16 | Four complete workspaces | — |
| 16 | Frontend–Backend Integration & State Sync | FR-004, NFR-001/012 | Typed client, query cache, error states | — |
| 17 | QA, Test Automation & UAT | NFR-020, AC-01…AC-16 | Automated suite + UAT report | GATE |
| 18 | Security, Performance & Accessibility Hardening | NFR-001…022 | Hardening report + load results | GATE |
| 19 | Deployment, Operations & Demo Readiness | NFR-017/018/022 | One-command stack + runbook | GATE |
| 20 | Documentation, Traceability Audit & Final Delivery | All | Final docs + traceability proof | GATE |
| 21 | Optional P1 Enhancements | FR-051…FR-057, NT-08 | Gated enhancements | Optional |

---

## 3. Global Conventions

### 3.1 Canonical roles
`CITIZEN`, `DEPARTMENT_OFFICER`, `SUPERINTENDENT_OFFICER`, `PLATFORM_ADMIN`.

### 3.2 Canonical statuses
`SUBMITTED`, `PENDING_DEPARTMENT_REVIEW`, `ACCEPTED`, `IN_PROGRESS`, `REJECTED`, `ESCALATED`, `RESOLVED`, `REOPENED` (P1 only).

Legal transitions are exactly those in SRS §11.1. Any other transition returns HTTP 409 and mutates nothing (BR-16).

### 3.3 Non-negotiable invariants
- Tracking number format `^CT-[0-9]{4}-[0-9]{6}$` and unique (FR-009, BR-01).
- Deadline = `accepted_at + sla_seconds`, never `submitted_at` (FR-027, BR-05).
- Production SLA default = **10,080 minutes / 604,800 seconds** (FR-033, BR-06, BR-19).
- Demo override allowed only when `ALLOW_DEMO_ESCALATION=true`, and the UI must label it visibly (AC-16).
- At most **one** escalation per complaint for its lifetime (FR-029, BR-08).
- Notification rows are written in the **same transaction** as the triggering change (FR-042, NFR-012).
- Append-only: status history, escalations, officer actions, audit logs (NFR-008, BR-10, FR-050).
- All timestamps stored UTC with microsecond precision; rendered in `APP_TIMEZONE` (NFR-009).
- No PII/token/location in logs or URLs (NFR-021).

### 3.4 Definition of Done for every phase
A phase is done only when **all** are true:
1. Every listed task and subtask is complete.
2. Code is merged, formatted, linted, and type-checks clean (`ruff`, ESLint, `tsc --noEmit`, TypeScript `strict`).
3. Unit tests for new logic exist and pass; integration tests cover every new endpoint touched.
4. Every requirement claimed by the phase has a named, passing test.
5. No secret, credential, PII, or generated artifact is committed.
6. `.env.example` and docs are updated for any new variable or route.
7. The phase acceptance criteria below are demonstrated (manual script or automated test).
8. No regression in earlier phases' tests.

### 3.5 Assumed repository layout (created in Phase 3)

```text
CivicTrack/
├─ backend/
│  ├─ app/
│  │  ├─ main.py  config.py  db.py  security.py  dependencies.py
│  │  ├─ models/  schemas/  api/  services/  core/  workers/
│  │  └─ utils/
│  ├─ alembic/  alembic.ini
│  ├─ tests/{unit,integration,e2e}/
│  ├─ pyproject.toml  Dockerfile  .env.example
├─ frontend/
│  ├─ src/{app,components,features,hooks,lib,pages,routes,styles,types}/
│  ├─ tests/  package.json  vite.config.ts  tailwind.config.ts  Dockerfile
├─ docs/  docker-compose.yml  Makefile  README.md  .github/workflows/ci.yml
```

---

## 4. Detailed Phases

### Phase 1 — Requirements Validation & Scope Baseline

**Objective:** Prove the documented scope is complete, internally consistent, and testable before any code exists.

**Requirements covered:** All FR-001…FR-064, NFR-001…NFR-022, BR-01…BR-20, NT-01…NT-08, AC-01…AC-16, and all 44 user stories (baseline only; implementation follows in later phases).

**Detailed tasks**
1. Build a requirement inventory from SRS: 64 FRs (50 P0, 7 P1, 7 P2), 22 NFRs, 20 BRs, 8 NT triggers, 16 ACs.
2. Cross-check PRD scope against SRS: every PRD feature must map to at least one FR; every FR must trace to a story or an explicit system requirement.
3. Verify 44 user stories: 18 CIT, 8 DEP, 5 SUP, 6 ADM, 3 SYS, 1 E2E, 4 P1 minus overlaps = 44 IDs as listed in `USER_STORIES.md`.
4. Confirm canonical roles, statuses, transitions, SLA window, tracking number format, and pagination (20/page) are consistent across PRD/SRS/TRD.
5. Confirm P2 exclusions (FR-058…FR-064) are labeled future and never enter P0 acceptance.
6. Record open questions and resolve each as **accept as documented** or **blocked**; no silent assumptions.

**Subtasks**
- 1.1 Extract FR/NFR/BR/NT/AC tables into a checklist.
- 1.2 Extract story IDs and map each to FRs.
- 1.3 Verify non-functional targets are measurable (p95, 5 MiB, 8 h, 10,080 min, 360 px).
- 1.4 Verify every AC-01…AC-16 is testable with concrete steps.
- 1.5 Reconcile terminology (`complaint` vs `ticket`, `Superintendent`, `Platform Admin`).
- 1.6 Produce `docs/TRACEABILITY_BASELINE.md` (or appendix in this file) with the matrices.

**Files/folders:** `docs/PHASES.md`, `docs/TRACEABILITY_BASELINE.md`, read-only: all four source docs + PDF.

**Technologies/tools:** Markdown, ripgrep/Select-String, spreadsheet-style tables, `pdftotext` for the PDF.

**Dependencies:** None.

**Deliverables**
- Requirement inventory with priority (P0/P1/P2).
- Story→FR and FR→AC matrices.
- Confirmed glossary and invariant list.
- Open-question log with zero unresolved P0 items.

**Acceptance criteria**
- Every ID in SRS appears exactly once in the inventory.
- Every P0 FR maps to at least one story and one AC or test.
- No contradictions remain among role names, statuses, SLA, or tracking format.
- P2 scope is explicitly marked "not built".

**Testing:** Manual document audit; scripted ID diff (extract IDs from SRS vs inventory) must return zero missing and zero duplicates.

**Definition of Done:** Baseline approved; all later phases reference it; no code written yet.

---

### Phase 2 — Architecture & Technical Design Baseline

**Objective:** Freeze the modular architecture, data flow, API surface, and security model so backend and frontend can be built in parallel without rework.

**Requirements covered:** TRD architecture, NFR-016, NFR-017, NFR-018, NFR-020; enables FR-001…FR-050.

**Detailed tasks**
1. Confirm system context: React SPA → FastAPI → MySQL 8.4, plus APScheduler worker and shared file volume.
2. Define backend modules: `auth`, `users`, `departments`, `categories`, `complaints`, `timeline`, `notifications`, `escalations`, `superintendent`, `admin`, `internal`, `health`.
3. Define layering rule: `api` (HTTP only) → `services` (transactions/business rules) → `models` (persistence). No business logic in routers.
4. Freeze REST contract list for all P0 endpoints with methods, auth role, request/response schema, and error codes.
5. Define the state machine and transition guard table from SRS §11.1.
6. Define escalation algorithm: candidate query, `GET_LOCK`, conditional update, unique index, transaction boundary, metrics.
7. Define auth model: JWT bearer, 8 h expiry, `sessionStorage`, role + object-scope checks, 401 vs 403 vs 404 policy.
8. Define frontend architecture: route tree per role, TanStack Query keys, form validation with Zod, error boundary, protected route wrapper.
9. Produce ADRs for the decisions that carry risk (escalation idempotency, notification atomicity, upload storage, time handling).

**Subtasks**
- 2.1 Context + container diagram (Mermaid in TRD or `docs/ARCHITECTURE.md`).
- 2.2 Module/dependency map.
- 2.3 Endpoint catalogue with role matrix.
- 2.4 Status transition matrix.
- 2.5 Sequence diagrams: submit, accept, escalate, resolve, superintendent action.
- 2.6 Error taxonomy (`400/401/403/404/409/422/500`) and envelope.
- 2.7 ADR-001…ADR-008.

**Files/folders:** `docs/ARCHITECTURE.md`, `docs/ADRs/`, `docs/API_CONTRACT.md`, `docs/STATE_MACHINE.md`.

**Technologies/tools:** Mermaid, OpenAPI 3.1 sketch, Markdown.

**Dependencies:** Phase 1.

**Deliverables**
- Architecture document with diagrams.
- Frozen endpoint catalogue and role matrix.
- State machine + escalation algorithm spec.
- ADR set.

**Acceptance criteria**
- Every P0 FR has a named owning module and endpoint (or worker job).
- Every endpoint declares allowed roles and object-scope rule.
- Escalation spec states exactly how duplicates are prevented under concurrency.
- Frontend route tree covers all four roles.

**Testing:** Design review walkthrough of AC-01…AC-16 against the diagrams; each AC must be traceable to a module and endpoint.

**Definition of Done:** Architecture review passes; no unresolved design blocker for Phases 3–13.

---

### Phase 3 — Repository, Tooling & Local Environment

**Objective:** Create a clean, reproducible monorepo skeleton with one-command local startup and CI.

**Requirements covered:** NFR-016, NFR-017, NFR-020 (tooling), NFR-022 (capacity config).

**Detailed tasks**
1. Initialize git repo and folder layout from §3.5.
2. Backend: Python 3.12, FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2, PyMySQL/async driver as per TRD, `ruff`, `pytest`, `pytest-asyncio`, `httpx`.
3. Frontend: React 18.3, Vite, TypeScript `strict`, Tailwind, shadcn/ui, React Router, TanStack Query, react-hook-form, Zod, Vitest, Playwright.
4. `docker-compose.yml`: `db` (MySQL 8.4), `api`, `worker`, `web`; named volume for uploads; healthchecks.
5. `.env.example` with every variable: DB URL, JWT secret, `APP_TIMEZONE`, `ESCALATION_WINDOW_MINUTES`, `ALLOW_DEMO_ESCALATION`, `ESCALATION_INTERVAL_SECONDS`, `INTERNAL_API_TOKEN`, upload dir/limits, Gemini keys (P1, disabled by default).
6. Makefile / npm scripts: `dev`, `test`, `lint`, `typecheck`, `migrate`, `seed`, `compose-up`, `compose-down`.
7. CI workflow: install → lint → typecheck → unit tests → build. Fail on warnings-as-errors where configured.
8. Pre-commit hooks for formatting and secret scanning.

**Subtasks**
- 3.1 Repo init + `.gitignore` (env, uploads, node_modules, `__pycache__`, dist).
- 3.2 Backend dependency manifest and entrypoint.
- 3.3 Frontend scaffold and Tailwind/shadcn init.
- 3.4 Compose + healthchecks.
- 3.5 Env validation module that refuses unsafe production config.
- 3.6 CI pipeline.
- 3.7 README quickstart verified on a clean clone.

**Files/folders:** root config, `backend/`, `frontend/`, `.github/workflows/ci.yml`, `.env.example`, `docker-compose.yml`, `Makefile`, `README.md`.

**Technologies/tools:** Docker Compose, Node 20+, pnpm/npm, Python 3.12, uv/pip, GitHub Actions.

**Dependencies:** Phase 2.

**Deliverables**
- Runnable empty app (`GET /health` → 200; frontend renders shell).
- Compose stack starting db/api/worker/web.
- CI green on first push.

**Acceptance criteria**
- `docker compose up` starts all four services from a clean clone with only `.env` copied.
- `/health` returns 200; web loads at configured port.
- Lint, typecheck, and test commands succeed on the skeleton.
- No secret committed; `.env` ignored.

**Testing:** Fresh-clone smoke test; CI run; container healthcheck inspection.

**Definition of Done:** One-command startup confirmed; CI green; env contract documented.

---

### Phase 4 — Database Schema & Migrations

**Objective:** Implement the full relational schema, constraints, indexes, and seed data exactly as specified.

**Requirements covered:** DB design in SRS/TRD; BR-01, BR-02, BR-03, BR-05, BR-08, BR-10, BR-16; NFR-008, NFR-009, NFR-012, NFR-019, NFR-022.

**Detailed tasks**
1. Create 11 tables: `users`, `departments`, `complaint_categories`, `complaints`, `complaint_images`, `complaint_status_history`, `complaint_comments`, `notifications`, `escalations`, `officer_actions`, `audit_logs`.
2. Apply types: `BIGINT` PKs, `VARCHAR` limits from FRs, `ENUM` or constrained `VARCHAR` for roles/statuses, `DATETIME(6)` UTC, `DECIMAL(9,6)`/`DECIMAL(10,6)` coordinates, `JSON` only where specified.
3. Constraints: unique email (case-insensitive), unique tracking number, unique `escalations.complaint_id`, FKs with intended delete behavior (restrict/no cascade for audit entities), non-null department on complaint, check constraints for status/role values.
4. Indexes: complaints by citizen+created, department+status+created, status+resolution_due_at, tracking number; notifications by user+read+created; history by complaint+timestamp; audit by actor/action/entity/date.
5. Write Alembic baseline migration and a second migration only if needed; verify downgrade path on a scratch DB.
6. Seed script: 1 admin, 4 departments, 8 categories mapped to departments, sample officers/superintendent, optional demo citizens and complaints.
7. Implement model layer with SQLAlchemy 2 typed mappings and relationships; keep enums in one module shared with schemas.
8. Add DB-level append-only protection where feasible (no update/delete endpoints; optionally triggers or service-only access).

**Subtasks**
- 4.1 Users/departments/categories.
- 4.2 Complaints + images + history + comments.
- 4.3 Notifications.
- 4.4 Escalations + officer actions.
- 4.5 Audit logs.
- 4.6 Indexes and constraints review.
- 4.7 Seed + reset scripts.
- 4.8 Migration round-trip test.

**Files/folders:** `backend/app/models/`, `backend/alembic/versions/`, `backend/app/db.py`, `backend/scripts/seed.py`, `backend/tests/integration/test_schema.py`.

**Technologies/tools:** MySQL 8.4, SQLAlchemy 2, Alembic, Docker.

**Dependencies:** Phase 3.

**Deliverables**
- Complete schema and migrations.
- Seeded development database.
- ER diagram in `docs/DATA_MODEL.md`.

**Acceptance criteria**
- All 11 tables exist with required columns, FKs, and unique constraints.
- Duplicate tracking number and duplicate escalation insert both fail at the DB level.
- `alembic upgrade head` then `downgrade base` then `upgrade head` succeeds on a clean DB.
- Seed produces a usable demo dataset.

**Testing:** Schema integration tests, constraint violation tests, migration round-trip, seed idempotency.

**Definition of Done:** Migrations run cleanly in CI; constraints proven by failing tests; seed documented.

---

### Phase 5 — Backend Foundation & Cross-Cutting Core

**Objective:** Build the shared backend chassis (config, errors, logging, transactions, pagination, time, health) before feature endpoints.

**Requirements covered:** NFR-009, NFR-012, NFR-018, NFR-021, NFR-016; supports all FRs.

**Detailed tasks**
1. App factory with routers, middleware (request ID, CORS, trust boundaries), startup/shutdown hooks.
2. Settings via Pydantic `BaseSettings`: fail fast on missing JWT secret, invalid window, unsafe demo flag, missing DB URL.
3. DB session dependency with explicit transaction boundary; service functions own commit/rollback; routers never commit.
4. Standard error envelope and exception handlers: validation (422), auth (401), forbidden (403), not found (404), conflict (409), unhandled (500, no internals leaked).
5. Structured JSON logging with request ID, actor ID (not email), route, status, duration; redaction filter for passwords/tokens/email/phone/location.
6. Pagination helper (page, page_size ≤ 100, default 20) and consistent list envelope `{items, page, page_size, total}`.
7. UTC helpers (`utcnow()` with microseconds), `APP_TIMEZONE` rendering helper.
8. Health endpoints: `/health` (liveness) and `/health/ready` (DB check).
9. Internal-token dependency for `/internal/*`.
10. Base test fixtures: app client, DB transaction rollback per test, factory helpers.

**Subtasks**
- 5.1 Config + validation tests.
- 5.2 Logging + redaction tests.
- 5.3 Error handlers + envelope tests.
- 5.4 Transaction helper and rollback test.
- 5.5 Pagination helper tests.
- 5.6 Health checks.
- 5.7 Test factories.

**Files/folders:** `backend/app/main.py`, `config.py`, `db.py`, `core/errors.py`, `core/logging.py`, `core/pagination.py`, `core/time.py`, `dependencies.py`, `backend/tests/conftest.py`.

**Technologies/tools:** FastAPI, Pydantic v2, SQLAlchemy, pytest, structlog/logging.

**Dependencies:** Phase 4.

**Deliverables**
- Running API skeleton with health, errors, logging, transactions, and test harness.

**Acceptance criteria**
- Invalid config prevents startup with a clear message.
- A forced exception returns 500 without stack trace or secrets.
- Logs contain request ID and duration but no PII/tokens.
- Test suite isolates DB state per test.

**Testing:** Unit tests for config/errors/pagination/time; integration test for rollback; log-redaction test.

**Definition of Done:** Cross-cutting tests pass; feature phases can rely on these helpers without modification.

---

### Phase 6 — Authentication, Sessions & RBAC

**Objective:** Deliver registration, login, logout, profile, user administration, and server-side role/object authorization.

**Requirements covered:** FR-001…FR-006, NFR-004…NFR-007, NFR-021; RBAC-01…RBAC-08; AC-01, AC-13, AC-14; US-CIT-01, US-CIT-02, US-CIT-15, US-CIT-17, US-ADM-01, US-SYS-01.

**Detailed tasks**
1. `POST /auth/register`: validate name 2–120, case-insensitive unique email ≤190, password 8–72 with letter+digit, optional phone 7–20; bcrypt cost ≥12; create `CITIZEN`; return 201 + JWT + public user.
2. `POST /auth/login`: verify active user + constant-time hash check; 8 h JWT; generic `Invalid email or password` on any failure; return token + user.
3. `POST /auth/logout`: 204; client discards token.
4. `GET /auth/me`: own profile with department name; no hash/PII leakage.
5. JWT dependency: decode, verify signature/expiry, load user, reject inactive; attach `CurrentUser`.
6. Role guard factory (`require_roles(...)`) and object-scope guards (citizen owner, officer department, superintendent escalated-only, admin global).
7. `GET /admin/users`, `POST /admin/users`, `PATCH /admin/users/{id}` (role/active): enforce exactly one active department for officers; block deactivating/demoting the last active admin.
8. Password never returned/logged; redact auth headers.
9. Auth tests: 12-case RBAC matrix from SRS; 401 vs 403 vs 404 semantics.

**Subtasks**
- 6.1 Password policy + bcrypt service.
- 6.2 JWT issue/verify + expiry tests.
- 6.3 Register/login/logout/me endpoints.
- 6.4 Role dependencies.
- 6.5 Object-scope helpers.
- 6.6 Admin user management.
- 6.7 Last-admin protection.
- 6.8 RBAC matrix tests.

**Files/folders:** `backend/app/api/auth.py`, `api/admin_users.py`, `services/auth_service.py`, `services/user_service.py`, `core/security.py`, `dependencies.py`, `schemas/auth.py`, `schemas/user.py`, `tests/integration/test_auth.py`, `test_rbac.py`.

**Technologies/tools:** FastAPI, passlib/bcrypt, python-jose or PyJWT, pytest.

**Dependencies:** Phase 5.

**Deliverables**
- Auth + user admin API with enforced RBAC.

**Acceptance criteria**
- AC-01 passes end-to-end via API.
- Invalid credentials and inactive users both return the same 401 message.
- Citizen gets 403 on admin/department/superintendent routes (AC-13).
- Officer cannot access another department's objects (AC-14).
- Last active admin cannot be deactivated or demoted.

**Testing:** Unit (password/JWT), integration (register/login/me/admin), RBAC matrix (12 cases), concurrency test for last-admin protection.

**Definition of Done:** All auth tests pass; no plaintext password or secret appears in DB or logs.

---

### Phase 7 — Notifications Engine

**Objective:** Provide transactional, owner-only in-app notifications for NT-01…NT-07 with unread counts and read state.

**Requirements covered:** FR-042…FR-045, NT-01…NT-07, BR-13, BR-14; AC-15; US-CIT-09…US-CIT-14, US-SYS-03.

**Detailed tasks**
1. Notification model usage: `user_id`, `complaint_id`, `trigger_code` (NT-xx), `title`, `body`, `read_at`, `created_at`, optional metadata JSON.
2. Notification service API: `notify_users(user_ids, complaint, trigger, payload)` callable **inside** the caller's transaction; no independent commits.
3. Recipient resolution helpers: citizen owner; all active officers of responsible department; all active superintendents; deduplicate user IDs.
4. Templates for each trigger with required fields:
   - NT-01 tracking, category, department, submitted time.
   - NT-02 department, accepting officer, acceptance time, deadline.
   - NT-03 rejection reason.
   - NT-04 new status + progress note.
   - NT-05 deadline + overdue duration + escalation time (to superintendents, dept officers, citizen).
   - NT-06 action type + summary + superintendent identity + timestamp.
   - NT-07 resolution note + resolving officer + resolution time.
5. `GET /notifications`: owner only, newest first, 20/page, unread count.
6. `POST /notifications/{id}/read` and `POST /notifications/read-all`: idempotent; foreign notification → 404.
7. Ensure no notification is created when the triggering transaction rolls back.

**Subtasks**
- 7.1 Service + template registry.
- 7.2 Recipient resolvers.
- 7.3 List/unread-count endpoint.
- 7.4 Mark-read endpoints.
- 7.5 Atomicity tests.
- 7.6 Content-field tests per trigger.

**Files/folders:** `backend/app/services/notification_service.py`, `api/notifications.py`, `schemas/notification.py`, `tests/integration/test_notifications.py`.

**Technologies/tools:** SQLAlchemy, pytest.

**Dependencies:** Phase 6 (users/roles); integrated by Phases 8–13.

**Deliverables**
- Notification engine + citizen notification API.

**Acceptance criteria**
- AC-15 passes: owner-only list, unread count correct, mark-read idempotent, foreign ID returns 404.
- Rolling back a triggering change leaves zero notification rows.
- Each NT template contains every field required by FR-045.

**Testing:** Integration tests per trigger; rollback/fault-injection test; pagination and read-state tests.

**Definition of Done:** Notification service is the only writer of notification rows; all later features call it inside their transaction.

---

### Phase 8 — Complaint Submission, Media & Routing

**Objective:** Implement category catalogue, complaint creation with validation, unique tracking numbers, department routing, dual history rows, and safe image upload.

**Requirements covered:** FR-007…FR-013, FR-010/FR-011, FR-009, NFR-013; BR-01…BR-04, BR-12, BR-16; AC-02, AC-03; US-CIT-03…US-CIT-06.

**Detailed tasks**
1. `GET /categories`: active categories with mapped active department; authenticated.
2. `POST /complaints`: validate title 5–150, description 20–2,000, active category, optional location ≤255, coordinates paired and ranged; 0–3 images.
3. Reject inactive/unmapped category with 422 and persist nothing (FR-012).
4. Generate tracking number `CT-YYYY-NNNNNN` with DB-backed uniqueness and retry on collision (FR-009).
5. Transaction: insert complaint `SUBMITTED`, set `PENDING_DEPARTMENT_REVIEW`, append two history rows (`null→SUBMITTED` citizen, `SUBMITTED→PENDING_DEPARTMENT_REVIEW` SYSTEM), create NT-01.
6. Upload pipeline: enforce JPEG/PNG/WebP by magic bytes, ≤5 MiB each, ≤3 files, random storage names, metadata rows; clean up files on rollback/failure.
7. Authorized media serving endpoint (no public static exposure).
8. Store `department_id` from category mapping and `sla_seconds` config snapshot only at acceptance (leave null at submission).

**Subtasks**
- 8.1 Category read endpoint.
- 8.2 Complaint schema + validators.
- 8.3 Tracking number generator.
- 8.4 Routing + transaction + history.
- 8.5 Upload validation/storage.
- 8.6 NT-01 integration.
- 8.7 Rollback cleanup.
- 8.8 Tests for invalid payload matrix.

**Files/folders:** `backend/app/api/categories.py`, `api/complaints.py`, `services/complaint_service.py`, `services/storage_service.py`, `services/tracking.py`, `schemas/complaint.py`, `tests/integration/test_complaint_create.py`, `test_uploads.py`.

**Technologies/tools:** FastAPI `UploadFile`, `python-magic` or manual signature check, Pillow optional, local volume storage.

**Dependencies:** Phases 4–7.

**Deliverables**
- Working submission flow with routing and image handling.

**Acceptance criteria**
- AC-02 passes: valid submission returns unique tracking number and appears in the correct department.
- AC-03 passes: visibility restricted to owner and mapped department.
- Invalid image/category/coordinate payload returns 422 with no complaint or orphan file.
- Exactly two history rows exist after submission.

**Testing:** Integration tests for happy path, boundary lengths, bad magic bytes, oversize, 4 images, inactive category, coordinate pairing, tracking uniqueness under concurrency.

**Definition of Done:** Submission is atomic; uploads are private; no orphan rows/files on failure.

---

### Phase 9 — Citizen Tracking & Timeline

**Objective:** Let citizens list and inspect only their own complaints with a complete, permission-filtered timeline.

**Requirements covered:** FR-014…FR-016, FR-050; BR-12, BR-15; AC-03, AC-06, AC-12; US-CIT-07, US-CIT-08.

**Detailed tasks**
1. `GET /complaints`: owner-only, newest first, 20/page, filters `status`, `category_id`; return summary fields.
2. `GET /complaints/{id}`: owner or authorized role; include tracking, title, description, category, department, status, submitted/accepted/deadline/resolved times, location, images, resolution summary.
3. `GET /complaints/{id}/timeline`: merge status history, progress notes, superintendent actions, escalation events, image additions; sort by event time then id; filter by viewer permission.
4. Compute `overdue_seconds` at request time for escalated items; never persist derived values that can go stale.
5. 404 for unknown, 403 for known-but-unauthorized (owner endpoint must not leak existence to strangers — follow SRS policy: citizen query restricted by owner).
6. Ensure timeline is read-only; no update/delete routes (FR-050, NFR-008).

**Subtasks**
- 9.1 List query + filters + pagination.
- 9.2 Detail serializer.
- 9.3 Timeline aggregator + ordering.
- 9.4 Visibility filter.
- 9.5 Tests for cross-citizen access.
- 9.6 Deadline/overdue formatting helpers.

**Files/folders:** `backend/app/api/complaints.py`, `services/complaint_query_service.py`, `services/timeline_service.py`, `schemas/complaint.py`, `tests/integration/test_citizen_tracking.py`.

**Technologies/tools:** SQLAlchemy queries, Pydantic serializers.

**Dependencies:** Phase 8.

**Deliverables**
- Citizen list/detail/timeline APIs.

**Acceptance criteria**
- A citizen sees only their own complaints (AC-03).
- Timeline is ascending by timestamp then id and includes status, notes, actions, escalation, images.
- No route allows mutation of history.

**Testing:** Owner vs non-owner tests, filter/pagination tests, ordering test with same-timestamp events.

**Definition of Done:** Citizens can fully track a complaint through every P0 status via API.

---

### Phase 10 — Department Review & Case Management

**Objective:** Implement the full department workflow: queue, accept, reject, assign, progress, evidence, and resolve.

**Requirements covered:** FR-017…FR-026, FR-027 (acceptance deadline), FR-050; BR-04, BR-05, BR-11, BR-13, BR-17, BR-18; AC-04…AC-06, AC-11, AC-12, AC-14; US-DEP-01…US-DEP-08.

**Detailed tasks**
1. `GET /department/complaints`: queue scoped to officer's department, newest first, 20/page, filters status/category/assignee, per-status counts.
2. `GET /department/summary`: counts by status and escalation state.
3. `GET /complaints/{id}` for officers: same department only; other department → 403; unknown → 404.
4. `POST /complaints/{id}/accept`: only from `PENDING_DEPARTMENT_REVIEW`; set `ACCEPTED`, `accepted_at=utcnow`, `accepted_by_user_id`, `sla_seconds=config window`, `resolution_due_at=accepted_at+sla_seconds`, history row, NT-02; all atomic.
5. `POST /complaints/{id}/reject`: reason 10–1,000; status `REJECTED`, timestamps/actor/reason, history, NT-03; terminal in P0.
6. `POST /complaints/{id}/assign`: active same-department officer; set assignee + timestamp; no status change, no citizen notification.
7. `POST /complaints/{id}/progress`: note 5–2,000; allowed from ACCEPTED/IN_PROGRESS/ESCALATED; optional ACCEPTED→IN_PROGRESS; history on change; NT-04. Escalated progress keeps status.
8. `POST /complaints/{id}/images`: 1–3 valid images, ≤5 MiB, max 10 per complaint; kind PROGRESS/RESOLUTION; allowed only in ACCEPTED/IN_PROGRESS/ESCALATED.
9. `POST /complaints/{id}/resolve`: note 10–2,000; from ACCEPTED/IN_PROGRESS/ESCALATED; set RESOLVED + timestamps/actor/note, history, NT-07; else 409.
10. Enforce actor role + department on every mutation; rejected/illegal transitions return 409 with no writes.

**Subtasks**
- 10.1 Queue + summary.
- 10.2 Accept + deadline computation.
- 10.3 Reject.
- 10.4 Assign.
- 10.5 Progress + status transition.
- 10.6 Evidence upload.
- 10.7 Resolve.
- 10.8 Transition-guard test matrix.
- 10.9 Permission tests per action.

**Files/folders:** `backend/app/api/department.py`, `api/complaints.py`, `services/department_service.py`, `services/complaint_service.py`, `schemas/department.py`, `tests/integration/test_department_flow.py`.

**Technologies/tools:** SQLAlchemy transactions, FastAPI, pytest.

**Dependencies:** Phases 8–9.

**Deliverables**
- Complete P0 department workflow.

**Acceptance criteria**
- AC-04: acceptance sets deadline exactly `accepted_at + window`; NT-02 includes department and target date.
- AC-05: rejection requires reason; NT-03 contains it; no deadline.
- AC-06: progress updates appear in citizen timeline with actor/time.
- AC-11 (department path): resolve creates NT-07 and terminal state.
- Officer from another department gets 403 on every endpoint (AC-14).
- Illegal transitions return 409 and change nothing.

**Testing:** Full transition matrix, boundary note lengths, cross-department access, image limits, resolve-from-invalid-status, transaction rollback.

**Definition of Done:** Every department story passes; no endpoint mutates state without role + department + status guard.

---

### Phase 11 — Escalation Engine (SLA Worker)

**Objective:** Automatically escalate overdue accepted complaints exactly once, with a guarded configuration and a manual demo trigger.

**Requirements covered:** FR-027…FR-034, NFR-002, NFR-003, NFR-011, NFR-012, NFR-018; BR-05…BR-08, BR-19; AC-07, AC-08, AC-16; US-SYS-02, US-SYS-03, US-ADM-06.

**Detailed tasks**
1. Configuration: `ESCALATION_WINDOW_MINUTES` default 10,080; reject non-default unless `ALLOW_DEMO_ESCALATION=true`; otherwise refuse startup or fall back with error log (FR-033). Expose `sla_seconds` at acceptance.
2. Candidate query: status `ACCEPTED` or `IN_PROGRESS`, `resolution_due_at <= utcnow()`, no existing escalation; order by deadline.
3. Worker loop with APScheduler: run once at startup, then every `ESCALATION_INTERVAL_SECONDS` (default 60).
4. Exactly-once algorithm:
   - Acquire DB advisory lock `GET_LOCK('civictrack_escalation', timeout)`.
   - Re-check candidate still eligible.
   - Insert escalation row (unique `complaint_id`) and conditional `UPDATE complaints SET status='ESCALATED' WHERE id=? AND status IN (...)`.
   - If affected rows = 0, roll back/skip.
   - Append history `previous→ESCALATED`, actor `SYSTEM`, reason `SLA_BREACH`.
   - Create NT-05 to citizen, responsible department active officers, all active superintendents.
   - Commit once; release lock.
5. `escalations` fields: `complaint_id` unique, `escalation_number`, `previous_status`, `deadline_at`, `escalated_at`, `overdue_seconds`, `trigger_source`, `reason_code`.
6. `POST /internal/escalations/run`: token-protected, same function, returns `{evaluated, escalated, skipped}`; no duplicates.
7. Structured log per run: evaluated, escalated, skipped, duration, errors; never log PII.
8. Handle DB failure gracefully; next run must catch up all overdue complaints.

**Subtasks**
- 11.1 Config guard + tests.
- 11.2 Candidate query.
- 11.3 Advisory lock + conditional update.
- 11.4 Escalation record + history.
- 11.5 NT-05 fan-out.
- 11.6 Scheduler entrypoint/container command.
- 11.7 Internal endpoint.
- 11.8 Idempotency tests (20 sequential + parallel workers).
- 11.9 Restart/catch-up test.

**Files/folders:** `backend/app/workers/escalation_worker.py`, `services/escalation_service.py`, `api/internal.py`, `config.py`, `tests/integration/test_escalation.py`, compose `worker` service.

**Technologies/tools:** APScheduler, MySQL `GET_LOCK`, SQLAlchemy, pytest, concurrent futures.

**Dependencies:** Phases 7, 10.

**Deliverables**
- Working scheduler + manual trigger + idempotency guarantees.

**Acceptance criteria**
- AC-07: overdue accepted complaint becomes `ESCALATED` with no human action.
- AC-08: 20 repeated runs produce exactly one escalation row and one transition.
- Parallel worker simulation produces exactly one escalation.
- Wrong window without demo flag is refused; demo window is visibly flagged (AC-16).
- Worker restart escalates all overdue complaints.

**Testing:** Time-travel tests (freeze clock or backdate `resolution_due_at`), concurrency tests, config-guard tests, restart test, NT-05 recipient test.

**Definition of Done:** Idempotency proven under sequential and parallel execution; worker logs metrics; no duplicate notifications.

---

### Phase 12 — Superintendent Oversight

**Objective:** Give the Superintendent an escalation queue, full visibility, supervisory actions, follow-up directives, and resolution authority.

**Requirements covered:** FR-035…FR-041, FR-050; BR-09, BR-10, BR-11, BR-18; AC-09…AC-11; US-SUP-01…US-SUP-05.

**Detailed tasks**
1. `GET /superintendent/escalations`: `ESCALATED` only, sorted by overdue duration desc; fields tracking, department, acceptance, deadline, overdue, status.
2. Detail view for escalated complaints: responsible department, acceptance date, deadline, overdue computed at request time, resolution info.
3. Timeline read for escalated complaints (plus oversight read of others allowed; operational actions restricted to escalated).
4. `POST /complaints/{id}/superintendent-actions`: type `INSTRUCTION|FOLLOW_UP|REASSIGN|NOTE`, note 5–2,000, optional `directed_department_id`; append-only row with actor/time; timeline entry; NT-06 to department officers + citizen.
5. Follow-up directive records `directed_department_id` without changing original `department_id` in P0.
6. Queue retention until `RESOLVED`; monitor subsequent department updates.
7. `POST /complaints/{id}/resolve` for Superintendent: same rules as FR-024, actor = superintendent, NT-07; only from ESCALATED.
8. Enforce escalated-only operational scope and 403 elsewhere.

**Subtasks**
- 12.1 Queue query + overdue ordering.
- 12.2 Detail projection.
- 12.3 Action types + validation.
- 12.4 Directed follow-up.
- 12.5 NT-06 fan-out.
- 12.6 Superintendent resolve.
- 12.7 Scope tests.

**Files/folders:** `backend/app/api/superintendent.py`, `api/complaints.py`, `services/superintendent_service.py`, `schemas/superintendent.py`, `tests/integration/test_superintendent.py`.

**Technologies/tools:** FastAPI, SQLAlchemy.

**Dependencies:** Phases 9–11.

**Deliverables**
- Superintendent oversight APIs.

**Acceptance criteria**
- AC-09: queue shows department, acceptance, deadline, overdue, full timeline.
- AC-10: action appears in timeline with identity/time; department + citizen get NT-06.
- AC-11 (superintendent path): resolve from ESCALATED records actor, note, NT-07, leaves queue.
- Non-escalated operational action returns 403/409 as specified.

**Testing:** Queue ordering, overdue computation, action validation, recipient tests, resolve permission tests.

**Definition of Done:** Superintendent can observe and act without bypassing the state machine or department ownership rules.

---

### Phase 13 — Administration, Configuration & Audit

**Objective:** Deliver department/category management, platform activity metrics, and read-only audit logs.

**Requirements covered:** FR-046…FR-049, FR-050; NFR-008, NFR-019; BR-15; US-ADM-02…US-ADM-05.

**Detailed tasks**
1. `POST/GET/PATCH /admin/departments`: create/update/list/deactivate; block deactivation while active categories or active officers reference it.
2. `POST/GET/PATCH /admin/categories`: create/update/list/deactivate, remap department; mapping must reference an active department; changes affect only future complaints.
3. `GET /admin/activity`: counts by status and department, escalation count, 20 most recent platform timeline events.
4. `GET /admin/audit-logs`: filters actor, action, entity type, date range; paginated; read-only, no update/delete routes.
5. Audit writer: append on admin/config actions, auth events, and sensitive mutations; include actor, action, entity, timestamp, safe metadata (no PII payloads).
6. Enforce `PLATFORM_ADMIN` on all routes; 403 otherwise.

**Subtasks**
- 13.1 Department CRUD + deactivation guards.
- 13.2 Category CRUD + remap semantics.
- 13.3 Activity aggregation.
- 13.4 Audit log query + pagination.
- 13.5 Audit writer integration.
- 13.6 Immutability tests.

**Files/folders:** `backend/app/api/admin.py`, `services/admin_service.py`, `services/audit_service.py`, `schemas/admin.py`, `tests/integration/test_admin.py`.

**Technologies/tools:** SQLAlchemy aggregation, FastAPI.

**Dependencies:** Phases 6, 10, 11.

**Deliverables**
- Admin configuration + audit APIs.

**Acceptance criteria**
- Cannot deactivate a department with active categories/officers.
- Category remap changes routing only for new complaints.
- Audit log filters work; `PUT/PATCH/DELETE` on audit/history returns 405/404 and never mutates rows.
- Non-admin receives 403.

**Testing:** Guard tests, remap-routing test, audit immutability test, activity count correctness.

**Definition of Done:** Admin surface complete; all audit entities proven append-only through the API.

---

### Phase 14 — Frontend Foundation & Design System

**Objective:** Build the React application shell, design system, routing, auth state, API client, and shared UI primitives.

**Requirements covered:** NFR-010, NFR-014, NFR-015, NFR-016, NFR-021 (client-side); enables all UI stories.

**Detailed tasks**
1. Vite + React 18.3 + TypeScript strict; path aliases; env typing.
2. Tailwind + shadcn/ui setup; design tokens for color, spacing, typography; contrast ≥4.5:1.
3. Route tree: public (`/login`, `/register`), citizen (`/complaints`, `/complaints/new`, `/complaints/:id`, `/notifications`, `/profile`), department (`/department`, `/department/:id`), superintendent (`/superintendent`, `/superintendent/:id`), admin (`/admin/users|departments|categories|activity|audit-logs`), `*` 404.
4. `ProtectedRoute` with role allow-list; redirect unauthenticated to login; hide unauthorized navigation (defense in depth, not the only check).
5. Auth context: token in `sessionStorage`, login/logout, `/auth/me` bootstrap, 401 interceptor → logout.
6. TanStack Query client with query keys, retry policy, error normalization; axios/fetch wrapper with bearer header.
7. Shared components: AppShell, Sidebar, Topbar, PageHeader, DataTable, Pagination, StatusBadge, EmptyState, ErrorState, LoadingSkeleton, ConfirmDialog, FormField, Toast.
8. Forms with react-hook-form + Zod; accessible labels, keyboard operation, visible focus.
9. Base layout responsive at 360 px; no horizontal scroll.

**Subtasks**
- 14.1 Scaffold + lint/type config.
- 14.2 Tailwind/shadcn tokens.
- 14.3 Router + guards.
- 14.4 Auth context.
- 14.5 API client + query keys.
- 14.6 Shared components.
- 14.7 Form primitives.
- 14.8 Accessibility baseline.

**Files/folders:** `frontend/src/app/`, `routes/`, `components/ui/`, `components/layout/`, `lib/api.ts`, `lib/queryKeys.ts`, `hooks/useAuth.ts`, `styles/`, `tests/`.

**Technologies/tools:** Vite, TypeScript, Tailwind, shadcn/ui, React Router, TanStack Query, react-hook-form, Zod, Vitest, Testing Library.

**Dependencies:** Phase 6 (auth contract); can start after Phase 2 for scaffolding.

**Deliverables**
- Running SPA shell with auth-aware navigation and reusable UI kit.

**Acceptance criteria**
- Unauthenticated users cannot reach protected routes.
- Each role sees only its navigation.
- Layout usable at 360 px; all controls keyboard-operable.
- API client attaches token and handles 401/403/404/422 consistently.

**Testing:** Component tests for guards and key primitives; axe accessibility check; viewport smoke test.

**Definition of Done:** Shell, design system, and auth plumbing stable enough for feature screens.

---

### Phase 15 — Role Workspaces & UI Flows

**Objective:** Build every P0 screen for Citizen, Department Officer, Superintendent, and Platform Admin, wired to the documented flows.

**Requirements covered:** US-CIT-01…US-CIT-15, US-CIT-17, US-DEP-01…US-DEP-08, US-SUP-01…US-SUP-05, US-ADM-01…US-ADM-06, US-SYS-01…US-SYS-03; AC-01…AC-16; NFR-010, NFR-015; BR-12.

**Detailed tasks**
1. Auth screens: register, login, profile; inline validation mirroring server rules; generic login error.
2. Citizen: complaint list with status/category filters and pagination; new-complaint form (≤5 required inputs, optional location/images, ≤3 images, preview, size/type errors); detail with status, deadline, images, resolution, timeline; notifications with unread badge and mark-read.
3. Department: queue with per-status counts and filters; detail with accept/reject/assign/progress/evidence/resolve dialogs; deadline display; escalated-state handling (progress allowed, no status overwrite).
4. Superintendent: escalation queue sorted by overdue; detail with overdue timer, timeline, action form (type/note/directive), resolve dialog.
5. Admin: users (create/role/activate/deactivate, last-admin error), departments (CRUD/deactivate guard messaging), categories (CRUD/remap), activity dashboard, audit log with filters.
6. Copy rules: never claim verification (BR-12); label demo escalation window visibly when `ALLOW_DEMO_ESCALATION`; show 403/404 states without leaking data.
7. Loading, empty, error, and optimistic-update states for every list/mutation.
8. Confirm destructive/irreversible actions; disable submit while pending.

**Subtasks**
- 15.1 Auth + profile screens.
- 15.2 Citizen screens.
- 15.3 Department screens.
- 15.4 Superintendent screens.
- 15.5 Admin screens.
- 15.6 Shared dialogs/forms.
- 15.7 Role-based navigation polish.
- 15.8 Copy + demo-window labels.

**Files/folders:** `frontend/src/pages/{auth,citizen,department,superintendent,admin}/`, `features/*/`, `components/`, `tests/`.

**Technologies/tools:** React, TanStack Query, react-hook-form, Zod, shadcn/ui, Testing Library.

**Dependencies:** Phase 14; backend phases 8–13 for live data.

**Deliverables**
- All P0 screens implemented and navigable.

**Acceptance criteria**
- Every P0 user story has a usable UI path.
- Complaint submission from a first-time user is completable in ≤60 seconds.
- Citizen cannot see department/superintendent navigation (AC-13).
- All forms surface server validation errors at the right field.
- No screen displays "verified" or implies verification.

**Testing:** Component tests per screen, form validation tests, role-navigation tests, manual timed submission, viewport and keyboard checks.

**Definition of Done:** All four workspaces meet their stories; no dead links or placeholder screens remain in P0 paths.

---

### Phase 16 — Frontend–Backend Integration & State Sync

**Objective:** Wire the SPA to the real API end-to-end, remove mocks, and make cache, error, and session behavior production-correct.

**Requirements covered:** FR-004, FR-014…FR-045 (client consumption), NFR-001, NFR-012, NFR-021; AC-01…AC-16 integration.

**Detailed tasks**
1. Replace all mock data with typed API calls generated/maintained from the frozen contract.
2. Define query keys per entity and invalidate precisely after mutations (accept, reject, progress, resolve, escalate, action, read).
3. Global error mapping: 401 → logout + redirect; 403 → permission state; 404 → not-found state; 409 → conflict message with refresh; 422 → field errors.
4. Session bootstrap: restore token from `sessionStorage`, call `/auth/me`, handle expiry gracefully.
5. Notifications unread badge polling or refetch-on-focus (no websockets required).
6. Escalation demo: surface scheduler effects on refresh; optionally trigger internal endpoint from a guarded dev-only admin action.
7. Remove console noise, dead code, and unhandled promise rejections.
8. Add a typed API error class and central toast handling.
9. Verify no token/PII appears in URLs or client logs.

**Subtasks**
- 16.1 Typed client per module.
- 16.2 Query/mutation hooks.
- 16.3 Cache invalidation map.
- 16.4 Error handling matrix.
- 16.5 Session expiry tests.
- 16.6 Notification refresh.
- 16.7 Mock removal audit.

**Files/folders:** `frontend/src/lib/api/`, `features/*/api.ts`, `features/*/hooks.ts`, `lib/errors.ts`, `app/providers.tsx`, `tests/integration/`.

**Technologies/tools:** TanStack Query, fetch/axios, MSW for contract tests.

**Dependencies:** Phases 14–15 and backend 6–13.

**Deliverables**
- Fully integrated P0 application with no mocks in production paths.

**Acceptance criteria**
- Every P0 flow works against the real backend.
- Mutations refresh affected views without manual reload.
- Expired/invalid token logs out cleanly.
- 403/404/409/422 each render a distinct, correct state.

**Testing:** MSW contract tests, Playwright smoke per role, manual cross-role run.

**Definition of Done:** Mock audit returns zero production mocks; all integration tests green.

---

### Phase 17 — QA, Test Automation & UAT

**Objective:** Prove AC-01…AC-16 and the critical lifecycle with automated unit, integration, and E2E tests, then run scripted UAT.

**Requirements covered:** NFR-020, AC-01…AC-16, all P0 FRs, BR-01…BR-20, NT-01…NT-07; US-E2E-01.

**Detailed tasks**
1. Unit coverage: deadline math, tracking generator, state guards, role matrix, notification templates, config guard, overdue computation.
2. Integration coverage: every endpoint happy path + auth failure + validation failure + scope failure + conflict.
3. E2E (Playwright) golden path:
   - Citizen registers → submits with image → sees tracking.
   - Officer accepts → deadline/NT-02.
   - Officer progresses → citizen timeline/NT-04.
   - Time-travel/backdate → escalation → NT-05.
   - Superintendent instructs → NT-06 → resolves → NT-07.
   - Citizen sees RESOLVED.
4. Negative E2E: citizen blocked from staff routes; officer blocked cross-department; invalid transition 409.
5. Idempotency E2E: repeated escalation run yields one record.
6. Accessibility: axe scan on all main screens; keyboard-only walkthrough.
7. Cross-browser: latest two Chrome/Edge/Firefox/Safari (or documented equivalents).
8. UAT script with pass/fail per AC; record evidence (screenshots, request IDs).
9. Seed-based performance smoke: 500 complaints / 100 users.

**Subtasks**
- 17.1 Unit suite completion.
- 17.2 Integration suite completion.
- 17.3 E2E golden path.
- 17.4 Negative E2E.
- 17.5 Accessibility audit.
- 17.6 Browser matrix.
- 17.7 UAT execution + report.
- 17.8 Coverage report.

**Files/folders:** `backend/tests/`, `frontend/tests/`, `e2e/`, `docs/UAT_REPORT.md`, `docs/TEST_PLAN.md`.

**Technologies/tools:** pytest, Vitest, Testing Library, Playwright, axe-core, coverage tools.

**Dependencies:** Phase 16.

**Deliverables**
- Automated suite + UAT report + coverage summary.

**Acceptance criteria**
- AC-01…AC-16 each pass with linked evidence.
- Golden-path E2E passes in CI.
- No P0 endpoint lacks an integration test.
- Accessibility audit has no critical/serious violations on main flows.
- UAT report has zero open P0 failures.

**Testing:** The phase **is** testing; CI must run unit + integration + E2E on every push.

**Definition of Done:** GATE — UAT signed off; all P0 tests green; known issues triaged with severity.

---

### Phase 18 — Security, Performance & Accessibility Hardening

**Objective:** Verify and harden security, performance, reliability, and accessibility against NFR targets.

**Requirements covered:** NFR-001…NFR-022; SEC/RBAC/IDEM coverage; BR-15, BR-19; AC-08, AC-13, AC-14, AC-16.

**Detailed tasks**
1. Security review: authn/authz on every route, object-scope checks, IDOR probes, injection, upload bypass, path traversal, mass assignment, CORS, error leakage.
2. Secret/config review: no secrets in repo; JWT secret ≥32 bytes; demo flag off by default; internal token required.
3. Log review: no password/token/email/phone/location/coordinate leakage (NFR-021).
4. Dependency and container scan; pin versions.
5. Performance: seed 500 complaints/100 users; measure p95 list ≤1 s, detail ≤2 s with 50 concurrent users; document results.
6. Escalation performance/concurrency: 20-run and parallel-run proof; worker restart/catch-up.
7. Reliability: container restart, DB reconnect, failed scheduler run recovery.
8. Accessibility: labels, focus, contrast, keyboard, screen-reader names.
9. Capacity: 2 GB image storage behavior; max upload enforcement.
10. Fix findings, re-test, and record residual risks.

**Subtasks**
- 18.1 Authorization/IDOR probe suite.
- 18.2 Upload security tests.
- 18.3 Log/PII audit.
- 18.4 Dependency scan.
- 18.5 Load test + results.
- 18.6 Concurrency/restart tests.
- 18.7 Accessibility fixes.
- 18.8 Hardening report.

**Files/folders:** `docs/SECURITY_REVIEW.md`, `docs/PERFORMANCE_REPORT.md`, `tests/security/`, `tests/load/`, config files.

**Technologies/tools:** OWASP ZAP or manual probes, k6/Locust, pytest, axe, Trivy/npm audit/pip-audit.

**Dependencies:** Phase 17.

**Deliverables**
- Hardening report with evidence and residual risk register.

**Acceptance criteria**
- No critical/high security finding open.
- p95 targets met at demo volume or documented with mitigation.
- Idempotency and restart guarantees re-proven.
- No PII in logs; no public access to uploads.
- Accessibility targets met.

**Testing:** Security probe suite, load test, restart test, log scan, axe.

**Definition of Done:** GATE — security/performance sign-off; residual risks accepted explicitly.

---

### Phase 19 — Deployment, Operations & Demo Readiness

**Objective:** Make the system deployable and demoable with one command, seeded data, and an operator runbook.

**Requirements covered:** NFR-017, NFR-018, NFR-022, NFR-011; AC-16; US-ADM-06.

**Detailed tasks**
1. Production Dockerfiles (multi-stage) for API and web; non-root users; healthchecks.
2. Compose/prod profile: db, api, worker, web, reverse proxy optional; persistent volumes for DB and uploads.
3. Migration-on-start strategy (explicit job or entrypoint) with failure visibility.
4. Environment matrix: dev, demo, prod; demo uses `ALLOW_DEMO_ESCALATION=true` and a short window, clearly labeled; prod stays 10,080.
5. Seed demo dataset: admin, departments, categories, officers, superintendent, citizens, complaints in every status, one overdue candidate.
6. Backups/restore for DB and uploads; retention note (no hard delete).
7. Health/readiness checks and worker visibility; log aggregation instructions.
8. Runbook: start, stop, reset, seed, trigger escalation, rotate JWT secret, restore, troubleshoot.
9. Verify fresh-clone deployment on a clean machine.

**Subtasks**
- 19.1 Dockerfiles.
- 19.2 Compose profiles.
- 19.3 Migration job.
- 19.4 Demo seed + reset.
- 19.5 Backups/restore.
- 19.6 Runbook.
- 19.7 Fresh-clone verification.

**Files/folders:** `docker-compose.yml`, `docker-compose.prod.yml`, `backend/Dockerfile`, `frontend/Dockerfile`, `scripts/`, `docs/RUNBOOK.md`, `README.md`.

**Technologies/tools:** Docker, Compose, nginx/Caddy, MySQL backup tools.

**Dependencies:** Phase 18.

**Deliverables**
- Reproducible deployment + demo dataset + runbook.

**Acceptance criteria**
- `docker compose up` from a clean clone starts all services after `.env` setup.
- Demo seed produces one complaint ready to escalate.
- Worker logs show scheduled runs; `/health/ready` reflects DB state.
- Restore procedure verified.
- Demo mode visibly labeled; prod default verified as 10,080 minutes.

**Testing:** Fresh-clone deploy, restart persistence, backup/restore drill, demo script dry run.

**Definition of Done:** GATE — demo environment ready; runbook validated by someone other than the author.

---

### Phase 20 — Documentation, Traceability Audit & Final Delivery

**Objective:** Finalize documentation, prove complete requirement coverage, and hand over a clean, reproducible deliverable.

**Requirements covered:** All P0 FR/NFR/BR/NT/AC/US; documentation of P1/P2 status.

**Detailed tasks**
1. Update `README.md`: overview, architecture, setup, env vars, demo credentials, scripts, test commands.
2. Finalize `docs/ARCHITECTURE.md`, `DATA_MODEL.md`, `API_CONTRACT.md`, `TEST_PLAN.md`, `SECURITY_REVIEW.md`, `RUNBOOK.md`, `UAT_REPORT.md`.
3. Re-run the traceability audit: every FR/NFR/BR/NT/AC/story appears in the matrices with an implementation location and test.
4. Record P1 as optional-gated and P2 as not built, with rationale.
5. Clean repository: no dead code, no TODOs in P0 paths, no secrets, no large artifacts.
6. Verify licenses/attributions for third-party assets.
7. Produce final demo script (5–10 minutes) covering submit → accept → progress → escalate → superintendent → resolve.
8. Tag release `v1.0.0-p0`; attach coverage and test reports.
9. Handover checklist signed.

**Subtasks**
- 20.1 README refresh.
- 20.2 Doc set completion.
- 20.3 Traceability re-audit (scripted ID diff).
- 20.4 Repo cleanup.
- 20.5 Final test run.
- 20.6 Demo script.
- 20.7 Release tag + handover.

**Files/folders:** `README.md`, `docs/*`, `CHANGELOG.md`, release notes.

**Technologies/tools:** Markdown, ripgrep, git tags, coverage reports.

**Dependencies:** Phase 19.

**Deliverables**
- Complete documentation set, traceability proof, tagged release, demo script.

**Acceptance criteria**
- Scripted ID diff reports zero missing P0 requirements.
- Every AC has evidence.
- Fresh clone + documented setup + tests all pass.
- Demo script runs without manual data fixes.
- P1/P2 status is explicit.

**Testing:** Final full suite, fresh-clone verification, traceability script, demo rehearsal.

**Definition of Done:** GATE — final sign-off; deliverable reproducible from documentation alone.

---

### Phase 21 — Optional P1 Enhancements (Gated)

**Objective:** If and only if every P0 acceptance criterion passes and time remains, add the seven P1 capabilities without destabilizing P0.

**Requirements covered:** FR-051…FR-057, NT-08; US-CIT-16, US-P1-01…US-P1-04.

**Entry gate (all required)**
- Phase 20 signed off; all P0 tests green; no open critical/high defects.
- P1 work isolated behind feature flags; P0 regression suite must stay green after each item.

**Detailed tasks**
1. FR-051: Gemini category suggestion with confidence label, explicit confirmation, 5 s timeout, manual fallback; never block submission.
2. FR-052: up to 3 same-category complaints within 500 m and 7 days as possible duplicates; submit-anyway; no auto-merge.
3. FR-053: Leaflet/OpenStreetMap view scoped to viewer permissions; popups link to detail.
4. FR-054: priority suggestion (LOW/MEDIUM/HIGH) requiring officer confirmation; never blocks routing.
5. FR-055: Recharts admin analytics by status, department, category, age.
6. FR-056: citizen rating 1–5 + optional comment ≤1,000 for RESOLVED, once per complaint.
7. FR-057: reopen request with reason; officer accept/decline; acceptance sets `REOPENED` and a new deadline on re-acceptance; NT-08.
8. Add migrations, API contracts (versioned), tests, and UI entry points.
9. Update traceability and docs; keep P2 out.

**Subtasks**
- 21.1 Feature flags + config.
- 21.2 FR-051 suggestion.
- 21.3 FR-052 duplicates.
- 21.4 FR-053 map.
- 21.5 FR-054 priority.
- 21.6 FR-055 analytics.
- 21.7 FR-056 rating.
- 21.8 FR-057 reopen + NT-08.
- 21.9 Regression + docs.

**Files/folders:** `backend/app/services/p1/`, `api/p1.py`, `frontend/src/features/p1/`, migrations, `tests/p1/`.

**Technologies/tools:** Gemini API, Leaflet/OpenStreetMap, Recharts, existing stack.

**Dependencies:** Phase 20.

**Deliverables**
- Optional P1 features, each independently flaggable.

**Acceptance criteria**
- Each P1 FR meets its "should" behavior and never blocks a P0 flow on failure.
- P0 regression suite remains green.
- NT-08 is transactional with reopening.
- P1 can be disabled by config without code changes.

**Testing:** Per-feature tests, failure/fallback tests, P0 regression, accessibility/perf re-check.

**Definition of Done:** P1 delivered behind flags with P0 unaffected; otherwise P1 is explicitly deferred.

---

## 5. Dependency Graph

```text
1 Requirements
   └─ 2 Architecture
        └─ 3 Repo/Env
             └─ 4 Database
                  └─ 5 Backend Foundation
                       └─ 6 Auth/RBAC
                            ├─ 7 Notifications
                            └─ 8 Submission
                                 └─ 9 Citizen Tracking
                                      └─ 10 Department
                                           └─ 11 Escalation
                                                ├─ 12 Superintendent
                                                └─ 13 Admin/Audit

3 Repo/Env ── 14 Frontend Foundation (after 6 contract)
14 ── 15 Workspaces
6..13 + 14..15 ── 16 Integration
16 ── 17 QA/UAT
17 ── 18 Security/Perf
18 ── 19 Deployment
19 ── 20 Docs/Delivery
20 ── 21 Optional P1
```

**Critical path:** 1 → 2 → 3 → 4 → 5 → 6 → 8 → 10 → 11 → 17 → 18 → 19 → 20.

---

## 6. Requirement Traceability Matrix

### 6.1 Functional Requirements (FR-001…FR-064)

| FR | Pri | Phase | Primary artifact / endpoint | Verified by |
|---|---|---|---|---|
| FR-001 | P0 | 6 | `POST /auth/register` | AC-01, test_auth |
| FR-002 | P0 | 6 | `POST /auth/login`, `/auth/logout` | AC-01, test_auth |
| FR-003 | P0 | 6 | bcrypt hashing in `security.py` | NFR-004 test |
| FR-004 | P0 | 6 | role + object guards on all routes | RBAC matrix, AC-13 |
| FR-005 | P0 | 6 | `GET /auth/me` | AC-01 |
| FR-006 | P0 | 6 | `/admin/users` | US-ADM-01, last-admin test |
| FR-007 | P0 | 8 | `GET /categories` | AC-02 |
| FR-008 | P0 | 8 | `POST /complaints` | AC-02 |
| FR-009 | P0 | 8 | tracking generator | AC-02, uniqueness test |
| FR-010 | P0 | 8 | upload validator | NFR-013, upload tests |
| FR-011 | P0 | 8 | coordinate validator | validation matrix |
| FR-012 | P0 | 8 | routing service | AC-03 |
| FR-013 | P0 | 8 | submission transaction | two-history-row test |
| FR-014 | P0 | 9 | `GET /complaints` | AC-03 |
| FR-015 | P0 | 9 | `GET /complaints/{id}` | AC-03 |
| FR-016 | P0 | 9 | `/timeline` aggregator | AC-06 |
| FR-017 | P0 | 10 | `GET /department/complaints` | US-DEP-01 |
| FR-018 | P0 | 10 | officer detail scope | AC-14 |
| FR-019 | P0 | 10 | `POST /accept` | AC-04 |
| FR-020 | P0 | 10 | `POST /reject` | AC-05 |
| FR-021 | P0 | 10 | `POST /assign` | US-DEP-05 |
| FR-022 | P0 | 10 | `POST /progress` | AC-06 |
| FR-023 | P0 | 10 | `POST /images` | US-DEP-06 |
| FR-024 | P0 | 10 | `POST /resolve` | AC-11 |
| FR-025 | P0 | 10 | `GET /department/summary` | US-DEP-01 |
| FR-026 | P0 | 10 | progress on ESCALATED | BR-18 test |
| FR-027 | P0 | 11 | deadline on acceptance | AC-04, BR-05 |
| FR-028 | P0 | 11 | scheduler | AC-07 |
| FR-029 | P0 | 11 | unique + lock + conditional update | AC-08, NFR-003 |
| FR-030 | P0 | 11 | escalation transition | AC-07 |
| FR-031 | P0 | 11 | `escalations` row | AC-07 |
| FR-032 | P0 | 11 | NT-05 fan-out | NFR-012, AC-07 |
| FR-033 | P0 | 11 | config guard | AC-16 |
| FR-034 | P0 | 11 | `POST /internal/escalations/run` | AC-08 |
| FR-035 | P0 | 12 | `GET /superintendent/escalations` | AC-09 |
| FR-036 | P0 | 12 | escalated detail projection | AC-09 |
| FR-037 | P0 | 12 | timeline read | AC-09 |
| FR-038 | P0 | 12 | `POST /superintendent-actions` | AC-10 |
| FR-039 | P0 | 12 | directed follow-up | BR-18 |
| FR-040 | P0 | 12 | queue retention | AC-11 |
| FR-041 | P0 | 12 | superintendent resolve | AC-11 |
| FR-042 | P0 | 7 | transactional notification service | NFR-012 |
| FR-043 | P0 | 7 | `GET /notifications` | AC-15 |
| FR-044 | P0 | 7 | mark read / read-all | AC-15 |
| FR-045 | P0 | 7 | NT templates | trigger content tests |
| FR-046 | P0 | 13 | `/admin/departments` | US-ADM-02 |
| FR-047 | P0 | 13 | `/admin/categories` | US-ADM-03 |
| FR-048 | P0 | 13 | `/admin/activity` | US-ADM-04 |
| FR-049 | P0 | 13 | `/admin/audit-logs` | US-ADM-05, NFR-008 |
| FR-050 | P0 | 10 | history writer + read-only routes | AC-06, NFR-008 |
| FR-051 | P1 | 21 | Gemini suggestion | P1 tests, fallback |
| FR-052 | P1 | 21 | duplicate detection | P1 tests |
| FR-053 | P1 | 21 | Leaflet map | P1 tests |
| FR-054 | P1 | 21 | priority suggestion | P1 tests |
| FR-055 | P1 | 21 | Recharts analytics | P1 tests |
| FR-056 | P1 | 21 | rating | P1 tests |
| FR-057 | P1 | 21 | reopen + NT-08 | P1 tests |
| FR-058 | P2 | — | not built | future |
| FR-059 | P2 | — | not built | future |
| FR-060 | P2 | — | not built | future |
| FR-061 | P2 | — | not built | future |
| FR-062 | P2 | — | not built | future |
| FR-063 | P2 | — | not built | future |
| FR-064 | P2 | — | not built | future |

**Coverage:** 50/50 P0 FRs assigned to phases 6–13; 7/7 P1 FRs assigned to gated phase 21; 7 P2 FRs explicitly excluded.

### 6.2 Non-Functional Requirements (NFR-001…NFR-022)

| NFR | Phase | Implementation / evidence |
|---|---|---|
| NFR-001 Performance | 18 | k6/Locust p95 list ≤1 s, detail ≤2 s |
| NFR-002 Timeliness | 11 | worker interval test, 2-min window |
| NFR-003 Concurrency | 11 | 20 sequential + parallel run test |
| NFR-004 Credential security | 6 | bcrypt cost ≥12, no plaintext test |
| NFR-005 Authorization | 6, 18 | 12-case RBAC + IDOR probe |
| NFR-006 Session security | 6 | 8 h expiry, secret ≥32 bytes |
| NFR-007 Privacy | 6, 9, 18 | field-level access tests |
| NFR-008 Audit immutability | 13, 17 | update/delete attempt returns 405/404 |
| NFR-009 Time handling | 5, 11 | UTC DATETIME(6), timezone render test |
| NFR-010 Usability | 14, 15, 17 | 360 px + timed ≤60 s submission |
| NFR-011 Reliability | 11, 19 | restart/catch-up test |
| NFR-012 Transactional integrity | 7, 8, 10, 11, 17 | rollback/fault injection |
| NFR-013 Upload safety | 8, 18 | magic bytes, size, random name |
| NFR-014 Compatibility | 17 | browser matrix |
| NFR-015 Accessibility | 14, 17, 18 | labels, focus, contrast, axe |
| NFR-016 Maintainability | 3, 20 | strict TS, ruff, schemas, `.env.example` |
| NFR-017 Portability | 3, 19 | clean-clone compose test |
| NFR-018 Observability | 5, 11, 19 | structured logs, `/health`, `/health/ready` |
| NFR-019 Retention | 4, 13 | no hard delete routes |
| NFR-020 Testability | 17 | unit/integration/E2E suite |
| NFR-021 Log hygiene | 5, 18 | redaction + log scan |
| NFR-022 Capacity | 4, 18, 19 | 500 complaints / 100 users / 2 GB seed |

### 6.3 Business Rules (BR-01…BR-20)

| BR | Phase | Enforcement |
|---|---|---|
| BR-01 unique tracking | 4, 8 | unique DB constraint + generator |
| BR-02 one citizen owner | 4, 8 | non-null FK |
| BR-03 one active department | 4, 8 | mapping + non-null FK |
| BR-04 authorized officer only | 6, 10 | role + department guard |
| BR-05 clock starts at acceptance | 10, 11 | `resolution_due_at` computation |
| BR-06 10,080 minutes | 11 | config default |
| BR-07 auto-escalate overdue | 11 | worker candidate query |
| BR-08 once per complaint | 4, 11 | unique index + lock |
| BR-09 superintendent full history | 12 | timeline access |
| BR-10 actor/time/from/to | 8, 10, 11, 12 | history writer |
| BR-11 resolve authority | 10, 12 | role guard |
| BR-12 no verification claim | 15, 20 | copy audit |
| BR-13 rejection reason shown | 10, 7 | NT-03 |
| BR-14 citizen notifications | 7 | NT-01…NT-07 |
| BR-15 PII restriction | 6, 9, 18 | scope + field tests |
| BR-16 legal transitions only | 10, 11, 12 | 409 guard matrix |
| BR-17 resolve note required | 10, 12 | schema validation |
| BR-18 preserve department | 10, 12 | no `department_id` mutation |
| BR-19 guarded demo window | 11, 19 | config guard |
| BR-20 never infer resolved | 10, 12 | only explicit resolve writers |

### 6.4 Notification Triggers (NT-01…NT-08)

| NT | Trigger | Phase | Recipients | Atomic with |
|---|---|---|---|---|
| NT-01 | Submitted | 8 | Citizen | submission |
| NT-02 | Accepted | 10 | Citizen | acceptance |
| NT-03 | Rejected | 10 | Citizen | rejection |
| NT-04 | Progress/status | 10 | Citizen | progress |
| NT-05 | Escalated | 11 | Superintendents, dept officers, Citizen | escalation |
| NT-06 | Supervisory action | 12 | Dept officers, Citizen | action |
| NT-07 | Resolved | 10, 12 | Citizen | resolution |
| NT-08 | Reopening accepted (P1) | 21 | Dept officers, Citizen | reopening |

### 6.5 Acceptance Criteria (AC-01…AC-16)

| AC | Phase | Test location |
|---|---|---|
| AC-01 register/login/profile | 6, 17 | `test_auth.py`, Playwright auth |
| AC-02 submit + tracking | 8, 17 | `test_complaint_create.py` |
| AC-03 visibility isolation | 9, 17 | `test_citizen_tracking.py` |
| AC-04 accept + deadline + NT-02 | 10, 17 | `test_department_flow.py` |
| AC-05 reject + reason + NT-03 | 10, 17 | department flow |
| AC-06 progress timeline | 9, 10, 17 | timeline tests |
| AC-07 auto escalation | 11, 17 | `test_escalation.py` |
| AC-08 20-run idempotency | 11, 17 | escalation concurrency |
| AC-09 superintendent queue | 12, 17 | `test_superintendent.py` |
| AC-10 instruction + NT-06 | 12, 17 | superintendent action |
| AC-11 resolve + NT-07 | 10, 12, 17 | resolve tests |
| AC-12 no false resolved | 10, 17 | state audit |
| AC-13 citizen 403 staff routes | 6, 17 | RBAC matrix |
| AC-14 cross-department 403 | 6, 10, 17 | scope tests |
| AC-15 notifications owner-only | 7, 17 | `test_notifications.py` |
| AC-16 SLA default + demo guard | 11, 18, 19 | config tests + demo label |

### 6.6 User Story Traceability (44 Stories)

| Story | Role | Phase | Requirements |
|---|---|---|---|
| US-CIT-01 | Citizen | 6 | FR-001, FR-003 |
| US-CIT-02 | Citizen | 6 | FR-002, FR-003 |
| US-CIT-03 | Citizen | 8 | FR-007, FR-008, FR-013 |
| US-CIT-04 | Citizen | 8 | FR-010 |
| US-CIT-05 | Citizen | 8 | FR-011 |
| US-CIT-06 | Citizen | 8 | FR-009, FR-012 |
| US-CIT-07 | Citizen | 9 | FR-014 |
| US-CIT-08 | Citizen | 9 | FR-015, FR-016 |
| US-CIT-09 | Citizen | 7 | NT-01, FR-042, FR-045 |
| US-CIT-10 | Citizen | 7 | NT-02, FR-045 |
| US-CIT-11 | Citizen | 7 | NT-03, FR-045 |
| US-CIT-12 | Citizen | 7 | NT-04, FR-045 |
| US-CIT-13 | Citizen | 7 | NT-05/NT-07, FR-045 |
| US-CIT-14 | Citizen | 7 | FR-043, FR-044 |
| US-CIT-15 | Citizen | 6 | FR-004, RBAC-01…08 |
| US-CIT-16 | Citizen (P1) | 21 | FR-056, FR-057 |
| US-CIT-17 | Citizen | 6 | FR-005 |
| US-DEP-01 | Officer | 10 | FR-017, FR-025 |
| US-DEP-02 | Officer | 10 | FR-018 |
| US-DEP-03 | Officer | 10 | FR-019, FR-027 |
| US-DEP-04 | Officer | 10 | FR-020 |
| US-DEP-05 | Officer | 10 | FR-021 |
| US-DEP-06 | Officer | 10 | FR-022, FR-023 |
| US-DEP-07 | Officer | 10 | FR-024 |
| US-DEP-08 | Officer | 10 | FR-026 |
| US-SUP-01 | Superintendent | 12 | FR-035, FR-032 |
| US-SUP-02 | Superintendent | 12 | FR-036, FR-037 |
| US-SUP-03 | Superintendent | 12 | FR-038 |
| US-SUP-04 | Superintendent | 12 | FR-039 |
| US-SUP-05 | Superintendent | 12 | FR-040, FR-041 |
| US-ADM-01 | Admin | 6 | FR-006 |
| US-ADM-02 | Admin | 13 | FR-046 |
| US-ADM-03 | Admin | 13 | FR-047 |
| US-ADM-04 | Admin | 13 | FR-048 |
| US-ADM-05 | Admin | 13 | FR-049 |
| US-ADM-06 | Admin | 11 | FR-033, FR-034 |
| US-SYS-01 | System | 6 | FR-004, RBAC |
| US-SYS-02 | System | 11 | FR-028, FR-030, FR-031, FR-032 |
| US-SYS-03 | System | 11 | FR-029, FR-042 |
| US-E2E-01 | All | 17 | AC-01…AC-16 |
| US-P1-01 | P1 | 21 | FR-051, FR-054 |
| US-P1-02 | P1 | 21 | FR-052 |
| US-P1-03 | P1 | 21 | FR-053 |
| US-P1-04 | P1 | 21 | FR-055 |

**Story totals:** 44 = 39 P0 + 5 P1 (`US-CIT-16`, `US-P1-01`…`US-P1-04`).

---

## 7. Cross-Cutting Coverage Matrices

### 7.1 Role-Based Access Control (RBAC-01…RBAC-08)

| Rule | Expected behavior | Phase |
|---|---|---|
| RBAC-01 | Citizen: own complaints/notifications/profile only | 6, 9 |
| RBAC-02 | Officer: assigned department only; 403 cross-department | 6, 10 |
| RBAC-03 | Superintendent: escalated operational actions; oversight read | 6, 12 |
| RBAC-04 | Admin: config/users/audit; no complaint workflow mutation | 6, 13 |
| RBAC-05 | Client routes hidden by role; server remains authoritative | 6, 14 |
| RBAC-06 | Inactive users rejected on every request | 6 |
| RBAC-07 | Unknown object → 404; unauthorized known object policy per SRS | 6, 9, 10 |
| RBAC-08 | Cross-role mutation attempts change no state | 6, 17 |

### 7.2 Security & Data Controls (SEC)

| Control | Phase |
|---|---|
| SEC-01 bcrypt cost ≥12, no plaintext storage/logging | 6 |
| SEC-02 JWT 8 h, secret ≥32 bytes, inactive-user rejection | 6 |
| SEC-03 Server-side role + object scope on every route | 6 |
| SEC-04 Upload magic-byte check, 5 MiB, 3/request, randomized names | 8 |
| SEC-05 Private media endpoint, no public static path | 8 |
| SEC-06 Internal escalation endpoint token-protected | 11 |
| SEC-07 Config fails closed on unsafe demo override | 11 |
| SEC-08 PII/token/location log redaction | 5, 18 |
| SEC-09 Read-only audit/history APIs | 13 |
| SEC-10 CORS allow-list, no wildcard with credentials | 5, 19 |

### 7.3 Database Objects

| Table | Phase | Key constraint |
|---|---|---|
| `users` | 4, 6 | unique email, role, active |
| `departments` | 4, 13 | unique name/code |
| `complaint_categories` | 4, 13 | FK department, active |
| `complaints` | 4, 8 | unique tracking, FKs, status |
| `complaint_images` | 4, 8 | max-10 enforced in service |
| `complaint_status_history` | 4, 8–12 | append-only |
| `complaint_comments` | 4, 10 | progress notes |
| `notifications` | 4, 7 | owner, read_at |
| `escalations` | 4, 11 | unique `complaint_id` |
| `officer_actions` | 4, 12 | append-only |
| `audit_logs` | 4, 13 | append-only, filterable |

### 7.4 Idempotency & Concurrency (IDEM)

| Case | Guarantee | Phase |
|---|---|---|
| Escalation repeated 20× | one row, one transition | 11 |
| Parallel workers | advisory lock + conditional update | 11 |
| Manual trigger during scheduled run | same lock, no duplicate | 11 |
| Mark notification read twice | idempotent, `read_at` stable | 7 |
| Duplicate tracking number | retry on unique violation | 8 |
| Double accept/resolve | second returns 409, no change | 10 |

### 7.5 Escalation (ESC) Invariants

| ID | Invariant | Phase |
|---|---|---|
| ESC-01 | Window default 10,080 min; demo only with flag | 11 |
| ESC-02 | Deadline from `accepted_at`, never `submitted_at` | 10, 11 |
| ESC-03 | Candidates exclude escalated/resolved/rejected | 11 |
| ESC-04 | Unique escalation row per complaint | 4, 11 |
| ESC-05 | Status update conditional on pre-state | 11 |
| ESC-06 | History + escalation + NT-05 in one transaction | 11 |
| ESC-07 | Startup run + interval run | 11 |
| ESC-08 | Token-protected manual run returns counts | 11 |
| ESC-09 | Restart catches up all overdue | 11, 19 |

---

## 8. P1 / P2 Scope Policy

### P1 — Optional, gated (Phase 21)
`FR-051` AI category suggestion, `FR-052` duplicate detection, `FR-053` map view, `FR-054` priority suggestion, `FR-055` analytics, `FR-056` rating, `FR-057` reopening + `NT-08`, stories `US-CIT-16` and `US-P1-01`…`US-P1-04`.

**Rules:** no P1 work before Phase 20 sign-off; every P1 feature flaggable and non-blocking; P0 regression must stay green; failure of an external service (e.g., Gemini) must fall back silently to manual flow.

### P2 — Explicitly not built
`FR-058`…`FR-064`: outbound channels/outbox, multi-tenancy, working-day calendars, image verification, public transparency portal, native mobile, external work-order integration. These are documented as future scope only and must not appear in P0/P1 acceptance.

---

## 9. Risk Register

| Risk | Impact | Mitigation | Phase |
|---|---|---|---|
| Duplicate escalations under concurrency | Critical | unique index + `GET_LOCK` + conditional update + tests | 11 |
| Deadline computed from submission | Critical | single service function + unit tests | 10, 11 |
| Notification written outside transaction | High | service requires caller transaction; rollback tests | 7 |
| Cross-department data leak | Critical | centralized scope guards + IDOR probes | 6, 18 |
| Upload bypass / public file exposure | High | magic bytes, private serving, random names | 8, 18 |
| Demo window leaking to production | High | fail-closed config guard + visible label | 11, 19 |
| Scope creep into P1/P2 | Medium | gated phases + traceability audit | 1, 20 |
| Frontend/backend contract drift | Medium | frozen contract + typed client + MSW tests | 2, 16 |
| Time pressure causing skipped tests | High | DoD per phase; no phase closes without tests | All |
| Accessibility regressions | Medium | axe in CI + keyboard checks | 14, 17 |

### Open questions (resolve in Phase 1)
1. Exact SRS policy for 403 vs 404 on cross-citizen complaint access — adopt the strictest non-disclosing interpretation and document it.
2. Whether `complaint_comments` and `officer_actions` overlap for progress notes — follow TRD schema; do not duplicate writes.
3. Demo seed credentials and demo SLA window value — decide at Phase 19 and document in README.
4. P1 Gemini key provisioning — only needed if Phase 21 is approved.

---

## 10. Final Delivery Checklist

- [ ] All 50 P0 FRs implemented and tested.
- [ ] All 22 NFRs verified with evidence.
- [ ] All 20 BRs enforced by code or DB constraints.
- [ ] NT-01…NT-07 transactional and content-complete.
- [ ] AC-01…AC-16 pass with linked evidence.
- [ ] 39 P0 user stories demonstrable; 5 P1 stories either delivered behind flags or explicitly deferred.
- [ ] Exactly-once escalation proven sequentially and in parallel.
- [ ] Deadline always derived from `accepted_at`.
- [ ] Production window 10,080 minutes; demo override guarded and labeled.
- [ ] RBAC/IDOR matrix green; no PII in logs or URLs.
- [ ] `docker compose up` works from a clean clone.
- [ ] UAT, security, performance, and accessibility reports complete.
- [ ] README, runbook, API contract, data model, and traceability final.
- [ ] P2 scope explicitly excluded.
- [ ] Release tagged and handover signed.

---

*End of roadmap.*

