# Play-by-Play Bugs Tracker

This document tracks play-by-play bugs identified from game logs. Each bug includes:
- **Description**: What the bug looks like in the log
- **Root Cause**: Where in the code the problem originates
- **Impact**: How this affects gameplay/realism
- **Fix Plan**: Steps to resolve the issue
- **Status**: Not Started / In Progress / Fixed

---

## Bug #1: Difficult Play Incorrectly Classified as Error (Should Be Hit)

### Description
A **line drive** (LA=10.2°, apex=9.3 ft) is intercepted mid-flight by the first baseman who had to travel 38.4 ft to reach it. He arrived 0.12s late (diving attempt), got a glove on it, but couldn't hold on. This is being scored as an **ERROR (E3)** when it should be a **HIT**.

The ball would have landed at 142.9 ft if not intercepted - it only traveled that far because Hoskins missed it. The right fielder would have eventually fielded it in the outfield.

**Log excerpt:**
```
⚾ BATTED BALL: LINE_DRIVE
  EV: 79.9 mph, LA: 10.2°, Spray: -45.0°
  Distance: 142.9 ft (apex: 9.3 ft)
  Hang time: 1.41 s
  Landing: (101.1, 101.0)
  
Play timeline:
  [ 0.00s] Ball hit to shallow right outfield (contact)
  [ 1.41s] ERROR! Diving attempt by first_base, ball hit glove but dropped (E3)
  
FieldingPlayModel:
  Fielder: Rhys Hoskins (1b)
  OptimalDistanceFt: 38.4      ← Had to travel 38+ feet
  RequiredSpeedFtPerSec: 30.6
  MaxSpeedFtPerSec: 25.3
  CatchProbability: 0.42
  Margin: -0.12s               ← Arrived LATE (diving/stretching)
  Outcome: ERROR (route_efficiency)
  
WARNING: Required speed (30.6 ft/s) exceeds fielder max (25.3 ft/s) by >10%

Runners after play: Pete Crow-Armstrong on first, Pete Crow-Armstrong on second
```

**Note on Spray Angle:** The spray angle (-45°) and landing position (+101.1, +101.0) ARE consistent.
In this system: **negative spray = right field direction** (not baseball's "opposite field" convention).
- Spray -45° → trajectory vy is negative → lands with positive field X = right field ✓

### The Real Baseball Situation

**What happened physically:**
1. Line drive with 9.3 ft apex hit toward shallow right field
2. Hoskins (1B, 6'3") had to run **38.4 ft** to intercept the ball mid-flight
3. Even at its apex (9.3 ft), catching this requires:
   - A 6'3" player with arms up reaches ~8 ft standing
   - Needs ~1+ ft of jump to reach 9.3 ft ball
   - While running at max speed and arriving late
4. He dove, got a glove on it, couldn't hold on
5. Ball then continued to the outfield where RF would retrieve it

**Why this is NOT an error:**
- In baseball, an **error** is failing to make a play with **ordinary effort**
- This play required: 38 ft sprint + leaping catch at 9+ ft height + perfect timing
- This is an **extraordinary effort** play - a diving attempt at a difficult ball
- Even if the ball came straight at him (no lateral movement), a 9.3 ft line drive requiring a jump is NOT routine
- **MLB scoring rule**: If the play requires more than ordinary effort, a failure is a HIT, not an error

**Secondary issue - baserunning:**
- Error automatically advanced the runner to second base
- In reality: RF picks up the ball in shallow outfield, batter would stay at first
- On a clean single to shallow RF, the batter doesn't try for second against a strong arm

### Root Cause Analysis

**CONFIRMED: Route Efficiency Logging Receives Wrong Position**

I traced through the code and found the exact bug location:

**File: `batted_ball/fly_ball_handler.py`**

```python
# Lines 1174-1210: _log_route_efficiency() method
def _log_route_efficiency(self,
                          responsible_position: str,
                          ball_position: FieldPosition,  # ← DOCUMENTED AS "Where ball landed/was caught"
                          hang_time: float,
                          ...):
    ...
    metrics = self.route_efficiency_analyzer.analyze_fielding_play(
        fielder=fielder,
        fielder_start_position=fielder_start_position,
        ball_intercept_position=ball_position,  # ← PASSES LANDING POSITION, NOT INTERCEPT!
        ball_hang_time=hang_time,
        fielding_result=catch_result
    )
```

The method is called at line 185 with `ball_position` which is the **landing position** from `BattedBallResult.land_position`, NOT the actual trajectory interception point calculated in `attempt_trajectory_interception()`.

**The Disconnect:**
1. `attempt_trajectory_interception()` (lines 729-966) correctly calculates `ball_pos_t` at each trajectory point
2. It finds where a fielder can intercept (in our case, at t=1.27s, position (91.1, 91.0, 3.2ft))
3. But `_log_route_efficiency()` is called AFTER with the original `ball_position` (landing spot 142.9 ft)
4. The route efficiency analyzer then calculates wrong distance/time to the wrong position

**Geometry Comparison:**
```
                          LOGGED (Wrong)        ACTUAL (Calculated)
Ball Position:            (101.1, 101.0)        (91.1, 91.0)
Ball Height:              0.0 ft (ground)       3.2 ft (chest high)
Distance from Home:       142.9 ft              128.6 ft  
Distance for Hoskins:     38.4 ft               27.1 ft
Time Available:           1.41s                 1.27s
Time Needed:              1.53s                 1.22s
Margin:                   -0.12s (LATE)         +0.05s (EARLY)
```

The ACTUAL interception (at Hoskins' Y-depth of 91 ft):
- Ball passes Y=91 at t=1.27s
- Ball position: (91.1, 91.0, 3.2 ft)
- Lateral distance: 27.1 ft
- Hoskins had +0.05s margin (can make the catch standing!)

**Impact on Error Classification:**
With CORRECT geometry (27.1 ft, +0.05s margin, 3.2 ft height):
- This IS actually a routine-ish play for a 6'3" first baseman
- The error classification MIGHT be correct!
- But the log looks wrong because it shows impossible numbers

With LOGGED geometry (38.4 ft, -0.12s margin):
- Looks like an impossible diving play
- Error classification looks WRONG based on logged data

### Impact
- **Logging is misleading**: Shows wrong distance (38.4 ft vs 27.1 ft) and wrong margin (-0.12s vs +0.05s)
- **Error classification is probably correct** - the actual gameplay uses trajectory interception
- **But log analysis is impossible** - the logged numbers don't reflect what happened
- Any debugging/tuning based on logged metrics will be wrong

### Fix Plan

**The Fix: Pass Actual Interception Point to Route Efficiency Logging**

The trajectory interception logic in `attempt_trajectory_interception()` correctly calculates the interception point (`ball_pos_t`), but this information is lost before logging.

**Option A: Capture Interception Point in FieldingResult** (Recommended)
1. Add `actual_intercept_position` field to `FieldingResult` class
2. In `attempt_trajectory_interception()`, when catch/error occurs, store `ball_pos_t`
3. In `_log_route_efficiency()`, use `catch_result.actual_intercept_position` if available

```python
# In attempt_trajectory_interception(), when catch succeeds or error occurs:
catch_result = FieldingResult(...)
catch_result.actual_intercept_position = ball_pos_t  # Store actual intercept

# In _log_route_efficiency():
intercept_position = (catch_result.actual_intercept_position 
                      if hasattr(catch_result, 'actual_intercept_position') 
                      else ball_position)  # Fallback to landing spot
```

**Option B: Log Intercept Point Separately**
1. Add a new event type `trajectory_intercept_metrics` logged directly from `attempt_trajectory_interception()`
2. Include: `ball_pos_t`, `t`, `margin`, actual distance

**Files to Modify:**
1. `batted_ball/fielding.py` - Add `actual_intercept_position` to `FieldingResult`
2. `batted_ball/fly_ball_handler.py`:
   - Line ~922: Store `ball_pos_t` in the fielding result
   - Lines 1207-1210: Use actual intercept position if available
3. `batted_ball/route_efficiency.py` - Update `analyze_fielding_play()` docstring

**Expected Log After Fix:**
```
FieldingPlayModel:
  Fielder: Rhys Hoskins (1b)
  InterceptType: trajectory  (NEW)
  InterceptPositionFt: (91.1, 91.0, 3.2)  (NEW - actual 3D position)
  OptimalDistanceFt: 27.1  (FIXED - was 38.4)
  RequiredSpeedFtPerSec: 24.1  (FIXED - was 30.6)
  MaxSpeedFtPerSec: 25.3
  CatchProbability: 0.75  (should be higher for routine play)
  Margin: +0.05s  (FIXED - was -0.12s)
  BallHeightAtInterceptFt: 3.2  (NEW)
  Outcome: ERROR
```

**Improved Play-by-Play Log Format:**

The current play-by-play event says:
```
[ 1.41s] ERROR! Diving attempt by first_base, ball hit glove but dropped (E3)
```

This is misleading because:
1. "1.41s" is the total hang time, not when the fielder intercepted
2. "Diving attempt" may or may not be accurate based on the geometry
3. No indication of WHERE the play happened (trajectory intercept vs landing spot)

**Suggested improved format:**
```
[ 1.27s] first_base intercepts line drive at (91, 91, 3.2ft) - 27.1ft traveled, +0.05s margin
[ 1.27s] ERROR (E3): Routine catch dropped by Rhys Hoskins
         Ball continues to right field for retrieval
```

Or for a difficult play that SHOULD be a hit:
```
[ 1.27s] first_base attempts diving catch at (91, 91, 8.5ft) - 38ft traveled, -0.12s margin
[ 1.27s] Ball off glove - scored as SINGLE (extraordinary effort, not error)
         Right fielder retrieves in shallow outfield
```

Key improvements:
- Log the ACTUAL intercept time, not hang time
- Log the 3D intercept position
- Log the travel distance and time margin
- Distinguish "routine catch dropped" (ERROR) from "diving/difficult attempt" (HIT)
- Indicate what happens to the ball after the play

---

## Phase 2: Scorekeeper Logic for Error vs Hit Classification

### The Problem

Currently, ANY dropped ball where the fielder got a glove on it is classified as an ERROR. But in real baseball, scorekeepers apply judgment:

- **ERROR**: Fielder failed to make a play with **ordinary effort**
- **HIT**: Fielder made an **extraordinary effort** but couldn't complete the play

**Current stats (observed)**:
- Simulation: ~1 error per team per game (2 total per game)
- MLB reality: ~0.5 errors per team per game (1 total per game)
- **We're charging 2x too many errors!**

### Proposed Scorekeeper Logic

When a fielder reaches a ball but fails to make the catch, calculate a **difficulty score** based on the play geometry:

```python
def determine_error_or_hit(
    distance_traveled_ft: float,
    time_margin_s: float,
    ball_height_ft: float,
    exit_velocity_mph: float
) -> str:
    """
    Scorekeeper determination: ERROR vs HIT for a dropped ball.
    
    This runs AFTER the fielder reaches the ball and drops it.
    The fielding physics stays the same - this is purely classification.
    
    Returns "ERROR" or "HIT"
    """
    
    # Calculate difficulty score (higher = harder play = more likely HIT)
    difficulty = 0.0
    
    # === Distance Factor ===
    # Routine plays are < 15 ft, difficult plays are > 25 ft
    if distance_traveled_ft > 30:
        difficulty += 0.4
    elif distance_traveled_ft > 20:
        difficulty += 0.2
    elif distance_traveled_ft > 10:
        difficulty += 0.1
    
    # === Time Margin Factor ===
    # Comfortable margin > 0.3s, barely made it < 0.1s
    if time_margin_s < 0.05:
        difficulty += 0.3  # Just barely got there
    elif time_margin_s < 0.15:
        difficulty += 0.15
    elif time_margin_s < 0.25:
        difficulty += 0.05
    
    # === Ball Height Factor ===
    # Comfortable catch zone is 3-6 ft (chest to face)
    if ball_height_ft > 8:
        difficulty += 0.25  # Had to jump
    elif ball_height_ft < 2.5:
        difficulty += 0.3   # Had to dive/scoop
    elif ball_height_ft > 6:
        difficulty += 0.1   # Reaching up
    # 3-6 ft adds nothing (routine height)
    
    # === Exit Velocity Factor ===
    # Hard-hit balls are harder to squeeze
    if exit_velocity_mph > 100:
        difficulty += 0.3
    elif exit_velocity_mph > 95:
        difficulty += 0.2
    elif exit_velocity_mph > 90:
        difficulty += 0.1
    
    # === Decision ===
    # difficulty > 0.5 = HIT (extraordinary effort play)
    # difficulty <= 0.5 = ERROR (should have made the play)
    
    if difficulty > 0.5:
        return "HIT"
    else:
        return "ERROR"
```

### Example: The Hoskins Play

```
distance_traveled = 27.1 ft  → +0.2 (> 20 ft)
time_margin = 0.05s          → +0.3 (barely got there)  
ball_height = 3.2 ft         → +0.0 (comfortable zone)
exit_velocity = 79.9 mph     → +0.0 (not hard hit)

Total difficulty = 0.5       → BORDERLINE
```

This would make it a close call - which feels right! A slightly harder-hit ball (90+ mph) or more distance (30+ ft) would tip it to a HIT.

### Factor Weights Rationale

| Factor | Weight | Rationale |
|--------|--------|-----------|
| Distance > 30 ft | 0.4 | Running 30+ ft and catching is difficult |
| Distance > 20 ft | 0.2 | Significant ground to cover |
| Margin < 0.05s | 0.3 | Barely got there, no time to set up |
| Margin < 0.15s | 0.15 | Rushed play |
| Height < 2.5 ft | 0.3 | Diving/scooping is hard |
| Height > 8 ft | 0.25 | Jumping catch is hard |
| EV > 100 mph | 0.3 | Ball is a bullet, hard to squeeze |
| EV > 95 mph | 0.2 | Hard-hit ball |

### Implementation Location

- **File**: `batted_ball/fly_ball_handler.py`
- **Method**: `handle_fielding_error()` or new `classify_error_or_hit()`
- **When**: After determining fielder got glove on ball but didn't complete catch
- **Data needed**: 
  - `distance_traveled_ft` - from route efficiency (AFTER we fix Bug #1)
  - `time_margin_s` - from route efficiency (AFTER we fix Bug #1)
  - `ball_height_ft` - from intercept position z-coordinate
  - `exit_velocity_mph` - from BattedBallResult

### Dependencies

This fix **depends on Bug #1 being fixed first** - we need the correct intercept geometry (distance, margin, height) rather than the wrong landing-spot metrics.

### Expected Impact

- Reduce errors from ~1.0 per team per game to ~0.5 (matching MLB)
- Increase BABIP slightly (more difficult plays become hits)
- More realistic scoring

### Status: Not Started - Design Complete, Depends on Bug #1 Fix

---

## Bug #2: Runner Appears on Multiple Bases Simultaneously

### Description
After an error, the play log shows the **same runner on both first AND second base**:

```
Runners after play: Pete Crow-Armstrong on first, Pete Crow-Armstrong on second
```

This is physically impossible - a runner can only be on one base at a time.

### Root Cause Analysis

**Issue: final_runner_positions Dictionary Corruption**
- File: `batted_ball/fly_ball_handler.py` → `handle_fielding_error()`
- The method adds the batter to `final_runner_positions` with their target base
- But it also processes "existing runners" which may incorrectly include the batter again
- There's no check to prevent the same runner from appearing at multiple bases

**Code Flow:**
```python
# Line 357: Add batter to first or second
result.final_runner_positions[batter_target] = batter_runner

# Lines 365-414: Loop through existing runners
for base in ["third", "second", "first"]:
    runner = self.baserunning_simulator.get_runner_at_base(base)
    if runner:
        # If batter_runner was somehow still at another base, they'd be added again
```

**Specific Scenario:**
1. With bases empty, batter (Crow-Armstrong) hits a ball
2. Fielder commits error
3. Batter advances to second (`batter_target = "second"`)
4. Code adds event: "Runner advances from first to second" even though no runner was on first
5. This creates a ghost entry putting Crow-Armstrong on first AND second

### Impact
- Invalid game state
- Confusing play-by-play logs
- Could cause downstream issues with scoring and runner management

### Fix Plan

**Phase 1: Add Duplicate Prevention** (Priority: Critical)
1. In `fly_ball_handler.py` → `handle_fielding_error()`:
   ```python
   # Before adding batter to final positions, clear any existing entry for this runner
   for base in list(result.final_runner_positions.keys()):
       if result.final_runner_positions[base] is batter_runner:
           del result.final_runner_positions[base]
   
   result.final_runner_positions[batter_target] = batter_runner
   ```

**Phase 2: Validate Runner Identity**
1. When processing "existing runners," skip if the runner is the batter:
   ```python
   for base in ["third", "second", "first"]:
       runner = self.baserunning_simulator.get_runner_at_base(base)
       if runner and runner is not batter_runner:  # Add identity check
           # Process runner advancement
   ```

**Phase 3: Add Final Validation**
1. At end of `handle_fielding_error()`, validate no duplicate runners:
   ```python
   # Validate no runner appears twice
   seen_runners = set()
   for base, runner in result.final_runner_positions.items():
       runner_id = id(runner)
       if runner_id in seen_runners:
           # Log warning and remove duplicate
           del result.final_runner_positions[base]
       seen_runners.add(runner_id)
   ```

### Files to Modify
- `batted_ball/fly_ball_handler.py` - `handle_fielding_error()`
- `batted_ball/game_simulation.py` - Add validation in `_handle_play_result()`

### Status: Not Started

---

## Bug #3: Event Timestamp Inconsistency (Runner Advances Before Error Recorded)

### Description
The event timeline shows a runner advancing to second at 2.01s, but the ball is recovered at 2.91s and batter reaches first at 3.76s. This creates a confusing sequence:

```
[ 1.41s] ERROR! Diving attempt by first_base...
[ 2.01s] Runner advances from first to second    ← Which runner? No runner was on first!
[ 2.91s] Ball recovered by 1b after error
[ 3.76s] Batter reaches first base on error
```

### Root Cause Analysis

1. The "runner advances from first to second" event at 2.01s is spurious
2. With bases empty, there's no runner on first to advance
3. The code is generating advancement events even when no runner exists at that base

**In `handle_fielding_error()`:**
```python
elif base == "first":
    # This branch executes even if no runner is actually on first
    # The check `if runner:` exists but something is wrong with runner detection
```

### Impact
- Confusing play-by-play narrative
- Phantom runners appearing in events
- Timeline doesn't make logical sense

### Fix Plan

**Phase 1: Fix Ghost Runner Detection**
1. Add explicit base occupancy check before generating events:
   ```python
   # In handle_fielding_error, BEFORE the loop
   bases_occupied_before_play = {
       base: self.baserunning_simulator.get_runner_at_base(base)
       for base in ["first", "second", "third"]
       if self.baserunning_simulator.get_runner_at_base(base) is not None
   }
   
   # Only process bases that actually had runners
   for base in ["third", "second", "first"]:
       if base not in bases_occupied_before_play:
           continue  # No runner was here, skip
   ```

**Phase 2: Validate Event Generation**
1. Don't generate "runner advances" events for non-existent runners
2. Add assertion: `assert runner is not None` before adding events

### Files to Modify
- `batted_ball/fly_ball_handler.py` - `handle_fielding_error()`

### Status: Not Started

---

## Bug #4: Parallel Simulator Doesn't Track Errors

### Description
The `simulate_random_parallel.py` script doesn't correctly track error statistics. When running parallel simulations, errors are always reported as 0.

### Root Cause Analysis

**File**: `examples/simulate_random_parallel.py`

In the `MockGameState` class (lines 198-227), errors are hardcoded to 0:

```python
class MockGameState:
    def __init__(self, result: ParallelGameResult):
        ...
        # Fielding (not tracked in parallel mode)
        self.away_errors = 0
        self.home_errors = 0
```

The comment says "not tracked in parallel mode" but this means we can't validate error rates from parallel simulations.

Additionally, `ParallelGameResult` dataclass doesn't include error fields:

```python
@dataclass
class ParallelGameResult:
    # ... has batting stats but NO error fields
```

### Impact
- Can't validate error rates from high-volume parallel testing
- Can't confirm the ~1 error/team/game observation or verify fixes
- Parallel mode gives incomplete statistics

### Fix Plan

1. Add error fields to `ParallelGameResult`:
   ```python
   @dataclass
   class ParallelGameResult:
       ...
       away_errors: int = 0
       home_errors: int = 0
   ```

2. Populate from `final_state` in `_simulate_single_game_worker()`:
   ```python
   return ParallelGameResult(
       ...
       away_errors=final_state.away_errors,
       home_errors=final_state.home_errors,
   )
   ```

3. Update `MockGameState` to use actual values:
   ```python
   self.away_errors = result.away_errors
   self.home_errors = result.home_errors
   ```

### Files to Modify
- `examples/simulate_random_parallel.py`

### Status: Not Started

---

## Testing Strategy

After fixes are implemented:

1. **Unit Tests**: Create specific test cases for each bug scenario
2. **Integration Tests**: Run 5-10 MLB games with `game_simulation.bat → Option 8`
3. **Log Review**: Search game logs for:
   - "ERROR" with "route_efficiency_warning" (Bug #1)
   - Duplicate runner names (Bug #2)
   - "Runner advances from first" with empty bases (Bug #3)

## Priority Order

1. **Bug #1** (Critical) - Logging wrong intercept geometry + Scorekeeper logic for error vs hit
2. **Bug #2** (Critical) - Runner duplication creates invalid game state
3. **Bug #3** (Medium) - Event timeline confusion (related to Bug #2)
4. **Bug #4** (Low) - Parallel simulator not tracking errors (easy fix, needed for validation)

---

*Last Updated: 2025-11-30*
*Log Source: Cubs vs Brewers game log analysis*
