@echo off
cd /d "%~dp0"

echo ========================================
echo   Streamlit Web App
echo ========================================
echo.
echo URL: http://localhost:8501
echo Keep this window open while using the web app.
echo.

if exist ".venv\Scripts\python.exe" (
    set "PY=.venv\Scripts\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PY=py"
    ) else (
        echo [ERROR] Python not found. Run start_gui.bat setup first.
        pause
        exit /b 1
    )
)

"%PY%" -m streamlit run web\streamlit_app.py --server.headless true --server.port 8501
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start. Try:
    echo   .venv\Scripts\pip install streamlit plotly pandas
    echo.
)

pause
