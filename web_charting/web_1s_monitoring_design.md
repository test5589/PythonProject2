# Web 端 1 秒監控設計說明

> 快速讓未來的自己（或我）在幾分鐘內回想起 Web 端 1 秒監控的整體設計與易踩坑位置。

---

## 1. 整體架構概念

- 主程式有一個「多貨幣對 1 秒監控模組」：`modules.monitors.multi_symbol_monitor.MultiSymbolMonitor`
- 真正負責把 1 秒 K 線寫入 **主資料庫** 的，是 MultiSymbolMonitor 裡的 aggregator（WS 收集 + DataManager 寫入）。
- **Web 端不直接寫主 DB**：
  - Web 只透過 FastAPI `/api/monitor/*` 控制 **啟動/停止/查詢狀態**。
  - Web Chart 前端只讀取主 DB 或 Web Chart DB 來畫圖，不參與寫入。
- GUI 與 Web 兩邊共用同一個 MultiSymbolMonitor 實例，因此：
  - 任一端啟動 1 秒監控，另一端看到的都是同一組監控狀態與寫入結果。

---

## 2. 控制入口總覽

### 2.1 GUI 入口（桌面程式）

- 檔案：`core/gui_monitoring.py`
- 類別：`GUIMonitoring`
- 關鍵方法：
  - `start_ws()`
    - 檢查模板是否為 A，必要時提示並自動切換（`MainGUI.set_monitor_template('A')`）。
    - 固定 `max_symbols = 5`。
    - 候選清單來自 `TradingConfig.SUPPORTED_SYMBOLS[:20]`（對應模板 A 的 20 檔）。
    - 呼叫 `core.gui_symbol_selector.select_symbols_for_backfill` 讓使用者在 GUI 選幣（最多 5 檔）。
    - 成功啟動後：
      - 更新 `controls.monitor_symbol_limit_var` 顯示實際選到幾檔（1~5）。
      - 呼叫 `self._multi_monitor.start_all_symbols_1s(..., specific_symbols=selected_symbols)`。
      - 呼叫 `gui.on_monitor_started()` 記錄開始時間與重設統計。
  - `stop_ws()`
    - 呼叫 `self._multi_monitor.stop_all_symbols_1s()` 停止監控。
    - 還原 GUI 按鈕狀態、將 `monitor_symbol_limit_var` 重新設為 `"(待選)"`。
    - 呼叫 `gui.on_monitor_stopped()` 記錄結束時間並寫入 summary log。

> **對應畫面：** 模板 A 由 `core/gui/monitor_board_template.py` 與 `MainGUI._update_dynamic_field` 負責，顯示每檔 1 秒寫入狀態與統計。

### 2.2 Web 入口（FastAPI + React 前端）

#### Backend：`web_charting/backend/api/monitor.py`

- 路由前綴：`/api/monitor`
- `POST /api/monitor/start`
  - Request model：`MonitorStartRequest`：
    - `category: str = 'crypto'`
    - `symbols: List[str] | None = None`
  - 邏輯：
    - 先取得共用的 `monitor = get_multi_symbol_monitor()`。
    - **若 `request.symbols` 有值**：
      - 正規化成大寫、去除 `/`：`symbols = [s.replace('/', '').upper() for s in request.symbols]`
      - 設定 `max_symbols = len(symbols)`。
      - 呼叫 `monitor.start_all_symbols_1s(category, max_symbols=max_symbols, specific_symbols=symbols)`。
    - **若 `request.symbols` 為空**：
      - 呼叫原本現有的 `start_all_symbols_monitoring(category=...)`，走預設多檔監控邏輯。
    - 回傳目前實際監控中的 symbols（`monitor.get_monitoring_symbols()`）。
- `POST /api/monitor/stop`：停止所有監控。
- `GET /api/monitor/status`：查詢目前是否在監控，以及監控哪些 symbol。

> **[DESIGN NOTE]** 目前 Web 預期只傳「單一 symbol」，但後端仍保留多檔清單的彈性。若未來要支援 Web 同時監多檔，這裡可以直接利用既有邏輯。

#### Frontend：React + Hooks

- 檔案：`web_charting/frontend/src/hooks/useMonitoring.js`
  - `startMonitoring(symbol)`：

    ```js
    const response = await fetch('/api/monitor/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      // [DESIGN NOTE] Web 端目前以「當前頁面的 symbol」作為唯一 1 秒監控對象
      body: JSON.stringify({
        category: 'crypto',
        symbols: symbol ? [symbol] : undefined,
      }),
    })
    ```

  - `stopMonitoring()`：呼叫 `POST /api/monitor/stop`，前端自己把 `monitoring` 狀態設為 `false`，停止每秒輪詢。
  - `fetchMonitorStatus()`：呼叫 `GET /api/monitor/status`，更新 `monitoring` 與 `monitorSymbols`。

- 檔案：`web_charting/frontend/src/App.jsx`
  - 狀態：`symbol` 由 `Header` 控制（例如 BTCUSDT / ETHUSDT）。
  - `startMonitoring` 包裝函式：

    ```js
    const startMonitoring = async () => {
      // 啟動監控時，強制切到 1 秒 timeframe
      setInterval(1)
      // [DESIGN NOTE] 使用當前頁面的 symbol 啟動 /api/monitor/start
      await startMonitoringCore(symbol)
    }
    ```

  - `useEffect` 監聽 `monitoring` 為 `true` 時，每秒重載 K 線資料（呼叫 `loadCandles()`）。

> **重點：** Web 端「目前頁面的 symbol」決定 1 秒監控對象；GUI 那邊則是人工選擇多檔幣種。

---

## 3. 今天調整較多、設計上要小心的區塊

以下是已加上 `[DESIGN NOTE]` 的熱點（之後你改到這幾塊，我可以特別提醒設計風險）：

1. **SQLite 寫入重試機制**
   - 檔案：`modules/utils/database/data_manager.py`
   - 方法：`_insert_single_in_transaction`
   - 位置：`max_retries = 3` 那一段。
   - 用途：處理 `database is locked`，目前採用「最多 3 次、0.2 秒間隔」的重試策略。
   - 風險：交易量變大或換 DB 時，這裡可能要重新評估，避免變成隱藏的效能瓶頸。

2. **GUI 1 秒監控選幣與上限**
   - 檔案：`core/gui_monitoring.py`
   - 方法：`GUIMonitoring.start_ws`
   - 關鍵點：
     - `max_symbols = 5`（固定最多 5 檔）。
     - 候選來自 `TradingConfig.SUPPORTED_SYMBOLS[:20]`，需與模板 A 的 20 檔一致。
   - 風險：若改動模板 A 排版、幣種數、或想放寬監控上限，這三處（模板 A、TradingConfig、start_ws）要一起想。

3. **GUI/WEB 共用 MultiSymbolMonitor 的停止流程**
   - 檔案：`core/gui_monitoring.py`
   - 方法：`GUIMonitoring.stop_ws`
   - 關鍵點：
     - 呼叫 `stop_all_symbols_1s()` 後，一次負責：
       - 還原 GUI 按鈕狀態。
       - 還原 `monitor_symbol_limit_var` 顯示為 `"(待選)"`。
       - 呼叫 `on_monitor_stopped()` 做 summary log。
   - 風險：未來若 Web 端也要「精細控制」停止流程（例如只停某些 symbol），要確認不會跟 GUI 流程衝突。

4. **模板切換與 B/C 視圖快取**
   - 檔案：`core/gui_main.py`
   - 方法：`set_monitor_template`
   - 行為：
     - 套用靜態模板後，若切到 B/C，會呼叫 `_render_template_b_from_cache` / `_render_template_c_from_cache`，實作在 `TemplateBView` / `TemplateCView`。
   - 風險：改模板版面或快取格式時，要同步調整這三者，否則畫面會顯示錯位或殘值。

5. **1 秒監控 Summary Log 與 stats_collector 整合**
   - 檔案：`core/gui_main.py` + `core/gui/monitor_message_handler.py`
   - 關鍵方法：
     - `MainGUI.on_monitor_started` / `on_monitor_stopped` / `_log_monitor_summary`
     - `MonitorMessageHandler.increment_summary` / `_classify_monitor_msg`
     - `MainGUI._on_duplicate_skip` / `_handle_duplicate_skip` / `_update_symbol_duplicate_block`
   - 風險：
     - 這幾個函式共同決定了 summary log 與模板 A 上的統計數字。
     - 若改訊息格式、分類規則或 stats_collector 的呼叫頻率，需要一起檢查這些地方。

6. **GUI 固定 1 秒監控面板 `_update_monitor_panel`**
   - 檔案：`core/gui_main.py`
   - 功能：把 `[SYMBOL] 🟢 1s 寫入 ... data_source=... (總共N)` 這種原始 log，轉成另一個「固定排版」的面板（不走模板 A 的 dynamic 欄位）。
   - 風險：這是另一套畫面邏輯，已用 `[DESIGN NOTE]` 標示。若日後想統一畫面或換呈現方式，需要先梳理與模板 A 的關係。

7. **Web 端 1 秒監控的 symbol 控制**
   - Backend：`web_charting/backend/api/monitor.py` → `/api/monitor/start`
   - Frontend：
     - `web_charting/frontend/src/hooks/useMonitoring.js` → `startMonitoring(symbol)`
     - `web_charting/frontend/src/App.jsx` → `startMonitoring` 包裝函式。
   - 行為：
     - App 把當前 `symbol`（Header 選擇）傳給 `startMonitoringCore(symbol)`。
     - Hook 將 symbol 包成陣列傳給 backend，實際啟動 1 檔 1 秒監控。
   - 風險：
     - 若改成同時監多檔、或允許不同 category，需要一起調整 hook + backend + GUI 顯示邏輯。

---

## 4. 未來擴充建議（草案）

這裡先列幾個未來可能會做的改動方向，方便下次打開時快速進入狀況：

1. **Web 操作同步影響 GUI 顯示**
   - 目前：Web 只能控制 MultiSymbolMonitor 的啟停與 symbol，GUI 會被動顯示結果。
   - 可能想要：當 Web 啟動 1 秒監控時，GUI 也自動切到模板 A、甚至自動聚焦該 symbol。
   - 方向：
     - 可以考慮在 GUI 這邊加一個簡單的 IPC / HTTP 端點，讓 Web 在啟動監控時順便發一個「提示事件」給 GUI。

2. **支援 Web 多 symbol 監控**
   - 調整點：
     - Frontend：`useMonitoring.startMonitoring(symbols)` 接受陣列。
     - Backend：`MonitorStartRequest.symbols` 照舊支援 list，只是開始真正用到多檔。
     - GUI 顯示：模板 A / 固定面板是否需要標示「這些 symbol 是由 Web 啟動」等額外資訊。

3. **更彈性的 SQLite 重試策略**
   - 目前是「固定 3 次、0.2 秒」重試，寫死在 DataManager。
   - 未來可以：
     - 抽成設定（例如 config / env），方便在不同環境調整。
     - 或切到 WAL / 其他 DB 並簡化重試邏輯。

---

> 之後如果你改到有標 `// [DESIGN NOTE]` 或 `# [DESIGN NOTE]` 的區塊，只要貼那段程式碼給我，我就會用這份設計說明幫你一起檢查設計風險。 
