"""
Randomized team simulation for unbiased testing.

Each game uses:
- Random away team
- Random home team (different from away)
- Random starting pitcher from each team's rotation
- Home team's ballpark
- Randomized wind conditions

This provides a more neutral test across the full range of 
player attributes in the database.
"""

import sys
import random
from pathlib import Path
from datetime import datetime
from typing import List, Tuple
import sqlite3

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator, PitcherRotation
from batted_ball.series_metrics import SeriesMetrics


# Map team abbreviations to their home ballpark
TEAM_BALLPARKS = {
    'CHC': 'wrigley',
    'CIN': 'great_american',
    'NYY': 'yankee',
    'BOS': 'fenway',
    'LAD': 'dodger',
    'SF': 'oracle',
    'SFG': 'oracle',
    'COL': 'coors',
    'HOU': 'minute_maid',
    'SD': 'petco',
    'SDP': 'petco',
    # Default to 'generic' for others
}


def get_all_teams() -> List[Tuple[str, str, int]]:
    """
    Get all teams from the database.
    
    Returns
    -------
    list of tuples
        Each tuple is (team_name, team_abbr, season)
    """
    conn = sqlite3.connect('baseball_teams.db')
    cursor = conn.cursor()
    cursor.execute("SELECT team_name, team_abbr, season FROM teams")
    teams = cursor.fetchall()
    conn.close()
    return teams


def get_team_ballpark(team_abbr: str) -> str:
    """Get the home ballpark for a team."""
    return TEAM_BALLPARKS.get(team_abbr.upper(), 'generic')


def simulate_random_games(num_games: int, verbose_console: bool = False):
    """
    Simulate games with random team matchups.
    
    Parameters
    ----------
    num_games : int
        Number of games to simulate
    verbose_console : bool
        If True, show game output in console (for small runs)
    """
    # Get all available teams
    all_teams = get_all_teams()
    
    if len(all_teams) < 2:
        print("❌ Need at least 2 teams in database!")
        return
    
    print(f"\n📊 Found {len(all_teams)} teams in database")
    print(f"🎲 Simulating {num_games} games with random matchups\n")
    
    # Create log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"game_log_RANDOM_{num_games}_games_{timestamp}.txt"
    log_path = Path("game_logs") / log_filename
    log_path.parent.mkdir(exist_ok=True)
    
    print(f"📝 Game log: {log_path}\n")
    
    # Initialize aggregated metrics
    # We'll track combined stats across all teams
    total_away_runs = 0
    total_home_runs = 0
    total_games = 0
    
    # Team loader (keep open for efficiency)
    loader = TeamLoader()
    
    # Cache loaded teams to avoid reloading
    team_cache = {}
    
    # Track matchups for the log
    matchup_history = []
    
    # Open log file
    with open(log_path, 'w', encoding='utf-8') as log_file:
        # Write header
        log_file.write(f"{'='*80}\n")
        log_file.write(f"RANDOMIZED GAME SERIES LOG\n")
        log_file.write(f"{'='*80}\n")
        log_file.write(f"Total Games: {num_games}\n")
        log_file.write(f"Teams in Pool: {len(all_teams)}\n")
        log_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Mode: Random teams, random starters each game\n")
        log_file.write(f"{'='*80}\n\n")
        log_file.flush()
        
        # Create series metrics for aggregate tracking
        series_metrics = SeriesMetrics(
            away_team_name="Various (Away)",
            home_team_name="Various (Home)"
        )
        
        for game_num in range(1, num_games + 1):
            # Pick two random different teams
            away_team_info, home_team_info = random.sample(all_teams, 2)
            away_name, away_abbr, away_season = away_team_info
            home_name, home_abbr, home_season = home_team_info
            
            print(f"Game {game_num}/{num_games}: {away_name} @ {home_name}")
            
            # Load teams (from cache if available)
            cache_key_away = (away_name, away_season)
            cache_key_home = (home_name, home_season)
            
            if cache_key_away not in team_cache:
                team_cache[cache_key_away] = loader.load_team(away_name, away_season)
            if cache_key_home not in team_cache:
                team_cache[cache_key_home] = loader.load_team(home_name, home_season)
            
            away_team = team_cache[cache_key_away]
            home_team = team_cache[cache_key_home]
            
            if not away_team or not home_team:
                print(f"  ⚠️ Failed to load teams, skipping...")
                continue
            
            # Reset pitcher states
            away_team.reset_pitcher_state()
            home_team.reset_pitcher_state()
            
            # Pick random starting pitchers
            away_starters = away_team.get_starters()
            home_starters = home_team.get_starters()
            
            if away_starters:
                away_starter = random.choice(away_starters[:min(5, len(away_starters))])
                # Set as the active pitcher
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
            
            away_sp_name = away_team.pitchers[0].name if away_team.pitchers else "Unknown"
            home_sp_name = home_team.pitchers[0].name if home_team.pitchers else "Unknown"
            
            print(f"  Starters: {away_sp_name} vs {home_sp_name}")
            
            # Get home team's ballpark
            ballpark = get_team_ballpark(home_abbr)
            
            # Write game header to log
            log_file.write(f"\n{'#'*80}\n")
            log_file.write(f"# GAME {game_num} of {num_games}\n")
            log_file.write(f"# {away_name} @ {home_name}\n")
            log_file.write(f"# Starters: {away_sp_name} vs {home_sp_name}\n")
            log_file.write(f"# Ballpark: {ballpark}\n")
            log_file.write(f"{'#'*80}\n\n")
            log_file.flush()
            
            # Create simulator
            sim = GameSimulator(
                away_team,
                home_team,
                verbose=True,
                debug_metrics=3,
                ballpark=ballpark,
                wind_enabled=True,
                starter_innings=5
            )
            
            # Capture output
            import io
            old_stdout = sys.stdout
            captured_output = io.StringIO()
            
            if verbose_console:
                class Tee:
                    def __init__(self, *streams):
                        self.streams = streams
                    def write(self, data):
                        for s in self.streams:
                            s.write(data)
                    def flush(self):
                        for s in self.streams:
                            s.flush()
                sys.stdout = Tee(old_stdout, captured_output)
            else:
                sys.stdout = captured_output
            
            try:
                final_state = sim.simulate_game(num_innings=9)
            finally:
                sys.stdout = old_stdout
                log_file.write(captured_output.getvalue())
                log_file.flush()
            
            # Update metrics
            series_metrics.update_from_game(final_state)
            
            total_away_runs += final_state.away_score
            total_home_runs += final_state.home_score
            total_games += 1
            
            # Track matchup
            matchup_history.append({
                'away': away_name,
                'home': home_name,
                'away_score': final_state.away_score,
                'home_score': final_state.home_score
            })
            
            # Show score
            winner = away_name if final_state.away_score > final_state.home_score else home_name
            print(f"  Final: {away_name} {final_state.away_score}, {home_name} {final_state.home_score} ({winner} wins)")
        
        # Write summary to log
        import io
        old_stdout = sys.stdout
        summary_output = io.StringIO()
        sys.stdout = summary_output
        
        try:
            series_metrics.print_summary()
        finally:
            sys.stdout = old_stdout
        
        log_file.write("\n\n")
        log_file.write(summary_output.getvalue())
        
        # Write matchup history
        log_file.write("\n\n")
        log_file.write("=" * 80 + "\n")
        log_file.write("MATCHUP HISTORY\n")
        log_file.write("=" * 80 + "\n\n")
        for i, m in enumerate(matchup_history, 1):
            log_file.write(f"Game {i}: {m['away']} {m['away_score']} @ {m['home']} {m['home_score']}\n")
        
        log_file.flush()
    
    loader.close()
    
    # Print summary to console
    print("\n" + "=" * 70)
    print("  RANDOMIZED SERIES COMPLETE")
    print("=" * 70)
    series_metrics.print_summary()
    
    print(f"\n✅ Complete game log saved to: {log_path}")
    print(f"   File size: {log_path.stat().st_size / 1024:.1f} KB")


def main():
    """Main entry point with interactive prompts."""
    # Check for command-line argument (for automated testing)
    if len(sys.argv) > 1:
        try:
            num_games = int(sys.argv[1])
            if 1 <= num_games <= 500:
                print(f"\n🎲 Running {num_games} randomized games (command-line mode)...")
                simulate_random_games(num_games, verbose_console=(num_games <= 3))
                return
        except ValueError:
            pass
    
    print("\n" + "=" * 70)
    print("  RANDOMIZED TEAM SIMULATION")
    print("=" * 70)
    print("\nThis mode randomly selects teams for each game,")
    print("providing unbiased testing across all MLB teams.\n")
    
    # Check database exists
    if not Path("baseball_teams.db").exists():
        print("❌ Database not found! Run option 5 first to add teams.")
        return
    
    # Get number of games
    while True:
        try:
            choice = input("Number of games to simulate (1-500, 0 to cancel): ").strip()
            if choice == '0':
                print("Cancelled.")
                return
            num_games = int(choice)
            if 1 <= num_games <= 500:
                break
            print("Please enter 1-500.")
        except ValueError:
            print("Invalid input.")
    
    # Confirm
    print(f"\nWill simulate {num_games} games with random team matchups.")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Run simulation
    verbose = num_games <= 3
    simulate_random_games(num_games, verbose_console=verbose)
    
    input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
