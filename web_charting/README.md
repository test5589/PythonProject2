# Web Charting Application

類似 TradingView 的 K線圖 Web 應用程式

## 🎯 功能特點

### K線圖顯示
- ✅ 多時間框架：1s, 2s, 5s, 10s, 15s, 30s, 1m, 5m, 10m, 30m, 1h, 4h, 8h
- ✅ 資料來源區分：
  - `real` 數據：深綠/深紅
  - `Aggregation` 數據：淺綠/淺紅
  - 低優先級數據：灰色
- ✅ 流暢60fps渲染

### 技術指標
1. **ADX and DI** - 趨勢強度指標
2. **Vegas 雙通道** - EMA 通道系統
3. **MA Cross 50 & 200** - 移動平均線交叉

### 獨立資料庫
- ✅ 不每次從主DB重新加載
- ✅ 手動控制資料同步
- ✅ 快速查詢優化
- ✅ 本地緩存

---

## 🏗️ 架構

### 技術棧

**前端**:
- React 18.2
- Lightweight Charts 4.1 (TradingView 開源版)
- Ant Design 5.11
- Zustand 4.4 (狀態管理)
- Vite 5.0 (構建工具)

**後端**:
- FastAPI 0.104
- SQLAlchemy 2.0
- Pandas 2.1
- NumPy 1.26

**資料庫**:
- SQLite (獨立資料庫)
- Redis (可選緩存)

### 目錄結構

```
web_charting/
├── backend/                  # 後端 API
│   ├── api/                  # API 路由
│   ├── database/             # 資料庫層
│   │   ├── models.py         # SQLAlchemy 模型
│   │   └── chart_db.py       # 資料庫管理器
│   ├── indicators/           # 指標計算
│   │   ├── adx.py
│   │   ├── vegas.py
│   │   └── ma_cross.py
│   ├── utils/                # 工具函數
│   ├── config.py             # 配置
│   ├── main.py               # FastAPI 主程式
│   └── requirements.txt      # Python 依賴
│
├── frontend/                 # 前端應用（待創建）
│   ├── src/
│   │   ├── components/       # React 組件
│   │   ├── api/              # API 調用
│   │   └── stores/           # 狀態管理
│   └── package.json
│
├── database/                 # 獨立資料庫
│   └── charting.db
│
└── docs/                     # 文檔
    ├── API.md
    ├── DATABASE_SCHEMA.md
    └── USER_GUIDE.md
```

---

## 📊 資料庫設計

### 主要表格

#### candlestick_data
K線資料表
```sql
CREATE TABLE candlestick_data (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(20),
    interval INTEGER,          -- 秒為單位
    timestamp REAL,            -- Unix timestamp
    open, high, low, close, volume REAL,
    data_source VARCHAR(20),   -- 'real', 'Aggregation', etc.
    priority INTEGER,          -- 資料優先級
    created_at, updated_at DATETIME
);
```

#### sync_history
同步記錄表
```sql
CREATE TABLE sync_history (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(20),
    interval INTEGER,
    start_time, end_time REAL,
    records_synced INTEGER,
    sync_status VARCHAR(20),   -- 'pending', 'running', 'completed', 'failed'
    error_message TEXT,
    created_at, completed_at DATETIME
);
```

#### indicator_cache
指標緩存表
```sql
CREATE TABLE indicator_cache (
    id INTEGER PRIMARY KEY,
    symbol VARCHAR(20),
    interval INTEGER,
    indicator_name VARCHAR(50),
    timestamp REAL,
    value REAL,
    params JSON
);
```

---

## 🚀 快速開始

### 方法 1: 一鍵啟動（推薦）

```bash
# Windows - 同時啟動後端和前端
start_all.bat
```

這將自動：
1. 啟動後端服務器（Port 8001）
2. 啟動前端服務器（Port 5173）
3. 打開兩個終端視窗

然後訪問: http://localhost:5173

---

### 方法 2: 分別啟動

#### 1. 後端設置

```bash
# 使用啟動腳本（推薦）
start_backend.bat

# 或手動啟動
cd web_charting/backend
pip install -r requirements.txt
python main.py
```

後端 API 將在 `http://localhost:8001` 運行

#### 2. 前端設置

```bash
# 使用啟動腳本（推薦）
start_frontend.bat

# 或手動啟動
cd web_charting/frontend
npm install
npm run dev
```

前端應用將在 `http://localhost:5173` 運行

---

## 📖 API 文檔

### 獲取 K線資料
```http
GET /api/charts/candles?symbol=BTCUSDT&interval=60&limit=1000
```

參數:
- `symbol`: 交易對（如 BTCUSDT）
- `interval`: 時間框架（秒，如 60 = 1分鐘）
- `limit`: 返回數量（默認1000，最大10000）
- `start_time`: 開始時間（可選，Unix timestamp）
- `end_time`: 結束時間（可選，Unix timestamp）
- `data_source`: 資料來源過濾（可選，如 "real"）

### 同步資料
```http
POST /api/sync
Content-Type: application/json

{
  "symbol": "BTCUSDT",
  "interval": 60,
  "start_time": null,
  "end_time": null,
  "overwrite": false
}
```

### 計算指標
```http
GET /api/indicators/adx?symbol=BTCUSDT&interval=60&period=14
GET /api/indicators/vegas?symbol=BTCUSDT&interval=60
GET /api/indicators/ma-cross?symbol=BTCUSDT&interval=60
```

---

## 🎨 顏色配置

```javascript
const COLORS = {
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
};
```

---

## 📈 性能目標

- 圖表加載: < 500ms （10000根K線）
- 指標計算: < 200ms
- 資料同步: < 3s （1天資料）
- UI響應: < 100ms

---

## 🔧 配置

編輯 `backend/config.py` 來調整配置：

```python
# 時間框架
TIMEFRAMES = [1, 2, 5, 10, 15, 30, 60, 300, 600, 1800, 3600, 14400, 28800]

# 資料庫路徑
CHART_DB_PATH = "database/charting.db"
MAIN_DB_PATH = "../database/historical_data.db"

# API 設置
HOST = "0.0.0.0"
PORT = 8001

# 性能設置
DEFAULT_CANDLES_LIMIT = 1000
MAX_CANDLES_LIMIT = 10000
BATCH_SIZE = 1000
```

---

## 📋 開發計劃

### ✅ 階段1: 基礎架構（已完成）
- [x] 創建項目結構
- [x] 設置配置系統
- [x] 設計資料庫模型

### ⏳ 階段2: 核心功能（進行中）
- [ ] 資料庫管理器
- [ ] 基本API路由
- [ ] React前端框架

### 📅 階段3: K線圖（待開始）
- [ ] Lightweight Charts 整合
- [ ] 多時間框架切換
- [ ] 顏色區分實現

### 📅 階段4: 資料同步（待開始）
- [ ] 主DB連接器
- [ ] 同步管理器
- [ ] 增量同步邏輯

### 📅 階段5: 技術指標（待開始）
- [ ] ADX and DI
- [ ] Vegas 雙通道
- [ ] MA Cross 50 & 200

### 📅 階段6: 優化（待開始）
- [ ] 性能優化
- [ ] UI/UX 優化
- [ ] 測試和調試

**預計完成時間**: 7-12天

---

## 🤝 貢獻

這是一個內部項目，目前不接受外部貢獻。

---

## 📄 許可證

專有軟體 - 保留所有權利

---

## 📞 支持

有問題或建議？查看文檔：
- [完整開發計劃](../docs/WEB_CHARTING_APP_PLAN.md)
- [API文檔](docs/API.md)
- [資料庫結構](docs/DATABASE_SCHEMA.md)
- [使用指南](docs/USER_GUIDE.md)

---

*最後更新: 2025-11-16*  
*版本: 0.1.0*  
*狀態: 開發中*
