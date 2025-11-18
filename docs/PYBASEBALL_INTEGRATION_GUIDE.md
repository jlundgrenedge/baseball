# PyBaseball Integration Guide

**Last Updated**: 2025-11-18
**Module**: `batted_ball.pybaseball_integration`
**Purpose**: Bridge real MLB statistics with physics-based simulation

---

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Stat-to-Attribute Mapping](#stat-to-attribute-mapping)
5. [Creating Players from MLB Data](#creating-players-from-mlb-data)
6. [Creating Teams from MLB Rosters](#creating-teams-from-mlb-rosters)
7. [Advanced Usage](#advanced-usage)
8. [Limitations](#limitations)

---

## Overview

The PyBaseball integration module allows you to:
- **Fetch real MLB player statistics** using the pybaseball package
- **Map MLB stats to physics-based attributes** (0-100,000 scale)
- **Create simulation players** from actual MLB players
- **Simulate games between real MLB teams**

### Key Features
- Percentile-based mapping ensures proper distribution
- Supports both offensive and defensive statistics
- Automatic position-based fielding attribute defaults
- Graceful fallback to league average when data unavailable

---

## Installation

### Prerequisites
```bash
pip install pybaseball pandas
```

### Optional: GPU acceleration
```bash
pip install cupy  # For GPU-accelerated simulations
```

### Verify Installation
```python
from batted_ball import PYBASEBALL_AVAILABLE

if PYBASEBALL_AVAILABLE:
    print("✓ PyBaseball integration ready")
else:
    print("✗ pybaseball not installed")
```

---

## Quick Start

### Example 1: Create a Player from MLB Data
```python
from batted_ball import create_mlb_player

# Create a hitter
judge = create_mlb_player("Aaron Judge", season=2024, role='hitter')
print(f"Bat Speed: {judge.attributes.get_bat_speed_mph():.1f} mph")

# Create a pitcher
cole = create_mlb_player("Gerrit Cole", season=2024, role='pitcher')
print(f"Velocity: {cole.get_pitch_velocity_mph():.1f} mph")
```

### Example 2: Simulate a Matchup
```python
from batted_ball import AtBatSimulator, create_mlb_player

pitcher = create_mlb_player("Shohei Ohtani", season=2024, role='pitcher')
hitter = create_mlb_player("Aaron Judge", season=2024, role='hitter')

sim = AtBatSimulator(pitcher, hitter)
result = sim.simulate_at_bat()

print(f"Outcome: {result.outcome}")
```

### Example 3: Simulate a Game Between Real Teams
```python
from batted_ball import create_team_from_mlb_roster, GameSimulator

# Define Yankees roster
yankees_hitters = [
    ("Juan Soto", "RF"),
    ("Aaron Judge", "CF"),
    ("Giancarlo Stanton", "DH"),
    ("Anthony Rizzo", "1B"),
    ("Gleyber Torres", "2B"),
    ("Anthony Volpe", "SS"),
    ("Jazz Chisholm", "3B"),
    ("Alex Verdugo", "LF"),
    ("Jose Trevino", "C"),
]

yankees_pitchers = [
    ("Gerrit Cole", "starter"),
    ("Carlos Rodon", "starter"),
    ("Clay Holmes", "reliever"),
]

# Create team
yankees = create_team_from_mlb_roster(
    "Yankees",
    yankees_hitters,
    yankees_pitchers,
    season=2024
)

# Similar for opponent...
# dodgers = create_team_from_mlb_roster(...)

# Simulate game
sim = GameSimulator(yankees, dodgers, verbose=True)
final = sim.simulate_game(num_innings=9)

print(f"Final Score: {final.away_score} - {final.home_score}")
```

---

## Stat-to-Attribute Mapping

### Mapping Philosophy
All mappings use **percentile-based scaling**:
- **50th percentile (league average) → 50,000**
- **95th percentile (elite) → 85,000**
- **99th percentile (superstar) → 95,000**
- **5th percentile (poor) → 15,000**

This ensures realistic attribute distributions that match MLB performance curves.

### Hitter Stat Mappings

| MLB Statistic | Maps To | Attribute |
|--------------|---------|-----------|
| Exit Velocity (avg) | BAT_SPEED | Direct correlation |
| Hard Hit % | BAT_SPEED, BARREL_ACCURACY | Contributes to both |
| Barrel % | BARREL_ACCURACY | Direct correlation |
| K% | ZONE_DISCERNMENT (inverse) | Lower K% = better |
| BB% | ZONE_DISCERNMENT | Higher BB% = better |
| Launch Angle (avg) | ATTACK_ANGLE_CONTROL | Direct correlation |
| Pull% / Oppo% | SPRAY_TENDENCY | Determines pull/oppo tendency |

**Example Calculation:**
```python
# Aaron Judge 2024: Exit Velocity = 95 mph (95th percentile)
# Mapping: 95th percentile → 85,000 attribute points
# Result: BAT_SPEED = 85,000
# Physics: Bat speed = 78.5 mph (elite)
```

### Pitcher Stat Mappings

| MLB Statistic | Maps To | Attribute |
|--------------|---------|-----------|
| Fastball Velocity | RAW_VELOCITY_CAP | Direct correlation |
| Spin Rate | SPIN_RATE_CAP | Direct correlation |
| K% | DECEPTION, SPIN_EFFICIENCY | Higher K% = better |
| Whiff% | DECEPTION | Contributes to deception |
| BB% | COMMAND, CONTROL (inverse) | Lower BB% = better |
| IP / Role | STAMINA | Starters higher than relievers |

**Example Calculation:**
```python
# Gerrit Cole 2024: Fastball = 97 mph (90th percentile)
# Mapping: 90th percentile → 78,000 attribute points
# Result: RAW_VELOCITY_CAP = 78,000
# Physics: Velocity = 96.8 mph (very good)
```

### Fielder Stat Mappings

| MLB Statistic | Maps To | Attribute |
|--------------|---------|-----------|
| Sprint Speed | TOP_SPRINT_SPEED | Direct correlation |
| Outs Above Average | REACTION_TIME, ROUTE_EFFICIENCY, FIELDING_SECURE | Contributes to all |
| Position | ARM_STRENGTH | Position-based defaults |

**Position-Based Arm Strength Defaults:**
- **Strongest**: RF (70,000), SS/3B (65,000)
- **Average**: CF/C (60,000), 2B/LF (50,000)
- **Weakest**: 1B (40,000), P (45,000)

---

## Creating Players from MLB Data

### Function: `create_mlb_player()`

```python
def create_mlb_player(
    player_name: str,
    season: int = 2024,
    role: str = 'hitter'
) -> Union[Hitter, Pitcher]
```

**Parameters:**
- `player_name` (str): Full name (e.g., "Aaron Judge")
- `season` (int): MLB season year (default: 2024)
- `role` (str): 'hitter', 'pitcher', 'starter', or 'reliever'

**Returns:**
- `Hitter` if role='hitter'
- `Pitcher` if role='pitcher'/'starter'/'reliever'

**Usage:**
```python
from batted_ball import create_mlb_player

# Create hitter
judge = create_mlb_player("Aaron Judge", season=2024, role='hitter')

# Create starting pitcher
cole = create_mlb_player("Gerrit Cole", season=2024, role='starter')

# Create reliever
hader = create_mlb_player("Josh Hader", season=2024, role='reliever')
```

### Low-Level Functions

For more control, use the lower-level functions:

```python
from batted_ball import (
    fetch_player_batting_stats,
    fetch_player_pitching_stats,
    create_hitter_from_mlb_stats,
    create_pitcher_from_mlb_stats
)

# Fetch stats manually
stats = fetch_player_batting_stats("Aaron Judge", season=2024)

# Inspect the raw stats
print(stats)
# {'exit_velocity_avg': 95.2,
#  'exit_velocity_avg_percentile': 95.0,
#  'barrel_pct': 18.4,
#  'barrel_pct_percentile': 98.0,
#  ...}

# Create player from stats
judge = create_hitter_from_mlb_stats("Aaron Judge", stats, position='RF')
```

---

## Creating Teams from MLB Rosters

### Function: `create_team_from_mlb_roster()`

```python
def create_team_from_mlb_roster(
    team_name: str,
    roster_hitters: List[Tuple[str, str]],
    roster_pitchers: List[Tuple[str, str]],
    season: int = 2024
) -> Team
```

**Parameters:**
- `team_name` (str): Team name
- `roster_hitters` (list): List of (player_name, position) tuples
- `roster_pitchers` (list): List of (player_name, role) tuples
- `season` (int): MLB season year

**Returns:**
- `Team` object ready for simulation

**Example:**
```python
from batted_ball import create_team_from_mlb_roster, GameSimulator

# Define Yankees 2024 roster
yankees_hitters = [
    ("Juan Soto", "RF"),
    ("Aaron Judge", "CF"),
    ("Giancarlo Stanton", "DH"),
    ("Anthony Rizzo", "1B"),
    ("Gleyber Torres", "2B"),
    ("Anthony Volpe", "SS"),
    ("Jazz Chisholm", "3B"),
    ("Alex Verdugo", "LF"),
    ("Jose Trevino", "C"),
]

yankees_pitchers = [
    ("Gerrit Cole", "starter"),
    ("Carlos Rodon", "starter"),
    ("Nestor Cortes", "starter"),
    ("Clay Holmes", "reliever"),
    ("Luke Weaver", "reliever"),
]

yankees = create_team_from_mlb_roster(
    "New York Yankees",
    yankees_hitters,
    yankees_pitchers,
    season=2024
)

# Create opponent team
# dodgers = create_team_from_mlb_roster(...)

# Simulate game
simulator = GameSimulator(yankees, dodgers, verbose=True)
final_state = simulator.simulate_game(num_innings=9)

print(f"Final Score: {final_state.away_score} - {final_state.home_score}")
```

---

## Advanced Usage

### Custom Stat Mappings

You can manually adjust stat-to-attribute mappings:

```python
from batted_ball.pybaseball_integration import (
    map_hitter_stats_to_attributes,
    create_hitter_from_mlb_stats
)

# Fetch stats
stats = fetch_player_batting_stats("Player Name", 2024)

# Manually adjust stats before mapping
stats['exit_velocity_avg_percentile'] = 95.0  # Boost to elite
stats['k_pct_percentile'] = 90.0  # Improve discipline

# Create player with adjusted stats
player = create_hitter_from_mlb_stats("Player Name", stats)
```

### Percentile-Based Analysis

```python
from batted_ball.pybaseball_integration import (
    stat_to_percentile,
    percentile_to_attribute
)

# Get league data (simplified example)
league_exit_velos = [85, 87, 89, 90, 92, 95, 98]  # Example data

# Calculate player's percentile
player_ev = 93
percentile = stat_to_percentile(player_ev, league_exit_velos)
print(f"Exit Velocity Percentile: {percentile:.1f}")

# Map to attribute
attribute = percentile_to_attribute(percentile)
print(f"BAT_SPEED Attribute: {attribute:.0f}")
```

### Mixing Real and Generated Players

```python
from batted_ball import create_mlb_player, create_test_team

# Real MLB player
judge = create_mlb_player("Aaron Judge", 2024, 'hitter')

# Generic team
team = create_test_team("Team", "average")

# Replace one player with real MLB player
team.hitters[3] = judge  # Replace cleanup hitter
```

---

## Limitations

### 1. Data Availability
- **pybaseball** requires internet connection to fetch data
- Some advanced metrics may not be available for all players
- Historical data may be incomplete for older seasons

**Workaround:**
```python
try:
    stats = fetch_player_batting_stats("Player", 2024)
    if stats is None:
        stats = {}  # Falls back to league average
    player = create_hitter_from_mlb_stats("Player", stats)
except Exception as e:
    print(f"Error: {e}")
    # Use generic player instead
    from batted_ball.attributes import create_power_hitter
    from batted_ball import Hitter
    player = Hitter("Player", create_power_hitter("good"))
```

### 2. Statcast Metrics Not Always Available
- Exit velocity, barrel %, launch angle require Statcast data
- Pre-2015 seasons may lack these metrics
- Minor league players not included

**Workaround:** Use FanGraphs data which has broader coverage:
```python
# The module automatically handles missing Statcast data
# by using available statistics and league averages
```

### 3. Mapping Approximations
- Some attributes (e.g., `PITCH_PLANE_MATCH`, `IMPACT_SPIN_GAIN`) are hard to measure from public stats
- These use defaults or indirect correlations

**Current Approach:**
- Well-measured stats (velocity, K%, BB%) map directly
- Indirect stats use league averages or correlations
- System is designed to be conservative (favor realism over extremes)

### 4. Seasonal Variance
- Player performance varies within seasons
- Injuries, hot streaks, slumps not captured
- Stats reflect full-season averages

**Consideration:**
```python
# For playoff simulations, consider using postseason stats
stats = fetch_player_batting_stats("Player", season=2024)
# Manually adjust based on recent performance if needed
stats['exit_velocity_avg_percentile'] += 5  # Hot streak adjustment
```

### 5. Position Changes
- Players who change positions mid-season
- Utility players with multiple positions

**Workaround:**
```python
# Specify primary position when creating player
player = create_hitter_from_mlb_stats("Utility Player", stats, position='2B')
```

---

## Troubleshooting

### Import Error: pybaseball not found
```bash
pip install pybaseball pandas
```

### Slow Data Fetching
- First fetch caches data locally
- Subsequent queries are faster
- Consider using `--quiet` flag in examples

### Player Not Found
```python
# Check spelling
stats = fetch_player_batting_stats("Aaron Judge", 2024)  # Correct
stats = fetch_player_batting_stats("Aron Juge", 2024)   # Returns None

# Handle missing data gracefully
if stats is None:
    print("Player not found, using defaults")
    stats = {}
```

### Percentile Calculation Issues
```python
# Ensure league data is not empty
league_values = [v for v in data if not np.isnan(v)]
percentile = stat_to_percentile(player_value, league_values)
```

---

## Example Scripts

See `examples/simulate_mlb_teams.py` for complete working examples:
- Yankees vs Dodgers simulation
- Individual player matchups
- Custom roster creation

**Run the example:**
```bash
cd /home/user/baseball
python examples/simulate_mlb_teams.py
```

---

## Future Enhancements

Potential improvements to the integration:
1. **Real-time data fetching** during season
2. **Player injury status** integration
3. **Park factors** from MLB stadiums
4. **Weather data** for game simulations
5. **Advanced fielding metrics** (DRS, UZR)
6. **Pitch mix modeling** from actual pitch usage

---

## Summary

The PyBaseball integration provides a seamless bridge between real MLB statistics and the physics-based simulation engine. By using percentile-based mapping, it ensures that real player capabilities are accurately represented in the simulation while maintaining the physics-first approach of the engine.

**Key Takeaways:**
- ✓ Fetch real MLB stats with `fetch_player_*_stats()`
- ✓ Create players with `create_mlb_player()` or `create_*_from_mlb_stats()`
- ✓ Build teams with `create_team_from_mlb_roster()`
- ✓ Simulate games between actual MLB teams
- ✓ Percentile-based mapping ensures realistic distributions
- ✓ Graceful fallback to defaults when data unavailable

---

**Documentation Version**: 1.0
**Last Updated**: 2025-11-18
**Module**: `batted_ball.pybaseball_integration`
