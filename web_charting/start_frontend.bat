@echo off
chcp 65001 >nul
REM Web Charting Frontend Startup Script
echo ========================================
echo Web Charting Frontend Starting...
echo ========================================
echo.

REM Change to frontend directory
cd /d "%~dp0frontend"

REM Check if node_modules exists
if not exist "node_modules\" (
    echo First run, installing dependencies...
    echo.
    call npm install
    echo.
    echo Dependencies installed!
    echo.
)

REM Start development server
echo Starting Vite development server...
echo Frontend App: http://localhost:5173
echo.

npm run dev

pause
