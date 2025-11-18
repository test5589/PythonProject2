"""
query_panel.py - 查詢和修補功能面板
負責數據查詢和自動修補功能
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from modules.utils.auto_heal_backfill import start_smart_auto_heal, stop_auto_heal
from modules.utils.data.aggregation_utils import (
    scan_missing_intervals,
    start_batch_aggregate_with_task,
    stop_batch_aggregate,
    AGG_INTERVALS,
    _interval_name
)

class QueryPanel:
    """查詢和修補功能面板"""
    
    def __init__(self, main_gui):
        self.main_gui = main_gui
        
    def create_window(self):
        """創建查詢/修補視窗"""
        # 建立子視窗
        query_win = tk.Toplevel(self.main_gui.root)
        query_win.title("查詢/修補")
        query_win.transient(self.main_gui.root)
        # 移除模態鎖定，允許窗口正常關閉
        # query_win.grab_set()
        
        # 置中顯示
        query_win.update_idletasks()
        x = (query_win.winfo_screenwidth() // 2) - (query_win.winfo_width() // 2)
        y = (query_win.winfo_screenheight() // 2) - (query_win.winfo_height() // 2)
        query_win.geometry(f"+{x}+{y}")

        def on_close():
            """正確處理窗口關閉"""
            # 清除主窗口的引用
            if hasattr(self.main_gui, 'query_win'):
                self.main_gui.query_win = None
            # 銷毀窗口
            query_win.destroy()
                
        query_win.protocol("WM_DELETE_WINDOW", on_close)

        # 創建修補功能區域
        self._create_heal_section(query_win)
        
        # 創建聚合檢查區域
        self._create_aggregation_section(query_win)
        
        return query_win
        
    def _create_heal_section(self, parent):
        """創建自動修補區域"""
        heal_frame = ttk.LabelFrame(parent, text="自動修補 15 分鐘（1秒資料）")
        heal_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(heal_frame, text="交易對:").pack(side=tk.LEFT, padx=(8,4))
        
        # 交易對選擇
        sym_var = tk.StringVar(value=(self.main_gui.symbol_entry.get().strip() or "BTCUSDT"))
        sym_combo = ttk.Combobox(heal_frame, textvariable=sym_var, 
                                values=["BTCUSDT", "ETHUSDT"], width=12, state="readonly")
        sym_combo.pack(side=tk.LEFT, padx=4)
        if not sym_var.get():
            sym_combo.set("BTCUSDT")
            
        def run_auto_heal():
            sym = sym_var.get().strip()
            if not sym:
                messagebox.showerror("錯誤", "請輸入交易對，如 BTCUSDT")
                return
            cat = self.main_gui.category_entry.get().strip() or "crypto"
            start_smart_auto_heal(cat, sym, emit=self.main_gui.emit)
            self.main_gui.log(f"🧩 智能修補啟動：{sym}")
            
        def stop_heal():
            sym = sym_var.get().strip()
            if not sym:
                messagebox.showerror("錯誤", "請輸入交易對，如 BTCUSDT")
                return
            stop_auto_heal(sym, emit=self.main_gui.emit)
            self.main_gui.log(f"⏹ 已請求停止修補：{sym}")
            
        ttk.Button(heal_frame, text="開始智能修補", command=run_auto_heal).pack(side=tk.LEFT, padx=6)
        ttk.Button(heal_frame, text="停止修補", command=stop_heal).pack(side=tk.LEFT, padx=6)
        
    def _create_aggregation_section(self, parent):
        """創建聚合檢查與修補區域"""
        agg_frame = ttk.LabelFrame(parent, text="聚合資料檢查與修補")
        agg_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(agg_frame, text="交易對:").pack(side=tk.LEFT, padx=(8,4))
        
        # 交易對選擇
        agg_sym_var = tk.StringVar(value=(self.main_gui.symbol_entry.get().strip() or "BTCUSDT"))
        agg_sym_combo = ttk.Combobox(agg_frame, textvariable=agg_sym_var, 
                                    values=["BTCUSDT", "ETHUSDT"], width=12, state="readonly")
        agg_sym_combo.pack(side=tk.LEFT, padx=4)
        if not agg_sym_var.get():
            agg_sym_combo.set("BTCUSDT")

        def run_agg_check():
            sym = agg_sym_var.get().strip()
            if not sym:
                messagebox.showerror("錯誤", "請選擇交易對")
                return
            cat = self.main_gui.category_entry.get().strip() or "crypto"
            self.main_gui.log(f"🔍 開始檢查聚合資料缺口：{sym}")
            
            def worker():
                try:
                    results = scan_missing_intervals(cat, sym, intervals=AGG_INTERVALS, 
                                                   lookback_days=7, emit=self.main_gui.emit)
                    # 彙總報告
                    report_lines = [f"📊 聚合缺口檢查報告（{sym}）"]
                    for sec in AGG_INTERVALS:
                        gap, exp, exist = results.get(sec, (0,0,0))
                        if gap > 0:
                            report_lines.append(f"  - {_interval_name(sec)}: 缺口 {gap} 區塊（預期 {exp}，實際 {exist}）")
                    if len(report_lines) == 1:
                        report_lines.append("  ✅ 所有級別皆完整")
                    self.main_gui.log("\n".join(report_lines))
                except Exception as e:
                    self.main_gui.log(f"❌ 聚合檢查錯誤：{e}")
                    
            threading.Thread(target=worker, daemon=True).start()

        def run_agg_repair():
            sym = agg_sym_var.get().strip()
            if not sym:
                messagebox.showerror("錯誤", "請選擇交易對")
                return
            cat = self.main_gui.category_entry.get().strip() or "crypto"
            
            # 選擇單位類型
            self._create_repair_dialog(parent, sym, cat)

        ttk.Button(agg_frame, text="聚合資料檢查", command=run_agg_check).pack(side=tk.LEFT, padx=6)
        ttk.Button(agg_frame, text="聚合資料修補", command=run_agg_repair).pack(side=tk.LEFT, padx=6)
        
    # 用於追踪活動窗口的類變量
    _active_repair_window = None
    
    def _create_repair_dialog(self, parent, sym, cat):
        """創建修補對話框（防止重複開啟）"""
        # 檢查是否已有修補窗口
        if QueryPanel._active_repair_window is not None:
            try:
                # 嘗試獲取窗口狀態，如果窗口存在則提示並退出
                if QueryPanel._active_repair_window.winfo_exists():
                    QueryPanel._active_repair_window.lift()  # 將窗口提到前面
                    self.main_gui.log("⚠️ 修補窗口已存在，請先關閉現有窗口")
                    return
            except Exception:
                pass  # 如果窗口已不存在，繼續創建新窗口
        
        # 創建新窗口
        repair_win = tk.Toplevel(parent)
        repair_win.title("聚合資料修補")
        repair_win.transient(parent)
        QueryPanel._active_repair_window = repair_win
        
        # 設置窗口關閉處理
        def on_window_close():
            QueryPanel._active_repair_window = None
            repair_win.destroy()
        
        repair_win.protocol("WM_DELETE_WINDOW", on_window_close)
        
        ttk.Label(repair_win, text="選擇聚合單位：").pack(pady=5)
        
        unit_var = tk.StringVar(value="秒")
        unit_frame = ttk.Frame(repair_win)
        unit_frame.pack(pady=5)
        
        for u in ["秒", "分鐘", "小時", "天"]:
            ttk.Radiobutton(unit_frame, text=u, variable=unit_var, value=u).pack(side=tk.LEFT, padx=5)
        
        # 創建狀態標籤顯示當前操作
        status_label = ttk.Label(repair_win, text="準備就緒", foreground="blue")
        status_label.pack(pady=(5, 10))
            
        btn_frame = ttk.Frame(repair_win)
        btn_frame.pack(pady=10)
        
        # 任務狀態變量
        task_running = False
        
        # 創建按鈕變量以便控制狀態
        start_btn = ttk.Button(btn_frame, text="開始修補")
        stop_btn = ttk.Button(btn_frame, text="停止修補", state='disabled')
        
        def do_repair():
            nonlocal task_running
            if task_running:
                self.main_gui.log("⚠️ 修補任務已在運行中")
                return
                
            task_running = True
            unit = unit_var.get()
            # 禁用開始按鈕，啟用停止按鈕
            start_btn.config(state='disabled')
            stop_btn.config(state='normal')
            status_label.config(text=f"正在修補 {unit} 級別聚合數據...", foreground="green")
            
            # 根據單位篩選 intervals
            mapping = {
                "秒": [2,5,10,15,30], 
                "分鐘": [60,120,300,600,900,1800], 
                "小時": [3600,7200,14400,28800,43200], 
                "天": [86400,259200,604800]
            }
            intervals = mapping.get(unit, [])
            self.main_gui.log(f"🔧 開始聚合修補（{sym}，單位：{unit}）")
            self.main_gui.log(f"💡 提示：可隨時點擊「停止修補」按鈕停止操作")
            
            # 啟動修補任務
            start_batch_aggregate_with_task(cat, sym, intervals=intervals, 
                                          lookback_days=7, emit=self.main_gui.emit)
            
            # 完成後恢復按鈕狀態
            def check_task_status():
                nonlocal task_running
                # TODO: 實際上應該檢查任務是否完成
                # 這裡簡化處理，等待幾秒後假定已完成
                task_running = False
                start_btn.config(state='normal')
                stop_btn.config(state='disabled')
                status_label.config(text="修補完成或已停止", foreground="blue")
            
            # 延遲恢復（給時間執行停止操作）- 實際應該通過回調或監控完成狀態
            repair_win.after(5000, check_task_status)
            
        def do_stop():
            nonlocal task_running
            stop_batch_aggregate(cat, sym, emit=self.main_gui.emit)
            self.main_gui.log(f"⏹ 已請求停止聚合修補：{sym}")
            
            # 更新界面狀態
            task_running = False
            start_btn.config(state='normal')
            stop_btn.config(state='disabled')
            status_label.config(text="已停止修補", foreground="red")
            
        start_btn.config(command=do_repair)
        stop_btn.config(command=do_stop)
        
        start_btn.pack(side=tk.LEFT, padx=5)
        stop_btn.pack(side=tk.LEFT, padx=5)
