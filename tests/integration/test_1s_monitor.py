"""測試 1 秒監控是否持續寫入新資料（不使用 readable_time 欄位）"""
import os
import sys
from datetime import datetime, timezone, timedelta

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = CURRENT_DIR

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from modules.utils.database.db_core import query_ohlcv

symbol = "BTCUSDT"
rows = query_ohlcv('crypto', symbol, 1, limit=1)

if rows:
    ts, category, sym, interval, o, h, l, c, v = rows[0]
    tw_tz = timezone(timedelta(hours=8))
    ts_tw = datetime.fromtimestamp(ts, tz=tw_tz).strftime('%Y-%m-%d %H:%M:%S')

    print("最新一筆 1 秒 K 線:")
    print(f"  timestamp: {ts}")
    print(f"  台灣時間: {ts_tw} (UTC+8)")
    print(f"  symbol: {sym}")
    print(f"  interval: {interval}s")
    print(f"  open: {o}, high: {h}, low: {l}, close: {c}, volume: {v}")
    print(f"  完整資料: {rows[0]}")
else:
    print("❌ 無資料")
