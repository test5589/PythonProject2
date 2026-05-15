#!/usr/bin/env python3
"""
日誌文件優化和整理
"""

import os
import glob
from datetime import datetime

def analyze_log_files():
    """分析日誌文件"""
    print("=" * 80)
    print("📄 日誌文件分析")
    print("=" * 80)
    
    log_locations = [
        "data/logs/",
        "data/",
        "logs/"
    ]
    
    all_logs = []
    for location in log_locations:
        if os.path.exists(location):
            logs = glob.glob(os.path.join(location, "*.log"))
            for log in logs:
                size = os.path.getsize(log) if os.path.exists(log) else 0
                all_logs.append((log, size))
    
    # 按類別分組
    categories = {
        "🌐 API相關": [],
        "📊 監控相關": [],
        "💾 數據相關": [],
        "🧪 測試相關": [],
        "🔧 其他": []
    }
    
    for log_path, size in all_logs:
        filename = os.path.basename(log_path)
        if any(keyword in filename for keyword in ['api', 'weight']):
            categories["🌐 API相關"].append((log_path, size))
        elif any(keyword in filename for keyword in ['monitor', 'ws']):
            categories["📊 監控相關"].append((log_path, size))
        elif any(keyword in filename for keyword in ['db', 'backfill', 'fetcher']):
            categories["💾 數據相關"].append((log_path, size))
        elif any(keyword in filename for keyword in ['test', 'capacity', 'anchor']):
            categories["🧪 測試相關"].append((log_path, size))
        else:
            categories["🔧 其他"].append((log_path, size))
    
    total_size = 0
    for category, logs in categories.items():
        if logs:
            print(f"\n{category}:")
            category_size = 0
            for log_path, size in logs:
                print(f"  - {os.path.basename(log_path)} ({size:,} bytes)")
                category_size += size
                total_size += size
            print(f"    小計: {category_size:,} bytes")
    
    print(f"\n📊 總計: {len(all_logs)} 個日誌文件，{total_size:,} bytes")
    return all_logs, categories

def suggest_log_optimization():
    """建議日誌優化方案"""
    print("\n" + "=" * 80)
    print("💡 日誌優化建議")
    print("=" * 80)
    
    suggestions = {
        "🗂️ 統一日誌位置": [
            "將所有日誌文件移動到 data/logs/ 目錄",
            "刪除其他位置的重複日誌文件",
            "建立清晰的日誌文件命名規範"
        ],
        "📅 日誌輪轉機制": [
            "實現日誌文件大小限制（如10MB）",
            "添加日期輪轉（每日/每週）",
            "自動壓縮舊日誌文件",
            "設定日誌保留期限（如30天）"
        ],
        "🏷️ 日誌分類優化": [
            "api/ - API相關日誌",
            "monitoring/ - 監控相關日誌", 
            "database/ - 數據庫相關日誌",
            "testing/ - 測試相關日誌",
            "system/ - 系統相關日誌"
        ],
        "🧹 清理建議": [
            "刪除空的或過小的日誌文件",
            "合併功能相似的日誌文件",
            "清理測試期間產生的臨時日誌",
            "建立日誌清理腳本"
        ]
    }
    
    for category, items in suggestions.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")

def create_log_structure():
    """創建建議的日誌結構"""
    print("\n" + "=" * 80)
    print("📁 建議的日誌結構")
    print("=" * 80)
    
    structure = """
data/logs/
├── api/
│   ├── api_client.log           # API客戶端日誌
│   ├── api_connector.log        # API連接器日誌
│   └── api_weight.log           # API權重日誌
├── monitoring/
│   ├── monitor.log              # 一般監控日誌
│   ├── multi_monitor.log        # 多貨幣對監控日誌
│   └── ws_1s.log               # WebSocket 1秒監控日誌
├── database/
│   ├── db_pool.log             # 數據庫連接池日誌
│   ├── backfill.log            # 回補日誌
│   └── fetcher.log             # 數據獲取日誌
├── testing/
│   ├── anchor_time.log         # 錨定時間測試日誌
│   ├── capacity_test.log       # 容量測試日誌
│   ├── weight_test.log         # 權重測試日誌
│   └── test.log               # 一般測試日誌
├── system/
│   ├── application.log         # 應用程序主日誌
│   ├── error.log              # 錯誤日誌
│   └── debug.log              # 調試日誌
└── archive/
    ├── 2025-11/               # 按月歸檔
    └── compressed/            # 壓縮歸檔
"""
    
    print(structure)

def generate_cleanup_script():
    """生成清理腳本"""
    print("\n" + "=" * 80)
    print("🧹 日誌清理腳本")
    print("=" * 80)
    
    script_content = '''#!/usr/bin/env python3
"""
日誌清理腳本
"""

import os
import glob
import gzip
import shutil
from datetime import datetime, timedelta

def cleanup_logs():
    """清理日誌文件"""
    log_dir = "data/logs"
    
    # 1. 刪除空文件
    for log_file in glob.glob(os.path.join(log_dir, "**/*.log"), recursive=True):
        if os.path.getsize(log_file) == 0:
            os.remove(log_file)
            print(f"刪除空文件: {log_file}")
    
    # 2. 壓縮大文件
    for log_file in glob.glob(os.path.join(log_dir, "**/*.log"), recursive=True):
        if os.path.getsize(log_file) > 10 * 1024 * 1024:  # 10MB
            with open(log_file, 'rb') as f_in:
                with gzip.open(f"{log_file}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            os.remove(log_file)
            print(f"壓縮文件: {log_file}")
    
    # 3. 刪除舊文件
    cutoff_date = datetime.now() - timedelta(days=30)
    for log_file in glob.glob(os.path.join(log_dir, "**/*.log*"), recursive=True):
        if os.path.getmtime(log_file) < cutoff_date.timestamp():
            os.remove(log_file)
            print(f"刪除舊文件: {log_file}")

if __name__ == "__main__":
    cleanup_logs()
'''
    
    print("建議創建 scripts/cleanup_logs.py:")
    print(script_content)

if __name__ == "__main__":
    analyze_log_files()
    suggest_log_optimization()
    create_log_structure()
    generate_cleanup_script()
