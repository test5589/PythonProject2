"""
async_backfill_runner.py - 異步回補執行器
完全分離數據處理和GUI更新，徹底解決GUI卡頓問題
"""

import queue
import threading
import time
from typing import Callable, Optional, Dict, Any
from datetime import datetime


class BackfillMessage:
    """回補訊息類型定義"""
    
    # 訊息類型
    START = 'start'              # 回補開始
    BATCH_START = 'batch_start'  # 批次開始
    BATCH_FETCHED = 'batch_fetched'  # 批次抓取完成
    BATCH_INSERTING = 'batch_inserting'  # 批次插入中
    BATCH_COMPLETE = 'batch_complete'  # 批次完成
    PROGRESS = 'progress'        # 進度更新
    COMPLETE = 'complete'        # 回補完成
    ERROR = 'error'              # 錯誤
    WARNING = 'warning'          # 警告
    INFO = 'info'                # 普通訊息
    SKIP_ALL = 'skip_all'        # 全部跳過
    
    # 日誌級別
    LEVEL_CRITICAL = 0  # 關鍵訊息
    LEVEL_SUMMARY = 1   # 摘要訊息
    LEVEL_NORMAL = 2    # 普通訊息
    LEVEL_VERBOSE = 3   # 詳細訊息
    
    def __init__(self, msg_type: str, data: Dict[str, Any], level: int = LEVEL_NORMAL):
        """
        初始化訊息
        
        Args:
            msg_type: 訊息類型
            data: 訊息數據
            level: 日誌級別
        """
        self.type = msg_type
        self.data = data
        self.level = level
        self.timestamp = time.time()


class AsyncBackfillRunner:
    """
    異步回補執行器
    完全分離數據處理和GUI更新
    """
    
    def __init__(self, gui):
        """
        初始化
        
        Args:
            gui: GUI實例
        """
        self.gui = gui
        # 線程安全的訊息隊列
        self.message_queue = queue.Queue()
        # 控制標誌
        self.is_running = False
        self.worker_thread = None
        self.update_interval = 200  # 200ms檢查一次隊列
        
    def start_backfill(self, backfill_func: Callable, *args, **kwargs):
        """
        啟動異步回補
        
        Args:
            backfill_func: 回補函數（會在子線程中執行）
            *args, **kwargs: 傳遞給回補函數的參數
        """
        if self.is_running:
            self._send_message(BackfillMessage.WARNING, 
                             {'message': '回補已在運行中'}, 
                             BackfillMessage.LEVEL_SUMMARY)
            return
        
        self.is_running = True
        
        # 包裝回補函數，添加訊息發送功能
        def wrapped_backfill():
            try:
                # 將訊息發送器注入到kwargs
                kwargs['message_sender'] = self._create_message_sender()
                
                # 執行回補（在子線程中）
                result = backfill_func(*args, **kwargs)
                
                # 發送完成訊息
                self._send_message(BackfillMessage.COMPLETE, 
                                 {'result': result}, 
                                 BackfillMessage.LEVEL_CRITICAL)
                
            except Exception as e:
                import traceback
                # 發送錯誤訊息
                self._send_message(BackfillMessage.ERROR, 
                                 {
                                     'message': str(e),
                                     'traceback': traceback.format_exc()
                                 }, 
                                 BackfillMessage.LEVEL_CRITICAL)
            finally:
                self.is_running = False
        
        # 啟動工作線程
        self.worker_thread = threading.Thread(target=wrapped_backfill, daemon=True)
        self.worker_thread.start()
        
        # 啟動GUI更新循環
        self._start_gui_update_loop()
    
    def _create_message_sender(self):
        """
        創建訊息發送器（供回補函數使用）
        
        Returns:
            MessageSender實例
        """
        return MessageSender(self.message_queue)
    
    def _send_message(self, msg_type: str, data: Dict[str, Any], level: int = BackfillMessage.LEVEL_NORMAL):
        """
        發送訊息到隊列
        
        Args:
            msg_type: 訊息類型
            data: 訊息數據
            level: 日誌級別
        """
        msg = BackfillMessage(msg_type, data, level)
        self.message_queue.put(msg)
    
    def _start_gui_update_loop(self):
        """啟動GUI更新循環（只有一個定時器）"""
        def update_loop():
            if not self.is_running and self.message_queue.empty():
                # 回補結束且隊列為空，停止更新循環
                return
            
            # 批量處理所有待處理的訊息
            messages = []
            try:
                # 一次性取出所有訊息（非阻塞）
                while True:
                    msg = self.message_queue.get_nowait()
                    messages.append(msg)
            except queue.Empty:
                pass
            
            # 批量更新GUI
            if messages:
                self._batch_update_gui(messages)
            
            # 繼續下一次檢查（只有這一個定時器）
            self.gui.root.after(self.update_interval, update_loop)
        
        # 啟動更新循環
        update_loop()
    
    def _batch_update_gui(self, messages: list):
        """
        批量更新GUI
        
        Args:
            messages: 訊息列表
        """
        # 獲取精簡模式狀態
        is_compact = self.gui.compact_var.get() if hasattr(self.gui, 'compact_var') else False
        
        # 累積日誌訊息
        log_messages = []
        
        for msg in messages:
            # 根據精簡模式過濾
            if is_compact and msg.level > BackfillMessage.LEVEL_SUMMARY:
                continue
            
            # 處理不同類型的訊息
            if msg.type == BackfillMessage.START:
                log_msg = self._format_start_message(msg.data)
                log_messages.append(log_msg)
                
            elif msg.type == BackfillMessage.BATCH_START:
                log_msg = self._format_batch_start_message(msg.data)
                log_messages.append(log_msg)
                
            elif msg.type == BackfillMessage.BATCH_FETCHED:
                log_msg = self._format_batch_fetched_message(msg.data)
                log_messages.append(log_msg)
                
            elif msg.type == BackfillMessage.BATCH_INSERTING:
                log_msg = self._format_batch_inserting_message(msg.data)
                log_messages.append(log_msg)
                
            elif msg.type == BackfillMessage.BATCH_COMPLETE:
                log_msg = self._format_batch_complete_message(msg.data)
                log_messages.append(log_msg)
                # 更新進度條
                self._update_progress_bar(msg.data)
                
            elif msg.type == BackfillMessage.PROGRESS:
                log_msg = self._format_progress_message(msg.data)
                log_messages.append(log_msg)
                self._update_progress_bar(msg.data)
                
            elif msg.type == BackfillMessage.COMPLETE:
                log_msg = self._format_complete_message(msg.data)
                log_messages.append(log_msg)
                # 隱藏進度條
                if hasattr(self.gui, 'progress_bar'):
                    self.gui.root.after(3000, self.gui.progress_bar.hide)
                
            elif msg.type == BackfillMessage.ERROR:
                log_msg = self._format_error_message(msg.data)
                log_messages.append(log_msg)
                # 記錄到進度條的異常區域
                if hasattr(self.gui, 'progress_bar'):
                    self.gui.progress_bar.log_exception(msg.data['message'])
                
            elif msg.type == BackfillMessage.WARNING:
                log_msg = self._format_warning_message(msg.data)
                log_messages.append(log_msg)
                
            elif msg.type == BackfillMessage.INFO:
                log_msg = msg.data.get('message', '')
                log_messages.append(log_msg)
                
            elif msg.type == BackfillMessage.SKIP_ALL:
                log_msg = self._format_skip_all_message(msg.data)
                log_messages.append(log_msg)
        
        # 一次性更新日誌（批量）
        if log_messages:
            combined_log = "\n".join(log_messages)
            self._update_log_text(combined_log)
    
    def _format_start_message(self, data: Dict[str, Any]) -> str:
        """格式化開始訊息"""
        symbol = data.get('symbol', '')
        interval = data.get('interval', '')
        start_time = data.get('start_time', '')
        end_time = data.get('end_time', '')
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        return f"🚀 {symbol_short} | 開始回補 {interval} ({start_time} → {end_time})"
    
    def _format_batch_start_message(self, data: Dict[str, Any]) -> str:
        """格式化批次開始訊息"""
        symbol = data.get('symbol', '')
        batch_num = data.get('batch_num', 0)
        batch_size = data.get('batch_size', 0)
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        return f"📦 {symbol_short} | 批次 {batch_num}: 正在抓取 {batch_size} 筆..."
    
    def _format_batch_fetched_message(self, data: Dict[str, Any]) -> str:
        """格式化批次抓取完成訊息"""
        symbol = data.get('symbol', '')
        batch_num = data.get('batch_num', 0)
        count = data.get('count', 0)
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        return f"✅ {symbol_short} | 批次 {batch_num}: 已抓取 {count} 筆"
    
    def _format_batch_inserting_message(self, data: Dict[str, Any]) -> str:
        """格式化批次插入中訊息"""
        symbol = data.get('symbol', '')
        batch_num = data.get('batch_num', 0)
        count = data.get('count', 0)
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        return f"💾 {symbol_short} | 批次 {batch_num}: 準備插入 {count} 筆"
    
    def _format_batch_complete_message(self, data: Dict[str, Any]) -> str:
        """格式化批次完成訊息"""
        symbol = data.get('symbol', '')
        batch_num = data.get('batch_num', 0)
        inserted = data.get('inserted', 0)
        skipped = data.get('skipped', 0)
        total = data.get('total', 0)
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        
        if skipped > 0:
            return f"🎯 {symbol_short} | 批次 {batch_num}: 插入 {inserted}/{total} 筆，跳過 {skipped} 筆"
        else:
            return f"🎯 {symbol_short} | 批次 {batch_num}: 成功插入 {inserted}/{total} 筆"
    
    def _format_progress_message(self, data: Dict[str, Any]) -> str:
        """格式化進度訊息"""
        symbol = data.get('symbol', '')
        current = data.get('current', 0)
        total = data.get('total', 0)
        detail = data.get('detail', '')
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        
        percent = (current / total * 100) if total > 0 else 0
        msg = f"📊 {symbol_short} | 進度: {current}/{total} ({percent:.1f}%)"
        if detail:
            msg += f" - {detail}"
        return msg
    
    def _format_complete_message(self, data: Dict[str, Any]) -> str:
        """格式化完成訊息"""
        symbol = data.get('symbol', '')
        total_inserted = data.get('total_inserted', 0)
        total_skipped = data.get('total_skipped', 0)
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        return f"✅ {symbol_short} | 回補完成！總計插入 {total_inserted:,} 筆，跳過 {total_skipped:,} 筆"
    
    def _format_error_message(self, data: Dict[str, Any]) -> str:
        """格式化錯誤訊息"""
        symbol = data.get('symbol', '')
        message = data.get('message', '')
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol if symbol else ''
        if symbol_short:
            return f"❌ {symbol_short} | 錯誤: {message}"
        else:
            return f"❌ 錯誤: {message}"
    
    def _format_warning_message(self, data: Dict[str, Any]) -> str:
        """格式化警告訊息"""
        symbol = data.get('symbol', '')
        message = data.get('message', '')
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol if symbol else ''
        if symbol_short:
            return f"⚠️ {symbol_short} | 警告: {message}"
        else:
            return f"⚠️ 警告: {message}"
    
    def _format_skip_all_message(self, data: Dict[str, Any]) -> str:
        """格式化全部跳過訊息"""
        symbol = data.get('symbol', '')
        batch_num = data.get('batch_num', 0)
        count = data.get('count', 0)
        symbol_short = symbol.split('USDT')[0] if 'USDT' in symbol else symbol
        return f"⏭️ {symbol_short} | 批次 {batch_num}: {count} 筆資料已存在，全部跳過"
    
    def _update_progress_bar(self, data: Dict[str, Any]):
        """更新進度條"""
        if hasattr(self.gui, 'progress_bar'):
            current = data.get('current', 0)
            total = data.get('total', 0)
            if total > 0:
                progress = int((current / total) * 100)
                self.gui.progress_bar.set_progress(progress)
    
    def _update_log_text(self, message: str):
        """更新日誌文本"""
        return
    
    def stop(self):
        """停止回補"""
        self.is_running = False


class MessageSender:
    """
    訊息發送器
    供回補函數使用，發送訊息到GUI
    """
    
    def __init__(self, message_queue: queue.Queue):
        """
        初始化
        
        Args:
            message_queue: 訊息隊列
        """
        self.queue = message_queue
    
    def start(self, symbol: str, interval: str, start_time, end_time):
        """回補開始"""
        self.queue.put(BackfillMessage(
            BackfillMessage.START,
            {
                'symbol': symbol,
                'interval': interval,
                'start_time': start_time.strftime('%Y-%m-%d %H:%M') if hasattr(start_time, 'strftime') else str(start_time),
                'end_time': end_time.strftime('%Y-%m-%d %H:%M') if hasattr(end_time, 'strftime') else str(end_time)
            },
            BackfillMessage.LEVEL_SUMMARY
        ))
    
    def batch_start(self, symbol: str, batch_num: int, batch_size: int):
        """批次開始"""
        self.queue.put(BackfillMessage(
            BackfillMessage.BATCH_START,
            {
                'symbol': symbol,
                'batch_num': batch_num,
                'batch_size': batch_size
            },
            BackfillMessage.LEVEL_NORMAL
        ))
    
    def batch_fetched(self, symbol: str, batch_num: int, count: int):
        """批次抓取完成"""
        self.queue.put(BackfillMessage(
            BackfillMessage.BATCH_FETCHED,
            {
                'symbol': symbol,
                'batch_num': batch_num,
                'count': count
            },
            BackfillMessage.LEVEL_VERBOSE
        ))
    
    def batch_inserting(self, symbol: str, batch_num: int, count: int):
        """批次插入中"""
        self.queue.put(BackfillMessage(
            BackfillMessage.BATCH_INSERTING,
            {
                'symbol': symbol,
                'batch_num': batch_num,
                'count': count
            },
            BackfillMessage.LEVEL_VERBOSE
        ))
    
    def batch_complete(self, symbol: str, batch_num: int, inserted: int, skipped: int, total: int):
        """批次完成"""
        self.queue.put(BackfillMessage(
            BackfillMessage.BATCH_COMPLETE,
            {
                'symbol': symbol,
                'batch_num': batch_num,
                'inserted': inserted,
                'skipped': skipped,
                'total': total,
                'current': inserted,  # 用於進度條
            },
            BackfillMessage.LEVEL_SUMMARY
        ))
    
    def progress(self, symbol: str, current: int, total: int, detail: str = ''):
        """進度更新"""
        self.queue.put(BackfillMessage(
            BackfillMessage.PROGRESS,
            {
                'symbol': symbol,
                'current': current,
                'total': total,
                'detail': detail
            },
            BackfillMessage.LEVEL_VERBOSE
        ))
    
    def complete(self, symbol: str, total_inserted: int, total_skipped: int):
        """回補完成"""
        self.queue.put(BackfillMessage(
            BackfillMessage.COMPLETE,
            {
                'symbol': symbol,
                'total_inserted': total_inserted,
                'total_skipped': total_skipped
            },
            BackfillMessage.LEVEL_CRITICAL
        ))
    
    def error(self, symbol: str, message: str):
        """錯誤"""
        self.queue.put(BackfillMessage(
            BackfillMessage.ERROR,
            {
                'symbol': symbol,
                'message': message
            },
            BackfillMessage.LEVEL_CRITICAL
        ))
    
    def warning(self, symbol: str, message: str):
        """警告"""
        self.queue.put(BackfillMessage(
            BackfillMessage.WARNING,
            {
                'symbol': symbol,
                'message': message
            },
            BackfillMessage.LEVEL_SUMMARY
        ))
    
    def info(self, symbol: str, message: str):
        """普通訊息"""
        self.queue.put(BackfillMessage(
            BackfillMessage.INFO,
            {
                'symbol': symbol,
                'message': message
            },
            BackfillMessage.LEVEL_NORMAL
        ))
    
    def skip_all(self, symbol: str, batch_num: int, count: int):
        """全部跳過"""
        self.queue.put(BackfillMessage(
            BackfillMessage.SKIP_ALL,
            {
                'symbol': symbol,
                'batch_num': batch_num,
                'count': count
            },
            BackfillMessage.LEVEL_SUMMARY
        ))
