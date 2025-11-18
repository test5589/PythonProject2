from typing import Dict, Optional, List

from modules.utils.logger import get_logger
from config.backfill_config import BackfillConfig
from config.trading_config import TradingConfig
from modules.utils.exceptions import BackfillInsertError, BackfillConfigurationError

logger = get_logger("data_validator")

# 使用集中配置的日誌聚合參數
LOG_AGGREGATION_CHUNK = BackfillConfig.LOG_AGGREGATION_CHUNK


class LogAggregationValidator:
    """確保不同類型的日誌聚合使用相同設定"""

    def __init__(self, expected_chunk: int = LOG_AGGREGATION_CHUNK):
        self.expected_chunk = expected_chunk
        self._labels: Dict[str, int] = {}

    def assert_chunk(self, label: str, chunk_size: int):
        self._labels[label] = chunk_size
        if chunk_size != self.expected_chunk:
            raise BackfillConfigurationError(
                f"日誌聚合設定錯誤：{label} 使用 {chunk_size} 筆/行，但規範為 {self.expected_chunk}"
            )

    def get_chunk_size(self) -> int:
        return self.expected_chunk


class BackfillErrorMonitor:
    """監聽回補進度訊息，只要出現關鍵錯誤字詞便立即拋出例外以終止流程"""

    DEFAULT_KEYWORDS = BackfillConfig.ERROR_KEYWORDS

    def __init__(self, keywords: Optional[List[str]] = None):
        self.keywords = keywords or self.DEFAULT_KEYWORDS

    def wrap_progress_cb(self, progress_cb: Optional[callable]):
        """回傳一個代理 callback：先將訊息傳給原 callback，再檢查是否含有錯誤關鍵字"""

        if progress_cb is None:
            return None

        def _wrapped(message: str):
            progress_cb(message)
            self._inspect_message(message)

        return _wrapped

    def _inspect_message(self, message: Optional[str]):
        if not message:
            return
        for keyword in self.keywords:
            if keyword in message:
                logger.error(f"🚨 偵測到回補錯誤訊息: {message}")
                raise BackfillInsertError(message)


def validate_symbol_binding(bound_symbols: List[str]) -> None:
    """驗證選擇的貨幣對是否都是有效的（在 SUPPORTED_SYMBOLS 中）"""
    if not bound_symbols:
        raise BackfillConfigurationError("未選擇任何貨幣對")

    # 檢查是否所有選擇的貨幣對都是有效的
    supported = {sym.upper() for sym in TradingConfig.SUPPORTED_SYMBOLS}
    actual = {sym.upper() for sym in bound_symbols}
    invalid = actual - supported

    if invalid:
        raise BackfillConfigurationError(
            f"選擇了無效的貨幣對: {', '.join(sorted(invalid))}\n"
            f"請只選擇配置中支持的貨幣對"
        )

    logger.info(f"✅ 貨幣對驗證通過：{len(bound_symbols)} 個有效貨幣對")
