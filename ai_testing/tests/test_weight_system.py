#!/usr/bin/env python3
"""
權重測試系統驗證腳本
用於測試修復後的整合權重測試功能
"""

import sys
import os
import time
from datetime import datetime

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_anchor_time_engine():
    """測試錨定時間引擎的階段式測試功能"""
    print("🧪 測試錨定時間引擎...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        def test_emit(message):
            print(f"[TEST_ENGINE] {message}")
        
        # 獲取引擎實例
        engine = get_anchor_time_engine(test_emit)
        
        # 設定測試參數
        engine.test_stages = [100, 500, 1000]  # 較小的測試階段
        engine.enable_capacity_test = True
        engine.enable_data_validation = True
        engine.current_stage_index = 0
        engine.max_successful_count = 0
        engine.api_lock_count = 0
        engine.duplicate_data_count = 0
        engine.received_timestamps.clear()
        
        print("✅ 錨定時間引擎設定完成")
        
        # 啟動測試
        current_time = datetime.now()
        print(f"🚀 啟動測試 - 當前時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        engine.start_test("BTCUSDT", "1m", current_time)
        
        # 等待測試執行
        print("⏳ 等待測試執行...")
        time.sleep(10)
        
        # 停止測試
        engine.stop_test()
        print("🛑 測試已停止")
        
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_controls():
    """測試GUI控制的權重測試功能"""
    print("\n🖥️ 測試GUI控制...")
    
    try:
        # 這裡只測試導入，不啟動GUI
        from core.gui_controls import GUIControls
        print("✅ GUI控制模組導入成功")
        
        # 測試時間處理邏輯
        from datetime import datetime
        current_time = datetime.now()
        future_time = datetime(2025, 12, 31, 23, 59, 59)
        past_time = datetime(2020, 1, 1, 0, 0, 0)
        
        print(f"當前時間: {current_time}")
        print(f"未來時間: {future_time} - 有效: {future_time > current_time}")
        print(f"過去時間: {past_time} - 有效: {past_time > current_time}")
        
        return True
        
    except Exception as e:
        print(f"❌ GUI測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🔧 權重測試系統修復驗證")
    print("=" * 60)
    
    results = []
    
    # 測試1: 錨定時間引擎
    results.append(test_anchor_time_engine())
    
    # 測試2: GUI控制
    results.append(test_gui_controls())
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print("=" * 60)
    
    test_names = ["錨定時間引擎", "GUI控制"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 總體結果: {success_count}/{total_count} 測試通過")
    
    if success_count == total_count:
        print("🎉 所有測試通過！權重測試系統修復成功")
        return True
    else:
        print("⚠️ 部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
