@echo off
cd /d "%~dp0"
set /p INPUT="Enter trade command: "
python main.py create "%INPUT%"
pause
