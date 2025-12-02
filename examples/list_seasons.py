#!/usr/bin/env python3
"""Test the season choice functionality."""

import sys
sys.path.insert(0, '.')

from batted_ball.season_stats_tracker import SeasonStatsTracker

# List available seasons
seasons = SeasonStatsTracker.list_available_seasons()
print(f"Available seasons ({len(seasons)} total):")
for s in seasons:
    status = "Complete" if s['is_complete'] else "In Progress"
    desc = s['description'] or "(no description)"
    print(f"  ID {s['season_id']}: {s['year']} - {s['total_games']} games ({status})")
    print(f"      {desc}")

if not seasons:
    print("  (none)")

# Delete the test season we created if it exists
test_seasons = [s for s in seasons if s['description'] == 'Test new season']
for s in test_seasons:
    print(f"\nCleaning up test season ID {s['season_id']}...")
    SeasonStatsTracker.delete_season(s['season_id'])
    print("Deleted.")
