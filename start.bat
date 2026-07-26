@echo off
cd /d "%~dp0"
if not exist config.json (
    echo [INFO] First run, starting setup wizard...
    python setup.py
    echo.
    echo Setup complete. Start monitoring now?
    choice /c yn /m "Y=Start N=Exit"
    if errorlevel 2 exit /b
)
python main.py monitor
pause
