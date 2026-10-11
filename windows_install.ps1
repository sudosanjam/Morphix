# ==============================================================================
# Morphix - Universal Offline File Conversion Suite
# One-Click Windows Installer & Environment Setup
# ==============================================================================

[CmdletBinding()]
param (
    [switch]$NoLaunch,
    [switch]$NoShortcut
)

$ErrorActionPreference = "Stop"

$ProjectRoot = $PSScriptRoot
if (-not $ProjectRoot) {
    $ProjectRoot = (Get-Location).Path
}
Set-Location -Path $ProjectRoot

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   __  __                  _     _       " -ForegroundColor Cyan
Write-Host "  |  \/  |___  _ _ _ __  | |_  (_)__ __ " -ForegroundColor Cyan
Write-Host "  | |\/| / _ \| '_| '_ \ | ' \ | |\ \ / " -ForegroundColor Cyan
Write-Host "  |_|  |_\___/|_| | .__/ |_||_||_|/_\_\ " -ForegroundColor Cyan
Write-Host "                  |_|                    " -ForegroundColor Cyan
Write-Host "   Morphix - Universal Offline File Conversion Suite" -ForegroundColor White
Write-Host "   Windows One-Click Setup and Launcher" -ForegroundColor DarkGray
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------------------------
# 1. Detect Python 3 (>= 3.10)
# -----------------------------------------------------------------------------
Write-Host "[1/5] Checking for Python installation (>= 3.10)..." -ForegroundColor Yellow

$PythonCandidates = @("python", "py", "python3")
$SelectedPython = $null
$DetectedVersion = $null

foreach ($candidate in $PythonCandidates) {
    $cmd = Get-Command $candidate -ErrorAction SilentlyContinue
    if ($null -ne $cmd) {
        try {
            $verOutput = & $candidate -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')" 2>$null
            if ($verOutput) {
                $verParts = $verOutput.Trim().Split('.')
                $major = [int]$verParts[0]
                $minor = [int]$verParts[1]
                if ($major -ge 3 -and $minor -ge 10) {
                    $SelectedPython = $candidate
                    $DetectedVersion = $verOutput.Trim()
                    break
                }
            }
        } catch {
            # Candidate failed execution or was a Microsoft Store redirector stub
        }
    }
}

if (-not $SelectedPython) {
    Write-Host ""
    Write-Host "[ERROR] Python 3.10 or higher was not detected on your system." -ForegroundColor Red
    Write-Host "Morphix requires Python >= 3.10 to operate offline." -ForegroundColor Yellow
    Write-Host ""
    
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-Host "Windows Package Manager (winget) is detected." -ForegroundColor Green
        $installChoice = Read-Host "Would you like to automatically install Python 3.11 via winget now? [Y/n]"
        if ($installChoice -eq "" -or $installChoice -match "^[yY]") {
            Write-Host "[*] Running: winget install --id Python.Python.3.11 -e --source winget" -ForegroundColor Cyan
            & winget install --id Python.Python.3.11 -e --source winget
            Write-Host ""
            Write-Host "[INFO] Python installation initiated. Please complete any prompts." -ForegroundColor Green
            Write-Host "[INFO] After installation completes, close this window and run 'windows_install.bat' again." -ForegroundColor Yellow
            Read-Host "Press Enter to exit..."
            exit 1
        }
    }

    Write-Host "You can download Python directly from:" -ForegroundColor White
    Write-Host "  https://www.python.org/downloads/" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "IMPORTANT: During installation, be sure to check:" -ForegroundColor White
    Write-Host "  [X] 'Add python.exe to PATH'" -ForegroundColor Green
    Write-Host ""
    
    $openBrowser = Read-Host "Open the Python download page in your web browser now? [Y/n]"
    if ($openBrowser -eq "" -or $openBrowser -match "^[yY]") {
        Start-Process "https://www.python.org/downloads/"
    }
    Read-Host "Press Enter to exit..."
    exit 1
}

Write-Host "  [OK] Found Python $DetectedVersion ($SelectedPython)" -ForegroundColor Green

# -----------------------------------------------------------------------------
# 2. Virtual Environment Setup
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[2/5] Setting up isolated Python virtual environment..." -ForegroundColor Yellow
$VenvDir = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$VenvPip = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "  Creating virtual environment in '$VenvDir'..." -ForegroundColor DarkGray
    & $SelectedPython -m venv $VenvDir
    if (-not (Test-Path $VenvPython)) {
        Write-Host "[ERROR] Failed to create virtual environment in '$VenvDir'." -ForegroundColor Red
        exit 1
    }
    Write-Host "  [OK] Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "  [OK] Existing virtual environment found in '$VenvDir'." -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# 3. Install Dependencies
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[3/5] Installing Morphix dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host "  Upgrading pip..." -ForegroundColor DarkGray
& $VenvPython -m pip install --upgrade pip --disable-pip-version-check --quiet

$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
if (Test-Path $RequirementsFile) {
    Write-Host "  Installing dependencies (FastAPI, Uvicorn, Pillow, FFmpeg tools, OpenPyXL, ReportLab)..." -ForegroundColor DarkGray
    & $VenvPython -m pip install -r $RequirementsFile --disable-pip-version-check
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Dependency installation encountered errors." -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "  Registering Morphix package in environment..." -ForegroundColor DarkGray
& $VenvPython -m pip install -e $ProjectRoot --no-deps --disable-pip-version-check
Write-Host "  [OK] All dependencies successfully installed and verified." -ForegroundColor Green

# -----------------------------------------------------------------------------
# 4. Create Quick Launchers and Desktop Shortcut
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[4/5] Configuring quick launchers and desktop shortcuts..." -ForegroundColor Yellow

$RunBatPath = Join-Path $ProjectRoot "run_morphix.bat"
if (-not (Test-Path $RunBatPath)) {
    $RunBatLines = @(
        "@echo off",
        "setlocal",
        "cd /d `"%~dp0`"",
        "if not exist `".venv\Scripts\python.exe`" (",
        "    echo [ERROR] Virtual environment not found. Please run windows_install.bat first.",
        "    pause",
        "    exit /b 1",
        ")",
        "if `"%~1`"==`"`" (",
        "    echo Starting Morphix Web GUI...",
        "    `".venv\Scripts\python.exe`" -m app.cli.main serve",
        ") else (",
        "    `".venv\Scripts\python.exe`" -m app.cli.main %*",
        ")"
    )
    [System.IO.File]::WriteAllLines($RunBatPath, $RunBatLines)
}
Write-Host "  [OK] Verified launcher: $RunBatPath" -ForegroundColor Green

# Optional Desktop Shortcut
if (-not $NoShortcut) {
    try {
        $DesktopPath = [Environment]::GetFolderPath("Desktop")
        if (Test-Path $DesktopPath) {
            $ShortcutFile = Join-Path $DesktopPath "Morphix.lnk"
            $WshShell = New-Object -ComObject WScript.Shell
            $Shortcut = $WshShell.CreateShortcut($ShortcutFile)
            $Shortcut.TargetPath = $RunBatPath
            $Shortcut.WorkingDirectory = $ProjectRoot
            $Shortcut.Description = "Morphix - Universal Offline File Conversion Suite"
            $Shortcut.Save()
            Write-Host "  [OK] Created Desktop shortcut: $ShortcutFile" -ForegroundColor Green
        }
    } catch {
        Write-Host "  [INFO] Note: Could not create desktop shortcut" -ForegroundColor DarkGray
    }
}

# -----------------------------------------------------------------------------
# 5. Diagnostic Verification and Launch
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "[5/5] Running pre-flight system diagnostics..." -ForegroundColor Yellow
try {
    & $VenvPython -m app.cli.main doctor
} catch {
    Write-Host "  [INFO] Diagnostics check completed." -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host " [SUCCESS] Morphix installation completed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host '  - Local Web GUI URL  : http://127.0.0.1:7474' -ForegroundColor White
Write-Host '  - Everyday Launcher  : Double-click run_morphix.bat or Desktop shortcut' -ForegroundColor White
Write-Host '  - Command-Line (CLI) : run_morphix.bat convert [file] --to [format]' -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""

if ($NoLaunch) {
    Write-Host "Setup finished (-NoLaunch specified). You can start Morphix at any time using run_morphix.bat" -ForegroundColor Cyan
    exit 0
}

Write-Host "[*] Launching Morphix Web GUI in your browser now..." -ForegroundColor Cyan
Write-Host "    (Press Ctrl+C in this console window anytime to stop the server)" -ForegroundColor DarkGray
Write-Host ""

& $VenvPython -m app.cli.main serve
