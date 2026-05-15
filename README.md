# 加密貨幣交易機器人

自動化加密貨幣交易與數據回補系統

---

## 🚀 啟動程式

### 主程式（唯一正確的入口）

```bash
python core/gui_main.py
```

這是**唯一正確**的程式啟動方式。啟動後會開啟GUI主控台。

---

## 🛠️ 獨立工具

以下是可以獨立運行的工具程式（非主程式入口）：

### 日誌查看器
```bash
python modules/utils/tools/log_viewer.py
```
用於查看歷史日誌文件。

---

## ⚠️ 重要說明

### 已清理的入口點

以下文件的 `if __name__ == "__main__"` 區塊已被移除或註釋：

- ❌ `config/api_config.py` - 配置文件，僅供導入
- ❌ `config/api_security.py` - 安全配置，僅供導入
- 🗑️ `core/Gui.py` - 舊版入口，**已徹底移除**
- ❌ `modules/monitors/monitor_spread.py` - 監控模組，應被主程式調用

### 為什麼要清理？

多個程式入口會造成：
- 🔴 新手不知道從哪裡啟動
- 🔴 可能讀取不同的配置
- 🔴 難以追蹤程式執行路徑
- 🔴 部署時容易出錯

---

## 📁 專案結構

```
PythonProject2/
├── core/                    # 核心模組
│   ├── gui_main.py         # ✅ 主程式入口（唯一）
│   ├── gui_backfill.py     # 回補功能GUI
│   └── gui_controls.py     # GUI控制元件
│
├── modules/                 # 功能模組
│   ├── utils/              # 工具函數
│   │   ├── api/            # API客戶端
│   │   ├── database/       # 資料庫管理
│   │   ├── backfill/       # 數據回補
│   │   ├── data/           # 數據處理
│   │   └── tools/          # 獨立工具
│   └── monitors/           # 監控模組
│
├── config/                  # 配置文件
│   ├── api_config.py       # API配置
│   ├── api_security.py     # 安全配置
│   └── trading_config.py   # 交易配置
│
├── docs/                    # 文檔
│   ├── code_architecture_review.md
│   ├── database_insert_performance.md
│   └── ...
│
└── data/                    # 數據存儲
    ├── database.db         # SQLite資料庫
    └── logs/               # 日誌文件
```

---

## 🔧 開發指南

### 配置設置

```python
# 導入配置（正確方式）
from config.api_config import setup_multiple_apis, list_api_status
from config.api_security import api_key_manager

# 在主程式中調用
setup_multiple_apis()
list_api_status()
```

### 測試功能

如需測試特定模組功能，請在主程式中導入並調用：

```python
# 測試監控功能
from modules.monitors.monitor_spread import monitor_spread
monitor_spread()

# 測試API金鑰管理
from config.api_security import setup_demo_keys
setup_demo_keys()
```

**⚠️ 不要直接運行模組文件！**

---

## 📊 最近更新

### 2025-11-15 性能優化

- ✅ 批量插入優化：速度提升 **6倍**
- ✅ 移除不必要延遲：速度提升 **5倍**
- ✅ 總體性能提升：**18倍加速**（36秒 → 2秒）

### 2025-11-15 架構清理

- ✅ 清理多餘程式入口點
- ✅ 明確標註主程式入口
- ✅ 改善代碼維護性

詳細信息請參閱：`docs/code_architecture_review.md`

---

## 🐛 問題回報

如遇到問題，請檢查：

1. **確認使用正確的啟動方式**：`python core/gui_main.py`
2. 檢查虛擬環境是否已激活
3. 查看日誌文件：`data/logs/`
4. 參閱文檔：`docs/`

---

## 📝 授權

此專案供個人使用，請勿用於商業用途。

---

*最後更新：2025-11-15*  
*維護者：交易機器人開發團隊*
