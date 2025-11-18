# Web K線圖應用開發計劃

**創建日期**: 2025-11-16  
**目標**: 創建類似 TradingView 的 K 線圖 Web 應用

---

## 🎯 核心需求

### 1. K線圖顯示
- ✅ 支持多時間框架：1s, 2s, 5s, 10s, 15s, 30s, 60s, 300s, 600s, 30m, 1h, 4h, 8h
- ✅ 顏色區分：
  - `real` 上漲 → 深綠色
  - `real` 下跌 → 深紅色
  - `Aggregation` 上漲 → 淺綠色
  - `Aggregation` 下跌 → 淺紅色
  - 優先級低/最低聚合 → 灰色
- ✅ 數據來源標記

### 2. 獨立資料庫
- ✅ 不每次從主 DB 重新加載
- ✅ 按需同步/更新
- ✅ 本地緩存資料
- ✅ 手動控制更新

### 3. 技術指標
需要實現 3 個指標：
1. **ADX and DI** - 趨勢強度指標
2. **Vegas雙通道** - EMA 通道系統
3. **MA Cross 50 & 200** - 移動平均線交叉

### 4. 未來擴展
- 與 GUI 1秒級監控串接
- 即時資料同步
- 核心策略模組對接

---

## 🏗️ 技術架構

### 技術棧選擇

#### 前端
```
- Framework: React (快速開發，組件豐富)
- Chart Library: Lightweight Charts (TradingView 開源版)
- UI Components: Ant Design (專業、完整)
- State Management: Zustand (輕量級)
- Build Tool: Vite (快速構建)
```

#### 後端  
```
- Framework: FastAPI (高性能，異步)
- Database: SQLite (獨立資料庫)
- ORM: SQLAlchemy (與主系統一致)
- Cache: Redis (可選，未來擴展)
```

### 目錄結構

```
PythonProject2/
├── web_charting/                    # 新建 Web 應用根目錄
│   ├── backend/                     # 後端 API
│   │   ├── api/                     # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── charts.py            # K線資料 API
│   │   │   ├── indicators.py        # 指標計算 API
│   │   │   └── sync.py              # 資料同步 API
│   │   ├── database/                # 資料庫層
│   │   │   ├── __init__.py
│   │   │   ├── models.py            # 資料模型
│   │   │   ├── chart_db.py          # Chart DB 管理
│   │   │   └── sync_manager.py      # 同步管理器
│   │   ├── indicators/              # 指標計算
│   │   │   ├── __init__.py
│   │   │   ├── adx.py               # ADX 指標
│   │   │   ├── vegas.py             # Vegas 通道
│   │   │   └── ma_cross.py          # MA 交叉
│   │   ├── utils/                   # 工具函數
│   │   │   ├── __init__.py
│   │   │   └── data_converter.py    # 資料轉換
│   │   ├── config.py                # 配置
│   │   ├── main.py                  # FastAPI 主程式
│   │   └── requirements.txt         # Python 依賴
│   │
│   ├── frontend/                    # 前端應用
│   │   ├── public/                  # 靜態資源
│   │   ├── src/
│   │   │   ├── components/          # React 組件
│   │   │   │   ├── Chart/           # K線圖組件
│   │   │   │   │   ├── CandlestickChart.tsx
│   │   │   │   │   ├── TimeframeSelector.tsx
│   │   │   │   │   └── DataSourceToggle.tsx
│   │   │   │   ├── Indicators/      # 指標組件
│   │   │   │   │   ├── ADXIndicator.tsx
│   │   │   │   │   ├── VegasChannel.tsx
│   │   │   │   │   └── MACross.tsx
│   │   │   │   ├── Controls/        # 控制面板
│   │   │   │   │   ├── SyncButton.tsx
│   │   │   │   │   └── SymbolSelector.tsx
│   │   │   │   └── Layout/          # 布局組件
│   │   │   ├── api/                 # API 調用
│   │   │   ├── hooks/               # Custom Hooks
│   │   │   ├── stores/              # Zustand Stores
│   │   │   ├── types/               # TypeScript 類型
│   │   │   ├── utils/               # 工具函數
│   │   │   ├── App.tsx              # 主應用
│   │   │   └── main.tsx             # 入口
│   │   ├── package.json             # npm 依賴
│   │   ├── tsconfig.json            # TypeScript 配置
│   │   └── vite.config.ts           # Vite 配置
│   │
│   ├── database/                    # 獨立資料庫
│   │   └── charting.db              # SQLite 資料庫
│   │
│   ├── docs/                        # 文檔
│   │   ├── API.md                   # API 文檔
│   │   ├── DATABASE_SCHEMA.md       # 資料庫結構
│   │   └── USER_GUIDE.md            # 使用指南
│   │
│   └── README.md                    # 項目說明
```

---

## 📊 資料庫設計

### 獨立資料庫 Schema

```sql
-- K線資料表
CREATE TABLE candlestick_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    interval INTEGER NOT NULL,           -- 秒為單位
    timestamp REAL NOT NULL,             -- Unix timestamp
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL,
    data_source VARCHAR(20) NOT NULL,    -- 'real', 'Aggregation', 'interpolated', etc.
    priority INTEGER DEFAULT 1,          -- 資料優先級 (1=最高)
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, timestamp, data_source)
);

-- 索引（優化查詢性能）
CREATE INDEX idx_symbol_interval_timestamp 
    ON candlestick_data(symbol, interval, timestamp);
    
CREATE INDEX idx_data_source 
    ON candlestick_data(data_source);
    
CREATE INDEX idx_timestamp 
    ON candlestick_data(timestamp);

-- 同步記錄表
CREATE TABLE sync_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    interval INTEGER NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    records_synced INTEGER DEFAULT 0,
    sync_status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME
);

-- 指標緩存表（可選，用於緩存計算結果）
CREATE TABLE indicator_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol VARCHAR(20) NOT NULL,
    interval INTEGER NOT NULL,
    indicator_name VARCHAR(50) NOT NULL,
    timestamp REAL NOT NULL,
    value REAL NOT NULL,
    params JSON,                         -- 指標參數（JSON格式）
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, interval, indicator_name, timestamp, params)
);
```

### 資料優先級定義

```python
DATA_PRIORITY = {
    'real': 1,              # 最高優先級 - 真實數據
    'Aggregation': 2,       # 聚合數據
    'interpolated': 3,      # 插值數據
    'inferior-Aggregation': 4,  # 低質量聚合
    'test': 5               # 測試數據 - 最低優先級
}
```

---

## 🎨 UI/UX 設計

### 頁面佈局

```
┌─────────────────────────────────────────────────────────────┐
│ Header: Logo | Symbol Selector | Sync Button | Settings    │
├─────────────────────────────────────────────────────────────┤
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Timeframe Bar:                                        │   │
│ │ [1s] [2s] [5s] [10s] [15s] [30s] [1m] [5m] ...      │   │
│ └───────────────────────────────────────────────────────┘   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │                                                         │   │
│ │                 Candlestick Chart                      │   │
│ │                                                         │   │
│ │                    (Lightweight Charts)                │   │
│ │                                                         │   │
│ └───────────────────────────────────────────────────────┘   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Indicators Panel:                                      │   │
│ │ ┌──────────┐ ┌──────────┐ ┌──────────┐               │   │
│ │ │   ADX    │ │  Vegas   │ │ MA Cross │               │   │
│ │ │          │ │          │ │          │               │   │
│ │ └──────────┘ └──────────┘ └──────────┘               │   │
│ └───────────────────────────────────────────────────────┘   │
│ ┌───────────────────────────────────────────────────────┐   │
│ │ Controls:                                              │   │
│ │ ☐ Show Real Data  ☐ Show Aggregation  ☐ Show Low Pri │   │
│ │ Last Sync: 2025-11-16 22:30:15 | [Sync Now]          │   │
│ └───────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 顏色方案

```javascript
const CHART_COLORS = {
  real: {
    up: '#00C853',      // 深綠色
    down: '#D50000',    // 深紅色
  },
  Aggregation: {
    up: '#69F0AE',      // 淺綠色
    down: '#FF5252',    // 淺紅色
  },
  lowPriority: {
    up: '#9E9E9E',      // 灰色
    down: '#757575',    // 深灰色
  },
  indicators: {
    adx: '#1976D2',     // 藍色
    diPlus: '#00C853',  // 綠色
    diMinus: '#D50000', // 紅色
    vegas: {
      filter: '#00C853',  // 綠色
      groupA: '#2196F3',  // 藍色
      groupB: '#F44336',  // 紅色
    },
    ma: {
      ma50: '#D50000',    // 紅色
      ma200: '#00C853',   // 綠色
    }
  }
};
```

---

## 🔄 資料同步機制

### 同步流程

```
1. 用戶點擊「Sync Now」按鈕
   ↓
2. 前端發送同步請求到後端
   POST /api/sync
   {
     "symbol": "BTCUSDT",
     "interval": 1,
     "start_time": null,  // null = 從上次同步時間開始
     "end_time": null,    // null = 到現在
     "overwrite": false   // 是否覆蓋現有數據
   }
   ↓
3. 後端從主資料庫讀取數據
   - 連接到主 DB: historical_data.db
   - 查詢指定範圍的資料
   ↓
4. 資料轉換和寫入
   - 轉換為 charting DB 格式
   - 批量插入到 charting.db
   - 更新 sync_history
   ↓
5. 返回同步結果
   {
     "status": "success",
     "records_synced": 1440,
     "time_range": {
       "start": "2025-11-15 00:00:00",
       "end": "2025-11-16 00:00:00"
     }
   }
   ↓
6. 前端更新顯示
   - 刷新圖表
   - 更新同步時間標籤
```

### 增量同步

```python
def incremental_sync(symbol, interval):
    """增量同步：只同步新增的數據"""
    # 1. 查詢上次同步的最後時間
    last_sync = get_last_sync_time(symbol, interval)
    
    # 2. 從主 DB 查詢新數據
    new_data = query_main_db(
        symbol=symbol,
        interval=interval,
        start_time=last_sync,
        end_time=datetime.now()
    )
    
    # 3. 插入到 charting DB
    insert_to_chart_db(new_data)
    
    # 4. 更新同步記錄
    update_sync_history(symbol, interval, len(new_data))
```

---

## 📈 技術指標實現

### 1. ADX and DI

```python
def calculate_adx(df, period=14):
    """
    計算 ADX (Average Directional Index)
    
    Args:
        df: DataFrame with OHLC data
        period: 計算週期（默認14）
    
    Returns:
        DataFrame with ADX, DI+, DI-
    """
    # True Range
    df['TR'] = df[['high', 'low', 'close']].apply(
        lambda x: max(
            x['high'] - x['low'],
            abs(x['high'] - x['close'].shift(1)),
            abs(x['low'] - x['close'].shift(1))
        ),
        axis=1
    )
    
    # Directional Movement
    df['DM+'] = df['high'].diff().apply(lambda x: max(x, 0))
    df['DM-'] = -df['low'].diff().apply(lambda x: max(x, 0))
    
    # Smoothed TR and DM
    df['SmoothedTR'] = df['TR'].ewm(span=period).mean()
    df['SmoothedDM+'] = df['DM+'].ewm(span=period).mean()
    df['SmoothedDM-'] = df['DM-'].ewm(span=period).mean()
    
    # DI+ and DI-
    df['DI+'] = 100 * df['SmoothedDM+'] / df['SmoothedTR']
    df['DI-'] = 100 * df['SmoothedDM-'] / df['SmoothedTR']
    
    # DX and ADX
    df['DX'] = 100 * abs(df['DI+'] - df['DI-']) / (df['DI+'] + df['DI-'])
    df['ADX'] = df['DX'].ewm(span=period).mean()
    
    return df[['ADX', 'DI+', 'DI-']]
```

### 2. Vegas 雙通道

```python
def calculate_vegas_channel(df, filter_period=12, 
                           group_a=[144, 169], 
                           group_b=[576, 676]):
    """
    計算 Vegas 雙通道
    
    Args:
        df: DataFrame with close prices
        filter_period: 過濾線週期
        group_a: A組通道週期
        group_b: B組通道週期
    
    Returns:
        DataFrame with Vegas lines
    """
    df['Filter'] = df['close'].ewm(span=filter_period).mean()
    df['Group_A1'] = df['close'].ewm(span=group_a[0]).mean()
    df['Group_A2'] = df['close'].ewm(span=group_a[1]).mean()
    df['Group_B1'] = df['close'].ewm(span=group_b[0]).mean()
    df['Group_B2'] = df['close'].ewm(span=group_b[1]).mean()
    
    return df[['Filter', 'Group_A1', 'Group_A2', 'Group_B1', 'Group_B2']]
```

### 3. MA Cross 50 & 200

```python
def calculate_ma_cross(df, short_period=50, long_period=200):
    """
    計算 MA 交叉
    
    Args:
        df: DataFrame with close prices
        short_period: 短期 MA 週期
        long_period: 長期 MA 週期
    
    Returns:
        DataFrame with MA lines and cross signals
    """
    df['MA50'] = df['close'].rolling(window=short_period).mean()
    df['MA200'] = df['close'].rolling(window=long_period).mean()
    
    # 檢測交叉點
    df['Cross'] = 0
    df.loc[(df['MA50'] > df['MA200']) & 
           (df['MA50'].shift(1) <= df['MA200'].shift(1)), 'Cross'] = 1  # 金叉
    df.loc[(df['MA50'] < df['MA200']) & 
           (df['MA50'].shift(1) >= df['MA200'].shift(1)), 'Cross'] = -1  # 死叉
    
    return df[['MA50', 'MA200', 'Cross']]
```

---

## 🚀 實施計劃

### 階段 1: 基礎架構（1-2天）
- [ ] 創建項目結構
- [ ] 設置獨立資料庫
- [ ] 實現基本 API（FastAPI）
- [ ] 創建 React 前端框架

### 階段 2: K線圖實現（2-3天）
- [ ] 整合 Lightweight Charts
- [ ] 實現多時間框架切換
- [ ] 實現顏色區分（real/Aggregation）
- [ ] 資料源過濾器

### 階段 3: 資料同步（1-2天）
- [ ] 主 DB 連接器
- [ ] 同步管理器
- [ ] 增量同步邏輯
- [ ] 同步狀態UI

### 階段 4: 技術指標（2-3天）
- [ ] ADX and DI 實現
- [ ] Vegas 雙通道實現
- [ ] MA Cross 實現
- [ ] 指標顯示優化

### 階段 5: 優化和測試（1-2天）
- [ ] 性能優化
- [ ] UI/UX 優化
- [ ] 測試和調試
- [ ] 文檔完善

**總計: 7-12天**

---

## 📋 依賴包

### Backend (requirements.txt)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pandas==2.1.3
numpy==1.26.2
python-dotenv==1.0.0
pydantic==2.5.0
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "lightweight-charts": "^4.1.0",
    "antd": "^5.11.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "dayjs": "^1.11.10"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
```

---

## 🔐 資料庫規劃建議（回答任務6）

### 1. 資料庫分離策略

```
主資料庫 (historical_data.db)
├── 用途: 存儲所有歷史交易數據
├── 特點: 完整、權威、原始數據
└── 訪問: 回補、一秒監控寫入

Web資料庫 (charting.db)
├── 用途: Web圖表專用
├── 特點: 快速、輕量、可重建
└── 訪問: Web應用讀寫、主DB同步

策略資料庫 (strategy.db) - 未來
├── 用途: 核心策略分析結果
├── 特點: 高頻讀寫、分析結果
└── 訪問: 策略模組、風險評估
```

### 2. 性能優化建議

#### 索引優化
```sql
-- 常用查詢索引
CREATE INDEX idx_query_fast 
    ON candlestick_data(symbol, interval, timestamp DESC);

-- 範圍查詢索引  
CREATE INDEX idx_time_range 
    ON candlestick_data(timestamp, symbol, interval);

-- 資料源過濾索引
CREATE INDEX idx_source_filter 
    ON candlestick_data(data_source, symbol, interval);
```

#### 分區策略（未來擴展）
```sql
-- 按時間分區（每月一個分區）
CREATE TABLE candlestick_data_2025_01 (...);
CREATE TABLE candlestick_data_2025_02 (...);
-- ...自動分區管理
```

#### 緩存層
```python
# Redis緩存最新數據（可選）
CACHE_CONFIG = {
    'latest_candles': {
        'ttl': 60,  # 60秒過期
        'key_pattern': 'chart:{symbol}:{interval}:latest'
    },
    'indicator_values': {
        'ttl': 300,  # 5分鐘過期
        'key_pattern': 'indicator:{name}:{symbol}:{interval}'
    }
}
```

### 3. 並發控制

```python
# 使用連接池
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'sqlite:///database/charting.db',
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20
)

# 事務隔離
with engine.begin() as conn:
    # 批量插入使用事務
    conn.execute(insert_statement, data_batch)
```

### 4. 維護策略

```python
# 定期清理舊數據（保留最近N天）
RETENTION_DAYS = 90

def cleanup_old_data():
    """清理超過保留期的數據"""
    cutoff_date = datetime.now() - timedelta(days=RETENTION_DAYS)
    db.execute(
        "DELETE FROM candlestick_data WHERE timestamp < ?",
        [cutoff_date.timestamp()]
    )
    db.execute("VACUUM")  # 回收空間

# 定期重建索引
def rebuild_indexes():
    """重建索引以優化查詢"""
    db.execute("REINDEX")
```

### 5. 備份方案

```python
# 每日備份
def backup_chart_db():
    """備份 Web 資料庫"""
    backup_path = f"backups/charting_{datetime.now():%Y%m%d}.db"
    shutil.copy2("database/charting.db", backup_path)
    
    # 只保留最近7天備份
    cleanup_old_backups(days=7)
```

---

## 💡 性能目標

- **圖表加載**: < 500ms （10000根K線）
- **指標計算**: < 200ms
- **資料同步**: < 3s （1天數據，1440根K線）
- **UI響應**: < 100ms （任何操作）

---

## ✅ 成功標準

1. ✅ 能夠顯示所有支持的時間框架
2. ✅ real 和 Aggregation 數據顏色區分清晰
3. ✅ 3個技術指標正確顯示
4. ✅ 同步功能穩定可靠
5. ✅ UI流暢不卡頓
6. ✅ 獨立資料庫運行穩定

---

*文檔版本: 1.0*  
*創建日期: 2025-11-16*  
*狀態: 待實施*
