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


def _build_template_segments_a() -> List[Tuple[int, int, str]]:
    """模板 A：根據 TradingConfig.SUPPORTED_SYMBOLS 前 MAX_SYMBOLS 個貨幣對，
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


def _build_template_segments_b() -> List[Tuple[int, int, str]]:
    """模板 B：最新 1 分鐘批量抓取結果專用版面。

    版面設計重點：
    - 第 1~4 行：顯示本次批量抓取的整體 summary（真警報/假警報/完全OK、交易對總數、總新增筆數、時間範圍、API 重試與 LOG 輪替統計）。
    - 從第 5 行開始，每個貨幣對使用 3 行顯示本次 1 分鐘驗證結果：
        1) 狀態 + 新增筆數 + DB 筆數
        2) API / DB 狀態與整體驗證結果
        3) 簡短警示文字（真警報 / 假警報 / 完全通過等）
    """

    global DYNAMIC_FIELD_SLOTS

    segments: List[Tuple[int, int, str]] = []

    # ===== 頂部全域 summary 區 =====
    # 第 1 行：真警報 / 假警報 / 完全 OK 數量
    line1 = "真警報(DB不足):"
    real_col = len(line1) + 1
    real_width = 4
    line1 += " " * real_width
    line1 += "  假警報(API少DB正常):"
    pseudo_col = len(line1) + 1
    pseudo_width = 4
    line1 += " " * pseudo_width
    line1 += "  完全OK:"
    ok_col = len(line1) + 1
    ok_width = 4
    line1 += " " * ok_width
    segments.append((1, 1, line1))

    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "real_alert_count")] = (1, real_col, real_width)
    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "pseudo_alert_count")] = (1, pseudo_col, pseudo_width)
    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "ok_count")] = (1, ok_col, ok_width)

    # 第 2 行：交易對總數 / 成功數 / 總新增筆數
    line2 = "交易對總數:"
    total_sym_col = len(line2) + 1
    total_sym_width = 4
    line2 += " " * total_sym_width
    line2 += "  成功抓取:"
    success_sym_col = len(line2) + 1
    success_sym_width = 4
    line2 += " " * success_sym_width
    line2 += "  總新增筆數:"
    total_ins_col = len(line2) + 1
    total_ins_width = 8
    line2 += " " * total_ins_width
    segments.append((2, 1, line2))

    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "total_symbols")] = (2, total_sym_col, total_sym_width)
    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "success_symbols")] = (2, success_sym_col, success_sym_width)
    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "total_inserted")] = (2, total_ins_col, total_ins_width)

    # 第 3 行：批次時間範圍（台北時間）
    line3 = "批次時間:"
    start_col = len(line3) + 1
    start_width = 19  # yyyy-mm-dd HH:MM:SS
    line3 += " " * start_width
    line3 += " → "
    end_col = len(line3) + 1
    end_width = 19
    line3 += " " * end_width
    line3 += " (UTC+8)"
    segments.append((3, 1, line3))

    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "range_start")] = (3, start_col, start_width)
    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "range_end")] = (3, end_col, end_width)

    # 第 4 行：API 重試與 LOG 輪替統計
    line4 = "API重試: 連線錯誤="
    conn_col = len(line4) + 1
    conn_width = 4
    line4 += " " * conn_width
    line4 += " 次, 超時="
    timeout_col = len(line4) + 1
    timeout_width = 4
    line4 += " " * timeout_width
    line4 += " 次  |  LOG輪替錯誤="
    rot_col = len(line4) + 1
    rot_width = 6
    line4 += " " * rot_width
    line4 += " 次"
    segments.append((4, 1, line4))

    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "api_conn_retries")] = (4, conn_col, conn_width)
    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "api_timeout_retries")] = (4, timeout_col, timeout_width)
    DYNAMIC_FIELD_SLOTS[("B_GLOBAL", "log_rotation_count")] = (4, rot_col, rot_width)

    # ===== 每個貨幣對 3 行狀態區 =====
    symbols = TradingConfig.SUPPORTED_SYMBOLS[:MAX_SYMBOLS]
    for idx, sym in enumerate(symbols):
        # 每個 symbol 區塊占用 3 行，從第 5 行開始往下排
        base_row = idx * 3 + 5  # 1-based 行號

        # 1) 整體狀態： 狀態 / 新增 / DB 筆數
        line_s1 = f"[{sym}] 狀態="
        state_col = len(line_s1) + 1
        state_width = 6
        line_s1 += " " * state_width
        line_s1 += "  新增="
        inserted_col = len(line_s1) + 1
        inserted_width = 6
        line_s1 += " " * inserted_width
        line_s1 += "  DB="
        db_col = len(line_s1) + 1
        db_width = 7
        line_s1 += " " * db_width
        segments.append((base_row + 0, 1, line_s1))

        DYNAMIC_FIELD_SLOTS[(sym, "b_state")] = (base_row + 0, state_col, state_width)
        DYNAMIC_FIELD_SLOTS[(sym, "b_inserted")] = (base_row + 0, inserted_col, inserted_width)
        DYNAMIC_FIELD_SLOTS[(sym, "b_db_count")] = (base_row + 0, db_col, db_width)

        # 2) API / DB 狀態與整體驗證結果
        line_s2 = "API:"
        api_col = len(line_s2) + 1
        api_width = 4
        line_s2 += " " * api_width
        line_s2 += "  DB:"
        dbs_col = len(line_s2) + 1
        dbs_width = 4
        line_s2 += " " * dbs_width
        line_s2 += "  驗證:"
        val_col = len(line_s2) + 1
        val_width = 4
        line_s2 += " " * val_width
        segments.append((base_row + 1, 1, line_s2))

        DYNAMIC_FIELD_SLOTS[(sym, "b_api_status")] = (base_row + 1, api_col, api_width)
        DYNAMIC_FIELD_SLOTS[(sym, "b_db_status")] = (base_row + 1, dbs_col, dbs_width)
        DYNAMIC_FIELD_SLOTS[(sym, "b_validation_status")] = (base_row + 1, val_col, val_width)

        # 3) 簡短警示文字
        line_s3 = "警示:"
        warn_col = len(line_s3) + 1
        warn_width = 70
        line_s3 += " " * warn_width
        segments.append((base_row + 2, 1, line_s3))

        DYNAMIC_FIELD_SLOTS[(sym, "b_warning")] = (base_row + 2, warn_col, warn_width)

    return segments


def _build_template_segments_c() -> List[Tuple[int, int, str]]:
    """模板 C：回補任務專用版面。

    設計重點：
    - 頂部 3 行顯示本次回補任務的整體摘要：
        1) 回補貨幣對總數、成功/失敗/跳過數量。
        2) 錯誤分類統計：驗證錯誤/插入錯誤/其他異常。
        3) 回補完成時間（台北時間）。
    - 從第 5 行開始，每個貨幣對使用 3 行顯示回補結果：
        1) 狀態（SUCCESS/FAILED/SKIPPED）與驗證結果（PASS/WARN）。
        2) 風險類型簡述（例如 驗證錯誤 / 插入錯誤 / 可能下架 / OK）。
        3) 備註欄位，用於顯示最後一條重要訊息簡短說明。
    """

    global DYNAMIC_FIELD_SLOTS

    segments: List[Tuple[int, int, str]] = []

    # ===== 頂部回補總覽區 =====
    # 第 1 行：總數 / 成功 / 失敗 / 跳過
    line1 = "回補總覽: 總數="
    total_col = len(line1) + 1
    total_width = 4
    line1 += " " * total_width
    line1 += "  成功="
    success_col = len(line1) + 1
    success_width = 4
    line1 += " " * success_width
    line1 += "  失敗="
    fail_col = len(line1) + 1
    fail_width = 4
    line1 += " " * fail_width
    line1 += "  跳過="
    skip_col = len(line1) + 1
    skip_width = 4
    line1 += " " * skip_width
    segments.append((1, 1, line1))

    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "total_symbols")] = (1, total_col, total_width)
    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "success_count")] = (1, success_col, success_width)
    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "failed_count")] = (1, fail_col, fail_width)
    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "skipped_count")] = (1, skip_col, skip_width)

    # 第 2 行：錯誤分類統計
    line2 = "錯誤統計: 驗證錯誤="
    val_err_col = len(line2) + 1
    val_err_width = 4
    line2 += " " * val_err_width
    line2 += "  插入錯誤="
    ins_err_col = len(line2) + 1
    ins_err_width = 4
    line2 += " " * ins_err_width
    line2 += "  其他異常="
    other_err_col = len(line2) + 1
    other_err_width = 4
    line2 += " " * other_err_width
    segments.append((2, 1, line2))

    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "validation_errors")] = (2, val_err_col, val_err_width)
    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "insert_errors")] = (2, ins_err_col, ins_err_width)
    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "other_errors")] = (2, other_err_col, other_err_width)

    # 第 3 行：回補完成時間（台北時間）
    line3 = "回補完成時間:"
    finish_col = len(line3) + 1
    finish_width = 19  # yyyy-mm-dd HH:MM:SS
    line3 += " " * finish_width
    line3 += " (UTC+8)"
    segments.append((3, 1, line3))

    DYNAMIC_FIELD_SLOTS[("C_GLOBAL", "finished_at")] = (3, finish_col, finish_width)

    # ===== 每個貨幣對 3 行狀態區（左右分欄排版） =====
    symbols = TradingConfig.SUPPORTED_SYMBOLS

    # 每個貨幣對區塊使用 3 行高度，左右各一欄（兩欄佈局）
    block_rows = 3
    cols_per_row = 2
    block_width = 44  # 每欄最大寬度，搭配 LOG_TEXT_WIDTH = 90，左右兩欄剛好
    start_row = 5

    for idx, sym in enumerate(symbols):
        # row_group: 第幾組 3 行區塊（從 0 起算）
        # col_group: 位於當列的左欄(0)或右欄(1)
        row_group = idx // cols_per_row
        col_group = idx % cols_per_row

        base_row = start_row + row_group * block_rows  # 1-based 行號
        base_col = 1 + col_group * block_width         # 1-based 起算欄位

        # 1) 狀態 + 驗證結果
        line_s1 = f"[{sym}] 狀態="
        local_status_col = len(line_s1) + 1
        status_width = 8
        line_s1 += " " * status_width
        line_s1 += "  驗證="
        local_valid_col = len(line_s1) + 1
        valid_width = 4
        line_s1 += " " * valid_width
        segments.append((base_row + 0, base_col, line_s1))

        status_col = base_col + local_status_col - 1
        valid_col = base_col + local_valid_col - 1
        DYNAMIC_FIELD_SLOTS[(sym, "c_status")] = (base_row + 0, status_col, status_width)
        DYNAMIC_FIELD_SLOTS[(sym, "c_validation")] = (base_row + 0, valid_col, valid_width)

        # 2) 風險類型
        line_s2 = "風險:"
        local_risk_col = len(line_s2) + 1
        risk_width = 30
        line_s2 += " " * risk_width
        segments.append((base_row + 1, base_col, line_s2))

        risk_col = base_col + local_risk_col - 1
        DYNAMIC_FIELD_SLOTS[(sym, "c_risk")] = (base_row + 1, risk_col, risk_width)

        # 3) 備註/最後訊息
        line_s3 = "備註:"
        local_note_col = len(line_s3) + 1
        note_width = 40  # 為了兩欄排版縮短備註欄寬
        line_s3 += " " * note_width
        segments.append((base_row + 2, base_col, line_s3))

        note_col = base_col + local_note_col - 1
        DYNAMIC_FIELD_SLOTS[(sym, "c_note")] = (base_row + 2, note_col, note_width)

    return segments


_TEMPLATE_BUILDERS = {
    "A": _build_template_segments_a,
    "B": _build_template_segments_b,
    "C": _build_template_segments_c,
}

# 對外暴露可用模板清單，供 GUI 給使用者選擇
AVAILABLE_TEMPLATES = sorted(_TEMPLATE_BUILDERS.keys())


def apply_template(gui, template_name: str = "A") -> None:
    """將指定模板內容套用到 MainGUI 的格子畫板上。

    Args:
        gui: MainGUI 實例（必須提供 _set_grid_segment 方法）
        template_name: 模板代號，例如 "A"、"B"。
    """
    if not hasattr(gui, "_set_grid_segment"):
        return

    global DYNAMIC_FIELD_SLOTS
    # 每次套用模板時重建動態欄位座標（就地清空，避免重新綁定導致外部引用失效）
    DYNAMIC_FIELD_SLOTS.clear()

    builder = _TEMPLATE_BUILDERS.get(template_name) or _TEMPLATE_BUILDERS["A"]
    try:
        segments = builder()
    except Exception:
        # 若建構模板失敗，嘗試退回模板 A
        try:
            segments = _TEMPLATE_BUILDERS["A"]()
        except Exception:
            return

    for row, col, text in segments:
        # 轉成 0-based index 給 _set_grid_segment 使用
        r_idx = max(0, row - 1)
        c_idx = max(0, col - 1)
        try:
            gui._set_grid_segment(r_idx, c_idx, text)
        except Exception:
            # 模板錯誤不應該讓程式整體失敗
            pass
