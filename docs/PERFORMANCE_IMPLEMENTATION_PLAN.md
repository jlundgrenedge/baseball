# Performance Optimization: Implementation Plan

> **Document Purpose**: Detailed implementation plan with checkable tasks based on Performance Optimization Analysis research findings. This document serves as the master checklist for achieving 100x+ speedup in simulation performance.

---

## Executive Summary

| Metric | Baseline | Target | Stretch Goal | Status |
|--------|----------|--------|--------------|--------|
| **Single Game** | ~30-60s | 3-5s | <1s | 🚧 IN PROGRESS |
| **162 Games (sequential)** | ~90 min | 10-15 min | 2-5 min | 🚧 IN PROGRESS |
| **162 Games (parallel, 8 cores)** | ~15-20 min | 3-5 min | <2 min | ⏳ PENDING |
| **Games/Hour** | ~100 | 1,000+ | 5,000+ | 🚧 IN PROGRESS |
| **At-bats/Second** | ~8 | ~50+ | ~100+ | 🚧 IN PROGRESS |

**Phases Completed**: 5 of 8
- ✅ Phase 1: Ultra-Fast Time Step Mode (9.7x speedup)
- ✅ Phase 2: Trajectory Buffer Pooling (100% pool efficiency)
- ✅ Phase 3: Aerodynamic Lookup Tables (14.5x combined speedup)
- ✅ Phase 4: Threading Support (for non-GIL workloads)
- ✅ Phase 5: Numba Parallel Integration (**7-8x batch speedup**)

**Current Bottleneck Analysis** (from profiling):
- **Physics Integration (RK4)**: ~50-70% of CPU time ← OPTIMIZED (Phases 1-3, 5)
- **Aerodynamic Force Calculations**: ~15-25% of CPU time ← OPTIMIZED (Phase 3)
- **Memory Allocation/GC**: ~15-25% of overhead ← OPTIMIZED (Phase 2)
- **Game Logic & Orchestration**: ~10-15% of CPU time
- **Logging/I/O**: ~5-10% (minimal in non-verbose mode)

**Key Finding**: The core bottleneck is the RK4 integration loop calling aerodynamic force calculations millions of times. All optimizations must target this hot path first.

---

## Priority Phases

### Phase 1: Ultra-Fast Time Step Mode (CRITICAL - Week 1) ✅ COMPLETE

**Impact**: Achieved ~5-10x speedup on trajectory calculations
**Risk**: Low-Medium (accuracy ~5% reduction acceptable for bulk sims)
**Complexity**: Low

The simulation already has a `fast_mode` (2ms time step vs 1ms default) for ~2x speedup. We extend this to an "ultra-fast" mode with 5-10ms steps for Monte Carlo workloads where statistical accuracy matters more than individual trajectory precision.

#### Benchmark Results (Actual)

| Mode | Time Step | Trajectories/sec | Speedup | Accuracy |
|------|-----------|------------------|---------|----------|
| ACCURATE | 1ms | 58.8 | 1.0x | baseline |
| FAST | 2ms | 118.7 | **2.0x** | +0.01% |
| ULTRA_FAST | 5ms | 290.9 | **4.9x** | +0.05% |
| EXTREME | 10ms | 568.5 | **9.7x** | +0.12% |

#### Tasks

- [x] **1.1** Add `DT_ULTRA_FAST = 0.005` constant to `constants.py` (5ms time step)
  - Also add `DT_EXTREME = 0.01` (10ms) for maximum throughput
  - Document accuracy tradeoffs in comments

- [x] **1.2** Create `SimulationMode` enum in `constants.py`
  ```python
  class SimulationMode(Enum):
      ACCURATE = "accurate"      # DT_DEFAULT (1ms) - validation, research
      FAST = "fast"              # DT_FAST (2ms) - single games
      ULTRA_FAST = "ultra_fast"  # DT_ULTRA_FAST (5ms) - bulk sims
      EXTREME = "extreme"        # DT_EXTREME (10ms) - massive Monte Carlo
  ```

- [x] **1.3** Update `FastTrajectorySimulator` to accept `simulation_mode`
  - Backward compatible with `fast_mode` parameter
  - Auto-selects time step based on mode

- [x] **1.4** Propagate `simulation_mode` through simulation stack
  - `GameSimulator.__init__` accepts `simulation_mode` (string or enum)
  - Passes to `AtBatSimulator`, which passes to `BattedBallSimulator`
  - Default remains `ACCURATE` for backward compatibility

- [x] **1.5** Validate accuracy at each mode
  - All modes pass 7/7 physics validation tests
  - Distance accuracy within 0.12% even at EXTREME mode

- [x] **1.6** Benchmark performance at each mode
  - Created `benchmarks/benchmark_simulation_modes.py`
  - Trajectory speedup: 2x (FAST), 5x (ULTRA_FAST), 10x (EXTREME)
  - Game speedup: ~1.8x (limited by non-physics game logic)

**Validation Criteria**: ✅ ALL PASSED
- ULTRA_FAST mode: <5% accuracy loss ✅ (actual: 0.05%)
- All modes pass physics validation ✅ (7/7 for all modes)
- Benchmark documented ✅

---

### Phase 2: Memory Pooling Integration (HIGH - Week 1-2) ✅ COMPLETE

**Impact**: Buffer pooling integrated, 100% hit rate achieved
**Risk**: None (same calculations, just reusing memory)
**Complexity**: Low-Medium

The `performance.py` module has `TrajectoryBuffer`, `ResultObjectPool`, and `StateVectorPool` already implemented. This phase wired up the TrajectoryBuffer into the FastTrajectorySimulator.

#### Tasks

- [x] **2.1** Audit current memory allocation hotspots
  - Trajectory integration identified as primary allocation hotspot
  - Arrays allocated per-trajectory: times, positions, velocities

- [x] **2.2** Create buffered integrator function
  - Added `integrate_trajectory_buffered()` to `integrator.py`
  - Accepts pre-allocated `times_buf`, `pos_buf`, `vel_buf` arrays
  - Returns `step_count` instead of creating new trimmed arrays
  - Fully Numba JIT-compiled for maximum performance

- [x] **2.3** Integrate `TrajectoryBuffer` into `FastTrajectorySimulator`
  - Added `use_buffer_pool=True` parameter to constructor
  - `simulate_batted_ball()` acquires buffer, runs integration, releases buffer
  - `simulate_pitch()` also uses buffered integration
  - Buffers are always released (try/finally pattern)

- [x] **2.4** Integrate `ResultObjectPool` into `AtBatSimulator`
  - DEFERRED: Result object pooling adds complexity for minimal gain
  - Trajectory buffers provide the main allocation savings

- [x] **2.5** Add pool statistics tracking
  - `TrajectoryBuffer.get_stats()` returns hits, misses, efficiency, peak concurrent
  - `get_all_pool_stats()` aggregates all pool statistics
  - `print_pool_stats()` prints formatted statistics for debugging
  - Verified 100% hit rate in testing

- [x] **2.6** Validate memory reduction
  - Physics validation: 7/7 tests pass ✅
  - Buffer pool: 100% efficiency (no allocation misses) ✅
  - Game simulation works correctly with buffers ✅

**Validation Criteria**: ✅ ALL PASSED
- Physics validation tests pass (7/7) ✅
- Buffer pool 100% efficiency ✅
- No allocation misses in normal operation ✅

---

### Phase 3: Aerodynamic Lookup Tables (MEDIUM - Week 2) ✅ COMPLETED

**Impact**: Achieved ~2x speedup with lookup alone, 14.5x combined with ULTRA_FAST mode
**Risk**: Realized <0.01% mean error (far better than 2% target)
**Complexity**: Medium

The `OptimizedAerodynamicForces` class in `performance.py` provides precomputed lookup tables but isn't integrated into the hot path. This phase creates Numba-compatible lookup tables and integrates them into the trajectory simulation.

#### Tasks

- [x] **3.1** Audit `OptimizedAerodynamicForces` implementation ✅
  - Reviewed table resolution (velocity 5-60 m/s, spin 0-4000 rpm)
  - Bilinear interpolation is adequate
  - Full physics too slow for JIT hot path

- [x] **3.2** Create Numba-compatible lookup function ✅
  - Created `_lookup_cd_cl()` @njit function in aerodynamics.py
  - Created `aerodynamic_force_tuple_lookup()` @njit function
  - Global numpy arrays for Numba compatibility

- [x] **3.3** Add lookup mode to trajectory simulation ✅
  - Added `use_lookup` parameter to `FastTrajectorySimulator`
  - Created `integrate_trajectory_lookup()` in integrator.py
  - Separate integration path for lookup mode

- [x] **3.4** Wire lookup mode to `SimulationMode` ✅
  - ACCURATE/FAST: `use_lookup=False`
  - ULTRA_FAST/EXTREME: `use_lookup=True` (auto-enabled)
  - Tables pre-fetched during simulator init

- [x] **3.5** Validate accuracy of lookup tables ✅
  - Cd mean error: 0.0018% (far below 2% target)
  - Cl mean error: 0.0000%
  - Trajectory distance error: <2%

- [x] **3.6** Benchmark force calculation speedup ✅
  - ACCURATE + lookup: 2.06x speedup
  - ULTRA_FAST + lookup: 14.5x total speedup vs baseline
  - Exceeds Phase 3 targets

**Validation Criteria** (all met):
- Physics validation passes: 7/7 tests ✅
- Trajectory accuracy within 2%: All cases pass ✅
- Significant speedup achieved: 14.5x combined ✅

**Files Modified**:
- `batted_ball/aerodynamics.py`: Added lookup tables, `_lookup_cd_cl()`, `aerodynamic_force_tuple_lookup()`, `get_lookup_tables()`, `validate_lookup_accuracy()`
- `batted_ball/integrator.py`: Added `integrate_trajectory_lookup()`, `_step_rk4_lookup()`
- `batted_ball/fast_trajectory.py`: Added `use_lookup` parameter, conditional integration path

---

### Phase 4: Thread-Based Parallelism (MEDIUM - Week 2-3) ✅ COMPLETE

**Impact**: Threading works but processes remain faster (~2x) for full game sims due to GIL contention in Python game logic
**Risk**: Low (same computation, just different execution model)
**Complexity**: Medium

Current `ParallelGameSimulator` uses multiprocessing (process-based) which has pickle overhead and memory duplication. Since Numba code releases the GIL, we can use threads for better efficiency. **FINDING**: Thread-based parallelism is slower than process-based for full game simulations because the game logic (Python code) holds the GIL. Threads are better suited for Numba-heavy batched trajectory calculations.

#### Tasks

- [x] **4.1** Profile multiprocessing overhead
  - Measured: Threads ~2x slower than processes for full game sims
  - Root cause: GIL contention in Python game logic
  - Documented in ThreadedGameSimulator docstring

- [x] **4.2** Create `ThreadedGameSimulator` class
  - Uses `concurrent.futures.ThreadPoolExecutor`
  - Each thread creates its own `GameSimulator` instance
  - Added to `batted_ball/parallel_game_simulation.py`

- [x] **4.3** Implement per-game RNG seeding for determinism
  - Each game gets seed = `base_seed + game_index * 10000`
  - Uses `np.random.seed()` per thread
  - Determinism test passes (same seeds → same results)

- [x] **4.4** Add dynamic load balancing
  - `concurrent.futures.as_completed()` for dynamic scheduling
  - Games complete as ready, not in submission order

- [x] **4.5** Benchmark thread vs process parallelism
  - Result: Process-based ~68% faster than thread-based
  - Expected: Python game logic holds GIL
  - Documented when to use each approach

- [x] **4.6** Test thread safety
  - Ran parallel games with same seeds
  - No data corruption detected
  - Thread safety test passes

**Validation Results**:
- ✅ Deterministic results with same base seed
- ⚠️ Thread-based slower than process-based (expected - GIL)
- ✅ No race conditions or data corruption
- ✅ Physics validation: 7/7 tests pass

**Files Modified**:
- `batted_ball/parallel_game_simulation.py`: Added `ThreadedGameSimulator` class, `_threaded_simulate_game()` function
- `examples/test_phase4_threads.py`: Validation test suite (all 5 tests pass)

---

### Phase 5: Numba Parallel Integration (MEDIUM - Week 3) ✅ COMPLETE

**Impact**: Achieved **7-8x speedup** on batch trajectory processing (exceeded expectations of 2-3x!)
**Risk**: Low (same math, parallel execution)
**Complexity**: Medium

Numba supports `@njit(parallel=True)` with `prange` for parallel loops. We used this to parallelize multiple trajectory calculations across CPU cores.

#### Tasks

- [x] **5.1** Identify parallelizable operations
  - Batch trajectory simulations (independent trajectories)
  - Fielder time calculations (independent fielder-target pairs)
  - Trajectory endpoint calculations (memory efficient mode)

- [x] **5.2** Create batch trajectory integrator
  - `integrate_trajectories_batch_parallel()` in integrator.py
  - Uses `prange` to parallelize across N trajectories
  - Stores full position/velocity/time arrays for each trajectory

- [x] **5.3** Parallelize fielder route calculations
  - `calculate_fielder_times_batch()` for parallel fielder arrival times
  - Parallelizes across fielder × target combinations
  - ~900 calculations in 20ms

- [x] **5.4** Add memory-efficient endpoints-only mode
  - `calculate_trajectory_endpoints_batch()` returns only landing positions
  - 2345x memory savings vs full trajectories
  - Use for fielding range analysis, hit probability

- [x] **5.5** Benchmark parallel Numba speedup
  - Sequential: ~680 trajectories/sec
  - Parallel: ~5000+ trajectories/sec
  - **Measured speedup: 7-8x** (on 8-core system)

- [x] **5.6** Validate parallel results match sequential
  - Distance differences: <0.12% (well within tolerance)
  - Apex heights: exact match
  - Physics validation: 7/7 tests pass

**Validation Results**:
- ✅ Physics validation: 7/7 tests pass
- ✅ Results match sequential: <0.12% difference
- ✅ Speedup: 7-8x on multi-core systems
- ✅ Memory efficiency: 2345x reduction in endpoints-only mode

**Files Modified**:
- `batted_ball/integrator.py`: Added `integrate_trajectories_batch_parallel()`, `calculate_trajectory_endpoints_batch()`, `calculate_fielder_times_batch()`, helper functions
- `batted_ball/fast_trajectory.py`: Added `ParallelBatchTrajectorySimulator` class, `benchmark_parallel_batch()` function
- `examples/test_phase5_parallel.py`: Validation test suite (all 5 tests pass)

**New Classes/Functions**:
- `ParallelBatchTrajectorySimulator`: High-level parallel batch trajectory simulator
- `integrate_trajectories_batch_parallel()`: @njit(parallel=True) batch integration
- `calculate_trajectory_endpoints_batch()`: Memory-efficient endpoints-only mode
- `calculate_fielder_times_batch()`: Parallel fielder arrival time calculation
- `create_batch_initial_states()`: Helper to build batch initial state arrays
- `create_batch_spin_params()`: Helper to build batch spin parameter arrays

---

### Phase 6: Data Structure Optimization (LOW - Week 3-4) ⏳ NOT STARTED

**Impact**: Expected ~1.2x speedup in Python-level logic
**Risk**: None (internal changes, same API)
**Complexity**: Low

Micro-optimizations in Python code: `__slots__`, enums vs strings, reducing dict access in hot paths.

#### Tasks

- [ ] **6.1** Add `__slots__` to frequently instantiated classes
  - `AtBatResult`, `PlayResult`, `PitchResult`
  - `BaseRunner`, `Fielder` (if recreated frequently)
  - Reduces memory and attribute access time

- [ ] **6.2** Replace string comparisons with enums in hot paths
  - `at_bat_result.outcome == "strikeout"` → `Outcome.STRIKEOUT`
  - Already partially done with `PlayOutcome` enum
  - Audit `at_bat.py`, `game_simulation.py` for remaining strings

- [ ] **6.3** Convert pitch type lookups to indexed access
  - Currently using dict keyed by string name
  - Create list/array with indexed access by pitch_type_id
  - Profile to confirm improvement

- [ ] **6.4** Use NumPy structured arrays for player attributes
  - Store all player stats in contiguous memory
  - Reduces cache misses when accessing multiple attributes
  - Profile to confirm improvement

- [ ] **6.5** Eliminate unnecessary string formatting
  - Audit hot paths for f-strings that aren't used
  - Defer description building until actually needed
  - Check `simulate_at_bat()` and `simulate_complete_play()`

- [ ] **6.6** Profile and benchmark micro-optimizations
  - Measure cumulative impact of all micro-optimizations
  - Target: 10-20% improvement in Python-level code

**Validation Criteria**:
- All tests pass
- External API unchanged
- Measurable improvement in Python-level profiling

---

### Phase 7: Native Code Extensions (STRETCH - Week 4+) ⏳ NOT STARTED

**Impact**: Expected ~2-3x additional speedup on hot paths
**Risk**: Medium (maintenance complexity, build requirements)
**Complexity**: High

If all Python/Numba optimizations are exhausted and we still need more speed, consider rewriting critical components in C/C++/Rust.

#### Tasks

- [ ] **7.1** Evaluate Cython for integration loop
  - Convert `integrator.py` to Cython with type annotations
  - Compare performance to Numba JIT
  - Assess maintenance tradeoffs

- [ ] **7.2** Evaluate Rust via PyO3
  - Prototype RK4 integrator in Rust
  - Use Rayon for parallel trajectory batches
  - Measure speedup vs. Numba

- [ ] **7.3** Create C extension for force calculations
  - Hand-optimize aerodynamic force calculation in C
  - Use SIMD intrinsics (SSE/AVX) for vector operations
  - Integrate via ctypes or cffi

- [ ] **7.4** Benchmark native code vs. Numba
  - Fair comparison: same algorithm, different implementation
  - Measure both single-thread and parallel performance
  - Document when native code is worth the complexity

- [ ] **7.5** Decision: adopt native code or not
  - Based on benchmarks, decide if complexity is justified
  - If <2x improvement over Numba, likely not worth it
  - Document decision and rationale

**Validation Criteria**:
- Native code produces identical results to Python/Numba
- Performance improvement justifies maintenance complexity
- Build process works on Windows/Linux/macOS

---

### Phase 8: GPU Integration (FUTURE) 🔮 DEFERRED

**Impact**: Expected 10-50x speedup for massive batch simulations
**Risk**: High (architectural changes, hardware requirements)
**Complexity**: High

> **Note**: This phase is deferred until CPU optimizations are exhausted. The `gpu_acceleration.py` module exists but requires significant architectural changes to integrate into the game loop.

#### Future Tasks (not currently scheduled)

- [ ] Design batch accumulation architecture for trajectory requests
- [ ] Determine minimum batch size for GPU benefit (~100+ trajectories)
- [ ] Handle sequential game state dependencies with GPU async
- [ ] Implement CuPy-based batch integrator
- [ ] Create GPU/CPU fallback selection logic

---

## Cumulative Speedup Projections

| Phase | Individual Speedup | Cumulative Speedup | Single Game Time |
|-------|-------------------|-------------------|------------------|
| Baseline | 1x | 1x | ~45s |
| Phase 1: Ultra-Fast Mode | 5-10x | 5-10x | ~5-9s |
| Phase 2: Memory Pooling | 1.5-2x | 7.5-20x | ~2-6s |
| Phase 3: Lookup Tables | 1.2-1.5x | 9-30x | ~1.5-5s |
| Phase 4: Thread Parallelism | 1.5x (parallel efficiency) | N/A | N/A |
| Phase 5: Numba Parallel | 2-3x (batches) | 18-90x | ~0.5-2.5s |
| Phase 6: Data Structures | 1.2x | 21-108x | ~0.4-2s |
| Phase 7: Native Code | 2-3x | 42-324x | ~0.1-1s |

**Note**: Speedups are not perfectly multiplicative due to Amdahl's Law. The projections assume optimization targets different portions of the code.

**Realistic Target**: 20-50x speedup achievable with Phases 1-5.

---

## Validation & Testing

### Accuracy Validation

After each phase, run:

```bash
# Physics validation (must pass 7/7 for ACCURATE mode)
python -m batted_ball.validation

# Document which tests pass at which simulation mode
# ACCURATE: 7/7, FAST: 7/7, ULTRA_FAST: 6-7/7, EXTREME: 5-7/7
```

### Performance Benchmarks

Create benchmark scripts:

```bash
# Single trajectory benchmark
python benchmarks/benchmark_trajectory.py --mode accurate --count 1000

# Single game benchmark  
python benchmarks/benchmark_game.py --mode ultra_fast --count 10

# Parallel games benchmark
python benchmarks/benchmark_parallel.py --games 162 --workers 8
```

### Determinism Tests

```bash
# Run twice with same seed, verify identical results
python tests/test_determinism.py --seed 12345 --games 10
```

### Regression Detection

- Track performance metrics in CI
- Alert if single-game time increases >5%
- Alert if any physics validation test fails
- Track memory usage trends

---

## Implementation Order

**Week 1**:
1. Phase 1: Ultra-Fast Mode (highest impact, lowest risk)
2. Phase 2: Memory Pooling (already implemented, just needs integration)

**Week 2**:
3. Phase 3: Lookup Tables (medium complexity, solid speedup)
4. Phase 4: Thread Parallelism (improves multi-game efficiency)

**Week 3**:
5. Phase 5: Numba Parallel (requires restructuring for batches)
6. Phase 6: Data Structures (micro-optimizations, polish)

**Week 4+ (if needed)**:
7. Phase 7: Native Code (only if stretch goals required)

---

## Quick Reference: Files to Modify

| Phase | Primary Files |
|-------|---------------|
| Phase 1 | `constants.py`, `fast_trajectory.py`, `game_simulation.py` |
| Phase 2 | `integrator.py`, `trajectory.py`, `at_bat.py`, `performance.py` |
| Phase 3 | `aerodynamics.py`, `performance.py` |
| Phase 4 | `parallel_game_simulation.py` (or new file) |
| Phase 5 | `integrator.py`, `fielding.py` |
| Phase 6 | `at_bat.py`, `play_outcome.py`, `player.py` |
| Phase 7 | New C/Rust modules, build system |

---

## Success Metrics

| Milestone | Criteria | Target Date |
|-----------|----------|-------------|
| **Phase 1 Complete** | Ultra-fast mode working, 5x speedup | Week 1 |
| **Phase 2 Complete** | Memory pooling integrated, 50% memory reduction | Week 1 |
| **10x Speedup** | Single game in <5 seconds | Week 2 |
| **Phase 4 Complete** | Thread-based parallelism, deterministic | Week 2 |
| **50x Speedup** | 162 games in <3 minutes parallel | Week 3 |
| **100x Speedup** | 1000+ games/hour | Week 4 |

---

*Document Version: 1.0*  
*Created: 2025-11-28*  
*Based on: Performance Optimization Analysis Research*
*Related: PERFORMANCE_RESEARCH_PROMPT.md, Baseball_Simulator_Performance_Optimization_Analysis.md*
