@echo off
cd /d "%~dp0"

echo ========================================
echo   Web Charting (TradingView-style K-line)
echo ========================================
echo.
echo Chart page:  http://localhost:5173
echo Backend API: http://localhost:8001/docs
echo.
echo NOTE: This is NOT start_web_app.bat (Streamlit on port 8501)
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] .venv not found. Run setup from start_gui.bat first.
    pause
    exit /b 1
)

if not exist "C:\Program Files\nodejs\npm.cmd" (
    where npm >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Node.js / npm not installed.
        echo Download: https://nodejs.org/  (LTS version)
        echo After install, close and reopen Cursor, then run this script again.
        echo.
        pause
        exit /b 1
    )
)

cd web_charting
call start_all.bat
