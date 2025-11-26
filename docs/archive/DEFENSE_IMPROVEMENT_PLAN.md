# Defense Improvement Plan

## Status: IMPLEMENTED (2025-11-25)

All changes have been implemented. Physics validation: 7/7 tests passing.

## Changes Made

### 1. Catch Probability Bands (fielding.py)
**Before → After:**
| Margin | Old Prob | New Prob | Effect |
|--------|----------|----------|--------|
| >= 1.0s | 0.99 | 0.95 | More routine drops |
| >= 0.5s | (0.98) | 0.92 | **New tier** |
| >= 0.2s | 0.98 | 0.88 | Harder routine catches |
| >= 0.0s | 0.85 | 0.78 | More drops on close plays |

### 2. Reaction Times (attributes.py)
**Before → After:**
| Level | Old Time | New Time |
|-------|----------|----------|
| Elite (85k) | 0.05s | 0.10s |
| Average (50k) | 0.10s | 0.18s |
| Slow (0) | 0.30s | 0.35s |

### 3. Route Penalties (fielding.py)
**Before → After:**
| Distance | Old Multiplier | New Multiplier |
|----------|----------------|----------------|
| Medium (30-60ft) | 0.30 | 0.50 |
| Long (60+ft) | 0.15 | 0.35 |

### 4. Route Efficiency Logging (route_efficiency.py)
Synced thresholds to match fielding.py for consistent logging display.

---

## Original Analysis (Pre-Implementation)

### Statistics
| Metric | Simulation | MLB Target | Status |
|--------|------------|------------|--------|
| BABIP | 0.248 | ~0.300 | **Too Low** |
| Fly Out Rate | 49.1% | ~35-40% | **Too High** |
| Ground Out Rate | 16.4% | ~25-30% | **Too Low** |
| K% | 26.2% | ~22-23% | Slightly high |

### Catch Probability Distribution
- 0.95 probability: 45.6% of plays (too many "routine" catches)
- 0.70 probability: 10.5%
- 0.50 probability: 8.1%
- 0.15 probability: 3.5%
- 0.02 probability: 32.3% (impossible plays)

### Time Margin Distribution
- Margin >= 1s: 48% of plays (fielders arrive way early)
- Margin 0-1s: 16%
- Margin < 0s: 36%

## Root Causes

1. **Fielders react too fast**: Current avg 0.10s, should be closer to 0.15-0.25s for average fielders
2. **Catch probability bands too steep**: Jump from 0.85 → 0.98 with almost no middle ground
3. **Range multipliers too generous**: Elite fielders get significant time bonuses
4. **Route inefficiency penalty too low**: Only 15% max penalty on long plays

## Recommended Changes

### 1. Increase Reaction Times (attributes.py)
```python
# Current: human_min=0.05, human_cap=0.30
# Proposed: human_min=0.10, human_cap=0.40
def get_reaction_time_s(self) -> float:
    return piecewise_logistic_map_inverse(
        self.REACTION_TIME,
        human_min=0.10,   # Elite (was 0.05)
        human_cap=0.40,   # Poor (was 0.30)
        super_cap=0.00    # Perfect (unchanged)
    )
```
**Effect**: Adds ~0.05s to every play, reducing margin by ~0.05s

### 2. Revise Catch Probability Bands (fielding.py)
```python
# Current bands:
# margin >= 1.0: 0.99 (routine)
# margin >= 0.2: 0.98
# margin >= 0.0: 0.85

# Proposed bands (more gradual):
if time_margin >= 1.5:
    probability = 0.98   # Very routine (was 0.99 at 1.0s)
elif time_margin >= 1.0:
    probability = 0.92   # Routine (new band)
elif time_margin >= 0.5:
    probability = 0.85   # Easy catch (new band)
elif time_margin >= 0.2:
    probability = 0.75   # Moderate difficulty (was 0.98)
elif time_margin >= 0.0:
    probability = 0.60   # Challenging (was 0.85)
elif time_margin > -0.15:
    probability = 0.35   # Diving (was 0.42)
elif time_margin > -0.35:
    probability = 0.08   # Spectacular (was 0.10)
else:
    probability = 0.02   # Impossible
```
**Effect**: More variety in catch difficulties, more drops

### 3. Reduce Range Multipliers (fielding.py)
```python
# Current:
# Elite: 1.08, Above avg: 1.03, Below avg: 0.95

# Proposed:
def get_effective_range_multiplier(self) -> float:
    route_efficiency = self.attributes.get_route_efficiency_pct()
    if route_efficiency >= 0.92:
        return 1.03   # Elite (was 1.08)
    elif route_efficiency >= 0.88:
        return 1.00   # Above average (was 1.03)
    else:
        return 0.92   # Below average (was 0.95)
```
**Effect**: Reduces elite fielder advantage

### 4. Increase Route Inefficiency Penalty (fielding.py)
```python
# Current: route_penalty = 1.0 + (1.0 - route_efficiency) * 0.15 (long)
# Proposed: route_penalty = 1.0 + (1.0 - route_efficiency) * 0.30 (long)

# Medium plays:
route_penalty = 1.0 + (1.0 - route_efficiency) * 0.50  # was 0.30

# Long plays:
route_penalty = 1.0 + (1.0 - route_efficiency) * 0.30  # was 0.15
```
**Effect**: Poor route-runners take more time

### 5. Increase Reaction Jitter (fielding.py)
```python
# Current: np.random.normal(0, 0.05)
# Proposed: np.random.normal(0, 0.08)
reaction_jitter = np.random.normal(0, 0.08)  # ±80ms std dev
```
**Effect**: More variability in fielder timing

### 6. Increase Jump Quality Impact (fielding.py)
```python
# Current:
# Poor jump (5%): -10% route efficiency
# Subpar jump (15%): -5%

# Proposed:
# Poor jump (8%): -15% route efficiency
# Subpar jump (17%): -8%
if jump_roll < 0.08:
    jump_modifier = -0.15  # Poor jump (was -0.10)
elif jump_roll < 0.25:
    jump_modifier = -0.08  # Subpar jump (was -0.05)
```
**Effect**: More bad jumps, more difficult plays

## Expected Outcomes

After these changes, expect:
- BABIP: 0.285-0.315 (currently 0.248)
- Fly Out Rate: 38-42% (currently 49.1%)
- More variety in catch probabilities (fewer 0.95 plays)
- More marginal catches (0.50-0.75 probability)
- Average time margins reduced by 0.1-0.2s

## Testing Plan

1. Run validation tests: `python -m batted_ball.validation` (must pass 7/7)
2. Run full game simulation and check:
   - BABIP should be 0.280-0.320
   - K% should remain ~22-25%
   - Hit distribution should match MLB patterns
3. Verify game logs show more variety in catch probabilities

## Implementation Priority

1. **High**: Catch probability bands (#2) - biggest impact on BABIP
2. **Medium**: Reaction times (#1) - consistent impact
3. **Medium**: Route penalties (#4) - helps differentiate fielders
4. **Low**: Range multipliers (#3), Jitter (#5), Jump quality (#6)
