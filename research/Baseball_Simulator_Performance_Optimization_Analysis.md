# Baseball Simulator Performance Optimization Analysis

## 1. Profiling & Bottleneck Analysis

**Overall Performance:** Profiling confirms that **physics calculations
dominate runtime**, consuming roughly 85-90% of total execution time,
whereas game logic and overhead account for only
\~10-15%[\[1\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L14-L22).
In particular, **numerical integration** of trajectories (the RK4 loop
in `integrator.py`) is by far the largest hotspot -- approximately
**50-70%** of total CPU time per
game[\[2\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L14-L19).
This integration loop includes thousands of time-steps per trajectory
(1ms steps by default) and invokes the aerodynamic force computation 4×
per step (for RK4). The aerodynamic force calculations themselves (in
`aerodynamics.py`) are the next largest contributor, since they involve
costly operations (vector normalization, square roots, cross products)
and are called millions of times. Together, the RK4 integrator and force
modeling constitute the bulk of "physics" time.

**Game Logic vs Physics:** The **gameplay logic** (at-bat state updates,
pitch selection, swing decisions, etc.) is relatively minor in
comparison -- on the order of 10-15% of
runtime[\[3\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L24-L29).
This includes Python-level decision-making in `AtBatSimulator` (e.g.
random pitch type selection, swing probability checks, string
comparisons for outcomes, etc.) and orchestrating each pitch/play. These
steps are not trivial, but they pale next to the raw physics loop.
Memory management and object creation also consume a noticeable fraction
(\~15-25%)[\[4\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L20-L25),
which manifests as Python overhead for constructing dictionaries
(`pitch_data`, results) each play, allocating NumPy arrays for
trajectory results, and garbage collection. The **dynamic memory
allocation** during each trajectory (creating time/position arrays,
etc.) introduces significant overhead and cache misses, contributing up
to one-quarter of
runtime[\[4\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L20-L25).

**Detailed Hotspots:** The most expensive functions identified via
profiling include:

- `integrate_trajectory_jit` (in `batted_ball.integrator`): This
  JIT-compiled RK4 loop accounts for roughly half of total runtime
  alone[\[2\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L14-L19).
  It iteratively updates the ball's state, and spends most of its time
  in two places -- calling the force function and performing vector
  arithmetic for RK4 steps.
- **Aerodynamic force computation** (in `batted_ball.aerodynamics`): The
  Numba-optimized function `aerodynamic_force_tuple` (and its helper
  `calculate_aerodynamic_forces_fast`) is called four times per
  integration step. This contributes a large portion of the integrator's
  cost. Every time-step requires normalization of velocity, computing
  drag and Magnus forces, etc., which is CPU-intensive. This inner loop
  is invoked on the order of *billions* of times in a full-season
  simulation.
- **Pitch trajectory simulation** (in
  `batted_ball.pitch.PitchSimulator.simulate`): Each pitch uses a
  smaller integration (flight \~0.4s). Pitch integration is also
  physics-based but uses a shorter duration (50--200 steps) and
  sometimes Euler integration for speed. It's less costly than a
  batted-ball flight, but across \~150--200 pitches/game it adds up. If
  Numba is not used for pitch integration (currently
  `integrate_trajectory` in pitch module is pure Python), those calls
  show up in the profile. In total, pitch trajectories contribute
  meaningfully but still well under the batted-ball portion.
- **At-bat and game orchestration** (in `AtBatSimulator.simulate_at_bat`
  and `GameSimulator.simulate_game`): These functions manage the
  sequence of pitches and plays. They show up in profiles mostly for
  their cumulative time (since they call into the heavy physics
  functions many times), but their *internal* overhead is modest
  (looping over pitches, updating counts, constructing result objects).
  Still, creating result dictionaries for each pitch and final at-bat
  result does incur some overhead (reflected in the 10-15% game logic
  figure)[\[3\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L24-L29).
- **Logging and I/O:** When run in non-verbose mode (which is the case
  for performance runs), **logging is minimal**. The
  `GameSimulator.log()` method simply returns if
  `verbose=False`[\[5\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/game_simulation.py#L523-L531),
  so console output is not a factor during bulk simulation. However,
  **string formatting** can still occur for play-by-play data -- e.g.
  constructing description strings for events. In the profile, logging
  and other I/O account for at most **5-10%** of
  time[\[6\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/PERFORMANCE_GUIDE.md#L22-L28)
  (and essentially 0% in truly silent mode). We should still ensure that
  no expensive string operations are happening unnecessarily in hot
  loops (for example, avoid f-string constructions unless needed).

**Physics vs Others -- Summary:** In a representative profile of a full
game, **approximately 70%** of time is spent in pure physics
calculations (trajectory integration + aerodynamic forces), **\~20%** in
memory management and object creation (array allocations, Python object
instantiation), and the remaining **\~10%** in game logic and
miscellaneous tasks (pitch selection logic, logging,
etc.)[\[1\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L14-L22)[\[3\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L24-L29).
This indicates that any optimization efforts should first target the
physics engine (integrator and forces), followed by reducing memory
overhead and then streamlining the Python-level logic. The profile did
**not** reveal any surprising hidden bottlenecks -- as expected, the
numerical integration is the critical path. That said, it's worth noting
that **Numba JIT** already eliminates a huge amount of Python overhead
in the integrator; the 50-70% for integration is the *optimized* cost
(had it been pure Python, it would dominate even more). This means
further improvements will require either algorithmic changes or
lower-level optimizations beyond what vanilla Numba provides.

To visualize the execution, the call hierarchy below highlights the
heavy hitters (pseudo-call-tree of one pitch with contact):

    GameSimulator.simulate_game 
     └─ AtBatSimulator.simulate_at_bat 
         ├─ PitchSimulator.simulate (called ~5 times per PA)
         │    └─ integrate_trajectory [...] → (RK4 loop for pitch flight) [7]
         └─ BattedBallSimulator.simulate_batted_ball (if contact)
              └─ FastTrajectorySimulator.integrate_trajectory_jit (RK4 loop for batted ball)
                   ├─ _step_rk4_jit (Numba) – calls aerodynamic_force_tuple 4x per step[8][9]
                   └─ (array writes to positions, velocities each step)[10]

In this breakdown, the deepest levels (`_step_rk4_jit` and the force
calculation) are where the CPU cycles concentrate. Any optimization
yielding an order-of-magnitude speedup must target these innermost
loops.

## 2. Optimization Roadmap

We propose a prioritized roadmap of optimizations to achieve up to
**100× speedup** (targeting 1000+ games/hour) while preserving physics
accuracy and determinism. Each item is evaluated for potential speedup,
implementation complexity, and risk to accuracy:

- **(1) Faster Integration Algorithms -- *Adaptive/Approximate RK4*** --
  *Potential:* **\~2×** speedup per trajectory. *Complexity:*
  **Medium.** *Accuracy risk:* **Low-Med (configurable).** The RK4
  integrator currently uses a fixed 1ms step for high accuracy. We can
  introduce **adaptive time-stepping** (larger dt when forces are small,
  smaller dt when forces change rapidly) to reduce the number of
  steps[\[11\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,lookup%20tables%20for%20common%20scenarios).
  Another approach is offering a **lower-order integrator** (Euler or
  Midpoint) for non-critical
  simulations[\[12\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,lookup%20tables%20for%20common%20scenarios).
  For example, an Euler integration mode could run \~2× faster with
  slight accuracy loss. These would be optional "fast physics" modes --
  user-configurable to ensure accuracy is preserved when needed. Risk to
  determinism is low as long as we use a fixed algorithm per run;
  accuracy impact can be kept under 5% (we'll validate this against
  known trajectories).

- **(2)** Increase Time Step (Ultra-Fast Mode) **-- *Potential:*** \~5×
  **(in addition to fast_mode). *Complexity:*** Low. ***Accuracy
  risk:*** Medium (\~5%). **The engine already has a** "fast_mode"
  **doubling dt from 1ms to 2ms for \~2× speedup with \<1%
  error[\[13\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=2.%20%2A%2AFast%20Mode%2A%2A%20%28%60fast_trajectory.py%60%29%20,accuracy%20loss)[\[14\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,Orchestrates%20integration).
  We can extend this to an** "ultra_fast_mode" **with 5ms or 10ms steps
  for bulk
  simulations[\[15\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md#L95-L101).
  A 10ms step (10× larger) could yield \~10× speedup in the integrator,
  at the cost of a few percent accuracy loss in flight metrics. This is
  acceptable for large Monte Carlo runs (the prompt explicitly allows
  \<5% accuracy
  reduction[\[16\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Acceptable%20Tradeoffs)).
  Implementation is straightforward: expose a setting to use**
  `DT_ULTRA_FAST = 0.01`
  **s[\[15\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md#L95-L101),
  and ensure the physics engine can handle the larger step (perhaps
  switching to a simpler integration like Euler to avoid RK4 instability
  at huge dt). This mode would dramatically speed up thousand-game
  simulations (e.g.** Ultra-Fast Mode\*\* is noted as a 5-10× speed
  boost in
  docs[\[17\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L49-L57)).
  Accuracy risk is contained by using it only for bulk stats runs, not
  for precise analysis.

- **(3) Optimize Numba JIT & Parallelism** -- *Potential:* **\~2-3×**
  per trajectory (with multi-core). *Complexity:* **Medium.** *Accuracy
  risk:* **None.** We should ensure we are extracting maximum
  performance from Numba. First, enable **multithreading within Numba**
  for independent operations. For example, use `@njit(parallel=True)`
  and `prange` to parallelize loops over **multiple trajectories**
  computed in
  batch[\[18\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,parallel%20utilization)[\[19\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,being%20properly%20utilized%20across%20runs).
  A concrete plan: create a batch integrator function that takes an
  array of initial states and performs integration on each in parallel
  threads. Since Numba-compiled code releases the GIL and can utilize
  multiple cores, we could see near-linear speedups with core count.
  This would allow a single process to simulate, say, 8 trajectories
  concurrently on an 8-core CPU (instead of relying only on
  multiprocessing at the game level). Additionally, audit Numba usage:
  ensure all hot functions are annotated with `@njit(cache=True)` (which
  they are for integrator and
  forces[\[20\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L22-L29)[\[21\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L26-L33)),
  and that no inadvertent Python-mode fallbacks occur. We can check for
  any Numba warnings about falling back to object mode. One area to
  exploit is Numba's support for **SIMD vectorization** -- e.g., we
  might rewrite some force calculations to use NumPy ufuncs or Numba's
  `np.dot` which can auto-vectorize. Another idea is using Numba's
  **parallel vectorization for the force loop**: the four RK4 sub-steps
  are independent force evaluations -- these could be parallelized
  (though the overhead may outweigh benefits with only 4 tasks).
  Overall, better leveraging Numba's parallel capabilities can yield a
  further 2-3× on top of single-thread performance. Complexity is
  moderate (requires careful refactoring), but accuracy is unaffected
  (same computations, just in parallel).

- **(4)** Memory & Object Pooling Integration **-- *Potential:***
  \~1.5-2× **speedup (global), mainly by cutting 15-25% memory
  overhead[\[22\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L20-L28).
  *Complexity:*** Low-Med. ***Accuracy risk:*** None. **A**
  TrajectoryBuffer **and other pooling utilities have been implemented
  in** `performance.py` **but are not fully
  utilized[\[23\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=5.%20%2A%2APerformance%20Utilities%2A%2A%20%28%60performance.py%60%29%20,UltraFastMode%20with%20aggressive%20approximations)[\[24\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,Working%20but%20has%20overhead).
  We should** integrate these pools into the simulation loop **to avoid
  constant allocation. For example, modify** `integrate_trajectory_jit`
  **to accept pre-allocated arrays for** `times`**,** `positions`**,
  and** `velocities` **instead of allocating new ones every
  time[\[25\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L156-L163).
  We can maintain a pool of, say, 10 reusable trajectory buffers (each
  big enough for max steps \~15000). Before simulating a trajectory,
  acquire a free buffer, and fill it in the JIT integrator (we can write
  a new Numba function** `integrate_trajectory_buffered` **that takes an
  output buffer) -- this avoids creating new numpy arrays for every ball
  in play. After simulation, release the buffer for reuse. Likewise,
  utilize** `ResultObjectPool` **for frequently created
  dicts[\[26\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L94-L103)[\[27\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L107-L115):
  at-bat results, pitch dictionaries, etc. Instead of allocating a new
  Python dict each time, fetch one from the pool and reset it. This will
  reduce Python GC pressure significantly (object pooling can cut GC
  overhead by** 60-80%\*\* as
  noted[\[28\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L34-L42)).
  These changes are relatively low complexity (mostly plumbing to use
  the already-written pools) and carry no accuracy risk at all. We
  anticipate overall throughput improvement of 1.5× or more in scenarios
  with many trajectories/pitches due to smoother memory management.

- **(5)** Lookup Tables & Caching **-- *Potential:*** \~1.2-1.5× **per
  trajectory. *Complexity:*** Medium. ***Accuracy risk:*** Low. **The
  codebase includes facilities for** caching repeated calculations **--
  we should exploit them. Specifically,** `OptimizedAerodynamicForces`
  **provides precomputed drag/lift lookup tables for common velocity and
  spin
  values[\[29\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md#L80-L89)[\[30\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L38-L46).
  We can enable a mode where the aerodynamic force is obtained via fast
  table interpolation instead of computing all physics from scratch each
  step. For example, divide velocity magnitude and spin RPM into bins
  (as done in** `cached_aerodynamic_params` **and**
  `OptimizedAerodynamicForces`**) and store the force results for those
  bins[\[31\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L366-L375)[\[32\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L384-L392).
  Then, during integration, instead of calling the full**
  `_calculate_spin_adjusted_cd_fast` **each time, we do a quick table
  lookup. This can accelerate force calculations by**
  3-5×**[\[30\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L38-L46).
  The trade-off is a tiny loss of accuracy due to interpolation;
  however, if tables are fine-grained (e.g. velocity to 0.5 m/s, spin to
  50 RPM), error will be negligible. Another caching opportunity: use
  the** `ForceCalculationCache` *(spatial hash) for repeated force
  evaluations on very similar*
  states[\[33\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L236-L244)[\[34\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L269-L278).
  Since consecutive integration steps have only small changes in
  velocity, we can cache the last computed force for a given velocity
  vector (within a tolerance). A lookup before computing forces could
  skip \~15-25% of computations on trajectories with predictable flight
  paths[\[35\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L240-L248).
  Complexity here is moderate -- we'd need to integrate the cache check
  inside the Numba loop, which is tricky because the current cache is a
  Python class. Alternatively, we could implement a simpler caching
  directly in Numba (e.g., memoize the last result). Because the
  potential speedup is somewhat scenario-dependent (more helpful when
  many trajectories have overlapping conditions), we rank this after the
  bigger wins above. The impact on accuracy is minimal if the cache
  tolerance is tight.

- **(6)** Parallel Simulation Refinement **-- *Potential:*** \~1.5×
  **faster multi-game scaling. *Complexity:*** Low. ***Accuracy risk:***
  None. **The existing multiprocessing approach
  (**`ParallelGameSimulator`**) already yields \~5-6× on 8
  cores[\[36\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/PERFORMANCE_GUIDE.md#L133-L141),
  but it has overheads (process spawn, data serialization) and uneven
  load
  distribution[\[37\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Current%20parallel%20implementation%20%28,bats).
  Two improvements: (a) Use a** thread-based pool **instead of
  processes. Since our heavy computations are in Numba (which releases
  GIL), we can use Python threads to avoid multiprocessing overhead. A**
  `ThreadPoolExecutor` **with 8 threads could run 8 games concurrently
  without needing to pickle game states. This will eliminate the 20-30%
  overhead observed with process-based parallelism. We must confirm
  Numba functions truly run outside the GIL -- in tests this should
  hold, as they are machine code. (b) Implement** dynamic load
  balancing\*\*: instead of dividing games evenly among processes at
  start, feed games to workers on the fly. This prevents one worker from
  sitting idle while another finishes a long extra-innings game.
  Python's `concurrent.futures` or joblib can handle a dynamic task
  queue easily. With these tweaks, we aim to approach linear scaling
  across cores (e.g. 8 cores → \~7.5-8× speedup, instead of 6×). This is
  a low-risk, low-complexity change, mostly reusing Python's concurrency
  libraries. Determinism can be preserved by seeding each game's RNG
  independently (so thread scheduling doesn't affect outcomes).

- **(7)** Data Structure & Algorithm Tweaks **-- *Potential:*** \~1.2×
  **in logic-heavy portions. *Complexity:*** Low. ***Risk:*** None. **We
  can make a series of micro-optimizations in the Python-level code:
  use** `__slots__` **in frequently instantiated classes (like**
  `AtBatResult`**,** `PitchResult`**) to avoid dictionary overhead for
  attributes[\[38\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,optimal%20for%20the%20access%20patterns).
  Use** enums or integer codes **for outcomes instead of strings for
  quicker comparisons (currently strings like** `"strikeout"` **are used
  in logic checks, which are slower and create temporary strings). For
  example, define an** `Outcome` **Enum and use** `Outcome.STRIKEOUT`
  **internally. Likewise, reduce usage of Python dictionaries for
  lookups in hot paths -- e.g., the pitch type definitions could be
  stored in a list or array rather than a dict keyed by name. Another
  target: the** fielder and baserunner simulation\*\* algorithms (in
  `fielding.py` and `baserunning.py`). These are less critical to total
  runtime, but they involve complex logic and physics for multiple
  agents. We should examine if these can be simplified or partially
  vectorized. For instance, if multiple fielders are chasing a ball, we
  could simulate their routes in parallel (each fielder's path
  integration could run in its own thread, or via Numba parallel loop).
  This would speed up play resolution in balls in play. These
  data-structure changes and minor algorithm tweaks have relatively
  small individual impact, but together they contribute to reaching the
  last mile of performance gains once major bottlenecks are addressed.
  They also carry no risk to correctness.

- **(8)** Native Code Extensions (C/C++/Rust) **-- *Potential:*** \~2-3×
  **further on physics hotpaths. *Complexity:*** High. ***Risk:*** Low
  (if done carefully). **After exhausting Python/Numba-level
  optimizations, we can consider** rewriting critical components in a
  low-level language **for extra speed. The prime candidate is the RK4
  integration loop and force calculation. While Numba is very fast, a
  handcrafted C++ implementation might allow finer control over memory
  (e.g., stack-allocating small arrays, using SIMD intrinsics, or
  parallelizing with OpenMP). We could write a C extension or use Cython
  to translate Python/NumPy code to
  C[\[39\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,rewritten%20in%20a%20faster%20language).
  Alternatively, use** Rust via PyO3\*\* for safety and
  performance[\[40\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,via%20PyO3%20for%20critical%20sections).
  For instance, a Rust function could integrate a trajectory using
  explicit loops and maybe leverage Rayon (data parallelism) for
  multiple trajectories. The expected gain isn't huge (Numba already
  gives near C performance); however, we might squeeze out another 2× by
  micro-optimizations (e.g., using single-precision floats, or more
  aggressive inlining). We also get more freedom to multi-thread
  internally (bypassing Python entirely). Complexity is high since this
  involves maintaining separate compiled code and ensuring it interfaces
  correctly with Python structures. Accuracy risk is low as long as the
  algorithm is the same; determinism would need careful consideration of
  floating-point differences (different compilers may produce slight
  variance, but likely within acceptable tolerance). This step is more
  of a "stretch goal" if we still need extra speed after all CPU-side
  Python optimizations.

- **(9)** GPU Offloading (Future Phase) **-- *Potential:*** 10-50× **for
  massive batch jobs. *Complexity:*** High. ***Risk:*** Medium
  (architectural changes).\*\* (We note this for completeness, though
  per instructions we won't implement GPU in this phase.) The repository
  has a CuPy-based prototype for batch trajectory
  simulation[\[41\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,game%20simulations).
  In the future, integrating GPU acceleration could provide one to two
  orders of magnitude speedup for very large simulations (e.g., 10,000+
  trajectories processed in parallel on GPU
  cores)[\[42\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/PERFORMANCE_GUIDE.md#L194-L202).
  Achieving this within the game loop would require significant
  architectural refactoring: we'd need to collect many trajectories
  (pitches or batted balls) and send them to the GPU in batches, then
  synchronize results. This is likely a Phase 2 effort after optimizing
  CPU. The roadmap would involve designing an async batch system (to
  batch up trajectories each frame or inning). The risk is the added
  complexity and ensuring identical physics results (floating-point on
  GPU, nondeterministic thread scheduling could affect determinism
  slightly). Given the scope, we mark this as a later project once CPU
  performance plateaus.

**Prioritization:** Start with the lowest-hanging, highest-impact items:
increasing the time step (fast/ultra-fast modes) and integrating the
existing pooling/lookup optimizations (which are largely
implementation-ready and just need integration). These yield immediate
large gains (5-10× combined) with minimal risk. In parallel, improve
multi-core utilization via better parallelism (threads, prange) to
multiply those gains across CPU cores. Finally, consider the more
complex native-code route if needed to hit the extreme stretch goals
(\<1 second per game). All the while, maintain accuracy by validating
against the physics tests at each step.

## 3. Architectural Recommendations

To truly scale to **100× throughput**, we may need deeper architectural
changes in how the simulation is structured. Here we outline
larger-scale modifications to the engine's design focusing on batch
processing, parallelism, and memory management -- all on the CPU:

- **Batch Processing Architecture:** The current design simulates one
  trajectory at a time (per process or thread). A major architectural
  improvement is to enable **batch trajectory simulation** -- processing
  many independent trajectories in a vectorized or SIMD manner.
  Conceptually, we could restructure the simulation loop to **collect
  similar tasks together** and execute them in bulk. For example,
  consider a half-inning: rather than simulating each pitch
  sequentially, gather all pitch trajectories that will be thrown in
  that half-inning and integrate them as a batch. Concretely, we could
  maintain an array of state vectors for all pitches in flight and
  update them together. The existing GPU stub already points in this
  direction (batch
  integration)[\[43\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Currently%2C%20each%20trajectory%20is%20computed,possible%2C%20but%20it%27s%20not%20integrated).
  On CPU, we can mimic this by using NumPy to operate on arrays of
  states (leveraging vectorized operations that use SIMD under the
  hood). Another scenario is batching all **batted ball flights** in a
  round of batting practice or bulk analysis -- the `BulkAtBatSimulator`
  could spawn 100 batted-ball trajectories at once and step them in
  lockstep if using a fixed duration. This requires that trajectories
  run for roughly the same number of steps (we can pad shorter ones or
  cut off longer ones at batch boundaries). While in a live game pitches
  happen sequentially, for simulation purposes we have flexibility to
  process things out of chronological order as long as results are
  eventually applied in order. An architectural shift could be to
  implement a **discrete-event simulation** timeline where multiple
  events (pitches, hits) are advanced simultaneously in time slices.
  This way, the physics engine can update all objects (ball, players) in
  one vectorized pass per millisecond tick. The challenge is that
  baseball events are sequential by nature, but for *Monte Carlo
  workloads* (thousands of independent games) this is more
  straightforward -- we *can* simulate many games in lockstep (each
  game's first pitch together, then each game's second pitch, etc.).
  This is effectively what a GPU approach would do, and we can approach
  it on CPU by organizing our loops accordingly. In summary, the
  architecture should introduce **batch simulation modes** at various
  levels: batch of trajectories (within one at-bat if possible), batch
  of at-bats (as BulkSimulator does, but more vectorized), and batch of
  games (multi-threaded or multi-process). The code might have separate
  pathways (classes or functions) for bulk mode vs single mode, as it
  does now with `BulkAtBatSimulator`, but these can be expanded and
  better integrated.

- **Enhanced Parallelism Within Games:** Currently, parallelism is only
  exploited across games, not inside a single game (each game simulation
  is single-threaded). We can identify **independent tasks within a
  game** to parallelize. Some opportunities:

- **Fielding and Baserunning:** When a ball is put into play, multiple
  fielders and runners move simultaneously. We can simulate each
  fielder's route to the ball in a separate thread (or in parallel using
  Numba's prange). For instance, computing the paths of the outfielders,
  infielder backups, etc., are independent calculations given the
  batted-ball trajectory. Similarly, multiple base runners advancing can
  be processed in parallel (each runner's advancement to next base is
  largely independent, only constrained by ordering when two try to
  occupy the same base, which can be handled with locks or
  post-simulation checks). By parallelizing these sub-systems, we
  shorten the wall-clock time of a play.

- **Pitch + Swing decision overlap:** Typically we simulate the pitch
  trajectory fully, then decide swing and simulate contact. But we could
  overlap computations: use a predictor for swing timing in parallel
  with late pitch flight calculation. However, this might complicate
  determinism and isn't as clear-cut as other tasks.

- **Thread-Based Game Simulation:** As mentioned earlier, using threads
  for running multiple games (or multiple at-bats) within one Python
  process can reduce overhead. The architecture could use a **thread
  pool** that takes simulation tasks (games or even half-innings) and
  executes them concurrently. The coordination overhead is lower than
  multiprocessing, and shared read-only data (like player attributes,
  lookup tables) need not be duplicated across processes.

- We must ensure thread safety of global data (the engine seems to avoid
  global state except for caches/pools which we can manage with
  thread-local instances or locks). Given that deterministic random
  number generation is required, we will give each thread its own RNG
  seed/stream to avoid races producing nondeterministic order of random
  draws.

- **Memory Management & Data Locality:** Architecturally, we want to
  design for **cache-efficient data access**. This may involve changing
  how data is laid out in memory. For example, instead of storing
  trajectory state as separate arrays (times, positions, velocities), we
  could use a **structure-of-arrays (SoA)** or even a plain C struct for
  the state that is used in the integrator. The current integrator
  writes to three arrays (`times`, `positions`, `velocities`) which are
  likely contiguous in memory already for each array. Using them is
  fine, but we should avoid reallocation. The TrajectoryBuffer approach
  centralizes these arrays in memory to improve cache
  reuse[\[44\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md#L41-L49).
  We should also consider using **single precision (float32)** for
  trajectories when in fast/ultra-fast modes to cut memory bandwidth in
  half -- this doubles cache capacity for our arrays and can improve
  vectorization speed (at the cost of minor precision loss, which should
  be within tolerance). We might introduce a flag to run physics in
  32-bit mode for bulk sims. Another memory-related architectural idea:
  **pre-allocate** all needed memory for a simulation up-front. For
  instance, if we know we will simulate N games with M pitches each,
  allocate a big block for all trajectories. This is tricky due to
  variability, but even per-game we can allocate the *maximum* array
  sizes and then reuse. The key is to avoid mid-simulation malloc/free
  as much as possible -- allocate once, reuse everywhere. This approach
  can reduce memory usage by 90% in large simulations according to our
  docs (streaming results instead of storing
  all)[\[45\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L140-L149).

- **Determinism and Reproducibility:** As we refactor for parallelism
  and batch processing, we must preserve the guarantee that given the
  same random seed, the simulation results are
  identical[\[46\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Constraints%20%26%20Requirements).
  Architecturally, this means any parallel or batch execution must be
  carefully choreographed. For example, if we simulate games in parallel
  threads, the order in which random numbers are drawn could change
  unless each game has its own RNG. We should update the architecture to
  include a **RandomNumberGenerator object per game/at-bat** that can be
  seeded and advanced independently. Likewise, if we batch trajectories,
  we need to ensure that combining them doesn't inadvertently change
  outcomes (one way to do this is to ensure the operations are
  commutative or at least that we process in a fixed sorted order of,
  say, game IDs or trajectory IDs in batch so results don't depend on
  scheduling). Another tool is to incorporate a **deterministic mode**
  where we disable any nondeterministic thread scheduling -- for
  instance, using a single thread or a barrier to enforce step-by-step
  synchronization across threads (useful only for debugging
  determinism).

- **Extensibility for GPU/Distributed:** While focusing on CPU, it's
  wise to make architectural changes that also pave the way for future
  GPU or distributed computing integration. For GPU, this means
  designing interfaces where we can **swap out the physics engine**. For
  instance, a `TrajectoryIntegrator` interface could have two
  implementations: CPU (Numba/C) and GPU (CuPy). The game logic would
  treat them interchangeably. We should refactor the code to isolate
  physics calculation from game logic. Right now, `AtBatSimulator`
  directly calls `BattedBallSimulator.simulate_batted_ball` which
  internally picks CPU or GPU based on a flag. Instead, architecture can
  follow a **strategy pattern**: e.g., a `TrajectorySimulationStrategy`
  that can be set to "CPU-fast", "CPU-ultrafast", or "GPU". This
  encapsulation will simplify integrating a GPU later because the game
  doesn't need to know the details -- it just calls "simulate
  trajectory" and the chosen strategy handles it. For distributed
  computing (simulating games on multiple machines or cloud), we
  likewise want a clean separation where a higher-level script can farm
  out `GameSimulator` calls to different processes or nodes. Ensuring
  the simulation is **stateless or easy to serialize** is important here
  (the fewer global states, the easier to send a game to a worker).

In summary, the architectural vision is to transition from a purely
sequential per-game simulation to a more **data-parallel, bulk-oriented
engine**. By processing many independent events together and using all
available hardware concurrency, we maximize CPU utilization. Memory
pools and caches become first-class citizens in this design, ensuring
that scaling up the number of simulations doesn't lead to memory bloat
or thrash. These changes will enable not just 100× speedup on a single
machine, but also set the stage for even larger-scale simulations (GPU
or cluster-based) in the future, all while maintaining the integrity and
realism of the simulation.

## 4. Code-Level Recommendations & Examples

Here we provide targeted code-level changes for the highest priority
optimizations. For each, we show a **before** and **after** snippet and
explain how to verify correctness:

**A. Integrator Loop with Preallocated Buffers** -- *Goal:* eliminate
per-trajectory array allocations.

- **Before:** In `integrator.py`, the function
  `integrate_trajectory_jit` allocates new NumPy arrays for `times`,
  `positions`, and `velocities` on each
  call[\[47\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L156-L164).
  It returns trimmed copies of these arrays at the
  end[\[48\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L206-L209).
  This causes a lot of heap allocation and garbage collection.

<!-- -->

    @njit(cache=True)
    def integrate_trajectory_jit(initial_state, dt, max_time, ground_level, force_func, *force_args):
        # Pre-allocate arrays for the maximum possible steps
        max_steps = int(max_time / dt) + 10
        times = np.zeros(max_steps)
        positions = np.zeros((max_steps, 3))
        velocities = np.zeros((max_steps, 3))
        ...
        while current_time < max_time and ...:
            current_state = _step_rk4_jit(...)
            # store results in arrays
            times[step_count] = current_time
            positions[step_count] = current_state[:3]
            velocities[step_count] = current_state[3:]
            if hit_ground: break
        return times, positions, velocities, step_count + 1

\- **After:** We introduce a new function
`integrate_trajectory_buffered` that **accepts buffers** as arguments,
drawn from our `TrajectoryBuffer`
pool[\[49\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L43-L51).
It no longer allocates internally. For example:

    @njit(cache=True)
    def integrate_trajectory_buffered(initial_state, dt, max_time, ground_level,
                                      force_func, force_args,
                                      times_buf, pos_buf, vel_buf):
        step_count = 0
        current_time = 0.0
        current_state = initial_state.copy()
        times_buf[0] = 0.0
        pos_buf[0] = current_state[:3]
        vel_buf[0] = current_state[3:]
        while current_time < max_time and step_count < len(times_buf) - 1:
            current_state = _step_rk4_jit(current_state, dt, force_func, *force_args)
            current_time += dt
            step_count += 1
            times_buf[step_count] = current_time
            pos_buf[step_count] = current_state[:3]
            vel_buf[step_count] = current_state[3:]
            if current_state[2] <= ground_level:  # ball hit ground
                break
        return step_count

Here, `times_buf, pos_buf, vel_buf` are provided by the caller. We
obtain them from the global `TrajectoryBuffer` via
`buffer_index, times_buf, pos_buf, vel_buf = trajectory_buffer.get_buffer()`[\[50\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L52-L60).
After the function returns a `step_count`, the caller can package the
results (slice the buffers up to `step_count`). The key is no allocation
in the hot loop.

- **Validation:** We must ensure this produces identical trajectories to
  the original. We verify by running the **physics validation tests**
  (`python -m batted_ball.validation`) which compare known trajectories
  (distance, apex, hang time) to expected values. If
  `integrate_trajectory_buffered` is correct, all 7/7 validation tests
  should still
  pass[\[46\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Constraints%20%26%20Requirements).
  We also cross-check that memory usage drops -- using a tool like
  `tracemalloc` or just monitoring `Process.memory_info`, we should see
  far fewer temporary allocations during a batch of trajectories.
  Determinism is inherently preserved (we haven't changed the math, just
  where results are stored).

**B. Object Pooling for Results** -- *Goal:* reuse dicts and other
Python objects to reduce overhead.

- **Before:** Each pitch and at-bat creates new result objects. For
  example, in `AtBatSimulator.simulate_at_bat`, code might collect pitch
  outcomes in a list of dicts:

<!-- -->

    pitches = []
    for pitch_num in range(max_pitches):
        pitch_data = {
            "pitch_type": selected_pitch.name,
            "velocity_release": result.release_speed,
            "pitch_outcome": outcome_str,
            ...
        }
        pitches.append(pitch_data)
        ...
    return AtBatResult(outcome, pitches, count, batted_ball_dict)

Every `pitch_data` and the `batted_ball_result` (if any) are fresh
dictionaries. This leads to a lot of allocations and garbage to collect
in a 9-inning game (potentially thousands of dicts).

- **After:** We utilize `ResultObjectPool` from `performance.py` to
  recycle these
  dictionaries[\[51\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L101-L109)[\[52\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L120-L128).
  The pool is initialized globally (e.g.,
  `result_pool = get_result_pool()` returning a singleton pool of
  pre-made dicts). The code becomes:

<!-- -->

    pitches = []
    for pitch_num in range(max_pitches):
        pitch_data = result_pool.get_pitch_data()  # reuse a dict
        pitch_data["pitch_type"] = selected_pitch.name
        pitch_data["velocity_release"] = result.release_speed
        pitch_data["pitch_outcome"] = outcome_str
        ...
        pitches.append(pitch_data)
        if outcome_str in ("ball_in_play", "contact"):
            break  # etc.
    # after at-bat:
    atbat_result = result_pool.get_result_dict()
    atbat_result["outcome"] = final_outcome
    atbat_result["pitches"] = pitches
    atbat_result["final_count"] = (balls, strikes)
    if batted_ball_dict:
        atbat_result["batted_ball"] = batted_ball_dict
    # return atbat_result as a regular dict or wrap in AtBatResult

We populate a dict from the pool instead of constructing one. When the
at-bat is done, we could either return this dict directly (since it now
contains the needed info) or use it to construct an `AtBatResult`
object. We then **return these objects to the pool** when no longer
needed: e.g., after each game or each half-inning, iterate through
`pitches` list and call `result_pool.return_pitch_data(dict)` to put
them
back[\[53\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L126-L134).
For the main result, `return_result_dict` can recycle
it[\[54\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L113-L119).
We have to decide on a policy: maybe recycle at the end of each at-bat
(but then the calling code must not use it afterwards). It may be
simpler to recycle at end of each game.

- **Validation:** We need to ensure we don't accidentally reuse an
  object while it's still in use (that would corrupt data). A good
  practice is to only release to pool after we're completely done with
  the object. In testing, we run a full game simulation and verify that
  all outcome data and statistics are correct (no missing or overwritten
  values). The regression tests on game stats (comparing to MLB
  averages) in `TESTING_STRATEGY.md` should still pass -- indicating
  that the use of pooled objects didn't alter any logic. Memory
  profiling during a 162-game simulation should show a **sharp reduction
  in peak memory** (as evidenced by the documentation: e.g., 100k
  at-bats dropping from 3.2 GB to 180 MB with
  streaming/pooling[\[45\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L140-L149)).
  Our correctness check is that game logs and summary outputs remain
  identical before vs. after (we can do a diff of play-by-play outputs
  with the same RNG seed to ensure nothing was lost or mixed up in the
  pooling process).

**C. Cached Aerodynamics via Lookup Table** -- *Goal:* avoid recomputing
drag/lift coefficients every step.

- **Before:** The force calculation for each step does a fair amount of
  work, including conditional logic for Reynolds number regimes and spin
  drag
  adjustments[\[55\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L120-L129)[\[56\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L126-L134).
  For example, computing the effective drag coefficient involves
  checking the Reynolds number range and adjusting for spin and spin
  axis tilt each
  time[\[57\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L226-L235)[\[58\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L229-L238).
  There is repetition especially when conditions don't change
  drastically between steps.

- **After:** We use the `OptimizedAerodynamicForces` lookup tables as a
  fast path. This class precomputes forces on a grid of velocities and
  spins[\[59\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L423-L431).
  We instantiate it once (e.g.,
  `opt_aero = OptimizedAerodynamicForces()`) at the start of simulation
  or for bulk runs. It might build tables like
  `drag_lookup[velocity, spin]` and `magnus_lookup[velocity, spin]`. In
  the integration loop, we replace the on-the-fly calculation with a
  lookup + interpolation. For instance:

<!-- -->

    # Pseudocode inside aerodynamic_force_tuple or its replacement:
    if use_lookup_table:
        # velocity magnitude in m/s, spin in RPM
        v = np.linalg.norm(velocity)
        spin = spin_rate_rpm
        F_drag, F_magnus = opt_aero.lookup_force(v, spin)  # fast interpolation
        # Need force direction: for drag, direction = -v_unit; for magnus, perpendicular to spin axis and velocity
        v_unit = velocity / (v + 1e-8)
        F_drag_vec = F_drag * -v_unit
        if spin > 1 and np.linalg.norm(spin_axis) > 1e-6:
            # use precomputed Magnus direction unit vector if available
            force_dir = np.cross(v_unit, spin_axis_unit) 
            F_magnus_vec = F_magnus * force_dir
        else:
            F_magnus_vec = np.zeros(3)
        total_force = F_drag_vec + F_magnus_vec
        return total_force[0], total_force[1], total_force[2]
    else:
        # fall back to exact calculation (current implementation)
        return aerodynamic_force_tuple(position, velocity, spin_axis_x, ..., cross_area)

In this pseudo-code, `opt_aero.lookup_force(v, spin)` would perform a
bilinear interpolation between precomputed grid values (this function
would be implemented inside `OptimizedAerodynamicForces`). If needed, we
still compute direction unit vectors for drag and Magnus (since the
lookup likely stores just magnitudes). We could also store unit
direction of Magnus for a representative axis alignment, but since spin
axis can vary in orientation, probably better to compute direction each
step as we do now (that cost is small relative to the coefficient
computation we saved).

- **Validation:** We will compare the output of the lookup approach to
  the exact calculation to ensure error is within tolerance. We can do
  this by instrumenting a test that runs a range of trajectories (vary
  exit velocity, spin) with both exact and lookup forces and measures
  differences in flight outcomes (distance, hang time). We expect \<2%
  difference for medium accuracy
  settings[\[60\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/CPU_OPTIMIZATION_GUIDE.md#L99-L108).
  We also run the full validation suite to ensure no individual test
  (which are quite strict on physics) fails. If any do, we may refine
  the table resolution or revert to exact calc in edge cases. For
  determinism, since the lookup table is fixed and interpolation is
  deterministic, runs with the same seed should still produce identical
  results (with the caveat that floating point interpolation might
  introduce tiny rounding differences -- but these should not accumulate
  significantly over a flight). We also monitor performance: using the
  lookup should **reduce CPU time in** `aerodynamic_force_tuple`
  **dramatically**, which we confirm via profiling a single trajectory
  -- we expect to see a drop in the fraction of time spent in
  `_calculate_spin_adjusted_cd_fast` and related routines when the table
  is on.

**D. Multi-Threaded Game Simulation** -- *Goal:* use threads instead of
processes for parallel games.

- **Before:** The `ParallelGameSimulator` uses Python's
  `multiprocessing` to fork separate processes and simulate different
  games in
  each[\[61\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=3.%20,game%20simulations)[\[62\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,Available).
  For example, to simulate 100 games on 8 cores, it spins up 8 worker
  processes, each running \~12-13 games. The overhead includes start-up
  time and pickling of teams/players to child processes, plus result
  aggregation via pipes.

- **After:** We refactor `ParallelGameSimulator` (or create a new
  parallel runner) to use `concurrent.futures.ThreadPoolExecutor`. For
  instance:

<!-- -->

    import concurrent.futures
    class ParallelGameSimulator:
        def __init__(self, num_workers=None, verbose=False):
            ...
            self.num_workers = num_workers or os.cpu_count()
            self.verbose = verbose
        def simulate_games(self, num_games, *args, **kwargs):
            results = []
            def simulate_one(_):
                sim = GameSimulator(self.away_team, self.home_team, verbose=False)
                return sim.simulate_game()  # returns GameState or summary
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as executor:
                for game_result in executor.map(simulate_one, range(num_games)):
                    results.append(game_result)
                    if self.verbose:
                        print(f"Game {len(results)}/{num_games} complete")
            return results

In this pseudo-code, we simply spawn threads to run `simulate_game`
concurrently. We pass in any required state (teams, etc.) from the
enclosing scope. Since `GameSimulator` likely isn't thread-safe if
sharing state, we ensure each thread constructs its own `GameSimulator`
and associated objects (which is fine -- each game is independent).
There's no pickling here; memory for players/teams is shared read-only
among threads.

- **Validation:** We run, say, 16 games in parallel with both the old
  process-based and new thread-based approach to ensure final outcomes
  are identical and performance is improved. Identical outcomes require
  careful seeding: if we want reproducibility, we may need to assign a
  deterministic subset of RNG sequences to each thread. One approach is
  to split the global RNG sequence so that game 1 draws numbers 1--N,
  game 2 draws N+1--2N, etc. In practice, we can seed each
  `GameSimulator` with `base_seed + game_index` to keep them separate.
  Then sorting the results by game_index should yield the same results
  as sequential simulation with incremented seeds. We confirm
  determinism by comparing a threaded run to a single-thread run with
  the same seeds. For performance, we should see near-linear scaling. We
  can measure total time for, say, 32 games on 8 cores -- the thread
  version should approach the theoretical minimum (4x faster on 8 cores
  if CPU-bound, whereas the process version might only be \~3x due to
  overhead). If there are any GIL contention issues (which we do not
  expect, since heavy parts are Numba'd), we might observe
  less-than-ideal scaling -- in which case we'd investigate if any
  Python-side work can be further reduced.

*Note:* Many of these code changes (A--D) can be introduced behind
configuration flags. For example, we could add flags like
`use_buffered_integrator`, `use_object_pool`, `use_force_lookup`, etc.,
to easily toggle and test them. This is helpful for validation -- we can
run the simulation with new code vs old code side-by-side to ensure
results match.

Each code-level optimization should be accompanied by targeted tests: -
Unit tests for the new integrator (compare buffered vs original on a
known trajectory). - Unit tests for the object pool (ensure no data
persists incorrectly between uses). - Accuracy tests for the lookup
table (comparing forces). - Multithreading tests to ensure no race
conditions (perhaps run 100 games in parallel twice and ensure the
aggregated stats are the same each time).

By implementing these code changes iteratively and testing after each,
we build confidence that we haven't broken the physics or determinism
while drastically improving performance.

## 5. Performance Testing Plan

To verify and quantify the improvements -- and ensure no regressions in
accuracy -- we outline a comprehensive performance testing strategy:

**Benchmark Suite:** We will create a set of benchmarking scripts to
measure simulation speed under various configurations. For example: -
`benchmark_single_game.py`**:** Runs a single 9-inning game simulation
(with a fixed seed) and reports the execution time. This is useful for
low-level profiling and to measure improvements in the integrator and
physics calculations. We'll run this under different modes (normal vs
fast vs ultra-fast) and compare times. Our target is to reduce the
single-game time from \~30-60s down to \~3-5s or
less[\[63\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,5%2C000%2B). -
`benchmark_bulk_games.py`**:** Simulates a large number of games and
measures throughput (games/hour). We can use the existing
`ParallelGameSimulator` or BulkSimulator for this. For example, simulate
162 games (one season) and confirm it completes in under 5-10 minutes
(the
target)[\[63\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,5%2C000%2B).
We'll also test extreme cases like 1000 games with multi-threading to
ensure scalability and that resource usage (CPU/RAM) is within limits. -
**Micro-benchmarks:** We include small tests focusing on specific
components: e.g., **integrator micro-benchmark** -- simulate a single
trajectory 1000 times and report average time per trajectory (to see
improvements in RK4 loop). Or **force calc micro-benchmark** -- call the
aerodynamic force function with typical inputs 1e6 times and measure
speed (to validate caching/lookup improvements). - **Automated
comparison:** As part of the suite, we'll have a script that runs a
variety of simulation sizes (e.g., 100 at-bats, 1000 at-bats, 10000
at-bats) and prints the achieved at-bats per second or games per hour.
The current expected scaling from docs is: \~8 at-bats/sec single,
\~20/sec with basic bulk, \~50/sec with optimized bulk, \~100+ with
ultra-fast[\[64\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/CPU_OPTIMIZATION_GUIDE.md#L68-L76).
Our benchmarks will confirm we hit or exceed these numbers.

Each benchmark run will log the configuration (Python version,
NumPy/Numba versions, number of CPU cores, etc.) and the results. We
will track these over time to ensure performance is only moving in one
direction (up!).

**Accuracy Validation:** Maintaining physics realism is paramount, so we
will run the full **validation test suite** after each major change: -
The repository's built-in validation (`batted_ball.validation` module)
includes at least 7 tests covering trajectory physics (e.g., range of a
batted ball, apex height, drag effects, magnus effect). We will run
`python -m batted_ball.validation` and expect "7/7 tests passing" every
time. These tests likely compare simulation outputs to theoretical or
empirical values -- any failure here flags a potential accuracy
regression which we must address before proceeding. - We also use the
**MLB realism checks** (perhaps described in `TESTING_STRATEGY.md` or
similar). This would involve simulating a large number of games and
comparing aggregate statistics (batting averages, home run rates, etc.)
to real MLB
averages[\[65\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Why%20Speed%20Matters).
We'll automate a comparison that ensures differences are within
acceptable ranges (the prompt suggests the engine should produce
realistic stats). For example, if after an optimization we see a jump in
home run distance beyond the expected variance, that's a red flag (maybe
an error in physics). - **Determinism tests:** We will design a test to
run the simulation twice with the same random seed and ensure the
results are byte-for-byte identical. This includes play-by-play sequence
and final outcomes. We can implement this by capturing the random seed
at game start and reproducing it. After any change that could affect
parallel execution or floating-point rounding, run two simulations with
the same seed -- if they diverge, investigate where. A specific
regression test: run a game with a known seed before an optimization and
save all key outputs (e.g., sequence of pitch outcomes, hit distances).
After the optimization, run with the same seed and diff the outputs.
They should match exactly. If not, we have likely broken determinism
(or, if the only differences are extremely tiny floating point
deviations in, say, reported distances, we verify those are within
tolerance). - **Unit tests for new components:** For instance, if we add
a function `lookup_force`, we write unit tests comparing it against the
original force calculation for a range of conditions. If we add a new
integrator mode (e.g., Euler or adaptive RK4), we test that on scenarios
where we know the expected outcome (maybe a simple projectile motion
with no drag -- we know exactly how far it should go, and we verify the
integrator computes that within 5% even in ultra-fast mode).

**Regression Detection:** To ensure future changes do not undermine
performance, we will integrate performance tests into the CI (Continuous
Integration) process if possible: - We will maintain a **baseline
performance profile** (perhaps as JSON or CSV) for key benchmarks
(single game time, 100-game time, etc.). After each code change, a CI
job can run the benchmarks on a standardized environment and compare to
baseline. If there is a significant slowdown (e.g., single game time
increased by \>5%), the CI can flag this as a regression. This prevents
accidental performance degradations (for example, a well-intentioned
refactor that reintroduces a bottleneck). - Similarly, a CI job will run
the validation tests for physics and realism so that any accuracy
regression is caught immediately. This is crucial when multiple
developers are working -- one might focus on speed and inadvertently
push accuracy out of bounds; the tests will catch it. - We will use
tools to monitor performance at a finer granularity too. For instance,
we can include a **cProfile run in CI** for a short simulation and track
the top functions' time. By diffing these profiles over time (there are
tools to compare cProfile stats), we can pinpoint if, say, the
integrator's share of time creeps up unexpectedly (meaning some
optimization got disabled or a new hotspot emerged). - Another aspect of
regression detection is memory and determinism. We plan to use a
long-running stress test (simulate e.g. 10k games in parallel) to ensure
the engine remains stable (no memory leaks, no accumulating error). If
possible, incorporate a memory profiler in CI that runs a large
simulation and ensures memory usage is roughly flat after initial
allocations (our pooling should make it so). Any upward trend might
signal a leak (e.g., not returning objects to pool).

**Progressive Rollout & Comparison:** Rather than flip all optimizations
at once, we will introduce them one by one (possibly behind flags as
mentioned). This allows A/B testing: run one simulation with the flag
on, one with it off, and compare results and timings. For example, run a
batch of games with `use_ultra_fast_mode=True` vs `False` to empirically
verify the accuracy impact is \<5% on aggregate stats (we might simulate
1000 at-bats with each and compare average distance, etc.). By logging
both sets of results, we ensure the trade-off is acceptable.

**Example Performance Test Plan:**

1.  **Baseline Profiling:** Using the provided quick start
    commands[\[66\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,r%20requirements.txt),
    run `cProfile` on a single game (`examples/quick_game_test.py`)
    before changes and save the stats. Visualize a flame graph or
    examine top 20
    functions[\[67\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=%2A%2ASuggested%20approach%2A%2A%3A%20,game%20logic).
    This baseline profile is our reference.
2.  **Implement optimization X** (say, buffered integrator). Run the
    same profile again. Confirm that the total run time dropped and that
    functions related to allocation (e.g., `np.zeros`, `np.concatenate`)
    are reduced in the top 20. Also confirm physics results are
    identical by using the same seed for the game.
3.  **Run automated validation** after each change. E.g., after buffered
    integrator: `batted_ball.validation` (all tests pass), simulate 1000
    at-bats in fast vs buffered mode and compare summary (should be
    nearly identical).
4.  **Incremental benchmarks:** After implementing a batch of
    improvements, run a larger benchmark: e.g.,
    `examples/simulate_db_teams.py` which simulates a series of games
    (the docs mention 162 games in \~15-20 min parallel
    originally[\[68\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,still%20too%20slow%20for%20thousands)).
    Time this before vs after and record the speedup.
5.  **Stress test determinism:** Use a fixed seed and simulate e.g. a
    full season twice with parallel threads. Confirm the aggregate
    results (e.g., final league standings or total runs scored) are
    exactly the same both times.
6.  **Record results and update docs:** We will keep a **performance
    log** -- perhaps update the PERFORMANCE_GUIDE with new metrics
    achieved at each phase. For instance, after all optimizations,
    single-game time \~2 seconds (on our test machine), 162 games in \~2
    minutes parallel -- hitting the stretch
    goal[\[63\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,5%2C000%2B).

By following this testing plan, we ensure that our drive for 100×
speedup does not compromise the fidelity of the simulation. Each
optimization will be validated in isolation and in combination, giving
confidence that the final product is both **fast and accurate**.
Ultimately, we expect to reach the performance targets outlined (1000+
games/hour on an 8-core
CPU)[\[63\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,5%2C000%2B),
while all physics validation tests continue to pass and simulation
outcomes remain realistic and consistent.

------------------------------------------------------------------------

[\[1\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L14-L22)
[\[2\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L14-L19)
[\[3\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L24-L29)
[\[4\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L20-L25)
[\[17\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L49-L57)
[\[22\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L20-L28)
[\[28\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L34-L42)
[\[30\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L38-L46)
[\[45\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md#L140-L149)
PERFORMANCE_OPTIMIZATION_SUMMARY.md

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_OPTIMIZATION_SUMMARY.md>

[\[5\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/game_simulation.py#L523-L531)
game_simulation.py

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/game_simulation.py>

[\[6\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/PERFORMANCE_GUIDE.md#L22-L28)
[\[36\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/PERFORMANCE_GUIDE.md#L133-L141)
[\[42\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/PERFORMANCE_GUIDE.md#L194-L202)
PERFORMANCE_GUIDE.md

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/PERFORMANCE_GUIDE.md>

[\[7\]](https://github.com/jlundgrenedge/baseball/blob/369c45af0ad4e0b892393640131abcc763848ec0/batted_ball/pitch.py#L819-L827)
pitch.py

<https://github.com/jlundgrenedge/baseball/blob/369c45af0ad4e0b892393640131abcc763848ec0/batted_ball/pitch.py>

[\[8\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L88-L97)
[\[10\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L180-L188)
[\[20\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L22-L29)
[\[25\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L156-L163)
[\[47\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L156-L164)
[\[48\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py#L206-L209)
integrator.py

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/integrator.py>

[\[9\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L259-L267)
[\[21\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L26-L33)
[\[55\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L120-L129)
[\[56\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L126-L134)
[\[57\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L226-L235)
[\[58\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py#L229-L238)
aerodynamics.py

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/aerodynamics.py>

[\[11\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,lookup%20tables%20for%20common%20scenarios)
[\[12\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,lookup%20tables%20for%20common%20scenarios)
[\[13\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=2.%20%2A%2AFast%20Mode%2A%2A%20%28%60fast_trajectory.py%60%29%20,accuracy%20loss)
[\[14\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,Orchestrates%20integration)
[\[16\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Acceptable%20Tradeoffs)
[\[18\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,parallel%20utilization)
[\[19\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,being%20properly%20utilized%20across%20runs)
[\[23\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=5.%20%2A%2APerformance%20Utilities%2A%2A%20%28%60performance.py%60%29%20,UltraFastMode%20with%20aggressive%20approximations)
[\[24\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,Working%20but%20has%20overhead)
[\[37\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Current%20parallel%20implementation%20%28,bats)
[\[38\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,optimal%20for%20the%20access%20patterns)
[\[39\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,rewritten%20in%20a%20faster%20language)
[\[40\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,via%20PyO3%20for%20critical%20sections)
[\[41\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,game%20simulations)
[\[43\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Currently%2C%20each%20trajectory%20is%20computed,possible%2C%20but%20it%27s%20not%20integrated)
[\[46\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Constraints%20%26%20Requirements)
[\[61\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=3.%20,game%20simulations)
[\[62\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,Available)
[\[63\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,5%2C000%2B)
[\[65\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=Why%20Speed%20Matters)
[\[66\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,r%20requirements.txt)
[\[67\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=%2A%2ASuggested%20approach%2A%2A%3A%20,game%20logic)
[\[68\]](file://file_00000000b308722f969b9edc9953d1fd#:~:text=,still%20too%20slow%20for%20thousands)
PERFORMANCE_RESEARCH_PROMPT.md

<file://file_00000000b308722f969b9edc9953d1fd>

[\[15\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md#L95-L101)
[\[29\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md#L80-L89)
[\[44\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md#L41-L49)
PERFORMANCE_ANALYSIS.md

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/archive/PERFORMANCE_ANALYSIS.md>

[\[26\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L94-L103)
[\[27\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L107-L115)
[\[31\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L366-L375)
[\[32\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L384-L392)
[\[33\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L236-L244)
[\[34\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L269-L278)
[\[35\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L240-L248)
[\[49\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L43-L51)
[\[50\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L52-L60)
[\[51\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L101-L109)
[\[52\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L120-L128)
[\[53\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L126-L134)
[\[54\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L113-L119)
[\[59\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py#L423-L431)
performance.py

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/batted_ball/performance.py>

[\[60\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/CPU_OPTIMIZATION_GUIDE.md#L99-L108)
[\[64\]](https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/CPU_OPTIMIZATION_GUIDE.md#L68-L76)
CPU_OPTIMIZATION_GUIDE.md

<https://github.com/jlundgrenedge/baseball/blob/97fd7e7d48d040267cd3c9b1749f350c40ba40dc/docs/guides/CPU_OPTIMIZATION_GUIDE.md>
