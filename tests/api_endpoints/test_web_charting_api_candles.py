"""
測試腳本：檢查 API 是否正常返回 K 線數據
"""
import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """測試健康檢查"""
    print("=" * 60)
    print("1. 測試健康檢查")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"狀態碼: {response.status_code}")
        print(f"響應: {response.json()}")
        print()
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        print()

def test_symbols():
    """測試獲取交易對列表"""
    print("=" * 60)
    print("2. 測試獲取交易對列表")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/api/charts/symbols")
        print(f"狀態碼: {response.status_code}")
        data = response.json()
        print(f"響應: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print()
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        print()

def test_candles():
    """測試獲取 K 線數據"""
    print("=" * 60)
    print("3. 測試獲取 K 線數據")
    print("=" * 60)
    try:
        params = {
            'symbol': 'BTCUSDT',
            'interval': 60,
            'limit': 10
        }
        response = requests.get(f"{BASE_URL}/api/charts/candles", params=params)
        print(f"狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 成功獲取數據")
            print(f"   交易對: {data.get('symbol')}")
            print(f"   時間框架: {data.get('interval')}秒")
            print(f"   數據數量: {data.get('count')}")
            
            if data.get('candles'):
                print(f"\n前 3 根 K 線:")
                for i, candle in enumerate(data['candles'][:3], 1):
                    print(f"   {i}. 時間:{candle['timestamp']} 開:{candle['open']} 高:{candle['high']} 低:{candle['low']} 收:{candle['close']}")
            else:
                print(f"⚠️ 沒有 K 線數據")
        else:
            print(f"❌ 請求失敗")
            print(f"響應: {response.text}")
        print()
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        print()

def main():
    print("\n")
    print("🔍 開始測試 Web Charting API")
    print("\n")
    
    # 確保後端正在運行
    print("請確保後端正在運行: http://localhost:8001")
    print()
    
    test_health()
    test_symbols()
    test_candles()
    
    print("=" * 60)
    print("測試完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
