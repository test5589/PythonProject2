"""gui_log_manager.py - 專門負責 GUI 介面的 LOG 編輯與過濾邏輯

設計目標：
- 與終端日誌（logging / print）完全解耦。
- 專門處理要顯示在 GUI Text 的內容格式。
- 目前優先支援：1 秒監控寫入訊息，只顯示 BTCUSDT，其他貨幣對先忽略。
"""

from datetime import datetime, timezone, timedelta
from typing import Callable


class GuiLogManager:
    """GUI 專用的 LOG 管理器

    由 MainGUI 傳入一個簡單的 `gui_log_func`（通常是 `MainGUI.log`），
    本類別只負責：
    - 判斷這一行訊息要不要顯示在 GUI
    - 決定顯示在 GUI 的最終文字長相
    """

    def __init__(self, gui_log_func: Callable[[str], None]):
        self._gui_log = gui_log_func

    # ===== 公開介面 =====
    def handle(self, msg: str) -> None:
        """處理一條原始訊息，決定如何顯示在 GUI。

        目前邏輯：
        - 若是 1 秒監控寫入訊息：
          - BTCUSDT → 顯示（套用固定格式）
          - 其他貨幣對 → 完全略過，不顯示在 GUI
        - 其他一般訊息 → 一律顯示在 GUI，之後再按需要細分。
        """
        # 先處理 1 秒監控寫入訊息
        if "🟢 1s 寫入" in msg:
            if self._is_1s_btc_message(msg):
                line = self._format_1s_btc_line(msg)
                self._gui_log(line)
            # 非 BTCUSDT 的 1 秒訊息直接忽略（GUI 不顯示）
            return

        # 其他一般訊息：全部顯示
        line = self._format_general_line(msg)
        self._gui_log(line)

    # ===== 1 秒監控相關判斷 =====
    def _is_1s_btc_message(self, msg: str) -> bool:
        """判斷是否為 BTCUSDT 的 1 秒寫入統計訊息"""
        if "🟢 1s 寫入" not in msg:
            return False
        if "data_source=" not in msg or "(總共" not in msg:
            return False

        # MultiSymbolMonitor 會在前面加上 [SYMBOL]
        # 這裡只保留 BTCUSDT，其它貨幣對先忽略
        if "[BTCUSDT]" in msg or "BTCUSDT" in msg:
            return True
        return False

    # ===== 各種格式化方法 =====
    def _format_1s_btc_line(self, raw_msg: str) -> str:
        """將 BTCUSDT 1 秒寫入訊息轉成終端風格格式"""
        ts = self._now_str()
        # 模仿 multi_monitor logger 的格式: 日期 | name | level | message
        return f"{ts} | multi_monitor | INFO | {raw_msg}"

    def _format_general_line(self, raw_msg: str) -> str:
        """一般訊息格式：統一在前面加上 GUI 專用前綴"""
        ts = self._now_str()
        return f"{ts} | gui | INFO | {raw_msg}"

    # ===== 時間工具 =====
    def _now_str(self) -> str:
        """取得目前台北時間的字串，格式與 logger 一致"""
        try:
            now_local = datetime.now(tz=timezone(timedelta(hours=8)))
            return now_local.strftime("%y/%m/%d %H:%M:%S")
        except Exception:
            # 極端情況下就回傳空字串，避免整個流程噴錯
            return ""
