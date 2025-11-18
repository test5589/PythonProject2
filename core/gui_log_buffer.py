"""
gui_log_buffer.py - GUI日誌緩衝系統
解決高頻日誌導致GUI卡死的問題
"""

import threading
import time
from collections import deque


class LogBuffer:
    """日誌緩衝器 - 批量更新GUI，避免過度使用root.after"""
    
    def __init__(self, gui, update_interval_ms=500, max_buffer_size=100):
        """
        初始化日誌緩衝器
        
        Args:
            gui: GUI實例
            update_interval_ms: GUI更新間隔（毫秒）
            max_buffer_size: 最大緩衝數量（達到後立即flush）
        """
        self.gui = gui
        self.buffer = deque()
        self.lock = threading.Lock()
        self.update_interval = update_interval_ms
        self.max_buffer_size = max_buffer_size  # 保留但不再用於觸發立即flush
        self.is_running = True
        
        # 啟動定時更新
        self._schedule_update()
    
    def add(self, msg: str):
        """
        添加日誌到緩衝區
        
        Args:
            msg: 日誌消息
        """
        with self.lock:
            self.buffer.append(msg)
            
            # 🔧 緊急修復：移除「緩衝區滿立即flush」邏輯
            # 這會導致大量 root.after() 調用，是GUI卡頓的根本原因
            # 現在只依靠定時器定期flush（每500ms）
            # 
            # ❌ 舊邏輯（導致卡頓）：
            # if len(self.buffer) >= 100:
            #     self.gui.root.after(0, self._flush_buffer)  # 每100條就調用一次
            #
            # ✅ 新邏輯（流暢）：
            # 只由定時器在 _schedule_update() 中定期flush
    
    def _schedule_update(self):
        """定期更新GUI（每500ms）"""
        if not self.is_running:
            return
        
        # 🔧 優化：只在有訊息時才flush
        if self.buffer:
            self._flush_buffer()
        
        # 繼續下一次更新
        self.gui.root.after(self.update_interval, self._schedule_update)
    
    def _flush_buffer(self):
        """將緩衝區內容批量寫入GUI"""
        with self.lock:
            if not self.buffer:
                return
            
            # 取出所有待處理的日誌
            self.buffer.clear()
    
    def flush_now(self):
        """立即flush所有緩衝日誌"""
        self.gui.root.after(0, self._flush_buffer)
    
    def stop(self):
        """停止緩衝器"""
        self.is_running = False
        self.flush_now()  # 最後flush一次


class BufferedGUILogger:
    """
    帶緩衝的GUI日誌記錄器
    用於替代直接的 root.after(0, lambda: gui.log(msg))
    """
    
    def __init__(self, gui, use_buffer=True):
        """
        初始化
        
        Args:
            gui: GUI實例
            use_buffer: 是否使用緩衝（默認True）
        """
        self.gui = gui
        self.use_buffer = use_buffer
        
        if use_buffer:
            self.buffer = LogBuffer(gui, update_interval_ms=500, max_buffer_size=100)
        else:
            self.buffer = None
    
    def log(self, msg: str):
        """
        記錄日誌
        
        Args:
            msg: 日誌消息
        """
        if self.use_buffer and self.buffer:
            # 使用緩衝（推薦）
            self.buffer.add(msg)
        else:
            return
    
    def __call__(self, msg: str):
        """允許作為函數調用"""
        self.log(msg)
    
    def flush(self):
        """立即flush緩衝"""
        if self.buffer:
            self.buffer.flush_now()
    
    def stop(self):
        """停止並清理"""
        if self.buffer:
            self.buffer.stop()
