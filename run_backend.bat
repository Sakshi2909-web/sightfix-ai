@echo off
title SightFix AI - Backend Server
echo ===================================================
echo  Starting SightFix AI Backend Server (FastAPI)
echo ===================================================
echo.

cd /d "%~dp0backend"

REM Activate virtual environment if available
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
)

REM Set PYTHONPATH to current directory so app module is always found
set PYTHONPATH=%cd%;%PYTHONPATH%

echo Running backend on http://localhost:8000 ...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
