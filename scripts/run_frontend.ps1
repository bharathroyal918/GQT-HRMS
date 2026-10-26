# ==============================================================================
# GQT HRMS — Start Frontend Development Server (Vite)
# ==============================================================================

Write-Host ">>> Starting GQT HRMS Frontend Web Server on http://localhost:5173..." -ForegroundColor Cyan

Push-Location frontend
npm run dev
Pop-Location
