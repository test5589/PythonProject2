# 創建的腳本和指令清單

## 🔧 AI創建的腳本清單

### 📊 分析和檢測腳本
1. **file_classification_analysis.py** 
   - 位置: `ai_testing/debug/`
   - 功能: 分析和分類所有Python文件
   - 用途: 文件組織和重構建議

2. **utils_analysis.py**
   - 位置: `ai_testing/debug/`
   - 功能: 分析utils資料夾結構
   - 用途: 模組重組建議

3. **docs_reorganization.py**
   - 位置: `ai_testing/debug/`
   - 功能: 分析docs資料夾結構
   - 用途: 文檔整理建議

4. **logs_optimization.py**
   - 位置: `ai_testing/debug/`
   - 功能: 分析日誌文件結構
   - 用途: 日誌管理優化

### 🧪 測試腳本
1. **test_api_fix.py**
   - 位置: `ai_testing/tests/`
   - 功能: 測試API修復效果
   - 用途: 驗證API相關修復

2. **test_all_fixes.py**
   - 位置: `ai_testing/tests/`
   - 功能: 測試所有修復項目
   - 用途: 全面驗證系統修復

3. **test_final_improvements.py**
   - 位置: `ai_testing/tests/`
   - 功能: 測試最終改善項目
   - 用途: 驗證系統優化效果

4. **test_fixes.py**
   - 位置: `ai_testing/tests/`
   - 功能: 基礎修復測試
   - 用途: 基本功能驗證

5. **test_optimizations.py**
   - 位置: `ai_testing/tests/`
   - 功能: 優化項目測試
   - 用途: 性能優化驗證

6. **test_weight_system.py**
   - 位置: `ai_testing/tests/`
   - 功能: 權重系統測試
   - 用途: 權重測試功能驗證

7. **capacity_test.py**
   - 位置: `ai_testing/tests/`
   - 功能: API容量測試
   - 用途: 測試API獲取能力

8. **advanced_capacity_test.py**
   - 位置: `ai_testing/tests/`
   - 功能: 進階容量測試
   - 用途: 深度API測試

9. **final_test.py**
   - 位置: `ai_testing/tests/`
   - 功能: 最終綜合測試
   - 用途: 系統整體驗證

10. **check_db.py**
    - 位置: `ai_testing/tests/`
    - 功能: 數據庫檢查
    - 用途: 數據庫狀態驗證

11. **test_db_view.py**
    - 位置: `ai_testing/tests/`
    - 功能: 數據庫視圖測試
    - 用途: 數據庫功能測試

### 🔧 工具腳本
1. **update_api_field.py**
   - 位置: `tools/`
   - 功能: 更新API欄位
   - 用途: API配置維護

2. **force_error_log.py**
   - 位置: `tools/`
   - 功能: 強制錯誤日誌
   - 用途: 錯誤日誌測試

3. **api_weight_evaluator.py**
   - 位置: `tools/`
   - 功能: API權重評估
   - 用途: API權重分析

### 🔍 調試工具
1. **debug_gui_crash.py**
   - 位置: `ai_testing/debug/`
   - 功能: GUI崩潰調試
   - 用途: GUI問題診斷

2. **fix_summary.py**
   - 位置: `ai_testing/debug/`
   - 功能: 修復總結報告
   - 用途: 修復過程記錄

## 🛠️ 常用指令清單

### 📁 資料夾管理指令
```bash
# 創建資料夾結構
mkdir tools
mkdir archive
mkdir archive\backup_files
mkdir ai_testing
mkdir ai_testing\tests
mkdir ai_testing\debug

# 移動文件到對應資料夾
move *.py target_folder\
move test_*.py ai_testing\tests\
move debug_*.py ai_testing\debug\
move *_backup.py archive\backup_files\
```

### 🧹 清理指令
```bash
# 清理空文件
for /f %i in ('dir /b /s *.py') do if %~zi==0 del "%i"

# 清理日誌文件
del data\logs\*.log
del logs\*.log

# 清理臨時文件
del *.tmp
del *.temp
rmdir /s /q __pycache__
```

### 🔍 檢查指令
```bash
# 檢查文件大小
dir /s *.py | find "bytes"

# 檢查空文件
for /f %i in ('dir /b /s *.py') do if %~zi==0 echo Empty: %i

# 檢查重複文件
dir /b *backup*.py
dir /b *original*.py
dir /b *fixed*.py
```

### 🧪 測試指令
```bash
# 運行測試腳本
python ai_testing\tests\test_all_fixes.py
python ai_testing\tests\test_final_improvements.py
python ai_testing\tests\capacity_test.py

# 運行分析腳本
python ai_testing\debug\file_classification_analysis.py
python ai_testing\debug\utils_analysis.py
python ai_testing\debug\logs_optimization.py
```

### 🚀 啟動指令
```bash
# 啟動GUI
python core\gui_main.py

# 啟動Web應用
streamlit run web\streamlit_app.py

# 啟動測試
python -m pytest ai_testing\tests\
```

## 📋 日誌清理腳本

### 自動清理腳本 (cleanup_logs.py)
```python
#!/usr/bin/env python3
"""
日誌清理腳本
"""
import os
import glob
import gzip
import shutil
from datetime import datetime, timedelta

def cleanup_logs():
    """清理日誌文件"""
    log_dir = "data/logs"
    
    # 1. 刪除空文件
    for log_file in glob.glob(os.path.join(log_dir, "**/*.log"), recursive=True):
        if os.path.getsize(log_file) == 0:
            os.remove(log_file)
            print(f"刪除空文件: {log_file}")
    
    # 2. 壓縮大文件
    for log_file in glob.glob(os.path.join(log_dir, "**/*.log"), recursive=True):
        if os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
            with open(log_file, 'rb') as f_in:
                with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(log_file)
            print(f"壓縮文件: {log_file}")
    
    # 3. 刪除舊文件
    cutoff_date = datetime.now() - timedelta(days=30)
    for log_file in glob.glob(os.path.join(log_dir, "**/*.log*"), recursive=True):
        if os.path.getmtime(log_file) < cutoff_date.timestamp():
            os.remove(log_file)
            print(f"刪除舊文件: {log_file}")

if __name__ == "__main__":
    cleanup_logs()
```

### 使用方法
```bash
# 創建清理腳本
echo "上述Python代碼" > scripts\cleanup_logs.py

# 運行清理
python scripts\cleanup_logs.py

# 設定定期清理 (Windows Task Scheduler)
schtasks /create /tn "LogCleanup" /tr "python C:\path\to\cleanup_logs.py" /sc daily
```

## 🔧 GUI調試指令

### GUI問題診斷
```bash
# 檢查GUI啟動問題
python core\gui_main.py

# 調試GUI崩潰
python ai_testing\debug\debug_gui_crash.py

# 檢查GUI控制器
python -c "from core.gui_controls import GUIControls; print('GUI Controls OK')"
```

### GUI修復指令
```bash
# 備份GUI文件
copy core\gui_controls.py core\gui_controls_backup.py

# 恢復GUI文件
copy archive\backup_files\gui_controls_original.py core\gui_controls.py

# 測試GUI修復
python ai_testing\tests\test_gui_fixes.py
```

## 📊 系統維護指令

### 定期維護
```bash
# 每日維護
python scripts\cleanup_logs.py
python ai_testing\tests\test_all_fixes.py

# 每週維護
python ai_testing\debug\file_classification_analysis.py
python ai_testing\debug\utils_analysis.py

# 每月維護
python ai_testing\debug\logs_optimization.py
python ai_testing\debug\docs_reorganization.py
```

### 系統檢查
```bash
# 檢查系統狀態
python -c "import sys; print(f'Python: {sys.version}')"
python -c "import modules.utils.database as db; print('Database OK')"
python -c "from core.gui_main import MainGUI; print('GUI OK')"

# 檢查依賴
pip list
pip check
```

---

*此清單包含所有AI創建的腳本和常用指令，用於系統維護和開發*
