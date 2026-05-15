# Fix Windows Firewall for Web Charting
# Run this script as Administrator

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Fixing Windows Firewall Rules" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Please right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "Running as Administrator... OK" -ForegroundColor Green
Write-Host ""

# Remove old rules if they exist
Write-Host "Removing old firewall rules (if any)..." -ForegroundColor Yellow
Remove-NetFirewallRule -DisplayName "Web Charting Backend" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "Web Charting Frontend" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "Python for Web Charting" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "Node.js for Web Charting" -ErrorAction SilentlyContinue

Write-Host "Creating new firewall rules..." -ForegroundColor Yellow
Write-Host ""

# Allow Backend Port 8001
Write-Host "1. Allowing port 8001 (Backend)..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName "Web Charting Backend" `
    -Direction Inbound `
    -LocalPort 8001 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any

# Allow Frontend Port 5173
Write-Host "2. Allowing port 5173 (Frontend)..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName "Web Charting Frontend" `
    -Direction Inbound `
    -LocalPort 5173 `
    -Protocol TCP `
    -Action Allow `
    -Profile Any

# Allow Python
Write-Host "3. Allowing Python..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName "Python for Web Charting" `
    -Direction Inbound `
    -Program "C:\Python312\python.exe" `
    -Action Allow `
    -Profile Any

# Allow Node.js (find node.exe location)
$nodePath = (Get-Command node -ErrorAction SilentlyContinue).Source
if ($nodePath) {
    Write-Host "4. Allowing Node.js at: $nodePath" -ForegroundColor Cyan
    New-NetFirewallRule -DisplayName "Node.js for Web Charting" `
        -Direction Inbound `
        -Program $nodePath `
        -Action Allow `
        -Profile Any
} else {
    Write-Host "4. Node.js not found, skipping..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "Firewall Rules Created!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""
Write-Host "You can now start the application:" -ForegroundColor Cyan
Write-Host "  cd web_charting" -ForegroundColor White
Write-Host "  .\start_all.bat" -ForegroundColor White
Write-Host ""

pause
