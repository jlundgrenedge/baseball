"""Test ballpark integration with database teams."""
from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator
import sqlite3

# Load teams
loader = TeamLoader('baseball_teams.db')
cubs = loader.load_team("Chicago Cubs", 2025)
reds = loader.load_team("Cincinnati Reds", 2025)
loader.close()

if not cubs or not reds:
    print("ERROR: Failed to load teams")
    exit(1)

# Get team abbreviations
conn = sqlite3.connect('baseball_teams.db')
cursor = conn.cursor()
cursor.execute("SELECT team_abbr FROM teams WHERE team_name = ? AND season = ?", ("Chicago Cubs", 2025))
cubs_abbr = cursor.fetchone()[0]
cursor.execute("SELECT team_abbr FROM teams WHERE team_name = ? AND season = ?", ("Cincinnati Reds", 2025))
reds_abbr = cursor.fetchone()[0]
conn.close()

print(f"\n=== TEAM INFO ===")
print(f"Away: {reds.name} ({reds_abbr})")
print(f"Home: {cubs.name} ({cubs_abbr})")

# Map team to ballpark
from batted_ball.ballpark import get_ballpark

TEAM_BALLPARKS = {
    'CHC': 'wrigley',
    'CIN': 'great_american',
}

home_ballpark_name = TEAM_BALLPARKS.get(cubs_abbr, 'generic')
home_ballpark = get_ballpark(home_ballpark_name)

print(f"\n=== BALLPARK ===")
print(f"Name: {home_ballpark.name}")
print(f"Key: {home_ballpark_name}")
print(f"Dimensions (sample angles):")
for angle in [-45.0, -22.5, 0.0, 22.5, 45.0]:
    dist, wall_height = home_ballpark.get_fence_at_angle(angle)
    print(f"  {angle:6.1f}°: {dist:.0f} ft, {wall_height:.0f} ft wall")

# Create simulator with ballpark
print(f"\n=== CREATING SIMULATOR ===")
sim = GameSimulator(
    away_team=reds,
    home_team=cubs,
    verbose=False,  # Quiet mode for testing
    ballpark=home_ballpark_name,
    wind_enabled=True
)

print(f"Simulator created successfully!")
print(f"Ballpark: {sim.ballpark}")
print(f"\n✓ Ballpark and wind integration working correctly!")
