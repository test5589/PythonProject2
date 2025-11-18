# 📚 專案文檔總目錄

## 🎯 文檔導航

歡迎使用自動化交易機器人系統文檔。本文檔提供完整的導航指引，幫助您快速找到所需信息。

---

## 🔴 必讀核心文檔（最高優先級）

### 1. [AI_IMPROVEMENT_GUIDELINES.md](AI_IMPROVEMENT_GUIDELINES.md) 🤖
**AI開發核心規則與協作準則**
- 📊 用戶與AI最常遇到的困難分析
- 🔴 5條絕對不可違背的核心規則
- 🎯 資料優先級系統定義（real > Aggregation > interpolated > inferior-Aggregation > test）
- ✅ AI自我檢查清單
- ⚠️ 嚴重警告與違背行為處理

### 2. [COMPLETE_FIX_SUMMARY_20251113.md](COMPLETE_FIX_SUMMARY_20251113.md) 📊
**最新修復總結報告（2025-11-13）**
- ✅ 6個主要需求全部完成
- 🕐 時間顯示優化（台灣時間UTC+8）
- 🔧 聚合按鈕修復
- 📝 回補提示增強
- 📊 GUI日誌管理優化

### 3. [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md) 📂
**完整專案結構說明**
- 📁 所有目錄的用途和組織
- 🎯 關鍵文件導航
- 🚀 快速開始指南
- 📊 資料流程圖

---

## 📁 文檔結構總覽

### 🏗️ 架構設計 (`architecture/`)
系統核心設計與架構相關文檔

#### 🎨 設計文檔 (`design/`)
- **[Blueprint.md](architecture/design/Blueprint.md)** - 系統主要想法與架構藍圖 (v3.0 - 完整架構重組計劃)

#### ⚡ 優化建議 (`optimization/`)
- **[architecture_optimization.md](architecture/optimization/architecture_optimization.md)** - 架構優化建議
- **[performance_optimization.md](architecture/optimization/performance_optimization.md)** - 性能優化建議
- **[security_optimization.md](architecture/optimization/security_optimization.md)** - 安全強化建議
- **[code_optimization_recommendations.md](architecture/optimization/code_optimization_recommendations.md)** - 代碼優化建議
- **[additional_improvements.md](architecture/optimization/additional_improvements.md)** - 額外改善建議

#### 🏛️ 設計決策 (`decisions/`)
- **[implementation_plan.md](architecture/decisions/implementation_plan.md)** - 實施計劃與優先級

#### 📊 監控系統 (`monitoring/`)
- **[multi_symbol_monitoring_guide.md](architecture/monitoring/multi_symbol_monitoring_guide.md)** - 多符號監控指南

---

### 📖 使用指南 (`guides/`)
面向用戶的實用指南

- **[web_app_guide.md](guides/web_app_guide.md)** - Web視覺化應用使用指南（原WEB_APP_README.md）
- **[interval_guide.md](guides/interval_guide.md)** - 時間間隔設定指南
- **[optimization_usage_guide.md](guides/optimization_usage_guide.md)** - 系統優化使用指南
- **[quick_test_guide.md](guides/quick_test_guide.md)** - 快速測試指南

---

### 📊 報告文檔 (`reports/`)
系統分析與修復報告

#### 🔍 分析報告 (`analysis/`)
- **[GUI_TIME_SELECTOR_FIX_REPORT.md](reports/analysis/GUI_TIME_SELECTOR_FIX_REPORT.md)** - GUI時間選擇器修復
- **[WORKFLOW_GUI_COMPLETE_FIX.md](reports/analysis/WORKFLOW_GUI_COMPLETE_FIX.md)** - Workflow與GUI完整修復
- **[FINAL_GUI_FIX_REPORT.md](reports/analysis/FINAL_GUI_FIX_REPORT.md)** - GUI最終修復報告
- 更多詳細修復報告...

#### 🐛 Bug報告 (`bugs/`)
- **[bug-Record.md](reports/bugs/bug-Record.md)** - Bug追蹤記錄
- **[FINAL_FIXES_REPORT.md](reports/bugs/FINAL_FIXES_REPORT.md)** - 最終修復報告

#### 📈 優化報告 (`optimization/`)
- **[SYSTEM_OPTIMIZATION_REPORT.md](reports/optimization/SYSTEM_OPTIMIZATION_REPORT.md)** - 系統優化報告
- **[FINAL_OPTIMIZATION_SUMMARY_20251111.md](reports/optimization/FINAL_OPTIMIZATION_SUMMARY_20251111.md)** - 優化總結

---

### 📖 開發文檔 (`development/`)
開發相關指南與說明

#### 🧪 測試指南 (`testing/`)
- **[testing_guide.md](development/testing/testing_guide.md)** - 測試覆蓋完善指南

---

### 🚀 專案文檔 (`projects/`)
專案相關的重要參考

- **[API_BLOCK_TEST_COMPLETED.md](projects/API_BLOCK_TEST_COMPLETED.md)** - API封鎖測試完成報告
- **[advanced_api_test_reference.md](projects/advanced_api_test_reference.md)** - 進階API測試參考（原core/advanced_api_test.md）

---

### ⚠️ 事件記錄 (`incidents/`)
重要事件與教訓記錄

- **[AI_betrayal.md](incidents/AI_betrayal.md)** - AI違背用戶指令行為記錄與改善措施

---

### 🎯 功能文檔 (`features/`)
新功能的完整說明與實現細節

- **[FEATURE_SYMBOL_SELECTOR.md](features/FEATURE_SYMBOL_SELECTOR.md)** - 貨幣對選擇器功能完整說明
- **[PHASE3_ASYNC_ARCHITECTURE_COMPLETE.md](features/PHASE3_ASYNC_ARCHITECTURE_COMPLETE.md)** - 階段3異步架構完成

---

### 🔧 修復文檔 (`fixes/`)
特定問題的修復記錄

- **[BUGFIX_SYMBOL_BINDING_AND_CLEANUP.md](fixes/BUGFIX_SYMBOL_BINDING_AND_CLEANUP.md)** - 綁定驗證修復與貨幣對清理 (2025-11-16)
- **[DATA_SOURCE_DISPLAY_FIX.md](fixes/DATA_SOURCE_DISPLAY_FIX.md)** - 資料來源顯示修復完整記錄

---

### 📝 變更日誌 (`changelogs/`)
系統變更追蹤

- **[work.md](changelogs/work.md)** - 工作日誌（包含API權重評估系統）
- **[CHANGES_20251111.md](changelogs/CHANGES_20251111.md)** - 2025-11-11 變更記錄

---

### 📈 分析文檔 (`analysis/`)
系統分析與優化研究

- **[SYMBOL_USAGE_ANALYSIS.md](analysis/SYMBOL_USAGE_ANALYSIS.md)** - 貨幣對使用分析與錯誤預防 (2025-11-16)
- **[PROJECT_OPTIMIZATION_ANALYSIS.md](analysis/PROJECT_OPTIMIZATION_ANALYSIS.md)** - 專案優化分析
- **[FINAL_COMPLETE_OPTIMIZATION.md](analysis/FINAL_COMPLETE_OPTIMIZATION.md)** - 最終完整優化
- **[PROJECT_FINAL_OPTIMIZATION_SUMMARY.md](analysis/PROJECT_FINAL_OPTIMIZATION_SUMMARY.md)** - 專案最終優化總結

---

### 🔧 維護文檔 (`maintenance/`)
系統維護與運營指南

#### 📈 監控指南 (`monitoring.md`)
- 系統監控最佳實踐
- 性能指標追蹤

---

### 📦 歷史文檔 (`archive/`)
已歸檔的歷史文檔

- `fix_summary_20251111.md` - 2025-11-11 修復總結
- `optimization_complete_summary.md` - 優化完成總結
- `update_summary_20251111_final.md` - 更新總結
- **[monitoring.md](maintenance/monitoring.md)** - 監控與可觀察性指南

#### 💾 備份恢復 (`backup.md`)
- 數據備份與災難恢復

#### ⚡ 性能優化 (`performance.md`)
- 系統性能調優指南

---

### 📝 變更記錄 (`changelogs/`)
系統變更歷史記錄

- **[work.md](changelogs/work.md)** - 待實施的工作項目
- **[CHANGES_20251111.md](changelogs/CHANGES_20251111.md)** - 2025-11-11變更記錄

---

### 📊 系統報告 (`reports/`)
各類分析報告與修復記錄

#### 🔍 分析報告 (`analysis/`)
- **[FINAL_GUI_FIX_REPORT.md](reports/analysis/FINAL_GUI_FIX_REPORT.md)** - GUI修復最終報告
- **[WORKFLOW_GUI_COMPLETE_FIX.md](reports/analysis/WORKFLOW_GUI_COMPLETE_FIX.md)** - Workflow與GUI完整修復
- **[PROJECT_OPTIMIZATION_ANALYSIS.md](reports/analysis/PROJECT_OPTIMIZATION_ANALYSIS.md)** - 專案優化分析報告
- 其他分析報告...

#### 🛠️ 優化報告 (`optimization/`)
- **[CODE_OPTIMIZATION_RECOMMENDATIONS.md](reports/optimization/CODE_OPTIMIZATION_RECOMMENDATIONS.md)** - 代碼優化建議 (2025-11-16)
- **[FINAL_OPTIMIZATION_SUMMARY.md](reports/optimization/FINAL_OPTIMIZATION_SUMMARY.md)** - 最終優化總結
- **[SYSTEM_OPTIMIZATION_REPORT.md](reports/optimization/SYSTEM_OPTIMIZATION_REPORT.md)** - 系統優化報告
- **[SCRIPTS_AND_COMMANDS_INVENTORY.md](reports/optimization/SCRIPTS_AND_COMMANDS_INVENTORY.md)** - 腳本與命令清單

#### 📋 完成報告 (`completion/`)
- **[WEEKLY_IMPROVEMENTS_COMPLETE.md](reports/completion/WEEKLY_IMPROVEMENTS_COMPLETE.md)** - 本周改進完成報告 (2025-11-16)
- **[PROJECT_OPTIMIZATION_COMPLETE_20251113.md](reports/completion/PROJECT_OPTIMIZATION_COMPLETE_20251113.md)** - 專案優化完成 (2025-11-13)

#### 🐛 錯誤報告 (`bugs/`)
- **[bug-Record.md](reports/bugs/bug-Record.md)** - 錯誤記錄
- **[FINAL_FIXES_REPORT.md](reports/bugs/FINAL_FIXES_REPORT.md)** - 最終修復報告

---

## 🚀 快速入門

### 新用戶建議閱讀順序
1. **[Blueprint.md](architecture/design/Blueprint.md)** - 了解系統架構與最新優化計劃
2. **[architecture_optimization.md](architecture/optimization/architecture_optimization.md)** - 架構優化建議
3. **[implementation_plan.md](architecture/decisions/implementation_plan.md)** - 實施計劃
4. **[testing_guide.md](development/testing/testing_guide.md)** - 測試指南

### 開發者建議閱讀順序
1. **[Blueprint.md](architecture/design/Blueprint.md)** - 系統設計理念與架構藍圖
2. **[architecture_optimization.md](architecture/optimization/architecture_optimization.md)** - 架構優化
3. **[performance_optimization.md](architecture/optimization/performance_optimization.md)** - 性能優化
4. **[security_optimization.md](architecture/optimization/security_optimization.md)** - 安全強化
5. **[PROJECT_OPTIMIZATION_ANALYSIS.md](reports/analysis/PROJECT_OPTIMIZATION_ANALYSIS.md)** - 最新優化分析

---

## 🔍 文檔搜索提示

### 按主題查找
- **架構設計**: 查看 `architecture/` 目錄
- **API權重**: 查看 `architecture/design/Blueprint.md`
- **優化建議**: 查看 `architecture/optimization/` 目錄
- **測試指南**: 查看 `development/testing/` 目錄
- **監控指南**: 查看 `maintenance/monitoring.md`
- **錯誤修復**: 查看 `reports/bugs/` 目錄

### 按文件類型查找
- **架構文檔**: `architecture/` 目錄
- **開發指南**: `development/` 目錄
- **用戶說明**: `user-guides/` 目錄
- **維護手冊**: `maintenance/` 目錄
- **分析報告**: `reports/analysis/` 目錄
- **修復記錄**: `reports/bugs/` 目錄
- **變更歷史**: `changelogs/` 目錄

---

## 📞 聯繫與貢獻

### 文檔維護
- 文檔問題請查看 `[work.md](changelogs/work.md)`
- 新功能建議請更新 `Blueprint.md`
- 代碼變更請記錄在 `changelogs/`

### 版本信息
- **最後更新**: 2025-11-13
- **文檔版本**: v3.0 (完整架構重組與優化計劃)
- **系統版本**: 自動化交易機器人 v2.1+

---

## 🎯 導航提示

- 📁 **目錄結構**: 使用左側樹狀圖瀏覽
- 🔍 **搜索功能**: 使用頁面內搜索 (Ctrl+F)
- 📎 **交叉引用**: 點擊藍色鏈接跳轉
- 📝 **編輯建議**: 如發現問題，請更新 `work.md`

---

*文檔最後更新: 2025-11-13*  
*維護者: Cascade AI Assistant*  
*適用系統: 自動化交易機器人 v3.0*
