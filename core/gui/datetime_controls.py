"""
datetime_controls.py - 時間日期選擇控制項
負責時間選擇器的創建和管理
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta, timezone
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config.trading_config import TradingConfig
from .layout_config import (
    TIME_FRAME_PADY,
    TIME_FRAME_PADX,
    DATETIME_START_LABELFRAME_PADDING,
    DATETIME_START_LABELFRAME_PADY,
    DATETIME_END_LABELFRAME_PADDING,
    DATETIME_END_LABELFRAME_PADY,
    DATETIME_END_LABELFRAME_PADX,
    ASSET_FRAME_PADY,
    ASSET_FRAME_PADX,
)

class DateTimeControls:
    """時間日期控制項管理器"""
    
    def __init__(self, gui):
        self.gui = gui
        
    def create_datetime_selectors(self, parent_frame):
        """創建開始和結束時間選擇器"""
        # 時間選擇器 - 與其他控制項統一10px左邊距
        time_frame = ttk.Frame(parent_frame)
        time_frame.pack(anchor=tk.W, pady=TIME_FRAME_PADY, padx=TIME_FRAME_PADX, fill=tk.X)

        # 台北時區
        taipei = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz=taipei)
        start_tw = now_tw - timedelta(days=1)

        # === 起始時間 ===
        start_frame = ttk.LabelFrame(time_frame, text="起始時間", padding=DATETIME_START_LABELFRAME_PADDING)
        start_frame.pack(side=tk.LEFT, padx=0, pady=DATETIME_START_LABELFRAME_PADY, anchor=tk.W)

        # 起始時間控件
        self.sy = ttk.Spinbox(start_frame, from_=2020, to=2030, width=5)
        self.sy.set(start_tw.year)
        self.sy.pack(side=tk.LEFT, padx=(0, 2), pady=0)

        ttk.Label(start_frame, text="年", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.sM = ttk.Spinbox(start_frame, from_=1, to=12, width=3, format="%02.0f")
        self.sM.set(start_tw.month)
        self.sM.pack(side=tk.LEFT, padx=0)

        ttk.Label(start_frame, text="月", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.sd = ttk.Spinbox(start_frame, from_=1, to=31, width=3, format="%02.0f")
        self.sd.set(start_tw.day)
        self.sd.pack(side=tk.LEFT, padx=0)

        ttk.Label(start_frame, text="日", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.sh = ttk.Spinbox(start_frame, from_=0, to=23, width=3, format="%02.0f")
        self.sh.set(start_tw.hour)
        self.sh.pack(side=tk.LEFT, padx=0)

        ttk.Label(start_frame, text="時", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.su = ttk.Spinbox(start_frame, from_=0, to=59, width=3, format="%02.0f")
        self.su.set(start_tw.minute)
        self.su.pack(side=tk.LEFT, padx=0)

        ttk.Label(start_frame, text="分", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.ss = ttk.Spinbox(start_frame, from_=0, to=59, width=3, format="%02.0f")
        self.ss.set(start_tw.second)
        self.ss.pack(side=tk.LEFT, padx=0)

        ttk.Label(start_frame, text="秒", anchor=tk.W).pack(side=tk.LEFT)

        # === 結束時間 ===
        end_frame = ttk.LabelFrame(time_frame, text="結束時間", padding=DATETIME_END_LABELFRAME_PADDING)
        end_frame.pack(side=tk.LEFT, padx=(DATETIME_END_LABELFRAME_PADX, 0), pady=DATETIME_END_LABELFRAME_PADY, anchor=tk.W)

        # 結束時間控件
        self.ey = ttk.Spinbox(end_frame, from_=2020, to=2030, width=5)
        self.ey.set(now_tw.year)
        self.ey.pack(side=tk.LEFT, padx=(0, 2), pady=0)

        ttk.Label(end_frame, text="年", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.eM = ttk.Spinbox(end_frame, from_=1, to=12, width=3, format="%02.0f")
        self.eM.set(now_tw.month)
        self.eM.pack(side=tk.LEFT, padx=0)

        ttk.Label(end_frame, text="月", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.ed = ttk.Spinbox(end_frame, from_=1, to=31, width=3, format="%02.0f")
        self.ed.set(now_tw.day)
        self.ed.pack(side=tk.LEFT, padx=0)

        ttk.Label(end_frame, text="日", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.eh = ttk.Spinbox(end_frame, from_=0, to=23, width=3, format="%02.0f")
        self.eh.set(now_tw.hour)
        self.eh.pack(side=tk.LEFT, padx=0)

        ttk.Label(end_frame, text="時", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.eu = ttk.Spinbox(end_frame, from_=0, to=59, width=3, format="%02.0f")
        self.eu.set(now_tw.minute)
        self.eu.pack(side=tk.LEFT, padx=0)

        ttk.Label(end_frame, text="分", anchor=tk.W).pack(side=tk.LEFT, padx=(0, 3))
        self.es = ttk.Spinbox(end_frame, from_=0, to=59, width=3, format="%02.0f")
        self.es.set(now_tw.second)
        self.es.pack(side=tk.LEFT, padx=0)

        ttk.Label(end_frame, text="秒", anchor=tk.W).pack(side=tk.LEFT)

        # === 資產分類和交易對 ===
        asset_frame = ttk.Frame(parent_frame)
        asset_frame.pack(anchor=tk.W, pady=ASSET_FRAME_PADY, padx=ASSET_FRAME_PADX, fill=tk.X)

        ttk.Label(asset_frame, text="資產分類:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_entry = ttk.Entry(asset_frame, width=20)
        self.category_entry.insert(0, TradingConfig.DEFAULT_CATEGORY)
        self.category_entry.pack(side=tk.LEFT, padx=(0, 15))

        ttk.Label(asset_frame, text="交易對:").pack(side=tk.LEFT, padx=(0, 5))
        self.symbol_entry = ttk.Entry(asset_frame, width=20)
        self.symbol_entry.insert(0, TradingConfig.DEFAULT_SYMBOL)
        self.symbol_entry.pack(side=tk.LEFT)
        
    def set_current_time(self):
        """設定為當前時間"""
        try:
            # 除錯提示
            self.gui.emit("[DEBUG] 🔘 '現在' 按鈕被點擊")
            print("[DEBUG] set_current_time 方法被調用")
            
            # 檢查所有Spinbox是否存在
            spinboxes = ['sy', 'sM', 'sd', 'sh', 'su', 'ss']
            for sb in spinboxes:
                if not hasattr(self, sb):
                    error_msg = f"[ERROR] Spinbox {sb} 不存在"
                    self.gui.emit(error_msg)
                    print(error_msg)
                    return
            
            now = datetime.now()
            
            # 設定時間值
            self.sy.set(now.year)
            self.sM.set(now.month)
            self.sd.set(now.day)
            self.sh.set(now.hour)
            self.su.set(now.minute)
            self.ss.set(0)  # 秒固定為0
            
            success_msg = f"[DATETIME] 🕐 已設定為當前時間: {now.strftime('%Y-%m-%d %H:%M:%S')}"
            self.gui.emit(success_msg)
            print("[DEBUG] set_current_time 執行成功")
            
        except Exception as e:
            error_msg = f"[ERROR] 設定當前時間失敗: {str(e)}"
            self.gui.emit(error_msg)
            print(f"[DEBUG] set_current_time 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def set_yesterday_to_today(self):
        """設定昨天到今天的時間範圍"""
        try:
            # 除錯提示
            self.gui.emit("[DEBUG] 🔘 '昨天到今天' 按鈕被點擊")
            print("[DEBUG] set_yesterday_to_today 方法被調用")
            
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            
            # 設定起始時間為昨天
            self.sy.set(yesterday.year)
            self.sM.set(yesterday.month)
            self.sd.set(yesterday.day)
            self.sh.set(0)
            self.su.set(0)
            self.ss.set(0)
            
            # 設定結束時間為今天
            self.ey.set(now.year)
            self.eM.set(now.month)
            self.ed.set(now.day)
            self.eh.set(now.hour)
            self.eu.set(now.minute)
            self.es.set(now.second)
            
            self.gui.emit("[DATETIME] 📅 已設定為昨天到今天")
            print("[DEBUG] set_yesterday_to_today 執行成功")
            
        except Exception as e:
            error_msg = f"[ERROR] 設定昨天到今天失敗: {str(e)}"
            self.gui.emit(error_msg)
            print(f"[DEBUG] set_yesterday_to_today 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def set_last_week(self):
        """設定最近一週的時間範圍"""
        try:
            now = datetime.now()
            last_week = now - timedelta(days=7)
            
            # 設定起始時間為一週前
            self.sy.set(last_week.year)
            self.sM.set(last_week.month)
            self.sd.set(last_week.day)
            self.sh.set(0)
            self.su.set(0)
            self.ss.set(0)
            
            # 設定結束時間為現在
            self.ey.set(now.year)
            self.eM.set(now.month)
            self.ed.set(now.day)
            self.eh.set(now.hour)
            self.eu.set(now.minute)
            self.es.set(now.second)
            
            self.gui.emit("[DATETIME] 📊 已設定為最近一週")
            print("[DEBUG] set_last_week 執行成功")
            
        except Exception as e:
            error_msg = f"[ERROR] 設定最近一週失敗: {str(e)}"
            self.gui.emit(error_msg)
            print(f"[DEBUG] set_last_week 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def add_one_hour(self):
        """增加一小時"""
        try:
            current = datetime(
                int(self.sy.get()), int(self.sM.get()), int(self.sd.get()),
                int(self.sh.get()), int(self.su.get()), int(self.ss.get())
            )
            new_time = current + timedelta(hours=1)
            self.sy.delete(0, tk.END)
            self.sy.insert(0, new_time.year)
            self.sM.delete(0, tk.END)
            self.sM.insert(0, f"{new_time.month:02d}")
            self.sd.delete(0, tk.END)
            self.sd.insert(0, f"{new_time.day:02d}")
            self.sh.delete(0, tk.END)
            self.sh.insert(0, f"{new_time.hour:02d}")
            self.su.delete(0, tk.END)
            self.su.insert(0, f"{new_time.minute:02d}")
            self.ss.delete(0, tk.END)
            self.ss.insert(0, f"{new_time.second:02d}")
            self.gui.emit(f"[DATETIME] ⏰ 已增加一小時: {new_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            self.gui.emit(f"[DATETIME] ❌ 時間調整失敗: {e}")
    
    def add_one_day(self):
        """增加一天"""
        try:
            current = datetime(
                int(self.sy.get()), int(self.sM.get()), int(self.sd.get()),
                int(self.sh.get()), int(self.su.get()), int(self.ss.get())
            )
            new_time = current + timedelta(days=1)
            self.sy.delete(0, tk.END)
            self.sy.insert(0, new_time.year)
            self.sM.delete(0, tk.END)
            self.sM.insert(0, f"{new_time.month:02d}")
            self.sd.delete(0, tk.END)
            self.sd.insert(0, f"{new_time.day:02d}")
            self.sh.delete(0, tk.END)
            self.sh.insert(0, f"{new_time.hour:02d}")
            self.su.delete(0, tk.END)
            self.su.insert(0, f"{new_time.minute:02d}")
            self.ss.delete(0, tk.END)
            self.ss.insert(0, f"{new_time.second:02d}")
            self.gui.emit(f"[DATETIME] 📅 已增加一天: {new_time.strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            self.gui.emit(f"[DATETIME] ❌ 日期調整失敗: {e}")
