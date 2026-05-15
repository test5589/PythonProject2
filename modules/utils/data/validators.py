"""validators.py - 統一資料驗證模組"""

from datetime import datetime, timezone
from typing import Tuple, Optional
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from config.trading_config import TradingConfig
from modules.utils.exceptions import ValidationError


class DataValidator:
    """統一資料驗證類別"""
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """
        驗證交易對是否有效
        
        Args:
            symbol: 交易對字串
            
        Returns:
            str: 標準化的交易對（大寫）
            
        Raises:
            ValidationError: 無效的交易對
        """
        if not symbol:
            raise ValidationError("交易對不能為空")
        
        symbol = symbol.upper().strip()
        if not TradingConfig.is_valid_symbol(symbol):
            raise ValidationError(
                f"無效的交易對：{symbol}\n"
                f"目前支持 {len(TradingConfig.SUPPORTED_SYMBOLS)} 個貨幣對\n"
                f"請使用貨幣選擇器選擇有效的貨幣對"
            )
        return symbol
    
    @staticmethod
    def validate_interval(interval: str) -> str:
        """
        驗證時間間隔是否有效
        
        Args:
            interval: 間隔字串（如 "1m", "1h"）
            
        Returns:
            str: 標準化的間隔
            
        Raises:
            ValidationError: 無效的間隔
        """
        if not interval:
            raise ValidationError("間隔不能為空")
        
        interval = interval.lower().strip()
        if not TradingConfig.is_valid_interval(interval):
            supported = ", ".join(TradingConfig.SUPPORTED_INTERVALS.keys())
            raise ValidationError(
                f"無效的間隔：{interval}\n"
                f"支援的間隔：{supported}"
            )
        return interval
    
    @staticmethod
    def validate_time_range(start: datetime, end: datetime) -> Tuple[datetime, datetime]:
        """
        驗證時間範圍是否有效
        
        Args:
            start: 開始時間
            end: 結束時間
            
        Returns:
            Tuple[datetime, datetime]: 驗證後的時間範圍
            
        Raises:
            ValidationError: 無效的時間範圍
        """
        if not isinstance(start, datetime):
            raise ValidationError("開始時間必須是 datetime 物件")
        
        if not isinstance(end, datetime):
            raise ValidationError("結束時間必須是 datetime 物件")
        
        if start >= end:
            raise ValidationError(
                f"開始時間必須早於結束時間\n"
                f"開始：{start}\n"
                f"結束：{end}"
            )
        
        # 檢查是否有時區資訊
        if start.tzinfo is None:
            raise ValidationError("開始時間缺少時區資訊")
        
        if end.tzinfo is None:
            raise ValidationError("結束時間缺少時區資訊")
        
        return start, end
    
    @staticmethod
    def validate_category(category: str) -> str:
        """
        驗證資產分類
        
        Args:
            category: 資產分類
            
        Returns:
            str: 標準化的分類
            
        Raises:
            ValidationError: 無效的分類
        """
        if not category:
            raise ValidationError("資產分類不能為空")
        
        category = category.strip().lower()
        
        # 允許的分類
        allowed_categories = ["crypto", "spot", "futures", "options"]
        
        if category not in allowed_categories:
            raise ValidationError(
                f"無效的資產分類：{category}\n"
                f"允許的分類：{', '.join(allowed_categories)}"
            )
        
        return category
    
    @staticmethod
    def validate_kline_data(kline: dict) -> dict:
        """
        驗證 K 線資料結構
        
        Args:
            kline: K 線資料字典
            
        Returns:
            dict: 驗證後的 K 線資料
            
        Raises:
            ValidationError: 無效的 K 線資料
        """
        if not isinstance(kline, dict):
            raise ValidationError("K 線資料必須是字典")
        
        # 必要欄位
        required_fields = ['open', 'high', 'low', 'close', 'volume']
        missing_fields = [f for f in required_fields if f not in kline]
        
        if missing_fields:
            raise ValidationError(
                f"K 線資料缺少必要欄位：{', '.join(missing_fields)}"
            )
        
        # 驗證數值
        try:
            open_price = float(kline['open'])
            high_price = float(kline['high'])
            low_price = float(kline['low'])
            close_price = float(kline['close'])
            volume = float(kline['volume'])
            
            # 檢查邏輯
            if high_price < low_price:
                raise ValidationError(
                    f"最高價 ({high_price}) 不能低於最低價 ({low_price})"
                )
            
            if open_price > high_price or open_price < low_price:
                raise ValidationError(
                    f"開盤價 ({open_price}) 超出最高/最低價範圍 [{low_price}, {high_price}]"
                )
            
            if close_price > high_price or close_price < low_price:
                raise ValidationError(
                    f"收盤價 ({close_price}) 超出最高/最低價範圍 [{low_price}, {high_price}]"
                )
            
            if volume < 0:
                raise ValidationError(f"成交量 ({volume}) 不能為負數")
            
        except (ValueError, TypeError) as e:
            raise ValidationError(f"K 線資料數值格式錯誤：{e}")
        
        return kline
    
    @staticmethod
    def validate_limit(limit: int, max_limit: int = 1000) -> int:
        """
        驗證查詢數量限制
        
        Args:
            limit: 查詢數量
            max_limit: 最大限制
            
        Returns:
            int: 驗證後的限制
            
        Raises:
            ValidationError: 無效的限制
        """
        if not isinstance(limit, int):
            raise ValidationError("查詢數量必須是整數")
        
        if limit <= 0:
            raise ValidationError("查詢數量必須大於 0")
        
        if limit > max_limit:
            raise ValidationError(
                f"查詢數量 ({limit}) 超過最大限制 ({max_limit})"
            )
        
        return limit
    
    @staticmethod
    def validate_api_url(api_url: Optional[str]) -> str:
        """
        驗證 API URL
        
        Args:
            api_url: API URL
            
        Returns:
            str: 驗證後的 URL
            
        Raises:
            ValidationError: 無效的 URL
        """
        if not api_url:
            raise ValidationError("API URL 不能為空")
        
        api_url = api_url.strip()
        
        if not api_url.startswith(('http://', 'https://')):
            raise ValidationError(
                f"API URL 必須以 http:// 或 https:// 開頭：{api_url}"
            )
        
        return api_url


class BatchValidator:
    """批次驗證工具"""
    
    @staticmethod
    def validate_symbols(symbols: list) -> list:
        """
        批次驗證多個交易對
        
        Args:
            symbols: 交易對列表
            
        Returns:
            list: 驗證後的交易對列表
            
        Raises:
            ValidationError: 包含無效交易對
        """
        if not symbols:
            raise ValidationError("交易對列表不能為空")
        
        validated = []
        errors = []
        
        for symbol in symbols:
            try:
                validated.append(DataValidator.validate_symbol(symbol))
            except ValidationError as e:
                errors.append(f"{symbol}: {str(e)}")
        
        if errors:
            raise ValidationError(
                f"批次驗證失敗，發現 {len(errors)} 個錯誤：\n" +
                "\n".join(errors)
            )
        
        return validated
    
    @staticmethod
    def validate_klines(klines: list) -> list:
        """
        批次驗證多筆 K 線資料
        
        Args:
            klines: K 線資料列表
            
        Returns:
            list: 驗證後的 K 線列表
            
        Raises:
            ValidationError: 包含無效資料
        """
        if not klines:
            raise ValidationError("K 線列表不能為空")
        
        validated = []
        errors = []
        
        for i, kline in enumerate(klines):
            try:
                validated.append(DataValidator.validate_kline_data(kline))
            except ValidationError as e:
                errors.append(f"第 {i+1} 筆：{str(e)}")
        
        if errors:
            raise ValidationError(
                f"批次驗證失敗，發現 {len(errors)} 個錯誤：\n" +
                "\n".join(errors[:5])  # 只顯示前 5 個錯誤
                + (f"\n... 還有 {len(errors)-5} 個錯誤" if len(errors) > 5 else "")
            )
        
        return validated
