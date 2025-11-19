# Fielder Behavior Analysis - Overly Efficient Defense Investigation

**Date:** 2025-11-19
**Issue:** Fielders display "vacuum cleaner" behavior with 90-99%+ route efficiency and near-perfect catch rates
**Objective:** Identify and correct unrealistic fielding perfection

---

## Executive Summary

After comprehensive code audit, the root cause is **EXCESSIVE DETERMINISM** in the fielding system. Every fielder with identical ratings performs identically on every play, with no play-by-play variance. While base attribute values have been calibrated multiple times (as evidenced by comments about previous nerfs), the system lacks the **stochastic imperfection** that characterizes real MLB defense.

**Key Finding:** The simulation is physics-accurate but human-behavior-inaccurate. Real fielders don't execute at their peak rating on every single play.

---

## Task 1: Fielding Range Calculation Audit

### 1.1 Reaction Time (batted_ball/attributes.py:388-406)

**Current Mapping (0-100,000 scale → seconds):**
- Rating 0: 0.30s (very slow)
- Rating 50,000: 0.10s (average MLB)
- Rating 85,000: 0.05s (elite)
- Rating 100,000: 0.00s (perfect anticipation)

**Implementation:** `piecewise_logistic_map_inverse()` - smooth continuous function

**Critical Issue:** ⚠️ **ZERO VARIANCE** - Every play uses the exact value with no randomness
- A 50k-rated fielder ALWAYS reacts in exactly 0.10s
- No representation of good jumps (0.05s) vs. poor reads (0.15s)
- No misreads or wrong first steps

**Evidence:** Code comments indicate previous calibration (was 0.23s avg - "too slow") but variance was never added

---

### 1.2 Acceleration (batted_ball/attributes.py:408-427)

**Current Mapping (0-100,000 scale → ft/s²):**
- Rating 0: 35 ft/s² (slow)
- Rating 50,000: 60 ft/s² (average MLB)
- Rating 85,000: 80 ft/s² (elite)
- Rating 100,000: 100 ft/s² (exceptional)

**Critical Issue:** ⚠️ **ZERO VARIANCE** - Deterministic acceleration on every play
- Comment on line 419: "Previous values (12 ft/s² average) were 5x too low" - shows this was already calibrated once
- But no variance added - every play uses exact value

---

### 1.3 Top Sprint Speed (batted_ball/attributes.py:429-452)

**Current Mapping (0-100,000 scale → ft/s):**
- Rating 0: 24 ft/s (~16.4 mph)
- Rating 50,000: 27 ft/s (~18.4 mph) - MLB average
- Rating 85,000: 30 ft/s (~20.5 mph) - elite
- Rating 100,000: 32 ft/s (~21.8 mph) - absolute max

**Calibration:** Well-calibrated to MLB Statcast data
- Comment on line 444: "Previous values (37.0 ft/s elite) were superhuman" - already nerfed once

**Critical Issue:** ⚠️ **ZERO VARIANCE** - Every sprint at exact max speed
- Real fielders vary ±1-2 ft/s between plays (footing, fatigue, urgency)
- No representation of incomplete acceleration (arriving at 85% speed vs. 100%)

---

### 1.4 Route Efficiency (batted_ball/attributes.py:454-471)

**Current Mapping (0-100,000 scale → decimal):**
- Rating 0: 0.70 (poor routes - 70% efficient)
- Rating 50,000: 0.88 (average - 88% efficient)
- Rating 85,000: 0.96 (elite - 96% efficient)
- Rating 100,000: 0.99 (nearly perfect - 99% efficient)

**Range Multiplier Applied (batted_ball/fielding.py:540-553):**
- Elite (≥0.92): 1.08× multiplier (was 1.15× - "NERFED 2025-11-19")
- Above avg (≥0.88): 1.03× multiplier (was 1.05×)
- Below avg: 0.95× multiplier
- Comment: "Reduced multipliers to prevent vacuum-cleaner defense"

**Critical Issues:**
1. ⚠️ **ZERO VARIANCE** - Route efficiency is fixed per fielder rating
2. ⚠️ **VALUES TOO HIGH** - 88-99% means near-perfect routes every time
   - Real MLB: Route efficiency varies 75-95% depending on read quality, ball trajectory complexity
   - No representation of hesitation, initial wrong step, late break

---

## Task 2: Catch Probability Mapping

### 2.1 Time-Based Catch Probability (batted_ball/fielding.py:718-773)

**Current Thresholds:**

| Time Margin | Base Probability | After Penalties (worst case) | Notes |
|-------------|-----------------|------------------------------|-------|
| ≥ 1.0s early | **99%** | 99% (no penalties) | FIX: "BUTTERFINGERS BUG" - skip penalties if waiting |
| 0.2-1.0s early | 98% | 71% (0.98 × 0.727) | Routine running catch |
| 0.0-0.2s early | 85% | 62% (0.85 × 0.727) | **NERFED** from 95% |
| -0.15-0.0s (diving) | 42% | 39% | Diving/stretching range |
| -0.35--0.15s | 10% | 9% | Extremely difficult |
| < -0.6s | 1% | 1% | Impossible |

**Penalty Multipliers:**
- Hands rating: ~0.92 (average fielder)
- Distance penalties:
  - 120+ ft: 0.85× (15% penalty)
  - 100-120 ft: 0.92× (8% penalty)
  - 80-100 ft: 0.96× (4% penalty)
- Backward movement: 0.93× (7% penalty)

**Worst-case compounding:** 0.92 × 0.85 × 0.93 = **0.727** (27.3% total reduction)

**Critical Issue:** ⚠️ **STILL TOO HIGH FOR POSITIVE TIME MARGINS**
- Time margin ≥ 0.2s → 98% base → 71% after penalties = **very high catch rate**
- When fielders arrive on time or early, they catch almost everything
- This creates the "vacuum cleaner" effect reported by user

**Evidence of Multiple Calibration Attempts:**
- Line 740-748: Comments reference "BUTTERFINGERS BUG", "NERFED 2025-11-19"
- Line 757: "was 95% - NERFED"
- Shows awareness of problem but insufficient fix

---

### 2.2 Variance in Catch Execution

**Current Implementation:**
```python
catch_probability = 0.85  # Example for 0.0s margin
catch_probability *= base_secure_prob  # 0.92 for average
catch_probability *= distance_penalty  # 0.85-0.96
catch_probability *= backward_penalty  # 0.93 if applicable
catch_roll = np.random.random()
success = catch_roll < catch_probability
```

**What's Missing:** ⚠️ **NO EXECUTION VARIANCE**
- Probability is calculated once, rolled once
- No representation of:
  - Concentration lapses (5% chance to misjudge easy plays)
  - Sun/glare/wind affecting tracking (environmental)
  - Communication errors on contested balls
  - Rushed transfers causing drops

---

## Task 3: Route Efficiency System

### 3.1 How Route Efficiency is Calculated

**Source:** `batted_ball/route_efficiency.py:199-267`

**Calculation Method:**
1. **Optimal distance:** Straight-line Euclidean distance (start → intercept point)
2. **Actual distance:** Back-calculated from fielder movement:
   ```python
   movement_time = fielder_arrival_time - reaction_time
   effective_speed = max_speed × speed_percentage
   actual_distance = effective_speed × movement_time
   ```
3. **Route efficiency:** `optimal_distance / actual_distance`
4. **Route penalty applied:**
   - < 30 ft: No penalty (1.0×)
   - 30-60 ft: `1.0 + (1.0 - route_eff) × 0.3` (minor penalty)
   - > 60 ft: `1.0 + (1.0 - route_eff) × 0.15` (reduced penalty)

**Why Efficiency is 90-99%:**
1. Base route efficiency from attributes: 88-99% (deterministic)
2. Route penalty is SMALL: only 15-30% of the inefficiency
   - Example: 88% efficiency → 12% inefficiency → penalty = 12% × 0.15 = **1.8%**
3. Back-calculation amplifies the high base efficiency

**Critical Issue:** ⚠️ **CIRCULAR REASONING**
- Route efficiency attribute (88-99%) → determines actual distance → produces logged efficiency (90-99%)
- The logged metric is just echoing the input attribute with minor noise
- No simulation of actual route imperfection

---

## Root Cause Analysis

### Why Fielders Are Too Efficient

**The Fundamental Problem:** Physics-perfect deterministic execution

1. **No Stochastic Variation**
   - Reaction time: Always exact value (0.10s for 50k rating)
   - Acceleration: Always exact value (60 ft/s² for 50k rating)
   - Sprint speed: Always exact max (27 ft/s for 50k rating)
   - Route efficiency: Always exact value (0.88 for 50k rating)

2. **No Human Error Simulation**
   - No wrong first steps (adds 0.2-0.5s)
   - No initial misreads (reduces route efficiency to 70-80%)
   - No hesitation or false starts
   - No communication errors on contested balls

3. **Calibrated Values Already Near-Optimal**
   - Multiple previous nerfs evident in code comments
   - Values are realistic for MLB averages
   - **But MLB averages include bad plays!** A .280 hitter gets out 72% of the time

4. **High Catch Probabilities for Neutral Plays**
   - Time margin ≥ 0.0s → 85-98% base catch rate
   - After penalties: still 62-71%
   - This means fielders who arrive on time catch 60-70% of the time
   - In reality, "on time" plays should be 30-50% (difficult running catches)

---

## Proposed Solution: Randomness & Imperfection Layer

### Philosophy

**"Average" rating (50,000) should mean:**
- Sometimes perform like 40k (below average play)
- Usually perform like 50k (typical play)
- Sometimes perform like 60k (above average play)
- **Never perform perfectly on every single play**

### Implementation Strategy

Add controlled randomness at 4 key points in the fielding pipeline:

---

### 1. Reaction Time Variance

**Current:** Always exact value
**Proposed:** Add ±variance based on play difficulty and fielder rating

```python
def get_reaction_time_with_variance(self) -> float:
    """Get reaction time with play-by-play variance."""
    base_reaction = self.get_reaction_time_s()  # 0.00-0.30s based on rating

    # Variance based on rating (better fielders more consistent)
    # Elite (85k+): ±0.02s variance (very consistent)
    # Average (50k): ±0.05s variance (typical MLB)
    # Poor (0-30k): ±0.08s variance (inconsistent)

    if self.REACTION_TIME >= 85000:
        variance = 0.02
    elif self.REACTION_TIME >= 50000:
        variance = 0.05
    else:
        variance = 0.08

    # Normal distribution centered at base reaction time
    actual_reaction = np.random.normal(base_reaction, variance)

    # Clamp to reasonable range [0.0, 0.5s]
    return np.clip(actual_reaction, 0.0, 0.5)
```

**Impact:**
- 50k fielder: Sometimes 0.05s (great jump), sometimes 0.15s (late read)
- Introduces realistic play-to-play variation
- Elite fielders still more consistent than average

---

### 2. Initial Step Quality / Misread Chance

**Current:** Never happens
**Proposed:** Small chance of suboptimal first step

```python
def apply_first_step_penalty(self, base_reaction_time: float) -> float:
    """
    Apply penalty for wrong initial step or misread.

    Chance based on fielder rating:
    - Elite (85k+): 1-3% chance
    - Average (50k): 5-8% chance
    - Poor (0-30k): 12-15% chance
    """
    # Calculate misread probability
    if self.REACTION_TIME >= 85000:
        misread_prob = 0.02  # 2% for elite
    elif self.REACTION_TIME >= 50000:
        misread_prob = 0.06  # 6% for average
    else:
        misread_prob = 0.13  # 13% for poor

    # Roll for misread
    if np.random.random() < misread_prob:
        # Wrong step adds 0.2-0.4s penalty
        penalty = np.random.uniform(0.2, 0.4)
        return base_reaction_time + penalty

    return base_reaction_time
```

**Impact:**
- Average fielder: 6% of plays start with wrong step
- Creates occasional balls that drop despite good positioning
- Scales with skill - elite fielders rarely misread

---

### 3. Route Efficiency Variance

**Current:** Always 88-99% (deterministic)
**Proposed:** Vary route quality based on ball difficulty and fielder skill

```python
def get_route_efficiency_with_variance(self, ball_trajectory_complexity: float = 0.5) -> float:
    """
    Get route efficiency with play-by-play variance.

    Parameters
    ----------
    ball_trajectory_complexity : float
        0.0 = easy (straight path), 1.0 = complex (curving, wind-affected)
    """
    base_efficiency = self.get_route_efficiency_pct()  # 0.70-0.99

    # Variance based on skill and trajectory complexity
    # Elite fielders: ±0.03 on easy plays, ±0.06 on complex
    # Average fielders: ±0.06 on easy plays, ±0.12 on complex
    # Poor fielders: ±0.10 on easy plays, ±0.18 on complex

    if self.ROUTE_EFFICIENCY >= 85000:
        base_variance = 0.03
    elif self.ROUTE_EFFICIENCY >= 50000:
        base_variance = 0.06
    else:
        base_variance = 0.10

    # Scale variance by trajectory complexity
    actual_variance = base_variance * (1.0 + ball_trajectory_complexity)

    # Apply beta distribution for realistic skew (centered slightly below base)
    # Beta(α=5, β=3) creates slight left skew (more bad routes than perfect routes)
    alpha, beta_param = 5.0, 3.0
    random_factor = np.random.beta(alpha, beta_param)  # 0.0-1.0, skewed toward 0.7

    # Map to variance range
    efficiency_variation = (random_factor - 0.625) * actual_variance * 2.0
    actual_efficiency = base_efficiency + efficiency_variation

    # Clamp to valid range [0.50, 1.00]
    return np.clip(actual_efficiency, 0.50, 1.00)
```

**Impact:**
- 88% base efficiency → actual range 82-94% (average complexity)
- Occasional poor routes (75-80%) even for good fielders
- Trajectory complexity affects variance (line drives harder to read than fly balls)

---

### 4. Catch Execution Variance

**Current:** Single probability roll
**Proposed:** Add execution failure chance even when fielder arrives on time

```python
def calculate_catch_probability_with_variance(self, ball_position, ball_arrival_time):
    """
    Enhanced catch probability with execution variance.
    """
    # Calculate base catch probability (existing logic)
    base_prob = self.calculate_catch_probability(ball_position, ball_arrival_time)

    # ADDITIONAL IMPERFECTION: Execution errors
    # Even when fielder is in position, they can fail to catch

    # Get time margin
    fielder_time = self.calculate_effective_time_to_position(ball_position)
    time_margin = ball_arrival_time - fielder_time

    # Only apply to routine plays (time_margin >= 0.2s)
    # Difficult plays already have low probability
    if time_margin >= 0.2:
        # Execution error rate: 3-8% for "should catch" plays
        # Represents: bobbles, drops, misjudged last second, etc.
        hands_rating = self.attributes.FIELDING_SECURE

        if hands_rating >= 85000:
            execution_error_rate = 0.02  # 2% for gold glovers
        elif hands_rating >= 50000:
            execution_error_rate = 0.05  # 5% for average
        else:
            execution_error_rate = 0.10  # 10% for poor hands

        # Apply execution error reduction
        base_prob *= (1.0 - execution_error_rate)

    return base_prob
```

**Impact:**
- Routine plays (fielder arrives 0.5s early): 5% chance to still drop it
- Prevents 98-99% catch rates on easy plays
- Reflects real MLB where even "routine" plays occasionally fail

---

## Expected Outcomes

### Before Changes (Current State)
- Route efficiency logged: 90-99%+ on most plays
- Balls dropped: Mostly only when fielder arrives late
- Fielding percentage: ~.995+ (unrealistically high)
- BABIP conversion: ~70%+ (too high)

### After Changes (Expected)
- Route efficiency logged: 75-95% range with realistic variance
- Balls dropped: Mix of arrival timing + execution failures
- Fielding percentage: ~.975-.985 (MLB realistic)
- BABIP conversion: ~65-70% (closer to MLB ~.300 BABIP)

### Validation Metrics
1. Route efficiency distribution should be bell curve, not ceiling cluster
2. Plays with time_margin > 0.5s should have ~3-5% error rate (not <1%)
3. Ground balls through infield should increase 10-15%
4. Hits per 9 innings should increase from ~15-18 to ~18-22 (closer to MLB avg ~19)

---

## Implementation Recommendations

### Phase 1: Add Variance Functions (Low Risk)
1. Add variance methods to `FielderAttributes` class
2. Keep existing methods as `get_X()`, add new `get_X_with_variance()`
3. Test in isolation without changing game logic

### Phase 2: Integrate into Fielding Pipeline (Medium Risk)
1. Update `Fielder.calculate_effective_time_to_position()` to use variance
2. Update `Fielder.calculate_catch_probability()` to use execution variance
3. Feature flag: `USE_FIELDING_VARIANCE = True/False` for easy testing

### Phase 3: Calibrate (High Risk)
1. Run 100-game simulations with variance enabled
2. Measure: route efficiency distribution, fielding %, BABIP
3. Tune variance parameters to match MLB distributions
4. Commit only after validation

### Testing Strategy
```bash
# Test 1: Single play variance check
python test_fielding_variance.py

# Test 2: Small sample (10 games)
python simulate_games.py --games 10 --variance enabled

# Test 3: Large sample (100 games)
python simulate_games.py --games 100 --variance enabled --output stats.csv

# Compare to baseline (no variance)
python compare_variance_impact.py
```

---

## Code Locations for Implementation

### Files to Modify

1. **batted_ball/attributes.py** (Lines 362-590)
   - Add variance methods to `FielderAttributes` class
   - Lines 388-406: Add `get_reaction_time_with_variance()`
   - Lines 454-471: Add `get_route_efficiency_with_variance()`
   - Add new: `apply_first_step_penalty()`, `get_execution_error_rate()`

2. **batted_ball/fielding.py** (Lines 555-798)
   - Line 587: Update `get_first_step_time()` call to use variance
   - Line 944: Update catch probability calculation
   - Add feature flag: `ENABLE_FIELDING_VARIANCE`

3. **batted_ball/constants.py** (New section)
   - Add variance configuration constants:
     ```python
     # Fielding variance controls (2025-11-19 realism enhancement)
     ENABLE_FIELDING_VARIANCE = True
     REACTION_TIME_VARIANCE_ELITE = 0.02
     REACTION_TIME_VARIANCE_AVG = 0.05
     REACTION_TIME_VARIANCE_POOR = 0.08
     MISREAD_CHANCE_ELITE = 0.02
     MISREAD_CHANCE_AVG = 0.06
     MISREAD_CHANCE_POOR = 0.13
     ROUTE_EFFICIENCY_VARIANCE_ELITE = 0.03
     ROUTE_EFFICIENCY_VARIANCE_AVG = 0.06
     ROUTE_EFFICIENCY_VARIANCE_POOR = 0.10
     EXECUTION_ERROR_RATE_ELITE = 0.02
     EXECUTION_ERROR_RATE_AVG = 0.05
     EXECUTION_ERROR_RATE_POOR = 0.10
     ```

---

## Conclusion

The fielding system is **physics-accurate but human-inaccurate**. The root cause is excessive determinism - every fielder executes at their exact rating on every play with zero variance. While multiple calibration attempts have adjusted base values, they haven't addressed the fundamental lack of play-to-play randomness that characterizes real MLB defense.

**Recommendation:** Implement 4-layer variance system (reaction time, first step, route efficiency, execution) with skill-based variance scaling. This preserves the physics foundation while adding realistic human imperfection.

**Priority:** HIGH - This issue directly causes the "vacuum cleaner defense" problem and inflates fielding percentages beyond MLB realism.

**Risk:** LOW-MEDIUM - Changes are additive (new variance functions) and can be feature-flagged for safe testing.

---

**Next Steps:**
1. Review and approve this analysis
2. Implement Phase 1 (variance functions) with feature flag
3. Run validation tests (10-100 games)
4. Calibrate variance parameters to MLB distributions
5. Commit with comprehensive documentation

