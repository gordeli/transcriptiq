<#
.SYNOPSIS
    Slim installer for Transcriptiq on Windows.

.DESCRIPTION
    Sets up a self-contained Python virtual environment under
    %LOCALAPPDATA%\Transcriptiq, installs Transcriptiq (and Whisper) into it,
    ensures ffmpeg is available, and creates Start Menu + Desktop shortcuts that
    launch the desktop GUI. Small download; dependencies are fetched on first
    run.

.USAGE
    Right-click this file and choose "Run with PowerShell", or run:
        powershell -ExecutionPolicy Bypass -File install-windows.ps1
#>

$ErrorActionPreference = "Stop"
$AppName  = "Transcriptiq"
$InstallDir = Join-Path $env:LOCALAPPDATA $AppName
$VenvDir  = Join-Path $InstallDir "venv"
$PyExe    = Join-Path $VenvDir "Scripts\python.exe"
$GuiExe   = Join-Path $VenvDir "Scripts\transcriptiq-gui.exe"
$Package  = "git+https://github.com/gordeli/transcriptiq.git"

Write-Host "=== Installing $AppName ===" -ForegroundColor Cyan

# 1. Ensure Python 3 is available -------------------------------------------
function Get-Python {
    foreach ($cmd in @("python", "py")) {
        $p = Get-Command $cmd -ErrorAction SilentlyContinue
        if ($p) {
            $v = & $p.Source -c "import sys; print(sys.version_info[0])" 2>$null
            if ($v -eq "3") { return $p.Source }
        }
    }
    return $null
}

$python = Get-Python
if (-not $python) {
    Write-Host "Python 3 not found. Installing via winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path","User")
    $python = Get-Python
    if (-not $python) { throw "Python install failed. Install Python 3 from python.org and re-run." }
}
Write-Host "Using Python: $python"

# 2. Ensure ffmpeg ----------------------------------------------------------
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "ffmpeg not found. Installing via winget..." -ForegroundColor Yellow
    winget install --id Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements
}

# 3. Create venv and install ------------------------------------------------
New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
if (-not (Test-Path $PyExe)) {
    Write-Host "Creating virtual environment..."
    & $python -m venv $VenvDir
}
Write-Host "Installing Transcriptiq (this downloads PyTorch + Whisper)..." -ForegroundColor Cyan
& $PyExe -m pip install --upgrade pip --quiet
& $PyExe -m pip install --upgrade $Package

# 4. Create shortcuts -------------------------------------------------------
function New-Shortcut($LinkPath) {
    $shell = New-Object -ComObject WScript.Shell
    $sc = $shell.CreateShortcut($LinkPath)
    $sc.TargetPath = $GuiExe
    $sc.WorkingDirectory = $VenvDir
    $sc.Description = "Transcriptiq - audio transcription"
    $sc.Save()
}
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$AppName.lnk"
$desktop   = Join-Path ([Environment]::GetFolderPath("Desktop")) "$AppName.lnk"
New-Shortcut $startMenu
New-Shortcut $desktop

Write-Host ""
Write-Host "=== $AppName installed! ===" -ForegroundColor Green
Write-Host "Launch it from the Start Menu / Desktop shortcut, or run:"
Write-Host "    $GuiExe"
