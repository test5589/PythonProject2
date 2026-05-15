"""
exceptions.py - 自訂例外類別（安全性增強版本）
"""

import logging
from typing import Dict, Any, Optional

# 設置異常日誌記錄器
logger = logging.getLogger(__name__)


class TradingBotException(Exception):
    """交易機器人基礎例外類別（安全性增強）"""

    def __init__(self, message: str, details: dict = None, log_level: str = "error"):
        """
        初始化例外

        Args:
            message: 安全的消息（不會洩漏敏感信息）
            details: 詳細信息（僅用於內部日誌）
            log_level: 日誌級別
        """
        self.safe_message = message
        self.details = details or {}
        self.log_level = log_level

        # 記錄詳細信息到日誌（不返回給用戶）
        if self.details:
            detail_str = self._format_details_for_logging()
            logger.log(getattr(logging, log_level.upper(), logging.ERROR),
                      f"例外詳情: {detail_str}")

        # 只使用安全消息初始化父類
        super().__init__(self.safe_message)

    def __str__(self):
        """返回安全的錯誤消息"""
        return self.safe_message

    def _format_details_for_logging(self) -> str:
        """格式化詳細信息用於日誌記錄"""
        # 清理敏感信息
        safe_details = self._sanitize_details(self.details)
        return ", ".join([f"{k}={v}" for k, v in safe_details.items()])

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """清理詳細信息中的敏感數據"""
        sanitized = {}
        sensitive_keys = ['password', 'secret', 'key', 'token', 'api_key', 'private_key']

        for key, value in details.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                sanitized[key] = "***HIDDEN***"
            else:
                # 限制值的長度
                str_value = str(value)
                if len(str_value) > 200:
                    str_value = str_value[:200] + "..."
                sanitized[key] = str_value

        return sanitized

    def get_safe_details(self) -> Dict[str, Any]:
        """獲取安全的詳細信息（用於用戶界面）"""
        return {
            'error_type': self.__class__.__name__,
            'safe_message': self.safe_message,
            'timestamp': self.details.get('timestamp', 'unknown')
        }


class APIError(TradingBotException):
    """API 相關錯誤"""

    def __init__(self, message: str, details: dict = None):
        # 為API錯誤提供標準化的安全消息
        safe_message = self._get_safe_api_message(message, details)
        super().__init__(safe_message, details, "warning")


    def _get_safe_api_message(self, original_message: str, details: Optional[Dict] = None) -> str:
        """生成安全的API錯誤消息"""
        # 檢查是否包含敏感信息
        sensitive_patterns = [
            r'api[_-]?key', r'secret', r'token', r'password',
            r'auth', r'credential', r'private'
        ]

        import re
        if any(re.search(pattern, original_message, re.IGNORECASE) for pattern in sensitive_patterns):
            return "API 認證失敗"

        # 先依 Binance 特定錯誤碼提供更精確訊息
        if details and details.get('api_error_code') == -1121:
            # Binance code -1121: Invalid symbol
            return "API 不支援該交易對 (Invalid symbol)"

        # 檢查HTTP狀態碼並提供通用消息
        if details and 'status_code' in details:
            status_code = details['status_code']
            if status_code == 401:
                return "API 認證失敗"
            elif status_code == 403:
                return "API 權限不足"
            elif status_code == 429:
                return "API 請求過於頻繁，請稍後重試"
            elif status_code >= 500:
                return "API 服務器錯誤"

        # 對於其他錯誤，提供通用消息
        return "API 請求失敗"


class NetworkError(TradingBotException):
    """網路連線錯誤"""

    def __init__(self, message: str, details: dict = None):
        safe_message = self._get_safe_network_message(message, details)
        super().__init__(safe_message, details, "warning")

    def _get_safe_network_message(self, original_message: str, details: Optional[Dict] = None) -> str:
        """生成安全的網路錯誤消息"""
        # 避免洩漏內部網路信息
        return "網路連線失敗，請檢查網路連接"


class DataIntegrityError(TradingBotException):
    """資料完整性錯誤"""

    def __init__(self, message: str, details: dict = None):
        safe_message = self._get_safe_data_message(message, details)
        super().__init__(safe_message, details, "error")

    def _get_safe_data_message(self, original_message: str, details: Optional[Dict] = None) -> str:
        """生成安全的資料錯誤消息"""
        # 避免洩漏資料庫結構信息
        return "資料處理錯誤"


class DatabaseError(TradingBotException):
    """資料庫操作錯誤"""

    def __init__(self, message: str, details: dict = None):
        safe_message = self._get_safe_db_message(message, details)
        super().__init__(safe_message, details, "error")

    def _get_safe_db_message(self, original_message: str, details: Optional[Dict] = None) -> str:
        """生成安全的資料庫錯誤消息"""
        # 避免洩漏資料庫結構和查詢信息
        return "資料庫操作失敗"


class ValidationError(TradingBotException):
    """資料驗證錯誤"""

    def __init__(self, message: str, details: dict = None):
        safe_message = self._get_safe_validation_message(message, details)
        super().__init__(safe_message, details, "info")

    def _get_safe_validation_message(self, original_message: str, details: Optional[Dict] = None) -> str:
        """生成安全的驗證錯誤消息"""
        # 驗證錯誤通常可以顯示給用戶，但要清理敏感信息
        return f"輸入驗證失敗: {original_message}"


class ConfigurationError(TradingBotException):
    """設定錯誤"""

    def __init__(self, message: str, details: dict = None):
        safe_message = self._get_safe_config_message(message, details)
        super().__init__(safe_message, details, "error")

    def _get_safe_config_message(self, original_message: str, details: Optional[Dict] = None) -> str:
        """生成安全的設定錯誤消息"""
        return "系統設定錯誤"


class BackfillError(TradingBotException):
    """回補資料錯誤"""

    def __init__(self, message: str, details: dict = None):
        safe_message = self._get_safe_backfill_message(message, details)
        super().__init__(safe_message, details, "warning")

    def _get_safe_backfill_message(self, original_message: str, details: Optional[Dict] = None) -> str:
        """生成安全的回補錯誤消息"""
        return "資料回補失敗"


def safe_exception_handler(func):
    """
    裝飾器：安全地處理異常，避免洩漏敏感信息

    使用方法：
    @safe_exception_handler
    def my_function():
        # 函數實現
        pass
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except TradingBotException:
            # 重新拋出自訂異常（已經是安全的）
            raise
        except Exception as e:
            # 將未知異常轉換為安全異常
            logger.error(f"未預期的異常: {type(e).__name__}: {str(e)}")
            raise TradingBotException(
                "操作失敗，請聯繫系統管理員",
                {
                    'original_error': type(e).__name__,
                    'function': func.__name__,
                    'timestamp': str(details.get('timestamp', 'unknown'))
                }
            )
    return wrapper


class MonitoringError(TradingBotException):
    """監控錯誤"""
    pass


class DataValidationError(Exception):
    """資料驗證錯誤異常"""

    def __init__(self, message: str, expected: int, actual: int, symbol: str, interval: str):
        self.message = message
        self.expected = expected
        self.actual = actual
        self.symbol = symbol
        self.interval = interval
        super().__init__(
            f"{message} (預期:{expected}, 實際:{actual}, 貨幣對:{symbol}, 間隔:{interval})"
        )


class BackfillInsertError(Exception):
    """在回補過程中偵測到不可忽略的插入錯誤"""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class BackfillConfigurationError(Exception):
    """回補配置錯誤"""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
