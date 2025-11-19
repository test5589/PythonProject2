"""monitor_message_handler.py - 1 秒監控訊息解析與統計輔助模組"""

from datetime import datetime, timezone, timedelta
import re

from core.gui.monitor_board_template import DYNAMIC_FIELD_SLOTS


class MonitorMessageHandler:
    """負責處理 1 秒監控相關訊息的輔助類別。

    將原本 MainGUI 中與 1 秒監控訊息解析、分類與統計有關的邏輯集中到此，
    MainGUI 只需在 Tk 主執行緒中呼叫對應方法。
    """

    def __init__(self, gui):
        self.gui = gui

    # ---- 對外入口 ----
    def handle_message(self, msg: str):
        gui = self.gui
        try:
            kind = self._classify_monitor_msg(msg)
            if kind is not None:
                self.increment_summary(kind)

            if "🟢 1s 寫入" in msg:
                self._handle_1s_message(msg)

            gui._schedule_render()
        except Exception:
            pass

    # ---- 單一訊息處理 ----
    def _handle_1s_message(self, msg: str):
        gui = self.gui
        try:
            symbol = None
            if msg.startswith("[") and "]" in msg:
                end = msg.find("]")
                if end > 1:
                    symbol = msg[1:end]
            if not symbol:
                return

            self._update_symbol_1s_block(symbol, msg)
        except Exception:
            pass

    def _update_symbol_1s_block(self, symbol: str, raw_msg: str):
        gui = self.gui

        if (symbol, "now_time") not in DYNAMIC_FIELD_SLOTS:
            return

        try:
            now_local = datetime.now(tz=timezone(timedelta(hours=8)))
            now_str = now_local.strftime("%y/%m/%d %H:%M:%S")
        except Exception:
            now_str = ""
        gui._update_dynamic_field(symbol, "now_time", now_str)

        local_ts_str = ""
        data_source = ""
        total_str = ""

        try:
            core = raw_msg
            if raw_msg.startswith("[") and "]" in raw_msg:
                end = raw_msg.find("]")
                if end > 1:
                    core = raw_msg[end + 1 :].strip()

            m = re.search(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\+\d{2}:\d{2}", core)
            if m is not None:
                ts_token = m.group(0)
                dt_utc = datetime.fromisoformat(ts_token)
                dt_local = dt_utc.astimezone(timezone(timedelta(hours=8)))
                local_ts_str = dt_local.strftime("%y/%m/%d %H:%M:%S")

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

        stats = getattr(gui, "session_symbol_stats", None)
        if stats is None:
            stats = {}
            gui.session_symbol_stats = stats
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

        gui._update_dynamic_field(symbol, ts_field, local_ts_str)
        gui._update_dynamic_field(symbol, ds_field, data_source)
        gui._update_dynamic_field(symbol, total_field, total_str)

    # ---- 訊息分類與統計 ----
    def _classify_monitor_msg(self, msg: str):
        if not msg:
            return None

        if "❌" in msg:
            return "alert"
        if "⚠️ 本次 1s 收集共有" in msg and "寫入失敗" in msg:
            return "alert"

        if "⚪ [假假警報]" in msg:
            return "false_alert"
        if "⚠️" in msg:
            return "false_alert"

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

        if "🟢 1s 寫入" in msg:
            return "log"

        return "log"

    def increment_summary(self, kind: str, delta: int = 1):
        """對外提供的統計累加介面，供其他模組（例如 duplicate skip）呼叫。"""

        self._increment_summary(kind, delta)

    def _increment_summary(self, kind: str, delta: int = 1):
        gui = self.gui

        if not kind:
            return

        try:
            summary = getattr(gui, "monitor_summary", None)
            if summary is None:
                summary = {"alert": 0, "false_alert": 0, "system": 0, "log": 0}
                gui.monitor_summary = summary
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
            value = str(gui.monitor_summary.get(kind, 0))
            gui._update_dynamic_field("GLOBAL", field, value)
        except Exception:
            pass
