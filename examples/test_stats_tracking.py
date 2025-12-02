"""
Quick test for stats tracking integration.

Tests the Scorekeeper and StatsEnabledGameSimulator with MLB teams.
"""

import sys
from datetime import date

# Add parent to path if needed
sys.path.insert(0, '.')

from batted_ball import (
    StatsEnabledGameSimulator, 
    StatsTrackingMode,
    simulate_game_with_stats,
    StatsDatabase,
)
from batted_ball.database.team_loader import TeamLoader


def test_stats_tracking():
    """Test stats tracking with MLB teams."""
    print("Loading MLB teams from database...")
    loader = TeamLoader()
    
    # Load two teams
    teams = loader.list_available_teams()
    if len(teams) < 2:
        print("Error: Need at least 2 teams in database")
        return False
    
    print(f"Available teams: {len(teams)}")
    print(f"First few: {teams[:5]}")
    
    # Use first two teams - parse name and season from format "Team Name (YYYY)"
    team1_str = teams[0]
    team2_str = teams[1]
    
    # Parse "Team Name (2025)" -> ("Team Name", 2025)
    team1_name = team1_str.rsplit(" (", 1)[0]
    team1_season = int(team1_str.rsplit(" (", 1)[1].rstrip(")"))
    team2_name = team2_str.rsplit(" (", 1)[0]
    team2_season = int(team2_str.rsplit(" (", 1)[1].rstrip(")"))
    
    print(f"Loading: {team1_name} ({team1_season}) vs {team2_name} ({team2_season})")
    
    away_team = loader.load_team(team1_name, team1_season)
    home_team = loader.load_team(team2_name, team2_season)
    
    if away_team is None or home_team is None:
        print("Failed to load teams")
        return False
    
    print(f"\nSimulating game with stats tracking...")
    print(f"{away_team.name} @ {home_team.name}")
    print("-" * 50)
    
    # Simulate with stats tracking
    simulator = StatsEnabledGameSimulator(
        away_team,
        home_team,
        stats_mode=StatsTrackingMode.STANDARD,
        game_date=date(2025, 4, 1),
        verbose=False,  # Quiet mode for test
    )
    
    game_state = simulator.simulate_game()
    
    print(f"\nFinal Score: {away_team.name} {game_state.away_score} - {home_team.name} {game_state.home_score}")
    
    # Get and print box score
    game_log = simulator.get_game_log()
    
    if game_log:
        print("\n=== BOX SCORE ===")
        print(game_log.get_line_score_str())
        
        # Print batting leaders from this game
        print(f"\n{game_log.away_team} Batting:")
        for stats in game_log.away_batting[:5]:
            if stats.plate_appearances > 0:
                print(f"  {stats.player_name}: {stats.hits}-{stats.at_bats}, {stats.home_runs} HR, {stats.rbi} RBI")
        
        print(f"\n{game_log.home_team} Batting:")
        for stats in game_log.home_batting[:5]:
            if stats.plate_appearances > 0:
                print(f"  {stats.player_name}: {stats.hits}-{stats.at_bats}, {stats.home_runs} HR, {stats.rbi} RBI")
        
        print(f"\n{game_log.away_team} Pitching:")
        for stats in game_log.away_pitching:
            ip = stats.innings_pitched
            print(f"  {stats.player_name}: {ip} IP, {stats.strikeouts} K, {stats.hits_allowed} H")
        
        print(f"\n{game_log.home_team} Pitching:")
        for stats in game_log.home_pitching:
            ip = stats.innings_pitched
            print(f"  {stats.player_name}: {ip} IP, {stats.strikeouts} K, {stats.hits_allowed} H")
        
        print("\n✓ Stats tracking working!")
        
        # Test database persistence
        print("\n=== Testing Database Persistence ===")
        db = StatsDatabase()
        season_id = db.get_or_create_season(2025, "Test simulation")
        game_id = db.record_game(season_id, game_log)
        print(f"Recorded game {game_id} to season {season_id}")
        
        # Query back
        standings = db.get_team_standings(season_id)
        print(f"\nStandings after 1 game:")
        for team in standings:
            print(f"  {team['team']}: {team['wins']}-{team['losses']}")
        
        db.close()
        print("\n✓ Database persistence working!")
        
        return True
    else:
        print("Error: No game log generated")
        return False


if __name__ == "__main__":
    success = test_stats_tracking()
    sys.exit(0 if success else 1)
