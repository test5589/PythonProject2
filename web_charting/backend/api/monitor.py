"""monitor.py - 1秒監控控制 API 路由"""

import logging
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from modules.monitors.multi_symbol_monitor import (
    get_multi_symbol_monitor,
    start_all_symbols_monitoring,
    stop_all_symbols_monitoring,
    fetch_all_symbols_latest_minute,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/monitor", tags=["monitor"])


class MonitorStartRequest(BaseModel):
    category: str = "crypto"
    symbols: List[str] | None = None


class MonitorControlResponse(BaseModel):
    status: str
    monitoring: bool
    symbols: List[str]


class MonitorStatusResponse(BaseModel):
    monitoring: bool
    symbols: List[str]


class FetchLatestMinuteResponse(BaseModel):
    status: str
    success: bool
    message: str = ""


@router.post("/start", response_model=MonitorControlResponse)
async def start_monitoring(request: MonitorStartRequest) -> MonitorControlResponse:
    """啟動多貨幣對 1秒監控"""
    try:
        monitor = get_multi_symbol_monitor()

        # 若有指定 symbols，僅啟動這些貨幣對的 1 秒監控
        # [DESIGN NOTE] 目前 Web 前端只會傳入單一 symbol（當前頁面），
        # 但這裡仍允許多檔清單，未來若調整 MultiSymbolMonitor 或 GUI 互動方式，需一併考慮此行為。
        if request.symbols:
            symbols = [s.replace("/", "").upper() for s in request.symbols]
            max_symbols = len(symbols)
            ok = monitor.start_all_symbols_1s(
                category=request.category,
                max_symbols=max_symbols,
                specific_symbols=symbols,
            )
        else:
            # 維持原有行為：啟動預設多貨幣對監控
            ok = start_all_symbols_monitoring(category=request.category)

        if not ok:
            raise HTTPException(status_code=400, detail="啟動多貨幣對監控失敗或已在執行中")
        symbols = monitor.get_monitoring_symbols()
        return MonitorControlResponse(
            status="started",
            monitoring=monitor.is_monitoring(),
            symbols=symbols,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"start_monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-latest-minute", response_model=FetchLatestMinuteResponse)
async def fetch_latest_minute(request: MonitorStartRequest) -> FetchLatestMinuteResponse:
    try:
        def progress_cb(msg: str):
            logger.info(msg)

        ok = fetch_all_symbols_latest_minute(category=request.category, progress_cb=progress_cb)

        if not ok:
            return FetchLatestMinuteResponse(
                status="no_new_data",
                success=False,
                message="批量抓取已執行，但主 DB 無新資料或所有交易對皆無新資料",
            )

        return FetchLatestMinuteResponse(
            status="completed",
            success=True,
            message="批量抓取最新 1 分鐘資料已完成",
        )
    except Exception as e:
        logger.error(f"fetch_latest_minute error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop", response_model=MonitorControlResponse)
async def stop_monitoring() -> MonitorControlResponse:
    """停止多貨幣對 1秒監控"""
    try:
        ok = stop_all_symbols_monitoring()
        monitor = get_multi_symbol_monitor()
        symbols = monitor.get_monitoring_symbols()
        if not ok:
            raise HTTPException(status_code=400, detail="目前沒有正在執行的監控")
        return MonitorControlResponse(
            status="stopped",
            monitoring=monitor.is_monitoring(),
            symbols=symbols,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"stop_monitoring error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status", response_model=MonitorStatusResponse)
async def get_monitor_status() -> MonitorStatusResponse:
    """取得目前監控狀態"""
    try:
        monitor = get_multi_symbol_monitor()
        symbols = monitor.get_monitoring_symbols()
        return MonitorStatusResponse(monitoring=monitor.is_monitoring(), symbols=symbols)
    except Exception as e:
        logger.error(f"get_monitor_status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
