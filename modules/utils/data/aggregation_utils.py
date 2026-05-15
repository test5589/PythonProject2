"""
aggregation_utils.py - 多級別聚合工具
- 支援從 1 秒 real 資料優先聚合至 2/5/10/15/30 秒、1/2/5/10/15/30 分鐘、1/2/4/8/12 小時、1/3/7 天
- 若源資料包含 interpolated，則標記為 inferior-Aggregation；純 real 則標記為 Aggregation
- 提供檢查缺口、批次修補、進度回報
"""
import sqlite3
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional, List, Tuple, Dict
from modules.utils.database.db_core import DB_PATH
from modules.utils.database.data_manager import insert_data

# 聚合任務管理
_AGG_TASKS = {}  # {symbol: {"ev": threading.Event, "thread": threading.Thread}}

# 定義所有聚合級別（秒）
AGG_INTERVALS = [
    # 秒
    2, 5, 10, 15, 30,
    # 分鐘
    60, 120, 300, 600, 900, 1800,
    # 小時
    3600, 7200, 14400, 28800, 43200,
    # 天
    86400, 259200, 604800
]

def _interval_name(sec: int) -> str:
    """把秒數轉為可讀名稱，例如 30s、5m、1h、1d"""
    if sec < 60:
        return f"{sec}s"
    elif sec < 3600:
        return f"{sec//60}m"
    elif sec < 86400:
        return f"{sec//3600}h"
    else:
        return f"{sec//86400}d"

def _count_rows(category: str, symbol: str, start_ts: float, end_ts: float, interval: int) -> int:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM historical_data
            WHERE category=? AND symbol=? AND interval=? AND timestamp>=? AND timestamp<?
            """,
            (category, symbol.replace('/', ''), interval, start_ts, end_ts)
        )
        n = cur.fetchone()[0] or 0
        conn.close()
        return int(n)
    except Exception:
        return 0

def _fetch_source_rows(category: str, symbol: str, start_ts: float, end_ts: float, source_interval: int = 1) -> List[dict]:
    """抓取指定時間範圍內的源資料（預設 1 秒），回傳 list of dict"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp, open, high, low, close, volume,
                   open_time, close_time, quote_asset_volume,
                   num_trades, taker_base_vol, taker_quote_vol,
                   data_source, interp_note
            FROM historical_data
            WHERE category=? AND symbol=? AND interval=? AND timestamp>=? AND timestamp<?
            ORDER BY timestamp
            """,
            (category, symbol.replace('/', ''), source_interval, start_ts, end_ts)
        )
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "timestamp": r[0],
                "open": r[1], "high": r[2], "low": r[3], "close": r[4], "volume": r[5],
                "open_time": r[6], "close_time": r[7], "quote_asset_volume": r[8],
                "num_trades": r[9], "taker_base_vol": r[10], "taker_quote_vol": r[11],
                "data_source": r[12] or "real",
                "interp_note": r[13]
            }
            for r in rows
        ]
    except Exception as e:
        return []

def _aggregate_one_bucket(rows: List[dict], target_interval: int) -> dict:
    """將多筆 1 秒資料聚合成一筆 target_interval 的 K 線"""
    if not rows:
        return {}
    # OHLCV
    opens = [r["open"] for r in rows if r["open"] is not None]
    highs = [r["high"] for r in rows if r["high"] is not None]
    lows = [r["low"] for r in rows if r["low"] is not None]
    closes = [r["close"] for r in rows if r["close"] is not None]
    volumes = [r["volume"] for r in rows if r["volume"] is not None]
    # 聚合規則
    open_val = opens[0] if opens else None
    high_val = max(highs) if highs else None
    low_val = min(lows) if lows else None
    close_val = closes[-1] if closes else None
    volume_val = sum(volumes) if volumes else 0.0
    # 其他欄位：取第一筆的 open_time，最後一筆的 close_time
    first = rows[0]
    last = rows[-1]
    agg = {
        "open_time": first["open_time"],
        "close_time": last["close_time"],
        "open": open_val,
        "high": high_val,
        "low": low_val,
        "close": close_val,
        "volume": volume_val,
        "quote_asset_volume": sum(r["quote_asset_volume"] or 0 for r in rows),
        "num_trades": sum(r["num_trades"] or 0 for r in rows),
        "taker_base_vol": sum(r["taker_base_vol"] or 0 for r in rows),
        "taker_quote_vol": sum(r["taker_quote_vol"] or 0 for r in rows)
    }
    # 來源標記：若源資料全為 real 則為 Aggregation，否則為 inferior-Aggregation
    if any(r["data_source"] != "real" for r in rows):
        agg["data_source"] = "inferior-Aggregation"
        agg["interp_note"] = "mixed_or_interpolated_source"
    else:
        agg["data_source"] = "Aggregation"
        agg["interp_note"] = None
    return agg

def scan_missing_intervals(category: str, symbol: str, intervals: List[int] = None,
                           lookback_days: int = 7, emit: Callable[[str], None] = print) -> Dict[int, Tuple[int, int, int]]:
    """
    掃描多級別的缺口，回傳 {interval: (gap_count, total_expected, existing_count)}
    """
    if intervals is None:
        intervals = AGG_INTERVALS
    results = {}
    now_ts = time.time()
    start_ts = now_ts - lookback_days * 86400
    for sec in intervals:
        expected = int((now_ts - start_ts) // sec)
        existing = _count_rows(category, symbol, start_ts, now_ts, sec)
        gap = max(0, expected - existing)
        results[sec] = (gap, expected, existing)
        emit(f"🔍 {_interval_name(sec)}: 預期 {expected} 筆，實際 {existing} 筆，缺口 {gap} 筆")
    return results

def aggregate_range(category: str, symbol: str, target_interval: int,
                     start_ts: float, end_ts: float,
                     emit: Callable[[str], None] = print,
                     cancel_event: Optional[threading.Event] = None) -> int:
    """
    在指定時間範圍內，從 1 秒資料聚合到 target_interval
    回傳實際新增筆數
    """
    # 檢查源資料（1 秒）是否足夠
    source_rows = _fetch_source_rows(category, symbol, start_ts, end_ts, source_interval=1)
    if not source_rows:
        emit(f"⚠️ 無 1 秒源資料於區間 {_fmt_range(start_ts, end_ts)}，跳過聚合")
        return 0
    # 按 bucket 分組
    bucket_map = {}
    for r in source_rows:
        ts = r["timestamp"]
        bucket_key = int(ts // target_interval) * target_interval
        bucket_map.setdefault(bucket_key, []).append(r)
    # 準備聚合與寫入
    added = 0
    total_buckets = len(bucket_map)
    for idx, (bucket_ts, bucket_rows) in enumerate(sorted(bucket_map.items()), start=1):
        if cancel_event and cancel_event.is_set():
            emit("⏹ 已停止聚合作業")
            return added
        agg = _aggregate_one_bucket(bucket_rows, target_interval)
        if not agg:
            continue
        # 設定 open_time/close_time 對應 bucket
        agg["open_time"] = int(bucket_ts * 1000)
        agg["close_time"] = int((bucket_ts + target_interval) * 1000)
        try:
            insert_data(category, symbol, target_interval, agg,
                        data_source=agg["data_source"], interp_note=agg["interp_note"])
            added += 1
            # 每 10 個 bucket 提示進度並顯示 data_source
            if idx % 10 == 0 or idx == total_buckets:
                emit(f"✅ 聚合寫入 {idx}/{total_buckets} data_source={agg['data_source']}")
        except Exception as e:
            emit(f"⚠️ 聚合寫入失敗 @ {bucket_ts}: {e}")
        # 每 10 個 bucket 提示進度
        if idx % 10 == 0 or idx == total_buckets:
            try:
                tw = timezone(timedelta(hours=8))
                next_ts = bucket_ts + target_interval
                next_u8 = datetime.fromtimestamp(next_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                remaining = total_buckets - idx
                emit(f"⏳ 聚合進度：{idx}/{total_buckets}，下一筆區間（UTC+8）{next_u8}，尚餘 {remaining} 區塊")
            except Exception:
                pass
    emit(f"✅ 聚合完成：{_interval_name(target_interval)} 級別；新增 {added} 筆 (Aggregation 或 inferior-Aggregation)")
    return added

def _fmt_range(start_ts: float, end_ts: float) -> str:
    try:
        tw = timezone(timedelta(hours=8))
        s8 = datetime.fromtimestamp(start_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
        e8 = datetime.fromtimestamp(end_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
        su = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        eu = datetime.fromtimestamp(end_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
        return f"[UTC+8 {s8} ~ {e8}) / [UTC {su} ~ {eu})"
    except Exception:
        return f"[{start_ts} ~ {end_ts})"

def batch_aggregate_missing(category: str, symbol: str,
                            intervals: List[int] = None,
                            lookback_days: int = 7,
                            emit: Callable[[str], None] = print,
                            cancel_event: Optional[threading.Event] = None) -> Dict[int, int]:
    """
    批次聚合所有缺少的區塊（依 intervals 順序由小到大）
    回傳 {interval: added_count}
    """
    if intervals is None:
        intervals = AGG_INTERVALS
    results = {}
    now_ts = time.time()
    start_ts = now_ts - lookback_days * 86400
    for sec in intervals:
        if cancel_event and cancel_event.is_set():
            emit("⏹ 批次聚合已取消")
            break
        # 檢查缺口
        existing = _count_rows(category, symbol, start_ts, now_ts, sec)
        expected = int((now_ts - start_ts) // sec)
        if existing >= expected:
            emit(f"✅ {_interval_name(sec)} 已完整，跳過聚合")
            results[sec] = 0
            continue
        emit(f"🔧 開始聚合 {_interval_name(sec)} 級別，目標區間 {_fmt_range(start_ts, now_ts)}")
        added = aggregate_range(category, symbol, sec, start_ts, now_ts, emit=emit, cancel_event=cancel_event)
        results[sec] = added
    emit("🏁 批次聚合完成")
    return results

def start_batch_aggregate_with_task(category: str, symbol: str,
                                    intervals: List[int] = None,
                                    lookback_days: int = 7,
                                    emit: Callable[[str], None] = print):
    """啟動可取消的批次聚合任務（支援 GUI 停止）"""
    key = f"{category}:{symbol.replace('/', '')}"
    if key in _AGG_TASKS:
        emit("⚠️ 聚合任務已在執行中")
        return
    ev = threading.Event()
    _AGG_TASKS[key] = {"ev": ev, "thread": None}
    def _runner():
        try:
            batch_aggregate_missing(category, symbol, intervals=intervals, lookback_days=lookback_days, emit=emit, cancel_event=ev)
        except Exception as e:
            emit(f"❌ 聚合任務錯誤：{e}")
        finally:
            _AGG_TASKS.pop(key, None)
    t = threading.Thread(target=_runner, daemon=True)
    _AGG_TASKS[key]["thread"] = t
    t.start()

def stop_batch_aggregate(category: str, symbol: str, emit: Callable[[str], None] = print):
    """停止批次聚合任務"""
    key = f"{category}:{symbol.replace('/', '')}"
    task = _AGG_TASKS.get(key)
    if not task:
        emit("ℹ️ 無執行中的聚合任務")
        return
    task["ev"].set()
    emit("⏹ 已請求停止聚合任務")
