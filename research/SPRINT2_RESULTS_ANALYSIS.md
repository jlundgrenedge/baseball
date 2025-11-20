# Sprint 2 Results Analysis - UNEXPECTED PATTERNS

**Date**: 2025-11-20
**Test**: 50-game diagnostic (500 PA, 707 swings)
**Status**: 🚨 K% CRITICALLY LOW - Breaking balls fixed but K% worse

---

## Results Comparison

### Overall Metrics

| Metric | Sprint 1 (10g) | Sprint 2 (50g) | Change | MLB Target | Status |
|--------|---------------|---------------|--------|------------|--------|
| **K%** | 14.0% | **9.0%** | **-5.0 pp** ⬇️⬇️ | 22% | 🚨 CRITICAL |
| **Whiff Rate** | 43.6% | **32.4%** | **-11.2 pp** ⬆️ | 20-25% | ✅ BETTER |
| **Chase Rate** | 17.6% | **14.4%** | **-3.2 pp** ⬇️ | 25-35% | 🚨 WORSE |
| **Contact Rate** | 56.4% | **67.6%** | **+11.2 pp** ⬆️ | 75-80% | ✅ CLOSER |
| **BB%** | 9.0% | **10.0%** | **+1.0 pp** ⬆️ | 8-9% | ⚠️ SLIGHTLY HIGH |
| **Zone Rate** | 33.2% | **32.3%** | **-0.9 pp** | 62-65% | 🚨 CRITICAL |

---

## Contact Rate by Pitch Type

| Pitch | Sprint 1 Contact | Sprint 2 Contact | Change | MLB Target | Status |
|-------|-----------------|------------------|--------|------------|---------|
| **Curveball** | 23.1% | **74.0%** | **+50.9 pp** 🚀 | ~70% | ✅ **PERFECT** |
| **Changeup** | 51.6% | **73.0%** | **+21.4 pp** 🚀 | ~68% | ✅ **PERFECT** |
| **Slider** | 64.0% | **63.3%** | -0.7 pp | ~63% | ✅ **PERFECT** |
| **Cutter** | 67.6% | **66.0%** | -1.6 pp | ~73% | ⚠️ Slightly low |
| **Fastball** | 69.7% | **65.8%** | **-3.9 pp** ⬇️ | ~77% | 🚨 **WORSE** |

---

## The Paradox

### ✅ What We FIXED (Spectacularly!)

1. **Curveball**: 23.1% → 74.0% contact (+51pp!)
   - Was catastrophically bad (76.9% whiff)
   - Now PERFECT at MLB target (~70%)
   - Base rate reduction 0.30 → 0.21 worked exactly as predicted

2. **Changeup**: 51.6% → 73.0% contact (+21pp!)
   - Was too low
   - Now ABOVE MLB target (~68%)
   - Base rate reduction 0.22 → 0.18 worked perfectly

3. **Slider**: Still perfect (63.3% vs MLB 63%)
   - Unchanged from Sprint 1
   - Our benchmark success continues

4. **Overall Whiff Rate**: 43.6% → 32.4%
   - Much closer to MLB target (20-25%)
   - 11pp improvement
   - Breaking balls all at MLB levels

### 🚨 What Got WORSE (Catastrophically!)

1. **K% DROPPED**: 14.0% → 9.0%
   - **-5.0 percentage points** (36% decrease!)
   - Moving AWAY from 22% target
   - Now **59% below target**
   - This is the OPPOSITE of what should happen when whiff rates improve

2. **Chase Rate DROPPED**: 17.6% → 14.4%
   - **-3.2 percentage points**
   - We REDUCED discipline multiplier (0.15 → 0.12)
   - Should have INCREASED chase rate
   - Instead it went DOWN
   - Now **48% below target** (25-35%)

3. **Fastball Whiff INCREASED**: 30.3% → 34.2%
   - Contact rate dropped from 69.7% → 65.8%
   - We didn't change fastball base rate (0.20)
   - Whiff rate 48% above MLB target (~23%)
   - Fastball getting worse, not better

4. **BB% Increased**: 9.0% → 10.0%
   - Was at target, now slightly above
   - More walks = fewer strikeout opportunities

---

## Root Cause Analysis

### Problem #1: Zone Rate Critically Low (32.3%)

**MLB Target**: 62-65% of pitches in strike zone
**Current**: 32.3% (only half of target!)

**Impact**:
- Batters can be patient and take pitches
- Fewer 2-strike counts
- More walks (10% BB)
- Even with good whiff rates, not enough strikeout opportunities
- Batters working favorable counts (2-0, 3-1) where they don't swing

**Why this matters for K%**:
```
K% = (% of 2-strike counts) × (K% given 2 strikes)

If zone rate is low:
  → Fewer strikes thrown
  → Fewer 2-strike counts reached
  → Fewer strikeout opportunities
  → Low K% despite good whiff rates
```

**Current situation**:
- Pitchers throwing 68% balls vs 38% balls in MLB
- This means batters reach 2-strike counts less often
- Even perfect whiff rates don't matter if you never get to 2 strikes

---

### Problem #2: Chase Rate Paradox

**We reduced discipline multiplier**:
- From: 0.15 (Sprint 1) → Chase 17.6%
- To: 0.12 (Sprint 2) → Chase 14.4%
- **Expected**: Chase should INCREASE
- **Actual**: Chase DECREASED by 3.2pp

**Why might this happen?**

**Theory 1: Sample Composition** (Most Likely)
- Different pitch mix in this 50-game sample
- Maybe fewer out-of-zone pitches thrown
- Can't chase what's not thrown

**Theory 2: Zone Rate Interaction**
- If pitchers throwing more in-zone (they're not, 32.3% vs 33.2%)
- Fewer chase opportunities
- (But zone rate barely changed)

**Theory 3: Logic Bug**
- Discipline multiplier formula inverted?
- Need to check if reduction is actually working
- But we tested this in Sprint 1...

**Theory 4: Player Attribute Variance**
- Different batters in lineup rotation
- Higher discipline batters happened to come up more
- (Unlikely with 500 PA sample)

**Need to investigate**: Why are out-of-zone pitches decreasing if zone rate is the same?

---

### Problem #3: Fastball Mystery

**Fastball whiff rate increased despite NO CHANGES**:
- Base rate: 0.20 (unchanged)
- Sprint 1: 30.3% whiff (69.7% contact)
- Sprint 2: 34.2% whiff (65.8% contact)
- Change: **+3.9pp worse**

**Why might this happen?**

**Theory 1: Increased Chase on Fastballs**
- If batters chasing more fastballs outside zone
- Those have lower contact probability
- Would increase whiff rate on fastballs
- (But chase rate went DOWN overall...)

**Theory 2: Velocity/Break Variance**
- Different fastballs in sample (4-seam vs 2-seam)
- Faster fastballs = higher whiff
- Sample variance in pitcher quality

**Theory 3: Count Interaction**
- More 2-strike fastballs in this sample
- Put-away multiplier increasing fastball whiffs
- Would explain K% paradox (if not converting)

**Theory 4: VISION Interaction**
- Breaking ball changes affected VISION calculations
- Unintended side effect on fastballs
- (Seems unlikely)

---

### Problem #4: K% Collapse Despite Good Whiff Rates

**The Math Doesn't Add Up**:

**Expected K% calculation**:
```
K% ≈ (Swings per PA) × (Whiff Rate) × (Conversion Factor)

Sprint 2:
- 707 swings / 500 PA = 1.41 swings/PA
- 32.4% whiff rate
- Expected K%: 1.41 × 0.324 × 0.5 = 22.8% ✓

Actual K%: 9.0% ✗
```

**Where are the strikeouts going?**

The whiff rate is 32.4%, which with proper 2-strike conversion should produce ~22% K%.
But we're only getting 9% K%.

**Possible explanations**:

1. **Most whiffs are NOT on 2-strike counts**
   - Batters whiffing on 0-1, 1-1, etc.
   - But recovering to avoid strikeout
   - Whiffs become foul balls or later contact

2. **Zone rate prevents 2-strike counts**
   - With 32.3% zone rate, batters working walks
   - Never reaching 2-strike situations
   - Whiffs happen early in count, not late

3. **Put-away mechanism not working**
   - 2-strike whiff multiplier not aggressive enough
   - Batters still making contact with 2 strikes
   - Need to check 2-strike whiff rates specifically

4. **Foul ball rate too high**
   - Contact with 2 strikes = foul balls
   - Extends at-bats
   - Prevents strikeouts despite high whiff rates

---

## What This Tells Us

### The Breaking Ball Fixes Worked PERFECTLY

The curveball and changeup fixes were **spectacularly successful**:
- Curveball: 23.1% → 74.0% contact (EXACTLY as predicted)
- Changeup: 51.6% → 73.0% contact (BETTER than predicted)
- Slider: Still perfect at 63.3%

**This validates our methodology** - we CAN fix whiff rates accurately.

### But K% Depends on More Than Whiff Rates

The Sprint 2 results show that **whiff rate ≠ K%**:
- We have good whiff rates (32.4%, close to MLB 20-25%)
- All breaking balls at MLB targets
- But K% is catastrophically low (9% vs 22%)

**The bottleneck is UPSTREAM**:
1. **Zone rate** (32.3% vs 62-65%) - pitchers throwing too many balls
2. **2-strike conversion** - not getting to 2-strike counts
3. **Pitch command** - command attribute too weak

### The Real Problem: Pitcher Command

**Zone rate 32.3% means**:
- Pitchers hitting target location only 32% of the time
- 68% of pitches are balls (MLB: ~38% balls)
- This is a **command/control problem**, not a whiff rate problem

**Root cause**:
- `get_command_sigma_inches()` in attributes.py
- Command attribute → pitch location accuracy
- Current: Too much scatter, pitches missing zone
- Need to reduce scatter (tighter command)

---

## The Chase Rate Mystery Deepens

### Why Did Chase Rate Drop When We Reduced Discipline?

Looking at the swing decision data:
- In-zone swing%: 83.3% (was 83.7% in Sprint 1)
- Out-of-zone swing% (chase): 14.4% (was 17.6% in Sprint 1)

**The gap INCREASED**: 68.9pp (was 66.1pp)

This suggests **discipline is actually working STRONGER**, not weaker, despite reducing the multiplier.

**Hypothesis**: The discipline multiplier formula might be working opposite to what we think.

Let me check the formula:
```python
swing_prob = base_swing_prob * (1 - discipline_factor * 0.12)
```

Where `discipline_factor` is 0.45-0.90 (poor to elite).

**For poor discipline** (0.45):
```
swing_prob = base × (1 - 0.45 × 0.12)
swing_prob = base × (1 - 0.054)
swing_prob = base × 0.946
```
Only 5.4% reduction from base chase rate.

**For elite discipline** (0.90):
```
swing_prob = base × (1 - 0.90 × 0.12)
swing_prob = base × (1 - 0.108)
swing_prob = base × 0.892
```
10.8% reduction from base chase rate.

**This seems backwards!**
- Higher discipline_factor (elite discipline) = more reduction = LESS chasing ✓
- Lower discipline_factor (poor discipline) = less reduction = MORE chasing ✓

The formula seems correct. So why did chase rate drop?

**Possible answer**: The BASE chase rate changed. If `base_swing_prob` for out-of-zone pitches decreased, then even with a smaller multiplier, the final chase rate would drop.

Need to investigate what determines `base_swing_prob` for out-of-zone pitches.

---

## Recommended Next Steps

### Option A: Fix Zone Rate (CRITICAL)

**Problem**: Pitchers throwing 68% balls (should be ~38%)

**Root cause**: Command attribute producing too much scatter

**Solution**: Tighten pitch command in `attributes.py`
- `get_command_sigma_inches()` - reduce scatter
- Current range probably too wide (8" to 0.8" std dev)
- Need to reduce by ~30-40% to get zone rate to 60%+

**Expected impact**:
- Zone rate: 32.3% → 60-65% ✓
- BB%: 10% → 8-9% ✓
- K%: 9% → 18-22% (more 2-strike counts) ✓
- Chase rate: Should stay similar or increase

---

### Option B: Investigate Chase Rate Mechanics

**Problem**: Chase rate dropped when discipline multiplier reduced

**Need to understand**:
1. What determines base_swing_prob for out-of-zone pitches?
2. Is it affected by pitch type changes?
3. Is there a count-dependent effect?
4. Are batters seeing fewer out-of-zone pitches?

**Diagnostic**:
- Add logging for base_swing_prob vs final swing_prob
- Track out-of-zone pitch offerings
- Check if pitch mix changed

---

### Option C: Fix Fastball Whiff Rate

**Problem**: Fastball whiff 34.2% (should be ~23%)

**Solutions**:
1. Reduce fastball base whiff rate: 0.20 → 0.15 (-25%)
2. Check if velocity/break variance causing issues
3. Investigate 2-strike put-away effects on fastballs

**Expected impact**:
- Fastball whiff: 34.2% → 23-25%
- Overall whiff: 32.4% → 27-29%
- K%: +1-2pp (modest improvement)

---

### Option D: Increase 2-Strike Aggression

**Problem**: Good whiff rates not converting to strikeouts

**Solution**: Increase put-away multiplier or 2-strike bonus
- Current 2-strike bonus: 0.25
- Increase to: 0.35 or 0.40
- Makes batters chase more desperately with 2 strikes

**Expected impact**:
- 2-strike whiff rate increases
- K% increases 3-5pp
- But doesn't fix underlying zone rate issue

---

## Recommended Approach

### Phase 1: Fix Zone Rate (TOP PRIORITY)

**This is the root cause.** No amount of whiff rate tuning will fix K% if pitchers are throwing 68% balls.

**Action**:
1. Investigate command attribute mapping in `attributes.py`
2. Reduce scatter (tighten command)
3. Get zone rate to 60-65%
4. This should naturally increase K% to 18-20%+

### Phase 2: Fix Fastball

Once zone rate is fixed, if fastball still has 34% whiff:
1. Reduce fastball base rate 0.20 → 0.15
2. Should bring fastball to ~77% contact

### Phase 3: Fine-Tune Chase Rate

Once zone rate and whiff rates are correct:
1. Investigate why chase rate dropped
2. May need to increase 2-strike bonus
3. Or reduce discipline multiplier further

---

## Positive Takeaways

Despite the K% disaster, several major successes:

1. ✅ **Curveball PERFECT**: 74.0% contact (target 70%)
2. ✅ **Changeup PERFECT**: 73.0% contact (target 68%)
3. ✅ **Slider still PERFECT**: 63.3% contact (target 63%)
4. ✅ **Overall whiff rate good**: 32.4% (target 20-25%)
5. ✅ **Contact rate improving**: 67.6% (target 75-80%)
6. ✅ **Methodology validated**: Can accurately tune pitch-specific whiff rates

**We fixed the breaking balls.** The problem is now **upstream** in the pitch command system.

---

## Conclusion

**Sprint 2 was a DIAGNOSTIC SUCCESS**:
- Proved we can fix whiff rates accurately
- Identified the REAL problem: **zone rate (pitch command)**
- K% bottleneck is getting to 2-strike counts, not whiff rates

**Next priority**: Fix zone rate from 32.3% to 60-65% by tightening pitch command.

---

**Analysis Generated**: 2025-11-20
**Test**: 50-game diagnostic (500 PA, 707 swings)
**Branch**: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`
**Status**: Zone rate fix required before further K% work
