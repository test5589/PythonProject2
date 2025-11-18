
重要參考文件不可刪除

#!/usr/bin/env python3
"""
advanced_api_test.py - 進階API測試工具
整合多段並發測試，涵蓋時間範圍分段和10個貨幣對並發功能
用戶可選擇段數，每段執行10個貨幣對同時請求，支援時間範圍控制

⚠️  TEST FILE - 待刪除文件 ⚠️
此文件為測試API封鎖行為而創建，整合多種測試方式
測試完成後此文件將被刪除
"""

import time
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import requests

# 簡單的日誌記錄
def log_message(message: str, level: str = "INFO"):
    """簡單的控制台日誌"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level} | {message}")

@dataclass
class KlineData:
    """K線數據結構"""
    open_time: int
    open: float
    high: float
    low: float
    close: float
    volume: float
    close_time: int
    quote_asset_volume: float
    num_trades: int
    taker_base_vol: float
    taker_quote_vol: float

@dataclass
class SegmentResult:
    """單段測試結果"""
    segment: int
    symbols_requested: int
    successful_requests: int
    blocked_requests: int
    invalid_kline_requests: int
    error_requests: int
    total_records_requested: int
    total_records_received: int
    test_duration: float
    symbol_results: List[Dict]
    start_date: str
    end_date: str

@dataclass
class AdvancedTestResult:
    """進階測試結果"""
    test_session: str
    symbol: str
    timeframe: str
    start_date: str
    total_segments: int
    records_per_request: int
    total_symbols_per_segment: int
    total_requested: int
    total_received: int
    successful_requests: int
    blocked_requests: int
    invalid_kline_requests: int
    error_requests: int
    test_duration: float
    segment_results: List[SegmentResult]

class AdvancedAPITester:
    """進階API測試器"""

    # 固定10個貨幣對
    SYMBOLS = ["BTCUSDT", "ETHUSDT", "XRPUSDT", "BNBUSDT", "SOLUSDT",
               "USDCUSDT", "TRXUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT"]

    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3/klines"
        self.test_start_time = None

    def timestamp_to_datetime(self, timestamp: int) -> datetime:
        """將timestamp轉換為datetime"""
        return datetime.fromtimestamp(timestamp / 1000)

    def datetime_to_timestamp(self, dt: datetime) -> int:
        """將datetime轉換為timestamp"""
        return int(dt.timestamp() * 1000)

    def parse_kline(self, item: List) -> Tuple[bool, Optional[KlineData], str]:
        """
        解析單個kline項目
        Returns: (is_valid, kline_data, error_message)
        """
        try:
            if len(item) != 12:  # Binance API返回12個字段，但我們只需要前11個
                return False, None, f"數據字段數量錯誤: 期望12個，實際{len(item)}個"

            kline = KlineData(
                open_time=int(item[0]),
                open=float(item[1]),
                high=float(item[2]),
                low=float(item[3]),
                close=float(item[4]),
                volume=float(item[5]),
                close_time=int(item[6]),
                quote_asset_volume=float(item[7]),
                num_trades=int(item[8]),
                taker_base_vol=float(item[9]),
                taker_quote_vol=float(item[10])
            )

            return True, kline, ""

        except (IndexError, ValueError, TypeError) as e:
            return False, None, f"解析kline失敗: {e}"

    def validate_klines_data(self, raw_data: List[List], expected_count: int) -> Tuple[bool, int, str]:
        """
        驗證kline數據完整性
        Returns: (is_valid, valid_count, error_message)
        """
        if not isinstance(raw_data, list):
            return False, 0, "返回數據不是列表格式"

        if len(raw_data) == 0:
            return False, 0, "返回數據為空"

        valid_count = 0
        invalid_items = []

        for i, item in enumerate(raw_data):
            is_valid, _, error_msg = self.parse_kline(item)
            if is_valid:
                valid_count += 1
            else:
                invalid_items.append(f"項目{i}: {error_msg}")

        if valid_count != expected_count:
            return False, valid_count, f"數據數量不匹配: 期望{expected_count}個，實際{valid_count}個"

        if invalid_items:
            return False, valid_count, f"發現無效kline項目: {invalid_items[:3]}"  # 只顯示前3個錯誤

        return True, valid_count, ""

    def make_request_with_time_range(self, symbol: str, timeframe: str, start_time: int, end_time: int, limit: int = 1000) -> Tuple[bool, int, str, List]:
        """
        發送帶時間範圍的API請求
        Returns: (success, actual_count, error_message, raw_data)
        """
        params = {
            'symbol': symbol,
            'interval': timeframe,
            'startTime': start_time,
            'endTime': end_time,
            'limit': limit
        }

        try:
            response = requests.get(self.base_url, params=params, timeout=10)

            if response.status_code == 200:
                raw_data = response.json()

                # 驗證數據完整性
                is_valid, valid_count, validation_error = self.validate_klines_data(raw_data, len(raw_data))

                if not is_valid:
                    return False, valid_count, f"數據驗證失敗: {validation_error}", raw_data

                return True, valid_count, "", raw_data

            elif response.status_code == 429:
                return False, 0, "429 Rate Limit Exceeded", []
            elif response.status_code == 418:
                return False, 0, "418 IP Banned", []
            else:
                return False, 0, f"HTTP {response.status_code}: {response.text}", []

        except Exception as e:
            return False, 0, f"請求異常: {str(e)}", []

    def run_concurrent_segment_test(self, segment: int, timeframe: str = "1m", records_per_request: int = 1000,
                                   start_date: str = "2020-10-01") -> SegmentResult:
        """
        運行單段並發測試 (10個貨幣對同時請求)
        加入時間範圍控制
        """
        # 計算當前段的時間範圍
        base_date = datetime.strptime(start_date, '%Y-%m-%d')
        current_date = base_date + timedelta(days=segment - 1)

        start_datetime = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = start_datetime + timedelta(minutes=records_per_request)

        start_timestamp = self.datetime_to_timestamp(start_datetime)
        end_timestamp = self.datetime_to_timestamp(end_datetime)

        log_message(f"📊 開始段{segment}: 10個貨幣對並發請求 ({records_per_request}筆/對)")
        log_message(f"   時間範圍: {start_datetime.strftime('%Y-%m-%d %H:%M:%S')} 到 {end_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

        segment_start_time = time.time()
        symbol_results = []
        successful_requests = 0
        blocked_requests = 0
        invalid_kline_requests = 0
        error_requests = 0
        total_received = 0

        # 創建線程來並發請求所有貨幣對
        threads = []
        results = {}

        def request_symbol(symbol):
            """請求單個貨幣對"""
            success, actual_count, error_msg, raw_data = self.make_request_with_time_range(
                symbol, timeframe, start_timestamp, end_timestamp, records_per_request
            )

            result = {
                'symbol': symbol,
                'success': success,
                'actual_count': actual_count,
                'blocked': '429' in error_msg or '418' in error_msg,
                'invalid_kline': '數據驗證失敗' in error_msg,
                'error_message': error_msg,
                'raw_data_length': len(raw_data) if raw_data else 0
            }

            results[symbol] = result

        # 啟動10個線程
        for symbol in self.SYMBOLS:
            thread = threading.Thread(target=request_symbol, args=(symbol,))
            threads.append(thread)
            thread.start()

        # 等待所有線程完成
        for thread in threads:
            thread.join()

        # 統計結果
        for symbol in self.SYMBOLS:
            if symbol in results:
                result = results[symbol]
                symbol_results.append(result)

                if result['success']:
                    successful_requests += 1
                    total_received += result['actual_count']
                    log_message(f"✅ {symbol}: 獲取{result['actual_count']}筆有效數據")
                elif result['blocked']:
                    blocked_requests += 1
                    log_message(f"🛑 {symbol}: 被封鎖 - {result['error_message']}")
                elif result['invalid_kline']:
                    invalid_kline_requests += 1
                    log_message(f"⚠️ {symbol}: 數據無效 - {result['error_message']}")
                else:
                    error_requests += 1
                    log_message(f"❌ {symbol}: 失敗 - {result['error_message']}")

        segment_duration = time.time() - segment_start_time

        return SegmentResult(
            segment=segment,
            symbols_requested=len(self.SYMBOLS),
            successful_requests=successful_requests,
            blocked_requests=blocked_requests,
            invalid_kline_requests=invalid_kline_requests,
            error_requests=error_requests,
            total_records_requested=len(self.SYMBOLS) * records_per_request,
            total_records_received=total_received,
            test_duration=segment_duration,
            symbol_results=symbol_results,
            start_date=start_datetime.strftime('%Y-%m-%d %H:%M:%S'),
            end_date=end_datetime.strftime('%Y-%m-%d %H:%M:%S')
        )

    def run_advanced_test(self, symbol: str = "BTCUSDT", timeframe: str = "1m",
                         start_date: str = "2020-10-01", total_segments: int = 1,
                         records_per_request: int = 1000) -> AdvancedTestResult:
        """
        運行整合的進階測試 - 多段並發測試
        每段 = 10個貨幣對同時請求，支援時間範圍控制
        """
        log_message(f"🚀 開始多段並發測試")
        log_message(f"測試配置: {total_segments}段 × 10貨幣對 × {records_per_request}筆/請求")
        log_message(f"總請求量: {total_segments * len(self.SYMBOLS) * records_per_request}筆資料")
        self.test_start_time = time.time()

        segment_results = []
        total_successful = 0
        total_blocked = 0
        total_invalid = 0
        total_error = 0
        total_received = 0

        for segment in range(1, total_segments + 1):
            segment_result = self.run_concurrent_segment_test(segment, timeframe, records_per_request, start_date)
            segment_results.append(segment_result)

            total_successful += segment_result.successful_requests
            total_blocked += segment_result.blocked_requests
            total_invalid += segment_result.invalid_kline_requests
            total_error += segment_result.error_requests
            total_received += segment_result.total_records_received

            # 如果有封鎖，停止測試
            if segment_result.blocked_requests > 0:
                log_message(f"⚠️ 段{segment}發現封鎖，停止後續測試")
                break

            # 段間間隔
            if segment < total_segments:
                time.sleep(1)

        test_duration = time.time() - self.test_start_time
        total_requested = total_segments * len(self.SYMBOLS) * records_per_request

        return AdvancedTestResult(
            test_session=datetime.now().strftime('%Y%m%d_%H%M%S'),
            symbol="",  # 不適用於多貨幣對測試
            timeframe=timeframe,
            start_date=start_date,
            total_segments=total_segments,
            records_per_request=records_per_request,
            total_symbols_per_segment=len(self.SYMBOLS),
            total_requested=total_requested,
            total_received=total_received,
            successful_requests=total_successful,
            blocked_requests=total_blocked,
            invalid_kline_requests=total_invalid,
            error_requests=total_error,
            test_duration=test_duration,
            segment_results=segment_results
        )

    def save_results(self, result: AdvancedTestResult, filename: Optional[str] = None):
        """儲存測試結果"""
        if filename is None:
            filename = f"advanced_test_{result.test_session}.json"

        os.makedirs("data", exist_ok=True)
        filepath = os.path.join("data", filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)

        log_message(f"💾 測試結果已儲存: {filepath}")

def main():
    """主函數"""
    print("=" * 80)
    print("🔬 進階API測試工具")
    print("多段並發測試: 每段10個貨幣對同時請求，支援時間範圍控制")
    print("固定貨幣對: BTC、ETH、XRP、BNB、SOL、USDC、TRX、DOGE、ADA、LINK")
    print("=" * 80)

    tester = AdvancedAPITester()

    # 用戶輸入參數
    timeframe = input("輸入測試時間框架 (預設: 1m): ").strip() or "1m"
    start_date = input("輸入開始日期 (預設: 2020-10-01): ").strip() or "2020-10-01"
    total_segments_input = input("輸入測試段數 (預設: 1): ").strip()
    total_segments = int(total_segments_input) if total_segments_input.isdigit() else 1
    records_per_request_input = input("輸入每請求筆數 (預設: 1000): ").strip()
    records_per_request = int(records_per_request_input) if records_per_request_input.isdigit() else 1000

    print(f"\n將執行多段並發測試")
    print(f"時間框架: {timeframe}")
    print(f"開始日期: {start_date}")
    print(f"測試段數: {total_segments}")
    print(f"每請求筆數: {records_per_request}")
    print(f"每段貨幣對數: {len(tester.SYMBOLS)}")
    print(f"每段總請求數: {len(tester.SYMBOLS)} 次")
    print(f"每段總資料量: {len(tester.SYMBOLS) * records_per_request} 筆")

    total_requests = total_segments * len(tester.SYMBOLS)
    total_records = total_requests * records_per_request
    print(f"總請求數: {total_requests} 次")
    print(f"總資料量: {total_records} 筆")

    confirm = input("\n開始測試? (y/N): ").strip().lower()
    if confirm != 'y':
        print("測試取消")
        return

    try:
        # 運行測試
        result = tester.run_advanced_test("", timeframe, start_date, total_segments, records_per_request)

        # 儲存結果
        tester.save_results(result)

        # 顯示總結 (按照用戶要求的格式)
        print("\n" + "=" * 80)
        print("📋 多段並發測試總結")
        print("=" * 80)
        print(f"測試類型: concurrent_segments")
        print(f"時間框架: {result.timeframe}")
        print(f"開始日期: {result.start_date}")
        print(f"測試段數: {result.total_segments}")
        print(f"每請求筆數: {result.records_per_request}")
        print(f"每段貨幣對數: {result.total_symbols_per_segment}")
        print(f"總請求數量: {result.total_requested}筆")
        print(f"實際獲取數量: {result.total_received}筆")
        print(f"成功請求: {result.successful_requests}")
        print(f"封鎖請求: {result.blocked_requests}")
        print(f"數據無效請求: {result.invalid_kline_requests}")
        print(f"錯誤請求: {result.error_requests}")
        print(f"測試時間: {result.test_duration:.1f}秒")

        print("\n🔍 詳細結果:")
        for seg_result in result.segment_results:
            status = "✅ 成功" if seg_result.blocked_requests == 0 else f"🛑 {seg_result.blocked_requests}個封鎖"
            print(f"段{seg_result.segment:2d}: {status} ({seg_result.total_records_received:5d}/{seg_result.total_records_requested:5d}筆) - {seg_result.test_duration:.1f}秒")

        print("\n🎯 結論:")
        if result.blocked_requests > 0:
            print(f"❌ 發現{result.blocked_requests}個請求被API封鎖！")
        else:
            print("✅ 在多段並發測試中未發現封鎖")

        if result.invalid_kline_requests > 0:
            print(f"⚠️ 發現{result.invalid_kline_requests}個數據無效的請求")
        else:
            print("✅ 所有數據都包含有效的11個kline字段")

        print(f"\n💾 詳細結果已儲存到: data/advanced_test_{result.test_session}.json")

    except KeyboardInterrupt:
        print("\n⏹️ 測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")

if __name__ == "__main__":
    main()
