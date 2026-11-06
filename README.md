# CivicTrack

CivicTrack is a community problem reporting and resolution platform. Citizens
submit issues, departments accept or reject them, officers record progress, and
overdue complaints escalate automatically after seven calendar days.

This repository contains the Phase 3 baseline: a clean monorepo, local Docker
Compose environment, FastAPI health probes, a React application shell, linting,
typechecking, tests, and CI. Domain features are added in later phases.

## Stack

| Area | Technology |
|---|---|
| Frontend | React 18.3, Vite, TypeScript strict, Tailwind CSS, shadcn/ui, React Router, TanStack Query |
| Backend | Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2, Alembic |
| Database | MySQL 8.4, InnoDB, `utf8mb4_0900_ai_ci`, UTC storage |
| Worker | APScheduler (escalation service stub until Phase 11) |
| Local runtime | Docker Compose: `db`, `api`, `worker`, `web` |
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

## Design documents

The product and architecture documents are kept in `CivicTrack/docs/` in this
workspace. They remain the source of truth for requirements and later phases.
