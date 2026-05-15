<#
.SYNOPSIS
    自動化環境配置腳本 - 用於快速重裝開發環境。
    
.DESCRIPTION
    此腳本將自動檢查並安裝必要的開發工具（Git, Python, Node.js），
    建立 Python 虛擬環境，安裝相應的套件，並初始化 Git 倉庫。
#>

$ErrorActionPreference = "Stop"

Write-Host "🚀 開始自動化環境配置..." -ForegroundColor Cyan

# 1. 檢查並安裝 winget (Windows Package Manager)
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ 找不到 winget，請確保您的 Windows 版本支援 winget。" -ForegroundColor Yellow
} else {
    Write-Host "✅ 偵測到 winget，準備安裝必要工具..." -ForegroundColor Green
}

# 2. 安裝必要工具
function Install-App {
    param ([string]$Id, [string]$Name)
    Write-Host "📦 檢查 $Name..." -ForegroundColor Cyan
    if (!(winget list --id $Id -e --source winget -ErrorAction SilentlyContinue)) {
        Write-Host "正在安裝 $Name..." -ForegroundColor Yellow
        winget install --id $Id -e --source winget --accept-source-agreements --accept-package-agreements
    } else {
        Write-Host "✅ $Name 已安裝。" -ForegroundColor Green
    }
}

Install-App -Id "Git.Git" -Name "Git"
Install-App -Id "Python.Python.3.11" -Name "Python 3.11"
Install-App -Id "OpenJS.NodeJS.LTS" -Name "Node.js (LTS)"

# 3. 重新整理路徑環境變數
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 4. 建立 Python 虛擬環境
Write-Host "🐍 建立 Python 虛擬環境..." -ForegroundColor Cyan
if (!(Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ 虛擬環境已建立。" -ForegroundColor Green
} else {
    Write-Host "✅ .venv 已存在。" -ForegroundColor Green
}

# 5. 安裝 Python 依賴
Write-Host "📥 安裝 Python 套件..." -ForegroundColor Cyan
& ".\.venv\Scripts\pip.exe" install -r requirements.txt
& ".\.venv\Scripts\pip.exe" install -r web_charting/backend/requirements.txt

# 6. 安裝前端依賴
Write-Host "📦 安裝前端 npm 套件..." -ForegroundColor Cyan
Set-Location "web_charting/frontend"
npm install
Set-Location "../.."

# 7. Git 初始化與遠端設定 (如果尚未連結)
Write-Host "🔧 檢查 Git 倉庫狀態..." -ForegroundColor Cyan
if (!(Test-Path ".git")) {
    git init
    Write-Host "✅ Git 已初始化。" -ForegroundColor Green
}

$remoteUrl = "https://github.com/test5589/PythonProject2.git"
if (!(git remote -v | Select-String "origin")) {
    git remote add origin $remoteUrl
    Write-Host "✅ 已連結至遠端倉庫: $remoteUrl" -ForegroundColor Green
}

Write-Host "`n✨ 環境配置完成！您可以開始開發了。" -ForegroundColor Cyan
Write-Host "提示: 執行 .\start_web_charting.bat 啟動圖表系統。" -ForegroundColor White
