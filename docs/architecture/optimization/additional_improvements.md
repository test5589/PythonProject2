# 額外改進建議

## 📋 已完成的優化（2025/11/11）

### ✅ 1. 模組化拆分
- 將 414 行的 Gui.py 拆分為 5 個檔案
- 每個檔案職責單一、易於維護

### ✅ 2. 統一配置管理  
- 創建 config/trading_config.py
- 集中管理貨幣對、間隔、秒數轉換

### ✅ 3. 自訂例外
- 創建 modules/utils/exceptions.py
- 8 種專業例外類型

### ✅ 4. 優化日誌系統
- 支援日誌輪替（大小或時間）
- 最多保留 5 個備份檔案
- 單檔最大 10MB

---

## 🔍 建議繼續優化的項目

### 🟡 優先級：中

#### 1. 資料驗證層
**問題**：輸入驗證分散在各處

**建議**：創建統一驗證模組
```python
# modules/utils/validators.py
class DataValidator:
    @staticmethod
    def validate_symbol(symbol: str) -> bool:
        from config.trading_config import TradingConfig
        return symbol.upper() in TradingConfig.SUPPORTED_SYMBOLS
    
    @staticmethod
    def validate_time_range(start, end) -> tuple:
        if start >= end:
            raise ValidationError("開始時間必須早於結束時間")
        return start, end
```

#### 2. 統一 API 客戶端
**問題**：data_fetcher.py、api_connector.py、backfill_data.py 功能重疊

**建議**：創建統一 API 客戶端（已提供範例於 optimization_recommendations.md）

#### 3. 資料庫連線池
**問題**：每次操作都建立新連線

**建議**：使用連線池提升效能
```python
# modules/utils/db_pool.py
import sqlite3
from queue import Queue

class ConnectionPool:
    def __init__(self, db_path, pool_size=5):
        self.pool = Queue(maxsize=pool_size)
        for _ in range(pool_size):
            self.pool.put(sqlite3.connect(db_path))
    
    def get_connection(self):
        return self.pool.get()
    
    def return_connection(self, conn):
        self.pool.put(conn)
```

---

### 🟢 優先級：低

#### 1. 型別提示（Type Hints）
**好處**：
- IDE 自動補全更好
- 更容易發現錯誤
- 程式碼更易讀

**範例**：
```python
def fetch_klines(
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int
) -> list[dict]:
    pass
```

#### 2. 單元測試
**建議架構**：
```
tests/
├── test_api_client.py
├── test_database.py
├── test_backfill.py
├── test_validators.py
└── test_config.py
```

#### 3. 設定檔外部化
**現狀**：設定寫在 Python 程式碼中

**建議**：使用 YAML 或 JSON
```yaml
# config/settings.yaml
trading:
  symbols:
    - BTCUSDT
    - ETHUSDT
    # ...
  default_symbol: BTCUSDT
  
api:
  timeout: 10
  max_retries: 3
  
logging:
  level: INFO
  max_bytes: 10485760  # 10MB
  backup_count: 5
```

---

## 🔧 程式碼品質改進

### 1. 命名一致性
**問題**：部分變數命名不一致
- 有些用 `sym`，有些用 `symbol`
- 有些用 `cat`，有些用 `category`

**建議**：統一使用完整名稱
```python
# ❌ 不好
def func(sym, cat):
    pass

# ✅ 好
def func(symbol, category):
    pass
```

### 2. 魔術數字
**問題**：硬編碼的數字分散各處

**建議**：集中定義常數
```python
# config/constants.py
class Constants:
    # API 限制
    MAX_KLINES_PER_REQUEST = 1000
    API_RATE_LIMIT_PER_MINUTE = 1000
    
    # 時間常數
    SECONDS_PER_DAY = 86400
    MILLISECONDS_PER_SECOND = 1000
    
    # UI 常數
    DIALOG_WIDTH = 600
    DIALOG_HEIGHT = 350
```

### 3. 長函數拆分
**建議檢查**：
- 函數超過 50 行 → 考慮拆分
- 巢狀超過 3 層 → 提取子函數
- 重複邏輯 → 提取共用函數

---

## 📊 效能優化

### 1. 資料庫索引
**檢查項目**：
```sql
-- 檢查是否有適當的索引
PRAGMA index_list('kline_data');

-- 建議索引
CREATE INDEX IF NOT EXISTS idx_symbol_interval_ts 
ON kline_data(symbol, interval, timestamp);
```

### 2. 批次插入
**現狀**：逐筆插入資料

**建議**：使用批次插入
```python
# ❌ 慢
for row in data:
    cursor.execute("INSERT ...", row)

# ✅ 快
cursor.executemany("INSERT ...", data)
```

### 3. 快取機制
**建議**：對常用查詢使用快取
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_interval_seconds(interval: str) -> int:
    return TradingConfig.INTERVAL_SECONDS[interval]
```

---

## 🛡️ 安全性改進

### 1. SQL 注入防護
**檢查**：所有 SQL 查詢是否使用參數化

```python
# ❌ 危險
query = f"SELECT * FROM kline_data WHERE symbol='{symbol}'"

# ✅ 安全
query = "SELECT * FROM kline_data WHERE symbol=?"
cursor.execute(query, (symbol,))
```

### 2. 敏感資訊管理
**建議**：使用環境變數
```python
# .env
API_KEY=your_secret_key
DATABASE_PATH=C:/path/to/db

# Python
from dotenv import load_dotenv
load_dotenv()
API_KEY = os.getenv("API_KEY")
```

---

## 📝 文檔改進

### 1. Docstring 標準化
**建議使用 Google 風格**：
```python
def fetch_klines(symbol: str, interval: str) -> list:
    """
    抓取 K 線資料
    
    Args:
        symbol: 交易對符號（如 BTCUSDT）
        interval: 時間間隔（如 1m, 1h）
        
    Returns:
        list: K 線資料列表
        
    Raises:
        APIError: API 請求失敗
        NetworkError: 網路連線錯誤
        
    Example:
        >>> fetch_klines("BTCUSDT", "1m")
        [{'open': 50000, ...}, ...]
    """
    pass
```

### 2. README 更新
**建議增加**：
- 安裝步驟
- 快速開始指南
- API 文檔
- 常見問題

---

## 🧪 測試策略

### 1. 單元測試
**覆蓋率目標**：> 70%

**優先測試**：
- 資料驗證函數
- 時間轉換函數
- API 呼叫邏輯
- 資料庫操作

### 2. 整合測試
**測試場景**：
- 完整回補流程
- 監控啟停
- 資料完整性檢查

### 3. 壓力測試
**測試項目**：
- 大量資料回補
- 長時間運行
- 記憶體洩漏檢查

---

## 🎯 總結

### 已完成（今日）
- ✅ 模組化拆分
- ✅ 統一配置
- ✅ 自訂例外
- ✅ 日誌優化

### 建議優先處理
1. 🟡 資料驗證層
2. 🟡 統一 API 客戶端
3. 🟡 資料庫連線池

### 長期改進
- 型別提示
- 單元測試
- 設定檔外部化
- 效能優化

---

**記住**：
1. 逐步改進，不要一次改太多
2. 每次修改後都要測試
3. 保留舊代碼備份
4. 記錄改動原因
