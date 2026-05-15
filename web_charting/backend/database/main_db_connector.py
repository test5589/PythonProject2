"""
main_db_connector.py - Main Database Connector
連接主資料庫以同步數據到 Chart DB
"""
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from web_charting_backend_config import config

logger = logging.getLogger(__name__)


class MainDatabaseConnector:
    """主資料庫連接器"""
    
    def __init__(self):
        """初始化主資料庫連接"""
        self.db_path = config.database.MAIN_DB_PATH
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """初始化連接"""
        if self._initialized:
            return
        
        try:
            if not self.db_path.exists():
                raise FileNotFoundError(f"主資料庫不存在: {self.db_path}")
            
            self.engine = create_engine(
                config.database.MAIN_DB_URL,
                echo=False
            )
            
            self.SessionLocal = sessionmaker(bind=self.engine)
            self._initialized = True
            
            logger.info(f"✅ 主資料庫連接成功: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ 主資料庫連接失敗: {e}")
            raise
    
    def fetch_candles(
        self,
        category: str,
        symbol: str,
        interval: int,
        start_time: float,
        end_time: float,
        data_source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        從主資料庫獲取 K線資料
        
        Args:
            category: 分類（crypto/stock）
            symbol: 交易對
            interval: 時間框架（秒）
            start_time: 開始時間（Unix timestamp）
            end_time: 結束時間（Unix timestamp）
            data_source: 資料來源過濾（可選）
            
        Returns:
            K線資料列表
        """
        if not self._initialized:
            self.initialize()
        
        try:
            session = self.SessionLocal()
            
            # 構建查詢
            query = """
                SELECT 
                    symbol,
                    interval,
                    timestamp,
                    open,
                    high,
                    low,
                    close,
                    volume,
                    data_source
                FROM historical_data
                WHERE category = :category
                    AND symbol = :symbol
                    AND interval = :interval
                    AND timestamp >= :start_time
                    AND timestamp <= :end_time
            """
            
            params = {
                'category': category,
                'symbol': symbol,
                'interval': interval,
                'start_time': start_time,
                'end_time': end_time
            }
            
            if data_source:
                query += " AND data_source = :data_source"
                params['data_source'] = data_source
            
            query += " ORDER BY timestamp ASC"
            
            result = session.execute(text(query), params)
            rows = result.fetchall()
            
            # 轉換為字典列表
            candles = []
            for row in rows:
                candles.append({
                    'symbol': row.symbol,
                    'interval': row.interval,
                    'timestamp': row.timestamp,
                    'open': row.open,
                    'high': row.high,
                    'low': row.low,
                    'close': row.close,
                    'volume': row.volume if row.volume else 0,
                    'data_source': row.data_source,
                    'priority': self._get_priority(row.data_source)
                })
            
            session.close()
            
            logger.info(f"✅ 從主DB獲取 {len(candles)} 根K線: {symbol}@{interval}s")
            return candles
            
        except Exception as e:
            logger.error(f"❌ 從主DB獲取資料失敗: {e}")
            raise
    
    def _get_priority(self, data_source: str) -> int:
        """獲取資料優先級"""
        return config.chart.DATA_PRIORITY.get(data_source, 5)
    
    def get_available_symbols(self, category: str = 'crypto') -> List[str]:
        """獲取可用的交易對列表"""
        if not self._initialized:
            self.initialize()
        
        try:
            session = self.SessionLocal()
            
            query = """
                SELECT DISTINCT symbol
                FROM historical_data
                WHERE category = :category
                ORDER BY symbol
            """
            
            result = session.execute(text(query), {'category': category})
            symbols = [row.symbol for row in result.fetchall()]
            
            session.close()
            
            logger.info(f"✅ 獲取 {len(symbols)} 個可用交易對")
            return symbols
            
        except Exception as e:
            logger.error(f"❌ 獲取交易對列表失敗: {e}")
            return []
    
    def get_data_range(
        self,
        category: str,
        symbol: str,
        interval: int
    ) -> Optional[Dict[str, float]]:
        """
        獲取資料時間範圍
        
        Returns:
            {'min_time': float, 'max_time': float, 'count': int}
        """
        if not self._initialized:
            self.initialize()
        
        try:
            session = self.SessionLocal()
            
            query = """
                SELECT 
                    MIN(timestamp) as min_time,
                    MAX(timestamp) as max_time,
                    COUNT(*) as count
                FROM historical_data
                WHERE category = :category
                    AND symbol = :symbol
                    AND interval = :interval
            """
            
            result = session.execute(text(query), {
                'category': category,
                'symbol': symbol,
                'interval': interval
            })
            
            row = result.fetchone()
            session.close()
            
            if row and row.count > 0:
                return {
                    'min_time': row.min_time,
                    'max_time': row.max_time,
                    'count': row.count
                }
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 獲取資料範圍失敗: {e}")
            return None
    
    def close(self):
        """關閉連接"""
        if self.engine:
            self.engine.dispose()
            self._initialized = False
            logger.info("🔌 主資料庫連接已關閉")


# 全局實例
main_db = MainDatabaseConnector()


if __name__ == "__main__":
    # 測試連接
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    
    print("測試主資料庫連接...")
    main_db.initialize()
    
    # 測試獲取交易對
    symbols = main_db.get_available_symbols('crypto')
    print(f"可用交易對: {symbols[:5]}...")
    
    print("✅ 測試完成")
