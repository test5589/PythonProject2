"""
測試運行腳本
統一執行所有測試並生成報告
"""
import unittest
import sys
import os
from datetime import datetime
from typing import List, Tuple

# 添加項目路徑
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def discover_and_run_tests(test_dir: str = None) -> unittest.TestResult:
    """
    發現並運行所有測試
    
    Args:
        test_dir: 測試目錄，默認為當前目錄
        
    Returns:
        測試結果
    """
    if test_dir is None:
        test_dir = os.path.dirname(__file__)
    
    # 發現測試
    loader = unittest.TestLoader()
    start_dir = test_dir
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 運行測試
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        descriptions=True,
        failfast=False
    )
    
    print("=" * 70)
    print(f"🧪 開始運行測試 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    result = runner.run(suite)
    
    return result

def generate_test_report(result: unittest.TestResult) -> str:
    """
    生成測試報告
    
    Args:
        result: 測試結果
        
    Returns:
        報告字符串
    """
    report_lines = []
    
    report_lines.append("=" * 70)
    report_lines.append("📊 測試報告")
    report_lines.append("=" * 70)
    
    # 基本統計
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    skipped = len(result.skipped) if hasattr(result, 'skipped') else 0
    success_rate = ((total_tests - failures - errors) / total_tests * 100) if total_tests > 0 else 0
    
    report_lines.append(f"📈 測試統計:")
    report_lines.append(f"   總測試數: {total_tests}")
    report_lines.append(f"   成功: {total_tests - failures - errors}")
    report_lines.append(f"   失敗: {failures}")
    report_lines.append(f"   錯誤: {errors}")
    report_lines.append(f"   跳過: {skipped}")
    report_lines.append(f"   成功率: {success_rate:.1f}%")
    
    # 狀態判定
    if failures == 0 and errors == 0:
        status = "✅ 全部通過"
        status_color = "綠色"
    elif failures > 0 or errors > 0:
        status = "❌ 有測試失敗"
        status_color = "紅色"
    else:
        status = "⚠️ 部分通過"
        status_color = "黃色"
    
    report_lines.append(f"\n🎯 測試狀態: {status} ({status_color})")
    
    # 失敗詳情
    if result.failures:
        report_lines.append(f"\n💥 失敗的測試 ({len(result.failures)}):")
        for i, (test, traceback) in enumerate(result.failures, 1):
            report_lines.append(f"   {i}. {test}")
            # 只顯示錯誤的最後幾行
            error_lines = traceback.strip().split('\n')
            relevant_lines = [line for line in error_lines if 'AssertionError' in line or 'assert' in line.lower()]
            if relevant_lines:
                report_lines.append(f"      └─ {relevant_lines[-1].strip()}")
    
    # 錯誤詳情
    if result.errors:
        report_lines.append(f"\n🚨 錯誤的測試 ({len(result.errors)}):")
        for i, (test, traceback) in enumerate(result.errors, 1):
            report_lines.append(f"   {i}. {test}")
            # 提取關鍵錯誤信息
            error_lines = traceback.strip().split('\n')
            for line in reversed(error_lines):
                if any(error_type in line for error_type in ['Error:', 'Exception:', 'ImportError:', 'ModuleNotFoundError:']):
                    report_lines.append(f"      └─ {line.strip()}")
                    break
    
    report_lines.append("\n" + "=" * 70)
    
    return "\n".join(report_lines)

def save_report_to_file(report: str, filename: str = None) -> None:
    """
    儲存報告到文件
    
    Args:
        report: 報告內容
        filename: 文件名，默認使用時間戳
    """
    if filename is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"test_report_{timestamp}.txt"
    
    report_dir = os.path.join(os.path.dirname(__file__), "reports")
    os.makedirs(report_dir, exist_ok=True)
    
    report_path = os.path.join(report_dir, filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 測試報告已保存到: {report_path}")

def main():
    """主函數"""
    try:
        # 運行測試
        result = discover_and_run_tests()
        
        # 生成報告
        report = generate_test_report(result)
        print(report)
        
        # 儲存報告
        save_report_to_file(report)
        
        # 設置退出代碼
        if result.failures or result.errors:
            sys.exit(1)  # 有失敗或錯誤時退出碼為1
        else:
            sys.exit(0)  # 全部通過時退出碼為0
            
    except Exception as e:
        print(f"\n❌ 測試運行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)  # 運行錯誤時退出碼為2

if __name__ == '__main__':
    main()
