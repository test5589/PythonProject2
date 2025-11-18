"""
gui_progress_bar.py - 回補進度條UI組件
替代詳細日誌，提供清晰的進度顯示
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime


class BackfillProgressBar:
    """回補進度條UI組件"""
    
    def __init__(self, parent_frame):
        """
        初始化進度條
        
        Args:
            parent_frame: 父容器
        """
        # 創建容器
        self.container = ttk.LabelFrame(parent_frame, text="📊 回補進度", padding=10)
        self.container.pack(fill=tk.X, padx=5, pady=5)
        
        # 主進度條（總體進度）
        self.main_label = ttk.Label(self.container, text="等待開始...")
        self.main_label.pack(fill=tk.X)
        
        self.main_progress = ttk.Progressbar(
            self.container, 
            mode='determinate',
            maximum=100
        )
        self.main_progress.pack(fill=tk.X, pady=(2, 5))
        
        # 當前批次進度條
        self.batch_label = ttk.Label(self.container, text="")
        self.batch_label.pack(fill=tk.X)
        
        self.batch_progress = ttk.Progressbar(
            self.container,
            mode='determinate',
            maximum=100
        )
        self.batch_progress.pack(fill=tk.X, pady=(2, 5))
        
        # 統計信息
        self.stats_frame = ttk.Frame(self.container)
        self.stats_frame.pack(fill=tk.X, pady=(5, 0))
        
        # 左側統計
        self.left_stats = ttk.Label(self.stats_frame, text="", anchor=tk.W)
        self.left_stats.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 右側統計
        self.right_stats = ttk.Label(self.stats_frame, text="", anchor=tk.E)
        self.right_stats.pack(side=tk.RIGHT)
        
        # 異常日誌區域（摺疊式）
        self.exception_frame = ttk.LabelFrame(
            self.container, 
            text="⚠️ 異常記錄（最近10筆）",
            padding=5
        )
        self.exception_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # 異常日誌文本框（小型）
        self.exception_text = tk.Text(
            self.exception_frame,
            height=5,
            width=50,
            font=("Courier New", 8),
            wrap=tk.NONE,
            bg="#FFF3CD",  # 淺黃色背景
            fg="#856404"   # 深黃色文字
        )
        self.exception_text.pack(fill=tk.BOTH, expand=True)
        
        # 異常日誌滾動條
        exception_scroll = ttk.Scrollbar(
            self.exception_text,
            command=self.exception_text.yview
        )
        exception_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.exception_text.config(yscrollcommand=exception_scroll.set)
        
        # 異常記錄緩衝（最多保留10筆） - 必須在reset()之前初始化
        self.exception_buffer = []
        self.max_exceptions = 10
        
        # 初始狀態
        self.reset()
    
    def reset(self):
        """重置進度條"""
        self.main_progress['value'] = 0
        self.batch_progress['value'] = 0
        self.main_label.config(text="等待開始...")
        self.batch_label.config(text="")
        self.left_stats.config(text="")
        self.right_stats.config(text="")
        self.exception_text.delete('1.0', tk.END)
        self.exception_buffer.clear()
    
    def update_main_progress(self, current, total, symbol, interval):
        """
        更新主進度條
        
        Args:
            current: 當前處理數量
            total: 總數量
            symbol: 當前貨幣對
            interval: 時間間隔
        """
        if total > 0:
            percentage = (current / total) * 100
            self.main_progress['value'] = percentage
            self.main_label.config(
                text=f"🎯 {symbol}@{interval} | 進度: {current}/{total} ({percentage:.1f}%)"
            )
    
    def update_batch_progress(self, batch_num, batch_current, batch_total):
        """
        更新批次進度條
        
        Args:
            batch_num: 批次編號
            batch_current: 批次內當前位置
            batch_total: 批次總數
        """
        if batch_total > 0:
            percentage = (batch_current / batch_total) * 100
            self.batch_progress['value'] = percentage
            self.batch_label.config(
                text=f"📦 批次 {batch_num} | {batch_current}/{batch_total} ({percentage:.1f}%)"
            )
    
    def set_progress(self, progress: int):
        """提供簡單的百分比更新介面，供非回補核心（如 async_backfill_runner）使用。

        僅更新主進度條的 value，不改變現有文字內容，避免影響原本的 update_main_progress 邏輯。
        """
        try:
            p = max(0, min(100, int(progress)))
            self.main_progress['value'] = p
        except Exception:
            # 任何格式問題都靜默忽略，避免影響回補流程
            pass
    
    def update_stats(self, inserted, skipped, elapsed_time=None):
        """
        更新統計信息
        
        Args:
            inserted: 插入數量
            skipped: 跳過數量
            elapsed_time: 已用時間（秒）
        """
        # 左側：插入和跳過統計
        self.left_stats.config(
            text=f"✅ 插入: {inserted:,} | ⏭️ 跳過: {skipped:,}"
        )
        
        # 右側：時間統計
        if elapsed_time is not None:
            minutes = int(elapsed_time // 60)
            seconds = int(elapsed_time % 60)
            time_str = f"⏱️ {minutes:02d}:{seconds:02d}"
            
            # 計算速度（筆/秒）
            total = inserted + skipped
            if elapsed_time > 0 and total > 0:
                speed = total / elapsed_time
                time_str += f" | 速度: {speed:.1f} 筆/秒"
            
            self.right_stats.config(text=time_str)
    
    def add_exception(self, exception_type, message):
        """
        添加異常記錄（只保留最近10筆）
        
        Args:
            exception_type: 異常類型（skip, error, warning）
            message: 異常訊息
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 根據類型設置圖標
        icon_map = {
            'skip': '⏭️',
            'error': '❌',
            'warning': '⚠️',
            'info': 'ℹ️'
        }
        icon = icon_map.get(exception_type, '•')
        
        # 格式化記錄
        record = f"[{timestamp}] {icon} {message}"
        
        # 添加到緩衝區
        self.exception_buffer.append(record)
        
        # 只保留最近N筆
        if len(self.exception_buffer) > self.max_exceptions:
            self.exception_buffer.pop(0)
        
        # 更新顯示
        self.exception_text.delete('1.0', tk.END)
        self.exception_text.insert('1.0', '\n'.join(self.exception_buffer))
        self.exception_text.see(tk.END)
    
    def set_complete(self, success=True):
        """
        設置完成狀態
        
        Args:
            success: 是否成功完成
        """
        if success:
            self.main_progress['value'] = 100
            self.main_label.config(text="✅ 回補完成！")
            self.batch_progress['value'] = 100
            self.batch_label.config(text="")
        else:
            self.main_label.config(text="❌ 回補失敗或已停止")
            self.batch_label.config(text="")
    
    def hide(self):
        """隱藏進度條"""
        self.container.pack_forget()
    
    def show(self):
        """顯示進度條"""
        self.container.pack(fill=tk.X, padx=5, pady=5)


class ProgressBarLogger:
    """
    進度條日誌記錄器
    將日誌訊息轉換為進度條更新
    """
    
    def __init__(self, progress_bar: BackfillProgressBar):
        """
        初始化
        
        Args:
            progress_bar: 進度條組件
        """
        self.progress_bar = progress_bar
        self.start_time = None
        self.total_inserted = 0
        self.total_skipped = 0
    
    def start(self, symbol, interval):
        """開始記錄"""
        import time
        self.start_time = time.time()
        self.total_inserted = 0
        self.total_skipped = 0
        self.progress_bar.reset()
        self.progress_bar.show()
    
    def log(self, msg: str):
        """
        處理日誌訊息並更新進度條
        
        Args:
            msg: 日誌訊息
        """
        import time
        import re
        
        # 解析訊息類型並更新進度條
        
        # 檢測跳過訊息（聚合和單筆）
        if "筆跳過" in msg or "⏭️" in msg:
            # 記錄為異常（只記錄聚合訊息，避免過多）
            if "最近" in msg and "筆跳過" in msg:
                self.progress_bar.add_exception('skip', msg)
            
            # 解析跳過數量
            try:
                if "總跳過:" in msg:
                    match = re.search(r'總跳過:(\d+)', msg)
                    if match:
                        self.total_skipped = int(match.group(1))
            except:
                pass
        
        # 檢測錯誤訊息
        elif "❌" in msg or "錯誤" in msg or "失敗" in msg or "🚨" in msg:
            self.progress_bar.add_exception('error', msg)
        
        # 檢測警告訊息
        elif "⚠️" in msg or "警告" in msg:
            self.progress_bar.add_exception('warning', msg)
        
        # 檢測批次訊息
        elif "📦 批次" in msg and "正在抓取" in msg:
            try:
                # 解析批次編號
                match = re.search(r'批次\s*(\d+)', msg)
                if match:
                    batch_num = int(match.group(1))
                    self.progress_bar.update_batch_progress(batch_num, 50, 100)
            except:
                pass
        
        # 檢測進度訊息（詳細或聚合）
        elif "總:" in msg or "總計:" in msg:
            try:
                # 解析總進度
                match = re.search(r'總[計:]?\s*(\d+)', msg)
                if match:
                    total = int(match.group(1))
                    self.total_inserted = total - self.total_skipped
                
                # 解析批次內進度
                match = re.search(r'批次(\d+)', msg)
                if match:
                    batch_num = int(match.group(1))
                    # 嘗試解析批次內位置
                    match2 = re.search(r'(\d+)/(\d+)', msg)
                    if match2:
                        current = int(match2.group(1))
                        total_batch = int(match2.group(2))
                        self.progress_bar.update_batch_progress(batch_num, current, total_batch)
            except:
                pass
        
        # 檢測成功插入訊息
        elif "✅" in msg and "批次" in msg:
            try:
                # 更新批次進度為完成
                match = re.search(r'批次(\d+)', msg)
                if match:
                    batch_num = int(match.group(1))
                    self.progress_bar.update_batch_progress(batch_num, 100, 100)
            except:
                pass
        
        # 更新統計
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.progress_bar.update_stats(
                self.total_inserted,
                self.total_skipped,
                elapsed
            )
    
    def finish(self, success=True):
        """完成記錄"""
        self.progress_bar.set_complete(success)
