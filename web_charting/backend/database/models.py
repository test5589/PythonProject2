"""
models.py - Database Models for Web Charting Application
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Index, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class CandlestickData(Base):
    """K線資料表"""
    __tablename__ = "candlestick_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(Integer, nullable=False, index=True)  # 秒為單位
    timestamp = Column(Float, nullable=False, index=True)   # Unix timestamp
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    data_source = Column(String(20), nullable=False, index=True)  # 'real', 'Aggregation', etc.
    priority = Column(Integer, default=1)                         # 資料優先級 (1=最高)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 複合索引
    __table_args__ = (
        # 查詢優化索引
        Index('idx_symbol_interval_timestamp', 'symbol', 'interval', 'timestamp'),
        Index('idx_timestamp_symbol', 'timestamp', 'symbol', 'interval'),
        Index('idx_source_symbol', 'data_source', 'symbol', 'interval'),
        
        # 唯一約束
        UniqueConstraint('symbol', 'interval', 'timestamp', 'data_source', name='uq_candle'),
    )
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'interval': self.interval,
            'timestamp': self.timestamp,
            'open': self.open,
            'high': self.high,
            'low': self.low,
            'close': self.close,
            'volume': self.volume,
            'data_source': self.data_source,
            'priority': self.priority,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    def __repr__(self):
        return f"<Candle {self.symbol}@{self.interval}s {self.timestamp} {self.data_source}>"


class SyncHistory(Base):
    """同步記錄表"""
    __tablename__ = "sync_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(Integer, nullable=False, index=True)
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    records_synced = Column(Integer, default=0)
    sync_status = Column(String(20), default='pending')  # 'pending', 'running', 'completed', 'failed'
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    
    __table_args__ = (
        Index('idx_sync_symbol_interval', 'symbol', 'interval'),
        Index('idx_sync_status', 'sync_status'),
    )
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'interval': self.interval,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'records_synced': self.records_synced,
            'sync_status': self.sync_status,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
    
    def __repr__(self):
        return f"<SyncHistory {self.symbol}@{self.interval}s {self.sync_status}>"


class IndicatorCache(Base):
    """指標緩存表"""
    __tablename__ = "indicator_cache"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, index=True)
    interval = Column(Integer, nullable=False, index=True)
    indicator_name = Column(String(50), nullable=False, index=True)
    timestamp = Column(Float, nullable=False, index=True)
    value = Column(Float, nullable=False)
    params = Column(JSON)  # 指標參數（JSON格式）
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_indicator_lookup', 'symbol', 'interval', 'indicator_name', 'timestamp'),
        UniqueConstraint('symbol', 'interval', 'indicator_name', 'timestamp', 'params', 
                        name='uq_indicator'),
    )
    
    def to_dict(self):
        """轉換為字典"""
        return {
            'id': self.id,
            'symbol': self.symbol,
            'interval': self.interval,
            'indicator_name': self.indicator_name,
            'timestamp': self.timestamp,
            'value': self.value,
            'params': self.params,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
    
    def __repr__(self):
        return f"<IndicatorCache {self.indicator_name} {self.symbol}@{self.interval}s>"
