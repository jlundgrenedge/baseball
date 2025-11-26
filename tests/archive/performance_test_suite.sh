#!/bin/bash
################################################################################
# Baseball Simulation Performance Test Suite
# Interactive menu for testing all performance optimization capabilities
################################################################################

echo ""
echo "========================================================================"
echo "  BASEBALL SIMULATION PERFORMANCE TEST SUITE"
echo "========================================================================"
echo ""
echo "  This interactive test suite allows you to benchmark and test all"
echo "  performance optimizations implemented in the baseball simulator:"
echo ""
echo "  OPTIMIZATIONS INCLUDED:"
echo "  - Numba JIT compilation (5-10× speedup)"
echo "  - Fast mode with larger time steps (2× additional speedup)"
echo "  - Multi-core parallelism (5-8× on 8 cores)"
echo "  - GPU acceleration (10-100× for large batches - if available)"
echo "  - Memory optimization (20-30% improvement)"
echo "  - Batch trajectory processing"
echo ""
echo "  EXPECTED PERFORMANCE:"
echo "  - 50-100+ trajectories/second with JIT"
echo "  - 100-1000× faster than original for large-scale simulations"
echo "  - GPU: 1000+ trajectories in seconds"
echo ""
echo "========================================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "ERROR: Python not found!"
        echo "Please install Python 3.7+ and ensure it's in your PATH"
        exit 1
    else
        PYTHON=python
    fi
else
    PYTHON=python3
fi

echo "Using Python: $PYTHON"
$PYTHON --version
echo ""

# Check if required packages are installed
echo "Checking dependencies..."

if ! $PYTHON -c "import numpy" 2>/dev/null; then
    echo ""
    echo "Installing required package: numpy..."
    $PYTHON -m pip install numpy
fi

if ! $PYTHON -c "import numba" 2>/dev/null; then
    echo ""
    echo "Installing required package: numba..."
    $PYTHON -m pip install numba
fi

echo ""
echo "Dependencies OK!"
echo ""
echo "Starting interactive test suite..."
echo ""
sleep 1

# Launch the Python test suite
$PYTHON performance_test_suite.py

echo ""
echo "========================================================================"
echo "  Test Suite Closed"
echo "========================================================================"
echo ""
echo "  For more information, see:"
echo "  - docs/PERFORMANCE_GUIDE.md"
echo "  - tests/test_performance_benchmarks.py"
echo "  - tests/test_optimization_accuracy.py"
echo ""
