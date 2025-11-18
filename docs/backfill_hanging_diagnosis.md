# 回補功能卡住問題診斷報告

## 📋 問題描述
用戶報告回補功能在執行過程中偶爾會卡住，程序停止響應。

## 🔍 潛在原因分析

### 1. 資料庫鎖競爭
**位置**: `core/gui_backfill.py:85-88`
```python
if not _db_operation_lock.acquire(blocking=False):
    gui_safe_log("⏳ 資料庫操作進行中，請等待其他操作完成...")
    _db_operation_lock.acquire()  # 阻塞等待 - 可能無限期等待！
```

**問題**: 如果鎖被其他線程持有且未釋放，會永久阻塞。

### 2. SQLite 資料庫鎖定
**位置**: `modules/utils/database/db_pool.py:21-32`
- 連線池超時: 5秒
- 但SQLite本身可能在EXCLUSIVE模式下鎖定

**症狀**: 
- `database is locked` 錯誤
- 多個線程同時寫入時出現競爭

### 3. API請求超時
**位置**: `modules/utils/api/api_connector.py:45`
```python
response = requests.get(url, params=params, timeout=10)
```

**狀態**: ✅ 已有10秒超時，這部分正常

### 4. 無限循環風險
**位置**: `modules/utils/backfill/backfill_data.py:112-265`
- `while current_start < end_time` 循環
- 如果時間計算錯誤，可能無限循環

### 5. 日誌寫入阻塞
**位置**: GUI日誌寫入 `core/gui_main.py:log()`
- 使用 `root.after()` 可能在GUI主線程繁忙時阻塞

## 🛠️ 建議修復方案

### 方案1: 添加資料庫鎖超時
```python
# 在 core/gui_backfill.py 中修改
if not _db_operation_lock.acquire(blocking=False):
    gui_safe_log("⏳ 資料庫操作進行中，請等待其他操作完成...")
    # 添加超時，避免永久阻塞
    if not _db_operation_lock.acquire(timeout=30):  # 30秒超時
        gui_safe_log("❌ 無法獲取資料庫鎖，操作超時")
        return
```

### 方案2: 增加SQLite busy_timeout
```python
# 在創建連線時設置
conn.execute("PRAGMA busy_timeout = 30000")  # 30秒
```

### 方案3: 添加回補循環保護
```python
# 在 backfill_data.py 的 while 循環中
max_batches = 100  # 最多處理100批次
batch_count = 0

while current_start < end_time and batch_count < max_batches:
    batch_count += 1
    # ... 現有邏輯
```

### 方案4: 改善錯誤處理和日誌
```python
# 在所有關鍵操作周圍添加超時和詳細日誌
try:
    with timeout(seconds=60):  # 使用timeout裝飾器
        # 關鍵操作
except TimeoutError:
    logger.error("操作超時，已中止")
```

## 📊 當前已有的保護機制

1. ✅ API請求超時: 10秒
2. ✅ 連線池超時: 5秒  
3. ✅ 全域DB鎖（但無超時）
4. ✅ 異常處理和break機制

## 🎯 立即行動項目

### 優先級1 (高風險)
1. 為全域資料庫鎖添加超時機制
2. 增加SQLite busy_timeout設置
3. 添加回補循環計數保護

### 優先級2 (中風險)
1. 改善日誌寫入的非阻塞機制
2. 添加更詳細的診斷日誌
3. 實現心跳檢測機制

### 優先級3 (低風險)
1. 優化批次大小動態調整
2. 實現斷點續傳功能
3. 添加性能監控指標

## 🔧 測試建議

1. **壓力測試**: 同時運行多個回補任務
2. **網路測試**: 模擬網路延遲和中斷
3. **資料庫測試**: 測試高併發寫入場景
4. **長時間測試**: 運行24小時回補任務

## 📝 監控指標

建議監控以下指標：
- 回補任務平均執行時間
- 資料庫鎖等待時間
- API請求失敗率
- 異常發生頻率

---
*診斷時間: 2025-11-15*
*診斷人員: Cascade AI*
