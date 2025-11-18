"""
ws_aggregator.py - 透過 Binance WebSocket 聚合 1 秒 OHLCV，寫入 database
"""
import json
import threading
import time
from datetime import datetime, timezone, timedelta

from websocket import WebSocketApp

from modules.utils.database.data_manager import insert_data
from modules.utils.logger import get_logger

logger = get_logger("ws_1s")


class _WS1sAggregator:
    def __init__(self, category: str, symbol: str, progress_cb=None):
        # Binance 要求 symbol 無斜線且小寫於路徑
        self.category = category
        self.symbol = symbol.replace("/", "").upper()
        self.ws_url = f"wss://stream.binance.com:9443/ws/{self.symbol.lower()}@trade"
        self.progress_cb = progress_cb
        self._stop = threading.Event()
        self._thread = None
        self._writer_thr = None
        
        # 使用 {second_ts: {open, high, low, close, volume}} 暫存
        self._buckets = {}
        self._bucket_lock = threading.Lock()  # 保護桶操作
        
        # 統計
        self._written = 0
        self._first_sec = None
        self._last_sec = None
        self._last_close = None
        self._real_count = 0
        self._fill_count = 0
        
        # 重連管理
        self._reconnect_count = 0
        self._max_reconnects = 10
        self._base_retry_delay = 1.0
        self._max_retry_delay = 60.0
        self._last_message_time = None
        self._connection_health_check_interval = 30
        
        # 連接狀態
        self._connected = False
        self._connection_start_time = None
        self._db_error_count = 0

    def _emit(self, msg: str):
        if self.progress_cb:
            try:
                self.progress_cb(msg)
            except Exception:
                pass
        # 不再透過 logger.info() 以避免顯示『現在時間』的時間戳

    def _on_message(self, _, message):
        try:
            data = json.loads(message)
            price = float(data.get("p") or data.get("price") or 0.0)
            qty = float(data.get("q") or data.get("quantity") or 0.0)
            # 交易時間（毫秒）
            t_ms = int(data.get("T") or data.get("E") or time.time() * 1000)
            sec = t_ms // 1000
            # 更新秒桶
            with self._bucket_lock:
                bucket = self._buckets.get(sec)
                if bucket is None:
                    self._buckets[sec] = {
                        "open": price,
                        "high": price,
                        "low": price,
                        "close": price,
                        "volume": qty,
                        "quote_volume": price * qty,
                        "num_trades": 1,
                    }
                else:
                    bucket["high"] = max(bucket["high"], price)
                    bucket["low"] = min(bucket["low"], price)
                    bucket["close"] = price
                    bucket["volume"] += qty
                    bucket["quote_volume"] = bucket.get("quote_volume", 0.0) + price * qty
                    bucket["num_trades"] = bucket.get("num_trades", 0) + 1
            # 記錄最後一次收到 trade 的時間，用於健康檢查
            self._last_message_time = time.time()
        except Exception as e:
            self._emit(f"❌ WS 處理訊息錯誤: {e}")

    def _on_error(self, _, error):
        self._emit(f"❌ WS 連線錯誤: {error}")

    def _on_close(self, *_):
        self._connected = False
        self._emit("🔌 WS 已關閉")

    def _on_open(self, *_):
        self._connected = True
        self._connection_start_time = time.time()
        self._last_message_time = self._connection_start_time
        self._emit(f"🟢 WS 已連線: {self.symbol}@trade")

    def _writer_loop(self):
        # 每 1 秒將前一秒資料寫入 DB
        last_flushed = int(time.time())
        while not self._stop.is_set():
            now_sec = int(time.time())
            # 將 <= now_sec - 1 的桶寫入（避免當前秒尚未完成）
            flush_upto = now_sec - 1
            with self._bucket_lock:
                secs_to_flush = [s for s in list(self._buckets.keys()) if s <= flush_upto]
                secs_to_flush.sort()
                buckets = {s: self._buckets.pop(s, None) for s in secs_to_flush}

            # 健康檢查：連線存在但長時間未收到任何 trade
            try:
                if self._connected:
                    last_activity = self._last_message_time or self._connection_start_time
                    if last_activity is not None:
                        inactivity = time.time() - last_activity
                        if inactivity >= self._connection_health_check_interval:
                            self._emit(
                                f"⚠️ {self.symbol} 已 {int(inactivity)} 秒沒有收到 trade，"
                                f"請檢查連線或市場是否休市"
                            )
                            # 避免持續重複輸出，重置計時點
                            now = time.time()
                            self._connection_start_time = now
                            self._last_message_time = now
            except Exception:
                pass

            for s in secs_to_flush:
                b = buckets.get(s)
                if not b:
                    continue

                # 若中間有缺秒，使用前一秒收盤價補齊（volume=0，標記為 no-trade-fill）
                if self._last_sec is not None and s > self._last_sec + 1 and self._last_close is not None:
                    for gap_s in range(self._last_sec + 1, s):
                        gap_kline = {
                            "open_time": gap_s * 1000,
                            "close_time": (gap_s + 1) * 1000,
                            "open": self._last_close,
                            "high": self._last_close,
                            "low": self._last_close,
                            "close": self._last_close,
                            "volume": 0.0,
                            "quote_asset_volume": 0.0,
                            "num_trades": 0,
                            "taker_base_vol": 0.0,
                            "taker_quote_vol": 0.0,
                        }
                        try:
                            insert_data(
                                self.category,
                                self.symbol,
                                1,
                                gap_kline,
                                data_source='real_no-trade-fill',
                            )
                            if self._first_sec is None:
                                self._first_sec = gap_s
                            self._last_sec = gap_s
                            self._written += 1
                            self._fill_count += 1
                            self._emit(
                                f"🟢 1s 寫入 {self.symbol} {datetime.fromtimestamp(gap_s, tz=timezone.utc)} "
                                f"data_source=real_no-trade-fill(總共{self._fill_count})"
                            )
                        except Exception as e:
                            self._db_error_count += 1
                            self._emit(f"❌ 寫入補線錯誤: {e}")

                kline = {
                    "open_time": s * 1000,
                    "close_time": (s + 1) * 1000,
                    "open": b["open"],
                    "high": b["high"],
                    "low": b["low"],
                    "close": b["close"],
                    "volume": b["volume"],
                    "quote_asset_volume": b.get("quote_volume", 0.0),
                    "num_trades": b.get("num_trades", 0),
                    "taker_base_vol": 0.0,
                    "taker_quote_vol": 0.0,
                }
                # interval=1 秒
                try:
                    insert_data(self.category, self.symbol, 1, kline, data_source='real')
                    # 更新統計
                    if self._first_sec is None:
                        self._first_sec = s
                    self._last_sec = s
                    self._last_close = b["close"]
                    self._written += 1
                    self._real_count += 1
                    self._emit(
                        f"🟢 1s 寫入 {self.symbol} {datetime.fromtimestamp(s, tz=timezone.utc)} "
                        f"data_source=real(總共{self._real_count})"
                    )
                except Exception as e:
                    self._db_error_count += 1
                    self._emit(f"❌ 寫入錯誤: {e}")
            time.sleep(0.2)

    def start(self):
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        # writer thread
        self._writer_thr = threading.Thread(target=self._writer_loop, daemon=True)
        self._writer_thr.start()

    def _run(self):
        self.ws = WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open,
        )
        # 這個會阻塞直到關閉
        while not self._stop.is_set():
            try:
                self.ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as e:
                self._emit(f"❌ WS 斷線重連: {e}")
                time.sleep(2)
            if self._stop.is_set():
                break

    def stop(self):
        self._stop.set()
        try:
            self.ws.close()
        except Exception:
            pass
        time.sleep(0.3)
        # 輸出收集摘要（以資料時間為準）
        try:
            if self._written > 0:
                s0 = self._first_sec
                s1 = self._last_sec + 1  # 區間為 [s0, s1)
                s0_u8 = datetime.fromtimestamp(s0, tz=timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                s1_u8 = datetime.fromtimestamp(s1, tz=timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
                s0_u = datetime.fromtimestamp(s0, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                s1_u = datetime.fromtimestamp(s1, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
                msg = f"✅ 1s 收集結束：新增 {self._written} 筆；時間段：[UTC+8 {s0_u8} ~ {s1_u8}) / [UTC {s0_u} ~ {s1_u})"
                self._emit(msg)
                # 同步輸出到終端（以區間起點作為前綴）
                pfx = f"[UTC+8 {s0_u8}] "
                print(pfx + msg)
            else:
                msg = "ℹ️ 1s 收集結束：本次無新增資料"
                self._emit(msg)
                print(msg)

            # 若本次收集中有任何 DB 寫入錯誤，輸出總結警示
            if self._db_error_count > 0:
                warn = f"⚠️ 本次 1s 收集共有 {self._db_error_count} 筆寫入失敗"
                self._emit(warn)
                print(warn)
        except Exception:
            pass


# 管理多個 handle
_HANDLES = {}

def start_1s_aggregator(category: str, symbol: str, progress_cb=None):
    key = f"{category}:{symbol.replace('/', '').upper()}"
    if key in _HANDLES:
        return _HANDLES[key]
    agg = _WS1sAggregator(category, symbol, progress_cb)
    _HANDLES[key] = agg
    agg.start()
    return agg


def stop_1s_aggregator(category: str, symbol: str):
    key = f"{category}:{symbol.replace('/', '').upper()}"
    agg = _HANDLES.pop(key, None)
    if agg:
        try:
            agg.stop()
        except Exception:
            pass
        return True
    return False
