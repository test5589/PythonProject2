"""db_pool.py - 資料庫連線池管理"""

import sqlite3
import threading
from queue import Queue, Empty, Full
from contextlib import contextmanager
from typing import Optional
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from modules.utils.logger import get_logger
from modules.utils.exceptions import DatabaseError

logger = get_logger("db_pool")


class ConnectionPool:
    """SQLite 資料庫連線池"""
    
    def __init__(self, db_path: str, pool_size: int = 5, timeout: float = 5.0):
        """
        初始化連線池
        
        Args:
            db_path: 資料庫路徑
            pool_size: 連線池大小
            timeout: 取得連線的超時時間（秒）
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        self.pool = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._closed = False
        
        # 初始化連線池
        self._initialize_pool()
        logger.info(f"資料庫連線池已初始化：{db_path}，大小：{pool_size}")
    
    def _initialize_pool(self):
        """初始化連線池"""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self.pool.put(conn, block=False)
            except Exception as e:
                logger.error(f"初始化連線失敗：{e}")
                raise DatabaseError(f"無法初始化資料庫連線池：{e}")
    
    def _create_connection(self) -> sqlite3.Connection:
        """
        創建新的資料庫連線
        
        Returns:
            sqlite3.Connection: 資料庫連線
        """
        try:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            # 啟用 WAL 模式以提升並發效能
            conn.execute("PRAGMA journal_mode=WAL")
            # 設定外鍵約束
            conn.execute("PRAGMA foreign_keys=ON")
            # 設定busy_timeout為30秒，減少"database is locked"錯誤
            conn.execute("PRAGMA busy_timeout = 30000")
            return conn
        except Exception as e:
            logger.error(f"創建連線失敗：{e}")
            raise DatabaseError(f"無法連線到資料庫：{e}")
    
    def get_connection(self, timeout: Optional[float] = None) -> sqlite3.Connection:
        """
        從連線池取得連線
        
        Args:
            timeout: 超時時間（秒），None 使用預設值
            
        Returns:
            sqlite3.Connection: 資料庫連線
            
        Raises:
            DatabaseError: 無法取得連線
        """
        if self._closed:
            raise DatabaseError("連線池已關閉")
        
        timeout = timeout or self.timeout
        
        try:
            conn = self.pool.get(timeout=timeout)
            # 檢查連線是否有效
            try:
                conn.execute("SELECT 1")
                return conn
            except Exception:
                # 連線無效，創建新連線
                logger.warning("偵測到無效連線，重新創建")
                return self._create_connection()
        except Empty:
            logger.error(f"無法在 {timeout} 秒內取得連線")
            raise DatabaseError(f"連線池已滿，無法在 {timeout} 秒內取得連線")
    
    def return_connection(self, conn: sqlite3.Connection):
        """
        將連線歸還到連線池
        
        Args:
            conn: 資料庫連線
        """
        if self._closed:
            try:
                conn.close()
            except Exception:
                pass
            return
        
        try:
            # 回滾任何未提交的事務
            conn.rollback()
            self.pool.put(conn, block=False)
        except Full:
            # 連線池已滿，關閉連線
            logger.warning("連線池已滿，關閉額外連線")
            try:
                conn.close()
            except Exception:
                pass
        except Exception as e:
            logger.error(f"歸還連線失敗：{e}")
            try:
                conn.close()
            except Exception:
                pass
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """
        上下文管理器：自動取得和歸還連線
        
        Args:
            commit: 是否自動提交
            
        Yields:
            sqlite3.Cursor: 資料庫游標
            
        Example:
            with pool.get_cursor(commit=True) as cursor:
                cursor.execute("INSERT INTO ...")
        """
        conn = self.get_connection()
        cursor = None
        try:
            cursor = conn.cursor()
            yield cursor
            if commit:
                conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"資料庫操作錯誤：{e}")
            raise DatabaseError(f"資料庫操作失敗：{e}")
        finally:
            if cursor:
                cursor.close()
            self.return_connection(conn)
    
    def close(self):
        """關閉連線池"""
        with self._lock:
            if self._closed:
                return
            
            self._closed = True
            
            # 關閉所有連線
            while not self.pool.empty():
                try:
                    conn = self.pool.get(block=False)
                    conn.close()
                except Empty:
                    break
                except Exception as e:
                    logger.error(f"關閉連線時出錯：{e}")
            
            logger.info("資料庫連線池已關閉")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def get_pool_status(self) -> dict:
        """
        取得連線池狀態
        
        Returns:
            dict: 連線池狀態資訊
        """
        return {
            "pool_size": self.pool_size,
            "available": self.pool.qsize(),
            "in_use": self.pool_size - self.pool.qsize(),
            "closed": self._closed,
            "db_path": self.db_path
        }


# ========== 全域連線池實例 ==========
_global_pool: Optional[ConnectionPool] = None
_pool_lock = threading.Lock()


def get_connection_pool(db_path: str = None, pool_size: int = 5) -> ConnectionPool:
    """
    取得全域連線池實例（單例模式）
    
    Args:
        db_path: 資料庫路徑
        pool_size: 連線池大小
        
    Returns:
        ConnectionPool: 連線池實例
    """
    global _global_pool
    
    if db_path is None:
        # 使用預設路徑
        from modules.utils.database import DB_PATH
        db_path = DB_PATH
    
    with _pool_lock:
        if _global_pool is None or _global_pool._closed:
            _global_pool = ConnectionPool(db_path, pool_size)
        return _global_pool


def close_connection_pool():
    """關閉全域連線池"""
    global _global_pool
    
    with _pool_lock:
        if _global_pool is not None:
            _global_pool.close()
            _global_pool = None


# ========== 便捷函數 ==========
@contextmanager
def get_db_cursor(commit: bool = False, db_path: str = None):
    """
    便捷的上下文管理器，用於取得資料庫游標
    
    Args:
        commit: 是否自動提交
        db_path: 資料庫路徑
        
    Yields:
        sqlite3.Cursor: 資料庫游標
        
    Example:
        with get_db_cursor(commit=True) as cursor:
            cursor.execute("INSERT INTO ...")
    """
    pool = get_connection_pool(db_path)
    with pool.get_cursor(commit=commit) as cursor:
        yield cursor
