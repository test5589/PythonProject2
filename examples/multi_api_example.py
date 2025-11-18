"""
多 API 使用範例 - 展示如何使用不同的 API 來源獲取資料
"""

import time
from datetime import datetime, timedelta
from modules.utils.api_connector import get_binance_klines_http
from modules.utils.database import insert_data
from modules.utils.api_manager import api_manager
from config.api_config import setup_multiple_apis, list_api_status

def fetch_data_with_specific_api(symbol: str, interval: str, api_name: str):
    """使用指定 API 獲取資料"""
    print(f"\n🔄 使用 API '{api_name}' 獲取 {symbol} {interval} 資料...")
    
    # 計算時間範圍（最近 1 小時）
    end_time = int(datetime.now().timestamp() * 1000)
    start_time = end_time - (60 * 60 * 1000)  # 1 小時前
    
    try:
        # 使用指定 API 獲取資料
        klines = get_binance_klines_http(
            symbol=symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=10,
            api_name=api_name
        )
        
        if klines:
            print(f"✅ 成功獲取 {len(klines)} 筆資料")
            
            # 轉換並插入資料庫
            api_url = api_manager.get_api(api_name).url
            for kline in klines:
                kline_dict = {
                    'open_time': int(kline[0]),
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5]),
                    'close_time': int(kline[6]),
                    'quote_asset_volume': float(kline[7]),
                    'num_trades': int(kline[8]),
                    'taker_base_vol': float(kline[9]),
                    'taker_quote_vol': float(kline[10])
                }
                
                insert_data(
                    category="spot",
                    symbol=symbol,
                    interval=60 if interval == "1m" else 1,  # 轉換為秒數
                    kline=kline_dict,
                    api=api_url
                )
            
            print(f"✅ 已將資料存入資料庫，API 標記為: {api_url}")
        else:
            print("❌ 未獲取到資料")
            
    except Exception as e:
        print(f"❌ 獲取資料失敗: {e}")

def demonstrate_multi_api_usage():
    """示範多 API 使用"""
    print("🚀 多 API 使用示範")
    
    # 設定多個 API
    setup_multiple_apis()
    list_api_status()
    
    # 測試不同的 API
    symbol = "BTCUSDT"
    interval = "1m"
    
    # 1. 使用預設 API
    fetch_data_with_specific_api(symbol, interval, "binance_official")
    
    # 2. 切換到測試網（如果啟用）
    if api_manager.get_api("binance_testnet").enabled:
        fetch_data_with_specific_api(symbol, interval, "binance_testnet")
    else:
        print("\n⚠️ 測試網 API 未啟用，跳過測試")
    
    # 3. 展示 API 優先級
    print("\n📊 API 優先級說明:")
    print("1. 資料庫中的 API 欄位決定資料的來源")
    print("2. 相同交易對、時間、級別但不同 API 的資料會被視為不同筆")
    print("3. 這確保了多 API 來源的資料不會互相覆蓋")

def add_custom_api_example():
    """示範如何新增自訂 API"""
    print("\n➕ 新增自訂 API 示範")
    
    from modules.utils.api_manager import APIConfig, APIType
    
    # 新增一個自訂 API
    custom_api = APIConfig(
        name="my_custom_api",
        url="https://my-custom-binance-proxy.com",
        api_type=APIType.CUSTOM,
        rate_limit=500,
        weight_per_request=2,  # 權重較高
        enabled=True
    )
    
    api_manager.add_api(custom_api)
    print(f"✅ 已新增自訂 API: {custom_api.name} -> {custom_api.url}")
    
    # 使用新的 API
    fetch_data_with_specific_api("ETHUSDT", "1m", "my_custom_api")

if __name__ == "__main__":
    demonstrate_multi_api_usage()
    add_custom_api_example()
