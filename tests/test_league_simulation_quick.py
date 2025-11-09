"""
Quick 8-Team League Simulation Test - 12 Game Season

This is a faster version of the full league simulation for quick testing.
Each team plays only 12 games instead of 60, making the test complete in a few minutes.

For the full 60-game season simulation, use test_league_simulation.py
"""
import sys
sys.path.append('.')

# Import and reuse the main simulation code
from test_league_simulation import LeagueSimulation


def main():
    """Run a quick 8-team league simulation with only 12 games per team."""
    print(f"\n{'='*80}")
    print(f"QUICK 8-TEAM LEAGUE SIMULATION - 12 GAME SEASON")
    print(f"{'='*80}")
    print(f"(For full 60-game season, run test_league_simulation.py)")

    # Define the 8 teams with varying qualities
    teams_config = {
        # Elite teams (2)
        "Dragons": "elite",
        "Thunderbolts": "elite",

        # Good teams (3)
        "Warriors": "good",
        "Hurricanes": "good",
        "Mavericks": "good",

        # Average teams (2)
        "Pioneers": "average",
        "Voyagers": "average",

        # Poor team (1)
        "Underdogs": "poor"
    }

    # Create and run simulation with only 12 games per team
    league = LeagueSimulation(teams_config)
    league.generate_schedule(games_per_team=12)
    league.simulate_season()

    # Display results
    league.print_standings()
    league.print_team_statistics()
    league.print_league_summary()

    print(f"\n{'='*80}")
    print(f"QUICK SIMULATION COMPLETE")
    print(f"{'='*80}")
    print(f"\nKey Findings:")
    print(f"  ✓ Simulated a 12-game season for 8 teams")
    print(f"  ✓ Teams distributed across 4 quality levels")
    print(f"  ✓ All standard statistics tracked and reported")
    print(f"  ✓ For full 60-game season, run test_league_simulation.py")


if __name__ == "__main__":
    main()
