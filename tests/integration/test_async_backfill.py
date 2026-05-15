"""
test_async_backfill.py - 異步回補架構測試

測試 MessageSender 和 BackfillMessage 的核心功能
"""

import unittest
from datetime import datetime
from core.async_backfill_runner import MessageSender, BackfillMessage


class MockQueue:
    """模擬 Queue 用於測試"""
    def __init__(self):
        self.messages = []
    
    def put(self, msg):
        self.messages.append(msg)
    
    def qsize(self):
        return len(self.messages)


class TestMessageSender(unittest.TestCase):
    """MessageSender 測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.message_queue = MockQueue()
        self.sender = MessageSender(self.message_queue)
    
    def test_message_sender_initialization(self):
        """測試 MessageSender 初始化"""
        self.assertIsNotNone(self.sender)
        self.assertEqual(self.message_queue.qsize(), 0)
    
    def test_send_start_message(self):
        """測試發送開始訊息"""
        now = datetime.now()
        self.sender.start("BTCUSDT", "1m", now, now)
        
        self.assertEqual(self.message_queue.qsize(), 1)
        msg = self.message_queue.messages[0]
        self.assertEqual(msg.type, BackfillMessage.START)
        self.assertEqual(msg.data['symbol'], "BTCUSDT")
    
    def test_send_batch_messages(self):
        """測試發送批次訊息"""
        self.sender.batch_start("BTCUSDT", 1, 500)
        self.sender.batch_fetched("BTCUSDT", 1, 500)
        
        self.assertEqual(self.message_queue.qsize(), 2)
        self.assertEqual(self.message_queue.messages[0].type, BackfillMessage.BATCH_START)
        self.assertEqual(self.message_queue.messages[1].type, BackfillMessage.BATCH_FETCHED)


class TestBackfillMessage(unittest.TestCase):
    """BackfillMessage 測試類"""
    
    def test_message_creation(self):
        """測試訊息創建"""
        data = {'test': 'data'}
        msg = BackfillMessage(BackfillMessage.INFO, data, BackfillMessage.LEVEL_NORMAL)
        self.assertEqual(msg.type, BackfillMessage.INFO)
        self.assertEqual(msg.data, data)
        self.assertEqual(msg.level, BackfillMessage.LEVEL_NORMAL)
        self.assertIsNotNone(msg.timestamp)
