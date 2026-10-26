# ==============================================================================
# GQT HRMS & Recruitment CRM — Local Development Bootstrap Script (Windows)
# ==============================================================================
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_dev.ps1
# ==============================================================================

Write-Host ">>> [1/5] Initializing GQT HRMS Development Environment..." -ForegroundColor Cyan

# Step 1: Ensure .env exists from template
if (-not (Test-Path ".env")) {
    Write-Host ">>> Creating .env from .env.example template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host ">>> Created .env. Please review database and environment settings." -ForegroundColor Green
} else {
    Write-Host ">>> Existing .env found." -ForegroundColor Green
}

# Step 2: Backend Virtual Environment
Write-Host ">>> [2/5] Setting up Python virtual environment in backend\.venv..." -ForegroundColor Cyan
if (-not (Test-Path "backend\.venv")) {
    python -m venv backend\.venv
}

$PYTHON = "backend\.venv\Scripts\python.exe"
& $PYTHON -m pip install --upgrade pip
& $PYTHON -m pip install -r backend\requirements.txt

# Step 3: Database Migrations
Write-Host ">>> [3/5] Applying Django migrations..." -ForegroundColor Cyan
Push-Location backend
& "..\$PYTHON" manage.py migrate
Pop-Location

# Step 4: Frontend NPM Installation
Write-Host ">>> [4/5] Installing frontend NPM dependencies..." -ForegroundColor Cyan
Push-Location frontend
npm install
Pop-Location

# Step 5: Verification
Write-Host ">>> [5/5] Running verification checks..." -ForegroundColor Cyan
powershell -ExecutionPolicy Bypass -File scripts\verify_dev.ps1

Write-Host "`n>>> GQT HRMS Setup Complete! Ready for development." -ForegroundColor Green
Write-Host "Run Backend:  powershell -File scripts\run_backend.ps1" -ForegroundColor Yellow
Write-Host "Run Frontend: powershell -File scripts\run_frontend.ps1" -ForegroundColor Yellow
