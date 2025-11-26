# Baseball Simulation Engine - Logging Implementation Analysis

## Executive Summary

The baseball simulation engine has a sophisticated logging infrastructure spanning multiple levels:
1. **Game level**: Full game flow and inning summary
2. **At-bat level**: Pitch sequence and swing/contact decisions
3. **Play level**: Fielding, baserunning, and outcome events
4. **Metrics level**: Comprehensive physics and decision tracking (SimMetricsCollector)

The system supports both **verbose console output** and **optional file logging**, with a new **SimMetricsCollector** system for detailed diagnostic output at configurable debug levels (OFF, BASIC, DETAILED, EXHAUSTIVE).

---

## 1. Current Logging Architecture

### 1.1 Game Level (game_simulation.py)

**Files**: 
- `/home/user/baseball/batted_ball/game_simulation.py` (985 lines)

**Key Components**:
- `GameSimulator.__init__(verbose, log_file, debug_metrics)` - Lines 205-250
  - `verbose`: bool - Controls console output
  - `log_file`: Optional file path for logging
  - `debug_metrics`: int (0-3) - Controls metrics debug level
- `log()` method - Lines 252-258 - Writes to console AND file
- `GameState` dataclass - Lines 42-159 - Tracks game state (score, outs, runners, stats)

**Current Logging Points**:
1. **Game start** (line 273-275): Game header with team names
2. **Inning start** (line 300-303): Inning summary with state
3. **At-bat setup** (line 328-330): Batter vs Pitcher, situation
4. **Strikeout/Walk** (line 415-416, 426-427): Outcome with outs count
5. **Runner advances** (line 435-436): Run scoring from walks
6. **Play execution** (line 597-630): Pitch sequence, play description, physics
7. **Game summary** (line 844-857): Final scores, stats, player performance

**Data Available But Not Logged**:
- Pitcher fatigue/performance trends across innings
- Count progressions and pitch intention vs actual
- Contact quality distribution
- Fielder movement/route efficiency
- Baserunner decision logic (why runners did/didn't advance)

---

### 1.2 At-Bat Level (at_bat.py)

**Files**: 
- `/home/user/baseball/batted_ball/at_bat.py` (957 lines)

**Key Functions**:
- `simulate_at_bat()` - Lines 789-920
  - Pitch selection logic
  - Swing decision logic
  - Contact quality determination
  
**Current Logging Points**:
1. **Pre-pitch** (line 828-832): Count, pitch type, location, velocity
2. **Swing decision** (line 858-859): "Swings..."
3. **Pitch outcome** (line 848-854): Called strike/ball
4. **Contact** (line 885-887): Contact quality, exit velocity, launch angle

**Pitch Selection Logic** (lines 230-312):
- `select_pitch_type()` - Uses arsenal, count, leverage, sequencing
- Weighted selection based on: count, situation, pitcher ahead/behind
- Factors: fastballs in fastball counts, breaking balls when ahead
- Sequencing: Avoids repeating same pitch, encourages set-ups

**Swing Decision Logic** (lines 835-841):
- `Hitter.decide_to_swing()` - Based on:
  - Pitch location (strike zone classification)
  - Ball/strike count (discipline increases with pitcher ahead)
  - Pitch velocity and type
  - Batter discipline attribute

**Contact Quality Model** (lines 861-883):
- Calls `ContactModel.simulate_contact()` if swing connects
- Returns: exit_velocity, launch_angle, distance, hang_time, contact_quality
- Records to metrics collector if enabled

**Data Available But Not Logged**:
- Pitch intention vs actual (why pitcher chose this pitch)
- Swing probability before decision
- Contact quality breakdown (sweet spot % vs off-center)
- Timing error in swing (early/late)
- Expected contact outcome distribution (whiff %, foul %, weak %, etc.)

---

### 1.3 Play Level (play_simulation.py)

**Files**: 
- `/home/user/baseball/batted_ball/play_simulation.py` (primary orchestrator)
- `/home/user/baseball/batted_ball/hit_handler.py` (533 lines)
- `/home/user/baseball/batted_ball/ground_ball_handler.py` (679 lines)
- `/home/user/baseball/batted_ball/fly_ball_handler.py` (1216 lines)
- `/home/user/baseball/batted_ball/baserunning.py` (1020 lines)
- `/home/user/baseball/batted_ball/fielding.py` (1709 lines)

**Play Flow**:
1. Ball lands (analyzed in `play_analyzer.analyze_batted_ball()`)
2. Home run check (fly balls only)
3. Catch attempt (fly/ground balls)
4. Fielding event (throw, relay)
5. Baserunning decisions (advance, hold, slide)
6. Final outcome determination

**Current Logging Points**:
- In play_simulation.py: PlayEvent objects added to result.events (PlayEvent has time, type, description)
- In game_simulation.py: Play description printed (line 597-630)

**Available Data Not Currently Logged**:
- Ball landing position details (x, y, depth, distance)
- Fielder assignment logic (which fielder, why)
- Fielder route efficiency (straight-line vs actual path)
- Throw accuracy and force play decisions
- Runner advancement logic (why they held vs advanced)
- Expected run value vs actual

---

### 1.4 Metrics & Debug Output (sim_metrics.py)

**Files**: 
- `/home/user/baseball/batted_ball/sim_metrics.py` (2402 lines - LARGEST FILE)

**Infrastructure**:
- `DebugLevel` enum (OFF, BASIC, DETAILED, EXHAUSTIVE)
- `SimMetricsCollector` class - Central metrics aggregation
- 7 metrics dataclasses (one per phase):
  1. `PitchMetrics` - Complete pitch-level tracking
  2. `SwingDecisionMetrics` - Hitter decision logic
  3. `BattedBallMetrics` - Trajectory and physics
  4. `FieldingMetrics` - Fielder performance
  5. `BaserunningMetrics` - Runner advancement
  6. `PitcherFatigueMetrics` - Pitcher performance degradation
  7. `ExpectedOutcomeMetrics` - Expected vs actual outcomes

**Current Integration Points**:
- Initialized in GameSimulator.__init__() (line 233-242)
- Used in at_bat.py _record_pitch_metrics() (line 129-228)
- Used in at_bat.py _record_batted_ball_metrics() (line 195-228)
- SimMetricsCollector.print_summary() called after game (line 290-291)

**New Diagnostic Features Already Implemented**:
- Pitcher fatigue tracking (velocity loss, spin loss, command penalty)
- Pitch intent vs actual (target location vs actual location)
- Hitter decision probabilities (swing %, chase %, whiff %)
- Contact model inputs (timing error, contact offset)
- Physics validation (drag/Magnus forces, aerodynamics)
- Fielder route efficiency calculations
- Baserunner speed diagnostics
- Expected vs actual run value

---

## 2. Key Logging Points Identified

### Tier 1: Pitch-Level (Most Granular)

**Location**: `at_bat.py` lines 789-920

Insertion Points:
```
BEFORE pitch simulation:
  - Pitch type selected [already done]
  - Pitch intention (strike_looking vs competitive vs waste vs corner)
  
AFTER pitch simulation:
  - Pitch release metrics (location, velocity, spin)
  - Pitch movement (break angles, IVB)
  - Command accuracy (distance from target)
  
BEFORE swing decision:
  - Hitter's decision model inputs
  - Swing probability calculation
  - Chase probability (if out of zone)
  
AFTER swing decision:
  - Did hitter swing? Why/why not?
  - Swing quality (early/late/perfect)
  - Contact offset from sweet spot
  
AFTER contact:
  - Contact quality outcome (weak/fair/solid/barrel)
  - Exit velocity/launch angle/spin
  - Expected distance vs actual physics distance
```

**Methods to Add Logging To**:
1. `select_pitch_type()` (line 230) - Log pitch selection rationale
2. `select_target_location()` (line 314) - Log target and intention
3. `simulate_pitch()` (line ~600+) - Log release and movement metrics
4. `_determine_pitch_intention()` (line 396) - Log decision logic
5. Swing decision evaluation - Log probability and outcome
6. Contact simulation - Log contact quality model evaluation

---

### Tier 2: Play-Level (Fielding/Baserunning)

**Locations**: 
- `play_simulation.py` (orchestration)
- `fly_ball_handler.py` (1216 lines)
- `ground_ball_handler.py` (679 lines)
- `fielding.py` (1709 lines)
- `baserunning.py` (1020 lines)

Insertion Points:
```
BALL LANDING ANALYSIS:
  - Ball landing position (x, y, depth from plate)
  - Hang time calculation
  - Hit type classification (GB/LD/FB/PU)
  
FIELDING PHASE:
  - Fielder assignment logic (which fielder, why)
  - Fielder reaction time
  - Route taken to intercept
  - Route efficiency (actual vs optimal path)
  - Catch probability (before vs after attempt)
  - Throw decision (who to throw to, why)
  - Throw accuracy and timing
  
BASERUNNING PHASE:
  - Runner advancement decisions (why held/advanced)
  - Runner speed evaluation
  - Lead distance
  - Jump quality
  - Run time to next base
  - Risk assessment (success probability)
  - Slide timing
  
OUTCOME DETERMINATION:
  - Final hit type (single/double/triple/HR)
  - Why this outcome (distance, fielder error, etc.)
  - Runners scored
  - Runners left on base
```

**Methods to Add Logging To**:
1. `play_analyzer.analyze_batted_ball()` - Ball landing details
2. `fielding.assign_fielder_to_ball()` - Fielder assignment logic
3. `fielding.simulate_fielder_movement()` - Route efficiency
4. `fly_ball_handler.attempt_trajectory_interception()` - Catch attempt logic
5. `ground_ball_handler.handle_ground_ball()` - GB fielding logic
6. `baserunning_simulator.advance_runner()` - Runner decision logic
7. `throwing_logic.determine_throw_target()` - Throw decision logic
8. `hit_handler.determine_hit_type()` - Hit type determination

---

### Tier 3: Game-Level (Aggregated Stats)

**Location**: `game_simulation.py` lines 750-857

Insertion Points:
```
AT-BAT SUMMARY:
  - Pitcher fatigue assessment before at-bat
  - Pitcher times through order (TTO)
  - High leverage situation indicator
  - At-bat expected value vs actual
  
INNING SUMMARY:
  - Runs scored in inning
  - Runners left on base
  - Pitcher performance (ERA pace, WHIP)
  
GAME SUMMARY:
  - Model drift analysis (expected vs actual scoring)
  - Statcast comparison (if available)
  - Physics validation results
```

**Methods to Add Logging To**:
1. `simulate_at_bat()` (line 323) - At-bat setup and TTO metrics
2. `process_play_result()` (line 492) - Play outcome and XR value
3. `print_final_summary()` (line 844) - Model drift summary

---

## 3. Data Flow Architecture

```
PITCH LEVEL:
  at_bat.py:select_pitch_type()
    ↓ (pitch_type, target)
  at_bat.py:simulate_pitch()
    ↓ (pitch_data: velocity, location, movement, spin)
  game_simulation.py:simulate_at_bat()
    ↓ (pitch logged to play_by_play)
  
SWING LEVEL:
  at_bat.py:simulate_at_bat()
    ↓ (hitter.decide_to_swing())
    ↓ (swing_decision_metrics → metrics_collector)
  
CONTACT LEVEL:
  at_bat.py:simulate_contact()
    ↓ (contact_result: exit_velocity, launch_angle, contact_quality)
    ↓ (batted_ball_metrics → metrics_collector)
  
PLAY LEVEL:
  game_simulation.py:simulate_at_bat()
    ↓ (at_bat_result.batted_ball_result)
  play_simulation.py:simulate_complete_play()
    ↓ (fielding, baserunning, outcome)
    ↓ (play_result: outcome, events, runs_scored)
  game_simulation.py:process_play_result()
    ↓ (update_game_state_from_play)
    ↓ (play_by_play logged)
  
GAME LEVEL:
  game_simulation.py:simulate_game()
    ↓ (accumulate stats across innings)
    ↓ (metrics_collector.print_summary())
```

---

## 4. Result Objects & Data Structures

### PlayResult (play_outcome.py)
```python
class PlayResult:
    outcome: PlayOutcome enum
    events: List[PlayEvent]
    runs_scored: int
    outs_made: int
    initial_runner_positions: Dict
    final_runner_positions: Dict
    batted_ball_result: BattedBallResult
    fielding_results: List
    baserunning_results: List
    play_description: str
    primary_fielder: Fielder
```

### AtBatResult (at_bat.py)
```python
class AtBatResult:
    outcome: str  # 'strikeout', 'walk', 'in_play', 'foul'
    pitches: List[Dict]  # Each with: type, location, velocity, result
    final_count: Tuple[int, int]  # (balls, strikes)
    batted_ball_result: Dict  # Only if in_play
```

### GameState (game_simulation.py)
```python
@dataclass
class GameState:
    inning, outs, away_score, home_score
    runner_on_first, _second, _third
    total_pitches, total_hits, total_home_runs
    [Team-specific stats: hits, singles, doubles, triples, HRs, Ks, BBs, errors, ABs]
    away_exit_velocities, away_launch_angles  # Lists for distribution analysis
    home_exit_velocities, home_launch_angles
```

### PlayByPlayEvent (game_simulation.py)
```python
@dataclass
class PlayByPlayEvent:
    inning, is_top
    batter_name, pitcher_name
    outcome, description
    physics_data: Dict
    game_state_after: str
```

---

## 5. Best Practices & Conventions

### Current Logging Style
- Console: Uses emoji symbols (⚾, 🚶, 🏃) for visual distinction
- File: Plain text with consistent formatting
- Indentation: 2-space indent per level
- Timestamps: Not currently used

### Available Infrastructure
1. **self.log()** method - Use instead of print() for dual console/file output
2. **self.verbose** flag - Check before logging
3. **self.metrics_collector** - For detailed diagnostic data
4. **PlayEvent** class - For structured event logging

### Example Current Usage
```python
# In game_simulation.py
if self.verbose:
    self.log(f"  ⚾ STRIKEOUT! {self.game_state.outs} out(s)")

# Alternative for detailed logs
if self.metrics_collector and self.metrics_collector.enabled:
    self._record_pitch_metrics(pitch_data, sequence_index)
```

---

## 6. Recommended Insertion Points (Priority Order)

### HIGH PRIORITY (Minimal impact, high value)

1. **Pitch Intention Logging** (at_bat.py line 396)
   - Add to _determine_pitch_intention(): Log why pitcher chose this intention
   - Impact: <1% performance, ~5 lines of logging

2. **Contact Quality Model** (at_bat.py line 861-878)
   - Expand contact_summary to include: sweet spot %, contact offset, timing error
   - Impact: <1% performance, ~10 lines

3. **Fielder Assignment Logic** (fielding.py _assign_fielder_to_ball)
   - Add fielder selection rationale: distance, angles, error margin
   - Impact: <1% performance, ~15 lines

4. **Runner Advancement Reasoning** (baserunning.py decide_runner_advancement)
   - Why runner held vs advanced: time margin, risk vs reward
   - Impact: <1% performance, ~10 lines

### MEDIUM PRIORITY (Moderate impact, very high value)

5. **Ball Landing Position Details** (play_analyzer or play_simulation.py line 147-154)
   - Exact landing coordinates, distance, hang time, park location
   - Impact: <2% performance, ~20 lines

6. **Expected vs Actual Comparison** (game_simulation.py process_play_result)
   - Expected distance (Statcast model) vs actual outcome
   - Impact: <1% performance, ~15 lines

7. **Pitcher Fatigue Tracking** (at_bat.py or game_simulation.py)
   - Velocity loss, spin loss, command penalty per inning
   - Impact: <2% performance, ~25 lines

### LOWER PRIORITY (More complex, requires refactoring)

8. **Fielding Route Efficiency** (fielding.py simulate_fielder_movement)
   - Straight-line distance vs actual path taken
   - Impact: <3% performance, ~30 lines, requires trajectory tracking

9. **Swing Probability Model Details** (at_bat.py hitter decision)
   - Full probability distribution for swing/take/chase
   - Impact: <2% performance, ~20 lines

10. **Play-by-Play Enrichment** (game_simulation.py)
    - Add play context: RISP, DPs available, park factors
    - Impact: <1% performance, ~30 lines

---

## 7. File Dependencies & Import Structure

```
CORE IMPORTS (always needed):
  - play_outcome.py: PlayResult, PlayEvent, PlayOutcome
  - sim_metrics.py: SimMetricsCollector, debug dataclasses
  
OPTIONAL LOGGING IMPORTS:
  - logging module (for structured logging)
  - datetime (for timestamps if added)
  
COMMONLY USED IN GAME FLOW:
  - at_bat.py → at_bat_result.pitches[] → game_simulation
  - play_simulation.py → play_result → game_simulation
  - game_simulation.py → play_by_play events → final_summary
```

---

## 8. Summary Table: Logging Coverage

| Phase | Current Coverage | Data Available | Recommended Next |
|-------|------------------|-----------------|-----------------|
| **Pitch Selection** | ✓ Type logged | Intention, weights, rationale | Log intention model |
| **Pitch Location** | ✓ Location + velocity | Command accuracy, error | Log target vs actual |
| **Swing Decision** | ✓ Yes/No logged | Probabilities, timing | Log decision rationale |
| **Contact Quality** | ✓ Basic logged | Sweet spot %, offset | Log full distribution |
| **Ball Landing** | ~ Implicit | Exact position, distance | Log explicit coordinates |
| **Fielding** | ~ Implicit | Assignment logic, route | Log fielder choice, route |
| **Baserunning** | ~ Implicit | Runner advancement logic | Log advancement reasoning |
| **Outcome** | ✓ Final outcome | Expected value, metrics | Log xBA, xwOBA, xr |
| **Game Summary** | ✓ Scores, stats | Full game flow | Log model drift, validation |

✓ = Well covered
~ = Partially covered  
(blank) = Not covered

---

## 9. Example Logging Implementations

### Example 1: Pitch Intention Logging
```python
# In at_bat.py _determine_pitch_intention()
intention = np.random.choice(intentions, p=probabilities)
if self.metrics_collector and self.metrics_collector.enabled:
    self.metrics_collector.log_pitch_intention(
        pitcher_name=self.pitcher.name,
        count=(balls, strikes),
        selected_intention=intention,
        intention_probabilities=dict(zip(intentions, probabilities))
    )
return intention
```

### Example 2: Contact Quality Logging
```python
# In at_bat.py after contact simulation
if contact_result:
    contact_quality = contact_result.get('contact_quality')
    contact_offset = contact_result.get('contact_offset_mm', 0)
    timing_error = contact_result.get('timing_error_ms', 0)
    
    self.log(f"    Contact offset: {contact_offset:.1f}mm, "
             f"Timing: {timing_error:+.1f}ms")
```

### Example 3: Fielder Assignment Logging
```python
# In fielding.py _assign_fielder_to_ball()
assigned_fielder = best_fielder_by_distance
if self.verbose:
    self.log(f"    Fielder assignment: {assigned_fielder.position} "
             f"({distance_to_ball:.1f} ft, reaction time {reaction_ms:.0f}ms)")
```

---

## Conclusion

The baseball simulation has a **well-structured, multi-tier logging system** with excellent foundation in:
- Game-level verbose output (console + file)
- Pitch-level tracking (at-bat sequencing)
- Play-level events (PlayEvent objects)
- Metrics collection (SimMetricsCollector with detailed dataclasses)

The main opportunities for enhancement are:
1. **Logging intent/reasoning** behind decisions (not just outcomes)
2. **Enriching existing logs** with physics/context data available in memory
3. **Adding model drift tracking** (expected vs actual at game level)
4. **Structured logging** for diagnostic/debugging workflows

All recommended additions have **minimal performance impact** (<3% overhead) and can be added **incrementally** without disrupting existing systems.

