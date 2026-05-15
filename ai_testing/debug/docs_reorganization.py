#!/usr/bin/env python3
"""
Docs資料夾重組和優化
"""

import os
import shutil
from datetime import datetime

def analyze_docs_structure():
    """分析docs資料夾結構"""
    print("=" * 80)
    print("📚 Docs資料夾結構分析")
    print("=" * 80)
    
    docs_structure = {
        "📐 architecture/": [
            "Blueprint.md",
            "GUI_improvements.md", 
            "additional_improvements.md",
            "api_weight_system_guide.md",
            "code_optimization_recommendations.md",
            "multi_symbol_monitoring_guide.md"
        ],
        "📦 archive/": [
            "fix_summary_20251111.md",
            "optimization_complete_summary.md",
            "update_summary_20251111_final.md"
        ],
        "📝 changelogs/": [
            "CHANGES_20251111.md",
            "work.md"
        ],
        "📖 guides/": [
            "interval_guide.md",
            "optimization_usage_guide.md", 
            "quick_test_guide.md"
        ],
        "📊 reports/": [
            "FINAL_OPTIMIZATION_SUMMARY_20251111.md",
            "bug-Record.md"
        ]
    }
    
    for category, files in docs_structure.items():
        print(f"\n{category}")
        for file in files:
            print(f"  - {file}")
    
    return docs_structure

def categorize_files():
    """分類文件狀態"""
    print("\n" + "=" * 80)
    print("📋 文件分類和狀態")
    print("=" * 80)
    
    categories = {
        "🟢 當前有效文檔": [
            "Blueprint.md (主要系統藍圖)",
            "api_weight_system_guide.md (API權重系統指南)",
            "multi_symbol_monitoring_guide.md (多貨幣對監控指南)",
            "interval_guide.md (時間間隔指南)",
            "bug-Record.md (錯誤記錄)"
        ],
        "🟡 需要更新的文檔": [
            "GUI_improvements.md (GUI改進，需要更新)",
            "code_optimization_recommendations.md (代碼優化建議，需要更新)",
            "optimization_usage_guide.md (優化使用指南，需要更新)",
            "quick_test_guide.md (快速測試指南，需要更新)"
        ],
        "🔴 過時文檔": [
            "additional_improvements.md (額外改進，已完成)",
            "fix_summary_20251111.md (舊的修復總結)",
            "optimization_complete_summary.md (舊的優化總結)",
            "update_summary_20251111_final.md (舊的更新總結)",
            "CHANGES_20251111.md (舊的變更記錄)",
            "FINAL_OPTIMIZATION_SUMMARY_20251111.md (舊的最終總結)",
            "work.md (工作記錄，內容不明)"
        ]
    }
    
    for category, files in categories.items():
        print(f"\n{category}:")
        for file in files:
            print(f"  - {file}")

def create_reorganization_plan():
    """創建重組計劃"""
    print("\n" + "=" * 80)
    print("🔄 重組計劃")
    print("=" * 80)
    
    plan = {
        "1. 創建新的資料夾結構": [
            "📁 current/ - 當前有效文檔",
            "📁 outdated/ - 過時文檔歸檔",
            "📁 templates/ - 文檔模板",
            "📁 maintenance/ - 維護記錄"
        ],
        "2. 文件重新分類": [
            "移動當前有效文檔到 current/",
            "移動過時文檔到 outdated/",
            "更新需要更新的文檔",
            "創建新的維護文檔"
        ],
        "3. 創建新文檔": [
            "README.md - 文檔總覽",
            "MAINTENANCE.md - 維護指南", 
            "TEMPLATES.md - 文檔模板",
            "INDEX.md - 文檔索引"
        ],
        "4. 優化現有文檔": [
            "更新Blueprint.md與根目錄BLUEPRINT.md同步",
            "合併相似內容的文檔",
            "標準化文檔格式",
            "添加交叉引用"
        ]
    }
    
    for step, actions in plan.items():
        print(f"\n{step}:")
        for action in actions:
            print(f"  - {action}")

def suggest_new_structure():
    """建議新的文檔結構"""
    print("\n" + "=" * 80)
    print("📁 建議的新文檔結構")
    print("=" * 80)
    
    new_structure = """
docs/
├── README.md                    # 文檔總覽和導航
├── INDEX.md                     # 文檔索引
│
├── current/                     # 當前有效文檔
│   ├── system/
│   │   ├── Blueprint.md         # 系統藍圖
│   │   └── architecture.md      # 系統架構
│   ├── guides/
│   │   ├── api_weight_guide.md  # API權重指南
│   │   ├── monitoring_guide.md  # 監控指南
│   │   └── interval_guide.md    # 時間間隔指南
│   └── maintenance/
│       ├── bug_record.md        # 錯誤記錄
│       └── optimization.md      # 優化記錄
│
├── templates/                   # 文檔模板
│   ├── guide_template.md        # 指南模板
│   ├── api_doc_template.md      # API文檔模板
│   └── changelog_template.md    # 變更記錄模板
│
└── outdated/                    # 過時文檔歸檔
    ├── 2025-11/                 # 按月份歸檔
    │   ├── fix_summaries/
    │   ├── old_guides/
    │   └── deprecated_docs/
    └── README.md                # 歸檔說明
"""
    
    print(new_structure)

if __name__ == "__main__":
    analyze_docs_structure()
    categorize_files()
    create_reorganization_plan()
    suggest_new_structure()
