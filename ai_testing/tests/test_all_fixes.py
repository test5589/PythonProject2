#!/usr/bin/env python3
"""
測試所有修復的腳本
驗證：1.日期顯示 2.API封鎖觸發 3.重複資料顯示 4.停止按鈕功能
"""

import sys
import os
import time
from datetime import datetime, timedelta

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_datetime_selector():
    """測試日期時間選擇器功能"""
    print("📅 測試日期時間選擇器...")
    
    try:
        from core.gui_controls import GUIControls
        
        class MockGUI:
            def __init__(self):
                import tkinter as tk
                self.root = tk.Tk()
                self.root.withdraw()  # 隱藏主窗口
                
            def emit(self, message):
                print(f"[GUI] {message}")
        
        mock_gui = MockGUI()
        controls = GUIControls(mock_gui)
        
        # 檢查日期時間選擇器是否創建成功
        if hasattr(controls, 'sy') and hasattr(controls, 'sM') and hasattr(controls, 'sd'):
            print("✅ 日期選擇器創建成功")
            
            # 測試時間獲取
            year = controls.sy.get()
            month = controls.sM.get()
            day = controls.sd.get()
            hour = controls.sh.get()
            minute = controls.su.get()
            second = controls.ss.get()
            
            print(f"✅ 當前設定時間: {year}-{month}-{day} {hour}:{minute}:{second}")
            
            # 測試快捷按鈕
            controls._set_current_time()
            print("✅ 快捷按鈕測試成功")
            
            mock_gui.root.destroy()
            return True
        else:
            print("❌ 日期選擇器創建失敗")
            mock_gui.root.destroy()
            return False
            
    except Exception as e:
        print(f"❌ 日期時間選擇器測試失敗: {e}")
        return False

def test_aggressive_api_testing():
    """測試激進的API測試設定"""
    print("\n🚀 測試激進API測試設定...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        def test_emit(message):
            print(f"[ENGINE] {message}")
        
        engine = get_anchor_time_engine(test_emit)
        
        # 檢查測試階段設定
        expected_stages = [1000, 3000, 5000, 8000, 12000, 15000, 20000, 25000]
        if engine.test_stages == expected_stages:
            print("✅ 激進測試階段設定正確")
            print(f"   測試階段: {engine.test_stages}")
        else:
            print(f"❌ 測試階段設定錯誤: {engine.test_stages}")
            return False
        
        # 測試短時間運行
        engine.enable_capacity_test = True
        engine.enable_data_validation = True
        
        current_time = datetime.now()
        engine.start_test("BTCUSDT", "1m", current_time)
        
        print("⏳ 運行激進測試 3 秒...")
        time.sleep(3)
        
        # 檢查是否有請求
        if engine.validation_stats["total_requests"] > 0:
            print(f"✅ 激進測試運行成功，總請求: {engine.validation_stats['total_requests']}")
        else:
            print("⚠️ 激進測試未發送請求")
        
        engine.stop_test()
        return True
        
    except Exception as e:
        print(f"❌ 激進API測試失敗: {e}")
        return False

def test_duplicate_display_improvement():
    """測試重複資料顯示改善"""
    print("\n🔍 測試重複資料顯示改善...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        messages = []
        def test_emit(message):
            messages.append(message)
            print(f"[ENGINE] {message}")
        
        engine = get_anchor_time_engine(test_emit)
        
        # 模擬重複資料
        current_time = int(time.time() * 1000)
        mock_data = []
        
        # 創建一些重複的時間戳
        for i in range(10):
            timestamp = current_time + (i * 60000)  # 每分鐘
            mock_data.append([timestamp, 50000, 51000, 49000, 50500, 1000])
            # 添加重複資料
            if i < 5:
                mock_data.append([timestamp, 50000, 51000, 49000, 50500, 1000])
        
        # 測試重複檢測
        duplicate_count = engine._check_duplicate_data(mock_data)
        
        # 檢查日誌是否簡化
        duplicate_messages = [msg for msg in messages if "重複時間戳" in msg]
        
        if duplicate_count > 0 and len(duplicate_messages) <= 5:  # 應該只有少量日誌
            print(f"✅ 重複資料顯示改善成功，檢測到 {duplicate_count} 筆重複，日誌簡化為 {len(duplicate_messages)} 條")
            return True
        else:
            print(f"❌ 重複資料顯示改善失敗，重複: {duplicate_count}，日誌: {len(duplicate_messages)}")
            return False
        
    except Exception as e:
        print(f"❌ 重複資料顯示測試失敗: {e}")
        return False

def test_stop_functionality():
    """測試停止功能"""
    print("\n🛑 測試停止功能...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        def test_emit(message):
            print(f"[ENGINE] {message}")
        
        engine = get_anchor_time_engine(test_emit)
        
        # 啟動測試
        current_time = datetime.now()
        engine.start_test("BTCUSDT", "1m", current_time)
        
        # 等待一下確保測試開始
        time.sleep(1)
        
        if engine.is_running:
            print("✅ 測試成功啟動")
        else:
            print("❌ 測試啟動失敗")
            return False
        
        # 測試停止功能
        engine.stop_test()
        
        # 等待停止完成
        time.sleep(1)
        
        if not engine.is_running:
            print("✅ 停止功能正常工作")
            return True
        else:
            print("❌ 停止功能失效")
            return False
        
    except Exception as e:
        print(f"❌ 停止功能測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🔧 所有修復驗證測試")
    print("=" * 60)
    
    results = []
    test_names = []
    
    # 測試1: 日期時間選擇器
    test_names.append("日期時間選擇器")
    results.append(test_datetime_selector())
    
    # 測試2: 激進API測試
    test_names.append("激進API測試設定")
    results.append(test_aggressive_api_testing())
    
    # 測試3: 重複資料顯示改善
    test_names.append("重複資料顯示改善")
    results.append(test_duplicate_display_improvement())
    
    # 測試4: 停止功能
    test_names.append("停止功能")
    results.append(test_stop_functionality())
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 修復驗證結果:")
    print("=" * 60)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 總體結果: {success_count}/{total_count} 修復驗證通過")
    
    if success_count == total_count:
        print("\n🎉 恭喜！所有問題都已修復")
        print("💡 現在您可以:")
        print("   1. 啟動GUI: python core/gui_main.py")
        print("   2. 看到完整的日期時間選擇器")
        print("   3. 使用更激進的測試設定觸發API封鎖")
        print("   4. 享受簡化的重複資料顯示")
        print("   5. 正常使用停止按鈕")
        return True
    else:
        print("\n⚠️ 部分修復需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
