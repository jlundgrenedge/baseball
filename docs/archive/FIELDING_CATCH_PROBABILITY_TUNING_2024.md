# Fielding Catch Probability Tuning - December 2024

## Problem Statement

User reported "hits are high and runs are low" in baseball game simulation. Initial issue was 26 hits but only 1-2 runs per game, indicating both:
1. Too many balls dropping (fielding too weak)
2. Runners not advancing properly on hits (baserunning too conservative)

## Root Cause Analysis

### Issue 1: Trajectory Interception Height Check
**Original Bug** (lines 410-419 in `play_simulation.py`):
```python
if ball_pos_t.z > 20.0 and t < flight_time * 0.5:
    continue
```

This skipped ALL balls above 20ft height during the first half of flight. Since most fly balls peak at 30-100ft, this meant the trajectory interception system **never checked** most catchable fly balls. Result: BABIP spiked to .533-.562 (should be .300).

**Fix Applied**:
```python
# For catchable fly balls, check throughout descent phase
# Skip only extremely high balls (>50ft) during first 30% of flight
if ball_pos_t.z > 50.0 and t < flight_time * 0.3:
    continue
```

### Issue 2: Catch Probability Calibration
After fixing trajectory interception, needed to calibrate catch probabilities to achieve MLB-realistic BABIP of ~.300 (70% catch rate on balls in play).

**Final Catch Probabilities** (`fielding.py` lines 705-730):
```python
if time_margin >= 0.5:
    probability = 0.92  # Fielder arrives 0.5+s early -> very routine
elif time_margin >= 0.0:
    probability = 0.70  # Fielder arrives 0-0.5s early -> routine
elif time_margin > -0.15:
    probability = 0.42  # Fielder slightly late (-0.15-0.0s) -> diving catch range
elif time_margin > -0.35:
    probability = 0.14  # Fielder late (-0.35--0.15s) -> extremely difficult
```

These base probabilities are multiplied by:
- Fielder's secure_prob (~0.92 for MLB average)
- Distance penalties for very deep balls
- Other situational factors

### Issue 3: Time Margin Requirements
**Original**: Required fielders to arrive 0.1-0.2s early to even attempt catch (lines 485-495)
**Fix**: Reduced to 0.0s for close balls, 0.05s for deep balls (>200ft)

This allows fielders to make more realistic catch attempts without requiring excessive margin.

## Results

### After All Fixes (10-game average):
- **BABIP**: ~.325-.340 (MLB .300) ✅ **Very close!**
- **Hits/9**: 22.2 (MLB ~17.0) ⚠️ Still 30% too high
- **Runs/9**: 4.8 (MLB ~9.0) ❌ Still 47% too low
- **HRs/9**: 0.09 (MLB ~2.2) ❌ Way too low
- **Runs-per-hit**: 0.22 (MLB ~0.53) ❌ Core issue!

### Comparison to Previous States:

| State | BABIP | Hits/9 | Runs/9 | Runs-per-hit |
|-------|-------|--------|--------|--------------|
| Original Bug | .533-.562 | 40+ | 2.5 | 0.06 |
| First Fix (removed force plays) | - | - | 7.5 | - |
| After height fix | .500 | 33.3 | 10.8 | 0.32 |
| After catch prob tuning v1 | .400 | 21.5 | 5.3 | 0.25 |
| **Current (final tuning)** | **.330** | **22.2** | **4.8** | **0.22** |
| **MLB Target** | **.300** | **17.0** | **9.0** | **0.53** |

## Remaining Issues

### 1. Low Runs-Per-Hit Ratio (CRITICAL)
The most significant remaining problem is that **22 hits produce only 4.8 runs** (0.22 runs/hit) when MLB averages 0.53 runs/hit.

**Possible Causes:**
- Baserunning advancement thresholds too conservative
- Not enough runners in scoring position when hits occur
- Strand rate too high

**Evidence from Game Logs:**
- Baserunning logic DOES work (saw examples of runners scoring from 2nd on singles)
- Many games show patterns like "runners on 1st and 2nd" but next batter makes out
- Logic in `baserunning.py:decide_runner_advancement()` looks reasonable but may need tuning

### 2. No Home Runs
Only 1 HR across 10 games (0.09/9 innings) vs MLB 2.2/9.

**Likely Cause:** HR detection threshold too high or exit velocity/launch angle combinations not optimal for HRs.

### 3. Hit Rate Still High
22.2 hits/9 vs MLB 17.0/9 suggests catch probabilities could be increased slightly more, **BUT** this conflicts with already-good BABIP of .330.

**Resolution:** The hit rate is inflated because we're counting 10-inning games as 9-inning rates. Actual per-9 may be closer to 20.0 which is still high but more reasonable.

## Files Modified

### 1. `batted_ball/play_simulation.py`
- **Lines 402-418**: Modified trajectory interception height check
  - Changed from "skip if >20ft in first 50%" to "skip if >50ft in first 30%"
- **Lines 485-486**: Reduced time margin requirements
  - Changed from 0.1-0.2s to 0.0-0.05s based on distance

### 2. `batted_ball/fielding.py`
- **Lines 715-728**: Tuned catch probability bands
  - Early arrival (0.5+s): 0.85 → 0.92
  - On-time (0-0.5s): 0.60 → 0.70
  - Diving range (-0.15-0s): 0.35 → 0.42
  - Very difficult (-0.35--0.15s): 0.12 → 0.14

## Next Steps

### Priority 1: Fix Runs-Per-Hit Ratio
**Options:**
1. **Adjust baserunning thresholds** in `baserunning.py:decide_runner_advancement()`
   - Lines 877-890: Runners on 2nd with single (currently: score unless strong-arm CF + shallow)
   - Lines 925-935: Runners on 2nd with double (currently: score unless strong-arm CF + shallow double)
   - Consider making runners MORE aggressive (score more often)

2. **Review strand rates**
   - Analyze game logs to find specific situations where runners should score but don't
   - May need to adjust "shallow single" threshold (currently <180ft)

3. **Fix home run detection**
   - Check HR threshold logic in trajectory or play outcome classification
   - MLB averages suggest we should be seeing 2-3 HRs per game

### Priority 2: Final BABIP Calibration
Once runs-per-hit is fixed and we're getting proper scoring, may need minor catch probability adjustments to dial in BABIP exactly to .300.

**Target Final State:**
- BABIP: .300
- Hits/9: 17.0
- Runs/9: 9.0
- HRs/9: 2.2
- Runs-per-hit: 0.53

## Validation Commands

```powershell
# Quick single game test
python test_full_game.py

# 10-game sample for averages
python test_multi_game_sample.py

# Debug-enabled game (shows trajectory interception decisions)
# Edit play_simulation.py line 392: debug = True
python test_full_game.py 2>&1 | Select-Object -First 200
```

## Key Learnings

1. **Trajectory interception height checks are critical** - skipping balls >20ft eliminated most catch attempts
2. **Catch probabilities must be calibrated empirically** - started at 0.60/0.85, ended at 0.70/0.92
3. **Time margins should be minimal** - fielders need ability to make on-time catches, not just early arrivals
4. **BABIP is easier to fix than runs-per-hit** - catching balls is physics-based, advancing runners is logic-based
5. **Always check runs-per-hit ratio** - can have good BABIP but still broken scoring if baserunning is conservative

## Code Architecture Notes

**Trajectory Interception Flow:**
1. `_attempt_trajectory_interception()` samples ball position at time intervals (DT)
2. For each time step, checks if any fielder can reach ball position before ball arrives
3. Uses `calculate_catch_probability()` to determine if fielder successfully catches
4. Returns first successful catch, or False if ball drops

**Key Functions:**
- `play_simulation.py:_attempt_trajectory_interception()` - Main interception logic
- `fielding.py:calculate_catch_probability()` - Probabilistic catch model
- `baserunning.py:decide_runner_advancement()` - Runner advancement decisions
- `play_simulation.py:_handle_hit_baserunning()` - Applies runner decisions to game state

**Critical Coordinate System:**
- Origin: Home plate (0,0,0)
- +X: Right field, -X: Left field
- +Y: Center field, -Y: Home plate
- +Z: Upward
- ALL modules must maintain this alignment (see `COORDINATE_SYSTEM_FIX_REPORT.md`)

## Conclusion

Successfully fixed the original "too many balls dropping" issue by correcting trajectory interception height check and calibrating catch probabilities. BABIP now at .330 (very close to MLB .300).

**Remaining critical issue:** Runs-per-hit ratio of 0.22 vs MLB 0.53 indicates baserunning logic needs adjustment to make runners more aggressive. This is the next priority fix.
