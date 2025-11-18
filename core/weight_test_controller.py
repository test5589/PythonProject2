"""
權重測試控制器
專門處理API權重測試的邏輯，從gui_controls.py中拆分出來
"""

import time
from datetime import datetime, timedelta
from typing import Optional


class WeightTestController:
    """權重測試控制器"""
    
    def __init__(self, gui_instance):
        self.gui = gui_instance
        self.is_testing = False
        self.test_thread = None
        
    def start_weight_test(self) -> bool:
        """啟動權重測試"""
        if self.is_testing:
            self.gui.emit("[WEIGHT_TEST] ⚠️ 測試已在進行中")
            return False
            
        try:
            # 記錄測試開始
            self._log_test_start()
            
            # 獲取測試參數
            test_params = self._get_test_parameters()
            
            # 顯示測試信息
            self._display_test_info(test_params)
            
            # 啟動錨定時間引擎
            success = self._start_anchor_engine(test_params)
            
            if success:
                self.is_testing = True
                self.gui.emit("[WEIGHT_TEST] 🚀 權重測試已啟動")
                return True
            else:
                self.gui.emit("[WEIGHT_TEST] ❌ 權重測試啟動失敗")
                return False
                
        except Exception as e:
            self.gui.emit(f"[WEIGHT_TEST] ❌ 啟動測試時發生錯誤: {e}")
            return False
    
    def stop_weight_test(self) -> bool:
        """停止權重測試"""
        if not self.is_testing:
            self.gui.emit("[WEIGHT_TEST] ⚠️ 沒有正在進行的測試")
            return False
            
        try:
            # 停止錨定時間引擎
            self._stop_anchor_engine()
            
            # 停止權重測試引擎（如果存在）
            self._stop_weight_engine()
            
            self.is_testing = False
            self.gui.emit("[WEIGHT_TEST] 🛑 權重測試已完全停止")
            return True
            
        except Exception as e:
            self.gui.emit(f"[WEIGHT_TEST] ❌ 停止測試時發生錯誤: {e}")
            return False
    
    def _log_test_start(self):
        """記錄測試開始到日誌文件"""
        import os
        
        try:
            error_log_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_error.log")
            with open(error_log_path, "a", encoding="utf-8") as f:
                f.write(f"\n=== {datetime.now()} ===\n")
                f.write("整合權重測試開始（錨定時間 + 權重評估）\n")
        except Exception as e:
            self.gui.emit(f"[WEIGHT_TEST] ⚠️ 日誌記錄失敗: {e}")
    
    def _get_test_parameters(self) -> dict:
        """獲取測試參數"""
        # 取得當前選擇的貨幣對
        current_symbol = "BTCUSDT"  # 預設值
        if hasattr(self.gui.controls, 'symbol_entry') and self.gui.controls.symbol_entry.get():
            current_symbol = self.gui.controls.symbol_entry.get()
        elif hasattr(self.gui, 'symbol_entry') and self.gui.symbol_entry.get():
            current_symbol = self.gui.symbol_entry.get()
        
        # 取得當前選擇的時間框架（從K線時間段選項）
        current_timeframe = "1m"  # 預設值
        if hasattr(self.gui.controls, 'backfill_interval_combo') and self.gui.controls.backfill_interval_combo.get():
            selected_interval = self.gui.controls.backfill_interval_combo.get()
            # 轉換中文時間框架為API格式
            current_timeframe = self.gui.controls._convert_interval_to_api_format(selected_interval)
        
        # 取得錨定開始時間
        anchor_start_time = self._get_anchor_start_time()
        
        return {
            'symbol': current_symbol,
            'timeframe': current_timeframe,
            'start_time': anchor_start_time
        }
    
    def _get_anchor_start_time(self) -> datetime:
        """獲取錨定開始時間"""
        # 預設使用當前時間
        anchor_start_time = datetime.now().replace(second=0, microsecond=0)
        
        # 嘗試從GUI時間選擇器獲取時間
        try:
            controls = self.gui.controls
            if (hasattr(controls, 'sy') and hasattr(controls, 'sM') and 
                hasattr(controls, 'sd') and hasattr(controls, 'sh') and 
                hasattr(controls, 'su') and hasattr(controls, 'ss')):
                
                start_date = f"{controls.sy.get()}-{controls.sM.get()}-{controls.sd.get()}"
                start_time = f"{controls.sh.get()}:{controls.su.get()}:{controls.ss.get()}"
                selected_time = datetime.strptime(f"{start_date} {start_time}", "%Y-%m-%d %H:%M:%S")
                
                # 只有當選擇的時間是未來時間時才使用
                if selected_time > datetime.now():
                    anchor_start_time = selected_time
                    self.gui.emit(f"[WEIGHT_TEST] 📅 使用選擇的未來時間: {selected_time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    self.gui.emit(f"[WEIGHT_TEST] ⚠️ 選擇的時間已過期，使用當前時間")
        except Exception as e:
            self.gui.emit(f"[WEIGHT_TEST] ⚠️ 時間選擇器讀取失敗，使用當前時間: {e}")
        
        return anchor_start_time
    
    def _display_test_info(self, params: dict):
        """顯示測試信息"""
        self.gui.emit("[WEIGHT_TEST] 🎯 啟動整合權重測試系統...")
        self.gui.emit("[WEIGHT_TEST] 📋 功能：錨定時間機制 + API權重評估 + 多樣化請求測試")
        self.gui.emit(f"[WEIGHT_TEST] 🎯 測試貨幣對: {params['symbol']}")
        self.gui.emit(f"[WEIGHT_TEST] ⏰ 測試時間框架: {params['timeframe']}")
        self.gui.emit(f"[WEIGHT_TEST] 📅 錨定開始時間: {params['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
        self.gui.emit(f"[WEIGHT_TEST] ⏱️ 測試持續時間: 60分鐘")
        self.gui.emit(f"[WEIGHT_TEST] 🎯 預計結束時間: {(params['start_time'] + timedelta(minutes=60)).strftime('%Y-%m-%d %H:%M:%S')}")
        self.gui.emit("[WEIGHT_TEST] 🔄 策略: 多時間段 + 多交易對輪換，避免重複資料")
    
    def _start_anchor_engine(self, params: dict) -> bool:
        """啟動錨定時間引擎"""
        try:
            # 停止之前的測試
            self._stop_anchor_engine()
            time.sleep(1)
            
            # 啟動新的測試
            from modules.utils.anchor_time import get_anchor_time_engine
            anchor_engine = get_anchor_time_engine(self.gui.emit)
            
            # 設定測試參數
            anchor_engine.enable_capacity_test = True
            anchor_engine.enable_data_validation = True
            anchor_engine.current_stage_index = 0
            anchor_engine.max_successful_count = 0
            anchor_engine.api_lock_count = 0
            anchor_engine.duplicate_data_count = 0
            anchor_engine.received_timestamps.clear()
            
            # 重置索引
            anchor_engine.current_timeframe_index = 0
            anchor_engine.current_symbol_index = 0
            
            # 啟動測試
            anchor_engine.start_test(params['symbol'], params['timeframe'], params['start_time'])
            
            # 記錄到日誌文件
            try:
                import os
                error_log_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_error.log")
                with open(error_log_path, "a", encoding="utf-8") as f:
                    f.write(f"整合測試已啟動 - 貨幣對: {params['symbol']}, 時間框架: {params['timeframe']}\n")
                    f.write(f"錨定時間: {params['start_time'].strftime('%Y-%m-%d %H:%M:%S')}\n")
            except:
                pass
            
            return True
            
        except Exception as e:
            self.gui.emit(f"[WEIGHT_TEST] ❌ 錨定引擎啟動失敗: {e}")
            return False
    
    def _stop_anchor_engine(self):
        """停止錨定時間引擎"""
        try:
            from modules.utils.anchor_time import get_anchor_time_engine
            anchor_engine = get_anchor_time_engine(self.gui.emit)
            
            if anchor_engine.is_running:
                anchor_engine.stop_test()
                self.gui.emit("[WEIGHT_TEST] 🛑 錨定時間測試已停止")
        except Exception as e:
            self.gui.emit(f"[WEIGHT_TEST] ⚠️ 停止錨定引擎時發生錯誤: {e}")
    
    def _stop_weight_engine(self):
        """停止權重測試引擎（如果存在）"""
        try:
            from modules.utils.testing.weight_test_engine import get_weight_test_engine
            test_engine = get_weight_test_engine(self.gui.emit)
            
            if test_engine.is_running:
                test_engine.stop_test()
                self.gui.emit("[WEIGHT_TEST] 🛑 權重測試引擎已停止")
        except:
            pass  # 權重測試引擎可能不存在
    
    def get_test_status(self) -> dict:
        """獲取測試狀態"""
        try:
            from modules.utils.anchor_time import get_anchor_time_engine
            anchor_engine = get_anchor_time_engine(self.gui.emit)
            
            return {
                'is_running': anchor_engine.is_running,
                'max_successful_count': anchor_engine.max_successful_count,
                'api_lock_count': anchor_engine.api_lock_count,
                'duplicate_data_count': anchor_engine.duplicate_data_count,
                'total_requests': anchor_engine.validation_stats.get('total_requests', 0),
                'current_stage': anchor_engine.current_stage_index + 1,
                'total_stages': len(anchor_engine.test_stages)
            }
        except:
            return {
                'is_running': False,
                'max_successful_count': 0,
                'api_lock_count': 0,
                'duplicate_data_count': 0,
                'total_requests': 0,
                'current_stage': 0,
                'total_stages': 0
            }
