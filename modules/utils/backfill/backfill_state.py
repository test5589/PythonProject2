"""
backfill_state.py
回補狀態管理器 - 處理回補暫停/恢復/停止功能
"""

import threading
from dataclasses import dataclass
from typing import Optional, Callable, Any
from datetime import datetime, timezone

@dataclass
class BackfillState:
    """回補狀態"""
    is_running: bool = False
    is_paused: bool = False
    is_stopped: bool = False
    current_symbol: str = ""
    current_interval: str = ""
    current_index: int = 0
    total_items: int = 0
    last_processed_time: Optional[datetime] = None
    error_message: Optional[str] = None

class BackfillStateManager:
    """回補狀態管理器"""
    
    def __init__(self):
        self.state = BackfillState()
        self._lock = threading.Lock()
        self._progress_callback: Optional[Callable] = None
        self._current_thread: Optional[threading.Thread] = None
        
    def start_backfill(self, symbol: str, interval: str, total_items: int, 
                      progress_callback: Optional[Callable] = None):
        """開始回補"""
        with self._lock:
            self.state = BackfillState(
                is_running=True,
                is_paused=False,
                is_stopped=False,
                current_symbol=symbol,
                current_interval=interval,
                current_index=0,
                total_items=total_items,
                last_processed_time=datetime.now(timezone.utc)
            )
            self._progress_callback = progress_callback
            
    def update_progress(self, index: int, message: str = ""):
        """更新進度"""
        with self._lock:
            if self.state.is_stopped:
                raise InterruptedError("回補已被停止")
            
            self.state.current_index = index
            self.state.last_processed_time = datetime.now(timezone.utc)
            
            if self._progress_callback:
                self._progress_callback(message)
        
        # 在釋放鎖之後檢查暫停狀態
        while True:
            with self._lock:
                if self.state.is_stopped:
                    raise InterruptedError("回補已被停止")
                if not self.state.is_paused:
                    break
            # 暫停狀態，短暫休眠後再檢查
            import time
            time.sleep(0.1)
                
    def pause_backfill(self):
        """暫停回補"""
        with self._lock:
            if self.state.is_running and not self.state.is_paused:
                self.state.is_paused = True
                return True
            return False
            
    def resume_backfill(self):
        """恢復回補"""
        with self._lock:
            if self.state.is_running and self.state.is_paused:
                self.state.is_paused = False
                return True
            return False
            
    def stop_backfill(self):
        """完全停止回補"""
        with self._lock:
            self.state.is_stopped = True
            self.state.is_running = False
            self.state.is_paused = False
            
    def get_state(self) -> BackfillState:
        """獲取當前狀態"""
        with self._lock:
            return BackfillState(
                is_running=self.state.is_running,
                is_paused=self.state.is_paused,
                is_stopped=self.state.is_stopped,
                current_symbol=self.state.current_symbol,
                current_interval=self.state.current_interval,
                current_index=self.state.current_index,
                total_items=self.state.total_items,
                last_processed_time=self.state.last_processed_time,
                error_message=self.state.error_message
            )
            
    def finish_backfill(self):
        """完成回補"""
        with self._lock:
            self.state.is_running = False
            self.state.is_paused = False
    
    def set_current_target(self, symbol: str, interval: str):
        """更新目前處理的貨幣對與間隔"""
        with self._lock:
            self.state.current_symbol = symbol
            self.state.current_interval = interval
            
    def set_error(self, error_message: str):
        """設定錯誤訊息"""
        with self._lock:
            self.state.error_message = error_message
            self.state.is_running = False

# 全域狀態管理器
backfill_state_manager = BackfillStateManager()
