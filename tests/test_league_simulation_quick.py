"""
Quick 8-Team League Simulation Test - 14 Game Season (Game Day Format)

This is a faster version of the full league simulation for quick testing.
Uses a realistic weekly league schedule with Thursday and Sunday game days.

Each team plays every other team twice (2 rounds) = 14 games per team
Each game day has 4 simultaneous games that are simulated in parallel

For the full 60-game season simulation, use test_league_simulation.py
"""
import sys
sys.path.append('.')

# Import and reuse the main simulation code
from test_league_simulation import LeagueSimulation


def main():
    """Run a quick 8-team league simulation with game day format."""
    print(f"\n{'='*80}")
    print(f"QUICK 8-TEAM LEAGUE SIMULATION - THURSDAY/SUNDAY LEAGUE")
    print(f"{'='*80}")
    print(f"Format: Weekly league with game days (Thursday & Sunday)")
    print(f"Season: 2 complete rounds = 14 games per team")
    print(f"Parallel: 4 games per day, all simulated simultaneously")
    print(f"\n(For full 60-game season, run test_league_simulation.py)")

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

    # Create and run simulation with game day format
    league = LeagueSimulation(teams_config)
    league.generate_game_day_schedule(rounds=2)  # 2 rounds = 14 games per team
    league.simulate_season_by_game_day()

    # Display results
    league.print_standings()
    league.print_team_statistics()
    league.print_league_summary()

    print(f"\n{'='*80}")
    print(f"QUICK SIMULATION COMPLETE")
    print(f"{'='*80}")
    print(f"\nKey Findings:")
    print(f"  ✓ Simulated a 14-game season for 8 teams (112 total games)")
    print(f"  ✓ Used realistic game day format (Thursday/Sunday league)")
    print(f"  ✓ 4 games per day simulated in parallel for efficiency")
    print(f"  ✓ Teams distributed across 4 quality levels")
    print(f"  ✓ For full 60-game season, run test_league_simulation.py")


if __name__ == "__main__":
    main()
