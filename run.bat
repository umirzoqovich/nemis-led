@echo off
title DeutschZentrum Target CRM Server
cd /d "%~dp0"
echo ===================================================
echo   DEUTSCHZENTRUM - NEMIS TILI TARGET CRM TIZIMI
echo ===================================================
echo.
echo Server ishga tushirilmoqda va brauzer ochilmoqda...
echo Boshqaruv paneli: http://localhost:8000
echo.
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" run.py
) else (
    python run.py
)
if errorlevel 1 (
    echo.
    echo Xatolik yuz berdi! Terminalda quyidagi buyruqni bering:
    echo .\.venv\Scripts\python.exe run.py
)
pause
