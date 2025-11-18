#!/usr/bin/env python3
"""
GUI Controls - 圖形介面控制模組
包含完整的回補區間選擇功能
"""

import os
import time
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta, timezone

class GUIControls:
    def __init__(self, root, main_gui):
        self.root = root
        self.gui = main_gui
        
        # 建立缺失的輸入欄位
        self.category_entry = tk.StringVar(value="crypto")
        
        # === 按鈕框架 ===
        self.button_frame = ttk.LabelFrame(root, text="主要控制")
        self.button_frame.pack(fill=tk.X, padx=10, pady=5)

        self.start_btn = ttk.Button(self.button_frame, text="🚀 開始監控", command=self.gui.monitor.start_ws)
        self.start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_btn = ttk.Button(self.button_frame, text="⏹️ 停止監控", command=self.gui.monitor.stop_ws, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # === WebSocket 監控 ===
        self.ws_frame = ttk.LabelFrame(root, text="WebSocket 多貨幣對監控")
        self.ws_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.ws_start_btn = ttk.Button(self.ws_frame, text="🌐 開始多貨幣對 1秒監控", command=self.gui.monitor.start_ws)
        self.ws_start_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.ws_stop_btn = ttk.Button(self.ws_frame, text="⛔ 停止多貨幣對 1秒監控", command=self.gui.monitor.stop_ws, state=tk.DISABLED)
        self.ws_stop_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # === 回補資料控制區 ===
        self.backfill_frame = ttk.LabelFrame(root, text="回補資料控制")
        self.backfill_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 交易對輸入
        symbol_frame = ttk.Frame(self.backfill_frame)
        symbol_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(symbol_frame, text="交易對:").pack(side=tk.LEFT)
        self.symbol_entry = tk.Entry(symbol_frame, width=15)
        self.symbol_entry.pack(side=tk.LEFT, padx=5)
        self.symbol_entry.insert(0, "BTCUSDT")
        
        # 時間框架選擇
        interval_frame = ttk.Frame(self.backfill_frame)
        interval_frame.pack(fill=tk.X, padx=5, pady=2)
        ttk.Label(interval_frame, text="時間框架:").pack(side=tk.LEFT)
        self.interval_var = tk.StringVar(value="1m")
        interval_combo = ttk.Combobox(interval_frame, textvariable=self.interval_var, 
                                     values=["1m", "3m", "5m", "15m", "30m", "1h", "4h", "1d"], 
                                     width=10, state="readonly")
        interval_combo.pack(side=tk.LEFT, padx=5)
        
        # 開始日期時間選擇
        datetime_frame = ttk.Frame(self.backfill_frame)
        datetime_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(datetime_frame, text="開始時間:").pack(side=tk.LEFT)
        
        # 日期選擇
        self.start_date_var = tk.StringVar(value=(datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"))
        self.start_date_entry = tk.Entry(datetime_frame, textvariable=self.start_date_var, width=12)
        self.start_date_entry.pack(side=tk.LEFT, padx=2)
        
        # 時間選擇
        ttk.Label(datetime_frame, text="時間:").pack(side=tk.LEFT, padx=(10, 2))
        self.start_hour_var = tk.StringVar(value="00")
        hour_spin = ttk.Spinbox(datetime_frame, from_=0, to=23, textvariable=self.start_hour_var, 
                               width=3, format="%02.0f")
        hour_spin.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(datetime_frame, text=":").pack(side=tk.LEFT)
        self.start_minute_var = tk.StringVar(value="00")
        minute_spin = ttk.Spinbox(datetime_frame, from_=0, to=59, textvariable=self.start_minute_var, 
                                 width=3, format="%02.0f")
        minute_spin.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(datetime_frame, text=":").pack(side=tk.LEFT)
        self.start_second_var = tk.StringVar(value="00")
        second_spin = ttk.Spinbox(datetime_frame, from_=0, to=59, textvariable=self.start_second_var, 
                                 width=3, format="%02.0f")
        second_spin.pack(side=tk.LEFT, padx=1)
        
        # 結束日期時間選擇
        end_datetime_frame = ttk.Frame(self.backfill_frame)
        end_datetime_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(end_datetime_frame, text="結束時間:").pack(side=tk.LEFT)
        
        # 結束日期選擇
        self.end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.end_date_entry = tk.Entry(end_datetime_frame, textvariable=self.end_date_var, width=12)
        self.end_date_entry.pack(side=tk.LEFT, padx=2)
        
        # 結束時間選擇
        ttk.Label(end_datetime_frame, text="時間:").pack(side=tk.LEFT, padx=(10, 2))
        self.end_hour_var = tk.StringVar(value="23")
        end_hour_spin = ttk.Spinbox(end_datetime_frame, from_=0, to=23, textvariable=self.end_hour_var, 
                                   width=3, format="%02.0f")
        end_hour_spin.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(end_datetime_frame, text=":").pack(side=tk.LEFT)
        self.end_minute_var = tk.StringVar(value="59")
        end_minute_spin = ttk.Spinbox(end_datetime_frame, from_=0, to=59, textvariable=self.end_minute_var, 
                                     width=3, format="%02.0f")
        end_minute_spin.pack(side=tk.LEFT, padx=1)
        
        ttk.Label(end_datetime_frame, text=":").pack(side=tk.LEFT)
        self.end_second_var = tk.StringVar(value="59")
        end_second_spin = ttk.Spinbox(end_datetime_frame, from_=0, to=59, textvariable=self.end_second_var, 
                                     width=3, format="%02.0f")
        end_second_spin.pack(side=tk.LEFT, padx=1)
        
        # 回補控制按鈕
        backfill_btn_frame = ttk.Frame(self.backfill_frame)
        backfill_btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.backfill_btn = ttk.Button(backfill_btn_frame, text="🚀 開始回補資料", command=self.gui.backfill.backfill_data)
        self.backfill_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.pause_resume_btn = ttk.Button(backfill_btn_frame, text="⏸️ 暫時停止回補", command=self.gui.backfill.toggle_pause_resume, state=tk.DISABLED)
        self.pause_resume_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.stop_backfill_btn = ttk.Button(backfill_btn_frame, text="⏹️ 完全停止回補", command=self.gui.backfill.stop_backfill, state=tk.DISABLED)
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
        
        # 權重測試按鈕（整合錨定時間）
        self.test_weight_btn = ttk.Button(self.weight_control_frame, text="🧪 權重測試模式", command=self.test_weight_system)
        self.test_weight_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 停止權重測試按鈕
        self.stop_weight_test_btn = ttk.Button(self.weight_control_frame, text="⏹️ 停止權重測試", command=self.stop_weight_test)
        self.stop_weight_test_btn.pack(side=tk.LEFT, padx=5, pady=5)
        
        # === 版面編輯 ===
        self.edit_btn = ttk.Button(self.button_frame, text="🛠 編輯版面", command=self.toggle_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.edit_ok_btn = ttk.Button(self.button_frame, text="✅ 套用", command=self._confirm_edit)
        self.edit_cancel_btn = ttk.Button(self.button_frame, text="↩️ 取消", command=self._cancel_edit)

        # === layout 設定檔路徑 ===
        self._layout_file = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "ui_layout.json"))

        # === 按鈕清單 ===
        self.buttons = [
            self.start_btn, self.stop_btn, 
            self.ws_start_btn, self.ws_stop_btn,
            self.backfill_btn, self.pause_resume_btn, self.stop_backfill_btn,
            self.weight_status_btn, self.reset_weight_btn, self.test_weight_btn, self.stop_weight_test_btn,
            self.edit_btn, self.edit_ok_btn, self.edit_cancel_btn
        ]

        # 初始化時隱藏編輯按鈕
        self.edit_ok_btn.pack_forget()
        self.edit_cancel_btn.pack_forget()

        # 載入儲存的版面
        self._apply_saved_layout()

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

    def reset_all_weights(self):
        """重置所有時間框架的權重設定"""
        try:
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
        """測試權重評估系統（整合錨定時間機制）"""
        try:
            # 立即寫入日誌檔案確保機制正常
            import os
            from datetime import datetime
            error_log_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_error.log")
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== {datetime.now()} ===\n")
                f.write("權重測試開始（整合錨定時間機制）\n")
            
            self.gui.emit("[WEIGHT_TEST] 啟動整合權重測試系統...")
            
            # 取得當前選擇的參數
            current_symbol = "BTCUSDT"
            if hasattr(self, 'symbol_entry') and self.symbol_entry.get():
                current_symbol = self.symbol_entry.get()
            
            current_timeframe = "1m"
            if hasattr(self, 'interval_var') and self.interval_var.get():
                current_timeframe = self.interval_var.get()
            
            # 取得開始時間作為錨定時間
            anchor_start_time = None
            if hasattr(self, 'start_date_var') and hasattr(self, 'start_hour_var') and hasattr(self, 'start_minute_var'):
                try:
                    anchor_start_time = datetime.strptime(
                        f"{self.start_date_var.get()} {self.start_hour_var.get()}:{self.start_minute_var.get()}:00",
                        "%Y-%m-%d %H:%M:%S"
                    )
                except:
                    anchor_start_time = datetime.now()
            
            # 修復 None 檢查
            if anchor_start_time is None:
                anchor_start_time = datetime.now()
            
            self.gui.emit(f"[WEIGHT_TEST] 測試貨幣對: {current_symbol}")
            self.gui.emit(f"[WEIGHT_TEST] 測試時間框架: {current_timeframe}")
            self.gui.emit(f"[WEIGHT_TEST] 錨定時間: {anchor_start_time.strftime('%Y/%m/%d %H:%M:%S')}")
            
            # 啟動錨定時間測試（整合權重評估）
            from modules.utils.anchor_time_engine import get_anchor_time_engine
            anchor_engine = get_anchor_time_engine(self.gui.emit)
            
            # 停止之前的測試
            if anchor_engine.is_running:
                anchor_engine.stop_test()
                time.sleep(1)
            
            # 啟動整合測試
            anchor_engine.start_test(current_symbol, current_timeframe, anchor_start_time)
            
            self.gui.emit("[WEIGHT_TEST] 整合權重測試已啟動，開始60分鐘錨定週期...")
            
            # 記錄啟動日誌
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"整合權重測試已啟動 - 貨幣對: {current_symbol}, 時間框架: {current_timeframe}\n")
            
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
        """停止權重測試（整合錨定時間）"""
        try:
            # 停止錨定時間測試
            from modules.utils.anchor_time_engine import get_anchor_time_engine
            anchor_engine = get_anchor_time_engine(self.gui.emit)
            anchor_engine.stop_test()
            
            # 停止傳統權重測試（備用）
            try:
                from modules.utils.weight_test_engine import get_weight_test_engine
                test_engine = get_weight_test_engine(self.gui.emit)
                test_engine.stop_test()
            except:
                pass
            
            self.gui.emit("[WEIGHT_TEST] 整合權重測試已停止")
        except Exception as e:
            self.gui.emit(f"[ERROR] 停止權重測試失敗: {e}")

    # === 版面編輯功能 ===
    def toggle_edit_mode(self):
        """切換編輯模式"""
        self.gui.emit("[LAYOUT] 進入版面編輯模式")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.ws_start_btn.config(state=tk.NORMAL)
        self.ws_stop_btn.config(state=tk.NORMAL)
        self.backfill_btn.config(state=tk.NORMAL)
        self.pause_resume_btn.config(state=tk.NORMAL)
        self.stop_backfill_btn.config(state=tk.NORMAL)
        self.weight_status_btn.config(state=tk.NORMAL)
        self.reset_weight_btn.config(state=tk.NORMAL)
        self.test_weight_btn.config(state=tk.NORMAL)
        self.stop_weight_test_btn.config(state=tk.NORMAL)
        
        self.edit_btn.pack_forget()
        self.edit_ok_btn.pack(side=tk.LEFT, padx=5)
        self.edit_cancel_btn.pack(side=tk.LEFT, padx=5)

    def _confirm_edit(self):
        """確認編輯"""
        self.gui.emit("[LAYOUT] 套用版面編輯")
        self.gui.utils.save_layout(self._layout_file)
        self._exit_edit_mode()

    def _cancel_edit(self):
        """取消編輯"""
        self.gui.emit("[LAYOUT] 取消版面編輯")
        self._apply_saved_layout()
        self._exit_edit_mode()

    def _exit_edit_mode(self):
        """退出編輯模式"""
        self.edit_ok_btn.pack_forget()
        self.edit_cancel_btn.pack_forget()
        self.edit_btn.pack(side=tk.LEFT, padx=5)

    def _apply_saved_layout(self):
        """載入儲存的版面"""
        try:
            self.gui.utils.apply_saved_layout(self._layout_file)
        except Exception as e:
            self.gui.emit(f"[LAYOUT] 載入版面失敗: {e}")
