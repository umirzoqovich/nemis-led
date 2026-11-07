@echo off
title Target CRM Server
cd /d "%~dp0"
echo ===================================================
echo     O'quv Markaz Target CRM Tizimi Ishga Tushmoqda...
echo ===================================================
echo.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
) else (
    python run.py
)
if errorlevel 1 (
    echo.
    echo Xatolik yuz berdi! Iltimos, terminalda quyidagi buyruqni tekshiring:
    echo .\.venv\Scripts\python.exe run.py
)
pause
