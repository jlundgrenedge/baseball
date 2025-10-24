@echo off
setlocal EnableDelayedExpansion

REM Baseball Batted Ball Physics Simulator - Quick Scenarios
REM ========================================================

echo.
echo ===============================================================
echo     BASEBALL SIMULATOR - QUICK SCENARIOS
echo ===============================================================
echo.
echo Choose a preset scenario to simulate:
echo.
echo 1.  Perfect Home Run (100 mph, 28°, optimal conditions)
echo 2.  Line Drive Single (95 mph, 12°, center field)
echo 3.  Pop-up (85 mph, 55°, too much launch angle)
echo 4.  Coors Field Blast (100 mph, 28°, high altitude)
echo 5.  Cold Weather Game (100 mph, 28°, 40°F)
echo 6.  Hot Summer Day (100 mph, 28°, 90°F)
echo 7.  Strong Tailwind (100 mph, 28°, 15 mph wind)
echo 8.  Strong Headwind (100 mph, 28°, -15 mph wind)
echo 9.  Weak Contact (75 mph, 25°, poor exit velocity)
echo 10. Power Hitter Special (110 mph, 28°, elite contact)
echo 11. Fenway Green Monster Test (100 mph, 28°, left field)
echo 12. Yankee Stadium Short Porch (95 mph, 32°, right field)
echo 13. Dead Ball Era (85 mph, 15°, low spin)
echo 14. Modern Launch Angle Revolution (105 mph, 25°, high spin)
echo 15. Pitcher's Park (100 mph, 28°, humid, sea level)
echo.
echo 0.  Custom simulation (opens full interactive mode)
echo.

set /p "scenario=Enter scenario number (0-15): "

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    pause
    exit /b 1
)

if "%scenario%"=="0" (
    call run_simulation.bat
    goto :end
)

REM Set parameters based on scenario
if "%scenario%"=="1" (
    set "title=Perfect Home Run"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="2" (
    set "title=Line Drive Single"
    set "exit_velocity=95.0"
    set "launch_angle=12.0"
    set "spray_angle=15.0"
    set "backspin_rpm=1200.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="3" (
    set "title=Pop-up"
    set "exit_velocity=85.0"
    set "launch_angle=55.0"
    set "spray_angle=0.0"
    set "backspin_rpm=2200.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="4" (
    set "title=Coors Field Blast"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=0.0"
    set "altitude=5200.0"
    set "temperature=75.0"
    set "humidity=0.3"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="5" (
    set "title=Cold Weather Game"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=40.0"
    set "humidity=0.6"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="6" (
    set "title=Hot Summer Day"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=90.0"
    set "humidity=0.7"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="7" (
    set "title=Strong Tailwind"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=15.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="8" (
    set "title=Strong Headwind"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=-15.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="9" (
    set "title=Weak Contact"
    set "exit_velocity=75.0"
    set "launch_angle=25.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1500.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="10" (
    set "title=Power Hitter Special"
    set "exit_velocity=110.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1900.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="11" (
    set "title=Fenway Green Monster Test"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=-15.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=200.0"
    set "altitude=20.0"
    set "temperature=75.0"
    set "humidity=0.6"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="12" (
    set "title=Yankee Stadium Short Porch"
    set "exit_velocity=95.0"
    set "launch_angle=32.0"
    set "spray_angle=25.0"
    set "backspin_rpm=1900.0"
    set "sidespin_rpm=-300.0"
    set "altitude=55.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="13" (
    set "title=Dead Ball Era"
    set "exit_velocity=85.0"
    set "launch_angle=15.0"
    set "spray_angle=0.0"
    set "backspin_rpm=800.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="14" (
    set "title=Modern Launch Angle Revolution"
    set "exit_velocity=105.0"
    set "launch_angle=25.0"
    set "spray_angle=0.0"
    set "backspin_rpm=2400.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=75.0"
    set "humidity=0.5"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

if "%scenario%"=="15" (
    set "title=Pitcher's Park"
    set "exit_velocity=100.0"
    set "launch_angle=28.0"
    set "spray_angle=0.0"
    set "backspin_rpm=1800.0"
    set "sidespin_rpm=0.0"
    set "altitude=0.0"
    set "temperature=70.0"
    set "humidity=0.8"
    set "wind_speed=0.0"
    set "wind_direction=0.0"
    goto :run_scenario
)

echo Invalid scenario number. Please try again.
pause
goto :end

:run_scenario
echo.
echo ===============================================================
echo                    SCENARIO: %title%
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
echo.

REM Create temporary Python script
echo import sys > temp_scenario.py
echo sys.path.insert(0, '.') >> temp_scenario.py
echo from batted_ball import BattedBallSimulator >> temp_scenario.py
echo. >> temp_scenario.py
echo # Create simulator >> temp_scenario.py
echo sim = BattedBallSimulator() >> temp_scenario.py
echo. >> temp_scenario.py
echo # Run simulation >> temp_scenario.py
echo result = sim.simulate( >> temp_scenario.py
echo     exit_velocity=%exit_velocity%, >> temp_scenario.py
echo     launch_angle=%launch_angle%, >> temp_scenario.py
echo     spray_angle=%spray_angle%, >> temp_scenario.py
echo     backspin_rpm=%backspin_rpm%, >> temp_scenario.py
echo     sidespin_rpm=%sidespin_rpm%, >> temp_scenario.py
echo     altitude=%altitude%, >> temp_scenario.py
echo     temperature=%temperature%, >> temp_scenario.py
echo     humidity=%humidity%, >> temp_scenario.py
echo     wind_speed=%wind_speed%, >> temp_scenario.py
echo     wind_direction=%wind_direction% >> temp_scenario.py
echo ) >> temp_scenario.py
echo. >> temp_scenario.py
echo # Display results >> temp_scenario.py
echo print("="*70) >> temp_scenario.py
echo print("                    SIMULATION RESULTS") >> temp_scenario.py
echo print("="*70) >> temp_scenario.py
echo print() >> temp_scenario.py
echo print(f"Distance: {result.distance:.1f} feet") >> temp_scenario.py
echo print(f"Flight time: {result.flight_time:.2f} seconds") >> temp_scenario.py
echo print(f"Peak height: {result.peak_height:.1f} feet") >> temp_scenario.py
echo print(f"Time to peak: {result.time_to_peak:.2f} seconds") >> temp_scenario.py
echo print(f"Final velocity: {result.final_velocity:.1f} mph") >> temp_scenario.py
echo print(f"Landing position: ({result.landing_x:.1f}, {result.landing_y:.1f}) feet") >> temp_scenario.py
echo print(f"Spray angle at landing: {result.spray_angle_landing:.1f} degrees") >> temp_scenario.py
echo print() >> temp_scenario.py
echo. >> temp_scenario.py
echo # Interpretation >> temp_scenario.py
echo print("="*70) >> temp_scenario.py
echo print("                    INTERPRETATION") >> temp_scenario.py
echo print("="*70) >> temp_scenario.py
echo distance = result.distance >> temp_scenario.py
echo if distance ^>= 400: >> temp_scenario.py
echo     print("Result: MONSTER HOME RUN! 🚀") >> temp_scenario.py
echo elif distance ^>= 350: >> temp_scenario.py
echo     print("Result: HOME RUN! ⚾") >> temp_scenario.py
echo elif distance ^>= 320: >> temp_scenario.py
echo     print("Result: Warning track power - might be out in some parks") >> temp_scenario.py
echo elif distance ^>= 250: >> temp_scenario.py
echo     print("Result: Deep fly ball - likely an out") >> temp_scenario.py
echo elif distance ^>= 150: >> temp_scenario.py
echo     print("Result: Base hit potential") >> temp_scenario.py
echo else: >> temp_scenario.py
echo     print("Result: Infield fly or weak contact") >> temp_scenario.py
echo print("="*70) >> temp_scenario.py

echo Running simulation...
echo.
python temp_scenario.py

REM Clean up
del temp_scenario.py

echo.
echo ===============================================================
echo.
set /p "run_another=Try another scenario? (Y/n): "
if /i not "%run_another%"=="n" (
    cls
    goto :start
)

:start
call quick_scenarios.bat

:end
echo.
echo Thank you for using the Baseball Simulator!
pause