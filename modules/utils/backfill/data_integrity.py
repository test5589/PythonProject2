"""data_integrity.py - 檢查資料庫缺漏範圍 (for backfill use)"""

import sqlite3, os, time

from datetime import datetime, timezone

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "system_data.db"))

def get_missing_ranges(category, symbol, interval, max_gap=600):
    """回傳缺口 [(start_ts, end_ts), …]，interval單位秒"""
    if not os.path.exists(DB_PATH):
        now = time.time();  return [(now - 86400, now)]
    conn = sqlite3.connect(DB_PATH); cur = conn.cursor()
    cur.execute("""SELECT timestamp FROM historical_data
                   WHERE category=? AND symbol=? AND interval=? ORDER BY timestamp""",
                (category, symbol, interval))
    rows = [r[0] for r in cur.fetchall()]; conn.close()
    if len(rows) < 2:  now = time.time();  return [(now - 86400, now)]
    gaps=[]; last=rows[0]
    for ts in rows[1:]:
        if ts-last > max_gap: gaps.append((last, ts))
        last = ts
    return gaps

