"""gui_main.py - 主視窗與初始化（原 Gui.py 的核心入口）"""

import sys
import os
import re
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timezone, timedelta
# 在這裡插入 ↓↓↓
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from modules.utils.database import init_db
from modules.utils.database.stats_collector import set_duplicate_skip_hook
from core.feature_panel import FeaturePanel
from core.gui.layout_config import (
    LOG_TEXT_HEIGHT,
    LOG_TEXT_WIDTH,
    LOG_TEXT_FONT_FAMILY,
    LOG_TEXT_FONT_SIZE,
    LOG_TEXT_PADX,
    LOG_TEXT_PADY,
)
from core.gui.gui_log_manager import GuiLogManager
from core.gui.monitor_board_template import (
    apply_template,
    MAX_SYMBOLS,
    LINES_PER_SYMBOL,
    DYNAMIC_FIELD_SLOTS,
)

# 子模組
from core.gui_controls import GUIControls
from core.gui_backfill import GUIBackfill
from core.gui_monitoring import GUIMonitoring
from core.gui_utils import GUIUtils


class MainGUI:
    """主 GUI 類別，負責初始化整個應用與模組整合"""
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Data Console")
        # 調整初始視窗大小：寬度回到 ，高度改為 
        self.root.geometry("750x700")

        # ---- 基礎屬性與狀態變數 ----
        self.overwrite_real_preference = None  # 覆蓋 real 資料設定
        self.overwrite_asked_count = 0
        self.edit_mode = False  # 是否處於版面編輯模式
        self._layout_backup = {}
        self._layout_preview = {}
        self._btn_click_blockers = {}
        self._buttons = []
        self._button_keys = {}
        # 1 秒監控面板狀態：{ symbol: { 'real': line_str, 'real_no-trade-fill': line_str } }
        self.monitor_panel_state = {}
        # 1 秒監控統計總覽：模板A 第 1 行的四個計數
        self.monitor_summary = {"alert": 0, "false_alert": 0, "system": 0, "log": 0}
        self.monitor_start_dt = None
        self.monitor_end_dt = None
        self.monitor_start_time_str = ""
        self.monitor_end_time_str = ""
        self.session_symbol_stats = {}
        # Grid 模板設定：預設可見 25 行，最多擴充到 200 行，每行使用 LOG_TEXT_WIDTH 格
        self.visible_rows = 25
        self.max_extra_rows = 175  # 200 - 25
        self.grid_rows = self.visible_rows + self.max_extra_rows  # 200 行
        self.grid_cols = LOG_TEXT_WIDTH
        self._init_grid()
        self._render_interval_ms = 100
        self._render_pending = False
        
        # ---- GUI日誌管理配置 ----
        self.max_log_lines = 2000  # GUI最多顯示2000行
        # GUI 目前執行期間的暫存日誌（關閉視窗會清空）
        self.temp_log_file = "data/temp/gui_session.log"
        # 監控模板 A 的統計結果長期保存檔（不會在關閉時刪除）
        self.monitor_summary_file = "data/monitor_summary.log"
        self._setup_temp_log()
        
        # ---- 提前建立 compact_var（emit 會用到）----
        self.compact_var = tk.BooleanVar(value=False)

        # ---- GUI LOG 管理器 ----
        self.gui_log_manager = GuiLogManager(self.log)

        # ---- 註冊 stats_collector duplicate skip hook（目前只用於 BTCUSDT 區塊）----
        try:
            set_duplicate_skip_hook(self._on_duplicate_skip)
        except Exception:
            # hook 失敗不影響主要功能
            pass

        # ---- DB 初始化 ----
        try:
            init_db()
        except Exception as e:
            print(f"DB 初始化失敗: {e}")

        # ---- 組件模組初始化 ----
        self.utils = GUIUtils(self)
        self.backfill = GUIBackfill(self)
        self.monitor = GUIMonitoring(self)
        self.controls = GUIControls(self)

        # ---- 進度條組件（階段2優化）----
        from core.gui_progress_bar import BackfillProgressBar
        self.progress_bar = BackfillProgressBar(root)
        self.progress_bar.hide()  # 初始隱藏
        
        # 建立含垂直捲軸的 LOG 區域
        log_frame = ttk.Frame(root)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=LOG_TEXT_PADX, pady=LOG_TEXT_PADY)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_frame,
            height=LOG_TEXT_HEIGHT,
            width=LOG_TEXT_WIDTH,
            bg="#111",
            fg="#0f0",
            insertbackground="white",
            font=(LOG_TEXT_FONT_FAMILY, LOG_TEXT_FONT_SIZE),
            yscrollcommand=scrollbar.set,
            state="disabled",  # 使用者不可直接編輯，僅程式可更新
        )
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        # 套用靜態模板（由 core/gui/monitor_board_template.py 定義）
        try:
            apply_template(self)
        except Exception:
            pass

        # 啟動時先渲染整個格子畫板（140 行 × 50 列）
        self._render_grid()

        # ---- 功能面板 ----
        FeaturePanel(root, self)
        
        # ---- 註冊關閉事件處理 ----
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    # ======= GUI日誌管理 =======
    def _setup_temp_log(self):
        """初始化臨時日誌文件，重啟時清空"""
        import os
        os.makedirs("data/temp", exist_ok=True)
        os.makedirs("data", exist_ok=True)
        # 重啟時清空舊的暫存日誌，但保留 monitor_summary_file
        if os.path.exists(self.temp_log_file):
            os.remove(self.temp_log_file)
    
    def _on_closing(self):
        """程序關閉時的清理工作"""
        import os
        # 清空本次 GUI session 的暫存日誌（保留長期統計檔 monitor_summary_file）
        if os.path.exists(self.temp_log_file):
            os.remove(self.temp_log_file)
        self.root.destroy()
    
    # ======= 通用輸出 =======
    def log(self, msg: str):
        """在主日誌視窗顯示訊息（限制行數+臨時存儲）"""
        import os
        from datetime import datetime
        
        # 寫入臨時日誌文件
        try:
            with open(self.temp_log_file, 'a', encoding='utf-8') as f:
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                f.write(f"[{timestamp}] {msg}\n")
        except Exception:
            pass

    # ======= Grid 模板管理 (50x50) =======
    def _init_grid(self):
        self.grid_lines = [" " * self.grid_cols for _ in range(self.grid_rows)]
        self._dirty_rows = set(range(self.grid_rows))

    def _set_grid_row(self, row_index, text):
        if not (0 <= row_index < self.grid_rows):
            return
        if text is None:
            text = ""
        if len(text) > self.grid_cols:
            line = text[: self.grid_cols]
        else:
            line = text.ljust(self.grid_cols)
        self.grid_lines[row_index] = line
        if hasattr(self, "_dirty_rows"):
            self._dirty_rows.add(row_index)

    def _set_grid_segment(self, row_index, col_start, text):
        if not (0 <= row_index < self.grid_rows):
            return
        if text is None:
            return
        if col_start < 0 or col_start >= self.grid_cols:
            return
        row = self.grid_lines[row_index]
        if len(row) < self.grid_cols:
            row = row.ljust(self.grid_cols)
        chars = list(row)
        for i, ch in enumerate(text):
            cidx = col_start + i
            if cidx >= self.grid_cols:
                break
            chars[cidx] = ch
        self.grid_lines[row_index] = "".join(chars)
        if hasattr(self, "_dirty_rows"):
            self._dirty_rows.add(row_index)

    def _render_grid(self):
        if not hasattr(self, "log_text"):
            return

        # 記住目前的捲動位置，避免每次重繪時滑軌跳動
        try:
            y_start, _ = self.log_text.yview()
        except Exception:
            y_start = None

        dirty_rows = getattr(self, "_dirty_rows", None)
        if not dirty_rows:
            return

        # 暫時開啟編輯權限供程式寫入
        self.log_text.configure(state="normal")

        # 確保 Text 內至少有 grid_rows 行，避免在重繪時變動行數
        try:
            total_lines = int(self.log_text.index("end-1c").split(".")[0])
        except Exception:
            total_lines = 0

        if total_lines < self.grid_rows:
            # 不足的行數補空行，之後只會在原位置覆寫，不再增刪行
            for _ in range(self.grid_rows - total_lines):
                self.log_text.insert(tk.END, "\n")

        # 只更新有變動的行，避免整個畫面重繪
        for idx in sorted(dirty_rows):
            if not (0 <= idx < self.grid_rows):
                continue
            row = idx + 1  # Text 的行號從 1 開始
            start_index = f"{row}.0"
            end_index = f"{row}.end"
            line = self.grid_lines[idx]
            self.log_text.delete(start_index, end_index)
            self.log_text.insert(start_index, line)

        self._dirty_rows.clear()

        # 恢復原本的捲動位置
        if y_start is not None:
            try:
                self.log_text.yview_moveto(y_start)
            except Exception:
                pass

        # 重繪完成後再次鎖定，避免使用者手動刪改內容
        self.log_text.configure(state="disabled")

    def _schedule_render(self):
        if getattr(self, "_render_pending", False):
            return
        self._render_pending = True
        try:
            self.root.after(self._render_interval_ms, self._flush_render)
        except Exception:
            self._render_pending = False

    def _flush_render(self):
        self._render_pending = False
        self._render_grid()

    def emit(self, msg: str):
        """統一日誌輸出介面：處理 1 秒監控與相關提示訊息。

        注意：Tk 只能在主執行緒操作，因此這裡只排程，實際更新在 _handle_monitor_message 中執行。
        """

        # 將訊息丟回 Tk 主執行緒處理，避免跨執行緒操作 Text 導致底層記憶體錯誤
        try:
            self.root.after(0, lambda m=msg: self._handle_monitor_message(m))
        except Exception:
            pass

    def _handle_monitor_message(self, msg: str):
        """在 Tk 主執行緒中處理所有 1 秒監控相關訊息：

        1) 先分類並更新模板A的四個總覽計數。
        2) 若為 🟢 1s 寫入 訊息，再更新對應貨幣對區塊。
        3) 統一排程一次重繪（帶有更新節流機制）。
        """

        try:
            kind = self._classify_monitor_msg(msg)
            if kind is not None:
                self._increment_summary(kind)

            if "🟢 1s 寫入" in msg:
                self._handle_1s_message(msg)

            self._schedule_render()
        except Exception:
            # 出錯時忽略，不影響其他功能
            pass

    def _handle_1s_message(self, msg: str):
        """在 Tk 主執行緒中處理 1 秒監控訊息，更新對應貨幣對區塊。"""

        try:
            # 解析開頭的 [SYMBOL]
            symbol = None
            if msg.startswith("[") and "]" in msg:
                end = msg.find("]")
                if end > 1:
                    symbol = msg[1:end]
            if not symbol:
                return

            self._update_symbol_1s_block(symbol, msg)
        except Exception:
            # 出錯時忽略，不影響其他功能
            pass

    # ======= 通用：單一貨幣對 1 秒監控區塊更新 =======
    def _update_symbol_1s_block(self, symbol: str, raw_msg: str):
        """解析指定 SYMBOL 的 1 秒監控訊息，更新該貨幣對區塊中的 1 秒寫入與 NOW 行。"""

        if (symbol, "now_time") not in DYNAMIC_FIELD_SLOTS:
            return

        # NOW 行（UTC+8 現在時間）
        try:
            now_local = datetime.now(tz=timezone(timedelta(hours=8)))
            now_str = now_local.strftime("%y/%m/%d %H:%M:%S")
        except Exception:
            now_str = ""
        self._update_dynamic_field(symbol, "now_time", now_str)

        local_ts_str = ""
        data_source = ""
        total_str = ""

        try:
            # 移除前綴 [SYMBOL]
            core = raw_msg
            if raw_msg.startswith("[") and "]" in raw_msg:
                end = raw_msg.find("]")
                if end > 1:
                    core = raw_msg[end + 1 :].strip()

            # 嘗試解析完整時間戳（例如 '2025-11-18 18:58:01+00:00'）
            m = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+\d{2}:\d{2}", core)
            if m is not None:
                ts_token = m.group(0)
                dt_utc = datetime.fromisoformat(ts_token)
                dt_local = dt_utc.astimezone(timezone(timedelta(hours=8)))
                local_ts_str = dt_local.strftime("%y/%m/%d %H:%M:%S")

            # 解析 data_source 與 總共 N
            if "data_source=" in core:
                _, tail = core.split("data_source=", 1)
                if "(總共" in tail:
                    src_part, count_part = tail.split("(總共", 1)
                    data_source = src_part.strip()
                    digits = "".join(ch for ch in count_part if ch.isdigit())
                    total_str = digits
        except Exception:
            pass

        if not data_source:
            data_source = "real"
        if not total_str:
            total_str = "?"
        stats = getattr(self, "session_symbol_stats", None)
        if stats is None:
            stats = {}
            self.session_symbol_stats = stats
        sym_stats = stats.setdefault(symbol, {"real": 0, "fill": 0, "other": 0})
        if data_source == "real":
            sym_stats["real"] += 1
        elif data_source == "real_no-trade-fill":
            sym_stats["fill"] += 1
        else:
            sym_stats["other"] += 1

        if data_source == "real_no-trade-fill":
            ts_field = "fill_ts"
            ds_field = "fill_data_source"
            total_field = "fill_total"
        else:
            ts_field = "real_ts"
            ds_field = "real_data_source"
            total_field = "real_total"

        self._update_dynamic_field(symbol, ts_field, local_ts_str)
        self._update_dynamic_field(symbol, ds_field, data_source)
        self._update_dynamic_field(symbol, total_field, total_str)

    def _update_dynamic_field(self, symbol: str, field_name: str, value: str):
        key = (symbol, field_name)
        slot = DYNAMIC_FIELD_SLOTS.get(key)
        if not slot:
            return
        row, col, width = slot
        if value is None:
            value = ""
        text = value[:width].ljust(width)
        row_index = row - 1
        col_start = col - 1
        self._set_grid_segment(row_index, col_start, text)

    def _classify_monitor_msg(self, msg: str):
        """將 1 秒監控相關訊息分類為 警報 / 假警報 / 系統提示 / 一般 LOG。"""

        if not msg:
            return None

        # 真正錯誤：含有 ❌ 或 1s 收集寫入失敗總結
        if "❌" in msg:
            return "alert"
        if "⚠️ 本次 1s 收集共有" in msg and "寫入失敗" in msg:
            return "alert"

        # 假警報 / 低優先異常：一般⚠️與假假警報
        if "⚪ [假假警報]" in msg:
            return "false_alert"
        if "⚠️" in msg:
            return "false_alert"

        # 系統提示：啟停、彙總、WS 狀態等
        system_tags = (
            "🚀",
            "🎉",
            "🛑",
            "⛔",
            "ℹ️ 1s 收集結束",
            "✅ 1s 收集結束",
            "🟢 多貨幣對一秒監控已啟動",
            "⏹️ 無監控執行中",
            "🟢 WS 已連線",
            "🔌 WS 已關閉",
        )
        if any(tag in msg for tag in system_tags):
            return "system"

        # 正常 1s 寫入
        if "🟢 1s 寫入" in msg:
            return "log"

        # 其他仍視為一般 LOG
        return "log"

    def _increment_summary(self, kind: str, delta: int = 1):
        """根據分類更新模板A第 1 行的四個計數欄位。"""

        if not kind:
            return

        try:
            summary = getattr(self, "monitor_summary", None)
            if summary is None:
                summary = {"alert": 0, "false_alert": 0, "system": 0, "log": 0}
                self.monitor_summary = summary
            if kind not in summary:
                return
            summary[kind] += delta
        except Exception:
            return

        field_map = {
            "alert": "alert_count",
            "false_alert": "false_alert_count",
            "system": "system_hint_count",
            "log": "log_count",
        }
        field = field_map.get(kind)
        if not field:
            return

        try:
            value = str(self.monitor_summary.get(kind, 0))
            self._update_dynamic_field("GLOBAL", field, value)
        except Exception:
            pass

    def on_monitor_started(self):
        """由 GUIMonitoring 在啟動多貨幣對 1 秒監控成功時呼叫：更新開始時間欄位。"""

        try:
            now_local = datetime.now(tz=timezone(timedelta(hours=8)))
            now_str = now_local.strftime("%y/%m/%d %H:%M:%S")
        except Exception:
            now_local = None
            now_str = ""

        self.monitor_start_dt = now_local
        self.monitor_end_dt = None
        self.monitor_start_time_str = now_str
        self.monitor_end_time_str = ""
        self.session_symbol_stats = {}
        self.monitor_summary = {"alert": 0, "false_alert": 0, "system": 0, "log": 0}
        summary_fields = {
            "alert": "alert_count",
            "false_alert": "false_alert_count",
            "system": "system_hint_count",
            "log": "log_count",
        }
        for kind, field in summary_fields.items():
            try:
                self._update_dynamic_field("GLOBAL", field, "0")
            except Exception:
                pass

        # 寫入開始時間，並清空結束時間，代表目前監控中
        self._update_dynamic_field("GLOBAL", "monitor_start", now_str)
        self._update_dynamic_field("GLOBAL", "monitor_end", "")
        self._schedule_render()

    def on_monitor_stopped(self):
        """由 GUIMonitoring 在停止多貨幣對 1 秒監控成功時呼叫：更新結束時間欄位。"""

        try:
            now_local = datetime.now(tz=timezone(timedelta(hours=8)))
            now_str = now_local.strftime("%y/%m/%d %H:%M:%S")
        except Exception:
            now_local = None
            now_str = ""

        self.monitor_end_dt = now_local
        self.monitor_end_time_str = now_str
        self._update_dynamic_field("GLOBAL", "monitor_end", now_str)
        self._schedule_render()
        try:
            self._log_monitor_summary()
        except Exception:
            pass

    def _log_monitor_summary(self):
        try:
            start_dt = getattr(self, "monitor_start_dt", None)
            end_dt = getattr(self, "monitor_end_dt", None)
            start_str = getattr(self, "monitor_start_time_str", "") or ""
            end_str = getattr(self, "monitor_end_time_str", "") or ""
            if not start_str and start_dt is not None:
                try:
                    start_str = start_dt.strftime("%y/%m/%d %H:%M:%S")
                except Exception:
                    start_str = ""
            if not end_str and end_dt is not None:
                try:
                    end_str = end_dt.strftime("%y/%m/%d %H:%M:%S")
                except Exception:
                    end_str = ""

            if start_dt is not None and end_dt is not None:
                try:
                    total_seconds = int((end_dt - start_dt).total_seconds())
                    duration_str = f"{total_seconds} 秒"
                except Exception:
                    duration_str = "未知"
            else:
                duration_str = "未知"

            summary = getattr(self, "monitor_summary", {}) or {}
            alert = summary.get("alert", 0)
            false_alert = summary.get("false_alert", 0)
            system = summary.get("system", 0)
            log_count = summary.get("log", 0)

            lines = []
            header = (
                f"[MonitorSummary] 開始={start_str}, 結束={end_str}, 持續={duration_str}, "
                f"警報={alert}, 假警報={false_alert}, 系統提示={system}, LOG={log_count}"
            )
            lines.append(header)

            stats = getattr(self, "session_symbol_stats", {}) or {}
            if stats:
                for sym in sorted(stats.keys()):
                    s = stats.get(sym, {}) or {}
                    real = s.get("real", 0)
                    fill = s.get("fill", 0)
                    other = s.get("other", 0)
                    line = f"[MonitorSummary] {sym}: real={real}, fill={fill}"
                    if other:
                        line += f", other={other}"
                    lines.append(line)

            for line in lines:
                self.log(line)

            try:
                import os
                os.makedirs("data", exist_ok=True)
                with open(self.monitor_summary_file, "a", encoding="utf-8") as f:
                    for line in lines:
                        f.write(line + "\n")
            except Exception:
                pass
        except Exception:
            pass

    def _on_duplicate_skip(self, info: dict):
        """由 stats_collector 呼叫的 hook：只處理 BTCUSDT 的重複跳過資訊。"""
        try:
            # 從資料庫線程切回 GUI 主線程（Tk 只能在主執行緒操作）
            self.root.after(0, lambda i=info: self._handle_duplicate_skip(i))
        except Exception:
            pass

    def _handle_duplicate_skip(self, info: dict):
        """在 Tk 主執行緒中處理重複跳過事件，更新對應貨幣對區塊的第 5~7 行。"""

        try:
            symbol = info.get("symbol")
            if not symbol:
                return

            self._update_symbol_duplicate_block(info)
            # 重複跳過視為低優先級假警報
            self._increment_summary("false_alert")
            self._schedule_render()
        except Exception:
            pass

    def _update_symbol_duplicate_block(self, info: dict):
        """更新指定貨幣對區塊中的 stats_collector 三行資訊。"""

        symbol = info.get("symbol", "")
        if not symbol:
            return
        if (symbol, "dup_now_time") not in DYNAMIC_FIELD_SLOTS:
            return

        count = info.get("count", 0)
        category = info.get("category", "")
        interval = info.get("interval", 0)
        readable_time = info.get("readable_time", "") or ""
        existing_source = info.get("existing_source", "") or ""
        new_source = info.get("new_source", "") or ""

        try:
            now_local = datetime.now(tz=timezone(timedelta(hours=8)))
            now_str = now_local.strftime("%y/%m/%d %H:%M:%S")
        except Exception:
            now_str = ""

        self._update_dynamic_field(symbol, "dup_now_time", now_str)
        self._update_dynamic_field(symbol, "dup_count", str(count))

        if interval:
            interval_str = f"{interval}s"
        else:
            interval_str = ""
        self._update_dynamic_field(symbol, "dup_interval", interval_str)

        self._update_dynamic_field(symbol, "dup_latest_ts", readable_time)
        self._update_dynamic_field(symbol, "dup_existing_source", existing_source)
        self._update_dynamic_field(symbol, "dup_new_source", new_source)

    # ======= 1 秒監控固定面板邏輯 =======
    def _update_monitor_panel(self, raw_msg: str):
        """解析 1 秒監控訊息，更新 monitor_panel_state，並重繪 log_text。

        目標顯示格式（GUI）：
        現在時間 | multi_monitor | INFO | [SYMBOL] 🟢 1s 寫入 SYMBOL 寫入時間 data_source=XXX(總共NN)
        """

        # 解析 symbol：訊息開頭的 [SYMBOL]
        symbol = None
        if raw_msg.startswith("[") and "]" in raw_msg:
            end = raw_msg.find("]")
            if end > 1:
                symbol = raw_msg[1:end]
        if not symbol:
            return

        # 判斷資料來源（real 或 real_no-trade-fill）
        try:
            _, tail = raw_msg.split("data_source=", 1)
        except ValueError:
            return

        if "(總共" not in tail:
            return

        source_name = tail.split("(總共", 1)[0].strip()

        # 更新狀態
        entry = self.monitor_panel_state.setdefault(symbol, {"real": None, "real_no-trade-fill": None})
        if source_name not in entry:
            # 未知來源先直接納入（以防未來多一種來源）
            entry[source_name] = None

        # 現在時間（GUI 端顯示用）
        try:
            now_local = datetime.now(tz=timezone(timedelta(hours=8)))
            now_str = now_local.strftime("%y/%m/%d %H:%M:%S")
        except Exception:
            now_str = ""  # 失敗就留空

        # 組裝一條 GUI 用的固定行：模仿終端機格式
        # 例：25/11/18 22:30:00 | multi_monitor | INFO | [BTCUSDT] 🟢 1s 寫入 BTCUSDT ...
        line = f"{now_str} | multi_monitor | INFO | {raw_msg}"
        entry[source_name] = line

        # 重繪整個面板（使用 50x50 grid 再渲染到 log_text）
        if not hasattr(self, "log_text"):
            return

        # 清空 grid 為空白
        self._init_grid()

        row_index = 0
        # 依 symbol 排序，且 real 在前、real_no-trade-fill 在後
        for sym in sorted(self.monitor_panel_state.keys()):
            row = self.monitor_panel_state[sym]
            real_line = row.get("real")
            if real_line and row_index < self.grid_rows:
                self._set_grid_row(row_index, real_line)
                row_index += 1
            fill_line = row.get("real_no-trade-fill")
            if fill_line and row_index < self.grid_rows:
                self._set_grid_row(row_index, fill_line)
                row_index += 1
            if row_index >= self.grid_rows:
                break

        self._render_grid()


# ============================================================
# ✅✅✅ 主程式入口 ✅✅✅
# 
# 這是唯一正確的程式啟動入口
# 啟動方式：python core/gui_main.py
# 
# ⚠️ 其他文件的 if __name__ 區塊已被移除或註釋
# ⚠️ 請勿使用其他文件作為程式入口
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    MainGUI(root)
    root.mainloop()
