# 📂 專案結構完整說明

**更新日期**: 2025-11-13  
**版本**: 2.0

---

## 🎯 專案總覽

這是一個自動化交易機器人系統，具備資料收集、存儲、分析和視覺化功能。

---

## 📁 根目錄結構

```
PythonProject2/
├── 📂 core/              # 核心GUI應用程式
├── 📂 modules/           # 功能模組
├── 📂 docs/              # 📚 完整文檔系統
├── 📂 data/              # 資料存儲（資料庫、臨時文件）
├── 📂 config/            # 配置文件
├── 📂 web/               # Web視覺化應用
├── 📂 tests/             # 單元測試
├── 📂 tools/             # 工具腳本
├── 📂 ai_testing/        # AI測試開發區
├── 📂 archive/           # 歷史備份
├── 📂 logs/              # 日誌文件
├── 📂 examples/          # 使用範例
├── .windsurf/            # Windsurf IDE 配置
└── requirements.txt      # Python 依賴
```

---

## 🏗️ 核心目錄詳解

### 📂 `core/` - 核心應用

**用途**: GUI主程式和核心功能模組

```
core/
├── gui_main.py              # 主GUI入口
├── gui_controls.py          # 控制項管理器
├── gui_backfill.py          # 回補功能
├── gui_monitoring.py        # 監控功能
├── gui_utils.py             # 工具函數
├── panels/                  # GUI面板
│   └── query_panel.py       # 查詢面板
└── gui/                     # GUI子模組
    ├── button_controls.py   # 按鈕控制
    ├── controls_base.py     # 基礎控制項
    └── quick_controls.py    # 快捷控制
```

**關鍵文件**:
- `gui_main.py` - 應用程式啟動入口
- `gui_controls.py` - 統一管理所有GUI控制項

---

### 📂 `modules/` - 功能模組

**用途**: 可重用的功能模組

```
modules/
├── utils/                   # 工具模組
│   ├── api/                 # API客戶端
│   │   └── api_client.py    # Binance API客戶端
│   ├── database/            # 資料庫操作
│   │   ├── db_core.py       # 資料庫核心
│   │   └── data_manager.py  # 資料管理器（優先級控制）
│   ├── data/                # 資料處理
│   │   ├── ws_aggregator.py # WebSocket聚合器（1秒資料）
│   │   └── aggregation_utils.py # 資料聚合工具
│   └── backfill/            # 回補功能
│       ├── backfill_data.py # 回補資料
│       └── auto_heal_core.py # 智能修補核心
└── monitors/                # 監控模組
    └── multi_symbol_monitor.py # 多貨幣對監控
```

**關鍵模組**:
- `api_client.py` - 負責與Binance API通信
- `data_manager.py` - 實現資料優先級保護系統
- `auto_heal_core.py` - 智能修補和內插功能

---

### 📂 `docs/` - 文檔系統 📚

**用途**: 完整的專案文檔和指南

```
docs/
├── 🔴 AI_IMPROVEMENT_GUIDELINES.md     # AI核心規則（最高優先級）
├── 📊 COMPLETE_FIX_SUMMARY_20251113.md # 最新修復總結
├── 📂 PROJECT_STRUCTURE.md             # 本文檔（專案結構）
├── 📖 README.md                         # 文檔導航索引
│
├── architecture/            # 🏗️ 系統架構
│   ├── design/              # 設計文檔
│   │   ├── Blueprint.md     # 系統架構藍圖（v3.0）
│   │   ├── GUI_improvements.md
│   │   └── api_weight_system_guide.md
│   ├── optimization/        # 優化建議
│   │   ├── architecture_optimization.md
│   │   ├── performance_optimization.md
│   │   ├── security_optimization.md
│   │   └── code_optimization_recommendations.md
│   ├── decisions/           # 設計決策
│   │   └── implementation_plan.md
│   └── monitoring/          # 監控系統
│       └── multi_symbol_monitoring_guide.md
│
├── guides/                  # 📖 使用指南
│   ├── web_app_guide.md     # Web應用使用指南
│   ├── interval_guide.md    # 時間間隔指南
│   ├── optimization_usage_guide.md # 優化使用指南
│   └── quick_test_guide.md  # 快速測試指南
│
├── reports/                 # 📊 報告文檔
│   ├── analysis/            # 分析報告
│   │   ├── GUI_TIME_SELECTOR_FIX_REPORT.md
│   │   ├── WORKFLOW_GUI_COMPLETE_FIX.md
│   │   ├── FINAL_GUI_FIX_REPORT.md
│   │   └── ... (8個詳細修復報告)
│   ├── bugs/                # Bug報告
│   │   ├── bug-Record.md    # Bug記錄
│   │   └── FINAL_FIXES_REPORT.md
│   └── optimization/        # 優化報告
│       ├── SYSTEM_OPTIMIZATION_REPORT.md
│       └── FINAL_OPTIMIZATION_SUMMARY_20251111.md
│
├── fixes/                   # 🔧 修復文檔
│   └── DATA_SOURCE_DISPLAY_FIX.md
│
├── incidents/               # ⚠️ 事件記錄
│   └── AI_betrayal.md       # AI違背行為記錄
│
├── projects/                # 🚀 專案相關
│   ├── API_BLOCK_TEST_COMPLETED.md
│   └── advanced_api_test_reference.md
│
├── changelogs/              # 📝 變更日誌
│   ├── work.md              # 工作日誌
│   └── CHANGES_20251111.md  # 變更記錄
│
├── development/             # 🛠️ 開發文檔
│   └── testing/
│       └── testing_guide.md # 測試指南
│
├── maintenance/             # 🔧 維護文檔
│   └── monitoring.md        # 監控指南
│
├── analysis/                # 📈 分析文檔
│   ├── PROJECT_OPTIMIZATION_ANALYSIS.md
│   ├── FINAL_COMPLETE_OPTIMIZATION.md
│   └── PROJECT_FINAL_OPTIMIZATION_SUMMARY.md
│
└── archive/                 # 📦 歷史文檔
    ├── fix_summary_20251111.md
    ├── optimization_complete_summary.md
    └── update_summary_20251111_final.md
```

---

### 📂 `data/` - 資料目錄

**用途**: 存儲資料庫和臨時文件

```
data/
├── system_data.db           # 主資料庫（SQLite）
├── temp/                    # 臨時文件目錄
│   └── gui_session.log      # GUI會話日誌（重啟時清空）
└── *.json                   # 測試結果JSON文件
```

**重要**: 
- `system_data.db` 包含所有交易資料
- `temp/` 目錄會在重啟時自動清理

---

### 📂 `web/` - Web應用

**用途**: Streamlit資料視覺化應用

```
web/
├── streamlit_app.py         # Streamlit主應用
└── components/              # Web組件
    └── visualizations.py    # 視覺化組件
```

**啟動方式**:
```bash
streamlit run web/streamlit_app.py
```

---

### 📂 `config/` - 配置文件

**用途**: 系統配置

```
config/
├── settings.json            # 系統設定
└── api_keys.json            # API密鑰（請勿提交到Git）
```

---

### 📂 `tests/` - 測試文件

**用途**: 單元測試和集成測試

```
tests/
├── test_api_client.py
├── test_data_manager.py
└── test_backfill.py
```

---

### 📂 `tools/` - 工具腳本

**用途**: 獨立工具腳本

```
tools/
├── db_inspector.py          # 資料庫檢查工具
├── data_cleaner.py          # 資料清理工具
└── backup_manager.py        # 備份管理工具
```

---

### 📂 `ai_testing/` - AI測試區

**用途**: AI輔助開發和測試

```
ai_testing/
├── README.md                # AI測試說明
├── tests/                   # 各種測試腳本
└── debug/                   # 除錯文件
```

---

## 🎯 關鍵文件導航

### 🔴 必讀文檔（最高優先級）

1. **`docs/AI_IMPROVEMENT_GUIDELINES.md`**  
   - AI開發核心規則
   - 資料優先級系統定義
   - 用戶-AI協作準則

2. **`docs/architecture/design/Blueprint.md`**  
   - 系統架構完整藍圖
   - 6個時間框架邏輯
   - 資料流程設計

3. **`docs/COMPLETE_FIX_SUMMARY_20251113.md`**  
   - 最新修復總結
   - 所有6個需求的完整實現

### 🟡 重要參考文檔

4. **`docs/guides/web_app_guide.md`**  
   - Web視覺化應用使用指南
   - 資料來源分析方法

5. **`docs/incidents/AI_betrayal.md`**  
   - AI違背行為記錄
   - 教訓和改善措施

6. **`modules/utils/database/data_manager.py`**  
   - 資料優先級實現代碼
   - 插入/覆蓋邏輯

### 🟢 開發參考

7. **`docs/changelogs/work.md`**  
   - API權重評估系統
   - 工作進度追蹤

8. **`docs/reports/bugs/bug-Record.md`**  
   - 已知問題和修復狀態

---

## 🚀 快速開始

### 1. 啟動GUI應用
```bash
python core/gui_main.py
```

### 2. 啟動Web視覺化
```bash
streamlit run web/streamlit_app.py
```

### 3. 運行測試
```bash
python -m pytest tests/
```

---

## 📊 資料流程圖

```
用戶操作 (GUI)
    ↓
核心控制器 (gui_main.py)
    ↓
功能模組 (modules/)
    ├→ API客戶端 → Binance API
    ├→ 資料管理器 → 資料庫 (data/)
    ├→ 回補模組 → 智能修補
    └→ 監控模組 → WebSocket聚合
         ↓
    資料驗證 (優先級檢查)
         ↓
    資料庫存儲 (SQLite)
         ↓
    Web視覺化 (Streamlit)
```

---

## 🔒 重要規則

### 資料優先級系統 🔴

```python
PRIORITY_MAP = {
    'real': 1,                    # 最高優先級 - 真實市場資料
    'Aggregation': 2,             # 純真實資料聚合
    'interpolated': 3,            # 線性內插資料
    'inferior-Aggregation': 4,    # 混合來源聚合
    'test': 5                     # 最低優先級 - 測試資料
}
```

**絕對規則**:
- ✅ real資料可以覆蓋所有其他類型
- ❌ interpolated永遠不可覆蓋real資料
- ⚠️ 資料唯一性由5個維度決定：timestamp + api + category + symbol + interval

---

## 📝 文檔維護

### 文檔更新原則

1. **重大變更**：必須更新 `AI_IMPROVEMENT_GUIDELINES.md`
2. **架構變更**：必須更新 `Blueprint.md`
3. **Bug修復**：記錄到 `bug-Record.md`
4. **功能新增**：更新對應的guide文檔

### 文檔層級

- **🔴 核心文檔**: 永遠不可刪除，必須保持更新
- **🟡 重要文檔**: 頻繁參考，定期審查
- **🟢 參考文檔**: 偶爾查閱，可歸檔
- **📦 歷史文檔**: 已歸檔到 `archive/`

---

## 🎯 下一步行動

### 新用戶
1. 閱讀 `docs/README.md` - 文檔導航
2. 閱讀 `docs/AI_IMPROVEMENT_GUIDELINES.md` - 核心規則
3. 啟動GUI並測試基本功能

### 開發者
1. 熟悉 `modules/` 結構
2. 閱讀 `Blueprint.md` 了解架構
3. 查看 `data_manager.py` 理解資料流程

### AI助手
1. **必讀** `AI_IMPROVEMENT_GUIDELINES.md` - 每次任務前確認規則
2. 參考 `AI_betrayal.md` - 避免重複錯誤
3. 遵守資料優先級系統 - 神聖不可侵犯

---

## 📞 問題排查

遇到問題時的檢查順序：

1. **GUI問題** → 查看 `docs/reports/analysis/`
2. **資料問題** → 檢查 `data_manager.py` 日誌
3. **API問題** → 參考 `api_client.py` 和錯誤日誌
4. **歷史問題** → 查閱 `bug-Record.md`

---

**維護者**: AI助手系統 + 用戶  
**最後審查**: 2025-11-13  
**版本**: 2.0 - 完整結構重組
