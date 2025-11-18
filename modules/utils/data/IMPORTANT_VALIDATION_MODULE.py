"""
IMPORTANT_VALIDATION_MODULE.py - 資料驗證核心模組
⚠️ 極為重要：此文件包含關鍵資料驗證邏輯，禁止隨意修改！
⚠️ 任何變更必須通過專案負責人審核，並記錄變更原因！

此模組負責驗證資料抓取的完整性和準確性，確保：
1. 時間範圍設定與實際抓取資料量的一致性
2. 資料完整性檢查和錯誤報警
3. 防止資料遺漏或重複的系統性保障

作者: 自動交易機器人專案團隊
建立日期: 2025-11-14
版本: 1.0.0

⚠️ 修改警告: 此文件被標記為核心驗證模組，修改前請務必評估影響！
"""

import logging
import os
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, Callable, List
from modules.utils.logger import get_logger
from modules.utils.database.db_core import DatabaseCore
from modules.utils.exceptions import (
    DataValidationError,
    BackfillInsertError,
    BackfillConfigurationError,
)
from modules.utils.data.backfill_monitoring_utils import (
    LOG_AGGREGATION_CHUNK,
    LogAggregationValidator,
    BackfillErrorMonitor,
    validate_symbol_binding,
)
from config.trading_config import TradingConfig

logger = get_logger("data_validator")

# 狀態檔路徑：用於記錄每日批量抓取驗證結果，便於跨執行比對與上次驗證時間差
VALIDATION_STATE_FILE = os.path.join("data", "latest_1m_validation_state.json")

# 1 分鐘驗證結果暫存：僅在「最新 1 分鐘批量抓取」流程中使用，用來統一輸出總結
_daily_1m_results: Dict[str, Dict[str, Any]] = {}

# 1 分鐘驗證參考時間範圍（本程式執行期間，同一天只初始化一次）
_daily_1m_ref_start_local: Optional[datetime] = None
_daily_1m_ref_end_local: Optional[datetime] = None


def get_or_init_daily_1m_range(
    today_start_local: datetime,
    now_local: datetime,
) -> Tuple[datetime, datetime]:
    """取得當天 1 分鐘驗證用的參考時間範圍（固定 end_time）。

    - 第一次呼叫當天會把範圍設為: [today_start_local, now_local]
    - 同一天後續呼叫，無論按鈕按得多晚，都沿用第一次的 end_time，
      避免『同一批 DB 筆數』因時間往後推而從假警報翻成真警報。
    """

    global _daily_1m_ref_start_local, _daily_1m_ref_end_local

    # 若尚未初始化，或跨天，則重設參考範圍
    if (
        _daily_1m_ref_start_local is None
        or _daily_1m_ref_start_local.date() != today_start_local.date()
    ):
        _daily_1m_ref_start_local = today_start_local
        _daily_1m_ref_end_local = now_local

    return _daily_1m_ref_start_local, _daily_1m_ref_end_local


def _load_validation_state() -> Dict[str, Any]:
    """載入每日批量驗證狀態（若檔案不存在或損壞則回傳空 dict）"""
    try:
        if not os.path.exists(VALIDATION_STATE_FILE):
            return {}
        with open(VALIDATION_STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ 讀取驗證狀態檔失敗: {e}")
        return {}


def _save_validation_state(state: Dict[str, Any]) -> None:
    """將每日批量驗證狀態寫回檔案"""
    try:
        os.makedirs(os.path.dirname(VALIDATION_STATE_FILE), exist_ok=True)
        with open(VALIDATION_STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"❌ 儲存驗證狀態檔失敗: {e}")


def _record_daily_batch_validation(
    symbol: str,
    interval: str,
    start_time: datetime,
    end_time: datetime,
    status: str,
    actual_fetched: int,
    min_acceptable: int,
    max_acceptable: int,
    progress_cb: Optional[Callable],
) -> None:
    """記錄每日批量抓取驗證結果並產生日誌。

    - status="ok" 代表驗證通過（綠色）；
    - 其他值代表需要關注（紅色），例如資料不足。
    - 日誌中會附上與上次驗證的時間差，方便人工判斷合理性。
    """
    try:
        tw_tz = timezone(timedelta(hours=8))
        now_tw = datetime.now(tw_tz)
        date_str = now_tw.strftime("%Y-%m-%d")
        key = f"{symbol}@{interval}"

        state = _load_validation_state()
        day_state = state.get(date_str, {})
        prev = day_state.get(key)

        # 計算與上次驗證的時間差（僅用於訊息顯示）
        delta_str = "首次驗證"
        if prev and "last_checked" in prev:
            try:
                prev_time = datetime.fromisoformat(prev["last_checked"])
                delta = now_tw - prev_time
                total_minutes = int(delta.total_seconds() // 60)
                if total_minutes < 60:
                    delta_str = f"{total_minutes} 分鐘前"
                else:
                    hours = total_minutes // 60
                    minutes = total_minutes % 60
                    delta_str = f"{hours} 小時 {minutes} 分鐘前"
            except Exception:
                delta_str = "時間差解析失敗"

        # 若今日已經有「驗證通過」紀錄且這次也是通過，就不再重複顯示（避免日誌淹沒），只更新時間
        if status == "ok" and prev and prev.get("last_status") == "ok":
            prev["last_checked"] = now_tw.isoformat()
            day_state[key] = prev
            state[date_str] = day_state
            _save_validation_state(state)
            return

        if status == "ok":
            msg = (
                f"🟢 [DAILY-VALIDATION] {date_str} {key} 批量抓取驗證通過 "
                f"(實際 {actual_fetched} 筆, 可接受範圍 {min_acceptable}-{max_acceptable}, "
                f"與上次驗證時間差: {delta_str})"
            )
            logger.info(msg)
        else:
            # 資料不足或異常，一律視為需要重點關注，使用紅色警告
            msg = (
                f"🔴 [DAILY-VALIDATION] {date_str} {key} 批量抓取可能缺資料 "
                f"(實際 {actual_fetched} 筆, 可接受範圍 {min_acceptable}-{max_acceptable}, "
                f"與上次驗證時間差: {delta_str})"
            )
            logger.warning(msg)

        if progress_cb:
            progress_cb(msg)

        day_state[key] = {
            "last_status": status,
            "last_checked": now_tw.isoformat(),
            "actual_fetched": actual_fetched,
            "min_acceptable": min_acceptable,
            "max_acceptable": max_acceptable,
        }
        state[date_str] = day_state
        _save_validation_state(state)
    except Exception as e:
        logger.error(f"❌ 記錄每日批量驗證狀態失敗: {e}")


def _count_db_1m_candles(
    category: str,
    symbol: str,
    start_time: datetime,
    end_time: datetime,
) -> int:
    """從主 DB 統計指定時間範圍內 interval=60 的 K 棒數量。

    僅做 COUNT(*) 查詢，不拉出實際資料，以降低負載。
    """
    core = DatabaseCore()

    # 確保時間具備時區資訊，統一使用 UTC timestamp
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    start_ts = start_time.timestamp()
    end_ts = end_time.timestamp()

    conn = core.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT COUNT(*)
            FROM historical_data
            WHERE category = ? AND symbol = ? AND interval = ?
              AND timestamp >= ? AND timestamp < ?
            """,
            (category, symbol, 60, start_ts, end_ts),
        )
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else 0
    except Exception as e:
        logger.error(f"❌ 主 DB 1m 筆數統計失敗: {symbol}@60 - {e}")
        return 0
    finally:
        conn.close()


class DataValidator:
    """
    資料驗證器 - 負責驗證資料抓取的完整性

    驗證邏輯:
    N = Y - X (結束時間戳 - 開始時間戳)
    預期筆數 = N / K線間隔秒數
    如果預期筆數 != 實際筆數，則觸發錯誤
    """

    def __init__(self):
        self.logger = logger

    def validate_backfill_data_integrity(self,
                                       symbol: str,
                                       interval: str,
                                       start_time: datetime,
                                       end_time: datetime,
                                       actual_inserted: int,
                                       skipped: int = 0,
                                       progress_cb: Optional[Callable] = None) -> Tuple[bool, str]:
        """
        驗證回補資料的完整性

        考慮到Binance API限制：
        - 每次請求最多返回1000筆資料
        - 對於長時間範圍，需要分批請求
        - 使用寬鬆驗證邏輯而不是精確匹配

        Args:
            symbol: 貨幣對符號 (如 'BTCUSDT')
            interval: K線間隔 (如 '1m', '5m', '1h')
            start_time: 開始時間
            end_time: 結束時間
            actual_inserted: 實際插入的資料筆數
            skipped: 跳過筆數 (預設0)
            progress_cb: 進度回調函數

        Returns:
            Tuple[bool, str]: (驗證通過, 訊息)

        Raises:
            DataValidationError: 當資料嚴重不完整時拋出
        """

        try:
            # 確保時間是timezone aware
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            # 轉換為台灣時間顯示
            tw_tz = timezone(timedelta(hours=8))
            start_tw = start_time.astimezone(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
            end_tw = end_time.astimezone(tw_tz).strftime('%Y-%m-%d %H:%M:%S')

            # 計算時間戳
            X = start_time.timestamp()  # 開始時間戳
            Y = end_time.timestamp()    # 結束時間戳

            # 計算 N = Y - X
            N = Y - X

            # 轉換間隔為秒數
            interval_seconds = self._interval_to_seconds(interval)

            if interval_seconds == 0:
                raise ValueError(f"無效的時間間隔: {interval}")

            # 計算理論最大筆數 = N / 間隔秒數
            max_expected = int(N / interval_seconds)

            # 考慮到Binance API限制和分批請求，使用寬鬆驗證
            # 設定可接受的最小筆數為理論值的70%
            min_acceptable = int(max_expected * 0.7)

            # 如果理論筆數超過1000，考慮分批請求的限制
            if max_expected > 1000:
                # 對於長時間範圍，實際筆數可能會因為分批請求而略少於理論值
                # 但不應該少於理論值的80%
                min_acceptable = max(min_acceptable, int(max_expected * 0.8))
            else:
                # 對於短時間範圍，使用更嚴格的驗證（90%）
                min_acceptable = int(max_expected * 0.9)

            # 修正bug：用總抓取筆數 (actual + skipped) 取代 effective（不扣 skipped，邏輯理性：總完整 >= min）
            total_fetched = actual_inserted + skipped  # 新增：總 klines 筆數，從 API 抓取
            effective_inserted = actual_inserted  # 修正：不扣 skipped（actual 已不含它）

            # 顯示驗證資訊（加 total_fetched 顯示，助 debug）
            validation_info = f"""
🔍 回補資料驗證 - {symbol}@{interval}
📅 時間範圍: {start_tw} → {end_tw} (UTC+8)
⏱️ 時間戳範圍: {X:.0f} → {Y:.0f}
📊 時間差異: {N:.0f} 秒
🎯 理論最大筆數: {max_expected} (間隔: {interval_seconds}秒)
✅ 實際插入筆數: {actual_inserted}（跳過 {skipped} 筆，總抓取: {total_fetched}）
🎯 可接受範圍: ≥ {min_acceptable} 筆
"""

            if progress_cb:
                progress_cb(validation_info.strip())

            self.logger.info(f"回補資料驗證 - {symbol}@{interval}: 理論{max_expected}筆, 實際{actual_inserted}筆, 最小可接受{min_acceptable}筆")

            # 驗證筆數是否在可接受範圍內（改用 total_fetched 檢查，理性：確保總完整）
            if total_fetched < min_acceptable:  # 改這裡：用 total（含 skipped），不盯 effective
                # 新增：檢查如果 skipped 多，表示資料已存在，視為正常（不拋錯）
                if skipped >= int(max_expected * 0.9):  # e.g., 90% 已有，理性閾值，避免假失敗
                    warning_msg = f"⚠️ 有效插入筆數低 ({effective_inserted})，但跳過 {skipped} 筆高，表示資料大多已存在。視為驗證通過。"
                    if progress_cb:
                        progress_cb(warning_msg)
                    self.logger.warning(warning_msg)
                    success_msg = f"✅ 回補資料驗證通過 (已有大多數據)! {symbol}@{interval} ({actual_inserted}筆插入, {skipped}筆跳過)"
                    if progress_cb:
                        progress_cb(success_msg)
                    self.logger.info(success_msg)
                    return True, success_msg  # 不拋錯，返回成功

                # 原有錯誤處理（只在 skipped 不高時觸發）
                error_msg = f"❌ 回補資料完整性檢查失敗! {symbol}@{interval} 資料筆數過少"
                detailed_error = f"""
{validation_info}
❌ 驗證結果: 失敗 - 資料筆數過少
💡 可能原因:
   • API資料不完整或中斷
   • 網路連線問題導致部分資料遺失
   • 市場休市期間缺少資料
   • 時間範圍設定錯誤
🔧 建議解決方案:
   • 檢查網路連線穩定性
   • 縮小時間範圍重新執行
   • 確認市場交易時間
   • 查看API狀態和限制
"""

                if progress_cb:
                    progress_cb(detailed_error.strip())

                self.logger.error(f"回補資料驗證失敗: {symbol}@{interval} 實際{actual_inserted}筆 < 最小可接受{min_acceptable}筆")

                # 對於資料嚴重不足的情況，拋出驗證錯誤
                raise DataValidationError(
                    error_msg,
                    max_expected,
                    actual_inserted,
                    symbol,
                    interval
                )

            elif actual_inserted > max_expected * 1.1:
                # 資料過多的警告（但不阻斷操作）
                warning_msg = f"⚠️ 回補資料筆數略多於預期! {symbol}@{interval} 實際{actual_inserted}筆 > 理論{max_expected}筆"
                if progress_cb:
                    progress_cb(warning_msg)
                self.logger.warning(f"回補資料筆數過多: {symbol}@{interval} 實際{actual_inserted}筆 > 理論{max_expected}筆")

            # 驗證通過
            success_msg = f"✅ 回補資料驗證通過! {symbol}@{interval} 資料筆數正常 ({actual_inserted}筆)"
            if progress_cb:
                progress_cb(success_msg)

            self.logger.info(f"回補資料驗證通過: {symbol}@{interval} ({actual_inserted}筆)")

            return True, success_msg

        except DataValidationError:
            raise  # 重新拋出驗證錯誤
        except Exception as e:
            error_msg = f"❌ 回補資料驗證過程發生錯誤: {e}"
            if progress_cb:
                progress_cb(error_msg)
            self.logger.error(f"回補資料驗證錯誤: {e}")
            raise DataValidationError(
                f"驗證過程錯誤: {e}",
                0,
                actual_inserted,
                symbol,
                interval
            )

    def _interval_to_seconds(self, interval: str) -> int:
        """
        將K線間隔字串轉換為秒數

        Args:
            interval: 間隔字串 (如 '1m', '5m', '1h', '1d')

        Returns:
            int: 秒數
        """
        interval = interval.lower().strip()

        # 分鐘
        if interval.endswith('m'):
            return int(interval[:-1]) * 60
        # 小時
        elif interval.endswith('h'):
            return int(interval[:-1]) * 3600
        # 天
        elif interval.endswith('d'):
            return int(interval[:-1]) * 86400
        # 秒
        elif interval.endswith('s'):
            return int(interval[:-1])
        else:
            raise ValueError(f"不支援的時間間隔格式: {interval}")

    def validate_batch_fetch_integrity(self,
                                      symbol: str,
                                      interval: str,
                                      start_time: datetime,
                                      end_time: datetime,
                                      actual_fetched: int,
                                      progress_cb: Optional[Callable] = None) -> Tuple[bool, str]:
        """
        驗證批量抓取資料的完整性 (簡化版本，用於1分鐘批量抓取)

        Args:
            symbol: 貨幣對符號
            interval: 間隔 (通常是 '1m')
            start_time: 開始時間
            end_time: 結束時間
            actual_fetched: 實際抓取的筆數
            progress_cb: 進度回調

        Returns:
            Tuple[bool, str]: (驗證通過, 訊息)
        """
        try:
            # 對於批量1分鐘抓取，我們使用更寬鬆的驗證邏輯
            # 因為可能會有資料重疊或市場休市等因素

            # 計算理論最大筆數
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            if end_time.tzinfo is None:
                end_time = end_time.replace(tzinfo=timezone.utc)

            X = start_time.timestamp()
            Y = end_time.timestamp()
            N = Y - X

            interval_seconds = self._interval_to_seconds(interval)
            max_expected = int(N / interval_seconds)

            # 批量抓取允許一定的誤差範圍 (90%-110%)
            min_acceptable = int(max_expected * 0.9)
            max_acceptable = int(max_expected * 1.1)

            # 轉換為台灣時間顯示
            tw_tz = timezone(timedelta(hours=8))
            start_tw = start_time.astimezone(tw_tz).strftime('%Y-%m-%d %H:%M:%S')
            end_tw = end_time.astimezone(tw_tz).strftime('%Y-%m-%d %H:%M:%S')

            validation_info = f"""
🔍 批量抓取驗證 - {symbol}@{interval}
📅 時間範圍: {start_tw} → {end_tw} (UTC+8)
📊 理論最大筆數: {max_expected}
✅ 實際抓取筆數: {actual_fetched}
🎯 可接受範圍: {min_acceptable} - {max_acceptable}
"""

            if progress_cb:
                progress_cb(validation_info.strip())

            if actual_fetched < min_acceptable:
                warning_msg = f"⚠️ 批量抓取資料可能不完整! {symbol} 抓取筆數過少 ({actual_fetched} < {min_acceptable})"
                if progress_cb:
                    progress_cb(warning_msg)
                self.logger.warning(f"批量抓取資料可能不完整: {symbol} 預期至少{min_acceptable}筆, 實際{actual_fetched}筆")
                # 記錄每日驗證結果（視為警告 / 缺資料）
                _record_daily_batch_validation(
                    symbol,
                    interval,
                    start_time,
                    end_time,
                    "warning",
                    actual_fetched,
                    min_acceptable,
                    max_acceptable,
                    progress_cb,
                )
                return False, warning_msg

            elif actual_fetched > max_acceptable:
                warning_msg = f"⚠️ 批量抓取資料可能過多! {symbol} 抓取筆數過多 ({actual_fetched} > {max_acceptable})"
                if progress_cb:
                    progress_cb(warning_msg)
                self.logger.warning(f"批量抓取資料可能過多: {symbol} 預期最多{max_acceptable}筆, 實際{actual_fetched}筆")
                # 同樣記錄為需要關注的狀態
                _record_daily_batch_validation(
                    symbol,
                    interval,
                    start_time,
                    end_time,
                    "warning",
                    actual_fetched,
                    min_acceptable,
                    max_acceptable,
                    progress_cb,
                )
                return False, warning_msg

            else:
                success_msg = f"✅ 批量抓取驗證通過! {symbol} 資料筆數正常 ({actual_fetched}筆)"
                if progress_cb:
                    progress_cb(success_msg)
                self.logger.info(f"批量抓取驗證通過: {symbol} ({actual_fetched}筆)")
                # 記錄每日驗證通過狀態
                _record_daily_batch_validation(
                    symbol,
                    interval,
                    start_time,
                    end_time,
                    "ok",
                    actual_fetched,
                    min_acceptable,
                    max_acceptable,
                    progress_cb,
                )
                return True, success_msg

        except Exception as e:
            error_msg = f"❌ 批量抓取驗證錯誤: {e}"
            if progress_cb:
                progress_cb(error_msg)
            self.logger.error(f"批量抓取驗證錯誤: {e}")
            return False, error_msg

def validate_daily_1m_completion(
    category: str,
    symbol: str,
    start_time: datetime,
    end_time: datetime,
    api_fetched: int,
    progress_cb: Optional[Callable] = None,
) -> Tuple[bool, str]:
    """綜合驗證某天某貨幣對的 1 分鐘資料是否完成（僅累積結果，不直接大量輸出）。

    驗證步驟：
    1) 依時間範圍計算理論最大筆數與可接受範圍；
    2) 比對本次 API 抓取新增筆數 api_fetched 是否在可接受範圍內（API_ok）；
    3) 從主 DB COUNT(*) 統計 interval=60 的實際 K 棒筆數，判斷 DB_ok；
    4) 只將結果寫入 _daily_1m_results，實際輸出交由 summarize_daily_1m_results 統一處理。
    """

    validator = _global_validator

    # 時間規範為 timezone-aware
    if start_time.tzinfo is None:
        start_time = start_time.replace(tzinfo=timezone.utc)
    if end_time.tzinfo is None:
        end_time = end_time.replace(tzinfo=timezone.utc)

    X = start_time.timestamp()
    Y = end_time.timestamp()
    N = Y - X

    # 計算理論最大筆數與可接受區間（共用給 API / DB）
    interval_seconds = validator._interval_to_seconds("1m")
    max_expected = int(N / interval_seconds)
    min_acceptable = int(max_expected * 0.9)
    max_acceptable = int(max_expected * 1.1)

    # API 驗證：本次新增筆數是否在可接受範圍內
    api_ok = min_acceptable <= api_fetched <= max_acceptable

    # DB 驗證：主 DB 1m 實際筆數
    db_count = _count_db_1m_candles(category, symbol, start_time, end_time)
    db_ok = min_acceptable <= db_count <= max_acceptable

    # 將結果暫存，供後續總結輸出使用
    _daily_1m_results[symbol] = {
        "api_ok": api_ok,
        "db_ok": db_ok,
        "api_fetched": api_fetched,
        "db_count": db_count,
        "min_acceptable": min_acceptable,
        "max_acceptable": max_acceptable,
    }

    # 僅回傳整體結果供呼叫端需要時使用；實際說明由 summarize_daily_1m_results 輸出
    overall_ok = api_ok and db_ok
    if overall_ok:
        final_msg = f"{symbol}@1m 今日 1 分鐘資料驗證通過 (API & DB 均在可接受範圍內)"
    else:
        final_msg = f"{symbol}@1m 今日 1 分鐘資料尚未完全完成 (API 通過: {api_ok}, DB 通過: {db_ok})"

    return overall_ok, final_msg


def reset_daily_1m_summary() -> None:
    """重置本次最新 1 分鐘驗證結果暫存（每次批量抓取前呼叫）。"""
    global _daily_1m_results
    _daily_1m_results = {}


def summarize_daily_1m_results(
    start_time: datetime,
    end_time: datetime,
    progress_cb: Optional[Callable] = None,
) -> None:
    """將本次批量 1 分鐘驗證結果彙總並輸出簡潔總結。

    - 真警報: DB 1m 筆數不在合理範圍內 (db_ok=False)，可能真的缺 K 棒；
    - 假警報: DB 1m 筆數正常，但本次 API 抓取筆數偏少 (api_ok=False, db_ok=True)，屬複檢提醒；
    - 完全通過: API & DB 均在合理範圍內。
    """

    if not _daily_1m_results:
        return

    tw_tz = timezone(timedelta(hours=8))
    start_tw = start_time.astimezone(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
    end_tw = end_time.astimezone(tw_tz).strftime("%Y-%m-%d %H:%M:%S")

    real_alerts: Dict[str, Dict[str, Any]] = {}
    pseudo_alerts: Dict[str, Dict[str, Any]] = {}
    fully_ok: List[str] = []

    for sym, info in _daily_1m_results.items():
        api_ok = info.get("api_ok", False)
        db_ok = info.get("db_ok", False)
        if not db_ok:
            real_alerts[sym] = info
        elif db_ok and not api_ok:
            pseudo_alerts[sym] = info
        else:
            fully_ok.append(sym)

    lines: List[str] = []
    lines.append("====== 今日 1 分鐘資料驗證總結 (最新批量抓取) ======")
    lines.append(f"📅 檢查時間範圍: {start_tw} → {end_tw} (UTC+8)")
    lines.append("")

    # 真警報：DB 筆數不在合理範圍
    if real_alerts:
        lines.append(f"🔴 真警報 (DB 1m 資料不足或異常): 共 {len(real_alerts)} 檔")
        for sym in sorted(real_alerts.keys()):
            info = real_alerts[sym]
            db_count = info["db_count"]
            min_acc = info["min_acceptable"]
            max_acc = info["max_acceptable"]
            lines.append(f"   - {sym}: DB 僅 {db_count} 筆，合理範圍 {min_acc}-{max_acc} (今日 1m 可能缺 K 棒)")
        lines.append("   建議：對以上交易對重新回補今日 1 分鐘資料，或檢查 API / 時間範圍設定是否正確。")
    else:
        lines.append("🟢 真警報: 0 檔（所有檢查到的交易對在 DB 的 1m 筆數都在合理範圍內）")
    lines.append("")

    # 假警報：DB 正常，本次 API 抓取少（複檢提醒）
    if pseudo_alerts:
        lines.append(f"🟡 假警報 / 複檢提醒 (DB 已齊，本次 API 抓取偏少): 共 {len(pseudo_alerts)} 檔")
        syms = sorted(pseudo_alerts.keys())
        lines.append("   交易對列表: " + ", ".join(syms))
        lines.append("   說明：")
        lines.append("   - 這些交易對在主 DB 中的 1 分鐘 K 棒數量已在合理範圍內，代表今天資料整體是齊的。")
        lines.append("   - 但本次『最新 1 分鐘抓取』新增的筆數很少或為 0，屬於複檢用的假警報。")
        lines.append("   - 常見情況：之前的回補已補齊今天資料，或這段時間市場沒有新成交。")
    else:
        lines.append("🟡 假警報 / 複檢提醒: 0 檔")
    lines.append("")

    lines.append(f"✅ API & DB 同時通過的交易對數量: {len(fully_ok)} 檔")

    summary = "\n".join(lines)
    if progress_cb:
        # 由呼叫方（例如 MultiSymbolMonitor）統一負責輸出，避免在終端機出現兩份相同總結
        progress_cb(summary)
    else:
        # 單獨呼叫時，才直接由 data_validator logger 輸出
        logger.info(summary)


# 全域驗證器實例
_global_validator = DataValidator()


def get_data_validator() -> DataValidator:
    """取得全域資料驗證器實例"""
    return _global_validator


def validate_backfill_integrity(symbol: str, interval: str, start_time: datetime,
                               end_time: datetime, actual_inserted: int,
                               skipped: int = 0,
                               progress_cb: Optional[Callable] = None) -> Tuple[bool, str]:
    """驗證回補資料完整性 (便捷函數)"""
    return _global_validator.validate_backfill_data_integrity(
        symbol, interval, start_time, end_time, actual_inserted, skipped, progress_cb
    )


def validate_batch_fetch_integrity(symbol: str, interval: str, start_time: datetime,
                                  end_time: datetime, actual_fetched: int,
                                  progress_cb: Optional[Callable] = None) -> Tuple[bool, str]:
    """驗證批量抓取完整性 (便捷函數)"""
    return _global_validator.validate_batch_fetch_integrity(
        symbol, interval, start_time, end_time, actual_fetched, progress_cb
    )


# 模組載入時的初始化檢查
if __name__ != "__main__":
    logger.info("🔒 資料驗證模組已載入 - 此為核心驗證模組，請勿隨意修改")
    logger.info("📋 驗證邏輯: N = Y - X, 預期筆數 = N / 間隔秒數")
