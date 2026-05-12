@echo off
:: ============================================================
::  AeroMind AI DroneTracking — Launch AirSim Binary
::  Run this FIRST before dashboard or simulation.
:: ============================================================
title AeroMind AI — AirSim Launcher

set SCRIPT_DIR=%~dp0
set BLOCKS=%SCRIPT_DIR%airsim_envs\Blocks\WindowsNoEditor\Blocks.exe
set NH=%SCRIPT_DIR%airsim_envs\AirSimNH\WindowsNoEditor\AirSimNH.exe
set CITY=%SCRIPT_DIR%airsim_envs\CityEnviron\WindowsNoEditor\CityEnviron.exe

echo.
echo  ============================================================
echo    AeroMind Autonomous Drone OS
echo    Launching AirSim Environment
echo  ============================================================
echo.

:: Deploy settings first
echo  Deploying AirSim settings...
python setup\setup_environment.py --skip-install >nul 2>&1
python -c "import shutil, pathlib; src=pathlib.Path('configs/airsim_settings.json'); dst=pathlib.Path.home()/'Documents'/'AirSim'/'settings.json'; dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); print('  Settings deployed ->',dst)"

echo.

:: Try environments in order of preference
if exist "%BLOCKS%" (
    echo  Starting Blocks environment...
    echo  Settings: %USERPROFILE%\Documents\AirSim\settings.json
    echo.
    echo  Wait for UE4 to load, then press any key to continue...
    start "" "%BLOCKS%" -windowed -ResX=1280 -ResY=720
    goto :started
)

if exist "%NH%" (
    echo  Starting AirSimNH environment...
    start "" "%NH%" -windowed -ResX=1280 -ResY=720
    goto :started
)

if exist "%CITY%" (
    echo  Starting CityEnviron...
    start "" "%CITY%" -windowed -ResX=1280 -ResY=720
    goto :started
)

:: No binary found
echo  [WARNING] No AirSim binary found!
echo.
echo  Download one first:
echo    python setup\download_airsim_env.py
echo.
echo  Or run in MOCK mode (no AirSim needed):
echo    launch_simulation.bat --mock
echo.
pause
exit /b 1

:started
echo.
echo  AirSim is starting. Wait 30-60 seconds for UE4 to fully load.
echo.
echo  Then run:  launch_simulation.bat
echo  Or:        launch_all.bat  (dashboard + simulation together)
echo.
timeout /t 10 /nobreak
echo  Checking AirSim connection...
python scripts\check_airsim.py
echo.
pause
