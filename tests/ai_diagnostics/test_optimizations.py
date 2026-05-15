"""測試優化功能"""

import sys
import time
from datetime import datetime, timezone, timedelta


def test_validators():
    """測試資料驗證層"""
    print("\n" + "="*60)
    print("1️⃣  測試資料驗證層")
    print("="*60)
    
    from modules.utils.validators import DataValidator, BatchValidator
    from modules.utils.exceptions import ValidationError
    
    # 測試交易對驗證
    print("\n📌 測試交易對驗證")
    try:
        result = DataValidator.validate_symbol("btcusdt")
        print(f"✅ 驗證成功：btcusdt -> {result}")
    except ValidationError as e:
        print(f"❌ 驗證失敗：{e}")
    
    try:
        result = DataValidator.validate_symbol("INVALID")
        print(f"✅ 驗證成功：{result}")
    except ValidationError as e:
        print(f"✅ 正確攔截無效交易對：INVALID")
    
    # 測試間隔驗證
    print("\n📌 測試間隔驗證")
    try:
        result = DataValidator.validate_interval("1m")
        print(f"✅ 驗證成功：1m -> {result}")
    except ValidationError as e:
        print(f"❌ 驗證失敗：{e}")
    
    # 測試時間範圍驗證
    print("\n📌 測試時間範圍驗證")
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 1, 2, tzinfo=timezone.utc)
    try:
        s, e = DataValidator.validate_time_range(start, end)
        print(f"✅ 時間範圍驗證成功")
    except ValidationError as e:
        print(f"❌ 驗證失敗：{e}")
    
    # 測試 K 線驗證
    print("\n📌 測試 K 線資料驗證")
    kline = {
        'open': 50000.0,
        'high': 51000.0,
        'low': 49000.0,
        'close': 50500.0,
        'volume': 100.5
    }
    try:
        result = DataValidator.validate_kline_data(kline)
        print(f"✅ K 線驗證成功")
    except ValidationError as e:
        print(f"❌ 驗證失敗：{e}")


def test_cache():
    """測試快取機制"""
    print("\n" + "="*60)
    print("2️⃣  測試快取機制")
    print("="*60)
    
    from config.trading_config import TradingConfig
    
    print("\n📌 測試間隔秒數快取")
    
    # 第一次呼叫（無快取）
    start = time.time()
    result1 = TradingConfig.get_interval_seconds("1m")
    time1 = time.time() - start
    print(f"第一次呼叫（無快取）：{result1} 秒，耗時：{time1*1000:.4f} ms")
    
    # 第二次呼叫（有快取）
    start = time.time()
    result2 = TradingConfig.get_interval_seconds("1m")
    time2 = time.time() - start
    print(f"第二次呼叫（有快取）：{result2} 秒，耗時：{time2*1000:.4f} ms")
    
    speedup = time1 / time2 if time2 > 0 else float('inf')
    print(f"✅ 快取加速：{speedup:.1f}x")


def test_api_client():
    """測試統一 API 客戶端"""
    print("\n" + "="*60)
    print("3️⃣  測試統一 API 客戶端")
    print("="*60)
    
    from modules.utils.api_client import get_api_client
    from modules.utils.exceptions import APIError, NetworkError
    
    client = get_api_client()
    
    # 測試連線
    print("\n📌 測試 API 連線")
    try:
        if client.test_connectivity():
            print("✅ API 連線測試成功")
        else:
            print("❌ API 連線測試失敗")
    except Exception as e:
        print(f"❌ 連線錯誤：{e}")
    
    # 測試取得伺服器時間
    print("\n📌 測試取得伺服器時間")
    try:
        server_time = client.get_server_time()
        print(f"✅ 伺服器時間：{server_time}")
    except Exception as e:
        print(f"❌ 取得時間失敗：{e}")
    
    # 測試抓取價格
    print("\n📌 測試抓取最新價格")
    try:
        price = client.fetch_latest_price("BTCUSDT")
        print(f"✅ BTC 價格：${price:,.2f}")
    except APIError as e:
        print(f"❌ API 錯誤：{e}")
    except NetworkError as e:
        print(f"❌ 網路錯誤：{e}")
    
    # 測試抓取 K 線
    print("\n📌 測試抓取 K 線資料")
    try:
        klines = client.fetch_klines("BTCUSDT", "1m", limit=5)
        print(f"✅ 成功抓取 {len(klines)} 筆 K 線資料")
        if klines:
            print(f"   最新收盤價：${klines[-1]['close']:,.2f}")
    except Exception as e:
        print(f"❌ 抓取失敗：{e}")


def test_connection_pool():
    """測試資料庫連線池"""
    print("\n" + "="*60)
    print("4️⃣  測試資料庫連線池")
    print("="*60)
    
    from modules.utils.db_pool import get_connection_pool, get_db_cursor
    
    # 取得連線池
    print("\n📌 取得連線池")
    try:
        pool = get_connection_pool()
        status = pool.get_pool_status()
        print(f"✅ 連線池狀態：")
        print(f"   - 總大小：{status['pool_size']}")
        print(f"   - 可用：{status['available']}")
        print(f"   - 使用中：{status['in_use']}")
        print(f"   - 資料庫：{status['db_path']}")
    except Exception as e:
        print(f"❌ 取得連線池失敗：{e}")
    
    # 測試查詢
    print("\n📌 測試使用連線池查詢")
    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM historical_data")
            count = cursor.fetchone()[0]
            print(f"✅ 查詢成功：資料庫共有 {count:,} 筆資料")
    except Exception as e:
        print(f"❌ 查詢失敗：{e}")


def test_batch_insert():
    """測試批次插入"""
    print("\n" + "="*60)
    print("5️⃣  測試批次插入")
    print("="*60)
    
    from modules.utils.database import batch_insert_data
    
    print("\n📌 準備測試資料")
    # 創建測試資料
    test_klines = []
    base_time = int(time.time() * 1000)
    for i in range(10):
        kline = {
            'open_time': base_time + i * 60000,
            'open': 50000.0 + i * 10,
            'high': 50100.0 + i * 10,
            'low': 49900.0 + i * 10,
            'close': 50050.0 + i * 10,
            'volume': 100.0 + i,
            'close_time': base_time + (i + 1) * 60000 - 1,
            'quote_asset_volume': 5000000.0,
            'num_trades': 1000,
            'taker_base_vol': 50.0,
            'taker_quote_vol': 2500000.0
        }
        test_klines.append(kline)
    
    print(f"✅ 已準備 {len(test_klines)} 筆測試資料")
    
    # 測試批次插入
    print("\n📌 執行批次插入")
    try:
        start = time.time()
        inserted = batch_insert_data(
            category="crypto",
            symbol="BTCUSDT",
            interval=60,
            klines=test_klines,
            data_source="test"
        )
        elapsed = time.time() - start
        print(f"✅ 批次插入完成")
        print(f"   - 插入數量：{inserted} 筆")
        print(f"   - 耗時：{elapsed:.3f} 秒")
        print(f"   - 速度：{inserted/elapsed:.1f} 筆/秒")
    except Exception as e:
        print(f"❌ 批次插入失敗：{e}")


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("🧪 開始測試優化功能")
    print("="*60)
    
    try:
        # 1. 資料驗證
        test_validators()
        
        # 2. 快取機制
        test_cache()
        
        # 3. API 客戶端
        test_api_client()
        
        # 4. 連線池
        test_connection_pool()
        
        # 5. 批次插入
        test_batch_insert()
        
        print("\n" + "="*60)
        print("🎉 所有測試完成！")
        print("="*60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被中斷")
    except Exception as e:
        print(f"\n\n❌ 測試過程中發生錯誤：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
