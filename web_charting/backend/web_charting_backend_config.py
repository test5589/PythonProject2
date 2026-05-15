"""web_charting_backend_config.py

後端專用的設定載入器，避免與專案根目錄的 `config` 套件名稱衝突。

- 這個模組會動態載入同目錄下的 `config.py`
- 但在 sys.modules 裡使用自訂名稱，不佔用頂層的 `config`
- 對外只提供 `config` 與 `Config` 兩個物件給 backend 其他模組使用
"""

from pathlib import Path
import importlib.util

# 取得 backend/config.py 的實際路徑
_CONFIG_PATH = Path(__file__).with_name("config.py")

# 建立動態載入的模組 spec
_spec = importlib.util.spec_from_file_location(
    "web_charting.backend._config",  # 自訂模組名稱，避免佔用頂層 `config`
    _CONFIG_PATH,
)
if _spec is None or _spec.loader is None:
    raise ImportError(f"無法載入後端設定模組: {_CONFIG_PATH}")

_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)

# 對外暴露與原本 backend/config.py 一樣的介面
Config = _module.Config
config = _module.config
