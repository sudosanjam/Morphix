@echo off
title Morphix - One-Click Setup
cd /d "%~dp0"

echo =============================================================
echo          Morphix One-Click Installer ^& Setup
echo =============================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    where py >nul 2>nul
    if %errorlevel% neq 0 (
        echo [X] Python 3 was not found on PATH.
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        echo (Check "Add Python to PATH" during installation)
        pause
        exit /b 1
    )
    set "PY_CMD=py -3"
) else (
    set "PY_CMD=python"
)

if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    %PY_CMD% -m venv .venv
    if %errorlevel% neq 0 (
        echo [X] Failed to create .venv
        pause
        exit /b 1
    )
)

echo [*] Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip

echo [*] Installing dependencies from requirements.txt...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [X] Error installing requirements.
    pause
    exit /b 1
)

echo.
echo =============================================================
echo          [SUCCESS] Morphix setup completed!
echo =============================================================
echo.
echo You can run Morphix anytime by double-clicking Morphix.exe or run.bat
echo.
set /p START_NOW="Launch Morphix now? (Y/N, default Y): "
if /i "%START_NOW%"=="N" goto end

start "" .venv\Scripts\python.exe run.py
timeout /t 2 >nul
start http://127.0.0.1:7474

:end
