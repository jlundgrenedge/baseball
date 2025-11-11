@echo off
echo ========================================
echo Baseball Game Simulation
echo ========================================
echo.
echo Choose simulation type:
echo   1. Single Game Demo (quick, interactive)
echo   2. Quick League Season (Thu/Sun league, 14 games each)
echo   3. Full League Season (8 teams, 60 games each)
echo   4. Performance Test Suite
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto single_game
if "%choice%"=="2" goto quick_league
if "%choice%"=="3" goto full_league
if "%choice%"=="4" goto performance
goto invalid

:single_game
echo.
echo ========================================
echo Running Single Game Simulation
echo ========================================
echo.
echo This runs a complete baseball game simulation that integrates
echo all the physics components for realistic gameplay:
echo.
echo - Pitch-by-pitch simulation with realistic physics
echo - Bat-ball collision mechanics with exit velocity/launch angle
echo - Fielding physics with reaction time, speed, and range
echo - Baserunning mechanics with acceleration and timing
echo - Complete play outcomes based on timing comparisons
echo.
pause
echo.
python examples\game_simulation_demo.py
goto end

:quick_league
echo.
echo ========================================
echo Running Quick League Simulation
echo ========================================
echo.
echo This simulates a quick 8-team league season:
echo - Thursday/Sunday league format
echo - 8 teams with varying skill levels
echo - 14 games per team (2 complete rounds)
echo - 4 games per day simulated in parallel
echo - Optimized for quick testing (2-5 minutes)
echo.
pause
echo.
python tests\test_league_simulation_quick.py
goto end

:full_league
echo.
echo ========================================
echo Running Full League Simulation
echo ========================================
echo.
echo This simulates a complete 8-team league season:
echo - 8 teams with varying skill levels
echo - 60 games per team (240 total games)
echo - Complete season statistics
echo - Realistic baseball season (~10-20 minutes)
echo.
pause
echo.
python tests\test_league_simulation.py
goto end

:performance
echo.
echo ========================================
echo PERFORMANCE TEST SUITE
echo ========================================
echo.
echo High-performance simulation capabilities:
echo - Numba JIT compilation (5-10x faster)
echo - Multi-core parallelism (5-8x faster on multi-core systems)
echo - GPU acceleration (10-100x for large batches)
echo - Batch processing for thousands of simulations
echo.
pause
echo.
python -m batted_ball.performance_test_suite
goto end

:invalid
echo Invalid choice. Please run the script again and select 1-4.
pause
exit /b

:end

echo.
echo ========================================
echo Game Simulation Complete!
echo ========================================
echo.
echo The baseball physics simulator can now simulate complete games
echo with realistic outcomes based on player attributes and physics.
echo.
echo Key features demonstrated:
echo - Full game flow from first pitch to final out
echo - Play-by-play action with physics details
echo - Realistic hit distributions and distances
echo - Fielding success based on hang time vs range
echo - Baserunning advancement based on timing
echo - Team quality differences affecting outcomes
echo.
echo You can modify team attributes in the code to test different
echo scenarios or use this as a foundation for more complex
echo baseball simulations and analysis.
echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo.
echo For high-performance simulations, run:
echo   performance_test_suite.bat
echo.
echo For documentation, see:
echo   docs\PERFORMANCE_GUIDE.md
echo.
pause
