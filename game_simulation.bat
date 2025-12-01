@echo off
echo ========================================
echo Baseball Game Simulation
echo ========================================
echo.
echo Choose simulation type:
echo.
echo   ** RECOMMENDED FOR TESTING **
echo   8. MLB Database Teams (Real rosters, pick teams)
echo   R. Random Teams (Random matchups each game - best for neutral testing)
echo   P. Parallel Random (4-8x faster using multiple CPU cores)
echo   U. Ultra-Fast Random (5x speed, summary stats only)
echo   S. 2025 Season Simulation (Real schedule, day-by-day)
echo.
echo   Other options:
echo   1. Single Game Demo (synthetic teams)
echo   5. Add MLB Teams to Database (Yankees vs Dodgers)
echo   9. Quick MLB Test (5 games, command-line)
echo   0. Physics Validation (7 benchmark tests)
echo.
echo   Legacy/Archive:
echo   2. Quick League Season [ARCHIVED - uses fake teams]
echo   3. Full League Season [ARCHIVED - uses fake teams]
echo   4. Performance Test Suite
echo   6. MLB Players: Individual Demo
echo   7. MLB Quick Demo (Players only)
echo.
set /p choice="Enter your choice (0-9, R, P, S, or U): "

if "%choice%"=="0" goto validation
if "%choice%"=="1" goto single_game
if "%choice%"=="2" goto quick_league
if "%choice%"=="3" goto full_league
if "%choice%"=="4" goto performance
if "%choice%"=="5" goto mlb_yankees_dodgers
if "%choice%"=="6" goto mlb_player_demo
if "%choice%"=="7" goto mlb_quick_demo
if "%choice%"=="8" goto db_teams
if "%choice%"=="9" goto quick_mlb
if "%choice%"=="r" goto random_teams
if "%choice%"=="R" goto random_teams
if "%choice%"=="p" goto parallel_random
if "%choice%"=="P" goto parallel_random
if "%choice%"=="s" goto season_sim
if "%choice%"=="S" goto season_sim
if "%choice%"=="u" goto ultrafast_random
if "%choice%"=="U" goto ultrafast_random
goto invalid

:validation
echo.
echo ========================================
echo Physics Validation (7 Tests)
echo ========================================
echo.
echo This runs the physics validation suite.
echo All 7 tests must pass before committing physics changes.
echo.
python -m batted_ball.validation
pause
goto end

:quick_mlb
echo.
echo ========================================
echo Quick MLB Test (5 games)
echo ========================================
echo.
python examples\quick_mlb_test.py 5
pause
goto end

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
echo [ARCHIVED] Quick League Simulation
echo ========================================
echo.
echo NOTE: This test uses synthetic teams and has been archived.
echo For testing, use Option 8 (MLB Database Teams) instead.
echo.
echo Files moved to: tests\archive\
echo.
pause
goto end

:full_league
echo.
echo ========================================
echo [ARCHIVED] Full League Simulation
echo ========================================
echo.
echo NOTE: This test uses synthetic teams and has been archived.
echo For testing, use Option 8 (MLB Database Teams) instead.
echo.
echo Files moved to: tests\archive\
echo.
pause
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

:random_teams
echo.
echo ========================================
echo Randomized Team Simulation
echo ========================================
echo.
echo Each game randomly selects:
echo   - Random away team from all 30 MLB teams
echo   - Random home team (different from away)
echo   - Random starting pitcher from each rotation
echo   - Home team's ballpark with wind effects
echo.
echo This provides unbiased testing across the full range
echo of player attributes in the database.
echo.
echo Output is saved to game_logs/ just like option 8.
echo.
pause
echo.
python examples\simulate_random_teams.py
goto end

:parallel_random
echo.
echo ========================================
echo Parallel Random Simulation (FAST!)
echo ========================================
echo.
echo Uses multiple CPU cores to simulate games in parallel.
echo Typically 4-8x faster than sequential simulation!
echo.
echo Features:
echo   - Random team matchups (same as option R)
echo   - Parallel processing across CPU cores
echo   - ULTRA_FAST physics mode
echo   - Summary statistics with MLB benchmarks
echo   - Supports up to 1000 games
echo.
echo Use for:
echo   - High-volume statistical validation
echo   - Quick regression testing after changes
echo   - Performance benchmarking
echo.
pause
echo.
python examples\simulate_random_parallel.py
goto end

:ultrafast_random
echo.
echo ========================================
echo Ultra-Fast Random Simulation
echo ========================================
echo.
echo Uses ULTRA_FAST physics mode (5x faster trajectories)
echo for high-volume simulation testing.
echo.
echo Features:
echo   - Random team matchups (same as option R)
echo   - 5x faster trajectory calculations
echo   - Summary statistics only (no play-by-play)
echo   - Supports up to 1000 games
echo.
echo Use for:
echo   - Statistical validation with large samples
echo   - Quick regression testing
echo   - Performance testing
echo.
pause
echo.
python examples\simulate_random_ultrafast.py
goto end

:season_sim
echo.
echo ========================================
echo 2025 MLB Season Simulation
echo ========================================
echo.
echo Simulate the 2025 MLB season using the real schedule!
echo.
echo Features:
echo   - Day-by-day simulation following actual schedule
echo   - Parallel processing for each day's games
echo   - Full standings with W-L, Run Diff, Streak, L10
echo   - Supports custom date ranges or full season
echo.
echo The simulation uses teams from baseball_teams.db.
echo Make sure your teams are loaded (option 5 or manage_teams.py).
echo.
echo Interactive mode lets you choose:
echo   - First week, first month, specific month
echo   - Custom date range
echo   - Full season simulation
echo.
pause
echo.
python examples\simulate_2025_season.py
goto end

:invalid
echo Invalid choice. Please run the script again and select 0-9.
pause
exit /b

:end

echo.
echo ========================================
echo Simulation Complete!
echo ========================================
echo.
echo RECOMMENDED TESTING WORKFLOW:
echo   1. Option 8 - Run 5-10 games with MLB teams
echo   2. Check game_logs/ for detailed output
echo   3. For physics changes, also run Option 0
echo.
echo See TESTING_STRATEGY.md for full testing guide.
echo.
pause
