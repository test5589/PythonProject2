"""
backfill_config.py - 回補功能配置參數集中管理

將所有硬編碼的回補相關參數集中到此文件，方便維護和調整。
"""

class BackfillConfig:
    """回補功能配置類"""
    
    # ========== 批次處理配置 ==========
    
    # 每批次最大時間範圍（秒）- 避免單次請求過大
    MAX_BATCH_DURATION_SECONDS = 999 * 60  # 999分鐘
    
    # 日誌聚合設定 - 多少筆合併為一行輸出
    LOG_AGGREGATION_CHUNK = 20
    
    # ========== 驗證配置 ==========
    
    # 資料完整性最小容忍比例（80%）
    MIN_DATA_COMPLETENESS_RATIO = 0.80
    
    # API 返回少筆的警告閾值比例
    API_LOW_DATA_WARNING_RATIO = 0.5  # 少於預期50%會警告
    
    # ========== 重試配置 ==========
    
    # API 請求重試次數
    API_RETRY_COUNT = 3
    
    # 重試間隔（秒）
    API_RETRY_DELAY_SECONDS = 2
    
    # ========== 並發配置 ==========
    
    # 多貨幣對並發數（避免API過載）
    MAX_CONCURRENT_SYMBOLS = 1  # 目前序列執行
    
    # ========== 監控配置 ==========
    
    # 多貨幣對監控最大數量
    MAX_MONITOR_SYMBOLS = 20
    
    # ========== 狀態管理配置 ==========
    
    # 資料庫鎖等待超時（秒）
    DB_LOCK_TIMEOUT_SECONDS = 10
    
    # 暫停檢查間隔（秒）
    PAUSE_CHECK_INTERVAL_SECONDS = 0.5
    
    # ========== UI配置 ==========
    
    # 貨幣選擇器最大選擇數量
    MAX_BACKFILL_SYMBOLS = 15
    
    # GUI 日誌緩衝區大小
    GUI_LOG_BUFFER_SIZE = 1000
    
    # ========== 時間配置 ==========
    
    # 台灣時區偏移（小時）
    TAIWAN_TIMEZONE_OFFSET_HOURS = 8
    
    # ========== 輸出配置 ==========
    
    # 日誌時間格式
    LOG_DATETIME_FORMAT = '%Y-%m-%d %H:%M:%S'
    
    # 批次摘要顯示的最大貨幣對數量
    MAX_SYMBOLS_IN_SUMMARY = 5
    
    # ========== 錯誤處理配置 ==========
    
    # 錯誤關鍵字列表（用於監控）
    ERROR_KEYWORDS = [
        "插入失敗",
        "❌ 回補錯誤",
        "資料庫鎖定錯誤",
        "database is locked",
    ]
    
    # ========== 進度報告配置 ==========
    
    # 是否啟用詳細日誌
    VERBOSE_LOGGING = True
    
    # 是否啟用批次摘要
    ENABLE_BATCH_SUMMARY = True
    
    # 是否啟用進度百分比
    ENABLE_PROGRESS_PERCENTAGE = True
    
    @classmethod
    def get_config_summary(cls) -> str:
        """獲取配置摘要"""
        return f"""
回補配置摘要:
- 最大批次時間: {cls.MAX_BATCH_DURATION_SECONDS // 60} 分鐘
- 日誌聚合: 每 {cls.LOG_AGGREGATION_CHUNK} 筆
- 資料完整性: 最小 {cls.MIN_DATA_COMPLETENESS_RATIO * 100}%
- API重試: {cls.API_RETRY_COUNT} 次
- 最大監控數: {cls.MAX_MONITOR_SYMBOLS} 個
- 最大選擇數: {cls.MAX_BACKFILL_SYMBOLS} 個
"""
