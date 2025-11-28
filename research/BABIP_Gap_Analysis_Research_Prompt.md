# BABIP Gap Analysis: Research Prompt for Further Investigation

## Executive Summary

Our baseball physics simulation has calibrated **exit velocity** and **hard hit rate** to match MLB targets (HHR ~38% vs 40% target, Avg EV ~90 mph vs 88 mph target), yet **BABIP remains stubbornly high at ~0.45 vs MLB's 0.295 target**. This document identifies gaps in our current research and implementation that may explain this discrepancy.

**Recent Discovery**: The primary issue is **ground ball fielding** - balls are getting through the infield at unrealistically high rates. Our ground ball BABIP is approximately 0.60-0.70 vs MLB's ~0.24 target.

---

## Current State

### What Works
- Exit velocity distribution matches MLB (mean ~90 mph, HHR ~38%)
- Physics validation passes 7/7 tests (trajectory, spin, altitude effects)
- Collision efficiency model properly accounts for bat-ball contact quality
- Trajectory physics correctly calculates ground ball landing positions (negative LA → 15-25 ft from home)
- Coordinate system conversion between trajectory coords (x=outfield, y=lateral) and field coords (x=lateral, y=forward) is correct

### What Doesn't Work
- **BABIP: ~0.45 vs 0.295 target** (balls in play are fielded only ~55% vs 70.5%)
- **Ground Ball BABIP: ~0.60-0.70 vs 0.24 target** (main problem area)
- **Ground Ball Fielding Rate: ~33% vs ~76% target**
- **K Rate: ~32% vs 22% target** (too many strikeouts)
- **Runs/Game: ~7.3 vs 4.5 target** (too many runs due to ground balls getting through)

---

## Recent Debugging Work: Ground Ball Fielding

### What We Discovered

1. **Ground ball trajectory physics is correct**: A 100 mph exit velocity, -5° launch angle ground ball lands at ~22 ft from home plate and rolls toward the outfield at ~124 fps with deceleration of ~12 fps².

2. **Spray angle convention is correct**: 
   - Negative spray → Right field (positive X in field coords)
   - Positive spray → Left field (negative X in field coords)

3. **The problem is interception timing**: The ground ball interception algorithm tests discrete time points (0.1s, 0.15s, etc.) along the ball path. Fast-moving balls can pass through a fielder's interception zone between these test points.

4. **Direct-path fix helped partially**: We added logic to detect balls passing near a fielder's Y-position and calculate if they can intercept by moving laterally. This fixed comebackers to the pitcher but didn't help balls to the "holes."

### Current Ground Ball Interception Test Results

```
Ground ball fielding test (100 mph, LA=-5):
============================================================
Up the middle        spray= +0  land=(-0, 22)   -> FIELDED  by pitcher
Toward SS            spray=+30  land=(-11, 19)  -> THROUGH
Toward 2B            spray=-30  land=(11, 19)   -> FIELDED  by first_base
Toward 3B            spray=+45  land=(-16, 16)  -> THROUGH
Toward 1B            spray=-45  land=(16, 16)   -> THROUGH
SS hole              spray=+15  land=(-6, 22)   -> FIELDED  by shortstop
2B hole              spray=-15  land=(6, 22)    -> THROUGH
Line toward 3B       spray=+60  land=(-19, 11)  -> THROUGH
Line toward 1B       spray=-60  land=(19, 11)   -> THROUGH

Fielded: 3/9 = 33%
Target: ~75-80% fielded for realistic ground ball BABIP (~0.24)
```

### Key Observations

1. **Balls landing near fielder positions get fielded** (up the middle → pitcher, SS hole → shortstop)
2. **Balls landing far from fielders get through** (lines toward corners, balls to holes)
3. **Infielder depth may be too deep**: SS at Y=80-85, 2B at Y=75-80, but balls land at Y=15-22

### The Core Problem

Ground balls land at Y=15-25 feet from home plate, but infielders are positioned at Y=75-85 feet. The ball must roll 50-70 feet to reach the infielders. During this time, the ball decelerates but is still moving fast (100+ fps initially).

The interception algorithm finds the closest point where a fielder could intercept, but:
- For balls hit to the "holes" (between fielders), the closest point is far from any fielder
- The lateral distance to the ball path exceeds the fielder's ability to cover in time

### Potential Fixes to Investigate

1. **Infielder positioning**: Are our infielders positioned too deep? MLB infielders play at ~90-120 ft from home for normal depth, not 75-85 ft.

2. **Infielder lateral range**: Our max lateral range is 18 ft, but maybe it should be higher for infielders who can anticipate and charge.

3. **Charging the ball**: Infielders move forward on ground balls. Our model may not account for this properly.

4. **Time step resolution**: The 0.05s time step may be too coarse for fast ground balls.

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

### **CRITICAL Gap 8: Infielder Positioning and Ground Ball Interception**

**This is the primary issue causing high BABIP.**

**Current State**:
Our infielders are positioned at:
- Pitcher: (0, 60.5) - on the mound
- Shortstop: (-20, 80-85) with random variance
- Second Base: (20, 75-80) with random variance
- Third Base: (-60, 70-75) with random variance
- First Base: (60, 68-75) with random variance

Ground balls land at Y=15-25 ft from home plate and roll toward outfield at 100-130 fps.

**The Problem**:
When a ground ball is hit to the "hole" (between fielders), no fielder can reach it in time:
- Ball lands at (11, 19) for spray=-30° (toward 2B hole)
- Closest fielder (2B at ~(20, 78)) is 60+ feet away
- Ball reaches outfield grass before fielder can intercept

**What's Missing**:
1. **Actual MLB infielder depth positioning** - How far from home plate do infielders really play?
2. **Infielder charging mechanics** - Do infielders move forward on contact?
3. **Lateral range data** - How far laterally can infielders reach on ground balls?
4. **Ground ball travel times by spray angle** - Time windows for different hit directions
5. **Infield hit rate by exit velocity and spray angle** - What % of ground balls become hits?

**Research Request**:
1. Standard MLB infielder positioning (feet from home plate, feet from foul line)
2. Infielder depth by situation (normal, double play, drawn in)
3. Ground ball fielding success rate by spray angle zone
4. Infield hit rate for ground balls 100+ mph
5. How does infielder reaction/first-step quickness affect range?

---

### Gap 9: Fielder Starting Positions and Shifts

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

## Priority Order (Updated Based on Recent Debugging)

**HIGHEST PRIORITY - Ground Ball Fielding (This is the main problem):**
1. **Gap 8** (Infielder Positioning) - Infielders may be positioned wrong; ground balls getting through at 67% rate vs 24% target
2. **Request E** (NEW - Ground Ball Fielding Physics) - Need exact data on infielder depth, range, and travel times

**HIGH PRIORITY - Contact Quality:**
3. **Gap 11** (Bat Speed Data) - We have the data, just need to use it
4. **Gap 12** (Squared-Up Rate) - Direct measure of contact quality
5. **Gap 1** (EV-LA Correlation) - Affects hit type distribution

**MEDIUM PRIORITY - Validation:**
6. **Request A** (BABIP Component Analysis) - Diagnose where we differ from reality
7. **Gap 6** (Hit Type Proportions) - Verify our mix is correct
8. **Gap 4** (Hang Time/Catch Probability) - Validate fly ball fielding

---

## NEW: Request E - Ground Ball Fielding Physics (CRITICAL)

This is the most important research request. Our ground ball BABIP is ~0.65-0.70 vs MLB's 0.24.

**Questions to Answer:**

1. **Infielder Positioning (feet from home plate)**:
   - Where do SS, 2B, 3B, 1B position themselves in "normal" depth?
   - What's the range of depths (shallow for bunt defense, deep for double play)?
   - How does positioning vary by batter (pull hitter vs spray hitter)?

2. **Ground Ball Travel Physics**:
   - At what speed (mph) do ground balls travel to infielders?
   - How much do ground balls decelerate per foot on grass/dirt?
   - What's the typical time window for an infielder to field a hard ground ball?

3. **Infielder Range Data**:
   - How far laterally can an average infielder cover?
   - What's the "hole" size between SS and 3B? Between SS and 2B?
   - How does first-step quickness affect range (in feet)?

4. **Ground Ball Outcome Data by Location**:
   - What % of ground balls up the middle become hits?
   - What % of ground balls in the "hole" become hits?
   - What % of ground balls hit directly at an infielder become outs?
   - Infield hit rate by exit velocity (90 mph vs 100 mph vs 110 mph)?

5. **Charging Mechanics**:
   - Do infielders charge (move forward) on ground ball contact?
   - How much time does charging save on a play?
   - When do infielders "play it on a hop" vs charge?

**Why This Matters:**
Our simulation has ground balls landing at Y=15-25 ft from home plate, but infielders positioned at Y=70-85 ft. The ball travels 50-60 ft before reaching the infielder. If our infielder positioning is wrong, or our travel time calculations are off, we'll have incorrect fielding rates.

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

---

## Current Ground Ball Implementation Details

### Coordinate Systems

**Trajectory Coordinates** (used in physics engine):
- X-axis: Direction toward outfield (positive = center field)
- Y-axis: Lateral direction (positive = left field)
- Z-axis: Vertical (positive = up)

**Field Coordinates** (used for positions and fielding):
- X-axis: Lateral (positive = RIGHT field, negative = LEFT field)
- Y-axis: Forward direction (positive = toward center field)
- Z-axis: Vertical (positive = up)

**Conversion**: `field_x = -trajectory_y, field_y = trajectory_x`

### Current Infielder Positions (Field Coordinates, feet)

From `batted_ball/constants.py`:
- Pitcher: (0, 60.5) - on the mound
- Catcher: (0, -3) - behind home plate
- First Baseman: (60, 75) - near first base line
- Second Baseman: (20, 80) - toward 2B bag, shallow
- Shortstop: (-20, 80) - toward 2B bag, shallow
- Third Baseman: (-60, 75) - near third base line

Note: Positions have random variance of 3-9 feet applied in `fielding.py:add_fielder()`.

**Question for Research AI**: Are these positions realistic for MLB infielders? The Y-coordinates (75-80 ft from home) seem potentially too shallow or too deep.

### Ground Ball Physics Parameters

From `batted_ball/ground_ball_interception.py` and `batted_ball/constants.py`:
- Rolling friction: 0.30 (grass)
- Air resistance: ~2 fps² (GROUND_BALL_AIR_RESISTANCE)
- Total deceleration: ~12 fps² (gravity * friction + air resistance)
- Fielder reaction time: ~0.18s
- Fielder sprint speed: ~28-30 fps (elite)
- Max lateral range checked: 18 feet

### Ground Ball Trajectory Example

100 mph exit velocity, -5° launch angle, spray=0° (up the middle):
- Landing position: (0, 22) feet from home
- Landing speed: ~124 fps (85 mph)
- Ball direction: (0, 1) - straight toward center field
- Time to reach Y=60 (pitcher): ~0.5s total (0.18s flight + 0.32s roll)
- Time to reach Y=80 (SS/2B): ~0.7s total

### Key Files for Ground Ball System

1. `batted_ball/ground_ball_interception.py` - Main interception algorithm
2. `batted_ball/trajectory.py` - Ball trajectory physics, coordinate conversion
3. `batted_ball/field_layout.py` - Defensive positions
4. `batted_ball/fielding.py` - Fielder attributes and movement
5. `batted_ball/constants.py` - Physics constants
6. `batted_ball/ground_ball_handler.py` - Ground ball play execution

---

## Files to Attach for Deep Research AI

**Critical Files (MUST attach):**
1. `batted_ball/ground_ball_interception.py` - The core algorithm that's not working
2. `batted_ball/field_layout.py` - Defensive positioning
3. `batted_ball/trajectory.py` - Ball physics and coordinate systems
4. `batted_ball/constants.py` - All physics constants
5. `research/BABIP_Gap_Analysis_Research_Prompt.md` - This document

**Important Context Files:**
6. `batted_ball/fielding.py` - Fielder attributes and movement
7. `batted_ball/contact.py` - Bat-ball collision model
8. `batted_ball/at_bat.py` - At-bat simulation including launch angle
9. `CLAUDE.md` or `.github/copilot-instructions.md` - Project guidelines

**For Understanding Game Flow:**
10. `batted_ball/play_simulation.py` - How plays are simulated
11. `batted_ball/ground_ball_handler.py` - Ground ball play execution

**Database/Player Creation:**
12. `batted_ball/attributes.py` - Player attribute system
13. `batted_ball/database/stats_converter.py` - MLB stats to attributes conversion

