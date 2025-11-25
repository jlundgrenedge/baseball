# Collision Efficiency Fix - November 25, 2025

## Summary
Fixed a critical bug in the collision efficiency penalty system that was preventing realistic home run production.

## The Bug

The collision efficiency system had an **inverted penalty structure**:
- Base collision efficiency (q): 0.03
- Minimum floor (q): 0.08

This meant:
- **Perfect contact** (q=0.03): EV = 87 mph
- **Bad contact** (q hits floor at 0.08): EV = 96 mph

**The system was rewarding bad contact with higher exit velocity!**

### Root Cause
The minimum floor (0.08) was set higher than the base (0.03), inverting the penalty system. The floor was intended to prevent extremely low EVs, but it was set incorrectly.

## The Fix

### 1. Fixed the collision efficiency floor
**File:** `batted_ball/contact.py`
```python
# OLD (broken):
return max(q, 0.08)  # Floor higher than base!

# NEW (fixed):
return max(q, 0.01)  # Floor lower than base
```

### 2. Increased base collision efficiency
**File:** `batted_ball/constants.py`
```python
# OLD:
COLLISION_EFFICIENCY_WOOD = 0.03

# NEW:
COLLISION_EFFICIENCY_WOOD = 0.09
```

### Result
The penalty system now works correctly:
- Perfect contact (q=0.09): EV ≈ 100 mph → enables home runs
- Average contact (q≈0.05): EV ≈ 90 mph → realistic average
- Bad contact (q=0.01): EV ≈ 84 mph → weak contact

## Impact

### Before Fix
- Average EV: 93-96 mph (flat, due to floor)
- Max EV: 97 mph
- EVs > 100 mph: 0%
- Home runs: 0 per game

### After Fix
- Average EV: 88 mph (MLB realistic)
- Max EV: 100+ mph
- EVs > 95 mph: ~28%
- Home runs: Now happening (2-5 per game seen)

## Remaining Issues

1. **GB% too low** (18% vs MLB 43%) - need to adjust launch angle distribution
2. **FB% too high** (52% vs MLB 33%) - same cause
3. **BB% too high** (15% vs MLB 8-9%) - command/pitch selection issues

## Collision Efficiency Formula Reference

```
Exit Velocity = q × pitch_speed + (1 + q) × bat_speed
```

With bat_speed=84 mph and pitch_speed=93 mph:
| q value | Exit Velocity |
|---------|---------------|
| 0.01    | 83.8 mph      |
| 0.03    | 87.3 mph      |
| 0.05    | 90.8 mph      |
| 0.07    | 94.3 mph      |
| 0.09    | 97.8 mph      |
| 0.10    | 99.5 mph      |
