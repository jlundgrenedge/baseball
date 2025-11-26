"""
Load teams from database for game simulations.

Converts database player records into Pitcher/Hitter/Team objects
ready for use in game simulations.
"""

from typing import List, Optional, Dict
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from batted_ball import Pitcher, Hitter
from batted_ball.attributes import PitcherAttributes, HitterAttributes
from batted_ball.game_simulation import Team
from batted_ball.player import generate_pitch_arsenal
from batted_ball.defense_factory import create_standard_defense

from .team_database import TeamDatabase


class TeamLoader:
    """Load teams from database for simulations."""

    def __init__(self, db_path: str = "baseball_teams.db"):
        """
        Initialize team loader.

        Parameters
        ----------
        db_path : str
            Path to database file
        """
        self.db = TeamDatabase(db_path)

    def close(self):
        """Close database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.close()

    def load_team(
        self,
        team_name: str,
        season: int = 2024,
        max_pitchers: int = 9,
        max_hitters: int = 9,
        num_starters: int = 5,
        num_relievers: int = 4
    ) -> Optional[Team]:
        """
        Load a team from the database for simulation.

        Parameters
        ----------
        team_name : str
            Team name (e.g., 'New York Yankees')
        season : int
            Season year
        max_pitchers : int
            Maximum number of pitchers to include (total)
        max_hitters : int
            Maximum number of hitters to include (by batting order)
        num_starters : int
            Number of starting pitchers to include (default 5)
        num_relievers : int
            Number of relief pitchers to include (default 4)

        Returns
        -------
        Team or None
            Team object ready for simulation, or None if not found
        """
        # Get team data from database
        team_data = self.db.get_team_data(team_name, season)
        if not team_data:
            print(f"Team '{team_name}' not found in database for season {season}")
            return None

        team_info = team_data['team_info']
        all_pitcher_records = team_data['pitchers']
        hitter_records = team_data['hitters'][:max_hitters]

        # Split pitchers into starters and relievers based on is_starter flag
        starter_records = [p for p in all_pitcher_records if p.get('is_starter', 0)]
        reliever_records = [p for p in all_pitcher_records if not p.get('is_starter', 0)]
        
        # Take the requested number of each, sorted by innings pitched
        starter_records = sorted(starter_records, key=lambda p: p.get('innings_pitched', 0) or 0, reverse=True)[:num_starters]
        reliever_records = sorted(reliever_records, key=lambda p: p.get('innings_pitched', 0) or 0, reverse=True)[:num_relievers]
        
        # Combine: starters first, then relievers
        pitcher_records = starter_records + reliever_records

        # Convert pitchers
        pitchers = []
        for record in pitcher_records:
            pitcher = self._create_pitcher_from_record(record)
            if pitcher:
                pitchers.append(pitcher)

        # Convert hitters
        hitters = []
        for record in hitter_records:
            hitter = self._create_hitter_from_record(record)
            if hitter:
                hitters.append(hitter)

        # Ensure we have minimum required players
        if len(pitchers) < 1:
            print(f"Warning: No pitchers found for {team_name}")
            return None

        if len(hitters) < 9:
            print(f"Warning: Only {len(hitters)} hitters found for {team_name}, need 9")
            # Duplicate existing hitters to fill lineup
            while len(hitters) < 9:
                hitters.append(hitters[len(hitters) % len(hitters)])

        # Fill pitcher rotation if needed
        while len(pitchers) < 9:
            pitchers.append(pitchers[len(pitchers) % len(pitchers)])

        # Create fielders dictionary from hitters' fielder objects (v2: player-specific defensive attributes)
        # This replaces create_standard_defense() which uses generic 50k fielders
        
        # Map database position abbreviations to standard position names
        POSITION_MAP = {
            'P': 'pitcher', 'C': 'catcher',
            '1B': 'first_base', '2B': 'second_base', '3B': 'third_base', 'SS': 'shortstop',
            'LF': 'left_field', 'CF': 'center_field', 'RF': 'right_field'
        }
        
        fielders = {}
        for hitter in hitters[:9]:  # Use first 9 hitters
            if hasattr(hitter, 'fielder') and hitter.fielder is not None:
                position_abbr = hitter.fielder.position.upper()  # Normalize to uppercase
                position_name = POSITION_MAP.get(position_abbr, position_abbr.lower())
                fielders[position_name] = hitter.fielder

        # If we don't have enough fielders (shouldn't happen), fill with defaults
        if len(fielders) < 9:
            print(f"Warning: Only {len(fielders)} fielders found, filling with defaults")
            default_fielders = create_standard_defense()
            # Merge: default fielders for missing positions
            for pos, fielder in default_fielders.items():
                if pos not in fielders:
                    fielders[pos] = fielder

        # Create Team object
        team = Team(
            name=team_info['team_name'],
            pitchers=pitchers,
            hitters=hitters[:9],  # Take first 9 for batting order
            fielders=fielders
        )

        print(f"[OK] Loaded {team_info['team_name']} ({season})")
        print(f"  {len(pitchers)} pitchers, {len(hitters)} hitters")  

        return team

    def _create_pitcher_from_record(self, record: Dict) -> Optional[Pitcher]:
        """
        Create a Pitcher object from database record (v2: includes NIBBLING_TENDENCY).

        Parameters
        ----------
        record : dict
            Database record with pitcher stats and attributes

        Returns
        -------
        Pitcher or None
        """
        # Create PitcherAttributes from stored ratings (v1 + v2)
        # Note: PUTAWAY_SKILL was removed - put-away mechanism uses get_stuff_rating()
        # which is calculated from RAW_VELOCITY_CAP, SPIN_RATE_CAP, and DECEPTION
        
        # NIBBLING_TENDENCY: Database stores as 0.0-1.0 REAL, but PitcherAttributes needs 0-100k
        nibbling_db = record.get('nibbling_tendency', 0.50)  # Get 0.0-1.0 value
        nibbling_attr = int(nibbling_db * 100000)  # Convert to 0-100k scale
        
        attrs = PitcherAttributes(
            RAW_VELOCITY_CAP=record['velocity'],
            COMMAND=record['command'],
            STAMINA=record['stamina'],
            SPIN_RATE_CAP=record['movement'],  # Use movement for spin
            # v2 attribute (Phase 2B addition)
            NIBBLING_TENDENCY=nibbling_attr,  # Converted from 0.0-1.0 to 0-100k
        )

        # Determine if starter based on is_starter flag from team_rosters
        # Fallback: use games_pitched heuristic if flag not available
        is_starter = record.get('is_starter', 0)
        if is_starter is None:
            is_starter = record.get('games_pitched', 0) > 15

        # Generate realistic pitch arsenal based on velocity/movement
        arsenal = generate_pitch_arsenal(
            attrs,
            role="starter" if is_starter else "reliever"
        )

        # Create Pitcher with is_starter flag
        pitcher = Pitcher(
            name=record['player_name'],
            attributes=attrs,
            pitch_arsenal=arsenal,
            is_starter=bool(is_starter)
        )

        return pitcher

    def _create_hitter_from_record(self, record: Dict) -> Optional[Hitter]:
        """
        Create a Hitter object from database record (v2: includes VISION + defensive attributes).
        
        v3 UPDATE (2025-11-25): Uses real bat tracking data when available:
        - bat_speed (mph) → BAT_SPEED attribute (direct mapping)
        - squared_up_rate → BARREL_ACCURACY adjustment
        - swing_length/hard_swing_rate → informational

        Parameters
        ----------
        record : dict
            Database record with hitter stats and attributes

        Returns
        -------
        Hitter or None
        """
        # Get power rating (needed for AAC calculation regardless of bat tracking availability)
        raw_power = record['power']
        
        # ============================================================
        # BAT_SPEED: Use real bat tracking data if available (SCALED to simulation range)
        # ============================================================
        # Bat tracking data provides actual swing speed in mph from Baseball Savant
        # 
        # CRITICAL: Real MLB bat speeds (63-79 mph) are LOWER than what the simulation expects!
        # The simulation was calibrated expecting ~75-90 mph bat speeds (old power-based method).
        # 
        # Solution: Scale real bat speeds to simulation-expected range:
        # - Real MLB range: 63-79 mph (16 mph spread)
        # - Simulation expected range: 75-91 mph (16 mph spread)  
        # - Offset: +12 mph
        #
        # This preserves relative differences (Oneil Cruz is still fastest) while
        # ensuring bat speeds produce realistic exit velocities for HR generation.
        actual_bat_speed_mph = record.get('bat_speed')
        
        if actual_bat_speed_mph is not None and actual_bat_speed_mph > 0:
            # Scale real bat speed to simulation range
            # Real: 63-79 mph → Sim: 75-91 mph (add 12 mph)
            bat_speed_mph = float(actual_bat_speed_mph) + 12.0
            
            # Convert simulation bat speed (mph) to attribute rating (0-100k)
            # Using inverse of piecewise_logistic_map with same parameters as get_bat_speed_mph()
            # human_min=60, human_cap=85, super_cap=95, H=85000
            
            # Inverse mapping: mph → rating
            # For the human range (60-85 mph → 0-85k):
            if bat_speed_mph <= 85.0:
                # Normalize to 0-1 in the human range
                normalized = (bat_speed_mph - 60.0) / (85.0 - 60.0)
                # Clamp to valid range
                normalized = max(0.0, min(1.0, normalized))
                # Apply inverse sigmoid scaling (k=8) and scale to 0-85k
                # sigmoid(x) = normalized → x = ln(normalized / (1-normalized))
                if normalized <= 0.01:
                    bat_speed_rating = 0
                elif normalized >= 0.99:
                    bat_speed_rating = 85000
                else:
                    import math
                    x = math.log(normalized / (1 - normalized))
                    # x was scaled by k=8 and shifted by -k/2, so: rating = (x + k/2) / k * H
                    bat_speed_rating = int(((x + 4) / 8) * 85000)
                    bat_speed_rating = max(0, min(85000, bat_speed_rating))
            else:
                # Superhuman range (85-95 mph → 85k-100k)
                normalized = (bat_speed_mph - 85.0) / (95.0 - 85.0)
                normalized = max(0.0, min(1.0, normalized))
                if normalized <= 0.01:
                    bat_speed_rating = 85000
                elif normalized >= 0.99:
                    bat_speed_rating = 100000
                else:
                    import math
                    x = math.log(normalized / (1 - normalized))
                    bat_speed_rating = int(85000 + ((x + 2.5) / 5) * 15000)
                    bat_speed_rating = max(85000, min(100000, bat_speed_rating))
            
            boosted_bat_speed = bat_speed_rating
        else:
            # Fallback: Use power-based estimation (legacy method)
            # FIX 2025-11-25: Boosted BAT_SPEED to match generic teams
            raw_power = record['power']
            if raw_power >= 70000:
                bat_speed_boost = 25000  # Power hitters
            elif raw_power >= 50000:
                bat_speed_boost = 22000  # Balanced hitters
            else:
                bat_speed_boost = 18000  # Contact hitters

            boosted_bat_speed = min(raw_power + bat_speed_boost, 100000)

        # ATTACK_ANGLE_CONTROL: Use stored value if available, otherwise boost based on power
        # FIX 2025-11-25 v3: ALWAYS apply boost to match generic team creation
        # Generic teams use: power=72-88k (18-24° LA), balanced=58-75k (13-18° LA)
        # 
        # The problem is that stored AAC values from stats_converter (50-70k) are too 
        # conservative compared to generic teams. Even elite power hitters like Michael Busch
        # (34 HR, .523 SLG) only get ~68k AAC, but need 75-85k for realistic HR production.
        #
        # Solution: Apply aggressive boost based on power level + home run rate indicators
        #
        # AAC → Launch Angle mapping:
        #   AAC=78k → LA=16.2° (too low for HRs)
        #   AAC=85k → LA=16.6°
        #   AAC=90k → LA=20.3°
        #   AAC=95k → LA=24.7° (good for HRs)
        #   AAC=100k → LA=27.2° (optimal HR zone)
        #
        # To get home runs, we need 20-28° launch angles, which requires AAC in 90-100k range!
        stored_aac = record.get('attack_angle_control')
        
        # Get HR rate indicators from the record
        hr_count = record.get('home_runs', 0) or 0
        ab_count = record.get('at_bats', 1) or 1  # Avoid division by zero
        slg = record.get('slugging_pct', 0.400) or 0.400
        hr_per_ab = hr_count / ab_count if ab_count > 0 else 0
        
        # Determine hitter archetype based on ACTUAL production, not power rating
        # The key insight: We were setting almost EVERYONE to 90k+ AAC, which produces
        # 20°+ mean launch angles. That's WAY too high for realistic batted ball distribution.
        #
        # MLB batted ball splits: 43% GB, 21% LD, 36% FB
        # To achieve this, we need MOST hitters around 8-12° mean launch angle (AAC ~55-65k)
        # with variance (15°) creating the natural GB/LD/FB distribution.
        #
        # Only true elite power hitters (30+ HR) should have elevated attack angles (16-20°).
        #
        # AAC → Launch Angle mapping (from attributes.py):
        #   AAC=50k → LA=7° (MLB average - produces correct GB% with 15° variance)
        #   AAC=60k → LA=10.4°
        #   AAC=70k → LA=13.8°
        #   AAC=80k → LA=15.8°
        #   AAC=85k → LA=16.5°
        #   AAC=90k → LA=20.3° (power hitter territory)
        #   AAC=95k → LA=24.7° (elite fly ball hitter)
        #
        is_elite_power = (hr_count >= 35) or (slg >= 0.550)  # Top ~10-15 hitters in MLB
        is_good_power = (hr_count >= 25) or (slg >= 0.480)   # Top 30-40 power hitters
        is_moderate_power = (hr_count >= 15) or (slg >= 0.420)
        
        # Calculate AAC based on actual production - MUCH more conservative than before
        # Goal: Average AAC around 55k for realistic GB% (~43%)
        if is_elite_power:
            min_aac = 80000  # Elite power: 80k for ~15.8° mean LA (still produces HRs with variance)
        elif is_good_power:
            min_aac = 70000  # Good power: 70k for ~13.8° mean LA
        elif is_moderate_power:
            min_aac = 60000  # Moderate power: 60k for ~10.4° mean LA
        elif raw_power >= 40000:
            min_aac = 50000  # Average hitter: 50k for ~7° mean LA (MLB average)
        else:
            min_aac = 45000  # Contact/speed hitter: 45k for ~5° mean LA (more GBs)
        
        if stored_aac is None or stored_aac == 0:
            # No stored value - use production-based calculation
            attack_angle_control = min_aac
        else:
            # ALWAYS ensure at least minimum AAC for power level
            # This is the key fix: stored values are too low, boost them up
            attack_angle_control = max(stored_aac, min_aac)

        # ============================================================
        # BARREL_ACCURACY: Adjust based on squared-up rate if available
        # ============================================================
        # squared_up_rate from bat tracking tells us how often hitter squares up the ball
        # Range: ~16% to ~43% (MLB 2024 data)
        # 
        # This should influence BARREL_ACCURACY which controls contact quality
        # Higher squared_up_rate → better barrel accuracy → more solid contact
        base_barrel_accuracy = record['contact']  # Start with contact attribute
        
        squared_up_rate = record.get('squared_up_rate')
        if squared_up_rate is not None and squared_up_rate > 0:
            # MLB average squared_up_rate is ~26%
            # Range is approximately 16% to 43%
            # Map this to a modifier for barrel accuracy
            # +10k for elite (>35%), +5k for good (>30%), 0 for average, -5k for poor (<20%)
            squared_up_pct = squared_up_rate * 100 if squared_up_rate < 1 else squared_up_rate
            
            if squared_up_pct >= 35:
                barrel_accuracy_mod = 10000  # Elite contact quality
            elif squared_up_pct >= 30:
                barrel_accuracy_mod = 5000   # Good contact quality
            elif squared_up_pct >= 24:
                barrel_accuracy_mod = 0      # Average
            elif squared_up_pct >= 20:
                barrel_accuracy_mod = -3000  # Below average
            else:
                barrel_accuracy_mod = -5000  # Poor contact quality
            
            adjusted_barrel_accuracy = min(100000, max(0, base_barrel_accuracy + barrel_accuracy_mod))
        else:
            adjusted_barrel_accuracy = base_barrel_accuracy

        hitter_attrs = HitterAttributes(
            BAT_SPEED=boosted_bat_speed,  # Real bat speed or power-based estimate
            BARREL_ACCURACY=adjusted_barrel_accuracy,  # Contact + squared-up adjustment
            ZONE_DISCERNMENT=record['discipline'],  # Discipline maps to pitch recognition
            # v2 attributes (Phase 2A/2C additions)
            VISION=record.get('vision', 50000),  # Contact frequency, default to average if missing
            # ATTACK_ANGLE_CONTROL is CRITICAL for HR generation (Phase 2C fix)
            # Without this, DB teams default to 50k which is much lower than generic teams (72k-88k for power)
            ATTACK_ANGLE_CONTROL=attack_angle_control,  # Launch angle tendency (dynamic fallback)
        )

        # Create Hitter with speed for baserunning
        hitter = Hitter(
            name=record['player_name'],
            attributes=hitter_attrs,
            speed=record['speed']  # Use stored speed rating for baserunning
        )

        # Create player-specific Fielder with defensive attributes (v2: CRITICAL for BABIP tuning)
        # This replaces generic 50k fielders with realistic defensive variety
        from batted_ball.attributes import FielderAttributes
        from batted_ball.fielding import Fielder

        defensive_attrs = FielderAttributes(
            REACTION_TIME=record.get('reaction_time', 50000),  # Default to average if missing
            TOP_SPRINT_SPEED=record.get('top_sprint_speed', 50000),
            ROUTE_EFFICIENCY=record.get('route_efficiency', 50000),
            ARM_STRENGTH=record.get('arm_strength', 50000),
            ARM_ACCURACY=record.get('arm_accuracy', 50000),
            FIELDING_SECURE=record.get('fielding_secure', 50000),
            # Other attributes use defaults
        )

        # Get position for fielder (default to LF if missing)
        position = record.get('primary_position', 'LF')
        if position is None or position == '':
            position = 'LF'
        # Normalize to uppercase (database may have lowercase)
        position = position.upper()

        fielder = Fielder(
            name=record['player_name'],
            position=position,
            attributes=defensive_attrs
        )

        # Link fielder to hitter for field/hit integration
        hitter.fielder = fielder

        return hitter

    def list_available_teams(self, season: Optional[int] = None) -> List[str]:
        """
        List all available teams in database.

        Parameters
        ----------
        season : int, optional
            Filter by season

        Returns
        -------
        list of str
            Team names
        """
        teams = self.db.list_teams(season=season)
        return [f"{team['team_name']} ({team['season']})" for team in teams]


if __name__ == "__main__":
    # Test team loading
    print("=== Team Loader Test ===\n")

    loader = TeamLoader("test_baseball.db")

    # List available teams
    print("Available teams:")
    teams = loader.list_available_teams()
    for team in teams:
        print(f"  {team}")

    # Try to load a team
    if teams:
        # Parse first team name and season
        team_str = teams[0]
        team_name = team_str.split(" (")[0]
        season = int(team_str.split("(")[1].rstrip(")"))

        print(f"\nLoading {team_name} ({season})...")
        team = loader.load_team(team_name, season)

        if team:
            print(f"\nTeam loaded successfully!")
            print(f"  Name: {team.name}")
            print(f"  Pitchers: {len(team.pitchers)}")
            print(f"  Lineup: {len(team.lineup)}")

            print("\n  Sample pitcher:")
            p = team.pitchers[0]
            print(f"    {p.name}")
            print(f"    Velocity: {p.attributes.get_raw_velocity_mph():.1f} mph")
            print(f"    Stamina: {p.attributes.get_stamina_pitches():.0f} pitches")

            print("\n  Sample hitter:")
            h = team.lineup[0]
            print(f"    {h.name}")
            print(f"    Bat speed: {h.hitter_attributes.get_bat_speed_mph():.1f} mph")
            print(f"    Sprint speed: {h.fielder_attributes.get_sprint_speed_fps():.1f} ft/s")

    loader.close()
    print("\nTest complete!")
