# CivicTrack backup (PowerShell) - MySQL dump + uploads tarball (19.5, DEP-010).
# Usage:  .\scripts\backup.ps1 [-OutputDir .\backups]
# File-based (no binary pipes through PowerShell, which corrupt gzip data):
# mysqldump -> tmp.sql -> alpine gzip (file I/O) -> .sql.gz
param([string]$OutputDir = ".\backups")
# docker writes progress to stderr; use Continue + explicit exit-code checks
# (Windows PowerShell 5.1 treats native stderr as error with Stop).
$ErrorActionPreference = "Continue"

if (-not (Test-Path .env)) { throw ".env not found - copy .env.example to .env first." }
$envMap = @{}
Get-Content .env | ForEach-Object {
  if ($_ -match '^\s*([^#\s=]+)\s*=\s*(.*)\s*$') { $envMap[$Matches[1]] = $Matches[2] }
}
$DbUser = if ($envMap.MYSQL_USER) { $envMap.MYSQL_USER } else { "civictrack" }
$DbPass = $envMap.MYSQL_PASSWORD
$DbName = if ($envMap.MYSQL_DATABASE) { $envMap.MYSQL_DATABASE } else { "civictrack" }
if (-not $DbPass) { throw "MYSQL_PASSWORD is required (set in .env)." }

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
$Stamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$TmpSql = Join-Path $OutputDir "tmp_$Stamp.sql"
$DbFile = Join-Path $OutputDir "civictrack_db_$Stamp.sql.gz"
$UploadFile = Join-Path $OutputDir "civictrack_uploads_$Stamp.tar.gz"
$BackupsAbs = (Resolve-Path $OutputDir).Path

Write-Host "[backup] dumping MySQL -> $DbFile"
# --no-tablespaces: the app DB user lacks PROCESS (MySQL 8.4 dumps tablespace
# metadata by default). SQL is text, so PowerShell redirection is safe here.
# cmd redirection (not PowerShell '>') to avoid UTF-16LE BOM / NUL bytes.
cmd /c "docker exec civictrack_db mysqldump --no-tablespaces -u$DbUser -p$DbPass $DbName > `"$TmpSql`""
if ($LASTEXITCODE -ne 0) { throw "mysqldump failed (exit $LASTEXITCODE)" }
# Compress via file I/O in alpine (never pipe binary through PowerShell).
docker run --rm -v "${BackupsAbs}:/b" alpine sh -c "cd /b && gzip -c tmp_$Stamp.sql > civictrack_db_$Stamp.sql.gz"
if ($LASTEXITCODE -ne 0) { throw "gzip failed (exit $LASTEXITCODE)" }
Remove-Item $TmpSql -ErrorAction SilentlyContinue
Write-Host "[backup] dumping uploads volume -> $UploadFile"
docker run --rm -v civictrack_uploads:/src:ro -v "${BackupsAbs}:/dst" alpine tar czf "/dst/civictrack_uploads_$Stamp.tar.gz" -C /src .
if ($LASTEXITCODE -ne 0) { throw "uploads tar failed (exit $LASTEXITCODE)" }
Get-Item $DbFile, $UploadFile | Format-Table Name, Length
Write-Host "[backup] restore with: .\scripts\restore.ps1 -DbFile $DbFile -UploadFile $UploadFile"
