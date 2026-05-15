"""
API安全性和金鑰管理模組
負責API金鑰加密存儲、身份驗證和安全配置
"""
import os
import json
import hashlib
import base64
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet
import secrets


class APIKeyManager:
    """API金鑰安全管理器"""

    def __init__(self, config_file: str = None):
        """
        初始化API金鑰管理器

        Args:
            config_file: 配置文件路徑，默認為項目data目錄下的api_keys.enc
        """
        if config_file is None:
            project_root = Path(__file__).parent.parent
            self.config_file = project_root / "data" / "api_keys.enc"
            self.key_file = project_root / "data" / ".key"
        else:
            self.config_file = Path(config_file)
            self.key_file = Path(str(config_file).replace('.enc', '.key'))

        self._cipher = None
        self._keys: Dict[str, Dict[str, Any]] = {}
        self._init_encryption()
        self._load_keys()

    def _init_encryption(self):
        """初始化加密"""
        try:
            if self.key_file.exists():
                with open(self.key_file, 'rb') as f:
                    key = f.read()
            else:
                # 生成新的加密金鑰
                key = Fernet.generate_key()
                self.key_file.parent.mkdir(parents=True, exist_ok=True)
                with open(self.key_file, 'wb') as f:
                    f.write(key)

            self._cipher = Fernet(key)
        except Exception as e:
            print(f"初始化加密失敗: {e}")
            # 回退到簡單的Base64編碼
            self._cipher = None

    def _load_keys(self) -> None:
        """載入加密的API金鑰配置"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'rb') as f:
                    encrypted_data = f.read()

                if self._cipher:
                    decrypted_data = self._cipher.decrypt(encrypted_data)
                    data = json.loads(decrypted_data.decode())
                else:
                    # 簡單解密（開發環境用）
                    decrypted_data = base64.b64decode(encrypted_data)
                    data = json.loads(decrypted_data.decode())

                self._keys = data.get('keys', {})
        except Exception as e:
            print(f"載入API金鑰配置失敗: {e}")
            self._keys = {}

    def _save_keys(self) -> None:
        """儲存加密的API金鑰配置"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)

            data = {
                'last_updated': datetime.now().isoformat(),
                'keys': self._keys
            }

            json_data = json.dumps(data, indent=2, ensure_ascii=False).encode()

            if self._cipher:
                encrypted_data = self._cipher.encrypt(json_data)
            else:
                # 簡單加密（開發環境用）
                encrypted_data = base64.b64encode(json_data)

            with open(self.config_file, 'wb') as f:
                f.write(encrypted_data)

        except Exception as e:
            print(f"儲存API金鑰配置失敗: {e}")

    def add_key(self, name: str, api_key: str, secret_key: str = None,
                provider: str = "binance", description: str = "") -> bool:
        """
        添加API金鑰

        Args:
            name: 金鑰名稱（用於識別）
            api_key: API金鑰
            secret_key: 秘密金鑰（可選）
            provider: 提供商名稱
            description: 描述信息

        Returns:
            bool: 添加成功返回True
        """
        if not self._validate_key_format(api_key):
            print(f"無效的API金鑰格式: {name}")
            return False

        # 加密儲存金鑰
        encrypted_key = self._encrypt_key(api_key)
        encrypted_secret = self._encrypt_key(secret_key) if secret_key else None

        self._keys[name] = {
            'provider': provider,
            'api_key': encrypted_key,
            'secret_key': encrypted_secret,
            'description': description,
            'created_at': datetime.now().isoformat(),
            'last_used': None,
            'rate_limits': {
                'requests_per_minute': 1000,
                'requests_per_hour': 50000
            },
            'enabled': True
        }

        self._save_keys()
        print(f"✅ API金鑰 {name} 添加成功")
        return True

    def get_key(self, name: str) -> Optional[Dict[str, Any]]:
        """
        獲取API金鑰

        Args:
            name: 金鑰名稱

        Returns:
            Optional[Dict]: 金鑰信息，包含解密後的金鑰
        """
        if name not in self._keys or not self._keys[name].get('enabled', True):
            return None

        key_info = self._keys[name].copy()

        try:
            # 解密金鑰
            key_info['api_key'] = self._decrypt_key(key_info['api_key'])
            if key_info.get('secret_key'):
                key_info['secret_key'] = self._decrypt_key(key_info['secret_key'])

            # 更新最後使用時間
            self._keys[name]['last_used'] = datetime.now().isoformat()
            self._save_keys()

            return key_info
        except Exception as e:
            print(f"解密金鑰失敗 {name}: {e}")
            return None

    def remove_key(self, name: str) -> bool:
        """
        移除API金鑰

        Args:
            name: 金鑰名稱

        Returns:
            bool: 移除成功返回True
        """
        if name in self._keys:
            del self._keys[name]
            self._save_keys()
            print(f"🗑️ API金鑰 {name} 已移除")
            return True
        return False

    def disable_key(self, name: str) -> bool:
        """停用API金鑰"""
        if name in self._keys:
            self._keys[name]['enabled'] = False
            self._save_keys()
            print(f"🚫 API金鑰 {name} 已停用")
            return True
        return False

    def enable_key(self, name: str) -> bool:
        """啟用API金鑰"""
        if name in self._keys:
            self._keys[name]['enabled'] = True
            self._save_keys()
            print(f"✅ API金鑰 {name} 已啟用")
            return True
        return False

    def list_keys(self) -> List[Dict[str, Any]]:
        """
        列出所有API金鑰（不包含敏感信息）

        Returns:
            List[Dict]: 金鑰列表（隱藏實際金鑰值）
        """
        result = []
        for name, info in self._keys.items():
            result.append({
                'name': name,
                'provider': info['provider'],
                'description': info['description'],
                'created_at': info['created_at'],
                'last_used': info['last_used'],
                'enabled': info.get('enabled', True)
            })
        return result

    def _validate_key_format(self, api_key: str) -> bool:
        """
        驗證API金鑰格式

        Args:
            api_key: API金鑰字符串

        Returns:
            bool: 格式有效返回True
        """
        if not api_key or not isinstance(api_key, str):
            return False

        # Binance API金鑰通常是64個字符的十六進制字符串
        if len(api_key) < 20:
            return False

        # 檢查是否包含非法字符
        import re
        if not re.match(r'^[A-Za-z0-9\-_\.]+$', api_key):
            return False

        return True

    def _encrypt_key(self, key: str) -> str:
        """
        加密API金鑰

        Args:
            key: 原始金鑰

        Returns:
            str: 加密後的金鑰
        """
        if not key:
            return ""

        try:
            if self._cipher:
                return self._cipher.encrypt(key.encode()).decode()
            else:
                # 簡單編碼（開發環境用）
                return base64.b64encode(key.encode()).decode()
        except Exception:
            return key  # 如果加密失敗，返回原始值

    def _decrypt_key(self, encrypted_key: str) -> str:
        """
        解密API金鑰

        Args:
            encrypted_key: 加密後的金鑰

        Returns:
            str: 原始金鑰
        """
        if not encrypted_key:
            return ""

        try:
            if self._cipher:
                return self._cipher.decrypt(encrypted_key.encode()).decode()
            else:
                # 簡單解碼（開發環境用）
                return base64.b64decode(encrypted_key.encode()).decode()
        except Exception:
            return encrypted_key  # 如果解密失敗，返回輸入值


class APIAuthManager:
    """API身份驗證和速率限制管理器"""

    def __init__(self, key_manager: APIKeyManager):
        self.key_manager = key_manager
        self._rate_limiters: Dict[str, Dict[str, Any]] = {}

    def authenticate_request(self, provider: str, api_key: str) -> tuple[bool, str]:
        """
        驗證API請求

        Args:
            provider: API提供商
            api_key: API金鑰

        Returns:
            tuple[bool, str]: (是否驗證成功, 錯誤信息)
        """
        # 檢查金鑰是否存在且啟用
        key_info = None
        key_name = None

        for name, info in self.key_manager._keys.items():
            if (info['provider'] == provider and
                info.get('enabled', True) and
                self.key_manager._decrypt_key(info['api_key']) == api_key):
                key_info = info
                key_name = name
                break

        if not key_info:
            return False, "無效或停用的API金鑰"

        # 檢查速率限制
        if not self._check_rate_limit(api_key, key_info.get('rate_limits', {})):
            return False, "超出速率限制，請稍後重試"

        return True, f"驗證成功 ({key_name})"

    def _check_rate_limit(self, api_key: str, limits: Dict[str, int]) -> bool:
        """
        檢查速率限制

        Args:
            api_key: API金鑰
            limits: 速率限制配置

        Returns:
            bool: 在限制內返回True
        """
        now = datetime.now()
        key_hash = hashlib.md5(api_key.encode()).hexdigest()

        if key_hash not in self._rate_limiters:
            self._rate_limiters[key_hash] = {
                'minute_count': 0,
                'hour_count': 0,
                'minute_start': now,
                'hour_start': now
            }

        limiter = self._rate_limiters[key_hash]

        # 重置計數器
        if (now - limiter['minute_start']).seconds >= 60:
            limiter['minute_count'] = 0
            limiter['minute_start'] = now

        if (now - limiter['hour_start']).seconds >= 3600:
            limiter['hour_count'] = 0
            limiter['hour_start'] = now

        # 檢查限制
        max_per_minute = limits.get('requests_per_minute', 1000)
        max_per_hour = limits.get('requests_per_hour', 50000)

        if limiter['minute_count'] >= max_per_minute:
            return False

        if limiter['hour_count'] >= max_per_hour:
            return False

        # 增加計數
        limiter['minute_count'] += 1
        limiter['hour_count'] += 1

        return True


# 全域實例
api_key_manager = APIKeyManager()
api_auth_manager = APIAuthManager(api_key_manager)


def setup_demo_keys():
    """
    設定演示用API金鑰（僅供開發測試）
    
    ⚠️ 警告：生產環境請勿使用此函數
    ⚠️ 注意：這些是虛構的金鑰，僅用於演示
    
    使用方式：
        from config.api_security import setup_demo_keys
        setup_demo_keys()
    """
    print("⚠️ 設定演示用API金鑰（僅供開發測試）")

    demo_keys = [
        {
            'name': 'binance_demo',
            'api_key': 'demo_api_key_for_binance_trading_bot_123456789',
            'secret_key': 'demo_secret_key_for_binance_trading_bot_987654321',
            'provider': 'binance',
            'description': 'Binance演示API金鑰（僅供測試）'
        }
    ]

    for key_info in demo_keys:
        api_key_manager.add_key(**key_info)


# ============================================================
# 注意：此安全配置文件僅供導入使用，不作為程式入口
# 主程式入口：python core/gui_main.py
# 
# 如需測試API金鑰管理功能，請在主程式中調用相關函數：
#   from config.api_security import api_key_manager, setup_demo_keys
#   setup_demo_keys()
#   keys = api_key_manager.list_keys()
# ============================================================
