## 2025-11-14 Backfill & Logging Update

### Overview
- 調整 GUI 回補流程，確保 🚀 開始回補資料 會依序處理所有在 `TradingConfig.SUPPORTED_SYMBOLS` 中註冊的貨幣對（同時保留手動輸入的優先權）。
- 2025-11-14 (更新) 回補按鈕現已固定使用 `TradingConfig.SUPPORTED_SYMBOLS`，GUI 交易對欄位僅作顯示；快捷選單同樣取自此清單以維持一致。
- 重新設計回補日誌輸出與資料驗證邏輯，減少終端機噪音並防止未處理的例外導致 GUI 閃退。
- 在 `IMPORTANT_VALIDATION_MODULE.py` 中加入新的守門員：統一日誌聚合份量、監控按鈕綁定，以及對關鍵錯誤的即時阻斷。

### Implementation Highlights
1. **多貨幣對回補綁定**
   - `core/gui_backfill.py` 現在會串接 `TradingConfig.SUPPORTED_SYMBOLS`，並在回補開始時透過 `validate_symbol_binding()` 確認所有貨幣對都已綁定。
   - 以序列方式在同一個背景執行緒處理各個貨幣對，針對每個 symbol 更新狀態並記錄進度，若遇到 `BackfillInsertError` 會顯示錯誤並停止該輪回補，避免 GUI 閃退。

2. **一致的日誌聚合機制**
   - 新的 `ChunkedLogAggregator` 讓 `⏭️ 跳過` 與 `批次NN NNN/NNN (總計:XXXX)` 兩種訊息都以相同 chunk（目前 20 筆）輸出；`IMPORTANT_VALIDATION_MODULE.LOG_AGGREGATION_CHUNK` 提供單一真值來源並由 `LogAggregationValidator` 強制檢查。
   - `fetch_and_insert()` 會統計成功/跳過/處理筆數，在批次結束或回補完成時輸出摘要，進而解決只看到 999 筆的終端機假象。

3. **新的驗證與錯誤處理**
   - `IMPORTANT_VALIDATION_MODULE.py` 新增 `BackfillConfigurationError`、`validate_symbol_binding()`、`LogAggregationValidator()`，確保 UI 綁定及日誌策略皆符合規範。
   - `BackfillErrorMonitor` 維持即時監控；`GUIBackfill` 對 `BackfillInsertError` 進行專屬處理，避免例外冒泡造成整個 GUI 終止。

4. **狀態管理擴充**
   - `BackfillStateManager` 增加 `set_current_target()`，方便在多貨幣對模式下同步顯示目前處理對象。

### Next Steps / Notes
- 若要調整 chunk 大小，只需在 `IMPORTANT_VALIDATION_MODULE.LOG_AGGREGATION_CHUNK` 改值即可，同時確保 `docs/` 內部流程文件更新。
- 若未來要支援自訂貨幣對，可在 `TradingConfig.SUPPORTED_SYMBOLS` 或額外的設定檔擴充，`validate_symbol_binding()` 會自動套用。
- GUI 回補若再次出現閃退，可先檢查 `logs/streamlit_debug.log`、`data/temp/gui_session.log` 以及本次新增的錯誤彙整訊息。


