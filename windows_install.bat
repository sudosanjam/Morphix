@echo off
setlocal enabledelayedexpansion
title Morphix Installer - Universal Offline File Conversion Suite

cd /d "%~dp0"

echo ======================================================================
echo    Morphix - Universal Offline File Conversion Suite
echo    One-Click Windows Setup ^& Launcher
echo ======================================================================
echo.

:: 1. Try running modern PowerShell installer with execution policy bypassed
where powershell >nul 2>nul
if %ERRORLEVEL% equ 0 (
    powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0windows_install.ps1" %*
    if !ERRORLEVEL! neq 0 (
        echo.
        echo [ERROR] Installation failed or exited with code !ERRORLEVEL!.
        pause
    )
    exit /b !ERRORLEVEL!
)

:: 2. Fallback to native Command Prompt installer if PowerShell is absent
echo [INFO] PowerShell not available. Proceeding with standard Command Prompt setup...
echo.

:: Detect Python
set "PYTHON_EXE="
for %%C in (python py python3) do (
    where %%C >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        %%C -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
        if !ERRORLEVEL! equ 0 (
            set "PYTHON_EXE=%%C"
            goto :python_found
        )
    )
)

:python_found
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python 3.10 or higher was not found on your computer.
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Remember to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [OK] Using Python: %PYTHON_EXE%

:: Setup Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [*] Creating virtual environment in .venv...
    %PYTHON_EXE% -m venv .venv
    if not exist ".venv\Scripts\python.exe" (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
)

:: Install Dependencies
echo [*] Installing dependencies from requirements.txt...
".venv\Scripts\python.exe" -m pip install --upgrade pip --quiet
".venv\Scripts\python.exe" -m pip install -r requirements.txt
".venv\Scripts\python.exe" -m pip install -e . --no-deps

:: Create run_morphix.bat
if not exist "run_morphix.bat" (
    (
        echo @echo off
        echo setlocal
        echo cd /d "%%~dp0"
        echo if not exist ".venv\Scripts\python.exe" ^(
        echo     echo [ERROR] Virtual environment not found. Please run windows_install.bat first.
        echo     pause
        echo     exit /b 1
        echo ^)
        echo if "%%~1"=="" ^(
        echo     echo Starting Morphix Web GUI...
        echo     ".venv\Scripts\python.exe" -m app.cli.main serve
        echo ^) else ^(
        echo     ".venv\Scripts\python.exe" -m app.cli.main %%*
        echo ^)
    ) > run_morphix.bat
)

echo.
echo ======================================================================
echo  [SUCCESS] Morphix installation complete!
echo  - Launch anytime: Double-click 'run_morphix.bat'
echo  - Starting Morphix Web GUI (http://127.0.0.1:7474)...
echo ======================================================================
echo.

".venv\Scripts\python.exe" -m app.cli.main serve
if %ERRORLEVEL% neq 0 pause
