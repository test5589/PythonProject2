"""
advanced_panel.py - 進階功能面板
負責進階功能的主要UI和數據庫操作
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import shutil
from modules.utils.database import DB_PATH
from config.trading_config import TradingConfig

class AdvancedPanel:
    """進階功能面板管理器"""
    
    def __init__(self, root, main_gui):
        self.main_gui = main_gui
        self.query_win = None
        
        # 創建進階功能面板
        self.panel = ttk.LabelFrame(root, text="進階功能")
        self.panel.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        # 建立缺失的輸入欄位
        self.main_gui.category_entry = tk.StringVar(value="crypto")
        self.main_gui.symbol_entry = tk.StringVar(value="BTCUSDT")
        
        # 創建主要按鈕
        self._create_main_buttons()
        
        # 創建貨幣對快捷選擇
        self._create_symbol_selector()
        
    def _create_main_buttons(self):
        """創建主要功能按鈕"""
        ttk.Button(self.panel, text="📂 開啟資料庫", command=self.open_database).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.panel, text="🔍 查詢/修補", command=self.open_query_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.panel, text="📈 分析資料", command=self.open_analyze_window).pack(side=tk.LEFT, padx=5)
        
    def _create_symbol_selector(self):
        """創建貨幣對快捷選擇器"""
        ttk.Label(self.panel, text="快捷選取:").pack(side=tk.LEFT, padx=(15, 5))

        self.symbol_combobox = ttk.Combobox(
            self.panel,
            values=TradingConfig.SUPPORTED_SYMBOLS,
            width=12
        )
        self.symbol_combobox.pack(side=tk.LEFT, padx=5)
        self.symbol_combobox.set("選擇...")

        # 綁定選單變動事件
        self.symbol_combobox.bind("<<ComboboxSelected>>", self._on_symbol_select)
        
    def _on_symbol_select(self, event):
        """當下拉式選單被選中時呼叫"""
        try:
            selected_symbol = self.symbol_combobox.get()
            print(f"[DEBUG] 選擇貨幣對: {selected_symbol}")

            if selected_symbol and selected_symbol != "選擇..." and self.main_gui:
                try:
                    # 更新 main_gui 上的 symbol_entry
                    if hasattr(self.main_gui, 'symbol_entry'):
                        if hasattr(self.main_gui.symbol_entry, 'set'):
                            # StringVar類型
                            self.main_gui.symbol_entry.set(selected_symbol)
                            print(f"[DEBUG] 成功更新 symbol_entry (StringVar) 為: {selected_symbol}")
                        elif hasattr(self.main_gui.symbol_entry, 'delete'):
                            # Entry widget類型
                            self.main_gui.symbol_entry.delete(0, tk.END)
                            self.main_gui.symbol_entry.insert(0, selected_symbol)
                            print(f"[DEBUG] 成功更新 symbol_entry (Entry) 為: {selected_symbol}")
                        else:
                            print(f"[DEBUG] symbol_entry 類型未知: {type(self.main_gui.symbol_entry)}")
                    else:
                        print("[DEBUG] main_gui 沒有 symbol_entry 屬性")
                        
                except Exception as e:
                    print(f"[DEBUG] 更新 symbol_entry 失敗: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("錯誤", f"無法更新主介面: {e}")
            else:
                print(f"[DEBUG] 跳過更新 - selected_symbol={selected_symbol}, main_gui存在={self.main_gui is not None}")
                
        except Exception as e:
            print(f"[DEBUG] _on_symbol_select 整體錯誤: {e}")
            import traceback
            traceback.print_exc()

    def open_database(self):
        """開啟資料庫（使用 DB Browser for SQLite）"""
        db_path = DB_PATH
        
        if not os.path.exists(db_path):
            messagebox.showerror("錯誤", f"資料庫不存在：{db_path}")
            return
        
        # 嘗試尋找 DB Browser for SQLite
        db_browser_paths = [
            r"C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe",
            r"C:\Program Files (x86)\DB Browser for SQLite\DB Browser for SQLite.exe",
            shutil.which("DB Browser for SQLite"),
            shutil.which("sqlitebrowser"),
        ]
        
        db_browser_exe = None
        for path in db_browser_paths:
            if path and os.path.exists(path):
                db_browser_exe = path
                break
        
        if db_browser_exe:
            try:
                subprocess.Popen([db_browser_exe, db_path])
                messagebox.showinfo("成功", f"正在使用 DB Browser 開啟資料庫：\n{db_path}")
            except Exception as e:
                messagebox.showerror("錯誤", f"無法啟動 DB Browser：{e}")
        else:
            # 如果找不到 DB Browser，提供下載連結
            result = messagebox.askyesno(
                "未找到 DB Browser",
                "未找到 DB Browser for SQLite。\n\n"
                "是否要在瀏覽器中開啟下載頁面？\n\n"
                "下載網址：https://sqlitebrowser.org/dl/",
                icon="question"
            )
            if result:
                import webbrowser
                webbrowser.open("https://sqlitebrowser.org/dl/")
            
            # 同時顯示資料庫路徑
            messagebox.showinfo("資料庫路徑", f"資料庫位置：\n{db_path}\n\n請安裝 DB Browser for SQLite 後重試。")
            
    def open_query_window(self):
        """開啟查詢/修補視窗"""
        from .query_panel import QueryPanel
        
        # 若視窗已存在則只聚焦
        if self.query_win and self.query_win.winfo_exists():
            self.query_win.deiconify()
            self.query_win.lift()
            self.query_win.focus_force()
            return

        # 創建查詢面板
        self.query_panel = QueryPanel(self.main_gui)
        self.query_win = self.query_panel.create_window()
        
    def open_analyze_window(self):
        """開啟分析資料視窗"""
        from .maintenance_panel import MaintenancePanel
        
        # 創建維護面板並開啟分析視窗
        maintenance_panel = MaintenancePanel(self.main_gui)
        maintenance_panel.open_analyze_window()
