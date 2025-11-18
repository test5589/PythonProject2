#!/usr/bin/env python3
"""
anchor_time_engine.py - 錨定時間統計引擎
實現完整的錨定時間機制和多時間框架統計
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from modules.api_weight_evaluator import get_api_weight_evaluator
from modules.utils.api_connector import get_binance_klines_http
from modules.utils.logger import get_logger

logger = get_logger("anchor_time")

class AnchorTimeEngine:
    """錨定時間統計引擎"""
    
    def __init__(self, gui_callback: Optional[Callable] = None):
        self.gui_callback = gui_callback
        self.evaluator = get_api_weight_evaluator()
        self.is_running = False
        self.test_thread = None
        
        # 錨定時間相關
        self.anchor_time: Optional[datetime] = None
        self.anchor_start_time: Optional[float] = None
        
        # 多時間框架統計
        self.timeframe_stats = {
            "1m": {"total": 0, "windows": []},
            "3m": {"total": 0, "windows": []}, 
            "5m": {"total": 0, "windows": []},
            "10m": {"total": 0, "windows": []},
            "30m": {"total": 0, "windows": []},
            "60m": {"total": 0, "windows": []}
        }
        
        # 當前窗口統計
        self.current_window_start: Optional[datetime] = None
        self.current_window_data = 0
        
        # 資料時間範圍記錄
        self.data_time_ranges: List[Tuple[datetime, datetime]] = []
        
    def start_test(self, symbol: str, timeframe: str, start_time: Optional[datetime] = None):
        """啟動錨定時間測試"""
        if self.is_running:
            self.stop_test()
            
        self.symbol = symbol
        self.timeframe = timeframe
        
        # 設定錨定時間
        if start_time:
            self.anchor_time = start_time
        else:
            self.anchor_time = datetime.now().replace(second=0, microsecond=0)
            
        self.anchor_start_time = time.time()
        self.is_running = True
        
        # 重置統計
        self._reset_statistics()
        
        # 啟動測試線程
        self.test_thread = threading.Thread(target=self._run_anchor_test, daemon=True)
        self.test_thread.start()
        
        self.emit(f"[ANCHOR] 錨定時間測試啟動")
        self.emit(f"[ANCHOR] 錨定時間: {self.anchor_time.strftime('%Y/%m/%d %H:%M:%S')}")
        self.emit(f"[ANCHOR] 測試貨幣對: {symbol}")
        self.emit(f"[ANCHOR] 測試時間框架: {timeframe}")
        
    def stop_test(self):
        """停止測試"""
        self.is_running = False
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=5)
        self.emit("[ANCHOR] 錨定時間測試已停止")
        
    def _reset_statistics(self):
        """重置統計數據"""
        for tf in self.timeframe_stats:
            self.timeframe_stats[tf] = {"total": 0, "windows": []}
        self.current_window_start = None
        self.current_window_data = 0
        self.data_time_ranges = []
        
    def _run_anchor_test(self):
        """執行錨定時間測試"""
        try:
            self.emit("[ANCHOR] === 開始錨定時間統計 ===")
            
            # 計算錨定週期結束時間
            anchor_end_time = self.anchor_time + timedelta(minutes=60)
            
            while self.is_running and datetime.now() < anchor_end_time:
                # 計算當前窗口
                now = datetime.now()
                current_window = now.replace(second=0, microsecond=0)
                
                if self.current_window_start != current_window:
                    # 新的分鐘窗口開始
                    if self.current_window_start is not None:
                        self._finish_previous_window()
                    
                    self.current_window_start = current_window
                    self.current_window_data = 0
                    
                    self.emit(f"[ANCHOR] 時間窗口: {current_window.strftime('%H:%M:%S')} - {(current_window + timedelta(minutes=1)).strftime('%H:%M:%S')}")
                
                # 在當前窗口內進行資料獲取
                self._test_data_fetching_in_window()
                
                # 短暫休息
                time.sleep(0.5)
            
            # 完成錨定週期
            if self.is_running:
                self._finish_previous_window()
                self._complete_anchor_cycle()
                
        except Exception as e:
            self.emit(f"[ANCHOR] 測試異常: {e}")
            logger.error(f"錨定時間測試異常: {e}")
            
    def _test_data_fetching_in_window(self):
        """在當前時間窗口內測試資料獲取（加強最大筆數測試）"""
        try:
            # 階段式測試：逐步增加請求筆數直到觸發限制
            test_counts = [1000, 2000, 3000, 5000, 8000, 10000, 15000, 20000]
            max_successful_count = 0
            total_window_data = 0
            
            self.emit(f"[ANCHOR] 開始階段式最大筆數測試...")
            
            for test_count in test_counts:
                self.emit(f"[ANCHOR] 測試 {test_count} 筆資料...")
                
                # 執行資料獲取
                success, data_count, time_range = self._fetch_data_with_time_range(
                    self.symbol, self.timeframe, test_count
                )
                
                if success and data_count > 0:
                    max_successful_count = test_count
                    total_window_data += data_count
                    self.emit(f"[ANCHOR] ✓ {test_count} 筆成功，實際獲取 {data_count} 筆")
                    
                    # 記錄資料時間範圍
                    if time_range:
                        self.data_time_ranges.append(time_range)
                        
                    # 短暫休息避免連續請求
                    time.sleep(0.5)
                else:
                    self.emit(f"[ANCHOR] ✗ {test_count} 筆失敗，觸發API限制")
                    # 觸發限制時更新權重評估
                    self.evaluator.mark_lock(self.timeframe, test_count)
                    break
            
            # 更新當前窗口統計
            self.current_window_data = max_successful_count
            
            self.emit(f"[ANCHOR] 窗口測試完成，最大成功筆數: {max_successful_count}")
            self.emit(f"[ANCHOR] 窗口總計獲取: {total_window_data} 筆資料")
            
            # 更新權重評估系統
            if max_successful_count > 0:
                self.evaluator.update_base_count(self.timeframe, max_successful_count)
                self.emit(f"[ANCHOR] 已更新 {self.timeframe} 框架基礎值為 {max_successful_count} 筆")
                
        except Exception as e:
            self.emit(f"[ANCHOR] 窗口測試異常: {e}")
            logger.error(f"窗口測試異常: {e}")
            
    def _fetch_data_with_time_range(self, symbol: str, timeframe: str, count: int) -> Tuple[bool, int, Optional[Tuple[datetime, datetime]]]:
        """獲取資料並返回時間範圍（驗證資料有效性）"""
        try:
            # 計算時間範圍
            end_time = int(time.time() * 1000)
            start_time = end_time - (count * self._get_timeframe_ms(timeframe))
            
            self.emit(f"[ANCHOR] 請求 {symbol} {timeframe} 資料，範圍: {count} 筆")
            
            data = get_binance_klines_http(symbol, timeframe, start_time, end_time, count)
            
            if data and len(data) > 0:
                # 驗證資料完整性（11項資料欄位）
                valid_data_count = 0
                first_time = None
                last_time = None
                
                for item in data:
                    # 檢查是否為完整的11項資料
                    if len(item) >= 11 and all(item[i] is not None for i in range(11)):
                        valid_data_count += 1
                        if first_time is None:
                            first_time = datetime.fromtimestamp(item[0] / 1000)
                        last_time = datetime.fromtimestamp(item[0] / 1000)
                
                if valid_data_count > 0:
                    self.emit(f"[ANCHOR] ✓ 有效資料 {valid_data_count}/{len(data)} 筆")
                    
                    # 記錄資料樣本（第一筆和最後一筆）
                    if len(data) > 0 and len(data[0]) >= 11:
                        sample_first = data[0]
                        sample_last = data[-1]
                        self.emit(f"[ANCHOR] 資料樣本 - 開始: 時間={datetime.fromtimestamp(sample_first[0]/1000).strftime('%H:%M:%S')}, 開盤={sample_first[1]}, 收盤={sample_first[4]}")
                        self.emit(f"[ANCHOR] 資料樣本 - 結束: 時間={datetime.fromtimestamp(sample_last[0]/1000).strftime('%H:%M:%S')}, 開盤={sample_last[1]}, 收盤={sample_last[4]}")
                    
                    return True, valid_data_count, (first_time, last_time)
                else:
                    self.emit(f"[ANCHOR] ✗ 無有效資料（缺少11項欄位）")
                    return False, 0, None
            else:
                self.emit(f"[ANCHOR] ✗ 無資料返回")
                return False, 0, None
                
        except Exception as e:
            error_msg = str(e).lower()
            if "429" in error_msg or "rate limit" in error_msg or "ip banned" in error_msg:
                self.evaluator.mark_lock(timeframe, count)
                self.emit(f"[ANCHOR] 🚫 API限制觸發: {e}")
            else:
                self.emit(f"[ANCHOR] ❌ API請求失敗: {e}")
            return False, 0, None
            
    def _get_timeframe_ms(self, timeframe: str) -> int:
        """取得時間框架的毫秒數"""
        timeframe_map = {
            "1m": 60 * 1000,
            "3m": 3 * 60 * 1000,
            "5m": 5 * 60 * 1000,
            "10m": 10 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000
        }
        return timeframe_map.get(timeframe, 60 * 1000)
        
    def _finish_previous_window(self):
        """完成前一個窗口的統計"""
        if self.current_window_start is None:
            return
            
        window_data = self.current_window_data
        window_time = self.current_window_start
        
        # 更新各時間框架統計
        self._update_timeframe_statistics(window_time, window_data)
        
        self.emit(f"[ANCHOR] 窗口 {window_time.strftime('%H:%M:%S')} 完成，獲取 {window_data} 筆資料")
        
    def _update_timeframe_statistics(self, window_time: datetime, data_count: int):
        """更新多時間框架統計"""
        # 1分鐘框架
        self.timeframe_stats["1m"]["total"] += data_count
        self.timeframe_stats["1m"]["windows"].append({
            "time": window_time,
            "count": data_count
        })
        
        # 更新其他時間框架（每N分鐘累積一次）
        timeframes = [3, 5, 10, 30, 60]
        for minutes in timeframes:
            tf_key = f"{minutes}m" if minutes < 60 else "1h"
            
            # 檢查是否需要更新該時間框架
            if window_time.minute % minutes == 0:
                self.timeframe_stats[tf_key]["total"] += data_count
                self.timeframe_stats[tf_key]["windows"].append({
                    "time": window_time,
                    "count": data_count
                })
                
    def _complete_anchor_cycle(self):
        """完成錨定週期統計"""
        self.emit("[ANCHOR] === 錨定週期完成 ===")
        
        total_time = time.time() - self.anchor_start_time
        self.emit(f"[ANCHOR] 總耗時: {total_time:.2f} 秒")
        
        # 顯示各時間框架統計
        for tf, stats in self.timeframe_stats.items():
            if stats["total"] > 0:
                avg_count = stats["total"] / len(stats["windows"]) if stats["windows"] else 0
                self.emit(f"[ANCHOR] {tf} 框架: 總計 {stats['total']} 筆, 平均 {avg_count:.1f} 筆/窗口, 窗口數 {len(stats['windows'])}")
        
        # 顯示資料時間範圍
        if self.data_time_ranges:
            first_range = self.data_time_ranges[0]
            last_range = self.data_time_ranges[-1]
            self.emit(f"[ANCHOR] 資料時間範圍: {first_range[0].strftime('%Y/%m/%d %H:%M:%S')} - {last_range[1].strftime('%Y/%m/%d %H:%M:%S')}")
        
        # 更新權重評估
        self._update_weight_evaluation()
        
    def _update_weight_evaluation(self):
        """根據統計結果更新權重評估"""
        try:
            # 使用1分鐘框架的統計作為基礎
            stats_1m = self.timeframe_stats["1m"]
            if stats_1m["total"] > 0:
                # 計算平均每分鐘獲取量
                avg_per_minute = stats_1m["total"] / len(stats_1m["windows"])
                
                # 更新權重評估系統
                self.evaluator.update_base_count("1m", int(avg_per_minute))
                self.emit(f"[ANCHOR] 已更新1m框架基礎值為 {int(avg_per_minute)} 筆")
                
        except Exception as e:
            self.emit(f"[ANCHOR] 更新權重評估失敗: {e}")
            
    def emit(self, message: str):
        """發送訊息到GUI和日誌"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_msg = f"{timestamp} | anchor_time | INFO | {message}"
        
        # 發送到GUI
        if self.gui_callback:
            try:
                self.gui_callback(f"[ANCHOR] {message}")
            except:
                pass
                
        # 寫入日誌
        logger.info(message)

# 全域實例
_anchor_engine: Optional[AnchorTimeEngine] = None

def get_anchor_time_engine(gui_callback: Optional[Callable] = None) -> AnchorTimeEngine:
    """取得錨定時間引擎實例"""
    global _anchor_engine
    if _anchor_engine is None:
        _anchor_engine = AnchorTimeEngine(gui_callback)
    return _anchor_engine
