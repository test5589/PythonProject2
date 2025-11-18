@echo off
REM 啟動交易資料視覺化Web應用
REM 這個腳本會啟動Streamlit web服務器，提供資料來源分析和缺口視覺化功能

cd /d "%~dp0"

echo 🚀 正在啟動交易資料視覺化Web應用...
echo 📊 應用功能：
echo    - 資料來源分佈視覺化
echo    - 資料缺口分析
echo    - 秒級資料完整性檢查
echo    - 即時除錯日誌
echo.
echo 🌐 應用將在以下地址啟動：
echo    http://localhost:8501
echo.
echo 💡 使用提示：
echo    - 在瀏覽器中開啟上述地址
echo    - 在側邊欄選擇交易對和時間範圍
echo    - 使用不同頁籤查看各種分析
echo.

python -m streamlit run web/streamlit_app.py --server.headless true --server.port 8501

echo.
echo 📋 如果應用沒有自動開啟瀏覽器，請手動在瀏覽器中訪問：
echo    http://localhost:8501
echo.
pause
