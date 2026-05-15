#!/usr/bin/env python3
"""
Utils資料夾分析和優化建議
"""

import os
import sys

def analyze_utils_structure():
    """分析utils資料夾結構"""
    utils_path = "modules/utils"
    
    print("=" * 80)
    print("📁 Utils資料夾結構分析")
    print("=" * 80)
    
    # 按功能分類
    categories = {
        "🌐 API相關": [
            "api_client.py",
            "api_connector.py", 
            "api_manager.py",
            "weight_test_engine.py"
        ],
        "💾 數據處理": [
            "database.py",
            "db_pool.py",
            "data_fetcher.py",
            "data_integrity.py",
            "validators.py"
        ],
        "🔄 回補和聚合": [
            "backfill_data.py",
            "backfill_state.py",
            "auto_heal_backfill.py",
            "aggregation_utils.py"
        ],
        "📊 監控和測試": [
            "anchor_time_engine.py",
            "multi_symbol_monitor.py",
            "ws_aggregator.py"
        ],
        "🛠️ 工具和日誌": [
            "logger.py",
            "log_viewer.py",
            "exceptions.py"
        ],
        "📦 備份和空文件": [
            "anchor_time_engine_backup.py",
            "dynamic_loader.py",
            "simulator.py"
        ]
    }
    
    for category, files in categories.items():
        print(f"\n{category}:")
        for file in files:
            file_path = os.path.join(utils_path, file)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                status = "✅" if size > 0 else "⚠️ 空文件"
                print(f"  - {file} ({size} bytes) {status}")
            else:
                print(f"  - {file} ❌ 不存在")
    
    return categories

def suggest_optimization():
    """建議優化方案"""
    print("\n" + "=" * 80)
    print("💡 優化建議")
    print("=" * 80)
    
    suggestions = {
        "🗂️ 建議創建子資料夾": {
            "api/": ["api_client.py", "api_connector.py", "api_manager.py", "weight_test_engine.py"],
            "database/": ["database.py", "db_pool.py", "data_integrity.py", "validators.py"],
            "backfill/": ["backfill_data.py", "backfill_state.py", "auto_heal_backfill.py", "aggregation_utils.py"],
            "monitoring/": ["anchor_time_engine.py", "multi_symbol_monitor.py", "ws_aggregator.py"],
            "core/": ["logger.py", "exceptions.py", "data_fetcher.py"]
        },
        "🗑️ 建議清理": [
            "anchor_time_engine_backup.py (備份文件)",
            "dynamic_loader.py (空文件)",
            "simulator.py (空文件)",
            "log_viewer.py (功能簡單，可合併到logger.py)"
        ],
        "🔧 建議優化": [
            "統一API相關模組的介面",
            "合併相似功能的小文件",
            "添加模組間的依賴管理",
            "創建統一的配置管理"
        ]
    }
    
    for category, items in suggestions.items():
        print(f"\n{category}:")
        if isinstance(items, dict):
            for folder, files in items.items():
                print(f"  📁 {folder}")
                for file in files:
                    print(f"    - {file}")
        else:
            for item in items:
                print(f"  - {item}")

def create_restructure_plan():
    """創建重構計劃"""
    print("\n" + "=" * 80)
    print("📋 重構執行計劃")
    print("=" * 80)
    
    plan = [
        "1. 創建子資料夾結構",
        "2. 移動文件到對應資料夾",
        "3. 更新import路徑",
        "4. 刪除不必要的文件",
        "5. 測試所有功能",
        "6. 更新文檔"
    ]
    
    for step in plan:
        print(f"  {step}")
    
    print(f"\n📊 統計:")
    print(f"  - 當前文件數: 22個")
    print(f"  - 建議保留: 18個")
    print(f"  - 建議刪除: 4個")
    print(f"  - 建議子資料夾: 5個")

if __name__ == "__main__":
    analyze_utils_structure()
    suggest_optimization()
    create_restructure_plan()
