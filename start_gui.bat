@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   Trading Data Console - GUI
echo ========================================
echo.

if exist ".venv\Scripts\python.exe" (
    set PY=.venv\Scripts\python.exe
    echo 使用虛擬環境: .venv
) else if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
    set PY=%LOCALAPPDATA%\Programs\Python\Python314\python.exe
    echo 使用系統 Python 3.14
) else (
    where python >nul 2>&1
    if not errorlevel 1 (
        set PY=python
        echo 使用系統 Python
    ) else (
        where py >nul 2>&1
        if not errorlevel 1 (
            set PY=py
            echo 使用 py 啟動器
        ) else (
            echo [錯誤] 找不到 Python。請安裝並勾選 Add to PATH：
            echo   https://www.python.org/downloads/
            pause
            exit /b 1
        )
    )
)

echo.
echo 正在啟動主程式 GUI...
echo.
"%PY%" core\gui_main.py
if errorlevel 1 (
    echo.
    echo [錯誤] 啟動失敗。若缺少套件，請先執行：
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

pause
