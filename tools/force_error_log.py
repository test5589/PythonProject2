#!/usr/bin/env python3
"""
force_error_log.py - 強制錯誤日誌記錄工具
當 GUI 當機時，確保錯誤被記錄到檔案
"""

import sys
import os
import traceback
from datetime import datetime

# 專案根目錄
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

def setup_error_logging():
    """設定全域錯誤捕捉"""
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """全域異常處理器"""
        error_msg = f"""
{'='*60}
時間: {datetime.now()}
類型: {exc_type.__name__}
錯誤: {exc_value}
{'='*60}
詳細堆疊:
{traceback.format_exc()}
{'='*60}
"""
        
        # 寫入多個位置確保記錄
        log_paths = [
            os.path.join(PROJECT_ROOT, "data", "crash_log.txt"),
            os.path.join(PROJECT_ROOT, "data", "logs", "crash.log"),
            os.path.join(PROJECT_ROOT, "gui_crash.log")
        ]
        
        for log_path in log_paths:
            try:
                os.makedirs(os.path.dirname(log_path), exist_ok=True)
                with open(log_path, "a", encoding="utf-8") as f:
                    f.write(error_msg)
            except:
                pass
        
        # 也輸出到終端機
        print(error_msg)
    
    # 設定全域異常處理器
    sys.excepthook = handle_exception

def test_gui_with_logging():
    """測試 GUI 並強制記錄錯誤"""
    print("🔧 設定強制錯誤日誌...")
    setup_error_logging()
    
    print("🚀 啟動 GUI (所有錯誤將被記錄)...")
    try:
        # 設定環境變數確保 UTF-8
        os.environ['PYTHONIOENCODING'] = 'utf-8'
        
        # 匯入並啟動 GUI
        from core.gui_main import MainGUI
        import tkinter as tk
        
        root = tk.Tk()
        gui = MainGUI(root)
        root.mainloop()
        
    except Exception as e:
        print(f"❌ GUI 啟動失敗: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_gui_with_logging()
