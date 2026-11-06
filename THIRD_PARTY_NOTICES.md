# Third-Party Notices — CivicTrack

> **Phase 20, DOC-036.** Project code is MIT (see `LICENSE`).
> Third-party packages are used under their own licenses below —
> no proprietary assets, fonts, or images are bundled.

## Backend — `backend/pyproject.toml`

| Package | License (SPDX) | Use |
|---|---|---|
| FastAPI | MIT | API framework |
| Uvicorn | BSD-3-Clause | ASGI server |
| Pydantic | MIT | schemas/validation |
| pydantic-settings | MIT | env contract |
| SQLAlchemy | MIT | ORM |
| PyMySQL | MIT | MySQL driver |
| Alembic | MIT | migrations |
| PyJWT | MIT | HS256 tokens |
| bcrypt | Apache-2.0 | password hashing |
| python-multipart | Apache-2.0 | uploads |
| httpx | BSD-3-Clause | HTTP client (tests) |
| Pillow | HPND | image helpers |
| APScheduler | MIT | escalation worker stub |
| python-dateutil | Apache-2.0 | date helpers |
| pytest / pytest-asyncio / pytest-cov | MIT | test harness |
| Ruff | MIT | lint/format |
| mypy | MIT | typecheck |
| pre-commit | MIT | hooks |

## Frontend — `frontend/package.json`

| Package | License (SPDX) | Use |
|---|---|---|
| React / React DOM | MIT | SPA |
| Vite | MIT | build/dev |
| TypeScript | Apache-2.0 | types |
| Tailwind CSS | MIT | styling |
| Radix UI Slot | MIT | primitives (via shadcn/ui pattern) |
| TanStack Query | MIT | server state |
| React Router | MIT | routing |
| React Hook Form + @hookform/resolvers | MIT | forms |
| Zod | MIT | validation |
| lucide-react | ISC | icons |
| class-variance-authority, clsx, tailwind-merge, tailwindcss-animate | MIT | styling utils |
| Vitest / Testing Library / Playwright / axe-core | Apache-2.0 / MIT / Apache-2.0 / MPL-2.0 | tests |
| ESLint, @typescript-eslint, Prettier, PostCSS/Autoprefixer | MIT / BSD-2-Clause / MIT / MIT | quality |

Frontend `package.json` already carries `overrides` for `@babel/*`;
all entries resolve from `frontend/package-lock.json`.

## Infrastructure

| Component | License | Use |
|---|---|---|
| MySQL 8.4 (Docker image) | GPLv2 (with MySQL exception) | database (deploy-time, not bundled) |
| Docker Compose | Apache-2.0 | orchestration |
| nginx (web) | BSD-2-Clause | SPA host + `/api` proxy |
| Caddy (optional proxy profile) | Apache-2.0 | TLS reverse proxy |

## Notes

- No Gemini, Leaflet/OSM, or Recharts code ships in the P0 tree; they
  are P1 (Phase 21) and would need notices before integration.
- `CivicTrack_Problem_Statement_and_Objectives.pdf` is the PS-14 brief;
  it is kept in-repo for traceability and is not redistributed as code.
- Demo accounts, seed names, and lorem-style content are original to
  this repo.
