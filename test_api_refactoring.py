"""
測試 API 客戶端重構後是否正常工作
"""

import sys
from datetime import datetime

# 測試導入
try:
    from modules.utils.api.api_client import BinanceAPIClient, get_api_client
    from modules.utils.api.api_validators import APIParamValidator
    from modules.utils.api.api_parsers import APIDataParser
    from modules.utils.api.api_exceptions import APIException
    print("✅ 所有模組導入成功")
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    sys.exit(1)

# 測試 APIParamValidator
print("\n📊 測試 APIParamValidator...")
try:
    # 測試符號清理
    symbol = APIParamValidator.clean_symbol("btcusdt")
    print(f"   符號清理: btcusdt → {symbol}")
    assert symbol == "BTCUSDT", "符號清理失敗"
    
    # 測試間隔清理
    interval = APIParamValidator.clean_interval("1m")
    print(f"   間隔清理: 1m → {interval}")
    assert interval == "1m", "間隔清理失敗"
    
    # 測試數值清理
    limit = APIParamValidator.clean_numeric(500, "limit")
    print(f"   數值清理: 500 → {limit}")
    assert limit == 500, "數值清理失敗"
    
    # 測試完整參數驗證
    params = {
        'symbol': 'btcusdt',
        'interval': '1m',
        'limit': 100
    }
    cleaned = APIParamValidator.validate_and_clean_params(params)
    print(f"   參數驗證: {params} → {cleaned}")
    
    print("✅ APIParamValidator 測試通過")
except Exception as e:
    print(f"❌ APIParamValidator 測試失敗: {e}")
    sys.exit(1)

# 測試 APIDataParser
print("\n📈 測試 APIDataParser...")
try:
    # 測試 K 線解析
    raw_klines = [[
        1499040000000,      # 開盤時間
        "0.01634000",       # 開盤價
        "0.80000000",       # 最高價
        "0.01575800",       # 最低價
        "0.01577100",       # 收盤價
        "148976.11427815",  # 成交量
        1499644799999,      # 收盤時間
        "2434.19055334",    # 成交額
        308,                # 成交筆數
        "1756.87402397",    # 主動買入成交量
        "28.46694368"       # 主動買入成交額
    ]]
    
    klines = APIDataParser.parse_klines(raw_klines)
    print(f"   K線解析: 成功解析 {len(klines)} 筆")
    assert len(klines) == 1, "K線解析數量錯誤"
    assert 'open' in klines[0], "K線缺少 open 字段"
    assert 'close' in klines[0], "K線缺少 close 字段"
    
    # 測試價格解析
    price_data = {'price': '50000.123'}
    price = APIDataParser.parse_price(price_data)
    print(f"   價格解析: {price_data} → {price}")
    assert price == 50000.123, "價格解析錯誤"
    
    # 測試時間解析
    time_data = {'serverTime': 1699123456789}
    timestamp = APIDataParser.parse_server_time(time_data)
    print(f"   時間解析: {time_data['serverTime']} → {timestamp}")
    
    print("✅ APIDataParser 測試通過")
except Exception as e:
    print(f"❌ APIDataParser 測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 BinanceAPIClient 向後兼容性
print("\n🔧 測試 BinanceAPIClient 向後兼容性...")
try:
    client = BinanceAPIClient()
    
    # 測試向後兼容的方法
    params = {'symbol': 'btcusdt', 'limit': 100}
    cleaned = client._validate_and_clean_params(params)
    print(f"   _validate_and_clean_params() 工作正常")
    
    sanitized = client._sanitize_params_for_logging({'api_key': 'secret123', 'symbol': 'BTC'})
    print(f"   _sanitize_params_for_logging() 工作正常: {sanitized}")
    assert sanitized['api_key'] == "***HIDDEN***", "敏感信息未隱藏"
    
    print("✅ BinanceAPIClient 向後兼容性測試通過")
except Exception as e:
    print(f"❌ BinanceAPIClient 測試失敗: {e}")
    sys.exit(1)

# 測試全域客戶端
print("\n🌐 測試全域客戶端...")
try:
    client = get_api_client()
    print(f"   全域客戶端類型: {type(client)}")
    assert isinstance(client, BinanceAPIClient), "全域客戶端類型錯誤"
    
    print("✅ 全域客戶端測試通過")
except Exception as e:
    print(f"❌ 全域客戶端測試失敗: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("🎉 所有測試通過！API 重構成功！")
print("="*50)
print("\n📋 總結:")
print("   ✅ APIParamValidator 工作正常")
print("   ✅ APIDataParser 工作正常")
print("   ✅ BinanceAPIClient 向後兼容")
print("   ✅ 全域客戶端正常")
print("\n重構完成，功能保持不變！")
