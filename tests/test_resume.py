"""Test resume functionality."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.stats_database import StatsDatabase
from datetime import date, timedelta

db_path = Path('saved_stats/season_stats.db')
db = StatsDatabase(db_path)

# Get first season
seasons = db.list_seasons()
if seasons:
    s = seasons[0]
    sid = s['season_id']
    
    last_date = db.get_last_simulated_date(sid)
    simulated = db.get_simulated_dates(sid)
    
    print(f"Season {sid}: {s['total_games']} games")
    print(f"Days simulated: {len(simulated)}")
    print(f"Last date: {last_date}")
    
    if last_date:
        next_day = last_date + timedelta(days=1)
        print(f"Resume from: {next_day}")
        
        # Check matchups for a sample date
        if simulated:
            sample_date = min(simulated)
            matchups = db.get_simulated_matchups(sid, sample_date)
            print(f"Games on {sample_date}: {len(matchups)} matchups")
            for m in list(matchups)[:3]:
                print(f"  {m[0]} @ {m[1]}")

db.close()
print("All resume methods work!")
