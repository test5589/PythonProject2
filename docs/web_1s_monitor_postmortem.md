# Web 1 秒監控 K 線問題修復反省報告

## 一、問題背景

- **現象**：
  - 在 Web 前端啟用 1 秒監控、timeframe 停在 1S 時，圖表有在每秒重新載入，但最新 K 線與價格看起來「沒有在動」。
  - 1 秒 K 線數量（例如 68940）長時間維持不變，讓人懷疑監控沒有寫入或 API 沒有更新。
- **目標**：
  - 監控啟用後，1S 圖必須能跟隨最新成交 K 線。
  - 明確區分「整天累積的 1S K 線總數」與「當前 1S 時間窗內的 K 棒數」。
  - 監控卡住時要有明確提示，而不是讓使用者自己猜。

---

## 二、最終真正關鍵、讓 1S 圖正常的修正

### 1. 後端：1 秒監控時改用主 DB 最新秒線

**位置**：`web_charting/backend/api/charts.py` → `get_candles`

**關鍵邏輯**：

- 當 `interval == 1` 且 `realtime == True`（監控 + 1S timeframe）：
  - 不再用 `get_data_range` 推 end_time，而是直接用「現在時間」作為查詢窗：
    - `now_ts = datetime.utcnow().timestamp()`
    - `start_ts = now_ts - limit * 1`
    - 時間窗 = `(start_ts, now_ts)`
  - 將這個時間窗丟給 `_build_subminute_response`，從 **主 DB** 抓出最新 600 秒的 1S K 線。

**效果**：

- 只要監控有持續寫 1 秒資料進 `system_data.db`，
- 每次 `/api/charts/candles?interval=1&realtime=true` 都會拿到「最新尾端」的秒線，
- 解決了「主 DB 有資料但 API 沒抓到最新」的風險。

---

### 2. 前端：監控 + 1S 一律帶 `realtime=true`

**位置**：`web_charting/frontend/src/hooks/useCandles.js`

**關鍵邏輯**：

- 建立 `/api/charts/candles` 時：

  ```js
  if (monitoring && (Number(interval) === 60 || Number(interval) === 1)) {
    params.append('realtime', 'true')
  }
  ```

- 原本只有 1 分鐘（60s）會帶 `realtime=true`，現在 1 秒也會。

**效果**：

- 監控 + 1S 圖不再走 Web Chart DB 的舊資料，而是直接走主 DB 即時路徑。
- 搭配後端修正，前端每秒請求的 1S K 線都會是「以現在時間為基準的最新秒線」。

---

### 3. 前端圖表：監控模式每次更新都 `scrollToRealTime()`

**位置**：`web_charting/frontend/src/components/BaseCandlestickChart.jsx`

**關鍵邏輯**：

- 在 `useEffect(..., [candlesData])` 的自動視圖調整中：

  ```js
  if (!hasAutoFitRef.current) {
    // 首次載入的處理（略）
  } else {
    // 監控模式下，不論是否為子分鐘 timeframe，都強制自動跟隨最新 K 線
    if (monitoring) {
      if (chartRef.current) {
        chartRef.current.timeScale().scrollToRealTime()
      }
      console.log('🔄 監控模式：自動跟隨最新 K 線', { isSubMinute })
    } else if (!isSubMinute) {
      // 非監控模式下，僅對分鐘以上 timeframe 嘗試跟隨
      if (chartRef.current) {
        chartRef.current.timeScale().scrollToRealTime()
      }
      console.log('🔄 非監控模式：分鐘以上使用 scrollToRealTime 跟隨')
    } else {
      console.log('ℹ️ Skip auto scroll:', { monitoring, isSubMinute })
    }
  }
  ```

**效果**：

- 只要 `monitoring === true`，每次 K 線資料更新後都會自動捲到最新 K 棒。
- 排除「資料其實有更新，但視窗還停在舊位置」造成的錯覺。

---

### 4. 前端：1S 監控「卡住」偵測與警告

**位置**：`web_charting/frontend/src/hooks/useCandles.js`

**關鍵邏輯**：

- 在 1S + 監控狀態下，每次成功取得 `data.candles` 時：

  ```js
  const is1s = Number(interval) === 1

  if (is1s && monitoring) {
    const latest = data.candles[data.candles.length - 1]
    const latestTs = latest?.timestamp
    if (latestTs) {
      if (last1sTimestampRef.current != null && latestTs <= last1sTimestampRef.current) {
        noProgressCounterRef.current += 1
      } else {
        last1sTimestampRef.current = latestTs
        noProgressCounterRef.current = 0
      }

      if (noProgressCounterRef.current >= 10) {
        const now = Date.now()
        if (!lastStallWarningRef.current || now - lastStallWarningRef.current > 30000) {
          lastStallWarningRef.current = now
          message.warning('1 秒監控已啟動，但最近一段時間 1 秒K線沒有更新，可能是 1 秒監控模組沒有持續寫入主資料庫')
        }
      }
    }
  }
  ```

**效果**：

- 若連續多次輪詢最新 timestamp 都沒有往前推進：
  - 約 10 秒內會跳出警告，提醒「監控可能沒寫入」。
- 將來如果真的監控掛掉，使用者不用再自己猜、自己看 console。 

---

### 5. 前端：清楚標示兩種不同的 K 線數量

**位置**：
- `web_charting/frontend/src/hooks/useCandles.js`
- `web_charting/frontend/src/App.jsx`
- `web_charting/frontend/src/components/BaseCandlestickChart.jsx`

**關鍵邏輯**：

1. 在 `useCandles` 中新增 state：

   ```js
   const [currentWindowCount, setCurrentWindowCount] = useState(0)
   ```

   每次成功取得 `data.candles` 後，記錄這次時間窗內實際 K 線數：

   ```js
   if (data.candles && data.candles.length > 0) {
     setCurrentWindowCount(data.candles.length)
     // ...原本的合併邏輯...
   }
   ```

2. 在 `App.jsx` 中，把 `currentWindowCount` 傳給圖表：

   ```js
   const { candlesData, loading, loadCandles, backfillStatus, currentWindowCount } = useCandles({...})

   <CandlestickChart
     symbol={symbol}
     interval={interval}
     candlesData={candlesData}
     loading={loading}
     monitoring={monitoring}
     currentWindowCount={currentWindowCount}
   />
   ```

3. 在 `BaseCandlestickChart` 顯示兩個數字：

   ```jsx
   {candlesData.length > 0 && (
     <span className="candles-count">
       累積 1 秒 K 線總數（從最早一筆到目前）：{candlesData.length} 根
     </span>
   )}

   {interval === 1 && currentWindowCount > 0 && (
     <span className="candles-count" style={{ marginLeft: '12px' }}>
       當前 1 秒時間窗實際 K 線數（不含右側空白）：{currentWindowCount} 根
     </span>
   )}
   ```

**效果**：

- **累積總數**：代表目前前端手上「今天從最早到現在」的全部 1 秒 K 線格子數。
- **當前時間窗 K 棒數**：代表這一次 API 回傳的這段 1 秒時間窗裡，實際有幾根 K 線（不含右側空白區域）。
- 避免再用單一數字（例如 68940）來判斷「有沒有在更新」，而忽略實際時間與價格變化。

---

## 三、邏輯錯誤與繞路的反省

### 1. 用「K 線總數」當作有無更新的判斷指標是錯的

- 一開始看到 `68940` 不變，我也朝「沒寫入」那方向懷疑。
- 但在這個系統設計裡：
  - 回補 / 補線已經先把當天的秒都填滿。
  - 1 秒監控多數是在「同一秒上覆蓋價格」，不是新增新的秒數。
- **正確做法**：
  - 用 `time_range.end_timestamp` 和最新 K 線價格判斷有無更新，
  - 而不是用總筆數來推測。

### 2. 過度懷疑「監控沒寫入 / 主 DB 沒更新」

- 在看到 `time_range` 之前，我一直假設：
  - 也許主 DB 沒新資料，
  - 監控沒寫入，所以圖不動。
- 但你貼出的兩次 `end_timestamp` 明顯在往後走：
  - 直接證明 DB 有新的秒線，API 也有抓到。
- **應該要做的**：
  - 一開始就請你貼 `time_range`，先確認「時間有沒有在往前」。
  - 一旦確認有，就應立刻把重點轉到前端視圖（auto scroll / 視窗邊界）與 UI 標示。

### 3. 在監控 process / GUI process 細節上花了太多篇幅

- 雖然從系統架構來看：
  - Web 後端與 GUI 各自有一套 `MultiSymbolMonitor`，
  - 不同 process 的 `_global_monitor` 確實互不影響。
- 但在這次「1S 圖不動」的實際問題上：
  - 真正關鍵是 API + 前端圖表，
  - process 細節講太多，對解決當下 bug 幫助有限，反而讓流程變複雜。

### 4. 說明過長，沒有完全遵守「白話 + 重點」的要求

- 在你多次明講「白話、不要廢話」的情況下，
  - 我仍然在某些回覆中講太多背景、操作細節，
  - 沒有優先用一兩句話直接講結論，造成溝通成本上升。

---

## 四、未來遇到類似問題的排錯流程（自我要求）

1. **先看後端時間軸**
   - 優先檢查 `/api/charts/candles` 回應的 `time_range.end_timestamp` 是否有變化。
   - 若有變化 → DB + API 正常，問題在前端視圖。
   - 若無變化 → 再去看監控模組 / 寫 DB 邏輯。

2. **以「最新一筆」為指標，不再用總數推測**
   - 顯示並檢查：
     - 最新 K 線的 timestamp
     - 最新 K 線的 close 價格
   - 不再用 `candlesData.length` 是否變化來判斷「有沒有更新」。

3. **先確認圖表視窗與 auto-scroll 邏輯**
   - 確認：
     - 每次資料更新都有觸發 `scrollToRealTime()`（在需要的模式下）。
     - 視窗顯示範圍是否已經在最後幾根 K 線附近。
   - 再處理像「右側空白」這類 UX 細節。

4. **說明上：先一句結論，再必要細節**
   - 回覆格式控制為：
     - 第一段：一句話講結論或是「現在會做什麼」。
     - 後面才用條列、短段落補充，避免讓說明本身變成干擾。

---

## 五、結語

這次 1 秒監控問題的真正解法，是把：

- **資料流**（監控寫入主 DB → API 以現在時間為基準抓最新 1 秒）、
- **圖表行為**（監控下強制自動跟隨最新 K 線）、
- **數字標示**（清楚分開「累積總數」與「當前時間窗 K 棒數」）

三件事打通。

我在過程中一開始過度聚焦在監控寫入與 GUI 細節，沒有立刻用你要的「白話、重點」方式處理，這是這份反省報告最重要的教訓。
