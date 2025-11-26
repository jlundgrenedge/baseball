# Option A: Contact Rate Investigation - Findings Report

**Date**: 2025-11-20
**Status**: ✅ DIAGNOSTIC COMPLETE - Unexpected Results
**Branch**: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`

---

## Executive Summary

Option A successfully implemented contact rate diagnostics and revealed an **unexpected finding**: Whiff rates are **TOO HIGH** (36.8%), not too low as hypothesized. This contradicts the initial assumption that low K% was caused by batters making contact too frequently.

### Key Findings

- **Whiff Rate**: 36.8% (MLB target: 20-25%) - **47% above target**
- **Contact Rate**: 63.2% (MLB target: 75-80%) - **15% below target**
- **K%**: 20.0% (MLB target: 22%) - **Close to target**
- **Conclusion**: Refinement changes may have overcorrected whiff probability

---

## Implementation Summary

### Sprint 1-2: Add Contact Rate Tracking

**Changes Made**:

1. **Added whiff logging** in `batted_ball/at_bat.py` (lines 650-671)
   - Logs every swing decision (whiff vs contact)
   - Tracks pitch type, velocity, movement, multipliers
   - Records batter and pitcher attributes

2. **Added contact rate analysis** in `research/run_small_debug_test.py`
   - Calculate contact rate = (swings - whiffs) / swings
   - Display overall and by-pitch-type breakdowns
   - Compare to MLB benchmarks with diagnostics

**Infrastructure**: Leveraged existing `DebugMetricsCollector` framework

---

## Test Results

### 3-Game Diagnostic Test

```
🎯 CONTACT RATE ANALYSIS:
   Total Swings: 38
   Total Contact: 24 (63.2%)
   Total Whiffs: 14 (36.8%)
   MLB Target Contact Rate: ~75-80%
   MLB Target Whiff Rate: ~20-25%

   Contact Rate by Pitch Type:
      fastball    :  10/ 13 contact ( 76.9%) |   3 whiffs ( 23.1%) ✅
      cutter      :   8/ 11 contact ( 72.7%) |   3 whiffs ( 27.3%) ✅
      curveball   :   5/  7 contact ( 71.4%) |   2 whiffs ( 28.6%) ⚠️
      slider      :   1/  3 contact ( 33.3%) |   2 whiffs ( 66.7%) 🚨
      splitter    :   0/  3 contact (  0.0%) |   3 whiffs (100.0%) 🚨
      changeup    :   0/  1 contact (  0.0%) |   1 whiffs (100.0%) 🚨
```

**Other Metrics**:
- **K%**: 20.0% (target: 22%) - Close!
- **BB%**: 6.7% (target: 8-9%) - Good
- **Chase Rate**: 12.9% (target: 25-35%) - Still low

---

## Analysis

### The Paradox: High Whiff Rates, Low K%

**Observation**: Whiff rate of 36.8% is 47% above MLB's 20-25% target, yet K% is only 20% (close to 22% target).

**Possible Explanations**:

1. **Sample Size Variance** (Most Likely)
   - 3-game test = only 38 swings
   - High variance in small samples
   - Need 10-game test for reliability

2. **Foul Ball Rates**
   - Many swings with 2 strikes result in fouls, not strikeouts
   - Whiff rate measures swings, K% measures plate appearances
   - May need to investigate foul ball frequency

3. **Chase Rate Still Low**
   - Chase rate at 12.9% (target: 25-35%)
   - Batters not swinging at enough pitches
   - Even with high whiff rates, low chase prevents strikeouts

4. **Breaking Ball Overrepresentation**
   - Slider/splitter/changeup showing 66-100% whiff rates
   - Far above MLB norms for these pitches
   - May indicate pitch selection bias in small sample

### Contact Rate by Pitch Type Analysis

**Performing Well** (close to MLB norms):
- **Fastball**: 76.9% contact (MLB: ~77-80%)
- **Cutter**: 72.7% contact (MLB: ~72-75%)
- **Curveball**: 71.4% contact (MLB: ~68-72%)

**Too High Whiff Rates** (need investigation):
- **Slider**: 66.7% whiff (MLB: ~35-40%)
- **Splitter**: 100.0% whiff (MLB: ~40-45%)
- **Changeup**: 100.0% whiff (MLB: ~30-35%)

**Hypothesis**: Breaking balls have excessive whiff rates in this sample, possibly due to:
- Small sample size (only 3-7 pitches each)
- Phase 2A refinement overcorrected whiff probability
- VISION attribute may be too punishing for off-speed pitches

---

## Comparison to Hypotheses

### Original Hypothesis (REJECTED)
**"Contact rates are too high → batters making contact too frequently → low K%"**

**Reality**: Contact rates are too low (63.2% vs 75-80%), meaning whiff rates are too high

### Revised Understanding
**"Whiff rates are too high for breaking balls, but chase rate is still low, creating a paradox where high whiffs don't translate to high K%"**

---

## Recommendations

### Priority 1: Investigate Foul Ball Frequency
**Why**: High whiff rates should produce high K%, but don't. Foul balls may be the missing link.

**Action**:
- Log foul ball outcomes in at_bat.py
- Calculate foul ball rate with 2 strikes
- Compare to MLB norms (~50-60% of 2-strike contacts are fouls)

**Expected Insight**: If foul rates are very high, this explains why whiff rates don't convert to K%

### Priority 2: Reduce Whiff Rates for Breaking Balls
**Why**: Sliders, splitters, changeups showing 66-100% whiff rates (far above MLB 30-45%)

**Options**:
- **A1**: Reduce base whiff rates for these pitches in `player.py`
  - Slider: 0.35 → 0.30 (-14%)
  - Changeup: 0.32 → 0.28 (-13%)
  - Splitter: 0.38 → 0.33 (-13%)

- **A2**: Reduce VISION impact on breaking balls
  - Breaking balls harder to track, but not *that* much harder
  - May need pitch-type specific VISION multipliers

- **A3**: Reduce put-away multiplier
  - Current: 1.0-1.30× based on stuff rating
  - Try: 1.0-1.20× (reduce by ~30%)

**Expected Impact**: +5-10 pp reduction in whiff rate → closer to MLB norms

### Priority 3: Increase Chase Rate (Still an Issue)
**Why**: 12.9% chase rate remains far below 25-35% target

**This was already attempted** in Refinement Sprints 1-2:
- Discipline multiplier: 0.85 → 0.40 → 0.30
- 2-strike bonus: 0.15 → 0.25

**Further options**:
- Reduce discipline multiplier even more (0.30 → 0.20)
- Increase 2-strike bonus more (0.25 → 0.35)
- Add out-of-zone pitch attractiveness (velocity/movement makes bad pitches tempting)

**Expected Impact**: +10-15 pp increase in chase rate

### Priority 4: Run 10-Game Diagnostic Test
**Why**: 3-game sample (38 swings) has high variance

**Action**: Create 10-game version of debug test
**Expected**: More reliable statistics, may show different contact/whiff rates

---

## Counterintuitive Conclusion

**The Phase 2A refinement (discipline reduction + 2-strike bonus) may have overcorrected whiff probability rather than undercorrected it.**

**Evidence**:
1. Whiff rate 47% above MLB target (36.8% vs 20-25%)
2. Breaking balls showing 66-100% whiff rates
3. Yet K% only at 20% (close to 22% target)

**Implication**: We may need to **reduce** whiff rates, not increase them

**But**: This contradicts initial K% gap (12.3% vs 22%). The truth is likely:
- Chase rate is still the bottleneck (12.9% vs 25-35%)
- Whiff rates are high on the pitches that are thrown, but not enough pitches are swung at
- Need both: more chases + lower whiffs on breaking balls

---

## Lessons Learned

### What Worked

1. **Contact Rate Diagnostic System**
   - Clean implementation using existing debug framework
   - Pitch-type breakdowns provide actionable insights
   - MLB benchmarks make issues immediately obvious

2. **Hypothesis Testing**
   - Started with clear hypothesis ("contact too high")
   - Data rejected hypothesis (contact too low)
   - Learned more from being wrong than from confirming assumptions

3. **Pitch-Type Granularity**
   - Breaking balls have different issues than fastballs
   - Generic "whiff rate" masks important details
   - Need pitch-specific tuning

### What Didn't Work

1. **3-Game Sample Size**
   - 38 swings insufficient for reliable stats
   - Splitter/changeup had 3-4 pitches each (100% whiff = 3/3 or 1/1)
   - 10+ game test needed

2. **Initial Hypothesis**
   - Assumed contact rates were too high (wrong)
   - Should have measured before theorizing
   - Option A was the right call: diagnose first, fix second

---

## Next Steps (Recommended Priority Order)

1. **Immediate**: Run 10-game diagnostic test
   - Get reliable statistics
   - Confirm 36.8% whiff rate finding
   - Check if breaking ball whiff rates stabilize

2. **Short-term**: Investigate foul ball rates
   - Add foul ball logging
   - Understand whiff-to-K% conversion
   - May explain the paradox

3. **Medium-term**: Tune whiff rates
   - **If 10-game test confirms high whiffs**: Reduce base rates for breaking balls
   - **If 10-game test shows normal whiffs**: Current settings may be fine

4. **Long-term**: Continue chase rate work
   - Still at 12.9% vs 25-35% target
   - May need more aggressive parameter changes
   - Consider out-of-zone pitch "attractiveness" factor

---

## Files Modified

### Created/Modified
- `batted_ball/at_bat.py` (lines 616-674): Added whiff logging
- `research/run_small_debug_test.py` (lines 126-177): Added contact rate analysis

### Commits
1. Option A implementation (a0d84e1)

### All Changes Pushed ✅
Branch: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`

---

## Conclusion

**Option A successfully diagnosed the contact rate issue but revealed unexpected results.**

### What We Learned

- **Whiff rates are TOO HIGH** (36.8% vs 20-25%), not too low
- **Breaking balls** (slider, splitter, changeup) have excessive whiff rates (66-100%)
- **Chase rate remains low** (12.9% vs 25-35%) - still a bottleneck
- **K% at 20%** is closer to target than expected, given the metrics

### The Path Forward

**Option A was diagnostic, not prescriptive.** The data suggests multiple issues:

1. ✅ **Contact rate system works** - can now monitor whiff/contact in real-time
2. ⚠️ **Whiff rates need reduction**, especially for breaking balls
3. ⚠️ **Chase rate still too low**, continues to be primary bottleneck
4. ❓ **Foul ball investigation needed** to explain whiff-to-K% conversion

**Recommendation**: Before making more parameter changes, run a 10-game diagnostic test to confirm these findings with statistical reliability.

---

**Report Generated**: 2025-11-20
**Author**: Claude (AI Assistant)
**Session**: Agent Mission 01G6so7LCSpGquX1yLqefgbh
**Status**: Option A Complete - Diagnostic Phase Successful
