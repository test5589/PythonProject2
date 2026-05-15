<#
.SYNOPSIS
    Environment Setup Script
#>

$ErrorActionPreference = "Continue"

Write-Host "🚀 Starting environment setup..." -ForegroundColor Cyan

# 1. Check winget
if (!(Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "⚠️ winget not found." -ForegroundColor Yellow
} else {
    Write-Host "✅ winget detected." -ForegroundColor Green
}

# 2. Define Install function
function Install-App {
    param ([string]$Id, [string]$Name)
    Write-Host "📦 Checking $Name..." -ForegroundColor Cyan
    $check = winget list --id $Id -e --source winget -ErrorAction SilentlyContinue
    if (!$check) {
        Write-Host "Installing $Name..." -ForegroundColor Yellow
        winget install --id $Id -e --source winget --accept-source-agreements --accept-package-agreements
    } else {
        Write-Host "✅ $Name is already installed." -ForegroundColor Green
    }
}

# 3. Run Installations
try {
    Install-App -Id "Git.Git" -Name "Git"
    Install-App -Id "Python.Python.3.11" -Name "Python 3.11"
    Install-App -Id "OpenJS.NodeJS.LTS" -Name "Node.js (LTS)"
} catch {
    Write-Host "⚠️ Issues during installation, please check manually." -ForegroundColor Yellow
}

# 4. Update Path
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 5. Python venv
Write-Host "🐍 Checking Python venv..." -ForegroundColor Cyan
if (!(Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "✅ Venv created." -ForegroundColor Green
} else {
    Write-Host "✅ .venv exists." -ForegroundColor Green
}

# 6. Install Python deps
Write-Host "📥 Installing Python packages..." -ForegroundColor Cyan
if (Test-Path "requirements.txt") {
    & ".\.venv\Scripts\pip.exe" install -r requirements.txt
}
if (Test-Path "web_charting/backend/requirements.txt") {
    & ".\.venv\Scripts\pip.exe" install -r web_charting/backend/requirements.txt
}

# 7. Frontend npm
Write-Host "📦 Installing npm packages..." -ForegroundColor Cyan
if (Test-Path "web_charting/frontend") {
    Push-Location "web_charting/frontend"
    npm install
    Pop-Location
}

# 8. Git Init
Write-Host "🔧 Checking Git status..." -ForegroundColor Cyan
if (!(Test-Path ".git")) {
    & git init
    Write-Host "✅ Git initialized." -ForegroundColor Green
}

$remoteUrl = "https://github.com/test5589/PythonProject2.git"
$remotes = & git remote -v
if (!($remotes -like "*origin*")) {
    & git remote add origin $remoteUrl
    Write-Host "✅ Remote linked." -ForegroundColor Green
}

Write-Host "✨ Setup Complete!" -ForegroundColor Cyan
