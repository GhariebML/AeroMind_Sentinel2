@echo off
:: ============================================================
::  AeroMind AI DroneTracking — Launch Dashboard
:: ============================================================
title AeroMind AI — Dashboard (http://localhost:5000)

set SCRIPT_DIR=%~dp0

echo.
echo  ============================================================
echo    AeroMind AI Surveillance Platform — Dashboard
echo    http://localhost:5000
echo  ============================================================
echo.

cd /d "%SCRIPT_DIR%"

:: Kill any existing server on port 5000
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000 "') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo  Starting Flask dashboard...
echo  Open your browser: http://localhost:5000
echo  Demo page:         http://localhost:5000/demo
echo.
echo  Press Ctrl+C to stop.
echo.

python dashboard\app.py

pause
