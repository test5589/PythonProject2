"""
controls_base.py - GUI基礎控制項
負責主要控制項的創建和配置管理
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from config.trading_config import TradingConfig
from .layout_config import (
    MAIN_CONTROL_PADY,
    MAIN_CONTROL_PADX,
    CONFIG_FRAME_PADY,
    CONFIG_FRAME_PADX,
    BACKFILL_FRAME_PADY,
    BACKFILL_FRAME_PADX,
    BACKFILL_BUTTON_PADY,
    BACKFILL_BUTTON_PADX,
    WEIGHT_FRAME_PADY,
    WEIGHT_FRAME_PADX,
    WEIGHT_BUTTON_PADY,
    WEIGHT_BUTTON_PADX,
)
from .monitor_board_template import AVAILABLE_TEMPLATES

class ControlsBase:
    """GUI基礎控制項管理器"""
    
    def __init__(self, gui):
        self.gui = gui
        
        # 初始化佈局文件路徑
        self._layout_file = os.path.join(os.path.dirname(__file__), "..", "..", "data", "layout.json")
        
        # 初始化權重測試控制器
        from core.weight_test_controller import WeightTestController
        self.weight_test_controller = WeightTestController(gui)
        
    def create_main_control_frame(self, root):
        """創建主控制框架"""
        # === 上方控制區 - 確保完全靠左 ===
        control_frame = ttk.Frame(root)
        control_frame.pack(anchor=tk.W, pady=MAIN_CONTROL_PADY, padx=MAIN_CONTROL_PADX, fill=tk.X)
        return control_frame
        
    def create_config_controls(self, parent_frame):
        """創建配置控制項"""
        # === K線時間段配置 ===
        control_options_frame = ttk.Frame(parent_frame)
        control_options_frame.pack(anchor=tk.W, pady=CONFIG_FRAME_PADY, padx=CONFIG_FRAME_PADX, fill=tk.X)

        ttk.Label(control_options_frame, text="K線時間段:").pack(side=tk.LEFT, padx=(0, 5))
        interval_options = list(TradingConfig.SUPPORTED_INTERVALS.keys())
        self.backfill_interval_combo = ttk.Combobox(control_options_frame,
                                                    values=interval_options,
                                                    width=8, state="readonly")
        self.backfill_interval_combo.set(TradingConfig.DEFAULT_INTERVAL)
        self.backfill_interval_combo.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Label(control_options_frame, text="(僅回補用)", font=("Arial", 8), foreground="gray").pack(side=tk.LEFT, padx=(0, 15))

        # 模板選擇（A/B ...），以 MainGUI.current_template 為預設
        ttk.Label(control_options_frame, text="模板:").pack(side=tk.LEFT, padx=(0, 5))
        self.template_var = tk.StringVar(value=getattr(self.gui, "current_template", "A"))
        self.template_combo = ttk.Combobox(
            control_options_frame,
            values=AVAILABLE_TEMPLATES,
            width=4,
            state="readonly",
            textvariable=self.template_var,
        )
        self.template_combo.pack(side=tk.LEFT, padx=(0, 10))

        def _on_template_changed(event=None):
            tpl = self.template_var.get()
            gui = self.gui
            if hasattr(gui, "set_monitor_template"):
                try:
                    gui.set_monitor_template(tpl)
                except Exception:
                    pass

        self.template_combo.bind("<<ComboboxSelected>>", _on_template_changed)
        
    def create_backfill_controls(self, root):
        """創建回補控制區域"""
        # === 回補控制區 ===
        self.backfill_control_frame = ttk.LabelFrame(root, text="回補資料控制（使用K線時間段設定）")
        self.backfill_control_frame.pack(fill=tk.X, padx=BACKFILL_FRAME_PADX, pady=BACKFILL_FRAME_PADY)

        self.backfill_btn = ttk.Button(self.backfill_control_frame, text="🚀 開始回補資料", command=self.gui.backfill.backfill_data)
        self.backfill_btn.pack(side=tk.LEFT, padx=BACKFILL_BUTTON_PADX, pady=BACKFILL_BUTTON_PADY)
        self.pause_resume_btn = ttk.Button(self.backfill_control_frame, text="⏸️ 暫時停止回補", command=self.gui.backfill.toggle_pause_resume, state=tk.DISABLED)
        self.pause_resume_btn.pack(side=tk.LEFT, padx=BACKFILL_BUTTON_PADX, pady=BACKFILL_BUTTON_PADY)
        self.stop_backfill_btn = ttk.Button(self.backfill_control_frame, text="⏹️ 完全停止回補", command=self.gui.backfill.stop_backfill, state=tk.DISABLED)
        self.stop_backfill_btn.pack(side=tk.LEFT, padx=BACKFILL_BUTTON_PADX, pady=BACKFILL_BUTTON_PADY)
        
    def create_weight_controls(self, root):
        """創建權重控制區域"""
        # === API 權重評估系統 ===
        self.weight_control_frame = ttk.LabelFrame(root, text="API 權重評估系統（6個時間框架）")
        self.weight_control_frame.pack(fill=tk.X, padx=WEIGHT_FRAME_PADX, pady=WEIGHT_FRAME_PADY)

        # 權重控制按鈕
        self.weight_status_btn = ttk.Button(self.weight_control_frame, text="📊 顯示權重狀態", command=self.show_weight_status)
        self.weight_status_btn.pack(side=tk.LEFT, padx=WEIGHT_BUTTON_PADX, pady=WEIGHT_BUTTON_PADY)
        self.reset_weight_btn = ttk.Button(self.weight_control_frame, text="🔄 重置所有權重", command=self.reset_all_weights)
        self.reset_weight_btn.pack(side=tk.LEFT, padx=WEIGHT_BUTTON_PADX, pady=WEIGHT_BUTTON_PADY)
        self.test_weight_btn = ttk.Button(self.weight_control_frame, text="🧪 權重測試模式", command=self.test_weight_system)
        self.test_weight_btn.pack(side=tk.LEFT, padx=WEIGHT_BUTTON_PADX, pady=WEIGHT_BUTTON_PADY)

        # 停止權重測試按鈕
        self.stop_weight_test_btn = ttk.Button(self.weight_control_frame, text="⏹️ 停止權重測試", command=self.stop_weight_test)
        self.stop_weight_test_btn.pack(side=tk.LEFT, padx=WEIGHT_BUTTON_PADX, pady=WEIGHT_BUTTON_PADY)
        
    def show_weight_status(self):
        """顯示權重狀態"""
        try:
            from tools.api_weight_evaluator import get_api_weight_evaluator
            evaluator = get_api_weight_evaluator()
            
            self.gui.emit("[STATUS] === 🔍 API權重評估系統狀態 ===")
            
            # 顯示1分鐘框架詳細信息
            stat_1m = evaluator.get_statistics("1m")
            
            status_text = {
                "normal": "[正常]",
                "locked": "[被鎖]", 
                "unlocked": "[解鎖]",
                "second_cycle": "[第二循環]",
                "halted": "[中止]"
            }.get(stat_1m["status"], "[未知]")
            
            self.gui.emit(f"[STATUS] === 📊 主要框架 (1分鐘) ===")
            self.gui.emit(f"[STATUS] 🎯 狀態: {status_text}")
            self.gui.emit(f"[STATUS] ⚖️ 權重係數: {stat_1m['weight']:.3f}")
            self.gui.emit(f"[STATUS] 📈 基礎筆數: {stat_1m['base_count']}")
            self.gui.emit(f"[STATUS] 🔢 建議筆數: {evaluator.get_optimal_count('1m')}")
            self.gui.emit(f"[STATUS] ⏰ 上次更新: {stat_1m.get('last_update', '無')}")
            
            if stat_1m.get('locked_at'):
                self.gui.emit(f"[STATUS] 🚫 被鎖時間: {stat_1m['locked_at']}")
            if stat_1m.get('unlock_time'):
                self.gui.emit(f"[STATUS] 🔓 預計解鎖: {stat_1m['unlock_time']}")
                
            # 顯示其他時間框架
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
            
    def reset_all_weights(self):
        """重置所有時間框架的權重設定"""
        try:
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
        
    def convert_interval_to_api_format(self, interval_display: str) -> str:
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
        
    def apply_saved_layout(self):
        """載入儲存的佈局"""
        self.gui.utils.load_and_apply_layout(self._layout_file)
