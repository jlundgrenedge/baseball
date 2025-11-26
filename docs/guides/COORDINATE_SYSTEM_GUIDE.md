# Coordinate System Quick Reference

## The Two Systems (Must Match!)

### TRAJECTORY SYSTEM (Physics / Integrator)
Used in: `integrator.py`, `aerodynamics.py`, `trajectory.py` calculations

```
      LEFT FIELD
           ↑ Y-axis (lateral, positive = left field)
           |
           |
CENTER →←  HOME  (0,0)
     FIELD |
           |    X-axis (positive = toward outfield/center field)
           ↓
      RIGHT FIELD
```

- **X-axis**: `+` toward outfield/center field, `-` toward home
- **Y-axis**: `+` left field, `-` right field  
- **Z-axis**: `+` up, `-` down

### FIELD SYSTEM (Positions / Fielding)
Used in: `field_layout.py`, `fielding.py`, `ground_ball_*.py`, all fielder positions

```
         LEFT FIELD (negative X)
              ↑ Y-axis
         3B   |   SS
              |
HOME (0,0) ←--+--→ 1B (positive X = RIGHT FIELD)
     Pitcher  |
        at    |
     (0,60.5)|
              ↓
           ...toward 1B
```

- **X-axis**: `+` right field, `-` left field
- **Y-axis**: `+` toward center field (outfield), `-` toward home
- **Z-axis**: `+` up, `-` down

## Converting Between Systems

### Position Conversion (from Trajectory to Field)
```python
from batted_ball.trajectory import BattedBallResult

# In BattedBallResult._calculate_results():
field_x = -trajectory_y  # Negate Y for right-hand coord system
field_y = trajectory_x   # X becomes the forward direction
field_z = trajectory_z   # Z unchanged
```

### Velocity Conversion (from Trajectory to Field)
```python
from batted_ball.trajectory import convert_velocity_trajectory_to_field

# At entry point to ground ball/fielding calculations:
vx_field, vy_field, vz_field = convert_velocity_trajectory_to_field(
    vx_traj, vy_traj, vz_traj
)

# Mathematically:
vx_field = -vy_traj  # Negate Y for right-hand system
vy_field = vx_traj   # Outfield velocity becomes forward
vz_field = vz_traj   # Vertical unchanged
```

## Where Conversions Happen

| Module | Data | Conversion Point | Status |
|--------|------|------------------|--------|
| `trajectory.py` | Landing position | `_calculate_results()` | ✓ Already done |
| `trajectory.py` | Velocity to field | New function `convert_velocity_trajectory_to_field()` | ✓ Added |
| `ground_ball_interception.py` | Velocity for interception | `find_best_interception()` entry | ✓ Fixed |
| `ground_ball_interception.py` | Velocity for trajectory viz | `get_ground_ball_trajectory_points()` | ✓ Fixed |
| `ground_ball_physics.py` | Velocity for rolling | `simulate_from_trajectory()` | ✓ Fixed |
| `outfield_interception.py` | Velocity for air catch | `find_best_interception_trajectory()` | ✓ Already correct |

## Important Rules

1. **NEVER mix coordinate systems**
   - If you use field positions, use field velocities
   - If you use trajectory velocities, use trajectory positions
   - Convert at module boundaries if needed

2. **Convert at entry points**
   - When a module receives data from another system, convert immediately
   - Don't mix systems within calculation logic

3. **Document coordinate system**
   - Every module's docstring should state which system it uses
   - Every function that converts should be explicit about it

4. **Test with specific scenarios**
   - Ground ball up middle: should have zero X-velocity
   - Ground ball to left: should have negative X-velocity
   - Ground ball to right: should have positive X-velocity

## Testing Scenarios

### Scenario 1: Hit up the middle
```
Trajectory velocity: (vx=+25, vy=0, vz=-5)  m/s
  ↓ Convert
Field velocity: (vx=0, vy=+25, vz=-5)  m/s
  ✓ Correct: no lateral component, straight forward
```

### Scenario 2: Hit to left field  
```
Trajectory velocity: (vx=+20, vy=+10, vz=-4)  m/s
  ↓ Convert
Field velocity: (vx=-10, vy=+20, vz=-4)  m/s
  ✓ Correct: negative X (left field), positive Y (forward)
```

### Scenario 3: Hit to right field
```
Trajectory velocity: (vx=+20, vy=-10, vz=-4)  m/s
  ↓ Convert
Field velocity: (vx=+10, vy=+20, vz=-4)  m/s
  ✓ Correct: positive X (right field), positive Y (forward)
```

## Common Mistakes

❌ **WRONG**: Using trajectory velocity directly with field positions
```python
# DON'T DO THIS
field_pos = (field_x, field_y)  # in field coords
traj_vel = (vx_traj, vy_traj)   # in trajectory coords
# Now using them together = 90° rotation!
```

✓ **RIGHT**: Convert velocity to field coordinates first
```python
# DO THIS
field_pos = (field_x, field_y)  # in field coords
field_vel = convert_velocity_trajectory_to_field(vx_traj, vy_traj, vz_traj)
# Now both in same coordinate system!
```

## References

- `COORDINATE_SYSTEM_ANALYSIS.md` - Detailed analysis of the bug
- `COORDINATE_SYSTEM_FIX_REPORT.md` - Implementation details
- `BEFORE_AND_AFTER.md` - Real examples of the fix
- Source: `batted_ball/trajectory.py` - `convert_velocity_trajectory_to_field()` function
