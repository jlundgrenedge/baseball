# Zone Rate Analysis - Command System Investigation

**Date**: 2025-11-20
**Problem**: Zone rate 32.3% (should be 62-65%)
**Status**: Root cause identified, fix designed

---

## The Command System Architecture

### 1. Pitch Intention System

Pitchers choose intentions based on count (`_determine_pitch_intention()` in `at_bat.py` line 406):

| Intention | Description | Example Target | Intended Zone? |
|-----------|-------------|---------------|---------------|
| `strike_looking` | Easy strike, middle of zone | (0", 30") ± 2-3" | ✅ Yes |
| `strike_competitive` | Strike on edges | (±6", 20-40") | ✅ Yes |
| `strike_corner` | Corner of zone | (±7", 20 or 40") | ✅ Yes |
| `waste_chase` | Outside zone for chase | (±10-15", 10-16" or 44-50") | ❌ No |
| `ball_intentional` | Intentionally throw ball | (±12-18", 8-15") | ❌ No |

**Intent Distribution** (0-0 count example):
- Strike intentions: ~90% (strike_looking 60%, strike_competitive 20%, strike_corner 10%)
- Ball intentions: ~10% (ball_intentional 10%)

### 2. Target Location Selection

Based on intention, specific targets chosen (`select_target_location()` line 318):

**Strike_looking** (60% of pitches):
```python
horizontal_target = np.random.normal(0, 2.0)    # Center ±2"
vertical_target = np.random.normal(30.0, 3.0)   # Middle ±3"
```
Target zone hit rate with NO command error: ~99%

**Strike_competitive** (20% of pitches):
```python
horizontal_target = ±6.0 ± 1.5"  # Edges
vertical_target = uniform(20-40")  # Anywhere in zone
```
Target zone hit rate with NO command error: ~90%

**Strike_corner** (10% of pitches):
```python
horizontal_target = ±7.0 ± 1.0"  # Near edge
vertical_target = 20 or 40 ± 1.0"  # Top or bottom
```
Target zone hit rate with NO command error: ~75%

**Weighted average of INTENDED strikes**: 0.60×99% + 0.20×90% + 0.10×75% + 0.10×0% = 77%

But with command error, actual zone rate is only 32.3%!

### 3. Command Error System

After target is chosen, command error is added (`get_command_error_inches()` in `player.py` line 179):

```python
command_sigma = self.attributes.get_command_sigma_inches()  # From COMMAND attribute

# Apply fatigue (up to 1.4× multiplier)
effective_sigma = command_sigma * fatigue_multiplier

# Random error in both directions
horizontal_error = np.random.normal(0, effective_sigma)
vertical_error = np.random.normal(0, effective_sigma)

actual_h = target_h + horizontal_error
actual_v = target_v + vertical_error
```

**Current sigma values** (from `attributes.py` line 915):
```python
piecewise_logistic_map_inverse(
    self.COMMAND,
    human_min=4.5,   # Elite command (85k rating)
    human_cap=10.0,  # Poor command (0 rating)
    super_cap=2.5    # Pinpoint (100k rating)
)
```

Average pitcher (50k rating): **~6.5" sigma**

---

## The Problem: Command Sigma Too Large

### Strike Zone Dimensions
- Width: ±8.5" (17" total)
- Height: 18"-42" (24" tall, center at 30")

### Miss Probability with Current Sigma (6.5")

**Scenario 1: Targeting Center** (60% of strike intentions)
- Target: (0", 30")
- Horizontal miss rate: P(|error| > 8.5") = P(|Z| > 1.31σ) = 19%
- Vertical miss rate: P(|error| > 12") = P(|Z| > 1.85σ) = 6%
- **Combined hit rate**: (1 - 0.19) × (1 - 0.06) = **76%**

**Scenario 2: Targeting Edge** (20% of strike intentions)
- Target: (6", 30")  - only 2.5" from horizontal edge
- Horizontal miss rate: P(error > 2.5" OR error < -14.5") = P(Z > 0.38σ OR Z < -2.23σ) ≈ 35%
- Vertical miss rate: 6% (same as center)
- **Combined hit rate**: (1 - 0.35) × (1 - 0.06) = **61%**

**Scenario 3: Targeting Corner** (10% of strike intentions)
- Target: (7", 20")  - 1.5" from horizontal edge, 2" from vertical edge
- Horizontal miss rate: ~40%
- Vertical miss rate: ~25%
- **Combined hit rate**: (1 - 0.40) × (1 - 0.25) = **45%**

**Scenario 4: Waste Pitch** (10% of all pitches)
- Target: Outside zone
- **Hit rate**: ~5% (mistake into zone)

**Overall expected zone rate**:
```
0.60 × 76% = 45.6%  (strike_looking)
0.20 × 61% = 12.2%  (strike_competitive)
0.10 × 45% =  4.5%  (strike_corner)
0.10 ×  5% =  0.5%  (waste/ball)
----------------------------
Total:        62.8%  ← This should be our zone rate!
```

**But we're getting 32.3%**. What's wrong?

---

## Additional Factors Reducing Zone Rate

### 1. Pitch Intention Distribution

Looking at the diagnostic output:
```
strike_looking      : 620 (27.9%) → Zone rate: 65.2%
strike_competitive  : 489 (22.0%) → Zone rate: 47.6%
strike_corner       : 163 ( 7.3%) → Zone rate: 33.1%
waste_chase         :  77 ( 3.5%) → Zone rate: 13.0%
ball_intentional    : 122 ( 5.5%) → Zone rate: 14.8%
```

Total logged: 1471 pitches (66% of 2223 total)

**Weighted zone rate from intentions**:
```
0.279 × 65.2% = 18.2%
0.220 × 47.6% = 10.5%
0.073 × 33.1% =  2.4%
0.035 × 13.0% =  0.5%
0.055 × 14.8% =  0.8%
--------------------------
Total (logged): 32.4% ✓ Matches observed 32.3%!
```

So the actual intention-by-intention zone rates match expectations with current sigma!

### 2. The Real Issue

**Strike_looking should hit 76% of the time** (targeting center with 6.5" sigma), **but only hitting 65.2%**.

**Strike_competitive should hit 61% of the time** (targeting edges with 6.5" sigma), **but only hitting 47.6%**.

**This means effective sigma is LARGER than 6.5"!**

Possible reasons:
1. **Fatigue multiplier**: Fresh pitchers have 1.0×, but tired pitchers have up to 1.4×
   - Average multiplier across game might be 1.1-1.2×
   - Effective sigma: 6.5" × 1.15 = 7.5"

2. **Pitch type variance**: Different pitch types may have additional error

3. **Physics simulation error**: The physics sim might add additional location variance

Let me recalculate with effective sigma = 7.5":

**Targeting center with 7.5" sigma**:
- Horizontal miss: P(|error| > 8.5") = P(|Z| > 1.13σ) = 26%
- Vertical miss: P(|error| > 12") = P(|Z| > 1.6σ) = 11%
- **Hit rate**: 0.74 × 0.89 = **66%** ✓ Matches 65.2%!

**Targeting edges (6", 30") with 7.5" sigma**:
- Horizontal miss: P(error > 2.5" OR error < -14.5") ≈ 42%
- Vertical miss: 11%
- **Hit rate**: 0.58 × 0.89 = **52%** ✓ Close to 47.6%!

**So effective sigma is ~7.5" (not 6.5")**

---

## The Fix: Reduce Command Sigma

To achieve 62-65% zone rate, we need **effective sigma ~4.0"** (accounting for fatigue).

### Backwards Calculation

Target zone rates WITH 4.0" effective sigma:

**Targeting center (4.0" sigma)**:
- Horizontal miss: P(|error| > 8.5") = P(|Z| > 2.13σ) = 3.3%
- Vertical miss: P(|error| > 12") = P(|Z| > 3.0σ) = 0.3%
- **Hit rate**: **96.4%** ✓

**Targeting edges (6", 30") with 4.0" sigma**:
- Horizontal: only 2.5" margin, P(miss) = 27%
- Vertical: 0.3%
- **Hit rate**: **72.8%** ✓

**Targeting corners (7", 20") with 4.0" sigma**:
- Horizontal: only 1.5" margin, P(miss) = 35%
- Vertical: only 2" margin, P(miss) = 31%
- **Hit rate**: **44.9%** ✓

**Expected overall zone rate**:
```
0.60 × 96.4% = 57.8%  (strike_looking)
0.20 × 72.8% = 14.6%  (strike_competitive)
0.10 × 44.9% =  4.5%  (strike_corner)
0.10 ×  5.0% =  0.5%  (waste/ball)
----------------------------
Total:         77.4%  ← TOO HIGH!
```

Hmm, that's too high. Let me try sigma = 5.0":

**Expected overall zone rate with 5.0" effective sigma**:
```
Targeting center: 88.5% hit
Targeting edges: 63.4% hit
Targeting corners: 35.8% hit

0.60 × 88.5% = 53.1%
0.20 × 63.4% = 12.7%
0.10 × 35.8% =  3.6%
0.10 ×  5.0% =  0.5%
----------------------------
Total:         69.9%  ← Still a bit high
```

Let me try sigma = 5.5":

**Expected overall zone rate with 5.5" effective sigma**:
```
Targeting center: 83.9% hit
Targeting edges: 57.2% hit
Targeting corners: 32.6% hit

0.60 × 83.9% = 50.3%
0.20 × 57.2% = 11.4%
0.10 × 32.6% =  3.3%
0.10 ×  5.0% =  0.5%
----------------------------
Total:         65.5%  ← PERFECT! Target is 62-65%
```

---

## Optimal Command Sigma Values

**Target effective sigma**: 5.5" (with fatigue average)
**Target base sigma**: 5.5" / 1.15 (avg fatigue) = **4.8"** for average pitcher

**New command sigma range**:
- **Elite (85k)**: 3.0" base (was 4.5") → 3.5" effective → 75% zone rate
- **Average (50k)**: 4.8" base (was 6.5") → 5.5" effective → 65% zone rate
- **Poor (20k)**: 7.0" base (was 8.5") → 8.0" effective → 50% zone rate
- **Superhuman (100k)**: 2.0" base (was 2.5") → 2.3" effective → 85% zone rate

**Reduction factor**: ~25-30% across the board

---

## Implementation

**File**: `batted_ball/attributes.py` line 915

**Change**:
```python
# OLD:
return piecewise_logistic_map_inverse(
    self.COMMAND,
    human_min=4.5,     # Elite command (85k)
    human_cap=10.0,    # Poor command (0)
    super_cap=2.5      # Pinpoint (100k)
)

# NEW:
return piecewise_logistic_map_inverse(
    self.COMMAND,
    human_min=3.0,     # Elite command (85k) - reduced from 4.5
    human_cap=7.0,     # Poor command (0) - reduced from 10.0
    super_cap=2.0      # Pinpoint (100k) - reduced from 2.5
)
```

**Expected impact**:
- Zone rate: 32.3% → 62-65% ✅
- BB%: 10% → 8-9% ✅
- K%: 9% → 18-20% (from more 2-strike counts) ✅
- Chase rate: Should increase (more out-of-zone pitches thrown with purpose)
- Whiff rates: Stay the same (already fixed)

---

## User's Point: Mistakes Can Help

The user correctly noted: "Sometimes a pitcher is trying to hit the corner and instead throws it right down the middle."

**This is already modeled!** When targeting corners (±7", 20 or 40") with command error:
- Sometimes error is negative (toward center)
- Pitcher aims corner, misses toward middle
- These "mistakes" still land in the zone (actually increase zone %)

**Example**: Aim for (7", 20"), get error of (-3", +2"):
- Actual location: (4", 22")
- Still in zone! (Wanted corner, got edge-middle)
- Easier for batter to hit (location difficulty lower)

So the bidirectional nature of error is already correct. We just need less total error magnitude.

---

## Validation Plan

After implementing the fix, run 50-game diagnostic:

**Success criteria**:
- Zone rate: 60-67% (target: 62-65%)
- BB%: 7-10% (target: 8-9%)
- K%: 18-23% (target: 22%)
- Chase rate: 18-25% (should improve with better pitching)
- Whiff rates: Maintain 28-34% (already good)
- Breaking ball contact: Maintain (curveball 74%, changeup 73%, slider 63%)

---

**Analysis Complete**: 2025-11-20
**Root Cause**: Command sigma too large (effective ~7.5", should be ~5.5")
**Fix**: Reduce command sigma range by ~30%
**Expected Result**: Zone rate 32.3% → 65%, K% 9% → 20%
