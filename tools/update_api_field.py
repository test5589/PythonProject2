#!/usr/bin/env python3
"""
為現有資料補上 API 欄位值 https://api.binance.com
"""

import os
import sqlite3
from modules.utils.database import DB_PATH

def update_existing_data_api():
    """為所有現有資料設定 API 欄位為 https://api.binance.com"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 資料庫不存在: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # 檢查是否有 API 欄位
        cur.execute("PRAGMA table_info(historical_data)")
        cols = [r[1] for r in cur.fetchall()]
        
        if 'api' not in cols:
            print("❌ API 欄位不存在，請先執行 init_db() 進行結構遷移")
            conn.close()
            return
        
        # 更新所有 NULL 或空值 API 欄位
        cur.execute("""
            UPDATE historical_data 
            SET api = 'https://api.binance.com' 
            WHERE api IS NULL OR api = ''
        """)
        
        affected_rows = cur.rowcount
        conn.commit()
        
        print(f"✅ 已更新 {affected_rows} 筆資料的 API 欄位為 https://api.binance.com")
        
        # 檢查更新結果
        cur.execute("SELECT COUNT(*) FROM historical_data WHERE api = 'https://api.binance.com'")
        total_with_api = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM historical_data")
        total_records = cur.fetchone()[0]
        
        print(f"📊 資料庫狀態：總計 {total_records} 筆，其中 {total_with_api} 筆已設定 API")
        
    except Exception as e:
        print(f"❌ 更新失敗: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_existing_data_api()
