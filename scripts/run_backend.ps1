# ==============================================================================
# GQT HRMS — Start Backend Development Server (Django)
# ==============================================================================

Write-Host ">>> Starting GQT HRMS Backend API Server on http://127.0.0.1:8000..." -ForegroundColor Cyan
Write-Host ">>> OpenAPI Swagger Docs: http://127.0.0.1:8000/api/v1/schema/swagger/" -ForegroundColor Gray

Push-Location backend
& ".\.venv\Scripts\python.exe" manage.py runserver 127.0.0.1:8000
Pop-Location
