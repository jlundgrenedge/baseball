@echo off

REM Baseball Batted Ball Physics Simulator - Main Launcher
REM ======================================================

echo.
echo ===============================================================
echo     BASEBALL BATTED BALL PHYSICS SIMULATOR
echo ===============================================================
echo.
echo Welcome! Choose how you'd like to run the simulation:
echo.
echo 1. Quick Scenarios  - Pre-configured scenarios (home runs, weather effects, etc.)
echo 2. Custom Simulation - Enter your own parameters with guided input
echo 3. Help             - View parameter explanations and tips
echo 4. Examples         - Run the built-in examples from the codebase
echo.
echo 0. Exit
echo.

set /p "choice=Enter your choice (0-4): "

if "%choice%"=="1" (
    call quick_scenarios.bat
    goto :end
)

if "%choice%"=="2" (
    call run_simulation.bat
    goto :end
)

if "%choice%"=="3" goto :help

if "%choice%"=="4" goto :examples

if "%choice%"=="0" goto :end

echo Invalid choice. Please try again.
pause
cls
goto :start

:help
cls
echo.
echo ===============================================================
echo                    PARAMETER GUIDE
echo ===============================================================
echo.
echo EXIT VELOCITY (mph):
echo   - Elite hitters: 105-115 mph
echo   - Good contact: 95-105 mph  
echo   - Average contact: 85-95 mph
echo   - Weak contact: 70-85 mph
echo.
echo LAUNCH ANGLE (degrees):
echo   - Optimal for home runs: 25-30°
echo   - Line drives: 10-20°
echo   - Ground balls: 0-10°
echo   - Pop-ups: 45°+
echo.
echo SPRAY ANGLE (degrees):
echo   - Center field: 0°
echo   - Pull side: +15° to +45°
echo   - Opposite field: -15° to -45°
echo.
echo BACKSPIN (rpm):
echo   - Optimal: 1800-2200 rpm
echo   - Low spin: 800-1200 rpm
echo   - High spin: 2200+ rpm
echo.
echo ENVIRONMENTAL FACTORS:
echo   - Altitude: Every 1000 ft adds ~6 feet of carry
echo   - Temperature: Every 10°F adds ~3-4 feet
echo   - Wind: Tailwind adds ~4 ft per mph
echo   - Humidity: Higher humidity = less carry
echo.
echo FAMOUS BALLPARKS:
echo   - Coors Field: 5200 ft altitude
echo   - Fenway Park: 20 ft altitude, Green Monster in left
echo   - Yankee Stadium: 55 ft altitude, short right field
echo.
pause
cls
goto :start

:examples
echo.
echo Running built-in examples...
echo.
python examples\basic_simulation.py
echo.
pause
cls
goto :start

:start
call launcher.bat

:end
echo.
echo Thank you for using the Baseball Batted Ball Physics Simulator!
echo.