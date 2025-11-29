# Baseball Physics Simulator - AI Developer Guide

**Version**: 1.3.2 | **Last Updated**: 2025-05-29

> **⚠️ PHYSICS-FIRST**: All gameplay emerges from physical parameters (exit velocity, sprint speed, throw times), NOT statistical probabilities. Changes must preserve 7/7 validation tests against MLB data.
>
> **⚠️ TEST WITH MLB DATA**: Use real MLB teams from the database, NOT synthetic `create_test_team()`. The simulation's purpose is modeling real baseball.

## Performance (Rust Acceleration)

Games complete in **~6 seconds** (was 30s) with full physics via Rust backend.

```bash
# Build Rust extension
cd trajectory_rs && maturin build --release && pip install target/wheels/*.whl

# Check availability
python -c "from batted_ball.fast_trajectory import is_rust_available; print(is_rust_available())"
python -c "from batted_ball import is_rust_physics_available; print(is_rust_physics_available())"
```

**Rust modules**: `fast_trajectory.py` (5x fly balls), `fast_ground_ball.py` (22x ground balls), `ground_ball_physics.py`, `ground_ball_interception.py`

## Quick Start

```bash
# PRIMARY TESTING METHOD - Real MLB teams from database
game_simulation.bat → Option 8 → Select teams → 5-10 games

# Physics validation (REQUIRED for physics changes only)
python -m batted_ball.validation  # Must pass 7/7 tests
```

**Never run more than 10 games for testing** - 5-10 games provides sufficient statistical signal.

## Testing Strategy (IMPORTANT)

See `TESTING_STRATEGY.md` for full details. Summary:

| Test Type | Command | When |
|-----------|---------|------|
| **Physics validation** | `python -m batted_ball.validation` | Physics changes (7/7 required) |
| **MLB games** | `game_simulation.bat` → Option 8 → 5-10 games | **ALL other testing** |
| Quick smoke test | `python examples/quick_game_test.py` | Sanity check only |

**DO NOT** use `create_test_team()` for testing. It creates synthetic teams that don't reflect real MLB gameplay.

## Architecture

**Layered Stack** (lower layers never import from higher):
1. **Physics Core**: `constants.py` → `aerodynamics.py` → `integrator.py` → `trajectory.py`
2. **Rust Acceleration**: `fast_trajectory.py`, `fast_ground_ball.py` (parallel physics with Rayon)
3. **Contact/Pitch**: `contact.py`, `pitch.py` (8 pitch types with spin)
4. **Actions**: `at_bat.py`, `fielding.py`, `baserunning.py`
5. **Play/Game**: `play_simulation.py` → `game_simulation.py`
6. **Database**: `database/` (MLB data via pybaseball) - **PRIMARY data source**

**Key Files**:
- `constants.py`: ALL empirical coefficients (MLB Statcast-calibrated) - modify here for physics tuning
- `attributes.py`: 0-100,000 scale → physics via `piecewise_logistic_map()` (85k = elite human cap)
- `validation.py`: 7 benchmark tests - exit velocity, launch angle, altitude, backspin, temperature effects
- `database/`: Real MLB player data - **use this for testing**
- `trajectory_rs/`: Rust library source (PyO3, Rayon) - rebuild after changes

## Critical Conventions

### Coordinate System (Home Plate Origin)
- **X**: Right field (+), Left field (-)
- **Y**: Center field (+), Home plate (-)  
- **Z**: Upward (+)

**Base positions** (feet): Home (0,0), 1B (63.64, 63.64), 2B (0, 127.28), 3B (-63.64, 63.64)

⚠️ **Trajectory uses internal coords** (x=outfield, y=lateral). Use `convert_velocity_trajectory_to_field()` when passing velocities to fielding modules.

### Units (Automatic Conversion)
- **Internal**: SI units (m, m/s, kg) for physics calculations
- **External API**: Baseball units (ft, mph, degrees) for all user-facing code
- Conversions via `MPH_TO_MS`, `FEET_TO_METERS` in constants.py - handled automatically

### API Patterns
```python
# Team access: use plural + index
pitcher = team.pitchers[0]  # ✓ NOT team.pitcher

# AtBatResult.outcome is STRING, PlayOutcome is ENUM
if at_bat_result.outcome == "in_play":  # ✓ String comparison
if play_result.outcome == PlayOutcome.SINGLE:  # ✓ Enum comparison

# Method names
result = simulator.simulate_at_bat()  # ✓ NOT .simulate()

# Rust acceleration (auto-fallback to Python)
from batted_ball import is_rust_physics_available
simulator = GroundBallSimulator(use_rust=True)  # Uses Rust if available
```

## Expected Game Stats (per 9 innings, 2-team combined)

| Metric | Expected Range | Red Flag |
|--------|----------------|----------|
| Runs | 8-10 | < 4 or > 16 |
| Hits | 15-20 | < 10 or > 28 |
| K% | 20-28% | < 15% or > 35% |
| BB% | 8-12% | < 4% or > 18% |
| HR | 2-4 | 0 in 5 games or > 8 |
| BABIP | .280-.320 | < .200 or > .400 |

## Common Bugs & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `'Team' has no attribute 'pitcher'` | Wrong attribute | Use `team.pitchers[0]` |
| Runners not advancing | Margin calc from wrong base | Use `decide_runner_advancement()` |
| 0 runs with many hits | Runner placement order | Get existing runners BEFORE placing batter |
| Fielders running wrong way | Velocity coord mismatch | Use `convert_velocity_trajectory_to_field()` |
| Rust not accelerating | Extension not built | Rebuild: `cd trajectory_rs && maturin build --release` |

## Development Workflow

### For Physics Changes
1. Make change in `constants.py`, `aerodynamics.py`, etc.
2. Run: `python -m batted_ball.validation` (must pass 7/7)
3. Run: `game_simulation.bat` → Option 8 → 5 games with MLB teams
4. Check game log in `game_logs/` for realistic stats

### For Game Logic Changes
1. Make change in `game_simulation.py`, `at_bat.py`, etc.
2. Run: `game_simulation.bat` → Option 8 → 5-10 games
3. Review log output for expected behavior

### For Rust Changes
1. Make changes in `trajectory_rs/src/`
2. Build: `cd trajectory_rs && maturin build --release && pip install target/wheels/*.whl`
3. Test: `python -c "from batted_ball import is_rust_physics_available; print(is_rust_physics_available())"`
4. Run: `game_simulation.bat` → Option 8 → 5 games

### For Bug Fixes
1. Reproduce with MLB teams (5 games)
2. Fix the bug
3. Verify with MLB teams (5 games)

## Git Workflow

**Work directly on `master`** - no feature branches needed.

```bash
# Before committing physics changes:
python -m batted_ball.validation   # Must pass 7/7

# Standard commit flow:
git add <files>
git commit -m "Brief description"
git push origin master
```

## Key Resources

- **Testing strategy**: `TESTING_STRATEGY.md` - How to test properly
- **Full AI guide**: `CLAUDE.md` - Comprehensive reference
- **Performance docs**: `docs/PERFORMANCE_IMPLEMENTATION_PLAN.md` - Rust acceleration details
- **Physics research**: `research/` - Empirical basis for coefficients
- **Game logs**: `game_logs/` - Output from test runs
