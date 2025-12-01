# Coordinate Systems in the Baseball Simulator

This document explains the two coordinate systems used in the baseball physics simulator and how they interact.

## Overview

The simulator uses **two different coordinate systems** that serve different purposes:

1. **Trajectory/Physics Coordinates** - Used for physics calculations (aerodynamics, trajectory integration)
2. **Field Coordinates** - Used for field layout, fielder positions, and ballpark dimensions

Understanding these systems is critical when working with spray angles, landing positions, and fence lookups.

---

## Trajectory/Physics Coordinate System

Used in: `integrator.py`, `ev_la_distribution.py`, `trajectory.py` (internal calculations)

| Axis | Direction |
|------|-----------|
| **X** | Toward center field (outfield direction) |
| **Y** | Lateral - **positive = LEFT field** |
| **Z** | Vertical (up) |

### Spray Angle Convention (Physics)

| Spray Angle | Direction | Description |
|-------------|-----------|-------------|
| **Positive (+)** | LEFT field | Pull side for right-handed hitter |
| **Zero (0)** | CENTER field | Straight away |
| **Negative (-)** | RIGHT field | Opposite field for right-handed hitter |

**Example**: A spray angle of `+30°` in physics coordinates sends the ball toward LEFT field.

### Where This Convention Is Used

- `get_spray_angle_for_launch_angle()` in `ev_la_distribution.py`
- `create_initial_state()` in `integrator.py`
- Input parameter `spray_angle` in `BattedBallSimulator.simulate()`

---

## Field Coordinate System

Used in: `field_layout.py`, `ballpark.py`, `play_simulation.py`, `hit_handler.py`

| Axis | Direction |
|------|-----------|
| **X** | Lateral - **positive = RIGHT field, negative = LEFT field** |
| **Y** | Toward center field (outfield direction) |
| **Z** | Vertical (up) |

### Spray Angle Convention (Field/Ballpark)

| Spray Angle | Direction | Description |
|-------------|-----------|-------------|
| **Negative (-)** | LEFT field | Green Monster at Fenway is at -45° |
| **Zero (0)** | CENTER field | Straight away |
| **Positive (+)** | RIGHT field | Right field line is at +45° |

**Example**: A spray angle of `-45°` in field coordinates represents the left field foul line.

### Where This Convention Is Used

- `BattedBallResult.spray_angle_landing`
- `BattedBallResult.landing_x` and `landing_y`
- `ballpark.py` fence profiles (e.g., Green Monster at -45°)
- `get_fence_at_angle()` in `BallparkDimensions`
- `get_nearest_fielder_position()` in `FieldLayout`

---

## Coordinate Conversion

The conversion happens automatically in `trajectory.py` when calculating `BattedBallResult`:

```python
# From trajectory.py _calculate_results():

# Trajectory coords (x=outfield, y=lateral left+) → Field coords (x=lateral right+, y=outfield)
self.landing_x = -landing_pos[1] * METERS_TO_FEET  # Negate Y for field X
self.landing_y = landing_pos[0] * METERS_TO_FEET   # Trajectory X becomes field Y

# Spray angle in FIELD convention (negative = left, positive = right)
self.spray_angle_landing = np.rad2deg(np.arctan2(self.landing_x, self.landing_y))
```

### Conversion Summary

| Trajectory | Field | Notes |
|------------|-------|-------|
| `traj_x` (toward outfield) | `field_y` (toward center) | Direct mapping |
| `traj_y` (left field +) | `-field_x` (right field +) | Sign flip! |
| `traj_z` (up) | `field_z` (up) | Same |

---

## Practical Examples

### Example 1: Hit to Left Field

```python
# Input (physics convention)
spray_angle = +30.0  # Positive = left field in physics

# After trajectory simulation, output (field convention):
landing_x = -210.6   # Negative = left field in field coords
landing_y = 330.8    # Toward outfield
spray_angle_landing = -32.5  # Negative = left field in field convention

# Fence lookup works correctly:
fenway.get_fence_at_angle(-32.5)  # Gets left-center fence, near Green Monster
```

### Example 2: Hit to Right Field

```python
# Input (physics convention)
spray_angle = -30.0  # Negative = right field in physics

# After trajectory simulation, output (field convention):
landing_x = +210.6   # Positive = right field in field coords
landing_y = 330.8    # Toward outfield
spray_angle_landing = +32.5  # Positive = right field in field convention

# Fence lookup works correctly:
fenway.get_fence_at_angle(+32.5)  # Gets right-center fence (shorter, lower)
```

---

## Ballpark Fence Profiles

All fence profiles in `ballpark.py` use the **field convention**:

```python
# Fenway Park fence profile
{
    -45.0:  (309, 37),  # LEFT FIELD LINE - Green Monster (37 ft wall!)
    -33.75: (327, 37),  # Left-center
    -22.5:  (345, 20),  # Left-center
    0.0:    (388, 10),  # CENTER FIELD
    22.5:   (378, 5),   # Right-center
    45.0:   (299, 5),   # RIGHT FIELD LINE - Pesky Pole
}
```

---

## Key Files Reference

| File | Coordinate System | Key Functions/Classes |
|------|-------------------|----------------------|
| `integrator.py` | Trajectory | `create_initial_state()` |
| `ev_la_distribution.py` | Trajectory | `get_spray_angle_for_launch_angle()` |
| `trajectory.py` | Both (converts) | `BattedBallResult`, `BattedBallSimulator` |
| `field_layout.py` | Field | `FieldPosition`, `FieldLayout` |
| `ballpark.py` | Field | `BallparkDimensions`, `get_fence_at_angle()` |
| `play_simulation.py` | Field | Calculates spray from field coords |
| `hit_handler.py` | Field | Calculates spray from field coords |

---

## Common Pitfalls

### ❌ Wrong: Passing physics spray angle directly to ballpark

```python
# DON'T DO THIS - physics spray has opposite sign convention!
spray_from_physics = +30.0  # Left field in physics
fence = ballpark.get_fence_at_angle(spray_from_physics)  # WRONG - gets RF fence!
```

### ✅ Correct: Use spray_angle_landing or recalculate from field coords

```python
# Option 1: Use the converted value from BattedBallResult
fence = ballpark.get_fence_at_angle(result.spray_angle_landing)  # Correct!

# Option 2: Calculate from field coordinates
spray = np.arctan2(ball_position.x, ball_position.y) * 180.0 / np.pi
fence = ballpark.get_fence_at_angle(spray)  # Correct!
```

---

## Bug Fix History

**November 2025**: Fixed coordinate mismatch where `spray_angle_landing` was calculated using trajectory coordinates instead of field coordinates. This caused left field hits to look up right field fence dimensions and vice versa.

The fix in `trajectory.py`:
```python
# Before (wrong - trajectory coords)
self.spray_angle_landing = np.rad2deg(np.arctan2(landing_pos[1], landing_pos[0]))

# After (correct - field coords)  
self.spray_angle_landing = np.rad2deg(np.arctan2(self.landing_x, self.landing_y))
```
