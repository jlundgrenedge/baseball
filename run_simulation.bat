@echo off
setlocal EnableDelayedExpansion

REM Baseball Batted Ball Physics Simulator - Interactive Runner
REM ============================================================

echo.
echo ===============================================================
echo     BASEBALL BATTED BALL PHYSICS SIMULATOR
echo ===============================================================
echo.
echo This tool will guide you through setting up a batted ball
echo simulation with custom parameters.
echo.

REM Set default values
set "exit_velocity=100.0"
set "launch_angle=28.0"
set "spray_angle=0.0"
set "backspin_rpm=1800.0"
set "sidespin_rpm=0.0"
set "altitude=0.0"
set "temperature=70.0"
set "humidity=0.5"
set "wind_speed=0.0"
set "wind_direction=0.0"
set "initial_height=3.0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python and try again.
    pause
    exit /b 1
)

echo Choose your input method:
echo 1. Use default values for quick simulation
echo 2. Enter custom values (guided input)
echo 3. Advanced mode (all parameters)
echo.
set /p "input_mode=Enter choice (1-3): "

if "%input_mode%"=="1" goto :run_simulation
if "%input_mode%"=="2" goto :guided_input
if "%input_mode%"=="3" goto :advanced_input

echo Invalid choice. Using guided input mode.

:guided_input
echo.
echo ===============================================================
echo                    GUIDED INPUT MODE
echo ===============================================================
echo.

echo --- BALL EXIT CONDITIONS ---
echo.
set /p "temp_exit_velocity=Exit velocity (mph) [default: %exit_velocity%]: "
if not "%temp_exit_velocity%"=="" set "exit_velocity=%temp_exit_velocity%"

set /p "temp_launch_angle=Launch angle (degrees, 0-90) [default: %launch_angle%]: "
if not "%temp_launch_angle%"=="" set "launch_angle=%temp_launch_angle%"

set /p "temp_spray_angle=Spray angle (degrees, + = pull, - = opposite field) [default: %spray_angle%]: "
if not "%temp_spray_angle%"=="" set "spray_angle=%temp_spray_angle%"

echo.
echo --- SPIN CONDITIONS ---
echo.
set /p "temp_backspin=Backspin (rpm, typical: 1500-2500) [default: %backspin_rpm%]: "
if not "%temp_backspin%"=="" set "backspin_rpm=%temp_backspin%"

set /p "temp_sidespin=Sidespin (rpm, + = toward pull side) [default: %sidespin_rpm%]: "
if not "%temp_sidespin%"=="" set "sidespin_rpm=%temp_sidespin%"

echo.
echo --- ENVIRONMENTAL CONDITIONS ---
echo.
set /p "temp_altitude=Altitude (feet above sea level) [default: %altitude%]: "
if not "%temp_altitude%"=="" set "altitude=%temp_altitude%"

set /p "temp_temperature=Temperature (Fahrenheit) [default: %temperature%]: "
if not "%temp_temperature%"=="" set "temperature=%temp_temperature%"

echo.
echo --- WIND CONDITIONS ---
echo.
set /p "temp_wind_speed=Wind speed (mph, + = tailwind) [default: %wind_speed%]: "
if not "%temp_wind_speed%"=="" set "wind_speed=%temp_wind_speed%"

set /p "temp_wind_direction=Wind direction (degrees, 0 = straight out) [default: %wind_direction%]: "
if not "%temp_wind_direction%"=="" set "wind_direction=%temp_wind_direction%"

goto :run_simulation

:advanced_input
echo.
echo ===============================================================
echo                    ADVANCED INPUT MODE
echo ===============================================================
echo.

echo All parameters (press Enter to use default values):
echo.

set /p "temp_exit_velocity=Exit velocity (mph) [%exit_velocity%]: "
if not "%temp_exit_velocity%"=="" set "exit_velocity=%temp_exit_velocity%"

set /p "temp_launch_angle=Launch angle (degrees) [%launch_angle%]: "
if not "%temp_launch_angle%"=="" set "launch_angle=%temp_launch_angle%"

set /p "temp_spray_angle=Spray angle (degrees) [%spray_angle%]: "
if not "%temp_spray_angle%"=="" set "spray_angle=%temp_spray_angle%"

set /p "temp_backspin=Backspin (rpm) [%backspin_rpm%]: "
if not "%temp_backspin%"=="" set "backspin_rpm=%temp_backspin%"

set /p "temp_sidespin=Sidespin (rpm) [%sidespin_rpm%]: "
if not "%temp_sidespin%"=="" set "sidespin_rpm=%temp_sidespin%"

set /p "temp_altitude=Altitude (feet) [%altitude%]: "
if not "%temp_altitude%"=="" set "altitude=%temp_altitude%"

set /p "temp_temperature=Temperature (F) [%temperature%]: "
if not "%temp_temperature%"=="" set "temperature=%temp_temperature%"

set /p "temp_humidity=Humidity (0.0-1.0) [%humidity%]: "
if not "%temp_humidity%"=="" set "humidity=%temp_humidity%"

set /p "temp_wind_speed=Wind speed (mph) [%wind_speed%]: "
if not "%temp_wind_speed%"=="" set "wind_speed=%temp_wind_speed%"

set /p "temp_wind_direction=Wind direction (degrees) [%wind_direction%]: "
if not "%temp_wind_direction%"=="" set "wind_direction=%temp_wind_direction%"

set /p "temp_initial_height=Initial height (feet) [%initial_height%]: "
if not "%temp_initial_height%"=="" set "initial_height=%temp_initial_height%"

:run_simulation
echo.
echo ===============================================================
echo                    SIMULATION PARAMETERS
echo ===============================================================
echo.
echo Exit velocity:     %exit_velocity% mph
echo Launch angle:      %launch_angle% degrees
echo Spray angle:       %spray_angle% degrees
echo Backspin:          %backspin_rpm% rpm
echo Sidespin:          %sidespin_rpm% rpm
echo Altitude:          %altitude% feet
echo Temperature:       %temperature% F
echo Humidity:          %humidity%
echo Wind speed:        %wind_speed% mph
echo Wind direction:    %wind_direction% degrees
echo Initial height:    %initial_height% feet
echo.

set /p "confirm=Run simulation with these parameters? (Y/n): "
if /i "%confirm%"=="n" goto :end

echo.
echo ===============================================================
echo                    RUNNING SIMULATION
echo ===============================================================
echo.

REM Create temporary Python script
echo import sys > temp_simulation.py
echo sys.path.insert(0, '.') >> temp_simulation.py
echo from batted_ball import BattedBallSimulator >> temp_simulation.py
echo. >> temp_simulation.py
echo # Create simulator >> temp_simulation.py
echo sim = BattedBallSimulator() >> temp_simulation.py
echo. >> temp_simulation.py
echo # Run simulation with user parameters >> temp_simulation.py
echo result = sim.simulate( >> temp_simulation.py
echo     exit_velocity=%exit_velocity%, >> temp_simulation.py
echo     launch_angle=%launch_angle%, >> temp_simulation.py
echo     spray_angle=%spray_angle%, >> temp_simulation.py
echo     backspin_rpm=%backspin_rpm%, >> temp_simulation.py
echo     sidespin_rpm=%sidespin_rpm%, >> temp_simulation.py
echo     altitude=%altitude%, >> temp_simulation.py
echo     temperature=%temperature%, >> temp_simulation.py
echo     humidity=%humidity%, >> temp_simulation.py
echo     wind_speed=%wind_speed%, >> temp_simulation.py
echo     wind_direction=%wind_direction%, >> temp_simulation.py
echo     initial_height=%initial_height% >> temp_simulation.py
echo ) >> temp_simulation.py
echo. >> temp_simulation.py
echo # Display results >> temp_simulation.py
echo print("="*70) >> temp_simulation.py
echo print("                    SIMULATION RESULTS") >> temp_simulation.py
echo print("="*70) >> temp_simulation.py
echo print() >> temp_simulation.py
echo print(f"Distance: {result.distance:.1f} feet") >> temp_simulation.py
echo print(f"Flight time: {result.flight_time:.2f} seconds") >> temp_simulation.py
echo print(f"Peak height: {result.peak_height:.1f} feet") >> temp_simulation.py
echo print(f"Time to peak: {result.time_to_peak:.2f} seconds") >> temp_simulation.py
echo print(f"Final velocity: {result.final_velocity:.1f} mph") >> temp_simulation.py
echo print(f"Landing position: ({result.landing_x:.1f}, {result.landing_y:.1f}) feet") >> temp_simulation.py
echo print(f"Spray angle at landing: {result.spray_angle_landing:.1f} degrees") >> temp_simulation.py
echo print() >> temp_simulation.py
echo. >> temp_simulation.py
echo # Interpretation >> temp_simulation.py
echo print("="*70) >> temp_simulation.py
echo print("                    INTERPRETATION") >> temp_simulation.py
echo print("="*70) >> temp_simulation.py
echo distance = result.distance >> temp_simulation.py
echo if distance ^>= 400: >> temp_simulation.py
echo     print("Result: MONSTER HOME RUN! 🚀") >> temp_simulation.py
echo elif distance ^>= 350: >> temp_simulation.py
echo     print("Result: HOME RUN! ⚾") >> temp_simulation.py
echo elif distance ^>= 320: >> temp_simulation.py
echo     print("Result: Warning track power - might be out in some parks") >> temp_simulation.py
echo elif distance ^>= 250: >> temp_simulation.py
echo     print("Result: Deep fly ball - likely an out") >> temp_simulation.py
echo elif distance ^>= 150: >> temp_simulation.py
echo     print("Result: Base hit potential") >> temp_simulation.py
echo else: >> temp_simulation.py
echo     print("Result: Infield fly or weak contact") >> temp_simulation.py
echo. >> temp_simulation.py
echo peak = result.peak_height >> temp_simulation.py
echo if peak ^> 150: >> temp_simulation.py
echo     print(f"Trajectory: Very high arc ({peak:.0f} ft peak)") >> temp_simulation.py
echo elif peak ^> 100: >> temp_simulation.py
echo     print(f"Trajectory: High arc ({peak:.0f} ft peak)") >> temp_simulation.py
echo elif peak ^> 50: >> temp_simulation.py
echo     print(f"Trajectory: Medium arc ({peak:.0f} ft peak)") >> temp_simulation.py
echo else: >> temp_simulation.py
echo     print(f"Trajectory: Line drive ({peak:.0f} ft peak)") >> temp_simulation.py
echo. >> temp_simulation.py
echo print("="*70) >> temp_simulation.py

REM Run the simulation
python temp_simulation.py

REM Clean up
del temp_simulation.py

echo.
echo ===============================================================
echo.
set /p "run_again=Run another simulation? (Y/n): "
if /i not "%run_again%"=="n" goto :guided_input

:end
echo.
echo Thank you for using the Baseball Batted Ball Physics Simulator!
echo.
pause