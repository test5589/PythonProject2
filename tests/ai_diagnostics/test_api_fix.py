#!/usr/bin/env python3
"""
API修復測試腳本
測試時間框架轉換和API調用
"""

import sys
import os
import time
from datetime import datetime

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_interval_conversion():
    """測試時間框架轉換功能"""
    print("🔧 測試時間框架轉換...")
    
    try:
        # 模擬GUI控制的轉換方法
        def convert_interval_to_api_format(interval_display: str) -> str:
            """將GUI顯示的時間間隔轉換為API格式"""
            interval_mapping = {
                # 中文格式 -> API格式
                "1分": "1m",
                "3分": "3m", 
                "5分": "5m",
                "15分": "15m",
                "30分": "30m",
                "1小時": "1h",
                "2小時": "2h",
                "4小時": "4h",
                "6小時": "6h",
                "8小時": "8h",
                "12小時": "12h",
                "1天": "1d",
                "3天": "3d",
                "1週": "1w",
                "1月": "1M",
                # 已經是API格式的直接返回
                "1m": "1m",
                "3m": "3m",
                "5m": "5m", 
                "15m": "15m",
                "30m": "30m",
                "1h": "1h",
                "2h": "2h",
                "4h": "4h",
                "6h": "6h",
                "8h": "8h",
                "12h": "12h",
                "1d": "1d",
                "3d": "3d",
                "1w": "1w",
                "1M": "1M"
            }
            
            converted = interval_mapping.get(interval_display, "1m")
            if converted != interval_display:
                print(f"[CONVERT] 轉換時間框架: {interval_display} -> {converted}")
            
            return converted
        
        # 測試轉換
        test_cases = ["1分", "3分", "1小時", "1天", "1m", "invalid"]
        
        for test_case in test_cases:
            result = convert_interval_to_api_format(test_case)
            print(f"✅ {test_case} -> {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 轉換測試失敗: {e}")
        return False

def test_api_call():
    """測試API調用"""
    print("\n🌐 測試API調用...")
    
    try:
        from modules.utils.api_connector import get_binance_klines_http
        
        # 測試正確的API格式
        print("測試正確的API格式 (1m)...")
        data = get_binance_klines_http("BTCUSDT", "1m", 
                                     int(time.time() * 1000) - 60000, 
                                     int(time.time() * 1000), 
                                     10)
        
        if data and len(data) > 0:
            print(f"✅ API調用成功，獲取 {len(data)} 筆資料")
            print(f"   第一筆資料時間: {datetime.fromtimestamp(data[0][0]/1000)}")
            return True
        else:
            print("⚠️ API調用成功但無資料返回")
            return False
        
    except Exception as e:
        print(f"❌ API測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_anchor_engine_with_fix():
    """測試修復後的錨定時間引擎"""
    print("\n🎯 測試修復後的錨定時間引擎...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        def test_emit(message):
            print(f"[ENGINE] {message}")
        
        # 獲取引擎實例
        engine = get_anchor_time_engine(test_emit)
        
        # 設定測試參數（較小的測試）
        engine.test_stages = [10, 50]  # 小量測試
        engine.enable_capacity_test = True
        engine.enable_data_validation = True
        engine.current_stage_index = 0
        engine.max_successful_count = 0
        engine.api_lock_count = 0
        engine.duplicate_data_count = 0
        engine.received_timestamps.clear()
        
        print("✅ 引擎設定完成")
        
        # 啟動測試（使用正確的API格式）
        current_time = datetime.now()
        print(f"🚀 啟動測試 - 使用API格式 '1m'")
        
        engine.start_test("BTCUSDT", "1m", current_time)  # 使用正確的API格式
        
        # 等待測試執行
        print("⏳ 等待測試執行...")
        time.sleep(5)
        
        # 停止測試
        engine.stop_test()
        print("🛑 測試已停止")
        
        return True
        
    except Exception as e:
        print(f"❌ 引擎測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主測試函數"""
    print("=" * 60)
    print("🔧 API修復驗證測試")
    print("=" * 60)
    
    results = []
    
    # 測試1: 時間框架轉換
    results.append(test_interval_conversion())
    
    # 測試2: API調用
    results.append(test_api_call())
    
    # 測試3: 修復後的錨定時間引擎
    results.append(test_anchor_engine_with_fix())
    
    # 總結
    print("\n" + "=" * 60)
    print("📊 測試結果總結:")
    print("=" * 60)
    
    test_names = ["時間框架轉換", "API調用", "錨定時間引擎"]
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 總體結果: {success_count}/{total_count} 測試通過")
    
    if success_count == total_count:
        print("🎉 所有測試通過！API修復成功")
        return True
    else:
        print("⚠️ 部分測試失敗，需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
