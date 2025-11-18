# 核心策略系統架構設計

**版本**: 1.0  
**日期**: 2025-11-16  
**狀態**: 設計中

---

## 🎯 系統需求

### 1. 核心功能
- ✅ 與 Web 數據串接
- ✅ 支援模擬交易（非真實交易）
- ✅ 訂單結果回傳到策略模組
- ✅ 詳細交易記錄（不可刪除）
- ✅ 統計分析（營利/虧損）

### 2. 多策略並行
- ✅ 支援多個策略同時運行
- ✅ 每個策略有獨立配置和權重
- ✅ 主模組整合所有策略結果
- ✅ 清晰的架構，易於維護

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────┐
│                    主控制器 (Master)                      │
│  - 策略載入和管理                                          │
│  - 權重計算和整合                                          │
│  - 最終決策輸出                                            │
└────────────────┬────────────────────────────────────────┘
                 │
        ┌────────┴─────────┬──────────────┐
        │                  │              │
┌───────▼──────┐  ┌───────▼──────┐  ┌───▼────────┐
│  策略模組 A   │  │  策略模組 B   │  │  策略模組 N │
│  權重: 0.4   │  │  權重: 0.3   │  │  權重: 0.3  │
└───────┬──────┘  └───────┬──────┘  └───┬────────┘
        │                  │              │
        └────────┬─────────┴──────────────┘
                 │
        ┌────────▼─────────────────────┐
        │      訂單執行引擎             │
        │  - 模擬交易                   │
        │  - 真實交易（可選）            │
        │  - 訂單管理                   │
        └────────┬─────────────────────┘
                 │
        ┌────────▼─────────────────────┐
        │      交易記錄系統             │
        │  - 訂單記錄                   │
        │  - 成交記錄                   │
        │  - 盈虧記錄                   │
        │  - 統計分析                   │
        └──────────────────────────────┘
```

---

## 📁 目錄結構

```
modules/
├── strategies/                    # 策略模組目錄
│   ├── __init__.py
│   ├── base_strategy.py          # 策略基類
│   ├── strategy_a.py             # 策略A
│   ├── strategy_b.py             # 策略B
│   └── ...
│
├── trading/                       # 交易執行模組
│   ├── __init__.py
│   ├── order_manager.py          # 訂單管理器
│   ├── simulator.py              # 模擬交易引擎
│   ├── executor.py               # 真實交易執行器
│   └── position_manager.py       # 倉位管理器
│
├── master/                        # 主控制器
│   ├── __init__.py
│   ├── strategy_master.py        # 策略主控
│   ├── weight_calculator.py      # 權重計算
│   └── decision_maker.py         # 決策製定
│
├── recorder/                      # 記錄系統
│   ├── __init__.py
│   ├── trade_recorder.py         # 交易記錄器
│   ├── performance_tracker.py    # 績效追蹤
│   └── statistics.py             # 統計分析
│
└── database/                      # 策略資料庫
    ├── __init__.py
    ├── strategy_db.py            # 策略資料庫
    └── models.py                 # 資料模型
```

---

## 💾 資料庫設計

### 1. 策略配置表
```sql
CREATE TABLE strategy_configs (
    id INTEGER PRIMARY KEY,
    strategy_name VARCHAR(100) UNIQUE,
    strategy_class VARCHAR(100),
    weight REAL,                    -- 權重 (0.0-1.0)
    enabled BOOLEAN DEFAULT 1,
    config_json JSON,               -- 策略參數
    created_at DATETIME,
    updated_at DATETIME
);
```

### 2. 訂單記錄表
```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE,
    strategy_name VARCHAR(100),
    symbol VARCHAR(20),
    side VARCHAR(10),              -- 'BUY' or 'SELL'
    order_type VARCHAR(20),        -- 'MARKET', 'LIMIT', etc.
    quantity REAL,
    price REAL,
    status VARCHAR(20),            -- 'PENDING', 'FILLED', 'CANCELLED'
    is_simulation BOOLEAN,         -- 是否模擬
    created_at DATETIME,
    filled_at DATETIME,
    FOREIGN KEY (strategy_name) REFERENCES strategy_configs(strategy_name)
);
```

### 3. 成交記錄表
```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY,
    trade_id VARCHAR(100) UNIQUE,
    order_id VARCHAR(100),
    strategy_name VARCHAR(100),
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity REAL,
    price REAL,
    commission REAL,
    is_simulation BOOLEAN,
    executed_at DATETIME,
    FOREIGN KEY (order_id) REFERENCES orders(order_id)
);
```

### 4. 盈虧記錄表（核心）
```sql
CREATE TABLE pnl_records (
    id INTEGER PRIMARY KEY,
    record_id VARCHAR(100) UNIQUE,
    strategy_name VARCHAR(100),
    symbol VARCHAR(20),
    entry_order_id VARCHAR(100),   -- 開倉訂單
    exit_order_id VARCHAR(100),    -- 平倉訂單
    entry_price REAL,
    exit_price REAL,
    quantity REAL,
    pnl REAL,                      -- 盈虧金額
    pnl_percentage REAL,           -- 盈虧百分比
    commission REAL,               -- 手續費
    net_pnl REAL,                  -- 淨盈虧
    hold_duration INTEGER,         -- 持倉時間（秒）
    is_simulation BOOLEAN,
    entry_time DATETIME,
    exit_time DATETIME,
    created_at DATETIME NOT NULL,
    -- 重要：不可刪除約束
    CONSTRAINT no_delete CHECK (1=1)
);
```

### 5. 策略績效表
```sql
CREATE TABLE strategy_performance (
    id INTEGER PRIMARY KEY,
    strategy_name VARCHAR(100),
    date DATE,
    total_trades INTEGER,
    winning_trades INTEGER,
    losing_trades INTEGER,
    total_pnl REAL,
    win_rate REAL,
    avg_win REAL,
    avg_loss REAL,
    max_drawdown REAL,
    sharpe_ratio REAL,
    created_at DATETIME,
    UNIQUE(strategy_name, date)
);
```

---

## 🔧 核心類設計

### 1. 策略基類
```python
# modules/strategies/base_strategy.py
from abc import ABC, abstractmethod

class BaseStrategy(ABC):
    def __init__(self, name, weight=1.0, config=None):
        self.name = name
        self.weight = weight
        self.config = config or {}
        self.enabled = True
    
    @abstractmethod
    def analyze(self, data):
        """分析數據，返回交易信號"""
        pass
    
    @abstractmethod
    def generate_signal(self, analysis_result):
        """生成交易信號 {'action': 'BUY/SELL/HOLD', 'confidence': 0.0-1.0}"""
        pass
    
    def on_order_filled(self, order_result):
        """訂單成交回調"""
        pass
    
    def on_trade_closed(self, pnl_result):
        """交易關閉回調（接收盈虧結果）"""
        pass
```

### 2. 主控制器
```python
# modules/master/strategy_master.py
class StrategyMaster:
    def __init__(self):
        self.strategies = {}
        self.weights = {}
    
    def register_strategy(self, strategy, weight):
        """註冊策略"""
        self.strategies[strategy.name] = strategy
        self.weights[strategy.name] = weight
    
    def get_combined_signal(self, data):
        """整合所有策略信號"""
        signals = {}
        for name, strategy in self.strategies.items():
            if strategy.enabled:
                signal = strategy.generate_signal(
                    strategy.analyze(data)
                )
                signals[name] = {
                    'signal': signal,
                    'weight': self.weights[name]
                }
        
        return self.calculate_weighted_decision(signals)
    
    def calculate_weighted_decision(self, signals):
        """計算加權決策"""
        # 實現加權邏輯
        pass
```

### 3. 訂單管理器
```python
# modules/trading/order_manager.py
class OrderManager:
    def __init__(self, is_simulation=True):
        self.is_simulation = is_simulation
        self.simulator = Simulator() if is_simulation else None
        self.executor = Executor() if not is_simulation else None
    
    async def place_order(self, order):
        """下單"""
        if self.is_simulation:
            result = await self.simulator.execute(order)
        else:
            result = await self.executor.execute(order)
        
        # 記錄訂單
        await self.record_order(order, result)
        
        # 回傳結果給策略
        await self.notify_strategy(order.strategy_name, result)
        
        return result
    
    async def notify_strategy(self, strategy_name, result):
        """通知策略訂單結果"""
        strategy = get_strategy(strategy_name)
        if result['status'] == 'FILLED':
            strategy.on_order_filled(result)
```

### 4. 交易記錄器
```python
# modules/recorder/trade_recorder.py
class TradeRecorder:
    def __init__(self, db_path):
        self.db = StrategyDatabase(db_path)
    
    async def record_order(self, order, result):
        """記錄訂單"""
        await self.db.insert_order({
            'order_id': order.order_id,
            'strategy_name': order.strategy_name,
            'symbol': order.symbol,
            'side': order.side,
            'quantity': order.quantity,
            'price': result.get('price'),
            'status': result['status'],
            'is_simulation': order.is_simulation,
            'created_at': datetime.now()
        })
    
    async def record_pnl(self, pnl_data):
        """記錄盈虧（不可刪除）"""
        await self.db.insert_pnl({
            'strategy_name': pnl_data['strategy'],
            'symbol': pnl_data['symbol'],
            'entry_price': pnl_data['entry_price'],
            'exit_price': pnl_data['exit_price'],
            'quantity': pnl_data['quantity'],
            'pnl': pnl_data['pnl'],
            'net_pnl': pnl_data['net_pnl'],
            'is_simulation': pnl_data['is_simulation'],
            'created_at': datetime.now()
        })
        
        # 通知策略
        strategy = get_strategy(pnl_data['strategy'])
        strategy.on_trade_closed(pnl_data)
```

---

## 🔄 完整流程

### 1. 系統啟動
```python
# 1. 初始化主控制器
master = StrategyMaster()

# 2. 載入策略
strategy_a = StrategyA(name="ADX_Strategy", weight=0.4)
strategy_b = StrategyB(name="MA_Cross", weight=0.3)
strategy_c = StrategyC(name="Vegas", weight=0.3)

# 3. 註冊策略
master.register_strategy(strategy_a, weight=0.4)
master.register_strategy(strategy_b, weight=0.3)
master.register_strategy(strategy_c, weight=0.3)

# 4. 啟動訂單管理器
order_manager = OrderManager(is_simulation=True)

# 5. 啟動記錄器
recorder = TradeRecorder(db_path="database/strategy.db")
```

### 2. 交易執行流程
```python
# 1. 獲取市場數據（from Web Charting DB）
data = await get_market_data(symbol="BTCUSDT", interval=60)

# 2. 主控制器分析
decision = master.get_combined_signal(data)

# 3. 如果有交易信號
if decision['action'] != 'HOLD':
    order = Order(
        strategy_name="Combined",
        symbol="BTCUSDT",
        side=decision['action'],
        quantity=decision['quantity'],
        is_simulation=True
    )
    
    # 4. 執行訂單
    result = await order_manager.place_order(order)
    
    # 5. 記錄訂單
    await recorder.record_order(order, result)
    
    # 6. 如果成交，記錄成交
    if result['status'] == 'FILLED':
        await recorder.record_trade(result)

# 7. 如果平倉，計算盈虧
if is_position_closed:
    pnl = calculate_pnl(entry, exit)
    
    # 8. 記錄盈虧（永久保存）
    await recorder.record_pnl(pnl)
    
    # 9. 通知策略
    strategy.on_trade_closed(pnl)
```

---

## 📊 統計分析功能

```python
# modules/recorder/statistics.py
class StrategyStatistics:
    def get_strategy_performance(self, strategy_name, period='daily'):
        """獲取策略績效"""
        return {
            'total_trades': 100,
            'winning_trades': 60,
            'losing_trades': 40,
            'win_rate': 0.6,
            'total_pnl': 1500.0,
            'avg_win': 50.0,
            'avg_loss': -30.0,
            'max_drawdown': -200.0,
            'sharpe_ratio': 1.5
        }
    
    def get_all_pnl_records(self, strategy_name=None):
        """獲取所有盈虧記錄（不可刪除）"""
        # 從資料庫讀取所有記錄
        pass
```

---

## ✅ 檢查清單

### 必須實現
- [ ] 策略基類
- [ ] 主控制器
- [ ] 訂單管理器
- [ ] 模擬交易引擎
- [ ] 交易記錄器
- [ ] 盈虧計算器
- [ ] 統計分析模組
- [ ] 資料庫模型

### 核心特性
- [ ] 多策略並行
- [ ] 權重計算
- [ ] 模擬交易
- [ ] 結果回傳
- [ ] 永久記錄
- [ ] 統計分析

---

*設計日期: 2025-11-16*  
*狀態: 規劃完成，待實施*
