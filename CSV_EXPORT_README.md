# CSV Export Guide

This guide explains how to export the MLB team database to CSV format for easy sharing with AI systems or external analysis tools.

## Quick Start

### Export Entire Database

```bash
# Export all teams to CSV files
python export_db_to_csv.py

# Output: csv_exports/ directory with 5 CSV files
```

### Export Single Team

```bash
# Export just one team
python export_db_to_csv.py --team "New York Yankees" --season 2024

# Output: csv_exports/new_york_yankees_2024.csv
```

### Custom Output Directory

```bash
# Export to custom location
python export_db_to_csv.py --output my_data/

# For AI: Use quiet mode
python export_db_to_csv.py --quiet
```

## Automatic CSV Export

**NEW**: When you add teams to the database, CSV files are automatically exported!

```bash
# This command now:
# 1. Fetches data from MLB
# 2. Stores in SQLite database
# 3. Exports to CSV automatically
python manage_teams.py add NYY 2024

# Skip CSV export if you want
python manage_teams.py add NYY 2024 --no-csv

# Custom CSV directory
python manage_teams.py add NYY 2024 --csv-dir my_exports/
```

## Output Files

The export creates 5 CSV files:

### 1. **teams.csv**
Team metadata

| Column | Description |
|--------|-------------|
| team_id | Unique identifier |
| team_name | Full team name (e.g., "New York Yankees") |
| team_abbr | Abbreviation (e.g., "NYY") |
| season | Year (e.g., 2024) |
| league | AL/NL |
| division | East/Central/West |

### 2. **pitchers.csv**
All pitchers with game attributes and MLB statistics

**Game Attributes** (0-100,000 scale):
- `velocity` - Fastball velocity
- `command` - Control and accuracy
- `stamina` - Endurance
- `movement` - Pitch movement quality
- `repertoire` - Variety of pitches

**MLB Stats** (source data):
- `era` - Earned run average
- `whip` - Walks + hits per inning
- `k_per_9` - Strikeouts per 9 innings
- `bb_per_9` - Walks per 9 innings
- `avg_fastball_velo` - Average fastball velocity (mph)
- `innings_pitched` - Total innings pitched

**Additional Columns**:
- `player_name` - Pitcher name
- `team_name` - Team
- `season` - Year
- `is_starter` - 1 if starter, 0 if reliever

### 3. **hitters.csv**
All hitters with game attributes and MLB statistics

**Game Attributes** (0-100,000 scale):
- `contact` - Bat-to-ball ability
- `power` - Exit velocity and distance
- `discipline` - Plate discipline and walk rate
- `speed` - Running speed

**MLB Stats** (source data):
- `batting_avg` - Batting average
- `on_base_pct` - On-base percentage
- `slugging_pct` - Slugging percentage
- `ops` - On-base plus slugging
- `home_runs` - Home runs
- `stolen_bases` - Stolen bases
- `avg_exit_velo` - Average exit velocity (mph)
- `max_exit_velo` - Maximum exit velocity (mph)
- `barrel_pct` - Barrel percentage
- `sprint_speed` - Sprint speed (ft/s)

**Additional Columns**:
- `player_name` - Hitter name
- `team_name` - Team
- `season` - Year
- `batting_order` - Position in lineup
- `position` - Defensive position

### 4. **team_rosters.csv**
Links between teams and players

| Column | Description |
|--------|-------------|
| roster_id | Unique identifier |
| team_id | Team ID (foreign key) |
| pitcher_id | Pitcher ID (if pitcher) |
| hitter_id | Hitter ID (if hitter) |
| player_name | Player name |
| player_type | "Pitcher" or "Hitter" |
| batting_order | Lineup position (hitters only) |
| is_starter | 1 if starting pitcher |

### 5. **teams_full.csv** ⭐ **BEST FOR AI**
Comprehensive denormalized view with all data in one file

This file combines all player attributes and stats into a single denormalized format - perfect for uploading to AI systems like Claude, ChatGPT, or data analysis tools.

**Columns include**:
- Team info (name, abbreviation, season)
- Player info (name, type)
- All game attributes (velocity, command, contact, power, etc.)
- All MLB stats (ERA, AVG, OPS, exit velo, etc.)
- Roster info (batting order, starter status)

**Use this file when you want to:**
- Upload all player data to an AI in one file
- Analyze teams in spreadsheet software
- Share complete team data with others
- Import into data analysis tools

## Usage Examples

### Example 1: Add Team and Get CSVs Automatically

```bash
# Add Yankees 2024
python manage_teams.py add NYY 2024

# Result: Database updated AND CSVs exported to csv_exports/
```

### Example 2: Add Multiple Teams

```bash
# Add entire AL East
python manage_teams.py add-multiple 2024 NYY BOS TB TOR BAL

# Result: All 5 teams in database and CSV files updated
```

### Example 3: Export Existing Database

```bash
# You already have teams in the database
# Just want to export to CSV
python export_db_to_csv.py

# Output: csv_exports/ directory created with all data
```

### Example 4: Export for AI Analysis

```bash
# Export with custom directory for organizing
python export_db_to_csv.py --output ai_upload/

# Then upload ai_upload/teams_full.csv to your AI system
```

### Example 5: Skip Auto-Export (Database Only)

```bash
# Only want SQLite database, no CSV
python manage_teams.py add LAD 2024 --no-csv

# Later, manually export when needed
python export_db_to_csv.py
```

## Understanding Game Attributes

The game attributes use a **0-100,000 scale** where:

| Range | Description | Example |
|-------|-------------|---------|
| 85,000-100,000 | Elite/Superhuman | MVP, Cy Young winners |
| 65,000-85,000 | Above average to elite | All-Stars, top players |
| 45,000-65,000 | Average MLB | Typical starting players |
| 30,000-45,000 | Below average | Bench players, rookies |

### Pitcher Attributes

- **Velocity** (85k = ~95 mph, 65k = ~90 mph, 45k = ~85 mph)
  - How hard the pitcher throws
  - Affects strikeout rate and contact quality

- **Command** (85k = 0.8" error, 65k = 2.5" error, 45k = 5.0" error)
  - Control and accuracy of pitches
  - Affects walks and hittable pitches

- **Stamina** (85k = 7+ IP, 65k = 6 IP, 45k = 5 IP)
  - Endurance across innings
  - Affects velocity decline over time

### Hitter Attributes

- **Contact** (85k = .300 BA, 65k = .270 BA, 45k = .240 BA)
  - Bat-to-ball ability
  - Affects batting average and strikeouts

- **Power** (85k = 40+ HR, 65k = 25 HR, 45k = 15 HR)
  - Exit velocity and distance
  - Affects extra-base hits and home runs

- **Discipline** (85k = 15% BB, 65k = 10% BB, 45k = 7% BB)
  - Plate discipline
  - Affects walk rate and pitch selection

- **Speed** (85k = 30 ft/s, 65k = 27 ft/s, 45k = 25 ft/s)
  - Running speed
  - Affects stolen bases and range on defense

## CSV File Locations

Default location: `csv_exports/` in the baseball directory

```
baseball/
├── baseball_teams.db          # SQLite database
├── csv_exports/               # CSV exports (auto-created)
│   ├── teams.csv             # Team metadata
│   ├── pitchers.csv          # All pitchers
│   ├── hitters.csv           # All hitters
│   ├── team_rosters.csv      # Team-player links
│   └── teams_full.csv        # ⭐ Complete denormalized view
├── manage_teams.py           # Add/manage teams
└── export_db_to_csv.py       # Export to CSV
```

## Programmatic Usage

### Python API

```python
from batted_ball.database import CSVExporter

# Export entire database
exporter = CSVExporter("baseball_teams.db")
exporter.export_all("my_exports/")

# Export single team
exporter.export_team_summary(
    team_name="New York Yankees",
    season=2024,
    output_path="yankees_2024.csv"
)
```

### Disable Auto-Export in Code

```python
from batted_ball.database import TeamDatabase

db = TeamDatabase()

# Add team without CSV export
db.fetch_and_store_team(
    "NYY",
    season=2024,
    export_csv=False  # Skip CSV export
)

# Later, manually export
from batted_ball.database import CSVExporter
exporter = CSVExporter(db.db_path)
exporter.export_all()
```

## Tips for AI Upload

1. **Use `teams_full.csv`** - It has everything in one file
2. **Include context** - Tell the AI:
   - Attributes are 0-100,000 scale
   - Higher values = better players
   - 65k+ = above average MLB player
3. **Ask specific questions**:
   - "Compare the power attributes of Yankees vs Dodgers"
   - "Which team has the highest average velocity?"
   - "Find players with 80k+ in any attribute"

## Troubleshooting

### "Database not found"
```bash
# Check current directory
ls *.db

# If database is elsewhere, specify path
python export_db_to_csv.py path/to/baseball_teams.db
```

### "No teams in database"
```bash
# Add teams first
python manage_teams.py add NYY 2024

# Then export
python export_db_to_csv.py
```

### CSV Files Not Updating
```bash
# Delete old exports
rm -rf csv_exports/

# Re-export
python export_db_to_csv.py

# Or force re-export when adding teams
python manage_teams.py add NYY 2024 --overwrite
```

## Advanced Options

### Custom Filters When Adding Teams

```bash
# Only players with significant playing time
python manage_teams.py add NYY 2024 --min-innings 50 --min-at-bats 200

# This affects both database and CSV exports
```

### Multiple Databases

```bash
# Create separate databases for different seasons
python manage_teams.py add NYY 2024 --db teams_2024.db
python manage_teams.py add NYY 2023 --db teams_2023.db

# Export each separately
python export_db_to_csv.py teams_2024.db --output csv_2024/
python export_db_to_csv.py teams_2023.db --output csv_2023/
```

## Summary

- **Automatic**: CSV files are generated automatically when you add teams
- **Manual**: Use `export_db_to_csv.py` to export existing database
- **Best for AI**: Upload `teams_full.csv` - it has everything
- **Customizable**: Control output directory and export behavior
- **Up-to-date**: CSVs always reflect current database state

For more information, see:
- `DATABASE_README.md` - Full database system documentation
- `CLAUDE.md` - Complete codebase guide
- `README.md` - Project overview
