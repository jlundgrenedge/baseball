# Baseball Team Database System

**Author**: Claude
**Date**: 2025-11-19
**Version**: 1.0

A complete database system for storing and using real MLB team data in baseball simulations.

---

## 🎯 Overview

This system allows you to:
- **Fetch real MLB player statistics** using pybaseball
- **Convert stats to game attributes** (0-100,000 scale)
- **Store teams in SQLite database** for fast access
- **Load teams for simulations** without re-scraping data every time

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install numpy scipy matplotlib pandas pybaseball numba
```

### 2. Populate Database with Sample Teams

```bash
# Create 6 sample teams for testing
python examples/populate_sample_teams.py
```

### 3. List Available Teams

```bash
python manage_teams.py list
```

### 4. Run a Simulation

```bash
# Single game
python examples/simulate_mlb_matchup.py "New York Yankees" "Los Angeles Dodgers" 2024

# 10-game series
python examples/simulate_mlb_matchup.py "New York Yankees" "Boston Red Sox" 2024 --games 10
```

---

## 📁 File Structure

```
batted_ball/database/
├── __init__.py               # Module exports
├── db_schema.py              # SQLite schema definition
├── stats_converter.py        # MLB stats → game attributes
├── pybaseball_fetcher.py     # Fetch data from pybaseball
├── team_database.py          # Database CRUD operations
└── team_loader.py            # Load teams for simulations

manage_teams.py               # CLI tool for database management
examples/
├── populate_sample_teams.py  # Create synthetic team data
└── simulate_mlb_matchup.py   # Run simulations from database
docs/
└── DATABASE_GUIDE.md         # Detailed documentation
```

---

## 🛠️ CLI Tools

### manage_teams.py

Command-line interface for managing the database.

#### Add a Team from pybaseball

```bash
python manage_teams.py add NYY 2024
python manage_teams.py add LAD 2023 --overwrite
python manage_teams.py add BOS 2024 --min-innings 15 --min-at-bats 40
```

#### Add Multiple Teams

```bash
# Add entire AL East
python manage_teams.py add-multiple 2024 NYY BOS TB TOR BAL
```

#### List Teams

```bash
# All teams
python manage_teams.py list

# Only 2024
python manage_teams.py list --season 2024
```

#### Delete a Team

```bash
python manage_teams.py delete "New York Yankees" 2024
```

#### Show Available Team Abbreviations

```bash
python manage_teams.py show-teams
```

### simulate_mlb_matchup.py

Run simulations between teams stored in the database.

```bash
# Single game with play-by-play
python examples/simulate_mlb_matchup.py "Team A" "Team B" 2024

# Multi-game series (quiet mode)
python examples/simulate_mlb_matchup.py "Team A" "Team B" 2024 --games 100 --quiet
```

---

## 📊 Database Schema

### Tables

#### **teams**
- Stores team metadata
- Columns: `team_id`, `team_name`, `team_abbr`, `season`, `league`, `division`

#### **pitchers**
- Stores pitcher statistics and attributes
- **Game attributes** (0-100k): `velocity`, `command`, `stamina`, `movement`, `repertoire`
- **MLB stats**: `era`, `whip`, `k_per_9`, `bb_per_9`, `avg_fastball_velo`, etc.

#### **hitters**
- Stores hitter statistics and attributes
- **Game attributes** (0-100k): `contact`, `power`, `discipline`, `speed`
- **MLB stats**: `batting_avg`, `ops`, `home_runs`, `avg_exit_velo`, `barrel_pct`, etc.

#### **team_rosters**
- Links players to teams
- Tracks batting order and starter status

---

## 🔄 Stats Conversion

The `StatsConverter` uses **percentile-based mapping** to convert MLB stats to game attributes:

### Pitcher Conversion

| Attribute | MLB Stats Used | Elite (90k+) | Average (50k) |
|-----------|----------------|--------------|---------------|
| Velocity | Fastball velocity | 97+ mph | 92.5 mph |
| Command | BB/9, WHIP | <1.8 BB/9 | 3.2 BB/9 |
| Stamina | IP/game | 6.5+ IP/G | 3.0 IP/G |
| Movement | K/9, ERA | 11+ K/9 | 8.5 K/9 |

### Hitter Conversion

| Attribute | MLB Stats Used | Elite (90k+) | Average (50k) |
|-----------|----------------|--------------|---------------|
| Contact | AVG, K% | .300 AVG, 15% K | .250 AVG, 23% K |
| Power | Exit velo, Barrel%, SLG, HR | 92+ EV, 12% Barrel | 87.5 EV, 6% Barrel |
| Discipline | BB%, OBP, K% | 15% BB, .380 OBP | 8.5% BB, .320 OBP |
| Speed | Sprint speed | 29.5+ ft/s | 27.5 ft/s |

---

## 💻 Python API

### Basic Usage

```python
from batted_ball.database import TeamDatabase, TeamLoader
from batted_ball.game_simulation import GameSimulator

# 1. Populate database (one-time)
db = TeamDatabase("baseball_teams.db")
db.fetch_and_store_team("NYY", season=2024)
db.fetch_and_store_team("LAD", season=2024)
db.close()

# 2. Load teams for simulation
loader = TeamLoader("baseball_teams.db")
yankees = loader.load_team("New York Yankees", 2024)
dodgers = loader.load_team("Los Angeles Dodgers", 2024)
loader.close()

# 3. Simulate games
sim = GameSimulator(away_team=dodgers, home_team=yankees, verbose=True)
result = sim.simulate_game(num_innings=9)

print(f"Final: Dodgers {result.away_score}, Yankees {result.home_score}")
```

### Advanced Usage

```python
from batted_ball.database import StatsConverter

# Convert custom player stats
converter = StatsConverter()

pitcher_attrs = converter.mlb_stats_to_pitcher_attributes(
    era=2.50,
    k_per_9=11.5,
    avg_fastball_velo=97.5,
    # ... other stats
)

hitter_attrs = converter.mlb_stats_to_hitter_attributes(
    batting_avg=0.300,
    ops=0.950,
    avg_exit_velo=92.5,
    # ... other stats
)
```

---

## 🧪 Testing with Sample Data

Since pybaseball requires internet access and may not work in all environments, use the sample data generator:

```bash
# Create 6 teams with realistic synthetic stats
python examples/populate_sample_teams.py
```

This creates:
- **Elite teams**: New York Yankees, Los Angeles Dodgers
- **Good teams**: Houston Astros, Atlanta Braves
- **Average teams**: Boston Red Sox, Chicago Cubs

All with realistic pitcher/hitter statistics and proper attribute conversion.

---

## 🌐 Using Real MLB Data

When pybaseball is available:

```bash
# Fetch real 2024 Yankees data
python manage_teams.py add NYY 2024

# Fetch multiple teams
python manage_teams.py add-multiple 2024 NYY LAD BOS HOU ATL

# Run simulation with real data
python examples/simulate_mlb_matchup.py "New York Yankees" "Los Angeles Dodgers" 2024
```

**Note**: pybaseball fetches data from FanGraphs. First run may take 30-60 seconds per team due to data download and caching.

---

## 📝 Examples

### Example 1: Build an AL East Database

```bash
python manage_teams.py add-multiple 2024 NYY BOS TB TOR BAL
python manage_teams.py list --season 2024
```

### Example 2: Simulate a Rivalry Series

```bash
# Yankees vs Red Sox, 10 games
python examples/simulate_mlb_matchup.py "New York Yankees" "Boston Red Sox" 2024 --games 10
```

### Example 3: Compare Team Strengths

```python
from batted_ball.database import TeamDatabase

db = TeamDatabase()

# Get team data
yankees_data = db.get_team_data("New York Yankees", 2024)
dodgers_data = db.get_team_data("Los Angeles Dodgers", 2024)

# Compare average pitcher velocity
yankees_avg_velo = sum(p['velocity'] for p in yankees_data['pitchers']) / len(yankees_data['pitchers'])
dodgers_avg_velo = sum(p['velocity'] for p in dodgers_data['pitchers']) / len(dodgers_data['pitchers'])

print(f"Yankees avg pitcher velocity rating: {yankees_avg_velo:,}")
print(f"Dodgers avg pitcher velocity rating: {dodgers_avg_velo:,}")

db.close()
```

---

## 🔍 Database Queries

The database is SQLite, so you can query it directly:

```python
import sqlite3

conn = sqlite3.connect("baseball_teams.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find hardest throwers
cursor.execute("""
    SELECT player_name, velocity, avg_fastball_velo, era
    FROM pitchers
    WHERE season = 2024
    ORDER BY velocity DESC
    LIMIT 10
""")

for row in cursor.fetchall():
    print(f"{row['player_name']:20s} - Velocity: {row['velocity']:,}")

conn.close()
```

---

## 🐛 Troubleshooting

### "No data found for team"
- pybaseball may have connection issues
- Try lowering thresholds: `--min-innings 10 --min-at-bats 30`
- Use sample data instead: `python examples/populate_sample_teams.py`

### "Only X hitters found, need 9"
- Lower threshold: `--min-at-bats 20`
- System will duplicate players to fill lineup if needed

### pybaseball SSL errors
- Common in restricted environments
- Use sample data generator for testing
- Alternatively, export data from FanGraphs manually

---

## 📚 Documentation

- **DATABASE_GUIDE.md** - Comprehensive guide with detailed examples
- **CLAUDE.md** - Main codebase documentation
- **IMPLEMENTATION_SUMMARY.md** - Architecture overview

---

## 🎉 Features

✅ **Automatic data fetching** from pybaseball
✅ **Smart stat conversion** using percentile mapping
✅ **SQLite storage** for fast access
✅ **Sample data generator** for testing
✅ **CLI tools** for easy management
✅ **Python API** for advanced usage
✅ **Multi-game simulations** with statistics
✅ **Historical season support** (2015-present)

---

## 🔮 Future Enhancements

Potential future features:
- Automatic Statcast integration (spin rates, extension)
- Defensive metrics (OAA, DRS) → fielding attributes
- Platoon splits (vs LHP/RHP)
- Web interface for database management
- REST API for team data
- Automated season updates

---

## 📄 License

Part of the Baseball Physics Simulation Engine project.

---

## 🙏 Credits

- **pybaseball** - For MLB data access
- **FanGraphs** - Statistical data source
- **Baseball Savant** - Statcast data
- **Baseball Physics Engine** - Core simulation system

---

## 📞 Support

For issues or questions:
1. Check DATABASE_GUIDE.md for detailed documentation
2. Review CLAUDE.md for codebase architecture
3. Examine example scripts in `examples/`

---

**Last Updated**: 2025-11-19
**Status**: Production Ready ✅
**Version**: 1.0.0
