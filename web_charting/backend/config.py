"""
config.py - Web Charting Application Configuration
"""
import os
from pathlib import Path

# 項目根目錄
BASE_DIR = Path(__file__).parent.parent
MAIN_PROJECT_DIR = BASE_DIR.parent

# 資料庫配置
class DatabaseConfig:
    """資料庫配置"""
    
    # Web Charts 獨立資料庫
    CHART_DB_PATH = BASE_DIR / "database" / "charting.db"
    CHART_DB_URL = f"sqlite:///{CHART_DB_PATH}"
    
    # 主資料庫（用於同步）
    MAIN_DB_PATH = MAIN_PROJECT_DIR / "data" / "system_data.db"
    MAIN_DB_URL = f"sqlite:///{MAIN_DB_PATH}"
    
    # 連接池配置
    POOL_SIZE = 10
    MAX_OVERFLOW = 20
    POOL_PRE_PING = True
    
    # SQLite 優化
    SQLITE_PRAGMAS = {
        'journal_mode': 'WAL',          # Write-Ahead Logging
        'cache_size': -64000,           # 64MB cache
        'synchronous': 'NORMAL',        # 平衡性能和安全
        'temp_store': 'MEMORY',         # 臨時數據在內存
        'mmap_size': 30000000000,       # 30GB mmap
        'page_size': 4096,              # 4KB頁面
        'foreign_keys': 1,              # 啟用外鍵
    }


class ChartConfig:
    """圖表配置"""
    
    # 支持的時間框架（秒）
    TIMEFRAMES = [1, 2, 5, 10, 15, 30, 60, 300, 600, 1800, 3600, 14400, 28800]
    
    # 時間框架顯示名稱
    TIMEFRAME_LABELS = {
        1: "1s",
        2: "2s",
        5: "5s",
        10: "10s",
        15: "15s",
        30: "30s",
        60: "1m",
        300: "5m",
        600: "10m",
        1800: "30m",
        3600: "1h",
        14400: "4h",
        28800: "8h",
    }
    
    # 資料來源優先級
    DATA_PRIORITY = {
        'real': 1,
        'Aggregation': 2,
        'interpolated': 3,
        'inferior-Aggregation': 4,
        'test': 5,
    }
    
    # 圖表顏色配置
    COLORS = {
        'real': {
            'up': '#00C853',      # 深綠色
            'down': '#D50000',    # 深紅色
        },
        'Aggregation': {
            'up': '#69F0AE',      # 淺綠色
            'down': '#FF5252',    # 淺紅色
        },
        'low_priority': {
            'up': '#9E9E9E',      # 灰色
            'down': '#757575',    # 深灰色
        },
    }
    
    # 默認加載K線數量
    DEFAULT_CANDLES_LIMIT = 3000
    MAX_CANDLES_LIMIT = 10000


class IndicatorConfig:
    """技術指標配置"""
    
    # ADX 配置
    ADX_PERIOD = 14
    ADX_THRESHOLD = 20
    
    # Vegas 雙通道配置
    VEGAS_FILTER = 12
    VEGAS_GROUP_A = [144, 169]
    VEGAS_GROUP_B = [576, 676]
    
    # MA Cross 配置
    MA_SHORT = 50
    MA_LONG = 200


class SyncConfig:
    """同步配置"""
    
    # 批量同步大小
    BATCH_SIZE = 1000
    
    # 最大同步天數（一次）
    MAX_SYNC_DAYS = 30
    
    # 增量同步間隔（秒）
    INCREMENTAL_SYNC_INTERVAL = 60
    
    # 並發同步數
    MAX_CONCURRENT_SYNCS = 3


class APIConfig:
    """API 配置"""
    
    # 服務器配置
    HOST = "0.0.0.0"
    PORT = 8001
    
    # CORS 配置
    CORS_ORIGINS = [
        "http://localhost:3000",     # React dev server
        "http://localhost:5173",     # Vite dev server
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    # API 限流
    RATE_LIMIT = "100/minute"
    
    # 超時配置
    REQUEST_TIMEOUT = 30


class CacheConfig:
    """緩存配置（可選）"""
    
    # 啟用緩存
    ENABLED = False
    
    # Redis 配置（未來擴展）
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379
    REDIS_DB = 0
    
    # 緩存 TTL（秒）
    LATEST_CANDLES_TTL = 60
    INDICATOR_TTL = 300


# 環境配置
class Config:
    """總配置"""
    
    # 環境
    ENV = os.getenv("ENV", "development")
    DEBUG = ENV == "development"
    
    # 子配置
    database = DatabaseConfig
    chart = ChartConfig
    indicator = IndicatorConfig
    sync = SyncConfig
    api = APIConfig
    cache = CacheConfig
    
    # 日誌配置
    LOG_LEVEL = "INFO" if not DEBUG else "DEBUG"
    LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
    LOG_FILE = BASE_DIR / "logs" / "app.log"


# 導出配置實例
config = Config()
