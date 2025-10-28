# Low Scoring Analysis and Fixes

## Current Issues (Per Test Game)
- **Runs/9**: 1.8 (should be ~9.0) - **80% too low**
- **Home Runs/9**: 0.9 (should be ~2.2) - **59% too low**  
- **BABIP**: 0.182 (should be ~.300) - **39% too low**
- **Hits/9**: 8.1 (should be ~17.0) - **52% too low**

## Root Causes Identified

### 1. HOME RUN THRESHOLD TOO HIGH ⚠️
**Location**: `play_simulation.py` line 1271-1282

```python
# PROBLEM: Requires peak height >= fence_height * 1.5 (15 ft for 10 ft fence!)
if peak_height >= fence_height * 1.5:  # 1.5x margin for trajectory arc
    is_home_run = True
```

**Issue**: This is WAY too conservative. A ball traveling 400+ ft will clear a 10 ft fence even with a peak height of only 30-40 ft. The 1.5x multiplier (requiring 15+ ft) prevents many legitimate home runs.

**MLB Reality**: 
- Average HR peak height: ~80-120 ft
- But balls with peak 40-60 ft can still clear 10 ft fence if trajectory is right
- Research shows balls 400+ ft with peak >30 ft are home runs

**Fix**: Use ball height at fence distance, not peak height requirement
- Calculate actual height at fence distance from trajectory
- OR use much more lenient peak height threshold (e.g., >30 ft)

### 2. CONTACT QUALITY GATES TOO RESTRICTIVE ⚠️
**Location**: `play_simulation.py` line 947-990

```python
# PROBLEM: "Fair" contact (80-95 mph) requires distance >= fence AND peak >= 15 ft
elif contact_quality == 'fair' or exit_velocity < 95:
    if distance_ft >= fence_distance and peak_height >= 15:
        result.outcome = PlayOutcome.HOME_RUN
```

**Issue**: Combines two restrictive checks:
1. Distance must equal/exceed fence (no margin)
2. Peak height >= 15 ft (arbitrary minimum)

**MLB Reality**:
- 90 mph exit velo balls CAN be home runs
- Peak height of 15 ft is meaningless - what matters is height AT the fence
- Many line-drive home runs have lower peak heights

**Fix**: 
- Remove peak height check from this gate (already checked in main HR logic)
- Allow 85-95 mph balls to be HRs if distance is sufficient

### 3. CONSERVATIVE BASERUNNING MARGIN ⚠️
**Location**: `play_simulation.py` line 1397

```python
# PROBLEM: Runner needs 1.5 second advantage to take next base
SAFE_MARGIN = 1.5  # Runner needs big advantage to attempt next base
```

**Issue**: MLB runners are more aggressive than this. A 1.5s margin means:
- Runner on 2nd rarely scores on single (should be ~85%)
- Runner on 1st rarely takes 3rd on single (should be ~20%)

**MLB Reality**:
- Runners with 0.5-1.0s margin routinely try for next base
- Managers/coaches encourage aggressive baserunning with <2 outs
- Close plays (0.2-0.5s margin) are common and exciting

**Fix**: Reduce SAFE_MARGIN to 0.5-0.8 seconds

### 4. LOW BABIP - FIELDERS TOO GOOD ⚠️
**BABIP**: 0.182 vs expected ~.300

**Issue**: Fielders are intercepting/catching too many balls. Combined issues:
- Catch probability model too generous to fielders
- Fielder positioning too optimal
- Time margins for interception too lenient (0.75s leeway)

**Fix**:
- Reduce fielder catch probability by ~10-15%
- Reduce interception time margin from 0.75s to 0.4s
- Add randomness to fielder starting positions

## Implementation Priority

### Phase 1: Home Run Fixes (Highest Impact)
1. ✅ Fix home run height threshold (peak >= 30 ft instead of 1.5x fence)
2. ✅ Remove peak height restriction from "fair" contact gate
3. ✅ Add distance cushion (ball 10+ ft past fence = HR regardless)

### Phase 2: Baserunning Fixes (High Impact)
1. ✅ Reduce SAFE_MARGIN from 1.5 to 0.6 seconds
2. ✅ Make baserunning decisions situation-aware (2 outs = more aggressive)
3. ✅ Add randomness to marginal decisions (0.5-1.0s margins = 50-80% go)

### Phase 3: BABIP Fixes (Medium Impact)
1. ⏳ Reduce fielder interception time margin (0.75s → 0.5s)
2. ⏳ Adjust catch probability model (-10% across the board)
3. ⏳ Add fielder positioning variance

## Expected Results After Fixes

| Metric | Current | Expected | MLB Avg |
|--------|---------|----------|---------|
| Runs/9 | 1.8 | 8-10 | ~9.0 |
| HRs/9 | 0.9 | 2.0-2.5 | ~2.2 |
| BABIP | .182 | .280-.310 | ~.300 |
| Hits/9 | 8.1 | 16-18 | ~17.0 |

## Testing Plan

1. Run `test_quick_game.py` (3 innings) - quick validation
2. Run `test_full_game.py` (9 innings) - full statistics
3. Run 10-game simulation - statistical validation
4. Validate against validation suite (7 physics tests must still pass)

## Code Changes Summary

### File: `batted_ball/play_simulation.py`

**Change 1** (Line ~1275): Fix HR height threshold
```python
# OLD
if peak_height >= fence_height * 1.5:  # Too restrictive!
    is_home_run = True

# NEW  
if peak_height >= 30.0:  # Reasonable minimum for clearing fence
    is_home_run = True
```

**Change 2** (Line ~960): Remove peak height gate for fair contact
```python
# OLD
elif contact_quality == 'fair' or exit_velocity < 95:
    if distance_ft >= fence_distance and peak_height >= 15:

# NEW
elif contact_quality == 'fair' or exit_velocity < 95:
    if distance_ft >= fence_distance - 5:  # 5 ft cushion
```

**Change 3** (Line ~1397): Reduce baserunning margin
```python
# OLD
SAFE_MARGIN = 1.5  # Too conservative

# NEW
SAFE_MARGIN = 0.6  # More realistic MLB aggression
```

**Change 4** (Line ~TBD): Reduce fielder intercept margin
```python
# OLD (in _attempt_trajectory_interception)
if time_margin >= -0.75:  # Very lenient

# NEW
if time_margin >= -0.5:  # More realistic
```
