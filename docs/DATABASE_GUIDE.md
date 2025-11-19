# MLB Team Database Guide

**Last Updated**: 2025-11-19

This guide explains how to use the MLB team database system to fetch real player statistics from pybaseball, convert them to game attributes, and use them in simulations.

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Database Architecture](#database-architecture)
4. [CLI Tools](#cli-tools)
5. [Python API](#python-api)
6. [Stat Conversion](#stat-conversion)
7. [Examples](#examples)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The database system provides:
- **Automatic fetching** of MLB player stats using pybaseball
- **Smart conversion** from MLB stats to game attributes (0-100,000 scale)
- **SQLite storage** for fast access without re-scraping
- **Team loading** for game simulations

### Benefits

✅ **No more manual data entry** - Automatically fetch real MLB data
✅ **Consistent attributes** - All players rated on same 0-100k scale
✅ **Fast simulations** - Load teams from database instantly
✅ **Historical seasons** - Store multiple seasons of data
✅ **Accurate ratings** - Percentile-based conversion from real stats

---

## Quick Start

### 1. Install Dependencies

```bash
pip install numpy scipy matplotlib pandas pybaseball numba
```

### 2. Add Your First Team

```bash
# Add the 2024 New York Yankees
python manage_teams.py add NYY 2024

# Add multiple teams at once
python manage_teams.py add-multiple 2024 NYY LAD BOS HOU ATL
```

### 3. List Teams in Database

```bash
python manage_teams.py list
```

### 4. Simulate a Matchup

```bash
python examples/simulate_mlb_matchup.py "New York Yankees" "Los Angeles Dodgers" 2024
```

---

## Database Architecture

### Schema

The database uses SQLite with 4 main tables:

#### **teams**
- `team_id` (primary key)
- `team_name` (e.g., "New York Yankees")
- `team_abbr` (e.g., "NYY")
- `season` (e.g., 2024)
- `league`, `division`

#### **pitchers**
- `pitcher_id` (primary key)
- `player_name`
- **Game attributes** (0-100k scale):
  - `velocity`, `command`, `stamina`, `movement`, `repertoire`
- **MLB statistics** (source data):
  - `era`, `whip`, `k_per_9`, `bb_per_9`, `avg_fastball_velo`, etc.

#### **hitters**
- `hitter_id` (primary key)
- `player_name`
- **Game attributes** (0-100k scale):
  - `contact`, `power`, `discipline`, `speed`
- **MLB statistics** (source data):
  - `batting_avg`, `ops`, `home_runs`, `avg_exit_velo`, `barrel_pct`, etc.

#### **team_rosters**
- Links players to teams
- `batting_order` for hitters
- `is_starter` for pitchers

### File Structure

```
batted_ball/
├── database/
│   ├── __init__.py
│   ├── db_schema.py          # Database schema definition
│   ├── stats_converter.py    # MLB stats → game attributes
│   ├── pybaseball_fetcher.py # Fetch data from pybaseball
│   ├── team_database.py      # Database operations (CRUD)
│   └── team_loader.py        # Load teams for simulations
manage_teams.py               # CLI tool for database management
examples/
└── simulate_mlb_matchup.py   # Example: simulate games from database
```

---

## CLI Tools

### `manage_teams.py`

Command-line interface for managing the team database.

#### Add a Team

```bash
python manage_teams.py add <TEAM_ABBR> <SEASON> [options]

# Examples:
python manage_teams.py add NYY 2024
python manage_teams.py add LAD 2023 --overwrite
python manage_teams.py add BOS 2024 --min-innings 15 --min-at-bats 40
```

**Options:**
- `--min-innings <N>` - Minimum innings pitched for pitchers (default: 20.0)
- `--min-at-bats <N>` - Minimum at-bats for hitters (default: 50)
- `--overwrite` - Overwrite existing team data
- `--db <PATH>` - Database file path (default: baseball_teams.db)

#### Add Multiple Teams

```bash
python manage_teams.py add-multiple <SEASON> <TEAM1> <TEAM2> ... [options]

# Example: Add all AL East teams for 2024
python manage_teams.py add-multiple 2024 NYY BOS TB TOR BAL
```

#### List Teams

```bash
python manage_teams.py list [options]

# List all teams
python manage_teams.py list

# List only 2024 teams
python manage_teams.py list --season 2024
```

#### Delete a Team

```bash
python manage_teams.py delete "<TEAM_NAME>" <SEASON>

# Example:
python manage_teams.py delete "New York Yankees" 2024
```

#### Show Available Teams

```bash
python manage_teams.py show-teams
```

Displays all 30 MLB teams with abbreviations.

---

## Python API

### Fetching and Storing Teams

```python
from batted_ball.database import TeamDatabase

# Open database
db = TeamDatabase("baseball_teams.db")

# Fetch and store a team
num_pitchers, num_hitters = db.fetch_and_store_team(
    team_abbr="NYY",
    season=2024,
    min_pitcher_innings=20.0,
    min_hitter_at_bats=50
)

print(f"Stored {num_pitchers} pitchers and {num_hitters} hitters")

# List all teams
teams = db.list_teams(season=2024)
for team in teams:
    print(f"{team['team_name']} ({team['season']})")

# Get team data
team_data = db.get_team_data("New York Yankees", 2024)
print(f"Pitchers: {len(team_data['pitchers'])}")
print(f"Hitters: {len(team_data['hitters'])}")

db.close()
```

### Loading Teams for Simulation

```python
from batted_ball.database import TeamLoader
from batted_ball.game_simulation import GameSimulator

# Load teams
loader = TeamLoader("baseball_teams.db")

yankees = loader.load_team("New York Yankees", season=2024)
dodgers = loader.load_team("Los Angeles Dodgers", season=2024)

loader.close()

# Simulate game
sim = GameSimulator(away_team=dodgers, home_team=yankees, verbose=True)
result = sim.simulate_game(num_innings=9)

print(f"Final: Dodgers {result.away_score}, Yankees {result.home_score}")
```

### Direct Stats Conversion

```python
from batted_ball.database import StatsConverter

converter = StatsConverter()

# Convert pitcher stats
pitcher_attrs = converter.mlb_stats_to_pitcher_attributes(
    era=2.50,
    whip=0.95,
    k_per_9=11.5,
    bb_per_9=1.8,
    avg_fastball_velo=97.5,
    innings_pitched=180.0,
    games_pitched=30
)

print(f"Velocity: {pitcher_attrs['velocity']:,} / 100,000")
print(f"Command:  {pitcher_attrs['command']:,} / 100,000")
print(f"Stamina:  {pitcher_attrs['stamina']:,} / 100,000")

# Convert hitter stats
hitter_attrs = converter.mlb_stats_to_hitter_attributes(
    batting_avg=0.300,
    ops=0.950,
    home_runs=40,
    strikeouts=120,
    walks=90,
    at_bats=580,
    avg_exit_velo=92.5,
    barrel_pct=12.5
)

print(f"Contact:    {hitter_attrs['contact']:,} / 100,000")
print(f"Power:      {hitter_attrs['power']:,} / 100,000")
print(f"Discipline: {hitter_attrs['discipline']:,} / 100,000")
```

---

## Stat Conversion

### How MLB Stats Map to Game Attributes

The `StatsConverter` uses **percentile-based mapping** to convert real MLB statistics into the game's 0-100,000 attribute scale.

#### Pitcher Attributes

| Game Attribute | MLB Stats Used | Elite (90k+) | Average (50k) |
|---------------|----------------|--------------|---------------|
| **Velocity** | Fastball velocity | 97+ mph | 92.5 mph |
| **Command** | BB/9, WHIP | <1.8 BB/9 | 3.2 BB/9 |
| **Stamina** | IP/game | 6.5+ IP/G | 3.0 IP/G |
| **Movement** | K/9, ERA | 11+ K/9 | 8.5 K/9 |
| **Repertoire** | K/9, ERA | <2.5 ERA | 4.2 ERA |

#### Hitter Attributes

| Game Attribute | MLB Stats Used | Elite (90k+) | Average (50k) |
|---------------|----------------|--------------|---------------|
| **Contact** | AVG, K% | .300 AVG, 15% K | .250 AVG, 23% K |
| **Power** | Exit velo, Barrel%, SLG, HR | 92+ EV, 12% Barrel | 87.5 EV, 6% Barrel |
| **Discipline** | BB%, OBP, K% | 15% BB, .380 OBP | 8.5% BB, .320 OBP |
| **Speed** | Sprint speed | 29.5+ ft/s | 27.5 ft/s |

### Percentile Ranges

The converter maps stats to attributes using these ranges:

- **Elite** (90k-100k): Top 10% of MLB players
- **Good** (70k-90k): Top 30% of MLB players
- **Average** (50k-70k): League average
- **Below Average** (30k-50k): Bottom 30%
- **Poor** (0-30k): Below MLB-quality

This ensures realistic distributions where:
- Elite players (MVPs, Cy Young candidates) rate 85k-100k
- Solid starters rate 60k-80k
- Average players rate 45k-60k
- Bench/role players rate 30k-50k

---

## Examples

### Example 1: Build a Division

```bash
# Add all AL East teams for 2024
python manage_teams.py add-multiple 2024 NYY BOS TB TOR BAL

# Simulate Yankees vs Red Sox
python examples/simulate_mlb_matchup.py "New York Yankees" "Boston Red Sox" 2024

# Simulate a 10-game series
python examples/simulate_mlb_matchup.py "Tampa Bay Rays" "Toronto Blue Jays" 2024 --games 10
```

### Example 2: Historical Season

```bash
# Add 2023 World Series teams
python manage_teams.py add TEX 2023
python manage_teams.py add ARI 2023

# Simulate 2023 World Series matchup
python examples/simulate_mlb_matchup.py "Texas Rangers" "Arizona Diamondbacks" 2023 --games 7
```

### Example 3: Python Workflow

```python
from batted_ball.database import TeamDatabase, TeamLoader
from batted_ball.game_simulation import GameSimulator

# 1. Fetch and store teams
db = TeamDatabase()
db.fetch_and_store_team("LAD", 2024)
db.fetch_and_store_team("SF", 2024)
db.close()

# 2. Load teams for simulation
loader = TeamLoader()
dodgers = loader.load_team("Los Angeles Dodgers", 2024)
giants = loader.load_team("San Francisco Giants", 2024)
loader.close()

# 3. Simulate series
dodgers_wins = 0
giants_wins = 0

for game in range(10):
    sim = GameSimulator(away_team=giants, home_team=dodgers, verbose=False)
    result = sim.simulate_game()

    if result.home_score > result.away_score:
        dodgers_wins += 1
    else:
        giants_wins += 1

print(f"Dodgers: {dodgers_wins} wins")
print(f"Giants: {giants_wins} wins")
```

### Example 4: Custom Database Analysis

```python
import sqlite3

# Open database directly
conn = sqlite3.connect("baseball_teams.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find highest velocity pitcher
cursor.execute("""
    SELECT player_name, velocity, avg_fastball_velo, era
    FROM pitchers
    WHERE season = 2024
    ORDER BY velocity DESC
    LIMIT 10
""")

print("Top 10 hardest throwers (2024):")
for row in cursor.fetchall():
    print(f"  {row['player_name']:25s} - "
          f"Velocity: {row['velocity']:6,} - "
          f"Velo: {row['avg_fastball_velo']:.1f} mph - "
          f"ERA: {row['era']:.2f}")

conn.close()
```

---

## Troubleshooting

### Issue: "No data found for team"

**Cause**: pybaseball might be having issues fetching data for that team/season.

**Solutions**:
- Verify team abbreviation: `python manage_teams.py show-teams`
- Try a different season (2023, 2022)
- Lower the minimum thresholds: `--min-innings 10 --min-at-bats 30`
- Check pybaseball status (it scrapes from FanGraphs which occasionally has issues)

### Issue: "Only X hitters found, need 9"

**Cause**: Not enough hitters meet the minimum at-bat threshold.

**Solution**: Lower the threshold:
```bash
python manage_teams.py add NYY 2024 --min-at-bats 20
```

### Issue: Missing Statcast data (exit velocity, sprint speed)

**Cause**: Not all stats are available from FanGraphs for all players.

**Effect**: The converter will use defaults for missing stats. Ratings will still be reasonable based on traditional stats (AVG, OPS, ERA, K/9).

**Solution**: This is expected behavior. The system gracefully handles missing data.

### Issue: Slow first run

**Cause**: pybaseball needs to download and cache data on first use.

**Solution**: Be patient on the first fetch (30-60 seconds). Subsequent fetches will be faster due to caching.

### Issue: "ImportError: No module named 'pybaseball'"

**Solution**: Install pybaseball:
```bash
pip install pybaseball
```

---

## Advanced Usage

### Database Backup

```bash
# Backup database
cp baseball_teams.db baseball_teams_backup_2024.db

# Restore from backup
cp baseball_teams_backup_2024.db baseball_teams.db
```

### Database Location

By default, the database is stored at `baseball_teams.db` in the project root. You can specify a different location:

```bash
python manage_teams.py add NYY 2024 --db /path/to/my_teams.db
python examples/simulate_mlb_matchup.py "Yankees" "Dodgers" 2024 --db /path/to/my_teams.db
```

### Updating Team Data

To update a team's stats (e.g., mid-season refresh):

```bash
python manage_teams.py add NYY 2024 --overwrite
```

This will fetch fresh data and replace the existing team.

---

## Future Enhancements

Potential future features:
- Automatic Statcast integration (exit velocity, spin rates)
- Defensive metrics (OAA, DRS) → fielding attributes
- Pitcher repertoire analysis (pitch usage percentages)
- Platoon splits (vs LHP/RHP)
- Web interface for database management
- REST API for team data

---

## References

- **pybaseball docs**: https://github.com/jldbc/pybaseball
- **FanGraphs**: https://www.fangraphs.com/
- **Baseball Savant**: https://baseballsavant.mlb.com/
- **Game attribute system**: `docs/IMPLEMENTATION_SUMMARY.md`
- **Stat conversion logic**: `batted_ball/database/stats_converter.py`

---

**Last Updated**: 2025-11-19
**Version**: 1.0
**Maintainer**: Baseball Physics Simulation Engine Project
