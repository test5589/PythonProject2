#!/usr/bin/env python3
"""
time_frame_manager.py - 時間框架管理器
管理多時間框架統計和時間相關計算
"""

from datetime import datetime
from typing import Dict, List, Callable

class TimeFrameManager:
    """時間框架管理器"""
    
    def __init__(self):
        # 多時間框架統計
        self.timeframe_stats = {
            "1m": {"total": 0, "windows": []},
            "3m": {"total": 0, "windows": []}, 
            "5m": {"total": 0, "windows": []},
            "10m": {"total": 0, "windows": []},
            "30m": {"total": 0, "windows": []},
            "60m": {"total": 0, "windows": []}  # 添加60m鍵
        }
        
    def reset_timeframe_stats(self):
        """重置時間框架統計"""
        for tf in self.timeframe_stats:
            self.timeframe_stats[tf] = {"total": 0, "windows": []}
            
    def get_timeframe_stats(self, timeframe: str) -> Dict:
        """取得指定時間框架的統計資料"""
        return self.timeframe_stats.get(timeframe, {"total": 0, "windows": []})
        
    def update_timeframe_statistics(self, window_time: datetime, data_count: int):
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
            tf_key = f"{minutes}m"
            
            # 檢查是否需要更新該時間框架
            if window_time.minute % minutes == 0:
                self.timeframe_stats[tf_key]["total"] += data_count
                self.timeframe_stats[tf_key]["windows"].append({
                    "time": window_time,
                    "count": data_count
                })
                
    def show_timeframe_statistics(self, emit_func: Callable):
        """顯示各時間框架統計"""
        emit_func("[INTEGRATED] === ⏰ 時間框架統計 ===")
        for tf, stats in self.timeframe_stats.items():
            if stats["total"] > 0:
                avg_count = stats["total"] / len(stats["windows"]) if stats["windows"] else 0
                emit_func(f"[INTEGRATED] {tf} 框架: 總計 {stats['total']} 筆, 平均 {avg_count:.1f} 筆/窗口, 窗口數 {len(stats['windows'])}")
                
    def get_timeframe_ms(self, timeframe: str) -> int:
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
        
    def calculate_theoretical_limits(self, max_successful_count: int, emit_func: Callable):
        """計算理論最大筆數"""
        emit_func("[INTEGRATED] === 🖥️ 本機獲取能力評估 ===")
        if max_successful_count > 0:
            # 估算不同時間框架的理論最大筆數
            timeframe_limits = {}
            for tf in ["1m", "3m", "5m", "15m", "30m", "1h"]:
                if tf == "1m":
                    timeframe_limits[tf] = max_successful_count
                elif tf == "3m":
                    timeframe_limits[tf] = max_successful_count * 3
                elif tf == "5m":
                    timeframe_limits[tf] = max_successful_count * 5
                elif tf == "15m":
                    timeframe_limits[tf] = max_successful_count * 15
                elif tf == "30m":
                    timeframe_limits[tf] = max_successful_count * 30
                elif tf == "1h":
                    timeframe_limits[tf] = max_successful_count * 60
                    
            for tf, limit in timeframe_limits.items():
                emit_func(f"[INTEGRATED] {tf} 理論最大: {limit} 筆")
