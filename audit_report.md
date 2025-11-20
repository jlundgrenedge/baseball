# Player Attribute Mapping Audit Report

**Date:** 2025-11-20
**Author:** Claude Code
**Purpose:** Audit how player attributes (0-100,000 scale) translate into physical performance

---

## Executive Summary

This audit examined player attribute mappings to identify whether ratings produce realistic variance across player types or if the ratings have muted or nonlinear effects.

### Key Findings

✅ **STRENGTHS:**
- Most attributes show good variance (10-50% difference from avg to elite)
- Mappings use continuous piecewise logistic functions (no hard tiers)
- Values calibrated to MLB Statcast data with documented sources
- Recent tuning improved realism significantly

⚠️ **ISSUES IDENTIFIED:**
1. **Constants.py mismatch** - Outdated values don't match attributes.py (HIGH PRIORITY)
2. **Baserunning consolidation** - base_running_iq handles too many concepts (MEDIUM PRIORITY)
3. **Route efficiency spread** - Only 9% variance, could be increased (LOW PRIORITY)

---

## Task 1: Speed Rating Conversion Analysis

### Fielder Sprint Speed

**Mapping:** `get_top_sprint_speed_fps()` in `attributes.py:429-452`

| Rating | Speed (ft/s) | Speed (mph) | 90ft Time | % vs Avg (50k) |
|--------|-------------|-------------|-----------|----------------|
| 0k     | 24.0        | 16.4        | 3.75s     | -11.1%         |
| 50k    | 27.0        | 18.4        | 3.33s     | baseline       |
| 85k    | 30.0        | 20.5        | 3.00s     | +11.1%         |
| 100k   | 32.0        | 21.8        | 2.81s     | +18.5%         |

**MLB Benchmarks (Statcast):**
- Average: ~27 ft/s ✓
- Elite outfielders: ~30 ft/s ✓
- Fastest: ~31 ft/s ✓

**Assessment:** ✅ **EXCELLENT**
- Values match MLB Statcast data exactly
- 11% increase from avg→elite creates observable difference (0.33s faster on 90ft run)
- Comment on line 440 confirms Statcast calibration
- Previous values (37.0 ft/s elite) were superhuman, now corrected

### Runner Sprint Speed

**Mapping:** `get_sprint_speed_fps()` in `baserunning.py:164-179`

| Rating | Speed (ft/s) | Home-to-First Time | % vs Avg (50k) |
|--------|--------------|-------------------|----------------|
| 0k     | 22.0         | ~5.5s             | -18.5%         |
| 50k    | 27.0         | ~4.3s             | baseline       |
| 85k    | 30.0         | ~3.8s             | +11.1%         |
| 100k   | 32.0         | ~3.6s             | +18.5%         |

**MLB Benchmarks:**
- Elite: ~3.7s ✓
- Average: ~4.3s ✓
- Slow: ~5.2s ✓

**Assessment:** ✅ **EXCELLENT**
- Same mapping as fielders (consistent)
- Produces realistic home-to-first times
- Good spread across rating ranges

---

## Task 2: Reaction Time and Route Efficiency Analysis

### Fielder Reaction Time

**Mapping:** `get_reaction_time_s()` in `attributes.py:388-406` (INVERSE)

| Rating | Reaction Time | % vs Avg (50k) | Improvement |
|--------|--------------|----------------|-------------|
| 0k     | 0.30s        | +200%          | -           |
| 50k    | 0.10s        | baseline       | baseline    |
| 85k    | 0.05s        | -50%           | 0.05s faster|
| 100k   | 0.00s        | -100%          | 0.10s faster|

**Code Comment (line 399):**
> "Previous values (0.23s average) were too slow, causing fielders to react 0.13s late on every play, contributing to excessive hits."

**Assessment:** ✅ **EXCELLENT**
- 50% reduction from avg→elite (huge improvement)
- Recently tuned from 0.23s to 0.10s avg
- Creates observable difference in play execution

### Route Efficiency

**Mapping:** `get_route_efficiency_pct()` in `attributes.py:454-471`

| Rating | Efficiency | 100ft Actual Distance | % vs Avg (50k) |
|--------|-----------|----------------------|----------------|
| 0k     | 0.70      | 142.9ft              | -20.5%         |
| 50k    | 0.88      | 113.6ft              | baseline       |
| 85k    | 0.96      | 104.2ft              | +9.1%          |
| 100k   | 0.99      | 101.0ft              | +12.5%         |

**MLB Target Range:** 85-95% (per CLAUDE.md)

**Assessment:** ⚠️ **MODERATE**
- Values match MLB target range (85-95% ✓)
- Only 9% spread from avg→elite (lower than other attributes)
- Multiplied with speed/reaction for compound effect
- **Recommendation:** Could increase to 12-15% spread if fielders feel too similar in gameplay

---

## Task 3: Arm Strength and Throw Velocity Analysis

### Arm Strength

**Mapping:** `get_arm_strength_mph()` in `attributes.py:493-512`

| Rating | Throw Velocity | Home-to-2nd Time | % vs Avg (50k) |
|--------|---------------|------------------|----------------|
| 0k     | 60 mph        | 1.93s            | -20.0%         |
| 50k    | 75 mph        | 1.55s            | baseline       |
| 85k    | 88 mph        | 1.32s            | +17.3%         |
| 100k   | 100 mph       | 1.16s            | +33.3%         |

**Code Comment (line 499):**
> "DECREASED from 82 mph for realistic game-speed throws. Game-speed infield throws are rarely max effort. Most routine plays use 75-80 mph."

**Assessment:** ✅ **EXCELLENT**
- Recently tuned from 82 mph → 75 mph avg (more realistic)
- 17% increase avg→elite creates 0.23s advantage on 127ft throw
- Elite values (88 mph) match top MLB infielders
- Accounts for game-speed vs max effort difference

### Transfer Time

**Mapping:** `get_transfer_time_s()` in `attributes.py:473-491` (INVERSE)

| Rating | Transfer Time | % vs Avg (50k) | Improvement |
|--------|--------------|----------------|-------------|
| 0k     | 1.20s        | +60%           | -           |
| 50k    | 0.75s        | baseline       | baseline    |
| 85k    | 0.50s        | -33.3%         | 0.25s faster|
| 100k   | 0.30s        | -60.0%         | 0.45s faster|

**Code Comment (line 479):**
> "INCREASED from 0.45s to slow down unrealistic double plays. Real-world double play pivot and release takes significant time."

**Assessment:** ✅ **EXCELLENT**
- 33% reduction avg→elite (strong variance)
- Recently tuned from 0.45s avg to 0.75s (more realistic)
- Fixed double play timing issues

---

## Task 4: Baserunning Aggression and Jump Logic Analysis

### Current Implementation

**File:** `baserunning.py`

**Attributes:**
- `sprint_speed` (0-100k) → physical speed
- `acceleration` (0-100k) → burst acceleration
- `base_running_iq` (0-100k) → **MULTIPLE CONCEPTS**
  - Reaction time (line 198-214)
  - Leadoff distance (line 233-262)
  - Decision making (implied)
- `sliding_ability` (0-100k) → slide mechanics
- `turn_efficiency` (0-100k) → speed retention in turns

### The Problem: Attribute Consolidation

**base_running_iq currently handles:**

1. **Reaction Time** (`get_reaction_time_seconds()`)
   - 0k → 0.40s (slow)
   - 50k → 0.18s (average)
   - 85k → 0.08s (elite)

2. **Leadoff Distance** (`get_optimal_leadoff()`)
   - First base: 9-13.5 ft
   - Second base: 12-18 ft
   - Third base: 9-15 ft

3. **Decision Making** (implicit in various functions)

**Missing Attributes:**
- ❌ No explicit `JUMP` attribute (stolen base jump timing)
- ❌ No explicit `STEAL_IQ` attribute
- ❌ No explicit `AGGRESSION` attribute (risk-taking)

### Impact

**Cannot create player archetypes like:**
- Fast runner with poor jumps (high speed, low JUMP)
- Slow runner with great instincts (low speed, high STEAL_IQ)
- Conservative speedster (high speed, low AGGRESSION)
- Aggressive grinder (low speed, high AGGRESSION)

**In real MLB scouting:**
- Speed rating (20-80 scale)
- Baserunning instincts (20-80 scale) ← SEPARATE TOOL
- Stolen base ability (20-80 scale) ← SEPARATE TOOL

### Recommendation

**Split base_running_iq into 3 separate attributes:**

```python
class BaseRunner:
    def __init__(
        self,
        name: str,
        sprint_speed: int = 50000,       # EXISTING
        acceleration: int = 50000,       # EXISTING
        reaction_time: int = 50000,      # NEW - first move speed
        base_aggression: int = 50000,    # NEW - leadoff distance, risk-taking
        jump_ability: int = 50000,       # NEW - stolen base jump timing
        sliding_ability: int = 50000,    # EXISTING
        turn_efficiency: int = 50000,    # EXISTING
    ):
```

**Benefits:**
- More realistic player archetypes
- Better stolen base modeling (separate jump from speed)
- Aligns with MLB scouting (separate tools)
- More tuning levers for gameplay balance

**Effort:** 2-3 hours (refactor + test)

---

## Task 5: Mapping Curve Evaluation

### Curve Shape Analysis

All attributes use **piecewise logistic mapping** functions:

```python
def piecewise_logistic_map(
    rating: float,
    human_min: float,
    human_cap: float,
    super_cap: float,
    H: float = 85000.0,  # Human capability threshold
    k: float = 8.0,      # Steepness for human range
    k2: float = 5.0      # Steepness for superhuman range
)
```

**Characteristics:**
- **0k-85k:** Smooth logistic spread across normal human range
- **85k-100k:** Gentler scaling for superhuman headroom
- **No hard tiers:** Continuous function prevents cliff effects

### Linearity Assessment

| Attribute | Curve Type | Steepness | Assessment |
|-----------|-----------|-----------|------------|
| Sprint Speed | Logistic | Moderate | ✓ Good spread |
| Reaction Time | Inverse Logistic | Steep | ✓ Strong differentiation |
| Arm Strength | Logistic | Moderate | ✓ Good spread |
| Bat Speed | Logistic | Moderate | ✓ Good spread |
| Route Efficiency | Logistic | Gentle | ⚠ Could be steeper |

**Overall Assessment:** ✅ **GOOD**
- Avoids overly flat mid-tier (40-70k range)
- Steepness parameter (k=8.0) provides good differentiation
- Superhuman range (85k-100k) exists for future expansion
- No discontinuities or tier problems

### Variance Summary

| Attribute | 50k Value | 85k Value | Spread % | Target | Status |
|-----------|-----------|-----------|----------|--------|--------|
| Sprint Speed | 27.0 ft/s | 30.0 ft/s | +11.1% | 10-15% | ✅ GOOD |
| Reaction Time | 0.10s | 0.05s | -50.0% | 15%+ | ✅ EXCELLENT |
| Route Efficiency | 0.88 | 0.96 | +9.1% | 10-15% | ⚠ MODERATE |
| Arm Strength | 75 mph | 88 mph | +17.3% | 15%+ | ✅ EXCELLENT |
| Transfer Time | 0.75s | 0.50s | -33.3% | 15%+ | ✅ EXCELLENT |
| Acceleration | 60 ft/s² | 80 ft/s² | +33.3% | 15%+ | ✅ EXCELLENT |
| Bat Speed | 75 mph | 85 mph | +13.3% | 10-15% | ✅ GOOD |
| Barrel Accuracy | 10mm | 5mm | -50.0% | 15%+ | ✅ EXCELLENT |

**Target:** Minimum 10% difference between avg (50k) and elite (85k) for observable gameplay variance

**Results:** 7/8 attributes meet or exceed target ✅

---

## Critical Issue: Constants.py Mismatch

### The Problem

**File:** `batted_ball/constants.py`

The constants file contains **OUTDATED** physical constants that don't match the values actually used by the attribute system.

### Specific Mismatches

**Sprint Speed Constants:**

```python
# In constants.py (WRONG - lines 575-578)
FIELDER_SPRINT_SPEED_MIN = 30.0    # ft/s
FIELDER_SPRINT_SPEED_AVG = 35.0    # ft/s (~23.9 mph)
FIELDER_SPRINT_SPEED_ELITE = 40.0  # ft/s (~27.3 mph)
FIELDER_SPRINT_SPEED_MAX = 42.0    # ft/s (~28.6 mph)

# Actual values from attributes.py mappings (CORRECT)
0k   → 24.0 ft/s
50k  → 27.0 ft/s (MLB average)
85k  → 30.0 ft/s (elite)
100k → 32.0 ft/s (max)
```

**Statcast Calibrated Constants:**

```python
# In constants.py (also inconsistent - lines 644-647)
FIELDER_SPRINT_SPEED_STATCAST_MIN = 26.5    # ft/s
FIELDER_SPRINT_SPEED_STATCAST_AVG = 28.5    # ft/s
FIELDER_SPRINT_SPEED_STATCAST_ELITE = 30.0  # ft/s
FIELDER_SPRINT_SPEED_STATCAST_MAX = 31.0    # ft/s

# These are closer but still don't exactly match attributes.py
```

### Impact

1. **Developer Confusion:** Reading constants.py suggests avg fielder runs 35 ft/s, but actual mapping uses 27 ft/s
2. **Potential Bugs:** If any code directly uses these constants instead of attribute mappings
3. **Code Inconsistency:** Two sources of truth for the same physical values
4. **Documentation Mismatch:** Comments cite Statcast but values don't match

### Root Cause

The attribute system was recently recalibrated (comments show "Previous values (37.0 ft/s elite) were superhuman"), but constants.py was not updated to match.

### The Fix

**File:** `batted_ball/constants.py`

**Lines to update:** 575-578, 644-647

```python
# BEFORE (WRONG):
FIELDER_SPRINT_SPEED_MIN = 30.0    # ft/s (~20.5 mph) - slowest MLB players
FIELDER_SPRINT_SPEED_AVG = 35.0    # ft/s (~23.9 mph) - MLB average
FIELDER_SPRINT_SPEED_ELITE = 40.0  # ft/s (~27.3 mph) - elite sprinters
FIELDER_SPRINT_SPEED_MAX = 42.0    # ft/s (~28.6 mph) - absolute fastest

# AFTER (CORRECT - matches attributes.py):
FIELDER_SPRINT_SPEED_MIN = 24.0    # ft/s (~16.4 mph) - 0k rating
FIELDER_SPRINT_SPEED_AVG = 27.0    # ft/s (~18.4 mph) - 50k rating (MLB Statcast avg)
FIELDER_SPRINT_SPEED_ELITE = 30.0  # ft/s (~20.5 mph) - 85k rating (elite)
FIELDER_SPRINT_SPEED_MAX = 32.0    # ft/s (~21.8 mph) - 100k rating (fastest)
```

```python
# BEFORE (INCONSISTENT):
FIELDER_SPRINT_SPEED_STATCAST_MIN = 26.5    # ft/s - Slow 1B archetype
FIELDER_SPRINT_SPEED_STATCAST_AVG = 28.5    # ft/s - Average MLB SS
FIELDER_SPRINT_SPEED_STATCAST_ELITE = 30.0  # ft/s - Elite Gold Glove CF
FIELDER_SPRINT_SPEED_STATCAST_MAX = 31.0    # ft/s - Absolute fastest

# AFTER (REMOVE - redundant with corrected values above):
# Delete lines 644-647 or consolidate into single set of constants
```

### Verification

After fix, verify in code:
- Search for `FIELDER_SPRINT_SPEED_AVG` usage
- Ensure no code relies on old 35.0 ft/s value
- Update any related constants (acceleration, etc.) if needed

---

## Summary of Recommendations

### HIGH PRIORITY

**1. Fix Constants.py Mismatch**
- **File:** `batted_ball/constants.py`
- **Lines:** 575-578, 644-647
- **Action:** Update sprint speed constants to match attributes.py
- **Effort:** 5 minutes
- **Impact:** HIGH (code consistency, prevents bugs)
- **Details:** See "Critical Issue" section above

### MEDIUM PRIORITY

**2. Split Baserunning Attributes**
- **File:** `batted_ball/baserunning.py`
- **Action:** Split `base_running_iq` into:
  - `REACTION_TIME` (first-move speed)
  - `BASE_AGGRESSION` (leadoff distance, risk-taking)
  - `JUMP_ABILITY` (stolen base jump timing)
- **Effort:** 2-3 hours (refactor + test)
- **Impact:** MEDIUM (better player archetypes, more realistic stolen bases)
- **Details:** See "Task 4" section above

### LOW PRIORITY

**3. Consider Route Efficiency Boost**
- **File:** `batted_ball/attributes.py`
- **Lines:** 466-471
- **Action:** Monitor if fielders feel too similar; if so, increase spread:
  - Current: 0k→0.70, 50k→0.88, 85k→0.96 (9% spread)
  - Option: 0k→0.65, 50k→0.85, 85k→0.96 (13% spread)
- **Effort:** 10 minutes to test
- **Impact:** LOW (only if problem observed in gameplay)

---

## Conclusion

The attribute mapping system is **well-designed and well-calibrated** with most attributes showing appropriate variance. The piecewise logistic mapping approach avoids tier problems and creates smooth, continuous performance curves.

The two main issues identified—constants.py mismatch and baserunning attribute consolidation—are fixable with minimal effort and would improve code consistency and gameplay realism.

**Overall Grade: A-**

**Strengths:**
- ✅ MLB Statcast calibration
- ✅ Continuous mapping functions
- ✅ Strong variance across rating ranges
- ✅ Recent tuning shows active maintenance

**Areas for Improvement:**
- ⚠️ Constants.py synchronization
- ⚠️ Baserunning attribute granularity

---

**End of Report**
