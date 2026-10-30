@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel% equ 0 (
  start "" http://localhost:8000
  py -3 server.py
) else (
  where python >nul 2>nul
  if %errorlevel% equ 0 (
    start "" http://localhost:8000
    python server.py
  ) else (
    echo Please install Python 3.10 or newer from python.org, then run this launcher again.
  )
)
pause
