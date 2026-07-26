@echo off
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.9+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b
)

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [INFO] First run, installing dependencies...
    pip install -r requirements.txt
    echo.
)

python launcher.py

if errorlevel 1 (
    echo.
    echo [ERROR] Program exited with error. Press any key to close.
    pause >nul
)
