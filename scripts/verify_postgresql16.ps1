# ==============================================================================
# GQT HRMS — PostgreSQL 16 Staging Verification Harness (Windows / WSL)
# ==============================================================================
param(
    [string]$DatabaseUrl = $env:POSTGRES_TEST_DATABASE_URL
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " GQT HRMS -- PostgreSQL 16 Staging Verification Harness" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

if (-not $DatabaseUrl) {
    $DatabaseUrl = "postgresql://gqt_hrms_app:gqt_staging_password_secure@localhost:5432/gqt_hrms_staging"
}

$env:DATABASE_URL = $DatabaseUrl
$env:POSTGRES_TEST_DATABASE_URL = $DatabaseUrl
$env:DB_SSLMODE = "require"
$env:USE_SQLITE_FOR_LOCAL_DEV = "False"

Write-Host "`n[Check 1/3] Verifying PostgreSQL Server Connection..." -ForegroundColor Yellow
$py = "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "python"
}

& $py scripts\inspect_pg_schema.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Unable to connect to PostgreSQL 16 instance at $DatabaseUrl" -ForegroundColor Red
    exit 1
}

Write-Host "`n[Check 2/3] Verifying Database Schema and Migration Consistency..." -ForegroundColor Yellow
& $py backend\manage.py makemigrations --check --dry-run
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Migration drift detected." -ForegroundColor Red
    exit 1
}
Write-Host "PASS: Zero schema drift detected." -ForegroundColor Green

Write-Host "`n[Check 3/3] Running PostgreSQL 16 Staging and Concurrency Test Suite..." -ForegroundColor Yellow
& $py -m pytest backend\tests\test_postgresql_staging.py -v --durations=10
if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: PostgreSQL 16 staging tests failed." -ForegroundColor Red
    exit 1
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " ALL POSTGRESQL 16 STAGING CHECKS PASSED SUCCESSFULLY!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
