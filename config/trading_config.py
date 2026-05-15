"""trading_config.py - 統一交易配置管理模組"""


from datetime import timedelta
from functools import lru_cache

class TradingConfig:
    """交易設定類別 - 統一管理所有交易相關的設定"""
    
    # ========== 支援的貨幣對（按分類）==========
    
    # Crypto（加密貨幣）- 精選常用交易對
    CRYPTO_SYMBOLS = [
        # === 主流幣（前10大市值）===
        "BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT",
        "ADAUSDT", "DOGEUSDT", "TRXUSDT", "LINKUSDT", "AVAXUSDT",
        
        # === Staking/質押代幣 ===
        "WBETHUSDT",
        
        # === Wrapped 代幣 ===
        "WBTCUSDT",
        
        # === Layer 1 & Layer 2 ===
        "ARBUSDT", "OPUSDT", "STRKUSDT", "SEIUSDT", "SUIUSDT",
        "APTUSDT", "NEARUSDT", "ICPUSDT", "INJUSDT", "ATOMUSDT",
        "DOTUSDT", "XLMUSDT", "VETUSDT", "ALGOUSDT", "FILUSDT",
        "HBARUSDT", "QNTUSDT", "KASUSDT", "XTZUSDT", "STXUSDT",
        "TONUSDT", "XDCUSDT",
        
        # === DeFi 代幣 ===
        "UNIUSDT", "AAVEUSDT", "CRVUSDT", "CAKEUSDT", "GRTUSDT",
        "JUPUSDT",
        
        # === Meme 幣 ===
        "SHIBUSDT", "PEPEUSDT", "BONKUSDT", "WLDUSDT", "FLRUSDT",
        
        # === AI & 新概念 ===
        "TAOUSDT", "FETUSDT", "ENAUSDT", "TIAUSDT",
        
        # === GameFi & NFT ===
        "IMXUSDT",
        
        # === 交易所代幣 ===
        "GTUSDT", "CROUSDT",
        
        # === 隱私幣 ===
        "LTCUSDT",
        
        # === 老牌幣 ===
        "BCHUSDT", "ETCUSDT",
        
        # === 新興/特殊代幣 ===
        "ONDOUSDT", "POLUSDT", "LDOUSDT", "TELUSDT", "DCRUSDT",
        "MNTUSDT", "NEXOUSDT", "RLUSDUSDT",
        
        # === 特殊USDT對 ===
        "CGETH.HASHKEYUSDT",
        
        # === 貴金屬錨定 ===
        "XAUTUSDT", "PAXGUSDT",
    ]
    
    # Stock（股票） - 預留給未來
    STOCK_SYMBOLS = [
        # 預留給股票交易對
        # 例如: "AAPL", "TSLA", "GOOGL" 等
    ]
    
    # 所有支援的貨幣對（兼容性）
    SUPPORTED_SYMBOLS = CRYPTO_SYMBOLS + STOCK_SYMBOLS
    
    # 默認貨幣對
    DEFAULT_SYMBOL = "BTCUSDT"
    
    # 每次回補最多選擇數量
    MAX_BACKFILL_SYMBOLS = 15
    MAX_MONITOR_SYMBOLS = 20
    
    # ========== 支援的間隔 ==========
    # 格式：顯示名稱 -> API 格式
    SUPPORTED_INTERVALS = {
        "1分": "1m",
        "3分": "3m",
        "5分": "5m",
        "15分": "15m",
        "30分": "30m",
        "1小時": "1h",
        "2小時": "2h",
        "4小時": "4h",
        "6小時": "6h",
        "8小時": "8h",
        "12小時": "12h",
        "1天": "1d",
        "3天": "3d",
        "1週": "1w",
        "1月": "1M"
    }
    
    # 默認間隔
    DEFAULT_INTERVAL = "1分"
    
    # ========== 間隔秒數對應 ==========
    # 用於資料庫和計算
    INTERVAL_SECONDS = {
        "1s": 1,
        "5s": 5,
        "15s": 15,
        "30s": 30,
        "1m": 60,
        "3m": 180,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "2h": 7200,
        "4h": 14400,
        "6h": 21600,
        "8h": 28800,
        "12h": 43200,
        "1d": 86400,
        "3d": 259200,
        "1w": 604800,
        "1M": 2592000,  # 30天近似值
    }
    
    # 秒數 -> 間隔名稱（反向查詢）
    SECONDS_TO_INTERVAL = {v: k for k, v in INTERVAL_SECONDS.items()}
    
    # ========== 間隔人類可讀名稱 ==========
    INTERVAL_READABLE = {
        "1s": "1秒",
        "5s": "5秒",
        "15s": "15秒",
        "30s": "30秒",
        "1m": "1分鐘",
        "3m": "3分鐘",
        "5m": "5分鐘",
        "15m": "15分鐘",
        "30m": "30分鐘",
        "1h": "1小時",
        "2h": "2小時",
        "4h": "4小時",
        "6h": "6小時",
        "8h": "8小時",
        "12h": "12小時",
        "1d": "1天",
        "3d": "3天",
        "1w": "1週",
        "1M": "1月",
    }
    
    # ========== API 設定 ==========
    API_RATE_LIMIT = 1000  # 每分鐘請求限制
    API_TIMEOUT = 10       # 請求超時（秒）
    API_MAX_RETRIES = 3    # 最大重試次數
    
    # ========== 資料庫設定 ==========
    DEFAULT_CATEGORY = "crypto"
    
    @classmethod
    @lru_cache(maxsize=100)
    def get_interval_seconds(cls, interval: str) -> int:
        """
        獲取間隔對應的秒數（帶快取）
        
        Args:
            interval: 間隔字串（如 "1m", "1h"）
            
        Returns:
            int: 秒數
            
        Raises:
            ValueError: 無效的間隔
        """
        if interval not in cls.INTERVAL_SECONDS:
            raise ValueError(f"無效的間隔：{interval}")
        return cls.INTERVAL_SECONDS[interval]
    
    @classmethod
    def get_readable_interval(cls, interval: str) -> str:
        """
        獲取間隔的人類可讀名稱
        
        Args:
            interval: 間隔字串（如 "1m", "1h"）
            
        Returns:
            str: 可讀名稱（如 "1分鐘", "1小時"）
        """
        return cls.INTERVAL_READABLE.get(interval, interval)
    
    @classmethod
    def is_valid_symbol(cls, symbol: str) -> bool:
        """
        檢查貨幣對是否有效
        
        Args:
            symbol: 貨幣對字串
            
        Returns:
            bool: 是否有效
        """
        return symbol.upper() in cls.SUPPORTED_SYMBOLS
    
    @classmethod
    def is_valid_interval(cls, interval: str) -> bool:
        """
        檢查間隔是否有效
        
        Args:
            interval: 間隔字串
            
        Returns:
            bool: 是否有效
        """
        return interval in cls.INTERVAL_SECONDS
