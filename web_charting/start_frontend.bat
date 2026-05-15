@echo off
chcp 65001 >nul
REM Web Charting Frontend Startup Script
echo ========================================
echo Web Charting Frontend Starting...
echo ========================================
echo.

REM Change to frontend directory
cd /d "%~dp0frontend"

REM Prefer official Node.js (Cursor terminal may not have npm on PATH)
set "NODE_DIR=C:\Program Files\nodejs"
if exist "%NODE_DIR%\npm.cmd" (
    set "NPM=%NODE_DIR%\npm.cmd"
) else (
    set "NPM=npm"
)

if not exist "node_modules\" (
    echo First run, installing dependencies...
    echo.
    call "%NPM%" install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Install Node.js from https://nodejs.org/
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed!
    echo.
)

echo Starting Vite development server...
echo Frontend App: http://localhost:5173
echo.

call "%NPM%" run dev

pause
