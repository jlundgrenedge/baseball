"""
Test Phase 4: Export functionality for stats database.
"""
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.stats_database import StatsDatabase


def test_exports():
    """Test CSV and HTML export functionality."""
    print("=" * 60)
    print("Phase 4 Export Tests")
    print("=" * 60)
    
    # Check for existing stats database
    db_path = Path("saved_stats/season_stats.db")
    if not db_path.exists():
        print("❌ No stats database found. Run a simulation first.")
        return False
    
    db = StatsDatabase(db_path)
    seasons = db.list_seasons()
    
    if not seasons:
        print("❌ No seasons in database.")
        return False
    
    season_id = seasons[0]['season_id']
    print(f"\n📊 Testing exports for season {season_id}")
    
    # Test CSV exports
    print("\n--- CSV Export Tests ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Test batting CSV
        batting_csv = Path(tmpdir) / "batting.csv"
        rows = db.export_batting_to_csv(season_id, str(batting_csv), min_pa=1)
        
        if batting_csv.exists():
            content = batting_csv.read_text()
            lines = content.strip().split('\n')
            print(f"✅ Batting CSV: {rows} rows exported")
            print(f"   Header: {lines[0][:80]}...")
            if len(lines) > 1:
                print(f"   Sample: {lines[1][:80]}...")
        else:
            print("❌ Batting CSV not created")
            return False
        
        # Test pitching CSV
        pitching_csv = Path(tmpdir) / "pitching.csv"
        rows = db.export_pitching_to_csv(season_id, str(pitching_csv), min_ip=0)
        
        if pitching_csv.exists():
            content = pitching_csv.read_text()
            lines = content.strip().split('\n')
            print(f"✅ Pitching CSV: {rows} rows exported")
            print(f"   Header: {lines[0][:80]}...")
            if len(lines) > 1:
                print(f"   Sample: {lines[1][:80]}...")
        else:
            print("❌ Pitching CSV not created")
            return False
    
    # Test HTML export
    print("\n--- HTML Export Test ---")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        html_file = Path(tmpdir) / "report.html"
        db.export_to_html(season_id, str(html_file), min_pa=1, min_ip=0)
        
        if html_file.exists():
            content = html_file.read_text(encoding='utf-8')
            size_kb = len(content) / 1024
            
            # Check for key elements
            has_title = "<title>" in content
            has_batting = "Batting Statistics" in content
            has_pitching = "Pitching Statistics" in content
            has_leaders = "League Leaders" in content
            has_style = "<style>" in content
            
            print(f"✅ HTML Report: {size_kb:.1f} KB")
            print(f"   ✓ Title: {has_title}")
            print(f"   ✓ Batting section: {has_batting}")
            print(f"   ✓ Pitching section: {has_pitching}")
            print(f"   ✓ Leaders section: {has_leaders}")
            print(f"   ✓ Styled: {has_style}")
            
            if not all([has_title, has_batting, has_pitching, has_leaders, has_style]):
                print("❌ HTML missing expected sections")
                return False
        else:
            print("❌ HTML report not created")
            return False
    
    print("\n" + "=" * 60)
    print("✅ All Phase 4 export tests passed!")
    print("=" * 60)
    
    db.close()
    return True


if __name__ == "__main__":
    success = test_exports()
    sys.exit(0 if success else 1)
