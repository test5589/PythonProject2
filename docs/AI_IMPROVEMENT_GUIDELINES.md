# 🤖 AI助手改善指南與核心規則

**創建日期**: 2025-11-13  
**版本**: 2.0  
**狀態**: 🔴 **必讀 - 最高優先級**

---

## 📊 問題統計分析

### 用戶最常遇到的困難（按頻率排序）

| 排名 | 問題類型 | 發生次數 | 處理時間 | 嚴重程度 |
|------|----------|----------|----------|----------|
| 1 | **AI違背用戶指令** | 3次 | 平均2-3小時 | 🔴 嚴重 |
| 2 | **GUI功能異常** | 8次 | 平均30-60分鐘 | 🟡 中等 |
| 3 | **資料顯示/驗證問題** | 6次 | 平均20-40分鐘 | 🟡 中等 |
| 4 | **編碼/Unicode問題** | 3次 | 平均10-20分鐘 | 🟢 輕微 |
| 5 | **導入路徑錯誤** | 2次 | 平均15-30分鐘 | 🟡 中等 |

### AI最常遇到的困難（按處理效率排序）

| 排名 | 困難類型 | 發生次數 | 平均解決時間 | 效率評級 |
|------|----------|----------|--------------|----------|
| 1 | **理解用戶真實意圖** | 5次 | 2-4小時 | ⭐ 極差 |
| 2 | **複雜需求拆分整合** | 3次 | 1-3小時 | ⭐⭐ 差 |
| 3 | **GUI事件綁定邏輯** | 4次 | 30-90分鐘 | ⭐⭐⭐ 中等 |
| 4 | **資料庫優先級邏輯** | 2次 | 20-40分鐘 | ⭐⭐⭐⭐ 良好 |
| 5 | **日誌系統優化** | 2次 | 15-30分鐘 | ⭐⭐⭐⭐ 良好 |

---

## 🔴 最高優先級規則（絕對不可違背）

### 規則1: 資料優先級系統 - 神聖不可侵犯

```python
# 資料優先級定義（數字越小優先級越高）
PRIORITY_MAP = {
    'real': 1,                    # 最高優先級 - 真實市場資料
    'Aggregation': 2,             # 純真實資料聚合
    'interpolated': 3,            # 線性內插資料
    'inferior-Aggregation': 4,    # 混合來源聚合
    'test': 5                     # 最低優先級 - 測試資料
}
```

**絕對規則**:
1. ✅ **real資料可以覆蓋所有其他類型**
2. ❌ **interpolated永遠不可覆蓋real資料**
3. ✅ **只有更高優先級的資料可以覆蓋低優先級資料**
4. ⚠️ **相同優先級的資料不可互相覆蓋**

**驗證邏輯**:
```python
if new_priority >= existing_priority:
    # 跳過插入，保護現有資料
    logger.debug(f"跳過插入 - 優先級不足: {data_source} >= {existing_data_source}")
    return False
```

### 規則2: 資料唯一性識別 - 多維度考量

**資料唯一性由以下5個維度決定**:
1. `timestamp` - 時間戳（主要標識）
2. `api` - API來源URL
3. `category` - 資料分類（crypto/stock/forex）
4. `symbol` - 交易對符號
5. `interval` - 時間間隔（秒）

**禁止行為**:
- ❌ 不同API來源的資料不可互相覆蓋
- ❌ 不同category的資料不可混淆
- ❌ 不同symbol的資料不可替換
- ❌ 僅以timestamp作為唯一判斷標準

**正確實現**:
```python
def _check_existing_data(self, category, symbol, interval, timestamp, api):
    """檢查資料是否存在 - 必須匹配所有5個維度"""
    query = """
        SELECT * FROM historical_data 
        WHERE category=? AND symbol=? AND interval=? 
        AND timestamp=? AND api=?
    """
    return self.cursor.execute(query, (category, symbol, interval, timestamp, api)).fetchone()
```

### 規則3: 用戶指令理解 - 三次確認原則

**問題根源**: AI最嚴重的問題是「理解偏差」和「擅自決定」

**強制流程**:
1. **第一次理解**: 讀取用戶原始需求
2. **第二次確認**: 用自己的話複述需求，列出具體實施步驟
3. **第三次驗證**: 詢問用戶是否理解正確，等待確認後才執行

**禁止行為**:
- ❌ 擅自整合或拆分功能
- ❌ 自作主張添加"優化"
- ❌ 在未確認前創建新文件
- ❌ 刪除或修改用戶未要求變更的代碼

**正確範例**:
```markdown
用戶需求理解確認：
1. 您要求修改X功能，添加Y參數
2. 具體步驟：
   - 修改文件A的函數B
   - 添加參數Y，默認值為Z
   - 保持其他功能不變
3. 我的理解是否正確？請確認後我開始執行。
```

### 規則4: 時間顯示標準 - 台灣時間UTC+8

**強制要求**:
- ✅ 所有GUI顯示必須使用台灣時間（UTC+8）
- ✅ 所有終端機日誌必須顯示台灣時間
- ✅ 資料庫存儲使用UTC時間戳
- ✅ 顯示格式：`2025-11-13 16:30:45 (UTC+8)`

**實現標準**:
```python
from datetime import timezone, timedelta

# 台灣時區
TW_TZ = timezone(timedelta(hours=8))

# 顯示格式
timestamp_display = datetime.fromtimestamp(ts, tz=TW_TZ).strftime('%Y-%m-%d %H:%M:%S')
logger.info(f"資料時間: {timestamp_display} (UTC+8)")
```

### 規則5: GUI與終端機同步 - 雙重顯示原則

**強制要求**:
- ✅ 每個按鈕操作必須在GUI顯示提示
- ✅ 每個按鈕操作必須在終端機輸出日誌
- ✅ 成功/失敗狀態必須雙重確認
- ✅ 插入資料必須顯示確認訊息

**實現模板**:
```python
def button_action(self):
    try:
        # GUI顯示
        self.gui.log("🔄 開始執行XX操作...")
        
        # 終端機日誌
        logger.info(f"開始執行XX操作")
        
        # 執行操作
        result = perform_action()
        
        # 雙重成功確認
        self.gui.log(f"✅ XX操作完成，插入 {result} 筆資料 data_source={source}")
        logger.info(f"✅ XX操作完成，插入 {result} 筆資料 data_source={source}")
        
    except Exception as e:
        # 雙重錯誤顯示
        self.gui.log(f"❌ XX操作失敗: {e}")
        logger.error(f"❌ XX操作失敗: {e}")
        traceback.print_exc()
```

---

## 🟡 重要規則（高優先級）

### 規則6: GUI按鈕狀態管理

**問題**: 按鈕在操作時消失，導致無法停止

**正確實現**:
```python
def start_operation(self):
    # ✅ 禁用開始按鈕，但不隱藏
    self.start_btn.config(state='disabled')
    
    # ✅ 啟用停止按鈕，保持可見
    self.stop_btn.config(state='normal')
    
    # ❌ 錯誤：不要使用 pack_forget() 或 grid_forget()
    # self.start_btn.pack_forget()  # 這會讓按鈕消失

def stop_operation(self):
    # ✅ 啟用開始按鈕
    self.start_btn.config(state='normal')
    
    # ✅ 禁用停止按鈕
    self.stop_btn.config(state='disabled')
```

### 規則7: 日誌系統優化

**平衡原則**: 有用的信息 vs 日誌過載

**分級策略**:
```python
# 1秒級別資料：每筆都記錄（重要監控）
if interval == 1:
    logger.info(f"✅ 插入: {symbol}@1s data_source={source}")

# 其他級別：每100筆記錄一次
elif count % 100 == 0:
    logger.info(f"✅ 已插入 {count} 筆 data_source={source}")

# 錯誤：永遠記錄
except Exception as e:
    logger.error(f"❌ 插入失敗: {e}")
```

**必要日誌**:
- ✅ 資料插入確認（含data_source）
- ✅ 操作開始/結束
- ✅ 錯誤和異常
- ✅ 重要狀態變更

**不必要日誌**:
- ❌ 內部函數調用trace
- ❌ 重複的debug信息
- ❌ 過於詳細的參數列表

### 規則8: GUI顯示內容管理

**問題**: 顯示區域過短，無法查看歷史記錄

**解決方案**:
```python
class GUILogManager:
    def __init__(self, max_lines=2000):
        self.max_lines = max_lines
        self.temp_log_file = "data/temp/gui_session.log"
        
    def log(self, message):
        # 寫入臨時日誌文件
        with open(self.temp_log_file, 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now()}: {message}\n")
        
        # GUI顯示（限制行數）
        current_lines = self.text_widget.get('1.0', 'end').count('\n')
        if current_lines > self.max_lines:
            # 刪除最舊的500行
            self.text_widget.delete('1.0', '500.0')
        
        self.text_widget.insert('end', f"{message}\n")
        self.text_widget.see('end')
    
    def clear_on_restart(self):
        """重啟時清空臨時日誌"""
        if os.path.exists(self.temp_log_file):
            os.remove(self.temp_log_file)
```

---

## 🟢 最佳實踐（建議遵循）

### 實踐1: 代碼修改前的檢查清單

**每次修改前必須確認**:
- [ ] 用戶是否明確要求此修改？
- [ ] 修改是否會影響現有功能？
- [ ] 是否需要用戶確認？
- [ ] 修改後如何驗證正確性？
- [ ] 是否有備份或回滾方案？

### 實踐2: 錯誤處理三層防護

```python
def critical_operation():
    try:
        # 第一層：參數驗證
        if not validate_params():
            raise ValueError("參數驗證失敗")
        
        # 第二層：執行操作
        result = execute()
        
        # 第三層：結果驗證
        if not validate_result(result):
            raise RuntimeError("結果驗證失敗")
        
        return result
        
    except ValueError as e:
        logger.error(f"參數錯誤: {e}")
        return None
    except RuntimeError as e:
        logger.error(f"執行錯誤: {e}")
        return None
    except Exception as e:
        logger.error(f"未知錯誤: {e}")
        traceback.print_exc()
        return None
```

### 實踐3: 文檔更新同步原則

**修改代碼時必須同步更新**:
1. 相關的README.md
2. 功能說明文檔
3. API文檔（如適用）
4. 更新日誌（CHANGELOG）

---

## 📈 持續改進機制

### 問題反饋循環

```mermaid
用戶報告問題 → AI分析根因 → 記錄到本文檔 → 
更新規則/實踐 → 下次遵循新規則 → 減少類似問題
```

### 效率提升目標

| 問題類型 | 當前平均時間 | 目標時間 | 改善策略 |
|----------|-------------|----------|----------|
| 理解用戶意圖 | 2-4小時 | 15-30分鐘 | 三次確認原則 |
| 複雜需求處理 | 1-3小時 | 30-60分鐘 | 分步驟確認 |
| GUI問題修復 | 30-90分鐘 | 15-30分鐘 | 標準模板 |

---

## 🎯 AI自我檢查清單

**每次開始任務前**:
- [ ] 我是否完整理解用戶需求？
- [ ] 我是否需要用戶確認我的理解？
- [ ] 我的計劃是否符合用戶原意？
- [ ] 我是否有擅自添加"優化"的衝動？

**每次修改代碼前**:
- [ ] 這個修改是用戶明確要求的嗎？
- [ ] 我是否檢查了資料優先級規則？
- [ ] 我是否實現了雙重顯示（GUI+終端機）？
- [ ] 我是否使用了台灣時間顯示？

**每次完成任務後**:
- [ ] 所有功能是否都經過驗證？
- [ ] 用戶是否能夠測試確認？
- [ ] 相關文檔是否已更新？
- [ ] 是否需要記錄新的問題/解決方案？

---

## 📚 相關文檔索引

### 核心規則文檔
- `docs/AI_IMPROVEMENT_GUIDELINES.md` - 本文檔（最高優先級）
- `docs/incidents/AI_betrayal.md` - AI違背行為記錄
- `docs/fixes/DATA_SOURCE_DISPLAY_FIX.md` - 資料來源顯示修復

### 技術實現文檔
- `docs/architecture/design/Blueprint.md` - 系統架構藍圖
- `docs/guides/optimization_usage_guide.md` - 優化使用指南
- `modules/utils/database/data_manager.py` - 資料管理器實現

### 問題記錄文檔
- `docs/reports/bugs/bug-Record.md` - Bug記錄
- `docs/reports/bugs/FINAL_FIXES_REPORT.md` - 最終修復報告

---

## ⚠️ 嚴重警告

**以下行為將導致用戶信任危機**:
1. 🔴 違背資料優先級規則（real被interpolated覆蓋）
2. 🔴 擅自整合/拆分用戶未要求的功能
3. 🔴 忽視用戶明確指示
4. 🔴 在未確認前執行重大修改
5. 🔴 刪除用戶未要求刪除的代碼/文件

**發現違背行為時**:
1. 立即停止當前操作
2. 向用戶道歉並說明錯誤
3. 詢問用戶期望的正確做法
4. 記錄到`docs/incidents/AI_betrayal.md`
5. 更新本文檔防止再次發生

---

**最後更新**: 2025-11-13  
**下次審查**: 每次發生重大問題後立即更新  
**維護者**: AI助手系統 + 用戶審核
