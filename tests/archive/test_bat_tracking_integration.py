"""
Test script for bat tracking data integration.

Validates that bat tracking data from Baseball Savant is properly integrated
into the game simulation via the team loader.

Bat Tracking Metrics Used:
- bat_speed (mph): Average swing speed → BAT_SPEED attribute (direct mapping)
- squared_up_rate: How often ball is squared up → BARREL_ACCURACY adjustment
- swing_length (ft): Stored for future use
- hard_swing_rate: Stored for future use

Author: Claude
Date: 2025-11-25
"""

import sqlite3
from batted_ball.database.team_loader import TeamLoader


def test_bat_tracking_mapping():
    """Test that bat speed maps correctly from mph to rating and back."""
    print("=" * 80)
    print("BAT TRACKING DATA INTEGRATION TEST")
    print("=" * 80)
    
    # Load a team with bat tracking data
    loader = TeamLoader()
    team = loader.load_team('St. Louis Cardinals', 2025)
    
    if team is None:
        print("ERROR: Could not load team")
        return False
    
    # Get database values for comparison
    conn = sqlite3.connect('baseball_teams.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT player_name, bat_speed, squared_up_rate, contact 
        FROM hitters 
        WHERE bat_speed IS NOT NULL
    ''')
    db_data = {row[0]: {'bat_speed': row[1], 'squared_up': row[2], 'contact': row[3]} 
               for row in cursor.fetchall()}
    conn.close()
    
    print("\n1. BAT SPEED MAPPING TEST")
    print("-" * 80)
    print(f"{'Player':<25} {'DB mph':<12} {'Rating':<12} {'Mapped mph':<12} {'Match?':<8}")
    print("-" * 80)
    
    all_passed = True
    for hitter in team.hitters:
        if hitter.name in db_data:
            db_mph = db_data[hitter.name]['bat_speed']
            rating = hitter.attributes.BAT_SPEED
            mapped_mph = hitter.attributes.get_bat_speed_mph()
            
            # NOTE: We apply +12 mph scaling to real bat speeds to match simulation expectations
            # Real MLB: 63-79 mph → Simulation: 75-91 mph
            scaled_db_mph = db_mph + 12.0 if db_mph else db_mph
            
            # Check if mapping is accurate (within 0.5 mph of SCALED value)
            match = abs(scaled_db_mph - mapped_mph) < 0.5
            status = "✓" if match else "✗"
            if not match:
                all_passed = False
            
            print(f"{hitter.name:<25} {db_mph:<12.1f} {rating:<12.0f} {mapped_mph:<12.1f} {status:<8} (scaled: {scaled_db_mph:.1f})")
    
    print("\n2. SQUARED-UP RATE ADJUSTMENT TEST")
    print("-" * 80)
    print(f"{'Player':<25} {'Sq-Up %':<10} {'Base BA':<10} {'Modifier':<10} {'Final BA':<10}")
    print("-" * 80)
    
    for hitter in team.hitters:
        if hitter.name in db_data:
            sq_rate = db_data[hitter.name]['squared_up']
            base_contact = db_data[hitter.name]['contact']
            final_ba = hitter.attributes.BARREL_ACCURACY
            
            if sq_rate:
                sq_pct = sq_rate * 100 if sq_rate < 1 else sq_rate
                
                # Calculate expected modifier
                if sq_pct >= 35:
                    expected_mod = 10000
                elif sq_pct >= 30:
                    expected_mod = 5000
                elif sq_pct >= 24:
                    expected_mod = 0
                elif sq_pct >= 20:
                    expected_mod = -3000
                else:
                    expected_mod = -5000
                
                expected_final = min(100000, max(0, base_contact + expected_mod))
                match = final_ba == expected_final
                status = "✓" if match else "✗"
                
                print(f"{hitter.name:<25} {sq_pct:<10.1f} {base_contact:<10.0f} {expected_mod:>+10} {final_ba:<10.0f} {status}")
    
    loader.close()
    
    print("\n" + "=" * 80)
    print("TEST COMPLETE")
    print("=" * 80)
    
    return all_passed


def show_bat_tracking_stats():
    """Display bat tracking data currently in database."""
    conn = sqlite3.connect('baseball_teams.db')
    cursor = conn.cursor()
    
    # Summary stats
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            AVG(bat_speed) as avg_bat_speed,
            MIN(bat_speed) as min_bat_speed,
            MAX(bat_speed) as max_bat_speed,
            AVG(squared_up_rate) * 100 as avg_squared_up,
            AVG(hard_swing_rate) * 100 as avg_hard_swing
        FROM hitters 
        WHERE bat_speed IS NOT NULL
    ''')
    row = cursor.fetchone()
    
    print("\n" + "=" * 80)
    print("BAT TRACKING DATA SUMMARY")
    print("=" * 80)
    print(f"Players with bat tracking: {row[0]}")
    print(f"Bat speed range: {row[2]:.1f} - {row[3]:.1f} mph (avg: {row[1]:.1f})")
    print(f"Squared-up rate: {row[4]:.1f}% avg")
    print(f"Hard swing rate: {row[5]:.1f}% avg")
    
    # Top 5 by bat speed
    print("\nTop 5 Bat Speed:")
    cursor.execute('''
        SELECT player_name, bat_speed, squared_up_rate * 100
        FROM hitters 
        WHERE bat_speed IS NOT NULL
        ORDER BY bat_speed DESC
        LIMIT 5
    ''')
    for name, bs, sq in cursor.fetchall():
        print(f"  {name}: {bs:.1f} mph, {sq:.1f}% squared-up")
    
    conn.close()


if __name__ == "__main__":
    show_bat_tracking_stats()
    print()
    test_bat_tracking_mapping()
