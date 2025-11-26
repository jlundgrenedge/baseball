# BABIP Gap Analysis: Research Prompt for Further Investigation

## Executive Summary

Our baseball physics simulation has calibrated **exit velocity** and **hard hit rate** to match MLB targets (HHR ~38% vs 40% target, Avg EV ~90 mph vs 88 mph target), yet **BABIP remains stubbornly low at ~0.18 vs MLB's 0.295 target**. This document identifies gaps in our current research and implementation that may explain this discrepancy.

---

## Current State

### What Works
- Exit velocity distribution matches MLB (mean ~90 mph, HHR ~38%)
- Physics validation passes 7/7 tests (trajectory, spin, altitude effects)
- Collision efficiency model properly accounts for bat-ball contact quality
- Launch angle has mixture model with extreme tails for weak contact

### What Doesn't Work
- **BABIP: 0.18 vs 0.295 target** (balls in play are fielded 82% vs 70.5%)
- **K Rate: ~32% vs 22% target** (too many strikeouts)
- **Runs/Game: ~1.5 vs 4.5 target** (insufficient offense)

---

## Gap Analysis: Launch Angle Research

### Gap 1: Correlation Between Exit Velocity and Launch Angle

**Current Research Says**: "MLB data shows a slight negative correlation between EV and LA for the hardest-hit balls"

**What's Missing**: 
- Quantified correlation coefficients (r-value) for EV-LA relationship
- How this correlation varies by:
  - Contact quality (solid vs fair vs weak)
  - Pitch type
  - Pitch location
  - Batter handedness
- The bivariate joint distribution of (EV, LA) rather than treating them independently

**Why This Matters**: If hardest-hit balls (95+ mph) tend toward line-drive angles (10-25°), they fall for hits. If our model allows many 100+ mph balls at catchable fly ball angles (30-40°), they become easy outs.

**Research Request**: Provide empirical data on the joint distribution of (EV, LA) from MLB Statcast, including:
1. Correlation coefficient for EV vs LA overall
2. 2D density plot or heatmap of (EV, LA) distribution
3. Conditional distributions: P(LA | EV > 95mph) vs P(LA | EV < 85mph)
4. How "barrel" contact (optimal EV+LA) is distributed vs non-barrel

---

### Gap 2: Spray Angle Distribution and Correlation with LA

**Current Research Says**: "The ball's horizontal direction is primarily determined by bat angle at contact and timing"

**What's Missing**:
- Empirical spray angle distributions by hit type (ground ball vs line drive vs fly ball)
- Correlation between spray angle and launch angle
- Pull rate for ground balls vs fly balls (GB are often more pulled)
- How spray angle affects fielding difficulty and BABIP

**Why This Matters**: A ground ball pulled sharply to the left side has different BABIP than one hit up the middle. If our spray model creates too many catchable spray angles, BABIP suffers.

**Research Request**:
1. Spray angle distribution by launch angle bucket (<10°, 10-25°, 25-45°, >45°)
2. Pull/center/opposite field rates by batted ball type
3. BABIP by spray angle bucket
4. Correlation coefficients between LA and spray angle

---

### Gap 3: Batted Ball Landing Distance by LA/EV Combination

**Current Research Says**: Details on fly ball trajectories and optimal launch angles for distance

**What's Missing**:
- Landing distances for ground balls and line drives
- How EV translates to ground ball distance (not just time to fielder)
- The "sweet spot" for line drive hits - which (EV, LA) combinations fall for hits
- Gap between infield and outfield where balls land

**Why This Matters**: Balls landing 180-220 feet from home plate (shallow outfield) are the hardest to field. If our LA distribution doesn't produce enough balls in this "hit zone," BABIP drops.

**Research Request**:
1. Distribution of landing distances by launch angle bucket
2. Heat map of (landing distance, hang time) for batted balls
3. What (EV, LA) combinations produce landing distances in 150-250 ft range
4. MLB data on where hits vs outs land in the field

---

### Gap 4: Hang Time and Catch Probability Relationship

**Current Research Says**: General principles of fly ball physics and fielder range

**What's Missing**:
- Empirical catch probability curves by (distance, hang time)
- How marginal changes in LA affect catch probability
- The "hang time sweet spot" where balls are hard to catch
- Line drive hang times (typically 0.8-1.5s) vs fielder coverage ability

**Why This Matters**: Our fielding model uses hang time margins to determine catch probability. If LA distribution produces too many high-hang-time fly balls, fielders can reach them easily.

**Research Request**:
1. Catch probability as function of (distance to fielder, hang time)
2. Distribution of hang times for hits vs outs
3. For each launch angle range, what's the average catch probability?
4. Statcast "catch probability" model parameters if available

---

### Gap 5: Launch Angle Distribution Shape - Is It Really Normal?

**Current Research Says**: "More normal than bimodal" with heavy tails, mean ~10-15°, std dev ~15-20°

**What's Missing**:
- Is the distribution actually normal, or skewed?
- Exact parameters for mixture model components
- How the distribution varies by count (0-2 vs 3-0)
- Whether tail behavior should be modeled separately

**Why This Matters**: The exact shape determines how many balls land in the "hit zone." A distribution that's too wide or too centered on fly ball angles will produce low BABIP.

**Research Request**:
1. Skewness and kurtosis of actual MLB LA distribution
2. Best-fit distribution type (normal, skew-normal, mixture)
3. Fitted parameters for that distribution
4. How shape varies by batter type (contact hitter vs power hitter)

---

### Gap 6: Hit Type Proportions (GB/LD/FB/PU) and Their BABIP

**Current Research Says**: General ranges for each category

**What's Missing**:
- Exact proportions of each hit type in MLB
- BABIP for each hit type (critical for overall BABIP calculation)
- How our simulation's hit type proportions compare to MLB
- Whether we're producing too many fly balls or pop-ups

**Why This Matters**: 
- Ground balls: BABIP ~0.239 (44% of BIP in MLB)
- Line drives: BABIP ~0.685 (21% of BIP)
- Fly balls: BABIP ~0.145 (26% of BIP)  
- Pop-ups: BABIP ~0.010 (9% of BIP)

If our mix differs from MLB, our overall BABIP will differ accordingly.

**Research Request**:
1. Exact MLB proportions of GB/LD/FB/PU
2. BABIP for each category
3. Launch angle thresholds that define each category
4. Expected vs actual BABIP given our hit type mix

---

### Gap 7: Line Drive Definition and Production

**Current Research Says**: Line drives have LA in 10-25° range

**What's Missing**:
- What EV threshold makes a line drive vs weak fly ball?
- How many of our 10-25° LA balls have sufficient EV to be true line drives?
- The "barrel" zone definition and how often we produce barrels
- Whether our contact model produces enough barrels

**Why This Matters**: Line drives are hits 68.5% of the time. If our 10-25° LA balls are mostly weak contact (low EV), they may be caught. A true line drive needs both optimal LA AND high EV.

**Research Request**:
1. Definition of "barrel" in terms of EV and LA thresholds
2. Barrel rate in MLB (~7% of BIP)
3. BABIP for barrel vs non-barrel contact
4. Our simulation's barrel rate

---

## Gap Analysis: Fielding Model

### Gap 8: Fielder Starting Positions and Shifts

**Current Research Says**: Generic fielder positioning

**What's Missing**:
- Actual MLB fielder positioning data (defensive shifts)
- How positioning affects BABIP (shifted teams have different BABIP)
- Whether our fielders are positioned too optimally
- Coverage gaps that should exist but don't in our model

**Research Request**:
1. Average fielder starting positions in MLB
2. Range of positions (standard vs shifted)
3. Coverage heat maps showing defensive "holes"
4. BABIP by spray angle with standard vs shifted defense

---

### Gap 9: Route Efficiency and Range Realism

**Current Research Says**: Elite fielders have 95%+ route efficiency

**What's Missing**:
- Distribution of route efficiency across MLB fielders
- How route efficiency affects catch probability in practice
- Whether our fielders are too efficient (too many catches)
- First-step quickness impact on range

**Research Request**:
1. MLB route efficiency distribution (mean, std dev)
2. Relationship between route efficiency and range (OAA)
3. How much range is gained by 5% better route efficiency
4. Our fielders' effective range vs MLB averages

---

### Gap 10: Ground Ball Fielding Time Windows

**Current Research Says**: Infielders have ~0.8-1.2s to field hard ground balls

**What's Missing**:
- Exact time windows for different ground ball speeds
- When a ground ball becomes uncatchable (threshold)
- How infield hit rate relates to ground ball speed
- Whether our infielders are fielding too many hard grounders

**Research Request**:
1. Ground ball travel times to each infield position by EV
2. Infield hit rates by ground ball EV
3. Time threshold where ground balls become hits
4. Our simulation's infield hit rate vs MLB

---

## Specific Research Requests

### Request A: BABIP Component Analysis

Please provide a breakdown of MLB BABIP by:
1. Batted ball type (GB/LD/FB/PU)
2. Exit velocity bucket (< 80, 80-90, 90-100, 100+ mph)
3. Launch angle bucket (< 0°, 0-10°, 10-25°, 25-45°, > 45°)
4. Combined (EV, LA) matrix showing hit probability for each cell

This will allow us to diagnose exactly WHERE our simulation differs from reality.

---

### Request B: Optimal Launch Angle for BABIP

Research the question: "What launch angle maximizes BABIP at various exit velocities?"

Specifically:
1. At 85 mph EV, what LA range has highest BABIP?
2. At 95 mph EV, what LA range has highest BABIP?
3. At 105 mph EV, what LA range has highest BABIP?
4. How does the optimal LA for BABIP differ from optimal LA for slugging?

---

### Request C: Line Drive Production Requirements

Research: "What swing/contact characteristics produce line drives?"

1. What barrel accuracy (contact offset) is needed for line drives?
2. What attack angle produces 10-25° launch angles?
3. How does timing affect line drive production?
4. What percentage of swings should produce line drives?

---

### Request D: Catch Probability Model Validation

Research: "How does catch probability relate to fielder arrival margin?"

Our current model uses:
- ≥1.0s margin → 95% catch
- ≥0.5s margin → 92% catch
- ≥0.0s margin → 80% catch
- Negative margin → scaled probability

Please validate or correct these thresholds with:
1. Statcast catch probability data
2. Catch % vs arrival time differential
3. Whether our thresholds are too generous

---

## Gap Analysis: Player Creation Pipeline

### Gap 11: Bat Speed Data Available But Not Used

**Current State**: 
We now fetch **actual Statcast bat speed** from Baseball Savant bat tracking (available 2024+).
However, the simulation derives bat speed from the `power` attribute using `piecewise_logistic_map()`.

**Data Available (from database investigation)**:
- Statcast bat speed: avg=71.0 mph (range 68-73 mph for typical players)
- Power attribute produces: avg=73.1 mph bat speed (2 mph higher than actual)

**The Problem**:
The power attribute → bat speed mapping was calibrated before actual bat speed data was available.
Now we have the real data but aren't using it.

**Research Request**:
1. What is the distribution of MLB bat speeds from bat tracking? (mean, std dev, range)
2. How does bat speed correlate with exit velocity? (formula if possible)
3. How should we calibrate the power → bat speed mapping to match reality?
4. Or should we use actual bat speed directly instead of deriving it?

---

### Gap 12: Squared-Up Rate Not Mapped to Contact Quality

**Current State**:
We fetch `squared_up_rate` from Statcast bat tracking (0-1 scale, e.g., 0.22-0.36).
This directly measures how often a hitter squares up the ball (optimal contact).
However, this is NOT used in the simulation - instead we derive barrel accuracy from batting average and K%.

**Data Available**:
- Pete Crow-Armstrong: squared_up_rate = 0.221 (22.1%)
- Nico Hoerner: squared_up_rate = 0.364 (36.4%)
- Average MLB: ~28% squared-up rate

**The Problem**:
Squared-up rate is the most direct measure of contact quality available, but it's ignored.
Instead, we use indirect stats (AVG, K%) that conflate contact frequency with contact quality.

**Research Request**:
1. What is the distribution of squared-up rates across MLB? (mean, std dev)
2. How does squared-up rate correlate with exit velocity distribution?
3. How does squared-up rate correlate with BABIP?
4. What barrel offset (in inches) corresponds to squared-up contact?

---

### Gap 13: Attack Angle Control Inferred, Not Measured

**Current State**:
The `attack_angle_control` attribute is calculated from HR rate, SLG, and barrel%.
There's no direct launch angle data being used.

**Data Available**:
- Statcast provides average launch angle per player
- We currently don't fetch or store this

**The Problem**:
Launch angle is fundamental to hit outcomes, but we're inferring it from power stats rather than measuring it directly.

**Research Request**:
1. What is the distribution of mean launch angles across MLB hitters?
2. How does LA correlate with HR rate, FB rate, GB rate?
3. Can we fetch LA directly from Statcast and use it to calibrate attack_angle_control?
4. What attack_angle_control values produce which mean launch angles?

---

### Gap 14: Contact Attribute Too High for Power Hitters

**Current State**:
Contact attribute is derived from batting average + K% (inverted).
Power hitters with low AVG and high K% get low contact, which is correct.
But power hitters with moderate AVG still get high contact, making their barrel accuracy too tight.

**Data From Database**:
- Nico Hoerner (contact hitter): contact=93,499 → barrel error=0.28" (very tight)
- Pete Crow-Armstrong (power hitter): contact=42,546 → barrel error=0.75"
- Average contact=52,585 → barrel error=0.59"

**The Problem**:
If average barrel error is 0.59", and elite contact hitters have 0.28", the simulation may produce too many hard-hit balls that become easy outs (high EV + catchable LA).

**Research Request**:
1. What is the actual barrel offset distribution for MLB contact?
2. How does squared-up rate translate to barrel offset in inches?
3. Are we making barrel accuracy too tight overall?

---

## Hypotheses to Test

Based on the gaps identified, here are hypotheses for why BABIP is low:

### Hypothesis 1: Launch Angle Distribution Too Wide
Our LA standard deviation (~15-20°) may produce too many balls at catchable angles (30-45° fly balls and pop-ups).

### Hypothesis 2: Insufficient Line Drive Production
Our contact model may not produce enough 10-25° LA balls with high EV (true line drives).

### Hypothesis 3: Fielders Too Efficient
Our route efficiency and reaction time parameters may make fielders unrealistically good.

### Hypothesis 4: EV-LA Correlation Missing
If high-EV balls are uniformly distributed across LA (rather than concentrated in line-drive zone), more are caught.

### Hypothesis 5: Bat Speed Too High
Power attribute → bat speed mapping produces 73 mph avg, but actual Statcast shows 71 mph.
This 2 mph difference affects exit velocity calculations.

### Hypothesis 6: Barrel Accuracy Too Tight
Contact attribute produces 0.59" avg barrel error, but if real MLB is looser (e.g., 0.8"),
we're producing too many "squared up" contacts that go to catchable locations.

### Hypothesis 7: Spray Angle Creates Easy Outs
If balls are too often sprayed to where fielders stand, catch rates are artificially high.

---

## Player Creation Pipeline Summary

### Current Flow
```
MLB Stats (pybaseball/Savant) 
    → StatsConverter.mlb_stats_to_hitter_attributes_v2()
        → power, contact, discipline, speed, vision, attack_angle_control
            → HitterAttributes class
                → Physics parameters (bat_speed_mph, barrel_accuracy_mm, etc.)
```

### Data We Fetch But Don't Use
| Data | Source | What It Measures | Current Status |
|------|--------|------------------|----------------|
| bat_speed | Bat Tracking | Actual bat speed in mph | FETCHED, NOT USED |
| swing_length | Bat Tracking | Swing arc length | FETCHED, NOT USED |
| squared_up_rate | Bat Tracking | % of good contact | FETCHED, NOT USED |
| hard_swing_rate | Bat Tracking | % of hard swings | FETCHED, NOT USED |

### What We Derive Instead
| Physics Param | Derived From | Better Source Available? |
|--------------|--------------|--------------------------|
| Bat Speed | power attr (from SLG, HR, EV) | YES: bat_speed column |
| Barrel Accuracy | contact attr (from AVG, K%) | YES: squared_up_rate |
| Attack Angle | attack_angle_control (from HR, SLG) | MAYBE: direct LA data |

### Proposed Fixes

1. **Use Actual Bat Speed**: When bat_speed is available, use it directly instead of deriving from power attribute.

2. **Map Squared-Up Rate to Barrel Accuracy**: 
   - squared_up_rate of 0.36 (elite) → barrel_accuracy ~0.3"
   - squared_up_rate of 0.22 (average) → barrel_accuracy ~0.6"
   - squared_up_rate of 0.15 (poor) → barrel_accuracy ~1.0"

3. **Fetch and Use Launch Angle Data**: Add mean launch angle to the Statcast fetch, use it to set attack_angle_control.

### Implementation Details for Bat Speed Fix

**Current Code Path (batted_ball/attributes.py:HitterAttributes.get_bat_speed_mph)**:
```python
def get_bat_speed_mph(self) -> float:
    """Convert BAT_SPEED attribute to physical bat speed (60-95 mph range)."""
    rating = self.get_attribute(HitterAttributeType.BAT_SPEED)  # Uses POWER-derived value
    return piecewise_logistic_map(rating, 60.0, 95.0, 85000)
```

**Proposed Fix**:
1. Add `actual_bat_speed: Optional[float]` parameter to `HitterAttributes.__init__()`
2. Store it as instance variable when provided
3. Modify `get_bat_speed_mph()` to return actual value if available, else derive from power

**Files to Modify**:
- `batted_ball/attributes.py`: Add actual_bat_speed parameter and logic
- `batted_ball/database/db_manager.py`: Pass bat_speed when loading hitter
- `batted_ball/player.py`: Update Hitter class to pass bat_speed to attributes

### Implementation Details for Squared-Up Rate Fix

**Proposed Mapping (squared_up_rate → barrel_error_mm)**:
```python
def squared_up_to_barrel_error(squared_up_rate: float) -> float:
    """Convert squared-up rate (0-1) to barrel error in mm.
    
    Higher squared-up rate = tighter contact = smaller error.
    - 0.36 (elite, like Nico Hoerner) → 7.5mm (0.3")
    - 0.28 (average) → 15mm (0.6")
    - 0.18 (poor) → 25mm (1.0")
    """
    # Linear interpolation: error = 40 - 90*rate (clamped to 5-30mm range)
    error = 40.0 - 90.0 * squared_up_rate
    return max(5.0, min(30.0, error))
```

---

## Output Format Requested

For each research area, please provide:
1. **Data**: Specific numbers, distributions, correlations
2. **Source**: Where the data comes from (Statcast, Baseball Savant, academic papers)
3. **Implementation Guidance**: How to incorporate this into a physics simulation
4. **Validation Approach**: How to verify the implementation matches reality

---

## Priority Order

1. **Request A** (BABIP Component Analysis) - Diagnose the exact problem
2. **Gap 11** (Bat Speed Data) - We have the data, just need to use it
3. **Gap 12** (Squared-Up Rate) - Direct measure of contact quality
4. **Gap 1** (EV-LA Correlation) - Likely biggest impact on BABIP
5. **Gap 6** (Hit Type Proportions) - Verify our mix is correct
6. **Gap 4** (Hang Time/Catch Probability) - Validate fielding model
7. **Gap 7** (Line Drive/Barrel Production) - Ensure we make enough line drives

---

## Database Investigation Results (Actual Data)

### Sample Team: Chicago Cubs 2025

**Statcast Data Availability:**
- Sprint Speed: 100% available
- Exit Velocity: 100% available  
- Barrel %: 100% available
- OAA: 86% available
- Arm Strength: 79% available
- Bat Speed (Tracking): 71% available
- Squared-Up Rate: 71% available

**Attribute Distributions (14 hitters):**
- Contact: min=37,491, avg=52,585, max=93,499
- Power: min=17,340, avg=43,525, max=66,149
- Vision: avg=53,326
- Attack Angle Control: avg=56,168

**Physics Parameter Implications:**
- Power=43,525 → Bat Speed=73.1 mph (actual Statcast: 71.0 mph) ⚠️
- Contact=52,585 → Barrel Error=0.59" (MLB target: ~0.6") ✓
- Attack Angle=56,168 → Mean LA=14.5° (MLB target: ~12°) ⚠️

**Key Discrepancy:**
Actual Statcast bat speed (71.0 mph) is 2 mph lower than what power attribute produces (73.1 mph).
This means we're overestimating bat speed → overestimating exit velocity → potentially affecting BABIP.

---

## Context for the Research AI

This is for a physics-based baseball simulation where all gameplay emerges from physical parameters (exit velocity, sprint speed, throw times), NOT statistical probabilities. The simulation calculates ball trajectories, fielder movements, and determines outcomes based on physics.

Current implementation:
- Exit velocity from bat-ball collision model (q = 0.13 base efficiency)
- Launch angle from mixture model (normal distribution + extreme tails)
- Fielding from kinematic model (reaction time, acceleration, top speed)
- All coordinates in feet, velocities in mph, angles in degrees

The goal is to produce realistic BABIP (~0.295) through correct physical modeling, not by artificially inflating hit probabilities.
