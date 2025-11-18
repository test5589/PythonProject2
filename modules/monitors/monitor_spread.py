# monitors/monitor_spread.py
# 大臣：監控 spread 變化與被動成交率，為 market making 策略發警訊

import ccxt  # 用於連交易所 API
import time
import os
import talib  # 用於計算指標 (如 ATR 輔助 spread 調整)
import pandas as pd  # 處理數據
import logging  # 日志記錄

# 設定日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 配置 (可從 config.py 匯入，暫時硬碼)
SYMBOL = 'BTC/USDT'  # 監控資產
EXCHANGE = 'binance'  # 交易所
SPREAD_THRESHOLD_LOW = 0.05  # spread 太窄閾值 (風險高，反向打)
SPREAD_THRESHOLD_HIGH = 0.2  # spread 太寬閾值 (拿不到單)
FILL_WINDOW = 10  # 計算 passive fill rate 的窗口 (最近10筆)

# 環境變數 for API key (安全)
API_KEY = os.environ.get('BINANCE_API_KEY', 'your_key_here')
API_SECRET = os.environ.get('BINANCE_SECRET', 'your_secret_here')

def connect_exchange():
    """連接到交易所"""
    try:
        exchange = ccxt.binance({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
        })
        return exchange
    except Exception as e:
        logging.error(f"API 連接錯誤: {e}")
        return None

def get_order_book(symbol=SYMBOL, limit=10):
    """獲取 order book 數據，回傳當前 spread"""
    exchange = connect_exchange()
    if exchange:
        try:
            order_book = exchange.fetch_order_book(symbol, limit)
            bid = order_book['bids'][0][0] if order_book['bids'] else 0  # 最高買價
            ask = order_book['asks'][0][0] if order_book['asks'] else 0  # 最低賣價
            spread = ask - bid if ask > bid else 0
            return spread, bid, ask
        except Exception as e:
            logging.error(f"獲取 order book 錯誤: {e}")
            return 0, 0, 0
    return 0, 0, 0

def calculate_passive_fill_rate(fills_history):
    """計算被動成交率 (passive fills / total orders)"""
    if not fills_history:
        return 0
    passive_count = sum(1 for fill in fills_history if fill['type'] == 'passive')  # 假設歷史有 'type' 標記
    total = len(fills_history)
    return (passive_count / total) * 100 if total > 0 else 0

def monitor_spread():
    """主監控函數：檢查 spread 並發警訊"""
    exchange = connect_exchange()
    if not exchange:
        return "警訊：API 連接失敗"

    # 模擬歷史 fills (真實中從 db 或 API 取)
    fills_history = []  # 例如 [{'type': 'passive', 'price': 100}, ...] - 你可從 database.py 載入

    while True:  # 無限迴圈，1分鐘檢查
        spread, bid, ask = get_order_book()
        fill_rate = calculate_passive_fill_rate(fills_history[-FILL_WINDOW:])

        logging.info(f"當前 Spread: {spread:.4f}, Bid: {bid:.2f}, Ask: {ask:.2f}")
        logging.info(f"被動成交率: {fill_rate:.2f}%")

        # 偵測警訊
        if spread < SPREAD_THRESHOLD_LOW:
            alert = "警訊：Spread 太窄，反向打風險高！建議放大 spread。"
        elif spread > SPREAD_THRESHOLD_HIGH:
            alert = "警訊：Spread 太寬，拿不到單！建議窄化 spread。"
        elif fill_rate < 50:  # 低於50% 警訊
            alert = "警訊：被動成交率低，定價不佳！檢查 order book depth。"
        else:
            alert = None

        if alert:
            logging.warning(alert)
            return alert  # 上報給宰相

        # 模擬更新 fills_history (真實中從交易 callback 取)
        # fills_history.append({'type': 'passive' if random else 'active', 'price': bid})

        time.sleep(60)  # 1分鐘間隔

# ============================================================
# 注意：此監控模組應由主程式調用，不作為獨立入口
# 主程式入口：python core/gui_main.py
# 
# 如需測試監控功能，請在主程式中調用：
#   from modules.monitors.monitor_spread import monitor_spread
#   monitor_spread()
# ============================================================
# if __name__ == "__main__":
#     monitor_spread()  # 測試用，已註釋
