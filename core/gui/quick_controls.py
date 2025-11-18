"""
quick_controls.py - 快捷控制項
負責快捷按鈕和快捷功能的管理
"""

import tkinter as tk
from tkinter import ttk
from .layout_config import (
    QUICK_BUTTONS_FRAME_PADY,
    QUICK_BUTTONS_FRAME_PADX,
    QUICK_BUTTONS_PADY,
)

class QuickControls:
    """快捷控制項管理器"""
    
    def __init__(self, gui, datetime_controls):
        self.gui = gui
        self.datetime_controls = datetime_controls
        
    def create_quick_buttons(self, parent_frame):
        """創建快捷按鈕"""
        # === 快捷按鈕 ===
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(anchor=tk.W, pady=QUICK_BUTTONS_FRAME_PADY, padx=QUICK_BUTTONS_FRAME_PADX, fill=tk.X)

        # 創建快捷按鈕
        self.quick_now_btn = ttk.Button(button_frame, text="🕐 現在", command=self._set_current_time)
        self.quick_yesterday_btn = ttk.Button(button_frame, text="📅 昨天→今天", command=self._set_yesterday_to_today)
        self.quick_week_btn = ttk.Button(button_frame, text="📊 最近一週", command=self._set_last_week)

        # pack佈局
        self.quick_now_btn.pack(side=tk.LEFT, padx=(0, 5), pady=QUICK_BUTTONS_PADY)
        self.quick_yesterday_btn.pack(side=tk.LEFT, padx=(0, 5), pady=QUICK_BUTTONS_PADY)
        self.quick_week_btn.pack(side=tk.LEFT, padx=0, pady=QUICK_BUTTONS_PADY)

        return [self.quick_now_btn, self.quick_yesterday_btn, self.quick_week_btn]
        
    def get_quick_button_keys(self):
        """取得快捷按鈕鍵映射"""
        return {
            self.quick_now_btn: "quick_now",
            self.quick_yesterday_btn: "quick_yesterday",
            self.quick_week_btn: "quick_week"
        }
        
    def _set_current_time(self):
        """設定為當前時間"""
        self.datetime_controls.set_current_time()
        
    def _set_yesterday_to_today(self):
        """設定昨天到今天的時間範圍"""
        self.datetime_controls.set_yesterday_to_today()
        
    def _set_last_week(self):
        """設定最近一週的時間範圍"""
        self.datetime_controls.set_last_week()
