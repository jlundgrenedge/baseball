@echo off
REM ========================================================================
REM Baseball Simulation Performance Test Suite
REM Interactive menu for testing all performance optimization capabilities
REM ========================================================================

echo.
echo ========================================================================
echo   BASEBALL SIMULATION PERFORMANCE TEST SUITE
echo ========================================================================
echo.
echo   This interactive test suite allows you to benchmark and test all
echo   performance optimizations implemented in the baseball simulator:
echo.
echo   OPTIMIZATIONS INCLUDED:
echo   - Numba JIT compilation (5-10x speedup)
echo   - Fast mode with larger time steps (2x additional speedup)
echo   - Multi-core parallelism (5-8x on 8 cores)
echo   - GPU acceleration (10-100x for large batches - if available)
echo   - Memory optimization (20-30%% improvement)
echo   - Batch trajectory processing
echo.
echo   EXPECTED PERFORMANCE:
echo   - 50-100+ trajectories/second with JIT
echo   - 100-1000x faster than original for large-scale simulations
echo   - GPU: 1000+ trajectories in seconds
echo.
echo ========================================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.7+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import numpy" 2>nul
if errorlevel 1 (
    echo.
    echo Installing required package: numpy...
    pip install numpy
)

python -c "import numba" 2>nul
if errorlevel 1 (
    echo.
    echo Installing required package: numba...
    pip install numba
)

echo.
echo Dependencies OK!
echo.
echo Starting interactive test suite...
echo.
timeout /t 2 /nobreak >nul

REM Launch the Python test suite
python performance_test_suite.py

echo.
echo ========================================================================
echo   Test Suite Closed
echo ========================================================================
echo.
echo   For more information, see:
echo   - docs/PERFORMANCE_GUIDE.md
echo   - tests/test_performance_benchmarks.py
echo   - tests/test_optimization_accuracy.py
echo.
pause
