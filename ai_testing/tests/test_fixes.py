#!/usr/bin/env python3
"""
test_fixes.py - 測試所有修復結果
"""

import os
import sys
import subprocess
from datetime import datetime

# 專案根目錄
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def test_api_weight_evaluator():
    """測試 API 權重評估器 emoji 修復"""
    print("🧪 測試 API 權重評估器 emoji 修復...")
    try:
        from modules.api_weight_evaluator import get_api_weight_evaluator
        evaluator = get_api_weight_evaluator()
        evaluator.reset_all()
        print("✅ API 權重評估器 emoji 修復成功")
        return True
    except Exception as e:
        print(f"❌ API 權重評估器測試失敗: {e}")
        return False

def test_symbol_selection():
    """測試貨幣對選擇功能"""
    print("🧪 測試貨幣對選擇功能...")
    try:
        import tkinter as tk
        from core.feature_panel import FeaturePanel
        
        # 建立測試視窗
        root = tk.Tk()
        root.withdraw()  # 隱藏視窗
        
        # 模擬 main_gui
        class MockMainGUI:
            def __init__(self):
                self.symbol_entry = tk.Entry(root)
        
        mock_gui = MockMainGUI()
        # 修正：傳入正確的參數 (root, main_gui)
        panel = FeaturePanel(root, mock_gui)
        
        # 測試選擇功能
        panel.symbol_combobox.set("BTCUSDT")
        panel._on_symbol_select(None)
        
        if mock_gui.symbol_entry.get() == "BTCUSDT":
            print("✅ 貨幣對選擇功能正常")
            root.destroy()
            return True
        else:
            print("❌ 貨幣對選擇功能異常")
            root.destroy()
            return False
            
    except Exception as e:
        print(f"❌ 貨幣對選擇測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_log_files():
    """檢查日誌檔案狀態"""
    print("🧪 檢查日誌檔案狀態...")
    
    # 檢查 test_error.log
    test_log_path = os.path.join(PROJECT_ROOT, "data", "test_error.log")
    if os.path.exists(test_log_path):
        size = os.path.getsize(test_log_path)
        print(f"✅ test_error.log 存在，大小: {size} bytes")
    else:
        print("❌ test_error.log 不存在")
        return False
    
    # 檢查清理後的 logs 目錄
    logs_dir = os.path.join(PROJECT_ROOT, "data", "logs")
    if os.path.exists(logs_dir):
        log_files = [f for f in os.listdir(logs_dir) if f.endswith('.log')]
        print(f"✅ logs 目錄清理完成，剩餘 {len(log_files)} 個日誌檔案")
        for f in log_files[:5]:  # 只顯示前5個
            print(f"   - {f}")
    else:
        print("❌ logs 目錄不存在")
        return False
    
    return True

def main():
    """主測試函數"""
    print("🔧 開始測試所有修復結果...")
    print("=" * 50)
    
    results = []
    
    # 測試各個修復
    results.append(("API 權重評估器 emoji 修復", test_api_weight_evaluator()))
    results.append(("貨幣對選擇功能", test_symbol_selection()))
    results.append(("日誌檔案狀態", check_log_files()))
    
    # 總結結果
    print("=" * 50)
    print("📊 測試結果總結:")
    
    success_count = 0
    for test_name, success in results:
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"   {test_name}: {status}")
        if success:
            success_count += 1
    
    print(f"\n🎯 總體結果: {success_count}/{len(results)} 個測試通過")
    
    if success_count == len(results):
        print("🎉 所有修復都成功！")
    else:
        print("⚠️ 還有部分問題需要解決")

if __name__ == "__main__":
    main()
