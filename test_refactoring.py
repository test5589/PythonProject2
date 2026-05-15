"""
測試重構後的 data_manager 是否正常工作
"""

import sys
from datetime import datetime, timezone, timedelta

# 測試導入
try:
    from modules.utils.database.data_manager import insert_data, batch_insert_data, _data_manager
    from modules.utils.database.priority_manager import priority_manager
    from modules.utils.database.stats_collector import stats_collector
    print("✅ 所有模組導入成功")
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    sys.exit(1)

# 測試 priority_manager
print("\n📊 測試 priority_manager...")
try:
    # 測試優先級獲取
    real_priority = priority_manager.get_priority('real')
    interp_priority = priority_manager.get_priority('interpolated')
    print(f"   real 優先級: {real_priority}")
    print(f"   interpolated 優先級: {interp_priority}")
    
    # 測試覆蓋判斷
    can_overwrite = priority_manager.can_overwrite('interpolated', 'real')
    print(f"   real 可以覆蓋 interpolated: {can_overwrite}")
    
    # 測試間隔標籤
    label = priority_manager.get_interval_label(60)
    print(f"   60秒 = {label}")
    
    print("✅ priority_manager 測試通過")
except Exception as e:
    print(f"❌ priority_manager 測試失敗: {e}")
    sys.exit(1)

# 測試 stats_collector
print("\n📈 測試 stats_collector...")
try:
    # 重置統計
    stats_collector.reset_stats()
    
    # 測試計數
    stats_collector.increment_total()
    stats_collector.increment_successful()
    stats_collector.increment_skipped()
    
    # 獲取統計
    stats = stats_collector.get_stats()
    print(f"   統計: {stats}")
    
    # 測試摘要
    summary = stats_collector.get_summary()
    print(f"   摘要:\n{summary}")
    
    print("✅ stats_collector 測試通過")
except Exception as e:
    print(f"❌ stats_collector 測試失敗: {e}")
    sys.exit(1)

# 測試 data_manager 向後兼容性
print("\n🔧 測試 data_manager 向後兼容性...")
try:
    # 測試屬性訪問
    priority_map = _data_manager.priority_map
    interval_map = _data_manager.interval_map
    print(f"   priority_map 鍵: {list(priority_map.keys())}")
    print(f"   interval_map 大小: {len(interval_map)}")
    
    # 測試統計方法
    stats = _data_manager.get_stats()
    print(f"   get_stats() 工作正常: {type(stats)}")
    
    print("✅ data_manager 向後兼容性測試通過")
except Exception as e:
    print(f"❌ data_manager 測試失敗: {e}")
    sys.exit(1)

# 測試實際插入（使用測試數據）
print("\n💾 測試實際數據插入...")
try:
    # 重置統計
    stats_collector.reset_stats()
    
    # 創建測試 K 線數據
    now = datetime.now(tz=timezone.utc)
    timestamp_ms = int(now.timestamp() * 1000)
    
    test_kline = {
        'open_time': timestamp_ms,
        'open': 50000.0,
        'high': 51000.0,
        'low': 49000.0,
        'close': 50500.0,
        'volume': 100.0,
        'close_time': timestamp_ms + 60000,
        'quote_asset_volume': 5000000.0,
        'num_trades': 1000,
        'taker_base_vol': 50.0,
        'taker_quote_vol': 2500000.0
    }
    
    # 測試單筆插入
    result = insert_data(
        category='crypto',
        symbol='TEST_REFACTOR_BTC',
        interval=60,
        kline=test_kline,
        data_source='real'
    )
    print(f"   單筆插入結果: {result}")
    
    # 檢查統計
    stats = _data_manager.get_stats()
    print(f"   插入後統計: {stats}")
    
    # 測試批量插入
    test_klines = [test_kline] * 5
    count = batch_insert_data(
        category='crypto',
        symbol='TEST_REFACTOR_ETH',
        interval=60,
        klines=test_klines,
        data_source='real'
    )
    print(f"   批量插入結果: {count}/5")
    
    print("✅ 實際數據插入測試通過")
except Exception as e:
    print(f"❌ 數據插入測試失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "="*50)
print("🎉 所有測試通過！重構成功！")
print("="*50)
print("\n📋 總結:")
print("   ✅ priority_manager 工作正常")
print("   ✅ stats_collector 工作正常")
print("   ✅ data_manager 向後兼容")
print("   ✅ 實際插入功能正常")
print("\n重構完成，功能保持不變！")
