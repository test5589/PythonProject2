#!/usr/bin/env python3
"""
weight_test_engine.py - 權重測試引擎
實現真正的時間框架控制和資料獲取測試
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
from tools.api_weight_evaluator import get_api_weight_evaluator
from modules.utils.api_connector import get_binance_klines_http
from modules.utils.logger import get_logger

logger = get_logger("weight_test")

class WeightTestEngine:
    """權重測試引擎"""
    
    def __init__(self, gui_callback: Optional[Callable] = None):
        self.gui_callback = gui_callback
        self.evaluator = get_api_weight_evaluator()
        self.is_running = False
        self.test_thread = None
        self.current_minute_start = None
        self.request_count_in_minute = 0
        
    def emit(self, message: str):
        """發送訊息到 GUI 或日誌"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[WEIGHT_TEST {timestamp}] {message}"
        
        if self.gui_callback:
            try:
                self.gui_callback(formatted_msg)
            except:
                pass
        
        logger.info(message)
        print(formatted_msg)
    
    def start_test(self, symbol: str = "BTCUSDT", timeframe: str = "1m"):
        """開始權重測試"""
        if self.is_running:
            self.emit("測試已在運行中...")
            return
            
        self.is_running = True
        self.test_thread = threading.Thread(
            target=self._run_test, 
            args=(symbol, timeframe), 
            daemon=True
        )
        self.test_thread.start()
    
    def stop_test(self):
        """停止權重測試"""
        self.is_running = False
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=2)
        self.emit("權重測試已停止")
    
    def _run_test(self, symbol: str, timeframe: str):
        """執行權重測試主邏輯"""
        try:
            self.emit(f"=== 開始權重測試 ===")
            self.emit(f"測試貨幣對: {symbol}")
            self.emit(f"時間框架: {timeframe}")
            
            # 取得當前權重狀態
            stats = self.evaluator.get_statistics(timeframe)
            self.emit(f"初始狀態 - 權重:{stats['weight']:.3f} | 建議筆數:{stats['base_count']} | 狀態:{stats['status']}")
            
            # 開始時間窗口控制測試
            self._test_time_window_control(symbol, timeframe)
            
        except Exception as e:
            self.emit(f"測試執行失敗: {e}")
            import traceback
            self.emit(f"錯誤詳情: {traceback.format_exc()}")
        finally:
            self.is_running = False
            self.emit("=== 權重測試結束 ===")
    
    def _test_time_window_control(self, symbol: str, timeframe: str):
        """測試時間窗口控制"""
        self.emit("開始時間窗口控制測試...")
        
        while self.is_running:
            # 記錄當前分鐘開始時間
            now = datetime.now()
            minute_start = now.replace(second=0, microsecond=0)
            next_minute = minute_start + timedelta(minutes=1)
            
            self.emit(f"時間窗口: {minute_start.strftime('%H:%M:%S')} - {next_minute.strftime('%H:%M:%S')}")
            
            # 重置當前分鐘計數器
            self.request_count_in_minute = 0
            
            # 在當前分鐘窗口內進行測試
            remaining_time = (next_minute - now).total_seconds()
            self.emit(f"剩餘時間: {remaining_time:.1f} 秒")
            
            # 取得建議的請求筆數
            optimal_count = self.evaluator.get_optimal_count(timeframe)
            self.emit(f"建議請求筆數: {optimal_count}")
            
            # 執行資料獲取測試
            success = self._fetch_data_with_limit(symbol, timeframe, optimal_count, remaining_time)
            
            if not success:
                self.emit("資料獲取失敗，可能觸發被鎖機制")
                # 標記被鎖並等待
                self.evaluator.mark_lock(timeframe, optimal_count)
                
                # 等待到下一分鐘
                sleep_time = (next_minute - datetime.now()).total_seconds()
                if sleep_time > 0:
                    self.emit(f"等待到下一分鐘: {sleep_time:.1f} 秒")
                    time.sleep(min(sleep_time, 60))
                    continue
            
            # 等待到下一分鐘窗口
            sleep_time = (next_minute - datetime.now()).total_seconds()
            if sleep_time > 0:
                self.emit(f"本分鐘測試完成，等待: {sleep_time:.1f} 秒")
                time.sleep(min(sleep_time, 60))
            else:
                self.emit("時間窗口已過，直接進入下一分鐘")
    
    def _fetch_data_with_limit(self, symbol: str, timeframe: str, count: int, time_limit: float) -> bool:
        """在時間限制內獲取指定筆數的資料"""
        try:
            self.emit(f"開始獲取 {count} 筆 {symbol} {timeframe} 資料...")
            
            start_time = time.time()
            
            # 模擬分批獲取 (每次最多1000筆)
            batch_size = min(1000, count)
            fetched = 0
            
            while fetched < count and self.is_running:
                current_batch = min(batch_size, count - fetched)
                
                # 檢查時間限制
                elapsed = time.time() - start_time
                if elapsed >= time_limit:
                    self.emit(f"時間限制到達 ({time_limit:.1f}s)，停止獲取")
                    break
                
                # 執行API請求
                try:
                    # 計算時間範圍（最近的一段時間）
                    end_time = int(time.time() * 1000)
                    start_time = end_time - (current_batch * 60 * 1000)  # 假設每筆資料間隔1分鐘
                    
                    data = get_binance_klines_http(symbol, timeframe, start_time, end_time, current_batch)
                    if data:
                        fetched += len(data)
                        self.emit(f"成功獲取 {len(data)} 筆資料 (總計: {fetched}/{count})")
                    else:
                        self.emit("API返回空資料")
                        break
                        
                except Exception as e:
                    if "429" in str(e) or "rate limit" in str(e).lower():
                        self.emit(f"觸發API限制: {e}")
                        return False
                    else:
                        self.emit(f"API請求錯誤: {e}")
                        break
                
                # 短暫延遲避免過快請求
                time.sleep(0.1)
            
            total_time = time.time() - start_time
            # 確保耗時是正數
            total_time = max(0, total_time)
            self.emit(f"資料獲取完成: {fetched}/{count} 筆，耗時 {total_time:.2f}s")
            
            return fetched >= count
            
        except Exception as e:
            self.emit(f"資料獲取異常: {e}")
            return False

# 全域實例
_test_engine: Optional[WeightTestEngine] = None

def get_weight_test_engine(gui_callback: Optional[Callable] = None) -> WeightTestEngine:
    """取得權重測試引擎實例"""
    global _test_engine
    if _test_engine is None:
        _test_engine = WeightTestEngine(gui_callback)
    return _test_engine
