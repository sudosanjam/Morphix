@echo off
title Morphix - Local Engine
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo .venv not found. Launching Setup...
    call setup.bat
    exit /b
)

start "" http://127.0.0.1:7474
.venv\Scripts\python.exe run.py
pause
