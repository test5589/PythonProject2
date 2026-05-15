"""
auto_heal_backfill.py - 自動修補統一管理
使用模組化結構管理自動修補功能
"""

from .backfill.auto_heal_core import start_smart_auto_heal, stop_auto_heal
from .backfill.backfill_scanner import scan_incomplete_seconds

# 向後相容性 - 重新導出所有主要函數
__all__ = [
    'start_smart_auto_heal',
    'stop_auto_heal', 
    'scan_incomplete_seconds'
]
