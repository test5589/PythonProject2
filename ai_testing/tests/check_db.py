import sqlite3
import os

db_path = "data/system_data.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print("資料庫 Tables:", tables)
    # 檢查 historical_data 是否存在
    if ('historical_data',) in tables:
        print("historical_data table 存在")
        columns = conn.execute("PRAGMA table_info(historical_data)").fetchall()
        print("Columns:", columns)
    else:
        print("historical_data table 不存在")
    conn.close()
else:
    print("資料庫檔案不存在:", db_path)
