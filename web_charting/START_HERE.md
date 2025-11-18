# 🚀 快速啟動指南

## PowerShell 用戶（推薦）

### 一鍵啟動
```powershell
.\start_all.bat
```

### 分別啟動
```powershell
# 啟動後端
.\start_backend.bat

# 啟動前端（新終端）
.\start_frontend.bat
```

## 訪問應用
- **前端**: http://localhost:5173
- **API文檔**: http://localhost:8001/docs

## 首次使用
1. 運行 `.\start_all.bat`
2. 等待服務啟動（約10秒）
3. 訪問 http://localhost:5173
4. 點擊「同步資料」按鈕
5. 查看K線圖

## 常見問題
**Q**: PowerShell 無法執行 bat 文件？  
**A**: 使用 `.\` 前綴，例如 `.\start_all.bat`

**Q**: 依賴安裝失敗？  
**A**: 確保已安裝 Python 和 Node.js

---

*創建: 2025-11-16*
