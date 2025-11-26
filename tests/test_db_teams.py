"""Test script to check database teams and pitcher attributes."""
import sqlite3
from batted_ball.database.team_loader import TeamLoader

# Check what's in database
print("=== DATABASE CONTENTS ===")
conn = sqlite3.connect('baseball_teams.db')
cursor = conn.cursor()
cursor.execute('SELECT DISTINCT team_abbr, season FROM teams ORDER BY season, team_abbr')
print("\nTeams in database:")
teams_data = cursor.fetchall()
for row in teams_data:
    print(f"  {row[0]} - {row[1]}")

if not teams_data:
    print("  (No teams found)")
    conn.close()
    exit(1)

# Get first team for testing
team_abbr, season = teams_data[0]

# Get full team name from database
cursor.execute('SELECT team_name FROM teams WHERE team_abbr = ? AND season = ?', (team_abbr, season))
team_name_row = cursor.fetchone()
team_name = team_name_row[0] if team_name_row else None

if not team_name:
    print(f"ERROR: Could not find full team name for {team_abbr}")
    conn.close()
    exit(1)

print(f"\n=== TESTING TEAM: {team_name} ({team_abbr} - {season}) ===")

# Check pitcher data
cursor.execute('''
    SELECT player_name, velocity, command, stamina, movement, 
           nibbling_tendency, putaway_skill
    FROM pitchers 
    WHERE season = ?
    LIMIT 1
''', (season,))

pitcher_row = cursor.fetchone()
if pitcher_row:
    print(f"\nSample pitcher data from database:")
    print(f"  Name: {pitcher_row[0]}")
    print(f"  Velocity: {pitcher_row[1]}")
    print(f"  Command: {pitcher_row[2]}")
    print(f"  Stamina: {pitcher_row[3]}")
    print(f"  Movement: {pitcher_row[4]}")
    print(f"  Nibbling Tendency: {pitcher_row[5]}")
    print(f"  Putaway Skill: {pitcher_row[6]} (NOT USED - v2 uses get_stuff_rating())")

conn.close()

# Test loading team
print(f"\n=== LOADING TEAM WITH TeamLoader ===")
loader = TeamLoader('baseball_teams.db')
team = loader.load_team(team_name, season)

if team:
    print(f"✓ Loaded {team.name}: {len(team.pitchers)} pitchers, {len(team.hitters)} hitters")
    
    if team.pitchers:
        p = team.pitchers[0]
        print(f"\nSample pitcher attributes:")
        print(f"  Name: {p.name}")
        print(f"  RAW_VELOCITY_CAP: {p.attributes.RAW_VELOCITY_CAP}")
        print(f"  COMMAND: {p.attributes.COMMAND}")
        print(f"  STAMINA: {p.attributes.STAMINA}")
        print(f"  SPIN_RATE_CAP: {p.attributes.SPIN_RATE_CAP}")
        print(f"  NIBBLING_TENDENCY: {p.attributes.NIBBLING_TENDENCY}")
        print(f"  get_stuff_rating(): {p.attributes.get_stuff_rating():.3f} (composite put-away)")
        print(f"  get_nibbling_tendency(): {p.attributes.get_nibbling_tendency():.3f} (0.0-1.0 scale)")
else:
    print(f"✗ Failed to load team {team_name} ({season})")
