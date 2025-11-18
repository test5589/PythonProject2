"""
數據庫模組測試
"""
import unittest
import os
import tempfile
import sqlite3
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# 添加項目路徑
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.utils.database.db_core import DatabaseCore
from modules.utils.database.data_manager import DataManager, insert_data, batch_insert_data


class TestDatabaseCore(unittest.TestCase):
    """數據庫核心功能測試"""
    
    def setUp(self) -> None:
        """測試前準備"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # 使用臨時數據庫
        self.db_core = DatabaseCore()
        self.original_db_path = self.db_core.db_path
        self.db_core.db_path = self.temp_db.name
    
    def tearDown(self) -> None:
        """測試後清理"""
        self.db_core.db_path = self.original_db_path
        try:
            os.unlink(self.temp_db.name)
        except FileNotFoundError:
            pass
    
    def test_database_initialization(self) -> None:
        """測試數據庫初始化"""
        self.db_core.init_database()
        
        # 檢查數據庫文件是否創建
        self.assertTrue(os.path.exists(self.temp_db.name))
        
        # 檢查表格是否創建
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='historical_data'")
        result = cursor.fetchone()
        conn.close()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0], 'historical_data')
    
    def test_table_structure(self) -> None:
        """測試表格結構"""
        self.db_core.init_database()
        
        table_info = self.db_core.get_table_info()
        self.assertIsNotNone(table_info)
        
        # 檢查必要欄位
        column_names = [col[1] for col in table_info['columns']]
        required_columns = ['timestamp', 'category', 'symbol', 'interval', 
                          'open', 'high', 'low', 'close', 'volume']
        
        for col in required_columns:
            self.assertIn(col, column_names)
    
    def test_query_ohlcv(self) -> None:
        """測試OHLCV查詢"""
        self.db_core.init_database()
        
        # 查詢空表
        result = self.db_core.query_ohlcv('crypto', 'BTCUSDT', 60, limit=5)
        self.assertEqual(len(result), 0)


class TestDataManager(unittest.TestCase):
    """數據管理器測試"""
    
    def setUp(self) -> None:
        """測試前準備"""
        self.data_manager = DataManager()
    
    def test_data_manager_initialization(self) -> None:
        """測試數據管理器初始化"""
        self.assertIsNotNone(self.data_manager.db_core)
        self.assertIsInstance(self.data_manager.priority_map, dict)
        self.assertIsInstance(self.data_manager.interval_map, dict)
    
    def test_priority_mapping(self) -> None:
        """測試優先級映射"""
        expected_priorities = {'real': 1, 'interpolated': 2, 'Aggregation': 3, 'inferior-Aggregation': 4}
        self.assertEqual(self.data_manager.priority_map, expected_priorities)
    
    @patch('modules.utils.database.data_manager.DataManager.insert_single_data')
    def test_insert_data_function(self, mock_insert: MagicMock) -> None:
        """測試插入數據函數"""
        test_kline = {'open': 50000, 'high': 51000, 'low': 49000, 'close': 50500, 'volume': 100}
        
        insert_data('crypto', 'BTCUSDT', 60, test_kline)
        
        mock_insert.assert_called_once_with(
            'crypto', 'BTCUSDT', 60, test_kline, 
            'real', None, None, None, None
        )


class TestConfigValidation(unittest.TestCase):
    """配置驗證測試"""
    
    def test_trading_config_import(self) -> None:
        """測試交易配置導入"""
        from config.trading_config import TradingConfig
        
        # 檢查重要配置
        self.assertIsInstance(TradingConfig.SUPPORTED_SYMBOLS, list)
        self.assertIsInstance(TradingConfig.INTERVAL_SECONDS, dict)
        self.assertGreater(len(TradingConfig.SUPPORTED_SYMBOLS), 0)
    
    def test_interval_validation(self) -> None:
        """測試時間間隔驗證"""
        from config.trading_config import TradingConfig
        
        # 測試有效間隔
        self.assertTrue(TradingConfig.is_valid_interval('1m'))
        self.assertTrue(TradingConfig.is_valid_interval('1h'))
        
        # 測試無效間隔
        self.assertFalse(TradingConfig.is_valid_interval('invalid'))
    
    def test_symbol_validation(self) -> None:
        """測試貨幣對驗證"""
        from config.trading_config import TradingConfig
        
        # 測試有效貨幣對
        self.assertTrue(TradingConfig.is_valid_symbol('BTCUSDT'))
        
        # 測試無效貨幣對
        self.assertFalse(TradingConfig.is_valid_symbol('INVALID'))


if __name__ == '__main__':
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    suite.addTests(loader.loadTestsFromTestCase(TestDatabaseCore))
    suite.addTests(loader.loadTestsFromTestCase(TestDataManager))
    suite.addTests(loader.loadTestsFromTestCase(TestConfigValidation))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # 輸出結果
    print(f"\n測試結果:")
    print(f"運行測試: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
    
    if result.failures:
        print("\n失敗的測試:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\n錯誤的測試:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
