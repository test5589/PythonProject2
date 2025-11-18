#!/usr/bin/env python3
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
