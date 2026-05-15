# PowerShell 統一測試執行腳本

$venvPython = ".\.venv\Scripts\python.exe"
$testScript = ".\tests\run_tests.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🧪 正在啟動統一測試系統 (PowerShell 版)..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if (Test-Path $venvPython) {
    & $venvPython $testScript
} else {
    Write-Host "❌ 錯誤: 找不到虛擬環境 Python ($venvPython)" -ForegroundColor Red
    Write-Host "請確保您已在專案目錄下建立了 .venv" -ForegroundColor Yellow
}

Write-Host "`n按任意鍵繼續..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
