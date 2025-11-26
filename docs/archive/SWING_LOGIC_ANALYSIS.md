# Swing Decision Logic Analysis & Improvement Plan

**Date**: 2025-11-20
**Version**: 1.0
**Status**: Diagnostic Complete, Improvements Designed

---

## Executive Summary

The current swing decision model (`batted_ball/player.py:decide_to_swing()`) has been audited and diagnosed. The analysis reveals that while base swing rates are reasonable, **the discipline rating has insufficient impact on swing behavior**, particularly chase rates. This document presents findings and proposed improvements.

---

## Current Implementation

### Location: `batted_ball/player.py:571-714`

### Key Inputs

The swing decision function receives:
- **pitch_location**: (h_inches, v_inches) at plate
- **is_strike**: Boolean indicating if pitch is in strike zone
- **count**: (balls, strikes)
- **pitch_velocity**: Pitch speed in mph
- **pitch_type**: Type of pitch (affects chase rate for breaking balls)

### Player Attributes Used

1. **ZONE_DISCERNMENT** (0-100k) → `get_zone_discernment_factor()` (0.40-0.96)
   - Higher = better pitch recognition, fewer chases
   - Maps: 0→0.40, 50k→0.70, 85k→0.88, 100k→0.96

2. **SWING_DECISION_LATENCY** (0-100k) → `get_swing_decision_latency_ms()` (75-200ms)
   - Lower = faster decisions, more aggressive
   - Maps: 0→200ms, 50k→130ms, 85k→100ms, 100k→75ms
   - Converted to aggression_factor (0.2-0.9)

### Swing Probability Model

```
BASE PROBABILITIES:
- In-zone (strike=True):
  - Center: 85%
  - Edges: 65-85% (varies with location difficulty)

- Out-of-zone (strike=False):
  - Just outside (<3" from zone): 35% * exp(-distance/4)
  - Further outside: 10% * exp(-distance/8)

ADJUSTMENTS:
1. Discipline adjustment:
   - In-zone: +0% to +15% for poor discipline
   - Out-of-zone: -60% for elite discipline (multiplier: 1 - disc_factor * 0.6)

2. Aggression adjustment:
   - Multiplier: 0.8 + aggression_factor * 0.4
   - Range: 0.8× to 1.2×

3. Velocity penalty:
   - Faster pitches: up to -10% for 100mph

4. Pitch type bonus (out-of-zone only):
   - Sliders/curves: +25% chase rate
   - Changeups/splitters: +15% chase rate

5. Count adjustments:
   - 2 strikes: +15% in-zone, +40% out-of-zone
   - 3 balls: -50% out-of-zone
```

---

## Diagnostic Results

### Test Setup
- **Script**: `diagnose_swing_logic.py`
- **Trials per test**: 1,000 iterations
- **Test locations**: Heart, edges, borderline, chase zones

### Key Findings

#### 1. ✅ Base Swing Rates (Acceptable)

| Zone | Location | Swing Rate | MLB Target | Status |
|------|----------|------------|------------|--------|
| Heart | (0", 30") | 88.1% | ~75-85% | Slightly high |
| Edge | (7", 30") | 77.1% | ~65-75% | ✅ Good |
| Borderline | (9", 30") | 14.3% | ~30-35% | Low (but reasonable) |
| Chase Low | (0", 12") | 1.9% | ~5-10% | Low |
| Way Outside | (16", 30") | 1.7% | ~1-3% | ✅ Good |

**Overall**: 84.6% swing rate on heart strikes, 13.3% chase rate on borderline pitches.

#### 2. ❌ CRITICAL ISSUE: Weak Discipline Effect

**Test**: Chase rate on pitch at (10", 16") - just outside zone

| Discipline Level | ZONE_DISCERNMENT | Discernment Factor | Chase Rate (0-0) |
|------------------|-------------------|-------------------|------------------|
| Poor (20k) | 20000 | 0.452 | 18.0% |
| Below Avg (40k) | 40000 | 0.612 | 13.0% |
| Average (50k) | 50000 | 0.721 | 13.6% |
| Good (70k) | 70000 | 0.846 | 10.8% |
| Elite (90k) | 90000 | 0.904 | 10.8% |

**Spread**: Poor (18.0%) - Elite (10.8%) = **only 7.2%**

**MLB Comparison**:
- Hitters with poor discipline (high chase rate): ~35-40%
- Hitters with elite discipline (low chase rate): ~20-25%
- Expected spread: **15-20 percentage points**

**Diagnosis**: The discipline multiplier `(1 - discipline_factor * 0.6)` is not aggressive enough.

#### 3. ⚠️ Aggression Factor Paradox

**Observation**: "Aggressive" hitters (low SWING_DECISION_LATENCY) have *lower* swing probabilities than disciplined hitters.

**Example** (Heart strike):
- Disciplined hitter (latency=70k, aggr=+0.244): 91.0% swing rate
- Aggressive hitter (latency=30k, aggr=-0.300): 77.4% swing rate

**Root Cause**: The aggression_factor calculation is inverted:
```python
# Current (line 645):
aggression_factor = np.clip(1.0 - (decision_latency_ms - 75) / 125, 0.2, 0.9)

# For aggressive hitter with latency=200ms (poor/slow):
# aggression_factor = 1.0 - (200 - 75) / 125 = 0.0 → clipped to 0.2 (LOW)

# For patient hitter with latency=100ms (elite/fast):
# aggression_factor = 1.0 - (100 - 75) / 125 = 0.8 (HIGH)
```

This is backwards! Fast decision makers should be *more* aggressive, not less.

#### 4. ✅ Zone Gradient (Good)

Swing probability decreases smoothly from center (87%) to zone edge (76%) to outside (14% → 2%).

#### 5. ✅ Count Adjustments (Working)

- **0-2 count**: Swing rates increase (+5-15%)
- **3-2 count**: Chase rates decrease (-40-50%)

---

## Identified Issues

### Issue 1: Insufficient Discipline Differentiation ❌

**Current**: 7.2% spread between poor and elite discipline
**Target**: 15-20% spread
**Impact**: High

Hitters with different ZONE_DISCERNMENT ratings behave too similarly, reducing gameplay variety and realism.

### Issue 2: Aggression Factor Inverted ⚠️

**Current**: Fast decision makers swing *less* often
**Expected**: Fast decision makers should swing *more* often
**Impact**: Medium

The SWING_DECISION_LATENCY attribute works opposite to its intended purpose.

### Issue 3: No Expected Value Reasoning ⚠️

**Current**: Swing decisions based solely on probabilistic models
**Missing**: EV calculation considering count, outs, runners, game situation
**Impact**: Low (nice-to-have)

Real hitters adjust swing decisions based on:
- Strike probability
- Expected contact quality given location
- Run value of taking vs swinging in current count

### Issue 4: Limited Pitch Recognition ⚠️

**Current**: Only breaking balls get chase bonuses
**Missing**: Pitch-specific recognition per hitter (some hitters struggle with sliders, others with changeups)
**Impact**: Low (enhancement)

The `pitch_recognition` attribute exists but isn't fully utilized in swing decisions.

---

## Proposed Improvements

### Fix 1: Increase Discipline Effect (HIGH PRIORITY)

**Change location**: `batted_ball/player.py:638-639`

**Current code**:
```python
else:
    # Good discipline = much lower chase rate
    swing_prob = base_swing_prob * (1 - discipline_factor * 0.6)
```

**Proposed change**:
```python
else:
    # Good discipline = much lower chase rate
    # Increased from 0.6 to 0.85 to create larger spread
    # Elite discipline (0.90 factor): 1 - 0.90*0.85 = 0.235 → 76.5% reduction
    # Poor discipline (0.45 factor):  1 - 0.45*0.85 = 0.617 → 38.3% reduction
    swing_prob = base_swing_prob * (1 - discipline_factor * 0.85)
```

**Expected impact**:
- Poor discipline (0.45): 35% base → 21.6% chase (38% reduction)
- Elite discipline (0.90): 35% base → 8.2% chase (77% reduction)
- **New spread**: 13.4 percentage points (better!)

### Fix 2: Correct Aggression Factor Calculation (HIGH PRIORITY)

**Change location**: `batted_ball/player.py:641-646`

**Current code**:
```python
# Adjust for decision speed (faster decisions = more aggressive swings)
# Swing decision latency: lower ms = faster = more aggressive
# Map to aggression factor: 75ms (elite, fast) = 0.9, 130ms (avg) = 0.5, 200ms (slow) = 0.2
decision_latency_ms = self.attributes.get_swing_decision_latency_ms()
aggression_factor = np.clip(1.0 - (decision_latency_ms - 75) / 125, 0.2, 0.9)
swing_prob = swing_prob * (0.8 + aggression_factor * 0.4)
```

**Issue**: The comment says "faster = more aggressive" but the math does the opposite.

**Proposed fix**:
```python
# Adjust for decision speed (faster decisions = more aggressive swings)
# Swing decision latency: lower ms = faster = more aggressive
# Map to aggression factor:
#   75ms (elite/fast) → 0.9 (very aggressive)
#   130ms (average)   → 0.5 (neutral)
#   200ms (slow)      → 0.2 (passive)
decision_latency_ms = self.attributes.get_swing_decision_latency_ms()

# CORRECTED: Lower latency = higher aggression
# aggression_factor = (200 - latency_ms) / 125
# 75ms → (200-75)/125 = 1.0 → clip to 0.9
# 130ms → (200-130)/125 = 0.56 → ~0.5
# 200ms → (200-200)/125 = 0.0 → clip to 0.2
aggression_factor = np.clip((200.0 - decision_latency_ms) / 125.0, 0.2, 0.9)

# Multiplier range: 0.88× (passive) to 1.16× (aggressive)
swing_prob = swing_prob * (0.8 + aggression_factor * 0.4)
```

**Expected impact**:
- Aggressive hitters (75ms latency): 16% boost to swing rate
- Passive hitters (200ms latency): 12% reduction to swing rate

### Fix 3: Add Expected Value Reasoning (OPTIONAL)

**New function**: Add `calculate_swing_ev()` method

**Pseudocode**:
```python
def calculate_swing_ev(self, pitch_location, is_strike, count):
    """
    Calculate expected run value of swinging vs taking.

    Returns
    -------
    tuple
        (ev_swing, ev_take) - Expected run values
    """
    balls, strikes = count

    # Estimate strike probability (from pitcher's perspective)
    strike_prob = 0.95 if is_strike else 0.10

    # Estimate contact probability
    contact_prob = self._estimate_contact_prob(pitch_location, is_strike)

    # Run value table (simplified)
    rv_strikeout = -0.30
    rv_walk = +0.33
    rv_single = +0.48
    rv_out = -0.27
    rv_called_strike = -0.05
    rv_ball = +0.04

    # EV if swing
    ev_swing = (
        contact_prob * (0.70 * rv_single + 0.30 * rv_out)  # Simplified
        + (1 - contact_prob) * rv_strikeout
    )

    # EV if take
    ev_take = strike_prob * rv_called_strike + (1 - strike_prob) * rv_ball

    return ev_swing, ev_take
```

**Usage**: Compare EVs and bias swing decision toward higher EV option.

**Impact**: More "smart" swings - hitters protect with 2 strikes, take on 3-0, etc.

### Fix 4: Enhance Pitch Recognition (OPTIONAL)

**Use existing** `pitch_recognition` dictionary more aggressively.

**Change location**: `batted_ball/player.py:653-659`

**Enhancement**:
```python
# Pitch type affects chase rate (breaking balls fool hitters)
pitch_type_lower = pitch_type.lower()
if not is_strike:  # Only affects out-of-zone pitches
    # Base pitch type modifiers
    if 'slider' in pitch_type_lower or 'curve' in pitch_type_lower:
        pitch_mod = 1.25  # +25% chase rate on breaking balls
    elif 'change' in pitch_type_lower or 'splitter' in pitch_type_lower:
        pitch_mod = 1.15  # +15% chase rate on off-speed
    else:
        pitch_mod = 1.0

    # Apply hitter-specific pitch recognition if available
    if pitch_type in self.pitch_recognition:
        recog_multiplier = self.get_pitch_recognition_multiplier(pitch_type)
        pitch_mod *= recog_multiplier

    swing_prob *= pitch_mod
```

**Impact**: Hitters who struggle with sliders chase them more; elite recognition reduces chase.

---

## Implementation Priority

### Phase 1: Critical Fixes (Do Now) ✅

1. **Fix discipline effect** (Issue #1)
   - File: `batted_ball/player.py:639`
   - Change: `0.6` → `0.85`
   - Testing: Re-run `diagnose_swing_logic.py`, verify spread >12%

2. **Fix aggression factor** (Issue #2)
   - File: `batted_ball/player.py:645`
   - Change: Invert formula
   - Testing: Verify aggressive hitters swing more, not less

### Phase 2: Enhancements (Nice-to-Have) 📋

3. **Add EV reasoning** (Issue #3)
   - New method in Hitter class
   - Integrate with swing decision
   - Testing: Check that 3-0 swing rate drops, 0-2 protection increases

4. **Enhance pitch recognition** (Issue #4)
   - Extend existing logic
   - Testing: Verify hitter-specific chase rates vary by pitch

---

## Testing Plan

### Test 1: Discipline Spread

**Run**: `python diagnose_swing_logic.py`

**Check**:
- Poor discipline (20k) chase rate: ~25-30%
- Elite discipline (90k) chase rate: ~10-15%
- Spread: **≥12 percentage points**

### Test 2: Aggression Behavior

**Create** two hitters:
- Fast decision (30k latency) → ~75ms
- Slow decision (70k latency) → ~160ms

**Check**:
- Fast decision hitter swings **more** on heart strikes
- Fast decision hitter chases **more** on borderline pitches

### Test 3: Game Simulation

**Run**: `python examples/quick_game_test.py`

**Check**:
- Team with high-discipline lineup: lower K rate, higher BB rate
- Team with aggressive lineup: higher K rate, more balls in play

### Test 4: Validation Suite

**Run**: `python -m batted_ball.validation`

**Check**: All 7/7 benchmarks still pass (swing logic doesn't affect physics)

---

## MLB Data Comparison

### MLB Statcast Benchmarks (2024 Season)

| Metric | MLB Average | Expected After Fixes |
|--------|-------------|----------------------|
| In-zone swing rate | 67-70% | 70-75% (calibrated) |
| Out-of-zone (chase) rate | 28-32% | 15-20% (avg hitter) |
| Chase rate - aggressive hitters | 35-40% | 25-30% |
| Chase rate - disciplined hitters | 20-25% | 10-15% |
| Heart of zone swing rate | 75-85% | 85-90% |

**Note**: The simulation may run slightly higher swing rates due to perfect pitch recognition (no deception from arm angle, tunneling, etc.).

---

## Code Changes Summary

### File: `batted_ball/player.py`

#### Change 1 (Line 639):
```diff
         else:
             # Good discipline = much lower chase rate
-            swing_prob = base_swing_prob * (1 - discipline_factor * 0.6)
+            swing_prob = base_swing_prob * (1 - discipline_factor * 0.85)
```

#### Change 2 (Line 645):
```diff
         decision_latency_ms = self.attributes.get_swing_decision_latency_ms()
-        aggression_factor = np.clip(1.0 - (decision_latency_ms - 75) / 125, 0.2, 0.9)
+        aggression_factor = np.clip((200.0 - decision_latency_ms) / 125.0, 0.2, 0.9)
         swing_prob = swing_prob * (0.8 + aggression_factor * 0.4)
```

---

## Conclusion

The current swing logic is **fundamentally sound** but has two critical bugs:

1. ❌ Discipline effect too weak (7% spread vs 15-20% needed)
2. ❌ Aggression factor inverted (fast hitters swing less instead of more)

**Recommended action**: Implement Phase 1 fixes immediately. Phase 2 enhancements can be added incrementally.

**Expected outcome**: More realistic and differentiated hitter behavior, better alignment with MLB data, increased gameplay variety.

---

**Document Version**: 1.0
**Last Updated**: 2025-11-20
**Next Review**: After Phase 1 implementation and testing
