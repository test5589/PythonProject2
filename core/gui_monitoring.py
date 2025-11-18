"""gui_monitoring.py - 監控功能模組 (1秒監控控制、WebSocket 啟停)"""

import threading
import time
from tkinter import messagebox
from modules.monitors.multi_symbol_monitor import get_multi_symbol_monitor
from modules.utils.logger import get_logger

logger = get_logger("monitor")


class GUIMonitoring:
    def __init__(self, gui):
        self.gui = gui
        self._ws_thread = None
        self._ws_running = False
        self._multi_monitor = get_multi_symbol_monitor(progress_cb=gui.emit)

    # ======== 啟動 1秒監控（多貨幣對） ========
    def start_ws(self):
        gui = self.gui
        category = gui.controls.category_entry.get()

        if not category:
            messagebox.showerror("錯誤", "請填寫資產分類")
            return

        if self._ws_running:
            messagebox.showinfo("提示", "多貨幣對監控已在執行中")
            return

        # 啟動所有貨幣對監控
        if self._multi_monitor.start_all_symbols_1s(category):
            self._ws_running = True
            gui.controls.ws_start_btn.config(state="disabled")
            gui.controls.ws_stop_btn.config(state="normal")
            gui.emit("🟢 多貨幣對一秒監控已啟動")
            # 紀錄本次監控開始時間
            if hasattr(gui, "on_monitor_started"):
                try:
                    gui.on_monitor_started()
                except Exception:
                    pass
        else:
            messagebox.showerror("錯誤", "啟動多貨幣對監控失敗")

    # ======== 停止 1秒監控（多貨幣對） ========
    def stop_ws(self):
        gui = self.gui
        if not self._ws_running:
            gui.emit("⏹️ 無監控執行中")
            return

        try:
            if self._multi_monitor.stop_all_symbols_1s():
                self._ws_running = False
                gui.emit("⛔ 多貨幣對一秒監控已停止")
                gui.controls.ws_start_btn.config(state="normal")
                gui.controls.ws_stop_btn.config(state="disabled")
                # 紀錄本次監控結束時間
                if hasattr(gui, "on_monitor_stopped"):
                    try:
                        gui.on_monitor_stopped()
                    except Exception:
                        pass
            else:
                gui.emit("❌ 停止監控失敗")
        except Exception as e:
            gui.emit(f"❌ 停止監控時出錯: {e}")
            logger.error(f"WebSocket 停止錯誤: {e}")
