# Performance Testing Suite

## Quick Start

### Windows
```batch
performance_test_suite.bat
```

### Linux/Mac
```bash
./performance_test_suite.sh
```

### Direct Python
```bash
python performance_test_suite.py
```

## What's Included

The interactive performance test suite provides easy access to all optimization benchmarks:

### Basic Tests
1. **Quick JIT Test** - Fast demonstration of JIT compilation speedup (10 trajectories)
2. **JIT Comparison** - Compare JIT vs normal mode (50 trajectories)
3. **Fast Mode Test** - Compare fast mode vs normal mode (50 trajectories)

### Game Simulation Tests
4. **Single Game** - Run one complete 9-inning game
5. **Multi-Core Parallel** - Simulate 10 games using all CPU cores
6. **Large-Scale Benchmark** - Simulate 50 games for comprehensive benchmark

### Batch Processing Tests
7. **Batch Trajectories** - Process 100 trajectories in batch mode
8. **Large Batch** - Process 1000 trajectories to test maximum throughput

### Advanced Tests
9. **GPU Acceleration** - Test GPU performance (requires CUDA + CuPy)
10. **Memory Optimization** - Benchmark object pooling and caching
11. **Comprehensive Report** - Generate complete performance analysis

### Validation
12. **Accuracy Tests** - Verify optimizations maintain simulation accuracy

## Expected Performance

### Trajectory Simulation
- **JIT Optimized**: 50-100+ trajectories/second
- **Fast Mode**: Additional 2× speedup
- **Batch Mode**: Efficient processing of 1000+ trajectories

### Game Simulation
- **Single Game**: ~30 seconds (varies by at-bats)
- **Multi-Core (8 cores)**: 5-8× faster than sequential
- **60 games**: ~1-2 minutes with parallelism (vs ~10 minutes sequential)

### GPU Acceleration (if available)
- **1000 trajectories**: Seconds instead of minutes
- **10,000+ trajectories**: 10-100× faster than CPU

## Sample Output

```
Quick JIT Performance Test
======================================================================
First call (JIT compilation)...
  Compilation time: 5.612s
  Distance: 122.6m
  Apex: 32.0m

Running 10 compiled trajectories...

Results:
  Total time:                  0.148s
  Average per trajectory:      14.77ms
  Throughput:                  67.7 traj/sec
  Speedup after compilation:   380×

✓ JIT optimization working correctly!
```

## Requirements

### Minimum
- Python 3.7+
- NumPy
- Numba

Install with:
```bash
pip install numpy numba
```

### Optional (for GPU acceleration)
- CUDA-capable GPU
- CuPy

Install with:
```bash
pip install cupy-cuda11x  # or cuda12x depending on CUDA version
```

## Documentation

For detailed information about performance optimizations:
- [Performance Guide](docs/PERFORMANCE_GUIDE.md) - Comprehensive optimization guide
- [Benchmark Tests](tests/test_performance_benchmarks.py) - Automated benchmark suite
- [Validation Tests](tests/test_optimization_accuracy.py) - Accuracy validation

## Troubleshooting

### Import Errors
If you see import errors, install dependencies:
```bash
pip install numpy numba
```

### GPU Not Available
GPU acceleration is optional. The test suite will detect if GPU is unavailable and provide installation instructions.

### Performance Lower Than Expected
- Ensure JIT compilation has completed (first run is always slower)
- Check CPU usage - should be 100% during multi-core tests
- Verify adequate cooling - thermal throttling can reduce performance
- Try fast mode for additional speedup

## Custom Testing

You can also import the test functions directly in your own scripts:

```python
from performance_test_suite import (
    test_quick_jit,
    test_parallel_games,
    test_batch_trajectories,
)

# Run specific tests
test_quick_jit(n_trajectories=100)
test_parallel_games(n_games=20)
test_batch_trajectories(n_trajectories=500)
```

## Performance Tips

1. **Start Small**: Begin with quick tests to verify everything works
2. **Check Accuracy**: Run validation tests to ensure correctness
3. **Scale Up**: Use larger benchmarks to test maximum performance
4. **GPU Testing**: If you have a GPU, test with 1000+ trajectories for best results
5. **Monitor Resources**: Watch CPU/GPU usage and temperatures during tests

## Support

For issues or questions:
1. Check the [Performance Guide](docs/PERFORMANCE_GUIDE.md)
2. Review test output for specific error messages
3. Ensure all dependencies are installed correctly
4. Verify Python version is 3.7 or higher
