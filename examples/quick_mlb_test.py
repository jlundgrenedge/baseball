"""
Quick MLB Teams Test

A streamlined way to run 5-10 games with real MLB teams from the database.
This is the recommended testing method for game logic validation.

Usage:
    python examples/quick_mlb_test.py              # Interactive team selection
    python examples/quick_mlb_test.py 5            # Run 5 games (interactive teams)
    python examples/quick_mlb_test.py 10 --quiet   # 10 games, minimal output
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator, PitcherRotation
from batted_ball.series_metrics import SeriesMetrics


def get_default_teams(loader: TeamLoader):
    """
    Get a reasonable default matchup from available teams.
    Tries to find teams from the same season.
    """
    teams = loader.db.list_teams()
    if not teams:
        return None, None
    
    # Group by season
    by_season = {}
    for t in teams:
        season = t['season']
        if season not in by_season:
            by_season[season] = []
        by_season[season].append(t)
    
    # Get most recent season with at least 2 teams
    for season in sorted(by_season.keys(), reverse=True):
        if len(by_season[season]) >= 2:
            sorted_teams = sorted(by_season[season], key=lambda x: x['team_name'])
            return (
                (sorted_teams[0]['team_name'], season),
                (sorted_teams[1]['team_name'], season)
            )
    
    return None, None


def select_team_interactive(loader: TeamLoader, prompt: str):
    """Simple interactive team selection."""
    teams = loader.db.list_teams()
    if not teams:
        print("\n❌ No teams in database!")
        print("   Run: game_simulation.bat → Option 5 to add teams")
        return None
    
    print(f"\n{prompt}:")
    for i, t in enumerate(sorted(teams, key=lambda x: (x['season'], x['team_name'])), 1):
        print(f"  {i}. {t['team_name']} ({t['season']})")
    
    try:
        choice = int(input("\nEnter number: "))
        sorted_teams = sorted(teams, key=lambda x: (x['season'], x['team_name']))
        if 1 <= choice <= len(sorted_teams):
            t = sorted_teams[choice - 1]
            return (t['team_name'], t['season'])
    except (ValueError, KeyboardInterrupt):
        pass
    
    return None


def run_quick_test(num_games: int = 5, quiet: bool = False, interactive: bool = True):
    """
    Run a quick test series with MLB teams.
    
    Parameters
    ----------
    num_games : int
        Number of games to simulate (5-10 recommended)
    quiet : bool
        If True, minimal console output
    interactive : bool
        If True, prompt for team selection
    """
    # Limit games to reasonable range
    num_games = max(1, min(num_games, 10))
    
    print(f"\n{'='*60}")
    print("QUICK MLB TEST")
    print(f"{'='*60}")
    
    # Check database
    db_path = Path("baseball_teams.db")
    if not db_path.exists():
        print("\n❌ Database not found: baseball_teams.db")
        print("   Run: game_simulation.bat → Option 5 to create")
        return
    
    loader = TeamLoader()
    
    try:
        # Get teams
        if interactive:
            away_info = select_team_interactive(loader, "Select AWAY team")
            if not away_info:
                return
            home_info = select_team_interactive(loader, "Select HOME team")
            if not home_info:
                return
        else:
            away_info, home_info = get_default_teams(loader)
            if not away_info or not home_info:
                print("\n❌ Need at least 2 teams in database")
                return
        
        # Load teams
        print(f"\nLoading {away_info[0]} vs {home_info[0]}...")
        away_team = loader.load_team(away_info[0], away_info[1])
        home_team = loader.load_team(home_info[0], home_info[1])
        
        if not away_team or not home_team:
            print("\n❌ Failed to load teams")
            return
        
        # Setup
        print(f"\n{'='*60}")
        print(f"SIMULATING {num_games} GAMES")
        print(f"{'='*60}")
        print(f"Away: {away_team.name}")
        print(f"Home: {home_team.name}")
        print()
        
        # Create log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = Path("game_logs") / f"quick_test_{timestamp}.txt"
        log_path.parent.mkdir(exist_ok=True)
        
        # Series tracking
        series = SeriesMetrics(
            away_team_name=away_team.name,
            home_team_name=home_team.name
        )
        
        # Pitcher rotations
        away_rotation = PitcherRotation(away_team, num_starters=5)
        home_rotation = PitcherRotation(home_team, num_starters=5)
        
        # Run games
        with open(log_path, 'w', encoding='utf-8') as log:
            log.write(f"Quick MLB Test: {away_team.name} @ {home_team.name}\n")
            log.write(f"Games: {num_games} | Date: {datetime.now()}\n")
            log.write("="*60 + "\n\n")
            
            for i in range(num_games):
                print(f"Game {i+1}/{num_games}...", end=" ", flush=True)
                
                # Reset pitchers
                away_team.reset_pitcher_state()
                home_team.reset_pitcher_state()
                
                # Set starters
                away_starter = away_rotation.get_game_starter()
                home_starter = home_rotation.get_game_starter()
                away_rotation.set_game_starter(away_team, away_starter)
                home_rotation.set_game_starter(home_team, home_starter)
                
                # Simulate (quiet mode - no console output)
                import io
                old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                
                try:
                    sim = GameSimulator(
                        away_team, home_team,
                        verbose=not quiet,
                        debug_metrics=0 if quiet else 2,
                        wind_enabled=True,
                        starter_innings=5
                    )
                    result = sim.simulate_game(num_innings=9)
                finally:
                    game_output = sys.stdout.getvalue()
                    sys.stdout = old_stdout
                
                # Log full output
                log.write(f"\n--- GAME {i+1} ---\n")
                log.write(game_output)
                
                # Update series
                series.update_from_game(result)
                
                # Print score
                winner = "←" if result.away_score > result.home_score else "→"
                print(f"{result.away_score}-{result.home_score} {winner}")
        
        # Summary
        print(f"\n{'='*60}")
        print("SERIES SUMMARY")
        print(f"{'='*60}")
        series.print_summary()
        
        print(f"\n✅ Full log saved: {log_path}")
        print(f"   Size: {log_path.stat().st_size / 1024:.1f} KB")
        
    finally:
        loader.close()


def main():
    parser = argparse.ArgumentParser(
        description="Quick MLB test - simulate 5-10 games with real teams"
    )
    parser.add_argument(
        'games', nargs='?', type=int, default=5,
        help="Number of games (1-10, default: 5)"
    )
    parser.add_argument(
        '--quiet', '-q', action='store_true',
        help="Minimal output (still saves full log)"
    )
    parser.add_argument(
        '--auto', '-a', action='store_true',
        help="Auto-select teams (no prompts)"
    )
    
    args = parser.parse_args()
    
    run_quick_test(
        num_games=args.games,
        quiet=args.quiet,
        interactive=not args.auto
    )


if __name__ == "__main__":
    main()
