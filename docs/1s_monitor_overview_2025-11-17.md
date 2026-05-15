# 1 秒 K 線監控與 Web 圖表資料流整理（2025-11-17）

## 1. 系統整體架構與角色

- **GUI 主程式 / 監控系統**
  - 使用 WebSocket（Binance）取得即時行情。
  - 透過 `ws_aggregator` 聚合成 1 秒 OHLCV。
  - 透過 `data_manager.insert_data` 寫入主資料庫 `system_data.db` 的 `historical_data` 表。
  - 所有「真實資料」一律寫入這個主資料庫。

- **Web Charting 應用（前後端）**
  - 後端：FastAPI（`web_charting/backend`）。
  - 前端：React + Ant Design + Lightweight Charts（`web_charting/frontend`）。
  - 自己有一個獨立的 `charting.db`，用來快取 / 同步 K 線（分鐘級以上）。
  - **重要規則**：Web Charting 不得把聚合 / 插值過的資料寫回主資料庫 `system_data.db`。

- **資料庫分工**
  - `system_data.db`（主 DB）
    - 表：`historical_data`。
    - 來源：監控系統 + 歷史下載。
    - 儲存真實 1 秒、1 分鐘等不同 interval 的 K 線。
  - `charting.db`（Web Chart DB）
    - 表：`candlestick_data`（ORM 定義在 `backend/database/models.py`）。
    - 來源：後端 `/api/sync` 從主 DB 同步過來。
    - 目前僅用於 **分鐘級以上** 的圖表快取。

---

## 2. 1 秒監控與寫入流程

### 2.1 WebSocket 聚合與寫入

- 檔案：`modules/utils/data/ws_aggregator.py`
  - 功能：接收交易所 WebSocket 報價，將 Tick 聚合成 1 秒 OHLCV。

- 檔案：`modules/utils/database/data_manager.py`
  - 函數：`insert_data(category, symbol, interval, kline, data_source='real', ...)`
  - 行為：
    - 驗證 K 線資料。
    - 根據 `data_source` 與優先級判斷是否覆蓋。
    - 對 `historical_data` 做 `INSERT OR REPLACE`（但會遵守優先級不覆蓋更高級資料）。

- 主 DB schema（`db_core.py` / `historical_data`）：
  - 核心欄位：`timestamp, readable_time, category, symbol, interval, open, high, low, close, volume`。
  - 其他欄位：`open_time, close_time, quote_asset_volume, num_trades, taker_base_vol, taker_quote_vol, data_source, interp_note, api`。
  - PK：`(timestamp, category, symbol, interval, api)`。

### 2.2 我們驗證 1 秒資料是否真的寫入

- 建立測試腳本 `web_charting/frontend/src/88888.py`：

  ```python
  import os
  import sys

  CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
  PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", ".."))
  if PROJECT_ROOT not in sys.path:
      sys.path.insert(0, PROJECT_ROOT)

  from modules.utils.database.db_core import query_ohlcv

  symbol = "BTCUSDT"
  rows = query_ohlcv('crypto', symbol, 1, limit=10)
  print("len(rows) =", len(rows))
  for r in rows:
      print(r)
  ```

- 在虛擬環境下執行：

  ```powershell
  & .venv\Scripts\Activate.ps1
  python web_charting/frontend/src/88888.py
  ```

- 實際輸出（節錄）：

  ```text
  len(rows) = 10
  (1763388862.0, '2025-11-17 14:14:22', 'crypto', 'BTCUSDT', 1, ...)
  ... 共 10 筆 ...
  ```

- 結論：
  - `system_data.db` 中 **確實有 BTCUSDT 的 1 秒 K 線**（`interval=1`）。
  - 1 秒監控寫入流程正常。

---

## 3. Web Charting 後端：1 秒 / 子分鐘 K 線處理

### 3.1 主資料庫連接器

- 檔案：`web_charting/backend/database/main_db_connector.py`
- 重要設定：
  - 透過 `config.database.MAIN_DB_PATH` 指向主專案根目錄下的 `data/system_data.db`。
  - `fetch_candles(...)` 會執行類似：

    ```sql
    SELECT symbol, interval, timestamp, open, high, low, close, volume, data_source
    FROM historical_data
    WHERE category = :category
      AND symbol = :symbol
      AND interval = :interval
      AND timestamp >= :start_time
      AND timestamp <= :end_time
    ORDER BY timestamp ASC
    ```

- 確認：後端與我們在 `88888.py` 測試中使用的是 **同一個 system_data.db**。

### 3.2 `/api/charts/candles` 子分鐘處理

- 檔案：`web_charting/backend/api/charts.py`
- 主要結構：
  - `GET /api/charts/candles`
    - 若 `interval < 60`：呼叫 `_build_subminute_response(...)`，從 **主 DB** 讀取 1 秒資料，在記憶體中聚合。
    - 若 `interval >= 60`：改走 `chart_db.query_candles(...)`（分鐘以上用 Web Chart DB）。

- `_build_subminute_response(...)` 行為：

  - 計算時間範圍：

    ```python
    tw = _calculate_time_window(interval, limit, start_time, end_time)
    start_ts = tw["start"]
    end_ts = tw["end"]
    ```

  - 從主 DB 拉 1 秒資料：

    ```python
    raw_1s = main_db.fetch_candles(
        category="crypto",
        symbol=symbol_up,
        interval=1,
        start_time=start_ts,
        end_time=end_ts,
        data_source=one_sec_source_filter,
    )
    ```

  - 若 `interval == 1`：
    - 直接對 `raw_1s` 排序、裁切 `limit`，組成 `CandlesListResponse` 回給前端。

  - 若 `interval in {2,5,10,15,30}`：
    - 先用 `_select_best_1s_candles` 依 `data_source` 優先級挑出每秒最佳一個。
    - 再用 `_aggregate_1s_to_interval` 在記憶體中聚合成目標秒數的 K 線。
    - **不寫回任何資料庫，只回傳給前端**。

### 3.3 時間窗修正（今天重要變更）

- 原本 `_calculate_time_window(...)`：
  - 預設抓 `limit * interval` 秒的資料，但不超過 24 小時。
  - 結果：如果使用者在某段時間後才打開圖表，時間窗可能只涵蓋「最近幾秒」，抓不到較早寫入的 1 秒資料，API 會回 `{ count: 0 }`。

- 今天修改後：

  ```python
  # 對於子分鐘時間框架，預設回溯整整 24 小時，之後在記憶體中用 limit 做裁剪
  window_seconds = 86400  # 固定 24 小時
  effective_start = max(0.0, effective_end - window_seconds)
  ```

- 效果：
  - `/api/charts/candles?symbol=BTCUSDT&interval=1&limit=10` 現在會回傳最近 24 小時內、時間排序後最後 10 根 1 秒 K 線。
  - 實際測試 JSON（節錄）：

    ```json
    {
      "symbol": "BTCUSDT",
      "interval": 1,
      "count": 10,
      "candles": [
        {"timestamp": 1763303681.0, "open": 95475.65, ...},
        ... 共 10 根 ...
      ],
      "time_range": {
        "start": "2025-11-16 22:34:41",
        "end": "2025-11-16 22:34:55"
      }
    }
    ```

- 結論：後端 1 秒資料 API 已可正常返回主 DB 的 1 秒 K 線。

---

## 4. 前端資料流與自動更新

### 4.1 App 狀態管理（`App.jsx`）

- 重要狀態：
  - `symbol`：目前選擇的交易對（預設 `BTCUSDT`）。
  - `interval`：時間框架（以秒為單位，預設 60）。
  - `dataSource`：資料來源過濾（`all` / `real` / `Aggregation`）。
  - `candlesData`：傳給圖表的 K 線資料陣列。
  - `monitoring`：是否處於「1 秒監控模式」。
  - 其它：`loading`, `lastSyncTime`, `monitorSymbols` 等。

- 載入 K 線：`loadCandles`：

  ```jsx
  const params = new URLSearchParams({
    symbol,
    interval,
    limit: 3000,
  })
  if (dataSource !== 'all') {
    params.append('data_source', dataSource)
  }
  const url = `/api/charts/candles?${params}`
  const response = await fetch(url)
  const data = await response.json()
  setCandlesData(data.candles || [])
  ```

- 初始載入 / 參數變化：

  ```jsx
  useEffect(() => {
    loadCandles()
    fetchMonitorStatus()  // /api/monitor/status
  }, [loadCandles, fetchMonitorStatus])
  ```

### 4.2 1 秒監控與自動輪詢

- 啟動 1 秒監控（按鈕在 `ControlPanel`）：

  ```jsx
  const startMonitoring = async () => {
    setInterval(1)
    ...
    const response = await fetch('/api/monitor/start', { method: 'POST', body: JSON.stringify({ category: 'crypto' }) })
    const data = await response.json()
    setMonitoring(!!data.monitoring)
    setMonitorSymbols(data.symbols || [])
  }
  ```

- 自動每秒重新抓 `/api/charts/candles`：

  ```jsx
  useEffect(() => {
    if (!monitoring) {
      return
    }

    console.log('⏱ 啟動監控模式，每秒自動載入 K 線')
    const id = window.setInterval(() => {
      loadCandles()
    }, 1000)

    return () => {
      console.log('⏹ 停止監控模式自動載入')
      window.clearInterval(id)
    }
  }, [monitoring, loadCandles])
  ```

- 也就是說：
  - **只有在 `monitoring === true` 的時候**，前端才會每秒自動刷新資料。
  - 若 `monitoring === false`，圖只會在：
    - 初次載入。
    - time frame / symbol 改變。
    - 手動按「重新整理」或同步之後。  
    這幾個時刻更新一次，不會持續動。

### 4.3 圖表組件渲染方式（`CandlestickChart.jsx`）

- 每次 `candlesData` 改變：
  - 清除舊的 series。
  - 依 `data_source` 分成 `real` / `Aggregation` / 低優先級，建立不同顏色的 series。
  - 只在第一次有資料時呼叫 `timeScale().fitContent()`，避免每次更新都重置使用者視圖。

- 時間欄位：

  ```jsx
  time: Math.floor(candle.timestamp)
  ```

  即直接把後端回來的 `timestamp`（秒）拿來當圖表的時間座標，符合 Lightweight Charts 要求。

---

## 5. 今天目前為止的關鍵結論

1. **主 DB 1 秒資料寫入正常**
   - `system_data.db` 的 `historical_data` 有 BTCUSDT 的 1 秒 K 線。
   - 已用獨立腳本 `88888.py` 驗證。

2. **Web Charting 後端 1 秒 API 正常**
   - `/api/charts/candles?symbol=BTCUSDT&interval=1` 現在會回 `count=10`、`data_source='real'` 的 1 秒 K 線。
   - 修正 `_calculate_time_window` 後，預設回溯 24 小時。

3. **前端能畫出 1 秒 K 線，但目前「不會持續更新」**
   - 已經有一段 K 線顯示出來（證明前端解析資料與繪圖 OK）。
   - 下一步要確認：
     - `monitoring` 是否成功切換成 `true`（UI Tag 會顯示「1秒監控：運行中」）。
     - 1 秒監控是否有持續寫入新資料（透過多次執行 `88888.py` 檢查 timestamp 是否往後移）。
     - 若資料有在變、前端也每秒抓，但圖仍不動，則需要調整圖表的視窗自動 follow 最新 K 線邏輯。

---

## 6. 後續延伸工作（概要）

> 詳細的「目前問題 & 待辦清單」會在另一份 `1s_monitor_issues_and_next_steps_2025-11-17.md` 中整理。

- 子分鐘時間框架的完整 template：
  - 1 秒實際資料為基礎。
  - 用 1 分鐘資料補洞 / 插值 1 秒（未來步驟）。
  - 在記憶體內將 1 秒聚合為 2/5/10/15/30 秒，不寫回主 DB。

- 前端：
  - 確保選擇 `1s` 時會自動使用主 DB 的資料流。
  - 改善自動更新與視圖控制，讓 1 秒圖在監控模式下可以穩定向右推進，又不一直重置使用者的縮放。
