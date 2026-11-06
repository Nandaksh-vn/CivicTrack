# CivicTrack Operator Runbook (Phase 19)

> **Scope:** Deploy, operate, demo, back up, restore, and troubleshoot the
> `db` / `api` / `worker` / `web` (+ optional reverse proxy) stack.
> **Requirements:** NFR-011/017/018/022, AC-16, US-ADM-06.
> **GATE:** demo-validated by a second operator (see §13 checklist).

## 1. Architecture at a glance

```
Browser ──> web (nginx :8080→80) ──/api + /health──> api (FastAPI :8000)
                                                            │
                              ┌─────────────────────────────┼──────────────┐
                              db (MySQL 8.4)   worker (APScheduler)   uploads volume
```

- `db` — MySQL 8.4, `utf8mb4_0900_ai_ci`, UTC. Volume `civictrack_db`.
- `migrate` — one-shot `alembic upgrade head` job. `api`/`worker` wait for it.
- `api` — FastAPI. Entrypoint also migrates (`RUN_MIGRATIONS=true`).
- `worker` — APScheduler escalation worker (stub until Phase 11; logs runs).
- `web` — nginx serving the Vite SPA. `/api/` → `api:8000/api/`, `/health` → `api:8000/health`.
- `proxy` (optional, `proxy` profile) — Caddy reverse proxy with auto-TLS.
- Volumes `civictrack_db` + `civictrack_uploads` persist across restarts (NFR-011/022).

## 2. Environment matrix (DEP-008)

| Variable | Development | Demo | Production |
|---|---|---|---|
| `ENVIRONMENT` | `development` | `demo` | `production` |
| `ESCALATION_WINDOW_MINUTES` | `10080` | `2` (short) | `10080` |
| `ALLOW_DEMO_ESCALATION` | `false` | `true` | `false` (enforced) |
| `VITE_ALLOW_DEMO_ESCALATION` (build-time) | `false` | `true` → banner | `false` |
| `ESCALATION_CHECK_SECONDS` | `60` | `30` | `60` |
| `SEED_DEMO_DATA` | `false` | `true` | `false` |
| Secrets (`JWT_SECRET`, `INTERNAL_TRIGGER_TOKEN`, DB passwords) | demo placeholders | demo placeholders | real 32+ char secrets, app refuses placeholders |

Templates: `.env.example` (dev), `.env.demo.example`, `.env.production.example`.
**AC-16 guard:** any `ESCALATION_WINDOW_MINUTES != 10080` without
`ALLOW_DEMO_ESCALATION=true` is reverted to `10080` with an error log.
Production also refuses to boot with placeholder secrets or demo flag on.

> ⚠️ The demo window is **always** visibly labelled: worker log
> `DEMO MODE: escalation window is … minutes` + SPA banner
> “Demo mode: 10-minute escalation window” (text is static; the *window* is
> `ESCALATION_WINDOW_MINUTES`).

## 3. Start

### 3.1 Development (default)

```bash
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
# Edit .env if you need the dev placeholders; localhost/dev-only is safe.
docker compose up -d --build
docker compose ps
curl http://localhost:8000/health        # {"status":"ok","version":"1.0.0"}
curl http://localhost:8000/health/ready  # {"status":"ready","db":"ok"}
# Web: http://localhost:8080   API docs: http://localhost:8000/docs
```

### 3.2 Demo (seeded, short escalation window)

```bash
cp .env.demo.example .env
docker compose up -d --build
docker compose run --rm seed python -m app.seed
docker compose run --rm seed python -m app.seed --check  # proves CT-2026-100009 is overdue
# Web: http://localhost:8080 — look for the amber "Demo mode" banner.
```

`docker compose up` alone also works after the `.env` copy: the `migrate`
job runs first, then `api` → `worker` → `web`. The seed step is explicit
(one-shot `seed` service) so CI and operators control when demo data appears.

### 3.3 Production (reverse proxy optional)

```bash
cp .env.production.example .env
# Replace EVERY CHANGE_ME / demo password with generated secrets. Set:
#   ENVIRONMENT=production  ESCALATION_WINDOW_MINUTES=10080  ALLOW_DEMO_ESCALATION=false
#   CORS_ORIGINS=https://<real-domain>
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
# With TLS-terminating proxy:
cp deploy/Caddyfile.example deploy/Caddyfile   # set {$DOMAIN:...}
docker compose -f docker-compose.yml -f docker-compose.prod.yml --profile proxy up -d --build
```

Production differences (overlay `docker-compose.prod.yml`): DB not published,
`api`/`web` bind `127.0.0.1` only, `restart: always`. Data stays in named volumes.

## 4. Stop

```bash
docker compose down              # keep DB + uploads (restart-safe)
docker compose down -v          # ⚠️ DESTROYS DB + uploads — local/demo only
# Prod overlay equivalent:
docker compose -f docker-compose.yml -f docker-compose.prod.yml down
```

## 5. Reset (demo only)

```bash
./scripts/reset.sh        # bash
.\scripts\reset.ps1       # PowerShell
```

Full reset = `down -v` + `up --build` + `seed` + `seed --check`.
For a rows-only reset (same volumes): `docker compose run --rm seed python -m app.seed --reset`
(refuses in production).

## 6. Seed

```bash
docker compose run --rm seed python -m app.seed            # idempotent
docker compose run --rm seed python -m app.seed --check    # verify + exit non-zero on failure
```

Demo dataset (Phase 19 deliverable):

| Role | Email | Password (`SEED_PASSWORD`) |
|---|---|---|
| Platform Admin | `admin@demo.local` | `Demo@12345` |
| Water Officer | `officer.water@demo.local` | same |
| Roads Officer | `officer.roads@demo.local` | same |
| Electrical Officer | `officer.electrical@demo.local` | same |
| Sanitation Officer | `officer.sanitation@demo.local` | same |
| Superintendent | `superintendent@demo.local` | same |
| Citizen 1 / 2 | `citizen1@demo.local` / `citizen2@demo.local` | same |

Departments: Water Supply, Road Maintenance, Electrical, Sanitation.
Categories: Water Leakage, Drainage Blockage, Pothole/Damaged Road, Broken
Streetlight, Road Lighting Repair, Garbage Collection.
Complaints: `CT-2026-100001…100008` cover every P0 status
(SUBMITTED → REOPENED) + **`CT-2026-100009` is the guaranteed overdue
candidate** (ACCEPTED, `resolution_due_at` in the past, `escalated_at` NULL).

Verify the overdue candidate:

```bash
docker compose exec db mysql -u$MYSQL_USER -p$MYSQL_PASSWORD -D$MYSQL_DATABASE \
  -e "SELECT complaint_number,status,accepted_at,resolution_due_at,escalated_at FROM complaints WHERE complaint_number='CT-2026-100009';"
```

## 7. Trigger escalation

```bash
./scripts/trigger-escalation.sh
# → docker compose exec worker python -c "from app.worker import run_escalation_check; run_escalation_check()"
# → docker compose logs --tail=30 worker   (event=escalation_run, evaluated/escalated/skipped)
```

The scheduled worker runs every `ESCALATION_CHECK_SECONDS`
(60 s prod/dev, 30 s demo) plus one run at startup. Until Phase 11 lands the
token-protected `POST /internal/escalations/run` endpoint, the script calls the
same function the scheduler calls. Once live, prefer:

```bash
curl -X POST http://localhost:8000/api/v1/internal/escalations/run \
  -H "X-Internal-Token: $INTERNAL_TRIGGER_TOKEN"
```

## 8. Rotate the JWT secret

1. Generate: `python -c "import secrets; print(secrets.token_urlsafe(48))"`
2. Set `JWT_SECRET` in `.env` to the new value.
3. `docker compose up -d --force-recreate api worker`
   (web needs no rebuild — secrets are server-side only).
4. Every existing token is invalidated (8 h lifetime); users log in again.
   Coordinate with a quiet window if sessions matter.

The internal trigger token is rotated the same way (`INTERNAL_TRIGGER_TOKEN`).

## 9. Backups & restore (DEP-010)

**What is backed up:** full MySQL dump + `civictrack_uploads` tarball.
**Retention:** keep 30 days (append-only; never hard-delete complaint data, NFR-019).
Store backups off-host (object storage / rsync) — local `./backups/` is not a
disaster plan.

```bash
./scripts/backup.sh [./backups]           # bash
.\scripts\backup.ps1 [-OutputDir .\backups]  # PowerShell
# → backups/civictrack_db_<UTC-stamp>.sql.gz + backups/civictrack_uploads_<UTC-stamp>.tar.gz
```

Restore (overwrites the DB; asks for confirmation without `--yes`):

```bash
./scripts/restore.sh <db_dump.sql.gz> [uploads.tar.gz] [--yes]
.\scripts\restore.ps1 -DbFile <db_dump.sql.gz> [-UploadFile <uploads.tar.gz>] [-Yes]
```

Restore stops `api/worker/web`, imports the dump, restores uploads, re-runs
`migrate`, runs `seed --check`, and restarts the stack. Verify with
`curl http://localhost:8000/health/ready` and the seed-check output.

> Restore drill (acceptance): backup → `docker compose down` →
> `docker compose up -d db` → `./scripts/restore.sh … --yes` → confirm
> `CT-2026-100009` still present and `/health/ready` is green.

## 10. Health & observability (DEP-011)

| Probe | Meaning | Command |
|---|---|---|
| `GET /health` | liveness (process up) | `curl http://localhost:8000/health` |
| `GET /health/ready` | readiness (DB reachable) | `curl http://localhost:8000/health/ready` |
| `docker compose ps` | container health (`healthy`) | — |
| Worker logs | scheduled runs + demo banner | `docker compose logs -f worker` |
| API logs | startup `demo_mode` / window + request IDs | `docker compose logs -f api` |

- **Verify prod default (AC-16):** with production `.env`,
  `docker compose logs api | grep escalation_window_minutes` shows `10080`
  and `demo_mode=False`.
- **Log aggregation:** all services log structured lines to stdout via the
  `json-file` driver (`max-size 10m`, `max-file 3`). Ship to your aggregator
  with Vector/Fluent Bit `docker` input or `docker compose logs --json` collectors.
  No PII/tokens are logged (NFR-021). Filter example:
  `docker compose logs api | grep 'event=escalation'`.

## 11. Troubleshooting

| Symptom | Check |
|---|---|
| `docker compose up` fails at `migrate` | `docker compose logs migrate` — migration errors exit non-zero; dependents never start. Fix the error, then `docker compose up -d --build`. |
| `api` unhealthy, `/health/ready` = 503 | MySQL down or wrong `DATABASE_URL`. `docker compose logs db api`; confirm `db` is `healthy` in `ps`. |
| Wrong escalation window | Window ≠ 10080 without `ALLOW_DEMO_ESCALATION=true` is reverted. Check `.env` + `logs api` for the `Non-default … reverting` error. |
| Prod refuses to boot | `ENVIRONMENT=production` + placeholder secrets/demo flag. Replace `CHANGE_ME` values; `ALLOW_DEMO_ESCALATION=false`. |
| Demo banner missing | Rebuild `web` after changing `VITE_ALLOW_DEMO_ESCALATION` (baked at build time): `docker compose build web && docker compose up -d web`. |
| Port already in use (3306/8000/8080) | Stop the other process or edit published ports in `docker-compose.yml`. |
| Worker logs silent | Worker starts after `migrate`. `docker compose logs worker`; confirm `event=worker_start` + interval runs. |
| Seed check fails for `CT-2026-100009` | Re-seed: `docker compose run --rm seed python -m app.seed`. If still failing, `reset` (demo only). |
| Data lost after `down -v` | Expected — `-v` deletes named volumes. Restore from backup (§9). |

## 12. 5-minute demo script (happy path)

1. Open `http://localhost:8080`, log in as `citizen1@demo.local`.
2. Show My Complaints → open `CT-2026-100009` (Accepted, overdue).
3. Log in as `officer.roads@demo.local` → Department Queue → note overdue badge.
4. Run `./scripts/trigger-escalation.sh` (demo) or wait ≤60 s (prod worker).
5. Log in as `superintendent@demo.local` → Escalation Queue → show the newly escalated complaint.
6. Resolve it, then log in as the citizen → show RESOLVED + notification.
7. Mention the banner: “Demo window is 2 minutes here; production is 10,080 (7 days).”

## 13. Fresh-clone verification (GATE)

Run on a clean machine **by someone other than the author** and tick each box:

- [ ] `git clone` → copy `.env` from the right template → `docker compose up -d --build` → all services `healthy` in `ps`.
- [ ] `curl /health` and `/health/ready` both green; worker logs show a scheduled run.
- [ ] Seed + `--check` pass; `CT-2026-100009` is ACCEPTED with a past deadline.
- [ ] `docker compose restart` (or `down`/`up` without `-v`) → data + uploads survive.
- [ ] Backup → restore drill → `/health/ready` green after restore.
- [ ] Demo `.env` shows the banner; production `.env` shows worker/API logs with `10080` + `demo_mode=False`.
- [ ] `./scripts/trigger-escalation.sh` (or cron/manual run) visibly moves the queue.

---

*Phase 19 files: `docker-compose.yml`, `docker-compose.prod.yml`,
`backend/Dockerfile`, `frontend/Dockerfile`, `scripts/`, this file, `README.md`.*
