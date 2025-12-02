#!/usr/bin/env python3
"""
Test the season stats tracker with a few games.

This tests the SeasonStatsTracker's ability to accumulate player stats
across multiple games.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pathlib import Path
from batted_ball.database.team_loader import TeamLoader
from batted_ball.stats_integration import StatsEnabledGameSimulator
from batted_ball.season_stats_tracker import SeasonStatsTracker
from batted_ball.game_simulation import SimulationMode


def main():
    """Run a few games and show accumulated stats."""
    print("=" * 70)
    print("SEASON STATS TRACKER TEST")
    print("=" * 70)
    
    # Use a test database (not the main one)
    test_db_path = Path(__file__).parent.parent / "saved_stats" / "test_season_stats.db"
    
    # Delete test database if exists to start fresh
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"Removed existing test database: {test_db_path}")
    
    # Load teams from database
    loader = TeamLoader()
    available_teams = loader.list_available_teams()
    
    if not available_teams:
        print("No teams found in database. Please populate the database first.")
        return
    
    # Find teams from 2025
    teams_2025 = [t for t in available_teams if "(2025)" in t]
    if len(teams_2025) < 4:
        print(f"Need at least 4 teams from 2025, found: {len(teams_2025)}")
        return
    
    # Use first 4 teams
    team_strs = teams_2025[:4]
    print(f"\nUsing teams: {team_strs}")
    
    # Load teams
    teams = []
    for team_str in team_strs:
        name = team_str.rsplit(" (", 1)[0]
        season = int(team_str.rsplit(" (", 1)[1].rstrip(")"))
        team = loader.load_team(name, season)
        if team:
            teams.append(team)
            print(f"  Loaded: {team.name}")
    
    if len(teams) < 4:
        print("Failed to load enough teams")
        return
    
    # Create stats tracker with test database
    tracker = SeasonStatsTracker(year=2025, db_path=test_db_path)
    
    # Simulate a series of games (like a double-header between each pair)
    matchups = [
        (teams[0], teams[1]),  # Team A vs Team B
        (teams[0], teams[1]),  # Rematch
        (teams[2], teams[3]),  # Team C vs Team D
        (teams[2], teams[3]),  # Rematch
    ]
    
    print(f"\n{'='*70}")
    print("SIMULATING 4 GAMES")
    print("="*70)
    
    for i, (away, home) in enumerate(matchups, 1):
        print(f"\nGame {i}: {away.name} @ {home.name}")
        
        # Create simulator for this game
        simulator = StatsEnabledGameSimulator(
            away_team=away,
            home_team=home,
            simulation_mode=SimulationMode.ULTRA_FAST,
            verbose=False
        )
        result = simulator.simulate_game()
        game_log = simulator.get_game_log()
        
        if game_log:
            tracker.record_game(game_log)
            away_score = game_log.away_score
            home_score = game_log.home_score
            print(f"  Final: {away.name} {away_score} - {home.name} {home_score}")
            
            # Show a player's game line
            if game_log.away_batting:
                player = game_log.away_batting[0]
                line = f"{player.at_bats}AB"
                if player.hits > 0:
                    line += f", {player.hits}H"
                if player.runs > 0:
                    line += f", {player.runs}R"
                if player.rbi > 0:
                    line += f", {player.rbi}RBI"
                print(f"    {player.player_name}: {line}")
    
    # Print accumulated stats
    print(f"\n{'='*70}")
    print("SEASON STATS SUMMARY")
    print("="*70)
    print(f"Games recorded: {tracker.games_recorded}")
    
    # Get batting leaders from database
    print(f"\n{'='*70}")
    print("BATTING LEADERS")
    print("="*70)
    
    # Home run leaders
    hr_leaders = tracker.get_batting_leaders("home_runs", limit=5)
    if hr_leaders:
        print("\nHome Run Leaders:")
        for player in hr_leaders:
            print(f"  {player['player_name']}: {player['home_runs']} HR")
    else:
        print("\nNo home run leaders (might need more games)")
    
    # RBI leaders
    rbi_leaders = tracker.get_batting_leaders("rbi", limit=5)
    if rbi_leaders:
        print("\nRBI Leaders:")
        for player in rbi_leaders:
            print(f"  {player['player_name']}: {player['rbi']} RBI")
    
    # Hits leaders
    hit_leaders = tracker.get_batting_leaders("hits", limit=5)
    if hit_leaders:
        print("\nHits Leaders:")
        for player in hit_leaders:
            print(f"  {player['player_name']}: {player['hits']} H in {player.get('at_bats', '?')} AB")
    
    # Pitching leaders
    print(f"\n{'='*70}")
    print("PITCHING LEADERS")
    print("="*70)
    
    k_leaders = tracker.get_pitching_leaders("strikeouts", limit=5)
    if k_leaders:
        print("\nStrikeout Leaders:")
        for player in k_leaders:
            print(f"  {player['player_name']}: {player['strikeouts']} K")
    
    # Test season summary
    summary = tracker.get_season_summary()
    if summary:
        print(f"\nSeason Summary:")
        print(f"  Total games: {summary.get('total_games', 0)}")
        print(f"  Total runs: {summary.get('total_runs', 0)}")
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
