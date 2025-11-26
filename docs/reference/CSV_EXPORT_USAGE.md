# CSV Export - Complete Solution

## What Was Created

I've implemented a complete CSV export system for the baseball database:

### New Files

1. **`batted_ball/database/csv_exporter.py`** (300+ lines)
   - Main CSV export module
   - Exports all database tables to CSV format
   - Creates denormalized view for AI ingestion

2. **`export_db_to_csv.py`** (Standalone script)
   - Command-line tool for exporting databases
   - Supports full export or single team
   - Executable standalone script

3. **`CSV_EXPORT_README.md`** (Complete documentation)
   - Usage examples
   - File format descriptions
   - Tips for AI upload

4. **`test_csv_export.py`** (Test suite)
   - Validates export functionality
   - Creates sample database for testing

### Modified Files

1. **`batted_ball/database/__init__.py`**
   - Added CSVExporter to public API

2. **`batted_ball/database/team_database.py`**
   - Added `export_csv` parameter to `fetch_and_store_team()`
   - Automatically exports CSV after adding teams (default: enabled)
   - Added `csv_output_dir` parameter for custom output location

3. **`manage_teams.py`**
   - Added `--no-csv` flag to skip automatic export
   - Added `--csv-dir` option for custom export directory
   - Passes CSV options to database operations

## Quick Usage

### Automatic Export (NEW - Default Behavior)

When you add teams, CSVs are automatically generated:

```bash
# Add a team - automatically exports to csv_exports/
python manage_teams.py add NYY 2024
```

Output:
```
============================================================
Fetching and storing NYY (2024)
============================================================

  ✓ Stored 15 pitchers and 20 hitters
============================================================

======================================================================
Exporting database to CSV: baseball_teams.db
Output directory: /home/user/baseball/csv_exports
======================================================================

  ✓ teams                → teams.csv                (    1 rows)
  ✓ pitchers             → pitchers.csv             (   15 rows)
  ✓ hitters              → hitters.csv              (   20 rows)
  ✓ team_rosters         → team_rosters.csv         (   35 rows)
  ✓ teams_full           → teams_full.csv           (   35 rows)

======================================================================
Exported 5 CSV files to /home/user/baseball/csv_exports
======================================================================
```

### Manual Export

Export an existing database:

```bash
# Export default database
python export_db_to_csv.py

# Export specific database
python export_db_to_csv.py custom.db

# Custom output directory
python export_db_to_csv.py --output my_exports/

# Export single team
python export_db_to_csv.py --team "New York Yankees" --season 2024
```

### Skip Automatic Export

If you don't want CSV files:

```bash
# Add team without CSV export
python manage_teams.py add NYY 2024 --no-csv

# Later, manually export when needed
python export_db_to_csv.py
```

### Custom Export Directory

```bash
# Export to custom location
python manage_teams.py add NYY 2024 --csv-dir my_data/

# Or when exporting manually
python export_db_to_csv.py --output my_data/
```

## Output Files

The system creates 5 CSV files:

### 1. teams.csv
Basic team metadata

### 2. pitchers.csv
All pitchers with:
- Game attributes (velocity, command, stamina, movement, repertoire)
- MLB statistics (ERA, WHIP, K/9, BB/9, velocity, innings)
- Team affiliation
- Starter status

### 3. hitters.csv
All hitters with:
- Game attributes (contact, power, discipline, speed)
- MLB statistics (AVG, OBP, SLG, OPS, HR, SB, exit velocity, sprint speed)
- Team affiliation
- Batting order

### 4. team_rosters.csv
Links between teams and players

### 5. teams_full.csv ⭐ **BEST FOR AI**
Complete denormalized view with all player data in one file
- Perfect for uploading to AI systems
- Combines all tables into single view
- Easy to analyze in spreadsheet software

## Programmatic Usage

### Python API

```python
from batted_ball.database import TeamDatabase, CSVExporter

# Method 1: Add team with automatic export
db = TeamDatabase()
db.fetch_and_store_team(
    "NYY",
    season=2024,
    export_csv=True,           # Default: True
    csv_output_dir="my_csvs/"  # Default: "csv_exports"
)

# Method 2: Manual export
exporter = CSVExporter("baseball_teams.db")
exporter.export_all("output_dir/")

# Method 3: Export single team
exporter.export_team_summary(
    team_name="New York Yankees",
    season=2024,
    output_path="yankees_2024.csv"
)
```

## CSV File Structure

### teams_full.csv (Recommended for AI)

Contains these columns:

**Team Info:**
- team_name
- team_abbr
- season
- league
- division

**Player Info:**
- player_type (Pitcher/Hitter)
- player_name

**Pitcher Attributes (0-100,000 scale):**
- attribute_velocity
- attribute_command
- attribute_stamina
- attribute_movement
- attribute_repertoire

**Hitter Attributes (0-100,000 scale):**
- attribute_contact
- attribute_power
- attribute_discipline
- attribute_speed

**Pitcher MLB Stats:**
- era
- whip
- k_per_9
- bb_per_9
- innings_pitched
- avg_fastball_velo

**Hitter MLB Stats:**
- batting_avg
- on_base_pct
- slugging_pct
- ops
- home_runs
- stolen_bases
- avg_exit_velo
- max_exit_velo
- barrel_pct
- sprint_speed

**Roster Info:**
- batting_order (for hitters)
- is_starter (for pitchers)
- hand (L/R)
- position

## Example Workflows

### Workflow 1: Build Database and Export

```bash
# Add multiple teams
python manage_teams.py add-multiple 2024 NYY BOS LAD SF

# CSVs are automatically created in csv_exports/
# Upload csv_exports/teams_full.csv to your AI
```

### Workflow 2: Update Database, Re-export

```bash
# Add more teams
python manage_teams.py add CHC 2024

# CSV automatically updated with new data
```

### Workflow 3: Database Only (No CSV)

```bash
# Build database without CSV
python manage_teams.py add NYY 2024 --no-csv
python manage_teams.py add BOS 2024 --no-csv

# Export all at once when ready
python export_db_to_csv.py
```

### Workflow 4: Multiple Output Locations

```bash
# Export to different directories
python export_db_to_csv.py --output analysis/
python export_db_to_csv.py --output backups/$(date +%Y%m%d)/
```

## Benefits

1. **Automatic**: CSVs generated automatically when adding teams
2. **AI-Friendly**: teams_full.csv perfect for AI ingestion
3. **Flexible**: Can disable auto-export or customize output
4. **Complete**: All player attributes and stats in CSV format
5. **Up-to-date**: Always reflects current database state

## Technical Details

### CSVExporter Class

Main methods:

```python
class CSVExporter:
    def export_all(output_dir, verbose=True)
        # Exports all 5 CSV files

    def export_teams(output_path)
        # Export teams.csv

    def export_pitchers(output_path)
        # Export pitchers.csv with team names

    def export_hitters(output_path)
        # Export hitters.csv with team names

    def export_team_rosters(output_path)
        # Export team_rosters.csv

    def export_teams_full(output_path)
        # Export comprehensive denormalized view

    def export_team_summary(team_name, season, output_path)
        # Export single team roster
```

### Integration Points

The CSV export is integrated at these points:

1. **`TeamDatabase.fetch_and_store_team()`**
   - Automatically calls CSV export after storing teams
   - Can be disabled with `export_csv=False`

2. **`manage_teams.py`**
   - Passes `--no-csv` flag to disable export
   - Passes `--csv-dir` for custom output location

3. **Standalone script**
   - `export_db_to_csv.py` for manual exports
   - Works with any existing database

## File Locations

Default structure:

```
baseball/
├── baseball_teams.db           # SQLite database
├── csv_exports/                # CSV files (auto-created)
│   ├── teams.csv
│   ├── pitchers.csv
│   ├── hitters.csv
│   ├── team_rosters.csv
│   └── teams_full.csv         # ⭐ Upload this to AI
├── manage_teams.py            # Team management CLI
└── export_db_to_csv.py        # CSV export CLI
```

## Summary

The CSV export system provides:

✅ **Automatic export** when adding teams (default)
✅ **Manual export** via standalone script
✅ **5 CSV files** including denormalized AI-friendly view
✅ **Flexible configuration** with command-line options
✅ **Complete data** - all attributes and MLB stats
✅ **Easy AI upload** - teams_full.csv has everything

For complete documentation, see `CSV_EXPORT_README.md`
