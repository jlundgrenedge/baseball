"""
Example: Simulate Games Between Real MLB Teams

This script demonstrates how to use the pybaseball integration to:
1. Fetch real MLB player statistics
2. Create teams from actual MLB rosters
3. Simulate games between real teams

Requirements:
- pip install pybaseball
- pip install pandas (dependency of pybaseball)

Author: Baseball Physics Simulation Engine
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from batted_ball import GameSimulator

# Check if pybaseball integration is available
try:
    from batted_ball import (
        PYBASEBALL_AVAILABLE,
        create_team_from_mlb_roster,
        create_mlb_player
    )
except ImportError:
    print("ERROR: PyBaseball integration not available.")
    print("Please install pybaseball: pip install pybaseball")
    sys.exit(1)

if not PYBASEBALL_AVAILABLE:
    print("ERROR: pybaseball package not installed.")
    print("Install with: pip install pybaseball")
    sys.exit(1)


def simulate_yankees_vs_dodgers(season: int = 2024):
    """
    Simulate a game between the 2024 Yankees and Dodgers.

    This example uses actual player names and fetches their real statistics
    from the specified MLB season.
    """
    print("=" * 60)
    print("MLB TEAM SIMULATION: Yankees vs Dodgers")
    print("=" * 60)
    print(f"Fetching player statistics from {season} MLB season...")
    print("(This may take a minute...)\n")

    # Define Yankees roster
    yankees_hitters = [
        ("Juan Soto", "RF"),
        ("Aaron Judge", "CF"),
        ("Giancarlo Stanton", "DH"),
        ("Anthony Rizzo", "1B"),
        ("Gleyber Torres", "2B"),
        ("Anthony Volpe", "SS"),
        ("Jazz Chisholm", "3B"),
        ("Alex Verdugo", "LF"),
        ("Jose Trevino", "C"),
    ]

    yankees_pitchers = [
        ("Gerrit Cole", "starter"),
        ("Carlos Rodon", "starter"),
        ("Clay Holmes", "reliever"),
    ]

    # Define Dodgers roster
    dodgers_hitters = [
        ("Mookie Betts", "RF"),
        ("Freddie Freeman", "1B"),
        ("Will Smith", "C"),
        ("Max Muncy", "3B"),
        ("Teoscar Hernandez", "LF"),
        ("Gavin Lux", "2B"),
        ("Miguel Rojas", "SS"),
        ("James Outman", "CF"),
        ("Chris Taylor", "DH"),
    ]

    dodgers_pitchers = [
        ("Tyler Glasnow", "starter"),
        ("Yoshinobu Yamamoto", "starter"),
        ("Evan Phillips", "reliever"),
    ]

    # Create teams from MLB rosters
    print("Creating Yankees team from MLB data...")
    try:
        yankees = create_team_from_mlb_roster(
            "New York Yankees",
            yankees_hitters,
            yankees_pitchers,
            season=season
        )
        print("✓ Yankees roster created successfully")
    except Exception as e:
        print(f"✗ Error creating Yankees roster: {e}")
        print("  Using generic team instead...")
        from batted_ball import create_test_team
        yankees = create_test_team("Yankees", "elite")

    print("\nCreating Dodgers team from MLB data...")
    try:
        dodgers = create_team_from_mlb_roster(
            "Los Angeles Dodgers",
            dodgers_hitters,
            dodgers_pitchers,
            season=season
        )
        print("✓ Dodgers roster created successfully")
    except Exception as e:
        print(f"✗ Error creating Dodgers roster: {e}")
        print("  Using generic team instead...")
        from batted_ball import create_test_team
        dodgers = create_test_team("Dodgers", "elite")

    # Simulate the game
    print("\n" + "=" * 60)
    print("STARTING GAME SIMULATION")
    print("=" * 60)

    simulator = GameSimulator(
        away_team=yankees,
        home_team=dodgers,
        verbose=True  # Show play-by-play
    )

    final_state = simulator.simulate_game(num_innings=9)

    # Display final results
    print("\n" + "=" * 60)
    print("FINAL SCORE")
    print("=" * 60)
    print(f"{yankees.name}: {final_state.away_score}")
    print(f"{dodgers.name}: {final_state.home_score}")
    print(f"\nTotal Pitches: {final_state.total_pitches}")
    print(f"Total Hits: {final_state.total_hits}")
    print(f"Home Runs: {final_state.total_home_runs}")
    print("=" * 60)


def simulate_single_player_at_bats():
    """
    Demonstrate fetching individual player stats and simulating at-bats.
    """
    print("\n" + "=" * 60)
    print("INDIVIDUAL PLAYER SIMULATION")
    print("=" * 60)

    from batted_ball import AtBatSimulator

    # Create pitcher from MLB data
    print("Creating Shohei Ohtani (Pitcher)...")
    try:
        ohtani_pitcher = create_mlb_player("Shohei Ohtani", season=2024, role='pitcher')
        print(f"✓ Created: {ohtani_pitcher.name}")
        print(f"  Velocity: {ohtani_pitcher.get_pitch_velocity_mph():.1f} mph")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("  Using default pitcher")
        from batted_ball.attributes import create_starter_pitcher
        from batted_ball import Pitcher, generate_pitch_arsenal
        attrs = create_starter_pitcher("elite")
        ohtani_pitcher = Pitcher("Ohtani", attrs, generate_pitch_arsenal(attrs, "starter"))

    # Create hitter from MLB data
    print("\nCreating Aaron Judge (Hitter)...")
    try:
        judge = create_mlb_player("Aaron Judge", season=2024, role='hitter')
        print(f"✓ Created: {judge.name}")
        print(f"  Bat Speed: {judge.attributes.get_bat_speed_mph():.1f} mph")
    except Exception as e:
        print(f"✗ Error: {e}")
        print("  Using default hitter")
        from batted_ball.attributes import create_power_hitter
        from batted_ball import Hitter
        judge = Hitter("Judge", create_power_hitter("elite"))

    # Simulate 10 at-bats
    print(f"\nSimulating 10 at-bats: {ohtani_pitcher.name} vs {judge.name}")
    print("-" * 60)

    simulator = AtBatSimulator(ohtani_pitcher, judge)

    outcomes = {
        'strikeout': 0,
        'walk': 0,
        'single': 0,
        'double': 0,
        'triple': 0,
        'home_run': 0,
        'out': 0
    }

    for i in range(10):
        result = simulator.simulate_at_bat()
        outcome = result.outcome

        # Categorize outcome
        if outcome in outcomes:
            outcomes[outcome] += 1
        elif 'out' in outcome:
            outcomes['out'] += 1

        print(f"  At-bat {i+1}: {outcome}")

    print("\n" + "-" * 60)
    print("RESULTS SUMMARY:")
    for outcome, count in outcomes.items():
        if count > 0:
            print(f"  {outcome.replace('_', ' ').title()}: {count}")


def main():
    """Main entry point."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║  PYBASEBALL INTEGRATION DEMONSTRATION" + " " * 19 + "║")
    print("║  Simulating games with real MLB players" + " " * 17 + "║")
    print("╚" + "=" * 58 + "╝")
    print("\n")

    # Check if user wants to run full simulation
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        print("Running quick demo (individual players only)...\n")
        simulate_single_player_at_bats()
    else:
        print("Running full demonstration...\n")
        print("NOTE: This will fetch data from Baseball Savant/FanGraphs.")
        print("      The first run may be slow due to data fetching.\n")

        # Simulate full game
        simulate_yankees_vs_dodgers(season=2024)

        # Individual player demo
        simulate_single_player_at_bats()

    print("\n" + "=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
    print("\nTry modifying the rosters in the script to simulate")
    print("your favorite teams and players!")


if __name__ == "__main__":
    main()
