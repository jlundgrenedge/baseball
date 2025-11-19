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
echo   5. MLB Teams: Yankees vs Dodgers (Real rosters)
echo   6. MLB Players: Individual Demo (Ohtani vs Judge)
echo   7. MLB Quick Demo (Players only)
echo   8. Database Teams: Select teams and simulate (Interactive)
echo.
set /p choice="Enter your choice (1-8): "

if "%choice%"=="1" goto single_game
if "%choice%"=="2" goto quick_league
if "%choice%"=="3" goto full_league
if "%choice%"=="4" goto performance
if "%choice%"=="5" goto mlb_yankees_dodgers
if "%choice%"=="6" goto mlb_player_demo
if "%choice%"=="7" goto mlb_quick_demo
if "%choice%"=="8" goto db_teams
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

:mlb_yankees_dodgers
echo.
echo ========================================
echo MLB: Yankees vs Dodgers Simulation
echo ========================================
echo.
echo This will simulate a complete 9-inning game between:
echo   - New York Yankees (Away)
echo   - Los Angeles Dodgers (Home)
echo.
echo Using REAL 2024 MLB player statistics:
echo - Fetches player data from Baseball Savant/FanGraphs
echo - Creates teams with actual roster attributes
echo - Physics-based simulation with play-by-play
echo.
echo Requirements:
echo   pip install pybaseball pandas
echo.
echo NOTE: First run may be slow due to data fetching.
echo.
pause
echo.
python examples\simulate_mlb_teams.py
goto end

:mlb_player_demo
echo.
echo ========================================
echo MLB: Individual Player Demo
echo ========================================
echo.
echo Simulating at-bats with real MLB players:
echo   Pitcher: Shohei Ohtani (2024 stats)
echo   Hitter:  Aaron Judge (2024 stats)
echo.
echo Will simulate 10 at-bats with physics-based outcomes.
echo.
echo Requirements:
echo   pip install pybaseball pandas
echo.
pause
echo.
python -c "import sys; sys.path.insert(0, '.'); from examples.simulate_mlb_teams import simulate_single_player_at_bats; simulate_single_player_at_bats()"
goto end

:mlb_quick_demo
echo.
echo ========================================
echo MLB: Quick Demo Mode
echo ========================================
echo.
echo Running quick demonstration with individual players only.
echo Skips full game simulation for faster testing.
echo.
echo Requirements:
echo   pip install pybaseball pandas
echo.
pause
echo.
python examples\simulate_mlb_teams.py --quick
goto end

:db_teams
echo.
echo ========================================
echo Database Team Selection
echo ========================================
echo.
echo Select teams from the database and simulate games:
echo   - Choose any two teams stored in baseball_teams.db
echo   - Select how many games to simulate (1-500)
echo   - View detailed results and statistics
echo.
echo To add teams to the database, run option 5 first.
echo.
echo Requirements:
echo   - baseball_teams.db must exist
echo   - Teams must be added via option 5 or manually
echo.
pause
echo.
python examples\simulate_db_teams.py
goto end

:invalid
echo Invalid choice. Please run the script again and select 1-8.
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
echo - REAL MLB player integration (options 5-7)
echo - Database team selection and simulation (option 8)
echo.
echo You can modify team attributes in the code to test different
echo scenarios or use this as a foundation for more complex
echo baseball simulations and analysis.
echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo.
echo For MLB team simulations:
echo   - Options 5-7 use real MLB player data
echo   - Requires: pip install pybaseball pandas
echo   - Edit examples\simulate_mlb_teams.py for custom matchups
echo.
echo For high-performance simulations, run:
echo   performance_test_suite.bat
echo.
echo For documentation, see:
echo   docs\PERFORMANCE_GUIDE.md
echo   docs\PYBASEBALL_INTEGRATION.md
echo.
pause
