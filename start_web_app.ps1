# Streamlit web app (use in PowerShell: .\start_web_app.ps1)
Set-Location $PSScriptRoot

$py = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    $py = "py"
}

Write-Host "========================================"
Write-Host "  Streamlit Web App"
Write-Host "========================================"
Write-Host ""
Write-Host "Open in browser: http://localhost:8501"
Write-Host ""

& $py -m streamlit run (Join-Path $PSScriptRoot "web\streamlit_app.py") `
    --server.headless true `
    --server.port 8501
