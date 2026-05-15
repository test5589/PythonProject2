@echo off
chcp 65001 >nul
REM Start both backend and frontend
echo ========================================
echo Web Charting Full Application Startup
echo ========================================
echo.
echo Starting backend and frontend...
echo.
echo Backend API: http://localhost:8001
echo Frontend App: http://localhost:5173
echo API Documentation: http://localhost:8001/docs
echo.

REM Start backend in new window
start "Web Charting Backend" cmd /k "cd /d %~dp0 && start_backend_safe.bat"

REM Wait 2 seconds for backend to start
timeout /t 2 /nobreak > nul

REM Start frontend in new window
start "Web Charting Frontend" cmd /k "cd /d %~dp0 && start_frontend.bat"

echo.
echo [OK] Backend and frontend started!
echo.
echo Please wait a few seconds for services to fully start
echo Then visit: http://localhost:5173
echo.

pause
