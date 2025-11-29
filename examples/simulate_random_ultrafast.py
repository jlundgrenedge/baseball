#!/usr/bin/env python3
"""
Ultra-fast random team simulation.

Uses SimulationMode.ULTRA_FAST for ~5x trajectory speedup.
Only shows summary statistics at the end (no play-by-play output).
Designed for high-volume simulation testing.
"""

import sys
import os
import random
import time
import warnings
import contextlib
import io
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.game_simulation import GameSimulator
from batted_ball.ballpark import get_ballpark
from batted_ball.series_metrics import SeriesMetrics
from batted_ball.constants import SimulationMode
from batted_ball.database.team_loader import TeamLoader


def get_all_teams():
    """Get list of all teams in database."""
    import sqlite3
    db_path = Path("baseball_teams.db")
    if not db_path.exists():
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT team_name, team_abbr, season FROM teams")
    teams = cursor.fetchall()
    conn.close()
    return teams


def get_team_ballpark(team_abbr: str) -> str:
    """Map team abbreviation to ballpark name."""
    ballpark_map = {
        'ARI': 'chase_field', 'ATL': 'truist_park', 'BAL': 'camden_yards',
        'BOS': 'fenway_park', 'CHC': 'wrigley_field', 'CWS': 'guaranteed_rate',
        'CIN': 'gabp', 'CLE': 'progressive_field', 'COL': 'coors_field',
        'DET': 'comerica_park', 'HOU': 'minute_maid', 'KC': 'kauffman_stadium',
        'LAA': 'angel_stadium', 'LAD': 'dodger_stadium', 'MIA': 'marlins_park',
        'MIL': 'american_family', 'MIN': 'target_field', 'NYM': 'citi_field',
        'NYY': 'yankee_stadium', 'OAK': 'oakland_coliseum', 'PHI': 'citizens_bank',
        'PIT': 'pnc_park', 'SD': 'petco_park', 'SF': 'oracle_park',
        'SEA': 'safeco_field', 'STL': 'busch_stadium', 'TB': 'tropicana_field',
        'TEX': 'globe_life', 'TOR': 'rogers_centre', 'WSH': 'nationals_park'
    }
    return ballpark_map.get(team_abbr, 'generic')


def simulate_ultrafast(num_games: int, simulation_mode: SimulationMode = SimulationMode.ULTRA_FAST):
    """
    Run ultra-fast random team simulation.
    
    Args:
        num_games: Number of games to simulate
        simulation_mode: SimulationMode.ULTRA_FAST (default) or SimulationMode.EXTREME
    """
    # Get available teams
    teams = get_all_teams()
    if not teams:
        print("❌ No teams found in database!")
        return
    
    mode_name = simulation_mode.name
    print(f"\n⚡ ULTRA-FAST RANDOM SIMULATION ({mode_name} mode)")
    print("=" * 60)
    print(f"Games to simulate: {num_games}")
    print(f"Teams available: {len(teams)}")
    print(f"Simulation mode: {mode_name}")
    print("=" * 60)
    
    # Initialize
    loader = TeamLoader()
    series_metrics = SeriesMetrics()
    team_cache = {}
    
    start_time = time.time()
    games_completed = 0
    
    print(f"\n🎲 Simulating {num_games} games...\n")
    
    # Suppress team loading warnings for cleaner output
    print("  (Loading teams quietly...)")
    
    # Progress tracking
    update_interval = max(1, num_games // 20)  # Update every 5%
    
    for game_num in range(1, num_games + 1):
        # Select random teams
        away_team_info, home_team_info = random.sample(teams, 2)
        away_name, away_abbr, away_season = away_team_info
        home_name, home_abbr, home_season = home_team_info
        
        # Load teams (with caching) - suppress verbose output
        cache_key_away = (away_name, away_season)
        cache_key_home = (home_name, home_season)
        
        # Redirect stdout to suppress team loading messages
        with contextlib.redirect_stdout(io.StringIO()):
            if cache_key_away not in team_cache:
                team_cache[cache_key_away] = loader.load_team(away_name, away_season)
            if cache_key_home not in team_cache:
                team_cache[cache_key_home] = loader.load_team(home_name, home_season)
        
        away_team = team_cache[cache_key_away]
        home_team = team_cache[cache_key_home]
        
        if not away_team or not home_team:
            continue
        
        # Reset pitcher states
        away_team.reset_pitcher_state()
        home_team.reset_pitcher_state()
        
        # Pick random starting pitchers
        away_starters = away_team.get_starters()
        home_starters = home_team.get_starters()
        
        if away_starters:
            away_starter = random.choice(away_starters[:min(5, len(away_starters))])
            for i, p in enumerate(away_team.pitchers):
                if p.name == away_starter.name:
                    away_team.pitchers[0], away_team.pitchers[i] = away_team.pitchers[i], away_team.pitchers[0]
                    break
        
        if home_starters:
            home_starter = random.choice(home_starters[:min(5, len(home_starters))])
            for i, p in enumerate(home_team.pitchers):
                if p.name == home_starter.name:
                    home_team.pitchers[0], home_team.pitchers[i] = home_team.pitchers[i], home_team.pitchers[0]
                    break
        
        # Get home team's ballpark
        ballpark = get_team_ballpark(home_abbr)
        
        # Create simulator with ultra-fast mode, suppress ballpark warnings
        with contextlib.redirect_stdout(io.StringIO()):
            sim = GameSimulator(
                away_team,
                home_team,
                verbose=False,  # No play-by-play output
                debug_metrics=0,  # No debug output
                ballpark=ballpark,
                wind_enabled=True,
                starter_innings=5,
                simulation_mode=simulation_mode
            )
            
            # Simulate game
            final_state = sim.simulate_game(num_innings=9)
        
        # Update metrics
        series_metrics.update_from_game(final_state)
        games_completed += 1
        
        # Progress update
        if game_num % update_interval == 0 or game_num == num_games:
            elapsed = time.time() - start_time
            rate = games_completed / (elapsed / 60) if elapsed > 0 else 0
            pct = (game_num / num_games) * 100
            print(f"  Progress: {game_num:4d}/{num_games} ({pct:5.1f}%) - {rate:.1f} games/min")
    
    loader.close()
    
    # Calculate timing
    elapsed = time.time() - start_time
    games_per_min = games_completed / (elapsed / 60) if elapsed > 0 else 0
    
    # Print summary
    print("\n" + "=" * 60)
    print(f"  ⚡ ULTRA-FAST SIMULATION COMPLETE ({mode_name})")
    print("=" * 60)
    print(f"\n⏱️  Timing:")
    print(f"   Total time: {elapsed:.1f} seconds ({elapsed/60:.1f} minutes)")
    print(f"   Games completed: {games_completed}")
    print(f"   Speed: {games_per_min:.1f} games/minute")
    
    # Print comprehensive statistics
    series_metrics.print_summary()


def main():
    """Main entry point."""
    # Check for command-line arguments
    num_games = 50  # Default
    mode = SimulationMode.ULTRA_FAST
    
    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
            if not 1 <= num_games <= 1000:
                print("Number of games must be 1-1000")
                return
        except ValueError:
            pass
    
    if len(sys.argv) > 2:
        mode_arg = sys.argv[2].upper()
        if mode_arg == "EXTREME":
            mode = SimulationMode.EXTREME
        elif mode_arg == "ULTRA_FAST":
            mode = SimulationMode.ULTRA_FAST
        elif mode_arg == "FAST":
            mode = SimulationMode.FAST
    
    # Interactive mode if no args
    if len(sys.argv) == 1:
        print("\n" + "=" * 60)
        print("  ⚡ ULTRA-FAST RANDOM SIMULATION")
        print("=" * 60)
        print("\nThis mode uses optimized physics for maximum speed.")
        print("Only summary statistics are shown (no play-by-play).\n")
        
        # Check database exists
        if not Path("baseball_teams.db").exists():
            print("❌ Database not found! Run option 5 first to add teams.")
            return
        
        # Get number of games
        while True:
            try:
                choice = input("Number of games to simulate (1-1000, 0 to cancel): ").strip()
                if choice == '0':
                    print("Cancelled.")
                    return
                num_games = int(choice)
                if 1 <= num_games <= 1000:
                    break
                print("Please enter 1-1000.")
            except ValueError:
                print("Invalid input.")
        
        # Get mode
        print("\nSimulation modes:")
        print("  1. ULTRA_FAST (5x faster, recommended)")
        print("  2. EXTREME (10x faster, slightly less accurate)")
        mode_choice = input("Select mode (1-2, default=1): ").strip()
        if mode_choice == '2':
            mode = SimulationMode.EXTREME
        
        # Confirm
        print(f"\nWill simulate {num_games} games in {mode.name} mode.")
        confirm = input("Proceed? (y/n): ").strip().lower()
        if confirm != 'y':
            print("Cancelled.")
            return
    
    # Run simulation
    simulate_ultrafast(num_games, mode)
    
    if len(sys.argv) == 1:
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
