# Phase 2A: Foul Ball Analysis & K% Tuning Strategy

**Date**: 2025-11-20
**Status**: Investigation Complete - Awaiting User's Diagnostic Results
**Branch**: `claude/tune-k-percent-constants-01YKoKUsdEWf7P48Ujsx4s8Q`

---

## Executive Summary

Investigation revealed that **foul balls are likely the missing piece** for achieving MLB-realistic K% targets. The current diagnostic (500 PA sample) shows:

- **K% = 14.8%** (target: 22%) - TOO LOW by 7.2pp
- **Chase rate = 14.1%** (MLB: 25-35%) - TOO LOW
- **In-zone swing% = 58.0%** (MLB: 65-70%) - TOO LOW

**New hypothesis**: These issues are symptoms of **at-bats that are too short** due to insufficient foul balls. Foul balls extend at-bats, create deeper counts, and generate more 2-strike K opportunities.

---

## What Are Foul Balls and Why Do They Matter?

### MLB Foul Ball Statistics

- **Foul ball rate**: ~20-25% of swings result in foul balls
- **Pitches per PA**: ~3.8-4.0 average
- **2-strike fouls**: Very common (batters "protecting the plate")
- **Impact on K%**: More fouls → deeper counts → more 2-strike battles → more K opportunities

### Current Foul Ball Mechanics

Located in `batted_ball/at_bat.py` lines 1106-1133:

```python
is_foul = False

# 1. Extreme launch angles (pop-ups behind or ground balls foul)
if launch_angle < -10 or launch_angle > 60:
    is_foul = True

# 2. Spray angle fouls (outside fair territory)
# Fair territory is roughly -45° to +45°
if abs(spray_angle) > 45:
    is_foul = True

# 3. Weak contact more likely to foul
# Previous 40% rate was causing too many fouls and reducing offensive production
if contact_quality == 'weak' and np.random.random() < 0.22:
    is_foul = True

if is_foul:
    pitch_data['pitch_outcome'] = 'foul'
    if strikes < 2:
        strikes += 1
    # With 2 strikes, foul doesn't add to count (MLB rule)
```

**Key Finding**: The weak contact foul probability was **reduced from 40% to 22%** based on a comment saying "too many fouls reducing offensive production". This may have overcorrected and is now causing at-bats to be too short.

---

## Enhanced Diagnostic Now Available

I've upgraded `research/run_50game_fixed_diagnostic.py` to track:

### NEW Foul Ball Metrics

1. **Foul ball rate** (% of swings)
2. **Foul balls by count** (0 strikes, 1 strike, 2 strikes)
3. **Pitches per PA** (average)
4. **Breakdown of contact outcomes**: fouls vs in-play

### Sample Output (What User Will See)

```
⚾ FOUL BALL ANALYSIS (NEW - KEY FOR K% TUNING):
   Total Fouls: 142
   Foul Ball Rate: 23.0% of swings (MLB: ~20-25%)
   MLB Target: 20-25% of swings result in foul balls

   Foul Balls by Count:
      With 0 strikes: 48 (33.8%)
      With 1 strike:  51 (35.9%)
      With 2 strikes: 43 (30.3%)
      → 2-strike fouls should be highest (batters protecting plate)

   Pitches per Plate Appearance:
      Average: 3.65 pitches/PA
      MLB Target: 3.8-4.0 pitches/PA

   🚨 PITCHES/PA TOO LOW: 3.65 (target: 3.8-4.0)
      → At-bats ending too quickly
      → Likely causes: low foul rate, high chase rate, or short counts
```

---

## Diagnostic Interpretation Guide

### Scenario 1: Foul Rate Too Low (< 15%)

**Problem**: At-bats too short → fewer 2-strike counts → lower K%

**Root Causes**:
- Weak contact foul probability too low (currently 22%)
- 2-strike fouls not common enough (batters should protect more)
- Extreme launch/spray angle thresholds too strict

**Solutions**:
1. Increase weak contact foul probability: 22% → 30-35%
2. Add count-dependent foul probability (more fouls with 2 strikes)
3. Slightly loosen extreme angle thresholds

### Scenario 2: Foul Rate OK (20-25%) but Pitches/PA Low (< 3.5)

**Problem**: Fouls happening but at-bats still too short

**Root Causes**:
- Too many early-count outs (high in-zone swing% + weak contact → quick outs)
- Chase rate too low (batters too patient early)
- Not enough 2-strike fouls extending battles

**Solutions**:
1. Reduce early-count aggression (0-0, 1-0 counts)
2. Increase 2-strike foul probability specifically
3. Increase chase rate to work deeper counts

### Scenario 3: Pitches/PA OK (3.8-4.0) but K% Still Low

**Problem**: At-bat length good, but not converting to Ks

**Root Causes**:
- 2-strike whiff rate too low (put-away mechanism weak)
- Chase rate low (not swinging at waste pitches)
- Contact rates too high on 2-strike pitches

**Solutions**:
1. Increase 2-strike whiff multiplier
2. Increase chase rate (especially 2-strike)
3. Reduce contact rates on breaking balls

---

## Recommended Tuning Sequence

### Step 1: Run Enhanced Diagnostic (User)

```bash
python research/run_50game_fixed_diagnostic.py
```

This will output current foul ball rates and pitches/PA. User should share these results.

### Step 2: Analyze Foul Ball Metrics

Based on diagnostic output, determine which scenario applies:
- Is foul rate too low?
- Is pitches/PA too low?
- Are at-bats reaching 2-strike counts?

### Step 3: Tune Foul Ball Generation (if needed)

**File**: `batted_ball/at_bat.py` lines 1106-1133

**Option A - Increase Overall Foul Rate**:
```python
# Increase weak contact foul probability
if contact_quality == 'weak' and np.random.random() < 0.30:  # Was 0.22
    is_foul = True
```

**Option B - Add Count-Dependent Foul Probability** (RECOMMENDED):
```python
# Add 2-strike protection fouls
if strikes >= 2:
    # Batters with 2 strikes "protect the plate" - more defensive swings
    # Even solid contact can go foul when protecting
    protection_foul_prob = 0.15  # 15% chance of foul even on fair contact
    if np.random.random() < protection_foul_prob:
        is_foul = True
```

**Option C - Adjust Extreme Angle Thresholds**:
```python
# Slightly more lenient thresholds
if launch_angle < -8 or launch_angle > 65:  # Was -10 to 60
    is_foul = True
```

### Step 4: Tune Swing Decisions (Phase 2A Primary Task)

**File**: `batted_ball/player.py` → `decide_to_swing()` method

**Current Issues**:
- Chase rate: 14.1% (need: 25-35%)
- In-zone swing%: 58% (need: 65-70%)

**Tuning Approach**:
1. Reduce ZONE_DISCERNMENT effectiveness (batters less disciplined)
2. Add count-based swing modifiers:
   - More aggressive with 2 strikes (protect plate)
   - More passive early in count (work deep counts)
3. Increase 2-strike chase rate specifically

### Step 5: Validate K% Target

After tuning, re-run diagnostic and verify:
- ✅ K% ~22%
- ✅ BB% maintained at 7-9%
- ✅ Foul rate 20-25%
- ✅ Pitches/PA 3.8-4.0

---

## Key Files for Phase 2A

### Foul Ball Tuning
- **batted_ball/at_bat.py** (lines 1106-1133) - Foul ball generation logic
- **batted_ball/contact.py** - Contact quality determination (affects weak contact fouls)

### Swing Decision Tuning
- **batted_ball/player.py** (lines ~630-710) - `decide_to_swing()` method
- **batted_ball/attributes.py** - ZONE_DISCERNMENT and swing tendency attributes

### Testing
- **research/run_50game_fixed_diagnostic.py** - Enhanced diagnostic with foul metrics (UPDATED)

---

## Expected Impact of Foul Ball Tuning

### If Foul Rate Increases: 22% → 28%

**Direct Effects**:
- Pitches per PA: 3.6 → 4.0 (+0.4 pitches)
- At-bats reaching 2 strikes: +10-15%
- 2-strike fouls extending battles: Common

**Indirect Effects**:
- K% increase: +3-5pp (more 2-strike opportunities)
- BB% slight increase: +0.5-1pp (longer at-bats = more 3-ball counts)
- BABIP decrease: Fewer balls in play overall

**Net Result**: Should help close the gap from 14.8% → 22% K%

---

## MLB Realism Targets (Reminder)

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| K% | 14.8% | 22% | 🚨 -7.2pp |
| BB% | 6.8% | 8-9% | ✅ Close |
| Zone rate | 59.4% | 62-65% | ✅ Good |
| Chase rate | 14.1% | 25-35% | 🚨 -11pp |
| In-zone swing% | 58% | 65-70% | 🚨 -7pp |
| **Foul rate** | **Unknown** | **20-25%** | **❓ TEST NEEDED** |
| **Pitches/PA** | **Unknown** | **3.8-4.0** | **❓ TEST NEEDED** |

---

## Next Steps

1. **User runs enhanced diagnostic** to get current foul rate and pitches/PA
2. **Analyze results** using scenarios in this document
3. **Tune foul ball generation** if rate is too low (< 15%)
4. **Tune swing decisions** to increase chase rate and in-zone swing%
5. **Re-validate** to ensure K% reaches 22% while maintaining BB% at 7-9%

---

## Questions for User (Based on Diagnostic Results)

After running the diagnostic, please share:

1. **Current foul ball rate**: X% of swings
2. **Current pitches/PA**: X.XX average
3. **Foul distribution by count**: 0-strike, 1-strike, 2-strike percentages
4. **Updated K% and BB%**: After any recent changes

This will determine whether foul ball tuning is the primary lever or if swing decision tuning is more critical.

---

## References

- **Phase 2B Implementation**: Complete, BB% tuned successfully
- **Original V2 Plan**: `research/v2_Implementation_Plan.md`
- **At-Bat Simulator**: `batted_ball/at_bat.py`
- **Player Swing Logic**: `batted_ball/player.py`
- **Enhanced Diagnostic**: `research/run_50game_fixed_diagnostic.py` (UPDATED 2025-11-20)

---

**Status**: Ready for user diagnostic results. Enhanced tooling in place to measure foul ball impact.
