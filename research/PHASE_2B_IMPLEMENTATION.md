# Phase 2B Implementation - BB% Decoupling (Walk Rate Control)

**Date**: 2025-11-20
**Status**: ✅ IMPLEMENTED - Ready for Testing
**Branch**: `claude/implement-v2-engine-01Y2MzbM9RsZ79GXBF1RLnow`
**Commit**: 4296496

---

## Overview

Phase 2B implements the BB% (Walk Rate) decoupling system from the v2 Implementation Plan. This phase introduces **dynamic pitcher control** and **umpire variability** to achieve realistic walk rates (8-9%) independent of strikeout rates.

**Goal**: Achieve 8-9% BB rate independent of K% (22% from Phase 2A)

**Current Baseline (Phase 2A)**: BB% ~2-4% (too low)
**Target**: BB% = 8-9%

---

## What Was Implemented

### 1. PitcherControlModule (`batted_ball/pitcher_control.py`)

**Purpose**: Replace hardcoded "intentional ball" probabilities with dynamic zone targeting.

**Key Features**:
- **Dynamic Zone Targeting**: Probability-based zone targeting that adjusts by count
- **Count-Based Strategy**:
  - 3-ball count: 90% zone targeting (must throw strike)
  - 2-strike count: 45% zone targeting (can waste pitches)
  - Behind in count (2-0, 3-1): 55% zone targeting (nibble)
  - Ahead in count (0-1, 0-2): 70% zone targeting (attack)
  - Neutral count (0-0, 1-1): 62% zone targeting (balanced)
- **Pitcher Attributes**:
  - CONTROL: Affects confidence in zone targeting
  - NIBBLING_TENDENCY: Personality trait (aggressive vs careful)
- **Location Generation**:
  - Zone targets: center, edge, or corner based on count
  - Out-of-zone targets: chase pitches (2-strike) or waste pitches

**Code Highlights**:
```python
def determine_zone_target_probability(balls, strikes, batter_threat_level):
    # Base probability from count
    if balls == 3:
        base_zone_prob = 0.90  # Must throw strike
    elif strikes == 2:
        base_zone_prob = 0.45  # Can waste
    elif balls >= 2:
        base_zone_prob = 0.55  # Behind, nibble
    elif strikes >= 1 and balls == 0:
        base_zone_prob = 0.70  # Ahead, attack
    else:
        base_zone_prob = 0.62  # Neutral

    # Adjust for control and nibbling
    control_adjustment = (control_bias - 0.65) * modifier
    nibbling_adjustment = (nibbling_tendency - 0.50) * 0.15

    return clamp(base_zone_prob + adjustments, 0.10, 0.95)
```

**Lines of Code**: 370

---

### 2. UmpireModel (`batted_ball/umpire.py`)

**Purpose**: Add realistic umpire variability to ball/strike calls on borderline pitches.

**Key Features**:
- **Three-Zone System**:
  1. **Clear Strike** (>2" inside zone): Always strike (100%)
  2. **Borderline** (within 2" of edge): Probabilistic call
  3. **Clear Ball** (>2" outside zone): Always ball (100%)
- **Borderline Call Logic**:
  - Base probability: 50% strike on edge pitches (configurable)
  - Distance-based adjustment: Closer to zone = higher strike probability
  - Catcher framing bonus: Up to +5% strike probability
- **Realistic Strike Zone**:
  - Horizontal: ±8.5" from center (17" wide)
  - Vertical: 18" to 42" (24" tall)
- **Framing Integration**:
  - Elite framers (85k+): ~90% of max bonus (~4.5% extra strike prob)
  - Average framers (50k): ~25% of max bonus (~1.25% extra strike prob)
  - Poor framers (20k): ~5% of max bonus (~0.25% extra strike prob)

**Code Highlights**:
```python
def call_pitch(horizontal_inches, vertical_inches, framing_bonus):
    # Check if clearly in or out
    if is_clearly_in_zone(horizontal, vertical):
        return 'strike'
    if is_clearly_out_of_zone(horizontal, vertical):
        return 'ball'

    # Borderline: Probabilistic
    distance_from_zone = calculate_distance_from_zone(horizontal, vertical)

    # Strike probability based on distance
    if distance_from_zone <= 0:  # Inside zone
        base_prob = borderline_bias + ((1.0 - borderline_bias) *
                    (-distance / borderline_distance))
    else:  # Outside zone
        base_prob = borderline_bias * (1.0 - (distance / borderline_distance))

    # Apply framing
    strike_probability = base_prob + framing_bonus

    return 'strike' if random() < strike_probability else 'ball'
```

**Lines of Code**: 397

---

### 3. New Attributes

#### PitcherAttributes.NIBBLING_TENDENCY (0-100,000 scale)

**Purpose**: Pitcher personality trait for zone targeting behavior.

**Mapping**:
- 0: 0.20 (very aggressive, attacks zone relentlessly)
- 50k: 0.50 (balanced approach, adjusts by situation)
- 85k: 0.75 (careful, nibbles edges frequently)
- 100k: 0.90 (extremely careful, rarely gives in)

**Impact**:
- High nibbling: Reduces zone targeting when not forced (more waste pitches)
- Low nibbling: More aggressive zone targeting even when ahead
- Affects ~15% of zone probability when not at extremes (0/3-ball, 0/2-strike)

**Code**:
```python
def get_nibbling_tendency(self) -> float:
    return piecewise_logistic_map(
        self.NIBBLING_TENDENCY,
        human_min=0.20,
        human_cap=0.75,
        super_cap=0.90
    )
```

#### FielderAttributes.FRAMING (0-100,000 scale)

**Purpose**: Catcher pitch framing ability for umpire model.

**Mapping**:
- Direct 0-100k scale (no transformation needed)
- Used by UmpireModel.get_framing_bonus() to calculate strike bonus

**Impact**:
- Elite (85k+): +4-5% strike probability on borderline pitches
- Average (50k): +1-1.5% strike probability
- Poor (20k): +0-0.5% strike probability
- ~20-30 borderline pitches per game → 1-2 extra strikes for elite framers

**Code**:
```python
def get_framing_rating(self) -> float:
    """Direct return of FRAMING attribute (0-100k)"""
    return float(self.FRAMING)
```

---

### 4. Configuration Constants (`batted_ball/constants.py`)

#### Pitcher Control Module Constants

```python
# Zone targeting probabilities by count
BB_ZONE_TARGET_NEUTRAL = 0.62      # Neutral counts (0-0, 1-1, 2-2)
BB_ZONE_TARGET_AHEAD = 0.70        # Ahead in count (0-1, 0-2)
BB_ZONE_TARGET_BEHIND = 0.55       # Behind in count (2-0, 3-1)
BB_ZONE_TARGET_THREE_BALL = 0.90   # 3-ball count (must throw strike)
```

**Tuning Range**: ±0.05 for each target
- If BB% too high: Increase zone targets by 0.02-0.05
- If BB% too low: Decrease zone targets by 0.02-0.05

#### Umpire Model Constants

```python
# Umpire call probabilities
BB_UMPIRE_BORDERLINE_BIAS = 0.50      # Base strike prob on borderline
                                       # 0.50 = neutral, 0.55 = pitcher-friendly

BB_BORDERLINE_DISTANCE_INCHES = 2.0   # Width of borderline zone
                                       # Pitches within ±2" of edge are borderline

BB_FRAMING_BONUS_MAX = 0.05           # Max catcher framing bonus
                                       # Elite catchers add up to +5% strike prob
```

**Tuning Range**:
- BB_UMPIRE_BORDERLINE_BIAS: 0.45-0.55 (±5% strike probability)
- BB_FRAMING_BONUS_MAX: 0.00-0.08 (0% to 8% max bonus)

#### Nibbling Personality

```python
BB_NIBBLING_BASE = 0.50  # Base nibbling tendency (0-1 scale)
                         # 0.0 = always aggressive
                         # 1.0 = always careful
```

#### Feature Flags

```python
V2_PITCHER_CONTROL_MODULE_ENABLED = True  # Enable dynamic zone targeting
V2_UMPIRE_MODEL_ENABLED = True            # Enable probabilistic borderline calls
```

**Usage**: Set to False to disable V2 features and use legacy V1 logic.

---

### 5. Integration (`batted_ball/at_bat.py`)

#### Changes to AtBatSimulator.__init__

**New parameter**:
```python
def __init__(
    self,
    pitcher: Pitcher,
    hitter: Hitter,
    # ... existing parameters ...
    catcher_framing_rating: float = 50000.0,  # NEW
):
```

**New instances**:
```python
# V2 Phase 2B: Create pitcher control and umpire models
if V2_PITCHER_CONTROL_MODULE_ENABLED:
    self.pitcher_control = PitcherControlModule(pitcher)
else:
    self.pitcher_control = None

if V2_UMPIRE_MODEL_ENABLED:
    self.umpire = UmpireModel()
else:
    self.umpire = None
```

#### Changes to select_target_location()

**V2 Logic** (when enabled):
```python
if V2_PITCHER_CONTROL_MODULE_ENABLED and self.pitcher_control is not None:
    # Use new pitcher control module for dynamic zone targeting
    horizontal_target, vertical_target = self.pitcher_control.generate_pitch_location(
        balls, strikes, pitch_type
    )

    # Simplified intention for return_intention compatibility
    in_zone = check_if_in_zone(horizontal_target, vertical_target)
    intention = 'strike_looking' if in_zone else 'ball_intentional'

    return (horizontal_target, vertical_target), intention if return_intention else (horizontal_target, vertical_target)
```

**Legacy V1 Logic** (when disabled):
- Falls back to original `_determine_pitch_intention()` logic
- Uses hardcoded intention probabilities

#### Changes to simulate_pitch()

**V2 Logic** (when enabled):
```python
if V2_UMPIRE_MODEL_ENABLED and self.umpire is not None:
    # Get framing bonus from catcher
    framing_bonus = self.umpire.get_framing_bonus(self.catcher_framing_rating)

    # Umpire makes call based on final pitch location
    final_h = result.plate_y * 12  # Convert feet to inches
    final_v = result.plate_z * 12  # Convert feet to inches
    umpire_call = self.umpire.call_pitch(final_h, final_v, framing_bonus)
    is_strike = (umpire_call == 'strike')
else:
    # Legacy V1: Use physics-based strike zone (perfect umpire)
    is_strike = result.is_strike
```

**Result**:
- `pitch_data['is_strike']` now uses umpire call in V2
- Borderline pitches have realistic variability
- Catcher framing affects strike probability

---

## How Phase 2B Achieves BB% Decoupling

### Problem Statement (Before Phase 2B)

**Issue**: BB% was too low (~2-4%) and coupled to K%.
- Hardcoded "intentional ball" probabilities were too conservative
- No umpire variability → perfect strike zone → fewer walks
- No catcher framing → missed strike-stealing opportunities
- When K% increased (Phase 2A), BB% often decreased paradoxically

### Solution (Phase 2B)

**1. Dynamic Zone Targeting** (PitcherControlModule)
- **Old**: Fixed probabilities (e.g., "10% intentional ball on first pitch")
- **New**: Dynamic probabilities based on count, control, nibbling tendency
- **Impact**: More realistic ball rates by count
  - 3-ball count: 90% zone (10% ball) → ~10% walk rate on 3-ball
  - Behind (2-0, 3-1): 55% zone (45% ball) → more nibbling → more walks
  - Neutral: 62% zone (38% ball) → realistic MLB zone rate

**2. Umpire Variability** (UmpireModel)
- **Old**: Perfect umpire → exact strike zone enforcement
- **New**: Probabilistic borderline calls → realistic strike zone
- **Impact**: Borderline pitches (20-30 per game) have uncertainty
  - Pitches just outside zone: ~25-45% called strike (varies by distance)
  - Pitches just inside zone: ~55-75% called strike (varies by distance)
  - Creates "effective" strike zone that's larger than rulebook zone

**3. Catcher Framing** (FRAMING attribute)
- **Old**: No framing influence → missed strike-stealing
- **New**: Elite framers add +4-5% strike probability on borderline
- **Impact**: 20-30 borderline pitches/game × 5% bonus = 1-2 extra strikes
  - Fewer walks for teams with elite framing catchers
  - More walks for teams with poor framing catchers

### Independence from K%

**K% (Phase 2A)** controlled by:
- Whiff probability (VISION attribute)
- 2-strike put-away probability
- Foul ball fatigue

**BB% (Phase 2B)** controlled by:
- Zone targeting probability (CONTROL, NIBBLING_TENDENCY)
- Umpire borderline bias
- Catcher framing bonus

**No Coupling**:
- Adjusting whiff rates (K%) doesn't affect zone targeting (BB%)
- Adjusting zone targeting (BB%) doesn't affect whiff rates (K%)
- Each system operates independently with separate tuning knobs

---

## Expected Results

### BB% Projection

**Current (Phase 2A only)**: ~2-4% BB rate
**Target**: 8-9% BB rate

**Mechanism**:
```
Ball% = 1 - Zone%
Zone% = 62% (neutral count average, from BB_ZONE_TARGET_NEUTRAL)
Ball% = 38%

Chase rate = 22-25% (from Phase 2A)
Balls taken = 75-78% of ball pitches

Expected BB% = (Ball% × Take%) / 4
             = (0.38 × 0.76) / 4
             = 7.2%
```

**With Adjustments**:
- Higher nibbling tendency: BB% → 8-9%
- Lower control pitchers: BB% → 9-10%
- Poor umpire calls: BB% → 8.5-9.5%
- Good catcher framing: BB% → 6.5-7.5%

**Range**: 7-10% BB rate (target 8-9%)

### Zone Rate by Count

**Expected Distribution**:
| Count | Zone Target | Actual Zone % (with command error) |
|-------|-------------|--------------------------------------|
| 0-0 | 62% | 58-62% |
| 1-0 | 62% | 58-62% |
| 2-0 | 55% | 50-55% |
| 3-0 | 90% | 85-88% |
| 0-1 | 70% | 65-70% |
| 1-1 | 62% | 58-62% |
| 2-1 | 62% | 58-62% |
| 3-1 | 55% | 50-55% |
| 0-2 | 70% | 65-70% |
| 1-2 | 62% | 58-62% |
| 2-2 | 62% | 58-62% |
| 3-2 | 62% | 58-62% |

**Overall Zone Rate**: 60-65% (MLB target: 62-65%)

### Umpire Call Distribution

**Borderline Pitches** (within 2" of zone edge): ~20-30 per game

**Expected Calls**:
- Just inside zone (+0" to +2"): 55-75% strike
- On edge (±0.5"): 45-55% strike
- Just outside zone (-2" to 0"): 25-45% strike

**Impact on Strike Zone**:
- Effective zone width: ~19-20" (vs rulebook 17")
- Effective zone height: ~26-28" (vs rulebook 24")
- Creates realistic "umpire zone" that's slightly larger than rulebook

---

## Tuning Guide

### If BB% is Too Low (<7%)

**Primary Adjustment**: Reduce zone targeting
```python
BB_ZONE_TARGET_NEUTRAL = 0.62 → 0.58  # -4pp zone rate
BB_ZONE_TARGET_AHEAD = 0.70 → 0.66     # -4pp zone rate
BB_ZONE_TARGET_BEHIND = 0.55 → 0.51    # -4pp zone rate
```

**Expected Impact**: Each -1pp zone rate → +0.5pp BB rate
- -4pp zone rate → +2pp BB rate (e.g., 6% → 8%)

**Secondary Adjustment**: Increase nibbling tendency
```python
# Increase NIBBLING_TENDENCY for all pitchers by 5-10k
# Or adjust BB_NIBBLING_BASE
BB_NIBBLING_BASE = 0.50 → 0.55
```

**Tertiary Adjustment**: Reduce umpire bias (batter-friendly)
```python
BB_UMPIRE_BORDERLINE_BIAS = 0.50 → 0.47  # Fewer borderline strikes
```

### If BB% is Too High (>10%)

**Primary Adjustment**: Increase zone targeting
```python
BB_ZONE_TARGET_NEUTRAL = 0.62 → 0.66  # +4pp zone rate
BB_ZONE_TARGET_AHEAD = 0.70 → 0.74     # +4pp zone rate
BB_ZONE_TARGET_BEHIND = 0.55 → 0.59    # +4pp zone rate
```

**Expected Impact**: Each +1pp zone rate → -0.5pp BB rate

**Secondary Adjustment**: Decrease nibbling tendency
```python
BB_NIBBLING_BASE = 0.50 → 0.45
```

**Tertiary Adjustment**: Increase umpire bias (pitcher-friendly)
```python
BB_UMPIRE_BORDERLINE_BIAS = 0.50 → 0.53  # More borderline strikes
```

### If Zone Rate is Correct but BB% Still Wrong

**Issue**: Zone rate is 62-65% but BB% isn't 8-9%
**Likely Cause**: Swing decisions (from hitter discipline)

**Check**:
1. Chase rate: Should be 22-25%
2. Take rate on balls: Should be 75-78%

**If chase rate is too high** (>30%):
- Hitters swinging at too many balls → fewer walks
- Increase hitter ZONE_DISCERNMENT attribute
- Or reduce 2-strike desperation swing probability

**If take rate is too low** (<70%):
- Hitters not taking enough balls → fewer walks
- Increase hitter discipline
- Or reduce swing% on out-of-zone pitches

---

## Testing Plan

### Local Testing

**Command**:
```bash
python research/run_50game_fixed_diagnostic.py
```

**What to Check**:

1. **BB% (CRITICAL)**:
   - Target: 8-9%
   - Success: 7-10%
   - Problem: <6% or >11%

2. **Zone Rate** (overall):
   - Target: 62-65%
   - Success: 60-67%
   - Problem: <58% or >70%

3. **Zone Rate by Count**:
   - 3-ball: 85-90% (should be very high)
   - 2-strike: 40-50% (should be low, waste pitches)
   - Behind (2-0, 3-1): 50-58%
   - Ahead (0-1, 0-2): 65-73%
   - Neutral: 58-65%

4. **K% Maintenance**:
   - Should remain ~19-22% (from Phase 2A)
   - If K% changes, BB% decoupling failed

5. **Chase Rate**:
   - Target: 22-25%
   - Should be stable from Phase 2A

6. **Borderline Call Distribution**:
   - Track strike% on pitches within 1-2" of zone edge
   - Should see ~45-55% strike rate on edge pitches

### What Success Looks Like

**Phase 2B Complete** when:
- ✅ BB% = 8-9%
- ✅ Zone rate = 62-65%
- ✅ K% maintained at 19-22% (no coupling)
- ✅ Chase rate maintained at 22-25%
- ✅ Zone rate by count matches MLB patterns
- ✅ Borderline pitches have realistic strike% distribution

**Next Step**: Move to Phase 2C (HR/FB decoupling) or Phase 3 (tuning)

---

## Files Modified

1. **batted_ball/pitcher_control.py** (NEW, 370 lines)
   - PitcherControlModule class
   - Dynamic zone targeting logic
   - Pitcher personality integration

2. **batted_ball/umpire.py** (NEW, 397 lines)
   - UmpireModel class
   - Borderline call logic
   - Catcher framing integration

3. **batted_ball/attributes.py** (MODIFIED)
   - Added NIBBLING_TENDENCY to PitcherAttributes
   - Added get_nibbling_tendency() method
   - Added FRAMING to FielderAttributes
   - Added get_framing_rating() method

4. **batted_ball/constants.py** (MODIFIED)
   - Added Phase 2B configuration section
   - 10 new tuning constants
   - 2 feature flags

5. **batted_ball/at_bat.py** (MODIFIED)
   - Added imports for PitcherControlModule, UmpireModel
   - Added catcher_framing_rating parameter
   - Created pitcher_control and umpire instances
   - Modified select_target_location() to use V2 logic
   - Modified simulate_pitch() to use V2 umpire calls

**Total Lines Added**: ~900 lines
**Total Lines Modified**: ~50 lines

---

## Known Limitations

1. **Catcher Framing**: Currently uses a single rating for the whole game
   - Future: Could vary by umpire or situation
   - Current impact: Small (~1-2 strikes per game)

2. **Umpire Consistency**: Currently fixed at 1.0 (perfect consistency)
   - Future: Could add umpire-to-umpire variation
   - Current impact: No umpire-specific biases

3. **Batter Threat Level**: Currently fixed at 0.5 (neutral)
   - Future: Could adjust zone targeting based on batter danger
   - Current impact: No batter-specific nibbling

4. **Intentional Walk**: Not explicitly modeled
   - Current: Very rare due to 3-ball zone targeting (90%)
   - Future: Could add explicit IBB logic

5. **Called Strike 3**: Not tracked separately from swinging K
   - Phase 2A handles overall K%, but doesn't distinguish types
   - Future: Could split K% into looking vs swinging

---

## Summary

**Phase 2B is COMPLETE** and ready for testing!

**What we built**:
- ✅ Dynamic pitcher control module (370 lines)
- ✅ Realistic umpire model with framing (397 lines)
- ✅ NIBBLING_TENDENCY pitcher personality
- ✅ FRAMING catcher attribute
- ✅ 10 tuning constants for BB% control
- ✅ Full integration into at_bat simulation
- ✅ Backwards compatible with V1 (feature flags)

**Expected outcome**:
- BB% = 8-9% (from 2-4%)
- Zone rate = 62-65%
- K% maintained at 19-22% (no coupling)
- Chase rate maintained at 22-25%

**Next steps**:
1. Run local testing: `python research/run_50game_fixed_diagnostic.py`
2. Check BB%, zone rate, K% independence
3. Tune if needed (see Tuning Guide above)
4. If successful: Move to Phase 2C (HR/FB decoupling)

---

**Implementation Complete**: 2025-11-20
**Commit**: 4296496
**Branch**: `claude/implement-v2-engine-01Y2MzbM9RsZ79GXBF1RLnow`
**Status**: ✅ READY FOR TESTING

Run the test and see if we've achieved BB% independence! 🎯
