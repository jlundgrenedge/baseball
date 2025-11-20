# Sprint 1 Results Analysis - MIXED OUTCOMES

**Date**: 2025-11-20
**Test**: 10-game diagnostic (100 PA, 149 swings)
**Status**: ⚠️ MIXED - Some improvements, unexpected K% decrease

---

## Results Comparison

### Overall Metrics

| Metric | Before Sprint 1 | After Sprint 1 | Change | Target | Status |
|--------|----------------|---------------|--------|--------|--------|
| **K%** | 16.0% | **14.0%** | **-2.0 pp** ⬇️ | 22% | 🚨 WORSE |
| **Whiff Rate** | 41.4% | **43.6%** | **+2.2 pp** ⬆️ | 20-25% | 🚨 WORSE |
| **Chase Rate** | 10.2% | **17.6%** | **+7.4 pp** ⬆️ | 25-35% | ✅ BETTER |
| **Contact Rate** | 58.6% | **56.4%** | **-2.2 pp** ⬇️ | 75-80% | 🚨 WORSE |
| **BB%** | 16.6% | **9.0%** | **-7.6 pp** ⬇️ | 8-9% | ✅ AT TARGET |
| **Zone Rate** | 30.7% | **33.2%** | **+2.5 pp** ⬆️ | 62-65% | ⚠️ SLIGHT IMPROVEMENT |

### Contact Rate by Pitch Type

| Pitch | Before Contact | After Contact | Change | MLB Target | Before Status | After Status |
|-------|---------------|---------------|--------|------------|---------------|--------------|
| **Fastball** | 76.3% | **69.7%** | **-6.6 pp** ⬇️ | ~77% | ✅ Perfect | ⚠️ Below target |
| **Cutter** | 59.5% | **67.6%** | **+8.1 pp** ⬆️ | ~73% | 🚨 Too low | ⚠️ Improved |
| **Slider** | 42.4% | **64.0%** | **+21.6 pp** ⬆️ | ~63% | 🚨 Way too low | ✅ AT TARGET |
| **Changeup** | 53.1% | **51.6%** | **-1.5 pp** ⬇️ | ~68% | 🚨 Too low | 🚨 Still too low |
| **Curveball** | (not in sample) | **23.1%** | N/A | ~70% | N/A | 🚨 TERRIBLE |

---

## What Worked

### ✅ Chase Rate Increased Significantly
- **From 10.2% → 17.6%** (+7.4 percentage points)
- Discipline multiplier reduction (0.30 → 0.15) is working
- Still below target (25-35%), but clear improvement

### ✅ BB% Reached Target
- **From 16.6% → 9.0%** (-7.6 percentage points)
- Now at MLB target range (8-9%)
- Unexpected benefit of increased chase rate

### ✅ Slider Contact Rate Fixed
- **From 42.4% → 64.0%** (+21.6 percentage points)
- Now at MLB target (~63%)
- Base rate reduction (0.35 → 0.24) worked perfectly for sliders

### ✅ Cutter Improved Significantly
- **From 59.5% → 67.6%** (+8.1 percentage points)
- Closer to MLB target (~73%)
- Base rate reduction (0.25 → 0.18) helped

---

## What Didn't Work

### 🚨 K% Decreased (Critical Issue)
- **From 16.0% → 14.0%** (-2.0 percentage points)
- **OPPOSITE** of intended effect
- Moving AWAY from 22% target

**Why This Happened**:
1. More swings on breaking balls (increased chase)
2. Breaking balls still have high whiff rates overall
3. More balls in play despite higher whiff rate
4. Sample composition changed (more curveballs)

**The Paradox**:
- Chase rate UP (good)
- Whiff rate UP (bad)
- K% DOWN (worse)

**Explanation**: Batters are making contact when it matters (preventing strikeouts with 2 strikes) but whiffing more on pitches that don't result in strikeouts (early in count, foul balls).

### 🚨 Overall Whiff Rate Increased
- **From 41.4% → 43.6%** (+2.2 percentage points)
- Still **74% above MLB target** (20-25%)
- Despite reducing base rates for slider/changeup/cutter

**Why**: More curveballs in this sample (26 swings, 76.9% whiff)

### 🚨 Fastball Contact Decreased
- **From 76.3% → 69.7%** (-6.6 percentage points)
- Was PERFECT, now below MLB target (~77%)
- **We didn't change fastball base rate (0.20)**

**Possible Causes**:
1. **Sample variance** (most likely) - small sample fluctuation
2. **Increased chase** → batters swinging at worse fastballs outside zone
3. **Put-away effect** → more 2-strike situations creating higher fastball whiffs

### 🚨 Curveball Terrible
- **23.1% contact (76.9% whiff)**
- MLB target: ~70% contact (~30% whiff)
- Base rate 0.30 unchanged → with multipliers = **77% whiff**

**Root Cause**: We didn't reduce curveball base rate in Sprint 1

### 🚨 Changeup Barely Improved
- **From 53.1% → 51.6%** (-1.5 pp, WORSE)
- Still far below MLB target (~68%)
- Base rate reduction (0.32 → 0.22) didn't help enough

---

## Root Cause Analysis

### Why Did K% Go Down Despite Higher Chase Rate?

**Theory 1: Sample Variance** (Most Likely)
- 100 PA is still relatively small sample
- K% variance at this sample size: ±3-4 percentage points
- Could be unlucky draw with more balls in play

**Theory 2: Pitch Mix Changed**
- More curveballs (26 swings) with terrible contact (23.1%)
- Curveball drags overall whiff rate up (76.9% whiff)
- But curveball whiffs not converting to strikeouts efficiently

**Theory 3: Contact When It Matters**
- Batters making contact on crucial 2-strike pitches
- Whiffing more on early-count or foul-territory pitches
- Need to investigate 2-strike whiff rates specifically

**Theory 4: Fastball Regression**
- Fastball contact dropped from 76.3% → 69.7%
- If fastballs are primary pitch with 2 strikes, this hurts K%
- May need fastball-specific fix

### Why Are Whiff Rates Still So High?

**Before Sprint 1** (41.4% overall):
- Slider: 57.6% whiff
- Changeup: 46.9% whiff
- Cutter: 40.5% whiff
- Fastball: 23.7% whiff

**After Sprint 1** (43.6% overall):
- **Curveball: 76.9% whiff** ← NEW, dragging average up
- Changeup: 48.4% whiff (worse)
- Slider: 36.0% whiff (MUCH better, at target!)
- Cutter: 32.4% whiff (better)
- Fastball: 30.3% whiff (worse)

**Insight**: Slider reached target (36% whiff vs MLB ~37%). Cutter improved significantly. But curveball and changeup still problematic.

---

## Pitch-Specific Analysis

### Fastball: 69.7% contact (MLB: ~77%)
- **Base rate**: 0.20 (unchanged)
- **Expected after multipliers**: 0.20 × 1.2 = 24% whiff → 76% contact ✓
- **Actual**: 30.3% whiff → 69.7% contact ✗
- **Status**: WORSE than expected
- **Likely cause**: Sample variance OR increased chase on bad fastballs

### Cutter: 67.6% contact (MLB: ~73%)
- **Base rate**: 0.25 → 0.18 (Sprint 1)
- **Expected**: 0.18 × 1.5 = 27% whiff → 73% contact ✓
- **Actual**: 32.4% whiff → 67.6% contact ⚠️
- **Status**: Improved significantly but still 5pp below target
- **May need**: Further reduction to 0.16?

### Slider: 64.0% contact (MLB: ~63%)
- **Base rate**: 0.35 → 0.24 (Sprint 1)
- **Expected**: 0.24 × 1.5 = 36% whiff → 64% contact ✓
- **Actual**: 36.0% whiff → 64.0% contact ✅
- **Status**: PERFECT, at MLB target

### Changeup: 51.6% contact (MLB: ~68%)
- **Base rate**: 0.32 → 0.22 (Sprint 1)
- **Expected**: 0.22 × 1.5 = 33% whiff → 67% contact ✓
- **Actual**: 48.4% whiff → 51.6% contact ✗
- **Status**: Still terrible, didn't improve as expected
- **Likely cause**: Multipliers higher than 1.5× OR base rate still too high

### Curveball: 23.1% contact (MLB: ~70%)
- **Base rate**: 0.30 (unchanged in Sprint 1)
- **Expected**: 0.30 × 1.5 = 45% whiff → 55% contact
- **Actual**: 76.9% whiff → 23.1% contact ✗✗✗
- **Status**: TERRIBLE, multipliers must be ~2.5× instead of 1.5×
- **Fix needed**: Reduce base rate 0.30 → 0.21 (-30%)

---

## What We Learned

### 1. Slider Base Rate Tuning Works
The slider went from 42.4% → 64.0% contact, exactly hitting the MLB target of ~63%. This validates that:
- Base rate reduction of 31% (0.35 → 0.24) was correct
- Multipliers for slider are indeed ~1.5×
- Our tuning methodology works when applied correctly

### 2. Chase Rate Discipline Reduction Works
Chase rate increased from 10.2% → 17.6% (+7.4 pp), proving:
- Discipline multiplier reduction (0.30 → 0.15) is effective
- Still not at target (25-35%), but trending correctly
- May need further reduction to 0.10 to reach 25%

### 3. Some Pitches Have Higher Multipliers
Curveball showing 76.9% whiff (expected ~45%) suggests:
- Curveball multipliers are ~2.5× instead of assumed 1.5×
- May have different VISION impact or velocity/break effects
- Need pitch-type specific multiplier analysis

### 4. Changeup More Resistant to Tuning
Despite reducing base from 0.32 → 0.22 (-31%), changeup still at 51.6% contact (target 68%):
- Either multipliers are much higher (~2.2×)
- Or base rate needs to be even lower (0.18?)
- Or changeup has unique physics making it harder to hit

### 5. K% Depends on More Than Whiff Rate
Higher whiff rate (43.6%) doesn't automatically mean higher K%:
- Timing of whiffs matters (early count vs 2-strike)
- Pitch type matters (which pitches get thrown with 2 strikes)
- Foul ball rate matters (whiffs that don't result in strikes)

### 6. 100 PA Still Has Variance
K% changed -2pp, but could be within variance:
- Fastball dropped 6.6pp (likely variance)
- Pitch mix different (curveball appeared)
- Need 200+ PA for true stability

---

## Recommended Next Steps

### Option A: Fix Remaining Breaking Balls (RECOMMENDED)

**Reduce curveball and adjust changeup**:

1. **Curveball**: 0.30 → 0.21 (-30%)
   - Current: 76.9% whiff
   - Expected after: 0.21 × 1.5 = 31.5% whiff → 68.5% contact (close to MLB 70%)

2. **Changeup**: 0.22 → 0.18 (-18% additional)
   - Current: 48.4% whiff
   - Expected after: 0.18 × 1.5 = 27% whiff → 73% contact (close to MLB 68%)

3. **Splitter**: 0.38 → 0.27 (-29%)
   - Not in sample but likely similar to curveball
   - Preventative fix

4. **Keep slider unchanged** (0.24) - it's perfect

**Expected Impact**:
- Whiff rate: 43.6% → 30-34% (closer to MLB 20-25%)
- K%: 14.0% → 19-22% (depends on how curveball is used)

---

### Option B: Further Increase Chase Rate

**Reduce discipline multiplier more**:
- Current: 0.15
- Proposed: 0.10 (33% additional reduction)
- Expected chase: 17.6% → 23-27% (closer to MLB 25-35%)

**Increase 2-strike bonus**:
- Current: 0.25
- Proposed: 0.35 (+10pp flat bonus)
- Expected K% increase: +2-3pp

**Expected Impact**:
- Chase rate: 17.6% → 25-30%
- K%: 14.0% → 18-20%

---

### Option C: Investigate Fastball (DIAGNOSTIC)

**Why did fastball contact drop?**
- Was 76.3% (perfect), now 69.7% (below target)
- Base rate unchanged at 0.20

**Possible fixes**:
1. Accept as sample variance (most likely)
2. Investigate if chasing bad fastballs
3. Check if 2-strike fastball whiffs increased

**Action**: Run another 10-game test before making fastball changes

---

### Option D: Combination Approach (AGGRESSIVE)

1. Fix curveball/changeup base rates (Option A)
2. Reduce discipline to 0.10 (Option B)
3. Increase 2-strike bonus to 0.35 (Option B)

**Expected Impact**:
- Whiff rate: 43.6% → 28-32%
- Chase rate: 17.6% → 25-30%
- K%: 14.0% → 21-24% ✅

**Risk**: May overshoot target

---

## Recommendation

**Primary: Option A + Partial Option B**

1. **Fix curveball and changeup base rates** (clear need based on data)
   - Curveball: 0.30 → 0.21
   - Changeup: 0.22 → 0.18
   - Splitter: 0.38 → 0.27

2. **Reduce discipline multiplier slightly** (continue trend)
   - From 0.15 → 0.12 (modest additional reduction)
   - Expected chase: 17.6% → 21-24%

3. **Keep everything else unchanged**
   - Slider perfect at 0.24
   - Cutter improving, give it another test
   - Fastball likely variance
   - 2-strike bonus adequate at 0.25

**Expected Outcome**:
- K%: 14.0% → 20-22% (close to target)
- Chase rate: 17.6% → 21-24% (approaching target)
- Whiff rate: 43.6% → 30-34% (closer to target)
- Contact rate: 56.4% → 66-70% (closer to target)

**Test Plan**: Run another 10-game diagnostic after these changes

---

## Positive Takeaways

Despite K% going down, several positives emerged:

1. ✅ **BB% at target** (9.0%, was 16.6%)
2. ✅ **Slider PERFECT** (64.0% contact, target ~63%)
3. ✅ **Chase rate improving** (17.6%, was 10.2%)
4. ✅ **Cutter improved** (67.6%, was 59.5%)
5. ✅ **Methodology validated** (slider success proves our approach works)

**The foundation is working.** We just need to apply the same logic to curveball and refine changeup.

---

## Conclusion

**Sprint 1 produced MIXED results:**

**Successes**:
- Slider contact reached MLB target (64.0%)
- Chase rate increased significantly (+7.4pp)
- BB% reached target (9.0%)
- Cutter improved substantially

**Failures**:
- K% decreased (-2.0pp) instead of increasing
- Overall whiff rate increased (+2.2pp)
- Curveball terrible (23.1% contact)
- Changeup didn't improve enough

**Root Cause**: We fixed 3 breaking balls (slider, cutter, changeup) but:
- Curveball unchanged and terrible
- Changeup reduction insufficient
- Fastball possible variance
- Sample happened to have more curveballs

**Next Step**: Apply same 30% reduction to curveball and further reduce changeup. Modestly reduce discipline multiplier to continue chase rate improvement.

---

**Analysis Generated**: 2025-11-20
**Test**: 10-game diagnostic (100 PA, 149 swings)
**Branch**: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`
**Status**: Sprint 2 planning recommended
