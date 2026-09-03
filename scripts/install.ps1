<#
.SYNOPSIS
    Antigravity Traffic Light - Windows Automated Installer
.DESCRIPTION
    Installs the Antigravity hook plugin, sets up python dependencies,
    and configures the background daemon and system tray applet for Windows.
#>

$ErrorActionPreference = "Stop"

$RepoDir = Split-Path -Parent $PSScriptRoot
$PluginDir = "$env:USERPROFILE\.gemini\config\plugins\agy-traffic-light"
$StartupDir = [Environment]::GetFolderPath('Startup')

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installing Antigravity Traffic Light (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Locate Python
Write-Host "[1/4] Detecting Python installation..." -ForegroundColor Yellow
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} else {
    Write-Error "Python not found in PATH! Please install Python 3 (https://python.org) and check 'Add python.exe to PATH'."
    exit 1
}
Write-Host "✓ Using: $PythonCmd" -ForegroundColor Green

# Locate pythonw for background execution without console window
$PythonW = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonW) {
    $PyDir = Split-Path (Get-Command python.exe).Source
    $PotentialW = Join-Path $PyDir "pythonw.exe"
    if (Test-Path $PotentialW) {
        $PythonW = $PotentialW
    } else {
        $PythonW = "python.exe"
    }
}

# 2. Link Antigravity Hook Plugin
Write-Host "[2/4] Linking Antigravity hook plugin to $PluginDir..." -ForegroundColor Yellow
$ParentDir = Split-Path -Parent $PluginDir
if (-not (Test-Path $ParentDir)) {
    New-Item -ItemType Directory -Path $ParentDir -Force | Out-Null
}
if (Test-Path $PluginDir) {
    # Remove existing junction / directory
    cmd /c "rmdir /q `"$PluginDir`" 2>nul || rd /s /q `"$PluginDir`" 2>nul"
}
# Create Directory Junction (works without Developer Mode / Admin rights)
cmd /c "mklink /J `"$PluginDir`" `"$RepoDir\plugin`""
Write-Host "✓ Antigravity hook plugin linked." -ForegroundColor Green

# 3. Setup Python package and dependencies
Write-Host "[3/4] Installing Python package & dependencies (psutil, pystray, Pillow)..." -ForegroundColor Yellow
& $PythonCmd -m pip install -e "$RepoDir"
Write-Host "✓ Python package installed." -ForegroundColor Green

# 4. Setup Windows Background Autostart
Write-Host "[4/4] Configuring background autostart..." -ForegroundColor Yellow

# Create VBS runner for Daemon to run completely hidden without console window
$DaemonVbsPath = Join-Path $StartupDir "agy-traffic-daemon.vbs"
$DaemonVbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """$PythonW"" -m agy_traffic_light.daemon --port 9876", 0, False
"@
Set-Content -Path $DaemonVbsPath -Value $DaemonVbsContent -Force

# Create VBS runner for System Tray Applet
$TrayVbsPath = Join-Path $StartupDir "agy-traffic-tray.vbs"
$TrayVbsContent = @"
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run """$PythonW"" -m agy_traffic_light.tray", 0, False
"@
Set-Content -Path $TrayVbsPath -Value $TrayVbsContent -Force

Write-Host "✓ Added startup runners to: $StartupDir" -ForegroundColor Green

# Start Daemon & Tray immediately
Write-Host "Starting Daemon and Tray now..." -ForegroundColor Yellow
Start-Process -FilePath $DaemonVbsPath
Start-Process -FilePath $TrayVbsPath

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Installation Successful on Windows!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✓ Core Daemon: http://127.0.0.1:9876 (running in background)" -ForegroundColor Green
Write-Host "✓ System Tray: Indicator dot active in Taskbar Notification Area" -ForegroundColor Green
Write-Host "✓ Test State: $PythonCmd scripts\simulate.py" -ForegroundColor Green
Write-Host "💡 To uninstall at any time: powershell .\scripts\uninstall.ps1" -ForegroundColor Yellow
Write-Host "==========================================" -ForegroundColor Cyan
