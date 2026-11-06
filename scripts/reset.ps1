# Full demo reset (PowerShell): tear down volumes, rebuild, migrate, seed (19.4).
# WARNING: deletes the local DB + uploads volumes. Never run in production.
Write-Host "[reset] stopping stack and deleting volumes (DESTRUCTIVE)..."
docker compose down -v --remove-orphans
Write-Host "[reset] rebuilding and starting..."
docker compose up -d --build
Write-Host "[reset] seeding demo data (idempotent)..."
docker compose run --rm seed python -m app.seed
Write-Host "[reset] verifying overdue candidate..."
docker compose run --rm seed python -m app.seed --check
Write-Host "[reset] done. Open http://localhost:8080 and log in with a demo account."
