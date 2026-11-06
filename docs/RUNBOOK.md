# CivicTrack — Operations & Incident Runbook

> **File:** `docs/RUNBOOK.md`  
> **Role:** Operational manual for system operators, SREs, and demonstrators  
> **Applies to:** Production, Demo, and Local Development environments  
> **Release:** v1.0.0-p0  

---

## 1. System Architecture & Component Inventory

| Container / Service | Image / Base | Internal Port | Host Port | Purpose | Health Indicator |
|---|---|---|---|---|---|
| `civictrack_db` | `mysql:8.4` | 3306 | 3306 | Relational store (InnoDB, UTC, utf8mb4) | `mysqladmin ping` |
| `civictrack_api` | Python 3.12-slim | 8000 | 8000 | FastAPI REST application & RBAC engine | `GET /api/v1/health` (HTTP 200) |
| `civictrack_worker` | Python 3.12-slim | — | — | Background SLA breach escalation processor | Process liveness (`os.kill(1, 0)`) |
| `civictrack_web` | nginx:1.27-alpine | 80 | 8080 (dev) / 80 (prod) | React SPA host + reverse proxy to `/api/` | `wget -qO- http://localhost/` |

---

## 2. Configuration & Environment Matrix

CivicTrack strictly differentiates between **Development**, **Demo**, and **Production** profiles:

| Variable | Dev Default | Demo Setting | Prod Requirement | Notes |
|---|---|---|---|---|
| `DATABASE_URL` | `sqlite:///./civictrack.db` or MySQL | `mysql+pymysql://...` | `mysql+pymysql://...` | PyMySQL driver with UTC charset |
| `JWT_SECRET_KEY` | Development dummy | Demo secret (≥32 bytes) | Cryptographic 256-bit random hex | Fails closed if < 32 bytes in prod |
| `ALLOW_DEMO_ESCALATION` | `false` | `true` | **`false`** | Fails closed if `true` in production |
| `ESCALATION_WINDOW_MINUTES` | `10080` (7 days) | `5` (demo fast breach) | **`10080`** | Reverts to 10,080 if demo flag is false |
| `INTERNAL_API_TOKEN` | Local dev token | Shared demo token | Strong random 256-bit secret | Required for manual trigger API |
| `MAX_FILE_SIZE_BYTES` | 5242880 (5 MiB) | 5242880 (5 MiB) | 5242880 (5 MiB) | Upload security threshold |
| `MAX_FILES_PER_REQUEST` | 3 | 3 | 3 | Upload request limit |
| `MAX_IMAGES_PER_COMPLAINT` | 10 | 10 | 10 | Case media storage cap |

---

## 3. Standard Operating Procedures (SOP)

### SOP-01: System Startup

#### Local / Development:
```bash
# Start MySQL container
docker compose up -d db

# Run migrations
cd backend && alembic upgrade head

# Run seed data
python -m app.seed

# Start API
uvicorn app.main:app --reload --port 8000

# Start Frontend
cd ../frontend && npm run dev
```

#### Production (Single Command):
```bash
docker compose -f docker-compose.prod.yml up -d
```
*Note: The `migration_seed` service executes `alembic upgrade head && python -m app.seed` before the API and Web services start.*

---

### SOP-02: System Shutdown & Teardown
```bash
# Graceful stop
docker compose down

# Stop and purge volumes (CAUTION: Destroys DB and uploads)
docker compose down -v
```

---

### SOP-03: Demo Dataset Reset & Seeding

CivicTrack includes an idempotent seed script that provisions standard departments, categories, test accounts for all four canonical roles, and complaints in all P0 statuses.

To execute seed:
```bash
# In backend container or virtual environment:
python -m app.seed
```

#### Demo Credentials:
| Role | Email | Password | Department |
|---|---|---|---|
| Platform Admin | `admin@civictrack.local` | `Admin@12345` | Global |
| City Superintendent | `superintendent@civictrack.local` | `Super@12345` | Global Oversight |
| Department Officer | `officer.water@civictrack.local` | `Officer@12345` | Water Supply & Sewage (`WTR`) |
| Department Officer | `officer.roads@civictrack.local` | `Officer@12345` | Roads & Transport (`RDS`) |
| Citizen | `citizen.jane@civictrack.local` | `Citizen@12345` | — |
| Citizen | `citizen.john@civictrack.local` | `Citizen@12345` | — |

---

### SOP-04: SLA Escalation Engine Management

#### Worker Liveness:
The worker loop executes every `ESCALATION_INTERVAL_SECONDS` (default: 60s). It automatically acquires an advisory lock (`civictrack_escalation_worker`), checks for `IN_PROGRESS` complaints past their `resolution_due_at`, creates `escalations` and history records, updates complaint status to `ESCALATED`, and sends `NT-05` notifications.

#### Manual Trigger (Demo / Ad-hoc):
To trigger an immediate escalation run without waiting for the timer:
```bash
curl -X POST http://localhost:8000/api/v1/internal/escalations/trigger \
  -H "X-Internal-Token: ${INTERNAL_API_TOKEN}"
```
Response:
```json
{
  "evaluated": 6,
  "escalated": 1,
  "skipped": 5
}
```

---

### SOP-05: Backup & Disaster Recovery

#### Performing a Backup:
```bash
# Cross-platform Python runner:
python scripts/backup.py --backup-dir ./backups --uploads-dir ./uploads

# Linux/macOS shell helper:
./scripts/backup.sh
```
Produces a timestamped `.tar.gz` bundle containing:
- `manifest.json`: Metadata, timestamp, and version signature.
- `uploads/`: Complete preserved image repository.
- `database.sql`: SQL dump of database state.

#### Restoring from Backup:
```bash
# Restore files and verify manifest:
python scripts/restore.py ./backups/civictrack_backup_YYYYMMDD_HHMMSS.tar.gz --uploads-dir ./uploads

# Linux/macOS shell helper:
./scripts/restore.sh ./backups/civictrack_backup_YYYYMMDD_HHMMSS.tar.gz
```

---

### SOP-06: JWT Secret Rotation

1. Generate new 256-bit cryptographic secret:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
2. Update `JWT_SECRET_KEY` in `.env`.
3. Restart `civictrack_api`:
   ```bash
   docker compose restart api
   ```
4. *Impact:* Active client JWTs issued under the old secret will return `401 Unauthorized`. Users will be redirected to the login screen without state corruption.

---

## 4. Troubleshooting Playbooks

### Issue 1: Database Connection Timeout
- **Symptoms:** API healthcheck fails, logs indicate `OperationalError: Can't connect to MySQL server`.
- **Diagnostic:** Run `docker compose ps` and `docker logs civictrack_db`.
- **Fix:** Ensure MySQL container reports `(healthy)`. Verify `DATABASE_URL` credentials and port mapping.

### Issue 2: Escalations Not Triggering for Demo
- **Symptoms:** Overdue complaint remains in `IN_PROGRESS`.
- **Diagnostic:** Check `.env` configuration. If `ALLOW_DEMO_ESCALATION=false`, the server automatically enforces the mandatory 10,080-minute (7-day) SLA window.
- **Fix:** Set `ALLOW_DEMO_ESCALATION=true` and `ESCALATION_WINDOW_MINUTES=5` in `.env`, then restart the worker.

### Issue 3: Upload Rejection (413 / 422)
- **Symptoms:** Image upload returns `FILE_TOO_LARGE` or `UNSUPPORTED_IMAGE_TYPE`.
- **Diagnostic:** CivicTrack strictly checks magic bytes (JPEG/PNG/WebP only) and maximum 5 MiB file size.
- **Fix:** Check image format and file size. Files over 5 MiB or non-image MIME types are rejected by design (SEC-04).

