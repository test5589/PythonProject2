@echo off
chcp 65001 >nul
REM Web Charting Backend - Safe Startup Script
echo ========================================
echo Web Charting Backend Starting...
echo ========================================
echo.

REM Locate project root and virtual environment
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
set "BACKEND_DIR=%SCRIPT_DIR%backend"
set "VENV_PY=%PROJECT_ROOT%\.venv\Scripts\python.exe"

if exist "%VENV_PY%" (
    echo Using virtual environment Python: "%VENV_PY%"
    set "PYTHON_EXE=%VENV_PY%"
) else (
    echo [WARNING] .venv not found, using system Python
    set "PYTHON_EXE=python"
)

REM Change to project root directory (for web_charting.backend.main import)
cd /d "%PROJECT_ROOT%"

REM Check if FastAPI is installed
echo Checking dependencies...
"%PYTHON_EXE%" -c "import fastapi" 2>nul
if errorlevel 1 (
    echo.
    echo [WARNING] FastAPI not found!
    echo Installing dependencies...
    echo.
    "%PYTHON_EXE%" -m pip install fastapi uvicorn sqlalchemy pandas numpy python-dotenv pydantic-settings --quiet
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies!
        echo Please run manually:
        echo   pip install -r requirements.txt
        pause
        exit /b 1
    )
    echo [OK] Dependencies installed!
    echo.
)

REM Check if uvicorn is installed
"%PYTHON_EXE%" -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo [WARNING] Uvicorn not found! Installing...
    "%PYTHON_EXE%" -m pip install uvicorn --quiet
)

echo [OK] All dependencies ready!
echo.

REM Start FastAPI
echo Starting FastAPI server...
echo Backend API: http://localhost:8001
echo API Documentation: http://localhost:8001/docs
echo Health Check: http://localhost:8001/health
echo.
echo Press Ctrl+C to stop the server
echo.

"%PYTHON_EXE%" -m uvicorn web_charting.backend.main:app --host 127.0.0.1 --port 8001 --reload

pause
