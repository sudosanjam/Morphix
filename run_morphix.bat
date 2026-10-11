@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ======================================================================
    echo  [ERROR] Morphix virtual environment not found!
    echo  Please run 'windows_install.bat' first to install dependencies.
    echo ======================================================================
    echo.
    pause
    exit /b 1
)

if "%~1"=="" (
    echo Starting Morphix Web GUI at http://127.0.0.1:7474
    echo Press Ctrl+C to stop the server.
    ".venv\Scripts\python.exe" -m app.cli.main serve
) else (
    ".venv\Scripts\python.exe" -m app.cli.main %*
)
