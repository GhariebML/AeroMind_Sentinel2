@echo off
:: ============================================================
::  AeroMind AI DroneTracking — Launch Simulation
::
::  Usage:
::    launch_simulation.bat              (real AirSim mode)
::    launch_simulation.bat --mock       (mock mode, no AirSim)
::    launch_simulation.bat --scenario highway
:: ============================================================
title AeroMind AI — Simulation Runner

set SCRIPT_DIR=%~dp0
set MOCK=
set SCENARIO=dense_urban

:: Parse arguments
:parse_args
if "%~1"=="" goto done_args
if /i "%~1"=="--mock"     set MOCK=--mock & shift & goto parse_args
if /i "%~1"=="--scenario" set SCENARIO=%~2 & shift & shift & goto parse_args
shift & goto parse_args
:done_args

cd /d "%SCRIPT_DIR%"

echo.
echo  ============================================================
echo    AeroMind AI Simulation Runner
echo    Scenario  : %SCENARIO%
echo    Mode      : %MOCK%
echo  ============================================================
echo.

if "%MOCK%"=="--mock" (
    echo  Running in MOCK mode ^(no AirSim required^)...
) else (
    echo  Connecting to AirSim at 127.0.0.1:41451 ...
    echo  Make sure launch_airsim.bat is already running!
    echo.
    python scripts\check_airsim.py
    if errorlevel 1 (
        echo.
        echo  [WARNING] AirSim not reachable. Switching to mock mode...
        set MOCK=--mock
    )
)

echo.
echo  Starting simulation. Frames saved to experiments\results\frames_%SCENARIO%\
echo  Press Ctrl+C to stop.
echo.

python scripts\run_simulation.py %MOCK% --record --scenario %SCENARIO%

echo.
echo  Simulation stopped.
pause
