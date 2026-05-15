# Data Source 顯示優化修復報告

**修復日期**: 2025-11-13  
**修復範圍**: 6個主要問題  
**狀態**: ✅ 全部完成

---

## 📋 修復總覽

### 問題1: 1秒鐘級別監控缺少 data_source=real 顯示 ✅

**檔案**: `modules/utils/data/ws_aggregator.py`

**問題描述**:
- WebSocket 1秒監控在插入資料時沒有傳遞 `data_source='real'` 參數
- GUI 和終端機日誌中沒有顯示資料來源信息

**修復內容**:
```python
# 第115行：添加 data_source='real' 參數
insert_data(self.category, self.symbol, 1, kline, data_source='real')

# 第121行：在日誌中顯示 data_source
self._emit(f"🟢 1s 寫入 {self.symbol} t={datetime.fromtimestamp(s, tz=timezone.utc)} close={b['close']} data_source=real")
```

**驗證方式**:
啟動1秒監控後，GUI和終端機應顯示：
```
🟢 1s 寫入 BTCUSDT t=2025-11-13 08:30:45 close=91234.56 data_source=real
```

---

### 問題2: 批量抓取最新1分鐘資料缺少 data_source 顯示 ✅

**檔案**: `modules/monitors/multi_symbol_monitor.py`

**問題描述**:
- 批量抓取功能已經傳遞 `data_source="real"`，但日誌沒有明確顯示

**修復內容**:
```python
# 第200-201行：添加插入確認日誌
inserted = batch_insert_data(category, symbol, 60, db_klines, data_source="real")
logger.info(f"✅ {symbol} 插入 {inserted} 筆 data_source=real")
```

**驗證方式**:
點擊「批量抓取最新1分鐘資料」按鈕後，應顯示：
```
✅ BTCUSDT 插入 17 筆 data_source=real
✅ ETHUSDT 插入 15 筆 data_source=real
```

---

### 問題3: 回補資料缺少 data_source=real 和插入確認 ✅

**檔案**: `modules/utils/backfill/backfill_data.py`

**問題描述**:
- 回補功能沒有傳遞 `data_source='real'` 參數
- 日誌中沒有顯示資料來源和插入確認

**修復內容**:
```python
# 第90-95行：添加 data_source='real' 參數
insert_data(
    category, 
    symbol, 
    interval_seconds, 
    k, 
    data_source='real',
    original_interval=interval, 
    overwrite_callback=overwrite_callback
)

# 第100行：在日誌中顯示 data_source
msg = f"{interval} - 批次{batch_num} {idx}/{batch_count} (總計:{total_inserted + idx}) close={k['close']:.2f} data_source=real"
```

**驗證方式**:
執行回補後，應顯示：
```
1m - 批次1 1/999 (總計:1) close=91234.56 data_source=real
1m - 批次1 2/999 (總計:2) close=91235.78 data_source=real
```

---

### 問題4: 智能修補和聚合修補缺少 data_source 顯示 ✅

**檔案**:
- `modules/utils/backfill/auto_heal_core.py`
- `modules/utils/data/aggregation_utils.py`

**問題描述**:
- 內插資料沒有顯示 `data_source=interpolated`
- 即時收集沒有顯示 `data_source=real`
- 聚合資料沒有明確顯示 `data_source=Aggregation` 或 `inferior-Aggregation`

**修復內容**:

**auto_heal_core.py**:
```python
# 第123-125行：每100筆顯示內插確認
if idx % 100 == 0:
    emit(f"✅ 內插寫入 {idx}/{seconds} data_source=interpolated")

# 第144行：完成訊息顯示 data_source
msg = f"✅ 內插完成：區間 {seconds} 秒；新增 {added} 筆，區間內總筆數 {after_cnt} 筆 data_source=interpolated"

# 第234行和第298行：即時收集結束顯示 data_source
emit(f"✅ 真實 1 秒收集結束：新增 {max(0, after_cnt - before_cnt)} 筆，區間內總筆數 {after_cnt} 筆 data_source=real")
```

**aggregation_utils.py**:
```python
# 第186-188行：每10個bucket顯示 data_source
if idx % 10 == 0 or idx == total_buckets:
    emit(f"✅ 聚合寫入 {idx}/{total_buckets} data_source={agg['data_source']}")

# 第201行：完成訊息顯示類型
emit(f"✅ 聚合完成：{_interval_name(target_interval)} 級別；新增 {added} 筆 (Aggregation 或 inferior-Aggregation)")
```

**驗證方式**:
- 智能修補內插：`✅ 內插寫入 100/900 data_source=interpolated`
- 智能修補即時收集：`✅ 真實 1 秒收集結束：新增 120 筆 data_source=real`
- 聚合修補：`✅ 聚合寫入 10/50 data_source=Aggregation`

**停止按鈕狀態**: ✅ 已確認存在於 `core/panels/query_panel.py` 第185行

---

### 問題5: 1秒鐘級別資料插入資料庫驗證 ✅

**檔案**: `modules/utils/database/data_manager.py`

**檢查結果**:
- ✅ `insert_single_data` 方法正確接受 `data_source` 參數（第42行）
- ✅ 優先級系統正常運作（第100-106行）
- ✅ 資料來源正確記錄到資料庫（第117行）

**資料庫表結構確認**:
```sql
-- historical_data 表包含 data_source 欄位
data_source TEXT DEFAULT 'real'
```

**資料來源優先級**:
```python
priority_map = {
    'real': 1,           # 最高優先級
    'Aggregation': 2,
    'interpolated': 3,
    'inferior-Aggregation': 4,
    'test': 5            # 最低優先級
}
```

---

### 問題6: 日誌系統優化 ✅

**檔案**: `modules/utils/database/data_manager.py`

**優化內容**:
```python
# 第121-123行：智能日誌輸出
# 1秒級別：每筆都顯示（重要監控數據）
# 其他級別：每100筆顯示一次（避免日誌過載）
if self._stats['successful_insertions'] % 100 == 0 or interval == 1:
    logger.info(f"✅ 插入成功: {symbol}@{interval}s timestamp={timestamp} data_source={data_source}")
```

**日誌級別設置**:
- 預設級別：`INFO`（適合查看關鍵操作）
- 詳細除錯：`DEBUG`（可通過配置啟用）

---

## 🎯 驗證檢查清單

### 1秒監控驗證
- [ ] 啟動多貨幣對1秒監控
- [ ] GUI顯示：`🟢 1s 寫入 ... data_source=real`
- [ ] 資料庫查詢：`SELECT * FROM historical_data WHERE interval=1` 確認 `data_source='real'`

### 批量抓取驗證
- [ ] 點擊「批量抓取最新1分鐘資料」
- [ ] GUI顯示：`✅ BTCUSDT 插入 X 筆 data_source=real`
- [ ] 無錯誤訊息

### 回補驗證
- [ ] 執行回補資料功能
- [ ] 日誌顯示：`1m - 批次1 1/999 (總計:1) close=... data_source=real`
- [ ] 資料庫確認 data_source 正確

### 智能修補驗證
- [ ] 啟動智能修補
- [ ] 內插階段顯示：`data_source=interpolated`
- [ ] 即時收集顯示：`data_source=real`

### 聚合修補驗證
- [ ] 執行聚合檢查與修補
- [ ] 顯示：`data_source=Aggregation` 或 `inferior-Aggregation`
- [ ] 停止按鈕可用

---

## 📊 資料來源類型說明

| 類型 | 說明 | 優先級 | 產生方式 |
|------|------|--------|----------|
| `real` | 真實市場資料 | 1 (最高) | WebSocket、REST API、批量抓取 |
| `Aggregation` | 純真實資料聚合 | 2 | 從1秒real資料聚合 |
| `interpolated` | 線性內插資料 | 3 | 從1分鐘資料內插 |
| `inferior-Aggregation` | 混合來源聚合 | 4 | 從包含interpolated的資料聚合 |
| `test` | 測試資料 | 5 (最低) | 測試環境 |

---

## 🔧 後續建議

### 已實現功能
1. ✅ 所有插入操作都傳遞正確的 `data_source` 參數
2. ✅ GUI 和終端機日誌明確顯示資料來源
3. ✅ 聚合修補有停止按鈕
4. ✅ 日誌系統優化，避免過多輸出

### 可選增強
1. 在資料庫查詢面板顯示 data_source 統計
2. 創建資料來源可視化圖表
3. 添加資料來源過濾器

---

## 📝 測試建議

### 快速測試腳本
```python
# 測試1秒監控
啟動GUI → 點擊「啟動多貨幣對1秒監控」→ 觀察日誌顯示 data_source=real

# 測試批量抓取
啟動GUI → 點擊「批量抓取最新1分鐘資料」→ 確認顯示插入數量和 data_source=real

# 測試回補
啟動GUI → 選擇時間範圍 → 點擊「開始回補資料」→ 觀察進度日誌包含 data_source=real

# 驗證資料庫
import sqlite3
conn = sqlite3.connect('data/historical_data.db')
cur = conn.cursor()
cur.execute("SELECT data_source, COUNT(*) FROM historical_data GROUP BY data_source")
print(cur.fetchall())
# 預期輸出：[('real', 10000), ('interpolated', 5000), ('Aggregation', 2000), ...]
```

---

## ✅ 修復狀態總結

| 問題 | 狀態 | 修復檔案 |
|------|------|----------|
| 1秒監控 data_source | ✅ 完成 | ws_aggregator.py |
| 批量抓取顯示 | ✅ 完成 | multi_symbol_monitor.py |
| 回補 data_source | ✅ 完成 | backfill_data.py |
| 智能修補顯示 | ✅ 完成 | auto_heal_core.py |
| 聚合修補顯示 | ✅ 完成 | aggregation_utils.py |
| 停止按鈕 | ✅ 已存在 | query_panel.py |
| 資料庫插入 | ✅ 驗證通過 | data_manager.py |
| 日誌優化 | ✅ 完成 | data_manager.py |

**總計**: 8/8 項目完成 🎉

---

## 🎓 修復後預期行為

### GUI 顯示範例
```
🟢 1s 寫入 BTCUSDT t=2025-11-13 08:30:45 close=91234.56 data_source=real
✅ BTCUSDT 插入 17 筆 data_source=real
1m - 批次1 50/999 (總計:50) close=91234.56 data_source=real
✅ 內插寫入 100/900 data_source=interpolated
✅ 聚合寫入 10/50 data_source=Aggregation
✅ 真實 1 秒收集結束：新增 120 筆 data_source=real
```

### 終端機輸出範例
```
2025-11-13 16:30:00 | ws_1s | INFO | 🟢 1s 寫入 BTCUSDT data_source=real
2025-11-13 16:30:15 | multi_monitor | INFO | ✅ BTCUSDT 插入 17 筆 data_source=real
2025-11-13 16:30:30 | backfill | INFO | 1m - 批次1 1/999 data_source=real
2025-11-13 16:31:00 | data_manager | INFO | ✅ 插入成功: BTCUSDT@1s data_source=real
```

---

**修復完成日期**: 2025-11-13  
**修復工程師**: AI Assistant (Cascade)  
**審核狀態**: 待用戶測試驗證
