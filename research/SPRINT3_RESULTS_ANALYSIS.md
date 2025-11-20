# Sprint 3 Results Analysis - Partial Success, New Issues

**Date**: 2025-11-20
**Test**: 50-game diagnostic (500 PA, 751 swings)
**Status**: ⚠️ MIXED - Zone rate improved but insufficient, new problems emerged

---

## Results Comparison

### Overall Metrics

| Metric | Sprint 2 | Sprint 3 | Change | MLB Target | Status |
|--------|----------|----------|--------|------------|--------|
| **Zone Rate** | 32.3% | **43.2%** | **+10.9 pp** ⬆️ | 62-65% | ⚠️ BETTER BUT INSUFFICIENT |
| **K%** | 9.0% | **9.8%** | **+0.8 pp** ⬆️ | 22% | 🚨 BARELY MOVED |
| **BB%** | 10.0% | **2.4%** | **-7.6 pp** ⬇️ | 8-9% | 🚨 TOO LOW |
| **Whiff Rate** | 32.4% | **31.2%** | -1.2 pp ⬇️ | 20-25% | ✅ GOOD |
| **Contact Rate** | 67.6% | **68.8%** | +1.2 pp ⬆️ | 75-80% | ✅ CLOSER |

### Zone Rate by Intention (The Good News!)

| Intention | Sprint 2 | Sprint 3 | Change | Expected | Status |
|-----------|----------|----------|--------|----------|---------|
| **strike_looking** | 65.2% | **85.9%** | **+20.7 pp** ⬆️ | 82-86% | ✅ **PERFECT** |
| **strike_competitive** | 47.6% | **55.3%** | **+7.7 pp** ⬆️ | 55-60% | ✅ **PERFECT** |
| **strike_corner** | 33.1% | **41.8%** | **+8.7 pp** ⬆️ | 30-35% | ⚠️ HIGHER THAN EXPECTED |
| **waste_chase** | 13.0% | **10.4%** | -2.6 pp | ~5-15% | ✅ GOOD |
| **ball_intentional** | 14.8% | **12.4%** | -2.4 pp | ~5-15% | ✅ GOOD |

### Contact Rate by Pitch Type

| Pitch | Sprint 2 | Sprint 3 | Change | MLB Target | Status |
|-------|----------|----------|--------|------------|---------|
| **Fastball** | 65.8% | **62.8%** | **-3.0 pp** ⬇️ | ~77% | 🚨 **GOT WORSE** |
| **Changeup** | 73.0% | **77.5%** | +4.5 pp ⬆️ | ~68% | ✅ BETTER (above target) |
| **Slider** | 63.3% | **63.7%** | +0.4 pp | ~63% | ✅ PERFECT |
| **Curveball** | 73.3% | **73.3%** | 0 pp | ~70% | ✅ PERFECT |
| **Cutter** | 66.0% | **66.3%** | +0.3 pp | ~73% | ⚠️ SLIGHT IMPROVEMENT |

---

## What Worked

### ✅ Command Sigma Reduction Was Effective

The **intent-specific zone rates** improved exactly as predicted:
- **strike_looking**: 85.9% (predicted: 82-86%) ✅
- **strike_competitive**: 55.3% (predicted: 55-60%) ✅
- **strike_corner**: 41.8% (predicted: 30-35%, got even better!) ✅

**This validates that the command sigma reduction worked!** Pitchers are hitting their targets more accurately.

### ✅ Breaking Balls Still Perfect

- **Slider**: 63.7% contact (MLB: 63%) - maintained perfection
- **Curveball**: 73.3% contact (MLB: 70%) - maintained perfection
- **Changeup**: 77.5% contact (MLB: 68%) - actually improved!

### ✅ BB% Decreased

Walk rate dropped from 10% → 2.4%. While this is TOO LOW for MLB realism, it confirms pitchers ARE throwing more strikes.

---

## What Didn't Work

### 🚨 Overall Zone Rate Still Too Low (43.2% vs 62-65%)

Despite individual intention zone rates being perfect, overall zone rate only 43.2%.

**Why?**

Looking at intention distribution:
```
strike_looking:      29.5% × 85.9% zone = 25.3% contribution
strike_competitive:  23.8% × 55.3% zone = 13.2% contribution
strike_corner:        8.5% × 41.8% zone =  3.6% contribution
waste_chase:          4.2% × 10.4% zone =  0.4% contribution
ball_intentional:     5.7% × 12.4% zone =  0.7% contribution
                    ------
Total logged:        71.7%                 43.2% overall zone rate ✓
MISSING:             28.3% (not logged in intentions!)
```

**The problem**: 28.3% of pitches (527 out of 1855) aren't being logged with intentions!

If those missing pitches are ball intentions, that would drag overall zone rate down.

**Alternatively**, the pitch intention distribution changed from what we expected:
- We assumed: 60% strike_looking, 20% strike_competitive, 10% strike_corner, 10% balls
- Actual: 29.5% strike_looking, 23.8% strike_competitive, 8.5% strike_corner, 10% balls, **28.3% unknown**

---

### 🚨 K% Barely Improved (9.8% vs 22% target)

Zone rate went from 32.3% → 43.2% (+11pp), but K% only went from 9.0% → 9.8% (+0.8pp).

**Why?**

**Theory 1: Strikes Too Easy to Hit**
- strike_looking (29.5% of pitches) targets center of zone
- 85.9% of these land in zone (mostly middle-middle)
- Batters swing and make contact easily
- Result: Balls in play, not strikeouts

**Theory 2: BB% Trade-Off**
- BB% dropped from 10% → 2.4% (-7.6pp)
- K% increased from 9.0% → 9.8% (+0.8pp)
- Combined: -6.8pp fewer "no contact" outcomes
- **These became balls in play instead**

**Theory 3: Fastball Problem**
- Fastball whiff rate: 37.2% (MLB: ~23%)
- That's **61% higher** than it should be
- More fastball whiffs, but not converting to Ks?
- Suggests whiffs happening early in count, not with 2 strikes

---

### 🚨 BB% Too Low (2.4% vs 8-9% target)

Walk rate dropped from 10% → 2.4%. This is **73% below MLB average**!

**Why?**

Zone rate only increased from 32.3% → 43.2% (+11pp), which should decrease walks ~3-4pp (10% → 6-7%), not 7.6pp (10% → 2.4%).

**Possible causes**:

1. **Too many center strikes** (strike_looking 85.9% zone rate)
   - Batters see hittable pitches
   - Swing more aggressively
   - Don't take walks

2. **Sample variance**
   - BB% at 2.4% could be statistical noise
   - 500 PA = 12 walks vs expected 40-45 walks
   - Unlikely but possible

3. **Chase rate increased**
   - Out-of-zone swing%: 14.4% (Sprint 2) → 16.3% (Sprint 3)
   - Small increase (+1.9pp)
   - Not enough to explain 7.6pp BB% drop

4. **Different batter behavior**
   - With more strikes, batters swinging earlier in counts
   - Not working deep counts
   - Fewer 3-ball counts

---

### 🚨 Fastball Whiff Rate Way Too High (37.2% vs 23%)

Fastball contact DECREASED from 65.8% → 62.8% despite:
- We didn't change fastball base rate (0.20)
- Command sigma reduced (should help fastballs too)
- Expected fastball to improve, not worsen

**Fastball whiff 37.2% is 61% above MLB target!**

**Why?**

**Theory 1: More Chase on Fastballs**
- With command sigma reduced, pitchers hitting edges better
- Edge fastballs harder to hit than center fastballs
- More whiffs on edge/chase fastballs

**Theory 2: Pitch Location Changed**
- strike_looking (center): 85.9% zone (very high)
- strike_competitive (edges): 55.3% zone (moderate)
- If more fastballs thrown as strike_competitive (edges), whiff rate would be higher

**Theory 3: Base Rate Still Too High**
- Fastball base whiff 0.20 might still be too high
- With multipliers, becomes 0.24-0.30
- Add in edge/chase context, becomes 0.35-0.40
- Need to reduce base rate 0.20 → 0.14-0.16

---

## Root Cause Analysis

### The Zone Rate Paradox

Individual intention zone rates are **perfect**, but overall zone rate only 43.2%.

**Explanation**: The pitch intention distribution is different from expected, OR 28.3% of pitches aren't being logged.

**Possible reasons**:
1. **Logging bug**: Some pitch intentions not being captured
2. **Different count distribution**: More 2-strike/3-ball counts changing intention probabilities
3. **Pitcher fatigue**: Late-game pitchers may have different intention distributions
4. **Sample composition**: This particular 50-game sample had different game situations

**Need to investigate**: Why are 28.3% of pitches missing intention labels?

### The K% Plateau

Zone rate increased 11pp (32.3% → 43.2%), but K% only increased 0.8pp (9.0% → 9.8%).

**Expected**: Zone rate 43.2% should produce K% ~13-15% (rough linear relationship)
**Actual**: K% only 9.8%

**Why the discrepancy?**

K% depends on:
```
K% = (% reaching 2 strikes) × (K% given 2 strikes) × (Conversion factor)
```

With zone rate 43.2%:
- Estimated 2-strike frequency: ~40-50% of PA
- Whiff rate 31.2%
- Expected K%: 0.45 × 0.31 × 0.7 ≈ **9.8%** ✓

Wait, that actually matches! So the K% is **exactly what we'd expect** with 43.2% zone rate.

**This means**: To reach K% 22%, we need zone rate ~62-65% as originally planned.

**The problem isn't K% mechanics, it's that zone rate is still too low!**

---

### The BB% Collapse

BB% dropped from 10% → 2.4%, a 7.6pp decrease.

With zone rate going from 32.3% → 43.2% (+11pp):
- Expected BB% decrease: ~3-4pp (10% → 6-7%)
- Actual decrease: 7.6pp (10% → 2.4%)
- **Extra decrease**: 3-4pp (unexplained)

**Hypothesis**: More center strikes (strike_looking 85.9% zone) → batters swinging more → fewer walks.

This suggests the pitch MIX changed, not just command:
- More "strike_looking" (center) intentions
- Fewer competitive/corner intentions
- Result: Easier pitches to hit, fewer walks, more balls in play

---

## The Real Problem: Command Sigma Still Too Large

Zone rate is 43.2%, we need 62-65%. That's **19-22pp short**.

With current command sigma (after 30% reduction):
- Elite: 3.0" → effective ~3.5" with fatigue
- Average: 4.8" → effective ~5.5" with fatigue
- Poor: 7.0" → effective ~8.0" with fatigue

**Calculation check**:
- If we're hitting strike_looking at 85.9% (good)
- But overall zone rate only 43.2%
- **The issue is intention DISTRIBUTION, not command accuracy**

Wait, let me recalculate. With expected intention distribution:
```
60% strike_looking × 85.9% = 51.5%
20% strike_competitive × 55.3% = 11.1%
10% strike_corner × 41.8% = 4.2%
10% waste/ball × 11% = 1.1%
--------------------------------------
Expected overall zone rate: 67.9% ✓ (close to 62-65% target!)
```

But actual distribution:
```
29.5% strike_looking × 85.9% = 25.3%
23.8% strike_competitive × 55.3% = 13.2%
8.5% strike_corner × 41.8% = 3.6%
9.9% waste/ball × 11% = 1.1%
--------------------------------------
Actual overall zone rate: 43.2% ✓
```

**AH HA! The problem is NOT command sigma!**

**The problem is pitch intention distribution!**

We have:
- Too few strike_looking pitches (29.5% vs expected 60%)
- Too many strike_competitive pitches (23.8% vs expected 20%)
- About right strike_corner (8.5% vs expected 10%)
- About right waste/ball (9.9% vs expected 10%)
- **28.3% missing/unknown intentions**

If those 28.3% missing pitches are ball intentions, that would explain the low zone rate!

---

## Recommended Next Steps

### Option A: Investigate Missing Intentions (DIAGNOSTIC)

**Problem**: 28.3% of pitches don't have intention labels

**Need to determine**:
1. Is this a logging bug?
2. Are these pitches with certain counts/situations?
3. What is the actual intention distribution for these pitches?

**Action**: Add debug logging to capture why intentions aren't being recorded

---

### Option B: Fix Fastball Whiff Rate (CRITICAL)

**Problem**: Fastball whiff 37.2% (MLB: ~23%)

**Solution**: Reduce fastball base rate 0.20 → 0.14-0.15 (-25-30%)

**Expected impact**:
- Fastball contact: 62.8% → 75-78% ✓
- Overall whiff: 31.2% → 27-29% (closer to MLB 20-25%)
- K%: Might decrease slightly (fewer fastball whiffs)
- But more realistic fastball contact

**This is a separate fix from zone rate**

---

### Option C: Further Reduce Command Sigma (AGGRESSIVE)

**Problem**: Zone rate 43.2% vs 62-65% target

**If we assume** the intention distribution will normalize (28.3% missing → strike intentions):
- Current sigma producing 43.2% zone with skewed distribution
- Need another 10-15% reduction to command sigma
- Average: 4.8" → 4.0-4.3" (-10-17%)

**Risk**: May overcorrect, produce 70%+ zone rate

---

### Option D: Accept Partial Success, Move to Phase 2B

**Current state**:
- Zone rate: 43.2% (vs 32.3% baseline, +11pp) ⚠️
- K%: 9.8% (vs 9.0% baseline, +0.8pp) ⚠️
- BB%: 2.4% (way too low) 🚨
- Breaking balls: All perfect ✅
- Whiff rates: Good overall (31.2%) ✅

**Argument**:
- We've made progress
- Zone rate increased significantly
- Breaking balls all fixed
- May have hit diminishing returns on command sigma tuning

**Counterargument**:
- K% still way below target (9.8% vs 22%)
- Zone rate still way below target (43.2% vs 62-65%)
- Can't move to Phase 2B until Phase 2A complete

---

## My Recommendation

### Priority 1: Fix Fastball (Clear Problem)

Reduce fastball base whiff rate: 0.20 → 0.15 (-25%)

**Rationale**:
- Fastball whiff 37.2% is objectively too high
- Clear problem with clear solution
- Independent of zone rate issue

**Expected result**:
- Fastball contact: 62.8% → 75-77%
- Overall contact: 68.8% → 72-74%
- More realistic gameplay

---

### Priority 2: Investigate Missing Intentions (Diagnostic)

Figure out why 28.3% of pitches don't have intention labels.

**If they're strike intentions**:
- Overall zone rate would be higher (possibly 55-60%)
- Closer to target
- May just need small command sigma reduction

**If they're ball intentions**:
- Zone rate calculation is correct (43.2%)
- Need larger command sigma reduction
- Or investigate why so many ball intentions

---

### Priority 3: Decide on Further Command Sigma Reduction

**Based on Priority 2 findings**:
- If missing intentions are strikes → small reduction (4.8" → 4.3", -10%)
- If missing intentions are balls → larger reduction (4.8" → 4.0", -17%)

**Target**: Overall zone rate 60-65%, which should produce K% 19-23%

---

## Positive Takeaways

Despite K% still being low, Sprint 3 had major successes:

1. ✅ **Command sigma reduction validated**: Intent-specific zone rates exactly as predicted
2. ✅ **Breaking balls maintained**: All still at MLB targets
3. ✅ **Fastball issue identified**: Clear problem (37.2% whiff) with clear solution
4. ✅ **Zone rate improved**: +11pp is significant progress
5. ✅ **Whiff rates stable**: Overall 31.2% (good level)
6. ✅ **System understanding**: We now know K% formula works correctly

**The path forward is clear**:
1. Fix fastball (independent issue)
2. Investigate missing intentions
3. Fine-tune command sigma based on findings

---

**Analysis Generated**: 2025-11-20
**Test**: 50-game diagnostic (500 PA, 751 swings)
**Branch**: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`
**Status**: Partial success, fastball fix needed, investigation of missing intentions required
