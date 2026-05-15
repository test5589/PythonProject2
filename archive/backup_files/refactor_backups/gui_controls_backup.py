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
        
        # 初始化佈局文件路徑
        self._layout_file = os.path.join(os.path.dirname(__file__), "..", "data", "layout.json")
        
        # 初始化權重測試控制器
        from core.weight_test_controller import WeightTestController
        self.weight_test_controller = WeightTestController(gui)

        # 創建控制項
        self._create_controls(root)
    
    def _create_controls(self, root):
        """創建所有控制項"""
        # === 簡化佈局組初始化 ===
        self.gui._layout_groups = {}

        # === 上方控制區 - 確保完全靠左 ===
        control_frame = ttk.Frame(root)
        control_frame.pack(anchor=tk.W, pady=10, padx=0, fill=tk.X)  # 完全靠左，無左邊距

        # === 創建時間選擇器 ===
        self._create_datetime_selectors(control_frame)

        # === 其他控制項 ===
        # K線時間段（使用統一配置）
        control_options_frame = ttk.Frame(control_frame)
        control_options_frame.pack(anchor=tk.W, pady=5, padx=10, fill=tk.X)  # 10px左邊距對齊

        ttk.Label(control_options_frame, text="K線時間段:").pack(side=tk.LEFT, padx=(0, 5))
        interval_options = list(TradingConfig.SUPPORTED_INTERVALS.keys())
        self.backfill_interval_combo = ttk.Combobox(control_options_frame,
                                                    values=interval_options,
                                                    width=8, state="readonly")
        self.backfill_interval_combo.set(TradingConfig.DEFAULT_INTERVAL)
        self.backfill_interval_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(control_options_frame, text="(僅回補用)", font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(0, 15))

        # === 按鈕區 ===
        self.button_frame = ttk.Frame(root)
        self.button_frame.pack(fill=tk.X, padx=10, pady=5, anchor="w")
        try:
            self.button_frame.configure(height=60)
            self.button_frame.pack_propagate(False)
        except Exception:
            pass

        # ---- 先建立主要按鈕並加入佈局組 ----
        self.fetch_btn = ttk.Button(self.button_frame, text="📥 批量抓取最新 1分鐘資料", command=self.gui.backfill.fetch_latest)
        self.fetch_btn.pack(side=tk.LEFT, padx=5)
        self.ws_start_btn = ttk.Button(self.button_frame, text="🟢 啟動多貨幣對 1秒監控", command=self.gui.monitor.start_ws)
        self.ws_start_btn.pack(side=tk.LEFT, padx=5)
        self.ws_stop_btn = ttk.Button(self.button_frame, text="⛔ 停止多貨幣對 1秒監控", command=self.gui.monitor.stop_ws, state=tk.DISABLED)
        self.ws_stop_btn.pack(side=tk.LEFT, padx=5)

        # 編輯按鈕
        self.edit_btn = ttk.Button(self.button_frame, text="🛠 編輯版面", command=self.toggle_edit_mode)
        self.edit_btn.pack(side=tk.LEFT, padx=5)
        self.edit_ok_btn = ttk.Button(self.button_frame, text="✅ 套用", command=self._confirm_edit)
        # 初始隱藏，不pack
        self.edit_cancel_btn = ttk.Button(self.button_frame, text="↩️ 取消", command=self._cancel_edit)
        # 初始隱藏，不pack

        # === 填充按鈕清單（簡化版）===
        self.gui._buttons = [self.fetch_btn, self.ws_start_btn, self.ws_stop_btn, 
                             self.edit_btn, self.edit_ok_btn, self.edit_cancel_btn]

        # 快捷按鈕會在 _create_datetime_selectors 中添加

        self.gui._button_keys = {
            self.fetch_btn: "fetch",
            self.ws_start_btn: "ws_start",
            self.ws_stop_btn: "ws_stop",
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

        # === 其他控制項區域 ===
        # 回補控制區
        self.backfill_control_frame = ttk.LabelFrame(root, text="回補資料控制（使用K線時間段設定）")
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

        # 權重控制按鈕
        self.weight_status_btn = ttk.Button(self.weight_control_frame, text="📊 顯示權重狀態", command=self.show_weight_status)
        self.weight_status_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.reset_weight_btn = ttk.Button(self.weight_control_frame, text="🔄 重置所有權重", command=self.reset_all_weights)
        self.reset_weight_btn.pack(side=tk.LEFT, padx=5, pady=5)
        self.test_weight_btn = ttk.Button(self.weight_control_frame, text="🧪 權重測試模式", command=self.test_weight_system)
        self.test_weight_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # 停止權重測試按鈕
        self.stop_weight_test_btn = ttk.Button(self.weight_control_frame, text="⏹️ 停止權重測試", command=self.stop_weight_test)
        self.stop_weight_test_btn.pack(side=tk.LEFT, padx=5, pady=5)

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
            
            from tools.api_weight_evaluator import get_api_weight_evaluator
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

    # 錨定時間測試功能已整合到權重測試系統中
    
    def _create_datetime_selectors(self, parent_frame):
        """創建開始和結束時間選擇器 - 完全靠左佈局"""
        from datetime import datetime, timedelta, timezone

        # 時間選擇器 - 與其他控制項統一10px左邊距
        time_frame = ttk.Frame(parent_frame)
        time_frame.pack(anchor=tk.W, pady=5, padx=10, fill=tk.X)  # 10px左邊距對齊

        # 台北時區
        taipei = timezone(timedelta(hours=8))
        now_tw = datetime.now(tz=taipei)
        start_tw = now_tw - timedelta(days=1)

        # === 起始時間 - 完全靠左 ===
        start_frame = ttk.LabelFrame(time_frame, text="起始時間", padding=3)
        start_frame.pack(side=tk.LEFT, padx=0, pady=2, anchor=tk.W)  # 完全靠左，無間距

        # 起始時間控件 - 超緊湊排列，靠左對齊
        self.sy = ttk.Spinbox(start_frame, from_=2020, to=2030, width=5)
        self.sy.set(start_tw.year)
        self.sy.pack(side=tk.LEFT, padx=(0, 2), pady=0)  # 第一個控件左邊距0

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

        # === 結束時間 - 緊跟起始時間 ===
        end_frame = ttk.LabelFrame(time_frame, text="結束時間", padding=3)
        end_frame.pack(side=tk.LEFT, padx=(15, 0), pady=2, anchor=tk.W)  # 與起始時間保持間距

        # 結束時間控件 - 緊湊排列，靠左對齊
        self.ey = ttk.Spinbox(end_frame, from_=2020, to=2030, width=5)
        self.ey.set(now_tw.year)
        self.ey.pack(side=tk.LEFT, padx=(0, 2), pady=0)  # 第一個控件左邊距0

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

        # === 快捷按鈕 ===
        button_frame = ttk.Frame(parent_frame)
        button_frame.pack(anchor=tk.W, pady=5, padx=10, fill=tk.X)  # 10px左邊距對齊

        # 創建快捷按鈕
        self.quick_now_btn = ttk.Button(button_frame, text="🕐 現在", command=self._set_current_time)
        self.quick_yesterday_btn = ttk.Button(button_frame, text="📅 昨天→今天", command=self._set_yesterday_to_today)
        self.quick_week_btn = ttk.Button(button_frame, text="📊 最近一週", command=self._set_last_week)

        # pack佈局
        self.quick_now_btn.pack(side=tk.LEFT, padx=(0, 5), pady=2)
        self.quick_yesterday_btn.pack(side=tk.LEFT, padx=(0, 5), pady=2)
        self.quick_week_btn.pack(side=tk.LEFT, padx=0, pady=2)

        # 加入全局按鈕清單以支持佈局調整
        self.gui._buttons.extend([
            self.quick_now_btn,
            self.quick_yesterday_btn,
            self.quick_week_btn
        ])

        # 加入按鈕鍵映射
        self.gui._button_keys.update({
            self.quick_now_btn: "quick_now",
            self.quick_yesterday_btn: "quick_yesterday",
            self.quick_week_btn: "quick_week"
        })

        # === 資產分類和交易對 ===
        asset_frame = ttk.Frame(parent_frame)
        asset_frame.pack(anchor=tk.W, pady=5, padx=10, fill=tk.X)  # 10px左邊距對齊

        ttk.Label(asset_frame, text="資產分類:").pack(side=tk.LEFT, padx=(0, 5))
        self.category_entry = ttk.Entry(asset_frame, width=20)
        self.category_entry.insert(0, TradingConfig.DEFAULT_CATEGORY)
        self.category_entry.pack(side=tk.LEFT, padx=(0, 15))  # 與交易對保持間距

        ttk.Label(asset_frame, text="交易對:").pack(side=tk.LEFT, padx=(0, 5))
        self.symbol_entry = ttk.Entry(asset_frame, width=20)
        self.symbol_entry.insert(0, TradingConfig.DEFAULT_SYMBOL)
        self.symbol_entry.pack(side=tk.LEFT)
    
    def _set_current_time(self):
        """設定為當前時間"""
        try:
            from datetime import datetime
            
            # 除錯提示：按鈕被點擊
            self.gui.emit("[DEBUG] 🔘 '現在' 按鈕被點擊")
            print("[DEBUG] _set_current_time 方法被調用")
            
            # 檢查所有Spinbox是否存在
            spinboxes = ['sy', 'sM', 'sd', 'sh', 'su', 'ss']
            for sb in spinboxes:
                if not hasattr(self, sb):
                    error_msg = f"[ERROR] Spinbox {sb} 不存在"
                    self.gui.emit(error_msg)
                    print(error_msg)
                    return
            
            now = datetime.now()
            
            # 設定時間值 - 使用ttk.Spinbox的set方法
            self.sy.set(now.year)
            self.sM.set(now.month)
            self.sd.set(now.day)
            self.sh.set(now.hour)
            self.su.set(now.minute)
            self.ss.set(0)  # 秒固定為0
            
            success_msg = f"[DATETIME] 🕐 已設定為當前時間: {now.strftime('%Y-%m-%d %H:%M:%S')}"
            self.gui.emit(success_msg)
            print("[DEBUG] _set_current_time 執行成功")
            
        except Exception as e:
            error_msg = f"[ERROR] 設定當前時間失敗: {str(e)}"
            self.gui.emit(error_msg)
            print(f"[DEBUG] _set_current_time 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_one_hour(self):
        """增加一小時"""
        from datetime import datetime, timedelta
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
    
    def _set_yesterday_to_today(self):
        """設定昨天到今天的時間範圍"""
        try:
            from datetime import datetime, timedelta
            
            # 除錯提示
            self.gui.emit("[DEBUG] 🔘 '昨天到今天' 按鈕被點擊")
            print("[DEBUG] _set_yesterday_to_today 方法被調用")
            
            now = datetime.now()
            yesterday = now - timedelta(days=1)
            
            # 設定起始時間為昨天 - 使用ttk.Spinbox的set方法
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
            print("[DEBUG] _set_yesterday_to_today 執行成功")
            
        except Exception as e:
            error_msg = f"[ERROR] 設定昨天到今天失敗: {str(e)}"
            self.gui.emit(error_msg)
            print(f"[DEBUG] _set_yesterday_to_today 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _set_last_week(self):
        """設定最近一週的時間範圍"""
        try:
            from datetime import datetime, timedelta
            
            now = datetime.now()
            last_week = now - timedelta(days=7)
            
            # 設定起始時間為一週前 - 使用ttk.Spinbox的set方法
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
            print("[DEBUG] _set_last_week 執行成功")
            
        except Exception as e:
            error_msg = f"[ERROR] 設定最近一週失敗: {str(e)}"
            self.gui.emit(error_msg)
            print(f"[DEBUG] _set_last_week 錯誤: {e}")
            import traceback
            traceback.print_exc()
    
    def _add_one_day(self):
        """增加一天"""
        from datetime import datetime, timedelta
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

    def _convert_interval_to_api_format(self, interval_display: str) -> str:
        """將GUI顯示的時間間隔轉換為API格式"""
        interval_mapping = {
            # 中文格式 -> API格式
            "1分": "1m",
            "3分": "3m", 
            "5分": "5m",
            "15分": "15m",
            "30分": "30m",
            "1小時": "1h",
            "2小時": "2h",
            "4小時": "4h",
            "6小時": "6h",
            "8小時": "8h",
            "12小時": "12h",
            "1天": "1d",
            "3天": "3d",
            "1週": "1w",
            "1月": "1M",
            # 已經是API格式的直接返回
            "1m": "1m",
            "3m": "3m",
            "5m": "5m", 
            "15m": "15m",
            "30m": "30m",
            "1h": "1h",
            "2h": "2h",
            "4h": "4h",
            "6h": "6h",
            "8h": "8h",
            "12h": "12h",
            "1d": "1d",
            "3d": "3d",
            "1w": "1w",
            "1M": "1M"
        }
        
        converted = interval_mapping.get(interval_display, "1m")
        if converted != interval_display:
            self.gui.emit(f"[INTERVAL] 轉換時間框架: {interval_display} -> {converted}")
        
        return converted

    def reset_all_weights(self):
        """重置所有時間框架的權重設定"""
        try:
            from tkinter import messagebox
            result = messagebox.askyesno("確認重置", 
                                        "確定要重置所有時間框架的權重設定嗎？\n"
                                        "這將清除所有被鎖紀錄和權重調整。")
            
            if not result:
                return
                
            from tools.api_weight_evaluator import get_api_weight_evaluator
            evaluator = get_api_weight_evaluator()
            evaluator.reset_all()
            
            self.gui.emit("[RESET] 所有時間框架權重已重置為預設值")
            self.show_weight_status()  # 顯示重置後狀態
            
        except Exception as e:
            self.gui.emit(f"❌ 重置權重失敗: {e}")

    def test_weight_system(self):
        """啟動權重測試系統"""
        self.weight_test_controller.start_weight_test()

    def stop_weight_test(self):
        """停止權重測試系統"""
        self.weight_test_controller.stop_weight_test()

    # === 載入 layout ===
    def _apply_saved_layout(self):
        self.gui.utils.load_and_apply_layout(self._layout_file)
