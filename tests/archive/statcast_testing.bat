@echo off
REM ============================================================================
REM Statcast Testing Batch File
REM Baseball Physics Simulation Engine - Statcast Calibration Tools
REM ============================================================================

:MENU
cls
echo.
echo ============================================================================
echo                    STATCAST TESTING SUITE
echo              Baseball Physics Simulation Engine
echo ============================================================================
echo.
echo   This batch file runs Statcast calibration tests with angle-dependent spin
echo   to improve accuracy, especially for line drives.
echo.
echo ============================================================================
echo.
echo   MENU OPTIONS:
echo.
echo   1. Check Spin Data Availability
echo      - Fetches Statcast data and checks for spin-related columns
echo      - Shows how much spin data is available
echo      - Displays correlation between launch angle and spin
echo.
echo   2. Run Calibration with Angle-Dependent Spin
echo      - Simulates trajectories using launch-angle-dependent spin estimates
echo      - Compares against real Statcast data
echo      - Generates detailed calibration report
echo.
echo   3. Run Full Test Suite (Both Steps)
echo      - Runs spin data check first
echo      - Then runs full calibration
echo      - Saves results to CSV
echo.
echo   4. Exit
echo.
echo ============================================================================
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto CHECK_SPIN
if "%choice%"=="2" goto RUN_CALIBRATION
if "%choice%"=="3" goto RUN_FULL_SUITE
if "%choice%"=="4" goto EXIT

echo.
echo Invalid choice! Please enter 1-4.
pause
goto MENU

:CHECK_SPIN
cls
echo.
echo ============================================================================
echo                    CHECKING SPIN DATA AVAILABILITY
echo ============================================================================
echo.
echo Running check_spin_data.py...
echo This will fetch Statcast data for June 2024 and check spin availability.
echo.
echo NOTE: First run may take 30-60 seconds to fetch data from MLB servers.
echo.
echo ============================================================================
echo.

python check_spin_data.py

echo.
echo ============================================================================
echo                    SPIN DATA CHECK COMPLETE
echo ============================================================================
echo.
pause
goto MENU

:RUN_CALIBRATION
cls
echo.
echo ============================================================================
echo              RUNNING CALIBRATION WITH ANGLE-DEPENDENT SPIN
echo ============================================================================
echo.
echo Running calibrate_with_spin.py...
echo This will:
echo   1. Fetch Statcast data for June 2024
echo   2. Bin data by exit velocity and launch angle
echo   3. Estimate backspin based on launch angle:
echo      - Line drives (^<20°): 600-1200 rpm
echo      - Fly balls (25-35°): 1200-1950 rpm
echo      - Pop-ups (^>35°): 1950-2700 rpm
echo   4. Run physics simulations with estimated spin
echo   5. Compare against real MLB data
echo.
echo Expected improvement:
echo   - Line drive errors should drop from +60-98 ft to +10-25 ft
echo   - Overall mean error should improve from 9.44%% to ~3-5%%
echo.
echo NOTE: This may take 2-3 minutes to complete all simulations.
echo.
echo ============================================================================
echo.

python calibrate_with_spin.py

echo.
echo ============================================================================
echo                    CALIBRATION COMPLETE
echo ============================================================================
echo.
echo Results saved to: calibration_with_angle_dependent_spin.csv
echo.
pause
goto MENU

:RUN_FULL_SUITE
cls
echo.
echo ============================================================================
echo                    RUNNING FULL TEST SUITE
echo ============================================================================
echo.
echo This will run both tests in sequence:
echo   1. Check spin data availability
echo   2. Run calibration with angle-dependent spin
echo.
echo ============================================================================
echo.
echo STEP 1: CHECKING SPIN DATA
echo ============================================================================
echo.

python check_spin_data.py

echo.
echo ============================================================================
echo STEP 2: RUNNING CALIBRATION
echo ============================================================================
echo.

python calibrate_with_spin.py

echo.
echo ============================================================================
echo                    FULL TEST SUITE COMPLETE
echo ============================================================================
echo.
echo All tests completed successfully!
echo Results saved to: calibration_with_angle_dependent_spin.csv
echo.
pause
goto MENU

:EXIT
cls
echo.
echo ============================================================================
echo                    EXITING STATCAST TESTING SUITE
echo ============================================================================
echo.
echo Thank you for using the Statcast Testing Suite!
echo.
echo For more information, see:
echo   - DATABASE_README.md
echo   - docs/STATCAST_CALIBRATION_FINDINGS.md
echo   - docs/REYNOLDS_NUMBER_ENHANCEMENT.md
echo.
echo ============================================================================
echo.
exit /b 0
