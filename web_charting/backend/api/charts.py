"""
charts.py - Charts API Routes
提供 K線圖資料的 API 端點
"""
import logging
import traceback
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from database.chart_db import chart_db
from database.main_db_connector import main_db
from web_charting_backend_config import config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/charts", tags=["charts"])


# ========== Response Models ==========

class CandleResponse(BaseModel):
    """K線資料回應模型"""
    symbol: str
    interval: int
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float
    data_source: str
    priority: int
    
    class Config:
        from_attributes = True


class CandlesListResponse(BaseModel):
    """K線列表回應"""
    symbol: str
    interval: int
    data_source_filter: Optional[str] = None
    count: int
    candles: List[CandleResponse]
    time_range: dict = Field(
        description="時間範圍",
        example={"start": "2025-11-16 00:00:00", "end": "2025-11-16 23:59:59"}
    )


# ========== Internal Helpers (sub-minute handling) ==========


def _normalize_main_db_candles(candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not candles:
        return candles
    normalized: List[Dict[str, Any]] = []
    real_priority = config.chart.DATA_PRIORITY.get("real", config.chart.DATA_PRIORITY.get("test", 5))
    for c in candles:
        ds = c.get("data_source") or "real"
        if ds == "real_no-trade-fill":
            c = dict(c)
            c["data_source"] = "real"
            c["priority"] = real_priority
        normalized.append(c)
    return normalized


def _calculate_time_window(
    interval: int,
    limit: int,
    start_time: Optional[float],
    end_time: Optional[float],
) -> Dict[str, float]:
    """計算子分鐘時間框架使用的查詢時間範圍（最多回溯 24 小時）。"""
    now_ts = datetime.now(timezone.utc).timestamp()
    effective_end = end_time if end_time is not None else now_ts

    if start_time is not None:
        effective_start = start_time
    else:
        # 對於子分鐘時間框架，預設回溯整整 24 小時，之後再在記憶體中用 limit 做裁剪
        # 這樣即使使用者稍晚才開圖，也能看到最近一天內的 1 秒資料
        window_seconds = 86400  # 固定 24 小時
        effective_start = max(0.0, effective_end - window_seconds)

    return {"start": effective_start, "end": effective_end}


def _get_1s_candles_with_backfill(
    symbol: str,
    start_ts: float,
    end_ts: float,
    limit: int,
    data_source_filter: Optional[str],
) -> List[Dict[str, Any]]:
    """嘗試使用 1 分鐘資料補齊 1 秒缺口。

    若主 DB 在指定時間範圍內沒有 1 分鐘資料，則回傳空列表，
    讓呼叫端可以回退使用原本的 1 秒 raw 資料邏輯，而不是直接拋出錯誤。
    """
    candles_1m = main_db.fetch_candles(
        category="crypto",
        symbol=symbol,
        interval=60,
        start_time=start_ts,
        end_time=end_ts,
        data_source="real",
    )
    if not candles_1m:
        logger.warning(
            "_get_1s_candles_with_backfill: 主資料庫沒有 1 分鐘資料，改由呼叫端回退使用 raw 1 秒資料",
        )
        return []
    raw_1s = main_db.fetch_candles(
        category="crypto",
        symbol=symbol,
        interval=1,
        start_time=start_ts,
        end_time=end_ts,
        data_source=None,
    )
    raw_1s = _normalize_main_db_candles(raw_1s)
    real_1s_by_ts: Dict[int, Dict[str, Any]] = {}
    for c in raw_1s:
        source = c.get("data_source") or "real"
        if source != "real":
            continue
        ts = int(c["timestamp"])
        if ts not in real_1s_by_ts:
            real_1s_by_ts[ts] = c
    all_1s: List[Dict[str, Any]] = []
    end_sec = int(end_ts)
    for m in candles_1m:
        minute_start = int(m["timestamp"])
        minute_close = float(m["close"])
        minute_volume = float(m.get("volume") or 0.0)
        second_range = [s for s in range(minute_start, minute_start + 60) if s <= end_sec]
        if not second_range:
            continue
        real_vol_sum = 0.0
        for s in second_range:
            real_c = real_1s_by_ts.get(s)
            if real_c is not None:
                real_vol_sum += float(real_c.get("volume") or 0.0)
        missing_secs = [s for s in second_range if s not in real_1s_by_ts]
        missing_count = len(missing_secs)
        remaining_vol = minute_volume - real_vol_sum
        if remaining_vol < 0.0:
            remaining_vol = 0.0
        fake_vol = remaining_vol / missing_count if missing_count > 0 else 0.0
        for s in second_range:
            real_c = real_1s_by_ts.get(s)
            if real_c is not None:
                c = dict(real_c)
                c["timestamp"] = float(int(c["timestamp"]))
                all_1s.append(c)
            else:
                c = {
                    "symbol": symbol,
                    "interval": 1,
                    "timestamp": float(s),
                    "open": minute_close,
                    "high": minute_close,
                    "low": minute_close,
                    "close": minute_close,
                    "volume": fake_vol,
                    "data_source": "interpolated",
                    "priority": config.chart.DATA_PRIORITY.get("interpolated", config.chart.DATA_PRIORITY.get("test", 5)),
                }
                all_1s.append(c)
    all_1s.sort(key=lambda x: x["timestamp"])
    if data_source_filter:
        all_1s = [c for c in all_1s if c.get("data_source") == data_source_filter]
    if len(all_1s) > limit:
        all_1s = all_1s[-limit:]
    return all_1s


def _select_best_1s_candles(one_sec_candles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """同一秒可能存在多個 data_source，按優先級選出每秒最佳的一筆。"""
    best_by_ts: Dict[int, Dict[str, Any]] = {}

    for c in one_sec_candles:
        ts = int(c["timestamp"])
        source = c.get("data_source") or "real"
        priority = config.chart.DATA_PRIORITY.get(source, config.chart.DATA_PRIORITY.get("test", 5))

        existing = best_by_ts.get(ts)
        if existing is None or priority < existing.get("priority", 999):
            new_c = dict(c)
            new_c["timestamp"] = ts
            new_c["data_source"] = source
            new_c["priority"] = priority
            best_by_ts[ts] = new_c

    return [best_by_ts[t] for t in sorted(best_by_ts.keys())]


def _aggregate_1s_to_interval(
    one_sec_candles: List[Dict[str, Any]], target_interval: int
) -> List[Dict[str, Any]]:
    """將 1 秒 K 線在記憶體中聚合成指定秒級別（2/5/10/15/30s）。"""
    if not one_sec_candles:
        return []

    buckets: Dict[int, Dict[str, Any]] = {}

    for c in one_sec_candles:
        ts = int(c["timestamp"])
        bucket_start = (ts // target_interval) * target_interval

        b = buckets.get(bucket_start)
        if b is None:
            b = {
                "symbol": c["symbol"],
                "interval": target_interval,
                "timestamp": bucket_start,
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
                "volume": float(c.get("volume") or 0.0),
                "sources": {c.get("data_source") or "real"},
            }
        else:
            price_high = float(c["high"])
            price_low = float(c["low"])
            price_close = float(c["close"])
            vol = float(c.get("volume") or 0.0)

            b["high"] = max(b["high"], price_high)
            b["low"] = min(b["low"], price_low)
            b["close"] = price_close
            b["volume"] += vol
            b["sources"].add(c.get("data_source") or "real")

        buckets[bucket_start] = b

    result: List[Dict[str, Any]] = []
    for bucket_start in sorted(buckets.keys()):
        b = buckets[bucket_start]

        # Web 端約定：所有由 1 秒聚合出的子分鐘 K 線一律視為 real 資料
        data_source = "real"
        priority = config.chart.DATA_PRIORITY.get("real", config.chart.DATA_PRIORITY.get("test", 5))

        result.append(
            {
                "symbol": b["symbol"],
                "interval": target_interval,
                "timestamp": float(bucket_start),
                "open": b["open"],
                "high": b["high"],
                "low": b["low"],
                "close": b["close"],
                "volume": b["volume"],
                "data_source": data_source,
                "priority": priority,
            }
        )

    return result


def _build_subminute_response(
    symbol: str,
    interval: int,
    limit: int,
    start_time: Optional[float],
    end_time: Optional[float],
    data_source: Optional[str],
) -> CandlesListResponse:
    """處理 interval < 60 秒的情況：

    - interval == 1: 從主DB讀取 1 秒資料（不聚合）
    - interval in {2,5,10,15,30}: 在記憶體中由 1 秒資料聚合
    """
    symbol_up = symbol.upper()

    # 計算查詢時間範圍
    # 對所有子分鐘 timeframe（1,2,5,10,15,30s），在未指定 start/end 時，
    # 一律以主 DB 1 秒資料的最新時間為基準，避免系統時間不準或時區問題導致抓不到最新資料。
    if start_time is None and end_time is None:
        data_range = main_db.get_data_range(
            category="crypto",
            symbol=symbol_up,
            interval=1,
        )

        if data_range and data_range.get("max_time") is not None:
            end_ts = float(data_range["max_time"])
            window_seconds = 86400.0  # 固定回溯 24 小時
            start_ts = max(0.0, end_ts - window_seconds)
        else:
            # 如果 DB 裡沒有資料，退回原本的時間窗計算邏輯
            tw = _calculate_time_window(interval, limit, start_time, end_time)
            start_ts = tw["start"]
            end_ts = tw["end"]
    else:
        tw = _calculate_time_window(interval, limit, start_time, end_time)
        start_ts = tw["start"]
        end_ts = tw["end"]

    # 根據 limit 與 interval 進一步收窄時間窗，避免每次請求都掃描過多 1 秒資料
    window_by_limit = float(limit * max(interval, 1))
    if window_by_limit > 0:
        # 僅保留最後 window_by_limit 秒的資料（不超過前面計算出的時間窗）
        if end_ts - start_ts > window_by_limit:
            start_ts = end_ts - window_by_limit

    # 這裡不再在圖表 API 直接使用 1 分鐘資料補齊 1 秒，
    # 避免主 DB 缺少 1 分鐘資料時，1 秒圖完全畫不出任何 K 棒。
    # 仍保留 _get_1s_candles_with_backfill 給其他同步 API 使用。

    # 先抓 1 秒資料作為基礎
    # 對 1 秒本身，先抓全部，再在記憶體中套用 data_source 過濾與正規化
    if interval == 1 and data_source is not None:
        one_sec_source_filter = None
    else:
        one_sec_source_filter = data_source if interval == 1 else None

    raw_1s = main_db.fetch_candles(
        category="crypto",
        symbol=symbol_up,
        interval=1,
        start_time=start_ts,
        end_time=end_ts,
        data_source=one_sec_source_filter,
    )
    raw_1s = _normalize_main_db_candles(raw_1s)

    if interval == 1:
        # 直接返回 1 秒 K 線（按時間排序，限制筆數）
        if data_source is not None:
            raw_1s = [c for c in raw_1s if c.get("data_source") == data_source]
        if not raw_1s:
            return CandlesListResponse(
                symbol=symbol_up,
                interval=interval,
                data_source_filter=data_source,
                count=0,
                candles=[],
                time_range={},
            )

        raw_1s_sorted = sorted(raw_1s, key=lambda c: c["timestamp"])
        raw_1s_sorted = raw_1s_sorted[-limit:]

        candle_responses = [CandleResponse(**c) for c in raw_1s_sorted]

        time_range = {
            "start": datetime.fromtimestamp(raw_1s_sorted[0]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "end": datetime.fromtimestamp(raw_1s_sorted[-1]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "start_timestamp": raw_1s_sorted[0]["timestamp"],
            "end_timestamp": raw_1s_sorted[-1]["timestamp"],
        }

        return CandlesListResponse(
            symbol=symbol_up,
            interval=interval,
            data_source_filter=data_source,
            count=len(candle_responses),
            candles=candle_responses,
            time_range=time_range,
        )

    # interval in {2,5,10,15,30}：用 1 秒資料在記憶體中做聚合
    if not raw_1s:
        logger.warning(f"⚠️ 無 1 秒資料可供聚合: {symbol_up}@{interval}s")
        return CandlesListResponse(
            symbol=symbol_up,
            interval=interval,
            data_source_filter=data_source,
            count=0,
            candles=[],
            time_range={},
        )

    best_1s = _select_best_1s_candles(raw_1s)
    aggregated = _aggregate_1s_to_interval(best_1s, interval)

    # 若呼叫方有指定 data_source，則在聚合後做過濾
    if data_source:
        aggregated = [c for c in aggregated if c["data_source"] == data_source]

    if not aggregated:
        return CandlesListResponse(
            symbol=symbol_up,
            interval=interval,
            data_source_filter=data_source,
            count=0,
            candles=[],
            time_range={},
        )

    # 限制筆數並排序
    aggregated_sorted = sorted(aggregated, key=lambda c: c["timestamp"])
    aggregated_sorted = aggregated_sorted[-limit:]

    candle_responses = [CandleResponse(**c) for c in aggregated_sorted]

    time_range = {
        "start": datetime.fromtimestamp(aggregated_sorted[0]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        "end": datetime.fromtimestamp(aggregated_sorted[-1]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        "start_timestamp": aggregated_sorted[0]["timestamp"],
        "end_timestamp": aggregated_sorted[-1]["timestamp"],
    }

    return CandlesListResponse(
        symbol=symbol_up,
        interval=interval,
        data_source_filter=data_source,
        count=len(candle_responses),
        candles=candle_responses,
        time_range=time_range,
    )


def _build_realtime_from_1s(
    symbol: str,
    interval: int,
    limit: int,
    start_time: Optional[float],
    end_time: Optional[float],
    data_source: Optional[str],
) -> CandlesListResponse:
    symbol_up = symbol.upper()

    if start_time is None and end_time is None:
        data_range = main_db.get_data_range(
            category="crypto",
            symbol=symbol_up,
            interval=1,
        )

        if data_range and data_range.get("max_time") is not None:
            end_ts = float(data_range["max_time"])
            window_seconds = 86400.0
            start_ts = max(0.0, end_ts - window_seconds)
        else:
            tw = _calculate_time_window(interval, limit, start_time, end_time)
            start_ts = tw["start"]
            end_ts = tw["end"]
    else:
        tw = _calculate_time_window(interval, limit, start_time, end_time)
        start_ts = tw["start"]
        end_ts = tw["end"]

    raw_1s = main_db.fetch_candles(
        category="crypto",
        symbol=symbol_up,
        interval=1,
        start_time=start_ts,
        end_time=end_ts,
        data_source=None,
    )
    raw_1s = _normalize_main_db_candles(raw_1s)

    if not raw_1s:
        logger.warning(
            f"⚠️ 無 1 秒資料可供即時聚合: {symbol_up}@{interval}s"
        )
        return CandlesListResponse(
            symbol=symbol_up,
            interval=interval,
            data_source_filter=data_source,
            count=0,
            candles=[],
            time_range={},
        )

    best_1s = _select_best_1s_candles(raw_1s)
    aggregated = _aggregate_1s_to_interval(best_1s, interval)

    if data_source:
        aggregated = [c for c in aggregated if c["data_source"] == data_source]

    if not aggregated:
        return CandlesListResponse(
            symbol=symbol_up,
            interval=interval,
            data_source_filter=data_source,
            count=0,
            candles=[],
            time_range={},
        )

    aggregated_sorted = sorted(aggregated, key=lambda c: c["timestamp"])
    aggregated_sorted = aggregated_sorted[-limit:]

    candle_responses = [CandleResponse(**c) for c in aggregated_sorted]

    time_range = {
        "start": datetime.fromtimestamp(aggregated_sorted[0]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        "end": datetime.fromtimestamp(aggregated_sorted[-1]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
        "start_timestamp": aggregated_sorted[0]["timestamp"],
        "end_timestamp": aggregated_sorted[-1]["timestamp"],
    }

    return CandlesListResponse(
        symbol=symbol_up,
        interval=interval,
        data_source_filter=data_source,
        count=len(candle_responses),
        candles=candle_responses,
        time_range=time_range,
    )


# ========== API Endpoints ==========

@router.get("/candles", response_model=CandlesListResponse)
async def get_candles(
    symbol: str = Query(..., description="交易對，如 BTCUSDT"),
    interval: int = Query(..., description="時間框架（秒），如 60=1分鐘"),
    limit: int = Query(
        default=config.chart.DEFAULT_CANDLES_LIMIT,
        le=config.chart.MAX_CANDLES_LIMIT,
        description=f"返回數量（最大{config.chart.MAX_CANDLES_LIMIT}）"
    ),
    start_time: Optional[float] = Query(
        default=None,
        description="開始時間（Unix timestamp）"
    ),
    end_time: Optional[float] = Query(
        default=None,
        description="結束時間（Unix timestamp）"
    ),
    data_source: Optional[str] = Query(
        default=None,
        description="資料來源過濾（real/Aggregation/interpolated）"
    ),
    realtime: bool = Query(
        default=False,
        description="是否使用主 DB 1 秒資料即時聚合（目前僅對 interval=60 啟用）",
    ),
):
    """
    獲取 K線資料
    
    **參數說明**:
    - **symbol**: 交易對名稱（如 BTCUSDT）
    - **interval**: 時間框架（秒為單位）
      - 1 = 1秒
      - 60 = 1分鐘
      - 3600 = 1小時
    - **limit**: 最多返回多少根K線
    - **start_time**: 開始時間（可選）
    - **end_time**: 結束時間（可選）
    - **data_source**: 只返回特定來源的資料（可選）
    
    **返回**:
    - K線列表（按時間從舊到新排序）
    """
    try:
        logger.info(
            f"📊 請求K線: {symbol}@{interval}s "
            f"limit={limit} source={data_source}"
        )

        # ========= 子分鐘時間框架 =========
        # 1 秒 timeframe 在監控即時模式下，直接使用主 DB 的 1 秒資料；
        # 其他情況仍優先使用 Web Chart DB 中已補齊的 1 秒資料，Web 無資料時才回退到主 DB。
        if interval < 60:
            # 監控模式的 1 秒即時圖：直接走主 DB 1 秒邏輯（避免卡在 Web DB 舊資料上），
            # 並以「現在時間」為基準計算查詢時間窗，確保每秒都能看到最新的 K 棒。
            if interval == 1 and realtime:
                try:
                    now_ts = datetime.now(timezone.utc).timestamp()
                    window_seconds = float(limit * max(interval, 1))
                    start_ts = max(0.0, now_ts - window_seconds)

                    return _build_subminute_response(
                        symbol=symbol,
                        interval=interval,
                        limit=limit,
                        start_time=start_ts,
                        end_time=now_ts,
                        data_source=data_source,
                    )
                except HTTPException:
                    raise
                except Exception as e:
                    logger.error(f"❌ 監控模式 1 秒即時資料處理失敗: {e}")
                    traceback.print_exc()
                    raise HTTPException(status_code=500, detail=str(e))

            # 非即時模式的 1 秒 timeframe：優先使用 Web DB 的 1 秒資料
            if interval == 1 and not realtime:
                try:
                    candles = chart_db.query_candles(
                        symbol=symbol.upper(),
                        interval=1,
                        start_time=start_time,
                        end_time=end_time,
                        data_source=None,
                        limit=limit,
                    )

                    if candles:
                        candle_responses = [CandleResponse.from_orm(c) for c in candles]

                        time_range = {
                            "start": datetime.fromtimestamp(candles[0].timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                            "end": datetime.fromtimestamp(candles[-1].timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                            "start_timestamp": candles[0].timestamp,
                            "end_timestamp": candles[-1].timestamp,
                        }

                        logger.info(f"✅ 從 Web DB 返回 {len(candles)} 根 1 秒K線")

                        return CandlesListResponse(
                            symbol=symbol.upper(),
                            interval=interval,
                            data_source_filter=data_source,
                            count=len(candles),
                            candles=candle_responses,
                            time_range=time_range,
                        )
                except Exception as e:
                    logger.error(f"⚠️ 從 Web DB 讀取 1 秒資料失敗，回退到主 DB 路徑: {e}")

            # 其餘子分鐘 timeframe 或 Web DB 無 1 秒資料時，使用主 DB 1 秒資料邏輯
            try:
                return _build_subminute_response(
                    symbol=symbol,
                    interval=interval,
                    limit=limit,
                    start_time=start_time,
                    end_time=end_time,
                    data_source=data_source,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ 子分鐘資料處理失敗: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

        # ========= 1 分鐘 timeframe 在即時模式下：用主 DB 1 秒資料聚合出 1 分鐘 =========
        if realtime and interval == 60:
            try:
                return _build_realtime_from_1s(
                    symbol=symbol,
                    interval=interval,
                    limit=limit,
                    start_time=start_time,
                    end_time=end_time,
                    data_source=data_source,
                )
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"❌ 即時資料處理失敗: {e}")
                traceback.print_exc()
                raise HTTPException(status_code=500, detail=str(e))

        # ========= 一般情況：走 Chart DB =========

        candles = chart_db.query_candles(
            symbol=symbol.upper(),
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            data_source=data_source,
            limit=limit,
        )

        if not candles:
            logger.warning(f"⚠️ 無K線資料: {symbol}@{interval}s")
            return CandlesListResponse(
                symbol=symbol.upper(),
                interval=interval,
                data_source_filter=data_source,
                count=0,
                candles=[],
                time_range={},
            )

        candle_responses = [CandleResponse.from_orm(candle) for candle in candles]

        time_range = {
            "start": datetime.fromtimestamp(candles[0].timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            "end": datetime.fromtimestamp(candles[-1].timestamp).strftime('%Y-%m-%d %H:%M:%S'),
            "start_timestamp": candles[0].timestamp,
            "end_timestamp": candles[-1].timestamp,
        }

        logger.info(f"✅ 返回 {len(candles)} 根K線")

        return CandlesListResponse(
            symbol=symbol.upper(),
            interval=interval,
            data_source_filter=data_source,
            count=len(candles),
            candles=candle_responses,
            time_range=time_range,
        )

    except Exception as e:
        logger.error(f"❌ 獲取K線失敗: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candles/1s-web-today", response_model=CandlesListResponse)
async def get_1s_candles_web_today(
    symbol: str = Query(..., description="交易對，如 BTCUSDT"),
    limit: int = Query(
        default=2000,
        le=config.chart.MAX_CANDLES_LIMIT,
        description="每次回補的最大返回數量",
    ),
    end_before: Optional[float] = Query(
        default=None,
        description="僅回傳早於此時間戳的資料（Unix timestamp）",
    ),
):
    try:
        symbol_up = symbol.upper()

        taipei_tz = timezone(timedelta(hours=8))
        now_taipei = datetime.now(tz=taipei_tz)
        today_start = now_taipei.replace(hour=0, minute=0, second=0, microsecond=0)
        start_utc = today_start.astimezone(timezone.utc)
        day_start_ts = start_utc.timestamp()

        if end_before is not None:
            end_ts = float(end_before)
        else:
            end_ts = datetime.now(tz=timezone.utc).timestamp()

        if end_ts <= day_start_ts:
            return CandlesListResponse(
                symbol=symbol_up,
                interval=1,
                data_source_filter=None,
                count=0,
                candles=[],
                time_range={},
            )

        candles = chart_db.query_candles(
            symbol=symbol_up,
            interval=1,
            start_time=day_start_ts,
            end_time=end_ts,
            data_source=None,
            limit=limit,
        )

        if not candles:
            return CandlesListResponse(
                symbol=symbol_up,
                interval=1,
                data_source_filter=None,
                count=0,
                candles=[],
                time_range={},
            )

        candle_responses = [CandleResponse.from_orm(c) for c in candles]

        time_range = {
            "start": datetime.fromtimestamp(candles[0].timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "end": datetime.fromtimestamp(candles[-1].timestamp).strftime("%Y-%m-%d %H:%M:%S"),
            "start_timestamp": candles[0].timestamp,
            "end_timestamp": candles[-1].timestamp,
        }

        return CandlesListResponse(
            symbol=symbol_up,
            interval=1,
            data_source_filter=None,
            count=len(candle_responses),
            candles=candle_responses,
            time_range=time_range,
        )

    except Exception as e:
        logger.error(f"❌ 獲取 1 秒 Web 當日資料失敗: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timeframes")
async def get_supported_timeframes():
    """
    獲取支持的時間框架列表
    
    **返回**:
    - 時間框架列表及其顯示名稱
    """
    try:
        return {
            "timeframes": [
                {
                    "seconds": tf,
                    "label": config.chart.TIMEFRAME_LABELS.get(tf, f"{tf}s")
                }
                for tf in config.chart.TIMEFRAMES
            ]
        }
    except Exception as e:
        logger.error(f"❌ 獲取時間框架失敗: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbols")
async def get_available_symbols():
    """
    獲取可用的交易對列表
    
    **返回**:
    - 已同步的交易對列表
    """
    try:
        from database.main_db_connector import main_db
        
        # 確保已初始化（但不會重複初始化）
        if not hasattr(main_db, '_initialized') or not main_db._initialized:
            main_db.initialize()
        
        symbols = main_db.get_available_symbols('crypto')
        
        logger.info(f"✅ 返回 {len(symbols)} 個交易對")
        
        return {
            "category": "crypto",
            "count": len(symbols),
            "symbols": symbols
        }
        
    except Exception as e:
        logger.error(f"❌ 獲取交易對列表失敗: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/data-sources")
async def get_data_sources():
    """
    獲取資料來源類型及其優先級
    
    **返回**:
    - 資料來源列表及優先級
    """
    return {
        "sources": [
            {
                "name": source,
                "priority": priority,
                "description": {
                    "real": "真實數據（最高優先級）",
                    "Aggregation": "聚合數據",
                    "interpolated": "插值數據",
                    "inferior-Aggregation": "低質量聚合",
                    "test": "測試數據（最低優先級）"
                }.get(source, "")
            }
            for source, priority in config.chart.DATA_PRIORITY.items()
        ]
    }


@router.get("/stats/{symbol}/{interval}")
async def get_symbol_stats(
    symbol: str,
    interval: int
):
    """
    獲取指定交易對的統計資訊
    
    **參數**:
    - **symbol**: 交易對
    - **interval**: 時間框架（秒）
    
    **返回**:
    - 資料統計（資料量、時間範圍、資料來源分布等）
    """
    try:
        with chart_db.get_session() as session:
            from sqlalchemy import func
            from database.models import CandlestickData
            
            # 總資料量
            total_count = session.query(func.count(CandlestickData.id)).filter(
                CandlestickData.symbol == symbol.upper(),
                CandlestickData.interval == interval
            ).scalar()
            
            if total_count == 0:
                return {
                    "symbol": symbol.upper(),
                    "interval": interval,
                    "total_count": 0,
                    "message": "無資料"
                }
            
            # 時間範圍
            time_range = session.query(
                func.min(CandlestickData.timestamp),
                func.max(CandlestickData.timestamp)
            ).filter(
                CandlestickData.symbol == symbol.upper(),
                CandlestickData.interval == interval
            ).first()
            
            # 資料來源分布
            source_dist = session.query(
                CandlestickData.data_source,
                func.count(CandlestickData.id)
            ).filter(
                CandlestickData.symbol == symbol.upper(),
                CandlestickData.interval == interval
            ).group_by(CandlestickData.data_source).all()
            
            return {
                "symbol": symbol.upper(),
                "interval": interval,
                "total_count": total_count,
                "time_range": {
                    "start": datetime.fromtimestamp(time_range[0]).strftime('%Y-%m-%d %H:%M:%S'),
                    "end": datetime.fromtimestamp(time_range[1]).strftime('%Y-%m-%d %H:%M:%S'),
                    "days": (time_range[1] - time_range[0]) / 86400
                },
                "data_source_distribution": [
                    {"source": source, "count": count}
                    for source, count in source_dist
                ]
            }
            
    except Exception as e:
        logger.error(f"❌ 獲取統計失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
