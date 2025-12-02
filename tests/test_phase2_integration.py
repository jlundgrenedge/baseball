"""
Test Phase 2 integration: SeasonSimulator with stats database
"""

from datetime import date
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.season_simulator import SeasonSimulator
from batted_ball.stats_database import StatsDatabase


def test_season_stats_integration():
    """Test that season simulation records player stats to database."""
    
    # Create stats database
    db = StatsDatabase()
    
    # Create a new season
    season_id = db.start_season(2025, "Phase 2 Integration Test")
    print(f"Created season: {season_id}")
    
    # Create simulator with stats tracking
    sim = SeasonSimulator(
        season=2024,
        num_workers=4,
        verbose=False,
        stats_db=db,
        stats_season_id=season_id
    )
    
    # Simulate a few days
    test_dates = [date(2025, 3, 27), date(2025, 3, 28)]
    
    total_games = 0
    for test_date in test_dates:
        results = sim.simulate_day(test_date)
        print(f"{test_date}: {len(results)} games")
        total_games += len(results)
    
    # Check database
    info = db.get_season_info(season_id)
    games_recorded = info['games_played']
    print(f"\nTotal games recorded: {games_recorded}")
    assert games_recorded == total_games, f"Expected {total_games}, got {games_recorded}"
    
    # Check batting leaders
    leaders = db.get_batting_leaders(season_id, "hits", limit=5)
    print("\nTop 5 Hit Leaders:")
    for leader in leaders:
        print(f"  {leader['player_name']} ({leader['team']}): {leader['hits']} H")
    
    assert len(leaders) > 0, "Should have batting leaders"
    
    # Check pitching leaders
    pit_leaders = db.get_pitching_leaders(season_id, "strikeouts", limit=5)
    print("\nTop 5 Strikeout Leaders:")
    for leader in pit_leaders:
        print(f"  {leader['player_name']} ({leader['team']}): {leader['strikeouts']} K")
    
    assert len(pit_leaders) > 0, "Should have pitching leaders"
    
    # Clean up - delete the test season
    db.delete_season(season_id)
    print(f"\nDeleted test season {season_id}")
    
    db.close()
    print("\n✅ Test complete!")


if __name__ == "__main__":
    test_season_stats_integration()
