"""Check actual fielder sprint speeds being used in simulations."""
from batted_ball.game_simulation import create_test_team

# Create test teams
home_team = create_test_team("Home")
away_team = create_test_team("Away")

print("FIELDER SPRINT SPEEDS")
print("=" * 80)

for team_name, team in [("Home", home_team), ("Away", away_team)]:
    print(f"\n{team_name} Team:")
    print("-" * 80)
    
    for position, fielder in team.fielders.items():
        sprint_speed_fps = fielder.get_sprint_speed_fps_statcast()
        sprint_speed_mph = sprint_speed_fps * 0.681818  # ft/s to mph
        reaction_time = fielder.get_reaction_time_seconds()
        
        print(f"  {position:12s}: {sprint_speed_fps:5.2f} ft/s ({sprint_speed_mph:5.2f} mph), reaction: {reaction_time:.3f}s")
