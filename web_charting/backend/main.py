"""
main.py - FastAPI Main Application
Web Charting 後端主程式
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import sys
from pathlib import Path

# 取得 backend 與專案根目錄路徑
backend_dir = Path(__file__).parent
project_root = backend_dir.parent.parent

# 確保專案根目錄在 sys.path 前面，讓 `config` 套件指向專案根目錄的 config/
project_root_str = str(project_root)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# backend 目錄通常會由啟動時的工作目錄自動加入 sys.path
# 這裡僅在缺少時追加（不搶在最前面），避免與 `config` 套件名稱衝突
backend_dir_str = str(backend_dir)
if backend_dir_str not in sys.path:
    sys.path.append(backend_dir_str)

from web_charting_backend_config import config
from database.chart_db import chart_db
from api.charts import router as charts_router
from api.sync import router as sync_router
from api.monitor import router as monitor_router

# 配置日誌
logging.basicConfig(
    level=logging.INFO if not config.DEBUG else logging.DEBUG,
    format=config.LOG_FORMAT
)

# 降低 uvicorn reload 所使用的 watchfiles 日誌等級，避免大量 DEBUG "changes detected" 刷螢幕
logging.getLogger("watchfiles").setLevel(logging.WARNING)
logging.getLogger("watchfiles.main").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# ========== 生命週期管理 ==========

@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用生命週期管理"""
    # 啟動時
    logger.info("🚀 Web Charting Backend 啟動中...")
    
    # 初始化資料庫
    try:
        chart_db.initialize()
        logger.info("✅ 資料庫初始化完成")
    except Exception as e:
        logger.error(f"❌ 資料庫初始化失敗: {e}")
        raise
    
    logger.info(f"✅ Web Charting Backend 已啟動 (環境: {config.ENV})")
    
    yield
    
    # 關閉時
    logger.info("🛑 Web Charting Backend 關閉中...")
    chart_db.close()
    logger.info("✅ Web Charting Backend 已關閉")


# ========== 創建應用 ==========

app = FastAPI(
    title="Web Charting API",
    description="類似 TradingView 的 K線圖 Web 應用後端 API",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)


# ========== CORS 中間件 ==========

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.api.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== 註冊路由 ==========

app.include_router(charts_router)
app.include_router(sync_router)
app.include_router(monitor_router)


# ========== 除錯路由（顯示所有已註冊路由） ==========

@app.get("/debug/routes")
async def debug_list_routes():
    """列出目前註冊的所有路由（僅用於除錯）。"""
    routes_info = []
    for r in app.routes:
        methods = getattr(r, "methods", None)
        routes_info.append({
            "path": getattr(r, "path", None),
            "name": getattr(r, "name", None),
            "methods": sorted(list(methods)) if methods else None,
        })
    return routes_info


# ========== 根路由 ==========

@app.get("/")
async def root():
    """根路徑"""
    return {
        "service": "Web Charting API",
        "version": "0.1.0",
        "status": "running",
        "environment": config.ENV,
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "charts": "/api/charts",
            "sync": "/api/sync"
        }
    }


@app.get("/health")
async def health_check():
    """健康檢查"""
    try:
        # 檢查資料庫連接
        from sqlalchemy import text
        with chart_db.get_session() as session:
            session.execute(text("SELECT 1"))
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": logging.Formatter().formatTime(logging.LogRecord(
                "", 0, "", 0, "", (), None
            ))
        }
    except Exception as e:
        logger.error(f"❌ 健康檢查失敗: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/config")
async def get_config():
    """獲取配置資訊（僅開發環境）"""
    if not config.DEBUG:
        return JSONResponse(
            status_code=403,
            content={"error": "僅開發環境可用"}
        )
    
    return {
        "environment": config.ENV,
        "debug": config.DEBUG,
        "database": {
            "chart_db": str(config.database.CHART_DB_PATH),
            "main_db": str(config.database.MAIN_DB_PATH)
        },
        "chart": {
            "timeframes": config.chart.TIMEFRAMES,
            "default_limit": config.chart.DEFAULT_CANDLES_LIMIT,
            "max_limit": config.chart.MAX_CANDLES_LIMIT
        },
        "api": {
            "host": config.api.HOST,
            "port": config.api.PORT,
            "cors_origins": config.api.CORS_ORIGINS
        }
    }


# ========== 錯誤處理 ==========

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """404 錯誤處理"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "請求的資源不存在",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """500 錯誤處理"""
    logger.error(f"內部錯誤: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "伺服器內部錯誤"
        }
    )


# ========== 啟動腳本 ==========

if __name__ == "__main__":
    import uvicorn
    
    logger.info("🚀 啟動 Web Charting Backend...")
    logger.info(f"📡 API文檔: http://{config.api.HOST}:{config.api.PORT}/docs")
    logger.info(f"📊 Chart DB: {config.database.CHART_DB_PATH}")
    logger.info(f"💾 Main DB: {config.database.MAIN_DB_PATH}")
    
    uvicorn.run(
        "main:app",
        host=config.api.HOST,
        port=config.api.PORT,
        reload=config.DEBUG,
        log_level="info"
    )
