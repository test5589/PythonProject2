# 故障排除指南

## ✅ 已解決問題

### 1. 後端 ImportError ✅ 已修復

**錯誤訊息**:
```
ImportError: attempted relative import with no known parent package
```

**原因**: 
- `main.py` 使用相對導入 (`from ..config import config`)
- 直接運行時 Python 無法識別父包

**解決方案**: ✅
- 改為絕對導入 (`from config import config`)
- 添加 `sys.path.insert(0, backend_dir)` 確保模組可被找到
- 修復了所有 API 文件的導入

**修復的文件**:
- `backend/main.py`
- `backend/api/charts.py`
- `backend/api/sync.py`

---

### 2. 批次文件亂碼 ✅ 已修復

**問題**: 
- Windows 終端顯示中文為亂碼
- 顯示如: `??銝?..` 而非正常中文

**解決方案**: ✅
- 添加 `chcp 65001` (UTF-8 編碼)
- 改用英文訊息
- 改善可讀性

**修復的文件**:
- `start_backend.bat`
- `start_frontend.bat`
- `start_all.bat`

**Before**:
```batch
echo 啟動中...  # 顯示為亂碼
```

**After**:
```batch
@echo off
chcp 65001 >nul
echo Starting...  # 正常顯示
```

---

### 3. Frontend npm 警告 ⚠️ 正常

**警告訊息**:
```
npm warn deprecated inflight@1.0.6
npm warn deprecated rimraf@3.0.2
npm warn deprecated glob@7.2.3
...
```

**狀態**: **正常，不是錯誤**

**說明**:
- 這些是依賴包的棄用警告
- 不影響應用運行
- 前端已成功啟動 ✅
- 可以正常使用

**如何處理**:
- 可以忽略這些警告
- 或運行 `npm audit fix` (可選)
- 不影響開發和使用

---

## 🚀 如何啟動應用

### 完整重啟步驟

1. **關閉所有終端**
   - 確保之前的進程都已停止

2. **啟動應用**
   ```powershell
   cd web_charting
   .\start_all.bat
   ```

3. **等待啟動** (約5-10秒)
   - 後端: http://localhost:8001
   - 前端: http://localhost:5173

4. **驗證成功**
   - ✅ 看到 "Backend Starting..."
   - ✅ 看到 "Frontend Starting..."
   - ✅ 看到 "VITE v5.x.x ready"
   - ✅ 沒有 ImportError
   - ✅ 沒有亂碼

---

## 📋 常見問題

### Q1: PowerShell 無法執行 .bat 文件?

**錯誤**:
```
start_all.bat : 無法辨識 'start_all.bat' 詞彙
```

**解決**:
```powershell
# 錯誤方式
start_all.bat

# 正確方式
.\start_all.bat
```

---

### Q2: 後端啟動失敗?

**檢查清單**:
1. 是否安裝了所有依賴?
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. Python 版本是否 >= 3.9?
   ```bash
   python --version
   ```

3. 端口 8001 是否被占用?
   ```powershell
   netstat -ano | findstr :8001
   ```

---

### Q3: 前端啟動失敗?

**檢查清單**:
1. 是否安裝了 Node.js?
   ```bash
   node --version
   npm --version
   ```

2. 是否安裝了依賴?
   ```bash
   cd frontend
   npm install
   ```

3. 端口 5173 是否被占用?
   ```powershell
   netstat -ano | findstr :5173
   ```

---

### Q4: 前端顯示 "無K線資料"?

**解決步驟**:
1. 確認後端正常運行
2. 訪問前端頁面
3. 點擊「同步資料」按鈕
4. 等待2-3秒
5. 查看K線圖

---

### Q5: 如何停止應用?

**方法 1**: 關閉終端視窗

**方法 2**: 在終端按 `Ctrl+C`

**方法 3**: 使用任務管理器結束進程

---

## 🔍 錯誤診斷

### 檢查後端是否正常

訪問: http://localhost:8001/health

**正常回應**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

### 檢查前端是否正常

訪問: http://localhost:5173

**正常**: 看到 Web Charting 界面

---

### 查看後端日誌

後端終端會顯示:
```
INFO: Uvicorn running on http://0.0.0.0:8001
INFO: Application startup complete
```

---

### 查看前端日誌

前端終端會顯示:
```
VITE v5.x.x ready in xxx ms
➜  Local:   http://localhost:5173/
```

---

## 📚 相關文檔

- **快速開始**: `START_HERE.md`
- **API 文檔**: http://localhost:8001/docs
- **項目 README**: `README.md`

---

## ✅ 驗證清單

啟動後檢查:

- [ ] 後端終端無錯誤
- [ ] 前端終端無錯誤
- [ ] http://localhost:8001/health 返回 healthy
- [ ] http://localhost:5173 可以訪問
- [ ] 沒有 ImportError
- [ ] 沒有中文亂碼
- [ ] 可以點擊「同步資料」
- [ ] 可以看到K線圖

**如果全部打勾，恭喜！應用運行正常！** ✅

---

*最後更新: 2025-11-16*  
*版本: 1.0*
