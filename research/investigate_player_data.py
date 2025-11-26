#!/usr/bin/env python
"""
Investigate player data in the database to identify gaps in player creation.

This script examines:
1. What raw stats are available for players
2. How those stats are converted to attributes
3. Whether the resulting physics parameters are realistic
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from batted_ball.database import TeamDatabase
from batted_ball.attributes import HitterAttributes
from batted_ball.database.stats_converter import StatsConverter

def investigate_database(db_path: str = "baseball_teams.db"):
    """Investigate player data in the database."""
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("=" * 80)
    print("PLAYER DATABASE INVESTIGATION")
    print("=" * 80)
    
    # 1. List available teams
    print("\n--- Available Teams ---")
    cursor.execute("SELECT team_id, team_name, team_abbr, season FROM teams ORDER BY season, team_name")
    teams = cursor.fetchall()
    for team in teams:
        print(f"  {team['team_name']} ({team['team_abbr']}, {team['season']})")
    
    if not teams:
        print("  No teams found in database!")
        return
    
    # Pick first team for analysis
    team = teams[0]
    team_id = team['team_id']
    team_name = team['team_name']
    season = team['season']
    print(f"\n--- Analyzing: {team_name} ({season}) ---")
    
    # 2. Analyze hitter data
    print("\n\n" + "=" * 80)
    print("HITTER RAW DATA ANALYSIS")
    print("=" * 80)
    
    # Get hitters via team_rosters join
    cursor.execute("""
        SELECT h.* FROM hitters h
        JOIN team_rosters tr ON tr.hitter_id = h.hitter_id
        WHERE tr.team_id = ? LIMIT 5
    """, (team_id,))
    
    hitters = cursor.fetchall()
    if hitters:
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        print(f"\nColumns available: {len(columns)}")
        print(", ".join(columns))
        
        print("\n--- Sample Hitter Data (first 5 players) ---")
        for h in hitters:
            print(f"\n  {h['player_name']}:")
            
            # Key batting stats
            if h['batting_avg']:
                print(f"    Batting: AVG={h['batting_avg']:.3f}, OBP={h['on_base_pct']:.3f}, "
                      f"SLG={h['slugging_pct']:.3f}, OPS={h['ops']:.3f}")
            
            # Power indicators
            if h['home_runs']:
                print(f"    Power: HR={h['home_runs']}, AB={h['at_bats']}, "
                      f"Barrel%={h['barrel_pct']}, EV={h['avg_exit_velo']}")
            
            # Speed
            print(f"    Speed: Sprint={h['sprint_speed']} ft/s, SB={h['stolen_bases']}" 
                  if h['sprint_speed'] else f"    Speed: Sprint=N/A, SB={h['stolen_bases']}")
            
            # Defensive
            if h['primary_position']:
                print(f"    Defense: Pos={h['primary_position']}, OAA={h['oaa']}, DRS={h['drs']}, "
                      f"Arm={h['arm_strength_mph']} mph")
            
            # Bat tracking
            if h['bat_speed']:
                print(f"    Bat Tracking: Speed={h['bat_speed']:.1f} mph, Swing={h['swing_length']} ft, "
                      f"Squared={h['squared_up_rate']}")
            else:
                print(f"    Bat Tracking: Not available")
            
            # Stored attributes
            print(f"    Attributes: Contact={h['contact']}, Power={h['power']}, "
                  f"Disc={h['discipline']}, Speed={h['speed']}")
            print(f"    v2 Attrs: Vision={h['vision']}, AttackAngle={h['attack_angle_control']}")
    
    # 3. Check for missing critical data
    print("\n\n" + "=" * 80)
    print("MISSING DATA ANALYSIS")
    print("=" * 80)
    
    cursor.execute("""
        SELECT COUNT(*) FROM hitters h
        JOIN team_rosters tr ON tr.hitter_id = h.hitter_id
        WHERE tr.team_id = ?
    """, (team_id,))
    total_hitters = cursor.fetchone()[0]
    
    critical_fields = [
        ('sprint_speed', 'Sprint Speed (Statcast)'),
        ('avg_exit_velo', 'Exit Velocity (Statcast)'),
        ('barrel_pct', 'Barrel % (Statcast)'),
        ('oaa', 'OAA (Defensive)'),
        ('arm_strength_mph', 'Arm Strength (Statcast)'),
        ('bat_speed', 'Bat Speed (Bat Tracking)'),
        ('squared_up_rate', 'Squared Up Rate (Bat Tracking)'),
    ]
    
    print(f"\nTotal hitters: {total_hitters}")
    print("\nMissing critical Statcast data:")
    for field, name in critical_fields:
        try:
            cursor.execute(f"""
                SELECT COUNT(*) FROM hitters h
                JOIN team_rosters tr ON tr.hitter_id = h.hitter_id
                WHERE tr.team_id = ? AND ({field} IS NULL OR {field} = 0)
            """, (team_id,))
            missing = cursor.fetchone()[0]
            pct = (missing / total_hitters * 100) if total_hitters > 0 else 0
            status = "⚠️" if pct > 50 else "✓" if pct == 0 else "⚡"
            print(f"  {status} {name}: {missing}/{total_hitters} missing ({pct:.0f}%)")
        except sqlite3.OperationalError:
            print(f"  ❌ {name}: Column not in database")
    
    # 4. Analyze converted attributes
    print("\n\n" + "=" * 80)
    print("ATTRIBUTE CONVERSION ANALYSIS")
    print("=" * 80)
    
    # Get a sample player with full data
    cursor.execute("""
        SELECT h.* FROM hitters h
        JOIN team_rosters tr ON tr.hitter_id = h.hitter_id
        WHERE tr.team_id = ? AND h.avg_exit_velo IS NOT NULL AND h.sprint_speed IS NOT NULL
        LIMIT 1
    """, (team_id,))
    sample = cursor.fetchone()
    
    if sample:
        print(f"\nSample player with full data: {sample['player_name']}")
        
        # Show raw stats
        print("\n  Raw Stats:")
        print(f"    AVG={sample['batting_avg']:.3f}, HR={sample['home_runs']}, "
              f"K={sample['strikeouts']}, BB={sample['walks']}, AB={sample['at_bats']}")
        print(f"    EV={sample['avg_exit_velo']:.1f} mph, Barrel%={sample['barrel_pct']:.1f}%, "
              f"Sprint={sample['sprint_speed']:.1f} ft/s")
        
        if sample['bat_speed']:
            print(f"    Bat Speed={sample['bat_speed']:.1f} mph (ACTUAL STATCAST DATA)")
        
        # Show stored attributes
        print("\n  Stored Attributes:")
        print(f"    Contact: {sample['contact']:,}")
        print(f"    Power: {sample['power']:,}")
        print(f"    Speed: {sample['speed']:,}")
        print(f"    Vision: {sample['vision']:,}")
        print(f"    Attack Angle Control: {sample['attack_angle_control']:,}")
        
        # Show what physical parameters these translate to
        print("\n  Physics Parameters from Attributes:")
        h_attrs = HitterAttributes(
            BAT_SPEED=sample['power'],
            ATTACK_ANGLE_CONTROL=sample['attack_angle_control'] or 50000,
            BARREL_ACCURACY=sample['contact'],
            VISION=sample['vision'] or 50000
        )
        
        print(f"    Bat Speed (from power attr): {h_attrs.get_bat_speed_mph():.1f} mph")
        if sample['bat_speed']:
            print(f"    Bat Speed (actual Statcast): {sample['bat_speed']:.1f} mph")
            diff = abs(h_attrs.get_bat_speed_mph() - sample['bat_speed'])
            print(f"    ⚠️ DISCREPANCY: {diff:.1f} mph difference!" if diff > 3 else f"    ✓ Within 3 mph")
        print(f"    Attack Angle Mean: {h_attrs.get_attack_angle_mean_deg():.1f}°")
        print(f"    Barrel Accuracy: {h_attrs.get_barrel_accuracy_mm():.1f} mm ({h_attrs.get_barrel_accuracy_mm()/25.4:.2f}\")")
        print(f"    Vision Factor: {h_attrs.get_tracking_ability_factor():.2f}")
    
    # 5. Check attribute distribution
    print("\n\n" + "=" * 80)
    print("ATTRIBUTE DISTRIBUTION (All Hitters)")
    print("=" * 80)
    
    cursor.execute("""
        SELECT 
            AVG(h.contact) as avg_contact,
            MIN(h.contact) as min_contact,
            MAX(h.contact) as max_contact,
            AVG(h.power) as avg_power,
            MIN(h.power) as min_power,
            MAX(h.power) as max_power,
            AVG(h.discipline) as avg_discipline,
            AVG(h.speed) as avg_speed,
            AVG(h.attack_angle_control) as avg_attack_angle,
            AVG(h.vision) as avg_vision,
            AVG(h.bat_speed) as avg_bat_speed_statcast,
            AVG(h.avg_exit_velo) as avg_ev_statcast
        FROM hitters h
        JOIN team_rosters tr ON tr.hitter_id = h.hitter_id
        WHERE tr.team_id = ?
    """, (team_id,))
    
    dist = cursor.fetchone()
    print(f"\n  Contact: min={dist['min_contact']:,.0f}, avg={dist['avg_contact']:,.0f}, max={dist['max_contact']:,.0f}")
    print(f"  Power: min={dist['min_power']:,.0f}, avg={dist['avg_power']:,.0f}, max={dist['max_power']:,.0f}")
    print(f"  Discipline: avg={dist['avg_discipline']:,.0f}")
    print(f"  Speed: avg={dist['avg_speed']:,.0f}")
    print(f"  Attack Angle Ctrl: avg={dist['avg_attack_angle']:,.0f}" if dist['avg_attack_angle'] else "  Attack Angle Ctrl: N/A")
    print(f"  Vision: avg={dist['avg_vision']:,.0f}" if dist['avg_vision'] else "  Vision: N/A")
    
    if dist['avg_bat_speed_statcast']:
        print(f"\n  Statcast Bat Speed (actual): avg={dist['avg_bat_speed_statcast']:.1f} mph")
    if dist['avg_ev_statcast']:
        print(f"  Statcast Exit Velo: avg={dist['avg_ev_statcast']:.1f} mph")
    
    # Show what these mean in physics terms
    print("\n  Physics implications from attributes:")
    for label, attr_val in [("Min Power", dist['min_power']), 
                            ("Avg Power", dist['avg_power']), 
                            ("Max Power", dist['max_power'])]:
        h = HitterAttributes(BAT_SPEED=attr_val)
        print(f"    {label} ({attr_val:,.0f}) → Bat Speed: {h.get_bat_speed_mph():.1f} mph")
    
    for label, attr_val in [("Min Contact", dist['min_contact']), 
                            ("Avg Contact", dist['avg_contact']), 
                            ("Max Contact", dist['max_contact'])]:
        h = HitterAttributes(BARREL_ACCURACY=attr_val)
        print(f"    {label} ({attr_val:,.0f}) → Barrel Error: {h.get_barrel_accuracy_mm():.1f} mm ({h.get_barrel_accuracy_mm()/25.4:.2f}\")")
    
    # 6. Compare with MLB targets
    print("\n\n" + "=" * 80)
    print("COMPARISON WITH MLB TARGETS")
    print("=" * 80)
    
    print("\n  MLB Target Values (from CLAUDE.md):")
    print("    Bat Speed: ~75 mph average, ~80-85 mph elite")
    print("    Exit Velocity: ~88 mph average, ~95+ mph elite")
    print("    Barrel Accuracy: ~0.6\" average, ~0.3-0.4\" elite")
    print("    Launch Angle: ~12° mean, ~15-20° std dev")
    print("    BABIP: ~0.295 target")
    print("    K Rate: ~22% target")
    
    print("\n  From Database Attributes:")
    avg_h = HitterAttributes(BAT_SPEED=dist['avg_power'], BARREL_ACCURACY=dist['avg_contact'])
    max_h = HitterAttributes(BAT_SPEED=dist['max_power'], BARREL_ACCURACY=dist['max_contact'])
    print(f"    Avg hitter: Bat Speed={avg_h.get_bat_speed_mph():.1f} mph, "
          f"Barrel Error={avg_h.get_barrel_accuracy_mm()/25.4:.2f}\"")
    print(f"    Best hitter: Bat Speed={max_h.get_bat_speed_mph():.1f} mph, "
          f"Barrel Error={max_h.get_barrel_accuracy_mm()/25.4:.2f}\"")
    
    if dist['avg_bat_speed_statcast']:
        print(f"\n  ⚠️ CRITICAL: Actual Statcast bat speed avg={dist['avg_bat_speed_statcast']:.1f} mph")
        print(f"     but power attribute produces bat speed={avg_h.get_bat_speed_mph():.1f} mph")
        diff = abs(dist['avg_bat_speed_statcast'] - avg_h.get_bat_speed_mph())
        if diff > 5:
            print(f"     ❌ MAJOR GAP: {diff:.1f} mph difference - bat speed not being used!")
    
    conn.close()
    
    # 7. Key findings
    print("\n\n" + "=" * 80)
    print("KEY FINDINGS / POTENTIAL ISSUES")
    print("=" * 80)
    print("""
    Check the output above for:
    
    1. MISSING STATCAST DATA
       - If sprint_speed, avg_exit_velo, or barrel_pct are missing for many players,
         the attribute conversion falls back to less accurate estimates
    
    2. BAT SPEED MISMATCH
       - We now have ACTUAL bat speed from Statcast bat tracking (2024+)
       - But the simulation uses BAT_SPEED derived from power attribute!
       - This means actual bat speeds are NOT used in the physics simulation
       - FIX: Use bat_speed column directly in HitterAttributes instead of deriving
    
    3. SQUARED-UP RATE NOT USED
       - We fetch squared_up_rate from bat tracking (0-1 scale)
       - This directly measures contact quality but isn't mapped to BARREL_ACCURACY
       - FIX: Use squared_up_rate to inform barrel accuracy attribute
    
    4. ATTACK ANGLE CONTROL IS INFERRED
       - attack_angle_control is calculated from HR rate, SLG, barrel%
       - NOT from actual launch angle data
       - This may produce wrong launch angle distributions
    
    5. ATTRIBUTE SCALING ISSUES  
       - If avg_power is too low (< 50k), bat speeds may be wrong
       - If avg_contact is too high, barrel accuracy may be too tight
    """)


if __name__ == "__main__":
    investigate_database()
