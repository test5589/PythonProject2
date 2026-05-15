"""
sync.py - Data Sync API Routes
處理資料同步的 API 端點
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from database.chart_db import chart_db
from database.main_db_connector import main_db
from web_charting_backend_config import config
from .charts import _get_1s_candles_with_backfill, _aggregate_1s_to_interval

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


# ========== Request/Response Models ==========

class SyncRequest(BaseModel):
    """同步請求模型"""
    symbol: str = Field(..., description="交易對，如 BTCUSDT")
    interval: int = Field(..., description="時間框架（秒）")
    category: str = Field(default="crypto", description="分類（crypto/stock）")
    start_time: Optional[float] = Field(
        default=None,
        description="開始時間（Unix timestamp），null=從上次同步時間開始"
    )
    end_time: Optional[float] = Field(
        default=None,
        description="結束時間（Unix timestamp），null=到現在"
    )
    overwrite: bool = Field(
        default=False,
        description="是否覆蓋現有數據"
    )
    data_source: Optional[str] = Field(
        default=None,
        description="只同步特定來源的資料（可選）"
    )


class SyncResponse(BaseModel):
    """同步回應模型"""
    status: str
    symbol: str
    interval: int
    records_synced: int
    time_range: dict
    message: str = ""
    error: Optional[str] = None


class SyncHistoryResponse(BaseModel):
    """同步歷史回應"""
    id: int
    symbol: str
    interval: int
    start_time: float
    end_time: float
    records_synced: int
    sync_status: str
    created_at: str
    completed_at: Optional[str] = None
    error_message: Optional[str] = None


class Sync1sFromMainRequest(BaseModel):
    symbol: str = Field(...)
    category: str = Field(default="crypto")
    overwrite: bool = Field(default=False)


class GapFillFrom1mRequest(BaseModel):
    symbol: str = Field(..., description="交易對，如 BTCUSDT")
    category: str = Field(default="crypto", description="分類（crypto/stock）")
    intervals: list[int] = Field(
        default_factory=lambda: [1, 2, 5],
        description="要補齊的秒級時間框架（必須 < 60，例如 [1,2,5]）",
    )


class GapFillResponse(BaseModel):
    status: str
    symbol: str
    filled: dict
    time_range: dict
    message: str = ""
    error: Optional[str] = None


# ========== API Endpoints ==========

@router.post("/", response_model=SyncResponse)
async def sync_data(request: SyncRequest):
    """
    同步資料從主資料庫到 Chart DB
    
    **流程**:
    1. 檢查同步範圍
    2. 從主DB獲取資料
    3. 寫入Chart DB
    4. 記錄同步歷史
    
    **參數**:
    - **symbol**: 交易對
    - **interval**: 時間框架（秒）
    - **category**: 分類（crypto/stock）
    - **start_time**: 開始時間（可選，null=從上次同步開始）
    - **end_time**: 結束時間（可選，null=到現在）
    - **overwrite**: 是否覆蓋現有數據
    - **data_source**: 資料來源過濾（可選）
    
    **返回**:
    - 同步結果
    """
    try:
        logger.info(
            f"🔄 開始同步: {request.symbol}@{request.interval}s "
            f"overwrite={request.overwrite}"
        )
        
        # 確定同步時間範圍
        if request.start_time is None:
            # 從上次同步時間開始
            last_sync_time = chart_db.get_last_sync_time(
                request.symbol.upper(),
                request.interval
            )
            if last_sync_time:
                start_time = last_sync_time
                logger.info(f"📅 從上次同步時間開始: {datetime.fromtimestamp(start_time)}")
            else:
                # 如果從未同步，同步最近30天
                start_time = (datetime.now() - timedelta(days=config.sync.MAX_SYNC_DAYS)).timestamp()
                logger.info(f"📅 首次同步，從 {config.sync.MAX_SYNC_DAYS} 天前開始")
        else:
            start_time = request.start_time
        
        if request.end_time is None:
            end_time = datetime.now().timestamp()
        else:
            end_time = request.end_time
        
        # 驗證時間範圍
        if start_time >= end_time:
            raise HTTPException(
                status_code=400,
                detail="開始時間必須早於結束時間"
            )
        
        # 創建同步記錄
        with chart_db.get_session() as session:
            sync_record = chart_db.create_sync_record(
                symbol=request.symbol.upper(),
                interval=request.interval,
                start_time=start_time,
                end_time=end_time,
                session=session
            )
            sync_id = sync_record.id
        
        try:
            # 更新狀態為執行中
            chart_db.update_sync_record(sync_id, 'running')
            
            # 如果需要覆蓋，先刪除舊資料
            if request.overwrite:
                deleted = chart_db.delete_candles(
                    symbol=request.symbol.upper(),
                    interval=request.interval,
                    start_time=start_time,
                    end_time=end_time
                )
                logger.info(f"🗑️ 已刪除舊資料: {deleted} 根K線")
            
            # 從主DB獲取資料
            main_db.initialize()
            candles = main_db.fetch_candles(
                category=request.category,
                symbol=request.symbol.upper(),
                interval=request.interval,
                start_time=start_time,
                end_time=end_time,
                data_source=request.data_source
            )

            # Web 端約定：1 分鐘以下 timeframe（interval < 60）的資料在 Chart DB 中一律標記為 real
            if request.interval < 60 and candles:
                real_priority = config.chart.DATA_PRIORITY.get("real", config.chart.DATA_PRIORITY.get("test", 5))
                for c in candles:
                    c["data_source"] = "real"
                    c["priority"] = real_priority
            
            if not candles:
                # 無資料
                chart_db.update_sync_record(
                    sync_id,
                    'completed',
                    records_synced=0
                )
                logger.warning(f"⚠️ 主DB無資料: {request.symbol}@{request.interval}s")
                return SyncResponse(
                    status="success",
                    symbol=request.symbol.upper(),
                    interval=request.interval,
                    records_synced=0,
                    time_range={
                        "start": datetime.fromtimestamp(start_time).strftime('%Y-%m-%d %H:%M:%S'),
                        "end": datetime.fromtimestamp(end_time).strftime('%Y-%m-%d %H:%M:%S')
                    },
                    message="主資料庫無資料"
                )
            
            # 批量插入到 Chart DB
            inserted = chart_db.insert_candles(candles)
            
            # 更新同步記錄為完成
            chart_db.update_sync_record(
                sync_id,
                'completed',
                records_synced=inserted
            )
            
            logger.info(f"✅ 同步完成: {inserted} 根K線")
            
            return SyncResponse(
                status="success",
                symbol=request.symbol.upper(),
                interval=request.interval,
                records_synced=inserted,
                time_range={
                    "start": datetime.fromtimestamp(candles[0]['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    "end": datetime.fromtimestamp(candles[-1]['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                    "start_timestamp": candles[0]['timestamp'],
                    "end_timestamp": candles[-1]['timestamp']
                },
                message=f"成功同步 {inserted} 根K線"
            )
            
        except Exception as e:
            # 更新同步記錄為失敗
            chart_db.update_sync_record(
                sync_id,
                'failed',
                error_message=str(e)
            )
            raise
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 同步失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/subminute/1s", response_model=SyncResponse)
async def sync_1s_from_main(request: Sync1sFromMainRequest):
    try:
        symbol_up = request.symbol.upper()

        taipei_tz = timezone(timedelta(hours=8))
        now_taipei = datetime.now(tz=taipei_tz)
        today_start = now_taipei.replace(hour=0, minute=0, second=0, microsecond=0)

        start_utc = today_start.astimezone(timezone.utc)
        end_utc = now_taipei.astimezone(timezone.utc)

        start_ts = start_utc.timestamp()
        end_ts = end_utc.timestamp()

        if start_ts >= end_ts:
            raise HTTPException(status_code=400, detail="開始時間必須早於結束時間")

        window_seconds = int(end_ts - start_ts) + 1
        if window_seconds <= 0:
            raise HTTPException(status_code=400, detail="時間範圍無效")

        candles_1s = _get_1s_candles_with_backfill(
            symbol=symbol_up,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=window_seconds,
            data_source_filter=None,
        )

        if not candles_1s:
            raise HTTPException(status_code=400, detail="主資料庫沒有可用的 1 秒/1 分鐘資料")

        deleted = 0
        if request.overwrite:
            deleted = chart_db.delete_candles(
                symbol=symbol_up,
                interval=1,
                start_time=start_ts,
                end_time=end_ts,
            )

        inserted = chart_db.insert_candles(candles_1s)

        time_range = {
            "start": datetime.fromtimestamp(candles_1s[0]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "end": datetime.fromtimestamp(candles_1s[-1]["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"),
            "start_timestamp": candles_1s[0]["timestamp"],
            "end_timestamp": candles_1s[-1]["timestamp"],
        }

        msg = f"成功從主DB聚合並同步 1 秒資料到 Chart DB: 插入/更新 {inserted} 筆, 刪除 {deleted} 筆"

        return SyncResponse(
            status="success",
            symbol=symbol_up,
            interval=1,
            records_synced=inserted,
            time_range=time_range,
            message=msg,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 1 秒同步失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/gap-fill/from-1m", response_model=GapFillResponse)
async def gap_fill_from_1m(request: GapFillFrom1mRequest):
    """從主 DB 的 1 分鐘資料推導出缺口 1s/2s/5s，僅補齊缺失部分到 Web Chart DB。"""
    try:
        symbol_up = request.symbol.upper()

        taipei_tz = timezone(timedelta(hours=8))
        now_taipei = datetime.now(tz=taipei_tz)
        today_start = now_taipei.replace(hour=0, minute=0, second=0, microsecond=0)

        start_utc = today_start.astimezone(timezone.utc)
        end_utc = now_taipei.astimezone(timezone.utc)

        start_ts = start_utc.timestamp()
        end_ts = end_utc.timestamp()

        if start_ts >= end_ts:
            raise HTTPException(status_code=400, detail="開始時間必須早於結束時間")

        window_seconds = int(end_ts - start_ts) + 1
        if window_seconds <= 0:
            raise HTTPException(status_code=400, detail="時間範圍無效")

        # 從主 DB 取得以 1 分鐘為基礎的 1 秒完整序列（含缺口內插）
        all_1s = _get_1s_candles_with_backfill(
            symbol=symbol_up,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=window_seconds,
            data_source_filter=None,
        )

        if not all_1s:
            raise HTTPException(
                status_code=400,
                detail="主資料庫沒有可用的 1 分鐘/1 秒資料，請先在主程式回補最新 1 分鐘",
            )

        filled = {}

        with chart_db.get_session() as session:
            # 1 秒缺口補齊（僅補 Web DB 尚不存在的 timestamp）
            if 1 in request.intervals:
                existing_1s = chart_db.query_candles(
                    symbol=symbol_up,
                    interval=1,
                    start_time=start_ts,
                    end_time=end_ts,
                    data_source=None,
                    limit=window_seconds,
                    session=session,
                )
                existing_ts = {int(c.timestamp) for c in existing_1s}
                new_1s = [c for c in all_1s if int(c["timestamp"]) not in existing_ts]

                if new_1s:
                    chart_db.insert_candles(new_1s, session=session)
                filled[1] = len(new_1s)
            else:
                filled[1] = 0

            # 2 秒 / 5 秒等子分鐘缺口補齊（由完整 1 秒序列聚合）
            for sub_interval in request.intervals:
                if sub_interval <= 1 or sub_interval >= 60:
                    continue

                aggregated = _aggregate_1s_to_interval(all_1s, sub_interval)
                if not aggregated:
                    filled[sub_interval] = 0
                    continue

                # Chart DB 可能已有部分資料，只補 timestamp 尚不存在的 bucket
                existing = chart_db.query_candles(
                    symbol=symbol_up,
                    interval=sub_interval,
                    start_time=start_ts,
                    end_time=end_ts,
                    data_source=None,
                    limit=window_seconds // max(sub_interval, 1) + 10,
                    session=session,
                )
                existing_ts = {int(c.timestamp) for c in existing}
                new_sub = [c for c in aggregated if int(c["timestamp"]) not in existing_ts]

                if new_sub:
                    chart_db.insert_candles(new_sub, session=session)
                filled[sub_interval] = len(new_sub)

        time_range = {
            "start": datetime.fromtimestamp(start_ts).strftime("%Y-%m-%d %H:%M:%S"),
            "end": datetime.fromtimestamp(end_ts).strftime("%Y-%m-%d %H:%M:%S"),
            "start_timestamp": start_ts,
            "end_timestamp": end_ts,
        }

        msg_parts = [
            f"{k}s: 補齊 {filled[k]} 根" for k in sorted(filled.keys())
        ]
        msg = "；".join(msg_parts) if msg_parts else "無缺口需要補齊"

        return GapFillResponse(
            status="success",
            symbol=symbol_up,
            filled=filled,
            time_range=time_range,
            message=msg,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 缺口補齊(1m→子分鐘)失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=list[SyncHistoryResponse])
async def get_sync_history(
    symbol: Optional[str] = None,
    interval: Optional[int] = None,
    limit: int = 50
):
    """
    獲取同步歷史記錄
    
    **參數**:
    - **symbol**: 過濾特定交易對（可選）
    - **interval**: 過濾特定時間框架（可選）
    - **limit**: 最多返回多少條記錄
    
    **返回**:
    - 同步歷史列表
    """
    try:
        with chart_db.get_session() as session:
            from database.models import SyncHistory
            
            query = session.query(SyncHistory)
            
            if symbol:
                query = query.filter(SyncHistory.symbol == symbol.upper())
            if interval:
                query = query.filter(SyncHistory.interval == interval)
            
            records = query.order_by(
                SyncHistory.created_at.desc()
            ).limit(limit).all()
            
            return [
                SyncHistoryResponse(
                    id=r.id,
                    symbol=r.symbol,
                    interval=r.interval,
                    start_time=r.start_time,
                    end_time=r.end_time,
                    records_synced=r.records_synced,
                    sync_status=r.sync_status,
                    created_at=r.created_at.isoformat() if r.created_at else "",
                    completed_at=r.completed_at.isoformat() if r.completed_at else None,
                    error_message=r.error_message
                )
                for r in records
            ]
            
    except Exception as e:
        logger.error(f"❌ 獲取同步歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{sync_id}")
async def get_sync_status(sync_id: int):
    """
    獲取特定同步任務的狀態
    
    **參數**:
    - **sync_id**: 同步記錄ID
    
    **返回**:
    - 同步狀態詳情
    """
    try:
        with chart_db.get_session() as session:
            from database.models import SyncHistory
            
            record = session.query(SyncHistory).filter(
                SyncHistory.id == sync_id
            ).first()
            
            if not record:
                raise HTTPException(status_code=404, detail="同步記錄不存在")
            
            return {
                "id": record.id,
                "symbol": record.symbol,
                "interval": record.interval,
                "status": record.sync_status,
                "records_synced": record.records_synced,
                "created_at": record.created_at.isoformat() if record.created_at else None,
                "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                "error_message": record.error_message
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取同步狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_all_data(confirm: bool = False):
    """
    清空所有 Chart DB 資料（危險操作！）
    
    **參數**:
    - **confirm**: 必須設為 true 才能執行
    
    **返回**:
    - 操作結果
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="必須設置 confirm=true 才能執行清空操作"
        )
    
    try:
        with chart_db.get_session() as session:
            from database.models import CandlestickData, SyncHistory, IndicatorCache
            
            # 刪除所有資料
            candles_deleted = session.query(CandlestickData).delete()
            sync_deleted = session.query(SyncHistory).delete()
            cache_deleted = session.query(IndicatorCache).delete()
            
            session.commit()
        
        # VACUUM 回收空間
        chart_db.vacuum()
        
        logger.warning(
            f"🗑️ 已清空所有資料: "
            f"K線={candles_deleted}, 同步記錄={sync_deleted}, 緩存={cache_deleted}"
        )
        
        return {
            "status": "success",
            "message": "所有資料已清空",
            "deleted": {
                "candles": candles_deleted,
                "sync_history": sync_deleted,
                "indicator_cache": cache_deleted
            }
        }
        
    except Exception as e:
        logger.error(f"❌ 清空資料失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
