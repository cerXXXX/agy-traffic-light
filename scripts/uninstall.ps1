<#
.SYNOPSIS
    Antigravity Traffic Light - Windows Automated Uninstaller
.DESCRIPTION
    Stops background processes, removes startup runners, unlinks the Antigravity hook plugin,
    and optionally uninstalls the Python package.
.PARAMETER PluginOnly
    Only unlinks the Antigravity hook plugin, leaving background processes intact.
.PARAMETER KeepPackage
    Removes plugin and startup runners, but keeps the Python package installed.
.PARAMETER Force
    Skips interactive confirmation.
#>

param(
    [switch]$PluginOnly,
    [switch]$KeepPackage,
    [switch]$Force
)

$ErrorActionPreference = "Continue"

$PluginDir = "$env:USERPROFILE\.gemini\config\plugins\agy-traffic-light"
$StartupDir = [Environment]::GetFolderPath('Startup')
$DaemonVbsPath = Join-Path $StartupDir "agy-traffic-daemon.vbs"
$TrayVbsPath = Join-Path $StartupDir "agy-traffic-tray.vbs"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Uninstalling Antigravity Traffic Light (Windows)" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not $Force -and [Environment]::UserInteractive) {
    $action = if ($PluginOnly) { "unlink the Antigravity hook plugin" } else { "stop background services, remove startup runners, and unlink the plugin" }
    $confirmation = Read-Host "Are you sure you want to $action? (y/N)"
    if ($confirmation -notmatch "^[yY]([eE][sS])?$") {
        Write-Host "Uninstallation cancelled." -ForegroundColor Yellow
        exit 0
    }
}

# 1. Remove Antigravity Hook Plugin
Write-Host "[1/4] Removing Antigravity hook plugin link..." -ForegroundColor Yellow
if (Test-Path $PluginDir) {
    cmd /c "rmdir /q `"$PluginDir`" 2>nul || rd /s /q `"$PluginDir`" 2>nul"
    Write-Host "✓ Antigravity hook plugin removed." -ForegroundColor Green
} else {
    Write-Host "• Hook plugin not found (skipped)." -ForegroundColor Gray
}

if ($PluginOnly) {
    Write-Host ""
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "Plugin Removal Complete!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    exit 0
}

# 2. Stop running processes
Write-Host "[2/4] Stopping running daemon & tray processes..." -ForegroundColor Yellow
Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match "agy_traffic_light"
} | ForEach-Object {
    Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Stopped process $($_.ProcessId) ($($_.Name))" -ForegroundColor Green
}

# 3. Remove Startup runners
Write-Host "[3/4] Removing startup runners..." -ForegroundColor Yellow
if (Test-Path $DaemonVbsPath) {
    Remove-Item -Path $DaemonVbsPath -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Removed $DaemonVbsPath" -ForegroundColor Green
}
if (Test-Path $TrayVbsPath) {
    Remove-Item -Path $TrayVbsPath -Force -ErrorAction SilentlyContinue
    Write-Host "✓ Removed $TrayVbsPath" -ForegroundColor Green
}

# 4. Uninstall Python Package
if (-not $KeepPackage) {
    Write-Host "[4/4] Uninstalling Python package..." -ForegroundColor Yellow
    $PythonCmd = $null
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $PythonCmd = "python"
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        $PythonCmd = "py"
    }
    if ($PythonCmd) {
        & $PythonCmd -m pip uninstall -y agy-traffic-light
        Write-Host "✓ Python package uninstalled." -ForegroundColor Green
    }
} else {
    Write-Host "[4/4] Keeping Python package as requested (-KeepPackage)." -ForegroundColor Gray
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Uninstallation Successful on Windows!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
