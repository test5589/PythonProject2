"""
test_async_backfill.py - 異步回補架構測試

測試 MessageSender 和 AsyncBackfillRunner 的核心功能
"""

import unittest
import time
import threading
from queue import Queue
from typing import List
from core.async_backfill_runner import MessageSender, BackfillMessage


class TestMessageSender(unittest.TestCase):
    """MessageSender 測試類"""
    
    def setUp(self):
        """測試前準備"""
        self.message_queue = Queue()
        self.received_messages: List[str] = []
        
        # 模擬 GUI 更新函數
        def mock_gui_update(msg: str):
            self.received_messages.append(msg)
        
        self.gui_update = mock_gui_update
        self.sender = MessageSender(self.message_queue, self.gui_update)
    
    def tearDown(self):
        """測試後清理"""
        if self.sender and self.sender.running:
            self.sender.stop()
        self.message_queue = None
        self.received_messages.clear()
    
    def test_message_sender_initialization(self):
        """測試 MessageSender 初始化"""
        self.assertIsNotNone(self.sender)
        self.assertFalse(self.sender.running)
        self.assertEqual(self.message_queue.qsize(), 0)
    
    def test_message_sender_start_stop(self):
        """測試 MessageSender 啟動和停止"""
        # 啟動
        self.sender.start()
        self.assertTrue(self.sender.running)
        time.sleep(0.1)  # 等待線程啟動
        
        # 停止
        self.sender.stop()
        time.sleep(0.1)  # 等待線程停止
        self.assertFalse(self.sender.running)
    
    def test_send_single_message(self):
        """測試發送單條訊息"""
        self.sender.start()
        
        # 發送訊息
        test_message = "🧪 測試訊息"
        self.sender.send(test_message)
        
        # 等待訊息處理
        time.sleep(0.2)
        
        # 驗證
        self.assertIn(test_message, self.received_messages)
        
        self.sender.stop()
    
    def test_send_multiple_messages(self):
        """測試發送多條訊息"""
        self.sender.start()
        
        # 發送多條訊息
        messages = [
            "📦 訊息 1",
            "📦 訊息 2",
            "📦 訊息 3",
            "📦 訊息 4",
            "📦 訊息 5",
        ]
        
        for msg in messages:
            self.sender.send(msg)
        
        # 等待訊息處理
        time.sleep(0.5)
        
        # 驗證所有訊息都收到了
        for msg in messages:
            self.assertIn(msg, self.received_messages)
        
        self.sender.stop()
    
    def test_message_order_preserved(self):
        """測試訊息順序保持"""
        self.sender.start()
        
        # 發送有序訊息
        messages = [f"📦 訊息 {i}" for i in range(10)]
        
        for msg in messages:
            self.sender.send(msg)
        
        # 等待訊息處理
        time.sleep(0.5)
        
        # 驗證順序
        for i, msg in enumerate(messages):
            self.assertEqual(self.received_messages[i], msg)
        
        self.sender.stop()
    
    def test_concurrent_send(self):
        """測試並發發送訊息"""
        self.sender.start()
        
        def send_messages(prefix: str, count: int):
            for i in range(count):
                self.sender.send(f"{prefix} {i}")
        
        # 創建多個線程同時發送
        threads = []
        for i in range(3):
            t = threading.Thread(target=send_messages, args=(f"線程{i}", 5))
            threads.append(t)
            t.start()
        
        # 等待所有線程完成
        for t in threads:
            t.join()
        
        # 等待訊息處理
        time.sleep(0.5)
        
        # 驗證訊息總數
        self.assertEqual(len(self.received_messages), 15)  # 3線程 x 5訊息
        
        self.sender.stop()
    
    def test_send_without_start(self):
        """測試未啟動時發送訊息"""
        # 不啟動，直接發送
        self.sender.send("測試訊息")
        
        # 訊息應該進入隊列
        self.assertGreater(self.message_queue.qsize(), 0)
        
        # 但不會被處理
        time.sleep(0.2)
        self.assertEqual(len(self.received_messages), 0)
    
    def test_stop_flushes_queue(self):
        """測試停止時清空隊列"""
        self.sender.start()
        
        # 發送大量訊息
        for i in range(100):
            self.sender.send(f"訊息 {i}")
        
        # 立即停止
        self.sender.stop()
        time.sleep(0.5)
        
        # 驗證隊列被清空或大部分訊息已處理
        # 注意：由於並發，可能有少量訊息未處理
        self.assertGreater(len(self.received_messages), 50)


class TestBackfillMessage(unittest.TestCase):
    """BackfillMessage 測試類"""
    
    def test_message_creation(self):
        """測試訊息創建"""
        msg = BackfillMessage(
            level="INFO",
            content="測試內容",
            symbol="BTCUSDT",
            progress=50.0
        )
        
        self.assertEqual(msg.level, "INFO")
        self.assertEqual(msg.content, "測試內容")
        self.assertEqual(msg.symbol, "BTCUSDT")
        self.assertEqual(msg.progress, 50.0)
    
    def test_message_default_values(self):
        """測試訊息默認值"""
        msg = BackfillMessage(
            level="INFO",
            content="測試內容"
        )
        
        self.assertIsNone(msg.symbol)
        self.assertIsNone(msg.progress)
    
    def test_message_representation(self):
        """測試訊息字串表示"""
        msg = BackfillMessage(
            level="ERROR",
            content="錯誤訊息",
            symbol="ETHUSDT",
            progress=75.5
        )
        
        msg_str = str(msg)
        self.assertIn("ERROR", msg_str)
        self.assertIn("錯誤訊息", msg_str)
        self.assertIn("ETHUSDT", msg_str)


class TestMessageSenderEdgeCases(unittest.TestCase):
    """MessageSender 邊界情況測試"""
    
    def setUp(self):
        """測試前準備"""
        self.message_queue = Queue()
        self.received_messages: List[str] = []
        
        def mock_gui_update(msg: str):
            self.received_messages.append(msg)
        
        self.gui_update = mock_gui_update
        self.sender = MessageSender(self.message_queue, self.gui_update)
    
    def tearDown(self):
        """測試後清理"""
        if self.sender and self.sender.running:
            self.sender.stop()
    
    def test_empty_message(self):
        """測試空訊息"""
        self.sender.start()
        self.sender.send("")
        time.sleep(0.2)
        
        # 空訊息也應該被處理
        self.assertIn("", self.received_messages)
        
        self.sender.stop()
    
    def test_unicode_message(self):
        """測試 Unicode 訊息"""
        self.sender.start()
        
        unicode_msgs = [
            "✅ 成功",
            "❌ 失敗",
            "🚀 啟動",
            "📊 數據",
            "⚠️ 警告",
        ]
        
        for msg in unicode_msgs:
            self.sender.send(msg)
        
        time.sleep(0.5)
        
        for msg in unicode_msgs:
            self.assertIn(msg, self.received_messages)
        
        self.sender.stop()
    
    def test_very_long_message(self):
        """測試超長訊息"""
        self.sender.start()
        
        long_msg = "測試" * 1000  # 4000 字符
        self.sender.send(long_msg)
        
        time.sleep(0.2)
        
        self.assertIn(long_msg, self.received_messages)
        
        self.sender.stop()
    
    def test_restart_sender(self):
        """測試重新啟動"""
        # 第一次啟動
        self.sender.start()
        self.sender.send("訊息1")
        time.sleep(0.2)
        self.sender.stop()
        time.sleep(0.2)
        
        # 清空接收列表
        self.received_messages.clear()
        
        # 第二次啟動
        self.sender.start()
        self.sender.send("訊息2")
        time.sleep(0.2)
        
        self.assertIn("訊息2", self.received_messages)
        
        self.sender.stop()


class TestMessageSenderPerformance(unittest.TestCase):
    """MessageSender 性能測試"""
    
    def setUp(self):
        """測試前準備"""
        self.message_queue = Queue()
        self.received_count = 0
        
        def mock_gui_update(msg: str):
            self.received_count += 1
        
        self.gui_update = mock_gui_update
        self.sender = MessageSender(self.message_queue, self.gui_update)
    
    def tearDown(self):
        """測試後清理"""
        if self.sender and self.sender.running:
            self.sender.stop()
    
    def test_high_throughput(self):
        """測試高吞吐量"""
        self.sender.start()
        
        message_count = 1000
        start_time = time.time()
        
        # 發送大量訊息
        for i in range(message_count):
            self.sender.send(f"訊息 {i}")
        
        # 等待處理完成
        time.sleep(2.0)
        
        elapsed = time.time() - start_time
        
        # 驗證大部分訊息被處理
        self.assertGreater(self.received_count, message_count * 0.9)
        
        # 計算吞吐量
        throughput = self.received_count / elapsed
        print(f"\n吞吐量: {throughput:.2f} 訊息/秒")
        
        self.sender.stop()


def run_tests():
    """運行所有測試"""
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    suite.addTests(loader.loadTestsFromTestCase(TestMessageSender))
    suite.addTests(loader.loadTestsFromTestCase(TestBackfillMessage))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageSenderEdgeCases))
    suite.addTests(loader.loadTestsFromTestCase(TestMessageSenderPerformance))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 返回測試結果
    return result.wasSuccessful()


if __name__ == '__main__':
    success = run_tests()
    exit(0 if success else 1)
