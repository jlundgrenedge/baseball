# Baseball Physics Simulator - AI Developer Guide

> **⚠️ PHYSICS-FIRST**: All gameplay emerges from physical parameters (exit velocity, sprint speed, throw times), NOT statistical probabilities. Changes must preserve 7/7 validation tests against MLB data.

## Quick Start

```python
# Simulate a full game
from batted_ball.game_simulation import create_test_team, GameSimulator
home = create_test_team("Home", quality="good")
away = create_test_team("Away", quality="average")
sim = GameSimulator(away, home, verbose=True)
result = sim.simulate_game(num_innings=9)

# Validate physics changes (REQUIRED after any physics modification)
python -m batted_ball.validation  # Must pass 7/7 tests
```

## Architecture

**Layered Stack** (lower layers never import from higher):
1. **Physics Core**: `constants.py` → `aerodynamics.py` → `integrator.py` → `trajectory.py`
2. **Contact/Pitch**: `contact.py`, `pitch.py` (8 pitch types with spin)
3. **Actions**: `at_bat.py`, `fielding.py`, `baserunning.py`
4. **Play/Game**: `play_simulation.py` → `game_simulation.py`
5. **Optional**: `database/` (MLB data via pybaseball), `series_metrics.py`, `ballpark.py`

**Key Files**:
- `constants.py`: ALL empirical coefficients (MLB Statcast-calibrated) - modify here for physics tuning
- `attributes.py`: 0-100,000 scale → physics via `piecewise_logistic_map()` (85k = elite human cap)
- `validation.py`: 7 benchmark tests - exit velocity, launch angle, altitude, backspin, temperature effects
- `fielding.py`: Largest file (1,479 lines) - fielder movement, catching, throwing physics

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

### Correct Imports (Common Mistakes)
```python
# ✓ CORRECT
from batted_ball.game_simulation import create_test_team, GameSimulator, Team
from batted_ball.play_simulation import PlaySimulator, create_standard_defense
from batted_ball.at_bat import AtBatSimulator

# ✗ WRONG - these don't exist in these modules
# from batted_ball.player import create_test_team
# from batted_ball.fielding import create_standard_defense
```

### API Patterns
```python
# Team access: use plural + index
pitcher = team.pitchers[0]  # ✓ NOT team.pitcher

# AtBatResult.outcome is STRING, PlayOutcome is ENUM
if at_bat_result.outcome == "in_play":  # ✓ String comparison
if play_result.outcome == PlayOutcome.SINGLE:  # ✓ Enum comparison

# Method names
result = simulator.simulate_at_bat()  # ✓ NOT .simulate()
```

## Testing & Validation

```bash
python -m batted_ball.validation          # 7 physics benchmarks (MUST pass)
python examples/game_simulation_demo.py   # Full game demo
python test_full_game.py                  # Quick 9-inning test
```

**Expected Game Stats** (per 9 innings): Runs ~9.0, Hits ~17.0, HR ~2.2, BABIP ~.300, K% ~20-25%

## Common Bugs & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| Import errors for `create_test_team` | Wrong module | Use `batted_ball.game_simulation` |
| `'Team' has no attribute 'pitcher'` | Wrong attribute | Use `team.pitchers[0]` |
| Runners not advancing | Margin calc from wrong base | Use `decide_runner_advancement()` |
| 0 runs with many hits | Runner placement order | Get existing runners BEFORE placing batter |
| Fielders running wrong way | Velocity coord mismatch | Use `convert_velocity_trajectory_to_field()` |

## Performance Modes

```python
# Standard: DT=0.001s (accurate, 30-60s per game)
sim = AtBatSimulator(pitcher, hitter)

# Fast: DT=0.002s (2x speedup, <1% accuracy loss)
sim = AtBatSimulator(pitcher, hitter, fast_mode=True)

# UltraFast: 10x speedup for bulk sims
from batted_ball.performance import UltraFastMode
with UltraFastMode():
    sim.simulate_game(num_innings=9)
```

## Adding Features

1. Add physics to appropriate layer module
2. Add coefficients to `constants.py` with MLB data source
3. Run `python -m batted_ball.validation` (7/7 required)
4. Add factory function if needed
5. Document in `docs/` folder

## Git Workflow

**Work directly on `master`** - no feature branches needed. Validate before pushing:

```bash
# Before committing any physics changes:
python -m batted_ball.validation   # Must pass 7/7
python test_full_game.py           # Verify realistic game stats

# Standard commit flow:
git add <files>
git commit -m "Brief description of change"
git push origin master
```

**Commit message format**: Include validation status for physics changes:
```
Adjusted drag coefficient for line drives

- Modified CD_BASE in constants.py
- Validation: 7/7 tests passing
- Source: MLB Statcast 2024 data
```

## Key Resources

- **Full AI guide**: `CLAUDE.md` (comprehensive 1500+ line reference)
- **Physics research**: `research/` folder (empirical basis for coefficients)
- **Examples**: `examples/game_simulation_demo.py`, `examples/basic_simulation.py`
- **Recent docs**: Check `docs/` file dates - newer = current implementation
