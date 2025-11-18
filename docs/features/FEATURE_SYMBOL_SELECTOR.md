# 貨幣對選擇器功能 - 使用說明

**日期**: 2025-11-16  
**狀態**: ✅ **已完成並可使用**  
**功能**: 回補前選擇要處理的貨幣對

---

## 🎯 功能概述

### 用戶需求

> "開始回補資料按鈕我希望能選定我要選擇的貨幣種類，請記住，這個功能必須區分成兩部分，就是資產分類中的crypto和股票，這兩個一定要區分清楚，然後如果我選擇crypto，我可以用選擇性來選取我要的種類，就是假如我要選十種貨幣，這個回補就只會執行這十種貨幣，假如我選擇一鍵全部，他就會按照順序一個一個開始回補。而回補資料按鈕要選擇的貨幣不超過15種(極限)。"

### 實現功能

✅ **分類顯示** - Crypto 和 Stock 分開  
✅ **多選功能** - 最多選擇 15 個貨幣對  
✅ **搜索過濾** - 快速找到想要的貨幣對  
✅ **快速操作** - 全選、清除、反選  
✅ **視覺分組** - 按類型分組顯示  
✅ **限制保護** - 超過15個會警告

---

## 📸 界面預覽

```
┌─────────────────────────────────────────────────────────┐
│  選擇回補貨幣對 - 加密貨幣                                │
├─────────────────────────────────────────────────────────┤
│  🔍 搜索: [______________]  [🗹全選] [☐清除] [↻反選]     │
│                                          已選: 5/15      │
├─────────────────────────────────────────────────────────┤
│  💡 提示：最多選擇 15 個貨幣對進行回補                    │
│                                                          │
│  💎 主流幣                                                │
│  ☑ BTC    ☑ ETH    ☑ XRP    ☐ BNB                       │
│  ☑ SOL    ☑ ADA    ☐ DOGE   ☐ TRX                       │
│                                                          │
│  💵 穩定幣                                                │
│  ☐ USDT   ☐ USDC   ☐ DAI    ☐ USDS                      │
│                                                          │
│  🔒 質押代幣                                              │
│  ☐ STETH  ☐ WSTETH ☐ RETH   ☐ WETH                      │
│                                                          │
│  ⛓️ Layer1/2                                             │
│  ☐ ARB    ☐ OP     ☐ SUI    ☐ SEI                       │
│                                                          │
│  ... (更多分類)                                          │
│                                                          │
├─────────────────────────────────────────────────────────┤
│                               [✓ 確定]  [✗ 取消]         │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 使用流程

### 步驟1: 開始回補

1. 在GUI主界面，填寫資產分類（crypto 或 stock）
2. 選擇時間範圍
3. 點擊「開始回補資料」按鈕

### 步驟2: 選擇貨幣對

選擇器對話框自動彈出：

```
💡 請選擇要回補的貨幣對（最多15個）...
```

### 步驟3: 選擇方式

#### 方式A: 逐個選擇
- 直接勾選想要的貨幣對
- 最多15個

#### 方式B: 搜索選擇
1. 在搜索框輸入貨幣名稱（如 "BTC"）
2. 列表自動過濾
3. 勾選想要的貨幣對

#### 方式C: 批量操作
- **全選** - 選擇當前可見的所有貨幣對（最多15個）
- **清除** - 取消所有選擇
- **反選** - 反轉當前選擇狀態

### 步驟4: 確認選擇

1. 檢查右上角的計數：`已選: X/15`
2. 點擊「✓ 確定」開始回補
3. 或點擊「✗ 取消」放棄

### 步驟5: 回補開始

```
🧩 本次回補貨幣對: BTC, ETH, SOL, ADA, XRP (共5個)
⏳ 開始補齊 crypto 資料 [間隔: 1m]...
```

---

## 💎 貨幣對分類

### Crypto（加密貨幣）- 150+ 種

#### 💎 主流幣（10種）
```
BTCUSDT, ETHUSDT, XRPUSDT, BNBUSDT, SOLUSDT
ADAUSDT, DOGEUSDT, TRXUSDT, LINKUSDT, AVAXUSDT
```

#### 💵 穩定幣（17種）
```
USDTUSDT, USDCUSDT, DAIUSDT, USDSUSDT, FDUSDUSDT
PYUSDUSDT, USDEUSDT, USDYUSDT, USDFUSDT, USTBUSDT
USDT0USDT, USDTBUSDT, USD1USDT, C1USDUSDT, USDGUSDT
BSC-USDUSDT, USDC.EUSDT
```

#### 🔒 質押代幣（13種）
```
STETHUSDT, WSTETHUSDT, RETHUSDT, WETHUSDT, WBETHUSDT
EZETHUSDT, RSETHUSDT, OSETHUSDT, WEETHUSDT, METHUSDT
SUSDEUSDT, SUSDSUSDT, LSETHUSDT
```

#### 🎁 Wrapped代幣（8種）
```
WBTCUSDT, WBTUSDT, WBNBUSDT, LBTCUSDT, FBTCUSDT
CBBTCUSDT, CLBTCUSDT, SOLVBTCUSDT
```

#### ⛓️ Layer 1/2（22種）
```
ARBUSDT, OPUSDT, STRKUSDT, SEIUSDT, SUIUSDT
APTUSDT, NEARUSDT, ICPUSDT, INJUSDT, ATOMUSDT
DOTUSDT, XLMUSDT, VETUSDT, ALGOUSDT, FILUSDT
HBARUSDT, QNTUSDT, KASUSDT, XTZUSDT, STXUSDT
TONUSDT, XDCUSDT
```

#### 🏦 DeFi（9種）
```
UNIUSDT, AAVEUSDT, CRVUSDT, CAKEUSDT, GRTUSDT
JUPUSDT, JUPSOLUSDT, JITOSOLUSDT, JLPUSDT
```

#### 🐸 Meme幣（5種）
```
SHIBUSDT, PEPEUSDT, BONKUSDT, WLDUSDT, FLRUSDT
```

#### 🤖 AI/新概念（6種）
```
TAOUSDT, FETUSDT, ENAUSDT, VIRTUALUSDT, HYPEUSDT, TIAUSDT
```

#### 🏢 交易所代幣（7種）
```
OKBUSDT, BGBUSDT, HTXUSDT, KCSUSDT, GTUSDT
LEOUSDT, CROUSDT
```

#### 🔐 隱私幣（3種）
```
XMRUSDT, ZECUSDT, DASHUSDT
```

#### 📜 老牌幣（3種）
```
LTCUSDT, BCHUSDT, ETCUSDT
```

#### 🏆 貴金屬錨定（2種）
```
XAUTUSDT, PAXGUSDT
```

#### 🌟 其他特殊代幣（50+種）
```
PIUSDT, ONDOUSDT, POLUSDT, HASHUSDT, SKYUSDT
RAINUSDT, AEROUSDT, OUSGUSDT, FTNUSDT, JAAAUSDT
... (更多)
```

### Stock（股票）
```
目前預留，未來添加
例如: AAPL, TSLA, GOOGL 等
```

---

## ⚙️ 技術細節

### 文件結構

```
core/
└── gui_symbol_selector.py  (NEW)
    ├── SymbolSelectorDialog        # 選擇器對話框
    ├── select_symbols_for_backfill # 便捷函數
    └── 500+ 行完整實現

config/
└── trading_config.py
    ├── CRYPTO_SYMBOLS (150+)       # 加密貨幣列表
    ├── STOCK_SYMBOLS               # 股票列表（預留）
    ├── SUPPORTED_SYMBOLS           # 所有支援的
    └── MAX_BACKFILL_SYMBOLS = 15   # 最大限制

core/
└── gui_backfill.py
    └── backfill_data()
        └── 集成選擇器調用
```

### 關鍵組件

#### 1. SymbolSelectorDialog 類

```python
class SymbolSelectorDialog:
    """貨幣對選擇器對話框"""
    
    def __init__(self, parent, category, current_selection):
        # 初始化對話框
        
    def create_ui(self):
        # 創建UI組件
        
    def create_checkbuttons(self):
        # 創建多選框
        
    def on_selection_change(self):
        # 處理選擇變化
        
    def select_all(self):
        # 全選功能
```

#### 2. 便捷函數

```python
def select_symbols_for_backfill(parent, category, current_selection):
    """
    打開選擇器並返回用戶選擇
    
    Returns:
        list: 用戶選擇的貨幣對列表
        None: 用戶取消
    """
```

#### 3. GUI集成

```python
# gui_backfill.py
from core.gui_symbol_selector import select_symbols_for_backfill

target_symbols = select_symbols_for_backfill(
    parent=gui.root,
    category=cat,  # 'crypto' 或 'stock'
    current_selection=None
)

if not target_symbols:
    gui.log("❌ 已取消回補")
    return
```

---

## 🛡️ 安全限制

### 最大數量限制

**限制**: 15 個貨幣對

**原因**:
1. 避免一次性回補過多資料
2. 防止資料庫壓力過大
3. 減少API請求負擔
4. 確保回補可控

**實現**:
```python
# config/trading_config.py
MAX_BACKFILL_SYMBOLS = 15

# 選擇器中自動檢查
if selected_count > MAX_BACKFILL_SYMBOLS:
    messagebox.showwarning("選擇超限", "最多只能選擇15個！")
```

### 全選保護

當可見貨幣對 > 15 時：
```
💡 提示
當前可見 50 個貨幣對，
但最多只能選擇 15 個。

將選擇前 15 個。
```

### 反選保護

當反選後 > 15 時：
```
⚠️ 警告
反選後將有 20 個貨幣對被選中，
超過限制 15 個！

請先清除一些選擇後再反選。
```

---

## 💡 使用建議

### 場景1: 回補主流幣

```
1. 點擊「開始回補」
2. 搜索框輸入 "BTC"
3. 勾選 BTCUSDT
4. 清除搜索，輸入 "ETH"
5. 勾選 ETHUSDT
6. 繼續添加其他主流幣
7. 確定
```

### 場景2: 回補全部穩定幣

```
1. 點擊「開始回補」
2. 滾動到 "💵 穩定幣" 分類
3. 逐個勾選想要的穩定幣
4. 或使用搜索：輸入 "USD"
5. 確定
```

### 場景3: 回補特定交易對

```
1. 準備一個交易對列表
2. 點擊「開始回補」
3. 逐個搜索並勾選
4. 確認數量 ≤ 15
5. 確定
```

---

## 🐛 常見問題

### Q1: 選擇器沒有彈出？

**檢查**:
1. 是否填寫了資產分類（category）
2. 是否選擇了正確的時間範圍
3. 控制台是否有錯誤訊息

### Q2: 找不到某個貨幣對？

**可能原因**:
1. 該貨幣對不在 CRYPTO_SYMBOLS 列表中
2. 搜索時拼寫錯誤
3. 該貨幣對屬於 stock 分類

**解決**:
- 檢查 `config/trading_config.py` 中的 CRYPTO_SYMBOLS
- 如需添加，請更新配置文件

### Q3: 為什麼限制15個？

**原因**:
1. 回補是資源密集操作
2. 避免資料庫過載
3. 確保回補可控可監控
4. 降低出錯風險

**替代方案**:
- 分批回補：先回補15個，完成後再回補另外15個

### Q4: 可以記住上次的選擇嗎？

**當前**: 不會記住

**未來改進**:
```python
# 保存上次選擇到配置文件
last_selection = ['BTCUSDT', 'ETHUSDT', ...]

# 傳入作為預設選擇
target_symbols = select_symbols_for_backfill(
    parent=gui.root,
    category=cat,
    current_selection=last_selection  # 預設選擇
)
```

---

## 🎨 自定義

### 修改最大數量

```python
# config/trading_config.py
MAX_BACKFILL_SYMBOLS = 20  # 改為20
```

### 添加新貨幣對

```python
# config/trading_config.py
CRYPTO_SYMBOLS = [
    # ... 現有的 ...
    "NEWCOINUSDT",  # 添加新幣
]
```

### 修改分類顯示

```python
# core/gui_symbol_selector.py
def get_symbol_category(self, symbol):
    if symbol in ["NEWCOINUSDT"]:
        return "🆕 新幣"
    # ... 其他分類 ...
```

---

## 📊 統計

### 當前支援

- **加密貨幣**: 150+ 個交易對
- **股票**: 0 個（預留）
- **分類**: 12+ 個類別
- **最大選擇**: 15 個

### 文件大小

- `gui_symbol_selector.py`: ~500 行
- `trading_config.py`: +100 行
- 總計新增: ~600 行代碼

---

## 🚀 未來改進

### 短期（1週）

- [ ] 記住上次選擇
- [ ] 添加預設組合（如"主流幣套餐"）
- [ ] 批量導入（從文件讀取列表）

### 中期（1個月）

- [ ] 多標籤頁（Crypto / Stock）
- [ ] 收藏功能
- [ ] 排序功能（按名稱、市值等）

### 長期（3個月）

- [ ] 市值數據顯示
- [ ] 24小時交易量顯示
- [ ] 價格變化顯示
- [ ] 推薦系統（根據歷史選擇）

---

## ✅ 總結

### 完成功能

1. ✅ 分類顯示（Crypto/Stock）
2. ✅ 多選功能（最多15個）
3. ✅ 搜索過濾
4. ✅ 快速操作（全選/清除/反選）
5. ✅ 視覺分組
6. ✅ 數量限制保護
7. ✅ 150+ 加密貨幣對

### 用戶體驗

- 🎨 清晰的視覺分組
- 🔍 強大的搜索功能
- ⚡ 快速操作按鈕
- 🛡️ 安全限制保護
- 📊 實時數量顯示

### 技術亮點

- 📦 模組化設計
- 🔧 易於擴展
- 🎯 職責分離
- 📝 完整註釋
- ✨ 用戶友好

---

**功能已完成並可立即使用！** 🎊

*文檔日期: 2025-11-16*  
*版本: 1.0*  
*狀態: ✅ 已完成*
