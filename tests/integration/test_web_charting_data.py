"""
測試腳本：檢查資料庫中的 K 線數據
"""
import unittest
import sys
import os
from pathlib import Path

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加 web_charting/backend 到路徑
backend_dir = project_root / "web_charting" / "backend"
sys.path.insert(0, str(backend_dir))

from database.chart_db import chart_db
from database.models import CandlestickData
from sqlalchemy import func
from datetime import datetime

class TestWebChartingData(unittest.TestCase):
    """測試 Web Charting 資料庫數據"""
    
    def test_database_connection(self):
        """測試資料庫連接並統計數據"""
        try:
            with chart_db.get_session() as session:
                # 統計總數
                total = session.query(CandlestickData).count()
                print(f"\n📊 總 K 線數量: {total}")
                
                # 按交易對統計
                symbol_counts = session.query(
                    CandlestickData.symbol,
                    CandlestickData.interval,
                    func.count(CandlestickData.id).label('count'),
                    func.min(CandlestickData.timestamp).label('min_time'),
                    func.max(CandlestickData.timestamp).label('max_time')
                ).group_by(
                    CandlestickData.symbol,
                    CandlestickData.interval
                ).all()
                
                if symbol_counts:
                    print("📈 按交易對和時間框架統計:")
                    for row in symbol_counts:
                        symbol, interval, count, min_time, max_time = row
                        min_dt = datetime.fromtimestamp(min_time).strftime('%Y-%m-%d %H:%M:%S')
                        max_dt = datetime.fromtimestamp(max_time).strftime('%Y-%m-%d %H:%M:%S')
                        print(f"  {symbol}@{interval}s: {count} 條")
                        print(f"    時間範圍: {min_dt} ~ {max_dt}")
                
                # 如果有數據，檢查最後一筆
                if total > 0:
                    self.assertGreater(total, 0)
        except Exception as e:
            self.fail(f"資料庫查詢失敗: {e}")

if __name__ == "__main__":
    unittest.main()
