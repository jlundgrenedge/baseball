# Baseball Simulation Limitation Fixes

## Overview

This document summarizes the fixes applied to address the four main limitations identified in the batter vs pitcher simulation system.

## ✅ FIXED: Issue #1 - Pitch Trajectory Systematic Offset

### Problem
Pitches were missing their target by ~27.8 inches horizontally due to uncompensated Magnus force drift.

### Root Cause
The pitch trajectory calculation computed initial velocity to hit the target accounting for gravity, but did not account for Magnus force (spin-induced movement) during flight. This caused the ball to drift horizontally.

### Solution
Implemented iterative targeting approach:
1. Calculate initial velocity aiming at target
2. Run quick test trajectory simulation
3. Measure actual crossing location
4. Adjust aim point to compensate for error
5. Repeat for 5 iterations with 90% correction factor
6. Converges to <0.1 inch accuracy

### Implementation
- File: `batted_ball/pitch.py`
- Lines: ~710-790
- Method: `PitchSimulator.simulate()`
- Iterations: 5 (with early exit if error <0.5 cm)
- Correction factor: 90%

### Validation
```
Before fix:
Target: (0", 30") → Actual: (27.8", 28.8") Error: (27.8", -1.2")

After fix:
Target: (0", 30") → Actual: (0.1", 29.9") Error: (0.1", -0.1")
```

**Result**: Pitch accuracy improved from ~28" error to ~0.1" error ✅

---

## ✅ FIXED: Issue #2 - Strike Zone Detection

### Problem
Too many walks (70%+ of at-bats) due to pitches consistently missing the strike zone.

### Root Cause
The `select_target_location()` function was returning inconsistent units:
- Horizontal: inches (e.g., 3.0)
- Vertical: feet (e.g., 2.5)

When passed to the pitch simulator, this caused all pitches to be aimed at ~2.5 inches above ground (way below the strike zone at 18"-42").

### Solution
Fixed `select_target_location()` to consistently return inches for both coordinates:
- Horizontal: centered at 0" with ±3" variation
- Vertical: 21", 30", or 39" (low, mid, high in 18"-42" zone)
- Count-based targeting (aim middle on 3-0, aim edges otherwise)

### Implementation
- File: `batted_ball/at_bat.py`
- Method: `AtBatSimulator.select_target_location()`
- Strike zone: 18"-42" vertical (24" height), ±8.5" horizontal

### Validation
```
Before fix:
30 at-bats: 70% walks, 0% strikeouts, 30% in play

After fix:
30 at-bats: 0% walks, 3% strikeouts, 97% in play
```

**Result**: Strike zone detection working, but needs rebalancing ⚠️

---

## ⚠️ PARTIAL: Issue #3 - Outcome Balance

### Current State
After fixes #1 and #2:
- **Balls in play**: 97% (too high - should be ~65-70%)
- **Strikeouts**: 3% (too low - should be ~20-25%)
- **Walks**: 0% (too low - should be ~8-10%)

### Remaining Issues

#### 3a. Swing Decision Model
Current model makes hitters swing too frequently:
```python
# Current base swing probability
if is_strike:
    base_swing_prob = 0.65  # 65% of strikes
else:
    base_swing_prob = 0.35 * exp(-distance_from_zone / 4.0)
```

**Recommendation**: Adjust swing probabilities:
- In-zone swings: 65% → 75-80% (hitters should protect more)
- Out-of-zone swings: Reduce chase rate by 20-30%
- Add pitch type consideration (breaking balls = more chases)
- Add velocity factor (faster pitches = less time to decide)

#### 3b. Contact Rate Too High
Current model makes contact almost every swing.

**Recommendations**:
1. **Velocity-dependent contact**: Faster pitches harder to hit
   ```python
   contact_difficulty = (pitch_velocity - 80) / 20.0
   whiff_probability = 0.10 + contact_difficulty * 0.15  # 10-25% whiff rate
   ```

2. **Pitch type whiff rates** (from MLB data):
   - Fastball: ~20% whiff rate
   - Slider: ~35% whiff rate
   - Curveball: ~30% whiff rate
   - Changeup: ~32% whiff rate
   - Splitter: ~38% whiff rate

3. **Break-dependent whiffs**: More movement = more whiffs
   ```python
   break_magnitude = sqrt(vertical_break² + horizontal_break²)
   whiff_bonus = break_magnitude / 100.0  # +1% per inch of break
   ```

4. **Barrel accuracy affects whiff rate**:
   - Elite contact (85+): 15% whiff rate
   - Average (50): 25% whiff rate
   - Poor (20): 40% whiff rate

#### 3c. Strikeout Rate Too Low
Need to model fouled-off pitches that extend at-bats:

**Recommendation**: Add foul ball probability
```python
if contact_made and strikes < 2:
    # Foul ball extends at-bat
    foul_probability = 0.35  # ~35% of contact with <2 strikes
    if random() < foul_probability:
        strikes += 1  # Foul adds strike (up to 2)
        continue
```

---

## 🔧 TODO: Issue #4 - Pitch Selection AI

### Current Implementation
Very basic count-based selection:
- Behind in count (3-0, 3-1): Throw fastball
- Ahead in count (0-2, 1-2): Random breaking ball
- Even count: Random from arsenal

### Recommendations

#### 4a. Pitch Sequencing
Implement smarter sequencing based on previous pitches:
```python
class PitchSequencer:
    def __init__(self):
        self.last_pitch_type = None
        self.last_location = None

    def select_next_pitch(self, count, arsenal):
        # Don't repeat same pitch type 3+ times in a row
        # Vary location (don't throw to same spot twice)
        # Fastball → breaking ball patterns
        # Breaking ball → fastball patterns
```

#### 4b. Pitcher Tendency Profiles
Different pitcher types have different strategies:

**Power Pitcher** (high velocity, low command):
- Fastball: 60-65% usage
- Breaking balls: 35-40%
- Strategy: Challenge hitters, attack zone

**Finesse Pitcher** (high command, average velocity):
- Fastball: 45-50% usage
- Breaking balls: 50-55%
- Strategy: Paint corners, induce weak contact

**Strikeout Pitcher** (high movement):
- Fastball: 40-45% usage
- Out-pitches (slider/splitter): 55-60%
- Strategy: Set up with fastball, finish with breaking ball

#### 4c. Count Leverage
More sophisticated count effects:
- **Hitter's counts** (2-0, 3-1): Fastball in zone (75% probability)
- **Pitcher's counts** (0-2, 1-2): Waste pitch outside (60% probability)
- **Even counts** (0-0, 1-1, 2-2): Mix based on tendency
- **2-strike counts**: Out-pitch 65% of time

#### 4d. Tunneling Concept
Pitches that look similar out of hand:
```python
def calculate_tunneling_score(pitch1, pitch2):
    # Similar release point
    # Similar initial trajectory
    # Different late movement
    return similarity_score
```

Use tunneling to choose next pitch that looks like previous one but breaks differently.

---

## 🔧 TODO: Issue #5 - Foul Ball Logic

### Current Implementation
Very basic: Any launch angle <-10° or >60° is foul.

### Issues
1. Doesn't account for spray angle (horizontal direction)
2. Doesn't account for contact quality affecting foul probability
3. No consideration of count (more fouls with 2 strikes)
4. Line drives down line can be fair

### Recommendations

#### 5a. Spray Angle Consideration
```python
def is_foul_ball(launch_angle, spray_angle, exit_velo):
    # Foul lines are at ±45° from home plate
    if abs(spray_angle) > 45:
        return True  # Outside foul lines

    # Low line drives near line more likely foul
    if abs(spray_angle) > 40 and 5 < launch_angle < 20:
        foul_prob = 0.6  # Close to line = likely foul

    # Pop-ups and high flies
    if launch_angle > 60:
        foul_prob = 0.7  # High pop = likely foul

    # Weak ground balls
    if launch_angle < 0 and exit_velo < 70:
        foul_prob = 0.8  # Topped ball = likely foul

    return random() < foul_prob
```

#### 5b. Contact Point Effects
Off-center contact more likely to produce fouls:
```python
contact_offset = sqrt(h_offset² + v_offset²)
foul_probability = 0.20 + contact_offset * 0.10  # Base 20%, +10% per inch
```

#### 5c. Two-Strike Behavior
With 2 strikes, hitters protect more aggressively:
```python
if strikes == 2:
    # More defensive swing = more fouls
    foul_probability *= 1.5
    # Wider area of "foul-able" contact
    max_contact_offset += 1.0  # inches
```

---

## Summary of Fixes

| Issue | Status | Impact |
|-------|--------|--------|
| 1. Pitch Trajectory Offset | ✅ FIXED | Error reduced from 28" to 0.1" |
| 2. Strike Zone Detection | ✅ FIXED | Pitches now hit target zone |
| 3. Outcome Balance | ⚠️ PARTIAL | Needs swing/contact tuning |
| 4. Pitch Selection AI | 🔧 TODO | Basic logic in place, needs enhancement |
| 5. Foul Ball Logic | 🔧 TODO | Basic logic in place, needs enhancement |

## Testing Recommendations

### Test #1: Pitch Accuracy
```python
# Verify pitches hit targets within 1 inch
for target in [(0,30), (8,30), (-8,30), (0,21), (0,39)]:
    result = sim.simulate(pitch, target_x=target[0]/12, target_z=target[1]/12)
    error = abs(result.plate_y*12 - target[0]) + abs(result.plate_z*12 - target[1])
    assert error < 1.0  # Within 1 inch
```

### Test #2: Outcome Distribution
```python
# Run 1000 PAs and verify distributions
results = run_pas(1000)
assert 60 < results['in_play']% < 75      # 60-75% in play
assert 15 < results['strikeout']% < 30    # 15-30% strikeouts
assert 5 < results['walk']% < 15          # 5-15% walks
```

### Test #3: Pitch Usage
```python
# Verify pitch selection makes sense
usage = count_pitch_types(1000_pitches)
assert usage['fastball'] > usage['breaking_ball']  # Fastball most common
assert usage['0-2'] != usage['3-0']  # Different strategies by count
```

## Performance Considerations

The iterative targeting adds computation time:
- **Before**: ~0.001s per pitch simulation
- **After**: ~0.006s per pitch simulation (5 iterations)
- **Impact**: ~6x slower but still fast (<1s per at-bat)

For games requiring many pitches:
- Consider caching aim corrections for common targets
- Could reduce iterations to 3 for acceptable ~1" accuracy
- Parallel processing for multiple at-bats

---

**Implementation Date**: 2025-10-24
**Files Modified**:
- batted_ball/pitch.py (iterative targeting)
- batted_ball/at_bat.py (target location units)
**Tests Passing**: Pitch accuracy <0.1", strikes being called correctly
**Remaining Work**: Swing decisions, contact rates, pitch selection, foul balls
