"""
gui_logger.py - 統一的GUI日誌系統
支持日誌級別過濾，使精簡模式真正有意義
"""

from enum import IntEnum
from typing import Callable, Optional


class LogLevel(IntEnum):
    """日誌級別定義"""
    CRITICAL = 0   # 關鍵訊息（錯誤、完成）- 始終顯示
    SUMMARY = 1    # 摘要訊息（批次開始/結束）- 精簡模式顯示
    NORMAL = 2     # 普通訊息（一般操作）- 精簡模式過濾
    VERBOSE = 3    # 詳細訊息（每50筆進度）- 精簡模式過濾
    DEBUG = 4      # 調試訊息 - 精簡模式過濾


class GUILogger:
    """
    GUI日誌記錄器
    支持日誌級別過濾，使精簡模式有實際作用
    """
    
    def __init__(self, gui_log_func: Callable[[str], None], compact_mode_func: Callable[[], bool]):
        """
        初始化
        
        Args:
            gui_log_func: GUI的log函數
            compact_mode_func: 獲取精簡模式狀態的函數
        """
        self.gui_log = gui_log_func
        self.get_compact_mode = compact_mode_func
    
    def log(self, message: str, level: LogLevel = LogLevel.NORMAL):
        """
        記錄日誌（根據級別和精簡模式過濾）
        
        Args:
            message: 日誌訊息
            level: 日誌級別
        """
        # 獲取當前精簡模式狀態
        is_compact = self.get_compact_mode()
        
        # 過濾邏輯
        if is_compact:
            # 精簡模式：只顯示 CRITICAL 和 SUMMARY
            if level > LogLevel.SUMMARY:
                return
        
        # 輸出到GUI
        self.gui_log(message)
    
    def critical(self, message: str):
        """關鍵訊息（錯誤、完成等）- 始終顯示"""
        self.log(message, LogLevel.CRITICAL)
    
    def summary(self, message: str):
        """摘要訊息（批次開始/結束）- 精簡模式顯示"""
        self.log(message, LogLevel.SUMMARY)
    
    def normal(self, message: str):
        """普通訊息（一般操作）- 精簡模式過濾"""
        self.log(message, LogLevel.NORMAL)
    
    def verbose(self, message: str):
        """詳細訊息（進度更新）- 精簡模式過濾"""
        self.log(message, LogLevel.VERBOSE)
    
    def debug(self, message: str):
        """調試訊息 - 精簡模式過濾"""
        self.log(message, LogLevel.DEBUG)


class BackfillLogger:
    """
    回補專用日誌記錄器
    提供便捷的日誌方法，自動分類級別
    """
    
    def __init__(self, gui_logger: GUILogger, symbol: str):
        """
        初始化
        
        Args:
            gui_logger: GUI日誌記錄器
            symbol: 貨幣對（用於前綴）
        """
        self.logger = gui_logger
        self.symbol = symbol
        self.symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
    
    def start(self, interval: str, start_time, end_time):
        """回補開始（摘要級別）"""
        self.logger.summary(
            f"🚀 {self.symbol_short} | 開始回補 {interval} "
            f"({start_time.strftime('%Y-%m-%d %H:%M')} → {end_time.strftime('%Y-%m-%d %H:%M')})"
        )
    
    def batch_start(self, batch_num: int, batch_size: int):
        """批次開始（普通級別）"""
        self.logger.normal(f"📦 {self.symbol_short} | 批次 {batch_num}: 正在抓取 {batch_size} 筆...")
    
    def batch_fetched(self, batch_num: int, count: int):
        """批次抓取完成（詳細級別）"""
        self.logger.verbose(f"✅ {self.symbol_short} | 批次 {batch_num}: 已抓取 {count} 筆")
    
    def batch_inserting(self, batch_num: int, count: int):
        """批次插入中（詳細級別）"""
        self.logger.verbose(f"💾 {self.symbol_short} | 批次 {batch_num}: 準備插入 {count} 筆")
    
    def batch_complete(self, batch_num: int, inserted: int, skipped: int, total: int):
        """批次完成（摘要級別）"""
        if skipped > 0:
            self.logger.summary(
                f"🎯 {self.symbol_short} | 批次 {batch_num}: "
                f"插入 {inserted}/{total} 筆，跳過 {skipped} 筆"
            )
        else:
            self.logger.summary(
                f"🎯 {self.symbol_short} | 批次 {batch_num}: "
                f"成功插入 {inserted}/{total} 筆"
            )
    
    def progress(self, current: int, total: int, detail: str = ""):
        """進度更新（詳細級別）"""
        percent = (current / total * 100) if total > 0 else 0
        msg = f"📊 {self.symbol_short} | 進度: {current}/{total} ({percent:.1f}%)"
        if detail:
            msg += f" - {detail}"
        self.logger.verbose(msg)
    
    def complete(self, total_inserted: int, total_skipped: int):
        """回補完成（關鍵級別）"""
        self.logger.critical(
            f"✅ {self.symbol_short} | 回補完成！"
            f"總計插入 {total_inserted:,} 筆，跳過 {total_skipped:,} 筆"
        )
    
    def error(self, message: str):
        """錯誤訊息（關鍵級別）"""
        self.logger.critical(f"❌ {self.symbol_short} | 錯誤: {message}")
    
    def warning(self, message: str):
        """警告訊息（摘要級別）"""
        self.logger.summary(f"⚠️ {self.symbol_short} | 警告: {message}")
    
    def info(self, message: str):
        """普通訊息（普通級別）"""
        self.logger.normal(f"ℹ️ {self.symbol_short} | {message}")
    
    def skip_all(self, batch_num: int, count: int):
        """全部跳過（摘要級別）"""
        self.logger.summary(
            f"⏭️ {self.symbol_short} | 批次 {batch_num}: "
            f"{count} 筆資料已存在，全部跳過"
        )


# 便捷函數
def create_gui_logger(gui) -> GUILogger:
    """
    創建GUI日誌記錄器
    
    Args:
        gui: MainGUI實例
    
    Returns:
        GUILogger實例
    """
    return GUILogger(
        gui_log_func=gui.log,
        compact_mode_func=lambda: gui.compact_var.get()
    )


def create_backfill_logger(gui_logger: GUILogger, symbol: str) -> BackfillLogger:
    """
    創建回補日誌記錄器
    
    Args:
        gui_logger: GUI日誌記錄器
        symbol: 貨幣對
    
    Returns:
        BackfillLogger實例
    """
    return BackfillLogger(gui_logger, symbol)
