@echo off
:: ============================================================
::  AeroMind AI DroneTracking — Launch Everything
::
::  Starts all components in the correct order:
::    1. AirSim binary (if found)
::    2. Flask dashboard (in new window)
::    3. Simulation runner
::
::  Usage:
::    launch_all.bat            (real AirSim if available, else mock)
::    launch_all.bat --mock     (force mock mode)
:: ============================================================
title AeroMind AI — Full System Launch

set SCRIPT_DIR=%~dp0
set MOCK_FLAG=

if /i "%~1"=="--mock" set MOCK_FLAG=--mock

cd /d "%SCRIPT_DIR%"

echo.
echo  ============================================================
echo    AeroMind AI Aerial Drone Tracking System
echo    Military Technical College — AIC Competition 2024
echo  ============================================================
echo.

:: ─── Step 1: Deploy settings ─────────────────────────────────
echo  [1/4] Deploying AirSim settings...
python -c "import shutil,pathlib; s=pathlib.Path('configs/airsim_settings.json'); d=pathlib.Path.home()/'Documents'/'AirSim'/'settings.json'; d.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(s,d); print('       OK ->',d)"
echo.

:: ─── Step 2: Start AirSim binary (if not mock) ───────────────
if "%MOCK_FLAG%"=="--mock" goto skip_airsim

set BLOCKS=%SCRIPT_DIR%airsim_envs\Blocks\WindowsNoEditor\Blocks.exe
set NH=%SCRIPT_DIR%airsim_envs\AirSimNH\WindowsNoEditor\AirSimNH.exe

echo  [2/4] Starting AirSim...
if exist "%BLOCKS%" (
    start "AirSim-Blocks" "%BLOCKS%" -windowed -ResX=1280 -ResY=720
    echo       Blocks.exe started ^(wait 30 s for UE4 to load^)
    ping 127.0.0.1 -n 35 >nul
) else if exist "%NH%" (
    start "AirSim-NH" "%NH%" -windowed -ResX=1280 -ResY=720
    echo       AirSimNH.exe started ^(wait 30 s for UE4 to load^)
    ping 127.0.0.1 -n 35 >nul
) else (
    echo       [WARN] No AirSim binary found. Switching to mock mode.
    set MOCK_FLAG=--mock
)
goto post_airsim

:skip_airsim
echo  [2/4] Skipping AirSim binary ^(mock mode^)
:post_airsim
echo.

:: ─── Step 3: Start Dashboard (background window) ─────────────
echo  [3/4] Starting Dashboard...
start "AeroMind AI-Dashboard" cmd /c "python dashboard\app.py"
ping 127.0.0.1 -n 4 >nul
echo       Dashboard: http://localhost:5000
echo       Demo page: http://localhost:5000/demo
echo.

:: ─── Step 4: Open browser ────────────────────────────────────
echo  [4/4] Opening browser...
start "" "http://localhost:5000/demo"
echo.

echo  ============================================================
echo    System ready!
echo    Dashboard: http://localhost:5000/demo
echo    Mode:      %MOCK_FLAG%
echo  ============================================================
echo.
echo  Click [Start Simulation] in the browser, or:
echo    python scripts\run_simulation.py %MOCK_FLAG% --record
echo.
echo  Press any key to start simulation in this window...
ping 127.0.0.1 -n 6 >nul

:: ─── Run simulation in this console ──────────────────────────
python scripts\run_simulation.py %MOCK_FLAG% --record --scenario dense_urban

echo.
echo  Simulation stopped.
pause
