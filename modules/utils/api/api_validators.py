"""
api_validators.py - API 參數驗證模組
從 api_client.py 提取的參數驗證邏輯
"""

import re
from typing import Any, Dict
from modules.utils.exceptions import ValidationError


class APIParamValidator:
    """
    API 參數驗證器
    
    負責驗證和清理 API 請求參數，確保輸入安全性。
    """
    
    # Binance 支援的時間間隔
    VALID_INTERVALS = [
        '1s', '1m', '3m', '5m', '15m', '30m',
        '1h', '2h', '4h', '6h', '8h', '12h',
        '1d', '3d', '1w', '1M'
    ]
    
    # 參數範圍限制
    PARAM_LIMITS = {
        'limit': (1, 1000),
        'start': (0, 2**31-1),
        'end': (0, 2**31-1),
        'fromId': (0, 2**31-1),
        'recvWindow': (5000, 60000)
    }
    
    # 危險的參數名稱
    DANGEROUS_PARAMS = ['eval', 'exec', 'system', 'import', 'open', 'file', 'path', 'cmd']
    
    # 危險的字符
    DANGEROUS_CHARS = ['<', '>', '"', "'", ';', '--', '/*', '*/']
    
    # 敏感的鍵名（用於日誌記錄）
    SENSITIVE_KEYS = ['secret', 'key', 'token', 'password', 'api_key']
    
    @classmethod
    def validate_and_clean_params(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        驗證和清理請求參數
        
        Args:
            params: 原始參數字典
            
        Returns:
            Dict[str, Any]: 清理後的參數字典
            
        Raises:
            ValidationError: 參數驗證失敗
        """
        if not isinstance(params, dict):
            raise ValidationError("參數必須是字典類型")
        
        cleaned = {}
        
        for key, value in params.items():
            # 驗證鍵名
            if not cls.is_valid_param_key(key):
                raise ValidationError(f"無效的參數名稱：{key}")
            
            # 清理和驗證值
            try:
                cleaned_value = cls.clean_param_value(key, value)
                cleaned[key] = cleaned_value
            except Exception as e:
                raise ValidationError(f"參數 '{key}' 驗證失敗：{e}")
        
        return cleaned
    
    @classmethod
    def is_valid_param_key(cls, key: str) -> bool:
        """
        驗證參數鍵名
        
        Args:
            key: 參數鍵名
            
        Returns:
            bool: 鍵名有效返回True
        """
        if not isinstance(key, str):
            return False
        
        # 檢查長度
        if len(key) == 0 or len(key) > 100:
            return False
        
        # 檢查字符（只允許字母、數字和下劃線）
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            return False
        
        # 檢查是否是已知的危險參數
        if key.lower() in cls.DANGEROUS_PARAMS:
            return False
        
        return True
    
    @classmethod
    def clean_param_value(cls, key: str, value: Any) -> Any:
        """
        清理參數值
        
        Args:
            key: 參數鍵名
            value: 參數值
            
        Returns:
            清理後的值
            
        Raises:
            ValidationError: 值無效
        """
        # 處理不同類型的參數
        if key in ['symbol', 'pair', 'baseAsset', 'quoteAsset']:
            return cls.clean_symbol(value)
        
        elif key in ['interval', 'timeframe']:
            return cls.clean_interval(value)
        
        elif key in ['limit', 'start', 'end', 'fromId', 'recvWindow']:
            return cls.clean_numeric(value, key)
        
        elif key in ['timestamp', 'startTime', 'endTime']:
            return cls.clean_timestamp(value)
        
        else:
            return cls.clean_string(value)
    
    @classmethod
    def clean_symbol(cls, value: Any) -> str:
        """
        清理貨幣對參數
        
        Args:
            value: 貨幣對值
            
        Returns:
            str: 清理後的貨幣對
            
        Raises:
            ValidationError: 格式錯誤
        """
        if not isinstance(value, (str, int)):
            raise ValidationError(f"貨幣對必須是字符串或數字，得到：{type(value)}")
        
        symbol = str(value).upper().strip()
        
        # 檢查格式（應該是兩個貨幣代碼相連，如 BTCUSDT）
        if not re.match(r'^[A-Z]{3,10}(USDT|BTC|ETH|BUSD)$', symbol):
            # 放寬檢查，允許更多格式
            if not re.match(r'^[A-Z]{2,20}$', symbol):
                raise ValidationError(f"無效的貨幣對格式：{symbol}")
        
        return symbol
    
    @classmethod
    def clean_interval(cls, value: Any) -> str:
        """
        清理時間間隔參數
        
        Args:
            value: 時間間隔值
            
        Returns:
            str: 清理後的時間間隔
            
        Raises:
            ValidationError: 不支援的間隔
        """
        if not isinstance(value, str):
            raise ValidationError(f"時間間隔必須是字符串，得到：{type(value)}")
        
        interval = value.strip().lower()
        
        if interval not in cls.VALID_INTERVALS:
            raise ValidationError(
                f"不支援的時間間隔：{interval}。"
                f"支援的間隔：{', '.join(cls.VALID_INTERVALS)}"
            )
        
        return interval
    
    @classmethod
    def clean_numeric(cls, value: Any, key: str) -> int:
        """
        清理數值參數
        
        Args:
            value: 數值
            key: 參數名稱
            
        Returns:
            int: 清理後的數值
            
        Raises:
            ValidationError: 數值無效或超出範圍
        """
        try:
            num = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"參數 '{key}' 必須是數字，得到：{value}")
        
        # 參數特定的範圍檢查
        if key in cls.PARAM_LIMITS:
            min_val, max_val = cls.PARAM_LIMITS[key]
            if not (min_val <= num <= max_val):
                raise ValidationError(
                    f"參數 '{key}' 超出範圍 {min_val}-{max_val}，得到：{num}"
                )
        
        return num
    
    @classmethod
    def clean_timestamp(cls, value: Any) -> int:
        """
        清理時間戳參數
        
        Args:
            value: 時間戳值
            
        Returns:
            int: 清理後的時間戳
            
        Raises:
            ValidationError: 時間戳無效
        """
        try:
            timestamp = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"時間戳必須是數字，得到：{value}")
        
        # 檢查時間戳範圍（支持毫秒級時間戳，1970-2100年）
        # Binance API 使用毫秒級時間戳（13位數字）
        min_timestamp = 0  # 1970-01-01
        max_timestamp = 4102444800000  # 2100-01-01 (毫秒級)
        
        if not (min_timestamp <= timestamp <= max_timestamp):
            raise ValidationError(f"時間戳超出範圍，得到：{timestamp}")
        
        return timestamp
    
    @classmethod
    def clean_string(cls, value: Any) -> str:
        """
        清理通用字符串參數
        
        Args:
            value: 字符串值
            
        Returns:
            str: 清理後的字符串
            
        Raises:
            ValidationError: 字符串無效
        """
        if value is None:
            return ""
        
        if not isinstance(value, (str, int, float)):
            raise ValidationError(f"參數必須是字符串或數字，得到：{type(value)}")
        
        result = str(value).strip()
        
        # 檢查長度
        if len(result) > 1000:
            raise ValidationError(f"參數過長（最大1000字符），得到：{len(result)}")
        
        # 檢查是否包含危險字符
        for char in cls.DANGEROUS_CHARS:
            if char in result:
                raise ValidationError(f"參數包含危險字符：{char}")
        
        return result
    
    @classmethod
    def sanitize_params_for_logging(cls, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        為日誌記錄清理參數（隱藏敏感信息）
        
        Args:
            params: 原始參數字典
            
        Returns:
            Dict[str, Any]: 清理後的參數字典
        """
        sanitized = {}
        
        for key, value in params.items():
            if any(sensitive in key.lower() for sensitive in cls.SENSITIVE_KEYS):
                sanitized[key] = "***HIDDEN***"
            else:
                sanitized[key] = value
        
        return sanitized


# 便捷函數（向後兼容）
def validate_and_clean_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """驗證和清理參數（便捷函數）"""
    return APIParamValidator.validate_and_clean_params(params)


def sanitize_params_for_logging(params: Dict[str, Any]) -> Dict[str, Any]:
    """為日誌清理參數（便捷函數）"""
    return APIParamValidator.sanitize_params_for_logging(params)
