"""
API模組測試
"""
import unittest
from unittest.mock import patch, MagicMock, Mock
import requests
import sys
import os

# 添加項目路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from modules.utils.api.api_client import BinanceAPIClient
from modules.utils.exceptions import APIError, NetworkError


class TestBinanceAPIClient(unittest.TestCase):
    """Binance API客戶端測試"""
    
    def setUp(self) -> None:
        """測試前準備"""
        self.client = BinanceAPIClient()
    
    def test_client_initialization(self) -> None:
        """測試客戶端初始化"""
        self.assertEqual(self.client.base_url, "https://api.binance.com")
        self.assertEqual(self.client.timeout, 10)
        self.assertEqual(self.client.max_retries, 3)
        self.assertIsNotNone(self.client.session)
    
    def test_custom_initialization(self) -> None:
        """測試自定義初始化"""
        custom_client = BinanceAPIClient(
            base_url="https://testnet.binance.vision",
            timeout=20
        )
        
        self.assertEqual(custom_client.base_url, "https://testnet.binance.vision")
        self.assertEqual(custom_client.timeout, 20)
    
    @patch('modules.utils.api.api_client.requests.Session.get')
    def test_successful_request(self, mock_get: MagicMock) -> None:
        """測試成功的請求"""
        # Mock 成功回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": "test"}
        mock_get.return_value = mock_response
        
        result = self.client._make_request('GET', '/api/v3/time')
        
        self.assertEqual(result, {"success": True, "data": "test"})
        mock_get.assert_called_once()
    
    @patch('modules.utils.api.api_client.requests.Session.get')
    def test_api_error_handling(self, mock_get: MagicMock) -> None:
        """測試API錯誤處理"""
        # Mock API錯誤回應
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"code": -1121, "msg": "Invalid symbol"}
        mock_get.return_value = mock_response
        
        with self.assertRaises(APIError) as context:
            self.client._make_request('GET', '/api/v3/klines', {"symbol": "INVALID"})
        
        self.assertIn("Invalid symbol", str(context.exception))
    
    @patch('modules.utils.api.api_client.requests.Session.get')
    def test_rate_limit_retry(self, mock_get: MagicMock) -> None:
        """測試速率限制重試"""
        # 第一次請求返回429，第二次成功
        mock_response_429 = Mock()
        mock_response_429.status_code = 429
        
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"success": True}
        
        mock_get.side_effect = [mock_response_429, mock_response_200]
        
        with patch('time.sleep'):  # 避免實際延遲
            result = self.client._make_request('GET', '/api/v3/time')
        
        self.assertEqual(result, {"success": True})
        self.assertEqual(mock_get.call_count, 2)
    
    @patch('modules.utils.api.api_client.requests.Session.get')
    def test_timeout_handling(self, mock_get: MagicMock) -> None:
        """測試超時處理"""
        mock_get.side_effect = requests.exceptions.Timeout()
        
        with patch('time.sleep'):  # 避免實際延遲
            with self.assertRaises(NetworkError) as context:
                self.client._make_request('GET', '/api/v3/time')
        
        self.assertIn("請求超時", str(context.exception))
        # 應該重試3次加上原始請求
        self.assertEqual(mock_get.call_count, 4)
    
    @patch('modules.utils.api.api_client.requests.Session.get')
    def test_connection_error_handling(self, mock_get: MagicMock) -> None:
        """測試連接錯誤處理"""
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        with patch('time.sleep'):  # 避免實際延遲
            with self.assertRaises(NetworkError) as context:
                self.client._make_request('GET', '/api/v3/time')
        
        self.assertIn("網路連線錯誤", str(context.exception))
        self.assertEqual(mock_get.call_count, 4)


class TestAPIConfig(unittest.TestCase):
    """API配置測試"""
    
    def test_trading_config_api_settings(self) -> None:
        """測試交易配置中的API設定"""
        from config.trading_config import TradingConfig
        
        # 檢查API配置
        self.assertIsInstance(TradingConfig.API_RATE_LIMIT, int)
        self.assertIsInstance(TradingConfig.API_TIMEOUT, int)
        self.assertIsInstance(TradingConfig.API_MAX_RETRIES, int)
        
        # 檢查合理的預設值
        self.assertGreater(TradingConfig.API_RATE_LIMIT, 0)
        self.assertGreater(TradingConfig.API_TIMEOUT, 0)
        self.assertGreaterEqual(TradingConfig.API_MAX_RETRIES, 1)


class TestExceptions(unittest.TestCase):
    """異常類測試"""
    
    def test_api_error(self) -> None:
        """測試API錯誤異常"""
        from modules.utils.exceptions import APIError
        
        error = APIError("測試錯誤", {"code": 400})
        
        self.assertEqual(error.message, "測試錯誤")
        self.assertEqual(error.details, {"code": 400})
        self.assertIn("測試錯誤", str(error))
        self.assertIn("code=400", str(error))
    
    def test_network_error(self) -> None:
        """測試網路錯誤異常"""
        from modules.utils.exceptions import NetworkError
        
        error = NetworkError("連接失敗")
        
        self.assertEqual(error.message, "連接失敗")
        self.assertEqual(str(error), "連接失敗")


if __name__ == '__main__':
    # 創建測試套件
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加測試類
    suite.addTests(loader.loadTestsFromTestCase(TestBinanceAPIClient))
    suite.addTests(loader.loadTestsFromTestCase(TestAPIConfig))
    suite.addTests(loader.loadTestsFromTestCase(TestExceptions))
    
    # 運行測試
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print(f"\nAPI測試結果:")
    print(f"運行測試: {result.testsRun}")
    print(f"失敗: {len(result.failures)}")
    print(f"錯誤: {len(result.errors)}")
