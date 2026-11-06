# CivicTrack — Performance Report (Phase 18 / Phase 20 DOC-032)

> **Date:** 06 November 2026
> **Targets (SRS NFR-001 etc.):** p95 list <= 1 s, detail <= 2 s
> (50 concurrent users), escalation 20-run idempotent, capacity
> 500 complaints / 100 users / 2 GB images (NFR-022)
> **Verdict:** targets not yet measured. This report records the
> method, the data available, and the exact numbers still owed.
> No p95 figure below is invented.

---

## 1. What was run in Phase 20

| Suite | Result | Note |
|---|---|---|
| Backend unit + integration | 125 passed, 31.8 s | `pytest tests/` (see `TEST_REPORT.md`) |
| Frontend unit/component | 57 passed, 10.4 s | `vitest run` (11 files) |
| Frontend typecheck / lint | clean | `tsc --noEmit`, `eslint --max-warnings=0` |
| Backend lint / format | `ruff check` clean; `ruff format --check` flagged 2 files | fixed in Phase 20 cleanup (DOC-035) |
| Backend coverage (term) | **58% total** | `app/seed.py` 0%, `app/worker.py` 0%, services 18-19% (see §3) |
| Frontend coverage | **not run** | `npm run test:coverage` fails: missing `@vitest/coverage-v8` |
| Load test (k6/Locust) | **not run** | requires Phase 8/11 endpoints (queues, timeline, mutations) |
| Docker compose config | pass | dev + prod overlay + seed/proxy profiles |

E2E Playwright (Chromium) needs running `api` + `web` and seeded MySQL,
and is recorded in `docs/UAT_REPORT.md` as 4/5 golden-path + 6/6
accessibility on the Phase 17 tree. It was not re-run in Phase 20
(see `TEST_REPORT.md` for the exact statement).

---

## 2. Performance budget and what governs it

| Flow | p95 target | Governing index / query | Test that will prove it |
|---|---|---|---|
| `GET /complaints` (citizen list) | <= 1 s | `ix_complaints_citizen_sub (citizen_id, submitted_at)` | `TEST-054` load |
| `GET /complaints/{id}` (detail) | <= 2 s | PK lookup + `complaint_images` / history indexes | `TEST-054` |
| `GET /department/complaints` (queue) | <= 1 s | `ix_complaints_dept_status_sub` | `TEST-054` |
| `GET /superintendent/escalations` | <= 1 s | `escalations` + `complaints.status_due` | `TEST-054` |
| `GET /notifications` | <= 1 s | `ix_notifications_recipient_read` | `TEST-054` |
| Mutations (accept/reject/progress/resolve) | <= 2 s | single transaction + `GET_LOCK` guard | `TEST-054`, `TEST-017` |
| Escalation 20-run | exactly 1 row | `uq_escalations_complaint_id` + advisory lock + conditional `UPDATE` | `TEST-020` (Phase 11) |
| 500-complaint / 100-user seed smoke | buildable | `app/seed.py` idempotent seed (`--check`) | `TEST-048` |

Design choices that protect these budgets are already in the tree:
- 20/page default pagination, `page_size <= 100` (`API_CONTRACT.md` §1).
- Paginated list envelope `{items, page, page_size, total, total_pages}`.
- Composite indexes above are in `0002_full_schema` + models
  (see `docs/DATA_MODEL.md` §7).
- `overdue_seconds` computed at request time, never persisted
  (`API_CONTRACT.md`, BE-056), so escalated reads stay fresh.

---

## 3. Measured coverage (closest proxy to "is it exercised")

Backend `pytest tests --cov=app --cov-report=term --collect-only`
(125 tests collected):

| Area | Coverage | Reading |
|---|---|---|
| `app/models/*`, `app/core/clock.py`, `app/core/errors.py`, `app/core/pagination.py` | 100% | schema + helpers fully exercised |
| `app/schemas/auth.py` 67%, `app/schemas/user.py` 80% | high | validation paths well covered |
| `app/services/auth_service.py` 19%, `app/services/user_service.py` 18% | low | integration tests run through HTTP; service units thin |
| `app/seed.py` 0%, `app/worker.py` 0% | **0%** | stub worker + seed never imported by the suite (seed runs in Compose `seed` service) |
| **Total** | **58%** | see `TEST_REPORT.md` for full table |

Frontend coverage could not be produced (missing `@vitest/coverage-v8`).
Fix: `npm i -D @vitest/coverage-v8` then re-run `npm run test:coverage`.
Component tests (57) cover guards, badges, forms, shell, validators.

---

## 4. Capacity statement (NFR-022)

- **Upload limits (contract):** 5 MiB per file, <=3 per submission,
  <=10 lifetime per complaint (`MAX_UPLOAD_MB=5`,
  `MAX_IMAGES_PER_COMPLAINT=10` in `.env.example`).
- **Volume:** `civictrack_uploads` Docker volume; 2 GB behaviour test
  (`TEST-057`) not run — needs the Phase 8 storage service.
- **Database:** MySQL 8.4 InnoDB, `civictrack_db` volume. Seed shape:
  4 departments, 6 categories, 8 users, 8 complaints (`app/seed.py`).
  A 500/100 volume smoke (`TEST-048`) is not run — Phase 8/18.

---

## 5. What is still owed (explicit)

| ID | Work | Phase |
|---|---|---|
| `TEST-048` | Seed 500 complaints / 100 users, run perf smoke | 18 |
| `TEST-054` | Load test, record p95 list/detail/queue/mutations/unread | 18 |
| `TEST-055` | Re-run escalation 20x/parallel/restart after hardening | 18 |
| `TEST-057` | Capacity limits (2 GB, 5 MiB, 3/request, 10/complaint) | 18 |
| Frontend coverage | Install `@vitest/coverage-v8`, publish report | 17/20 |
| E2E in this tree | Playwright golden path against live stack | 17 |

---

## 6. Phase 20 link (DOC-032)

This file plus `docs/SECURITY_REVIEW.md`, `docs/RUNBOOK.md`,
`docs/UAT_REPORT.md` completes DOC-032. Their Phase 18 GATE
(p95 met or mitigated, idempotency/restart re-proven, no PII in logs)
is **not** claimed here; see `docs/TRACEABILITY_AUDIT.md` for the
per-requirement statement.
