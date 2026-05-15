"""
database.py - 資料庫統一管理
使用模組化結構管理資料庫操作
"""

from .database.db_core import DB_PATH, init_db, query_ohlcv, _ensure_db_dir, _migrate_schema
from .database.data_manager import insert_data, batch_insert_data

# 向後相容性 - 重新導出所有主要函數和變數
__all__ = [
    'DB_PATH',
    'init_db', 
    'query_ohlcv',
    'insert_data',
    'batch_insert_data',
    '_ensure_db_dir',
    '_migrate_schema'
]
