"""
快速檢查後端是否運行
"""
import requests

def check_backend():
    print("=" * 60)
    print("檢查後端狀態")
    print("=" * 60)
    print()
    
    try:
        print("測試 1: Health Check")
        response = requests.get("http://localhost:8001/health", timeout=2)
        print(f"  狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ 後端正常運行")
            print(f"  響應: {response.json()}")
        else:
            print(f"  ❌ 後端返回錯誤")
            print(f"  內容: {response.text[:200]}")
    except requests.exceptions.ConnectionError:
        print(f"  ❌ 無法連接到後端 (Connection Error)")
        print(f"  後端可能沒有運行或已崩潰")
    except requests.exceptions.Timeout:
        print(f"  ❌ 連接超時")
        print(f"  後端可能卡住了")
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
    
    print()
    
    try:
        print("測試 2: Symbols API")
        response = requests.get("http://localhost:8001/api/charts/symbols", timeout=2)
        print(f"  狀態碼: {response.status_code}")
        if response.status_code == 200:
            print(f"  ✅ API 正常")
        else:
            print(f"  ❌ API 錯誤")
            print(f"  內容: {response.text[:200]}")
    except Exception as e:
        print(f"  ❌ 錯誤: {e}")
    
    print()
    print("=" * 60)
    print("建議:")
    print("如果看到連接錯誤，請重啟後端:")
    print("  cd web_charting")
    print("  .\\start_backend.bat")
    print("=" * 60)

if __name__ == "__main__":
    check_backend()
