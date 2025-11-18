"""此data_fetcher.py抓資料邏輯（真實）"""
"""data_fetcher.py - 使用 GET /api/v3/klines 抓取 K 線資料"""
print("[GUI] 即將呼叫 schedule_fetches()")
import time
from modules.utils.api.api_connector import get_binance_klines_http
from modules.utils.logger import get_logger

logger = get_logger("fetcher")

def interval_to_seconds(interval: str) -> int:  # 新增：重定義，從 backfill_data.py 抄，斷循環，防導入環
    m = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return int(interval[:-1]) * m[interval[-1]]

def fetch_klines(symbol: str, interval: str, start_time: int, end_time: int, limit: int = 1000):
    """ (REST API) 抓取歷史 K 線 (OHLCV) 資料
    :param symbol: 交易對 (e.g., "BTCUSDT")
    :param interval: K 線間隔 (e.g., "1s", "1m", "1h")
    :param start_time: 開始時間 (milliseconds)
    :param end_time: 結束時間 (milliseconds)
    :param limit: 最大回傳筆數
    :return: K 線資料 (list) 或 空 list
    """
    logger.info(f"抓取 {symbol}@{interval} 範圍 {start_time} → {end_time}")
    # (GEMINI 修正：)
    # 這是第二層防禦，避免 400 錯誤
    if not symbol:
        logger.error("❌ API 抓取錯誤: 'symbol' 參數為空，取消請求。")
        return []  # 直接回傳空列表，不請求 API
    try:
        # (GEMINI 註解：)
        # 你的 backfill_data.py 傳入的 symbol 可能是 "BTC/USDT"
        # 但 binance API 需要 "BTCUSDT"
        # 這裡的 .replace("/", "") 非常重要
        market_symbol = symbol.replace("/", "")
        klines = get_binance_klines_http(
            symbol=market_symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )
        # (GEMINI 修正：)
        # 這裡的邏輯*完全不變*，因為 klines 仍然是 API 傳回的原始列表
        # 幣安回傳的 klines 是 [ [timestamp, open, high, low, close, ...], [...] ]
        # 依照你的要求，我們在這裡將它轉換為包含所有 11 個欄位的完整字典
        processed_klines = []
        for k in klines:
            processed_klines.append({
                "open_time": k[0],
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
                "close_time": k[6],
                "quote_asset_volume": float(k[7]),
                "num_trades": int(k[8]),
                "taker_base_vol": float(k[9]),
                "taker_quote_vol": float(k[10])
            })
        logger.info(f"✅ 成功抓取 {len(processed_klines)} 筆 {symbol} K 線資料")

        # 新增：檢查少筆（絕對理性診斷，避免隱藏錯）
        expected_range_sec = (end_time - start_time) / 1000  # ms to sec
        expected_min = int(expected_range_sec / interval_to_seconds(interval)) * 0.8  # 80% 寬鬆預期
        if len(processed_klines) < expected_min:
            logger.warning(f"⚠️ API返回少筆 ({len(processed_klines)} < 預期~{expected_min})，可能API中斷/網路/範圍未來/符號錯: {symbol}@{interval} {start_time}→{end_time}")

        return processed_klines
    except Exception as e:
        logger.error(f"❌ API 抓取錯誤: {e}")
        return []  # 發生錯誤時回傳空列表
