"""monitor_board_template.py - 監控畫板靜態模板設定

你可以在這個檔案裡，直接指定「第幾行、第幾個字」要顯示什麼內容。

座標系統說明（非常重要）：
- row: 1 起算（1 = 最上面那一行, 8 = 第 8 行）
- col: 1 起算（1 = 該行最左邊第 1 個字, 26 = 第 26 個字）
- LOG 區目前大小：140 行 × 55 列（在 layout_config.LOG_TEXT_WIDTH / MainGUI.gridRows 設定）

使用方式：
- 修改 TEMPLATE_SEGMENTS 裡的 (row, col, text) 三元組。
- 每一個三元組代表：從第 row 行的第 col 個字開始，寫入 text 這段文字。
- 若 text 超過當前行剩下的空間，會自動截斷在畫板右邊界。

注意：
- 這只是「啟動時」或「手動套用時」的初始模板；
  之後程式（例如 BTC 1s 監控）可能會用 _set_grid_row/_set_grid_segment 覆寫某些區域。
"""

from typing import List, Tuple, Dict
from config.trading_config import TradingConfig

MAX_SYMBOLS = 20
LINES_PER_SYMBOL = 8

# 動態欄位座標：
# key: (symbol, field_name) -> value: (row, col, width)
# row/col 一律 1 起算，width 為可寫入的最大字元數
DYNAMIC_FIELD_SLOTS: Dict[Tuple[str, str], Tuple[int, int, int]] = {}


def _build_template_segments() -> List[Tuple[int, int, str]]:
    """根據 TradingConfig.SUPPORTED_SYMBOLS 前 MAX_SYMBOLS 個貨幣對，
    從第 1 行開始依序產生每個 8 行的監控區塊模板。

    每個區塊行內容樣式（以 BTCUSDT 為例）：

    1) [BTCUSDT]multi_monitor|INFO|
    2) NOW:(                )
    3) 🟢 1s 寫入 BTCUSDT(                )data_source=real           (總共:    )
    4) 🟢 1s 寫入 BTCUSDT(                )data_source=real_no-trade-fill   (總共:    )
    5) DATE | stats_collector | INFO |
    6) ⏭️ 已跳過    筆重複
    7) timestamp (crypto/BTCUSDT @ 1s, 最新:              , 現有來源=    , 新來源=    )
    8) -------------------------------------------------------

    會變動的時間 / 數字 / 來源欄位全部留空，由程式執行時覆寫。
    """

    global DYNAMIC_FIELD_SLOTS

    segments: List[Tuple[int, int, str]] = []

    # ===== 模板A：第 1 行全域統計列 =====
    # 1.警報 2.假警報 3.系統提示 4.LOG 以及本次監控的開始/結束時間（結束在下一行對齊）
    line1 = "1.警報:"
    alert_col = len(line1) + 1
    alert_width = 6
    line1 += " " * alert_width
    line1 += "  2.假警報:"
    false_col = len(line1) + 1
    false_width = 6
    line1 += " " * false_width
    line1 += "  3.系統提示:"
    system_col = len(line1) + 1
    system_width = 6
    line1 += " " * system_width
    line1 += "  4.LOG:"
    log_col = len(line1) + 1
    log_width = 6
    line1 += " " * log_width

    # 監控開始時間欄位（格式約 17 字：yy/MM/dd HH:MM:SS）
    line1 += "  開始:"
    start_col = len(line1) + 1
    start_width = 17
    line1 += " " * start_width

    segments.append((1, 1, line1))

    # 第 2 行：結束時間，值欄位與開始時間欄位垂直對齊
    line2 = " " * (start_col - len("結束:") - 1) + "結束:"
    end_col = start_col
    end_width = 17
    line2 += " " * end_width
    segments.append((2, 1, line2))

    # GLOBAL 統計欄位座標
    DYNAMIC_FIELD_SLOTS[("GLOBAL", "alert_count")] = (1, alert_col, alert_width)
    DYNAMIC_FIELD_SLOTS[("GLOBAL", "false_alert_count")] = (1, false_col, false_width)
    DYNAMIC_FIELD_SLOTS[("GLOBAL", "system_hint_count")] = (1, system_col, system_width)
    DYNAMIC_FIELD_SLOTS[("GLOBAL", "log_count")] = (1, log_col, log_width)
    DYNAMIC_FIELD_SLOTS[("GLOBAL", "monitor_start")] = (1, start_col, start_width)
    DYNAMIC_FIELD_SLOTS[("GLOBAL", "monitor_end")] = (2, end_col, end_width)

    symbols = TradingConfig.SUPPORTED_SYMBOLS[:MAX_SYMBOLS]
    for idx, sym in enumerate(symbols):
        # 每個 symbol 區塊從第 3 行開始往下排，每個占用 8 行
        base_row = idx * LINES_PER_SYMBOL + 3  # 1-based 行號

        # 1) 標頭
        header_line = f"[{sym}]multi_monitor|INFO|"
        segments.append((base_row + 0, 1, header_line))

        # 2) NOW 行，預留 16 字元給時間
        line2 = "NOW:("
        now_col = len(line2) + 1
        now_width = 16
        line2 += " " * now_width
        line2 += ")"
        segments.append((base_row + 1, 1, line2))
        DYNAMIC_FIELD_SLOTS[(sym, "now_time")] = (base_row + 1, now_col, now_width)

        # 3) 1 秒寫入（data_source=real）
        ts_width = 16
        ds_width = 18
        total_width = 6

        line3 = f"🟢 1s 寫入 {sym}("
        real_ts_col = len(line3) + 1
        line3 += " " * ts_width
        line3 += ")data_source="
        real_ds_col = len(line3) + 1
        line3 += " " * ds_width
        line3 += " 總共:"
        real_total_col = len(line3) + 1
        line3 += " " * total_width
        segments.append((base_row + 2, 1, line3))

        DYNAMIC_FIELD_SLOTS[(sym, "real_ts")] = (base_row + 2, real_ts_col, ts_width)
        DYNAMIC_FIELD_SLOTS[(sym, "real_data_source")] = (base_row + 2, real_ds_col, ds_width)
        DYNAMIC_FIELD_SLOTS[(sym, "real_total")] = (base_row + 2, real_total_col, total_width)

        # 4) 1 秒寫入（data_source=real_no-trade-fill）
        line4 = f"🟢 1s 寫入 {sym}("
        fill_ts_col = len(line4) + 1
        line4 += " " * ts_width
        line4 += ")data_source="
        fill_ds_col = len(line4) + 1
        line4 += " " * ds_width
        line4 += " 總共:"
        fill_total_col = len(line4) + 1
        line4 += " " * total_width
        segments.append((base_row + 3, 1, line4))

        DYNAMIC_FIELD_SLOTS[(sym, "fill_ts")] = (base_row + 3, fill_ts_col, ts_width)
        DYNAMIC_FIELD_SLOTS[(sym, "fill_data_source")] = (base_row + 3, fill_ds_col, ds_width)
        DYNAMIC_FIELD_SLOTS[(sym, "fill_total")] = (base_row + 3, fill_total_col, total_width)

        # 5) stats_collector 行：保留 DATE 標籤，後面 16 字元給時間
        line5 = "DATE "
        dup_now_col = len(line5) + 1
        dup_now_width = 16
        line5 += " " * dup_now_width
        line5 += " | stats_collector | INFO |"
        segments.append((base_row + 4, 1, line5))
        DYNAMIC_FIELD_SLOTS[(sym, "dup_now_time")] = (base_row + 4, dup_now_col, dup_now_width)

        # 6) 已跳過 N 筆重複
        line6 = "⏭️ 已跳過 "
        dup_count_col = len(line6) + 1
        dup_count_width = 6
        line6 += " " * dup_count_width
        line6 += " 筆重複"
        segments.append((base_row + 5, 1, line6))
        DYNAMIC_FIELD_SLOTS[(sym, "dup_count")] = (base_row + 5, dup_count_col, dup_count_width)

        # 7) timestamp 詳細說明
        line7 = f"timestamp (crypto/{sym} @ "
        dup_interval_col = len(line7) + 1
        dup_interval_width = 4
        line7 += " " * dup_interval_width
        line7 += ", 最新: "
        dup_latest_col = len(line7) + 1
        dup_latest_width = 19
        line7 += " " * dup_latest_width
        line7 += ", 現有來源="
        dup_exist_col = len(line7) + 1
        dup_exist_width = 12
        line7 += " " * dup_exist_width
        line7 += ", 新來源="
        dup_new_col = len(line7) + 1
        dup_new_width = 12
        line7 += " " * dup_new_width
        line7 += ")"
        segments.append((base_row + 6, 1, line7))

        DYNAMIC_FIELD_SLOTS[(sym, "dup_interval")] = (base_row + 6, dup_interval_col, dup_interval_width)
        DYNAMIC_FIELD_SLOTS[(sym, "dup_latest_ts")] = (base_row + 6, dup_latest_col, dup_latest_width)
        DYNAMIC_FIELD_SLOTS[(sym, "dup_existing_source")] = (base_row + 6, dup_exist_col, dup_exist_width)
        DYNAMIC_FIELD_SLOTS[(sym, "dup_new_source")] = (base_row + 6, dup_new_col, dup_new_width)

        # 8) 分隔線
        segments.append((base_row + 7, 1, "-------------------------------------------------------"))

    return segments


# (row, col, text) 三元組列表，row/col 一律 1 起算。
# 會根據目前交易設定中的前 MAX_SYMBOLS 個貨幣對，自動產生模板。
TEMPLATE_SEGMENTS: List[Tuple[int, int, str]] = _build_template_segments()


def apply_template(gui) -> None:
    """將本檔案定義的模板內容套用到 MainGUI 的格子畫板上。

    Args:
        gui: MainGUI 實例（必須提供 _set_grid_segment 方法）
    """
    if not hasattr(gui, "_set_grid_segment"):
        return

    for row, col, text in TEMPLATE_SEGMENTS:
        # 轉成 0-based index 給 _set_grid_segment 使用
        r_idx = max(0, row - 1)
        c_idx = max(0, col - 1)
        try:
            gui._set_grid_segment(r_idx, c_idx, text)
        except Exception:
            # 模板錯誤不應該讓程式整體失敗
            pass
