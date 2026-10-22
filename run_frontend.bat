@echo off
title SightFix AI - Frontend (Next.js)
echo ===================================================
echo  Starting SightFix AI Frontend (Next.js 14)
echo ===================================================
echo.

cd /d "%~dp0frontend"

REM Ensure Node.js is in PATH
set PATH=C:\Program Files\nodejs;%LOCALAPPDATA%\Programs\nodejs;%PATH%

echo Running frontend on http://localhost:3000 ...
npm run dev

pause
