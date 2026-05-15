"""gui_main.py - 主視窗與初始化（原 Gui.py 的核心入口）"""

import sys
import os
import re
import json
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
    AVAILABLE_TEMPLATES,
)
from core.gui.monitor_message_handler import MonitorMessageHandler
from core.gui.grid_renderer import GridRenderer
from core.gui.template_b_view import TemplateBView
from core.gui.template_c_view import TemplateCView

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
        # 模板設定檔路徑與目前使用模板（預設為上次關閉時的模板，若失敗則為 "A"）
        self.template_config_file = os.path.join(PROJECT_ROOT, "data", "gui_template.json")
        self.current_template = self._load_current_template()
        # 最新 1 分鐘批量抓取驗證的摘要快取（模板 B 使用）
        self.latest_1m_summary = None
        self.latest_1m_fetch_stats = None
        self.latest_1m_retry_stats = None
        self.latest_1m_log_rotation = None
        # 回補任務摘要快取（模板 C 使用）
        self.backfill_summary_cache = None
        # Grid 模板設定：預設可見 25 行，最多擴充到 200 行，每行使用 LOG_TEXT_WIDTH 格
        self.visible_rows = 25
        self.max_extra_rows = 175  # 200 - 25
        self.grid_rows = self.visible_rows + self.max_extra_rows  # 200 行
        self.grid_cols = LOG_TEXT_WIDTH
        self._render_interval_ms = 100
        self._render_pending = False
        # Grid 渲染器
        self.grid_renderer = GridRenderer(self)
        self._init_grid()
        
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

        # ---- 1 秒監控訊息處理器 ----
        self.monitor_message_handler = MonitorMessageHandler(self)

        # ---- 模板 B / C 渲染器 ----
        self.template_b_view = TemplateBView(self)
        self.template_c_view = TemplateCView(self)

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
            apply_template(self, getattr(self, "current_template", "A"))
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
        """初始化臨時日誌文件目錄（不再自動清空舊檔）。"""
        import os
        os.makedirs("data/temp", exist_ok=True)
        os.makedirs("data", exist_ok=True)
    
    def _on_closing(self):
        """程序關閉時的清理工作"""
        try:
            self._save_current_template()
        except Exception:
            pass
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

    # ======= 模板管理（A/B 等） =======
    def _load_current_template(self) -> str:
        """從設定檔載入最後一次使用的模板代號，失敗則回傳 "A"。"""

        try:
            path = getattr(self, "template_config_file", None)
            if not path or not os.path.exists(path):
                return "A"
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            tpl = data.get("current_template")
            if tpl in AVAILABLE_TEMPLATES:
                return tpl
        except Exception:
            pass
        return "A"

    def _save_current_template(self) -> None:
        """將目前使用的模板代號寫入設定檔。"""

        try:
            path = getattr(self, "template_config_file", None)
            if not path:
                return
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tpl = getattr(self, "current_template", "A")
            data = {"current_template": tpl}
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_monitor_template(self, template_name: str) -> None:
        """切換 1 秒/批量監控模板（例如 A/B），並套用到畫面。"""

        if not template_name or template_name not in AVAILABLE_TEMPLATES:
            return

        if getattr(self, "current_template", None) == template_name:
            return

        self.current_template = template_name
        try:
            self._save_current_template()
            # 同步更新下拉選單顯示
            if hasattr(self, "controls") and hasattr(self.controls, "template_var"):
                try:
                    self.controls.template_var.set(template_name)
                except Exception:
                    pass
        except Exception:
            pass

        # 重新初始化格子並套用新模板
        try:
            self._init_grid()
            apply_template(self, template_name)
        except Exception:
            return

        # [DESIGN NOTE] 模板 B/C 的內容是從快取資料填入動態欄位，實作分別在 TemplateBView/TemplateCView 中。
        # 若調整模板版面或快取結構，需同時更新這兩個 view 類別與此處的套用流程。
        # 切到 B：若已有 1 分鐘批量摘要快取，套用到畫面
        if template_name == "B":
            try:
                self._render_template_b_from_cache()
            except Exception:
                pass
        elif template_name == "C":
            # 切到 C：若已有回補摘要快取，套用到畫面
            try:
                self._render_template_c_from_cache()
            except Exception:
                pass
        elif template_name == "A":
            # 切回 A：把目前的 summary/time 再寫到模板 A 的 GLOBAL 欄位
            try:
                summary = getattr(self, "monitor_summary", {}) or {}
                field_map = {
                    "alert": "alert_count",
                    "false_alert": "false_alert_count",
                    "system": "system_hint_count",
                    "log": "log_count",
                }
                for kind, field in field_map.items():
                    value = str(summary.get(kind, 0))
                    self._update_dynamic_field("GLOBAL", field, value)

                start = getattr(self, "monitor_start_time_str", "") or ""
                end = getattr(self, "monitor_end_time_str", "") or ""
                if start:
                    self._update_dynamic_field("GLOBAL", "monitor_start", start)
                if end:
                    self._update_dynamic_field("GLOBAL", "monitor_end", end)
            except Exception:
                pass

        try:
            self._schedule_render()
        except Exception:
            pass

    def update_latest_1m_template(
        self,
        summary: dict,
        fetch_calls: int,
        total_rows: int,
        conn_retries: int,
        timeout_retries: int,
        rotation_count: int,
    ) -> None:
        """更新模板 B 用的最新 1 分鐘批量抓取摘要快取，必要時重繪畫面。"""

        self.latest_1m_summary = summary
        self.latest_1m_fetch_stats = {
            "fetch_calls": fetch_calls,
            "total_rows": total_rows,
        }
        self.latest_1m_retry_stats = {
            "conn": conn_retries,
            "timeout": timeout_retries,
        }
        self.latest_1m_log_rotation = {
            "rotation_count": rotation_count,
        }

        if getattr(self, "current_template", "A") != "B":
            return

        try:
            self._render_template_b_from_cache()
        except Exception:
            pass

    def _render_template_b_from_cache(self) -> None:
        """根據快取的最新 1 分鐘摘要資料，將內容填入模板 B 的動態欄位。"""
        self.template_b_view.render_from_cache()

    def update_backfill_template(self, summary: dict) -> None:
        """更新模板 C 用的回補任務摘要快取，必要時重繪畫面。"""

        self.backfill_summary_cache = summary or {}

        if getattr(self, "current_template", "A") != "C":
            return

        try:
            self._render_template_c_from_cache()
        except Exception:
            pass

    def _render_template_c_from_cache(self) -> None:
        """根據快取的回補摘要資料，將內容填入模板 C 的動態欄位。"""
        self.template_c_view.render_from_cache()

    # ======= Grid 模板管理 (50x50) =======
    def _init_grid(self):
        self.grid_renderer.init_grid()

    def _set_grid_row(self, row_index, text):
        self.grid_renderer.set_row(row_index, text)

    def _set_grid_segment(self, row_index, col_start, text):
        self.grid_renderer.set_segment(row_index, col_start, text)

    def _render_grid(self):
        self.grid_renderer.render_grid()

    def _schedule_render(self):
        self.grid_renderer.schedule_render()

    def _flush_render(self):
        self.grid_renderer.flush_render()

    def emit(self, msg: str):
        """統一日誌輸出介面：處理 1 秒監控與相關提示訊息。

        注意：Tk 只能在主執行緒操作，因此這裡只排程，實際更新在 _handle_monitor_message 中執行。
        """

        # 將訊息丟回 Tk 主執行緒處理，避免跨執行緒操作 Text 導致底層記憶體錯誤
        try:
            self.root.after(0, lambda m=msg: self.monitor_message_handler.handle_message(m))
        except Exception:
            pass

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
        # [DESIGN NOTE] 依賴 MonitorMessageHandler 累計的 monitor_summary 與 session_symbol_stats 結果。
        # 若未來調整 1 秒訊息分類或統計邏輯，請確認此摘要輸出仍然正確。
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
            # [DESIGN NOTE] 這個 hook 會在資料庫背景執行緒被呼叫，
            # 一定要透過 root.after 切回主執行緒後再更新 GUI 狀態，避免 Tk thread-safety 問題。
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
            if hasattr(self, "monitor_message_handler"):
                try:
                    self.monitor_message_handler.increment_summary("false_alert")
                except Exception:
                    pass
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

        # [DESIGN NOTE] 這個固定面板使用獨立的 monitor_panel_state + GridRenderer，
        # 與模板 A 上顯示的 1 秒欄位屬於兩套視覺呈現邏輯；若未來統一版面或改成其他呈現方式，
        # 修改前建議先梳理兩者的關係，避免互相覆蓋畫面。

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
