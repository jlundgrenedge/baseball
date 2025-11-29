# Performance Optimization: Implementation Plan

> **Document Purpose**: Detailed implementation plan with checkable tasks based on Performance Optimization Analysis research findings. This document serves as the master checklist for achieving 100x+ speedup in simulation performance.

---

## Executive Summary

| Metric | Baseline | Target | Stretch Goal | Status |
|--------|----------|--------|--------------|--------|
| **Single Game** | ~30-60s | 3-5s | <1s | ⏳ PENDING |
| **162 Games (sequential)** | ~90 min | 10-15 min | 2-5 min | ⏳ PENDING |
| **162 Games (parallel, 8 cores)** | ~15-20 min | 3-5 min | <2 min | ⏳ PENDING |
| **Games/Hour** | ~100 | 1,000+ | 5,000+ | ⏳ PENDING |
| **At-bats/Second** | ~8 | ~50+ | ~100+ | ⏳ PENDING |

**Current Bottleneck Analysis** (from profiling):
- **Physics Integration (RK4)**: ~50-70% of CPU time
- **Aerodynamic Force Calculations**: ~15-25% of CPU time  
- **Memory Allocation/GC**: ~15-25% of overhead
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

### Phase 2: Memory Pooling Integration (HIGH - Week 1-2) ⏳ NOT STARTED

**Impact**: Expected ~1.5-2x speedup by eliminating allocation overhead
**Risk**: None (same calculations, just reusing memory)
**Complexity**: Low-Medium

The `performance.py` module has `TrajectoryBuffer`, `ResultObjectPool`, and `StateVectorPool` already implemented but NOT integrated into the main simulation loop. This phase wires them up.

#### Tasks

- [ ] **2.1** Audit current memory allocation hotspots
  - Run `tracemalloc` on a single game simulation
  - Identify top 10 allocation sources
  - Document in `docs/guides/MEMORY_PROFILING.md`

- [ ] **2.2** Create buffered integrator function
  - Add `integrate_trajectory_buffered()` to `integrator.py`
  - Accepts pre-allocated `times_buf`, `pos_buf`, `vel_buf` arrays
  - Returns `step_count` instead of creating new trimmed arrays

- [ ] **2.3** Integrate `TrajectoryBuffer` into `BattedBallSimulator`
  - Acquire buffer before simulation: `buffer = get_trajectory_buffer().get_buffer()`
  - Pass buffers to `integrate_trajectory_buffered()`
  - Release buffer after extracting results: `buffer.release()`

- [ ] **2.4** Integrate `ResultObjectPool` into `AtBatSimulator`
  - Use `result_pool.get_pitch_data()` instead of creating new dicts
  - Use `result_pool.get_result_dict()` for at-bat results
  - Return objects to pool at end of at-bat or game

- [ ] **2.5** Add pool statistics tracking
  - Track pool hit/miss rates
  - Log pool utilization in verbose mode
  - Verify pools are being used (not just allocated)

- [ ] **2.6** Validate memory reduction
  - Compare peak memory for 100-game simulation before/after
  - Target: 50%+ reduction in peak memory
  - Target: 60-80% reduction in GC pause time

**Validation Criteria**:
- Physics validation tests pass (7/7)
- Game statistics unchanged (same RNG seed = identical results)
- Peak memory reduced by 50%+
- GC overhead reduced significantly

---

### Phase 3: Aerodynamic Lookup Tables (MEDIUM - Week 2) ⏳ NOT STARTED

**Impact**: Expected ~1.2-1.5x speedup on force calculations (3-5x on force calc itself)
**Risk**: Low (~2% accuracy loss from interpolation)
**Complexity**: Medium

The `OptimizedAerodynamicForces` class in `performance.py` provides precomputed lookup tables but isn't integrated into the hot path. This phase enables it.

#### Tasks

- [ ] **3.1** Audit `OptimizedAerodynamicForces` implementation
  - Verify table resolution is sufficient (velocity bins, spin bins)
  - Check interpolation method (bilinear should be adequate)
  - Measure cache lookup time vs. full calculation time

- [ ] **3.2** Create Numba-compatible lookup function
  - The current implementation uses Python classes
  - Create `@njit`-decorated `lookup_aerodynamic_force()` function
  - Accept velocity magnitude and spin rate, return force magnitude

- [ ] **3.3** Add lookup mode to `aerodynamic_force_tuple()`
  - Add `use_lookup` parameter (default False for accuracy)
  - When True, use table interpolation instead of full calculation
  - When False, use existing accurate calculation

- [ ] **3.4** Wire lookup mode to `SimulationMode`
  - ACCURATE/FAST: `use_lookup=False`
  - ULTRA_FAST/EXTREME: `use_lookup=True`

- [ ] **3.5** Validate accuracy of lookup tables
  - Compare lookup vs. exact for 10,000 random velocity/spin combinations
  - Document max error, mean error, std deviation
  - Target: <2% mean error, <5% max error

- [ ] **3.6** Benchmark force calculation speedup
  - Measure time for 1M force calculations with/without lookup
  - Target: 3-5x speedup on force calculation portion

**Validation Criteria**:
- Physics validation passes at ACCURATE/FAST modes
- Aggregate statistics within 2% at ULTRA_FAST/EXTREME modes
- Force calculation benchmarks show significant speedup

---

### Phase 4: Thread-Based Parallelism (MEDIUM - Week 2-3) ⏳ NOT STARTED

**Impact**: Expected ~1.5x improvement in parallel efficiency
**Risk**: Low (same computation, just different execution model)
**Complexity**: Medium

Current `ParallelGameSimulator` uses multiprocessing (process-based) which has pickle overhead and memory duplication. Since Numba code releases the GIL, we can use threads for better efficiency.

#### Tasks

- [ ] **4.1** Profile multiprocessing overhead
  - Measure time for process creation, data serialization
  - Calculate overhead as % of total parallel simulation time
  - Document baseline parallel efficiency (actual speedup / theoretical max)

- [ ] **4.2** Create `ThreadedGameSimulator` class
  - Use `concurrent.futures.ThreadPoolExecutor`
  - Each thread creates its own `GameSimulator` instance
  - Share read-only data (teams, players) without copying

- [ ] **4.3** Implement per-game RNG seeding for determinism
  - Each game gets seed = `base_seed + game_index`
  - Ensures reproducible results regardless of thread scheduling
  - Add test to verify determinism

- [ ] **4.4** Add dynamic load balancing
  - Use work-stealing queue instead of static partitioning
  - Games complete at different speeds (extra innings, etc.)
  - `concurrent.futures.as_completed()` for dynamic scheduling

- [ ] **4.5** Benchmark thread vs process parallelism
  - Run 100 games with both approaches on 8 cores
  - Measure wall-clock time and CPU utilization
  - Target: 20-30% improvement over process-based

- [ ] **4.6** Test thread safety
  - Run 1000 games in parallel twice with same seeds
  - Verify identical aggregate results both times
  - Add stress test to CI

**Validation Criteria**:
- Deterministic results with same base seed
- Thread-based faster than process-based for same core count
- No race conditions or data corruption

---

### Phase 5: Numba Parallel Integration (MEDIUM - Week 3) ⏳ NOT STARTED

**Impact**: Expected ~2-3x speedup on trajectory batches
**Risk**: Low (same math, parallel execution)
**Complexity**: Medium

Numba supports `@njit(parallel=True)` with `prange` for parallel loops. We can use this to parallelize multiple trajectory calculations within a single thread.

#### Tasks

- [ ] **5.1** Identify parallelizable operations
  - Multiple fielder route calculations (independent)
  - Batch trajectory simulations
  - Multiple at-bat simulations in bulk mode

- [ ] **5.2** Create batch trajectory integrator
  - `integrate_trajectories_batch()` accepts array of initial states
  - Uses `prange` to parallelize across trajectories
  - Requires restructuring to process N trajectories in lockstep

- [ ] **5.3** Parallelize fielder route calculations
  - In `fielding.py`, fielder routes are independent
  - Wrap fielder simulation loop with `prange`
  - Measure impact (fielding is ~10% of play resolution time)

- [ ] **5.4** Add `@njit(parallel=True)` to force calculation batches
  - When calculating forces for multiple states, vectorize
  - Use Numba's parallel reduction patterns

- [ ] **5.5** Benchmark parallel Numba speedup
  - Compare single-thread vs. parallel-thread Numba
  - Measure on 4-core, 8-core systems
  - Document scaling behavior

- [ ] **5.6** Validate parallel results match sequential
  - Same inputs should produce same outputs
  - Account for floating-point ordering differences (within tolerance)

**Validation Criteria**:
- Physics validation tests pass
- Results match sequential execution (within floating-point tolerance)
- Measurable speedup on multi-core systems

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
