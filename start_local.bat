@echo off
title SightFix AI - Launcher
echo ===================================================
echo  SightFix AI - Launching Backend and Frontend
echo ===================================================
echo.

start "SightFix AI Backend" cmd /k "%~dp0run_backend.bat"
timeout /t 2 /nobreak >nul
start "SightFix AI Frontend" cmd /k "%~dp0run_frontend.bat"

echo.
echo Servers launched!
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo.
pause
