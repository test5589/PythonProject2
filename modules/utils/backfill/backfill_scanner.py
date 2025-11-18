"""
backfill_scanner.py - 回補掃描和檢測
負責數據缺口檢測和完整性掃描
"""

import sqlite3
import time
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional
from modules.utils.database import DB_PATH

class BackfillScanner:
    """回補掃描器"""
    
    def count_rows(self, category: str, symbol: str, start_ts: float, end_ts: float) -> int:
        """計算指定時間範圍內的記錄數"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT COUNT(*) FROM historical_data
                WHERE category=? AND symbol=? AND interval=1 AND timestamp>=? AND timestamp<?
                """,
                (category, symbol.replace('/', ''), start_ts, end_ts)
            )
            n = cur.fetchone()[0] or 0
            conn.close()
            return int(n)
        except Exception:
            return 0

    def format_range(self, start_ts: float, end_ts: float) -> str:
        """格式化時間範圍顯示"""
        try:
            tw = timezone(timedelta(hours=8))
            s8 = datetime.fromtimestamp(start_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
            e8 = datetime.fromtimestamp(end_ts, tz=tw).strftime('%Y-%m-%d %H:%M:%S')
            su = datetime.fromtimestamp(start_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            eu = datetime.fromtimestamp(end_ts, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
            return f"[UTC+8 {s8} ~ {e8}) / [UTC {su} ~ {eu})"
        except Exception:
            return f"[{start_ts} ~ {end_ts})"

    def scan_incomplete_seconds(self, category: str, symbol: str, lookback_minutes: int = 60) -> Tuple[int, int, int]:
        """
        掃描最近指定分鐘的 1 秒級別資料，偵測：
        - 時間缺口（相鄰樣本 > 1.5 秒）
        - 欄位缺漏（open/high/low/close/volume 存在 None）

        :return: (gap_count, bad_rows, total_rows)
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            now_ts = time.time()
            start_ts = now_ts - lookback_minutes * 60
            
            cur.execute(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE category=? AND symbol=? AND interval=? AND timestamp>=?
                ORDER BY timestamp
                """,
                (category, symbol.replace("/", ""), 1, start_ts)
            )
            rows = cur.fetchall()
            conn.close()
            
            gap = 0
            bad = 0
            last_ts = None
            
            for r in rows:
                ts, o, h, l, c, v = r
                
                # 檢查欄位缺漏
                if o is None or h is None or l is None or c is None or v is None:
                    bad += 1
                    
                # 檢查時間缺口
                if last_ts is not None and (ts - last_ts) > 1.5:
                    gap += 1
                    
                last_ts = ts
                
            return gap, bad, len(rows)
        except Exception:
            return 0, 0, 0

    def find_earliest_incomplete_span(self, category: str, symbol: str, seconds: int = 900) -> Optional[float]:
        """
        尋找最早的『不完整或有缺口』的 1 秒區段起點（秒級 timestamp）。
        規則：
        - 欄位缺漏 open/high/low/close/volume 任一為 NULL
        - 或相鄰樣本間隔 > 1.5 秒
        回傳該段起點 timestamp（秒）。若找不到，回傳 None。
        """
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE category=? AND symbol=? AND interval=1
                ORDER BY timestamp ASC
                """,
                (category, symbol.replace("/", ""))
            )
            rows = cur.fetchall()
            conn.close()
            
            last_ts = None
            for r in rows:
                ts, o, h, l, c, v = r
                
                # 檢查欄位缺漏
                if o is None or h is None or l is None or c is None or v is None:
                    return ts
                    
                # 檢查時間缺口
                if last_ts is not None and (ts - last_ts) > 1.5:
                    # 缺口從 last_ts 後一秒開始
                    return last_ts + 1
                    
                last_ts = ts
                
            return None
        except Exception:
            return None
            
    def get_data_statistics(self, category: str, symbol: str) -> dict:
        """獲取數據統計信息"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            # 基本統計
            cur.execute(
                """
                SELECT COUNT(*), MIN(timestamp), MAX(timestamp)
                FROM historical_data
                WHERE category=? AND symbol=? AND interval=1
                """,
                (category, symbol.replace("/", ""))
            )
            row = cur.fetchone()
            
            if row and row[0] > 0:
                total_count, min_ts, max_ts = row
                
                # 計算預期記錄數
                expected_count = int((max_ts - min_ts) + 1)
                gap_percentage = ((expected_count - total_count) / expected_count * 100) if expected_count > 0 else 0
                
                stats = {
                    'total_records': total_count,
                    'expected_records': expected_count,
                    'missing_records': expected_count - total_count,
                    'gap_percentage': gap_percentage,
                    'earliest_time': datetime.fromtimestamp(min_ts, tz=timezone.utc),
                    'latest_time': datetime.fromtimestamp(max_ts, tz=timezone.utc),
                    'time_span_hours': (max_ts - min_ts) / 3600
                }
            else:
                stats = {
                    'total_records': 0,
                    'expected_records': 0,
                    'missing_records': 0,
                    'gap_percentage': 0,
                    'earliest_time': None,
                    'latest_time': None,
                    'time_span_hours': 0
                }
                
            conn.close()
            return stats
        except Exception as e:
            return {'error': str(e)}
            
    def detect_data_quality_issues(self, category: str, symbol: str, lookback_hours: int = 24) -> dict:
        """檢測數據品質問題"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            now_ts = time.time()
            start_ts = now_ts - lookback_hours * 3600
            
            # 檢測異常價格（高低價反轉、異常波動等）
            cur.execute(
                """
                SELECT timestamp, open, high, low, close, volume
                FROM historical_data
                WHERE category=? AND symbol=? AND interval=1 AND timestamp>=?
                ORDER BY timestamp
                """,
                (category, symbol.replace("/", ""), start_ts)
            )
            rows = cur.fetchall()
            conn.close()
            
            issues = {
                'invalid_ohlc': 0,  # 高低價錯誤
                'zero_volume': 0,   # 零成交量
                'extreme_gaps': 0,  # 極端價格跳躍
                'duplicate_timestamps': 0,  # 重複時間戳
                'null_fields': 0    # 空值欄位
            }
            
            seen_timestamps = set()
            last_close = None
            
            for r in rows:
                ts, o, h, l, c, v = r
                
                # 檢查重複時間戳
                if ts in seen_timestamps:
                    issues['duplicate_timestamps'] += 1
                seen_timestamps.add(ts)
                
                # 檢查空值
                if any(val is None for val in [o, h, l, c, v]):
                    issues['null_fields'] += 1
                    continue
                    
                # 檢查 OHLC 邏輯
                if h < l or h < max(o, c) or l > min(o, c):
                    issues['invalid_ohlc'] += 1
                    
                # 檢查零成交量
                if v == 0:
                    issues['zero_volume'] += 1
                    
                # 檢查極端價格跳躍（>10%）
                if last_close is not None:
                    price_change = abs((o - last_close) / last_close)
                    if price_change > 0.1:  # 10%
                        issues['extreme_gaps'] += 1
                        
                last_close = c
                
            issues['total_checked'] = len(rows)
            return issues
            
        except Exception as e:
            return {'error': str(e)}

# 向後相容性函數
def scan_incomplete_seconds(category: str, symbol: str, lookback_minutes: int = 60) -> Tuple[int, int, int]:
    """掃描不完整秒級數據（向後相容性函數）"""
    scanner = BackfillScanner()
    return scanner.scan_incomplete_seconds(category, symbol, lookback_minutes)
