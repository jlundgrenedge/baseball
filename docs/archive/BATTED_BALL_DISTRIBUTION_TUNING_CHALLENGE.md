# Batted Ball Distribution Tuning Challenge

## Overview

This document describes a fundamental physics tuning challenge in the baseball simulation. The goal is to help an AI research agent understand the problem deeply and propose solutions by examining the source code.

## The Problem Statement

We need the simulation to produce **MLB-realistic batted ball distributions**:

| Metric | Target | Current Best |
|--------|--------|--------------|
| Ground Ball % | 45% | 41-43% ✓ |
| Line Drive % | 21% | 34-46% ✗ |
| Fly Ball % | 34% | 14-22% ✗ |
| HR/FB Rate | 12.5% | 4-13% (inconsistent) |
| Avg Exit Velocity | 88 mph | 89-90 mph ✓ |
| Hard Hit Rate (95+ mph) | 40% | 20-24% ✗ |

**The core conundrum**: When we tune parameters to improve one metric, others degrade. Specifically:
- Increasing launch angle variance spreads more balls into FB range BUT reduces HR/FB rate
- The LD range (10-25°) captures too many outcomes regardless of mean/variance tuning
- A normal distribution fundamentally cannot match the asymmetric MLB distribution

## Key Files to Examine

### 1. `batted_ball/player.py` (Lines 520-580)
**Critical function**: `get_swing_path_angle_deg()`

This determines the launch angle for each batted ball. Key components:
- `mean_angle`: From hitter's attack angle attribute (varies by hitter type)
- `natural_variance`: Currently 19.5° std dev (we've tested 15°, 18°, 21°)
- `location_adjustment`: Pitch height affects launch angle (0.3°/inch from zone center)
- `pitch_adjustment`: Breaking balls produce more GB, fastballs more FB

**The issue**: We sample from a single normal distribution. MLB's actual distribution appears bimodal or has heavier tails.

### 2. `batted_ball/attributes.py` (Lines 160-220, 950-1100)
**Key functions**:
- `get_attack_angle_mean_deg()`: Maps raw attribute (0-100k scale) to mean swing angle
- `create_groundball_hitter()`: Attack angle 34k-42k → mean ~5°
- `create_balanced_hitter()`: Attack angle 46k-58k → mean ~12°
- `create_power_hitter()`: Attack angle 68k-88k → mean ~20°

**The mapping math** uses `piecewise_logistic_map()` with anchors:
- 0 → -5° (extreme grounder)
- 50k → 10° (average)
- 85k → 20° (elite lofter)
- 100k → 30° (superhuman)

### 3. `batted_ball/contact.py` (Lines 505-620)
**Function**: `full_collision()`

The physics collision model that determines:
- Exit velocity from bat speed + pitch speed + collision efficiency
- Launch angle from bat path + pitch trajectory + vertical offset
- Backspin from contact point offset

**Key constants** (from `constants.py`):
- `COLLISION_EFFICIENCY_WOOD = 0.11` (the "q" in BBS = q×v_pitch + (1+q)×v_bat)
- `OFFSET_EFFICIENCY_DEGRADATION = 0.10`

### 4. `batted_ball/game_simulation.py` (Lines 1535-1585)
**Function**: `create_test_team()`

Creates teams with weighted hitter type distribution:
```python
hitter_type_weights = [0.25, 0.25, 0.30, 0.15, 0.05]  # GB, LD, Balanced, FB, Power
```

This creates an effective weighted mean attack angle of ~12°, which falls right in the LD zone.

### 5. `batted_ball/constants.py`
Contains all physics coefficients. Key ones for this problem:
- Sweet spot physics
- COR (coefficient of restitution) degradation
- Spin factors

## Why This Is Hard

### 1. The Bin Width Problem
MLB batted ball categories have asymmetric bin widths:
- Ground Ball: < 10° (covers 10° + all negative angles)
- Line Drive: 10-25° (only 15° wide)
- Fly Ball: 25-50° (25° wide)
- Pop-up: > 50°

With a normal distribution centered around 12° (typical MLB mean), the LD bin naturally captures the peak of the distribution, while FB requires being 13°+ above the mean.

### 2. The Correlation Problem
In reality, hitters who swing with higher attack angles also tend to:
- Swing harder (power hitters)
- Have better barrel accuracy (elite contact)
- Face different pitch selection

Our model treats these somewhat independently.

### 3. The Selection Bias Problem
Not all swings result in contact. If high-offset swings (which might produce more extreme angles) are more likely to whiff, the contacted balls have a narrower distribution than the swing attempts.

### 4. The Normal Distribution Limitation
MLB's actual launch angle distribution is NOT normal. It appears to have:
- A peak around 10-15° (line drives)
- A secondary mode around 25-30° (fly balls)
- Heavy left tail (topped grounders)

A single normal distribution cannot replicate this shape.

## What We've Tried

1. **Zone center fix**: Discovered `pitch_location[1]` was absolute height (30" at zone center), not relative. Fixed by subtracting 30" - this dropped mean launch angle from 21° to 13°.

2. **Variance tuning**:
   - 15° std dev: Too concentrated in LD zone
   - 18° std dev: Better FB rate, HR/FB ~13% ✓
   - 21° std dev: Too spread, HR/FB drops to 4%

3. **Attack angle recalibration**: Adjusted the attribute mappings for different hitter types.

4. **Collision efficiency**: Tuned from 0.09 → 0.14 → 0.11 to target 88 mph average EV.

## Potential Solutions to Explore

### Option A: Bimodal Distribution
Instead of sampling from one normal distribution, sample from a mixture:
- 60% from N(μ=8°, σ=12°) - contact-focused swings
- 40% from N(μ=28°, σ=10°) - lift-focused swings

### Option B: Hitter-Specific Variance
Currently all hitters use the same natural variance. Power hitters might have higher variance (more extreme outcomes) while contact hitters have lower variance.

### Option C: Swing Intent Modeling
Model whether the hitter is trying to:
- Put ball in play (lower angle, tighter variance)
- Drive the ball (medium angle)
- Elevate for power (higher angle, more variance)

### Option D: Outcome-Dependent Modeling
Use different distributions based on contact quality:
- Squared-up contact → normal around 15°
- Topped balls → forced negative angles
- Under balls → forced high angles

### Option E: Adjust Classification Thresholds
If our physics is correct but produces different distributions, maybe adjust the LD/FB threshold from 25° to something else. However, this feels like fitting rather than fixing.

## Questions for the Research Agent

1. What does the academic literature say about MLB launch angle distributions? Is it truly bimodal?

2. Are there physics-based reasons why the distribution should be non-normal?

3. How do professional baseball simulation games (OOTP, MLB The Show) handle this?

4. Is there a way to make the variance depend on the mean (heteroscedasticity) that would help?

5. Should vertical contact offset directly determine launch angle rather than going through the swing path?

## Test Commands

After making changes, validate with:
```bash
python -m batted_ball.validation  # Must pass 7/7 physics tests
python test_collision.py          # Check batted ball distribution
```

## Current State Summary

The simulation produces realistic:
- Exit velocities (88-90 mph average)
- Ground ball rates (41-43%)
- Individual game outcomes (realistic scores, hit totals)

But struggles with:
- Too many line drives (35-45% vs 21% target)
- Too few fly balls (15-22% vs 34% target)
- Inconsistent HR/FB rate (varies 4-13% depending on variance setting)

The fundamental issue is that a single normal distribution for launch angles cannot simultaneously match all three GB/LD/FB percentage targets given the asymmetric bin widths used by MLB.
