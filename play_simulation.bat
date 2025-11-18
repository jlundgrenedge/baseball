@echo off
echo ========================================
echo MLB Team Simulation
echo ========================================
echo.
echo Simulate games with REAL MLB players!
echo.
echo Requirements:
echo   - pybaseball package (pip install pybaseball)
echo   - pandas package (pip install pandas)
echo.
echo ========================================
echo Choose simulation mode:
echo ========================================
echo   1. Yankees vs Dodgers (Full Game)
echo   2. Individual Player Demo (Ohtani vs Judge)
echo   3. Quick Demo (Individual players only)
echo   4. Custom Team Matchup (Advanced)
echo   5. Exit
echo.
set /p choice="Enter your choice (1-5): "

if "%choice%"=="1" goto yankees_dodgers
if "%choice%"=="2" goto player_demo
if "%choice%"=="3" goto quick_demo
if "%choice%"=="4" goto custom_matchup
if "%choice%"=="5" goto exit_script
goto invalid

:yankees_dodgers
echo.
echo ========================================
echo Yankees vs Dodgers Simulation
echo ========================================
echo.
echo This will simulate a complete 9-inning game between:
echo   - New York Yankees (Away)
echo   - Los Angeles Dodgers (Home)
echo.
echo The simulation will:
echo - Fetch real player statistics from 2024 MLB season
echo - Create teams with actual roster data
echo - Simulate a physics-based game with play-by-play
echo - Show final score and statistics
echo.
echo NOTE: First run may be slow due to data fetching
echo       from Baseball Savant/FanGraphs APIs
echo.
pause
echo.
echo Starting simulation...
echo.
python examples\simulate_mlb_teams.py
goto end

:player_demo
echo.
echo ========================================
echo Individual Player Simulation
echo ========================================
echo.
echo This demonstrates individual player simulations:
echo   Pitcher: Shohei Ohtani (2024 stats)
echo   Hitter:  Aaron Judge (2024 stats)
echo.
echo Will simulate 10 at-bats and show outcomes.
echo.
pause
echo.
python -c "import sys; sys.path.insert(0, '.'); from examples.simulate_mlb_teams import simulate_single_player_at_bats; simulate_single_player_at_bats()"
goto end

:quick_demo
echo.
echo ========================================
echo Quick Demo Mode
echo ========================================
echo.
echo Running quick demonstration with individual players only.
echo This skips the full game simulation for faster testing.
echo.
pause
echo.
python examples\simulate_mlb_teams.py --quick
goto end

:custom_matchup
echo.
echo ========================================
echo Custom Team Matchup
echo ========================================
echo.
echo This feature allows you to simulate games between
echo different MLB teams by modifying the script.
echo.
echo To create custom matchups:
echo   1. Open examples\simulate_mlb_teams.py
echo   2. Modify the roster lists in simulate_yankees_vs_dodgers()
echo   3. Change team names and player names
echo   4. Run the script again
echo.
echo Example teams you can create:
echo   - Any 2024 MLB team with real rosters
echo   - Historical matchups (specify different seasons)
echo   - Mixed teams with players from different eras
echo.
echo Current matchups available:
echo   - Yankees vs Dodgers (Option 1)
echo.
echo Would you like to:
echo   A. View the script for editing
echo   B. Return to main menu
echo.
set /p custom_choice="Enter your choice (A/B): "

if /i "%custom_choice%"=="A" goto view_script
if /i "%custom_choice%"=="B" goto end
goto invalid

:view_script
echo.
echo Opening script in default editor...
echo.
notepad examples\simulate_mlb_teams.py
goto end

:invalid
echo.
echo Invalid choice. Please run the script again and select a valid option.
echo.
pause
exit /b

:exit_script
echo.
echo Exiting...
exit /b

:end
echo.
echo ========================================
echo Simulation Complete!
echo ========================================
echo.
echo MLB TEAM SIMULATION FEATURES:
echo ========================================
echo.
echo What you just experienced:
echo - Real MLB player statistics from Baseball Savant
echo - Physics-based game simulation (not random dice rolls)
echo - Authentic player attributes mapped from actual stats
echo - Complete play-by-play with realistic outcomes
echo.
echo How it works:
echo - pybaseball fetches Statcast data for each player
echo - Player stats are converted to simulation attributes
echo - Physics engine simulates each pitch, swing, and fielding play
echo - Outcomes emerge from actual bat speed, pitch velocity, etc.
echo.
echo ========================================
echo CUSTOMIZATION OPTIONS:
echo ========================================
echo.
echo You can modify examples\simulate_mlb_teams.py to:
echo.
echo 1. Change teams:
echo    - Replace roster names with any MLB players
echo    - Mix players from different teams
echo    - Create historical matchups (change season year)
echo.
echo 2. Adjust rosters:
echo    - Add/remove players from lineup
echo    - Change batting order
echo    - Modify pitching rotation
echo.
echo 3. Simulation settings:
echo    - Change verbose=True/False for play-by-play
echo    - Modify number of innings
echo    - Adjust environmental conditions
echo.
echo Example roster modification:
echo.
echo     yankees_hitters = [
echo         ("Player Name", "Position"),
echo         ("Shohei Ohtani", "DH"),  # Add anyone!
echo         ...
echo     ]
echo.
echo ========================================
echo NEXT STEPS:
echo ========================================
echo.
echo 1. Install requirements (if not already installed):
echo    pip install pybaseball pandas
echo.
echo 2. Edit the script to create your own matchups:
echo    notepad examples\simulate_mlb_teams.py
echo.
echo 3. Run simulations with different teams and players
echo.
echo 4. For non-MLB simulations, use:
echo    game_simulation.bat
echo.
echo ========================================
echo TROUBLESHOOTING:
echo ========================================
echo.
echo If you see errors:
echo.
echo - "pybaseball not installed"
echo   Solution: pip install pybaseball pandas
echo.
echo - "Player not found"
echo   Solution: Check spelling, verify player played in specified season
echo.
echo - "Data fetch timeout"
echo   Solution: Check internet connection, try again later
echo.
echo - Generic team used instead
echo   Solution: This is expected fallback behavior if data unavailable
echo.
echo For more information, see:
echo   docs\PYBASEBALL_INTEGRATION.md
echo.
pause
