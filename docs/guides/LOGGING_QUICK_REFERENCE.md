# Baseball Simulation Logging - Quick Reference Guide

## Answer to Key Questions

### Q1: Where does game simulation and logging happen?

**Primary Files:**
- **game_simulation.py** (985 lines) - Main orchestrator
  - Lines 205-250: GameSimulator.__init__ with verbose/log_file/debug_metrics params
  - Lines 252-258: log() method (dual console+file output)
  - Lines 270-293: simulate_game() - Main game loop
  - Lines 295-320: simulate_half_inning() - Per-inning flow
  - Lines 323-399: simulate_at_bat() - At-bat orchestration
  - Lines 750-764: log_play_by_play() - Event recording

- **at_bat.py** (957 lines) - At-bat physics
  - Lines 789-920: simulate_at_bat() - Pitch sequence + swing + contact
  - Lines 230-312: select_pitch_type() - Pitch selection logic
  - Lines 314-394: select_target_location() - Pitch targeting
  - Lines 396-449: _determine_pitch_intention() - Intent calculation

### Q2: What's currently being logged?

**Game Level (game_simulation.py):**
- Game start/end headers
- Inning state transitions
- Batter vs pitcher setup
- Strikeouts and walks
- Plays (pitch sequence + outcome + physics)
- Final score and statistics

**At-Bat Level (at_bat.py):**
- Pitch type and location (verbose=True, line 828-832)
- Swing decision ("Swings...")
- Pitch outcome (called strike, ball, swinging strike)
- Contact quality summary (if verbose, line 885-887)

**Play Level (play_simulation.py):**
- PlayEvent objects added to result.events
- Events include: contact, home run, catch, error, baserunning

**Metrics Level (sim_metrics.py):**
- 7 dataclasses for detailed tracking:
  - PitchMetrics (pitch details)
  - SwingDecisionMetrics (swing probabilities)
  - BattedBallMetrics (trajectory and physics)
  - FieldingMetrics (fielder performance)
  - BaserunningMetrics (runner advancement)
  - PitcherFatigueMetrics (fatigue effects)
  - ExpectedOutcomeMetrics (expected vs actual)

### Q3: How does verbose mode work?

**Mechanism:**
```python
# In GameSimulator.__init__ (line 205):
def __init__(self, away_team, home_team, verbose=True, log_file=None, debug_metrics=0):
    self.verbose = verbose
    self.log_file = log_file
    self.log_handle = open(log_file, 'w') if log_file else None

# The log() method (line 252):
def log(self, message: str):
    if self.verbose:
        print(message)          # Console
    if self.log_handle:
        self.log_handle.write(message + '\n')  # File
        self.log_handle.flush()
```

**Check Pattern:**
```python
# Example from line 328-330:
if self.verbose:
    self.log(f"\n{batter.name} batting against {pitcher.name}")
    self.log(f"  Situation: {self.game_state.get_base_state().value}")
```

**Debug Metrics:**
- Integer 0-3 selects DebugLevel (OFF, BASIC, DETAILED, EXHAUSTIVE)
- Passed to SimMetricsCollector in line 240-242
- Controls detail level in print_summary() output

### Q4: Result Objects Structure

**PlayResult** (play_outcome.py):
```python
class PlayResult:
    outcome: PlayOutcome              # Final play outcome
    events: List[PlayEvent]           # Ordered sequence of events
    runs_scored: int                  # Runs scored on play
    outs_made: int                    # Outs recorded
    initial_runner_positions: Dict    # Before play
    final_runner_positions: Dict      # After play
    batted_ball_result: BattedBallResult
    fielding_results: List
    baserunning_results: List
    play_description: str             # Human-readable summary
```

**AtBatResult** (at_bat.py, line 32-62):
```python
class AtBatResult:
    outcome: str                      # 'strikeout', 'walk', 'in_play', 'foul'
    pitches: List[Dict]              # Each pitch: type, location, velocity, result
    final_count: Tuple[int, int]     # (balls, strikes)
    batted_ball_result: Optional[Dict]  # If in_play
```

**PlayEvent** (play_outcome.py, line 28-50):
```python
class PlayEvent:
    time: float                       # Seconds from contact
    event_type: str                   # 'catch', 'throw', 'runner_arrival', etc
    description: str                  # Human-readable
    positions_involved: List[str]     # Fielders involved
```

**GameState** (game_simulation.py, line 42-159):
```python
@dataclass
class GameState:
    inning, is_top, outs
    away_score, home_score
    runner_on_first, runner_on_second, runner_on_third  # Hitter objects
    # Stats tracking:
    away_hits, away_home_runs, away_strikeouts, away_walks, etc.
    away_exit_velocities: List[float]  # Distribution tracking
    away_launch_angles: List[float]
    # Similar for home team...
```

### Q5: Where key decisions happen

**Pitch Selection** (at_bat.py, line 230-312):
- `select_pitch_type()` - Weighted random by: arsenal usage, count leverage, sequencing
- Logic: fastballs when behind, breaking balls when ahead

**Pitch Targeting** (at_bat.py, line 314-394):
- `select_target_location()` - Returns (h_inches, v_inches) target
- `_determine_pitch_intention()` (line 396) - Selects: strike_looking, competitive, waste, corner

**Swing Decision** (at_bat.py, line 835-841):
- `Hitter.decide_to_swing()` - Based on: location, count, velocity, discipline rating
- Returns: bool (should swing)

**Contact Quality** (at_bat.py, line 861-883):
- `ContactModel.simulate_contact()` - Returns: exit_velocity, launch_angle, distance, contact_quality
- Contact quality: 'weak', 'fair', 'solid', 'barrel'

**Hit Type** (hit_handler.py, line 40-80):
- `determine_hit_type()` - Based on: distance, park fence, contact quality, exit velocity
- Outcomes: single, double, triple, home run

**Fielding** (fielding.py):
- Fielder assignment (1709 lines - complex logic)
- Route planning
- Catch probability

**Baserunning** (baserunning.py, 1020 lines):
- `advance_runner()` - Based on: distance, runner speed, throw timing
- Decision: hold, advance 1, advance 2, score

---

## Key Files by Purpose

| Purpose | File | Lines | Key Functions |
|---------|------|-------|----------------|
| **Game orchestration** | game_simulation.py | 985 | simulate_game(), simulate_at_bat(), process_play_result() |
| **Pitch/swing/contact** | at_bat.py | 957 | simulate_at_bat(), select_pitch_type(), decide_to_swing() |
| **Play execution** | play_simulation.py | ~400 | simulate_complete_play(), coordinate handlers |
| **Hit determination** | hit_handler.py | 533 | determine_hit_type() |
| **Ground ball logic** | ground_ball_handler.py | 679 | handle_ground_ball() |
| **Fly ball logic** | fly_ball_handler.py | 1216 | attempt_trajectory_interception() |
| **Fielding physics** | fielding.py | 1709 | (most complex - movement, distance, timing) |
| **Baserunning physics** | baserunning.py | 1020 | advance_runner(), calculate_run_time() |
| **Metrics/logging** | sim_metrics.py | 2402 | (largest - SimMetricsCollector + 7 dataclasses) |
| **Result objects** | play_outcome.py | ~86 | PlayResult, PlayEvent, PlayOutcome enum |

---

## Recommended Logging Insertion Points

### HIGHEST VALUE, LOWEST EFFORT

1. **Pitch Intention Logging**
   - File: at_bat.py
   - Function: _determine_pitch_intention() (line 396)
   - Add: Log why pitcher selected this intention
   - Effort: 5 lines
   - Impact: Shows pitcher strategy

2. **Contact Quality Details**
   - File: at_bat.py
   - After line 878 (contact_summary dict)
   - Add: sweet_spot_accuracy, timing_error, contact_offset
   - Effort: 10 lines
   - Impact: Explains why contact resulted in weak/solid/barrel

3. **Fielder Assignment Reasoning**
   - File: fielding.py
   - Function: _assign_fielder_to_ball()
   - Add: Why this fielder was chosen (distance, angle, error margin)
   - Effort: 15 lines
   - Impact: Clarifies fielding decisions

4. **Runner Advancement Logic**
   - File: baserunning.py
   - Function: advance_runner() or decide_runner_advancement()
   - Add: Time margin, risk calculation, advancement threshold
   - Effort: 10 lines
   - Impact: Shows runner decision-making

### HIGH VALUE, MODERATE EFFORT

5. **Ball Landing Position**
   - File: play_simulation.py or play_analyzer.py
   - After line 147-148: analyze_batted_ball()
   - Add: Explicit logging of (x, y, distance, park location)
   - Effort: 20 lines
   - Impact: Complete fielding context

6. **Expected vs Actual**
   - File: game_simulation.py
   - Function: process_play_result() (line 492)
   - Add: xDistance, xBA, expected_outcome vs actual
   - Effort: 15 lines
   - Impact: Model drift detection

7. **Pitcher Fatigue**
   - File: game_simulation.py or at_bat.py
   - Before at-bat (line 323)
   - Add: Velocity loss, spin loss, command penalty per inning
   - Effort: 25 lines
   - Impact: Pitcher performance context

---

## How to Enable Different Log Levels

```python
from batted_ball import GameSimulator

# Level 0: No debug metrics
sim = GameSimulator(away, home, verbose=True, debug_metrics=0)

# Level 1: Basic pitch/contact/fielding metrics
sim = GameSimulator(away, home, verbose=True, debug_metrics=1)

# Level 2: Detailed with probabilities, expected values
sim = GameSimulator(away, home, verbose=True, debug_metrics=2)

# Level 3: Exhaustive with all internal calculations
sim = GameSimulator(away, home, verbose=True, debug_metrics=3)

# Write to file instead of console
sim = GameSimulator(away, home, verbose=False, log_file="game_log.txt", debug_metrics=2)
```

---

## Data Flow Diagram

```
GAME START
  ↓
[game_simulation.py] simulate_game()
  ↓
While inning <= num_innings:
  ├─→ simulate_half_inning() 
  │    │
  │    └─→ While outs < 3:
  │         │
  │         └─→ simulate_at_bat(batting_team, pitching_team)
  │              │
  │              ├─→ [at_bat.py] AtBatSimulator.simulate_at_bat()
  │              │    ├─ select_pitch_type()
  │              │    ├─ select_target_location()
  │              │    ├─ simulate_pitch()
  │              │    ├─ hitter.decide_to_swing()
  │              │    ├─ simulate_contact()
  │              │    └─ return AtBatResult
  │              │
  │              ├─→ [if outcome in K/BB]
  │              │    ├─ handle_strikeout_or_walk()
  │              │    └─ log_play_by_play()
  │              │
  │              └─→ [if in_play]
  │                   ├─ [play_simulation.py] PlaySimulator.simulate_complete_play()
  │                   │   ├─ [play_analyzer] analyze_batted_ball()
  │                   │   ├─ [fly_ball_handler] OR [ground_ball_handler]
  │                   │   │   ├─ fielding decision
  │                   │   │   └─ baserunning decision
  │                   │   └─ return PlayResult
  │                   │
  │                   ├─ process_play_result(play_result)
  │                   ├─ update_game_state_from_play()
  │                   └─ log_play_by_play()
  │
  └─ continue next inning
  
[After all innings]
  ↓
print_final_summary()
metrics_collector.print_summary()
```

---

## Summary: Current vs Recommended Logging

| Component | Current | Recommended |
|-----------|---------|-------------|
| Pitch selection | ✓ Type only | + Intention, weights, rationale |
| Pitch location | ✓ Location + velo | + Command error, distance from target |
| Swing decision | ✓ Yes/No | + Probability, discipline applied, why |
| Contact quality | ✓ Basic | + Sweet spot %, timing error, offset |
| Ball landing | ~ Implicit | + Explicit coordinates, distance, zone |
| Fielder assign | ~ Implicit | + Why this fielder, distance, angles |
| Runner advance | ~ Implicit | + Time margin, risk, speed used |
| Play outcome | ✓ Final result | + Expected value, model drift |
| Game summary | ✓ Scores/stats | + Physics validation, drift analysis |

