# CivicTrack — Test Report (Phase 20, TEST-058)

> **Date:** 06 November 2026
> **Command baseline:** backend `pytest tests/`, frontend `vitest run`,
> `tsc --noEmit`, `eslint --max-warnings=0`, `ruff check`,
> `ruff format --check`, `docker compose config`.
> **Scope note:** E2E (Playwright) was not executed in this session. See §4.

---

## 1. Backend (TEST-058)

```bash
cd backend
python -m pytest backend/tests/unit backend/tests/integration -q
# root invocation from repo root: python -m pytest backend/tests/unit backend/tests/integration -q
```

Result: **125 passed, 7 warnings, 31.81 s** (Python 3.12.7, pytest 8.3.4).

| File | Tests |
|---|---|
| `tests/unit/test_config.py` | 7 |
| `tests/unit/test_deps.py` | 10 |
| `tests/unit/test_enums.py` | 10 |
| `tests/unit/test_health.py` | 2 |
| `tests/unit/test_schemas.py` | 18 |
| `tests/unit/test_security.py` | 17 |
| `tests/integration/test_auth.py` | 12 |
| `tests/integration/test_complaints.py` | 17 |
| `tests/integration/test_department_queue.py` | 3 |
| `tests/integration/test_rbac.py` | 18 |
| `tests/integration/test_schema_constraints.py` | 7 |
| `tests/integration/test_superintendent_queue.py` | 4 |
| **Total** | **125** |

Warnings: 1 DeprecationWarning (`anyio` BlockingPortal), 1
`PytestConfigWarning` (unknown `asyncio_mode`), 5 `SAWarning`
(transaction deassociated) on the constraint tests. No failures.

Coverage (`pytest --cov=app --cov-report=term --collect-only`):
**58% total (1216 stmts, 508 missed)**. Key lows: `app/seed.py` 0%,
`app/worker.py` 0% (stub), `app/services/auth_service.py` 19%,
`app/services/user_service.py` 18%. Models/helpers at 100%.

Lint/typecheck:

- `ruff check backend` — **clean** (after Phase 20 format fix).
- `ruff format --check backend` — 2 files flagged before fix
  (`backend/alembic/versions/0002_full_schema.py`,
  `backend/app/models/complaint_status_history.py`); fixed by running
  the formatter (DOC-035).
- `mypy app` — not run in this session (CI runs it; see
  `.github/workflows/ci.yml`). Record as not-run rather than passing.

## 2. Frontend (TEST-058)

```bash
cd frontend
npm run test:run      # vitest run
npm run typecheck     # tsc --noEmit
npm run lint          # eslint --max-warnings=0
npm run build         # tsc --noEmit && vite build
```

Result: **57 passed (11 files), 10.35 s**; typecheck/lint clean.
Files: `StatusBadge` (2), `FormField` (4), `client` (8),
`ProtectedRoute` (4), `validators` (5), `LoginPage` (4),
`accessibility` (2, axe), `RegisterPage` (4), `AppRoutes` (2),
`phase15` (10, role navigation + validators), `ui-primitives` (12).

`npm run test:coverage` — **fails**: `Cannot find dependency
'@vitest/coverage-v8'`. Fix: `npm i -D @vitest/coverage-v8`.
`npm run build` depends on the same toolchain; CI build is the recorded
evidence (396 kB JS in Phase 14/15 notes). Not re-run locally beyond
typecheck — vite build needs network-free `node_modules` which was present
(`frontend/node_modules/` exists); the failure mode above is coverage-only.

## 3. Compose / fresh-clone surface (TEST-059)

```bash
docker compose config                                # dev file: OK
docker compose -f docker-compose.yml -f docker-compose.prod.yml config --quiet
docker compose --profile seed --profile proxy config --quiet
```

All three validated in this session (no container start). Full
`docker compose up --build -d` + `curl /health` + seed + demo flow is
documented in `README.md` / `docs/RUNBOOK.md` / `docs/DEMO_SCRIPT.md`.
It was **not** executed against live MySQL in this session, so TEST-059
is recorded as *partially verified* (config + docs), not *boot-to-green*.

## 4. Not run (explicit)

- Playwright E2E (`frontend/tests/e2e/golden-path.spec.ts`,
  `accessibility.spec.ts`, `smoke.spec.ts`): requires a running
  `api` + `web` + seeded MySQL; backend stubs would fail golden-path
  steps 2+ (submit/accept/progress/escalate). Recorded as pending,
  not passing.
- `npx playwright install chromium` / `npm run e2e`: not run (browser
  binaries not fetched; offline CI note in `UAT_REPORT.md`).
- `pip-audit` / `npm audit` / Trivy: Phase 18 scope (`TEST-053`).

## 5. Phase 20 reading

TEST-058 is met for the **unit + integration + component** layers that
exist in this tree (125 + 57 green). The phase's full wording — *unit +
integration + component + E2E one final time* — is only partially met
because E2E cannot pass against stub endpoints. See
`docs/TRACEABILITY_AUDIT.md` §5 for the GATE impact.
