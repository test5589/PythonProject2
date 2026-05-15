# 多貨幣對監控與批量抓取功能指南

## 📋 功能概述

本文檔說明新增的多貨幣對監控與批量抓取功能，包括：
- 自動綁定所有 crypto 貨幣對進行 1 秒監控
- 批量抓取所有貨幣對最新 1 分鐘資料（台灣時間錨定）
- API 權重評估系統
- 資料缺失問題分析

---

## 🚀 新增功能

### 1️⃣ 多貨幣對 1 秒監控

**功能位置**：GUI 主視窗 → 「🟢 啟動多貨幣對 1秒監控」按鈕

**運作方式**：
- 自動讀取 `TradingConfig.SUPPORTED_SYMBOLS` 中的所有貨幣對
- 為每個貨幣對建立獨立的 WebSocket 連線
- 並行處理多個貨幣對的即時資料
- 統一日誌輸出，標明每個貨幣對的狀態

**使用步驟**：
1. 確認「資產分類」欄位填寫正確（預設：crypto）
2. 點擊「🟢 啟動多貨幣對 1秒監控」
3. 系統自動啟動所有配置的貨幣對監控
4. 日誌顯示各貨幣對的連線狀態與資料寫入情況

**停止方式**：點擊「⛔ 停止多貨幣對 1秒監控」

---

### 2️⃣ 批量抓取最新 1 分鐘資料

**功能位置**：GUI 主視窗 → 「📥 批量抓取最新 1分鐘資料」按鈕

**運作方式**：
- 自動抓取所有配置貨幣對的歷史資料
- 時間範圍：台灣時間當天 00:00:00 到現在
- 使用線程池並行抓取，提升效率
- 自動批次插入資料庫，優化效能

**使用步驟**：
1. 確認「資產分類」欄位填寫正確
2. 點擊「📥 批量抓取最新 1分鐘資料」
3. 系統並行抓取所有貨幣對資料
4. 完成後顯示成功統計與插入筆數

---

## 🧠 API 權重評估系統

### 系統目的
防止因 API 請求過頻繁導致 IP 被鎖定，動態調整請求筆數。

### 核心邏輯

#### 第一循環（被鎖處理）
1. **偵測被鎖**：當 API 返回 429 或 rate limit 錯誤
2. **扣除比例**：依次為 20% → 15% → 10% → 20%（循環）
3. **權重調整**：被鎖時扣除對應比例，解鎖時加回（比例-1%）
4. **連續判定**：連續 5 次被鎖觸發第二循環

#### 第二循環（平均補償）
1. **計算平均扣除**：最近 5 次的平均扣除比例
2. **補償公式**：
   - X = 平均扣除 × 0.312
   - Y = (平均扣除筆數) × X
3. **權重恢復**：當前權重 + X，筆數 + Y
4. **終止條件**：權重 > 1 恢復正常；權重 < 0.81 中止操作

### 使用方式

```python
from modules.api_weight_evaluator import get_api_weight_evaluator

# 取得評估器
evaluator = get_api_weight_evaluator()

# 取得建議請求筆數
count = evaluator.get_optimal_count("1m")

# 標記被鎖（系統自動處理）
evaluator.mark_lock("1m", detected_count=7584)

# 標記解鎖（系統自動處理）
evaluator.mark_unlock("1m")
```

---

## 📊 資料缺失問題分析

### 問題描述
在一秒監控日誌中，時間戳可能從 0 秒跳到 4 秒，看起像是資料缺失。

### 原因分析
1. **WebSocket 只在有交易時推送**：Binance WebSocket 只在實際發生交易時才推送資料
2. **秒桶聚合機制**：系統每 0.2 秒檢查，只寫入「已完成」的秒桶（前一秒）
3. **無交易 = 無資料**：如果某秒沒有交易，就不會有資料被寫入

### 這是正常行為
- **不是系統錯誤**：這是 WebSocket 的正常運作方式
- **不影響資料完整性**：查詢時會動態補齊時間段
- **節省儲存空間**：避免插入大量空資料

### 解決方案選項

#### 選項 A：插入空桶（不推薦）
```python
# 會產生大量無用資料，浪費空間
```

#### 選項 B：查詢時動態補齊（現行做法）
```python
# 在分析時自動生成完整時間序列
```

#### 選項 C：記錄缺失日誌（推薦）
```python
# 記錄但不插入，保持資料庫乾淨
```

---

## 🛠️ 技術實作細節

### 多貨幣對監控架構

```
MultiSymbolMonitor
├── 管理多個 _WS1sAggregator 實例
├── 統一進度回呼與日誌
├── 線程安全的狀態管理
└── 批量抓取功能（ThreadPoolExecutor）
```

### 批次插入優化

```python
# 使用 batch_insert_data 取代逐筆插入
inserted = batch_insert_data(category, symbol, 60, db_klines, data_source="real")
```

### 權重評估資料結構

```python
@dataclass
class TimeframeState:
    weight: float = 1.0
    base_count: int = 2000
    lock_records: List[LockRecord] = None
    status: str = "normal"
```

---

## 📁 相關檔案

| 檔案 | 用途 |
|------|------|
| `modules/utils/multi_symbol_monitor.py` | 多貨幣對監控管理器 |
| `modules/api_weight_evaluator.py` | API 權重評估系統 |
| `core/gui_monitoring.py` | GUI 監控功能（已更新） |
| `core/gui_backfill.py` | GUI 回補功能（已更新） |
| `core/gui_controls.py` | GUI 控制按鈕（已更新） |
| `data/api_weight_records.json` | 權重紀錄檔案 |
| `data/api_weight_log.txt` | 權重日誌檔案 |

---

## 🔧 設定與自訂

### 貨幣對配置
在 `config/trading_config.py` 中修改：
```python
SUPPORTED_SYMBOLS = ["BTCUSDT", "ETHUSDT", "BNBUSDT", ...]
```

### 權重評估參數
在 `modules/api_weight_evaluator.py` 中調整：
```python
TIMEFRAMES = ["1m", "3m", "5m", "10m", "30m", "1h"]
loss_table = [0.2, 0.15, 0.10]  # 扣除比例
```

---

## 📈 效能優化

### 並行處理
- **監控**：每個貨幣對獨立 WebSocket 連線
- **抓取**：使用 ThreadPoolExecutor，最多 5 個並行

### 資料庫優化
- **批次插入**：大幅提升寫入效能
- **連線池**：避免頻繁建立連線

### 記憶體管理
- **單例模式**：避免重複初始化
- **線程安全**：使用鎖保護共享資源

---

## ⚠️ 注意事項

1. **API 限制**：請確保遵守 Binance API 限制
2. **網路穩定性**：WebSocket 可能斷線，系統會自動重連
3. **資料量**：多貨幣對監控會產生大量資料，注意磁碟空間
4. **權重管理**：系統會自動調整，但建議監控權重狀態

---

## 🎯 未來改進方向

1. **GUI 監控面板**：即時顯示各貨幣對狀態
2. **權重視覺化**：圖表展示權重變化趨勢
3. **智能調度**：根據交易量動態調整監控頻率
4. **異常檢測**：自動偵測資料異常並警報

---

## 📞 技術支援

如遇到問題，請檢查：
1. 日誌檔案：`data/api_weight_log.txt`
2. 權重紀錄：`data/api_weight_records.json`
3. 系統日誌：查看 GUI 輸出與終端訊息

如有需要，可重置權重系統：
```python
from modules.api_weight_evaluator import get_api_weight_evaluator
evaluator = get_api_weight_evaluator()
evaluator.reset_all()
```
