# Attribute System Unification Status

## Overview
This document tracks the unification of the attribute system from the legacy 100-point scale to the physics-first 100,000-point scale across the codebase.

## Completed ✅

### Fielder Class (`batted_ball/fielding.py`)
**Status**: FULLY UNIFIED

**Changes Made**:
1. **Constructor Simplified**:
   - Removed all legacy 0-100 parameters (sprint_speed, acceleration, etc.)
   - Made `attributes: FielderAttributes` **required** (not Optional)
   - Renamed `attributes_v2` to `attributes` throughout
   - Removed all fallback logic

2. **Methods Updated** (removed all `if self.attributes_v2:` checks):
   - `get_acceleration_fps2()` - now just returns `self.attributes.get_acceleration_fps2()`
   - `get_sprint_speed_fps_statcast()` - now just returns `self.attributes.get_top_sprint_speed_fps()`
   - `get_first_step_time()` - now just returns `self.attributes.get_reaction_time_s()`
   - `get_route_efficiency()` - now just returns `self.attributes.get_route_efficiency_pct()`
   - `get_throw_velocity_mph()` - now just returns `self.attributes.get_arm_strength_mph()`
   - `get_transfer_time_seconds()` - now just returns `self.attributes.get_transfer_time_s()`
   - `get_throwing_accuracy_std_degrees()` - simplified to use only attributes
   - `get_effective_range_multiplier()` - simplified to use route efficiency from attributes
   - `calculate_catch_probability()` - removed fallback for `CATCH_PROB_BASE`

3. **Factory Functions Updated**:
   - `create_elite_fielder()` - uses `attributes` parameter
   - `create_average_fielder()` - uses `attributes` parameter
   - `create_poor_fielder()` - uses `attributes` parameter

4. **simulate_fielder_throw()**: Removed legacy fallback, uses only `fielder.attributes`

### Coordinate System (`batted_ball/trajectory.py`)
**Status**: FULLY UNIFIED

Added helper function `convert_position_trajectory_to_field()` to complement velocity conversion.

## Completed ✅ (Part 2)

### Pitcher Class (`batted_ball/player.py`)
**Status**: FULLY UNIFIED

**Changes Made**:
1. **Constructor Simplified**:
   - Removed all legacy 0-100 parameters (velocity, spin_rate, command, control, stamina, etc.)
   - Made `attributes: PitcherAttributes` **required** (not Optional)
   - Renamed `attributes_v2` to `attributes` throughout
   - Only kept `arm_slot` and `pitch_arsenal` for mechanical/tactical variety

2. **Methods Updated** (removed all fallback logic):
   - `get_pitch_velocity_mph()` - now uses only `self.attributes.get_raw_velocity_mph()`
   - `get_pitch_spin_rpm()` - now uses only `self.attributes.get_spin_rate_rpm()`
   - `get_command_error_inches()` - simplified (uses default for now, TODO: add to attributes)
   - `throw_pitch()` - simplified, stamina degradation implicit in velocity/spin methods
   - `__repr__()` - updated to show actual physical values

### Hitter Class (`batted_ball/player.py`)
**Status**: FULLY UNIFIED

**Changes Made**:
1. **Constructor Simplified**:
   - Removed all legacy parameters (bat_speed, swing_path_angle, barrel_accuracy, etc.)
   - Made `attributes: HitterAttributes` **required** (not Optional)
   - Renamed `attributes_v2` to `attributes` throughout
   - Kept `zone_discipline` and `swing_decision_aggressiveness` as simple 0-100 (TODO: move to attributes later)

2. **Methods Updated** (removed all fallback logic):
   - `get_bat_speed_mph()` - now just returns `self.attributes.get_bat_speed_mph()`
   - `get_swing_path_angle_deg()` - uses `self.attributes.get_attack_angle_mean/variance_deg()`
   - `get_contact_point_offset()` - uses `self.attributes.get_barrel_accuracy_mm()`
   - `get_timing_error()` - uses `self.attributes.get_timing_precision_ms()`

## Dependent Files Updated ✅

### `game_simulation.py`
**Status**: FULLY UPDATED

**Changes Made**:
- Line 722-730: Pitcher creation - changed `attributes_v2=` to `attributes=`
- Line 768-778: Hitter creation - changed `attributes_v2=` to `attributes=`
- Updated all attribute access to use new names

### Tests and Examples
**Files to Check**:
- `test_coordinate_fix.py` - uses `create_average_fielder()` ✅ (already compatible)
- `examples/*.py` - any files creating Pitchers/Hitters/Fielders
- `tests/*.py` - unit tests may have hard-coded legacy attributes

## Migration Strategy

### Step 1: Complete Pitcher Unification
1. Update `Pitcher.__init__()` to require `attributes`
2. Update all Pitcher methods to remove fallbacks
3. Update `game_simulation.py` Pitcher creation
4. Test with existing game simulations

### Step 2: Complete Hitter Unification
1. Update `Hitter.__init__()` to require `attributes`
2. Update all Hitter methods to remove fallbacks
3. Update `game_simulation.py` Hitter creation
4. Test with existing game simulations

### Step 3: Clean Up and Document
1. Remove any remaining fallback logic
2. Update docstrings to reflect 0-100,000 scale only
3. Update README and copilot instructions
4. Run full test suite

## Benefits of Unification

1. **Single Source of Truth**: Only one attribute system to maintain
2. **Physics-First**: All attributes map directly to physical units
3. **Cleaner Code**: No more `if attributes_v2:` checks everywhere
4. **Better Type Safety**: Required parameters catch errors at construction
5. **Easier to Understand**: One clear system vs. two competing systems

## Breaking Changes

### For External Users:
- Can no longer create Fielders with legacy 0-100 parameters
- Must use factory functions or create FielderAttributes manually
- Same will apply to Pitcher/Hitter when unified

### Migration Path:
```python
# Old (no longer works):
fielder = Fielder(name="SS", position="infield", sprint_speed=80, arm_strength=70)

# New (required):
from batted_ball.attributes import create_average_fielder
attributes = create_average_fielder("good")
fielder = Fielder(name="SS", position="infield", attributes=attributes)

# Or use factory function directly:
fielder = create_average_fielder("SS", "infield", "good")
```

## Testing Checklist

- [x] Fielder creation with factory functions
- [x] Fielder methods return correct physical values
- [x] Coordinate system conversions work
- [ ] Pitcher creation and methods
- [ ] Hitter creation and methods
- [ ] Full game simulation runs
- [ ] No regression in game outcomes
