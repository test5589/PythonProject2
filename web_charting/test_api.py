"""
test_api.py - 測試 Web Charting API
"""
import requests
import json
from datetime import datetime, timedelta

# API 基礎 URL
BASE_URL = "http://localhost:8001"


def print_section(title):
    """打印分隔線"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def test_root():
    """測試根路徑"""
    print_section("測試根路徑")
    response = requests.get(f"{BASE_URL}/")
    print(f"狀態碼: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_health():
    """測試健康檢查"""
    print_section("測試健康檢查")
    response = requests.get(f"{BASE_URL}/health")
    print(f"狀態碼: {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def test_timeframes():
    """測試獲取時間框架列表"""
    print_section("測試時間框架列表")
    response = requests.get(f"{BASE_URL}/api/charts/timeframes")
    print(f"狀態碼: {response.status_code}")
    data = response.json()
    print(f"支持的時間框架數量: {len(data['timeframes'])}")
    print("時間框架列表:")
    for tf in data['timeframes'][:5]:  # 只顯示前5個
        print(f"  - {tf['label']} ({tf['seconds']}秒)")
    print("  ...")


def test_data_sources():
    """測試獲取資料來源"""
    print_section("測試資料來源")
    response = requests.get(f"{BASE_URL}/api/charts/data-sources")
    print(f"狀態碼: {response.status_code}")
    data = response.json()
    print("資料來源及優先級:")
    for source in data['sources']:
        print(f"  - {source['name']} (優先級: {source['priority']})")
        print(f"    說明: {source['description']}")


def test_symbols():
    """測試獲取交易對列表"""
    print_section("測試交易對列表")
    response = requests.get(f"{BASE_URL}/api/charts/symbols")
    print(f"狀態碼: {response.status_code}")
    data = response.json()
    print(f"分類: {data['category']}")
    print(f"交易對數量: {data['count']}")
    if data['symbols']:
        print(f"前10個交易對: {data['symbols'][:10]}")


def test_sync(symbol="BTCUSDT", interval=60):
    """測試資料同步"""
    print_section(f"測試同步資料 - {symbol}@{interval}s")
    
    # 同步最近1天的資料
    end_time = datetime.now().timestamp()
    start_time = (datetime.now() - timedelta(days=1)).timestamp()
    
    payload = {
        "symbol": symbol,
        "interval": interval,
        "category": "crypto",
        "start_time": start_time,
        "end_time": end_time,
        "overwrite": False
    }
    
    print(f"同步請求: {symbol}@{interval}s")
    print(f"時間範圍: {datetime.fromtimestamp(start_time)} 至 {datetime.fromtimestamp(end_time)}")
    
    response = requests.post(f"{BASE_URL}/api/sync/", json=payload)
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"同步狀態: {data['status']}")
        print(f"同步筆數: {data['records_synced']}")
        print(f"時間範圍: {data['time_range']}")
        print(f"訊息: {data['message']}")
    else:
        print(f"錯誤: {response.text}")


def test_get_candles(symbol="BTCUSDT", interval=60, limit=100):
    """測試獲取K線資料"""
    print_section(f"測試獲取K線 - {symbol}@{interval}s")
    
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    
    response = requests.get(f"{BASE_URL}/api/charts/candles", params=params)
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"交易對: {data['symbol']}")
        print(f"時間框架: {data['interval']}s")
        print(f"K線數量: {data['count']}")
        if data['time_range']:
            print(f"時間範圍: {data['time_range']}")
        
        if data['candles']:
            print(f"\n前3根K線:")
            for i, candle in enumerate(data['candles'][:3], 1):
                ts = datetime.fromtimestamp(candle['timestamp'])
                print(f"  {i}. {ts} | O:{candle['open']} H:{candle['high']} L:{candle['low']} C:{candle['close']} | {candle['data_source']}")
    else:
        print(f"錯誤: {response.text}")


def test_stats(symbol="BTCUSDT", interval=60):
    """測試獲取統計資訊"""
    print_section(f"測試統計資訊 - {symbol}@{interval}s")
    
    response = requests.get(f"{BASE_URL}/api/charts/stats/{symbol}/{interval}")
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"錯誤: {response.text}")


def test_sync_history():
    """測試同步歷史"""
    print_section("測試同步歷史")
    
    params = {"limit": 10}
    response = requests.get(f"{BASE_URL}/api/sync/history", params=params)
    print(f"狀態碼: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"同步記錄數量: {len(data)}")
        
        if data:
            print("\n最近的同步記錄:")
            for i, record in enumerate(data[:5], 1):
                print(f"\n  {i}. ID: {record['id']}")
                print(f"     交易對: {record['symbol']}@{record['interval']}s")
                print(f"     狀態: {record['sync_status']}")
                print(f"     同步筆數: {record['records_synced']}")
                print(f"     創建時間: {record['created_at']}")
    else:
        print(f"錯誤: {response.text}")


def main():
    """執行所有測試"""
    print("\n" + "=" * 60)
    print("  Web Charting API 測試")
    print("=" * 60)
    
    try:
        # 基礎測試
        test_root()
        test_health()
        test_timeframes()
        test_data_sources()
        test_symbols()
        
        # 同步測試
        print("\n" + "!" * 60)
        print("  開始資料同步測試 (這可能需要一些時間)")
        print("!" * 60)
        test_sync("BTCUSDT", 60)  # 同步 BTCUSDT 1分鐘K線
        
        # 查詢測試
        test_get_candles("BTCUSDT", 60, 100)
        test_stats("BTCUSDT", 60)
        test_sync_history()
        
        print("\n" + "=" * 60)
        print("  ✅ 所有測試完成")
        print("=" * 60)
        
    except requests.exceptions.ConnectionError:
        print("\n" + "!" * 60)
        print("  ❌ 無法連接到API服務器")
        print("  請確認後端是否已啟動: python backend/main.py")
        print("  或運行: start_backend.bat")
        print("!" * 60)
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
