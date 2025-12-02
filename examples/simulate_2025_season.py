"""
Simulate the 2025 MLB Season.

This script simulates the 2025 MLB season using the real schedule,
processing games day-by-day with parallel execution.

Usage:
    python examples/simulate_2025_season.py  # Interactive mode
    python examples/simulate_2025_season.py --first-week
    python examples/simulate_2025_season.py --month april
    python examples/simulate_2025_season.py --full-season
    python examples/simulate_2025_season.py --start 2025-04-01 --end 2025-04-30
"""

import sys
import argparse
from datetime import date, datetime
from pathlib import Path

# Add parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.season_simulator import SeasonSimulator


def parse_date(date_str: str) -> date:
    """Parse a date string in various formats."""
    for fmt in ['%Y-%m-%d', '%Y%m%d', '%m/%d/%Y', '%m-%d-%Y']:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {date_str}")


def run_simulation(start_date: date, end_date: date, save_results: bool = True):
    """Run the simulation for a date range."""
    print("\n" + "="*60)
    print("  2025 MLB SEASON SIMULATOR")
    print("="*60)
    
    # Create simulator
    sim = SeasonSimulator(verbose=True)
    
    # Check for available teams
    available = sim._get_available_teams()
    if not available:
        print("\n⚠️  No teams found in database!")
        print("    Run 'python manage_teams.py' to add teams first.")
        return None
    
    print(f"\n📋 Teams available: {len(available)}/30")
    if len(available) < 30:
        all_teams = sim.schedule.get_all_teams()
        missing = set(all_teams) - available
        print(f"   Missing: {', '.join(sorted(missing))}")
    
    # Run simulation
    print("\n🎮 Starting simulation...")
    stats = sim.simulate_range(start_date, end_date)
    
    # Show results
    print("\n" + "="*60)
    print("  SIMULATION COMPLETE")
    print("="*60)
    print(f"  Games simulated: {stats['games_simulated']}")
    print(f"  Games skipped:   {stats['games_skipped']} (teams not in database)")
    print(f"  Time elapsed:    {stats['elapsed_seconds']:.1f}s")
    print(f"  Games/second:    {stats['games_per_second']:.2f}")
    print("="*60)
    
    # Show standings
    sim.print_standings()
    
    # Show summary stats
    summary = sim.get_summary_stats()
    if summary:
        print(f"\n📊 Summary Statistics:")
        print(f"   Runs per game:    {summary['runs_per_game']:.2f}")
        print(f"   HRs per game:     {summary['home_runs_per_game']:.2f}")
        print(f"   Home team wins:   {summary['home_team_wins']} ({100*summary['home_team_wins']/summary['games_played']:.1f}%)")
        print(f"   Away team wins:   {summary['away_team_wins']} ({100*summary['away_team_wins']/summary['games_played']:.1f}%)")
        
        print(f"\n📈 Batting Metrics:")
        print(f"   Batting Avg:      {summary['batting_avg']:.3f}")
        print(f"   On-Base Pct:      {summary['on_base_pct']:.3f}")
        print(f"   Slugging Pct:     {summary['slugging_pct']:.3f}")
        print(f"   OPS:              {summary['ops']:.3f}")
        print(f"   BABIP:            {summary['babip']:.3f}")
        print(f"   K Rate:           {summary['strikeout_rate']:.1f}%")
        print(f"   BB Rate:          {summary['walk_rate']:.1f}%")
        print(f"   Avg Exit Velo:    {summary['avg_exit_velocity']:.1f} mph")
        print(f"   Avg Launch Angle: {summary['avg_launch_angle']:.1f}°")
        print(f"   GB Rate:          {summary['ground_ball_rate']:.1f}%")
        print(f"   LD Rate:          {summary['line_drive_rate']:.1f}%")
        print(f"   FB Rate:          {summary['fly_ball_rate']:.1f}%")
        
        print(f"\n⚾ Pitching Metrics:")
        print(f"   ERA:              {summary['era']:.2f}")
        print(f"   WHIP:             {summary['whip']:.2f}")
        print(f"   K/9:              {summary['k_per_9']:.1f}")
        print(f"   BB/9:             {summary['bb_per_9']:.1f}")
        print(f"   HR/9:             {summary['hr_per_9']:.1f}")
    
    # Save results
    if save_results:
        output_file = f"game_logs/season_sim_{start_date}_{end_date}.json"
        sim.save_results(output_file)
    
    return sim


def interactive_mode():
    """Interactive menu for season simulation."""
    print("\n" + "="*60)
    print("  2025 MLB SEASON SIMULATOR")
    print("="*60)
    
    sim = SeasonSimulator(verbose=False)
    first_date, last_date = sim.schedule.get_date_range()
    
    print(f"\n  Schedule: {first_date} to {last_date}")
    print(f"  Teams in database: {len(sim._get_available_teams())}/30")
    
    print("\n  Options:")
    print("    1. Simulate first week")
    print("    2. Simulate first month")
    print("    3. Simulate specific month")
    print("    4. Simulate custom date range")
    print("    5. Simulate full season")
    print("    6. Show schedule info")
    print("    Q. Quit")
    
    while True:
        choice = input("\n  Enter choice: ").strip().upper()
        
        if choice == 'Q':
            print("  Goodbye!")
            return
        
        if choice == '1':
            # First week
            from datetime import timedelta
            run_simulation(first_date, first_date + timedelta(days=6))
            return
        
        elif choice == '2':
            # First month (April typically)
            from datetime import timedelta
            # Find end of first month
            end_month = first_date.month
            end_date = first_date
            while end_date.month == end_month:
                end_date += timedelta(days=1)
            end_date -= timedelta(days=1)
            run_simulation(first_date, end_date)
            return
        
        elif choice == '3':
            print("\n  Months available:")
            print("    1. March")
            print("    2. April")
            print("    3. May")
            print("    4. June")
            print("    5. July")
            print("    6. August")
            print("    7. September")
            print("    8. October")
            
            month_choice = input("  Select month (1-8): ").strip()
            month_map = {'1': 3, '2': 4, '3': 5, '4': 6, '5': 7, '6': 8, '7': 9, '8': 10}
            
            if month_choice not in month_map:
                print("  Invalid choice")
                continue
            
            month = month_map[month_choice]
            start = date(2025, month, 1)
            
            # Find end of month
            if month == 12:
                end = date(2025, 12, 31)
            else:
                from datetime import timedelta
                end = date(2025, month + 1, 1) - timedelta(days=1)
            
            run_simulation(start, end)
            return
        
        elif choice == '4':
            start_str = input("  Start date (YYYY-MM-DD): ").strip()
            end_str = input("  End date (YYYY-MM-DD): ").strip()
            
            try:
                start = parse_date(start_str)
                end = parse_date(end_str)
                run_simulation(start, end)
                return
            except ValueError as e:
                print(f"  Error: {e}")
                continue
        
        elif choice == '5':
            confirm = input("  Simulate full season? This may take a while (y/n): ").strip().lower()
            if confirm == 'y':
                run_simulation(first_date, last_date)
                return
        
        elif choice == '6':
            print(f"\n  Schedule information:")
            print(f"    First game: {first_date}")
            print(f"    Last game: {last_date}")
            print(f"    Total game days: {len(sim.schedule.get_all_game_dates())}")
            print(f"    Teams: {len(sim.schedule.get_all_teams())}")
            
            # Sample some days
            print("\n  Sample game days:")
            for game_date in list(sim.schedule.get_all_game_dates())[:5]:
                games = sim.schedule.get_games_for_date(game_date)
                print(f"    {game_date}: {len(games)} games")
        
        else:
            print("  Invalid choice. Try again.")


def main():
    parser = argparse.ArgumentParser(description='Simulate the 2025 MLB Season')
    parser.add_argument('--first-week', action='store_true', help='Simulate first week of season')
    parser.add_argument('--first-month', action='store_true', help='Simulate first month')
    parser.add_argument('--month', type=str, help='Simulate specific month (e.g., april, may)')
    parser.add_argument('--full-season', action='store_true', help='Simulate entire season')
    parser.add_argument('--start', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', type=str, help='End date (YYYY-MM-DD)')
    parser.add_argument('--no-save', action='store_true', help='Do not save results to file')
    
    args = parser.parse_args()
    
    # Get schedule dates
    sim = SeasonSimulator(verbose=False)
    first_date, last_date = sim.schedule.get_date_range()
    
    save_results = not args.no_save
    
    if args.first_week:
        from datetime import timedelta
        run_simulation(first_date, first_date + timedelta(days=6), save_results)
    
    elif args.first_month:
        from datetime import timedelta
        end_month = first_date.month
        end_date = first_date
        while end_date.month == end_month:
            end_date += timedelta(days=1)
        end_date -= timedelta(days=1)
        run_simulation(first_date, end_date, save_results)
    
    elif args.month:
        month_map = {
            'march': 3, 'mar': 3, '3': 3,
            'april': 4, 'apr': 4, '4': 4,
            'may': 5, '5': 5,
            'june': 6, 'jun': 6, '6': 6,
            'july': 7, 'jul': 7, '7': 7,
            'august': 8, 'aug': 8, '8': 8,
            'september': 9, 'sep': 9, '9': 9,
            'october': 10, 'oct': 10, '10': 10,
        }
        month = month_map.get(args.month.lower())
        if not month:
            print(f"Unknown month: {args.month}")
            sys.exit(1)
        
        start = date(2025, month, 1)
        from datetime import timedelta
        if month == 12:
            end = date(2025, 12, 31)
        else:
            end = date(2025, month + 1, 1) - timedelta(days=1)
        
        run_simulation(start, end, save_results)
    
    elif args.full_season:
        run_simulation(first_date, last_date, save_results)
    
    elif args.start and args.end:
        start = parse_date(args.start)
        end = parse_date(args.end)
        run_simulation(start, end, save_results)
    
    else:
        # Interactive mode
        interactive_mode()


if __name__ == "__main__":
    main()
