# Deep Research Prompt: Baseball Physics Simulator Performance Optimization

## Executive Summary

**Objective**: Analyze the `baseball` simulation engine codebase and provide a comprehensive report on how to achieve a **100x+ speedup** in simulation performance.

**Current State**: A 162-game simulation using real MLB database players takes approximately **1.5 hours** (~90 minutes).

**Target State**: We want to simulate **thousands of games** (1,600-16,000+) in that same 1.5-hour window for better statistical validation.

**Repository**: `jlundgrenedge/baseball` (GitHub)

---

## Background & Context

### What This Simulation Does

This is a **physics-based baseball simulation engine** (~25,600 lines of Python) that models complete 9-inning games from pitch to play outcome. Unlike arcade games or pure statistical simulations, **every outcome emerges from rigorous physics calculations** calibrated against MLB Statcast data.

**Core simulation loop per game**:
1. ~150-200 pitches per game
2. Each pitch involves:
   - Pitch trajectory simulation (RK4 integration with 1ms time steps)
   - Swing decision modeling
   - Contact physics (if swung)
   - Batted ball trajectory simulation (RK4 integration, potentially 5-10 seconds of flight time = 5,000-10,000 integration steps)
   - Fielding simulation (fielder movement, catch timing, throws)
   - Baserunning simulation
3. Full game: ~200-300 trajectory integrations per game
4. Each trajectory: ~5,000-15,000 RK4 steps

### What We've Already Implemented (Preliminary Optimizations)

1. **Numba JIT Compilation** (`integrator.py`, `aerodynamics.py`)
   - Core integration loop is JIT-compiled
   - Aerodynamic force calculations are JIT-compiled
   - Provides ~5-10x speedup over pure Python

2. **Fast Mode** (`fast_trajectory.py`)
   - Larger time step (2ms vs 1ms default)
   - ~2x speedup with <1% accuracy loss

3. **Parallel Game Simulation** (`parallel_game_simulation.py`)
   - Uses Python multiprocessing to run games on multiple CPU cores
   - ~5-8x speedup on 8-core systems for multi-game simulations

4. **GPU Acceleration Stub** (`gpu_acceleration.py`)
   - CuPy-based GPU trajectory simulation
   - Works for batch trajectory calculations
   - **NOT integrated into game simulation loop**

5. **Performance Utilities** (`performance.py`)
   - Object pooling (TrajectoryBuffer, ResultObjectPool, StateVectorPool)
   - Force calculation caching (ForceCalculationCache)
   - Lookup table aerodynamics (OptimizedAerodynamicForces)
   - UltraFastMode with aggressive approximations

6. **Bulk Simulation** (`bulk_simulation.py`)
   - Optimized for large-scale at-bat analysis
   - Batch processing with streaming results

### Current Performance Metrics

- **Single game**: ~30-60 seconds
- **162 games (sequential)**: ~1.5 hours
- **162 games (parallel, 8 cores)**: ~15-20 minutes (but still too slow for thousands)
- **Target**: 162 games in ~1-2 minutes (so we can do 5,000+ games per hour)

---

## Key Files to Analyze

### Tier 1: Critical Path (Integration & Physics)

| File | Lines | Description | Likely Bottleneck? |
|------|-------|-------------|-------------------|
| `batted_ball/integrator.py` | 513 | RK4 numerical solver, JIT-compiled | **HIGH** - Called millions of times |
| `batted_ball/aerodynamics.py` | 589 | Drag + Magnus force calculations | **HIGH** - Called 4x per RK4 step |
| `batted_ball/trajectory.py` | 661 | BattedBallSimulator class | **MEDIUM** - Orchestrates integration |
| `batted_ball/constants.py` | 849 | All physics constants, time steps | MEDIUM - DT_DEFAULT controls loop count |

### Tier 2: Game Logic & Player Simulation

| File | Lines | Description | Likely Bottleneck? |
|------|-------|-------------|-------------------|
| `batted_ball/at_bat.py` | 830 | Plate appearance simulation | MEDIUM - Per-pitch overhead |
| `batted_ball/pitch.py` | 880 | Pitch trajectory simulation | MEDIUM - Per-pitch trajectory |
| `batted_ball/contact.py` | 699 | Sweet spot physics | LOW |
| `batted_ball/game_simulation.py` | 815+ | Full game orchestration | LOW - Just orchestration |

### Tier 3: Fielding & Baserunning

| File | Lines | Description | Likely Bottleneck? |
|------|-------|-------------|-------------------|
| `batted_ball/fielding.py` | 1,479 | Fielder movement, throws | MEDIUM - Complex calculations |
| `batted_ball/baserunning.py` | 982 | Runner mechanics | LOW |
| `batted_ball/play_simulation.py` | ~600 | Coordinates all actions | LOW |

### Tier 4: Existing Performance Infrastructure

| File | Lines | Description | Status |
|------|-------|-------------|--------|
| `batted_ball/performance.py` | 588 | Caching, pooling, lookup tables | Partially integrated |
| `batted_ball/bulk_simulation.py` | 426 | Bulk at-bat processing | Available but underutilized |
| `batted_ball/gpu_acceleration.py` | 460 | CUDA trajectory batching | **NOT integrated into game loop** |
| `batted_ball/parallel_game_simulation.py` | 605 | Multi-core games | Working but has overhead |
| `batted_ball/fast_trajectory.py` | ~300 | Fast mode simulator | Available |

---

## Research Questions

### 1. Profile-Based Analysis

**Question**: Where is the actual time being spent?

Please analyze:
- Which functions consume the most time per game?
- What is the breakdown between trajectory integration, force calculations, and game logic?
- Are there unexpected bottlenecks outside of physics (e.g., logging, data structures, object creation)?

**Suggested approach**:
- Run `cProfile` on a single game simulation
- Identify the top 20 time-consuming functions
- Calculate percentage of time in physics vs. game logic

### 2. Integration Loop Optimization

**Question**: Can we fundamentally speed up the RK4 integration loop?

The integration loop in `integrator.py` is the hot path. Each trajectory requires 5,000-15,000 steps, and each step calls the force function 4 times.

Please analyze:
- Is Numba JIT being used optimally? (Check `@njit(cache=True)` decorations)
- Are there any remaining Python-level overheads in the hot path?
- Could we use adaptive time stepping to reduce step count?
- Would Euler integration (instead of RK4) be acceptable for gameplay accuracy?
- Could we pre-compute trajectory lookup tables for common scenarios?

### 3. Batch Processing Architecture

**Question**: Can we restructure the simulation to process trajectories in batches?

Currently, each trajectory is computed sequentially within a game. GPU acceleration (`gpu_acceleration.py`) shows batch processing is possible, but it's not integrated.

Please analyze:
- Can we batch all pitch trajectories for a half-inning?
- Can we batch all batted ball trajectories?
- What architectural changes would enable GPU batch processing within the game loop?
- Could we use NumPy vectorization even without GPU?

### 4. Parallelization Strategy

**Question**: How can we maximize parallel utilization?

Current parallel implementation (`parallel_game_simulation.py`) uses multiprocessing at the game level. But:
- Process creation has overhead
- Games are not load-balanced (some games have more at-bats)

Please analyze:
- Would thread-based parallelism work better for CPU-bound Numba code?
- Could we parallelize within a game (e.g., parallel fielder simulations)?
- What's the overhead of current process-based approach?
- Could we use `concurrent.futures` or `joblib` more efficiently?

### 5. Memory & Allocation Analysis

**Question**: Is object creation/GC a significant overhead?

The `performance.py` module has object pooling infrastructure that may not be fully utilized.

Please analyze:
- Are we creating too many temporary arrays in the hot path?
- Is the object pooling actually being used in the main simulation?
- Could we pre-allocate all arrays needed for a full game?
- Would using NumPy structured arrays reduce allocation overhead?

### 6. Logging & I/O Overhead

**Question**: How much time is spent on logging, file I/O, and string formatting?

The simulation generates detailed play-by-play logs. Even in non-verbose mode, there may be hidden overhead.

Please analyze:
- What is the overhead of the `log()` method in `game_simulation.py`?
- Are we building strings that are never used when verbose=False?
- Is there I/O blocking during simulation (file writes, console output)?
- Could we defer all logging to post-simulation processing?
- Are there unnecessary string interpolations in hot paths?

### 7. Numba Optimization Deep Dive

**Question**: Are we getting maximum performance from Numba JIT compilation?

Numba is already used in `integrator.py` and `aerodynamics.py`, but there may be room for improvement.

Please analyze:
- Are all hot-path functions properly decorated with `@njit(cache=True)`?
- Are there any functions that fall back to object mode (check for warnings)?
- Could we use `@njit(parallel=True)` with `prange` for any loops?
- Are we passing Python objects that force boxing/unboxing overhead?
- Could we use Numba's `@vectorize` or `@guvectorize` for element-wise operations?
- Is the Numba cache being properly utilized across runs?

> **Note**: GPU integration via `gpu_acceleration.py` exists but requires significant architectural changes to integrate into the game loop. Consider this a future phase after CPU optimizations are exhausted.

### 8. Caching & Memoization

**Question**: Are there repeated calculations we can cache?

Please analyze:
- Are we recalculating the same aerodynamic parameters repeatedly?
- Could we cache pitcher-specific pitch templates?
- Could we cache fielder movement paths for common scenarios?
- Are lookup tables in `performance.py` being utilized?

### 9. Data Structure Efficiency

**Question**: Are our data structures optimal for the access patterns?

Please analyze:
- Are dataclasses adding overhead vs. simple tuples or named tuples?
- Could we use NumPy structured arrays for player attributes?
- Is there excessive dictionary access in hot paths?
- Could we use slots in classes to reduce memory overhead?

### 10. Language-Level Options

**Question**: Should any components be rewritten in a faster language?

Please analyze:
- Would Cython provide additional speedup beyond Numba?
- Could we write a C extension for the core integration loop?
- Would PyPy provide benefits (compatibility issues with NumPy/Numba)?
- Could we use Rust via PyO3 for critical sections?

---

## Deliverables Requested

### 1. Profiling Report

- Detailed breakdown of where time is spent
- Flame graph or call tree visualization
- Identification of top 10 optimization targets

### 2. Optimization Roadmap

Provide a prioritized list of optimizations with:
- Estimated speedup potential
- Implementation complexity (Low/Medium/High)
- Risk of accuracy degradation
- Dependencies on other changes

### 3. Architectural Recommendations

- Proposed changes to enable batch processing
- GPU integration strategy
- Memory management improvements

### 4. Code-Level Recommendations

For each high-priority optimization:
- Specific files and functions to modify
- Before/after code examples
- Testing approach to verify accuracy

### 5. Performance Testing Plan

- Benchmark scripts to measure improvements
- Accuracy validation tests
- Regression detection approach

---

## Constraints & Requirements

### Must Preserve

1. **Physics accuracy**: 7/7 validation tests must pass (`python -m batted_ball.validation`)
2. **MLB realism**: Game statistics must match expected ranges (see TESTING_STRATEGY.md)
3. **Determinism**: Given same RNG seed, simulation should produce identical results
4. **Python compatibility**: Must work with Python 3.9+

### Acceptable Tradeoffs

1. **Accuracy reduction** of <5% in trajectory distances is acceptable for bulk simulations
2. **Memory increase** is acceptable if it improves speed
3. **Additional dependencies** (e.g., CuPy, Cython) are acceptable
4. **Breaking changes** to internal APIs are fine; external API should remain stable

### Performance Targets

| Metric | Current | Target | Stretch Goal |
|--------|---------|--------|--------------|
| Single game | 30-60s | 3-5s | <1s |
| 162 games | 90 min | 5-10 min | 1-2 min |
| Games/hour | ~100 | 1,000+ | 5,000+ |

---

## Additional Context

### Why Speed Matters

We need to run thousands of games to:
1. **Validate simulation accuracy**: Compare aggregated stats to MLB averages
2. **Test player balance**: Ensure attribute system produces realistic outcomes
3. **Detect bugs**: Edge cases only appear in large samples
4. **Enable season simulations**: Want to run full 162-game seasons for multiple teams

### Current Technology Stack

- **Python 3.11**
- **NumPy**: Core numerical operations
- **Numba**: JIT compilation for hot paths
- **CuPy** (optional): GPU acceleration
- **Multiprocessing**: Parallel game execution

### Development Environment

- Windows 11
- 8-core CPU (can test with more)
- NVIDIA GPU available (if GPU approach is viable)
- ~16GB RAM

---

## Appendix: Quick Start for Analysis

```bash
# Clone and setup
git clone https://github.com/jlundgrenedge/baseball.git
cd baseball
pip install -r requirements.txt

# Run a single game for profiling
python -m cProfile -o profile.stats examples/quick_game_test.py

# View profile results
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative').print_stats(30)"

# Run physics validation
python -m batted_ball.validation

# Run parallel games for timing
python examples/simulate_db_teams.py
```

---

## Contact & Follow-Up

After completing this analysis, please provide:

1. A summary document with key findings
2. Prioritized optimization recommendations
3. Proof-of-concept code for top 2-3 optimizations
4. Benchmarks showing before/after performance

We're particularly interested in **architectural changes** that could enable order-of-magnitude improvements, not just incremental tuning.

---

*Document Version: 1.0*  
*Created: 2025-11-28*  
*Purpose: Deep research prompt for simulation performance optimization*
