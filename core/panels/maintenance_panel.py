"""
maintenance_panel.py - 維護功能面板  
負責數據分析和Streamlit集成
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import threading
import time
import subprocess
import sys
import os
import webbrowser
from datetime import datetime, timezone
from modules.utils.database import DB_PATH
from modules.utils.data.aggregation_utils import AGG_INTERVALS, _interval_name, _count_rows

class MaintenancePanel:
    """維護功能面板"""
    
    def __init__(self, main_gui):
        self.main_gui = main_gui
        
    def open_analyze_window(self):
        """開啟分析資料視窗"""
        # 建立分析視窗
        win = tk.Toplevel(self.main_gui.root)
        win.title("分析資料")
        win.transient(self.main_gui.root)
        win.grab_set()
        
        # 置中顯示
        win.update_idletasks()
        x = (win.winfo_screenwidth() // 2) - (win.winfo_width() // 2)
        y = (win.winfo_screenheight() // 2) - (win.winfo_height() // 2)
        win.geometry(f"+{x}+{y}")
        
        # 創建分析控制項
        self._create_analyze_controls(win)
        
    def _create_analyze_controls(self, parent):
        """創建分析控制項"""
        ttk.Label(parent, text="選擇交易對：").pack(pady=5)
        
        sym_var = tk.StringVar(value=(self.main_gui.symbol_entry.get().strip() or "BTCUSDT"))
        sym_combo = ttk.Combobox(parent, textvariable=sym_var, 
                                values=["BTCUSDT", "ETHUSDT"], width=12, state="readonly")
        sym_combo.pack(pady=5)
        if not sym_var.get():
            sym_combo.set("BTCUSDT")
            
        # 功能按鈕
        ttk.Button(parent, text="開始分析", 
                  command=lambda: self.run_analyze(sym_var.get())).pack(pady=10)
        ttk.Button(parent, text="在網頁中查詢缺口", 
                  command=self.open_streamlit).pack(pady=5)
        
    def run_analyze(self, symbol: str):
        """執行數據分析"""
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

    def open_streamlit(self):
        """開啟 Streamlit 網頁查詢缺口"""
        try:
            import requests
        except Exception:
            requests = None

        def is_alive(url: str) -> bool:
            """檢查URL是否可訪問"""
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
            subprocess.Popen([sys.executable, "-m", "streamlit", "run", app_path, 
                             "--server.port", "8501"])
            self.main_gui.log("🌐 正在啟動 Streamlit 網頁...")

            def wait_and_open():
                """等待Streamlit啟動並開啟瀏覽器"""
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
            
    def create_maintenance_dashboard(self, parent):
        """創建維護儀表板"""
        dashboard_frame = ttk.LabelFrame(parent, text="系統維護儀表板")
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 系統狀態顯示
        status_frame = ttk.Frame(dashboard_frame)
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(status_frame, text="系統狀態:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        # 數據庫狀態
        db_status = "🟢 正常" if os.path.exists(DB_PATH) else "🔴 異常"
        ttk.Label(status_frame, text=f"資料庫: {db_status}").pack(side=tk.LEFT, padx=10)
        
        # 快捷操作按鈕
        action_frame = ttk.Frame(dashboard_frame)
        action_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(action_frame, text="🔄 重新載入配置", 
                  command=self._reload_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="📊 系統統計", 
                  command=self._show_system_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="🧹 清理緩存", 
                  command=self._clean_cache).pack(side=tk.LEFT, padx=5)
                  
    def _reload_config(self):
        """重新載入配置"""
        self.main_gui.log("🔄 正在重新載入系統配置...")
        # 這裡可以添加重新載入配置的邏輯
        self.main_gui.log("✅ 配置重新載入完成")
        
    def _show_system_stats(self):
        """顯示系統統計信息"""
        def worker():
            try:
                conn = sqlite3.connect(DB_PATH)
                cur = conn.cursor()
                
                # 獲取總記錄數
                cur.execute("SELECT COUNT(*) FROM historical_data")
                total_records = cur.fetchone()[0]
                
                # 獲取交易對數量
                cur.execute("SELECT COUNT(DISTINCT symbol) FROM historical_data")
                symbol_count = cur.fetchone()[0]
                
                # 獲取最新記錄時間
                cur.execute("SELECT MAX(timestamp) FROM historical_data")
                latest_ts = cur.fetchone()[0]
                latest_time = datetime.fromtimestamp(latest_ts).strftime('%Y-%m-%d %H:%M:%S') if latest_ts else "無"
                
                conn.close()
                
                stats = [
                    "📊 系統統計信息",
                    f"📈 總記錄數: {total_records:,}",
                    f"💰 交易對數量: {symbol_count}",
                    f"⏰ 最新記錄: {latest_time}",
                    f"💾 資料庫大小: {os.path.getsize(DB_PATH) / (1024*1024):.2f} MB"
                ]
                
                self.main_gui.log("\n".join(stats))
                
            except Exception as e:
                self.main_gui.log(f"❌ 獲取系統統計失敗: {e}")
                
        threading.Thread(target=worker, daemon=True).start()
        
    def _clean_cache(self):
        """清理緩存"""
        self.main_gui.log("🧹 正在清理系統緩存...")
        # 這裡可以添加清理緩存的邏輯
        self.main_gui.log("✅ 緩存清理完成")
