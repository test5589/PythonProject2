#!/usr/bin/env python3
"""
anchor_time_engine.py - 錨定時間統計引擎
實現完整的錨定時間機制和多時間框架統計
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Tuple
from tools.api_weight_evaluator import get_api_weight_evaluator
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
            "60m": {"total": 0, "windows": []}  # 添加60m鍵
        }
        
        # 當前窗口統計
        self.current_window_start: Optional[datetime] = None
        self.current_window_data = 0
        
        # 資料時間範圍記錄
        self.data_time_ranges: List[Tuple[datetime, datetime]] = []
        
        # 測試階段設定（每次固定1000筆，通過不同時間段和交易對避免重複）
        self.test_stages = [1000] * 20  # 固定每次1000筆，進行20輪測試
        
        # 改善後的分階段測試配置（減少重複資料）
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
        self.enable_capacity_test = False  # 是否啟用最大筆數測試
        self.enable_data_validation = False  # 是否啟用11項資料驗證
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
        
        # 設定錨定時間（確保為當前時間或未來時間）
        if start_time and start_time > datetime.now():
            self.anchor_time = start_time
        else:
            # 使用當前時間作為錨定時間
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
            
            # 立即開始測試，不等待特定時間窗口
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
        """在當前時間窗口內測試資料獲取（支援階段式測試和資料驗證）"""
        try:
            if self.enable_capacity_test:
                # 階段式測試模式：測試不同筆數的獲取能力
                self._run_capacity_test_in_window()
            else:
                # 標準模式：使用權重評估系統建議的筆數
                optimal_count = self.evaluator.get_optimal_count(self.timeframe)
                success, data_count, time_range, raw_data = self._fetch_data_with_validation(
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
        """在窗口內執行階段式筆數測試（故意觸發API封鎖）"""
        try:
            # 重置階段索引，確保每個窗口都進行完整測試
            if self.current_stage_index >= len(self.test_stages):
                self.current_stage_index = 0  # 重新開始測試
                
            test_count = self.test_stages[self.current_stage_index]
            
            # 使用改善後的分階段配置選擇時間段和交易對
            test_params = self._get_improved_test_parameters(self.current_stage_index)
            current_timeframe = test_params["timeframe"]
            current_symbol = test_params["symbol"]
            phase = test_params["phase"]
            
            self.emit(f"[CAPACITY] 🧪 階段 {self.current_stage_index + 1}/{len(self.test_stages)}: 測試 {test_count} 筆資料")
            self.emit(f"[CAPACITY] 📊 交易對: {current_symbol} | K線時間段: {current_timeframe} | 階段: {phase}")
            self.emit(f"[CAPACITY] 🎯 目標：通過分階段時間範圍避免重複資料並觸發API封鎖")
            self.emit(f"[CAPACITY] ⏰ 時間範圍: {test_params['time_info']}")
            
            # 顯示進度條
            progress = (self.current_stage_index + 1) / len(self.test_stages) * 100
            progress_bar = "█" * int(progress // 10) + "░" * (10 - int(progress // 10))
            self.emit(f"[CAPACITY] 📊 測試進度: [{progress_bar}] {progress:.1f}%")
            
            success, data_count, time_range, raw_data = self._fetch_data_with_validation(
                current_symbol, current_timeframe, test_count
            )
            
            if success and data_count > 0:
                self.max_successful_count = max(self.max_successful_count, data_count)
                self.current_window_data += data_count
                
                self.emit(f"[CAPACITY] ✅ 成功獲取 {data_count} 筆資料")
                self.emit(f"[CAPACITY] 📊 目前最大成功筆數: {self.max_successful_count}")
                
                # 顯示實時統計
                total_requests = self.validation_stats["total_requests"]
                success_rate = (self.current_stage_index + 1) / len(self.test_stages) * 100 if self.test_stages else 0
                self.emit(f"[CAPACITY] 📈 成功率: {success_rate:.1f}% | 總請求: {total_requests} | API封鎖: {self.api_lock_count}")
                
                # 記錄資料時間範圍
                if time_range:
                    self.data_time_ranges.append(time_range)
                    start_str = time_range[0].strftime('%Y-%m-%d %H:%M:%S')
                    end_str = time_range[1].strftime('%Y-%m-%d %H:%M:%S')
                    self.emit(f"[CAPACITY] ⏰ 資料時間範圍: {start_str} 至 {end_str}")
                
                # 進入下一階段，更新時間段和交易對索引
                self.current_stage_index += 1
                self.current_timeframe_index += 1
                
                # 每3個階段更換交易對
                if self.current_stage_index % 3 == 0:
                    self.current_symbol_index += 1
                
                # 更短的休息時間，增加觸發封鎖的機會
                time.sleep(0.05)  # 減少到50毫秒，更激進
                
                # 如果還有更多階段，立即繼續測試
                if self.current_stage_index < len(self.test_stages):
                    self.emit(f"[CAPACITY] 🔄 立即進行下一階段測試...")
                    self._run_capacity_test_in_window()  # 遞歸調用繼續測試
                
            else:
                self.emit(f"[CAPACITY] ❌ 階段 {self.current_stage_index + 1} 測試失敗或被封鎖")
                if self.api_lock_count > 0:
                    self.emit(f"[CAPACITY] 🎯 成功觸發API封鎖！這是預期行為")
                    self.emit(f"[CAPACITY] 📈 封鎖前最大成功筆數: {self.max_successful_count}")
                else:
                    self.emit(f"[CAPACITY] 📈 測試完成，最大成功筆數: {self.max_successful_count}")
                
        except Exception as e:
            self.emit(f"[CAPACITY] 階段測試異常: {e}")
            # 檢查是否為API限制相關異常
            if "429" in str(e) or "rate limit" in str(e).lower() or "banned" in str(e).lower():
                self.emit(f"[CAPACITY] 🎯 成功觸發API限制異常！這是預期行為")
                self.emit(f"[CAPACITY] 💡 API限制類型: {type(e).__name__}")
                self.api_lock_count += 1
            elif "400" in str(e) or "Bad Request" in str(e):
                self.emit(f"[CAPACITY] ❌ API請求參數錯誤: {e}")
                self.emit(f"[CAPACITY] 💡 請檢查貨幣對和時間框架設定")
            else:
                self.emit(f"[CAPACITY] ❌ 未知錯誤: {e}")
                self.emit(f"[CAPACITY] 💡 錯誤類型: {type(e).__name__}")
            
    def _fetch_data_with_validation(self, symbol: str, timeframe: str, count: int) -> Tuple[bool, int, Optional[Tuple[datetime, datetime]], Optional[List]]:
        """獲取資料並進行11項欄位驗證"""
        try:
            # 計算時間範圍
            end_time = int(time.time() * 1000)
            start_time = end_time - (count * self._get_timeframe_ms(timeframe))
            
            data = get_binance_klines_http(symbol, timeframe, start_time, end_time, count)
            self.validation_stats["total_requests"] += 1
            
            if data and len(data) > 0:
                # 解析資料時間範圍
                first_time = datetime.fromtimestamp(data[0][0] / 1000)
                last_time = datetime.fromtimestamp(data[-1][0] / 1000)
                
                # 重複資料檢測
                duplicate_count = self._check_duplicate_data(data)
                if duplicate_count > 0:
                    self.duplicate_data_count += duplicate_count
                    self.emit(f"[DUPLICATE] ⚠️ 發現 {duplicate_count} 筆重複時間戳資料")
                    self.emit(f"[DUPLICATE] 📊 累計重複資料: {self.duplicate_data_count} 筆")
                
                # 11項資料驗證（如果啟用）
                if self.enable_data_validation:
                    valid_count, validation_report = self._validate_kline_data(data)
                    self.validation_stats["valid_data_count"] += valid_count
                    self.validation_stats["invalid_data_count"] += (len(data) - valid_count)
                    
                    if validation_report:
                        self.emit(f"[VALIDATION] 📊 資料驗證: {valid_count}/{len(data)} 筆有效")
                        if len(data) - valid_count > 0:
                            self.emit(f"[VALIDATION] ⚠️ 發現 {len(data) - valid_count} 筆無效資料")
                
                return True, len(data), (first_time, last_time), data
            else:
                return False, 0, None, None
                
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                self.api_lock_count += 1
                self.evaluator.mark_lock(timeframe, count)
                self.emit(f"[API_LIMIT] 🚫 觸發API限制 (第{self.api_lock_count}次): {e}")
                self.emit(f"[API_LIMIT] 📊 當前測試筆數: {count}, 最大成功筆數: {self.max_successful_count}")
            else:
                self.emit(f"[ERROR] API請求失敗: {e}")
            return False, 0, None, None
            
    def _validate_kline_data(self, data: List) -> Tuple[int, Dict]:
        """驗證K線資料的11項欄位完整性"""
        valid_count = 0
        validation_report = {
            "total_items": len(data),
            "field_errors": {},
            "sample_data": None
        }
        
        # Binance K線資料的11個欄位：
        # [0] 開盤時間, [1] 開盤價, [2] 最高價, [3] 最低價, [4] 收盤價,
        # [5] 成交量, [6] 收盤時間, [7] 成交額, [8] 成交筆數,
        # [9] 主動買入成交量, [10] 主動買入成交額
        
        required_fields = 11
        field_names = [
            "開盤時間", "開盤價", "最高價", "最低價", "收盤價",
            "成交量", "收盤時間", "成交額", "成交筆數", 
            "主動買入成交量", "主動買入成交額"
        ]
        
        for i, item in enumerate(data):
            is_valid = True
            
            # 檢查欄位數量
            if len(item) < required_fields:
                validation_report["field_errors"][f"item_{i}"] = f"欄位不足，只有{len(item)}個欄位"
                is_valid = False
                continue
            
            # 檢查每個欄位的有效性
            for field_idx in range(required_fields):
                if item[field_idx] is None:
                    validation_report["field_errors"][f"item_{i}_field_{field_idx}"] = f"{field_names[field_idx]}為空值"
                    is_valid = False
                elif field_idx in [0, 6, 8]:  # 時間戳和成交筆數應為整數
                    try:
                        int(item[field_idx])
                    except (ValueError, TypeError):
                        validation_report["field_errors"][f"item_{i}_field_{field_idx}"] = f"{field_names[field_idx]}格式錯誤"
                        is_valid = False
                else:  # 價格和成交量應為數值
                    try:
                        float(item[field_idx])
                    except (ValueError, TypeError):
                        validation_report["field_errors"][f"item_{i}_field_{field_idx}"] = f"{field_names[field_idx]}格式錯誤"
                        is_valid = False
            
            if is_valid:
                valid_count += 1
                # 保存第一筆有效資料作為樣本
                if validation_report["sample_data"] is None:
                    validation_report["sample_data"] = {
                        "開盤時間": datetime.fromtimestamp(item[0]/1000).strftime('%Y-%m-%d %H:%M:%S'),
                        "開盤價": item[1],
                        "最高價": item[2],
                        "最低價": item[3],
                        "收盤價": item[4],
                        "成交量": item[5]
                    }
        
        return valid_count, validation_report
    
    def _check_duplicate_data(self, data: List) -> int:
        """檢測重複的時間戳資料"""
        if not data:
            return 0
        
        duplicate_count = 0
        duplicate_samples = []
        
        for kline in data:
            timestamp = kline[0]  # 開盤時間戳
            
            if timestamp in self.received_timestamps:
                duplicate_count += 1
                # 只收集前3筆重複資料作為樣本
                if len(duplicate_samples) < 3:
                    timestamp_dt = datetime.fromtimestamp(timestamp / 1000)
                    duplicate_samples.append(timestamp_dt.strftime('%H:%M:%S'))
            else:
                self.received_timestamps.add(timestamp)
        
        if duplicate_count > 0:
            # 簡化顯示：只顯示統計和樣本
            if duplicate_samples:
                sample_str = ", ".join(duplicate_samples)
                if duplicate_count > 3:
                    sample_str += f" ...等{duplicate_count}筆"
                self.emit(f"[DUPLICATE] 🔍 重複時間戳樣本: {sample_str}")
            
            self.emit(f"[DUPLICATE] ⚠️ 本次發現 {duplicate_count} 筆重複資料")
            self.duplicate_data_count += duplicate_count
            self.emit(f"[DUPLICATE] 📊 累計重複資料: {self.duplicate_data_count} 筆")
        
        return duplicate_count
    
    def _fetch_data_with_time_range(self, symbol: str, timeframe: str, count: int) -> Tuple[bool, int, Optional[Tuple[datetime, datetime]]]:
        """獲取資料並返回時間範圍（向後相容性方法）"""
        success, data_count, time_range, raw_data = self._fetch_data_with_validation(symbol, timeframe, count)
        return success, data_count, time_range
            
    def _get_timeframe_ms(self, timeframe: str) -> int:
        """取得時間框架的毫秒數"""
        timeframe_map = {
            "1m": 60 * 1000,
            "3m": 3 * 60 * 1000,
            "5m": 5 * 60 * 1000,
            "15m": 15 * 60 * 1000,
            "30m": 30 * 60 * 1000,
            "1h": 60 * 60 * 1000,
            "2h": 2 * 60 * 60 * 1000,
            "4h": 4 * 60 * 60 * 1000,
            "6h": 6 * 60 * 60 * 1000,
            "8h": 8 * 60 * 60 * 1000,
            "12h": 12 * 60 * 60 * 1000,
            "1d": 24 * 60 * 60 * 1000,
            "3d": 3 * 24 * 60 * 60 * 1000,
            "1w": 7 * 24 * 60 * 60 * 1000,
            "1M": 30 * 24 * 60 * 60 * 1000,  # 30天近似值
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
            tf_key = f"{minutes}m"  # 統一使用分鐘格式，避免"1h"鍵不存在的問題
            
            # 檢查是否需要更新該時間框架
            if window_time.minute % minutes == 0:
                self.timeframe_stats[tf_key]["total"] += data_count
                self.timeframe_stats[tf_key]["windows"].append({
                    "time": window_time,
                    "count": data_count
                })
                
    def _complete_anchor_cycle(self):
        """完成錨定週期統計（整合版本）"""
        self.emit("[INTEGRATED] === 🎯 整合測試週期完成 ===")
        
        total_time = time.time() - self.anchor_start_time
        self.emit(f"[INTEGRATED] ⏱️ 總耗時: {total_time:.2f} 秒 ({total_time/60:.1f} 分鐘)")
        
        # 顯示階段式測試結果
        if self.enable_capacity_test:
            self.emit("[INTEGRATED] === 📊 階段式測試結果 ===")
            self.emit(f"[INTEGRATED] 🏆 最大成功筆數: {self.max_successful_count}")
            self.emit(f"[INTEGRATED] 🚫 API被鎖次數: {self.api_lock_count}")
            self.emit(f"[INTEGRATED] 📋 測試階段: {self.test_stages}")
            
            if self.max_successful_count > 0:
                # 根據測試結果給出建議
                safe_count = int(self.max_successful_count * 0.8)  # 80%安全係數
                self.emit(f"[INTEGRATED] 💡 建議安全筆數: {safe_count} (80%安全係數)")
        
        # 顯示重複資料檢測結果
        self.emit("[INTEGRATED] === 🔍 重複資料檢測結果 ===")
        self.emit(f"[INTEGRATED] 📊 總請求次數: {self.validation_stats['total_requests']}")
        self.emit(f"[INTEGRATED] 🔄 重複資料筆數: {self.duplicate_data_count}")
        self.emit(f"[INTEGRATED] 📈 資料唯一性: {len(self.received_timestamps)} 個唯一時間戳")
        
        if self.validation_stats['total_requests'] > 0:
            total_data = self.validation_stats['valid_data_count'] + self.validation_stats['invalid_data_count']
            if total_data > 0:
                duplicate_rate = (self.duplicate_data_count / total_data) * 100
                self.emit(f"[INTEGRATED] 📊 重複率: {duplicate_rate:.2f}%")
                
                if self.duplicate_data_count == 0:
                    self.emit("[INTEGRATED] ✅ 未發現重複資料，API回應正常")
                else:
                    self.emit(f"[INTEGRATED] ⚠️ 發現重複資料，可能API判定資料遺失")
        
        # 顯示資料驗證結果
        if self.enable_data_validation:
            self.emit("[INTEGRATED] === 🔍 資料驗證結果 ===")
            self.emit(f"[INTEGRATED] ✅ 有效資料筆數: {self.validation_stats['valid_data_count']}")
            self.emit(f"[INTEGRATED] ❌ 無效資料筆數: {self.validation_stats['invalid_data_count']}")
            
            if self.validation_stats['total_requests'] > 0:
                valid_rate = (self.validation_stats['valid_data_count'] / 
                            (self.validation_stats['valid_data_count'] + self.validation_stats['invalid_data_count'])) * 100
                self.emit(f"[INTEGRATED] 📈 資料有效率: {valid_rate:.2f}%")
        
        # 顯示各時間框架統計
        self.emit("[INTEGRATED] === ⏰ 時間框架統計 ===")
        for tf, stats in self.timeframe_stats.items():
            if stats["total"] > 0:
                avg_count = stats["total"] / len(stats["windows"]) if stats["windows"] else 0
                self.emit(f"[INTEGRATED] {tf} 框架: 總計 {stats['total']} 筆, 平均 {avg_count:.1f} 筆/窗口, 窗口數 {len(stats['windows'])}")
        
        # 顯示資料時間範圍
        if self.data_time_ranges:
            first_range = self.data_time_ranges[0]
            last_range = self.data_time_ranges[-1]
            self.emit(f"[INTEGRATED] 📅 資料時間範圍: {first_range[0].strftime('%Y/%m/%d %H:%M:%S')} - {last_range[1].strftime('%Y/%m/%d %H:%M:%S')}")
        
        # 顯示本機評估結果
        self.emit("[INTEGRATED] === 🖥️ 本機獲取能力評估 ===")
        if self.max_successful_count > 0:
            # 估算不同時間框架的理論最大筆數
            timeframe_limits = {}
            for tf in ["1m", "3m", "5m", "15m", "30m", "1h"]:
                if tf == "1m":
                    timeframe_limits[tf] = self.max_successful_count
                elif tf == "3m":
                    timeframe_limits[tf] = self.max_successful_count * 3
                elif tf == "5m":
                    timeframe_limits[tf] = self.max_successful_count * 5
                elif tf == "15m":
                    timeframe_limits[tf] = self.max_successful_count * 15
                elif tf == "30m":
                    timeframe_limits[tf] = self.max_successful_count * 30
                elif tf == "1h":
                    timeframe_limits[tf] = self.max_successful_count * 60
                    
            for tf, limit in timeframe_limits.items():
                self.emit(f"[INTEGRATED] {tf} 理論最大: {limit} 筆")
        
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
    
    def _get_improved_test_parameters(self, stage_index: int) -> dict:
        """獲取改善後的測試參數，減少重複資料"""
        # 計算當前階段和階段內的測試索引
        phase = ((stage_index // 4) % 5) + 1
        test_in_phase = stage_index % 4
        
        config = self.test_phases[phase]
        
        # 計算時間範圍
        end_time = datetime.now() - timedelta(days=config["days_offset"])
        
        # 根據時間段計算起始時間
        timeframe = config["timeframes"][test_in_phase]
        symbol = config["symbols"][test_in_phase]
        
        # 動態計算時間範圍避免重疊
        if timeframe == "1m":
            start_time = end_time - timedelta(hours=16, minutes=40)  # 1000分鐘
            time_info = f"{start_time.strftime('%m月%d日%H時%M分')} 到 {end_time.strftime('%m月%d日%H時%M分')} (16小時40分鐘)"
        elif timeframe == "3m":
            start_time = end_time - timedelta(hours=50)  # 3000分鐘
            time_info = f"{start_time.strftime('%m月%d日%H時')} 到 {end_time.strftime('%m月%d日%H時')} (50小時)"
        elif timeframe == "5m":
            start_time = end_time - timedelta(hours=83, minutes=20)  # 5000分鐘
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (3.5天)"
        elif timeframe == "15m":
            start_time = end_time - timedelta(days=10, hours=10)  # 15000分鐘
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (10天)"
        elif timeframe == "30m":
            start_time = end_time - timedelta(days=20, hours=20)  # 30000分鐘
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (21天)"
        elif timeframe == "1h":
            start_time = end_time - timedelta(days=41, hours=16)  # 1000小時
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (42天)"
        elif timeframe == "2h":
            start_time = end_time - timedelta(days=83, hours=8)  # 2000小時
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (83天)"
        elif timeframe == "4h":
            start_time = end_time - timedelta(days=166, hours=16)  # 4000小時
            time_info = f"{start_time.strftime('%m月%d日')} 到 {end_time.strftime('%m月%d日')} (167天)"
        else:
            start_time = end_time - timedelta(hours=16, minutes=40)
            time_info = f"{start_time.strftime('%m月%d日%H時%M分')} 到 {end_time.strftime('%m月%d日%H時%M分')} (16小時40分鐘)"
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "start_time": start_time,
            "end_time": end_time,
            "phase": phase,
            "time_info": time_info,
            "expected_overlap": self._calculate_expected_overlap(stage_index)
        }
    
    def _calculate_expected_overlap(self, stage_index: int) -> float:
        """計算預期重疊率"""
        # 基於階段配置計算預期重疊率
        phase = ((stage_index // 4) % 5) + 1
        
        # 不同階段的預期重疊率不同
        if phase == 1:
            return 0.05  # 最近1天，預期5%重疊
        elif phase == 2:
            return 0.03  # 2-3天前，預期3%重疊
        elif phase == 3:
            return 0.02  # 4-7天前，預期2%重疊
        elif phase == 4:
            return 0.01  # 1-2週前，預期1%重疊
        else:
            return 0.01  # 2-4週前，預期1%重疊
    
    def should_adjust_strategy(self, duplicate_rate: float) -> bool:
        """判斷是否需要調整策略"""
        return duplicate_rate > self.duplicate_threshold

# 全域實例
_anchor_engine: Optional[AnchorTimeEngine] = None

def get_anchor_time_engine(gui_callback: Optional[Callable] = None) -> AnchorTimeEngine:
    """取得錨定時間引擎實例"""
    global _anchor_engine
    if _anchor_engine is None:
        _anchor_engine = AnchorTimeEngine(gui_callback)
    return _anchor_engine
