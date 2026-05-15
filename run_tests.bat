@echo off
REM 統一測試執行腳本

set "VENV_PYTHON=C:\Users\Administrator\Downloads\PythonProject2-master\PythonProject2-master\.venv\Scripts\python.exe"
set "TEST_SCRIPT=C:\Users\Administrator\Downloads\PythonProject2-master\PythonProject2-master\tests\run_tests.py"

echo ========================================
echo 🧪 正在啟動統一測試系統...
echo ========================================

if exist "%VENV_PYTHON%" (
    "%VENV_PYTHON%" "%TEST_SCRIPT%"
) else (
    echo ❌ 錯誤: 找不到虛擬環境 Python (%VENV_PYTHON%)
    echo 請確保您已在專案目錄下建立了 .venv
    pause
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ⚠️ 測試完成，但部分測試未通過 (Exit Code: %ERRORLEVEL%)
) else (
    echo.
    echo ✅ 所有測試執行完畢
)

pause
