# Scoring Calibration Progress - December 2024

## Problem Statement
Baseball simulation had "hits high, runs low" issue after fielding fixes. Specifically:
- **Initial State**: Runs/9 = 4.5-4.8 vs MLB target 9.0 (only 50% of target)
- **Hits/9**: ~18.0 (close to MLB target 17.0)
- **HRs/9**: 0.03 vs target 2.2 (virtually no home runs)
- **Root Cause**: Low exit velocities due to (1) bat speeds too low, (2) collision efficiency too low

## Calibration Iterations

### Phase 1: Bat Speed Calibration
**Problem**: Average bat speeds 63-73 mph vs MLB 70-80 mph  
**Solution**: Boosted `get_bat_speed_mph()` anchor points by ~7 mph across entire range
- human_min: 45 → 52 mph
- human_cap: 73 → 80 mph  
- super_cap: 85 → 92 mph

**Result**: Average hitters now 75-87 mph bat speed (MLB-realistic)

### Phase 2: Collision Efficiency Tuning
**Problem**: COLLISION_EFFICIENCY_WOOD = 0.09 produced exit velocities too low for HRs  
**Physics Context**: Wood bats should have q = 0.15-0.25 based on COR research

**Iterations**:
- q = 0.09 → HRs/9 = 0.03 (baseline, broken)
- q = 0.19 → HRs/9 = 3.5+ (too many)
- q = 0.14 → HRs/9 = 1.8 (getting closer)
- q = 0.15 → HRs/9 = 2.34 (target achieved!)

**Result**: With q=0.15, Runs/9 improved from 4.5 → 5.0

### Phase 3: Baserunning Aggression (Iterative)
**Problem**: Even with HRs fixed, runs per hit = 0.28 vs MLB 0.53  
**Approach**: Made baserunning progressively more aggressive

**Iterations**:
- Original: 230-270 ft threshold for first-to-third on singles
- Iteration 1: 200 ft with angle-based logic → Runs/9 = 5.0
- Iteration 2: 180 ft simple distance → Runs/9 = 5.6  
- Iteration 3: 150 ft ultra-aggressive → Runs/9 = 5.1 (BACKFIRED - too many outs)
- **Final**: Reverted to 180 ft threshold

Also made scoring from 1st on doubles more aggressive:
- 2 outs + 300+ ft → attempt to score
- 0-1 outs + speed>60 + 350+ ft → attempt to score

**Result**: Runs/9 = 5.6-5.9 with 180 ft threshold

### Phase 4: Extra-Base Hit Rate Increase
**Problem**: Only ~11% of hits were extra-base hits (2B+3B), far below MLB ~30%  
**Approach**: Lower distance thresholds for doubles and triples

**Changes**:
- Doubles: 260 ft → 230 ft (in both `_determine_hit_type` and `_handle_ball_in_play`)
- Gap hit doubles: 220 ft → 200 ft
- Triples: 340 ft → 300 ft (AND lowered angle/EV requirements)

**Result**: Runs/9 = 5.7, Hits/9 = 17.7 (hits perfect!)

### Phase 5: Final Collision Efficiency Boost
**Problem**: Still at 5.7 runs/9 (63% of target 9.0)  
**Approach**: Increase HRs slightly more for guaranteed runs

**Final Tuning**:
- q = 0.15 → HRs/9 = 2.34, Runs/9 = 5.7
- **q = 0.16** → HRs/9 = 2.61, Runs/9 = **6.4** ✅
- q = 0.17 → HRs/9 = 3.24, Runs/9 = 6.2 (diminishing returns)

**Result**: **BEST BALANCE at q = 0.16**

## Final Results (20-Game Sample)

### Current State with q=0.16
- **Runs/9**: 6.4 vs target 9.0 (71% of target) ⚠️
- **Hits/9**: 16.6 vs target 17.0 (98% of target) ✅
- **HRs/9**: 2.61 vs target 2.2 (119% of target) ✅ (acceptable)
- **Runs per hit**: 0.39 vs MLB 0.53 (74% of target)

### Progress Summary
| Metric | Initial | After Bat Speed | After q=0.15 | After Baserunning | After XBH | **Final (q=0.16)** | Target | % of Target |
|--------|---------|----------------|--------------|-------------------|-----------|-------|--------|-------------|
| Runs/9 | 4.5 | 5.0 | 5.0 | 5.9 | 5.7 | **6.4** | 9.0 | **71%** |
| Hits/9 | ~18.0 | ~18.0 | 18.0 | 18.0 | 17.7 | **16.6** | 17.0 | **98%** |
| HRs/9 | 0.03 | 1.5 | 2.34 | 2.34 | 1.57 | **2.61** | 2.2 | **119%** |
| R/H | 0.25 | 0.28 | 0.28 | 0.33 | 0.32 | **0.39** | 0.53 | **74%** |

**Total Improvement**: Runs/9 increased from 4.5 → 6.4 (**+42% improvement**, need +29% more)

## Remaining Gap Analysis

### What's Working
✅ **Home runs**: Now at MLB-like rate (2.61 HRs/9)  
✅ **Hit rate**: Very close to MLB target (16.6 hits/9)  
✅ **Exit velocities**: Realistic bat speeds producing MLB-like contact outcomes  
✅ **Extra-base hits**: More doubles/triples from lowered thresholds

### What's Still Short
⚠️ **Runs per hit**: 0.39 vs MLB 0.53 (26% gap remaining)  
⚠️ **Overall scoring**: 6.4 vs 9.0 runs/9 (29% gap remaining)

### Likely Causes of Remaining Gap

1. **Hit Clustering**: MLB teams score more efficiently because hits cluster (multiple hits in same inning). Our simulation may spread hits too evenly across innings, leading to more stranded runners.

2. **Runners Stranded in Scoring Position**: Despite aggressive baserunning, runners on 2nd/3rd may not be scoring at MLB rates.

3. **Double Play Rate**: If DP rate is slightly high (>10% of opportunities), this kills rallies and prevents runs.

4. **Baserunning Timing**: Even with 180 ft threshold, margins may be too tight. Runners attempting advances may be getting thrown out more than MLB rates.

5. **Hit Type Distribution**: While we increased doubles/triples, the mix may still not match MLB. Need to analyze:
   - Singles: ~70% of non-HR hits (we may be higher)
   - Doubles: ~20% of non-HR hits
   - Triples: ~2% of non-HR hits

## Recommendation: Accept Current State or Deep Dive

### Option A: Accept 6.4 Runs/9 (71% of target)
**Pros:**
- Hits and HRs are MLB-realistic  
- Physics-based approach maintained integrity
- Further tuning may require unrealistic parameter changes

**Cons:**
- Still 2.6 runs/9 short of target
- Runs-per-hit below MLB levels

### Option B: Deep Analysis of Anomaly Games
Investigate games with terrible run efficiency:
- Game 6: 0 runs on 8 hits
- Game 12: 1 run on 12 hits  
- Game 15: 2 runs on 17 hits

**Questions to Answer**:
1. How many runners reached 2nd/3rd and didn't score?
2. How many double plays occurred?
3. Were hits clustered or spread evenly?
4. What were the exact margins on baserunning attempts?

### Option C: Increase Base-Stealing / Aggressive Advances
Add base-stealing simulation to manufacture runs without relying solely on hits.

## Code Changes Made

### Files Modified:
1. **batted_ball/attributes.py** (lines 133-151):
   - Boosted bat speed anchors: 45/63/73/85 → 52/70/80/92 mph

2. **batted_ball/constants.py** (line 232):
   - COLLISION_EFFICIENCY_WOOD: 0.09 → 0.16

3. **batted_ball/baserunning.py** (multiple sections):
   - Lines 882-896: First-to-third on singles: 230-270 ft → 180 ft threshold
   - Lines 935-961: Scoring from 1st on doubles: made much more aggressive

4. **batted_ball/play_simulation.py**:
   - Lines 1037-1044: Doubles threshold: 260 ft → 230 ft, Triples: 340 ft → 300 ft
   - Lines 1018-1028: Fair contact doubles/triples thresholds adjusted
   - Lines 1503-1510: _handle_ball_in_play doubles: 250 ft → 230 ft

### Key Constants:
```python
# Bat speed (attributes.py get_bat_speed_mph)
human_min=52, human_cap=80, super_cap=92

# Collision efficiency (constants.py)
COLLISION_EFFICIENCY_WOOD = 0.16

# Baserunning (baserunning.py)
first_to_third_threshold = 180  # feet
score_from_first_on_double = 300  # feet with 2 outs

# Hit type thresholds (play_simulation.py)
doubles_threshold = 230  # feet
triples_threshold = 300  # feet (with gap angle requirement)
```

## Testing Commands
```bash
# Run 20-game sample for statistical validation
python test_multi_game_sample.py

# Run single game with detailed logging
python test_full_game.py

# Analyze specific game log
# Check enhanced_game_log.txt for timing, margins, decisions
```

## Next Steps (If Pursuing 9.0 Runs/9 Target)

1. **Analyze Anomaly Games**: 
   - Extract play-by-play from low-scoring high-hit games
   - Identify where runners are getting stranded
   - Check double play frequency

2. **Hit Clustering Analysis**:
   - Measure innings with 2+ hits vs 0-1 hits
   - Compare to MLB distribution (should have more "crooked number" innings)

3. **Runner Advancement Efficiency**:
   - Track what % of runners on 2nd score
   - Track what % of runners on 3rd score
   - Compare to MLB benchmarks (~60% from 2nd, ~85% from 3rd)

4. **Consider Alternative Approaches**:
   - Add base-stealing mechanics (currently absent)
   - Adjust pitcher fatigue to increase hits late in games
   - Reduce fielding range slightly to allow more hits to drop

5. **Validate Against Full Season**:
   - Run 100-game sample to reduce variance
   - Current 20-game samples show high variance (0-16 runs per game)

## Physics Integrity Notes

**Critical**: All changes maintained physics-based approach:
- Bat speeds based on MLB Statcast 2024 data
- Collision efficiency within physically valid range (0.15-0.25 for wood)
- Distance thresholds reflect realistic outfield hit distribution
- Baserunning thresholds based on typical MLB advancement patterns (though more aggressive)

**No artificial probability boosts or dice rolls added** - all outcomes emerge from physics + timing calculations.
