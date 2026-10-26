# GQT HRMS Master Quality & Acceptance Verification Script (Windows)

Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host ' GQT HRMS — Master Foundation Verification Suite (Windows)' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

$TotalFailures = 0

# Check 1: Django System Checks
Write-Host '`n[Check 1/6] Running Django System Checks...' -ForegroundColor Yellow
Push-Location backend
& '.\.venv\Scripts\python.exe' manage.py check
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: Django system check reported issues!' -ForegroundColor Red
    $TotalFailures++
} else {
    Write-Host 'PASS: Django system checks clean.' -ForegroundColor Green
}
Pop-Location

# Check 2: Django Migration Consistency
Write-Host '`n[Check 2/6] Verifying Migration Consistency...' -ForegroundColor Yellow
Push-Location backend
& '.\.venv\Scripts\python.exe' manage.py makemigrations --check --dry-run
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: Pending migrations detected without migration files!' -ForegroundColor Red
    $TotalFailures++
} else {
    Write-Host 'PASS: Zero migration drift detected.' -ForegroundColor Green
}
Pop-Location

# Check 3: Backend Automated Pytest Suite
Write-Host '`n[Check 3/6] Running Backend Pytest Suite...' -ForegroundColor Yellow
Push-Location backend
& '.\.venv\Scripts\python.exe' -m pytest
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: Backend tests failed!' -ForegroundColor Red
    $TotalFailures++
} else {
    Write-Host 'PASS: All backend automated tests passed.' -ForegroundColor Green
}
Pop-Location

# Check 4: Frontend TypeScript Type Checking
Write-Host '`n[Check 4/6] Running Frontend TypeScript Type Check...' -ForegroundColor Yellow
Push-Location frontend
npm run lint
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: Frontend type check reported errors!' -ForegroundColor Red
    $TotalFailures++
} else {
    Write-Host 'PASS: Frontend TypeScript compilation clean.' -ForegroundColor Green
}
Pop-Location

# Check 5: Frontend Vitest Component Tests
Write-Host '`n[Check 5/6] Running Frontend Vitest Component Tests...' -ForegroundColor Yellow
Push-Location frontend
npm test
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: Frontend component tests failed!' -ForegroundColor Red
    $TotalFailures++
} else {
    Write-Host 'PASS: All frontend Vitest tests passed.' -ForegroundColor Green
}
Pop-Location

# Check 6: Frontend Production Build
Write-Host '`n[Check 6/6] Verifying Frontend Production Build...' -ForegroundColor Yellow
Push-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host 'FAIL: Frontend production build failed!' -ForegroundColor Red
    $TotalFailures++
} else {
    Write-Host 'PASS: Frontend production build generated successfully in dist/.' -ForegroundColor Green
}
Pop-Location

Write-Host '`n==========================================================' -ForegroundColor Cyan
if ($TotalFailures -eq 0) {
    Write-Host ' ALL CHECKS PASSED: GQT HRMS Phase 5 (Student Registration & Eligibility Engine) Verified and Ready for Phase 6!' -ForegroundColor Green
} else {
    Write-Host " VERIFICATION FAILED: $TotalFailures check(s) did not pass." -ForegroundColor Red
}
Write-Host '==========================================================' -ForegroundColor Cyan
