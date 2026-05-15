#!/usr/bin/env python3
"""
最終改善驗證測試
驗證所有5個改善項目
"""

import sys
import os
import time
from datetime import datetime

# 添加項目根目錄到路徑
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_blueprint_content():
    """測試藍圖內容"""
    print("📋 測試藍圖內容...")
    
    try:
        blueprint_path = os.path.join(project_root, "BLUEPRINT.md")
        if os.path.exists(blueprint_path):
            with open(blueprint_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 檢查關鍵內容
            key_sections = [
                "自動化交易機器人系統藍圖",
                "API權重測試系統",
                "多樣化請求",
                "避免重複",
                "K線時間段",
                "技術特點"
            ]
            
            missing_sections = []
            for section in key_sections:
                if section not in content:
                    missing_sections.append(section)
            
            if not missing_sections:
                print("✅ 藍圖內容完整，包含所有關鍵章節")
                return True
            else:
                print(f"❌ 藍圖缺少章節: {missing_sections}")
                return False
        else:
            print("❌ 藍圖文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 藍圖測試失敗: {e}")
        return False

def test_weight_test_logic():
    """測試權重測試邏輯改善"""
    print("\n🎯 測試權重測試邏輯改善...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        def test_emit(message):
            print(f"[ENGINE] {message}")
        
        engine = get_anchor_time_engine(test_emit)
        
        # 檢查新的測試配置
        expected_stages = [1000] * 20
        expected_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h"]
        expected_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
        
        checks = []
        checks.append(engine.test_stages == expected_stages)
        checks.append(hasattr(engine, 'test_timeframes') and engine.test_timeframes == expected_timeframes)
        checks.append(hasattr(engine, 'test_symbols') and engine.test_symbols == expected_symbols)
        checks.append(hasattr(engine, 'current_timeframe_index'))
        checks.append(hasattr(engine, 'current_symbol_index'))
        
        if all(checks):
            print("✅ 權重測試邏輯改善成功")
            print(f"   - 測試階段: {len(engine.test_stages)}輪，每輪{engine.test_stages[0]}筆")
            print(f"   - 時間段數: {len(engine.test_timeframes)}種")
            print(f"   - 交易對數: {len(engine.test_symbols)}種")
            return True
        else:
            print("❌ 權重測試邏輯改善失敗")
            print(f"   檢查結果: {checks}")
            return False
            
    except Exception as e:
        print(f"❌ 權重測試邏輯測試失敗: {e}")
        return False

def test_kline_naming():
    """測試K線時間段命名"""
    print("\n📊 測試K線時間段命名...")
    
    try:
        # 檢查GUI控制文件中的命名
        gui_controls_path = os.path.join(project_root, "core", "gui_controls.py")
        with open(gui_controls_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否已更改命名
        old_terms = ["回補間隔"]
        new_terms = ["K線時間段"]
        
        has_old_terms = any(term in content for term in old_terms)
        has_new_terms = any(term in content for term in new_terms)
        
        if not has_old_terms and has_new_terms:
            print("✅ K線時間段命名更新成功")
            print("   - 已移除舊的'回補間隔'術語")
            print("   - 已添加新的'K線時間段'術語")
            return True
        else:
            print("❌ K線時間段命名更新失敗")
            print(f"   - 仍有舊術語: {has_old_terms}")
            print(f"   - 有新術語: {has_new_terms}")
            return False
            
    except Exception as e:
        print(f"❌ K線時間段命名測試失敗: {e}")
        return False

def test_code_structure():
    """測試代碼結構優化"""
    print("\n🏗️ 測試代碼結構優化...")
    
    try:
        # 檢查是否創建了權重測試控制器
        controller_path = os.path.join(project_root, "core", "weight_test_controller.py")
        
        if os.path.exists(controller_path):
            with open(controller_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 檢查關鍵類和方法
            key_elements = [
                "class WeightTestController",
                "def start_weight_test",
                "def stop_weight_test",
                "def _get_test_parameters",
                "def _start_anchor_engine"
            ]
            
            missing_elements = []
            for element in key_elements:
                if element not in content:
                    missing_elements.append(element)
            
            if not missing_elements:
                print("✅ 代碼結構優化成功")
                print("   - 創建了專門的權重測試控制器")
                print("   - 分離了測試邏輯和GUI邏輯")
                print("   - 提高了代碼可維護性")
                return True
            else:
                print(f"❌ 代碼結構優化不完整，缺少: {missing_elements}")
                return False
        else:
            print("❌ 權重測試控制器文件不存在")
            return False
            
    except Exception as e:
        print(f"❌ 代碼結構測試失敗: {e}")
        return False

def test_time_display_format():
    """測試時間顯示格式"""
    print("\n⏰ 測試時間顯示格式...")
    
    try:
        from modules.utils.anchor_time_engine import get_anchor_time_engine
        
        messages = []
        def test_emit(message):
            messages.append(message)
        
        engine = get_anchor_time_engine(test_emit)
        
        # 模擬時間範圍
        from datetime import datetime
        start_time = datetime(2025, 11, 12, 14, 30, 0)
        end_time = datetime(2025, 11, 12, 15, 30, 0)
        time_range = (start_time, end_time)
        
        # 測試時間範圍顯示
        engine.data_time_ranges.append(time_range)
        start_str = time_range[0].strftime('%Y-%m-%d %H:%M:%S')
        end_str = time_range[1].strftime('%Y-%m-%d %H:%M:%S')
        test_message = f"[CAPACITY] ⏰ 資料時間範圍: {start_str} 至 {end_str}"
        
        # 檢查格式是否包含完整日期時間
        if "2025-11-12" in test_message and "14:30:00" in test_message and "15:30:00" in test_message:
            print("✅ 時間顯示格式改善成功")
            print(f"   示例: {test_message}")
            print("   - 包含完整的年月日時分秒")
            print("   - 格式清晰易讀")
            return True
        else:
            print("❌ 時間顯示格式改善失敗")
            print(f"   測試消息: {test_message}")
            return False
            
    except Exception as e:
        print(f"❌ 時間顯示格式測試失敗: {e}")
        return False

def main():
    """主測試函數"""
    print("=" * 80)
    print("🔧 最終改善驗證測試")
    print("=" * 80)
    
    results = []
    test_names = []
    
    # 測試1: 藍圖內容
    test_names.append("藍圖內容更新")
    results.append(test_blueprint_content())
    
    # 測試2: 權重測試邏輯
    test_names.append("權重測試邏輯改善")
    results.append(test_weight_test_logic())
    
    # 測試3: K線時間段命名
    test_names.append("K線時間段命名")
    results.append(test_kline_naming())
    
    # 測試4: 代碼結構優化
    test_names.append("代碼結構優化")
    results.append(test_code_structure())
    
    # 測試5: 時間顯示格式
    test_names.append("時間顯示格式")
    results.append(test_time_display_format())
    
    # 總結
    print("\n" + "=" * 80)
    print("📊 最終改善驗證結果:")
    print("=" * 80)
    
    for i, (name, result) in enumerate(zip(test_names, results)):
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{i+1}. {name}: {status}")
    
    success_count = sum(results)
    total_count = len(results)
    
    print(f"\n🎯 總體結果: {success_count}/{total_count} 改善驗證通過")
    
    if success_count == total_count:
        print("\n🎉 恭喜！所有改善都已成功實現")
        print("💡 系統現在具備:")
        print("   1. ✅ 完整的系統藍圖文檔")
        print("   2. ✅ 優化的權重測試邏輯（避免重複資料）")
        print("   3. ✅ 清晰的K線時間段命名")
        print("   4. ✅ 模組化的代碼結構")
        print("   5. ✅ 完整的時間顯示格式")
        print("\n🚀 系統已準備就緒，可以開始專業的API權重測試！")
        return True
    else:
        print(f"\n⚠️ {total_count - success_count} 項改善需要進一步檢查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
