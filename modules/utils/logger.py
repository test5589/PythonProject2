"""logger.py - 優化的全域日誌紀錄模組（支援日誌輪替）"""
import os
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from typing import Optional
import re


class SafeRotatingFileHandler(RotatingFileHandler):
    """在 Windows 上更穩定的 RotatingFileHandler。

    主要解決問題：
    - 當日誌檔案被其他程式（例如編輯器、檔案檢視器）開啟時，
      標準 RotatingFileHandler 在輪替時呼叫 os.rename 會觸發
      PermissionError [WinError 32]，進而讓呼叫 logger 的業務程式碼拋例外。

    處理策略：
    - 捕捉 PermissionError，改為只在 stdout 印出提示訊息，但不讓例外往外丟。
      這樣即使輪替失敗，至少不會影響資料寫入流程（例如 1 秒 K 線 insert_data）。
    """

    # 統計輪替時發生 PermissionError 的次數（僅供診斷）
    permission_error_count = 0
    # 是否已經對本程式執行期間的 PermissionError 發出過一次性提示
    permission_error_reported = False

    def doRollover(self):  # type: ignore[override]
        try:
            super().doRollover()
        except PermissionError as e:
            # 統計次數，並在本程式執行期間只輸出一次總結性提示，避免每筆都干擾使用者。
            try:
                SafeRotatingFileHandler.permission_error_count += 1
                if not SafeRotatingFileHandler.permission_error_reported:
                    SafeRotatingFileHandler.permission_error_reported = True
                    print(
                        f"[LOG-ROTATION] 本程式執行期間，log 輪替已發生至少 "
                        f"{SafeRotatingFileHandler.permission_error_count} 次 PermissionError，"
                        "這只代表日誌檔案被其他程式佔用，僅影響 log 檔整理，不影響交易或資料寫入。"
                    )
            except Exception:
                # 統計本身失敗時完全靜默
                pass


def get_log_rotation_stats() -> tuple[int, bool]:
    """取得日誌輪替 PermissionError 的統計 (次數, 是否曾輸出提示)。"""
    return SafeRotatingFileHandler.permission_error_count, SafeRotatingFileHandler.permission_error_reported

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "logs"))
os.makedirs(LOG_DIR, exist_ok=True)


class SymbolPrefixFormatter(logging.Formatter):
    """自定義格式化器：將貨幣對名稱移到日期前面"""
    
    def format(self, record):
        # 先使用父類格式化
        formatted = super().format(record)
        
        # 檢查訊息是否以"SYMBOL |"開頭（如"ETH | "）
        # 格式: 日期 | name | level | SYMBOL | 訊息
        match = re.match(r'^(.*?\s+\|\s+.*?\s+\|\s+.*?\s+\|\s+)([A-Z]+)\s+\|\s+(.*)$', formatted)
        if match:
            # 重新排列: SYMBOL | 日期 | name | level | 訊息
            prefix, symbol, rest = match.groups()
            return f"{symbol} | {prefix}{rest}"
        
        return formatted


class LoggerManager:
    """統一的日誌管理器"""
    
    _loggers = {}
    
    @classmethod
    def get_logger(
        cls,
        name: str,
        level: int = logging.INFO,
        log_to_file: bool = True,
        log_to_console: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        use_time_rotation: bool = False
    ) -> logging.Logger:
        """
        獲取或創建 logger
        
        Args:
            name: logger 名稱
            level: 日誌級別
            log_to_file: 是否記錄到文件
            log_to_console: 是否輸出到控制台
            max_bytes: 單個日誌文件最大大小（字節）
            backup_count: 保留的日誌文件數量
            use_time_rotation: 是否使用時間輪替（每天一個文件）
            
        Returns:
            logging.Logger: 日誌器實例
        """
        # 如果 logger 已存在，直接返回
        if name in cls._loggers:
            return cls._loggers[name]
        
        # 創建新 logger
        logger = logging.getLogger(name)
        logger.setLevel(level)
        
        # 避免重複添加 handler
        if logger.handlers:
            cls._loggers[name] = logger
            return logger
        
        # 格式器 - 對backfill和data_manager使用自定義格式器
        if name in ['backfill', 'data_manager']:
            formatter = SymbolPrefixFormatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%y/%m/%d %H:%M:%S"
            )
        else:
            formatter = logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(message)s",
                datefmt="%y/%m/%d %H:%M:%S"
            )
        
        # 文件處理器
        if log_to_file:
            log_path = os.path.join(LOG_DIR, f"{name}.log")
            
            if use_time_rotation:
                # 時間輪替：每天一個新文件
                file_handler = TimedRotatingFileHandler(
                    log_path,
                    when="midnight",
                    interval=1,
                    backupCount=backup_count,
                    encoding="utf-8"
                )
            else:
                # 大小輪替：文件大小達到限制時輪替
                # 使用 SafeRotatingFileHandler 在 Windows 上忽略 PermissionError
                file_handler = SafeRotatingFileHandler(
                    log_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding="utf-8"
                )
            
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        
        # 控制台處理器
        if log_to_console:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # 緩存 logger
        cls._loggers[name] = logger
        
        return logger
    
    @classmethod
    def shutdown_all(cls):
        """關閉所有 logger"""
        for logger in cls._loggers.values():
            for handler in logger.handlers:
                handler.close()
        cls._loggers.clear()
        logging.shutdown()


# 向後兼容：保留舊的 get_logger 函數
def get_logger(name: str, filename: Optional[str] = None) -> logging.Logger:
    """
    向後兼容的 get_logger 函數
    
    Args:
        name: logger 名稱
        filename: （已棄用）文件名參數
        
    Returns:
        logging.Logger: 日誌器實例
    """
    return LoggerManager.get_logger(name)
