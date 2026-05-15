"""
auto_heal_core.py - 自動修補核心邏輯
實現智能修補和實時收集功能
"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Callable, Optional
from modules.utils.data.ws_aggregator import start_1s_aggregator, stop_1s_aggregator
from modules.utils.database import insert_data
from modules.utils.data.data_fetcher import fetch_klines
from .backfill_scanner import BackfillScanner

# 全局任務字典
_TASKS = {}

class AutoHealCore:
    """自動修補核心類"""
    
    def __init__(self):
        self.scanner = BackfillScanner()
        
    def interpolate_fill_1s_from_1m(self, category: str, symbol: str, start_ts: float, seconds: int = 900,
                                   emit: Callable[[str], None] = print, method: str = 'linear', 
                                   cancel_event: Optional[threading.Event] = None):
        """用 1 分鐘 K 線在指定區間做 1 秒內插"""
        sym = symbol.replace("/", "")
        # 轉毫秒
        start_ms = int(start_ts * 1000)
        end_ms = int((start_ts + seconds) * 1000)
        # 加邊界以涵蓋前後 minute 邊界
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
            """找到所在分鐘開頭與下一分鐘開頭"""
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
        before_cnt = self.scanner.count_rows(category, sym, start_ts, start_ts + seconds)
        
        # 轉換為台灣時間顯示
        tw = timezone(timedelta(hours=8))
        start_tw = datetime.fromtimestamp(start_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
        end_tw = datetime.fromtimestamp(start_ts + seconds, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
        emit(f"🕒 內插時間範圍: {start_tw} → {end_tw} (UTC+8)")
        
        emit(f"📦 內插時間段：{self.scanner.format_range(start_ts, start_ts + seconds)}（開始前已有 {before_cnt} 筆）")
        
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
                
            # 線性內插計算
            if m1 is not None:
                k1 = minutes_map.get(m1)
                span_ms = (m1 - m0)
                t = (sec_ms - m0) / span_ms if span_ms > 0 else 0.0
                c0 = float(k0['close'])
                c1 = float(k1['close'])
                close_val = c0 + (c1 - c0) * t if method == 'linear' else c0
            else:
                close_val = float(k0['close'])
                
            # 計算 OHLC 值
            if sec_ts == int(m0/1000):
                open_val = float(k0['open'])
            else:
                open_val = close_val_prev
                
            high_val = max(open_val, close_val)
            low_val = min(open_val, close_val)
            vol_per_sec = float(k0['volume']) / 60.0
            
            # 準備寫入資料
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
                # 每100筆輸出一次確認
                if idx % 100 == 0:
                    emit(f"✅ 內插寫入 {idx}/{seconds} data_source=interpolated")
            except Exception as e:
                emit(f"⚠️ 內插寫入失敗 @ {sec_ts}: {e}")
                
            close_val_prev = close_val
            
            # 每 10 秒輸出進度
            if idx % 10 == 0:
                try:
                    next_ts = sec_ts + 1
                    tw = timezone(timedelta(hours=8))
                    next_u8 = datetime.fromtimestamp(next_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                    remaining = int(start_ts + seconds - next_ts)
                    emit(f"⏳ 內插進度：{idx}/{seconds}，下一筆資料時間（UTC+8）{next_u8}，尚餘 {max(0, remaining)} 秒")
                except Exception:
                    pass
                    
        after_cnt = self.scanner.count_rows(category, sym, start_ts, start_ts + seconds)
        added = max(0, after_cnt - before_cnt)
        msg = f"✅ 內插完成：區間 {seconds} 秒；新增 {added} 筆，區間內總筆數 {after_cnt} 筆 data_source=interpolated"
        emit(msg)
        
        try:
            # 以區間起點作為前綴（UTC+8）
            tw = timezone(timedelta(hours=8))
            pfx = datetime.fromtimestamp(start_ts, tz=tw).strftime("[UTC+8 %Y-%m-%d %H:%M:%S] ")
            print(pfx + msg)
        except Exception:
            print(msg)
            
    def start_smart_auto_heal(self, category: str, symbol: str, emit: Callable[[str], None] = print,
                             minutes_interpolate: int = 15, minutes_realtime: int = 15):
        """啟動智能自動修補"""
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

        def runner():
            try:
                # 啟動前，確保沒有殘留的 WS 監控
                try:
                    stop_1s_aggregator(cat, sym)
                except Exception:
                    pass
                    
                # 迴圈重複內插，直到沒有過去缺口
                while not ev.is_set():
                    start_ts = self.scanner.find_earliest_incomplete_span(cat, sym, seconds=minutes_interpolate*60)
                    now_ts = time.time()
                    
                    if start_ts is None or start_ts >= now_ts - 2:
                        emit("✅ 所有過去缺口已補完，結束內插階段")
                        break
                        
                    # 估算剩餘區塊
                    remaining_blocks = 1
                    try:
                        total_gap_seconds = now_ts - start_ts
                        remaining_blocks = int((total_gap_seconds + minutes_interpolate*60 - 1) // (minutes_interpolate*60))
                    except Exception:
                        pass
                        
                    tw = timezone(timedelta(hours=8))
                    start_time_display = datetime.fromtimestamp(start_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                    emit(f"🧩 開始內插補齊 {minutes_interpolate} 分鐘：{start_time_display} (UTC+8)")
                    emit(f"⏳ 預估剩餘 {remaining_blocks} 個區塊，約需 {remaining_blocks * minutes_interpolate} 分鐘（可隨時按停止）")
                    
                    self.interpolate_fill_1s_from_1m(cat, sym, start_ts, seconds=minutes_interpolate*60, 
                                                   emit=emit, method='linear', cancel_event=ev)
                    
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
                before_cnt = self.scanner.count_rows(cat, sym, rt_start, rt_end_plan)
                
                emit(f"🛠 開始真實 1 秒收集 {minutes_realtime} 分鐘…時間段：{self.scanner.format_range(rt_start, rt_end_plan)}（開始前 {before_cnt} 筆）")
                
                _TASKS[sym]["realtime"] = True
                
                # 再次檢查是否已被要求停止
                if ev.is_set():
                    emit("⏹ 修補任務已停止")
                    return
                    
                start_1s_aggregator(cat, sym, emit)
                end_at = rt_end_plan
                
                while time.time() < end_at and not ev.is_set():
                    time.sleep(1)
                    
                stop_1s_aggregator(cat, sym)
                after_cnt = self.scanner.count_rows(cat, sym, rt_start, rt_end_plan)
                
                # 轉換時間範圍為台灣時間顯示
                tw = timezone(timedelta(hours=8))
                start_tw = datetime.fromtimestamp(rt_start, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                end_tw = datetime.fromtimestamp(rt_end_plan, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                
                emit(f"✅ 真實 1 秒收集結束：新增 {max(0, after_cnt - before_cnt)} 筆，區間內總筆數 {after_cnt} 筆 data_source=real")
                emit(f"🕒 時間範圍: {start_tw} → {end_tw} (UTC+8)")
                
            except Exception as e:
                emit(f"❌ 任務錯誤：{e}")
            finally:
                _TASKS.pop(sym, None)
                
        threading.Thread(target=runner, daemon=True).start()
        
    def stop_auto_heal(self, symbol: str, emit: Callable[[str], None] = print):
        """停止自動修補"""
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
        
    def start_realtime_only(self, category: str, symbol: str, minutes: int = 15, 
                           emit: Callable[[str], None] = print):
        """僅啟動實時收集"""
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

        def runner():
            try:
                rt_start = time.time()
                rt_end_plan = rt_start + minutes * 60
                before_cnt = self.scanner.count_rows(cat, sym, rt_start, rt_end_plan)
                
                # 啟動前，確保沒有殘留的 WS 監控
                try:
                    stop_1s_aggregator(cat, sym)
                except Exception:
                    pass
                    
                emit(f"🛠 僅啟動真實 1 秒收集 {minutes} 分鐘…時間段：{self.scanner.format_range(rt_start, rt_end_plan)}（開始前 {before_cnt} 筆）")
                
                start_1s_aggregator(cat, sym, emit)
                end_at = rt_end_plan
                
                while time.time() < end_at and not ev.is_set():
                    time.sleep(1)
                    
                stop_1s_aggregator(cat, sym)
                after_cnt = self.scanner.count_rows(cat, sym, rt_start, rt_end_plan)
                emit(f"✅ 真實 1 秒收集結束：新增 {max(0, after_cnt - before_cnt)} 筆，區間內總筆數 {after_cnt} 筆 data_source=real")
                
            except Exception as e:
                emit(f"❌ 任務錯誤：{e}")
            finally:
                _TASKS.pop(sym, None)
                
        threading.Thread(target=runner, daemon=True).start()

# 全域實例
_auto_heal_core = AutoHealCore()

# 向後相容性函數
def start_smart_auto_heal(category: str, symbol: str, emit: Callable[[str], None] = print,
                         minutes_interpolate: int = 15, minutes_realtime: int = 15):
    """啟動智能自動修補（向後相容性函數）"""
    return _auto_heal_core.start_smart_auto_heal(category, symbol, emit, minutes_interpolate, minutes_realtime)

def stop_auto_heal(symbol: str, emit: Callable[[str], None] = print):
    """停止自動修補（向後相容性函數）"""
    return _auto_heal_core.stop_auto_heal(symbol, emit)
