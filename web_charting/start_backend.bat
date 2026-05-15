@echo off
chcp 65001 >nul
REM Web Charting Backend Startup Script
echo ========================================
echo Web Charting Backend Starting...
echo ========================================
echo.

REM Change to backend directory
cd /d "%~dp0backend"

REM Note: Not using virtual environment for now
REM Using global Python installation
REM If you want to use venv, install dependencies first:
REM   pip install -r requirements.txt

REM Start FastAPI
echo Starting FastAPI server...
echo API Documentation: http://localhost:8001/docs
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 8001 --reload

pause
