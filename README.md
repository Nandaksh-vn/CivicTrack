# CivicTrack

CivicTrack is a community problem reporting and resolution platform. Citizens
submit issues, departments accept or reject them, officers record progress, and
overdue complaints escalate automatically after seven calendar days.

This repository is a clean monorepo with a Docker Compose environment,
FastAPI health probes, a React application shell, linting, typechecking,
tests, CI, and — since Phase 19 — a one-command deployment, demo dataset,
and operator runbook. See the [Runbook](docs/RUNBOOK.md) for production
operations.

## Stack

| Area | Technology |
|---|---|
| Frontend | React 18.3, Vite, TypeScript strict, Tailwind CSS, shadcn/ui, React Router, TanStack Query |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Database | MySQL 8.4, InnoDB, `utf8mb4_0900_ai_ci`, UTC storage |
| Worker | APScheduler (escalation service stub until Phase 11) |
| Local runtime | Docker Compose: `db`, `migrate`, `api`, `worker`, `web` (+ optional `proxy`) |
| Quality | Ruff, mypy, pytest, ESLint, Vitest, Playwright, pre-commit |

## Prerequisites

- Docker Desktop (or Docker Engine + Compose v2)
- Python 3.12+ for local backend development
- Node.js 20+ and npm for local frontend development
- `make` is optional; equivalent npm, pytest, and docker commands are shown below

## Quickstart

1. Copy the environment contract:

   ```bash
   cp .env.example .env
   ```

   On PowerShell:

   ```powershell
   Copy-Item .env.example .env
   ```

   The checked-in development values are safe for local use. Before any
   production deployment, replace `JWT_SECRET`, `INTERNAL_TRIGGER_TOKEN`, the
   MySQL passwords, and set `ENVIRONMENT=production`.

2. Start the stack:

   ```bash
   docker compose up --build -d
   ```

3. Confirm all four services are healthy:

   ```bash
   docker compose ps
   curl http://localhost:8000/health
   ```

   Expected response:

   ```json
   {"status":"ok","version":"1.0.0"}
   ```

4. Open the application:

   - Web: <http://localhost:8080>
   - API docs: <http://localhost:8000/docs>
   - Readiness (including MySQL): <http://localhost:8000/health/ready>

5. Stop the stack:

   ```bash
   docker compose down
   ```

   Use `docker compose down -v` only when you also want to delete the database
   and upload volumes.

## Demo deployment (Phase 19)

For a seeded, demo-ready stack with a short, visibly-labelled escalation
window (AC-16):

```bash
cp .env.demo.example .env        # ENVIRONMENT=demo, ESCALATION_WINDOW_MINUTES=2
docker compose up -d --build
docker compose run --rm seed python -m app.seed
docker compose run --rm seed python -m app.seed --check  # proves CT-2026-100009 is overdue
```

- Web: <http://localhost:8080> (amber “Demo mode” banner), API: <http://localhost:8000>
- The stack is `db → migrate → api → worker → web`. The one-shot `migrate`
  job runs `alembic upgrade head` first; `api`/`worker` wait for it, so a
  failed migration stops startup immediately. `seed` is a one-shot
  `seed`-profile service, safe to re-run.
- Demo accounts (password `SEED_PASSWORD`, default `Demo@12345`):
  `admin@demo.local`, `officer.{water,roads,electrical,sanitation}@demo.local`,
  `superintendent@demo.local`, `citizen1@demo.local`, `citizen2@demo.local`.
- The overdue demo complaint is **`CT-2026-100009`** (ACCEPTED, deadline past).

Full operator instructions: **[docs/RUNBOOK.md](docs/RUNBOOK.md)** —
start/stop/reset/seed/trigger escalation/rotate JWT secret/backup/restore.

### Environment matrix (dev / demo / prod)

| Variable | dev | demo | prod |
|---|---|---|---|
| `ENVIRONMENT` | `development` | `demo` | `production` |
| `ESCALATION_WINDOW_MINUTES` | `10080` | `2` | `10080` |
| `ALLOW_DEMO_ESCALATION` | `false` | `true` | `false` |
| `VITE_ALLOW_DEMO_ESCALATION` (build) | `false` | `true` | `false` |

Production example: `cp .env.production.example .env`, replace every
`CHANGE_ME` secret, then
`docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.
The prod overlay unpublishes the DB, binds `api`/`web` to `127.0.0.1`, and can
add the `proxy` (Caddy) profile for TLS. Back up with `scripts/backup.{sh,ps1}`
and restore with `scripts/restore.{sh,ps1}` (30-day retention, append-only).

## Local development (without Docker)

Start MySQL first (for example, `docker compose up -d db`), then:

### Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The local API reads environment variables from the process. Export the values
from `.env` or run `alembic upgrade head` from an environment where
`DATABASE_URL` is set.

### Frontend

```bash
cd frontend
npm ci
npm run dev
```

The Vite dev server runs at <http://localhost:5173> and proxies `/api` and
`/health` to <http://localhost:8000>.

## Verification commands

```bash
# Backend
cd backend
ruff check .
ruff format --check .
mypy app
pytest tests/ --cov=app --cov-report=term-missing

# Frontend
cd frontend
npm run lint
npm run typecheck
npm run test:run
npm run build

# Compose file only (does not start containers)
docker compose config
```

Playwright requires browser binaries. Install them once with:

```bash
cd frontend
npx playwright install chromium
npm run e2e
```

Pre-commit hooks are optional but recommended:

```bash
python -m pip install pre-commit
pre-commit install
pre-commit run --all-files
```

## Project layout

```text
.
├── backend/
│   ├── app/
│   │   ├── api/v1/            # versioned routers (added in later phases)
│   │   ├── core/              # config, clock, errors, logging
│   │   ├── db/                # SQLAlchemy engine, session, declarative base
│   │   ├── models/            # ORM models (Phase 4+)
│   │   ├── schemas/           # Pydantic schemas (Phase 5+)
│   │   ├── services/          # domain services (Phase 6+)
│   │   ├── main.py            # FastAPI application factory and health probes
│   │   └── worker.py          # APScheduler worker entrypoint
│   ├── alembic/               # migration environment
│   ├── docker/mysql/init.sql  # MySQL bootstrap
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/        # layout and shadcn/ui primitives
│   │   ├── pages/             # route pages
│   │   ├── router/            # React Router route tree
│   │   └── styles/            # Tailwind and design tokens
│   ├── tests/unit/            # Vitest + Testing Library
│   ├── tests/e2e/             # Playwright smoke tests
│   └── nginx.conf             # SPA fallback and API proxy
├── .github/workflows/ci.yml
├── docker-compose.yml
├── Makefile
└── .env.example
```

## Environment contract

The full list is in [`.env.example`](.env.example). Key variables:

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | MySQL DSN | SQLAlchemy connection used by API and worker |
| `ENVIRONMENT` | `development` | `development`, `demo`, `staging`, or `production` |
| `APP_TIMEZONE` | `Asia/Kolkata` | Display timezone; storage remains UTC |
| `JWT_SECRET` | placeholder | HS256 signing secret, 32+ characters in production |
| `JWT_EXPIRES_MINUTES` | `480` | Access token lifetime |
| `CORS_ORIGINS` | local origins | Comma-separated allowed browser origins |
| `ESCALATION_WINDOW_MINUTES` | `10080` | Seven calendar days; production default |
| `ALLOW_DEMO_ESCALATION` | `false` | Must be explicitly enabled for a shortened demo window |
| `ESCALATION_CHECK_SECONDS` | `60` | Worker polling interval |
| `INTERNAL_TRIGGER_TOKEN` | placeholder | Token for `/api/v1/internal/*` endpoints |
| `MAX_UPLOAD_MB` | `5` | Maximum image size |
| `MAX_IMAGES_PER_COMPLAINT` | `10` | Lifetime image limit per complaint |
| `VITE_API_BASE_URL` | `/api/v1` | Frontend API prefix |

The app also accepts these compatibility aliases:
`APP_ENV`, `JWT_SECRET_KEY`, `ESCALATION_INTERVAL_SECONDS`, and
`INTERNAL_API_TOKEN`.

### Safety behaviour

- A non-default `ESCALATION_WINDOW_MINUTES` is reverted to `10080` unless
  `ALLOW_DEMO_ESCALATION=true`.
- Production startup is refused when the JWT secret, internal token, or database
  credentials are still placeholders.
- `.env` is git-ignored. Only `.env.example` is committed.

## CI

`.github/workflows/ci.yml` runs three jobs:

- Backend: Ruff, Ruff format check, mypy, pytest with coverage.
- Frontend: ESLint, TypeScript, Vitest, production build.
- Compose: `docker compose config` validation.

## Deployment & operations

See [docs/RUNBOOK.md](docs/RUNBOOK.md) for start/stop/reset/seed,
escalation triggering, JWT rotation, backup/restore, health checks,
log aggregation, and troubleshooting. Production uses
`docker compose -f docker-compose.yml -f docker-compose.prod.yml`;
backup scripts are `scripts/backup.*` / `scripts/restore.*`.

## Design documents

The product and architecture documents are kept in `docs/` in this
workspace. They remain the source of truth for requirements and later phases.

## Final delivery (Phase 20)

Release: **documentation baseline for `v1.0.0-p0`** — tag withheld until the
code GATE closes (see `docs/TRACEABILITY_AUDIT.md` §5).

- **Documentation set:** `docs/ARCHITECTURE.md` (v1.0),
  `docs/DATA_MODEL.md`, `docs/API_CONTRACT.md` (v1.0),
  `docs/STATE_MACHINE.md`, `docs/ADRs/` (8), `docs/TEST_PLAN.md`,
  `docs/UAT_REPORT.md`, `docs/SECURITY_REVIEW.md`,
  `docs/PERFORMANCE_REPORT.md`, `docs/RUNBOOK.md`,
  `docs/TRACEABILITY_BASELINE.md`, `docs/TRACEABILITY_AUDIT.md`,
  `docs/DEMO_SCRIPT.md`, `docs/HANDOVER.md`, `docs/TEST_REPORT.md`,
  `CHANGELOG.md`, `THIRD_PARTY_NOTICES.md`, `LICENSE` (MIT).
- **Traceability verdict:** all 50 P0 FR IDs are assigned to phases, but
  only the auth/config subset (FR-001..FR-006, FR-033) is implemented
  with passing tests today; 30 P0 rows are missing and 12 are partial
  (stubs / DB-only). See `docs/TRACEABILITY_AUDIT.md` §2 for the
  per-FR table. P1 (FR-051..FR-057) is optional-gated and not started;
  P2 (FR-058..FR-064) is explicitly not built (DOC-034).
- **Test evidence (TEST-058):** backend 125 passed
  (`pytest tests/`, 58% coverage), frontend 57 passed
  (`vitest run`), typecheck/lint clean. E2E golden path and frontend
  coverage (`@vitest/coverage-v8`) are recorded as not-run — see
  `docs/TEST_REPORT.md`.
- **Demo:** `cp .env.demo.example .env && docker compose up -d --build
  && docker compose run --rm seed python -m app.seed` then follow
  `docs/DEMO_SCRIPT.md` (submit → accept → progress → escalate →
  superintendent → resolve). Demo users: `admin@demo.local`,
  `officer.roads@demo.local`, `superintendent@demo.local`,
  `citizen1@demo.local` — password `Demo@12345`. Overdue candidate:
  `CT-2026-100009`. The escalation worker is still a Phase 11 stub
  (`app/worker.py`), so auto-escalation is not yet live.
- **Handover:** `docs/HANDOVER.md` (acceptance checklist + signature
  block). Fresh-clone boot and demo rehearsal must be signed by
  reviewers before `v1.0.0-p0` is tagged.

Test commands:

```bash
cd backend && python -m pytest tests -q
cd frontend && npm run test:run && npm run typecheck && npm run lint
```
