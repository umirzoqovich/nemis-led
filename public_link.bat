@echo off
title Target CRM - Internet Havolasi (Public HTTPS)
echo ======================================================================
echo           O'QUV MARKAZ CRM - TARGET UCHUN OCHIQ HAVOLA
echo ======================================================================
echo.
echo 1. Oldin 'run.bat' orqali CRM ni ishga tushirganingizga ishonch hosil qiling!
echo 2. Quyida beriladigan https://... havolani nusxalang.
echo 3. Shu havolaning orqasiga '/form' qo'shib, Instagram reklamaga qo'ying!
echo.
echo Masalan: https://a.pinggy.link/form
echo ======================================================================
echo.
ssh -p 443 -R0:localhost:8000 a.pinggy.io
pause

