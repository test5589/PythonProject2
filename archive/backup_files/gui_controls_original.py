"""gui_controls.py - 控制區、按鈕與版面配置管理"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
import datetime
from datetime import datetime, timedelta, timezone
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.trading_config import TradingConfig



class GUIControls:
    """負責 GUI 上方的所有控制區塊、按鈕、版面編輯與 layout 儲存"""
    def __init__(self, gui):
        self.gui = gui
        root = gui.root

        # === 上方控制區 ===
        control_frame = ttk.Frame(root)
        control_frame.pack(pady=10)

        # ---- 起訖時間選擇 ----
        start_frame = ttk.Frame(control_frame)
        start_frame.pack(anchor="w", pady=2)
        end_frame = ttk.Frame(control_frame)
        end_frame.pack(anchor="w", pady=2)

        years = [str(y) for y in range(2020, 2036)]
        months = [f"{m:02d}" for m in range(1, 13)]
        days = [f"{d:02d}" for d in range(1, 32)]
        hours = [f"{h:02d}" for h in range(0, 24)]
        minutes = [f"{m:02d}" for m in range(0, 60)]
        seconds = [f"{s:02d}" for s in range(0, 60)]

        taipei = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz=taipei)
        start_tw = now_tw - timedelta(days=1)

        # === 起始時間 ===
        ttk.Label(start_frame, text="起始時間:").pack(side=tk.LEFT, padx=(10, 5))
        self.sy = ttk.Combobox(start_frame, values=years, width=6); self.sy.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="年").pack(side=tk.LEFT)
        self.sM = ttk.Combobox(start_frame, values=months, width=4); self.sM.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="月").pack(side=tk.LEFT)
        self.sd = ttk.Combobox(start_frame, values=days, width=4); self.sd.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="日").pack(side=tk.LEFT)
        self.sh = ttk.Combobox(start_frame, values=hours, width=4); self.sh.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="時").pack(side=tk.LEFT)
        self.su = ttk.Combobox(start_frame, values=minutes, width=4); self.su.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="分").pack(side=tk.LEFT)
        self.ss = ttk.Combobox(start_frame, values=seconds, width=4); self.ss.pack(side=tk.LEFT)
        ttk.Label(start_frame, text="秒").pack(side=tk.LEFT)

        # === 結束時間 ===
        ttk.Label(end_frame, text="結束時間:").pack(side=tk.LEFT, padx=(10, 5))
        self.ey = ttk.Combobox(end_frame, values=years, width=6); self.ey.pack(side=tk.LEFT)
        ttk.Label(end_frame, text="年").pack(side=tk.LEFT)
        self.eM = ttk.Combobox(end_frame, values=months, width=4); self.eM.pack(side=tk.LEFT)
        ttk.Label(end_frame, text="月").pack(side=tk.LEFT)
        self.ed = ttk.Combobox(end_frame, values=days, width=4); self.ed.pack(side=tk.LEFT)
        ttk.Label(end_frame, text="日").pack(side=tk.LEFT)
        self.eh = ttk.Combobox(end_frame, values=hours, width=4); self.eh.pack(side=tk.LEFT)
        ttk.Label(end_frame, text="時").pack(side=tk.LEFT)
        self.eu = ttk.Combobox(end_frame, values=minutes, width=4); self.eu.pack(side=tk.LEFT)
        ttk.Label(end_frame, text="分").pack(side=tk.LEFT)
        self.es = ttk.Combobox(end_frame, values=seconds, width=4); self.es.pack(side=tk.LEFT)
        ttk.Label(end_frame, text="秒").pack(side=tk.LEFT)

        # === 預設時間值 ===
        self.sy.set(str(start_tw.year)); self.sM.set(f"{start_tw.month:02d}"); self.sd.set(f"{start_tw.day:02d}")
        self.sh.set(f"{start_tw.hour:02d}"); self.su.set(f"{start_tw.minute:02d}"); self.ss.set(f"{start_tw.second:02d}")
        self.ey.set(str(now_tw.year)); self.eM.set(f"{now_tw.month:02d}"); self.ed.set(f"{now_tw.day:02d}")
        self.eh.set(f"{now_tw.hour:02d}"); self.eu.set(f"{now_tw.minute:02d}"); self.es.set(f"{now_tw.second:02d}")

        # === 其他控制項 ===
        ttk.Label(control_frame, text="資產分類:").pack(side=tk.LEFT, padx=(10, 5))
        self.category_entry = ttk.Entry(control_frame, width=20)
        self.category_entry.insert(0, TradingConfig.DEFAULT_CATEGORY)
        self.category_entry.pack(side=tk.LEFT, padx=5)

        ttk.Label(control_frame, text="交易對:").pack(side=tk.LEFT, padx=(10, 5))
        self.symbol_entry = ttk.Entry(control_frame, width=20)
        self.symbol_entry.insert(0, TradingConfig.DEFAULT_SYMBOL)
        self.symbol_entry.pack(side=tk.LEFT, padx=5)

        # 回補間隔（使用統一配置）
        ttk.Label(control_frame, text="回補間隔:").pack(side=tk.LEFT, padx=(10, 5))
        interval_options = list(TradingConfig.SUPPORTED_INTERVALS.keys())
        self.backfill_interval_combo = ttk.Combobox(control_frame,
                                                    values=interval_options,
                                                    width=8, state="readonly")
        self.backfill_interval_combo.set(TradingConfig.DEFAULT_INTERVAL)
        self.backfill_interval_combo.pack(side=tk.LEFT)

        ttk.Label(control_frame, text="(僅回補用)", font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=2)

        # 版面配置選擇
        ttk.Label(control_frame, text="按鈕位置:").pack(side=tk.LEFT, padx=(10, 5))
        self.layout_combo = ttk.Combobox(control_frame, values=["靠左", "置中", "靠右"], width=6)
        self.layout_combo.set("靠左")
        self.layout_combo.pack(side=tk.LEFT)
        self.layout_combo.bind("<<ComboboxSelected>>", lambda e: self.apply_layout())

        # === 按鈕區 ===
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5, anchor="w")
        try:
            self.button_frame.configure(height=60)
            self.button_frame.pack_propagate(False)
        except Exception:
            pass

        # ---- 按鈕建立 ----
        self.fetch_btn = ttk.Button(self.button_frame, text="📥 批量抓取最新 1分鐘資料", command=self.gui.backfill.fetch_latest)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        self.ws_start_btn = ttk.Button(self.button_frame, text="🟢 啟動多貨幣對 1秒監控", command=self.gui.monitor.start_ws)
        self.ws_start_btn.pack(side=tk.LEFT, padx=5)
        self.ws_stop_btn = ttk.Button(self.button_frame, text="⛔ 停止多貨幣對 1秒監控", command=self.gui.monitor.stop_ws, state=tk.DISABLED)
        self.ws_stop_btn.pack(side=tk.LEFT, padx=5)

        # 回補控制區
        self.backfill_control_frame = ttk.LabelFrame(root, text="回補資料控制（使用回補間隔設定）")
        self.backfill_control_frame.pack(fill=tk.X, padx=10, pady=5)

        self.backfill_btn = ttk.Button(self.backfill_control_frame, text="🚀 開始回補資料", command=self.gui.backfill.backfill_data)
        self.backfill_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.pause_resume_btn = ttk.Button(self.backfill_control_frame, text="⏸️ 暫時停止回補", command=self.gui.backfill.toggle_pause_resume, state=tk.DISABLED)
        self.pause_resume_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_backfill_btn = ttk.Button(self.backfill_control_frame, text="⏹️ 完全停止回補", command=self.gui.backfill.stop_backfill, state=tk.DISABLED)
        self.stop_backfill_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # === API 權重評估系統 ===
        self.weight_control_frame = ttk.LabelFrame(root, text="API 權重評估系統（6個時間框架）")
        self.weight_control_frame.pack(fill=tk.X, padx=10, pady=5)

        # 權重狀態顯示按鈕
        self.weight_status_btn = ttk.Button(self.weight_control_frame, text="📊 顯示權重狀態", command=self.show_weight_status)
        self.weight_status_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 重置權重按鈕
        self.reset_weight_btn = ttk.Button(self.weight_control_frame, text="🔄 重置所有權重", command=self.reset_all_weights)
        self.reset_weight_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 權重測試按鈕
        self.test_weight_btn = ttk.Button(self.weight_control_frame, text="🧪 權重測試模式", command=self.test_weight_system)
        self.test_weight_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 停止權重測試按鈕
        self.stop_weight_test_btn = ttk.Button(self.weight_control_frame, text="⏹️ 停止權重測試", command=self.stop_weight_test)
        self.stop_weight_test_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # === 錨定時間測試系統 ===
        self.anchor_control_frame = ttk.LabelFrame(root, text="錨定時間測試（60分鐘完整週期）")
        self.anchor_control_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 錨定時間測試按鈕
        self.start_anchor_test_btn = ttk.Button(self.anchor_control_frame, text="🎯 啟動錨定測試", command=self.start_anchor_time_test)
        self.start_anchor_test_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 停止錨定時間測試按鈕
        self.stop_anchor_test_btn = ttk.Button(self.anchor_control_frame, text="⏹️ 停止錨定測試", command=self.stop_anchor_time_test)
        self.stop_anchor_test_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # === 版面編輯 ===
        self.edit_btn = ttk.Button(self.button_frame, text="🛠 編輯版面", command=self.toggle_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.edit_ok_btn = ttk.Button(self.button_frame, text="✅ 套用", command=self._confirm_edit)
        self.edit_cancel_btn = ttk.Button(self.button_frame, text="↩️ 取消", command=self._cancel_edit)

        # === layout 設定檔路徑 ===
        self._layout_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ui_layout.json"))

        # === 按鈕清單 ===
        self.gui._buttons = [self.fetch_btn, self.ws_start_btn, self.ws_stop_btn, 
                             self.weight_status_btn, self.reset_weight_btn, self.test_weight_btn,
                             self.edit_btn, self.edit_ok_btn, self.edit_cancel_btn]
        self.gui._button_keys = {
            self.fetch_btn: "fetch",
            self.ws_start_btn: "ws_start",
            self.ws_stop_btn: "ws_stop",
            self.weight_status_btn: "weight_status",
            self.reset_weight_btn: "reset_weight",
            self.test_weight_btn: "test_weight",
            self.edit_btn: "edit",
            self.edit_ok_btn: "edit_ok",
            self.edit_cancel_btn: "edit_cancel",
        }

        # 套用儲存布局
        self._apply_saved_layout()

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

    # === 版面配置調整 ===
    def apply_layout(self):
        self.gui.utils.apply_layout_from_choice(self.layout_combo.get())

    # === 編輯模式切換 ===
    def toggle_edit_mode(self):
        self.gui.utils.toggle_edit_mode()

    # === layout 儲存 ===
    def _confirm_edit(self):
        self.gui.utils.confirm_edit_layout()

    def _cancel_edit(self):
        self.gui.utils.cancel_edit_layout()

    # === API 權重評估系統功能 ===
    def show_weight_status(self):
        """顯示所有時間框架的權重狀態（安全版本）"""
        try:
            # 立即顯示開始訊息
            self.gui.emit("[STATUS] 正在讀取權重狀態...")
            
            from modules.api_weight_evaluator import get_api_weight_evaluator
            evaluator = get_api_weight_evaluator()
            
            self.gui.emit("[STATUS] === API 權重評估狀態 ===")
            self.gui.emit("[STATUS] 重點關注：1分鐘時間框架")
            
            # 只讀取 1m 框架避免複雜操作
            try:
                stats_1m = evaluator.get_statistics("1m")
                
                # 使用文字狀態而非 emoji
                status_text = {
                    "normal": "[正常]",
                    "locked": "[被鎖]", 
                    "unlocked": "[解鎖]",
                    "second_cycle": "[第二循環]",
                    "halted": "[中止]"
                }.get(stats_1m["status"], "[未知]")
                
                self.gui.emit(f"[STATUS] 1分鐘框架: {status_text}")
                self.gui.emit(f"[STATUS] 權重={stats_1m['weight']:.3f} | "
                             f"建議筆數={stats_1m['base_count']} | "
                             f"狀態={stats_1m['status']}")
                self.gui.emit(f"[STATUS] 被鎖次數={stats_1m['total_locks']} | "
                             f"解鎖次數={stats_1m['unlock_times']}")
                
                # 簡化狀態提示
                if stats_1m["status"] == "second_cycle":
                    self.gui.emit("[STATUS] 提示: 已啟動第二循環機制")
                elif stats_1m["weight"] < 0.81:
                    self.gui.emit("[STATUS] 警告: 權重過低，系統已中止")
                elif stats_1m["weight"] >= 1.0:
                    self.gui.emit("[STATUS] 狀態: 權重正常，可正常請求")
                else:
                    self.gui.emit("[STATUS] 狀態: 權重調整中")
                    
            except Exception as inner_e:
                self.gui.emit(f"[STATUS] 讀取 1m 框架失敗: {inner_e}")
            
            # 嘗試讀取其他框架（可選）
            try:
                self.gui.emit("[STATUS] --- 其他時間框架 ---")
                all_stats = evaluator.get_all_statistics()
                
                for tf, stat in all_stats.items():
                    if tf == "1m":
                        continue
                    
                    status_text = {
                        "normal": "[正常]",
                        "locked": "[被鎖]", 
                        "unlocked": "[解鎖]",
                        "second_cycle": "[第二循環]",
                        "halted": "[中止]"
                    }.get(stat["status"], "[未知]")
                    
                    self.gui.emit(f"[STATUS] [{tf}] {status_text} | "
                                 f"權重={stat['weight']:.3f} | "
                                 f"筆數={stat['base_count']}")
                    
            except Exception as inner_e:
                self.gui.emit(f"[STATUS] 讀取其他框架時出錯: {inner_e}")
            
            self.gui.emit("[STATUS] === 權重狀態顯示完成 ===")
            
        except Exception as e:
            self.gui.emit(f"[ERROR] 顯示權重狀態失敗: {e}")
            # 不顯示詳細 traceback 避免當機

    def start_anchor_time_test(self):
        """啟動錨定時間測試"""
        try:
            from modules.utils.anchor_time_engine import get_anchor_time_engine
            
            # 取得參數
            current_symbol = "BTCUSDT"
            if hasattr(self, 'symbol_entry') and self.symbol_entry.get():
                current_symbol = self.symbol_entry.get()
            
            current_timeframe = "1m"
            if hasattr(self, 'interval_var') and self.interval_var.get():
                current_timeframe = self.interval_var.get()
            
            # 取得開始時間
            anchor_start_time = None
            if hasattr(self, 'start_datetime'):
                try:
                    anchor_start_time = datetime.strptime(
                        f"{self.start_date_var.get()} {self.start_hour_var.get()}:{self.start_minute_var.get()}:00",
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    anchor_start_time = datetime.now()
            
            # 取得錨定時間引擎
            anchor_engine = get_anchor_time_engine(self.gui.emit)
            
            # 停止之前的測試
            if anchor_engine.is_running:
                anchor_engine.stop_test()
                time.sleep(1)
            
            # 啟動新測試
            anchor_engine.start_test(current_symbol, current_timeframe, anchor_start_time)
            
            self.gui.emit("[ANCHOR] 錨定時間測試已啟動")
            
        except Exception as e:
            self.gui.emit(f"[ERROR] 啟動錨定時間測試失敗: {e}")
            
    def stop_anchor_time_test(self):
        """停止錨定時間測試"""
        try:
            from modules.utils.anchor_time_engine import get_anchor_time_engine
            anchor_engine = get_anchor_time_engine(self.gui.emit)
            anchor_engine.stop_test()
            self.gui.emit("[ANCHOR] 錨定時間測試已停止")
        except Exception as e:
            self.gui.emit(f"[ERROR] 停止錨定時間測試失敗: {e}")

    def reset_all_weights(self):
        """重置所有時間框架的權重設定"""
        try:
            from tkinter import messagebox
            result = messagebox.askyesno("確認重置", 
                                        "確定要重置所有時間框架的權重設定嗎？\n"
                                        "這將清除所有被鎖紀錄和權重調整。")
            
            if not result:
                return
                
            from modules.api_weight_evaluator import get_api_weight_evaluator
            evaluator = get_api_weight_evaluator()
            evaluator.reset_all()
            
            self.gui.emit("[RESET] 所有時間框架權重已重置為預設值")
            self.show_weight_status()  # 顯示重置後狀態
            
        except Exception as e:
            self.gui.emit(f"❌ 重置權重失敗: {e}")

    def test_weight_system(self):
        """測試權重評估系統（真實時間窗口控制）"""
        try:
            # 立即寫入日誌檔案確保機制正常
            import os
            from datetime import datetime
            error_log_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_error.log")
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== {datetime.now()} ===\n")
                f.write("權重測試開始（真實時間窗口控制）\n")
            
            self.gui.emit("[WEIGHT_TEST] 啟動真實權重測試系統...")
            
            # 匯入並初始化權重測試引擎
            from modules.utils.weight_test_engine import get_weight_test_engine
            
            # 取得當前選擇的貨幣對
            current_symbol = "BTCUSDT"  # 預設值
            if hasattr(self, 'symbol_entry') and self.symbol_entry.get():
                current_symbol = self.symbol_entry.get()
            elif hasattr(self.gui, 'symbol_entry') and self.gui.symbol_entry.get():
                current_symbol = self.gui.symbol_entry.get()
            
            # 取得當前選擇的時間框架
            current_timeframe = "1m"  # 預設值
            if hasattr(self, 'interval_var') and self.interval_var.get():
                current_timeframe = self.interval_var.get()
            
            self.gui.emit(f"[WEIGHT_TEST] 測試貨幣對: {current_symbol}")
            self.gui.emit(f"[WEIGHT_TEST] 測試時間框架: {current_timeframe}")
            
            # 取得測試引擎實例
            test_engine = get_weight_test_engine(self.gui.emit)
            
            # 停止之前的測試（如果有）
            if test_engine.is_running:
                test_engine.stop_test()
                time.sleep(1)
            
            # 開始新測試
            test_engine.start_test(current_symbol, current_timeframe)
            
            self.gui.emit("[WEIGHT_TEST] 權重測試已啟動，正在監控時間窗口...")
            
            # 記錄啟動日誌
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"權重測試引擎已啟動 - 貨幣對: {current_symbol}\n")
            
        except Exception as e:
            # 強制寫入所有可能的錯誤位置
            error_msg = f"[WEIGHT_TEST_ERROR] {datetime.now()}: {e}\n"
            
            # 1. 嘗試寫入 GUI
            try:
                self.gui.emit(error_msg.strip())
            except:
                pass
            
            # 2. 嘗試寫入 test_error.log
            try:
                with open(error_log_path, "a", encoding="utf-8") as f:
                    f.write(error_msg)
                    import traceback
                    f.write(f"詳細錯誤: {traceback.format_exc()}\n")
            except:
                pass
            
            # 3. 嘗試寫入根目錄
            try:
                root_log = os.path.join(os.path.dirname(__file__), "..", "emergency_log.txt")
                with open(root_log, "a", encoding="utf-8") as f:
                    f.write(error_msg)
            except:
                pass
            
            # 4. 最後嘗試 print
            try:
                print(error_msg.strip())
            except:
                pass

    def stop_weight_test(self):
        """停止權重測試"""
        try:
            from modules.utils.weight_test_engine import get_weight_test_engine
            test_engine = get_weight_test_engine()
            
            if test_engine.is_running:
                test_engine.stop_test()
                self.gui.emit("[WEIGHT_TEST] 權重測試已停止")
            else:
                self.gui.emit("[WEIGHT_TEST] 沒有正在運行的測試")
                
        except Exception as e:
            self.gui.emit(f"[WEIGHT_TEST_ERROR] 停止測試失敗: {e}")

    # === 載入 layout ===
    def _apply_saved_layout(self):
        self.gui.utils.apply_saved_layout(self._layout_file)
