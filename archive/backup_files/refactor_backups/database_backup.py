"""此database.py為資料庫相關邏輯"""


import os
import sqlite3
import time
from datetime import datetime, timezone, timedelta
from modules.utils.api_manager import api_manager, get_default_api_url

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "system_data.db"))

"""__file__：目前執行的 Python 檔案的檔案路徑（例如 .../modules/utils/database.py）。
   os.path.dirname(__file__)：取得該檔案的目錄（.../modules/utils）。

os.path.join(os.path.dirname(__file__), "..", "..", "data", "system_data.db")：
從 modules/utils 向上兩層（modules → 專案根目錄），再進入 data 資料夾，最後指向 system_data.db。
等同於 .../PythonProject2/data/system_data.db。

os.path.abspath(...)：把上一步產生的相對路徑標準化成絕對路徑（完整路徑），
避免不同工作目錄造成找不到檔案的問題。"""





"""你在 gui.py 匯入了 modules.utils.database，
但 database.py 裡又在頂部 匯入自己，導致「循環匯入」。
這是多餘的、自我循環導入。
所以 Python 無法完成載入（因為還在初始化中）。"""
"""from modules.utils.database import query_ohlcv, init_db"""

def _ensure_db_dir():
    """確保資料夾存在（例如 data/）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)



def init_db():
    """初始化資料庫（建立 historical_data 表格）"""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS historical_data (
            timestamp REAL,
            readable_time TEXT,
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
    # 嘗試執行結構遷移（處理舊資料表缺少欄位的情況）
    _migrate_schema(conn)
    conn.commit()
    conn.close()



def batch_insert_data(category: str, symbol: str, interval: int, klines: list[dict], *, data_source: str = 'real', interp_note: str | None = None, api: str = None, original_interval: str = None, overwrite_callback: callable = None):
    """
    批次插入多筆資料，效能優於逐筆插入
    
    Args:
        category: 資產分類
        symbol: 交易對
        interval: 間隔秒數
        klines: K 線資料列表
        data_source: 資料來源（real/interpolated/Aggregation/inferior-Aggregation）
        interp_note: 插值註記
        api: API URL
        original_interval: 原始間隔字串（如 1m, 1h）
        overwrite_callback: 覆蓋確認回呼函數
    """
    if not klines:
        return
    
    # 如果沒有指定 API，使用預設 API
    if api is None:
        api = get_default_api_url()
    
    # 如果沒有指定原始間格，嘗試從秒數推斷
    if original_interval is None:
        interval_map = {
            1: "1s", 60: "1m", 300: "5m", 900: "15m", 1800: "30m",
            3600: "1h", 14400: "4h", 28800: "8h", 43200: "12h", 86400: "1d"
        }
        original_interval = interval_map.get(interval, f"{interval}s")
    
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # 準備批次資料
    batch_data = []
    skipped_count = 0
    
    for kline in klines:
        # 計算時間戳
        try:
            ts_ms = kline.get("open_time")
            if ts_ms is None:
                ct = kline.get("close_time")
                if ct is not None:
                    ts_ms = int(ct) - int(interval * 1000)
            if ts_ms is None:
                ts_ms = int(time.time() * 1000)
            ts = ts_ms / 1000.0
            taipei_dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
            readable_time = taipei_dt.strftime("%Y/%m/%d %H:%M:%S")
        except Exception:
            ts = time.time()
            taipei_dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
            readable_time = taipei_dt.strftime("%Y/%m/%d %H:%M:%S")
        
        # 檢查現存資料
        cur.execute(
            "SELECT data_source FROM historical_data WHERE timestamp=? AND category=? AND symbol=? AND interval=? AND api=?",
            (ts, category, symbol, interval, api)
        )
        row = cur.fetchone()
        
        if row:
            existing_source = row[0] or 'real'
            priority = {'real': 1, 'interpolated': 2, 'Aggregation': 3, 'inferior-Aggregation': 4}
            existing_priority = priority.get(existing_source, 99)
            new_priority = priority.get(data_source, 99)
            
            # 如果現有資料優先級更高，跳過
            if existing_priority < new_priority:
                skipped_count += 1
                continue
            
            # real 對 real 的情況
            if existing_source == 'real' and data_source == 'real':
                if overwrite_callback:
                    if not overwrite_callback(symbol, original_interval, readable_time):
                        skipped_count += 1
                        continue
                else:
                    skipped_count += 1
                    continue
        
        # 準備資料行
        open_time = kline.get('open_time', int(ts * 1000))
        close_time = kline.get('close_time', int(open_time + (interval * 1000)))
        
        batch_data.append((
            ts,
            readable_time,
            category,
            symbol,
            interval,
            float(kline.get('open', 0.0)),
            float(kline.get('high', 0.0)),
            float(kline.get('low', 0.0)),
            float(kline.get('close', 0.0)),
            float(kline.get('volume', 0.0)),
            float(open_time),
            float(close_time),
            float(kline.get('quote_asset_volume', 0.0)),
            int(kline.get('num_trades', 0)),
            float(kline.get('taker_base_vol', 0.0)),
            float(kline.get('taker_quote_vol', 0.0)),
            data_source,
            interp_note,
            api,
        ))
    
    # 批次插入
    if batch_data:
        cur.executemany(
            """
            INSERT OR REPLACE INTO historical_data
            (timestamp, readable_time, category, symbol, interval,
             open, high, low, close, volume,
             open_time, close_time, quote_asset_volume, num_trades, taker_base_vol, taker_quote_vol,
             data_source, interp_note, api)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            batch_data
        )
        conn.commit()
        print(f"✅ 批次插入完成: {len(batch_data)} 筆資料 ({symbol} @ {original_interval}), 跳過 {skipped_count} 筆")
    
    conn.close()
    return len(batch_data)


def insert_data(category: str, symbol: str, interval: int, kline: dict, *, data_source: str = 'real', interp_note: str | None = None, api: str = None, original_interval: str = None, overwrite_callback: callable = None):
    # 如果沒有指定 API，使用預設 API
    if api is None:
        api = get_default_api_url()
    
    # 如果沒有指定原始間格，嘗試從秒數推斷
    if original_interval is None:
        if interval == 1:
            original_interval = "1s"
        elif interval == 60:
            original_interval = "1m"
        elif interval == 300:
            original_interval = "5m"
        elif interval == 900:
            original_interval = "15m"
        elif interval == 1800:
            original_interval = "30m"
        elif interval == 3600:
            original_interval = "1h"
        elif interval == 14400:
            original_interval = "4h"
        elif interval == 28800:
            original_interval = "8h"
        elif interval == 43200:
            original_interval = "12h"
        elif interval == 86400:
            original_interval = "1d"
        else:
            original_interval = f"{interval}s"
    # 以資料本身的時間作為日誌前綴（UTC+8），優先使用 kline.open_time（毫秒）
    try:
        ts_ms = kline.get("open_time")
        if ts_ms is None:
            # 備援：若有 close_time，回推 interval 秒
            ct = kline.get("close_time")
            if ct is not None:
                ts_ms = int(ct) - int(interval * 1000)
        if ts_ms is None:
            ts_ms = int(time.time() * 1000)
        ts = ts_ms / 1000.0
        taipei_dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        readable_time = taipei_dt.strftime("%Y/%m/%d %H:%M:%S")
        pfx = taipei_dt.strftime("[UTC+8 %Y-%m-%d %H:%M:%S] ")
    except Exception:
        ts = time.time()
        taipei_dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
        readable_time = taipei_dt.strftime("%Y/%m/%d %H:%M:%S")
        pfx = "[UTC+8] "
    print(f"{pfx}🧾 insert_data() 準備寫入: {symbol} @ {original_interval}")
    try:
        _ensure_db_dir()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        # 其他原始欄位（若缺則以預設值補上）
        # 其他原始欄位（若缺則以預設值補上）
        open_time = kline.get('open_time')
        if open_time is None:
            # 若無 open_time，以 ts(ms) 推回：timestamp 為秒，轉 ms
            open_time = int(ts * 1000)
        close_time = kline.get('close_time')
        if close_time is None:
            # 以 interval 粗估 close_time = open_time + interval*1000
            close_time = int(open_time + (interval * 1000))
        quote_asset_volume = float(kline.get('quote_asset_volume', 0.0))
        num_trades = int(kline.get('num_trades', 0))
        taker_base_vol = float(kline.get('taker_base_vol', 0.0))
        taker_quote_vol = float(kline.get('taker_quote_vol', 0.0))

        # 寫入前檢查現存來源，實現資料來源優先級：real > interpolated > Aggregation > inferior-Aggregation
        cur.execute(
            """
            SELECT data_source FROM historical_data
            WHERE timestamp=? AND category=? AND symbol=? AND interval=? AND api=?
            """,
            (ts, category, symbol, interval, api)
        )
        row = cur.fetchone()
        if row:
            existing_source = row[0] or 'real'
            # 定義優先級順序（數字越小優先級越高）
            priority = {
                'real': 1,
                'interpolated': 2,
                'Aggregation': 3,
                'inferior-Aggregation': 4
            }
            
            existing_priority = priority.get(existing_source, 99)
            new_priority = priority.get(data_source, 99)
            
            # 特殊情況：如果現有是 real，新資料也是 real，需要詢問用戶
            if existing_source == 'real' and data_source == 'real':
                if overwrite_callback:
                    # 詢問用戶是否覆蓋
                    should_overwrite = overwrite_callback(symbol, original_interval, readable_time)
                    if not should_overwrite:
                        conn.close()
                        print(f"{pfx}⏭ 跳過：用戶選擇不覆蓋現有 real 資料")
                        return
                else:
                    # 沒有 callback，默認跳過
                    conn.close()
                    print(f"{pfx}⏭ 跳過：已存在 real 資料，不覆蓋")
                    return
            # 如果現有資料優先級高於新資料，則跳過插入
            elif existing_priority < new_priority:
                conn.close()
                print(f"{pfx}⏭ 跳過：已存在 {existing_source} 資料（優先級 {existing_priority}），不以 {data_source}（優先級 {new_priority}）覆蓋")
                return
        # 若現有為 interpolated 且新資料為 real，允許覆蓋；其他情況 REPLACE 不會改變一致資料
        cur.execute(
            """
            INSERT OR REPLACE INTO historical_data
            (timestamp, readable_time, category, symbol, interval,
             open, high, low, close, volume,
             open_time, close_time, quote_asset_volume, num_trades, taker_base_vol, taker_quote_vol,
             data_source, interp_note, api)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ts,
                readable_time,
                category,
                symbol,
                interval,
                float(kline.get('open', 0.0)),
                float(kline.get('high', 0.0)),
                float(kline.get('low', 0.0)),
                float(kline.get('close', 0.0)),
                float(kline.get('volume', 0.0)),
                float(open_time),
                float(close_time),
                quote_asset_volume,
                num_trades,
                taker_base_vol,
                taker_quote_vol,
                data_source,
                interp_note,
                api,
            ),
        )
        conn.commit()
        conn.close()
        print(f"{pfx}✅ insert_data: 已寫入 {symbol} @ {original_interval} → close={kline.get('close')} source={data_source} note={interp_note or ''}")
    except Exception as e:
        # 盡可能使用資料時間作為前綴（與前面一致），失敗則退回固定標籤
        try:
            if 'ts' in locals():
                taipei_dt = datetime.fromtimestamp(ts, tz=timezone(timedelta(hours=8)))
                pfx = taipei_dt.strftime("[UTC+8 %Y-%m-%d %H:%M:%S] ")
            else:
                pfx = "[UTC+8] "
        except Exception:
            pfx = "[UTC+8] "
        print(f"{pfx}❌ insert_data() 錯誤: {e}")


def _migrate_schema(conn: sqlite3.Connection):
    """針對歷史資料表執行結構遷移：若缺少 OHLCV 欄位則新增。"""
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(historical_data)")
        cols = [r[1] for r in cur.fetchall()]
        needed = [
        "open", "high", "low", "close", "volume",
        "open_time", "close_time", "quote_asset_volume", "num_trades", "taker_base_vol", "taker_quote_vol"
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
                default_api = get_default_api_url()
                cur.execute(f"ALTER TABLE historical_data ADD COLUMN api TEXT DEFAULT '{default_api}'")
            except Exception:
                pass
        conn.commit()
    except Exception as e:
        print(f"⚠️ schema 遷移失敗: {e}")


def query_ohlcv(category: str, symbol: str, interval: int, limit: int = 5): # (GEMINI 修正：新增 category 參數)
    """查詢最新資料"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 查詢完整 OHLCV 欄位
    # WHERE 條件句新增 category
    cur.execute(
        """
        SELECT timestamp, readable_time, category, symbol, interval,
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
