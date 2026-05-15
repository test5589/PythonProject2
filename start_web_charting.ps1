# TradingView-style chart app (PowerShell)
# Usage: .\start_web_charting.ps1

$root = $PSScriptRoot
$venvPy = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPy)) {
    Write-Host "[ERROR] .venv not found. Install deps first."
    exit 1
}

$npm = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npm) {
    Write-Host "[ERROR] npm not found. Install Node.js from https://nodejs.org/"
    Write-Host "Then reopen terminal and run this script again."
    exit 1
}

Write-Host "Starting backend (port 8001) and frontend (port 5173)..."
Write-Host "Open: http://localhost:5173"
Write-Host ""

$wc = Join-Path $root "web_charting"
Start-Process cmd -ArgumentList "/k", "cd /d `"$wc`" && start_backend_safe.bat"
Start-Sleep -Seconds 3
Start-Process cmd -ArgumentList "/k", "cd /d `"$wc`" && start_frontend.bat"

Write-Host "Two command windows should open. Wait ~10 seconds, then open http://localhost:5173"
