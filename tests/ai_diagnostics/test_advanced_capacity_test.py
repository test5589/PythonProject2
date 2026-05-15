#!/usr/bin/env python3
"""
advanced_capacity_test.py - 進階API獲取能力測試
透過分批請求測試真實的最大獲取能力
"""

import time
from datetime import datetime, timedelta
from modules.utils.api_connector import get_binance_klines_http
from modules.utils.logger import get_logger

logger = get_logger("advanced_capacity_test")

def test_advanced_capacity(symbol: str, timeframe: str, target_total: int = 10000):
    """測試分批獲取的最大能力"""
    print(f"\n🧪 進階測試 {symbol} {timeframe} - 目標: {target_total} 筆")
    print("=" * 60)
    
    batch_size = 1000  # Binance API限制
    total_fetched = 0
    batch_count = 0
    start_time = time.time()
    error_count = 0
    
    # 計算時間範圍
    end_time_ms = int(time.time() * 1000)
    timeframe_ms = get_timeframe_ms(timeframe)
    
    while total_fetched < target_total:
        batch_count += 1
        
        # 計算這次請求的時間範圍
        batch_end_time = end_time_ms - (total_fetched * timeframe_ms)
        batch_start_time = batch_end_time - (batch_size * timeframe_ms)
        
        print(f"📊 批次 {batch_count}: 請求 {batch_size} 筆 (已獲取: {total_fetched})")
        
        try:
            # 發送API請求
            data = get_binance_klines_http(symbol, timeframe, batch_start_time, batch_end_time, batch_size)
            
            if data and len(data) > 0:
                # 驗證資料完整性
                valid_data = [item for item in data if len(item) >= 11 and all(item[i] is not None for i in range(11))]
                
                if valid_data:
                    total_fetched += len(valid_data)
                    print(f"✅ 成功: {len(valid_data)} 筆 (總計: {total_fetched})")
                    
                    # 顯示時間範圍
                    first_time = datetime.fromtimestamp(valid_data[0][0] / 1000)
                    last_time = datetime.fromtimestamp(valid_data[-1][0] / 1000)
                    print(f"   時間範圍: {first_time.strftime('%Y-%m-%d %H:%M:%S')} - {last_time.strftime('%Y-%m-%d %H:%M:%S')}")
                    
                else:
                    print(f"❌ 無效資料: {len(data)} 筆但無完整11項欄位")
                    error_count += 1
                    break
                    
            else:
                print(f"❌ 無資料返回")
                error_count += 1
                break
            
            # 短暫休息避免API限制
            time.sleep(0.1)
            
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate limit" in error_msg:
                print(f"🚫 API限制觸發: {e}")
                error_count += 1
                break
            else:
                print(f"❌ 請求失敗: {e}")
                error_count += 1
                break
        
        # 安全檢查：避免無限循環
        if batch_count > 50:  # 最多50個批次
            print(f"⚠️ 達到批次上限，停止測試")
            break
    
    total_time = time.time() - start_time
    
    # 生成報告
    print(f"\n📈 {timeframe} 進階測試總結:")
    print(f"   總獲取筆數: {total_fetched}")
    print(f"   總批次數: {batch_count}")
    print(f"   總耗時: {total_time:.2f} 秒")
    print(f"   平均速度: {total_fetched/total_time:.1f} 筆/秒")
    print(f"   錯誤次數: {error_count}")
    
    if total_fetched > 0:
        print(f"   成功率: {(batch_count-error_count)/batch_count*100:.1f}%")
    
    return total_fetched, batch_count, error_count

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

def test_continuous_requests(symbol: str, timeframe: str, duration_minutes: int = 5):
    """測試持續請求能力（模擬實際使用場景）"""
    print(f"\n🔄 持續請求測試 {symbol} {timeframe} - 持續 {duration_minutes} 分鐘")
    print("=" * 60)
    
    start_time = time.time()
    end_time = start_time + (duration_minutes * 60)
    total_requests = 0
    total_data = 0
    error_count = 0
    
    while time.time() < end_time:
        total_requests += 1
        
        try:
            # 每次請求1000筆
            end_time_ms = int(time.time() * 1000)
            start_time_ms = end_time_ms - (1000 * get_timeframe_ms(timeframe))
            
            data = get_binance_klines_http(symbol, timeframe, start_time_ms, end_time_ms, 1000)
            
            if data and len(data) > 0:
                valid_data = [item for item in data if len(item) >= 11]
                total_data += len(valid_data)
                print(f"✅ 請求 {total_requests}: {len(valid_data)} 筆 (總計: {total_data})")
            else:
                error_count += 1
                print(f"❌ 請求 {total_requests}: 無資料")
            
            # 每分鐘休息一下模擬實際使用
            time.sleep(60)
            
        except Exception as e:
            error_count += 1
            print(f"❌ 請求 {total_requests} 失敗: {e}")
            time.sleep(60)
    
    actual_duration = time.time() - start_time
    
    print(f"\n📈 持續請求測試總結:")
    print(f"   測試時長: {actual_duration/60:.1f} 分鐘")
    print(f"   總請求次數: {total_requests}")
    print(f"   總獲取資料: {total_data} 筆")
    print(f"   錯誤次數: {error_count}")
    print(f"   成功率: {(total_requests-error_count)/total_requests*100:.1f}%")
    print(f"   平均每分鐘: {total_data/(actual_duration/60):.1f} 筆")

def main():
    """主測試函數"""
    print("🚀 進階API獲取能力評估")
    print("=" * 70)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("測試目標:")
    print("1. 測試分批請求的最大獲取能力")
    print("2. 測試持續請求的穩定性")
    print("=" * 70)
    
    # 測試參數
    test_symbol = "BTCUSDT"
    
    # 1. 進階分批測試
    print("\n🎯 第一階段：進階分批測試")
    test_timeframes = ["1m", "5m", "15m", "1h"]
    
    for timeframe in test_timeframes:
        try:
            total_fetched, batch_count, error_count = test_advanced_capacity(test_symbol, timeframe, 5000)
            
            if error_count == 0 and total_fetched >= 5000:
                print(f"✅ {timeframe} 可穩定獲取大量資料")
            else:
                print(f"⚠️ {timeframe} 在大量獲取時遇到限制")
                
        except Exception as e:
            print(f"❌ {timeframe} 進階測試失敗: {e}")
    
    # 2. 持續請求測試（短時間）
    print(f"\n🎯 第二階段：持續請求測試")
    try:
        test_continuous_requests(test_symbol, "1m", 2)  # 測試2分鐘
    except Exception as e:
        print(f"❌ 持續請求測試失敗: {e}")
    
    # 3. 結論建議
    print(f"\n" + "=" * 70)
    print("📊 進階評估結論")
    print("=" * 70)
    print("1. Binance API單次請求限制為1000筆")
    print("2. 可透過分批請求獲取更多資料")
    print("3. 建議每次請求間隔0.1-1秒避免觸發限制")
    print("4. 實際回補時應採用分批策略")
    print("5. 權重系統應基於1000筆批次進行優化")

if __name__ == "__main__":
    main()
