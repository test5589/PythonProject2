"""
button_controls.py - 按鈕控制項管理
負責主要功能按鈕的創建和管理
"""

import tkinter as tk
from tkinter import ttk
from .layout_config import (
    BUTTON_FRAME_PADY,
    BUTTON_FRAME_PADX,
    BUTTON_FRAME_HEIGHT,
)

class ButtonControls:
    """按鈕控制項管理器"""
    
    def __init__(self, gui):
        self.gui = gui
        
    def create_button_frame(self, root):
        """創建按鈕框架"""
        # === 按鈕區 ===
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(fill=tk.X, padx=BUTTON_FRAME_PADX, pady=BUTTON_FRAME_PADY, anchor="w")
        try:
            self.button_frame.configure(height=BUTTON_FRAME_HEIGHT)
            self.button_frame.pack_propagate(False)
        except Exception:
            pass
        return self.button_frame
        
    def create_main_buttons(self, button_frame):
        """創建主要功能按鈕"""
        # 主要按鈕
        self.fetch_btn = ttk.Button(button_frame, text="📥 批量抓取最新 1分鐘資料", command=self.gui.backfill.fetch_latest)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        
        self.ws_start_btn = ttk.Button(button_frame, text="🟢 啟動多貨幣對 1秒監控", command=self.gui.monitor.start_ws)
        self.ws_start_btn.pack(side=tk.LEFT, padx=5)
        
        self.ws_stop_btn = ttk.Button(button_frame, text="⛔ 停止多貨幣對 1秒監控", command=self.gui.monitor.stop_ws, state=tk.DISABLED)
        self.ws_stop_btn.pack(side=tk.LEFT, padx=5)
        
        return [self.fetch_btn, self.ws_start_btn, self.ws_stop_btn]
        
    def create_edit_buttons(self, button_frame):
        """創建編輯按鈕"""
        # 編輯按鈕
        self.edit_btn = ttk.Button(button_frame, text="🛠 編輯版面", command=self.toggle_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        
        self.edit_ok_btn = ttk.Button(button_frame, text="✅ 套用", command=self.confirm_edit)
        # 初始隱藏，不pack
        
        self.edit_cancel_btn = ttk.Button(button_frame, text="↩️ 取消", command=self.cancel_edit)
        # 初始隱藏，不pack
        
        return [self.edit_btn, self.edit_ok_btn, self.edit_cancel_btn]
        
    def setup_button_lists(self):
        """設置按鈕清單和映射"""
        # === 填充按鈕清單 ===
        self.gui._buttons = [
            self.fetch_btn, self.ws_start_btn, self.ws_stop_btn, 
            self.edit_btn, self.edit_ok_btn, self.edit_cancel_btn
        ]

        self.gui._button_keys = {
            self.fetch_btn: "fetch",
            self.ws_start_btn: "ws_start",
            self.ws_stop_btn: "ws_stop",
            self.edit_btn: "edit",
            self.edit_ok_btn: "edit_ok",
            self.edit_cancel_btn: "edit_cancel",
        }
        
    def setup_button_frame_bindings(self):
        """設置按鈕框架綁定"""
        try:
            self.edit_ok_btn.place_forget()
            self.edit_cancel_btn.place_forget()
        except Exception:
            pass

        # 綁定容器尺寸變動
        try:
            self.button_frame.bind("<Configure>", self.gui.utils._on_button_frame_resize)
        except Exception:
            pass
            
    def toggle_edit_mode(self):
        """切換編輯模式"""
        self.gui.utils.toggle_edit_mode()

    def confirm_edit(self):
        """確認編輯"""
        self.gui.utils.confirm_edit_layout()

    def cancel_edit(self):
        """取消編輯"""
        self.gui.utils.cancel_edit_layout()
        
    def add_quick_buttons_to_list(self, quick_buttons):
        """將快捷按鈕加入按鈕清單"""
        self.gui._buttons.extend(quick_buttons)
        
    def add_quick_buttons_to_keys(self, quick_button_keys):
        """將快捷按鈕鍵映射加入"""
        self.gui._button_keys.update(quick_button_keys)
