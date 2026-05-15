"""此為子模組介面GUI 分層設計"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sqlite3, os, subprocess, shutil
import threading
import time
from datetime import datetime, timezone, timedelta
from modules.utils.database import DB_PATH
from modules.utils.auto_heal_backfill import (
    start_smart_auto_heal,
    stop_auto_heal,
)
from modules.utils.aggregation_utils import (
    scan_missing_intervals,
    batch_aggregate_missing,
    start_batch_aggregate_with_task,
    stop_batch_aggregate,
    AGG_INTERVALS,
    _interval_name,
    _fmt_range
)
from config.trading_config import TradingConfig

class FeaturePanel:
    def __init__(self, root, main_gui):
        # 保存 main_gui 的實例 (instance)，這樣我們才能存取它的元件
        self.main_gui = main_gui
        self.query_win = None
        panel = ttk.LabelFrame(root, text="進階功能")
        panel.pack(anchor=tk.W, padx=10, pady=5)  # 靠左對齊
        
        # 建立缺失的輸入欄位
        self.main_gui.category_entry = tk.StringVar(value="crypto")
        self.main_gui.symbol_entry = tk.StringVar(value="BTCUSDT")

        ttk.Button(panel, text="📂 開啟資料庫", command=self.open_db).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel, text="🔍 查詢/修補", command=self.query_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(panel, text="📈 分析資料", command=self.analyze_data).pack(side=tk.LEFT, padx=5)

        # --- 新增下拉式選單 ---
        ttk.Label(panel, text="快捷選取:").pack(side=tk.LEFT, padx=(15, 5))

        self.symbol_combobox = ttk.Combobox(
            panel,
            values=TradingConfig.SUPPORTED_SYMBOLS,
            width=12
        )
        self.symbol_combobox.pack(side=tk.LEFT, padx=5)
        self.symbol_combobox.set("選擇...")  # 預設文字

        # 綁定選單變動事件
        self.symbol_combobox.bind("<<ComboboxSelected>>", self._on_symbol_select)
        # --- 新增結束 ---
    def _on_symbol_select(self, event):
        """
        當下拉式選單被選中時呼叫此函式
        """
        try:
            # 1. 獲取選中的值
            selected_symbol = self.symbol_combobox.get()
            
            print(f"[DEBUG] 選擇貨幣對: {selected_symbol}")

            if selected_symbol and selected_symbol != "選擇..." and self.main_gui:
                try:
                    # 2. 更新 main_gui 上的 symbol_entry (交易對輸入框)
                    if hasattr(self.main_gui, 'symbol_entry'):
                        # 檢查是否為StringVar或Entry widget
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

    def open_db(self):
        """開啟資料庫（使用 DB Browser for SQLite）"""
        # 使用默認資料庫路徑
        db_path = DB_PATH
        
        if not os.path.exists(db_path):
            messagebox.showerror("錯誤", f"資料庫不存在：{db_path}")
            return
        
        # 嘗試尋找 DB Browser for SQLite
        db_browser_paths = [
            r"C:\Program Files\DB Browser for SQLite\DB Browser for SQLite.exe",
            r"C:\Program Files (x86)\DB Browser for SQLite\DB Browser for SQLite.exe",
            shutil.which("DB Browser for SQLite"),  # 檢查 PATH 環境變數
            shutil.which("sqlitebrowser"),  # Linux/Mac 名稱
        ]
        
        db_browser_exe = None
        for path in db_browser_paths:
            if path and os.path.exists(path):
                db_browser_exe = path
                break
        
        if db_browser_exe:
            try:
                # 使用 DB Browser 開啟資料庫
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

    def query_data(self):
        # 若視窗已存在則只聚焦，不重複開啟
        if self.query_win and self.query_win.winfo_exists():
            self.query_win.deiconify(); self.query_win.lift(); self.query_win.focus_force()
            return

        # 建立子視窗，設定為 transient（跟隨主視窗）
        self.query_win = tk.Toplevel(self.main_gui.root)
        self.query_win.title("查詢/修補")
        self.query_win.transient(self.main_gui.root)  # 跟隨主視窗
        self.query_win.grab_set()  # 模態視窗
        
        # 置中顯示子視窗
        self.query_win.update_idletasks()
        x = (self.query_win.winfo_screenwidth() // 2) - (self.query_win.winfo_width() // 2)
        y = (self.query_win.winfo_screenheight() // 2) - (self.query_win.winfo_height() // 2)
        self.query_win.geometry(f"+{x}+{y}")

        def on_close():
            try:
                self.query_win.destroy()
            finally:
                self.query_win = None
        self.query_win.protocol("WM_DELETE_WINDOW", on_close)

        # 僅保留修補相關操作（不需要起訖時間）
        heal_frame = ttk.LabelFrame(self.query_win, text="自動修補 15 分鐘（1秒資料）")
        heal_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(heal_frame, text="交易對:").pack(side=tk.LEFT, padx=(8,4))
        # 下拉選單（預設 BTCUSDT）
        sym_var = tk.StringVar(value=(self.main_gui.symbol_entry.get().strip() or "BTCUSDT"))
        sym_combo = ttk.Combobox(heal_frame, textvariable=sym_var, values=["BTCUSDT", "ETHUSDT"], width=12, state="readonly")
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

        # --- 新增聚合檢查與修補區塊 ---
        agg_frame = ttk.LabelFrame(self.query_win, text="聚合資料檢查與修補")
        agg_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(agg_frame, text="交易對:").pack(side=tk.LEFT, padx=(8,4))
        agg_sym_var = tk.StringVar(value=(self.main_gui.symbol_entry.get().strip() or "BTCUSDT"))
        agg_sym_combo = ttk.Combobox(agg_frame, textvariable=agg_sym_var, values=["BTCUSDT", "ETHUSDT"], width=12, state="readonly")
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
                    results = scan_missing_intervals(cat, sym, intervals=AGG_INTERVALS, lookback_days=7, emit=self.main_gui.emit)
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
            # 選擇單位類型（秒/分鐘/小時/天）
            repair_win = tk.Toplevel(self.query_win)
            repair_win.title("聚合資料修補")
            ttk.Label(repair_win, text="選擇聚合單位：").pack(pady=5)
            unit_var = tk.StringVar(value="秒")
            unit_frame = ttk.Frame(repair_win)
            unit_frame.pack(pady=5)
            for u in ["秒", "分鐘", "小時", "天"]:
                ttk.Radiobutton(unit_frame, text=u, variable=unit_var, value=u).pack(side=tk.LEFT, padx=5)
            btn_frame = ttk.Frame(repair_win)
            btn_frame.pack(pady=10)
            ttk.Button(btn_frame, text="開始修補", command=lambda: _do_repair(unit_var.get(), sym, cat, repair_win)).pack(side=tk.LEFT, padx=5)
            ttk.Button(btn_frame, text="停止修補", command=lambda: _do_stop(sym, cat)).pack(side=tk.LEFT, padx=5)

        def _do_stop(sym: str, cat: str):
            stop_batch_aggregate(cat, sym, emit=self.main_gui.emit)
            self.main_gui.log(f"⏹ 已請求停止聚合修補：{sym}")

        def _do_repair(unit: str, sym: str, cat: str, win: tk.Toplevel):
            win.destroy()
            # 根據單位篩選 intervals
            mapping = {"秒": [2,5,10,15,30], "分鐘": [60,120,300,600,900,1800], "小時": [3600,7200,14400,28800,43200], "天": [86400,259200,604800]}
            intervals = mapping.get(unit, [])
            self.main_gui.log(f"🔧 開始聚合修補（{sym}，單位：{unit}）")
            start_batch_aggregate_with_task(cat, sym, intervals=intervals, lookback_days=7, emit=self.main_gui.emit)

        ttk.Button(agg_frame, text="聚合資料檢查", command=run_agg_check).pack(side=tk.LEFT, padx=6)
        ttk.Button(agg_frame, text="聚合資料修補", command=run_agg_repair).pack(side=tk.LEFT, padx=6)

    def analyze_data(self):
        """分析資料：顯示從最早到現在的缺口統計，並支援在網頁查詢"""
        # 建立分析視窗，設定為 transient（跟隨主視窗）
        win = tk.Toplevel(self.main_gui.root)
        win.title("分析資料")
        win.transient(self.main_gui.root)  # 跟隨主視窗
        win.grab_set()  # 模態視窗
        
        # 置中顯示子視窗
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        
        ttk.Label(win, text="選擇交易對：").pack(pady=5)
        sym_var = tk.StringVar(value=(self.main_gui.symbol_entry.get().strip() or "BTCUSDT"))
        sym_combo = ttk.Combobox(win, textvariable=sym_var, values=["BTCUSDT", "ETHUSDT"], width=12, state="readonly")
        sym_combo.pack(pady=5)
        if not sym_var.get():
            sym_combo.set("BTCUSDT")
        ttk.Button(win, text="開始分析", command=lambda: self._run_analyze(sym_var.get())).pack(pady=10)
        ttk.Button(win, text="在網頁中查詢缺口", command=self._open_streamlit).pack(pady=5)

    def _run_analyze(self, symbol: str):
        if not symbol:
            messagebox.showerror("錯誤", "請選擇交易對")
            return
        cat = self.main_gui.category_entry.get().strip() or "crypto"
        self.main_gui.log(f"🔍 開始分析 {symbol} 從最早到現在的缺口統計")
        def worker():
            try:
                # 找出最早資料時間
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                cur.execute(
                    "SELECT MIN(timestamp), MAX(timestamp) FROM historical_data WHERE category=? AND symbol=?",
                    (cat, symbol)
                )
                row = cur.fetchone()
                conn.close()
                if row and row[0] and row[1]:
                    earliest_ts, latest_ts = row[0], row[1]
                    now_ts = time.time()
                    # 擴展到現在
                    end_ts = max(latest_ts, now_ts)
                    self.main_gui.log(f"📅 資料範圍：{datetime.fromtimestamp(earliest_ts, tz=timezone.utc)} ~ {datetime.fromtimestamp(end_ts, tz=timezone.utc)}")
                    # 檢查各級別缺口
                    from modules.utils.aggregation_utils import AGG_INTERVALS, _interval_name, _count_rows
                    report = [f"📊 {symbol} 缺口統計（從最早到現在）"]
                    for sec in AGG_INTERVALS:
                        existing = _count_rows(cat, symbol, earliest_ts, end_ts, sec)
                        expected = int((end_ts - earliest_ts) // sec)
                        gap = max(0, expected - existing)
                        if gap > 0:
                            report.append(f"  - {_interval_name(sec)}: 缺口 {gap} 區塊（預期 {expected}，實際 {existing}）")
                    if len(report) == 1:
                        report.append("  ✅ 所有級別皆完整")
                    self.main_gui.log("\n".join(report))
                else:
                    self.main_gui.log("⚠️ 資料庫中無該交易對資料")
            except Exception as e:
                self.main_gui.log(f"❌ 分析錯誤：{e}")
        threading.Thread(target=worker, daemon=True).start()

    def _open_streamlit(self):
        """開啟 Streamlit 網頁查詢缺口（先檢查 8501，再決定是否啟動新實例）"""
        import subprocess
        import sys
        import os
        import webbrowser
        import time
        try:
            import requests
        except Exception:
            requests = None

        def is_alive(url: str) -> bool:
            try:
                if requests is None:
                    return False
                r = requests.get(url, timeout=1)
                return r.status_code < 500
            except Exception:
                return False

        app_url = "http://localhost:8501"
        health_urls = [f"{app_url}/healthz", app_url]

        # 若 8501 已運作，直接開啟瀏覽器
        if any(is_alive(u) for u in health_urls):
            webbrowser.open(app_url)
            self.main_gui.log("🌐 Streamlit 已在執行，已自動開啟瀏覽器：http://localhost:8501")
            return

        # 尚未運作則啟動
        try:
            app_path = os.path.join(os.getcwd(), "web", "streamlit_app.py")
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", app_path, "--server.port", "8501"])
            self.main_gui.log("🌐 正在啟動 Streamlit 網頁...")

            def wait_and_open():
                # 最多等待 10 秒檢查健康狀態
                for _ in range(20):
                    time.sleep(0.5)
                    if any(is_alive(u) for u in health_urls):
                        break
                webbrowser.open(app_url)
                self.main_gui.log("🌐 已自動開啟瀏覽器：http://localhost:8501")
            threading.Thread(target=wait_and_open, daemon=True).start()
        except Exception as e:
            self.main_gui.log(f"❌ 啟動 Streamlit 失敗：{e}")
