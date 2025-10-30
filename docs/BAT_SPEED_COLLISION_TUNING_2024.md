# Bat Speed & Collision Efficiency Tuning (December 2024)

## Problem Statement
After fixing fielding (BABIP .330), runs per game remained too low:
- **Before**: Runs/9 = 4.5-4.8 (target: 9.0)
- **Symptom**: Only 1 HR in 30 games (HRs/9 = 0.03 vs target 2.2)
- **Root Cause**: Exit velocities too low (75-88 mph vs MLB avg 88-92 mph)

## Investigation

### Initial Diagnosis
Checked exit velocity calculations and found two issues:

1. **Bat Speed Mapping Too Low**
   - Old values: 50k rating → 63 mph, 85k → 73 mph
   - Result: Average hitters had 68-83 mph bat speed
   - MLB Actual: Average ~70 mph, Elite ~77-80 mph

2. **Collision Efficiency Too Low**  
   - Old value: `COLLISION_EFFICIENCY_WOOD = 0.09`
   - Formula: `EV = q×pitch + (1+q)×bat`
   - With q=0.09, pitch=95, bat=80: EV = 95.8 mph (too low)
   - MLB Research: q should be 0.15-0.25 for wood bats

### Fix #1: Bat Speed Boost
**File**: `batted_ball/attributes.py` lines 133-151

Changed `get_bat_speed_mph()` anchor points:
```python
# OLD:
human_min=45.0, human_cap=73.0, super_cap=85.0

# NEW (calibrated to MLB Statcast 2024):
human_min=52.0, human_cap=80.0, super_cap=92.0
```

**Result**: Bat speeds increased by ~7 mph across the board
- Average hitters: 68-83 mph → 75-87 mph
- Elite hitters: 75-83 mph → 82-87 mph

### Fix #2: Collision Efficiency Tuning
**File**: `batted_ball/constants.py` line 232

Iteratively tested collision efficiency values:

| q Value | HRs/9 | Runs/9 | Hits/9 | Assessment |
|---------|-------|--------|--------|------------|
| 0.09 (old) | 0.03 | 4.5 | 21.1 | Way too low |
| 0.19 | 6.3 | 10.8 | 22.5 | Way too high |
| 0.14 | 1.71 | 5.0 | 16.6 | **Close!** |

**Final Value**: `COLLISION_EFFICIENCY_WOOD = 0.14`

With q=0.14:
- Pitch 95 mph + Bat 80 mph → EV = 0.14×95 + 1.14×80 = **104.5 mph**
- Pitch 95 mph + Bat 70 mph → EV = 0.14×95 + 1.14×70 = **93.1 mph**

## Results (20-Game Sample with q=0.14)

| Metric | Before Fixes | After Fixes | MLB Target | Status |
|--------|--------------|-------------|------------|--------|
| Runs/9 | 4.5 | **5.0** | 9.0 | ⚠️ Still 45% low |
| Hits/9 | 21.1 | **16.6** | 17.0 | ✅ Perfect! |
| HRs/9 | 0.03 | **1.71** | 2.2 | ⚠️ Close (78%) |
| BABIP | .330 | ~.318 | .300 | ✅ Good |
| Runs per Hit | 0.21 | **0.30** | 0.53 | ❌ Still 43% low |

## Remaining Issues

### 1. Home Run Rate Slightly Low
- Current: 1.71 HRs/9 (78% of target)
- Possible Fix: Boost q from 0.14 to 0.15 or 0.16
- Risk: Don't want to overshoot and get 6+ HRs/9 again

### 2. Runs Per Hit Too Low
- Current: 0.30 runs/hit vs MLB 0.53 runs/hit
- **This is the main problem** - getting hits but not scoring
- Possible causes:
  - Not enough extra-base hits (doubles/triples)
  - Baserunning not aggressive enough
  - Hit clustering (need multiple hits per inning)
  - Force plays / double plays too frequent

### 3. Exit Velocity Distribution
Need to verify that EV distribution matches MLB:
- MLB: Mean ~88 mph, 90th percentile ~105 mph, max ~115-120 mph
- Current: Need to analyze enhanced_game_log.txt for distribution

## Next Steps

1. **Fine-tune collision efficiency**
   - Test q=0.15 to get HRs/9 closer to 2.2
   - Monitor for overcorrection

2. **Analyze run scoring patterns**
   - Check enhanced_game_log.txt for runner advancement decisions
   - Count first-to-third on singles, scoring from 2nd on singles
   - Verify runners scoring from 1st on doubles

3. **Extra-base hit rates**
   - Calculate doubles/triples per 9 innings
   - Compare to MLB: ~5% triples, ~20% doubles of all hits
   - May need to adjust hit type classification in play_simulation.py

4. **Consider baserunning boost**
   - Current thresholds may still be too conservative
   - MLB: ~28% first-to-third rate on singles
   - MLB: ~50% score from 2nd on singles

## Code Changes Summary

### Modified Files
1. **batted_ball/attributes.py**
   - Lines 133-151: Bat speed anchor points boosted by ~7 mph

2. **batted_ball/constants.py**
   - Line 232: `COLLISION_EFFICIENCY_WOOD` changed from 0.09 → 0.14

3. **batted_ball/baserunning.py**
   - Lines 863-950: Previously made more aggressive (from earlier session)
   - May need further adjustments

### Validation
- Run `python test_multi_game_sample.py` for 20+ game averages
- Check `enhanced_game_log.txt` for play-by-play analysis
- Monitor Runs/9, Hits/9, HRs/9, BABIP

## Technical Notes

### Exit Velocity Formula
The collision model uses a physics-based approach:
```python
exit_velocity = collision_efficiency_q * pitch_speed_mph + 
                (1.0 + collision_efficiency_q) * bat_speed_mph
```

This formula accounts for:
- Conservation of momentum in bat-ball collision
- Coefficient of restitution (energy loss)
- The fact that bat velocity contributes more than pitch velocity

### Why q=0.14 Works
- Lower than theoretical physics (0.18-0.20) due to:
  - Vibration energy loss
  - Off-center contact frequency
  - Sweet spot distance penalties
  - Real-world bat performance vs ideal conditions

### Bat Speed Calibration
The piecewise logistic mapping ensures:
- Smooth progression through human range (0-85k rating)
- Realistic MLB averages at 50k rating
- Room for elite performance at 85k rating
- Headroom for "superhuman" attributes beyond 85k

## References
- MLB Statcast 2024: Average bat speed ~70 mph, elite ~77-80 mph
- MLB Statcast 2024: Average exit velo ~88-90 mph, 90th% ~105 mph
- Collision efficiency research: Typical q values 0.15-0.25 for wood bats
- Previous fixes: See `FIELDING_CATCH_PROBABILITY_TUNING_2024.md`
