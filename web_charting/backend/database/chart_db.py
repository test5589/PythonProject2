"""
chart_db.py - Chart Database Manager
管理 Web Charting 應用的獨立資料庫
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from database.models import Base, CandlestickData, SyncHistory, IndicatorCache
from web_charting_backend_config import config

logger = logging.getLogger(__name__)


class ChartDatabaseManager:
    """Chart 資料庫管理器"""
    
    def __init__(self):
        """初始化資料庫管理器"""
        self.db_path = config.database.CHART_DB_PATH
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def initialize(self):
        """初始化資料庫連接"""
        if self._initialized:
            logger.warning("資料庫已經初始化")
            return
        
        try:
            # 確保資料庫目錄存在
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 創建引擎
            self.engine = create_engine(
                config.database.CHART_DB_URL,
                poolclass=QueuePool,
                pool_size=config.database.POOL_SIZE,
                max_overflow=config.database.MAX_OVERFLOW,
                pool_pre_ping=config.database.POOL_PRE_PING,
                echo=False,  # 生產環境設為 False
            )
            
            # 應用 SQLite 優化設置
            self._apply_sqlite_pragmas()
            
            # 創建表格
            Base.metadata.create_all(bind=self.engine)
            
            # 創建 Session 工廠
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            self._initialized = True
            logger.info(f"✅ Chart 資料庫初始化成功: {self.db_path}")
            
        except Exception as e:
            logger.error(f"❌ 資料庫初始化失敗: {e}")
            raise
    
    def _apply_sqlite_pragmas(self):
        """應用 SQLite 優化設置"""
        try:
            with self.engine.connect() as conn:
                for key, value in config.database.SQLITE_PRAGMAS.items():
                    conn.execute(text(f"PRAGMA {key}={value}"))
                conn.commit()
            logger.info("✅ SQLite 優化設置已應用")
        except Exception as e:
            logger.warning(f"⚠️ SQLite 優化設置應用失敗: {e}")
    
    @contextmanager
    def get_session(self) -> Session:
        """獲取資料庫 Session（上下文管理器）"""
        if not self._initialized:
            self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Session 錯誤: {e}")
            raise
        finally:
            session.close()
    
    def close(self):
        """關閉資料庫連接"""
        if self.engine:
            self.engine.dispose()
            self._initialized = False
            logger.info("🔌 資料庫連接已關閉")
    
    # ========== K線資料操作 ==========
    
    def insert_candles(
        self, 
        candles: List[Dict[str, Any]], 
        session: Optional[Session] = None
    ) -> int:
        """
        批量插入 K線資料（使用 upsert 邏輯）
        
        Args:
            candles: K線資料列表
            session: 可選的現有 Session
            
        Returns:
            插入/更新的記錄數
        """
        if not candles:
            return 0
        
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            inserted = 0
            updated = 0
            
            for candle_data in candles:
                try:
                    # 檢查是否已存在（根據 unique constraint）
                    existing = session.query(CandlestickData).filter(
                        CandlestickData.symbol == candle_data['symbol'],
                        CandlestickData.interval == candle_data['interval'],
                        CandlestickData.timestamp == candle_data['timestamp'],
                        CandlestickData.data_source == candle_data['data_source']
                    ).first()
                    
                    if existing:
                        # 更新現有記錄
                        for key, value in candle_data.items():
                            if key not in ['created_at']:  # 保留創建時間
                                setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                        updated += 1
                    else:
                        # 插入新記錄
                        candle = CandlestickData(**candle_data)
                        session.add(candle)
                        inserted += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ 處理K線失敗: {e}")
                    continue
            
            if not use_existing_session:
                session.commit()
            
            logger.info(f"✅ K線處理完成: 新增 {inserted} 條, 更新 {updated} 條 (總計 {len(candles)} 條)")
            return inserted + updated
            
        except Exception as e:
            if not use_existing_session:
                session.rollback()
            logger.error(f"❌ 批量插入K線失敗: {e}")
            raise
        finally:
            if not use_existing_session:
                session.close()
    
    def query_candles(
        self,
        symbol: str,
        interval: int,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        data_source: Optional[str] = None,
        limit: int = 1000,
        session: Optional[Session] = None
    ) -> List[CandlestickData]:
        """
        查詢 K線資料
        
        Args:
            symbol: 交易對
            interval: 時間框架（秒）
            start_time: 開始時間（Unix timestamp）
            end_time: 結束時間（Unix timestamp）
            data_source: 資料來源過濾
            limit: 最大返回數量
            session: 可選的現有 Session
            
        Returns:
            K線資料列表
        """
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            query = session.query(CandlestickData).filter(
                CandlestickData.symbol == symbol,
                CandlestickData.interval == interval
            )
            
            if start_time:
                query = query.filter(CandlestickData.timestamp >= start_time)
            if end_time:
                query = query.filter(CandlestickData.timestamp <= end_time)
            if data_source:
                query = query.filter(CandlestickData.data_source == data_source)
            
            # 按時間倒序排列，取最新的 N 條
            candles = query.order_by(CandlestickData.timestamp.desc()).limit(limit).all()
            
            # 反轉順序（從舊到新）
            candles.reverse()
            
            return candles
            
        except Exception as e:
            logger.error(f"❌ 查詢K線失敗: {e}")
            raise
        finally:
            if not use_existing_session:
                session.close()
    
    def delete_candles(
        self,
        symbol: str,
        interval: int,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        session: Optional[Session] = None
    ) -> int:
        """
        刪除 K線資料
        
        Args:
            symbol: 交易對
            interval: 時間框架（秒）
            start_time: 開始時間（可選）
            end_time: 結束時間（可選）
            session: 可選的現有 Session
            
        Returns:
            刪除的記錄數
        """
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            query = session.query(CandlestickData).filter(
                CandlestickData.symbol == symbol,
                CandlestickData.interval == interval
            )
            
            if start_time:
                query = query.filter(CandlestickData.timestamp >= start_time)
            if end_time:
                query = query.filter(CandlestickData.timestamp <= end_time)
            
            deleted = query.delete()
            
            if not use_existing_session:
                session.commit()
            
            logger.info(f"✅ 刪除 {deleted} 根K線")
            return deleted
            
        except Exception as e:
            if not use_existing_session:
                session.rollback()
            logger.error(f"❌ 刪除K線失敗: {e}")
            raise
        finally:
            if not use_existing_session:
                session.close()
    
    # ========== 同步記錄操作 ==========
    
    def create_sync_record(
        self,
        symbol: str,
        interval: int,
        start_time: float,
        end_time: float,
        session: Optional[Session] = None
    ) -> SyncHistory:
        """創建同步記錄"""
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            sync_record = SyncHistory(
                symbol=symbol,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                sync_status='pending'
            )
            
            session.add(sync_record)
            
            if not use_existing_session:
                session.commit()
                session.refresh(sync_record)
            
            return sync_record
            
        except Exception as e:
            if not use_existing_session:
                session.rollback()
            logger.error(f"❌ 創建同步記錄失敗: {e}")
            raise
        finally:
            if not use_existing_session:
                session.close()
    
    def update_sync_record(
        self,
        sync_id: int,
        status: str,
        records_synced: Optional[int] = None,
        error_message: Optional[str] = None,
        session: Optional[Session] = None
    ):
        """更新同步記錄"""
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            sync_record = session.query(SyncHistory).filter(
                SyncHistory.id == sync_id
            ).first()
            
            if sync_record:
                sync_record.sync_status = status
                if records_synced is not None:
                    sync_record.records_synced = records_synced
                if error_message:
                    sync_record.error_message = error_message
                if status in ['completed', 'failed']:
                    sync_record.completed_at = datetime.utcnow()
                
                if not use_existing_session:
                    session.commit()
            
        except Exception as e:
            if not use_existing_session:
                session.rollback()
            logger.error(f"❌ 更新同步記錄失敗: {e}")
            raise
        finally:
            if not use_existing_session:
                session.close()
    
    def get_last_sync_time(
        self,
        symbol: str,
        interval: int,
        session: Optional[Session] = None
    ) -> Optional[float]:
        """獲取最後同步時間"""
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            last_sync = session.query(SyncHistory).filter(
                SyncHistory.symbol == symbol,
                SyncHistory.interval == interval,
                SyncHistory.sync_status == 'completed'
            ).order_by(SyncHistory.end_time.desc()).first()
            
            return last_sync.end_time if last_sync else None
            
        except Exception as e:
            logger.error(f"❌ 獲取最後同步時間失敗: {e}")
            return None
        finally:
            if not use_existing_session:
                session.close()
    
    # ========== 指標緩存操作 ==========
    
    def cache_indicator(
        self,
        symbol: str,
        interval: int,
        indicator_name: str,
        timestamp: float,
        value: float,
        params: Optional[Dict] = None,
        session: Optional[Session] = None
    ):
        """緩存指標值"""
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            indicator = IndicatorCache(
                symbol=symbol,
                interval=interval,
                indicator_name=indicator_name,
                timestamp=timestamp,
                value=value,
                params=params
            )
            
            session.merge(indicator)
            
            if not use_existing_session:
                session.commit()
            
        except Exception as e:
            if not use_existing_session:
                session.rollback()
            logger.error(f"❌ 緩存指標失敗: {e}")
            raise
        finally:
            if not use_existing_session:
                session.close()
    
    # ========== 維護操作 ==========
    
    def cleanup_old_data(self, days: int = 90, session: Optional[Session] = None):
        """清理舊數據"""
        use_existing_session = session is not None
        
        try:
            if not use_existing_session:
                session = self.SessionLocal()
            
            from datetime import timedelta
            cutoff_time = (datetime.utcnow() - timedelta(days=days)).timestamp()
            
            deleted = session.query(CandlestickData).filter(
                CandlestickData.timestamp < cutoff_time
            ).delete()
            
            if not use_existing_session:
                session.commit()
            
            logger.info(f"✅ 清理舊數據：刪除 {deleted} 條記錄")
            return deleted
            
        except Exception as e:
            if not use_existing_session:
                session.rollback()
            logger.error(f"❌ 清理舊數據失敗: {e}")
            raise
        finally:
            if not use_existing_session:
                session.close()
    
    def vacuum(self):
        """執行 VACUUM 回收空間"""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM"))
                conn.commit()
            logger.info("✅ VACUUM 完成")
        except Exception as e:
            logger.error(f"❌ VACUUM 失敗: {e}")
            raise


# 全局實例
chart_db = ChartDatabaseManager()


def init_db():
    """初始化資料庫（供外部調用）"""
    chart_db.initialize()
    return chart_db


if __name__ == "__main__":
    # 測試資料庫初始化
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
    )
    
    print("開始測試 Chart 資料庫...")
    init_db()
    print("✅ 資料庫測試完成")
