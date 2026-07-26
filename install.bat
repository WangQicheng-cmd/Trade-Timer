@echo off
cd /d "%~dp0"
pip install -r requirements.txt
if %errorlevel%==0 (
    echo.
    echo [OK] Dependencies installed. Run setup.bat next.
) else (
    echo.
    echo [ERROR] Install failed. Check Python environment.
)
pause
