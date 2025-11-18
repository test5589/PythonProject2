"""
測試腳本：檢查資料庫中的 K 線數據
"""
import sys
from pathlib import Path

# 添加 backend 到路徑
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from database.chart_db import chart_db

def main():
    print("=" * 60)
    print("檢查 K 線資料庫")
    print("=" * 60)
    print()
    
    # 檢查資料
    try:
        with chart_db.get_session() as session:
            from database.models import CandlestickData
            
            # 統計總數
            total = session.query(CandlestickData).count()
            print(f"📊 總 K 線數量: {total}")
            print()
            
            # 按交易對統計
            from sqlalchemy import func
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
                print("-" * 60)
                from datetime import datetime
                for row in symbol_counts:
                    symbol, interval, count, min_time, max_time = row
                    min_dt = datetime.fromtimestamp(min_time).strftime('%Y-%m-%d %H:%M:%S')
                    max_dt = datetime.fromtimestamp(max_time).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {symbol}@{interval}s: {count} 條")
                    print(f"    時間範圍: {min_dt} ~ {max_dt}")
                print()
            else:
                print("⚠️ 資料庫中沒有 K 線資料")
                print()
            
            # 查詢最近的 5 條記錄
            if total > 0:
                print("🔍 最近的 5 條記錄:")
                print("-" * 60)
                recent = session.query(CandlestickData).order_by(
                    CandlestickData.timestamp.desc()
                ).limit(5).all()
                
                for candle in recent:
                    dt = datetime.fromtimestamp(candle.timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    print(f"  {candle.symbol}@{candle.interval}s | {dt}")
                    print(f"    O:{candle.open:.2f} H:{candle.high:.2f} L:{candle.low:.2f} C:{candle.close:.2f}")
                    print(f"    V:{candle.volume:.4f} | Source:{candle.data_source}")
                print()
                
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 60)
    print("檢查完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
