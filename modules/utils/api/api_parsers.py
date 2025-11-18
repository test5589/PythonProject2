"""
api_parsers.py - API 數據解析模組
從 api_client.py 提取的數據解析邏輯
"""

from typing import List, Dict, Any
from modules.utils.logger import get_logger

logger = get_logger("api_parsers")


class APIDataParser:
    """
    API 數據解析器
    
    負責將 API 返回的原始數據轉換為標準化格式。
    """
    
    @staticmethod
    def parse_klines(raw_data: List[List]) -> List[Dict[str, Any]]:
        """
        解析原始 K 線資料
        
        Binance API 返回的 K 線格式：
        [
            [
                1499040000000,      // 開盤時間
                "0.01634000",       // 開盤價
                "0.80000000",       // 最高價
                "0.01575800",       // 最低價
                "0.01577100",       // 收盤價
                "148976.11427815",  // 成交量
                1499644799999,      // 收盤時間
                "2434.19055334",    // 成交額
                308,                // 成交筆數
                "1756.87402397",    // 主動買入成交量
                "28.46694368",      // 主動買入成交額
                "17928899.62484339" // 忽略
            ]
        ]
        
        Args:
            raw_data: Binance API 原始資料
            
        Returns:
            List[Dict]: 標準化的 K 線資料
        """
        klines = []
        
        for item in raw_data:
            try:
                kline = {
                    'open_time': int(item[0]),
                    'open': float(item[1]),
                    'high': float(item[2]),
                    'low': float(item[3]),
                    'close': float(item[4]),
                    'volume': float(item[5]),
                    'close_time': int(item[6]),
                    'quote_asset_volume': float(item[7]),
                    'num_trades': int(item[8]),
                    'taker_base_vol': float(item[9]),
                    'taker_quote_vol': float(item[10])
                }
                klines.append(kline)
            except (IndexError, ValueError, TypeError) as e:
                logger.warning(f"解析 K 線資料失敗：{e}，資料：{item}")
                continue
        
        return klines
    
    @staticmethod
    def parse_price(data: Dict[str, Any]) -> float:
        """
        解析價格資料
        
        Args:
            data: API 返回的價格數據
            
        Returns:
            float: 價格
            
        Raises:
            ValueError: 無法解析價格
        """
        try:
            return float(data['price'])
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"無法解析價格資料：{e}")
    
    @staticmethod
    def parse_server_time(data: Dict[str, Any]) -> int:
        """
        解析伺服器時間
        
        Args:
            data: API 返回的時間數據
            
        Returns:
            int: 時間戳（秒）
            
        Raises:
            ValueError: 無法解析時間
        """
        try:
            return int(data['serverTime']) / 1000
        except (KeyError, ValueError, TypeError) as e:
            raise ValueError(f"無法解析伺服器時間：{e}")
    
    @staticmethod
    def parse_24h_ticker(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析 24 小時統計資料
        
        Args:
            data: API 返回的統計數據
            
        Returns:
            Dict: 格式化的統計資料
        """
        return {
            'symbol': data.get('symbol'),
            'price_change': float(data.get('priceChange', 0)),
            'price_change_percent': float(data.get('priceChangePercent', 0)),
            'weighted_avg_price': float(data.get('weightedAvgPrice', 0)),
            'prev_close_price': float(data.get('prevClosePrice', 0)),
            'last_price': float(data.get('lastPrice', 0)),
            'last_qty': float(data.get('lastQty', 0)),
            'bid_price': float(data.get('bidPrice', 0)),
            'ask_price': float(data.get('askPrice', 0)),
            'open_price': float(data.get('openPrice', 0)),
            'high_price': float(data.get('highPrice', 0)),
            'low_price': float(data.get('lowPrice', 0)),
            'volume': float(data.get('volume', 0)),
            'quote_volume': float(data.get('quoteVolume', 0)),
            'open_time': int(data.get('openTime', 0)),
            'close_time': int(data.get('closeTime', 0)),
            'first_id': int(data.get('firstId', 0)),
            'last_id': int(data.get('lastId', 0)),
            'count': int(data.get('count', 0))
        }


# 便捷函數（向後兼容）
def parse_klines(raw_data: List[List]) -> List[Dict[str, Any]]:
    """解析 K 線資料（便捷函數）"""
    return APIDataParser.parse_klines(raw_data)


def parse_price(data: Dict[str, Any]) -> float:
    """解析價格資料（便捷函數）"""
    return APIDataParser.parse_price(data)


def parse_server_time(data: Dict[str, Any]) -> int:
    """解析伺服器時間（便捷函數）"""
    return APIDataParser.parse_server_time(data)


def parse_24h_ticker(data: Dict[str, Any]) -> Dict[str, Any]:
    """解析 24 小時統計（便捷函數）"""
    return APIDataParser.parse_24h_ticker(data)
