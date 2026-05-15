"""
db_core.py - 資料庫核心操作
負責資料庫連接、初始化和基本操作
"""

import os
import sqlite3

# 資料庫路徑設定
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "system_data.db"))

# 預設API URL（避免循環導入）
DEFAULT_API_URL = "https://api.binance.com"

class DatabaseCore:
    """資料庫核心操作類"""
    
    def __init__(self):
        self.db_path = DB_PATH
        
    def ensure_db_dir(self) -> None:
        """
        確保資料庫目錄存在
        
        如果資料庫所在目錄不存在，會自動創建該目錄及其父目錄。
        使用 exist_ok=True 確保即使目錄已存在也不會報錯。
        
        Returns:
            None
        """
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
    def get_connection(self) -> sqlite3.Connection:
        """獲取資料庫連接（加長 timeout + busy_timeout，減少 database is locked 錯誤）。

        - 每次呼叫都建立一個新的連線；
        - 設定 timeout=30 秒，並透過 PRAGMA busy_timeout 讓 SQLite 在被鎖住時等待一段時間，
          避免在批量寫入時頻繁拋出 "database is locked"。
        """
        self.ensure_db_dir()
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        try:
            # 讓 SQLite 在遇到鎖時最多等待 30 秒，而不是立刻丟出錯誤
            conn.execute("PRAGMA busy_timeout=30000")
        except Exception:
            # 設定失敗時不影響主要流程
            pass
        return conn
        
    def init_database(self) -> None:
        """
        初始化資料庫（建立 historical_data 表格）
        
        創建 historical_data 表格，包含所有必要的欄位：
        - 基本OHLCV數據 (open, high, low, close, volume)
        - 時間戳記和可讀時間
        - 幣安原始數據欄位 (11欄格式)
        - 數據來源標記和API標識
        
        如果表格已存在，不會重複創建。
        同時執行結構遷移以確保欄位完整性。
        
        Returns:
            None
            
        Raises:
            sqlite3.Error: 當資料庫操作失敗時
        """
        self.ensure_db_dir()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS historical_data (
                timestamp REAL,
                category TEXT,
                symbol TEXT,
                interval INTEGER,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                -- 追加的原始欄位（依幣安 11 欄）
                open_time REAL,
                close_time REAL,
                quote_asset_volume REAL,
                num_trades INTEGER,
                taker_base_vol REAL,
                taker_quote_vol REAL,
                -- 來源標記
                data_source TEXT DEFAULT 'real',
                interp_note TEXT,
                api TEXT DEFAULT 'https://api.binance.com',
                PRIMARY KEY (timestamp, category, symbol, interval, api)
            )
            """
        )
        
        # 執行結構遷移
        self.migrate_schema(conn)
        conn.commit()
        conn.close()
        
    def migrate_schema(self, conn: sqlite3.Connection):
        """針對歷史資料表執行結構遷移"""
        try:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(historical_data)")
            cols = [r[1] for r in cur.fetchall()]

            # 如果仍存在舊的 readable_time 欄位，執行一次性遷移以物理移除該欄位
            if 'readable_time' in cols:
                try:
                    # 建立新的表結構（不含 readable_time）
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS historical_data_new (
                            timestamp REAL,
                            category TEXT,
                            symbol TEXT,
                            interval INTEGER,
                            open REAL,
                            high REAL,
                            low REAL,
                            close REAL,
                            volume REAL,
                            open_time REAL,
                            close_time REAL,
                            quote_asset_volume REAL,
                            num_trades INTEGER,
                            taker_base_vol REAL,
                            taker_quote_vol REAL,
                            data_source TEXT DEFAULT 'real',
                            interp_note TEXT,
                            api TEXT DEFAULT 'https://api.binance.com',
                            PRIMARY KEY (timestamp, category, symbol, interval, api)
                        )
                        """
                    )

                    # 將舊表資料（排除 readable_time）複製到新表
                    cur.execute(
                        """
                        INSERT OR REPLACE INTO historical_data_new (
                            timestamp, category, symbol, interval,
                            open, high, low, close, volume,
                            open_time, close_time, quote_asset_volume, num_trades,
                            taker_base_vol, taker_quote_vol,
                            data_source, interp_note, api
                        )
                        SELECT
                            timestamp, category, symbol, interval,
                            open, high, low, close, volume,
                            open_time, close_time, quote_asset_volume, num_trades,
                            taker_base_vol, taker_quote_vol,
                            data_source, interp_note, api
                        FROM historical_data
                        """
                    )

                    # 刪除舊表並將新表改名為 historical_data
                    cur.execute("DROP TABLE historical_data")
                    cur.execute("ALTER TABLE historical_data_new RENAME TO historical_data")

                    # 重新取得欄位資訊，供後續遷移步驟使用
                    cur.execute("PRAGMA table_info(historical_data)")
                    cols = [r[1] for r in cur.fetchall()]
                except Exception as e:
                    print(f"⚠️ readable_time 欄位遷移失敗: {e}")
            
            needed = [
                "open", "high", "low", "close", "volume",
                "open_time", "close_time", "quote_asset_volume", 
                "num_trades", "taker_base_vol", "taker_quote_vol"
            ]
            
            for col in needed:
                if col not in cols:
                    try:
                        cur.execute(f"ALTER TABLE historical_data ADD COLUMN {col} REAL")
                    except Exception:
                        pass
                        
            # 新增來源欄位
            if 'data_source' not in cols:
                try:
                    cur.execute("ALTER TABLE historical_data ADD COLUMN data_source TEXT DEFAULT 'real'")
                except Exception:
                    pass
                    
            if 'interp_note' not in cols:
                try:
                    cur.execute("ALTER TABLE historical_data ADD COLUMN interp_note TEXT")
                except Exception:
                    pass
                    
            # 新增 API 欄位
            if 'api' not in cols:
                try:
                    cur.execute(f"ALTER TABLE historical_data ADD COLUMN api TEXT DEFAULT '{DEFAULT_API_URL}'")
                except Exception:
                    pass
                    
            conn.commit()
        except Exception as e:
            print(f"⚠️ schema 遷移失敗: {e}")
            
    def query_ohlcv(self, category: str, symbol: str, interval: int, limit: int = 5):
        """查詢最新資料"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute(
            """
            SELECT timestamp, category, symbol, interval,
                   open, high, low, close, volume
            FROM historical_data
            WHERE category=? AND symbol=? AND interval=?
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (category, symbol, interval, limit)
        )
        rows = cur.fetchall()
        conn.close()
        return rows
        
    def execute_query(self, query: str, params: tuple = (), fetch_one: bool = False):
        """執行自定義查詢"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(query, params)
            if fetch_one:
                result = cur.fetchone()
            else:
                result = cur.fetchall()
            conn.commit()
            return result
        except Exception as e:
            print(f"❌ 查詢執行失敗: {e}")
            return None
        finally:
            conn.close()
            
    def get_table_info(self, table_name: str = "historical_data"):
        """獲取表格信息"""
        conn = self.get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(f"PRAGMA table_info({table_name})")
            columns = cur.fetchall()
            
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            row_count = cur.fetchone()[0]
            
            return {
                'columns': columns,
                'row_count': row_count
            }
        except Exception as e:
            print(f"❌ 獲取表格信息失敗: {e}")
            return None
        finally:
            conn.close()

# 全域實例
_db_core = DatabaseCore()

# 向後相容性函數
def _ensure_db_dir():
    """確保資料庫目錄存在（向後相容性函數）"""
    return _db_core.ensure_db_dir()

def init_db():
    """初始化資料庫（向後相容性函數）"""
    return _db_core.init_database()

def query_ohlcv(category: str, symbol: str, interval: int, limit: int = 5) -> list:
    """
    查詢最新資料（向後相容性函數）
    
    根據指定的分類、交易對和時間間隔查詢最新的OHLCV數據。
    
    Args:
        category (str): 數據分類，通常為 'crypto'
        symbol (str): 交易對符號，如 'BTCUSDT'
        interval (int): 時間間隔（秒），如 60 代表1分鐘
        limit (int, optional): 查詢記錄數量限制，默認為5
        
    Returns:
        list: 包含OHLCV數據的元組列表，按時間戳記降序排列
              每個元組格式: (timestamp, category, symbol, interval, open, high, low, close, volume)
              
    Example:
        >>> query_ohlcv('crypto', 'BTCUSDT', 60, 10)
        [(1699123456.0, 'crypto', 'BTCUSDT', 60, 50000.0, 51000.0, 49000.0, 50500.0, 100.5)]
    """
    return _db_core.query_ohlcv(category, symbol, interval, limit)

def _migrate_schema(conn: sqlite3.Connection):
    """執行結構遷移（向後相容性函數）"""
    return _db_core.migrate_schema(conn)
