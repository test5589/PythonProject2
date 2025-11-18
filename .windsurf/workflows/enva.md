---
description: 數據庫資料分析
---

# 數據庫資料分析工作流程

## 環境設定

1. **使用DB Browser數據庫**
   - 主要工具：DB Browser for SQLite
   - 用於查看和管理交易資料
   - 支援SQL查詢和資料匯出

2. **開發環境**
   - 主要IDE：PyCharm 2025.2.3
   - Python版本：使用虛擬環境
   - 專案根目錄：自動化交易機器人系統

3. **未來發展規劃**
   - 後端資料庫：計劃添加上傳和修改功能
   - 前端開發：考慮新增web前端界面
   - 資料分析：擴展更多分析功能

## 工作流程步驟

### 步驟1：檢查變更需求
```bash
# 檢查 docs/changelogs/work.md 是否有新的程式碼需求
cat docs/changelogs/work.md
```

### 步驟2：檢查架構藍圖  
```bash
# 檢查 docs/architecture/Blueprint.md 的主要想法
cat docs/architecture/Blueprint.md
```

### 步驟3：實施程式碼變更
- 根據work.md的需求添加或修改程式碼
- 參考Blueprint.md進行架構設計
- 允許微調和補充擴張

### 步驟4：文件分類整理
```bash
# 檢查專案根目錄的md文件
find . -name "*.md" -maxdepth 1

# 移動未分類的md文件到docs目錄
# 根據內容分類到適當的子目錄
```

### 步驟5：更新文檔
- 更新相關的技術文檔
- 記錄變更歷史
- 維護架構一致性

## 重要規則

1. **不可刪除的文件**：
   - `docs/changelogs/work.md`
   - `docs/architecture/Blueprint.md`

2. **文件分類**：
   - 每次行動後檢查.md文件是否需要分類
   - 歸放到docs目錄的適當位置

3. **每次工作檢查.md檔案分類**：
   - 每次開始工作時，必須檢查專案根目錄是否有未分類的.md檔案
   - 如果發現未分類的.md檔案，立即將其移動到docs目錄的適當子目錄
   - 分類原則：技術文檔→docs/，分析報告→docs/analysis/，架構設計→docs/architecture/

4. **每次結束工作檢查.md檔案優化**：
   - 每次結束工作前，必須檢查所有.md檔案內容是否需要優化
   - 檢查內容是否需要補充、刪減或合併重複內容
   - 確保文檔結構清晰、內容準確、格式統一
   - 刪除過時或重複的文檔內容

5. **自訂分析目錄**：
   - `docs/analysis/` - AI分析和察看內容
   - 用於存放系統分析報告和改善建議

## 使用方式

執行此workflow時，請按照步驟順序進行，確保：
- 程式碼變更符合架構設計
- 文檔分類完整
- 開發環境一致性
