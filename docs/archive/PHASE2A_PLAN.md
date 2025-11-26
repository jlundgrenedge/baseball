# Phase 2A: K% Decoupling - Implementation Plan

**Date**: 2025-11-20
**Status**: Starting Implementation
**Branch**: `claude/add-agent-mission-01G6so7LCSpGquX1yLqefgbh`
**Goal**: Fix K% from 6.5% → 22% (MLB target)

---

## Executive Summary

**Phase 1 Root Cause Analysis Identified**:
- **Chase rate = 0%** (should be 25-35%) 🚨 **PRIMARY ISSUE**
- In-zone swing rate = 82.5% (slightly high but acceptable)
- Contact rate = very high (need whiff logging to quantify)
- Barrel accuracy multipliers may be too generous (double-dipping concern)

**Phase 2A Strategy**:
1. **Fix chase rate mechanics** (0% → 25-35%) - CRITICAL
2. **Separate VISION from POWER** - Decouple contact frequency from contact quality
3. **Add two-stage strikeout model** - Put-away probability for finishing off batters
4. **Recalibrate whiff factors** - Reduce barrel accuracy impact

---

## Root Cause Deep Dive

### Issue #1: Zero Chase Rate 🚨

**Current Behavior** (from Phase 1 data):
```
In-Zone Swing%: 82.5% (MLB: ~65-70%)
Out-of-Zone Swing% (Chase): 0.0% (MLB: ~25-35%)
```

**Code Location**: `batted_ball/player.py:656-671`

**Current Logic**:
```python
discipline_factor = self.attributes.get_zone_discernment_factor()  # 0.45-0.90
if is_strike:
    swing_prob = base_swing_prob + (1 - discipline_factor) * 0.15
else:
    # Out-of-zone: reduce swing probability
    swing_prob = base_swing_prob * (1 - discipline_factor * 0.85)
```

**Problem Analysis**:
- Discipline factor of 0.85 is too strong for out-of-zone reduction
- Elite discipline (0.90 factor): `1 - 0.90*0.85 = 0.235` → 76.5% reduction
- This makes chase rate = `0.35 * 0.235 = 8.2%` (should be ~30%)
- In practice, we're seeing 0% chase rate → formula is over-suppressing

**Solution**:
- Reduce discipline impact from `0.85` → `0.40`
- Elite discipline (0.90 factor): `1 - 0.90*0.40 = 0.64` → 36% reduction
- New chase rate = `0.35 * 0.64 = 22.4%` for elite batters ✓
- Poor discipline (0.45 factor): `1 - 0.45*0.40 = 0.82` → 18% reduction
- New chase rate = `0.35 * 0.82 = 28.7%` for poor batters ✓
- Creates 6.3 percentage point spread (22.4% to 28.7%) - reasonable

### Issue #2: VISION vs POWER Not Decoupled

**Current Behavior**:
- Barrel accuracy affects BOTH whiff probability AND contact quality
- This is "double-dipping" - elite contact hitters get:
  1. Lower whiff rate (more frequent contact)
  2. Better exit velocity/launch angle (higher quality contact)
- This over-rewards elite contact ability

**Code Location**: `batted_ball/player.py:936-945`

**Current Logic**:
```python
# In calculate_whiff_probability()
barrel_error_mm = self.attributes.get_barrel_accuracy_mm()
contact_factor = 0.80 + (barrel_error_mm - 5) * 0.040  # 0.80-1.60
whiff_prob = base_whiff_rate * velocity_factor * break_factor * contact_factor
```

**Problem Analysis**:
- Barrel accuracy (POWER) is reducing whiff probability (VISION)
- These should be independent:
  - **VISION** = ability to make contact at all (affects whiff rate)
  - **POWER** = quality of contact when made (affects exit velo)
- Current system conflates them

**Solution**:
- Add new `VISION` attribute (0-100,000 scale)
- Map to "tracking ability" (0.5-1.0 scale)
- Use VISION for whiff calculations
- Use barrel accuracy ONLY for contact quality (exit velo/launch angle)

### Issue #3: No Put-Away Mechanism

**Current Behavior**:
- 2-strike situations use same whiff calculation as 0-2 or 1-2
- No increased likelihood of finishing off the at-bat
- Batters can foul off indefinitely with no penalty

**Code Location**: `batted_ball/at_bat.py:616-630`

**Current Logic**:
```python
whiff_prob = self.hitter.calculate_whiff_probability(...)
pitcher_whiff_mult = self.pitcher.get_pitch_whiff_multiplier(pitch_type)
whiff_prob *= pitcher_whiff_mult
whiff_prob = np.clip(whiff_prob, 0.05, 0.75)
if np.random.random() < whiff_prob:
    return None  # Whiff!
```

**Problem Analysis**:
- No adjustment for 2-strike count
- Pitchers should have advantage in put-away situations
- MLB data shows higher whiff rates with 2 strikes

**Solution**:
- Add "put-away factor" for 2-strike counts
- Increase whiff probability by 1.3× when strikes = 2
- Based on pitcher's "finishing ability" (stuff rating)
- Elite pitchers get 1.4-1.5× multiplier
- Average pitchers get 1.2-1.3× multiplier

---

## Implementation Tasks

### Task Group 1: Fix Chase Rate (CRITICAL)

**Priority**: 🔥 HIGHEST - This is the primary K% issue

#### Task 1.1: Reduce Discipline Impact on Chase Rate

**File**: `batted_ball/player.py:665-671`

**Current Code**:
```python
else:
    # Good discipline = much lower chase rate
    # FIXED 2025-11-20: Increased from 0.6 to 0.85 to create larger spread
    # Elite discipline (0.90 factor): 1 - 0.90*0.85 = 0.235 → 76.5% reduction
    # Poor discipline (0.45 factor):  1 - 0.45*0.85 = 0.617 → 38.3% reduction
    # This creates a ~13-15 percentage point spread matching MLB data
    swing_prob = base_swing_prob * (1 - discipline_factor * 0.85)
```

**New Code**:
```python
else:
    # Good discipline = lower chase rate, but not eliminating chases
    # PHASE 2A FIX 2025-11-20: Reduced from 0.85 to 0.40
    # Elite discipline (0.90 factor): 1 - 0.90*0.40 = 0.64 → 36% reduction
    #   → Base chase 35% * 0.64 = 22.4% actual chase rate ✓
    # Poor discipline (0.45 factor):  1 - 0.45*0.40 = 0.82 → 18% reduction
    #   → Base chase 35% * 0.82 = 28.7% actual chase rate ✓
    # This creates 6.3 percentage point spread (elite to poor)
    swing_prob = base_swing_prob * (1 - discipline_factor * 0.40)
```

**Expected Impact**:
- Chase rate: 0% → 22-29% (depending on batter discipline)
- K% increase: ~8% → ~15-18% (still need whiff fixes for full 22%)
- BB% impact: Minimal (chase rate affects out-of-zone pitches)

**Testing**:
```bash
python research/run_small_debug_test.py
# Should see out-of-zone swing rate increase from 0% to ~25%
```

#### Task 1.2: Add Count-Specific Chase Adjustments

**File**: `batted_ball/player.py:696-709`

**Current Code** (2-strike protection):
```python
if strikes == 2:
    # Protect the plate with 2 strikes
    if is_strike:
        swing_prob = min(swing_prob + 0.15, 0.95)  # +15%, cap at 95%
    else:
        swing_prob = min(swing_prob * 1.4, 0.70)  # +40% chase, cap at 70%
```

**Issue**: 1.4× multiplier on 0% chase = still 0%

**New Code**:
```python
if strikes == 2:
    # Protect the plate with 2 strikes
    if is_strike:
        swing_prob = min(swing_prob + 0.15, 0.95)  # +15%, cap at 95%
    else:
        # PHASE 2A FIX: Ensure minimum chase rate with 2 strikes
        # Base chase rate (after discipline) + 2-strike desperation
        base_chase_after_discipline = swing_prob
        two_strike_bonus = 0.15  # Flat +15% chase with 2 strikes
        swing_prob = min(base_chase_after_discipline * 1.4 + two_strike_bonus, 0.70)
```

**Expected Impact**:
- 2-strike chase rate: Increases by +15 percentage points
- More realistic "protect the plate" behavior
- K% increase: Additional ~2-3%

---

### Task Group 2: Separate VISION from POWER

**Priority**: 🔥 HIGH - Decouples contact frequency from contact quality

#### Task 2.1: Add VISION Attribute

**File**: `batted_ball/attributes.py`

**New Attribute**:
```python
class HitterAttributes:
    # Existing attributes
    BAT_SPEED: int           # 0-100,000 (power - exit velo)
    ATTACK_ANGLE: int        # 0-100,000 (launch angle tendency)
    CONTACT: int             # 0-100,000 (barrel accuracy - contact quality)
    DISCIPLINE: int          # 0-100,000 (zone recognition)

    # NEW: Phase 2A addition
    VISION: int              # 0-100,000 (tracking ability - contact frequency)
```

**Mapping Function**:
```python
def get_tracking_ability_factor(self) -> float:
    """
    Convert VISION rating to tracking ability factor (0.5-1.0).

    This affects whiff probability - higher vision = better pitch tracking = more contact.
    Separate from barrel accuracy which affects contact quality.

    Returns
    -------
    float
        0.5 = Poor tracking (elite pitches hard to follow)
        0.75 = Average tracking (typical MLB hitter)
        1.0 = Elite tracking (rarely fooled, very low whiff rate)
    """
    return piecewise_logistic_map(
        self.VISION,
        human_min=0.5,    # Poor vision → high whiff rate multiplier (2.0×)
        human_cap=0.75,   # Elite vision → average whiff rate (1.33×)
        super_cap=1.0     # Superhuman vision → low whiff rate (1.0×)
    )
```

**Note**: `tracking_ability_factor` is inverted when used:
- `whiff_prob *= (2.0 - tracking_ability_factor)`
- tracking = 0.5 → multiplier = 1.5× (high whiff)
- tracking = 0.75 → multiplier = 1.25× (average whiff)
- tracking = 1.0 → multiplier = 1.0× (low whiff)

#### Task 2.2: Update Whiff Calculation to Use VISION

**File**: `batted_ball/player.py:936-956`

**Current Code**:
```python
# Barrel accuracy affects ability to make contact
barrel_error_mm = self.attributes.get_barrel_accuracy_mm()
contact_factor = 0.80 + (barrel_error_mm - 5) * 0.040
# ...
whiff_prob = base_whiff_rate * velocity_factor * break_factor * contact_factor * pitch_contact_mult
```

**New Code**:
```python
# PHASE 2A: Use VISION for contact frequency, not barrel accuracy
# VISION affects whether contact is made at all (tracking ability)
tracking_ability = self.attributes.get_tracking_ability_factor()  # 0.5-1.0
vision_factor = 2.0 - tracking_ability  # Invert: 1.0-1.5
# vision_factor:
#   - tracking = 1.0 (elite) → factor = 1.0 (low whiff)
#   - tracking = 0.75 (avg) → factor = 1.25 (average whiff)
#   - tracking = 0.5 (poor) → factor = 1.5 (high whiff)

# Barrel accuracy NO LONGER affects whiff probability
# It only affects contact quality (exit velo/launch angle) in contact.py

whiff_prob = base_whiff_rate * velocity_factor * break_factor * vision_factor * pitch_contact_mult
```

**Expected Impact**:
- Decouples contact frequency from contact quality
- K% increase: ~3-5% (elite contact hitters will whiff more often)
- Power hitters can have high whiff rates (realistic)
- Contact hitters can have low power (realistic)

#### Task 2.3: Initialize VISION Attribute for Existing Players

**File**: `batted_ball/game_simulation.py:1284+` (in `create_test_team()`)

**Strategy**:
- For existing code, derive VISION from CONTACT initially
- Elite contact hitters (CONTACT > 75k) → Elite vision (VISION = CONTACT)
- Power hitters (BAT_SPEED > 75k) → Lower vision (VISION = 0.6 * CONTACT)
- This creates realistic archetypes:
  - Contact hitters: High VISION, low power (low K%, low HR)
  - Power hitters: Low VISION, high power (high K%, high HR)

**Code Addition**:
```python
# In create_test_team(), when creating HitterAttributes
if bat_speed > 75000:  # Power hitter
    vision = int(contact * 0.6)  # Lower vision = more whiffs
elif contact > 75000:  # Contact hitter
    vision = contact  # High vision = fewer whiffs
else:  # Balanced
    vision = int(contact * 0.85)
```

---

### Task Group 3: Add Put-Away Mechanism

**Priority**: 🟡 MEDIUM - Adds realism to 2-strike situations

#### Task 3.1: Add Put-Away Multiplier

**File**: `batted_ball/at_bat.py:616-634`

**Current Code**:
```python
whiff_prob = self.hitter.calculate_whiff_probability(
    pitch_velocity=pitch_velocity,
    pitch_type=pitch_type,
    pitch_break=pitch_break,
    debug_collector=self.debug_collector,
)

# NEW: Apply pitcher's pitch-specific effectiveness (stuff rating)
pitcher_whiff_mult = self.pitcher.get_pitch_whiff_multiplier(pitch_type)
whiff_prob *= pitcher_whiff_mult

# Clip to reasonable bounds after applying multipliers
whiff_prob = np.clip(whiff_prob, 0.05, 0.75)
```

**New Code**:
```python
whiff_prob = self.hitter.calculate_whiff_probability(
    pitch_velocity=pitch_velocity,
    pitch_type=pitch_type,
    pitch_break=pitch_break,
    debug_collector=self.debug_collector,
)

# Apply pitcher's pitch-specific effectiveness (stuff rating)
pitcher_whiff_mult = self.pitcher.get_pitch_whiff_multiplier(pitch_type)
whiff_prob *= pitcher_whiff_mult

# PHASE 2A: Add put-away multiplier for 2-strike counts
# Get current count from pitch_data context
current_count = pitch_data.get('count_before', (0, 0))
if current_count[1] >= 2:  # 2 strikes
    # Pitchers have advantage finishing off batters
    # Elite stuff (high stuff rating) → higher put-away ability
    stuff_rating = self.pitcher.attributes.get_stuff_rating()  # 0.0-1.0
    put_away_mult = 1.2 + (stuff_rating * 0.3)  # 1.2-1.5×
    whiff_prob *= put_away_mult

# Clip to reasonable bounds after applying multipliers
whiff_prob = np.clip(whiff_prob, 0.05, 0.80)  # Increased cap from 0.75 to 0.80
```

**Expected Impact**:
- 2-strike whiff rate: Increases by 20-50% depending on pitcher stuff
- K% increase: ~2-3%
- More realistic "put-away pitch" dynamics

#### Task 3.2: Add Stuff Rating to Pitcher Attributes

**File**: `batted_ball/attributes.py`

**New Method**:
```python
class PitcherAttributes:
    def get_stuff_rating(self) -> float:
        """
        Get overall "stuff" rating (0.0-1.0) representing pitch quality.

        Based on:
        - Velocity (higher = better stuff)
        - Movement (more movement = better stuff)
        - Deception (more deceptive = better stuff)

        Returns
        -------
        float
            0.0-0.4 = Below average stuff
            0.4-0.6 = Average stuff
            0.6-0.8 = Good stuff
            0.8-1.0 = Elite stuff (put-away ability)
        """
        # Simple average of velocity, movement, deception factors
        velocity_factor = (self.VELOCITY - 50000) / 50000  # 0.0-1.0
        movement_factor = (self.MOVEMENT - 50000) / 50000  # 0.0-1.0
        deception_factor = (self.DECEPTION - 50000) / 50000  # 0.0-1.0

        avg_stuff = (velocity_factor + movement_factor + deception_factor) / 3.0
        return np.clip(avg_stuff, 0.0, 1.0)
```

---

## Testing Strategy

### Test 1: Chase Rate Validation

**Script**: `research/test_chase_rate_fix.py`

**Approach**:
1. Run 10 at-bats with debug collector
2. Measure out-of-zone swing rate
3. Compare before/after Task 1.1

**Success Criteria**:
- Before: 0% chase rate
- After: 22-29% chase rate (depending on batter discipline)

### Test 2: K% Validation

**Script**: `research/run_small_debug_test.py` (re-run)

**Approach**:
1. Run 3 games with all Phase 2A changes
2. Measure K% in plate appearances
3. Compare to Phase 1 baseline (0% in sample, 6.5% in 10-game)

**Success Criteria**:
- After Task 1.1-1.2: K% increases to ~12-15%
- After Task 2.1-2.2: K% increases to ~18-20%
- After Task 3.1-3.2: K% increases to ~20-22% ✓ TARGET

### Test 3: Full 10-Game Validation

**Script**: `research/run_mlb_realism_baseline.py --games 10`

**Approach**:
1. Run full 10-game simulation with Phase 2A changes
2. Compare MLB realism benchmarks
3. Ensure K% reaches 22% without breaking other metrics

**Success Criteria**:
- K% = 20-24% (target: 22%)
- BB% unchanged or slightly improved (still ~18%, will fix in Phase 2B)
- Other metrics (BABIP, HR/FB, etc.) remain stable

---

## Implementation Order

### Sprint 1: Fix Chase Rate (Days 1-2)

1. ✅ Create Phase 2A implementation plan (this document)
2. ⏳ Task 1.1: Reduce discipline impact (0.85 → 0.40)
3. ⏳ Task 1.2: Add 2-strike chase adjustment
4. ⏳ Test 1: Validate chase rate fix
5. ⏳ Commit: "Phase 2A Sprint 1: Fix chase rate mechanics"

### Sprint 2: Separate VISION from POWER (Days 3-4)

6. ⏳ Task 2.1: Add VISION attribute to HitterAttributes
7. ⏳ Task 2.2: Update whiff calculation to use VISION
8. ⏳ Task 2.3: Initialize VISION for existing players
9. ⏳ Test 2: Validate K% improvement
10. ⏳ Commit: "Phase 2A Sprint 2: Decouple VISION from POWER"

### Sprint 3: Add Put-Away Mechanism (Day 5)

11. ⏳ Task 3.1: Add put-away multiplier for 2-strike counts
12. ⏳ Task 3.2: Add stuff rating to PitcherAttributes
13. ⏳ Test 3: Full 10-game validation
14. ⏳ Commit: "Phase 2A Sprint 3: Add put-away mechanism"

### Sprint 4: Documentation & Validation (Day 6)

15. ⏳ Document Phase 2A findings
16. ⏳ Update debug metrics to log VISION effects
17. ⏳ Create Phase 2A completion report
18. ⏳ Commit: "Phase 2A COMPLETE: K% fixed (6.5% → 22%)"

---

## Risk Assessment

### High Risks:

⚠️ **Chase rate fix may be insufficient** (Task 1.1)
- Mitigation: Start with 0.40 multiplier, can adjust to 0.35 if needed
- Fallback: Add flat minimum chase rate (15%) regardless of discipline

⚠️ **VISION attribute initialization may not match existing archetypes**
- Mitigation: Derive VISION from CONTACT initially
- Fallback: Add manual override for team creation

### Medium Risks:

⚠️ **K% may increase too much** (overcorrection)
- Mitigation: Test after each sprint, adjust multipliers
- Fallback: Increase minimum whiff bounds (0.05 → 0.08)

⚠️ **Other metrics may degrade** (BABIP, BB%, etc.)
- Mitigation: Run full validation suite after each sprint
- Fallback: Revert specific changes that break other metrics

### Low Risks:

✅ **Performance overhead** - No complex calculations added
✅ **Backward compatibility** - All changes are parameter adjustments
✅ **Code complexity** - Changes are localized to player.py and at_bat.py

---

## Success Criteria

### Phase 2A Success:

✅ **K% reaches 20-24%** (current: 6.5%, target: 22%)
✅ **Chase rate reaches 22-35%** (current: 0%, target: 25-35%)
✅ **VISION and POWER are decoupled** (power hitters can have high K%)
✅ **Put-away mechanism adds realism** (2-strike whiff rate increases)
✅ **Other MLB metrics remain stable** (BB%, BABIP, HR/FB, etc.)

### Exit Criteria:

- Run 20-game validation showing K% = 20-24% consistently
- Debug metrics show chase rate in 22-35% range
- No regressions in other MLB benchmark tests (7/10 → 8/10+ passing)

---

## Timeline

**Total Duration**: 6 days

- Sprint 1 (Chase Rate): Days 1-2
- Sprint 2 (VISION/POWER): Days 3-4
- Sprint 3 (Put-Away): Day 5
- Sprint 4 (Documentation): Day 6

**Estimated Completion**: 2025-11-26 (6 days from start)

---

**Document Created**: 2025-11-20
**Author**: Claude (AI Assistant)
**Session**: Agent Mission 01G6so7LCSpGquX1yLqefgbh
**Status**: Ready to Begin Sprint 1
