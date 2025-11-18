#!/usr/bin/env python3
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
