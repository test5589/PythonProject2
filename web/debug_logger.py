"""
Streamlit 除錯日誌模組
- 記錄使用者選擇的參數
- 記錄資料庫查詢過程
- 記錄錯誤原因
"""
import os
import sqlite3
from datetime import datetime, timezone, timedelta
import pandas as pd

# 模組版本（寫入日誌以確認是否已載入新版本）
VERSION = "2025-11-11-18:00"

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "streamlit_debug.log")

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

def write_debug_log(message: str):
    """寫入除錯日誌"""
    ensure_log_dir()
    taipei_tz = timezone(timedelta(hours=8))
    timestamp = datetime.now(tz=taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

def debug_load_data(symbol: str, interval: int, start_ts: float, end_ts: float):
    """除錯版本的 load_data，記錄詳細過程"""
    # 再次確保 pandas 可用（避免某些環境快取造成 NameError）
    try:
        import pandas as pd  # noqa: F401
    except Exception as _e:
        write_debug_log(f"❌ 錯誤: 無法匯入 pandas：{_e}")
        return None, f"無法匯入 pandas：{_e}"

    taipei_tz = timezone(timedelta(hours=8))
    start_readable = datetime.fromtimestamp(start_ts, tz=taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
    end_readable = datetime.fromtimestamp(end_ts, tz=taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
    
    write_debug_log(f"=== 開始載入資料 === [debug_logger {VERSION}]")
    write_debug_log(f"交易對: {symbol}")
    write_debug_log(f"級別: {interval}秒")
    write_debug_log(f"開始時間: {start_readable} (UTC+8) | 時間戳: {start_ts}")
    write_debug_log(f"結束時間: {end_readable} (UTC+8) | 時間戳: {end_ts}")
    
    # 檢查資料庫檔案
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "system_data.db"))
    write_debug_log(f"資料庫路徑: {db_path}")
    write_debug_log(f"資料庫存在: {os.path.exists(db_path)}")
    
    if not os.path.exists(db_path):
        write_debug_log("❌ 錯誤: 資料庫檔案不存在")
        return None, "資料庫檔案不存在"
    
    try:
        conn = sqlite3.connect(db_path)
        write_debug_log("✅ 資料庫連線成功")
        
        # 檢查 table 是否存在
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historical_data'")
        table_exists = cursor.fetchone()
        write_debug_log(f"historical_data table 存在: {table_exists is not None}")
        
        if not table_exists:
            write_debug_log("❌ 錯誤: historical_data table 不存在")
            conn.close()
            return None, "historical_data table 不存在"
        
        # 執行查詢
        query = """
            SELECT timestamp, open, high, low, close, volume,
                   data_source, interp_note
            FROM historical_data
            WHERE symbol=? AND interval=? AND timestamp>=? AND timestamp<?
            ORDER BY timestamp
        """
        write_debug_log(f"執行查詢: {query.strip()}")
        write_debug_log(f"參數: ({symbol}, {interval}, {start_ts}, {end_ts})")
        
        df = pd.read_sql_query(query, conn, params=(symbol, interval, start_ts, end_ts))
        conn.close()
        
        write_debug_log(f"✅ 查詢成功，取得 {len(df)} 筆資料")
        
        if len(df) == 0:
            # 檢查是否有該交易對的任何資料
            conn = sqlite3.connect(db_path)
            count = conn.execute("SELECT COUNT(*) FROM historical_data WHERE symbol=?", (symbol,)).fetchone()[0]
            write_debug_log(f"資料庫中 {symbol} 總筆數: {count}")
            
            if count == 0:
                write_debug_log("⚠️ 警告: 資料庫中沒有該交易對的任何資料")
            else:
                # 檢查時間範圍
                min_ts = conn.execute("SELECT MIN(timestamp) FROM historical_data WHERE symbol=?", (symbol,)).fetchone()[0]
                max_ts = conn.execute("SELECT MAX(timestamp) FROM historical_data WHERE symbol=?", (symbol,)).fetchone()[0]
                min_readable = datetime.fromtimestamp(min_ts, tz=taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
                max_readable = datetime.fromtimestamp(max_ts, tz=taipei_tz).strftime("%Y-%m-%d %H:%M:%S")
                write_debug_log(f"{symbol} 資料時間範圍: {min_readable} ~ {max_readable}")
                write_debug_log(f"查詢範圍: {start_readable} ~ {end_readable}")
                if start_ts > max_ts or end_ts < min_ts:
                    write_debug_log("❌ 錯誤: 查詢時間範圍不在資料範圍內")
            conn.close()
        
        return df, None
        
    except Exception as e:
        write_debug_log(f"❌ 錯誤: {str(e)}")
        return None, str(e)

def get_debug_log_content():
    """取得除錯日誌內容"""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return "尚無除錯日誌"
