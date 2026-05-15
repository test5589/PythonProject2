"""
API 配置範例 - 展示如何配置多個 API 來源
"""

from modules.utils.api_manager import APIManager, APIConfig, APIType, api_manager

def setup_multiple_apis():
    """設定多個 API 來源的範例"""
    
    # 1. 幣安官方 API（已經在 APIManager 初始化時加入）
    
    # 2. 幣安測試網 API（如果需要）
    binance_testnet = APIConfig(
        name="binance_testnet",
        url="https://testnet.binance.vision",
        api_type=APIType.BINANCE,
        rate_limit=600,  # 測試網限制較低
        weight_per_request=1,
        enabled=False  # 預設停用
    )
    api_manager.add_api(binance_testnet)
    
    # 3. 自訂 API（例如第三方代理）
    custom_proxy = APIConfig(
        name="custom_proxy_1",
        url="https://api.binance-proxy.com",
        api_type=APIType.CUSTOM,
        rate_limit=1000,
        weight_per_request=1,
        enabled=False  # 預設停用
    )
    api_manager.add_api(custom_proxy)
    
    # 4. 備用 API
    backup_api = APIConfig(
        name="backup_api",
        url="https://backup.binance-api.com",
        api_type=APIType.CUSTOM,
        rate_limit=800,
        weight_per_request=1,
        enabled=False  # 預設停用
    )
    api_manager.add_api(backup_api)
    
    print("✅ 已設定多個 API 來源")
    print("📋 可用的 API:")
    for api in api_manager.list_apis():
        status = "啟用" if api.enabled else "停用"
        print(f"  - {api.name}: {api.url} ({status})")

def switch_to_testnet():
    """切換到測試網 API"""
    api_manager.enable_api("binance_testnet")
    api_manager.set_default_api("binance_testnet")
    print("✅ 已切換到測試網 API")

def switch_to_mainnet():
    """切換回主網 API"""
    api_manager.set_default_api("binance_official")
    print("✅ 已切換回主網 API")

def list_api_status():
    """列出所有 API 狀態"""
    print("📊 API 狀態:")
    for api in api_manager.list_apis():
        status = "啟用" if api.enabled else "停用"
        default = " (預設)" if api.name == api_manager._default_api else ""
        print(f"  - {api.name}: {api.url} ({status}){default}")

# 注意：此配置文件僅供導入使用，不作為程式入口
# 如需測試配置，請從主程式 (core/gui_main.py) 調用相關函數
