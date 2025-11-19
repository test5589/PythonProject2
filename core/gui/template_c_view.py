"""template_c_view.py - 模板 C（回補摘要）畫面渲染模組"""

from datetime import datetime as _dt, timezone, timedelta


class TemplateCView:
    def __init__(self, gui):
        self.gui = gui

    def update_backfill_template(self, summary: dict) -> None:
        gui = self.gui

        gui.backfill_summary_cache = summary or {}

        if getattr(gui, "current_template", "A") != "C":
            return

        try:
            self.render_from_cache()
        except Exception:
            pass

    def render_from_cache(self) -> None:
        gui = self.gui

        summary = getattr(gui, "backfill_summary_cache", None) or {}
        if not summary:
            return

        total = summary.get("total", 0)
        success = summary.get("success", 0)
        failed = summary.get("failed", 0)
        skipped = summary.get("skipped", 0)
        val_err = summary.get("validation_errors", 0)
        ins_err = summary.get("insert_errors", 0)
        other_err = summary.get("other_errors", 0)
        finished_at = summary.get("finished_at")
        symbols_info = summary.get("symbols") or {}

        try:
            gui._update_dynamic_field("C_GLOBAL", "total_symbols", str(total))
            gui._update_dynamic_field("C_GLOBAL", "success_count", str(success))
            gui._update_dynamic_field("C_GLOBAL", "failed_count", str(failed))
            gui._update_dynamic_field("C_GLOBAL", "skipped_count", str(skipped))
        except Exception:
            pass

        try:
            gui._update_dynamic_field("C_GLOBAL", "validation_errors", str(val_err))
            gui._update_dynamic_field("C_GLOBAL", "insert_errors", str(ins_err))
            gui._update_dynamic_field("C_GLOBAL", "other_errors", str(other_err))
        except Exception:
            pass

        try:
            if isinstance(finished_at, _dt):
                tw_tz = timezone(timedelta(hours=8))
                finished_str = finished_at.astimezone(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
            else:
                finished_str = str(finished_at) if finished_at else ""
            gui._update_dynamic_field("C_GLOBAL", "finished_at", finished_str)
        except Exception:
            pass

        try:
            from config.trading_config import TradingConfig
            symbols = TradingConfig.SUPPORTED_SYMBOLS
        except Exception:
            symbols = []

        for sym in symbols:
            info = symbols_info.get(sym)
            if not info:
                continue

            status = str(info.get("status", ""))
            validation = str(info.get("validation", ""))
            risk = str(info.get("risk", ""))
            note = str(info.get("note", ""))

            try:
                gui._update_dynamic_field(sym, "c_status", status)
                gui._update_dynamic_field(sym, "c_validation", validation)
                gui._update_dynamic_field(sym, "c_risk", risk)
                gui._update_dynamic_field(sym, "c_note", note)
            except Exception:
                continue

        try:
            gui._schedule_render()
        except Exception:
            pass
