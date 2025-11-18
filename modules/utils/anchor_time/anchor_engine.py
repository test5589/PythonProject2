#!/usr/bin/env python3
"""
anchor_engine.py - 錨定時間引擎核心
實現錨定時間機制和測試控制
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from tools.api_weight_evaluator import get_api_weight_evaluator
from modules.utils.api.api_connector import get_binance_klines_http
from modules.utils.logger import get_logger
from .time_frame_manager import TimeFrameManager
from .statistics_collector import StatisticsCollector

logger = get_logger("anchor_time")

class AnchorTimeEngine:
    """錨定時間引擎核心類"""
    
    def __init__(self, gui_callback: Optional[Callable] = None):
        self.gui_callback = gui_callback
        self.evaluator = get_api_weight_evaluator()
        self.is_running = False
        self.test_thread = None
        
        # 錨定時間相關
        self.anchor_time: Optional[datetime] = None
        self.anchor_start_time: Optional[float] = None
        
        # 使用獨立的管理器
        self.time_frame_manager = TimeFrameManager()
        self.statistics_collector = StatisticsCollector(self.emit)
        
        # 當前窗口統計
        self.current_window_start: Optional[datetime] = None
        self.current_window_data = 0
        
        # 資料時間範圍記錄
        self.data_time_ranges: List[Tuple[datetime, datetime]] = []
        
        # 測試階段設定
        self.test_stages = [1000] * 20  # 固定每次1000筆，進行20輪測試
        
        # 改善後的分階段測試配置
        self.test_phases = {
            1: {"days_offset": 1, "timeframes": ["1m", "5m", "15m", "1h"], "symbols": ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT"]},
            2: {"days_offset": 2, "timeframes": ["3m", "30m", "2h", "4h"], "symbols": ["XRPUSDT", "BTCUSDT", "ETHUSDT", "BNBUSDT"]},
            3: {"days_offset": 5, "timeframes": ["1m", "15m", "1h", "4h"], "symbols": ["ADAUSDT", "XRPUSDT", "BTCUSDT", "ETHUSDT"]},
            4: {"days_offset": 10, "timeframes": ["5m", "30m", "2h", "1h"], "symbols": ["BNBUSDT", "ADAUSDT", "XRPUSDT", "BTCUSDT"]},
            5: {"days_offset": 21, "timeframes": ["3m", "15m", "1h", "4h"], "symbols": ["ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]}
        }
        
        # 重複率監控
        self.duplicate_threshold = 0.15  # 15%重複率閾值
        
        # 舊的配置（保留作為備用）
        self.test_timeframes = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h"]
        self.test_symbols = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "XRPUSDT"]
        
        # 當前測試配置索引
        self.current_timeframe_index = 0
        self.current_symbol_index = 0
        self.enable_capacity_test = False
        self.enable_data_validation = False
        self.current_stage_index = 0
        self.max_successful_count = 0
        self.api_lock_count = 0
        
        # 資料驗證統計
        self.validation_stats = {
            "total_requests": 0,
            "valid_data_count": 0,
            "invalid_data_count": 0,
            "field_validation_errors": []
        }
        
        # 重複資料檢測
        self.received_timestamps = set()  # 儲存已收到的時間戳
        self.duplicate_data_count = 0     # 重複資料計數
        
    def start_test(self, symbol: str, timeframe: str, start_time: Optional[datetime] = None):
        """啟動錨定時間測試"""
        if self.is_running:
            self.stop_test()
            
        self.symbol = symbol
        self.timeframe = timeframe
        
        # 設定錨定時間
        if start_time and start_time > datetime.now():
            self.anchor_time = start_time
        else:
            self.anchor_time = datetime.now().replace(second=0, microsecond=0)
            self.emit(f"[ANCHOR] ⚠️ 錨定時間已調整為當前時間（原時間已過期或無效）")
            
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
        """停止錨定時間測試"""
        self.is_running = False
        
        # 強制停止所有測試階段
        self.current_stage_index = len(self.test_stages)
        
        # 清理測試狀態
        self.enable_capacity_test = False
        self.enable_data_validation = False
        
        self.emit("[ANCHOR] 錨定時間測試已強制停止")
        self.emit("[ANCHOR] 測試統計已保存")
        
        if self.test_thread and self.test_thread.is_alive():
            self.test_thread.join(timeout=5)
        self.emit("[ANCHOR] 錨定時間測試已停止")
        
    def _reset_statistics(self):
        """重置統計數據"""
        self.time_frame_manager.reset_timeframe_stats()
        self.statistics_collector.reset_statistics()
        self.current_window_start = None
        self.current_window_data = 0
        self.data_time_ranges = []
        
    def _run_anchor_test(self):
        """執行錨定時間測試"""
        try:
            self.emit("[ANCHOR] === 開始錨定時間統計 ===")
            
            # 計算錨定週期結束時間
            anchor_end_time = self.anchor_time + timedelta(minutes=60)
            
            # 立即開始測試
            self.emit(f"[ANCHOR] 🚀 立即開始階段式測試（60分鐘週期）")
            self.emit(f"[ANCHOR] ⏰ 測試結束時間: {anchor_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 立即執行第一次測試
            now = datetime.now()
            self.current_window_start = now.replace(second=0, microsecond=0)
            self.current_window_data = 0
            
            self.emit(f"[ANCHOR] 🎯 開始階段式權重測試...")
            self._test_data_fetching_in_window()
            
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
                    
                    # 在新窗口內進行資料獲取
                    self._test_data_fetching_in_window()
                
                # 短暫休息
                time.sleep(1)
            
            # 完成錨定週期
            if self.is_running:
                self._finish_previous_window()
                self._complete_anchor_cycle()
                
        except Exception as e:
            self.emit(f"[ANCHOR] 測試異常: {e}")
            logger.error(f"錨定時間測試異常: {e}")
            
    def _test_data_fetching_in_window(self):
        """在當前時間窗口內測試資料獲取"""
        try:
            if self.enable_capacity_test:
                # 階段式測試模式
                self._run_capacity_test_in_window()
            else:
                # 標準模式
                optimal_count = self.evaluator.get_optimal_count(self.timeframe)
                success, data_count, time_range, raw_data = self.statistics_collector.fetch_data_with_validation(
                    self.symbol, self.timeframe, optimal_count
                )
                
                if success and data_count > 0:
                    self.current_window_data += data_count
                    self.emit(f"[ANCHOR] 窗口內獲取 {data_count} 筆資料 (窗口總計: {self.current_window_data})")
                    
                    # 記錄資料時間範圍
                    if time_range:
                        self.data_time_ranges.append(time_range)
                        self.emit(f"[ANCHOR] 資料時間範圍: {time_range[0].strftime('%H:%M:%S')} - {time_range[1].strftime('%H:%M:%S')}")
                else:
                    self.emit("[ANCHOR] 窗口內資料獲取失敗或無資料")
                
        except Exception as e:
            self.emit(f"[ANCHOR] 窗口測試異常: {e}")
            
    def _run_capacity_test_in_window(self):
        """在窗口內執行階段式筆數測試"""
        try:
            # 重置階段索引
            if self.current_stage_index >= len(self.test_stages):
                self.current_stage_index = 0
                
            test_count = self.test_stages[self.current_stage_index]
            
            # 使用改善後的分階段配置
            test_params = self._get_improved_test_parameters(self.current_stage_index)
            current_timeframe = test_params["timeframe"]
            current_symbol = test_params["symbol"]
            phase = test_params["phase"]
            
            self.emit(f"[CAPACITY] 🧪 階段 {self.current_stage_index + 1}/{len(self.test_stages)}: 測試 {test_count} 筆資料")
            self.emit(f"[CAPACITY] 📊 交易對: {current_symbol} | K線時間段: {current_timeframe} | 階段: {phase}")
            self.emit(f"[CAPACITY] ⏰ 時間範圍: {test_params['time_info']}")
            
            # 顯示進度條
            progress = (self.current_stage_index + 1) / len(self.test_stages) * 100
            progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
            self.emit(f"[CAPACITY] 📊 測試進度: [{progress_bar}] {progress:.1f}%")
            
            success, data_count, time_range, raw_data = self.statistics_collector.fetch_data_with_validation(
                current_symbol, current_timeframe, test_count
            )
            
            if success and data_count > 0:
                self.max_successful_count = max(self.max_successful_count, data_count)
                self.current_window_data += data_count
                
                self.emit(f"[CAPACITY] ✅ 成功獲取 {data_count} 筆資料")
                self.emit(f"[CAPACITY] 📊 目前最大成功筆數: {self.max_successful_count}")
                
                # 記錄資料時間範圍
                if time_range:
                    self.data_time_ranges.append(time_range)
                
                # 進入下一階段
                self.current_stage_index += 1
                self.current_timeframe_index += 1
                
                # 每3個階段更換交易對
                if self.current_stage_index % 3 == 0:
                    self.current_symbol_index += 1
                
                time.sleep(0.05)
                
                # 繼續下一階段
                if self.current_stage_index < len(self.test_stages):
                    self._run_capacity_test_in_window()
                
            else:
                self.emit(f"[CAPACITY] ❌ 階段 {self.current_stage_index + 1} 測試失敗或被封鎖")
                
        except Exception as e:
            self.emit(f"[CAPACITY] 階段測試異常: {e}")
            # 檢查是否為API限制相關異常
            if "429" in str(e) or "rate limit" in str(e).lower() or "banned" in str(e).lower():
                self.emit(f"[CAPACITY] 🎯 成功觸發API限制異常！這是預期行為")
                self.api_lock_count += 1
                
    def _finish_previous_window(self):
        """完成前一個窗口的統計"""
        if self.current_window_start is None:
            return
            
        window_data = self.current_window_data
        window_time = self.current_window_start
        
        # 更新時間框架統計
        self.time_frame_manager.update_timeframe_statistics(window_time, window_data)
        
        self.emit(f"[ANCHOR] 窗口 {window_time.strftime('%H:%M:%S')} 完成，獲取 {window_data} 筆資料")
        
    def _complete_anchor_cycle(self):
        """完成錨定週期統計"""
        self.emit("[INTEGRATED] === 🎯 整合測試週期完成 ===")
        
        total_time = time.time() - self.anchor_start_time
        self.emit(f"[INTEGRATED] ⏱️ 總耗時: {total_time:.2f} 秒 ({total_time/60:.1f} 分鐘)")
        
        # 顯示測試結果
        self.statistics_collector.show_test_results(
            self.enable_capacity_test,
            self.max_successful_count,
            self.api_lock_count,
            self.test_stages,
            self.enable_data_validation
        )
        
        # 顯示時間框架統計
        self.time_frame_manager.show_timeframe_statistics(self.emit)
        
        # 顯示資料時間範圍
        if self.data_time_ranges:
            first_range = self.data_time_ranges[0]
            last_range = self.data_time_ranges[-1]
            self.emit(f"[INTEGRATED] 📅 資料時間範圍: {first_range[0].strftime('%Y/%m/%d %H:%M:%S')} - {last_range[1].strftime('%Y/%m/%d %H:%M:%S')}")
        
        # 更新權重評估
        self._update_weight_evaluation()
        
    def _update_weight_evaluation(self):
        """根據統計結果更新權重評估"""
        try:
            # 使用時間框架管理器的統計結果
            stats_1m = self.time_frame_manager.get_timeframe_stats("1m")
            if stats_1m["total"] > 0:
                avg_per_minute = stats_1m["total"] / len(stats_1m["windows"])
                self.evaluator.update_base_count("1m", int(avg_per_minute))
                self.emit(f"[ANCHOR] 已更新1m框架基礎值為 {int(avg_per_minute)} 筆")
        except Exception as e:
            self.emit(f"[ANCHOR] 更新權重評估失敗: {e}")
            
    def _get_improved_test_parameters(self, stage_index: int) -> dict:
        """獲取改善後的測試參數"""
        # 計算當前階段和階段內的測試索引
        phase = ((stage_index // 4) % 5) + 1
        test_in_phase = stage_index % 4
        
        config = self.test_phases[phase]
        
        # 計算時間範圍
        end_time = datetime.now() - timedelta(days=config["days_offset"])
        timeframe = config["timeframes"][test_in_phase]
        symbol = config["symbols"][test_in_phase]
        
        # 動態計算時間範圍避免重疊
        timeframe_info = self._calculate_time_range(timeframe, end_time)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_time": timeframe_info["start_time"],
            "end_time": end_time,
            "phase": phase,
            "time_info": timeframe_info["time_info"],
            "expected_overlap": self._calculate_expected_overlap(stage_index)
        }
    
    def _calculate_time_range(self, timeframe: str, end_time: datetime) -> dict:
        """計算時間範圍"""
        if timeframe == "1m":
            start_time = end_time - timedelta(hours=16, minutes=40)
            time_info = f"{start_time.strftime('%m月%d日%H時%M分')} 到 {end_time.strftime('%m月%d日%H時%M分')} (16小時40分鐘)"
        elif timeframe == "3m":
            start_time = end_time - timedelta(hours=50)
            time_info = f"{start_time.strftime('%m月%d日%H時')} 到 {end_time.strftime('%m月%d日%H時')} (50小時)"
        elif timeframe == "5m":
            start_time = end_time - timedelta(hours=83, minutes=20)
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (3.5天)"
        elif timeframe == "15m":
            start_time = end_time - timedelta(days=10, hours=10)
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (10天)"
        elif timeframe == "30m":
            start_time = end_time - timedelta(days=20, hours=20)
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (21天)"
        elif timeframe == "1h":
            start_time = end_time - timedelta(days=41, hours=16)
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (42天)"
        elif timeframe == "2h":
            start_time = end_time - timedelta(days=83, hours=8)
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (83天)"
        elif timeframe == "4h":
            start_time = end_time - timedelta(days=166, hours=16)
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (167天)"
        else:
            start_time = end_time - timedelta(hours=16, minutes=40)
            time_info = f"{start_time.strftime('%m月%d日%H時%M分')} 到 {end_time.strftime('%m月%d日%H時%M分')} (16小時40分鐘)"
        
        return {"start_time": start_time, "time_info": time_info}
    
    def _calculate_expected_overlap(self, stage_index: int) -> float:
        """計算預期重疊率"""
        phase = ((stage_index // 4) % 5) + 1
        
        overlap_rates = {1: 0.05, 2: 0.03, 3: 0.02, 4: 0.01, 5: 0.01}
        return overlap_rates.get(phase, 0.01)
    
    def should_adjust_strategy(self, duplicate_rate: float) -> bool:
        """判斷是否需要調整策略"""
        return duplicate_rate > self.duplicate_threshold
            
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
