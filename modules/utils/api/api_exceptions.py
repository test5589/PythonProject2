"""
api_exceptions.py - API 異常定義模組
定義 API 相關的自定義異常類型
"""


class APIException(Exception):
    """API 異常基類"""
    pass


class APIRequestError(APIException):
    """API 請求錯誤"""
    
    def __init__(self, message: str, status_code: int = None, response_data: dict = None):
        self.message = message
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(self.message)


class APIRateLimitError(APIException):
    """API 速率限制錯誤"""
    
    def __init__(self, message: str = "超過 API 速率限制", retry_after: int = None):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class APITimeoutError(APIException):
    """API 請求超時錯誤"""
    
    def __init__(self, message: str, timeout_seconds: int = None):
        self.message = message
        self.timeout_seconds = timeout_seconds
        super().__init__(self.message)


class APIConnectionError(APIException):
    """API 連線錯誤"""
    
    def __init__(self, message: str, original_error: Exception = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class APIParseError(APIException):
    """API 回應解析錯誤"""
    
    def __init__(self, message: str, raw_data: str = None):
        self.message = message
        self.raw_data = raw_data
        super().__init__(self.message)


class APIValidationError(APIException):
    """API 參數驗證錯誤"""
    
    def __init__(self, message: str, param_name: str = None, param_value: any = None):
        self.message = message
        self.param_name = param_name
        self.param_value = param_value
        super().__init__(self.message)
