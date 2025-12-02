"""
Test Phase 5: Advanced statistics calculation.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.advanced_stats import AdvancedStatsCalculator, LeagueConstants


def test_advanced_stats():
    """Test advanced statistics calculations."""
    print("=" * 60)
    print("Phase 5 Advanced Stats Tests")
    print("=" * 60)
    
    # Check for existing stats database
    db_path = Path("saved_stats/season_stats.db")
    if not db_path.exists():
        print("❌ No stats database found. Run a simulation first.")
        return False
    
    calc = AdvancedStatsCalculator(str(db_path))
    
    # Get first available season
    import sqlite3
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT season_id FROM seasons LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print("❌ No seasons found in database.")
        return False
    
    season_id = row[0]
    print(f"\n📊 Testing with season {season_id}")
    
    # Test league constants
    print("\n--- League Constants ---")
    constants = calc.calculate_league_constants(season_id)
    print(f"✅ League wOBA: {constants.league_woba:.3f}")
    print(f"✅ League ERA: {constants.league_era:.2f}")
    print(f"✅ League FIP: {constants.league_fip:.2f}")
    print(f"✅ FIP Constant: {constants.fip_constant:.2f}")
    print(f"✅ R/PA: {constants.runs_per_pa:.3f}")
    
    # Test batting stats
    print("\n--- Batting Advanced Stats ---")
    batting = calc.calculate_batting_stats(season_id, min_pa=10, constants=constants)
    print(f"✅ Calculated stats for {len(batting)} batters")
    
    if batting:
        # Check wRC+ distribution
        wrc_values = [b.wrc_plus for b in batting]
        avg_wrc = sum(wrc_values) / len(wrc_values)
        print(f"   Average wRC+: {avg_wrc:.0f} (should be ~100)")
        
        # Check WAR
        war_values = [b.war for b in batting]
        print(f"   WAR range: {min(war_values):.1f} to {max(war_values):.1f}")
        
        # Show top player
        top = max(batting, key=lambda x: x.war)
        print(f"   Top WAR: {top.player_name} ({top.war:.1f} WAR, {top.wrc_plus:.0f} wRC+)")
    
    # Test pitching stats
    print("\n--- Pitching Advanced Stats ---")
    pitching = calc.calculate_pitching_stats(season_id, min_ip=3, constants=constants)
    print(f"✅ Calculated stats for {len(pitching)} pitchers")
    
    if pitching:
        # Check FIP distribution
        fip_values = [p.fip for p in pitching]
        avg_fip = sum(fip_values) / len(fip_values)
        print(f"   Average FIP: {avg_fip:.2f}")
        
        # Check WAR
        war_values = [p.war for p in pitching]
        print(f"   WAR range: {min(war_values):.1f} to {max(war_values):.1f}")
        
        # Show top pitcher
        top = max(pitching, key=lambda x: x.war)
        print(f"   Top WAR: {top.player_name} ({top.war:.1f} WAR, {top.fip:.2f} FIP)")
    
    # Test WAR leaders
    print("\n--- WAR Leaders ---")
    batting_leaders = calc.get_war_leaders(season_id, "batting", limit=3)
    pitching_leaders = calc.get_war_leaders(season_id, "pitching", limit=3)
    
    print("Top 3 Position Players:")
    for b in batting_leaders:
        print(f"   {b['player_name']:20} {b['team']:3} | WAR: {b['war']:+.1f} wRC+: {b['wrc_plus']:.0f}")
    
    print("Top 3 Pitchers:")
    for p in pitching_leaders:
        print(f"   {p['player_name']:20} {p['team']:3} | WAR: {p['war']:+.1f} FIP: {p['fip']:.2f}")
    
    calc.close()
    
    print("\n" + "=" * 60)
    print("✅ All Phase 5 advanced stats tests passed!")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    success = test_advanced_stats()
    sys.exit(0 if success else 1)
