"""backfill_data.py - 使用 REST API 智慧補齊 + 秒級背景 + 日誌與進度"""
import time
from datetime import datetime, timedelta, timezone
from modules.utils.database import insert_data, batch_insert_data
from .data_integrity import get_missing_ranges
from modules.utils.logger import get_logger
from modules.utils.data.data_fetcher import fetch_klines
from .backfill_state import backfill_state_manager
from modules.utils.data.IMPORTANT_VALIDATION_MODULE import validate_backfill_integrity
from modules.utils.data.backfill_monitoring_utils import (
    BackfillErrorMonitor,
    LOG_AGGREGATION_CHUNK,
    LogAggregationValidator,
)

logger = get_logger("backfill")


class ChunkedLogAggregator:
    """將多筆日誌摘要為單行輸出"""

    def __init__(self, chunk_size, formatter, report_cb, label, validator: LogAggregationValidator):
        self.chunk_size = chunk_size
        self.formatter = formatter
        self.report_cb = report_cb
        self.label = label
        self.validator = validator
        self.validator.assert_chunk(label, chunk_size)
        self.buffer = []

    def add(self, record):
        self.buffer.append(record)
        if len(self.buffer) >= self.chunk_size:
            self.flush()

    def flush(self, force=False):
        if not self.buffer:
            return
        if force or len(self.buffer) >= self.chunk_size:
            message = self.formatter(self.buffer)
            self.report_cb(message)
            self.buffer.clear()

    def force_flush(self):
        if self.buffer:
            message = self.formatter(self.buffer)
            self.report_cb(message)
            self.buffer.clear()


def _format_success_chunk(records):
    last = records[-1]
    count = len(records)
    interval = last['interval']
    batch_num = last['batch_num']
    batch_count = last['batch_count']
    total = last['global_idx']
    idx = last['batch_idx']
    close = last['close']
    tw_time = last['tw_short']
    symbol_short = last.get('symbol_short', '')
    prefix = f"{symbol_short} | " if symbol_short else ""
    return (
        f"{prefix}{interval} 批次{batch_num:02d} ✅ 最近{count}筆 • 最新 {tw_time} close={close:.2f} • 總:{total}"
    )


def _format_skip_chunk(records):
    last = records[-1]
    count = len(records)
    interval = last['interval']
    batch_num = last['batch_num']
    total_skipped = last['total_skipped']
    tw_time = last['tw_short']
    source = last['existing_source']
    symbol_short = last.get('symbol_short', '')
    prefix = f"{symbol_short} | " if symbol_short else ""
    return (
        f"{prefix}{interval} 批次{batch_num:02d} ⏭️ 最近{count}筆跳過 • 最新 {tw_time} • 總跳過:{total_skipped} • 來源={source}"
    )

def interval_to_seconds(interval: str) -> int:
    m = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(interval[:-1]) * m[interval[-1]]

def fetch_and_insert(category, symbol, interval, start_time, end_time, progress_cb=None, overwrite_callback=None, gui_logger=None, message_sender=None):
    """
    回補資料批次抓取與插入
    
    Args:
        category: 資產分類
        symbol: 貨幣對
        interval: 時間間隔
        start_time: 開始時間
        end_time: 結束時間
        progress_cb: 進度回調（舊版，用於兼容）
        overwrite_callback: 覆蓋回調
        gui_logger: GUI日誌記錄器（舊版，支持日誌級別）
        message_sender: 訊息發送器（新版，異步架構）- 優先使用
    """
    # 統一定義貨幣對縮寫
    symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
    logger.info(f"{symbol_short} | 抓取 {symbol}@{interval} 範圍 {start_time} → {end_time}")
    
    # 優先使用新的異步訊息發送器
    if message_sender:
        message_sender.start(symbol, interval, start_time, end_time)
        blog = None  # 不使用舊的日誌系統
    elif gui_logger:
        # 退回到舊的日誌系統
        from core.gui_logger import BackfillLogger
        blog = BackfillLogger(gui_logger, symbol)
        blog.start(interval, start_time, end_time)
    else:
        blog = None
    
    # 計算間隔秒數
    interval_seconds = interval_to_seconds(interval)
    
    # 幣安 API 限制每次最多 1000 筆，需要分批處理
    current_start = start_time
    total_inserted = 0
    total_processed = 0
    total_skipped = 0
    batch_num = 0

    def report(msg: str):
        """兼容舊版的報告函數"""
        if progress_cb:
            progress_cb(msg)

    # 添加批次計數保護，避免無限循環
    MAX_BATCHES = 1000  # 最多處理1000批次（約100萬筆資料）
    
    while current_start < end_time and batch_num < MAX_BATCHES:
        batch_num += 1
        
        # 檢查是否達到批次上限
        if batch_num >= MAX_BATCHES:
            logger.warning(f"⚠️ 已達到最大批次限制 ({MAX_BATCHES})，停止回補")
            report(f"⚠️ 已達到最大批次限制，請縮小時間範圍或聯繫技術支援")

        # 計算這一批的結束時間（最多 1000 筆）
        batch_end = min(
            current_start + timedelta(seconds=interval_seconds * 999),  # 999 筆，保留一點緩衝
            end_time
        )

        # 新增：檢查 pause 狀態（絕對理性輪詢，避免失靈）
        state = backfill_state_manager.get_state()  # 獲取當前狀態
        if state.is_paused:  # 如果已暫停
            report("⏸️ 回補暫停，等待恢復...")
            # 🔧 修復：在 while 循環中重新獲取狀態，確保能檢測到恢復
            while True:
                state = backfill_state_manager.get_state()  # 重新獲取最新狀態
                if state.is_stopped:
                    raise InterruptedError("回補已被停止")
                if not state.is_paused:  # 已恢復
                    break
                time.sleep(0.5)  # 短暫等待後重新檢查
            report("▶️ 回補已恢復")

        state = backfill_state_manager.get_state()
        if state.is_stopped:
            raise InterruptedError("回補已被停止")

        # 格式化時間顯示（移除微秒，只顯示到秒）
        start_str = current_start.strftime('%Y-%m-%d %H:%M:%S')
        end_str = batch_end.strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"📦 批次 {batch_num}: {start_str} → {end_str}")
        
        # 使用訊息發送器（優先）或舊日誌系統
        if message_sender:
            message_sender.batch_start(symbol, batch_num, 999)
        elif blog:
            blog.batch_start(batch_num, 999)
        else:
            report(f"📦 批次 {batch_num}: 正在抓取...")
        
        # 抓取資料（轉換 datetime 為毫秒時間戳）
        start_ms = int(current_start.timestamp() * 1000)
        end_ms = int(batch_end.timestamp() * 1000)
        klines = fetch_klines(symbol, interval, start_time=start_ms, end_time=end_ms)
        
        if not klines:
            logger.warning(f"⚠️ 批次 {batch_num} 無資料")
            if message_sender:
                message_sender.warning(symbol, f"批次 {batch_num} 無資料")
            elif blog:
                blog.warning(f"批次 {batch_num} 無資料")
            current_start = batch_end + timedelta(seconds=interval_seconds)
            continue
        
        # 抓取完成記錄（詳細級別）
        if message_sender:
            message_sender.batch_fetched(symbol, batch_num, len(klines))
        elif blog:
            blog.batch_fetched(batch_num, len(klines))
        
        batch_count = len(klines)
        
        if batch_count == 0:
            logger.warning(f"⚠️ 批次 {batch_num} 無資料")
            # 如果這批沒資料，跳到下一批
            current_start = batch_end + timedelta(seconds=interval_seconds)
            continue
        
        # 驗證第一筆資料的完整性（只在第一批檢查）
        if batch_num == 1 and len(klines) > 0:
            first_kline = klines[0]
            required_fields = ['open_time', 'open', 'high', 'low', 'close', 'volume', 
                              'close_time', 'quote_asset_volume', 'num_trades', 
                              'taker_base_vol', 'taker_quote_vol']
            
            missing_fields = [f for f in required_fields if f not in first_kline]
            if missing_fields:
                error_msg = f"❌ 資料不完整！缺少欄位: {', '.join(missing_fields)}"
                logger.error(error_msg)
                report(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"✅ 資料完整性檢查通過（11 個欄位）")
        
        # ===== 性能優化：使用批量插入 =====
        # 重要：batch_insert_data內部已有重複檢查邏輯，不需要預過濾
        
        logger.info(f"{symbol_short} | 📊 批次{batch_num:02d} 準備批量插入 {batch_count} 筆資料")
        
        # 插入開始記錄（詳細級別）
        if message_sender:
            message_sender.batch_inserting(symbol, batch_num, batch_count)
        elif blog:
            blog.batch_inserting(batch_num, batch_count)
        
        # 使用批量插入（一次事務提交，內部處理重複檢查）
        inserted_count = batch_insert_data(
            category,
            symbol,
            interval_seconds,
            klines,  # 直接傳入所有資料，讓batch_insert處理
            data_source='real',
            original_interval=interval,
            overwrite_callback=overwrite_callback
        )
        
        # 計算跳過數量（總數 - 插入數）
        skipped_in_batch = batch_count - inserted_count
        total_skipped += skipped_in_batch
        total_inserted += inserted_count
        total_processed += batch_count
        
        # 進度更新（使用state manager）
        try:
            estimated_total = total_inserted
            backfill_state_manager.update_progress(
                estimated_total,
                f"{symbol_short} | {interval} - 批次{batch_num} 完成 (插入:{inserted_count}/{batch_count})"
            )
        except (InterruptedError, KeyboardInterrupt):
            logger.info("回補被停止")
            raise
        except Exception:
            pass  # 進度更新失敗不影響回補
        
        # 批次完成訊息（使用分級日誌）
        if message_sender:
            if skipped_in_batch == batch_count:
                # 全部跳過
                message_sender.skip_all(symbol, batch_num, batch_count)
            else:
                # 正常完成
                message_sender.batch_complete(symbol, batch_num, inserted_count, skipped_in_batch, batch_count)
            # 詳細進度
            if inserted_count > 0:
                message_sender.progress(symbol, total_inserted, total_inserted + total_skipped, f"批次{batch_num}完成")
        elif blog:
            if skipped_in_batch == batch_count:
                blog.skip_all(batch_num, batch_count)
            else:
                blog.batch_complete(batch_num, inserted_count, skipped_in_batch, batch_count)
            if inserted_count > 0:
                blog.progress(total_inserted, total_inserted + total_skipped, f"批次{batch_num}完成")
        else:
            # 兼容舊版
            batch_complete_msg = f"{symbol_short} | 🎯 批次{batch_num:02d} 批量插入完成：成功 {inserted_count}/{batch_count} 筆，跳過 {skipped_in_batch} 筆"
            logger.info(batch_complete_msg)
            report(batch_complete_msg)
        
        # 移動到下一批的起始時間
        # 使用最後一筆資料的時間 + 間隔
        last_kline_time_ms = klines[-1].get('close_time', klines[-1].get('open_time'))
        current_start = datetime.fromtimestamp(last_kline_time_ms / 1000, tz=timezone.utc) + timedelta(seconds=interval_seconds)
        
        # 若已達結束時間則退出；否則短暫延遲後處理下一批
        if current_start >= end_time:
            break
        # 優化：減少批次間延遲從100ms到10ms
        time.sleep(0.01)
    
    # 回補完成訊息
    if message_sender:
        message_sender.complete(symbol, total_inserted, total_skipped)
    elif blog:
        blog.complete(total_inserted, total_skipped)
    else:
        # 兼容舊版
        if total_skipped:
            summary = f"{interval} - ⏭️ 本次共跳過 {total_skipped} 筆重複 timestamp (data_source=real)"
            logger.info(summary)
            report(summary)
        
        logger.info(
            f"✅ 完成抓取 {symbol}@{interval}，成功插入 {total_inserted} 筆資料，"
            f"跳過 {total_skipped} 筆（處理總數 {total_processed}）"
        )
    
    return total_inserted, total_skipped

def smart_backfill(category, symbol, interval="1s",start_time=None, end_time=None, progress_cb=None, overwrite_callback=None, gui_logger=None, message_sender=None):
    """
    智慧回補函數
    
    Args:
        gui_logger: GUI日誌記錄器（舊版，支持日誌級別）
        message_sender: 訊息發送器（新版，異步架構）- 優先使用
    """
    # 轉換為台灣時間顯示
    tw_tz = timezone(timedelta(hours=8))
    monitor = BackfillErrorMonitor()
    progress_proxy = monitor.wrap_progress_cb(progress_cb) if progress_cb else None

    def emit(msg: str):
        if progress_proxy:
            progress_proxy(msg)
    
    if start_time is None:
        start_time = datetime.now(tz=timezone.utc) - timedelta(days=3)
    if end_time is None:
        end_time = datetime.now(tz=timezone.utc)
    
    # 轉換為台灣時間顯示
    start_tw = start_time.astimezone(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
    end_tw = end_time.astimezone(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
    
    logger.info(f"🚀 智慧補齊 {symbol}@{interval} 開始")
    logger.info(f"📅 時間範圍: {start_tw} → {end_tw} (UTC+8)")
    emit(f"🚀 智慧補齊 {symbol}@{interval} 開始")
    emit(f"📅 時間範圍: {start_tw} → {end_tw} (UTC+8)")

    # 若 GUI 已指定起計時間，直接抓該區間
    if start_time and end_time:
        # 先檢查資料庫中已存在的資料量
        from modules.utils.database.data_manager import _data_manager
        conn = _data_manager.db_core.get_connection()
        cursor = conn.cursor()
        
        try:
            # 轉換時間為時間戳
            start_ts = start_time.timestamp()
            end_ts = end_time.timestamp()
            
            cursor.execute("""
                SELECT COUNT(*) FROM historical_data 
                WHERE category=? AND symbol=? AND interval=? AND timestamp BETWEEN ? AND ? AND data_source='real'
            """, (category, symbol, interval_to_seconds(interval), start_ts, end_ts))
            
            existing_count = cursor.fetchone()[0]
            if existing_count > 0:
                msg = f"ℹ️ 該時間範圍內已有 {existing_count} 筆 real 的資料存在"
                logger.info(msg)
                emit(msg)
        finally:
            conn.close()
        
        # 插入資料並獲取實際插入筆數
        actual_inserted, skipped = fetch_and_insert(
            category, symbol, interval, start_time, end_time, progress_proxy, overwrite_callback, gui_logger, message_sender
        )
        
        # ⚠️ 重要：進行資料完整性驗證
        try:
            validation_passed, validation_msg = validate_backfill_integrity(
                symbol, interval, start_time, end_time, actual_inserted, skipped, progress_proxy
            )
            
            if not validation_passed:
                # 驗證失敗，拋出異常終止操作
                raise ValueError(f"資料驗證失敗: {validation_msg}")
                
        except Exception as validation_error:
            # 驗證失敗時顯示錯誤並終止
            error_msg = f"❌ 資料驗證錯誤，終止操作: {validation_error}"
            logger.error(error_msg)
            emit(error_msg)
            raise validation_error
        
        emit(f"🎯 指定區間補齊完成 ({start_tw} → {end_tw}) - 驗證通過")
        logger.info(f"🎯 指定區間補齊完成 ({start_tw} → {end_tw}) - 驗證通過")
        return True

    # 否則走缺口掃描模式
    secs = interval_to_seconds(interval)
    missing = get_missing_ranges(category, symbol, secs)
    if not missing:
        msg = "✅ 無需補齊，資料完整"
        emit(msg)
        logger.info(msg)
        return True
    
    # 顯示缺口數量
    logger.info(f"🔎 發現 {len(missing)} 個時間缺口")
    emit(f"🔎 發現 {len(missing)} 個時間缺口")
        
    for s, e in missing:
        try:
            # 轉換為台灣時間顯示
            s_tw = datetime.fromtimestamp(s, tz=tw_tz).strftime('%Y-%m-%d %H:%M:%S')
            e_tw = datetime.fromtimestamp(e, tz=tw_tz).strftime('%Y-%m-%d %H:%M:%S')
            
            msg = f"📦 補齊區間: {s_tw} → {e_tw} (UTC+8)"
            logger.info(msg)
            emit(msg)
            
            # 先檢查區間內已存在的資料
            from modules.utils.database.data_manager import _data_manager
            conn = _data_manager.db_core.get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    SELECT COUNT(*) FROM historical_data 
                    WHERE category=? AND symbol=? AND interval=? AND timestamp BETWEEN ? AND ? AND data_source='real'
                """, (category, symbol, secs, s, e))
                
                existing_count = cursor.fetchone()[0]
                if existing_count > 0:
                    msg = f"ℹ️ 區間內已有 {existing_count} 筆 real 的資料存在"
                    logger.info(msg)
                    emit(msg)
            finally:
                conn.close()
            
            # 插入資料
            fetch_and_insert(
                category,
                symbol,
                interval,
                datetime.fromtimestamp(s, tz=timezone.utc),
                datetime.fromtimestamp(e, tz=timezone.utc),
                progress_proxy,
                overwrite_callback,
                gui_logger,  # 傳遞GUI日誌記錄器
                message_sender,  # 傳遞訊息發送器
            )
                         
        except Exception as exc:
            error_msg = f"❌ 補齊錯誤: {type(exc).__name__} - {exc}"
            logger.error(error_msg)
            emit(error_msg)
    
    msg = f"✅ 智慧補齊完成 ({symbol}@{interval})"
    emit(msg)
    logger.info(msg)
    return True

def slow_background_seconds(category, symbol, progress_cb=None):
    logger.info(f"🐢 背景秒級補齊 {symbol} 開始")
    for sec in [1]:  # 目前僅1s合法，其他間隔由GUI合成
        smart_backfill(category, symbol, f"{sec}s", progress_cb=progress_cb)
        time.sleep(900)
    if progress_cb: progress_cb("✅ 背景秒級補齊完成")
