@echo off

REM Baseball Batted Ball Physics Simulator - Main Launcher
REM ======================================================

echo.
echo ===============================================================
echo     BASEBALL PHYSICS SIMULATOR (Phases 1+2+3)
echo ===============================================================
echo.
echo Welcome! Choose how you'd like to run the simulation:
echo.
echo === QUICK START ===
echo 1. Quick Scenarios     - Pre-configured batted ball scenarios
echo 2. Custom Simulation   - Enter your own parameters with guided input
echo.
echo === PHASE 2: COLLISION PHYSICS ===
echo 3. Collision Scenarios - Sweet spot, wood vs aluminum, contact quality
echo.
echo === PHASE 3: PITCH PHYSICS ===
echo 4. Pitch Scenarios     - Different pitch types (fastball, curve, slider, etc.)
echo.
echo === COMPLETE AT-BATS ===
echo 5. Complete At-Bats    - Full sequence: Pitch + Collision + Trajectory
echo.
echo === OTHER ===
echo 6. Help                - View parameter explanations and tips
echo 7. Examples            - Run the built-in examples from the codebase
echo 8. Validation Tests    - Run physics validation tests
echo.
echo 0. Exit
echo.

set /p "choice=Enter your choice (0-8): "

if "%choice%"=="1" (
    call quick_scenarios.bat
    goto :end
)

if "%choice%"=="2" (
    call run_simulation.bat
    goto :end
)

if "%choice%"=="3" (
    call collision_scenarios.bat
    goto :end
)

if "%choice%"=="4" (
    call pitch_scenarios.bat
    goto :end
)

if "%choice%"=="5" (
    call complete_atbat.bat
    goto :end
)

if "%choice%"=="6" goto :help

if "%choice%"=="7" goto :examples

if "%choice%"=="8" goto :validation

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
echo === PHASE 1: BATTED BALL TRAJECTORY ===
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
pause
cls
echo.
echo ===============================================================
echo                PARAMETER GUIDE (continued)
echo ===============================================================
echo.
echo === PHASE 2: COLLISION PHYSICS ===
echo.
echo BAT SPEED (mph):
echo   - Elite MLB hitters: 75-80 mph
echo   - Average MLB: 68-72 mph
echo   - Good amateur: 65-68 mph
echo   - Average amateur: 60-65 mph
echo.
echo PITCH SPEED (mph):
echo   - Elite fastball: 95-102 mph
echo   - Average fastball: 88-93 mph
echo   - Changeup: 78-88 mph (10 mph slower than fastball)
echo   - Curveball: 72-82 mph
echo.
echo CONTACT QUALITY:
echo   - Sweet spot: Maximum exit velocity, COR = 0.55
echo   - 1 inch off: 10%% exit velocity reduction
echo   - 2 inches off: 25%% reduction
echo   - 3+ inches off: 40%% reduction (broken bat territory)
echo.
echo CONTACT LOCATION (vertical):
echo   - Below center: Higher launch angle, more backspin
echo   - Above center: Lower launch angle (topped ball)
echo   - Perfect center: Optimal for line drives
echo.
pause
cls
echo.
echo ===============================================================
echo                PARAMETER GUIDE (continued)
echo ===============================================================
echo.
echo === PHASE 3: PITCH PHYSICS ===
echo.
echo PITCH TYPES:
echo   - 4-Seam Fastball: 88-102 mph, 2000-2700 rpm, "rises"
echo   - 2-Seam Fastball: 86-96 mph, arm-side run, sinking action
echo   - Curveball: 72-82 mph, 2200-3200 rpm, 12-6 drop
echo   - Slider: 82-90 mph, 2200-2800 rpm, sharp horizontal break
echo   - Changeup: 78-88 mph, 1500-2000 rpm, fading action
echo   - Splitter: 85-92 mph, 1000-1500 rpm, tumbling drop
echo.
echo PITCH MOVEMENT:
echo   - Fastball: 10-20 inches vertical "rise" (less drop)
echo   - Curveball: 10-25 inches vertical drop
echo   - Slider: 10-20 inches horizontal break
echo   - All pitches lose 8-10 mph from drag over 60 feet
echo.
echo STRIKE ZONE:
echo   - Width: 17 inches
echo   - Height: 1.5 ft (knees) to 3.5 ft (letters)
echo   - Pitches move 5-12 inches due to spin!
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
cls
echo.
echo ===============================================================
echo                    BUILT-IN EXAMPLES
echo ===============================================================
echo.
echo Choose an example to run:
echo.
echo 1. Basic Simulation
echo 2. Distance Analysis
echo 3. Collision Demo (Phase 2)
echo 4. Validate Model (Phase 1)
echo 5. Validate Collision (Phase 2)
echo 6. Validate Pitch (Phase 3)
echo.
echo 0. Back to main menu
echo.
set /p "ex_choice=Enter choice: "

if "%ex_choice%"=="0" goto :start
if "%ex_choice%"=="1" (
    python examples\basic_simulation.py
    pause
    goto :examples
)
if "%ex_choice%"=="2" (
    python examples\distance_analysis.py
    pause
    goto :examples
)
if "%ex_choice%"=="3" (
    python examples\collision_demo.py
    pause
    goto :examples
)
if "%ex_choice%"=="4" (
    python examples\validate_model.py
    pause
    goto :examples
)
if "%ex_choice%"=="5" (
    python examples\validate_collision.py
    pause
    goto :examples
)
if "%ex_choice%"=="6" (
    python examples\validate_pitch.py
    pause
    goto :examples
)
echo Invalid choice.
pause
goto :examples

:validation
cls
echo.
echo ===============================================================
echo                    VALIDATION TESTS
echo ===============================================================
echo.
echo Running all physics validation tests...
echo.
echo.
echo === PHASE 1: Trajectory Physics ===
python examples\validate_model.py
echo.
echo.
echo === PHASE 2: Collision Physics ===
python examples\validate_collision.py
echo.
echo.
echo === PHASE 3: Pitch Physics ===
python examples\validate_pitch.py
echo.
echo.
echo ===============================================================
echo                    ALL VALIDATIONS COMPLETE
echo ===============================================================
echo.
pause
goto :start

:start
call launcher.bat

:end
echo.
echo Thank you for using the Baseball Physics Simulator!
echo.