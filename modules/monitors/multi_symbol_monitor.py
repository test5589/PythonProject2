"""multi_symbol_monitor.py - 多貨幣對監控管理器（支援一秒監控與批量抓取）"""

import threading
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Callable, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed

from modules.utils.data.ws_aggregator import _WS1sAggregator
from modules.utils.database import batch_insert_data
from modules.utils.api.api_client import (
    get_api_client,
    reset_kline_fetch_stats,
    get_kline_fetch_stats,
    reset_api_retry_stats,
    get_api_retry_stats,
)
from modules.utils.logger import get_logger, get_log_rotation_stats
from modules.utils.exceptions import APIError
from modules.utils.data.IMPORTANT_VALIDATION_MODULE import (
    validate_batch_fetch_integrity,
    validate_daily_1m_completion,
    reset_daily_1m_summary,
    summarize_daily_1m_results,
    get_or_init_daily_1m_range,
)
from config.trading_config import TradingConfig

logger = get_logger("multi_monitor")


class MultiSymbolMonitor:
    """多貨幣對監控管理器"""
    
    # 最大監控貨幣對數量（避免資源過載）
    MAX_MONITOR_SYMBOLS = 20
    
    def __init__(self, progress_cb: Optional[Callable] = None):
        self.progress_cb = progress_cb
        self._monitors: Dict[str, _WS1sAggregator] = {}
        self._monitoring = False
        self._lock = threading.Lock()
        
    def _emit(self, msg: str):
        """統一訊息輸出"""
        if self.progress_cb:
            try:
                self.progress_cb(msg)
            except Exception:
                pass
        logger.info(msg)
    
    def start_all_symbols_1s(self, category: str = "crypto") -> bool:
        """
        啟動所有支援貨幣對的一秒監控
        
        Args:
            category: 資產分類（預設 crypto）
            
        Returns:
            bool: 是否成功啟動
        """
        with self._lock:
            if self._monitoring:
                self._emit("⚠️ 多貨幣對監控已在執行中")
                return False
            
            all_symbols = TradingConfig.SUPPORTED_SYMBOLS
            if not all_symbols:
                self._emit("❌ 無可用的貨幣對配置")
                return False
            
            # 限制監控數量以避免資源過載
            if len(all_symbols) > self.MAX_MONITOR_SYMBOLS:
                self._emit(
                    f"⚠️ 配置了 {len(all_symbols)} 個貨幣對，"
                    f"為避免資源過載，僅監控前 {self.MAX_MONITOR_SYMBOLS} 個"
                )
                symbols = all_symbols[:self.MAX_MONITOR_SYMBOLS]
            else:
                symbols = all_symbols
            
            self._emit(f"🚀 啟動多貨幣對一秒監控：{len(symbols)} 個貨幣對")
            
            success_count = 0
            for symbol in symbols:
                try:
                    key = f"{category}:{symbol}"
                    monitor = _WS1sAggregator(category, symbol, self._symbol_progress_cb(symbol))
                    self._monitors[key] = monitor
                    monitor.start()
                    success_count += 1
                    self._emit(f"✅ 啟動監控：{symbol}")
                except Exception as e:
                    self._emit(f"❌ 啟動失敗 {symbol}：{e}")
            
            if success_count > 0:
                self._monitoring = True
                self._emit(f"🎉 成功啟動 {success_count}/{len(symbols)} 個貨幣對監控")
                return True
            else:
                self._emit("❌ 所有貨幣對啟動失敗")
                return False
    
    def stop_all_symbols_1s(self) -> bool:
        """
        停止所有一秒監控
        
        Returns:
            bool: 是否成功停止
        """
        with self._lock:
            if not self._monitoring:
                self._emit("⚠️ 無監控在執行")
                return False
            
            self._emit("🛑 停止多貨幣對監控...")
            
            stop_count = 0
            for key, monitor in self._monitors.items():
                try:
                    monitor.stop()
                    stop_count += 1
                    self._emit(f"✅ 停止監控：{key}")
                except Exception as e:
                    self._emit(f"❌ 停止失敗 {key}：{e}")
            
            self._monitors.clear()
            self._monitoring = False
            self._emit(f"🎉 成功停止 {stop_count} 個監控")
            return True
    
    def _symbol_progress_cb(self, symbol: str) -> Callable:
        """為每個貨幣對生成專屬的進度回呼"""
        def cb(msg: str):
            self._emit(f"[{symbol}] {msg}")
        return cb
    
    def is_monitoring(self) -> bool:
        """檢查是否正在監控"""
        return self._monitoring
    
    def get_monitoring_symbols(self) -> List[str]:
        """取得正在監控的貨幣對列表"""
        with self._lock:
            return list(self._monitors.keys())
    
    # ========== 批量抓取功能 ==========
    def fetch_all_symbols_latest_minute(self, category: str = "crypto") -> bool:
        """
        批量抓取所有貨幣對的最新一分鐘資料
        
        Args:
            category: 資產分類
            
        Returns:
            bool: 是否成功
        """
        # 獲取全域資料庫操作鎖
        from modules.utils.database.data_manager import _db_operation_lock
        
        if not _db_operation_lock.acquire(blocking=False):
            self._emit("⏳ 資料庫操作進行中，請等待其他操作完成...")
            _db_operation_lock.acquire()  # 阻塞等待
            self._emit("✅ 資料庫操作鎖已獲取，繼續批量抓取")
        
        try:
            all_symbols = TradingConfig.SUPPORTED_SYMBOLS
            if not all_symbols:
                self._emit("❌ 無可用的貨幣對配置")
                return False
            
            # 限制批量抓取數量
            if len(all_symbols) > self.MAX_MONITOR_SYMBOLS:
                self._emit(
                    f"⚠️ 配置了 {len(all_symbols)} 個貨幣對，"
                    f"為避免API過載，僅抓取前 {self.MAX_MONITOR_SYMBOLS} 個"
                )
                symbols = all_symbols[:self.MAX_MONITOR_SYMBOLS]
            else:
                symbols = all_symbols

            # 重置 1 分鐘驗證暫存與 API 抓取/重試統計，並紀錄每個貨幣對在本次任務中實際抓取/插入的筆數，供事後驗證使用
            reset_daily_1m_summary()
            reset_kline_fetch_stats()
            reset_api_retry_stats()
            symbol_inserted: Dict[str, int] = {sym: 0 for sym in symbols}

            self._emit(f"📥 開始批量抓取 {len(symbols)} 個貨幣對的最新 1 分鐘資料")
            
            # ====== 抓取範圍：永遠用『現在』作為結束時間 ======
            taipei_tz = timezone(timedelta(hours=8))
            now_taipei = datetime.now(tz=taipei_tz)
            today_start = now_taipei.replace(hour=0, minute=0, second=0, microsecond=0)

            fetch_start_utc = today_start.astimezone(timezone.utc)
            fetch_end_utc = now_taipei.astimezone(timezone.utc)

            self._emit(
                f"📅 時間範圍: {today_start.strftime('%Y-%m-%d %H:%M:%S')} → {now_taipei.strftime('%Y-%m-%d %H:%M:%S')} (UTC+8)"
            )
            self._emit(
                f"🔢 估計每個貨幣對最多抓取 {int((now_taipei - today_start).total_seconds() / 60)} 筆資料"
            )

            # ====== 驗證範圍：同一天內固定用第一次按按鈕時的區間 ======
            ref_start_local, ref_end_local = get_or_init_daily_1m_range(today_start, now_taipei)
            validate_start_utc = ref_start_local.astimezone(timezone.utc)
            validate_end_utc = ref_end_local.astimezone(timezone.utc)
            
            # 使用線程池並行抓取（每個貨幣對內部帶簡單重試機制）
            success_count = 0
            total_inserted = 0
            
            with ThreadPoolExecutor(max_workers=min(5, len(symbols))) as executor:
                # 提交任務
                future_to_symbol = {
                    executor.submit(
                        self._fetch_single_symbol_with_retry,
                        category,
                        symbol,
                        fetch_start_utc,
                        fetch_end_utc,
                    ): symbol
                    for symbol in symbols
                }
                
                # 收集結果
                for future in as_completed(future_to_symbol):
                    symbol = future_to_symbol[future]
                    try:
                        inserted = future.result()
                        # 累計每個貨幣對在本次任務中實際插入的筆數，供後續驗證使用
                        symbol_inserted[symbol] += max(0, inserted or 0)
                        if inserted > 0:
                            success_count += 1
                            total_inserted += inserted
                            self._emit(f"✅ {symbol}: 插入 {inserted} 筆 data_source=real")
                        else:
                            self._emit(f"⚠️ {symbol}: 無新資料")
                    except APIError as e:
                        details = getattr(e, "details", {}) or {}
                        if details.get("status_code") == 400 and details.get("api_error_code") == -1121:
                            # Binance 回傳 Invalid symbol，代表 REST K 線 API 不支援這個交易對
                            self._emit(f"⚠️ {symbol}: REST K 線 API 不支援 (Invalid symbol)，略過此貨幣對")
                        else:
                            self._emit(f"❌ {symbol}：抓取失敗 - {e}")
                    except Exception as e:
                        self._emit(f"❌ {symbol}：抓取失敗 - {e}")

            # B 方案 + 二次驗證：在整體抓取完成後，針對每個貨幣對做一次綜合驗證（API 抓取 + 主 DB 1m 筆數），並在最後輸出統一總結
            for sym in symbols:
                api_fetched = symbol_inserted.get(sym, 0)
                try:
                    validate_daily_1m_completion(
                        category,
                        sym,
                        validate_start_utc,
                        validate_end_utc,
                        api_fetched,
                        progress_cb=None,  # 單筆不直接噴大量 log，統一在總結時輸出
                    )
                except Exception as e:
                    # 驗證本身不應中斷整體流程，但若驗證邏輯出錯，仍需留痕
                    self._emit(f"⚠️ {sym}: 綜合 1m 驗證過程發生錯誤 - {e}")

            # 針對本次批量結果輸出一次性的真警報 / 假警報統計總結（使用固定的驗證範圍）
            summarize_daily_1m_results(validate_start_utc, validate_end_utc, progress_cb=self._emit)

            # 額外輸出一次 API 抓取統計（成功警報彙總）
            fetch_calls, total_rows = get_kline_fetch_stats()
            self._emit(
                f"🟢 [API-FETCH 成功警報] 本次 1 分鐘批量抓取成功呼叫次數: {fetch_calls} 次，累計取得 {total_rows} 筆 K 線資料"
            )

            # 輸出 API 重試統計（假假警報彙總）
            conn_retries, timeout_retries = get_api_retry_stats()
            self._emit(
                f"⚪ [API-RETRY 假假警報] 本次 API 重試次數：連線錯誤 {conn_retries} 次，請求超時 {timeout_retries} 次（僅影響請求延遲，不影響已成功寫入的資料）"
            )

            # 輸出日誌輪替 PermissionError 統計（假假警報彙總）
            rotation_count, rotation_reported = get_log_rotation_stats()
            if rotation_count > 0:
                self._emit("🟣 [LOG-ROTATION 假假警報] 日誌輪替 PermissionError 摘要：")
                self._emit(
                    f"   - 本程式執行期間共偵測到 {rotation_count} 次日誌輪替 PermissionError（log 檔可能被編輯器或檔案總管佔用）"
                )
                self._emit("   - 影響：僅影響 log 檔整理，不影響交易邏輯與資料寫入")
            else:
                self._emit("🟣 [LOG-ROTATION 假假警報] 日誌輪替 PermissionError: 0 次（未偵測到 log 檔輪替失敗）")
            
            # 台灣時間的完成時間
            finish_time = datetime.now(tz=timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
            self._emit(f"🎉 批量抓取完成: 成功 {success_count}/{len(symbols)} 個貨幣對，總計插入 {total_inserted} 筆 (完成時間: {finish_time} UTC+8)")
            if total_inserted > 0:
                self._emit(f"✅ 所有插入的資料都使用 data_source=real 以確保最高優先級")
            return success_count > 0
            
        finally:
            # 釋放鎖
            _db_operation_lock.release()
            self._emit("🔓 資料庫操作鎖已釋放")
    
    def _fetch_single_symbol_with_retry(self, category: str, symbol: str, start: datetime, end: datetime, max_attempts: int = 2) -> int:
        """抓取單個貨幣對的資料（帶簡單重試機制）"""
        last_exception: Optional[Exception] = None
        for attempt in range(1, max_attempts + 1):
            try:
                if attempt > 1:
                    self._emit(f"🔁 {symbol}: 第 {attempt} 次重試抓取最新 1 分鐘資料")
                return self._fetch_single_symbol(category, symbol, start, end)
            except APIError as e:
                details = getattr(e, "details", {}) or {}
                # Binance Invalid symbol 不重試，直接拋出
                if details.get("status_code") == 400 and details.get("api_error_code") == -1121:
                    last_exception = e
                    break
                last_exception = e
                if attempt >= max_attempts:
                    break
                self._emit(f"⚠️ {symbol}: 抓取 1m 資料失敗，準備重試 ({attempt}/{max_attempts}) - {e}")
                time.sleep(1)
            except Exception as e:
                last_exception = e
                if attempt >= max_attempts:
                    break
                self._emit(f"⚠️ {symbol}: 抓取 1m 資料發生錯誤，準備重試 ({attempt}/{max_attempts}) - {e}")
                time.sleep(1)

        if last_exception is not None:
            # 將最後一次例外拋回給上層，讓統一錯誤處理機制接手
            raise last_exception
        return 0

    def _fetch_single_symbol(self, category: str, symbol: str, start: datetime, end: datetime) -> int:
        """抓取單個貨幣對的資料（支援超過 1000 根 1m，自動分批多次請求）。"""
        try:
            client = get_api_client()

            # 目標時間範圍（毫秒）
            start_ms = int(start.timestamp() * 1000)
            end_ms = int(end.timestamp() * 1000)

            all_klines = []
            curr_start_ms = start_ms

            while curr_start_ms < end_ms:
                # 由 curr_start_ms 開始，最多抓 1000 根，並限制在 end_ms 之前
                batch = client.fetch_klines(
                    symbol,
                    "1m",
                    start_time=curr_start_ms,
                    end_time=end_ms,
                    limit=1000,
                )

                if not batch:
                    break

                # 過濾出真正落在 [start_ms, end_ms) 的 K 線
                for kline in batch:
                    ot = kline.get("open_time")
                    if ot is None:
                        continue
                    if ot < start_ms or ot >= end_ms:
                        continue
                    all_klines.append(kline)

                # 準備下一輪起點：上一批最後一根的下一分鐘
                last_open_ms = batch[-1].get("open_time")
                if last_open_ms is None:
                    break
                next_start_ms = last_open_ms + 60_000  # 1 分鐘 = 60,000ms

                # 安全檢查：避免 API 回傳重複 open_time 導致死循環
                if next_start_ms <= curr_start_ms:
                    break

                curr_start_ms = next_start_ms

                # 若本批少於 1000 根，代表已經抓到尾端，結束迴圈
                if len(batch) < 1000:
                    break

            if not all_klines:
                return 0

            # 轉換為資料庫格式
            db_klines = []
            for kline in all_klines:
                db_klines.append({
                    "open_time": kline["open_time"],
                    "open": kline["open"],
                    "high": kline["high"],
                    "low": kline["low"],
                    "close": kline["close"],
                    "volume": kline["volume"],
                })

            # 批次插入（已存在的 K 線會被忽略，只計算真正新增的筆數）
            inserted = batch_insert_data(category, symbol, 60, db_klines, data_source="real")
            logger.info(f"✅ {symbol} 插入 {inserted} 筆 data_source=real")
            return inserted

        except Exception as e:
            logger.error(f"抓取 {symbol} 失敗：{e}")
            raise


# 全域管理器實例
_global_monitor: Optional[MultiSymbolMonitor] = None
_monitor_lock = threading.Lock()


def get_multi_symbol_monitor(progress_cb: Optional[Callable] = None) -> MultiSymbolMonitor:
    """取得全域多貨幣對監控管理器（單例模式）"""
    global _global_monitor
    
    with _monitor_lock:
        if _global_monitor is None:
            _global_monitor = MultiSymbolMonitor(progress_cb)
        return _global_monitor


def start_all_symbols_monitoring(category: str = "crypto", progress_cb: Optional[Callable] = None) -> bool:
    """便捷函數：啟動所有貨幣對監控"""
    monitor = get_multi_symbol_monitor(progress_cb)
    return monitor.start_all_symbols_1s(category)


def stop_all_symbols_monitoring() -> bool:
    """便捷函數：停止所有貨幣對監控"""
    global _global_monitor
    
    if _global_monitor is not None:
        return _global_monitor.stop_all_symbols_1s()
    return False


def fetch_all_symbols_latest_minute(category: str = "crypto", progress_cb: Optional[Callable] = None) -> bool:
    """便捷函數：批量抓取所有貨幣對最新一分鐘"""
    monitor = get_multi_symbol_monitor(progress_cb)
    return monitor.fetch_all_symbols_latest_minute(category)
