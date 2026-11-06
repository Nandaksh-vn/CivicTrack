# CivicTrack restore (PowerShell) - verify a backup drill (19.5, DEP-010).
# Usage:  .\scripts\restore.ps1 -DbFile .\backups\civictrack_db_<stamp>.sql.gz [-UploadFile ...] [-Yes]
# File-based (no binary pipes through PowerShell, which corrupt gzip data).
param(
  [Parameter(Mandatory = $true)][string]$DbFile,
  [string]$UploadFile = "",
  [switch]$Yes
)
# docker writes progress to stderr; use Continue + explicit exit-code checks
# (Windows PowerShell 5.1 treats native stderr as error with Stop).
$ErrorActionPreference = "Continue"

if (-not (Test-Path $DbFile)) { throw "Backup file not found: $DbFile" }
if ($UploadFile -and -not (Test-Path $UploadFile)) { throw "Uploads archive not found: $UploadFile" }
if (-not $Yes) {
  $answer = Read-Host "This will OVERWRITE the database from $DbFile. Type 'yes' to continue"
  if ($answer -ne "yes") { Write-Host "Aborted."; exit 1 }
}
if (-not (Test-Path .env)) { throw ".env not found." }
$envMap = @{}
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#\s=]+)\s*=\s*(.*)\s*$') { $envMap[$Matches[1]] = $Matches[2] }
}
$DbUser = if ($envMap.MYSQL_USER) { $envMap.MYSQL_USER } else { "civictrack" }
$DbPass = $envMap.MYSQL_PASSWORD
$DbName = if ($envMap.MYSQL_DATABASE) { $envMap.MYSQL_DATABASE } else { "civictrack" }
$DbAbs = (Resolve-Path $DbFile).Path
$BackupsAbs = Split-Path $DbAbs -Parent
$TmpSql = Join-Path $BackupsAbs "restore_tmp.sql"

Write-Host "[restore] stopping api/worker/web..."
docker compose stop api worker web
Write-Host "[restore] restoring MySQL from $DbFile"
# Decompress via file I/O in alpine, then import the plain .sql file.
docker run --rm -v "${BackupsAbs}:/b" alpine sh -c "cd /b && gunzip -c '$([IO.Path]::GetFileName($DbAbs))' > restore_tmp.sql"
if ($LASTEXITCODE -ne 0) { throw "gunzip failed (exit $LASTEXITCODE)" }
# Import with cmd input redirection (text SQL, avoids PowerShell pipeline issues).
cmd /c "docker exec -i civictrack_db mysql -u$DbUser -p$DbPass $DbName < `"$TmpSql`""
if ($LASTEXITCODE -ne 0) { throw "MySQL import failed (exit $LASTEXITCODE)" }
Remove-Item $TmpSql -ErrorAction SilentlyContinue
if ($UploadFile) {
  Write-Host "[restore] restoring uploads from $UploadFile"
  $UploadName = Split-Path $UploadFile -Leaf
  docker run --rm -v civictrack_uploads:/dst -v "${BackupsAbs}:/backup" alpine sh -c "cd /dst && tar xzf /backup/$UploadName && ls -la"
  if ($LASTEXITCODE -ne 0) { throw "Uploads restore failed (exit $LASTEXITCODE)" }
}
Write-Host "[restore] migrating + verifying..."
docker compose run --rm migrate
if ($LASTEXITCODE -ne 0) { throw "Migration failed (exit $LASTEXITCODE)" }
docker compose run --rm seed python -m app.seed --check
if ($LASTEXITCODE -ne 0) { throw "Seed check failed (exit $LASTEXITCODE)" }
docker compose up -d --build api worker web
Start-Sleep 3
try { Invoke-WebRequest -UseBasicParsing http://localhost:8000/health/ready | Select-Object StatusCode, Content } catch { Write-Warning "[restore] /health/ready not green yet - check: docker compose logs api" }
Write-Host "[restore] complete."
