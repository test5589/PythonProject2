"""
自動修補 15 分鐘（1秒級別）
限制說明：Binance REST 不提供歷史 1 秒 K 線，故此功能以 WebSocket 即時聚合為主，
從啟動當下往後收集 15 分鐘的 1 秒資料並寫入資料庫。
此外，提供資料庫掃描：在最近一段時間檢查缺漏（時間缺口、欄位缺漏）。
"""
import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional, Tuple
import sqlite3

from modules.utils.ws_aggregator import start_1s_aggregator, stop_1s_aggregator
from modules.utils.database import DB_PATH, insert_data
from modules.utils.data_fetcher import fetch_klines

_TASKS = {}

def _count_rows(category: str, symbol: str, start_ts: float, end_ts: float) -> int:
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*) FROM historical_data
            WHERE category=? AND symbol=? AND interval=1 AND timestamp>=? AND timestamp<?
            """,
            (category, symbol.replace('/', ''), start_ts, end_ts)
        )
        n = cur.fetchone()[0] or 0
        conn.close()
        return int(n)
    except Exception:
        return 0

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


def scan_incomplete_seconds(category: str, symbol: str, lookback_minutes: int = 60) -> Tuple[int, int, int]:
    """
    掃描最近 lookback_minutes 分鐘的 1 秒級別資料，偵測：
    - 時間缺口（相鄰樣本 > 1.5 秒）
    - 欄位缺漏（open/high/low/close/volume 存在 None）

    :return: (gap_count, bad_rows, total_rows)
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        now_ts = time.time()
        start_ts = now_ts - lookback_minutes * 60
        cur.execute(
            """
            SELECT timestamp, open, high, low, close, volume
            FROM historical_data
            WHERE category=? AND symbol=? AND interval=? AND timestamp>=?
            ORDER BY timestamp
            """,
            (category, symbol.replace("/", ""), 1, start_ts)
        )
        rows = cur.fetchall()
        conn.close()
        gap = 0
        bad = 0
        last_ts = None
        for r in rows:
            ts, o, h, l, c, v = r
            if o is None or h is None or l is None or c is None or v is None:
                bad += 1
            if last_ts is not None and (ts - last_ts) > 1.5:
                gap += 1
            last_ts = ts
        return gap, bad, len(rows)
    except Exception:
        return 0, 0, 0


def auto_heal_15m_1s(category: str, symbol: str, emit: Callable[[str], None] = print, minutes: int = 15,
                      lookback_minutes: int = 60):
    """
    啟動 1 秒即時聚合，持續 minutes 分鐘後自動停止；啟動前先掃描最近資料的缺漏情況。
    :param category: 資產分類（例如 crypto）
    :param symbol:   交易對（例如 BTCUSDT 或 BTC/USDT，內部會統一處理）
    :param emit:     日誌輸出函式
    :param minutes:  預設 15 分鐘
    :param lookback_minutes: 掃描 DB 的時間範圍（預設 60 分鐘）
    """
    if not category:
        category = "crypto"
    sym = (symbol or "").strip()
    if not sym:
        emit("❌ 請輸入交易對，例如 BTCUSDT")
        return

    # 掃描資料庫現況
    gap, bad, total = scan_incomplete_seconds(category, sym, lookback_minutes=lookback_minutes)
    emit(f"🔎 掃描結果（最近{lookback_minutes}分）：記錄 {total} 筆，缺口 {gap}，不完整列 {bad}")
    emit(f"🛠 自動修補 1秒資料啟動：{sym}，持續 {minutes} 分鐘（向未來補齊）")

    def _run():
        try:
            start_1s_aggregator(category, sym, emit)
            t_end = time.time() + minutes * 60
            while time.time() < t_end:
                time.sleep(1)
            stop_1s_aggregator(category, sym)
            emit(f"✅ 自動修補完成（{minutes} 分鐘）：{sym}")
        except Exception as e:
            emit(f"❌ 自動修補發生錯誤：{e}")

    threading.Thread(target=_run, daemon=True).start()


# ---- A：尋找最早缺口，並用 1m → 1s 內插補齊（可重複、可驗證）----
def find_earliest_incomplete_span(category: str, symbol: str, seconds: int = 900) -> Optional[float]:
    """
    尋找最早的『不完整或有缺口』的 1 秒區段起點（秒級 timestamp）。
    規則：
    - 欄位缺漏 open/high/low/close/volume 任一為 NULL
    - 或相鄰樣本間隔 > 1.5 秒
    回傳該段起點 timestamp（秒）。若找不到，回傳 None。
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT timestamp, open, high, low, close, volume
            FROM historical_data
            WHERE category=? AND symbol=? AND interval=1
            ORDER BY timestamp ASC
            """,
            (category, symbol.replace("/", ""))
        )
        rows = cur.fetchall()
        conn.close()
        last_ts = None
        for r in rows:
            ts, o, h, l, c, v = r
            if o is None or h is None or l is None or c is None or v is None:
                return ts
            if last_ts is not None and (ts - last_ts) > 1.5:
                # 缺口從 last_ts 後一秒開始
                return last_ts + 1
            last_ts = ts
        return None
    except Exception:
        return None


def interpolate_fill_1s_from_1m(category: str, symbol: str, start_ts: float, seconds: int = 900,
                                 emit: Callable[[str], None] = print, method: str = 'linear', cancel_event: Optional[threading.Event] = None):
    """
    用 1 分鐘 K 線在 [start_ts, start_ts+seconds) 區間做 1 秒內插，寫入 DB。
    - 資料來源：即時抓取的 1m REST（不造假時間點）
    - 可重複、可驗證：演算法完全決定且依賴 1m 收到的原始值 → 同樣時段重跑結果一致
    - 寫入時標記 data_source='interpolated', interp_note='from_1m_linear'
    - 不覆蓋現有 real；若該秒已有 real 則跳過；若已有 interpolated 再跑一樣的演算法值一致，REPLACE 不會變
    """
    sym = symbol.replace("/", "")
    # 轉毫秒
    start_ms = int(start_ts * 1000)
    end_ms = int((start_ts + seconds) * 1000)
    # 加一些邊界以涵蓋前後 minute 邊界
    fetch_start_ms = start_ms - 60_000
    fetch_end_ms = end_ms + 60_000
    try:
        kl_1m = fetch_klines(sym, '1m', fetch_start_ms, fetch_end_ms, limit=1000)
    except Exception as e:
        emit(f"❌ 取得 1m K 線失敗：{e}")
        return
    if not kl_1m:
        emit("⚠️ 沒取得任何 1m K 線，跳過內插")
        return
    # 依 open_time 排序
    kl_1m.sort(key=lambda k: k['open_time'])
    # 建立每分鐘界線的對應
    minutes_map = {k['open_time']: k for k in kl_1m}
    minute_keys = sorted(minutes_map.keys())

    def find_neighbor_minutes(ms: int):
        # 找到所在分鐘開頭與下一分鐘開頭
        # 每根 1m: [open_time, close_time)
        # 將 ms 所在的分鐘頭找出
        import bisect
        i = bisect.bisect_right(minute_keys, ms) - 1
        if i < 0:
            return None, None
        m0 = minute_keys[i]
        m1 = minute_keys[i+1] if i+1 < len(minute_keys) else None
        return m0, m1

    # 逐秒生成
    last_minute_head = None
    close_val_prev = None
    before_cnt = _count_rows(category, sym, start_ts, start_ts + seconds)
    emit(f"📦 內插時間段：{_fmt_range(start_ts, start_ts + seconds)}（開始前已有 {before_cnt} 筆）")
    for idx, sec_ts in enumerate(range(int(start_ts), int(start_ts + seconds)), start=1):
        if cancel_event and cancel_event.is_set():
            emit("⏹ 已停止內插作業")
            return
        sec_ms = sec_ts * 1000
        m0, m1 = find_neighbor_minutes(sec_ms)
        if m0 is None:
            continue
        k0 = minutes_map.get(m0)
        # 若換到新的一分鐘，將上一秒收斂值初始化為該分鐘的 open
        if last_minute_head != m0:
            close_val_prev = float(k0['open'])
            last_minute_head = m0
        # 線性目標：使用 minute 收到的 open/close 作為端點，簡化且可重現
        # 取得下一分鐘以計算跨界線段；若沒有下一分鐘，使用本分鐘 close 作為固定值
        if m1 is not None:
            k1 = minutes_map.get(m1)
            span_ms = (m1 - m0)
            t = (sec_ms - m0) / span_ms if span_ms > 0 else 0.0
            # 線性內插 close；open 取前一秒 close；高低由 open/close 決定
            c0 = float(k0['close']); c1 = float(k1['close'])
            close_val = c0 + (c1 - c0) * t if method == 'linear' else c0
        else:
            close_val = float(k0['close'])
        # open 取上一秒生成值（或 minute open 作為第一秒起點）
        # 為了可重現，第一秒使用 k0['open']，之後每秒 open=前一秒 close
        if sec_ts == int(m0/1000):
            open_val = float(k0['open'])
        else:
            open_val = close_val_prev  # 由上一輪保存
        high_val = max(open_val, close_val)
        low_val = min(open_val, close_val)
        # 均勻分配本分鐘的量到 60 秒（可重現）
        vol_per_sec = float(k0['volume']) / 60.0
        # 準備寫入
        kline_1s = {
            'open_time': sec_ms,
            'close_time': sec_ms + 1000,
            'open': open_val,
            'high': high_val,
            'low': low_val,
            'close': close_val,
            'volume': vol_per_sec,
            'quote_asset_volume': 0.0,
            'num_trades': 0,
            'taker_base_vol': 0.0,
            'taker_quote_vol': 0.0,
        }
        try:
            insert_data(category, sym, 1, kline_1s, data_source='interpolated', interp_note='from_1m_linear')
        except Exception as e:
            emit(f"⚠️ 內插寫入失敗 @ {sec_ts}: {e}")
        close_val_prev = close_val
        # 每 10 秒輸出一次進度與下一筆資料時間提示
        if idx % 10 == 0:
            try:
                next_ts = sec_ts + 1
                tw = timezone(timedelta(hours=8))
                next_u8 = datetime.fromtimestamp(next_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                remaining = int(start_ts + seconds - next_ts)
                emit(f"⏳ 內插進度：{idx}/{seconds}，下一筆資料時間（UTC+8）{next_u8}，尚餘 {max(0, remaining)} 秒")
            except Exception:
                pass
    after_cnt = _count_rows(category, sym, start_ts, start_ts + seconds)
    added = max(0, after_cnt - before_cnt)
    msg = f"✅ 內插完成：區間 {seconds} 秒；新增 {added} 筆，區間內總筆數 {after_cnt} 筆"
    emit(msg)
    try:
        # 以區間起點作為前綴（UTC+8）
        tw = timezone(timedelta(hours=8))
        pfx = datetime.fromtimestamp(start_ts, tz=tw).strftime("[UTC+8 %Y-%m-%d %H:%M:%S] ")
        print(pfx + msg)
    except Exception:
        print(msg)


def smart_auto_heal_15m(category: str, symbol: str, emit: Callable[[str], None] = print,
                         minutes_interpolate: int = 15, minutes_realtime: int = 15):
    """
    智能自動修補：
    1) 先找最早 15 分鐘缺口/不完整，若存在且在過去 → A: 以 1m→1s 內插回補（標記 interpolated）
       - 重複執行結果一致；若未來有真實 1s，因 insert_data 規則會覆蓋內插為 real
    2) 接著 B: 從現在起啟動 1 秒聚合 minutes_realtime 分鐘，寫入 real
    """
    cat = category or 'crypto'
    sym = (symbol or '').replace('/', '')
    if not sym:
        emit("❌ 請輸入交易對，例如 BTCUSDT")
        return
    start_ts = find_earliest_incomplete_span(cat, sym, seconds=minutes_interpolate*60)
    now_ts = time.time()
    if start_ts is not None and start_ts < now_ts - 2:  # 在過去
        emit(f"🧩 發現最早缺口：{datetime.fromtimestamp(start_ts, tz=timezone.utc)}，先以 1m→1s 補 {minutes_interpolate} 分鐘…")
        interpolate_fill_1s_from_1m(cat, sym, start_ts, seconds=minutes_interpolate*60, emit=emit, method='linear')
    else:
        emit("✅ 未發現過去缺口或缺口在當前，跳過內插階段")
    # 再啟動真實 1 秒收集
    emit(f"🛠 開始真實 1 秒收集 {minutes_realtime} 分鐘…將於 {minutes_realtime} 分鐘後自動停止")
    def _run_real():
        try:
            start_1s_aggregator(cat, sym, emit)
            t_end = time.time() + minutes_realtime * 60
            # 開始時提示具體停止時間
            try:
                tw = timezone(timedelta(hours=8))
                t_end_u8 = datetime.fromtimestamp(t_end, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                t_end_u = datetime.fromtimestamp(t_end, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                emit(f"⏳ 預計停止時間：[UTC+8 {t_end_u8}] / [UTC {t_end_u}]")
            except Exception:
                pass
            last_report = 0
            while time.time() < t_end:
                time.sleep(1)
                # 每 30 秒輸出一次剩餘時間
                now = time.time()
                if int(now - last_report) >= 30:
                    remaining = int(max(0, t_end - now))
                    try:
                        tw = timezone(timedelta(hours=8))
                        t_end_u8 = datetime.fromtimestamp(t_end, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                        emit(f"⏳ 真實收集進行中：尚餘 {remaining} 秒，預計停止（UTC+8）{t_end_u8}")
                    except Exception:
                        emit(f"⏳ 真實收集進行中：尚餘 {remaining} 秒")
                    last_report = now
            stop_1s_aggregator(cat, sym)
            emit("✅ 真實 1 秒收集完成")
        except Exception as e:
            emit(f"❌ 真實 1 秒收集錯誤：{e}")
    threading.Thread(target=_run_real, daemon=True).start()


def start_smart_auto_heal(category: str, symbol: str, emit: Callable[[str], None] = print,
                          minutes_interpolate: int = 15, minutes_realtime: int = 15):
    cat = category or 'crypto'
    sym = (symbol or '').replace('/', '')
    if not sym:
        emit("❌ 請輸入交易對，例如 BTCUSDT")
        return
    if sym in _TASKS:
        emit("⚠️ 修補任務已在執行中")
        return
    ev = threading.Event()
    _TASKS[sym] = {"ev": ev, "realtime": False, "category": cat}

    def _runner():
        try:
            # 啟動前，確保沒有殘留的 WS 監控
            try:
                stop_1s_aggregator(cat, sym)
            except Exception:
                pass
            # 迴圈重複內插，直到沒有過去缺口
            while not ev.is_set():
                start_ts = find_earliest_incomplete_span(cat, sym, seconds=minutes_interpolate*60)
                now_ts = time.time()
                if start_ts is None or start_ts >= now_ts - 2:
                    emit("✅ 所有過去缺口已補完，結束內插階段")
                    break
                # 估算剩餘區塊與預計時間（粗略：每區塊 15 分鐘）
                remaining_blocks = 1  # 簡化：先提示至少還有一塊
                try:
                    # 簡易估算：從最早缺口到現在的總秒數，除以區塊大小
                    total_gap_seconds = now_ts - start_ts
                    remaining_blocks = int((total_gap_seconds + minutes_interpolate*60 - 1) // (minutes_interpolate*60))
                except Exception:
                    pass
                emit(f"🧩 開始內插補齊 {minutes_interpolate} 分鐘：{datetime.fromtimestamp(start_ts, tz=timezone.utc)}")
                emit(f"⏳ 預估剩餘 {remaining_blocks} 個區塊，約需 {remaining_blocks * minutes_interpolate} 分鐘（可隨時按停止）")
                interpolate_fill_1s_from_1m(cat, sym, start_ts, seconds=minutes_interpolate*60, emit=emit, method='linear', cancel_event=ev)
                if ev.is_set():
                    emit("⏹ 修補任務已停止")
                    return
                emit("🔄 檢查下一個過去缺口…")
            if ev.is_set():
                emit("⏹ 修補任務已停止")
                return
            # 即時收集統計
            rt_start = time.time()
            rt_end_plan = rt_start + minutes_realtime * 60
            before_cnt = _count_rows(cat, sym, rt_start, rt_end_plan)
            emit(f"🛠 開始真實 1 秒收集 {minutes_realtime} 分鐘…時間段：{_fmt_range(rt_start, rt_end_plan)}（開始前 {before_cnt} 筆）")
            _TASKS[sym]["realtime"] = True
            # 再次檢查是否已被要求停止，避免在停止後仍啟動 WS
            if ev.is_set():
                emit("⏹ 修補任務已停止")
                return
            start_1s_aggregator(cat, sym, emit)
            end_at = rt_end_plan
            while time.time() < end_at and not ev.is_set():
                time.sleep(1)
            stop_1s_aggregator(cat, sym)
            after_cnt = _count_rows(cat, sym, rt_start, rt_end_plan)
            emit(f"✅ 真實 1 秒收集結束：新增 {max(0, after_cnt - before_cnt)} 筆，區間內總筆數 {after_cnt} 筆")
        except Exception as e:
            emit(f"❌ 任務錯誤：{e}")
        finally:
            _TASKS.pop(sym, None)
    threading.Thread(target=_runner, daemon=True).start()


def stop_auto_heal(symbol: str, emit: Callable[[str], None] = print):
    sym = (symbol or '').replace('/', '')
    t = _TASKS.get(sym)
    if not t:
        emit("ℹ️ 無執行中的修補任務")
        return
    t["ev"].set()
    try:
        # 無論是否處於即時階段，一律嘗試停止 WS
        stop_1s_aggregator(t.get("category") or 'crypto', sym)
    except Exception:
        pass
    emit("⏹ 已要求停止修補")


def start_realtime_only(category: str, symbol: str, minutes: int = 15, emit: Callable[[str], None] = print):
    cat = category or 'crypto'
    sym = (symbol or '').replace('/', '')
    if not sym:
        emit("❌ 請輸入交易對，例如 BTCUSDT")
        return
    if sym in _TASKS:
        emit("⚠️ 修補任務已在執行中")
        return
    ev = threading.Event()
    _TASKS[sym] = {"ev": ev, "realtime": True, "category": cat}

    def _runner():
        try:
            rt_start = time.time()
            rt_end_plan = rt_start + minutes * 60
            before_cnt = _count_rows(cat, sym, rt_start, rt_end_plan)
            # 啟動前，確保沒有殘留的 WS 監控
            try:
                stop_1s_aggregator(cat, sym)
            except Exception:
                pass
            emit(f"🛠 僅啟動真實 1 秒收集 {minutes} 分鐘…時間段：{_fmt_range(rt_start, rt_end_plan)}（開始前 {before_cnt} 筆）")
            start_1s_aggregator(cat, sym, emit)
            end_at = rt_end_plan
            while time.time() < end_at and not ev.is_set():
                time.sleep(1)
            stop_1s_aggregator(cat, sym)
            after_cnt = _count_rows(cat, sym, rt_start, rt_end_plan)
            emit(f"✅ 真實 1 秒收集結束：新增 {max(0, after_cnt - before_cnt)} 筆，區間內總筆數 {after_cnt} 筆")
        except Exception as e:
            emit(f"❌ 任務錯誤：{e}")
        finally:
            _TASKS.pop(sym, None)
    threading.Thread(target=_runner, daemon=True).start()
