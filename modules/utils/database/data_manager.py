"""
data_manager.py - 數據管理器（重構版）
負責數據的插入、批量操作和優先級管理

重構說明：
- 優先級管理已提取至 priority_manager.py
- 統計收集已提取至 stats_collector.py
- 核心插入邏輯保留在此文件
"""

import sqlite3
import threading
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Callable, Tuple, Any
from threading import Lock
from .db_core import DatabaseCore, DEFAULT_API_URL
from .priority_manager import priority_manager
from .stats_collector import stats_collector
from modules.utils.logger import get_logger

logger = get_logger("data_manager")

class DataManager:
    """
    數據管理器 - 負責高效的數據庫操作（重構版）
    
    提供線程安全的數據插入、批量操作功能。
    優先級管理委託給 priority_manager。
    統計收集委託給 stats_collector。
    """
    
    def __init__(self):
        self.db_core = DatabaseCore()
        self._insert_lock = Lock()  # 插入操作鎖
        
        # 向後兼容屬性（委託給新模組）
        self.priority_map = priority_manager.PRIORITY_MAP
        self.interval_map = priority_manager.INTERVAL_MAP

    def insert_single_data(
        self, 
        category: str, 
        symbol: str, 
        interval: int, 
        kline: Dict[str, Any], 
        data_source: str = 'real', 
        interp_note: Optional[str] = None, 
        api: Optional[str] = None, 
        original_interval: Optional[str] = None, 
        overwrite_callback: Optional[Callable] = None,
        return_status: bool = False
    ) -> bool:
        """
        插入單筆數據到資料庫
        
        提供完整的數據插入邏輯，包括：
        - 數據驗證和清理
        - 重複檢查和優先級管理
        - 線程安全操作
        - 詳細的統計記錄
        
        Args:
            category (str): 數據分類，通常為 'crypto'
            symbol (str): 交易對符號，如 'BTCUSDT'
            interval (int): 時間間隔（秒）
            kline (Dict[str, Any]): K線數據字典，包含OHLCV等字段
            data_source (str, optional): 數據來源，默認為 'real'
            interp_note (Optional[str], optional): 插值說明
            api (Optional[str], optional): API來源URL
            original_interval (Optional[str], optional): 原始時間間隔
            overwrite_callback (Optional[Callable], optional): 覆蓋確認回調函數
            
        Returns:
            bool 或 (bool, dict): 預設回傳布林值；若 return_status=True，則回傳 (結果, 狀態資訊)
            
        Raises:
            ValueError: 當必要數據缺失時
            sqlite3.Error: 當數據庫操作失敗時
        """
        with self._insert_lock:
            stats_collector.increment_total()
            
            try:
                # 參數驗證
                if not self._validate_kline_data(kline):
                    logger.error(f"K線數據驗證失敗: {symbol}@{interval}")
                    stats_collector.increment_skipped()
                    return self._build_result(
                        False,
                        'invalid_kline',
                        {'category': category, 'symbol': symbol, 'interval': interval},
                        return_status
                    )
                
                if api is None:
                    api = DEFAULT_API_URL
                
                # 提取時間戳
                timestamp = self._extract_timestamp(kline)
                if timestamp is None:
                    logger.error(f"無法提取時間戳: {kline}")
                    stats_collector.increment_skipped()
                    return self._build_result(
                        False,
                        'missing_timestamp',
                        {'category': category, 'symbol': symbol, 'interval': interval},
                        return_status
                    )
                
                # 檢查是否已存在
                existing_data = self._check_existing_data(category, symbol, interval, timestamp, api)
                
                if existing_data:
                    # 檢查優先級
                    existing_priority = self.priority_map.get(existing_data['data_source'], 999)
                    new_priority = self.priority_map.get(data_source, 999)
                    
                    if new_priority >= existing_priority:
                        logger.debug(f"跳過插入 - 優先級不足: {symbol}@{interval} ({data_source} >= {existing_data['data_source']})")
                        stats_collector.increment_skipped()
                        self._record_duplicate_skip(category, symbol, interval, timestamp, data_source, existing_data.get('data_source'))
                        return self._build_result(
                            False,
                            'duplicate_skipped',
                            {
                                'category': category,
                                'symbol': symbol,
                                'interval': interval,
                                'timestamp': timestamp,
                                'existing_source': existing_data.get('data_source')
                            },
                            return_status
                        )
                    
                    # 需要覆蓋 - 調用回調確認
                    if overwrite_callback:
                        if not overwrite_callback(existing_data, kline, data_source):
                            stats_collector.increment_skipped()
                            return self._build_result(
                                False,
                                'overwrite_declined',
                                {'category': category, 'symbol': symbol, 'interval': interval, 'timestamp': timestamp},
                                return_status
                            )
                    
                    stats_collector.increment_overwrites()
                
                # 執行插入
                success = self._perform_insert(category, symbol, interval, kline, timestamp, data_source, interp_note, api, original_interval)
                
                if success:
                    stats_collector.increment_successful()
                    successful_count = stats_collector.get_successful_count()
                    # 轉換為台灣時間顯示
                    try:
                        tw = timezone(timedelta(hours=8))
                        ts_tw = datetime.fromtimestamp(timestamp, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                        # 每100筆輸出一次確認，避免日誌過多；
                        # 但對 interval==1 的資料，不在這裡重複輸出成功訊息，
                        # 讓 1 秒監控只由 ws_aggregator 的動態統計 LOG 負責顯示。
                        if interval != 1 and successful_count % 100 == 0:
                            logger.info(f"✅ 插入成功: {symbol}@{interval}s 台灣時間={ts_tw} (UTC+8) data_source={data_source}")
                    except Exception:
                        # 保留原始顯示方式作為備份
                        if interval != 1 and successful_count % 100 == 0:
                            logger.info(f"✅ 插入成功: {symbol}@{interval}s timestamp={timestamp} data_source={data_source}")
                    return self._build_result(True, 'success', None, return_status)
                else:
                    logger.error(f"插入失敗: {symbol}@{interval}")
                    return self._build_result(False, 'error', {'category': category, 'symbol': symbol, 'interval': interval, 'timestamp': timestamp}, return_status)
                    
            except Exception as e:
                logger.error(f"數據插入異常: {symbol}@{interval} - {e}")
                return self._build_result(False, 'error', {'category': category, 'symbol': symbol, 'interval': interval, 'timestamp': None, 'error': str(e)}, return_status)
    
    def _validate_kline_data(self, kline: Dict[str, Any]) -> bool:
        """
        驗證K線數據完整性
        
        Args:
            kline: K線數據字典
            
        Returns:
            bool: 數據有效返回True
        """
        REQUIRED_FIELDS = ['open', 'high', 'low', 'close', 'volume']
        TIME_FIELDS = ['open_time', 'timestamp']  # 至少需要一個時間字段
        
        # 檢查必要字段
        for field in REQUIRED_FIELDS:
            if field not in kline or kline[field] is None:
                logger.debug(f"缺少必要字段: {field}")
                return False
        
        # 檢查時間字段
        if not any(field in kline and kline[field] is not None for field in TIME_FIELDS):
            logger.debug(f"缺少時間字段: {TIME_FIELDS}")
            return False
        
        # 數值有效性檢查
        try:
            for field in REQUIRED_FIELDS:
                value = float(kline[field])
                if value < 0:
                    logger.debug(f"負數值: {field}={value}")
                    return False
        except (ValueError, TypeError):
            logger.debug(f"無效數值格式")
            return False
        
        return True
    
    def _extract_timestamp(self, kline: Dict[str, Any]) -> Optional[float]:
        """
        從K線數據中提取時間戳
        
        Args:
            kline: K線數據字典
            
        Returns:
            Optional[float]: 時間戳（秒），失敗返回None
        """
        # 嘗試多種時間字段
        time_fields = ['open_time', 'timestamp', 'time', 'close_time']
        
        for field in time_fields:
            if field in kline and kline[field] is not None:
                try:
                    timestamp = float(kline[field])
                    # 如果是毫秒時間戳，轉換為秒
                    if timestamp > 1e10:  # 大於10位數字，可能是毫秒
                        timestamp = timestamp / 1000
                    return timestamp
                except (ValueError, TypeError):
                    continue
        
        return None
    
    def _check_existing_data(self, category: str, symbol: str, interval: int, timestamp: float, api: str) -> Optional[Dict[str, Any]]:
        """
        檢查數據是否已存在
        
        Args:
            category: 數據分類
            symbol: 交易對符號
            interval: 時間間隔
            timestamp: 時間戳
            api: API來源
            
        Returns:
            Optional[Dict]: 存在則返回現有數據，否則返回None
        """
        try:
            conn = self.db_core.get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT data_source, timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE category=? AND symbol=? AND interval=? AND timestamp=? AND api=?
                LIMIT 1
            """, (category, symbol, interval, timestamp, api))
            
            row = cursor.fetchone()
            
            if row:
                return {
                    'data_source': row[0],
                    'timestamp': row[1],
                    'open': row[2],
                    'high': row[3],
                    'low': row[4],
                    'close': row[5],
                    'volume': row[6]
                }
            
            return None
            
        except Exception as e:
            logger.error(f"檢查現有數據失敗: {e}")
            return None
        finally:
            conn.close()
    
    def _perform_insert(self, category: str, symbol: str, interval: int, kline: Dict[str, Any], 
                       timestamp: float, data_source: str, interp_note: Optional[str], 
                       api: str, original_interval: Optional[str]) -> bool:
        """
        執行實際的數據插入操作
        
        Args:
            category: 數據分類
            symbol: 交易對符號  
            interval: 時間間隔
            kline: K線數據
            timestamp: 時間戳
            data_source: 數據來源
            interp_note: 插值說明
            api: API來源
            original_interval: 原始間隔
            
        Returns:
            bool: 插入成功返回True
        """
        try:
            conn = self.db_core.get_connection()
            cursor = conn.cursor()
            
            # 插入或替換數據（不再寫入 readable_time 欄位，僅依 timestamp 為準）
            cursor.execute("""
                INSERT OR REPLACE INTO historical_data 
                (timestamp, category, symbol, interval, 
                 open, high, low, close, volume,
                 open_time, close_time, quote_asset_volume, num_trades, 
                 taker_base_vol, taker_quote_vol,
                 data_source, interp_note, api)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, category, symbol, interval,
                float(kline.get('open', 0)), float(kline.get('high', 0)), 
                float(kline.get('low', 0)), float(kline.get('close', 0)), float(kline.get('volume', 0)),
                kline.get('open_time'), kline.get('close_time'), 
                kline.get('quote_asset_volume'), kline.get('num_trades'),
                kline.get('taker_base_vol'), kline.get('taker_quote_vol'),
                data_source, interp_note, api
            ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"執行插入失敗: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            conn.close()
    
    def batch_insert_data_optimized(self, category: str, symbol: str, interval: int, 
                                   klines: List[Dict[str, Any]], data_source: str = 'real',
                                   interp_note: Optional[str] = None, api: Optional[str] = None,
                                   original_interval: Optional[str] = None, 
                                   overwrite_callback: Optional[Callable] = None) -> int:
        """
        優化的批次插入實現
        
        Args:
            category: 數據分類
            symbol: 交易對符號
            interval: 時間間隔
            klines: K線數據列表
            data_source: 數據來源
            interp_note: 插值說明
            api: API來源
            original_interval: 原始間隔
            overwrite_callback: 覆蓋確認回調
            
        Returns:
            int: 成功插入的記錄數量
        """
        if not klines:
            return 0
        
        if api is None:
            api = DEFAULT_API_URL
        
        success_count = 0
        
        try:
            conn = self.db_core.get_connection()
            conn.execute("BEGIN TRANSACTION")
            
            for kline in klines:
                if self._insert_single_in_transaction(conn, category, symbol, interval, kline, 
                                                    data_source, interp_note, api, original_interval, overwrite_callback):
                    success_count += 1
            
            conn.commit()
            logger.info(f"批次插入完成: {symbol}@{interval} 成功插入 {success_count}/{len(klines)} 筆")
            
        except Exception as e:
            logger.error(f"批次插入失敗: {e}")
            if conn:
                conn.rollback()
        finally:
            conn.close()
        
        return success_count
    
    def _insert_single_in_transaction(self, conn: sqlite3.Connection, category: str, symbol: str, 
                                     interval: int, kline: Dict[str, Any], data_source: str,
                                     interp_note: Optional[str], api: str, original_interval: Optional[str],
                                     overwrite_callback: Optional[Callable]) -> bool:
        """在事務中插入單筆數據"""
        try:
            # 驗證數據
            if not self._validate_kline_data(kline):
                return False
            
            timestamp = self._extract_timestamp(kline)
            if timestamp is None:
                return False
            
            # 檢查現有數據（在同一連接中）
            cursor = conn.cursor()
            cursor.execute("""
                SELECT data_source FROM historical_data
                WHERE category=? AND symbol=? AND interval=? AND timestamp=? AND api=?
            """, (category, symbol, interval, timestamp, api))
            
            existing = cursor.fetchone()
            
            # 處理已存在的資料
            if existing:
                if not overwrite_callback:
                    # 沒有覆蓋回調，直接跳過（不覆蓋）
                    return False
                else:
                    # 有覆蓋回調，檢查優先級
                    existing_priority = self.priority_map.get(existing[0], 999)
                    new_priority = self.priority_map.get(data_source, 999)
                    if new_priority >= existing_priority:
                        return False
            
            # 準備插入數據（不再寫入 readable_time 欄位）
            cursor.execute("""
                INSERT OR REPLACE INTO historical_data 
                (timestamp, category, symbol, interval, 
                 open, high, low, close, volume,
                 open_time, close_time, quote_asset_volume, num_trades, 
                 taker_base_vol, taker_quote_vol,
                 data_source, interp_note, api)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp, category, symbol, interval,
                float(kline.get('open', 0)), float(kline.get('high', 0)), 
                float(kline.get('low', 0)), float(kline.get('close', 0)), float(kline.get('volume', 0)),
                kline.get('open_time'), kline.get('close_time'), 
                kline.get('quote_asset_volume'), kline.get('num_trades'),
                kline.get('taker_base_vol'), kline.get('taker_quote_vol'),
                data_source, interp_note, api
            ))
            
            return True
            
        except Exception as e:
            # 顯示更詳細的錯誤資訊，包括貨幣對、間隔和錯誤類型
            error_type = type(e).__name__
            error_msg = str(e)
            
            # 檢查是否為資料庫鎖定錯誤
            if "database is locked" in error_msg.lower():
                logger.error(f"資料庫鎖定錯誤: 貨幣對={symbol}, 間隔={interval}秒, 時間戳={timestamp}, 資料來源={data_source}")
                logger.error(f"建議解決方案: 1.減少並行寫入操作 2.增加交易超時時間 3.可能需要重啟程式釋放鎖定")
            else:
                # 其他類型錯誤
                logger.error(f"事務中插入失敗: 貨幣對={symbol}, 間隔={interval}秒, 錯誤類型={error_type}, 詳細={error_msg}")
            
            return False
    
    def _record_duplicate_skip(self, category: str, symbol: str, interval: int, timestamp: float, new_source: str, existing_source: Optional[str]) -> None:
        """
        累計重複時間戳跳過次數並定期輸出摘要（委託給 stats_collector）
        """
        stats_collector.record_duplicate_skip(category, symbol, interval, timestamp, new_source, existing_source)

    def _build_result(self, success: bool, status: str, meta: Optional[Dict[str, Any]], return_status: bool):
        """
        建立統一的回傳格式，兼容舊有布林值與新的狀態資訊
        """
        if meta is None:
            meta = {}
        meta.setdefault('status', status)
        if return_status:
            return success, meta
        return success

    def get_stats(self) -> Dict[str, int]:
        """獲取統計信息（委託給 stats_collector）"""
        return stats_collector.get_stats()
    
    def reset_stats(self) -> None:
        """重置統計信息（委託給 stats_collector）"""
        stats_collector.reset_stats()

# 全域實例
_data_manager = DataManager()

# 全域資料庫操作鎖，防止批量抓取和回補同時運行
_db_operation_lock = threading.Lock()

def insert_data(category: str, symbol: str, interval: int, kline: Dict, data_source: str = 'real', interp_note: Optional[str] = None, api: Optional[str] = None, original_interval: Optional[str] = None, overwrite_callback: Optional[Callable] = None, return_status: bool = False):
    """插入資料（向後相容性函數）"""
    return _data_manager.insert_single_data(
        category,
        symbol,
        interval,
        kline,
        data_source,
        interp_note,
        api,
        original_interval,
        overwrite_callback,
        return_status
    )

def batch_insert_data(
    category: str, 
    symbol: str, 
    interval: int, 
    klines: List[Dict[str, Any]], 
    data_source: str = 'real', 
    interp_note: Optional[str] = None, 
    api: Optional[str] = None, 
    original_interval: Optional[str] = None, 
    overwrite_callback: Optional[Callable] = None
) -> int:
    """
    批次插入資料（向後相容性函數）
    
    高效地插入多筆K線數據，使用事務確保數據一致性。
    
    Args:
        category (str): 數據分類
        symbol (str): 交易對符號
        interval (int): 時間間隔（秒）
        klines (List[Dict[str, Any]]): K線數據列表
        data_source (str, optional): 數據來源，默認為 'real'
        interp_note (Optional[str], optional): 插值說明
        api (Optional[str], optional): API來源URL
        original_interval (Optional[str], optional): 原始時間間隔
        overwrite_callback (Optional[Callable], optional): 覆蓋確認回調函數
        
    Returns:
        int: 成功插入的記錄數量
        
    Example:
        >>> klines = [{'open_time': 1699123456000, 'open': 50000, 'high': 51000, 'low': 49000, 'close': 50500, 'volume': 100}]
        >>> count = batch_insert_data('crypto', 'BTCUSDT', 60, klines)
        >>> print(f"插入了 {count} 筆記錄")
    """
    return _data_manager.batch_insert_data_optimized(category, symbol, interval, klines, data_source, interp_note, api, original_interval, overwrite_callback)
