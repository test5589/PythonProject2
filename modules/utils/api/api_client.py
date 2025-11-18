"""api_client.py - 統一 API 客戶端（重構版）

重構說明：
- 參數驗證已提取至 api_validators.py
- 數據解析已提取至 api_parsers.py
- 異常定義已提取至 api_exceptions.py
- 核心請求邏輯保留在此文件
"""

import requests
import time
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config.trading_config import TradingConfig
from modules.utils.exceptions import APIError, NetworkError, ValidationError
from modules.utils.data.validators import DataValidator
from modules.utils.logger import get_logger

# 導入新的模組
from .api_validators import APIParamValidator
from .api_parsers import APIDataParser

logger = get_logger("api_client")

# ====== K 線抓取統計（供批量抓取流程彙總使用）======
_kline_fetch_success_count = 0
_kline_fetch_success_rows = 0

# API 重試統計（假假警報）：連線錯誤與請求超時
_api_retry_conn_error_count = 0
_api_retry_timeout_count = 0


def reset_kline_fetch_stats() -> None:
    """重置本程式期間的 K 線抓取統計（在批量抓取開始前呼叫）。"""
    global _kline_fetch_success_count, _kline_fetch_success_rows
    _kline_fetch_success_count = 0
    _kline_fetch_success_rows = 0


def get_kline_fetch_stats() -> tuple[int, int]:
    """取得目前累計的 K 線抓取統計 (成功呼叫次數, 累計筆數)。"""
    return _kline_fetch_success_count, _kline_fetch_success_rows


def reset_api_retry_stats() -> None:
    """重置 API 重試統計（在批量抓取開始前呼叫）。"""
    global _api_retry_conn_error_count, _api_retry_timeout_count
    _api_retry_conn_error_count = 0
    _api_retry_timeout_count = 0


def get_api_retry_stats() -> tuple[int, int]:
    """取得目前 API 重試統計 (連線錯誤次數, 請求超時次數)。"""
    return _api_retry_conn_error_count, _api_retry_timeout_count


class BinanceAPIClient:
    """統一的 Binance API 客戶端"""
    
    def __init__(self, base_url: str = "https://api.binance.com", timeout: int = None):
        """
        初始化 API 客戶端
        
        Args:
            base_url: API 基礎 URL
            timeout: 請求超時時間（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout or TradingConfig.API_TIMEOUT
        self.max_retries = TradingConfig.API_MAX_RETRIES
        self.session = requests.Session()
        
        # 設定請求標頭
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Trading Bot)',
            'Accept': 'application/json'
        })
        
        logger.info(f"API 客戶端已初始化：{base_url}")
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        retry_count: int = 0
    ) -> Any:
        """
        發送 API 請求（帶重試機制和輸入驗證）
        
        Args:
            method: HTTP 方法（GET/POST）
            endpoint: API 端點
            params: 請求參數（會被驗證和清理）
            retry_count: 當前重試次數
            
        Returns:
            API 回應資料
            
        Raises:
            APIError: API 錯誤
            NetworkError: 網路錯誤
            ValidationError: 輸入驗證錯誤
        """
        # 驗證和清理輸入參數（委託給 APIParamValidator）
        if params:
            params = APIParamValidator.validate_and_clean_params(params)
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"發送請求：{method} {url}")
            if params:
                logger.debug(f"請求參數：{APIParamValidator.sanitize_params_for_logging(params)}")
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=params, timeout=self.timeout)
            elif method.upper() == 'POST':
                response = self.session.post(url, json=params, timeout=self.timeout)
            else:
                raise ValidationError(f"不支援的 HTTP 方法：{method}")
            
            # 檢查回應狀態
            if response.status_code == 429:
                # 超過速率限制
                if retry_count < self.max_retries:
                    wait_time = 2 ** retry_count  # 指數退避
                    logger.warning(f"超過 API 速率限制，等待 {wait_time} 秒後重試")
                    time.sleep(wait_time)
                    return self._make_request(method, endpoint, params, retry_count + 1)
                else:
                    raise APIError("超過 API 速率限制，已達最大重試次數")
            
            if response.status_code != 200:
                error_msg = f"API 錯誤：HTTP {response.status_code}"
                error_body_preview = None
                api_error_code = None
                api_error_msg = None
                try:
                    error_data = response.json()
                    api_error_code = error_data.get('code')
                    api_error_msg = error_data.get('msg')
                    error_msg += f" - {api_error_msg or '未知錯誤'}"
                    error_body_preview = str(error_data)
                except Exception:
                    text = response.text or ""
                    error_body_preview = text[:200] + ("..." if len(text) > 200 else "")
                    error_msg += f" - {error_body_preview}"

                # 記錄詳細錯誤到 api_client logger，方便排查特定 symbol 的問題
                try:
                    safe_params = APIParamValidator.sanitize_params_for_logging(params or {})
                except Exception:
                    safe_params = params
                logger.error(
                    f"[HTTP] API 請求失敗：{error_msg} | endpoint={endpoint} | params={safe_params} | body={error_body_preview}"
                )

                # 將 HTTP 狀態碼與 Binance code/msg 放入 details，方便上層辨識 Invalid symbol 等情況
                details = {"status_code": response.status_code}
                if api_error_code is not None:
                    details["api_error_code"] = api_error_code
                if api_error_msg:
                    details["api_error_msg"] = api_error_msg
                if params:
                    if 'symbol' in params:
                        details['symbol'] = params['symbol']
                    if 'interval' in params:
                        details['interval'] = params['interval']

                raise APIError(error_msg, details=details)
            
            # 解析 JSON 回應
            try:
                data = response.json()
                logger.debug(f"收到回應：{len(str(data))} bytes")
                return data
            except Exception as e:
                raise APIError(f"無法解析 API 回應：{e}")
        
        except requests.exceptions.Timeout:
            if retry_count < self.max_retries:
                # 假假警報：請求超時，記錄重試次數
                try:
                    global _api_retry_timeout_count
                    _api_retry_timeout_count += 1
                except Exception:
                    pass
                logger.warning(
                    f"⚪ [假假警報] 請求超時，重試 {retry_count + 1}/{self.max_retries}"
                )
                time.sleep(1)
                return self._make_request(method, endpoint, params, retry_count + 1)
            else:
                raise NetworkError(f"請求超時（{self.timeout}秒）")
        
        except requests.exceptions.ConnectionError as e:
            if retry_count < self.max_retries:
                # 假假警報：連線錯誤，記錄重試次數
                try:
                    global _api_retry_conn_error_count
                    _api_retry_conn_error_count += 1
                except Exception:
                    pass
                logger.warning(
                    f"⚪ [假假警報] 連線錯誤，重試 {retry_count + 1}/{self.max_retries}"
                )
                time.sleep(1)
                return self._make_request(method, endpoint, params, retry_count + 1)
            else:
                raise NetworkError(f"網路連線錯誤：{e}")
        
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"請求失敗：{e}")
    
    # ========== 已移至 api_validators.py 的方法（保留註釋供參考）==========
    # _validate_and_clean_params() → APIParamValidator.validate_and_clean_params()
    # _is_valid_param_key() → APIParamValidator.is_valid_param_key()
    # _clean_param_value() → APIParamValidator.clean_param_value()
    # _clean_symbol_param() → APIParamValidator.clean_symbol()
    # _clean_interval_param() → APIParamValidator.clean_interval()
    # _clean_numeric_param() → APIParamValidator.clean_numeric()
    # _clean_timestamp_param() → APIParamValidator.clean_timestamp()
    # _clean_string_param() → APIParamValidator.clean_string()
    # _sanitize_params_for_logging() → APIParamValidator.sanitize_params_for_logging()
    
    # ========== 向後兼容方法（委託給新模組）==========
    def _validate_and_clean_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """驗證和清理參數（向後兼容，委託給 APIParamValidator）"""
        return APIParamValidator.validate_and_clean_params(params)
    
    def _sanitize_params_for_logging(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """為日誌清理參數（向後兼容，委託給 APIParamValidator）"""
        return APIParamValidator.sanitize_params_for_logging(params)
    
    def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        抓取 K 線資料
        
        Args:
            symbol: 交易對（如 BTCUSDT）
            interval: 時間間隔（如 1m, 1h）
            start_time: 開始時間（毫秒時間戳）
            end_time: 結束時間（毫秒時間戳）
            limit: 數量限制（最大 1000）
            
        Returns:
            List[Dict]: K 線資料列表
            
        Raises:
            ValidationError: 參數驗證錯誤
            APIError: API 錯誤
            NetworkError: 網路錯誤
        """
        # 驗證參數
        symbol = DataValidator.validate_symbol(symbol)
        interval = DataValidator.validate_interval(interval)
        limit = DataValidator.validate_limit(limit, max_limit=1000)
        
        # 構建參數
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        if start_time is not None:
            params['startTime'] = int(start_time)
        
        if end_time is not None:
            params['endTime'] = int(end_time)
        
        logger.info(f"抓取 K 線：{symbol} @ {interval}，數量：{limit}")
        
        # 發送請求
        raw_data = self._make_request('GET', '/api/v3/klines', params)
        
        # 轉換為標準格式（委託給 APIDataParser）
        klines = APIDataParser.parse_klines(raw_data)

        # 累積統計：成功呼叫次數與累計筆數
        try:
            global _kline_fetch_success_count, _kline_fetch_success_rows
            _kline_fetch_success_count += 1
            _kline_fetch_success_rows += len(klines)
        except Exception:
            # 統計失敗不影響主流程
            pass

        # 單筆成功訊息：帶成功警報標籤，照常顯示在 api_client logger（終端機 + GUI）
        logger.info(f"🟢 [成功警報] 成功抓取 {len(klines)} 筆 K 線資料")

        return klines
    
    # ========== 已移至 api_parsers.py 的方法（保留向後兼容）==========
    def _parse_klines(self, raw_data: List[List]) -> List[Dict[str, Any]]:
        """解析 K 線資料（向後兼容，委託給 APIDataParser）"""
        return APIDataParser.parse_klines(raw_data)
    
    def fetch_latest_price(self, symbol: str) -> float:
        """
        抓取最新價格
        
        Args:
            symbol: 交易對
            
        Returns:
            float: 最新價格
        """
        symbol = DataValidator.validate_symbol(symbol)
        
        data = self._make_request('GET', '/api/v3/ticker/price', {'symbol': symbol})
        
        try:
            price = APIDataParser.parse_price(data)
            logger.info(f"{symbol} 最新價格：{price}")
            return price
        except ValueError as e:
            raise APIError(str(e))
    
    def fetch_24h_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        抓取 24 小時統計資料
        
        Args:
            symbol: 交易對
            
        Returns:
            Dict: 24小時統計資料
        """
        symbol = DataValidator.validate_symbol(symbol)
        
        data = self._make_request('GET', '/api/v3/ticker/24hr', {'symbol': symbol})
        
        logger.info(f"{symbol} 24小時統計：成交量 {data.get('volume', 'N/A')}")
        
        return data
    
    def test_connectivity(self) -> bool:
        """
        測試 API 連線
        
        Returns:
            bool: 是否連線成功
        """
        try:
            self._make_request('GET', '/api/v3/ping')
            logger.info("API 連線測試成功")
            return True
        except Exception as e:
            logger.error(f"API 連線測試失敗：{e}")
            return False
    
    def get_server_time(self) -> datetime:
        """
        取得伺服器時間
        
        Returns:
            datetime: 伺服器時間
        """
        data = self._make_request('GET', '/api/v3/time')
        
        try:
            timestamp = APIDataParser.parse_server_time(data)
            server_time = datetime.fromtimestamp(timestamp)
            logger.info(f"伺服器時間：{server_time}")
            return server_time
        except ValueError as e:
            raise APIError(str(e))
    
    def close(self):
        """關閉會話"""
        self.session.close()
        logger.info("API 客戶端已關閉")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# ========== 全域客戶端實例（單例模式）==========
_global_client: Optional[BinanceAPIClient] = None


def get_api_client(base_url: str = None) -> BinanceAPIClient:
    """
    取得全域 API 客戶端實例
    
    Args:
        base_url: API 基礎 URL
        
    Returns:
        BinanceAPIClient: API 客戶端
    """
    global _global_client
    
    if base_url is None:
        base_url = "https://api.binance.com"
    
    if _global_client is None:
        _global_client = BinanceAPIClient(base_url)
    
    return _global_client


def close_api_client():
    """關閉全域 API 客戶端"""
    global _global_client
    
    if _global_client is not None:
        _global_client.close()
        _global_client = None
