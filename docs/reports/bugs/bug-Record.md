# Bug 記錄 - GUI 當機問題

## 🐛 錯誤描述

### 第一次錯誤 (2025-11-12)
**錯誤類型**: UnicodeEncodeError

**錯誤訊息**:
```
🧪 === 執行 GUI 測試 ===
🚀 GUI 已啟動，等待 5 秒...
❌ GUI 已退出
📥 錯誤: Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "C:\Users\hands\PycharmProjects\PythonProject2\core\gui_main.py", line 14, in <module>
    from core.feature_panel import FeaturePanel
  File "C:\Users\hands\PycharmProjects\PythonProject2\core\feature_panel.py", line 10, in <module>
    from modules.utils.auto_heal_backfill import (
    ...<2 lines>...
    )
  File "C:\Users\hands\PycharmProjects\PythonProject2\modules\utils\auto_heal_backfill.py", line 15, in <module>   
    from modules.utils.data_fetcher import fetch_klines
  File "C:\Users\hands\PycharmProjects\PythonProject2\modules\utils\data_fetcher.py", line 4, in <module>
    print("\U0001f7e2 GUI: 即將呼叫 schedule_fetches()")
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'cp950' codec can't encode character '\U0001f7e2' in position 0: illegal multibyte sequence 
```

**問題原因**: Windows CP950 編碼無法處理 Unicode emoji 字元 `\U0001f7e2` (🟢)

**影響範圍**: GUI 程式無法啟動

---

## 🔧 第一次解決方法

### 解決方案 1: 修復 Unicode 編碼問題
```python
# 在 data_fetcher.py 第 4 行
# 原來: print("\U0001f7e2 GUI: 即將呼叫 schedule_fetches()")
# 修改為: print("🟢 GUI: 即將呼叫 schedule_fetches()")
# 或者使用 ASCII 安全版本: print("[GUI] 即將呼叫 schedule_fetches()")
```

### 解決方案 2: 設定環境變數
```powershell
# 在執行前設定 UTF-8 編碼
$env:PYTHONIOENCODING="utf-8"
python -m core.gui_main
```

### 解決方案 3: 修改 Python 腳本編碼宣告
```python
# 在所有 .py 檔案開頭加入
# -*- coding: utf-8 -*-
```

---

## 🐛 第二次錯誤 (持續當機)

**錯誤類型**: GUI 當機但無終端機錯誤訊息

**問題描述**: 
- GUI 可以啟動
- 點擊權重測試按鈕後當機
- 終端機沒有顯示任何錯誤訊息
- 推測是執行緒或 GUI 阻塞問題

**可能原因**:
1. 執行緒死鎖
2. GUI 更新衝突
3. 記憶體洩漏
4. 模組循環匯入

---

## 🔧 第二次解決方法 (進行中)

### 解決方案 1: 強化錯誤捕獲
```python
# 在所有關鍵位置加入 try-catch
import traceback
import logging

def safe_execute(func, *args, **kwargs):
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logging.error(f"執行失敗: {e}")
        logging.error(f"詳細錯誤: {traceback.format_exc()}")
        return None
```

### 解決方案 2: 簡化權重測試邏輯
- 移除複雜的執行緒操作
- 改用同步執行 + 進度條
- 避免長時間阻塞

### 解決方案 3: 加入日誌監控
- 寫入檔案日誌
- 實時監控程序狀態
- 自動產生崩潰報告

---

## 📊 問題統計

| 錯誤次數 | 日期 | 錯誤類型 | 狀態 | 解決方案 |
|---------|------|----------|------|----------|
| 1 | 2025-11-12 | UnicodeEncodeError | ✅ 已解決 | 修改 emoji 字元 |
| 2 | 2025-11-12 | GUI 當機 | ✅ 已解決 | 執行緒優化 + 極簡化測試 |
| 3 | 2025-11-12 | FeaturePanel 初始化錯誤 | ✅ 已解決 | 修正測試腳本參數傳遞 |

---

## 🎯 預防措施

1. **編碼標準化**: 所有 print 陳述使用 ASCII 安全字元
2. **錯誤處理**: 所有可能失敗的操作加入 try-catch
3. **日誌系統**: 建立完整的錯誤追蹤機制
4. **測試覆蓋**: GUI 功能單元測試
5. **記憶體監控**: 加入記憶體使用監控

---

---

## 🐛 問題 #3: FeaturePanel 初始化錯誤

### 📅 發生時間
2025-11-12 15:30:00

### 📋 錯誤描述
測試腳本 `test_fixes.py` 在測試貨幣對選擇功能時失敗，錯誤訊息：
```
❌ 貨幣對選擇測試失敗: FeaturePanel.__init__() missing 1 required positional argument: 'main_gui'
```

### 🔍 問題分析
1. **測試腳本問題**: `FeaturePanel` 類別初始化需要正確的參數
2. **參數不匹配**: 測試腳本傳入的參數與實際建構函式不符
3. **模擬對象不完整**: `MockMainGUI` 可能缺少必要的屬性

### 🛠️ 處理過程
1. 檢查 `FeaturePanel` 的建構函式簽名
2. 分析測試腳本的模擬對象設計
3. 修正參數傳遞和模擬對象結構

### ✅ 處理結果
- [x] 修正 `FeaturePanel` 初始化參數
- [x] 完善測試腳本的模擬對象
- [x] 驗證貨幣對選擇功能正常運作

**修復詳情**:
1. 發現 `FeaturePanel.__init__(self, root, main_gui)` 需要兩個參數
2. 測試腳本原本只傳入 `main_gui`，缺少 `root` 參數
3. 修正為 `FeaturePanel(root, mock_gui)` 後測試通過
4. Debug 訊息顯示貨幣對選擇功能正常運作

**測試結果**:
```
[DEBUG] 選擇貨幣對: BTCUSDT
[DEBUG] 成功更新 symbol_entry 為: BTCUSDT
✅ 貨幣對選擇功能正常
```

---

## 📝 備註

- Windows 環境下的 Unicode 處理需要特別注意
- GUI 執行緒問題需要仔細設計
- 建議使用專門的日誌系統取代 print
- 測試腳本需要準確模擬 GUI 組件的依賴關係
