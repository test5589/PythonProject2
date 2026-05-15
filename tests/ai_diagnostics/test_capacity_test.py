#!/usr/bin/env python3
"""
capacity_test.py - 本機API獲取能力評估工具
測試不同時間框架下的最大可獲取資料筆數
"""

import time
from datetime import datetime
from modules.utils.api_connector import get_binance_klines_http
from modules.utils.logger import get_logger

logger = get_logger("capacity_test")

def test_timeframe_capacity(symbol: str, timeframe: str, max_test_count: int = 20000):
    """測試特定時間框架的獲取能力"""
    print(f"\n🧪 測試 {symbol} {timeframe} 時間框架...")
    print("=" * 50)
    
    # 階段式測試
    test_stages = [1000, 2000, 5000, 8000, 10000, 15000, 20000]
    successful_counts = []
    
    for test_count in test_stages:
        if test_count > max_test_count:
            break
            
        print(f"📊 測試 {test_count} 筆資料...")
        
        try:
            start_time = time.time()
            
            # 計算時間範圍
            end_time_ms = int(time.time() * 1000)
            start_time_ms = end_time_ms - (test_count * get_timeframe_ms(timeframe))
            
            # 發送API請求
            data = get_binance_klines_http(symbol, timeframe, start_time_ms, end_time_ms, test_count)
            
            request_time = time.time() - start_time
            
            if data and len(data) > 0:
                # 驗證資料完整性
                valid_data = [item for item in data if len(item) >= 11 and all(item[i] is not None for i in range(11))]
                
                print(f"✅ 成功: 總計 {len(data)} 筆, 有效 {len(valid_data)} 筆")
                print(f"   請求耗時: {request_time:.2f} 秒")
                print(f"   平均速度: {len(data)/request_time:.1f} 筆/秒")
                
                # 顯示資料樣本
                if len(valid_data) > 0:
                    first_item = valid_data[0]
                    last_item = valid_data[-1]
                    print(f"   時間範圍: {datetime.fromtimestamp(first_item[0]/1000).strftime('%H:%M:%S')} - {datetime.fromtimestamp(last_item[0]/1000).strftime('%H:%M:%S')}")
                    print(f"   價格範圍: {first_item[4]} - {last_item[4]}")
                
                successful_counts.append((test_count, len(valid_data), request_time))
                
                # 短暫休息避免API限制
                time.sleep(1)
                
            else:
                print(f"❌ 失敗: 無資料返回")
                break
                
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate limit" in error_msg:
                print(f"🚫 API限制觸發: {e}")
                print(f"   最大成功筆數: {successful_counts[-1][0] if successful_counts else 0}")
                break
            else:
                print(f"❌ 請求失敗: {e}")
                break
    
    return successful_counts

def get_timeframe_ms(timeframe: str) -> int:
    """取得時間框架的毫秒數"""
    timeframe_map = {
        "1m": 60 * 1000,
        "3m": 3 * 60 * 1000,
        "5m": 5 * 60 * 1000,
        "15m": 15 * 60 * 1000,
        "30m": 30 * 60 * 1000,
        "1h": 60 * 60 * 1000,
        "4h": 4 * 60 * 60 * 1000,
        "1d": 24 * 60 * 60 * 1000
    }
    return timeframe_map.get(timeframe, 60 * 1000)

def main():
    """主測試函數"""
    print("🚀 本機API獲取能力評估")
    print("=" * 60)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"測試目標: 評估各時間框架最大可獲取資料筆數")
    print("=" * 60)
    
    # 測試參數
    test_symbol = "BTCUSDT"
    test_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h"]
    
    results = {}
    
    for timeframe in test_timeframes:
        try:
            successful_counts = test_timeframe_capacity(test_symbol, timeframe)
            results[timeframe] = successful_counts
            
            if successful_counts:
                max_count = successful_counts[-1][0]
                max_valid = successful_counts[-1][1]
                avg_speed = sum(count[1]/count[2] for count in successful_counts) / len(successful_counts)
                
                print(f"\n📈 {timeframe} 框架總結:")
                print(f"   最大請求筆數: {max_count}")
                print(f"   最大有效筆數: {max_valid}")
                print(f"   平均獲取速度: {avg_speed:.1f} 筆/秒")
                
        except Exception as e:
            print(f"❌ {timeframe} 測試失敗: {e}")
            results[timeframe] = []
    
    # 生成評估報告
    print("\n" + "=" * 60)
    print("📊 評估報告總結")
    print("=" * 60)
    
    for timeframe, counts in results.items():
        if counts:
            max_count = counts[-1][0]
            max_valid = counts[-1][1]
            print(f"{timeframe:>4}: 最大 {max_count:>5} 筆 (有效 {max_valid:>5} 筆)")
        else:
            print(f"{timeframe:>4}: 測試失敗")
    
    print("\n💡 建議:")
    print("- 1m框架適合小批量即時資料獲取")
    print("- 較高時間框架適合大批量歷史資料回補")
    print("- 建議根據實際需求選擇合適的時間框架和批量大小")
    print("- 注意API限制，避免短時間內大量請求")

if __name__ == "__main__":
    main()
