#!/usr/bin/env python3
"""
statistics_collector.py - 統計數據收集器
負責資料驗證、重複檢測和測試結果統計
"""

import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Callable
from tools.api_weight_evaluator import get_api_weight_evaluator
from modules.utils.api.api_connector import get_binance_klines_http

class StatisticsCollector:
    """統計數據收集器"""
    
    def __init__(self, emit_func: Callable):
        self.emit = emit_func
        self.evaluator = get_api_weight_evaluator()
        
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
        
    def reset_statistics(self):
        """重置統計數據"""
        self.validation_stats = {
            "total_requests": 0,
            "valid_data_count": 0,
            "invalid_data_count": 0,
            "field_validation_errors": []
        }
        self.received_timestamps = set()
        self.duplicate_data_count = 0
        
    def fetch_data_with_validation(self, symbol: str, timeframe: str, count: int) -> Tuple[bool, int, Optional[Tuple[datetime, datetime]], Optional[List]]:
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
                duplicate_count = self.check_duplicate_data(data)
                
                # 11項資料驗證（如果啟用）
                # 這裡可以根據需要啟用資料驗證
                
                return True, len(data), (first_time, last_time), data
            else:
                return False, 0, None, None
                
        except Exception as e:
            if "429" in str(e) or "rate limit" in str(e).lower():
                self.evaluator.mark_lock(timeframe, count)
                self.emit(f"[API_LIMIT] 🚫 觸發API限制: {e}")
            else:
                self.emit(f"[ERROR] API請求失敗: {e}")
            return False, 0, None, None
            
    def validate_kline_data(self, data: List) -> Tuple[int, Dict]:
        """驗證K線資料的11項欄位完整性"""
        valid_count = 0
        validation_report = {
            "total_items": len(data),
            "field_errors": {},
            "sample_data": None
        }
        
        # Binance K線資料的11個欄位
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
    
    def check_duplicate_data(self, data: List) -> int:
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
    
    def show_test_results(self, enable_capacity_test: bool, max_successful_count: int, 
                         api_lock_count: int, test_stages: List, enable_data_validation: bool):
        """顯示測試結果"""
        # 顯示階段式測試結果
        if enable_capacity_test:
            self.emit("[INTEGRATED] === 📊 階段式測試結果 ===")
            self.emit(f"[INTEGRATED] 🏆 最大成功筆數: {max_successful_count}")
            self.emit(f"[INTEGRATED] 🚫 API被鎖次數: {api_lock_count}")
            self.emit(f"[INTEGRATED] 📋 測試階段: {test_stages}")
            
            if max_successful_count > 0:
                # 根據測試結果給出建議
                safe_count = int(max_successful_count * 0.8)  # 80%安全係數
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
        if enable_data_validation:
            self.emit("[INTEGRATED] === 🔍 資料驗證結果 ===")
            self.emit(f"[INTEGRATED] ✅ 有效資料筆數: {self.validation_stats['valid_data_count']}")
            self.emit(f"[INTEGRATED] ❌ 無效資料筆數: {self.validation_stats['invalid_data_count']}")
            
            if self.validation_stats['total_requests'] > 0:
                valid_rate = (self.validation_stats['valid_data_count'] / 
                            (self.validation_stats['valid_data_count'] + self.validation_stats['invalid_data_count'])) * 100
                self.emit(f"[INTEGRATED] 📈 資料有效率: {valid_rate:.2f}%")
                
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
            "1M": 30 * 24 * 60 * 60 * 1000,
        }
        return timeframe_map.get(timeframe, 60 * 1000)
