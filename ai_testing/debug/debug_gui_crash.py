#!/usr/bin/env python3
"""
debug_gui_crash.py - GUI 當機問題診斷工具
用於分析和監控 GUI 當機原因
"""

import os
import sys
import time
import subprocess
from datetime import datetime

# 專案根目錄
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def check_log_files():
    """檢查所有相關日誌檔案"""
    print("🔍 === 檢查日誌檔案 ===")
    
    # 檢查 data 目錄下的日誌
    data_dir = os.path.join(PROJECT_ROOT, "data", "logs")
    if os.path.exists(data_dir):
        print(f"📁 日誌目錄: {data_dir}")
        for file in os.listdir(data_dir):
            if file.endswith('.log'):
                file_path = os.path.join(data_dir, file)
                size = os.path.getsize(file_path)
                mtime = os.path.getmtime(file_path)
                mtime_str = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M:%S')
                print(f"  📄 {file}: {size} bytes, 修改時間: {mtime_str}")
                
                # 顯示最後幾行
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if lines:
                            print(f"    最後一行: {lines[-1].strip()}")
                except Exception as e:
                    print(f"    ❌ 讀取失敗: {e}")
    
    # 檢查 API 權重日誌
    api_weight_log = os.path.join(PROJECT_ROOT, "data", "api_weight_log.txt")
    if os.path.exists(api_weight_log):
        size = os.path.getsize(api_weight_log)
        print(f"📄 API 權重日誌: {size} bytes")
        with open(api_weight_log, 'r', encoding='utf-8') as f:
            content = f.read()
            if content.strip():
                print(f"    內容: {content.strip()}")
            else:
                print("    內容: 空檔案")

def run_gui_test():
    """執行 GUI 測試"""
    print("\n🚀 === 執行 GUI 測試 ===")
    
    try:
        # 啟動 GUI
        import subprocess
        import sys
        
        # 使用相同的 Python 環境
        python_cmd = sys.executable
        gui_script = os.path.join(os.path.dirname(__file__), "core", "gui_main.py")
        
        print(f"🔧 啟動命令: {python_cmd} {gui_script}")
        print("⏳ 等待 GUI 啟動...")
        
        # 啟動子程序（不創建新視窗，直接在當前終端機運行）
        process = subprocess.Popen(
            [python_cmd, gui_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # 等待 3 秒檢查是否還在運行
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ GUI 成功啟動並正在運行")
            print("📝 測試建議:")
            print("   1. 測試貨幣對選擇功能")
            print("   2. 點擊 '🧪 權重測試模式' 按鈕")
            print("   3. 觀察時間窗口控制是否正常")
            print("   4. 測試 '⏹️ 停止權重測試' 按鈕")
            print("\n⏱️  等待 10 秒後自動終止測試...")
            
            # 等待 10 秒讓用戶看到結果
            for i in range(10, 0, -1):
                print(f"⏳ 剩餘 {i} 秒...", end="\r")
                time.sleep(1)
            print("                        ")  # 清除行
            
        else:
            print("❌ GUI 啟動失敗或立即退出")
            stdout, stderr = process.communicate()
            if stdout:
                print(f"📤 輸出: {stdout}")
            if stderr:
                print(f"📥 錯誤: {stderr}")
        
        # 終止程序
        try:
            process.terminate()
            process.wait(timeout=3)
            print("🛑 GUI 已正常終止")
        except subprocess.TimeoutExpired:
            process.kill()
            print("🔫 GUI 已強制終止")
        except Exception as e:
            print(f"⚠️ 終止 GUI 時發生錯誤: {e}")
            
    except Exception as e:
        print(f"❌ 執行失敗: {e}")
        import traceback
        print(f"詳細錯誤: {traceback.format_exc()}")

def check_dependencies():
    """檢查依賴模組"""
    print("\n📦 === 檢查依賴模組 ===")
    
    modules_to_check = [
        "modules.api_weight_evaluator",
        "modules.utils.database",
        "core.gui_main",
        "core.gui_controls"
    ]
    
    for module in modules_to_check:
        try:
            __import__(module)
            print(f"✅ {module}")
        except Exception as e:
            print(f"❌ {module}: {e}")

def main():
    """主函數"""
    print("🔧 GUI 當機問題診斷工具")
    print("=" * 50)
    
    # 檢查依賴
    check_dependencies()
    
    # 檢查日誌檔案
    check_log_files()
    
    # 執行 GUI 測試
    run_gui_test()
    
    # 再次檢查日誌
    print("\n🔍 === 測試後日誌檢查 ===")
    check_log_files()
    
    print("\n✅ 診斷完成")

if __name__ == "__main__":
    main()
