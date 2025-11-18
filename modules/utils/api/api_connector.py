"""
api_connector.py
專門負責所有原始 API (HTTP) 請求的模組
"""

import requests
import time
from modules.utils.logger import get_logger
from .api_manager import api_manager, get_default_api_url

logger = get_logger("api_connector")


def get_binance_klines_http(symbol: str, interval: str, start_time: int, end_time: int, limit: int = 1000, api_name: str = None):
    """
    直接呼叫 Binance v3 klines API (使用 requests)

    :param symbol: 交易對 (e.g., "BTCUSDT")
    :param interval: K 線間隔 (e.g., "1s", "1m")
    :param start_time: 開始時間 (milliseconds)
    :param end_time: 結束時間 (milliseconds)
    :param limit: 最大回傳筆數
    :param api_name: API 名稱，若為 None 則使用預設 API
    :return: 原始 K 線資料 (list of lists) 或 空 list
    """

    # 1. 準備 URL 和參數
    # 使用 API 管理器獲取 API URL
    api_url = api_manager.get_api(api_name).url if api_name else get_default_api_url()
    url = f"{api_url}/api/v3/klines"

    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": limit
    }

    api_display_name = api_name or "預設"
    logger.info(f"[HTTP] 準備呼叫 Klines API: {symbol} @ {interval} (來源: {api_display_name})")

    try:
        # 2. 發送 GET 請求
        response = requests.get(url, params=params, timeout=10)

        # 3. 檢查 HTTP 錯誤 (例如 400, 404, 500)
        response.raise_for_status()

        # 4. 解析 JSON 資料
        data = response.json()

        if not isinstance(data, list):
            logger.warning(f"[HTTP] API 回傳的不是列表: {data}")
            return []

        logger.info(f"[HTTP] 成功取得 {len(data)} 筆原始 K 線資料")
        return data

    except requests.exceptions.HTTPError as http_err:
        logger.error(f"❌ [HTTP] API 請求失敗 (HTTP 錯誤): {http_err} - 參數: {params}")
        logger.error(f"❌ [HTTP] 錯誤內容: {response.text}")
        return []
    except requests.exceptions.RequestException as req_err:
        logger.error(f"❌ [HTTP] API 請求失敗 (網路錯誤): {req_err}")
        return []
    except Exception as e:
        logger.error(f"❌ [HTTP] API 請求失敗 (未知錯誤): {e}")
        return []
