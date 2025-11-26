# Phase 2A: Foul Ball Tuning Recommendations

**Date**: 2025-11-20
**Diagnostic Results**: 500 PA sample
**Status**: CRITICAL - Foul rate is HALF the MLB target
**Branch**: `claude/tune-k-percent-constants-01YKoKUsdEWf7P48Ujsx4s8Q`

---

## 🚨 Critical Diagnostic Results

### Foul Ball Metrics (PRIMARY BOTTLENECK)

| Metric | Current | Target | Gap | Status |
|--------|---------|--------|-----|--------|
| **Foul Ball Rate** | **10.6%** | **20-25%** | **-10pp** | **🚨 CRITICAL** |
| **Pitches per PA** | **3.12** | **3.8-4.0** | **-0.7** | **🚨 CRITICAL** |
| 2-strike fouls | 27.5% of fouls | Should be highest | Inverted | 🚨 |

### Impact on K% and BB%

| Metric | Current | Target | Gap | Status |
|--------|---------|--------|-----|--------|
| K% | 16.2% | 22% | -5.8pp | 🚨 |
| BB% | 4.8% | 8-9% | -3.2pp | ⚠️ |
| Zone rate | 60.1% | 62-65% | -2pp | ✅ Close |

### Other Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Chase rate | 17.7% | 25-35% | ⚠️ Low |
| In-zone swing% | 58% | 65-70% | ⚠️ Low |
| Contact rate | 71.1% | 75-80% | ⚠️ Low |
| Whiff rate | 28.9% | 20-25% | ⚠️ High |

---

## Root Cause Analysis

### The Foul Ball Chain Reaction

```
Current State:
Low foul rate (10.6%) → Short at-bats (3.12 pitches) → Fewer 2-strike counts → Low K% (16.2%)

Target State:
Higher foul rate (20-25%) → Longer at-bats (3.8-4.0 pitches) → More 2-strike counts → Higher K% (22%)
```

**Mathematical Impact**:
- Current: 3.12 pitches/PA means ~1.56 pitches per half-inning PA
- Target: 3.8 pitches/PA means ~1.90 pitches per half-inning PA
- **Difference: +0.34 pitches per PA = +22% more pitch opportunities**
- This directly translates to more 2-strike counts and more K opportunities

### Why Foul Balls Matter So Much

1. **Extend at-bats**: Force batters to see more pitches
2. **Create 2-strike battles**: Most K's happen after prolonged 2-strike fouls
3. **Work pitchers**: More pitches → more fatigue → more mistakes
4. **Realistic baseball**: MLB games have long at-bats with foul balls

**Real MLB Pattern**:
- Batter gets to 2 strikes
- Fouls off 3-4 pitches protecting the plate
- Either strikes out or puts ball in play
- This pattern is MISSING from your simulation (only 27.5% of fouls with 2 strikes!)

---

## Recommended Tuning Strategy

### Phase 1: Increase Foul Ball Rate (PRIORITY 1)

**Goal**: 10.6% → 20-25% foul rate

**File**: `batted_ball/at_bat.py` lines 1106-1133

#### Option A: Increase Weak Contact Foul Probability (CONSERVATIVE)

**Current**:
```python
# Weak contact more likely to foul (reduced from 0.4 to 0.22 to increase balls in play)
# Previous 40% rate was causing too many fouls and reducing offensive production
if contact_quality == 'weak' and np.random.random() < 0.22:
    is_foul = True
```

**Recommended**:
```python
# Weak contact more likely to foul
# Calibrated for 20-25% overall foul rate to achieve MLB-realistic at-bat lengths
if contact_quality == 'weak' and np.random.random() < 0.38:  # Increased from 0.22
    is_foul = True
```

**Rationale**: The comment says 0.40 was "too many fouls", but diagnostic shows 0.22 is far too few. Try 0.38 as middle ground.

#### Option B: Add Count-Dependent Foul Probability (RECOMMENDED)

**Add after existing foul logic** (after line 1125):

```python
# 2-strike protection fouls (batters "protecting the plate")
# With 2 strikes, batters take defensive swings that often result in fouls
# This is the PRIMARY source of foul balls in MLB
if strikes >= 2 and not is_foul:  # Only apply if not already marked foul
    # Even solid/fair contact can go foul when protecting with 2 strikes
    # Probability scales with contact quality:
    # - Solid contact: 10% chance of protection foul
    # - Fair contact: 15% chance of protection foul
    # - Weak contact: Already handled above
    if contact_quality == 'solid':
        protection_foul_prob = 0.10
    elif contact_quality == 'fair':
        protection_foul_prob = 0.15
    else:  # weak (already has high foul chance above)
        protection_foul_prob = 0.05  # Small additional boost

    if np.random.random() < protection_foul_prob:
        is_foul = True
```

**Rationale**: This creates the realistic MLB pattern where batters with 2 strikes foul off multiple pitches. Should increase 2-strike fouls from 27.5% → 40-50% of all fouls.

#### Option C: Adjust Extreme Angle Thresholds (MINOR TWEAK)

**Current**:
```python
# Launch angle fouls (pop-ups behind or ground balls foul)
if launch_angle < -10 or launch_angle > 60:
    is_foul = True
```

**Recommended**:
```python
# Launch angle fouls (pop-ups behind or ground balls foul)
# Slightly more lenient to capture more realistic foul territory
if launch_angle < -8 or launch_angle > 65:  # Was -10 to 60
    is_foul = True
```

**Rationale**: Minor adjustment to capture a few more edge cases.

#### Option D: Add Fair/Solid Contact Foul Probability (AGGRESSIVE)

**Add after weak contact foul logic**:

```python
# Fair contact can also go foul (less likely than weak)
if contact_quality == 'fair' and np.random.random() < 0.12:
    is_foul = True

# Even solid contact occasionally goes foul (rare)
if contact_quality == 'solid' and np.random.random() < 0.05:
    is_foul = True
```

**Rationale**: Not all fouls are weak contact. Even good swings can go foul due to timing/location.

### Recommended Implementation: **Option B + partial Option A**

```python
# Combined approach for maximum realism:

# 1. Increase weak contact foul rate (was too low)
if contact_quality == 'weak' and np.random.random() < 0.35:  # Was 0.22
    is_foul = True

# 2. Add 2-strike protection fouls (NEW - most important!)
if strikes >= 2 and not is_foul:
    if contact_quality == 'solid':
        protection_foul_prob = 0.10
    elif contact_quality == 'fair':
        protection_foul_prob = 0.15
    else:  # weak
        protection_foul_prob = 0.05

    if np.random.random() < protection_foul_prob:
        is_foul = True
```

**Expected Impact**:
- Foul rate: 10.6% → 22-24% ✅
- 2-strike fouls: 27.5% → 45-50% of all fouls ✅
- Pitches/PA: 3.12 → 3.7-3.9 ✅
- K%: 16.2% → ~20-21% (closer to 22% target) ✅

---

## Phase 2: Fix Pitch Intention Distribution (PRIORITY 2)

### Critical Issue Discovered

Your diagnostic shows a MASSIVE discrepancy in pitch intentions:

| Intention | Current | Expected | Difference | Status |
|-----------|---------|----------|------------|--------|
| strike_competitive | 10.5% | 35.5% | **-25.0pp** | 🚨🚨🚨 |
| ball_intentional | 33.4% | 9.2% | **+24.2pp** | 🚨🚨🚨 |
| strike_looking | 31.0% | 34.9% | -3.9pp | ⚠️ |
| strike_corner | 16.3% | 13.6% | +2.7pp | ✅ |
| waste_chase | 8.9% | 6.8% | +2.1pp | ✅ |

**Problem**: Pitchers are throwing 3.6× more intentional balls than expected and 3.4× fewer competitive strikes!

**Impact**: This is likely contributing to:
- Low BB% (4.8% vs 8-9%) - Paradoxically, batters are chasing the intentional balls
- Short at-bats - Not enough competitive strikes to work counts

### Investigate Pitcher Control Module

**File**: `batted_ball/pitcher_control.py`

This is a V2 Phase 2B module that controls zone targeting. Something may be wrong with the count-based targeting logic.

**Hypothesis**: The nibbling tendency or 3-ball count targeting is too aggressive, causing pitchers to aim outside the zone too often.

**Check**:
1. `BB_ZONE_TARGET_THREE_BALL` constant - May be too low
2. Nibbling tendency logic - May be too strong
3. Strike intention classifications - May be miscategorized

**Recommendation**: This needs a separate investigation. For now, focus on foul balls (higher priority).

---

## Phase 3: Tune Swing Decisions (PRIORITY 3)

### Current Issues

- Chase rate: 17.7% (target: 25-35%) - Still too low
- In-zone swing%: 58% (target: 65-70%) - Still too low

### Why These Matter Less Than Fouls

With longer at-bats from foul balls, these metrics will naturally improve:
- More 2-strike counts → more protective swings → higher in-zone swing%
- More 2-strike counts → more chasing waste pitches → higher chase rate

**Recommendation**: Wait until after foul ball tuning to see if these self-correct. If not, then tune swing decisions in player.py.

---

## Testing Protocol

### Step 1: Apply Foul Ball Tuning

Implement recommended changes to `batted_ball/at_bat.py`:
- Increase weak contact foul rate: 0.22 → 0.35
- Add 2-strike protection foul logic (NEW)

### Step 2: Run Diagnostic

```bash
python research/run_50game_fixed_diagnostic.py
```

### Step 3: Verify Targets

**Success Criteria** (after foul tuning):
- ✅ Foul rate: 20-25% (currently 10.6%)
- ✅ Pitches/PA: 3.7-4.0 (currently 3.12)
- ✅ 2-strike fouls: 40-50% of fouls (currently 27.5%)
- ✅ K%: 20-22% (currently 16.2%)
- ✅ BB%: 6-9% (currently 4.8%)

### Step 4: Iterate if Needed

If foul rate still too low:
- Increase weak contact probability further (0.35 → 0.40)
- Increase 2-strike protection probabilities (+0.05 each)

If foul rate too high (> 30%):
- Reduce weak contact probability (0.35 → 0.30)
- Reduce 2-strike protection probabilities (-0.05 each)

---

## Expected Final Results

### After Foul Ball Tuning

| Metric | Before | After | Target | Status |
|--------|--------|-------|--------|--------|
| Foul rate | 10.6% | **22%** | 20-25% | ✅ |
| Pitches/PA | 3.12 | **3.8** | 3.8-4.0 | ✅ |
| K% | 16.2% | **~21%** | 22% | ⚠️ Close |
| BB% | 4.8% | **~7%** | 8-9% | ⚠️ Close |

### After Swing Decision Tuning (if needed)

| Metric | Before | After | Target | Status |
|--------|--------|-------|--------|--------|
| K% | ~21% | **22%** | 22% | ✅ |
| BB% | ~7% | **8-9%** | 8-9% | ✅ |
| Chase rate | 17.7% | **27%** | 25-35% | ✅ |
| In-zone swing% | 58% | **67%** | 65-70% | ✅ |

---

## Code Changes Summary

### batted_ball/at_bat.py (lines 1122-1126)

**BEFORE**:
```python
# Weak contact more likely to foul (reduced from 0.4 to 0.22 to increase balls in play)
# Previous 40% rate was causing too many fouls and reducing offensive production
if contact_quality == 'weak' and np.random.random() < 0.22:
    is_foul = True
```

**AFTER**:
```python
# Weak contact more likely to foul
# Calibrated for MLB-realistic foul rate (20-25% of swings)
if contact_quality == 'weak' and np.random.random() < 0.35:  # Increased from 0.22
    is_foul = True

# 2-strike protection fouls - batters defending the plate with 2 strikes
# This is the PRIMARY source of prolonged at-bats in MLB
# Defensive swings often result in fouls even on decent contact
if strikes >= 2 and not is_foul:
    # Protection foul probability by contact quality
    if contact_quality == 'solid':
        protection_foul_prob = 0.10  # 10% chance even on good contact
    elif contact_quality == 'fair':
        protection_foul_prob = 0.15  # 15% chance on fair contact
    else:  # weak (already has high foul chance above)
        protection_foul_prob = 0.05  # Small additional boost

    if np.random.random() < protection_foul_prob:
        is_foul = True
```

---

## Next Steps

1. **Apply foul ball tuning** (recommended code above)
2. **Run diagnostic** to measure impact
3. **Share results** for analysis
4. **Iterate if needed** (tune probabilities)
5. **Move to swing decisions** if K% still below target after foul tuning

---

## References

- Original handoff: Phase 2B complete, Phase 2A needs K% tuning
- Enhanced diagnostic: `research/run_50game_fixed_diagnostic.py`
- Foul ball analysis: `research/PHASE_2A_FOUL_BALL_ANALYSIS.md`
- At-bat simulator: `batted_ball/at_bat.py`

---

**Ready to implement!** The foul ball fix is clear and well-scoped.
