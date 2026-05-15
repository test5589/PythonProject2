"""
API 管理器 - 統一處理多個 API 來源
支援未來擴展不同的 API 地址
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class APIType(Enum):
    """API 類型枚舉"""
    BINANCE = "binance"
    CUSTOM = "custom"

@dataclass
class APIConfig:
    """API 配置"""
    name: str
    url: str
    api_type: APIType
    rate_limit: int = 1200  # 每分鐘請求限制
    weight_per_request: int = 1  # 每個請求的權重
    enabled: bool = True

class APIManager:
    """API 管理器 - 統一管理多個 API 來源"""
    
    def __init__(self):
        self._apis: Dict[str, APIConfig] = {}
        self._default_api = None
        self._init_default_apis()
    
    def _init_default_apis(self):
        """初始化預設 API"""
        # 幣安官方 API
        binance_config = APIConfig(
            name="binance_official",
            url="https://api.binance.com",
            api_type=APIType.BINANCE,
            rate_limit=1200,
            weight_per_request=1
        )
        self.add_api(binance_config)
        self._default_api = "binance_official"
    
    def add_api(self, config: APIConfig):
        """新增 API 配置"""
        self._apis[config.name] = config
    
    def get_api(self, name: Optional[str] = None) -> APIConfig:
        """獲取 API 配置"""
        if name is None:
            name = self._default_api
        
        if name not in self._apis:
            raise ValueError(f"API '{name}' 不存在")
        
        return self._apis[name]
    
    def get_default_api(self) -> APIConfig:
        """獲取預設 API"""
        return self.get_api(self._default_api)
    
    def set_default_api(self, name: str):
        """設定預設 API"""
        if name not in self._apis:
            raise ValueError(f"API '{name}' 不存在")
        self._default_api = name
    
    def list_apis(self) -> List[APIConfig]:
        """列出所有 API"""
        return list(self._apis.values())
    
    def get_enabled_apis(self) -> List[APIConfig]:
        """獲取所有啟用的 API"""
        return [api for api in self._apis.values() if api.enabled]
    
    def disable_api(self, name: str):
        """停用 API"""
        if name in self._apis:
            self._apis[name].enabled = False
    
    def enable_api(self, name: str):
        """啟用 API"""
        if name in self._apis:
            self._apis[name].enabled = True
    
    def get_api_by_url(self, url: str) -> Optional[APIConfig]:
        """根據 URL 獲取 API 配置"""
        for api in self._apis.values():
            if api.url == url:
                return api
        return None

# 全域 API 管理器實例
api_manager = APIManager()

def get_api_url(name: Optional[str] = None) -> str:
    """獲取 API URL"""
    return api_manager.get_api(name).url

def get_default_api_url() -> str:
    """獲取預設 API URL"""
    return api_manager.get_default_api().url

def is_valid_api_url(url: str) -> bool:
    """檢查是否為有效的 API URL"""
    return api_manager.get_api_by_url(url) is not None
