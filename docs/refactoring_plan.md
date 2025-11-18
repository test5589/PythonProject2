# 大文件拆分方案

**日期**: 2025-11-15  
**目標**: 拆分3個大文件以提升可維護性

---

## 📋 文件列表

| 文件 | 當前行數 | 複雜度 | 優先級 |
|------|----------|--------|--------|
| `data_manager.py` | 504 | 高 | P1 |
| `api_client.py` | 497 | 高 | P2 |
| `anchor_engine.py` | 406 | 中 | P3 |

---

## 🎯 拆分原則

1. **不改變功能** - 只重構結構，不修改邏輯
2. **好維護** - 單一職責，清晰命名
3. **簡潔** - 移除不必要的層級
4. **必要** - 只拆分真正需要的部分

---

## 📁 拆分方案 1: data_manager.py (504行)

### 當前結構分析

```
data_manager.py (504行)
├── DataManager類 (主類)
│   ├── 插入相關方法 (~200行)
│   │   ├── insert_single_data()
│   │   ├── _validate_kline_data()
│   │   ├── _extract_timestamp()
│   │   ├── _check_existing_data()
│   │   └── _insert_single_in_transaction()
│   ├── 批量操作方法 (~100行)
│   │   └── batch_insert_data()
│   ├── 優先級管理 (~50行)
│   │   ├── priority_map
│   │   └── 覆蓋邏輯
│   └── 統計與工具 (~100行)
│       ├── _stats
│       ├── get_stats()
│       └── _build_result()
├── 全域函數 (~50行)
│   ├── insert_data() - 向後兼容
│   └── batch_insert_data() - 全域函數
└── 全域鎖 (_db_operation_lock)
```

### 拆分方案

```
modules/utils/database/
├── db_core.py           # 已存在，不動
├── data_manager.py      # 主入口（簡化為 ~100行）
├── insert_handler.py    # 插入邏輯 (~200行) 新建
├── batch_handler.py     # 批量操作 (~100行) 新建
├── priority_manager.py  # 優先級管理 (~50行) 新建
└── stats_collector.py   # 統計收集 (~50行) 新建
```

### 職責劃分

#### 1. `data_manager.py` (簡化後 ~100行)
- 統一入口和接口
- 協調各個Handler
- 維護向後兼容性

#### 2. `insert_handler.py` (新建 ~200行)
- `insert_single_data()` - 單筆插入
- `_validate_kline_data()` - 數據驗證
- `_extract_timestamp()` - 時間戳提取
- `_check_existing_data()` - 重複檢查
- `_insert_single_in_transaction()` - 事務插入

#### 3. `batch_handler.py` (新建 ~100行)
- `batch_insert_data()` - 批量插入
- 批量事務管理
- 批量統計

#### 4. `priority_manager.py` (新建 ~50行)
- `priority_map` - 優先級映射
- `check_priority()` - 優先級檢查
- 覆蓋邏輯判斷

#### 5. `stats_collector.py` (新建 ~50行)
- 統計數據收集
- `get_stats()` - 獲取統計
- `reset_stats()` - 重置統計

---

## 📁 拆分方案 2: api_client.py (497行)

### 當前結構分析

```
api_client.py (497行)
├── APIClient類
│   ├── 請求方法 (~150行)
│   │   ├── get_klines()
│   │   ├── _make_request()
│   │   └── 錯誤處理
│   ├── 參數驗證 (~200行)
│   │   ├── clean_category()
│   │   ├── clean_symbol()
│   │   ├── clean_interval()
│   │   ├── clean_start_time()
│   │   ├── clean_end_time()
│   │   ├── clean_limit()
│   │   ├── clean_from_id()
│   │   └── clean_to_id()
│   └── 數據解析 (~100行)
│       └── _parse_response()
└── 異常類定義 (~50行)
```

### 拆分方案

```
modules/utils/api/
├── api_client.py        # 主客戶端（簡化為 ~150行）
├── validators.py        # 參數驗證 (~200行) 新建
├── parsers.py           # 數據解析 (~100行) 新建
└── exceptions.py        # 異常定義 (~50行) 新建
```

---

## 📁 拆分方案 3: anchor_engine.py (406行)

### 評估

406行處於臨界點，建議：
- **暫不拆分** - 除非超過500行
- 結構已經相對清晰
- 拆分收益不大

如需拆分，可以：
```
modules/strategies/anchor/
├── anchor_engine.py     # 主引擎
├── anchor_calculator.py # 計算邏輯
└── anchor_validator.py  # 驗證邏輯
```

---

## 🚀 執行順序

1. **第一步**: 拆分 `data_manager.py` (最重要)
2. **第二步**: 拆分 `api_client.py`
3. **第三步**: 評估 `anchor_engine.py`（可選）

---

## ✅ 拆分檢查清單

每個文件拆分後需要檢查：

- [ ] 所有導入正確
- [ ] 功能完全相同
- [ ] 測試通過
- [ ] 無循環依賴
- [ ] 向後兼容性保持
- [ ] 文檔更新

---

*計劃日期: 2025-11-15*  
*執行人: AI Code Refactorer*
