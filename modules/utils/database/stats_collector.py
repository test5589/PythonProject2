"""
stats_collector.py - 數據操作統計收集
負責收集和管理數據插入、覆蓋、跳過等統計信息
"""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Callable, Any
from threading import Lock
from modules.utils.logger import get_logger

logger = get_logger("stats_collector")

# 提供給 GUI 的可選 hook：當發生重複跳過時，通知外部（例如 MainGUI）
_duplicate_skip_hook: Optional[Callable[[Dict[str, Any]], None]] = None


def set_duplicate_skip_hook(hook: Optional[Callable[[Dict[str, Any]], None]]) -> None:
    """註冊或清除重複跳過事件的 hook。

    這個 hook 會在 record_duplicate_skip 成功記錄一筆重複時被呼叫，
    並傳出一個 dict，包含 category、symbol、interval、timestamp 等資訊。
    """
    global _duplicate_skip_hook
    _duplicate_skip_hook = hook


class StatsCollector:
    """
    統計信息收集器
    
    收集數據插入操作的統計信息，包括：
    - 總插入次數
    - 成功插入次數
    - 覆蓋次數
    - 跳過次數
    - 重複跳過計數
    """
    
    def __init__(self):
        """初始化統計收集器"""
        self._lock = Lock()
        self._stats = {
            'total_insertions': 0,       # 總插入嘗試次數
            'successful_insertions': 0,  # 成功插入次數
            'overwrites': 0,              # 覆蓋次數
            'skipped': 0                  # 跳過次數
        }
        self._duplicate_skip_counters = defaultdict(int)  # 重複跳過計數器
        self._duplicate_log_threshold = 1  # 每1次輸出一次日誌（每次更新目前累積次數）
    
    def increment_total(self) -> None:
        """增加總插入嘗試計數"""
        with self._lock:
            self._stats['total_insertions'] += 1
    
    def increment_successful(self) -> None:
        """增加成功插入計數"""
        with self._lock:
            self._stats['successful_insertions'] += 1
    
    def increment_overwrites(self) -> None:
        """增加覆蓋計數"""
        with self._lock:
            self._stats['overwrites'] += 1
    
    def increment_skipped(self) -> None:
        """增加跳過計數"""
        with self._lock:
            self._stats['skipped'] += 1
    
    def get_successful_count(self) -> int:
        """獲取成功插入計數"""
        with self._lock:
            return self._stats['successful_insertions']
    
    def record_duplicate_skip(
        self, 
        category: str, 
        symbol: str, 
        interval: int, 
        timestamp: float, 
        new_source: str, 
        existing_source: Optional[str]
    ) -> None:
        """
        記錄重複數據跳過，並定期輸出摘要
        
        Args:
            category: 數據分類
            symbol: 交易對符號
            interval: 時間間隔
            timestamp: 時間戳
            new_source: 新數據來源
            existing_source: 現有數據來源
        """
        key = (category, symbol, interval, new_source)
        
        with self._lock:
            self._duplicate_skip_counters[key] += 1
            count = self._duplicate_skip_counters[key]
        
        # 每N次輸出一次日誌，避免日誌過多
        if count % self._duplicate_log_threshold == 0:
            try:
                tw = timezone(timedelta(hours=8))
                readable_time = datetime.fromtimestamp(timestamp, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
                logger.info(
                    f"⏭️ 已跳過 {count} 筆重複 timestamp "
                    f"({category}/{symbol} @ {interval}s, 最新: {readable_time}, "
                    f"現有來源={existing_source}, 新來源={new_source})"
                )

                # 若有 GUI hook，則將資訊傳遞出去（例如更新畫板）
                if _duplicate_skip_hook is not None:
                    try:
                        payload: Dict[str, Any] = {
                            "category": category,
                            "symbol": symbol,
                            "interval": interval,
                            "timestamp": timestamp,
                            "new_source": new_source,
                            "existing_source": existing_source,
                            "count": count,
                            "readable_time": readable_time,
                        }
                        _duplicate_skip_hook(payload)
                    except Exception:
                        # hook 失敗不影響主流程
                        pass
            except Exception as e:
                logger.error(f"記錄重複跳過時發生錯誤: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """
        獲取統計信息副本
        
        Returns:
            Dict[str, int]: 統計信息字典
        """
        with self._lock:
            return self._stats.copy()
    
    def reset_stats(self) -> None:
        """重置所有統計信息"""
        with self._lock:
            self._stats = {
                'total_insertions': 0,
                'successful_insertions': 0,
                'overwrites': 0,
                'skipped': 0
            }
            self._duplicate_skip_counters.clear()
            logger.info("統計信息已重置")
    
    def get_summary(self) -> str:
        """
        獲取統計信息摘要
        
        Returns:
            str: 格式化的統計摘要
        """
        stats = self.get_stats()
        total = stats['total_insertions']
        
        if total == 0:
            return "尚無數據插入操作"
        
        success_rate = (stats['successful_insertions'] / total * 100) if total > 0 else 0
        
        return (
            f"數據插入統計:\n"
            f"  總嘗試: {total}\n"
            f"  成功: {stats['successful_insertions']} ({success_rate:.1f}%)\n"
            f"  覆蓋: {stats['overwrites']}\n"
            f"  跳過: {stats['skipped']}"
        )


# 全域實例
stats_collector = StatsCollector()
