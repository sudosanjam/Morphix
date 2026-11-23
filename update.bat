@echo off
title Morphix - One-Click Updater
cd /d "%~dp0"

echo =============================================================
echo             Morphix One-Click Repository Updater
echo =============================================================
echo.

echo [*] Pulling latest updates from GitHub...
git pull origin main
if %errorlevel% neq 0 (
    echo [*] Fallback pull...
    git pull
)

if exist ".venv\Scripts\python.exe" (
    echo [*] Synchronizing requirements...
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    echo [*] Verifying installation...
    .venv\Scripts\python.exe -c "import app; print('[✓] Morphix core verified.')"
) else (
    echo [!] Note: .venv not found. Please run setup.bat or Setup.exe.
)

echo.
echo =============================================================
echo          [SUCCESS] Morphix is fully updated!
echo =============================================================
echo.
pause
