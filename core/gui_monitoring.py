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

        # 1. 檢查是否為模板 A（監控模板）
        current_template = getattr(gui, "current_template", "A")
        if current_template != "A":
            result = messagebox.askyesno(
                "模板檢查",
                "啟動 1 秒監控建議使用【模板 A】。\n"
                "當前模板非 A，可能會導致顯示異常。\n\n"
                "是否自動切換至模板 A 並繼續？"
            )
            if result:
                if hasattr(gui, "set_monitor_template"):
                    gui.set_monitor_template("A")
            else:
                return

        # 2. 讀取使用者選擇的數量限制
        max_symbols = 5  # 預設值
        # [DESIGN NOTE] GUI 版 1 秒監控目前固定最多 5 檔，候選名單來自模板 A 的前 20 檔。
        # 若要放寬監控數量或改變模板 A 的排列，需同步調整 monitor_board_template.py 與這裡的邏輯。

        # 3. 準備模板 A 的候選名單（前 20 個）
        # 這裡必須與 monitor_board_template.py 的邏輯一致
        from config.trading_config import TradingConfig
        template_a_candidates = TradingConfig.SUPPORTED_SYMBOLS[:20]

        # 4. 彈出選擇視窗
        from core.gui_symbol_selector import select_symbols_for_backfill
        
        gui.emit(f"💡 請從模板 A 的名單中選擇最多 {max_symbols} 個貨幣對進行監控...")
        
        selected_symbols = select_symbols_for_backfill(
            parent=gui.root,
            category=category,
            custom_available_symbols=template_a_candidates,
            max_selection=max_symbols
        )

        if not selected_symbols:
            gui.emit("❌ 已取消啟動監控")
            return

        # 更新顯示的監控貨幣對數為實際選擇數量
        try:
            controls = getattr(gui, 'controls', None)
            if controls is not None and hasattr(controls, 'monitor_symbol_limit_var'):
                controls.monitor_symbol_limit_var.set(str(len(selected_symbols)))
        except Exception:
            pass

        # 啟動指定貨幣對監控
        # 注意：start_all_symbols_1s 會再次檢查 max_symbols 和 specific_symbols 的邏輯
        if self._multi_monitor.start_all_symbols_1s(category, max_symbols=max_symbols, specific_symbols=selected_symbols):
            self._ws_running = True
            gui.controls.ws_start_btn.config(state="disabled")
            gui.controls.ws_stop_btn.config(state="normal")
            gui.emit(f"🟢 多貨幣對一秒監控已啟動（{len(selected_symbols)} 個）")
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
                # [DESIGN NOTE] GUI 與 Web 共用同一個 MultiSymbolMonitor；
                # 停止時同時還原 GUI 按鈕狀態、監控貨幣對顯示與監控統計 on_monitor_stopped。
                # 重設顯示的監控貨幣對數為待選
                try:
                    controls = getattr(gui, 'controls', None)
                    if controls is not None and hasattr(controls, 'monitor_symbol_limit_var'):
                        controls.monitor_symbol_limit_var.set("(待選)")
                except Exception:
                    pass
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
