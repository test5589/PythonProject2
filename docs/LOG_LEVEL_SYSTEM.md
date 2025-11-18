# 分級日誌系統設計文檔

**創建日期**: 2025-11-16  
**狀態**: ✅ **已實現**  
**目的**: 讓精簡日誌選項真正有意義且易於維護

---

## 🎯 問題背景

### 用戶反饋
> "現在精簡日誌選用跟沒有選用的時候，幾乎內容都一樣，你有任何優化方案可以讓這個選項發揮它真正用途嗎？並且在日後更好維護。"

### 原因分析

為了優化GUI性能，我們移除了大量詳細日誌：
- 從999條減少到1條/批次
- 不管是否打勾，輸出都一樣
- **精簡日誌選項失去意義**

---

## 💡 解決方案：分級日誌系統

### 設計原則

**不打勾（詳細模式）**：
- 顯示每個批次的詳細過程
- API調用細節
- 進度更新訊息
- 資料驗證訊息

**打勾（精簡模式）**：
- 只顯示關鍵摘要
- 開始/結束訊息
- 錯誤和警告
- 最終統計

### 日誌級別定義

```python
class LogLevel(IntEnum):
    CRITICAL = 0   # 關鍵訊息（錯誤、完成）- 始終顯示
    SUMMARY = 1    # 摘要訊息（批次開始/結束）- 精簡模式顯示
    NORMAL = 2     # 普通訊息（一般操作）- 精簡模式過濾
    VERBOSE = 3    # 詳細訊息（每50筆進度）- 精簡模式過濾
    DEBUG = 4      # 調試訊息 - 精簡模式過濾
```

### 過濾邏輯

```python
if is_compact:
    # 精簡模式：只顯示 CRITICAL 和 SUMMARY
    if level > LogLevel.SUMMARY:
        return  # 過濾 NORMAL, VERBOSE, DEBUG
else:
    # 詳細模式：顯示所有級別
    pass  # 不過濾
```

---

## 🏗️ 系統架構

### 核心組件

```
core/gui_logger.py
├── LogLevel (Enum)              # 日誌級別定義
├── GUILogger                    # 基礎GUI日誌記錄器
│   ├── log(message, level)      # 根據級別過濾
│   ├── critical(message)        # CRITICAL級別
│   ├── summary(message)         # SUMMARY級別
│   ├── normal(message)          # NORMAL級別
│   ├── verbose(message)         # VERBOSE級別
│   └── debug(message)           # DEBUG級別
│
└── BackfillLogger               # 回補專用記錄器
    ├── start()                  # 回補開始 (SUMMARY)
    ├── batch_start()            # 批次開始 (NORMAL)
    ├── batch_fetched()          # 批次抓取 (VERBOSE)
    ├── batch_inserting()        # 批次插入 (VERBOSE)
    ├── batch_complete()         # 批次完成 (SUMMARY)
    ├── progress()               # 進度更新 (VERBOSE)
    ├── complete()               # 回補完成 (CRITICAL)
    ├── error()                  # 錯誤訊息 (CRITICAL)
    ├── warning()                # 警告訊息 (SUMMARY)
    ├── info()                   # 普通訊息 (NORMAL)
    └── skip_all()               # 全部跳過 (SUMMARY)
```

### 數據流

```
用戶操作
    ↓
gui.compact_var.get()  # 獲取精簡模式狀態
    ↓
create_gui_logger(gui)
    ↓
GUILogger
    ↓
BackfillLogger
    ↓
blog.batch_start()  # NORMAL級別
    ↓
GUILogger.log(message, LogLevel.NORMAL)
    ↓
if is_compact and level > SUMMARY:
    return  # 過濾！
    ↓
gui.log(message)  # 輸出到GUI
```

---

## 📝 使用方法

### 1. 創建日誌記錄器

```python
from core.gui_logger import create_gui_logger, BackfillLogger

# 在 gui_backfill.py 中
gui_logger = create_gui_logger(gui)

# 在 backfill_data.py 中
blog = BackfillLogger(gui_logger, symbol)
```

### 2. 記錄不同級別的日誌

```python
# 回補開始 (SUMMARY - 精簡模式顯示)
blog.start(interval, start_time, end_time)

# 批次開始 (NORMAL - 精簡模式過濾)
blog.batch_start(batch_num, 999)

# 批次抓取完成 (VERBOSE - 精簡模式過濾)
blog.batch_fetched(batch_num, len(klines))

# 批次插入中 (VERBOSE - 精簡模式過濾)
blog.batch_inserting(batch_num, batch_count)

# 批次完成 (SUMMARY - 精簡模式顯示)
blog.batch_complete(batch_num, inserted, skipped, total)

# 進度更新 (VERBOSE - 精簡模式過濾)
blog.progress(current, total, "detail")

# 回補完成 (CRITICAL - 始終顯示)
blog.complete(total_inserted, total_skipped)

# 錯誤訊息 (CRITICAL - 始終顯示)
blog.error("錯誤訊息")

# 警告訊息 (SUMMARY - 精簡模式顯示)
blog.warning("警告訊息")
```

---

## 📊 日誌輸出對比

### 詳細模式（不打勾）

```
🚀 BTC | 開始回補 1m (2024-12-14 00:00 → 2024-12-15 00:00)

📦 BTC | 批次 1: 正在抓取 999 筆...
✅ BTC | 批次 1: 已抓取 999 筆
💾 BTC | 批次 1: 準備插入 999 筆
🎯 BTC | 批次 1: 成功插入 999/999 筆
📊 BTC | 進度: 999/50000 (2.0%) - 批次1完成

📦 BTC | 批次 2: 正在抓取 999 筆...
✅ BTC | 批次 2: 已抓取 999 筆
💾 BTC | 批次 2: 準備插入 999 筆
🎯 BTC | 批次 2: 插入 500/999 筆，跳過 499 筆
📊 BTC | 進度: 1499/50000 (3.0%) - 批次2完成

...

✅ BTC | 回補完成！總計插入 45,000 筆，跳過 5,000 筆
```

**特點**：
- ✅ 顯示每個批次的詳細過程
- ✅ 顯示抓取、插入細節
- ✅ 顯示進度更新
- ✅ 信息豐富，適合開發和調試

### 精簡模式（打勾）

```
🚀 BTC | 開始回補 1m (2024-12-14 00:00 → 2024-12-15 00:00)

🎯 BTC | 批次 1: 成功插入 999/999 筆
🎯 BTC | 批次 2: 插入 500/999 筆，跳過 499 筆
⏭️ BTC | 批次 3: 999 筆資料已存在，全部跳過
🎯 BTC | 批次 4: 成功插入 999/999 筆

...

✅ BTC | 回補完成！總計插入 45,000 筆，跳過 5,000 筆
```

**特點**：
- ✅ 只顯示關鍵摘要
- ✅ 不顯示抓取、插入細節
- ✅ 不顯示進度更新
- ✅ 簡潔清晰，適合日常使用

---

## 🎨 維護性設計

### 1. 集中管理

所有日誌級別定義在 `core/gui_logger.py`：
- 統一的級別定義
- 統一的過濾邏輯
- 易於修改和擴展

### 2. 語義化方法

```python
# 不好：需要記住級別
logger.log("批次開始", LogLevel.NORMAL)

# 好：語義清晰
blog.batch_start(batch_num, 999)
```

### 3. 自動前綴

```python
# 不需要手動添加前綴
blog.error("錯誤")  # 自動輸出：❌ BTC | 錯誤: 錯誤
```

### 4. 向後兼容

保留舊的 `progress_cb` 方式：
```python
if gui_logger:
    blog.batch_start(...)  # 新方式
else:
    report(f"批次開始...")  # 舊方式
```

---

## 🔧 添加新日誌的步驟

### 步驟1: 確定日誌級別

```
是否總是需要顯示？
    ↓ 是
CRITICAL (錯誤、完成)

    ↓ 否
是否精簡模式需要？
    ↓ 是
SUMMARY (批次摘要、警告)

    ↓ 否
是否一般操作？
    ↓ 是
NORMAL (批次開始、一般訊息)

    ↓ 否
是否詳細進度？
    ↓ 是
VERBOSE (進度更新、詳細訊息)

    ↓ 否
DEBUG (調試訊息)
```

### 步驟2: 在 BackfillLogger 添加方法（如需要）

```python
class BackfillLogger:
    def new_operation(self, param1, param2):
        """新操作（普通級別）"""
        self.logger.normal(
            f"🆕 {self.symbol_short} | 新操作: {param1} → {param2}"
        )
```

### 步驟3: 在業務代碼中調用

```python
if gui_logger:
    blog.new_operation(param1, param2)
```

---

## ✅ 優勢

### 1. 真正的精簡模式

- ✅ 詳細模式：信息豐富
- ✅ 精簡模式：清晰簡潔
- ✅ 選項真正有意義

### 2. 易於維護

- ✅ 集中管理日誌級別
- ✅ 語義化方法名稱
- ✅ 統一的過濾邏輯

### 3. 性能優化

- ✅ 精簡模式減少GUI負載
- ✅ 過濾發生在記錄前
- ✅ 不會產生無用日誌

### 4. 向後兼容

- ✅ 保留舊的 `report()` 方式
- ✅ 漸進式遷移
- ✅ 不破壞現有功能

### 5. 可擴展性

- ✅ 易於添加新日誌級別
- ✅ 易於添加新日誌方法
- ✅ 支持多種日誌輸出目標

---

## 🧪 測試建議

### 測試1: 詳細模式

```
1. 不打勾「精簡日誌」
2. 開始回補
3. 觀察日誌輸出
期待：
- 顯示批次開始、抓取、插入訊息
- 顯示進度更新
- 信息豐富
```

### 測試2: 精簡模式

```
1. 打勾「精簡日誌」
2. 開始回補
3. 觀察日誌輸出
期待：
- 只顯示批次完成摘要
- 不顯示抓取、插入細節
- 不顯示進度更新
- 簡潔清晰
```

### 測試3: 動態切換

```
1. 回補過程中切換精簡模式
2. 觀察日誌是否立即改變
期待：
- 打勾後立即過濾詳細訊息
- 取消打勾後立即顯示詳細訊息
```

---

## 🎉 總結

### 解決的問題

1. ✅ 精簡日誌選項真正有意義
2. ✅ 易於維護和擴展
3. ✅ 性能優化（減少無用日誌）
4. ✅ 向後兼容

### 關鍵特性

1. **分級日誌** - 5個清晰的日誌級別
2. **智能過濾** - 根據精簡模式自動過濾
3. **語義化API** - 方法名稱清晰易懂
4. **集中管理** - 統一的日誌系統

### 未來擴展

可以輕鬆添加：
- 更多日誌級別
- 多種輸出目標（文件、網絡）
- 日誌格式化選項
- 日誌搜索和過濾

---

*文檔創建日期: 2025-11-16*  
*狀態: ✅ 已實現並可用*  
*維護性: ⭐⭐⭐⭐⭐ 優秀*
