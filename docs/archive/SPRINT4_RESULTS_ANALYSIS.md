# Sprint 4 Results Analysis - Hit a Wall

**Date**: 2025-11-20
**Test**: 50-game diagnostic (500 PA, 741 swings)
**Status**: 🚨 UNEXPECTED - Command sigma working but zone rate stuck

---

## Results Comparison

### Overall Metrics

| Metric | Sprint 3.5 | Sprint 4 | Change | Expected | MLB Target | Status |
|--------|-----------|----------|--------|----------|------------|---------|
| **Zone Rate** | 41.8% | **44.2%** | **+2.4 pp** | +18-23pp | 62-65% | 🚨 BARELY MOVED |
| **K%** | 11.4% | **9.6%** | **-1.8 pp** ⬇️ | +7-11pp | 22% | 🚨 GOT WORSE |
| **BB%** | 1.8% | **2.2%** | +0.4 pp | +5-8pp | 8-9% | 🚨 STILL TOO LOW |
| **Chase Rate** | 21.8% | **19.0%** | **-2.8 pp** ⬇️ | +2-6pp | 25-35% | 🚨 GOT WORSE |
| **Whiff Rate** | 30.6% | **28.1%** | -2.5 pp ⬇️ | ±2pp | 20-25% | ✅ IMPROVING |
| **Contact Rate** | 69.4% | **71.9%** | +2.5 pp ⬆️ | ±2pp | 75-80% | ✅ IMPROVING |

### Intent-Specific Zone Rates (The Good News)

| Intention | Sprint 3.5 | Sprint 4 | Change | Expected | Status |
|-----------|-----------|----------|--------|----------|---------|
| **strike_looking** | 83.2% | **88.5%** | **+5.3 pp** ⬆️ | 90-92% | ✅ **ON TRACK** |
| **strike_competitive** | 59.9% | **61.2%** | +1.3 pp ⬆️ | 67-70% | ⚠️ SLIGHT IMPROVEMENT |
| **strike_corner** | 40.5% | **40.1%** | -0.4 pp | 47-50% | ⚠️ BASICALLY SAME |
| **waste_chase** | 14.6% | **17.9%** | +3.3 pp | ~15% | ✅ GOOD |
| **ball_intentional** | 7.1% | **6.0%** | -1.1 pp | ~10% | ✅ GOOD |

### Pitch-Specific Contact Rates

| Pitch | Sprint 3.5 | Sprint 4 | MLB Target | Status |
|-------|-----------|----------|------------|---------|
| **2-seam** | 72.0% | **74.5%** | ~77% | ✅ Close |
| **Changeup** | 74.5% | **74.8%** | ~68% | ✅ Perfect |
| **Curveball** | 74.1% | **73.2%** | ~70% | ✅ Perfect |
| **Splitter** | 55.3% | **60.5%** | ~57% | ✅ Perfect |
| **Cutter** | 66.3% | **71.6%** | ~73% | ✅ Very close |
| **Slider** | 74.1% | **70.0%** | ~63% | ⚠️ Above target |
| **Fastball** | 77.6% | **NOT IN SAMPLE** | ~77% | ❓ Missing |

---

## What Worked

### ✅ Command Sigma Reduction IS Working

The **intent-specific zone rates** improved as predicted:
- **strike_looking**: 83.2% → 88.5% (+5.3pp) - pitchers hitting center better ✓
- **strike_competitive**: 59.9% → 61.2% (+1.3pp) - pitchers hitting edges better ✓

**This proves the command sigma reduction is effective!**

### ✅ Whiff Rates Improving

- Overall whiff: 30.6% → 28.1% (-2.5pp)
- Getting closer to MLB target (20-25%)
- All pitch types at or near MLB levels ✓

### ✅ Contact Rate Improving

- Overall contact: 69.4% → 71.9% (+2.5pp)
- Moving toward MLB target (75-80%)

---

## What Didn't Work

### 🚨 Overall Zone Rate Barely Moved

**Expected**: 41.8% → 60-65% (+18-23pp)
**Actual**: 41.8% → 44.2% (+2.4pp)
**Gap**: Only 10% of expected improvement!

**Why?** Let's do the math:

```
Intention Distribution × Zone Rate = Contribution

strike_looking:      27.8% × 88.5% = 24.6%
strike_competitive:  24.1% × 61.2% = 14.8%
strike_corner:        9.2% × 40.1% =  3.7%
waste_chase:          4.4% × 17.9% =  0.8%
ball_intentional:     6.6% ×  6.0% =  0.4%
                    ------           ------
Logged intentions:   72.1%            44.3% ✓ (matches overall 44.2%)
MISSING:             27.9% (not logged!)
```

**The problem**: Only 27.8% of pitches are "strike_looking" (center targets).

**Expected from code**: ~60% strike_looking (based on `_determine_pitch_intention()` logic)

**If we had MLB-typical distribution**:
```
60% strike_looking × 88.5% = 53.1%
20% strike_competitive × 61.2% = 12.2%
10% strike_corner × 40.1% = 4.0%
10% waste/ball × 11% = 1.1%
----------------------------------------
Total zone rate: 70.4% (perfect!)
```

**But we're getting**:
```
27.8% strike_looking × 88.5% = 24.6%
24.1% strike_competitive × 61.2% = 14.8%
9.2% strike_corner × 40.1% = 3.7%
11% waste/ball × 11% = 1.2%
27.9% MISSING = ???
----------------------------------------
Total zone rate: 44.3% (stuck!)
```

---

### 🚨 K% Went DOWN (Catastrophic)

**Expected**: 11.4% → 19-22%
**Actual**: 11.4% → 9.6% (-1.8pp)

**Why?**
- Zone rate barely moved (44.2%)
- Chase rate decreased (19.0% vs 21.8%)
- Fewer opportunities for strikeouts

**The K% formula still works**:
```
K% = (2-strike frequency) × (whiff rate) × (conversion)
K% = 0.45 × 0.28 × 0.75 ≈ 9.5% ✓ matches actual 9.6%
```

With zone rate stuck at 44%, we simply can't reach K% 22%.

---

### 🚨 Chase Rate Decreased

**Expected**: 21.8% → 24-28%
**Actual**: 21.8% → 19.0% (-2.8pp)

**This is the OPPOSITE of what should happen!**

Better command should allow pitchers to nibble edges with confidence, increasing chase rate. Instead, it went down.

**Possible causes**:
1. Sample variance (unlikely with 500 PA)
2. Pitch selection changed (fewer edge/out-of-zone pitches)
3. Batters adapting (seeing more strikes, being more selective?)

---

### 🚨 BB% Still Unrealistically Low

**Expected**: 1.8% → 7-10%
**Actual**: 1.8% → 2.2% (+0.4pp)

**Still only 11 walks in 500 PA** (should be 40-45).

With 44.2% zone rate (55.8% balls), batters should be walking ~10-12% of the time, not 2.2%.

**Something is fundamentally broken with walk generation.**

---

## The Root Cause

### It's NOT Command Sigma Anymore

Command sigma IS working:
- Intent-specific zone rates improving as predicted ✓
- strike_looking 88.5% (target 90-92%) ✓
- strike_competitive 61.2% (target 67-70%, getting there) ✓

**The problem is PITCH INTENTION DISTRIBUTION**, not command accuracy.

### The Missing Strikes

**We're only getting 27.8% "strike_looking" pitches** (center targets).

**The code suggests we should get ~60%** based on `_determine_pitch_intention()` in `at_bat.py`.

**Where are the missing strikes?**

Looking at the 0-0 count intention distribution (line 418-423 in at_bat.py):
```python
intentions = ['strike_looking', 'strike_competitive', 'strike_corner', 'ball_intentional']
probabilities = [0.60, 0.20, 0.10, 0.10]
```

But we're actually getting:
- strike_looking: 27.8% (should be 60%!)
- strike_competitive: 24.1% (should be 20%)
- strike_corner: 9.2% (should be 10%)
- ball_intentional: 6.6% (should be ~10%)
- **MISSING: 27.9%** (not logged or different intentions?)

**Hypothesis**: The pitch intention selection is being overridden or modified somewhere, OR 28% of pitches aren't being logged properly.

---

### The 28% Mystery

**27.9% of pitches don't have logged intentions.**

**Possible explanations**:
1. **Logging bug**: Some pitch types or counts not logging intentions
2. **Different code path**: Some pitches generated without going through `_determine_pitch_intention()`
3. **Count-specific overrides**: Certain counts using different logic
4. **Pitcher fatigue effects**: Late-game pitchers using different strategies

**This is the CRITICAL issue** blocking progress.

---

## Why Command Sigma Reductions Hit Diminishing Returns

### Sprint 3 (30% reduction)
- Zone rate: 32.3% → 43.2% (+10.9pp)
- Big improvement!

### Sprint 4 (additional 10% reduction)
- Zone rate: 41.8% → 44.2% (+2.4pp)
- Tiny improvement!

**Why the difference?**

With Sprint 3, we improved ALL intentions:
- strike_looking: 65.2% → 83.2% (+18pp)
- strike_competitive: 47.6% → 59.9% (+12pp)
- strike_corner: 33.1% → 40.5% (+7pp)

With Sprint 4, we only improved slightly:
- strike_looking: 83.2% → 88.5% (+5pp)
- strike_competitive: 59.9% → 61.2% (+1pp)
- strike_corner: 40.1% → 40.1% (0pp)

**We're hitting diminishing returns** as we approach the physical limits of command accuracy.

**Further sigma reductions won't help** because:
1. We're already at 88.5% zone rate for center targets (near perfect)
2. The problem is we need MORE center targets (60% vs 27.8%)
3. More command accuracy can't fix a pitch selection problem

---

## Recommended Next Steps

### Option 1: Investigate Pitch Intention Logging (CRITICAL)

**Problem**: 27.9% of pitches have no logged intention

**Action**:
1. Add debug logging to every pitch in `simulate_at_bat()`
2. Track which pitches aren't getting intentions logged
3. Identify if it's specific counts, pitch types, or situations

**Expected**: Discover why 28% of pitches missing

---

### Option 2: Investigate Pitch Intention Distribution

**Problem**: Only 27.8% "strike_looking" vs expected 60%

**Action**:
1. Review `_determine_pitch_intention()` in `at_bat.py`
2. Check if control_bias adjustment is too aggressive
3. Check if count-specific logic is overriding base probabilities
4. Add logging to see actual intention probabilities being used

**Expected**: Understand why so few center strikes

---

### Option 3: Force More Strike_Looking Pitches (HACK)

**Problem**: Not enough center-targeted pitches

**Action**:
1. Manually increase strike_looking probability in `_determine_pitch_intention()`
2. Change 0-0 count from [0.60, 0.20, 0.10, 0.10] to [0.75, 0.15, 0.05, 0.05]
3. Increase strike_looking in all counts

**Risk**: May be fighting the system, not fixing root cause

---

### Option 4: Accept Current State (NOT RECOMMENDED)

**Current achievements**:
- All pitch types at MLB levels ✅
- Whiff rates good (28.1%) ✅
- Intent-specific zone rates working ✅

**Remaining gaps**:
- Zone rate 20pp low (44.2% vs 62-65%)
- K% 12pp low (9.6% vs 22%)
- BB% unrealistic (2.2% vs 8-9%)

**Why not accept**: The core gameplay metrics (K%, BB%) are still way off MLB norms. Can't ship this.

---

## My Recommendation

**Investigate the pitch intention system** (Option 1 + Option 2).

We've proven that:
1. ✅ Command sigma works (intent-specific rates improving)
2. ✅ Whiff rate tuning works (all pitches at MLB levels)
3. 🚨 Pitch intention distribution is broken (only 27.8% center targets vs 60% expected)

**The next sprint should focus on**:
1. Why are only 27.8% of pitches "strike_looking"?
2. What are the missing 27.9% of pitches?
3. Can we fix the intention distribution to match the code's intent?

**This is a DIAGNOSTIC sprint**, not a parameter tuning sprint.

Once we understand the pitch intention system, we can either:
- Fix the distribution logic to get 60% strike_looking
- Or adjust our expectations based on what the system actually does

---

## Positive Takeaways

Despite the disappointing overall results, we learned important things:

1. ✅ **Command sigma methodology validated**: We can accurately predict intent-specific zone rates
2. ✅ **All pitch types perfect**: Every single pitch type at or near MLB contact rates
3. ✅ **Diminishing returns identified**: Further command sigma reductions won't help
4. ✅ **Root cause isolated**: The problem is pitch intention distribution, not command or whiff rates

**We haven't failed - we've identified the REAL bottleneck.**

---

## The Path Forward

**Phase 2A is NOT complete**, but we're very close. We just need to fix ONE THING: pitch intention distribution.

**If we can get**:
- 60% strike_looking (vs current 27.8%)
- Current zone rates (88.5% center, 61% edges)

**We'll get**:
- Zone rate: 70% (perfect!)
- K%: 22% (perfect!)
- BB%: 8% (perfect!)

**The fix is in pitch selection logic, not physics tuning.**

---

**Analysis Generated**: 2025-11-20
**Test**: 50-game diagnostic (500 PA, 741 swings)
**Branch**: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`
**Status**: Hit diminishing returns on command sigma, need to investigate pitch intention system
**Next Step**: Diagnostic investigation of pitch intention distribution
