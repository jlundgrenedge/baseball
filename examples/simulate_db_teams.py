"""
Interactive team selection and game simulation from database.

Allows users to:
1. Select two teams from baseball_teams.db
2. Choose number of games to simulate
3. Run simulations and view results
"""

import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass, field

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database.team_loader import TeamLoader
from batted_ball.game_simulation import GameSimulator


@dataclass
class TeamStatistics:
    """Aggregate statistics for a team across multiple games"""
    # Game results
    wins: int = 0
    losses: int = 0
    total_runs: int = 0

    # Batting statistics
    hits: int = 0
    singles: int = 0
    doubles: int = 0
    triples: int = 0
    home_runs: int = 0
    strikeouts: int = 0
    walks: int = 0
    at_bats: int = 0

    # Batted ball type distribution
    ground_balls: int = 0
    line_drives: int = 0
    fly_balls: int = 0

    # Physics-based statistics
    exit_velocities: List[float] = field(default_factory=list)
    launch_angles: List[float] = field(default_factory=list)

    # Defensive statistics
    errors: int = 0

    # Pitching statistics
    total_pitches: int = 0

    def batting_average(self) -> float:
        """Calculate batting average"""
        if self.at_bats == 0:
            return 0.0
        return self.hits / self.at_bats

    def on_base_percentage(self) -> float:
        """Calculate on-base percentage"""
        pa = self.at_bats + self.walks  # Plate appearances (simplified)
        if pa == 0:
            return 0.0
        return (self.hits + self.walks) / pa

    def slugging_percentage(self) -> float:
        """Calculate slugging percentage"""
        if self.at_bats == 0:
            return 0.0
        total_bases = (self.singles + 2*self.doubles + 3*self.triples + 4*self.home_runs)
        return total_bases / self.at_bats

    def avg_exit_velocity(self) -> float:
        """Calculate average exit velocity"""
        if not self.exit_velocities:
            return 0.0
        return sum(self.exit_velocities) / len(self.exit_velocities)

    def avg_launch_angle(self) -> float:
        """Calculate average launch angle"""
        if not self.launch_angles:
            return 0.0
        return sum(self.launch_angles) / len(self.launch_angles)

    def ground_ball_percentage(self) -> float:
        """Calculate ground ball percentage"""
        total_balls = self.ground_balls + self.line_drives + self.fly_balls
        if total_balls == 0:
            return 0.0
        return (self.ground_balls / total_balls) * 100

    def fly_ball_percentage(self) -> float:
        """Calculate fly ball percentage"""
        total_balls = self.ground_balls + self.line_drives + self.fly_balls
        if total_balls == 0:
            return 0.0
        return (self.fly_balls / total_balls) * 100

    def line_drive_percentage(self) -> float:
        """Calculate line drive percentage"""
        total_balls = self.ground_balls + self.line_drives + self.fly_balls
        if total_balls == 0:
            return 0.0
        return (self.line_drives / total_balls) * 100


def clear_screen():
    """Clear the console screen."""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')


def display_header(title: str):
    """Display a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def select_team(loader: TeamLoader, prompt: str) -> Optional[tuple]:
    """
    Display team list and let user select one.

    Returns
    -------
    tuple or None
        (team_name, season) or None if cancelled
    """
    teams = loader.db.list_teams()

    if not teams:
        print("\n❌ No teams found in database!")
        print("\nTo add teams, use:")
        print("  python -m batted_ball.database.team_database")
        print("  or run examples/simulate_mlb_teams.py")
        return None

    # Group teams by season
    seasons = {}
    for team in teams:
        season = team['season']
        if season not in seasons:
            seasons[season] = []
        seasons[season].append(team)

    while True:
        display_header(prompt)
        print("\nAvailable teams:\n")

        # Display teams grouped by season
        idx = 1
        team_map = {}
        for season in sorted(seasons.keys(), reverse=True):
            print(f"\n  {season} Season:")
            for team in sorted(seasons[season], key=lambda t: t['team_name']):
                print(f"    {idx}. {team['team_name']}")
                team_map[idx] = (team['team_name'], team['season'])
                idx += 1

        print(f"\n    0. Cancel")
        print()

        try:
            choice = input("Enter team number: ").strip()

            if choice == '0':
                return None

            choice_num = int(choice)
            if choice_num in team_map:
                return team_map[choice_num]
            else:
                print(f"\n❌ Invalid choice. Please enter 1-{len(team_map)} or 0 to cancel.")
                input("\nPress Enter to continue...")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input.")
            input("\nPress Enter to continue...")


def get_num_games() -> Optional[int]:
    """
    Get number of games to simulate from user.

    Returns
    -------
    int or None
        Number of games, or None if cancelled
    """
    while True:
        display_header("Select Number of Games")
        print("\nHow many games would you like to simulate?")
        print("\n  Recommendations:")
        print("    1-10   : Quick test (~10-60 seconds)")
        print("    11-50  : Small series (~1-5 minutes)")
        print("    51-162 : Full season (~5-30 minutes)")
        print("\n  0. Cancel")
        print()

        try:
            choice = input("Enter number of games (1-500): ").strip()

            if choice == '0':
                return None

            num_games = int(choice)
            if 1 <= num_games <= 500:
                return num_games
            else:
                print("\n❌ Please enter a number between 1 and 500.")
                input("\nPress Enter to continue...")
        except (ValueError, KeyboardInterrupt):
            print("\n❌ Invalid input.")
            input("\nPress Enter to continue...")


def simulate_games(away_team_info: tuple, home_team_info: tuple, num_games: int):
    """
    Load teams from database and simulate games.

    Parameters
    ----------
    away_team_info : tuple
        (team_name, season) for away team
    home_team_info : tuple
        (team_name, season) for home team
    num_games : int
        Number of games to simulate
    """
    away_name, away_season = away_team_info
    home_name, home_season = home_team_info

    display_header("Loading Teams")

    # Load teams from database
    print(f"\nLoading {away_name} ({away_season})...")
    loader = TeamLoader()
    away_team = loader.load_team(away_name, away_season)

    if not away_team:
        print(f"\n❌ Failed to load {away_name}")
        loader.close()
        return

    print(f"\nLoading {home_name} ({home_season})...")
    home_team = loader.load_team(home_name, home_season)

    if not home_team:
        print(f"\n❌ Failed to load {home_name}")
        loader.close()
        return

    loader.close()

    # Display matchup
    display_header("Matchup")
    print(f"\n  Away: {away_team.name} ({away_season})")
    print(f"  Home: {home_team.name} ({home_season})")
    print(f"  Games: {num_games}")
    print()

    # Confirm before running
    confirm = input("Start simulation? (y/n): ").strip().lower()
    if confirm != 'y':
        print("\n❌ Simulation cancelled.")
        return

    # Create log file for game output
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_away = away_name.replace(" ", "_")
    safe_home = home_name.replace(" ", "_")
    log_filename = f"game_log_{safe_away}_vs_{safe_home}_{timestamp}.txt"
    log_path = Path("game_logs") / log_filename

    # Create game_logs directory if it doesn't exist
    log_path.parent.mkdir(exist_ok=True)

    # Run simulations
    display_header(f"Simulating {num_games} Game{'s' if num_games > 1 else ''}")
    print(f"\n📝 Game log will be saved to: {log_path}")
    print()

    # Initialize statistics trackers
    away_stats = TeamStatistics()
    home_stats = TeamStatistics()

    # Determine verbosity based on number of games
    # For 1-3 games: show in console
    # For 4+ games: only save to log file
    show_in_console = num_games <= 3

    # Open the log file for the entire series
    with open(log_path, 'w', encoding='utf-8') as log_file:
        # Write header to log file
        log_file.write(f"{'='*80}\n")
        log_file.write(f"GAME SERIES LOG\n")
        log_file.write(f"{'='*80}\n")
        log_file.write(f"Away Team: {away_team.name} ({away_season})\n")
        log_file.write(f"Home Team: {home_team.name} ({home_season})\n")
        log_file.write(f"Number of Games: {num_games}\n")
        log_file.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"{'='*80}\n\n")
        log_file.flush()

        for i in range(num_games):
            if num_games > 1:
                print(f"\nGame {i+1}/{num_games}:")
                print("-" * 50)

            # Write game separator to log file
            log_file.write(f"\n\n{'#'*80}\n")
            log_file.write(f"# GAME {i+1} of {num_games}\n")
            log_file.write(f"{'#'*80}\n\n")
            log_file.flush()

            # Create simulator with verbose=True (no log_file to avoid truncation)
            sim = GameSimulator(away_team, home_team, verbose=True)

            # Capture stdout to write to log file
            import io
            import sys
            old_stdout = sys.stdout
            captured_output = io.StringIO()

            # If we want console output, use a Tee to write to both
            if show_in_console:
                class Tee:
                    def __init__(self, *streams):
                        self.streams = streams
                    def write(self, data):
                        for stream in self.streams:
                            stream.write(data)
                    def flush(self):
                        for stream in self.streams:
                            stream.flush()

                sys.stdout = Tee(old_stdout, captured_output)
            else:
                # Only capture, don't show in console
                sys.stdout = captured_output

            try:
                # Simulate game
                final_state = sim.simulate_game(num_innings=9)
            finally:
                # Restore stdout
                sys.stdout = old_stdout

                # Write captured output to log file
                game_output = captured_output.getvalue()
                log_file.write(game_output)
                log_file.flush()

            # Aggregate statistics from game state
            # Away team stats
            away_stats.total_runs += final_state.away_score
            away_stats.hits += final_state.away_hits
            away_stats.singles += final_state.away_singles
            away_stats.doubles += final_state.away_doubles
            away_stats.triples += final_state.away_triples
            away_stats.home_runs += final_state.away_home_runs
            away_stats.strikeouts += final_state.away_strikeouts
            away_stats.walks += final_state.away_walks
            away_stats.at_bats += final_state.away_at_bats
            away_stats.ground_balls += final_state.away_ground_balls
            away_stats.line_drives += final_state.away_line_drives
            away_stats.fly_balls += final_state.away_fly_balls
            away_stats.exit_velocities.extend(final_state.away_exit_velocities)
            away_stats.launch_angles.extend(final_state.away_launch_angles)
            away_stats.errors += final_state.away_errors

            # Home team stats
            home_stats.total_runs += final_state.home_score
            home_stats.hits += final_state.home_hits
            home_stats.singles += final_state.home_singles
            home_stats.doubles += final_state.home_doubles
            home_stats.triples += final_state.home_triples
            home_stats.home_runs += final_state.home_home_runs
            home_stats.strikeouts += final_state.home_strikeouts
            home_stats.walks += final_state.home_walks
            home_stats.at_bats += final_state.home_at_bats
            home_stats.ground_balls += final_state.home_ground_balls
            home_stats.line_drives += final_state.home_line_drives
            home_stats.fly_balls += final_state.home_fly_balls
            home_stats.exit_velocities.extend(final_state.home_exit_velocities)
            home_stats.launch_angles.extend(final_state.home_launch_angles)
            home_stats.errors += final_state.home_errors

            # Total pitches
            away_stats.total_pitches += final_state.total_pitches
            home_stats.total_pitches += final_state.total_pitches

            # Track wins/losses
            if final_state.away_score > final_state.home_score:
                away_stats.wins += 1
                home_stats.losses += 1
                winner = away_team.name
            else:
                home_stats.wins += 1
                away_stats.losses += 1
                winner = home_team.name

            # Display score summary (always shown)
            print(f"\nFinal Score:")
            print(f"  {away_team.name}: {final_state.away_score}")
            print(f"  {home_team.name}: {final_state.home_score}")
            print(f"  Winner: {winner}")

        # Write series summary to log file
        log_file.write(f"\n\n{'='*80}\n")
        log_file.write(f"SERIES SUMMARY\n")
        log_file.write(f"{'='*80}\n\n")

        # Away team statistics
        log_file.write(f"{away_team.name} ({away_season}):\n")
        log_file.write(f"{'='*60}\n")
        log_file.write(f"  Record: {away_stats.wins}-{away_stats.losses}\n")
        log_file.write(f"  Total Runs: {away_stats.total_runs} ({away_stats.total_runs/num_games:.2f} per game)\n\n")

        log_file.write(f"  BATTING STATISTICS:\n")
        log_file.write(f"    At-Bats: {away_stats.at_bats}\n")
        log_file.write(f"    Hits: {away_stats.hits} (AVG: {away_stats.batting_average():.3f})\n")
        log_file.write(f"      Singles: {away_stats.singles}\n")
        log_file.write(f"      Doubles: {away_stats.doubles}\n")
        log_file.write(f"      Triples: {away_stats.triples}\n")
        log_file.write(f"      Home Runs: {away_stats.home_runs}\n")
        log_file.write(f"    Walks: {away_stats.walks}\n")
        log_file.write(f"    Strikeouts: {away_stats.strikeouts}\n")
        log_file.write(f"    On-Base Percentage: {away_stats.on_base_percentage():.3f}\n")
        log_file.write(f"    Slugging Percentage: {away_stats.slugging_percentage():.3f}\n\n")

        log_file.write(f"  BATTED BALL DISTRIBUTION:\n")
        log_file.write(f"    Ground Balls: {away_stats.ground_balls} ({away_stats.ground_ball_percentage():.1f}%)\n")
        log_file.write(f"    Line Drives: {away_stats.line_drives} ({away_stats.line_drive_percentage():.1f}%)\n")
        log_file.write(f"    Fly Balls: {away_stats.fly_balls} ({away_stats.fly_ball_percentage():.1f}%)\n\n")

        log_file.write(f"  PHYSICS-BASED METRICS:\n")
        log_file.write(f"    Avg Exit Velocity: {away_stats.avg_exit_velocity():.1f} mph\n")
        log_file.write(f"    Avg Launch Angle: {away_stats.avg_launch_angle():.1f}°\n\n")

        log_file.write(f"  DEFENSIVE STATISTICS:\n")
        log_file.write(f"    Errors: {away_stats.errors}\n\n")

        # Home team statistics
        log_file.write(f"{home_team.name} ({home_season}):\n")
        log_file.write(f"{'='*60}\n")
        log_file.write(f"  Record: {home_stats.wins}-{home_stats.losses}\n")
        log_file.write(f"  Total Runs: {home_stats.total_runs} ({home_stats.total_runs/num_games:.2f} per game)\n\n")

        log_file.write(f"  BATTING STATISTICS:\n")
        log_file.write(f"    At-Bats: {home_stats.at_bats}\n")
        log_file.write(f"    Hits: {home_stats.hits} (AVG: {home_stats.batting_average():.3f})\n")
        log_file.write(f"      Singles: {home_stats.singles}\n")
        log_file.write(f"      Doubles: {home_stats.doubles}\n")
        log_file.write(f"      Triples: {home_stats.triples}\n")
        log_file.write(f"      Home Runs: {home_stats.home_runs}\n")
        log_file.write(f"    Walks: {home_stats.walks}\n")
        log_file.write(f"    Strikeouts: {home_stats.strikeouts}\n")
        log_file.write(f"    On-Base Percentage: {home_stats.on_base_percentage():.3f}\n")
        log_file.write(f"    Slugging Percentage: {home_stats.slugging_percentage():.3f}\n\n")

        log_file.write(f"  BATTED BALL DISTRIBUTION:\n")
        log_file.write(f"    Ground Balls: {home_stats.ground_balls} ({home_stats.ground_ball_percentage():.1f}%)\n")
        log_file.write(f"    Line Drives: {home_stats.line_drives} ({home_stats.line_drive_percentage():.1f}%)\n")
        log_file.write(f"    Fly Balls: {home_stats.fly_balls} ({home_stats.fly_ball_percentage():.1f}%)\n\n")

        log_file.write(f"  PHYSICS-BASED METRICS:\n")
        log_file.write(f"    Avg Exit Velocity: {home_stats.avg_exit_velocity():.1f} mph\n")
        log_file.write(f"    Avg Launch Angle: {home_stats.avg_launch_angle():.1f}°\n\n")

        log_file.write(f"  DEFENSIVE STATISTICS:\n")
        log_file.write(f"    Errors: {home_stats.errors}\n\n")

        # Series winner
        log_file.write(f"{'='*60}\n")
        log_file.write(f"Series Winner: ")
        if away_stats.wins > home_stats.wins:
            log_file.write(f"{away_team.name} ({away_stats.wins}-{home_stats.wins})\n")
        elif home_stats.wins > away_stats.wins:
            log_file.write(f"{home_team.name} ({home_stats.wins}-{away_stats.wins})\n")
        else:
            log_file.write(f"TIED ({away_stats.wins}-{home_stats.wins})\n")
        log_file.write(f"{'='*80}\n")

    # Display summary to console
    display_header("Series Results")

    # Away team results
    print(f"\n  {away_team.name} ({away_season}):")
    print(f"  {'='*60}")
    print(f"    Record: {away_stats.wins}-{away_stats.losses}")
    print(f"    Runs: {away_stats.total_runs} ({away_stats.total_runs/num_games:.2f}/game)")
    print(f"\n    BATTING:")
    print(f"      AVG: {away_stats.batting_average():.3f} | OBP: {away_stats.on_base_percentage():.3f} | SLG: {away_stats.slugging_percentage():.3f}")
    print(f"      Hits: {away_stats.hits} ({away_stats.singles}-{away_stats.doubles}-{away_stats.triples}, {away_stats.home_runs} HR)")
    print(f"      BB: {away_stats.walks} | K: {away_stats.strikeouts}")
    print(f"\n    BATTED BALL:")
    print(f"      GB: {away_stats.ground_ball_percentage():.1f}% | LD: {away_stats.line_drive_percentage():.1f}% | FB: {away_stats.fly_ball_percentage():.1f}%")
    print(f"\n    PHYSICS:")
    print(f"      Avg Exit Velo: {away_stats.avg_exit_velocity():.1f} mph")
    print(f"      Avg Launch Angle: {away_stats.avg_launch_angle():.1f}°")
    print(f"\n    DEFENSE:")
    print(f"      Errors: {away_stats.errors}")

    # Home team results
    print(f"\n  {home_team.name} ({home_season}):")
    print(f"  {'='*60}")
    print(f"    Record: {home_stats.wins}-{home_stats.losses}")
    print(f"    Runs: {home_stats.total_runs} ({home_stats.total_runs/num_games:.2f}/game)")
    print(f"\n    BATTING:")
    print(f"      AVG: {home_stats.batting_average():.3f} | OBP: {home_stats.on_base_percentage():.3f} | SLG: {home_stats.slugging_percentage():.3f}")
    print(f"      Hits: {home_stats.hits} ({home_stats.singles}-{home_stats.doubles}-{home_stats.triples}, {home_stats.home_runs} HR)")
    print(f"      BB: {home_stats.walks} | K: {home_stats.strikeouts}")
    print(f"\n    BATTED BALL:")
    print(f"      GB: {home_stats.ground_ball_percentage():.1f}% | LD: {home_stats.line_drive_percentage():.1f}% | FB: {home_stats.fly_ball_percentage():.1f}%")
    print(f"\n    PHYSICS:")
    print(f"      Avg Exit Velo: {home_stats.avg_exit_velocity():.1f} mph")
    print(f"      Avg Launch Angle: {home_stats.avg_launch_angle():.1f}°")
    print(f"\n    DEFENSE:")
    print(f"      Errors: {home_stats.errors}")

    # Series winner
    print(f"\n  {'='*60}")
    print(f"  Series Winner: ", end="")
    if away_stats.wins > home_stats.wins:
        print(f"{away_team.name} ({away_stats.wins}-{home_stats.wins})")
    elif home_stats.wins > away_stats.wins:
        print(f"{home_team.name} ({home_stats.wins}-{away_stats.wins})")
    else:
        print(f"TIED ({away_stats.wins}-{home_stats.wins})")

    print("\n" + "=" * 70)
    print(f"\n✅ Complete game log saved to: {log_path}")
    print(f"   File size: {log_path.stat().st_size / 1024:.1f} KB")


def main():
    """Main interactive loop."""
    # Check if database exists
    db_path = Path("baseball_teams.db")
    if not db_path.exists():
        display_header("Database Not Found")
        print(f"\n❌ Database file '{db_path}' not found!")
        print("\nTo create the database and add teams:")
        print("  1. Run: python examples/simulate_mlb_teams.py")
        print("  2. Or manually run: python -m batted_ball.database.team_database")
        print("\nThis will fetch MLB team data and populate the database.")
        print()
        input("Press Enter to exit...")
        return

    loader = TeamLoader()

    try:
        while True:
            clear_screen()
            display_header("Baseball Team Simulation")
            print("\nSimulate games between teams stored in the database.")
            print()

            # Select away team
            away_info = select_team(loader, "Select Away Team")
            if not away_info:
                break

            clear_screen()
            print(f"\n✓ Away Team: {away_info[0]} ({away_info[1]})")

            # Select home team
            home_info = select_team(loader, "Select Home Team")
            if not home_info:
                continue

            clear_screen()
            print(f"\n✓ Away Team: {away_info[0]} ({away_info[1]})")
            print(f"✓ Home Team: {home_info[0]} ({home_info[1]})")

            # Get number of games
            num_games = get_num_games()
            if not num_games:
                continue

            # Simulate games
            simulate_games(away_info, home_info, num_games)

            # Ask to continue
            print()
            choice = input("Simulate another series? (y/n): ").strip().lower()
            if choice != 'y':
                break

    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user.")

    finally:
        loader.close()
        print("\nThank you for using the Baseball Team Simulator!")
        print()


if __name__ == "__main__":
    main()
