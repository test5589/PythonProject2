#!/usr/bin/env python3
"""
文件分類分析腳本
檢測並分類所有未歸納的程式碼文件
"""

import os
import glob
from pathlib import Path

def analyze_python_files():
    """分析所有Python文件"""
    print("=" * 80)
    print("🔍 Python文件分類分析")
    print("=" * 80)
    
    # 獲取所有Python文件
    python_files = []
    for root, dirs, files in os.walk("."):
        # 跳過某些目錄
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'venv', '.venv']]
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    # 按類別分類
    categories = {
        "🧪 測試和調試腳本": [],
        "🏗️ 核心系統文件": [],
        "🔧 工具和實用程序": [],
        "🌐 Web應用文件": [],
        "⚙️ 配置文件": [],
        "📊 示例和演示": [],
        "🗑️ 備份和重複文件": [],
        "❓ 未分類文件": []
    }
    
    for file_path in python_files:
        filename = os.path.basename(file_path)
        file_dir = os.path.dirname(file_path)
        
        # 分類邏輯
        if any(keyword in filename.lower() for keyword in ['test', 'debug', 'capacity', 'check', 'final']):
            categories["🧪 測試和調試腳本"].append(file_path)
        elif any(keyword in filename.lower() for keyword in ['backup', 'original', 'fixed', 'restored']):
            categories["🗑️ 備份和重複文件"].append(file_path)
        elif 'core' in file_dir:
            categories["🏗️ 核心系統文件"].append(file_path)
        elif 'config' in file_dir:
            categories["⚙️ 配置文件"].append(file_path)
        elif 'web' in file_dir:
            categories["🌐 Web應用文件"].append(file_path)
        elif 'examples' in file_dir:
            categories["📊 示例和演示"].append(file_path)
        elif any(keyword in filename.lower() for keyword in ['update', 'force', 'api_weight']):
            categories["🔧 工具和實用程序"].append(file_path)
        else:
            categories["❓ 未分類文件"].append(file_path)
    
    # 顯示分類結果
    for category, files in categories.items():
        if files:
            print(f"\n{category} ({len(files)}個文件):")
            for file in sorted(files):
                size = os.path.getsize(file) if os.path.exists(file) else 0
                print(f"  - {file} ({size:,} bytes)")
    
    return categories

def suggest_reorganization():
    """建議重組方案"""
    print("\n" + "=" * 80)
    print("📋 文件重組建議")
    print("=" * 80)
    
    suggestions = {
        "🧪 移動到 ai_testing/": [
            "所有測試腳本 (*test*.py, *debug*.py, *capacity*.py)",
            "調試工具 (debug_*.py, check_*.py)",
            "最終測試腳本 (final_*.py)"
        ],
        "🗑️ 清理備份文件": [
            "刪除 *_backup.py, *_original.py, *_fixed.py",
            "保留最新版本，移除重複文件",
            "歸檔到 archive/ 資料夾"
        ],
        "🔧 創建 tools/ 資料夾": [
            "移動工具腳本 (update_*.py, force_*.py)",
            "API相關工具 (api_weight_evaluator.py)",
            "數據庫工具 (check_db.py)"
        ],
        "🌐 整理 web/ 資料夾": [
            "保持現有結構",
            "確保所有web相關文件在此"
        ],
        "📊 整理 examples/ 資料夾": [
            "保持現有結構",
            "添加更多示例文件"
        ]
    }
    
    for category, items in suggestions.items():
        print(f"\n{category}:")
        for item in items:
            print(f"  - {item}")

def create_folder_structure():
    """建議的資料夾結構"""
    print("\n" + "=" * 80)
    print("📁 建議的資料夾結構")
    print("=" * 80)
    
    structure = """
PythonProject2/
├── core/                        # 核心系統文件
│   ├── gui_*.py                # GUI相關
│   ├── weight_test_controller.py
│   └── feature_panel.py
├── modules/                     # 模組
│   ├── utils/                  # 工具模組
│   └── api_weight_evaluator.py
├── config/                      # 配置文件
│   ├── api_config.py
│   └── trading_config.py
├── web/                         # Web應用
│   ├── streamlit_app.py
│   └── debug_logger.py
├── examples/                    # 示例代碼
│   └── multi_api_example.py
├── tools/                       # 工具腳本 (新建)
│   ├── update_api_field.py
│   ├── force_error_log.py
│   └── check_db.py
├── ai_testing/                  # AI測試和調試
│   ├── tests/                  # 測試腳本
│   │   ├── capacity_test.py
│   │   ├── advanced_capacity_test.py
│   │   ├── final_test.py
│   │   └── test_*.py
│   └── debug/                  # 調試工具
│       ├── debug_gui_crash.py
│       └── *analysis*.py
└── archive/                     # 歸檔 (新建)
    └── backup_files/           # 備份文件
        ├── gui_controls_backup.py
        ├── gui_controls_original.py
        └── gui_controls_fixed.py
"""
    
    print(structure)

if __name__ == "__main__":
    categories = analyze_python_files()
    suggest_reorganization()
    create_folder_structure()
