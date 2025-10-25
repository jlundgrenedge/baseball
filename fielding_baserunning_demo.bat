@echo off
echo ========================================
echo Baseball Fielding and Baserunning Demo
echo ========================================
echo.
echo This demonstration shows the new fielding and baserunning mechanics
echo that complete the baseball physics simulation engine.
echo.
echo Features demonstrated:
echo - Physics-based fielding with reaction time, speed, and range
echo - Realistic baserunning with acceleration and turn efficiency  
echo - Complete play simulation integrating all components
echo - Outcome determination based on timing comparisons
echo - Validation against MLB performance benchmarks
echo.
pause
echo.

echo Running fielding and baserunning demonstration...
python examples\fielding_baserunning_demo.py
echo.

echo Running validation tests...
python examples\validate_fielding_baserunning.py
echo.

echo Running complete play scenarios...
python examples\complete_play_scenarios.py
echo.

echo ========================================
echo Demonstration Complete!
echo ========================================
echo.
echo The baseball physics simulator now includes:
echo Phase 1: Spin-dependent aerodynamics
echo Phase 2: Bat-ball collision physics  
echo Phase 3: Pitch trajectory simulation
echo Phase 4: Player attributes and at-bat engine
echo Phase 5: Fielding and baserunning mechanics
echo.
echo You can now simulate complete baseball plays from pitch
echo to final outcome with realistic physics throughout!
echo.
pause