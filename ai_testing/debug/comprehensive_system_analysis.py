#!/usr/bin/env python3
"""
全面系統分析和優化建議
"""

import os
import glob
from pathlib import Path
import json

def analyze_entire_system():
    """全面分析整個系統"""
    print("=" * 80)
    print("🔍 全面系統分析")
    print("=" * 80)
    
    analysis = {
        "file_counts": {},
        "folder_structure": {},
        "optimization_needed": [],
        "cleanup_candidates": [],
        "empty_files": [],
        "large_files": [],
        "duplicate_candidates": []
    }
    
    # 分析文件類型分布
    file_types = {}
    total_size = 0
    
    for root, dirs, files in os.walk("."):
        # 跳過特定目錄
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.venv', 'node_modules']]
        
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path):
                ext = os.path.splitext(file)[1].lower()
                size = os.path.getsize(file_path)
                
                if ext not in file_types:
                    file_types[ext] = {"count": 0, "size": 0, "files": []}
                
                file_types[ext]["count"] += 1
                file_types[ext]["size"] += size
                file_types[ext]["files"].append(file_path)
                total_size += size
                
                # 檢查空文件
                if size == 0:
                    analysis["empty_files"].append(file_path)
                
                # 檢查大文件 (>1MB)
                if size > 1024 * 1024:
                    analysis["large_files"].append((file_path, size))
    
    analysis["file_counts"] = file_types
    
    # 顯示文件類型統計
    print("\n📊 文件類型統計:")
    for ext, info in sorted(file_types.items(), key=lambda x: x[1]["size"], reverse=True):
        if info["count"] > 0:
            print(f"  {ext or '無副檔名'}: {info['count']}個文件, {info['size']:,} bytes")
    
    print(f"\n📈 總計: {sum(info['count'] for info in file_types.values())}個文件, {total_size:,} bytes")
    
    return analysis

def analyze_folder_structure():
    """分析資料夾結構"""
    print("\n" + "=" * 80)
    print("📁 資料夾結構分析")
    print("=" * 80)
    
    structure = {}
    
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.venv']]
        
        level = root.replace(".", "").count(os.sep)
        indent = "  " * level
        folder_name = os.path.basename(root) or "根目錄"
        
        file_count = len([f for f in files if not f.startswith('.')])
        subfolder_count = len(dirs)
        
        print(f"{indent}📁 {folder_name}/ ({file_count}個文件, {subfolder_count}個子資料夾)")
        
        if level < 3:  # 只顯示前3層的文件
            for file in sorted(files):
                if not file.startswith('.'):
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
                    print(f"{indent}  📄 {file} ({size:,} bytes)")

def identify_optimization_opportunities():
    """識別優化機會"""
    print("\n" + "=" * 80)
    print("💡 優化機會識別")
    print("=" * 80)
    
    opportunities = {
        "🗑️ 可以刪除的文件": [],
        "📦 可以合併的文件": [],
        "🔄 需要重新組織的文件": [],
        "🧹 需要清理的資料夾": [],
        "⚡ 性能優化建議": []
    }
    
    # 檢查空文件
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.venv']]
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                opportunities["🗑️ 可以刪除的文件"].append(f"{file_path} (空文件)")
    
    # 檢查可能的重複文件
    potential_duplicates = [
        ("modules/utils/dynamic_loader.py", "modules/utils/simulator.py"),
        ("modules/advisors/", "所有空的advisor文件"),
        ("modules/strategies/", "所有空的strategy文件"),
        ("modules/monitors/monitor_volume.py", "空的monitor文件")
    ]
    
    for dup in potential_duplicates:
        opportunities["📦 可以合併的文件"].append(f"{dup[0]} 和 {dup[1]}")
    
    # 重新組織建議
    reorganization_suggestions = [
        "將所有空的模組文件移到 templates/ 資料夾作為模板",
        "創建 scripts/ 資料夾存放維護腳本",
        "將 web/debug_logger.py 移到 tools/ 資料夾",
        "統一所有測試文件到 ai_testing/tests/",
        "創建 config/logging/ 子資料夾管理日誌配置"
    ]
    
    opportunities["🔄 需要重新組織的文件"] = reorganization_suggestions
    
    # 清理建議
    cleanup_suggestions = [
        "清理 data/logs/ 中的空日誌文件",
        "壓縮 data/logs/ 中的大日誌文件",
        "刪除 __pycache__/ 資料夾",
        "清理臨時文件和備份文件",
        "整理 docs/ 資料夾中的過時文檔"
    ]
    
    opportunities["🧹 需要清理的資料夾"] = cleanup_suggestions
    
    # 性能優化建議
    performance_suggestions = [
        "實現日誌輪轉機制避免日誌文件過大",
        "添加文件緩存機制提高讀取效率",
        "優化數據庫連接池配置",
        "實現異步處理提高API請求效率",
        "添加內存監控避免內存洩漏"
    ]
    
    opportunities["⚡ 性能優化建議"] = performance_suggestions
    
    # 顯示優化建議
    for category, suggestions in opportunities.items():
        if suggestions:
            print(f"\n{category}:")
            for suggestion in suggestions:
                print(f"  - {suggestion}")
    
    return opportunities

def generate_cleanup_script():
    """生成清理腳本"""
    print("\n" + "=" * 80)
    print("🧹 自動清理腳本")
    print("=" * 80)
    
    script_content = '''#!/usr/bin/env python3
"""
自動系統清理腳本
"""

import os
import glob
import shutil
from pathlib import Path

def cleanup_system():
    """執行系統清理"""
    print("🧹 開始系統清理...")
    
    # 1. 刪除空文件
    empty_files = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.venv']]
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.exists(file_path) and os.path.getsize(file_path) == 0:
                if file.endswith(('.py', '.log', '.tmp')):
                    os.remove(file_path)
                    empty_files.append(file_path)
                    print(f"刪除空文件: {file_path}")
    
    # 2. 清理__pycache__
    pycache_dirs = glob.glob("**/__pycache__", recursive=True)
    for pycache_dir in pycache_dirs:
        shutil.rmtree(pycache_dir)
        print(f"刪除緩存目錄: {pycache_dir}")
    
    # 3. 清理臨時文件
    temp_files = glob.glob("**/*.tmp", recursive=True) + glob.glob("**/*.temp", recursive=True)
    for temp_file in temp_files:
        os.remove(temp_file)
        print(f"刪除臨時文件: {temp_file}")
    
    # 4. 清理空日誌文件
    log_files = glob.glob("data/logs/*.log") + glob.glob("logs/*.log")
    for log_file in log_files:
        if os.path.exists(log_file) and os.path.getsize(log_file) == 0:
            os.remove(log_file)
            print(f"刪除空日誌: {log_file}")
    
    print(f"✅ 清理完成！刪除了 {len(empty_files)} 個空文件")

if __name__ == "__main__":
    cleanup_system()
'''
    
    # 保存清理腳本
    with open("tools/system_cleanup.py", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("✅ 清理腳本已創建: tools/system_cleanup.py")
    print("\n使用方法:")
    print("  python tools/system_cleanup.py")

def create_maintenance_schedule():
    """創建維護計劃"""
    print("\n" + "=" * 80)
    print("📅 系統維護計劃")
    print("=" * 80)
    
    schedule = {
        "每日維護": [
            "檢查系統運行狀態",
            "清理臨時文件",
            "檢查錯誤日誌",
            "運行基本測試"
        ],
        "每週維護": [
            "運行完整測試套件",
            "清理大日誌文件",
            "檢查磁盤空間",
            "更新文檔",
            "備份重要配置"
        ],
        "每月維護": [
            "全面系統分析",
            "性能評估",
            "安全檢查",
            "依賴更新",
            "歸檔舊文件"
        ],
        "季度維護": [
            "系統架構檢查",
            "代碼重構評估",
            "性能優化",
            "文檔大更新",
            "災難恢復測試"
        ]
    }
    
    for period, tasks in schedule.items():
        print(f"\n{period}:")
        for task in tasks:
            print(f"  - {task}")
    
    # 創建維護腳本
    maintenance_script = '''#!/usr/bin/env python3
"""
系統維護腳本
"""

import os
import subprocess
from datetime import datetime

def daily_maintenance():
    """每日維護"""
    print("🔄 執行每日維護...")
    
    # 運行系統清理
    subprocess.run(["python", "tools/system_cleanup.py"])
    
    # 運行基本測試
    subprocess.run(["python", "ai_testing/tests/test_all_fixes.py"])
    
    print("✅ 每日維護完成")

def weekly_maintenance():
    """每週維護"""
    print("🔄 執行每週維護...")
    
    # 執行每日維護
    daily_maintenance()
    
    # 運行完整分析
    subprocess.run(["python", "comprehensive_system_analysis.py"])
    
    print("✅ 每週維護完成")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "daily":
            daily_maintenance()
        elif sys.argv[1] == "weekly":
            weekly_maintenance()
    else:
        print("使用方法: python maintenance.py [daily|weekly]")
'''
    
    with open("tools/maintenance.py", "w", encoding="utf-8") as f:
        f.write(maintenance_script)
    
    print("\n✅ 維護腳本已創建: tools/maintenance.py")

if __name__ == "__main__":
    analysis = analyze_entire_system()
    analyze_folder_structure()
    opportunities = identify_optimization_opportunities()
    generate_cleanup_script()
    create_maintenance_schedule()
    
    print("\n" + "=" * 80)
    print("🎯 分析完成總結")
    print("=" * 80)
    print(f"📊 發現 {len(analysis['empty_files'])} 個空文件")
    print(f"📦 發現 {len(analysis['large_files'])} 個大文件")
    print(f"🔧 生成了系統清理和維護腳本")
    print(f"💡 提供了全面的優化建議")
    print("\n🚀 建議立即執行:")
    print("  1. python tools/system_cleanup.py")
    print("  2. python tools/maintenance.py daily")
    print("  3. 檢查並實施優化建議")
