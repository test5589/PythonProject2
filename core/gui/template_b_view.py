"""template_b_view.py - 模板 B（1 分鐘批量驗證）畫面渲染模組"""

from datetime import datetime as _dt, timezone, timedelta

from core.gui.monitor_board_template import MAX_SYMBOLS


class TemplateBView:
    def __init__(self, gui):
        self.gui = gui

    def update_latest_1m_template(
        self,
        summary: dict,
        fetch_calls: int,
        total_rows: int,
        conn_retries: int,
        timeout_retries: int,
        rotation_count: int,
    ) -> None:
        gui = self.gui

        gui.latest_1m_summary = summary
        gui.latest_1m_fetch_stats = {
            "fetch_calls": fetch_calls,
            "total_rows": total_rows,
        }
        gui.latest_1m_retry_stats = {
            "conn": conn_retries,
            "timeout": timeout_retries,
        }
        gui.latest_1m_log_rotation = {
            "rotation_count": rotation_count,
        }

        if getattr(gui, "current_template", "A") != "B":
            return

        try:
            self.render_from_cache()
        except Exception:
            pass

    def render_from_cache(self) -> None:
        gui = self.gui

        summary = getattr(gui, "latest_1m_summary", None)
        if not summary:
            return

        from config.trading_config import TradingConfig

        results = summary.get("results") or {}
        real_alerts = summary.get("real_alerts") or {}
        pseudo_alerts = summary.get("pseudo_alerts") or {}
        fully_ok = summary.get("fully_ok") or []
        start_time = summary.get("start_time")
        end_time = summary.get("end_time")

        fetch_stats = getattr(gui, "latest_1m_fetch_stats", None) or {}
        retry_stats = getattr(gui, "latest_1m_retry_stats", None) or {}
        log_rot = getattr(gui, "latest_1m_log_rotation", None) or {}

        try:
            gui._update_dynamic_field("B_GLOBAL", "real_alert_count", str(len(real_alerts)))
            gui._update_dynamic_field("B_GLOBAL", "pseudo_alert_count", str(len(pseudo_alerts)))
            gui._update_dynamic_field("B_GLOBAL", "ok_count", str(len(fully_ok)))
        except Exception:
            pass

        try:
            total_symbols = len(results)
            success_symbols = sum(1 for info in results.values() if (info or {}).get("api_fetched", 0) > 0)
            total_inserted = fetch_stats.get("total_rows")
            if total_inserted is None:
                total_inserted = ""
            gui._update_dynamic_field("B_GLOBAL", "total_symbols", str(total_symbols))
            gui._update_dynamic_field("B_GLOBAL", "success_symbols", str(success_symbols))
            gui._update_dynamic_field("B_GLOBAL", "total_inserted", str(total_inserted))
        except Exception:
            pass

        try:
            tw_tz = timezone(timedelta(hours=8))
            if isinstance(start_time, _dt):
                start_tw = start_time.astimezone(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
            else:
                start_tw = ""
            if isinstance(end_time, _dt):
                end_tw = end_time.astimezone(tw_tz).strftime("%Y-%m-%d %H:%M:%S")
            else:
                end_tw = ""
            gui._update_dynamic_field("B_GLOBAL", "range_start", start_tw)
            gui._update_dynamic_field("B_GLOBAL", "range_end", end_tw)
        except Exception:
            pass

        try:
            conn = retry_stats.get("conn", "")
            timeout = retry_stats.get("timeout", "")
            rotation_count = log_rot.get("rotation_count", "")
            gui._update_dynamic_field("B_GLOBAL", "api_conn_retries", str(conn))
            gui._update_dynamic_field("B_GLOBAL", "api_timeout_retries", str(timeout))
            gui._update_dynamic_field("B_GLOBAL", "log_rotation_count", str(rotation_count))
        except Exception:
            pass

        try:
            symbols = TradingConfig.SUPPORTED_SYMBOLS[:MAX_SYMBOLS]
        except Exception:
            symbols = []

        for sym in symbols:
            info = results.get(sym)
            if not info:
                continue

            api_ok = bool(info.get("api_ok"))
            db_ok = bool(info.get("db_ok"))
            api_fetched = info.get("api_fetched", 0)
            db_count = info.get("db_count", 0)
            min_acc = info.get("min_acceptable", 0)
            max_acc = info.get("max_acceptable", 0)

            if not db_ok:
                state = "ALERT"
            elif db_ok and not api_ok:
                state = "FEW"
            else:
                state = "OK"

            if api_fetched < min_acc:
                api_status = "少"
            elif api_fetched > max_acc:
                api_status = "多"
            else:
                api_status = "OK"

            if db_count < min_acc:
                db_status = "少"
            elif db_count > max_acc:
                db_status = "多"
            else:
                db_status = "OK"

            validation_status = "PASS" if api_ok and db_ok else "WARN"

            if not db_ok:
                warning = "ALERT: DB 1m 筆數不足，今日 1m 可能缺 K 棒"
            elif db_ok and not api_ok:
                warning = "FAKE: DB 已齊，本次 API 新增偏少（複檢提醒）"
            else:
                warning = "OK: API & DB 均在合理範圍內"

            try:
                gui._update_dynamic_field(sym, "b_state", state)
                gui._update_dynamic_field(sym, "b_inserted", str(api_fetched))
                gui._update_dynamic_field(sym, "b_db_count", str(db_count))
                gui._update_dynamic_field(sym, "b_api_status", api_status)
                gui._update_dynamic_field(sym, "b_db_status", db_status)
                gui._update_dynamic_field(sym, "b_validation_status", validation_status)
                gui._update_dynamic_field(sym, "b_warning", warning)
            except Exception:
                continue

        try:
            gui._schedule_render()
        except Exception:
            pass
