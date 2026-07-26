# AI Trade Alarm - Windows 一键安装脚本
# 用法：在 PowerShell 中执行
#   irm https://raw.githubusercontent.com/<用户名>/ai-trade-alarm/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$AppName = "TradeTimer"
$InstallDir = "$env:USERPROFILE\$AppName"

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "  TradeTimer - Installer" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Git
$gitOk = $false
try { git --version | Out-Null; $gitOk = $true } catch {}

if (-not $gitOk) {
    Write-Host "[ERROR] Git not found. Please install Git first:" -ForegroundColor Red
    Write-Host "  https://git-scm.com/download/win"
    return
}
Write-Host "[OK] Git found" -ForegroundColor Green

# 检查 Python
$pythonOk = $false
try { python --version | Out-Null; $pythonOk = $true } catch {}
if (-not $pythonOk) {
    try { python3 --version | Out-Null; $alias = "python3"; $pythonOk = $true } catch {}
}

if (-not $pythonOk) {
    Write-Host "[ERROR] Python not found. Please install Python 3.9+ first:" -ForegroundColor Red
    Write-Host "  https://www.python.org/downloads/"
    Write-Host "  Remember to check 'Add Python to PATH' during installation"
    return
}
Write-Host "[OK] Python found" -ForegroundColor Green

# 克隆或更新
if (Test-Path $InstallDir) {
    Write-Host "[INFO] Updating existing installation..." -ForegroundColor Yellow
    Set-Location $InstallDir
    git pull
} else {
    Write-Host "[INFO] Cloning repository..." -ForegroundColor Yellow
    git clone https://github.com/WangQicheng-cmd/Trade-Timer.git $InstallDir 2>$null
    if (-not (Test-Path $InstallDir)) {
        Write-Host "[ERROR] Clone failed. Please check repository URL." -ForegroundColor Red
        return
    }
    Set-Location $InstallDir
}

# 安装依赖
Write-Host "[INFO] Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Dependency installation failed" -ForegroundColor Red
    return
}
Write-Host "[OK] Dependencies installed" -ForegroundColor Green

# 创建桌面快捷方式
$shortcutPath = "$env:USERPROFILE\Desktop\TradeTimer.bat"
$batContent = @"
@echo off
cd /d "$InstallDir"
python launcher.py
"@
Set-Content -Path $shortcutPath -Value $batContent -Encoding ASCII

Write-Host ""
Write-Host "======================================" -ForegroundColor Green
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Next steps:" -ForegroundColor Cyan
Write-Host "    1. Install Ollama: https://ollama.ai/"
Write-Host "    2. Run: ollama pull deepseek-r1"
Write-Host "    3. Run: ollama serve"
Write-Host "    4. Double-click 'AI-Trade-Alarm.bat' on your Desktop"
Write-Host "       Or run: cd $InstallDir ; python launcher.py"
Write-Host ""
Write-Host "  First time? Select option 1 in the menu to configure." -ForegroundColor Yellow
Write-Host ""

Set-Location $InstallDir
Write-Host "Starting TradeTimer now..." -ForegroundColor Cyan
python launcher.py
