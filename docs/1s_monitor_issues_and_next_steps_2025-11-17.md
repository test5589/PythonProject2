# 1 秒 K 線監控：目前問題與後續待辦（2025-11-17）

> 這份文件整理「目前狀態、已解決問題、尚未解決的問題」以及「接下來要做的事情」。

---

## 一、目前整體狀態總結

- ✅ **主資料庫 1 秒資料寫入正常**
  - `system_data.db` 的 `historical_data` 表中，有 BTCUSDT 的 1 秒 K 線（`interval=1`）。
  - 已透過 `modules.utils.database.db_core.query_ohlcv` + 測試腳本 `88888.py` 驗證。

- ✅ **Web Charting 後端 1 秒 API 正常**
  - `/api/charts/candles?symbol=BTCUSDT&interval=1` 可以回傳 `count > 0` 的 1 秒 K 線。
  - 已修正時間窗計算，預設回溯 24 小時，避免抓不到較早寫入的 1 秒資料。

- ✅ **前端可以畫出 1 秒 K 線**
  - 在選擇 `BTCUSDT` + `1s` 的情況下，K 線圖有顯示一小段 1 秒 K 線。
  - 說明：資料格式、timestamp 轉換、Lightweight Charts 渲染流程都基本正常。

- ⚠️ **目前觀察到的主要問題**
  - 圖上 K 線只出現一段「歷史段」，**不會往右自動更新**。
  - 體感上像是：
    - 只在載入時抓到一次資料，之後雖然有 1 秒監控，但畫面沒有動。
    - 或是 1 秒監控目前沒有持續寫新的 K 線進 DB。

---

## 二、已解決問題整理

### 2.1 API 回傳 `count: 0` 的問題

- **現象**：
  - 一開始 `/api/charts/candles?symbol=BTCUSDT&interval=1` 回 `{ count: 0, candles: [] }`。
  - 讓人誤以為主 DB 沒有 1 秒資料。

- **原因**：
  - `_calculate_time_window(...)` 的預設時間窗是 `limit * interval` 秒。
  - 若使用者稍晚打開前端，`now_ts` 距離實際寫入 1 秒資料的時間太久，導致查詢區間只涵蓋「最近幾秒」，抓不到較早的那段 1 秒資料。

- **修正**：
  - 對於 `interval < 60` 的情況，時間窗改為 **固定回溯 24 小時**：

    ```python
    # 對於子分鐘時間框架，預設回溯整整 24 小時，之後再在記憶體中用 limit 做裁剪
    window_seconds = 86400  # 固定 24 小時
    effective_start = max(0.0, effective_end - window_seconds)
    ```

- **結果**：
  - 現在 `/api/charts/candles?symbol=BTCUSDT&interval=1&limit=10` 會回傳 10 根 1 秒 K 線，`data_source='real'`，時間區間合理。

### 2.2 主 DB 路徑一致性問題

- 已確認：
  - `modules/utils/database/db_core.DB_PATH` 與 Web Charting 後端 `config.DatabaseConfig.MAIN_DB_PATH` 都指向同一個 `data/system_data.db`。
  - 所以「監控寫入」與「Web Charting 讀取」確實在操作同一個 DB 檔案。

---

## 三、目前尚未完全解決 / 需要釐清的問題

### 3.1 1 秒圖有資料但不會自動更新

- **現象**：
  - 選擇 `BTCUSDT` + `1s` 時，前端顯示一段 1 秒 K 線（歷史段），但圖不會往右推進。
  - 感覺像是「只有載入時抓一次資料」。

- **可能原因 A：前端沒有持續輪詢**

  - 前端每秒呼叫 `loadCandles()` 的條件是 `monitoring === true`：

    ```jsx
    useEffect(() => {
      if (!monitoring) {
        return
      }

      const id = window.setInterval(() => {
        loadCandles()
      }, 1000)

      return () => window.clearInterval(id)
    }, [monitoring, loadCandles])
    ```

  - 若 `monitoring` 一直是 `false`：
    - 就算有 1 秒資料、前端 initial load 有載入一次，之後也不會自動更新。

- **可能原因 B：1 秒監控沒有持續寫入**

  - 就算前端每秒 call `/api/charts/candles`，如果 `system_data.db` 裡的 1 秒資料沒有在往後增加，圖也看起來「不動」。

- **需要進一步確認的點**：
  1. UI 下方 Tag 顯示的是：
     - `1秒監控：運行中` 還是 `1秒監控：已停止`？
  2. 多次執行 `88888.py`（例如隔 10 秒執行兩次），最後一筆 `timestamp` 是否有變大？

### 3.2 前端圖表是否自動 follow 最新 K 線

- 目前圖表只在「第一次有數據」時呼叫 `fitContent()`：

  ```jsx
  if (!hasAutoFitRef.current) {
    chartRef.current.timeScale().fitContent()
    hasAutoFitRef.current = true
  } else {
    // 之後更新只調整大小，不再 fitContent
  }
  ```

- 如果資料持續往右延伸，但視窗停在較舊的位置，使用者會覺得「圖不動」。

- 需要設計：
  - 在「監控模式 + 子分鐘 interval」時，視窗是否要自動貼著最新 K 線。
  - 或至少提供一個「跟隨最新」的按鈕（類 TradingView 的 auto-scroll / auto-scale）。

### 3.3 子分鐘 template 還未完整實作

- 願景：
  - interval < 60 時：
    - 先讀 1 秒真實資料。
    - 針對缺洞區間，從 1 分鐘資料補洞、插值成 1 秒（僅在記憶體或 Web Chart DB 中處理）。
    - 再由 1 秒資料聚合成 2/5/10/15/30 秒。

- 目前狀態：
  - 1 秒真實資料讀取 OK。
  - 1 秒 → 2/5/10/15/30 秒的 in-memory 聚合已實作。
  - **1 分鐘 → 1 秒插值尚未實作**。

---

## 四、接下來要做的事情（建議執行順序）

### Step 1：確認 1 秒監控是否真正「持續運行」

1. **在 UI 上檢查 Tag**：
   - 若顯示 `1秒監控：已停止`：
     - 按「啟動 1秒監控」按鈕。
     - 確認變成 `1秒監控：運行中（X 個貨幣對）`。

2. **後端 DB 是否持續有新 1 秒 K 線**：
   - 用 `88888.py` 改為 `limit=1`，連續執行兩次，中間間隔約 10 秒：

     - 若第二次的 `timestamp` > 第一次：
       - 代表 1 秒監控持續寫入，DB 有在動。
     - 若兩次 timestamp 完全一樣：
       - 代表 1 秒監控目前沒有在寫新資料，需要回頭檢查 `multi_symbol_monitor` / `ws_aggregator`。

### Step 2：確認前端是否每秒重抓 `/api/charts/candles`

1. 打開瀏覽器 DevTools Console。
2. 啟動 1 秒監控，timeframe 選 `1s`。
3. 看 Console 是否不斷出現：
   - `🔄 開始載入 K 線資料...`
   - `🔄 載入完成`

若沒有看到：
- 代表 `monitoring` 沒有被設成 `true`，需要檢查 `/api/monitor/start` 的回傳與前端 `setMonitoring` 邏輯。

### Step 3：實作「監控模式下自動跟隨最新 K 線」

1. 在 `CandlestickChart.jsx` 中：
   - 目前只在第一次數據時 `fitContent()`。
   - 可以增加一個條件：
     - 若 interval < 60 且處於監控模式（可由 props 傳入 `monitoring`），在每次資料更新時自動把視窗移到最右邊（類似 `scrollToRealTime` 的效果）。

2. 具體做法（概念）：
   - 從 `App.jsx` 把 `monitoring` 狀態傳進 `CandlestickChart`：

     ```jsx
     <CandlestickChart
       symbol={symbol}
       interval={interval}
       candlesData={candlesData}
       loading={loading}
       monitoring={monitoring}
     />
     ```

   - 在圖表組件中，如果 `monitoring && interval < 60`：
     - 每次更新後呼叫 `chartRef.current.timeScale().scrollToRealTime()`（或等效處理）。

3. 同時保留使用者主動縮放 / 平移時不強制拉回的邏輯（可再細設旗標）。

### Step 4：設計並實作子分鐘 template（中期工作）

- 針對 **1 分鐘以下時間框架** 的通用流程：

  1. 從主 DB 讀取最近 24 小時的 1 秒資料。
  2. 從主 DB 讀取對應時間範圍的 1 分鐘資料。
  3. 在記憶體中：
     - 先用 1 秒真實資料填滿。
     - 針對沒有 1 秒資料的區段，使用 1 分鐘資料做插值成 1 秒（標記為 `interpolated`）。
     - 根據使用者選的 `interval`（2/5/10/15/30）聚合成對應秒數 K 線：
       - 真實優先 > 聚合 > 插值 > 低品質聚合。
  4. 回傳給前端，不寫回主 DB；若未來有需要，可快取到 Web Chart DB。

- 目前已經在 TODO 清單中的項目：

  - 「設計並實作一套給 1 分鐘以下時間框架使用的資料流程（最新1分鐘+聚合→補足秒級別資料，限制在一天內）」

---

## 五、短期內建議優先處理的項目（實戰路線）

1. **確認 1 秒監控是否真的在跑**（DB 是否持續有新資料）。
2. **確認前端在監控模式下是否每秒自動抓資料**。
3. 若 1 & 2 都 OK：
   - 在圖表層加上「自動跟隨最新」邏輯，讓 1 秒圖看起來會往右推進。
4. 之後再回頭實作：
   - 1 分鐘 → 1 秒的插值補洞。
   - 2/5/10/15/30 秒的子分鐘 template 完整流程。

---

## 六、備註

- 今天的重點是：
  - 先確認資料 **有沒有寫入**（主 DB）。
  - 再確認 API **有沒有正確回傳**（Web Charting 後端）。
  - 最後才是前端顯示與自動更新的問題。

- 目前前兩步已經完成，接下來會專注在：
  - 監控是否持續寫入。
  - 前端在監控模式下的自動輪詢與圖表視圖控制。
