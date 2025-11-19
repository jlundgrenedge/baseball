#!/usr/bin/env python
"""
Populate database with sample team data for testing.

This script creates synthetic but realistic team data based on typical MLB statistics,
allowing you to test the database system without needing to fetch from pybaseball.
"""

import sys
from pathlib import Path
import pandas as pd
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from batted_ball.database import TeamDatabase


def create_sample_pitchers(team_name: str, season: int, quality: str = "average") -> pd.DataFrame:
    """Create sample pitcher data."""

    # Quality presets
    quality_params = {
        "elite": {
            "era_range": (2.0, 3.5),
            "whip_range": (0.90, 1.15),
            "k9_range": (9.5, 13.0),
            "bb9_range": (1.5, 2.8),
            "velo_range": (94.0, 99.0),
        },
        "good": {
            "era_range": (3.0, 4.0),
            "whip_range": (1.10, 1.30),
            "k9_range": (8.0, 10.5),
            "bb9_range": (2.0, 3.5),
            "velo_range": (91.0, 95.0),
        },
        "average": {
            "era_range": (3.5, 4.8),
            "whip_range": (1.20, 1.40),
            "k9_range": (7.5, 9.5),
            "bb9_range": (2.5, 4.0),
            "velo_range": (89.0, 93.0),
        },
    }

    params = quality_params.get(quality, quality_params["average"])

    pitchers = []

    # Generate 12 pitchers (5 starters, 7 relievers)
    starter_names = [
        f"{team_name} Ace",
        f"{team_name} Starter 2",
        f"{team_name} Starter 3",
        f"{team_name} Starter 4",
        f"{team_name} Starter 5",
    ]

    reliever_names = [
        f"{team_name} Closer",
        f"{team_name} Setup",
        f"{team_name} Reliever 1",
        f"{team_name} Reliever 2",
        f"{team_name} Reliever 3",
        f"{team_name} Reliever 4",
        f"{team_name} Long Relief",
    ]

    # Starters
    for i, name in enumerate(starter_names):
        # Ace gets better stats
        multiplier = 0.85 if i == 0 else (0.95 if i <= 2 else 1.05)

        era_min, era_max = params["era_range"]
        era = random.uniform(era_min * multiplier, era_max * multiplier)

        whip_min, whip_max = params["whip_range"]
        whip = random.uniform(whip_min * multiplier, whip_max * multiplier)

        k9_min, k9_max = params["k9_range"]
        k9 = random.uniform(k9_min / multiplier, k9_max / multiplier)

        bb9_min, bb9_max = params["bb9_range"]
        bb9 = random.uniform(bb9_min * multiplier, bb9_max * multiplier)

        velo_min, velo_max = params["velo_range"]
        velo = random.uniform(velo_min, velo_max)

        ip = random.uniform(150.0, 200.0)
        games = random.randint(28, 32)

        pitchers.append({
            'player_name': name,
            'team': team_name,
            'season': season,
            'innings_pitched': ip,
            'games_pitched': games,
            'games_started': games,
            'era': round(era, 2),
            'whip': round(whip, 2),
            'k_per_9': round(k9, 1),
            'bb_per_9': round(bb9, 1),
            'strikeouts': int(k9 * ip / 9),
            'walks': int(bb9 * ip / 9),
            'avg_fastball_velo': round(velo, 1),
        })

    # Relievers
    for i, name in enumerate(reliever_names):
        # Closer gets better stats
        multiplier = 0.90 if i == 0 else 1.0

        era_min, era_max = params["era_range"]
        era = random.uniform(era_min * multiplier, era_max * multiplier)

        whip_min, whip_max = params["whip_range"]
        whip = random.uniform(whip_min * multiplier, whip_max * multiplier)

        k9_min, k9_max = params["k9_range"]
        # Relievers typically have higher K/9
        k9 = random.uniform(k9_min / multiplier, k9_max / multiplier) * 1.15

        bb9_min, bb9_max = params["bb9_range"]
        bb9 = random.uniform(bb9_min * multiplier, bb9_max * multiplier)

        velo_min, velo_max = params["velo_range"]
        # Relievers throw harder
        velo = random.uniform(velo_min + 2, velo_max + 3)

        ip = random.uniform(40.0, 80.0)
        games = random.randint(50, 70)

        pitchers.append({
            'player_name': name,
            'team': team_name,
            'season': season,
            'innings_pitched': ip,
            'games_pitched': games,
            'games_started': 0,
            'era': round(era, 2),
            'whip': round(whip, 2),
            'k_per_9': round(k9, 1),
            'bb_per_9': round(bb9, 1),
            'strikeouts': int(k9 * ip / 9),
            'walks': int(bb9 * ip / 9),
            'avg_fastball_velo': round(velo, 1),
        })

    return pd.DataFrame(pitchers)


def create_sample_hitters(team_name: str, season: int, quality: str = "average") -> pd.DataFrame:
    """Create sample hitter data."""

    # Quality presets
    quality_params = {
        "elite": {
            "avg_range": (0.270, 0.320),
            "obp_range": (0.350, 0.420),
            "slg_range": (0.480, 0.620),
            "hr_range": (25, 45),
            "k_pct_range": (15, 22),
            "bb_pct_range": (10, 18),
            "ev_range": (88.5, 93.0),
            "barrel_range": (8.0, 15.0),
            "speed_range": (27.5, 30.0),
        },
        "good": {
            "avg_range": (0.250, 0.290),
            "obp_range": (0.320, 0.370),
            "slg_range": (0.420, 0.520),
            "hr_range": (18, 32),
            "k_pct_range": (18, 25),
            "bb_pct_range": (7, 12),
            "ev_range": (86.0, 90.0),
            "barrel_range": (5.5, 10.0),
            "speed_range": (27.0, 28.5),
        },
        "average": {
            "avg_range": (0.230, 0.270),
            "obp_range": (0.300, 0.340),
            "slg_range": (0.380, 0.460),
            "hr_range": (12, 25),
            "k_pct_range": (20, 28),
            "bb_pct_range": (6, 10),
            "ev_range": (84.0, 88.0),
            "barrel_range": (4.0, 7.5),
            "speed_range": (26.5, 28.0),
        },
    }

    params = quality_params.get(quality, quality_params["average"])

    hitters = []

    # Batting order positions with typical profiles
    positions = [
        ("Leadoff", True, 1.1),      # Speed/OBP
        ("2nd Hitter", True, 1.05),  # Contact
        ("3rd Hitter", False, 0.90), # Best hitter
        ("Cleanup", False, 0.95),    # Power
        ("5th Hitter", False, 1.0),  # Balanced
        ("6th Hitter", False, 1.05), # Balanced
        ("7th Hitter", False, 1.1),  # Below average
        ("8th Hitter", True, 1.15),  # Speed/defense
        ("9th Hitter", True, 1.2),   # Pitcher-like
    ]

    for i, (pos_name, speed_oriented, multiplier) in enumerate(positions):
        name = f"{team_name} {pos_name}"

        avg_min, avg_max = params["avg_range"]
        avg = random.uniform(avg_min / multiplier, avg_max / multiplier)

        obp_min, obp_max = params["obp_range"]
        obp = random.uniform(obp_min / multiplier, obp_max / multiplier)

        slg_min, slg_max = params["slg_range"]
        slg = random.uniform(slg_min / multiplier, slg_max / multiplier)

        ops = obp + slg

        hr_min, hr_max = params["hr_range"]
        hr = int(random.uniform(hr_min / multiplier, hr_max / multiplier))

        ab = random.randint(450, 600)

        k_pct_min, k_pct_max = params["k_pct_range"]
        k_pct = random.uniform(k_pct_min * multiplier, k_pct_max * multiplier) / 100

        bb_pct_min, bb_pct_max = params["bb_pct_range"]
        bb_pct = random.uniform(bb_pct_min / multiplier, bb_pct_max / multiplier) / 100

        k = int(ab * k_pct)
        bb = int(ab * bb_pct)

        ev_min, ev_max = params["ev_range"]
        ev = random.uniform(ev_min / multiplier, ev_max / multiplier)

        barrel_min, barrel_max = params["barrel_range"]
        barrel = random.uniform(barrel_min / multiplier, barrel_max / multiplier)

        speed_min, speed_max = params["speed_range"]
        if speed_oriented:
            # Speed guys are faster
            speed = random.uniform(speed_min + 1, speed_max + 1.5)
        else:
            speed = random.uniform(speed_min, speed_max)

        sb = int(random.uniform(5, 30) if speed > 28 else random.uniform(0, 10))

        hitters.append({
            'player_name': name,
            'team': team_name,
            'season': season,
            'games_played': random.randint(140, 162),
            'at_bats': ab,
            'plate_appearances': int(ab * 1.15),
            'hits': int(ab * avg),
            'home_runs': hr,
            'runs': int(hr * 1.3 + random.randint(20, 40)),
            'rbi': int(hr * 1.5 + random.randint(20, 40)),
            'stolen_bases': sb,
            'walks': bb,
            'strikeouts': k,
            'batting_avg': round(avg, 3),
            'on_base_pct': round(obp, 3),
            'slugging_pct': round(slg, 3),
            'ops': round(ops, 3),
            'avg_exit_velo': round(ev, 1),
            'max_exit_velo': round(ev + random.uniform(8, 12), 1),
            'barrel_pct': round(barrel, 1),
            'sprint_speed': round(speed, 1),
        })

    return pd.DataFrame(hitters)


def populate_sample_teams(db_path: str = "baseball_teams.db"):
    """Populate database with sample teams."""

    print("\n" + "="*70)
    print("Populating Database with Sample Teams")
    print("="*70)

    db = TeamDatabase(db_path)

    # Create sample teams
    teams = [
        ("New York Yankees", "NYY", 2024, "elite"),
        ("Los Angeles Dodgers", "LAD", 2024, "elite"),
        ("Houston Astros", "HOU", 2024, "good"),
        ("Atlanta Braves", "ATL", 2024, "good"),
        ("Boston Red Sox", "BOS", 2024, "average"),
        ("Chicago Cubs", "CHC", 2024, "average"),
    ]

    for team_name, team_abbr, season, quality in teams:
        print(f"\nCreating {team_name} ({quality})...")

        # Create sample data
        pitchers_df = create_sample_pitchers(team_name, season, quality)
        hitters_df = create_sample_hitters(team_name, season, quality)

        # Store in database manually
        cursor = db.conn.cursor()

        # Create team
        cursor.execute("""
            INSERT OR REPLACE INTO teams (team_name, team_abbr, season)
            VALUES (?, ?, ?)
        """, (team_name, team_abbr, season))
        team_id = cursor.lastrowid

        # Store pitchers
        num_pitchers = 0
        for _, row in pitchers_df.iterrows():
            pitcher_id = db._store_pitcher(row, season)
            if pitcher_id:
                cursor.execute("""
                    INSERT INTO team_rosters (team_id, pitcher_id, is_starter)
                    VALUES (?, ?, ?)
                """, (team_id, pitcher_id, int(row.get('games_started', 0) > 0)))
                num_pitchers += 1

        # Store hitters
        num_hitters = 0
        for idx, row in hitters_df.iterrows():
            hitter_id = db._store_hitter(row, season)
            if hitter_id:
                cursor.execute("""
                    INSERT INTO team_rosters (team_id, hitter_id, batting_order)
                    VALUES (?, ?, ?)
                """, (team_id, hitter_id, idx + 1))
                num_hitters += 1

        db.conn.commit()

        print(f"  ✓ Stored {num_pitchers} pitchers and {num_hitters} hitters")

    db.close()

    print("\n" + "="*70)
    print("✓ Database populated successfully!")
    print("="*70)
    print("\nTry running:")
    print('  python manage_teams.py list')
    print('  python examples/simulate_mlb_matchup.py "New York Yankees" "Los Angeles Dodgers" 2024')
    print()


if __name__ == "__main__":
    populate_sample_teams()
