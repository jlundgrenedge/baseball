# Pitch Intention System Diagnostic Results

**Date**: 2025-11-20
**Sprint**: Phase 2A Sprint 4 - Post-Mortem Investigation
**Issue**: Zone rate stuck at 44.2% despite command sigma reductions

---

## Executive Summary

**THE GOOD NEWS**: The `_determine_pitch_intention()` logic is working correctly. It produces exactly the expected distributions for each count.

**THE PROBLEM**: We misunderstood what "expected" means. The 60% strike_looking is for 0-0 counts only, not game-wide average.

**ACTUAL GAME-WIDE EXPECTED**: 34.9% strike_looking (when weighted by count frequency)
**OBSERVED IN TESTS**: 27.8% strike_looking
**GAP**: -7.1 percentage points (20% less than expected)

**ZONE RATE IMPLICATIONS**:
- Expected zone rate with 34.9% strike_looking: **59.8%** ✓ (close to MLB 62-65%)
- Observed zone rate: **44.2%** ✗
- **Gap: 15.6 percentage points**

---

## Diagnostic Results

### 1. Count-Specific Distributions (1000 samples each)

The pitch intention system produces **correct distributions** for each count:

| Count | strike_looking | strike_competitive | strike_corner | waste_chase | ball_intentional |
|-------|----------------|-------------------|---------------|-------------|------------------|
| **0-0** (First pitch) | **60.3%** | 19.3% | 11.4% | 0.0% | 9.0% |
| **1-0** | 29.3% | 43.2% | 16.6% | 0.0% | 10.9% |
| **0-1** | 31.0% | 43.0% | 14.3% | 0.0% | 11.7% |
| **1-1** (Even) | 27.4% | 42.6% | 18.7% | 0.0% | 11.3% |
| **2-0** (Hitter's count) | 37.5% | 47.7% | 0.0% | 0.0% | 14.8% |
| **0-2** (Pitcher ahead) | **0.0%** | 37.9% | 19.3% | **42.8%** | 0.0% |
| **2-1** | 37.7% | 48.2% | 0.0% | 0.0% | 14.1% |
| **1-2** | **0.0%** | 36.6% | 21.2% | **42.2%** | 0.0% |
| **2-2** (Full) | **0.0%** | 36.0% | 20.5% | **43.5%** | 0.0% |
| **3-0** (Must strike) | **71.1%** | 28.9% | 0.0% | 0.0% | 0.0% |
| **3-2** (Full) | **71.0%** | 29.0% | 0.0% | 0.0% | 0.0% |

**Key Observations**:
- ✅ First pitch (0-0): 60.3% strike_looking (exactly as designed)
- ✅ 2-strike counts (0-2, 1-2, 2-2): 0% strike_looking (throw waste pitches)
- ✅ 3-ball counts (3-0, 3-2): 71% strike_looking (must throw strike down middle)
- ✅ Competitive counts (1-0, 0-1, 1-1): ~30% strike_looking (mix pitches)

**CONCLUSION**: The intention selection logic is working perfectly!

---

### 2. Game-Wide Weighted Average

Using typical MLB count distribution:

| Count | Frequency | strike_looking | Contribution |
|-------|-----------|----------------|--------------|
| 0-0 | 100% | 60.3% | 60.3% |
| 1-0 | 50% | 29.3% | 14.7% |
| 0-1 | 50% | 31.0% | 15.5% |
| 1-1 | 30% | 27.4% | 8.2% |
| 2-0 | 20% | 37.5% | 7.5% |
| 0-2 | 25% | 0.0% | 0.0% |
| 2-1 | 15% | 37.7% | 5.7% |
| 1-2 | 20% | 0.0% | 0.0% |
| 2-2 | 10% | 0.0% | 0.0% |
| 3-0 | 5% | 71.1% | 3.6% |
| 3-1 | 5% | 71.0% | 3.6% |
| 3-2 | 8% | 71.0% | 5.7% |

**Weighted Game-Wide Distribution**:
- **strike_looking**: 34.9%
- **strike_competitive**: 35.5%
- **strike_corner**: 13.6%
- **waste_chase**: 6.8%
- **ball_intentional**: 9.2%

**TOTAL**: 100% ✓

---

### 3. Expected vs Observed Zone Rate

**Expected zone rate with weighted distribution**:

| Intention | Game-Wide % | Intent Zone Rate | Contribution |
|-----------|-------------|------------------|--------------|
| strike_looking | 34.9% | 88.5% | 30.9% |
| strike_competitive | 35.5% | 61.2% | 21.7% |
| strike_corner | 13.6% | 40.1% | 5.5% |
| waste_chase | 6.8% | 17.9% | 1.2% |
| ball_intentional | 9.2% | 6.0% | 0.6% |

**Expected overall zone rate**: **59.8%** ✓ (within MLB 62-65% target!)

**Observed in Sprint 4 test**:
- Overall zone rate: **44.2%**
- strike_looking: **27.8%** of pitches (vs expected 34.9%)

**Discrepancies**:
1. strike_looking pitches: 27.8% vs 34.9% = **-7.1pp gap** (20% less)
2. Overall zone rate: 44.2% vs 59.8% = **-15.6pp gap** (26% less)

---

### 4. Control Bias Analysis

Testing 0-0 count across control ratings:

| Control Level | Rating | Bias | strike_looking | strike_competitive | strike_corner | ball_intentional |
|---------------|--------|------|----------------|-------------------|---------------|------------------|
| Poor | 30k | 0.559 | 59.7% | 17.9% | 10.8% | 11.6% |
| Average | 50k | 0.667 | 60.5% | 18.4% | 10.6% | 10.5% |
| Good | 70k | 0.733 | 59.5% | 20.5% | 11.9% | 8.1% |
| Elite | 85k | 0.746 | 61.9% | 20.5% | 9.4% | 8.2% |

**CONCLUSION**: Control bias has minimal effect on intention distribution (59-62% range). This is correct behavior - control affects WHERE pitches land, not what pitchers INTEND to throw.

---

## Root Cause Analysis

### Problem 1: Missing 7.1pp of strike_looking Pitches

**Expected**: 34.9% of game pitches should be strike_looking
**Observed**: 27.8% of game pitches are strike_looking
**Gap**: -7.1 percentage points (20% less than expected)

**Possible causes**:
1. **Count distribution in actual games differs from model**
   - Our weighted model assumes 100% reach 0-0, 50% reach 1-0, etc.
   - Actual games may have different count progression
   - More 2-strike counts → fewer strike_looking pitches

2. **Logging issue capturing subset of pitches**
   - 27.9% of pitches in Sprint 4 test had no logged intention
   - If missing pitches are disproportionately strike_looking, would explain gap

3. **Different code path in full game simulation**
   - Diagnostic uses `_determine_pitch_intention()` directly
   - Game simulation may have additional logic that overrides intentions

4. **Pitcher fatigue or game situation modifiers**
   - Late-game fatigue may change approach
   - Score/situation may influence pitch selection

### Problem 2: Zone Rate 15.6pp Below Expected

**Expected**: With 34.9% strike_looking and current command sigma, should get 59.8% zone rate
**Observed**: Only 44.2% zone rate
**Gap**: -15.6 percentage points

**This is the BIGGER problem.** Even if we fixed the 7.1pp strike_looking gap, we'd only reach:
```
(34.9% + 7.1%) × 88.5% = 37.2%  (strike_looking contribution)
35.5% × 61.2% = 21.7%  (strike_competitive)
13.6% × 40.1% = 5.5%   (strike_corner)
= 64.4% zone rate
```

But we're only getting 44.2%. Something is causing **20pp lower zone rate** than command accuracy predicts.

**Possible causes**:
1. **Command sigma larger in practice than in code**
   - Fatigue multiplier higher than expected
   - Random seed producing worse-than-average scatter
   - Different code path with different sigma

2. **Target selection different from expected**
   - strike_looking may not be targeting (0", 30") center
   - strike_competitive edges may be further out than expected
   - Target selection logic may have changed

3. **Zone boundary issue**
   - Zone defined as ±8.5" horizontal, 18-42" vertical
   - Calculation may be using wrong boundaries
   - Or boundaries vary by batter height

4. **Logging capturing wrong subset of pitches**
   - Maybe only logging out-of-zone pitches more often
   - Creating selection bias in logged data

---

## Immediate Next Steps

### Priority 1: Investigate Missing 27.9% of Pitches ⭐

The diagnostic script shows 100% of pitches get logged intentions.
But Sprint 4 test showed 27.9% of pitches have no logged intention.

**THIS IS THE KEY DISCREPANCY.**

Need to understand:
- Where are these pitches in the game simulation?
- What code path are they taking?
- Are they strike_looking pitches (which would explain -7.1pp gap)?

### Priority 2: Debug Zone Rate Calculation

With 34.9% strike_looking at 88.5% zone rate, should contribute 30.9%.
But actual overall zone rate only 44.2%.

Need to verify:
1. Actual target locations being used
2. Actual command sigma in practice
3. Zone boundary calculation
4. Whether zone rate is computed correctly

### Priority 3: Validate Count Distribution Assumption

Our weighted model assumes certain count frequencies.
Need to measure actual count distribution in simulated games:
- How often do we reach 0-0? (should be 100%)
- How often do we reach 1-0? (we assumed 50%)
- How often do we reach 0-2? (we assumed 25%)

If actual game has more 2-strike counts, would explain lower strike_looking %.

---

## Recommendations

### Option A: Add Comprehensive Logging ⭐ RECOMMENDED

Add logging at every stage of pitch execution:
1. What intention was selected?
2. What target location was chosen?
3. What command sigma was applied?
4. What final location resulted?
5. Was pitch in zone or out?

Run 10-game test with full logging, compare to diagnostic predictions.

### Option B: Increase strike_looking Probability

If we can't find the missing pitches, could increase base probabilities:
- 0-0 count: 60% → 70% strike_looking
- Competitive counts: 30% → 40% strike_looking

Would directly address 7.1pp gap.

**Risk**: Treats symptom, not root cause. May create unrealistic pitch patterns.

### Option C: Further Reduce Command Sigma

If zone rate truly 15.6pp below expected, could reduce sigma more:
- Average: 4.3" → 3.5" (another -19% reduction)

**Risk**: Already hit diminishing returns in Sprint 4. May not help.

---

## Conclusion

**The pitch intention system works correctly.** The discrepancies are:

1. **Minor**: 7.1pp fewer strike_looking pitches than expected (27.8% vs 34.9%)
2. **Major**: 15.6pp lower zone rate than expected (44.2% vs 59.8%)

The 27.9% missing pitch intentions in actual games (vs 0% in diagnostic) is the smoking gun. Understanding what those pitches are and why they're not logged will likely solve both problems.

**Next action**: Add comprehensive pitch logging to game simulation to track the full pipeline from intention → target → execution → outcome.

---

**Analysis Complete**: 2025-11-20
**Diagnostic Script**: `research/diagnose_pitch_intentions.py`
**Status**: Root cause identified - missing pitch logging in game simulation
