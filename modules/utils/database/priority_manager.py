"""
priority_manager.py - 數據優先級管理
負責管理不同數據來源的優先級和覆蓋邏輯
"""

from typing import Optional, Dict
from modules.utils.logger import get_logger

logger = get_logger("priority_manager")


class PriorityManager:
    """
    數據優先級管理器
    
    管理不同數據來源的優先級，決定哪些數據可以覆蓋現有數據。
    優先級越低的數據可以覆蓋優先級越高的數據。
    """
    
    # 優先級映射：數字越小，優先級越高
    PRIORITY_MAP = {
        'real': 1,            # 真實數據（最高優先級）
        'interpolated': 2,    # 插值數據
        'Aggregation': 3,     # 聚合數據
        'inferior-Aggregation': 4  # 低質量聚合數據（最低優先級）
    }
    
    # 時間間隔映射
    INTERVAL_MAP = {
        1: "1s",
        60: "1m",
        300: "5m",
        900: "15m",
        1800: "30m",
        3600: "1h",
        14400: "4h",
        28800: "8h",
        43200: "12h",
        86400: "1d"
    }
    
    def __init__(self):
        """初始化優先級管理器"""
        pass
    
    def get_priority(self, data_source: str) -> int:
        """
        獲取數據來源的優先級
        
        Args:
            data_source: 數據來源標識
            
        Returns:
            int: 優先級數字（越小越高），未知來源返回999
        """
        return self.PRIORITY_MAP.get(data_source, 999)
    
    def can_overwrite(self, existing_source: str, new_source: str) -> bool:
        """
        判斷新數據是否可以覆蓋現有數據
        
        Args:
            existing_source: 現有數據來源
            new_source: 新數據來源
            
        Returns:
            bool: 可以覆蓋返回True
        """
        existing_priority = self.get_priority(existing_source)
        new_priority = self.get_priority(new_source)
        
        # 新數據優先級更高（數字更小）才能覆蓋
        can_replace = new_priority < existing_priority
        
        if not can_replace:
            logger.debug(
                f"優先級不足，無法覆蓋: "
                f"新={new_source}({new_priority}) vs 舊={existing_source}({existing_priority})"
            )
        
        return can_replace
    
    def get_interval_label(self, interval_seconds: int) -> str:
        """
        獲取時間間隔的可讀標籤
        
        Args:
            interval_seconds: 時間間隔（秒）
            
        Returns:
            str: 可讀標籤，如 "1m", "5m", "1h"
        """
        return self.INTERVAL_MAP.get(interval_seconds, f"{interval_seconds}s")
    
    def validate_data_source(self, data_source: str) -> bool:
        """
        驗證數據來源是否有效
        
        Args:
            data_source: 數據來源標識
            
        Returns:
            bool: 有效返回True
        """
        if not data_source:
            return False
        
        # 如果不在已知列表中，記錄警告但仍然接受
        if data_source not in self.PRIORITY_MAP:
            logger.warning(f"未知的數據來源: {data_source}，將使用默認優先級")
        
        return True


# 全域實例
priority_manager = PriorityManager()
