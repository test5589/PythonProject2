# AI測試和調試資料夾

## 📁 資料夾結構

### `/tests/` - 測試腳本
包含所有AI輔助創建的測試腳本：
- `test_*.py` - 各種功能測試腳本
- 用於驗證系統功能和修復效果

### `/debug/` - 調試工具
包含調試和分析工具：
- `*analysis*.py` - 系統分析腳本
- `fix_summary.py` - 修復總結報告
- 其他調試輔助工具

## 🎯 用途

1. **功能測試**: 驗證新功能和修復效果
2. **系統分析**: 分析代碼結構和性能
3. **調試輔助**: 協助問題診斷和解決
4. **開發記錄**: 保存開發過程中的測試和分析

## 📋 使用指南

### 運行測試
```bash
# 進入測試目錄
cd ai_testing/tests

# 運行特定測試
python test_api_fix.py
python test_all_fixes.py
python test_final_improvements.py
```

### 使用調試工具
```bash
# 進入調試目錄
cd ai_testing/debug

# 運行分析工具
python utils_analysis.py
python fix_summary.py
```

## 🔧 維護

- 定期清理過時的測試腳本
- 更新測試以反映最新的系統變更
- 保持調試工具的實用性和準確性

---
*此資料夾由AI輔助創建和維護，用於提高開發效率和代碼品質*
