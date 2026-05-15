#!/usr/bin/env python3
"""
最終測試腳本 - 驗證所有修復和優化
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_complete_system():
    """測試完整的權重測試系統"""
    print("🚀 完整系統測試...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        def test_emit(message):
            print(f"[SYSTEM] {message}")
        
        # 獲取引擎實例
        engine = get_anchor_time_engine(test_emit)
        
        # 設定完整測試參數
        engine.test_stages = [100, 500, 1000, 2000]  # 中等規模測試
        engine.enable_capacity_test = True
        engine.enable_data_validation = True
        engine.current_stage_index = 0
        engine.max_successful_count = 0
        engine.api_lock_count = 0
        engine.duplicate_data_count = 0
        engine.received_timestamps.clear()
        
        print("✅ 系統設定完成")
        print("📊 測試階段:", engine.test_stages)
        print("🎯 預期行為: 階段式測試 → 重複檢測 → 資料驗證 → API限制觸發")
        
        # 啟動測試
        current_time = datetime.now()
        print(f"🚀 啟動完整測試 - 開始時間: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏰ 預計結束時間: {(current_time + timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')}")
        
        engine.start_test("BTCUSDT", "1m", current_time)
        
        # 等待測試執行
        print("⏳ 等待測試執行（10秒）...")
        time.sleep(10)
        
        # 檢查測試狀態
        print(f"📊 測試狀態檢查:")
        print(f"   - 是否運行: {engine.is_running}")
        print(f"   - 最大成功筆數: {engine.max_successful_count}")
        print(f"   - API封鎖次數: {engine.api_lock_count}")
        print(f"   - 重複資料筆數: {engine.duplicate_data_count}")
        print(f"   - 總請求次數: {engine.validation_stats['total_requests']}")
        
        # 停止測試
        engine.stop_test()
        print("🛑 測試已停止")
        
        # 評估測試結果
        success = True
        if engine.max_successful_count == 0:
            print("⚠️ 警告: 未成功獲取任何資料")
            success = False
        
        if engine.validation_stats['total_requests'] == 0:
            print("⚠️ 警告: 未發送任何API請求")
            success = False
        
        if success:
            print("🎉 完整系統測試成功！")
        
        return success
        
    except Exception as e:
        print(f"❌ 系統測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_integration():
    """測試GUI整合功能"""
    print("\n🖥️ GUI整合測試...")
    
    try:
        from core.gui_controls import GUIControls
        
        # 測試時間框架轉換
        class MockGUI:
            def emit(self, message):
                print(f"[GUI] {message}")
        
        mock_gui = MockGUI()
        controls = GUIControls(mock_gui)
        
        # 測試轉換功能
        test_intervals = ["1分", "1小時", "1天", "1m", "invalid"]
        print("📋 測試時間框架轉換:")
        
        for interval in test_intervals:
            converted = controls._convert_interval_to_api_format(interval)
            print(f"   {interval} → {converted}")
        
        print("✅ GUI整合測試完成")
        return True
        
    except Exception as e:
        print(f"❌ GUI整合測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_system_status():
    """顯示系統狀態"""
    print("\n" + "=" * 60)
    print("📊 系統狀態總覽")
    print("=" * 60)
    
    try:
        # 檢查關鍵模組
        modules_to_check = [
            "modules.utils.anchor_time_engine",
            "modules.utils.api_connector", 
            "core.gui_controls",
            "modules.utils.database"
        ]
        
        for module_name in modules_to_check:
            try:
                __import__(module_name)
                print(f"✅ {module_name}")
            except Exception as e:
                print(f"❌ {module_name}: {e}")
        
        # 檢查配置
        from config.trading_config import SUPPORTED_INTERVALS
        print(f"\n📋 支援的時間間隔: {len(SUPPORTED_INTERVALS)} 個")
        
        # 檢查日誌
        import os
        log_dir = os.path.join(project_root, "data", "logs")
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
            print(f"📄 日誌檔案: {len(log_files)} 個")
        
        print("\n🎯 系統已準備就緒！")
        
    except Exception as e:
        print(f"❌ 系統狀態檢查失敗: {e}")

def main():
    """主測試函數"""
    print("=" * 60)
    print("🔧 最終系統驗證測試")
    print("=" * 60)
    
    # 顯示系統狀態
    show_system_status()
    
    results = []
    
    # 測試1: GUI整合
    results.append(test_gui_integration())
    
    # 測試2: 完整系統
    results.append(test_complete_system())
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 最終測試結果:")
    print("=" * 60)
    
    test_names = ["GUI整合", "完整系統"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 總體結果: {success_count}/{total_count} 測試通過")
    
    if success_count == total_count:
        print("\n🎉 恭喜！所有系統測試通過")
        print("💡 您現在可以:")
        print("   1. 啟動GUI: python core/gui_main.py")
        print("   2. 點擊 '🧪 權重測試模式' 按鈕")
        print("   3. 觀察階段式測試進度和API限制觸發")
        print("   4. 查看重複資料檢測和資料驗證結果")
        return True
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤信息")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
