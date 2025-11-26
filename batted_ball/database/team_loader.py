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
        
        PHASE 3 UPDATE (2025-11-26): Uses real bat tracking data when available:
        - bat_speed (mph) → actual_bat_speed_mph (direct, scaled to sim range)
        - squared_up_rate → actual_barrel_accuracy_mm (converted via mapping)
        
        When Statcast data is available, it's used directly. Otherwise, falls back
        to attribute-based derivation.

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
        # BAT_SPEED: Use real bat tracking data if available (TRUE values)
        # ============================================================
        # Bat tracking data provides actual swing speed in mph from Baseball Savant
        # 
        # PHASE 3 UPDATE 2025-11-26: Using TRUE bat speeds (no scaling)
        # Real MLB bat speeds: 63-79 mph
        # 
        # To compensate for lower bat speeds, collision efficiency (q) was increased
        # from 0.13 to 0.18. This maintains the same exit velocities while using
        # physically accurate bat speeds from Statcast data.
        #
        # Math: EV = q × pitch_speed + (1 + q) × bat_speed
        # Old: q_eff=0.064, bat=83 mph → 89 mph EV
        # New: q_eff=0.110, bat=71 mph → 89 mph EV (same result)
        actual_bat_speed_mph = record.get('bat_speed')
        true_bat_speed_mph = None  # Will be passed to HitterAttributes
        
        if actual_bat_speed_mph is not None and actual_bat_speed_mph > 0:
            # Use TRUE bat speed directly (no scaling)
            true_bat_speed_mph = float(actual_bat_speed_mph)
            # Use 50k as placeholder BAT_SPEED rating (won't be used due to actual value)
            boosted_bat_speed = 50000
        else:
            # Fallback: Use power-based estimation (legacy method)
            # FIX 2025-11-25: Boosted BAT_SPEED to match generic teams
            if raw_power >= 70000:
                bat_speed_boost = 25000  # Power hitters
            elif raw_power >= 50000:
                bat_speed_boost = 22000  # Balanced hitters
            else:
                bat_speed_boost = 18000  # Contact hitters

            boosted_bat_speed = min(raw_power + bat_speed_boost, 100000)

        # ============================================================
        # BARREL_ACCURACY: Convert squared-up rate to barrel error in mm
        # ============================================================
        # squared_up_rate from bat tracking tells us how often hitter squares up the ball
        # Range: ~16% to ~43% (MLB 2024 data)
        # 
        # PHASE 3: Direct conversion to physical barrel accuracy
        # Higher squared_up_rate → smaller error → more solid contact
        base_barrel_accuracy = record['contact']  # For fallback rating
        actual_barrel_accuracy_mm = None  # Will be passed to HitterAttributes
        
        squared_up_rate = record.get('squared_up_rate')
        if squared_up_rate is not None and squared_up_rate > 0:
            # Convert squared-up rate to barrel error in mm using research mapping:
            # - 0.36 (elite, ~36%) → 7.5mm (0.3")
            # - 0.28 (average, ~28%) → 15mm (0.6")
            # - 0.18 (poor, ~18%) → 25mm (1.0")
            # 
            # Linear interpolation: error = 40 - 90*rate (clamped to 5-30mm range)
            # This formula gives:
            #   rate=0.40 → 40-36=4mm (elite)
            #   rate=0.28 → 40-25.2=14.8mm (average)  
            #   rate=0.18 → 40-16.2=23.8mm (poor)
            #   rate=0.10 → 40-9=31mm (very poor)
            squared_up_pct = squared_up_rate if squared_up_rate < 1 else squared_up_rate / 100
            barrel_error_mm = 40.0 - 90.0 * squared_up_pct
            actual_barrel_accuracy_mm = max(5.0, min(30.0, barrel_error_mm))
            # Keep base_barrel_accuracy as fallback rating (won't be used due to actual value)
            adjusted_barrel_accuracy = base_barrel_accuracy
        else:
            # No squared-up data - use contact attribute only
            adjusted_barrel_accuracy = base_barrel_accuracy

        # ATTACK_ANGLE_CONTROL: Use stored value if available, otherwise boost based on power
        # FIX 2025-11-25 v3: ALWAYS apply boost to match generic team creation
        # Generic teams use: power=72-88k (18-24° LA), balanced=58-75k (13-18° LA)
        # 
        # The problem is that stored AAC values from stats_converter (50-70k) are too 
        # conservative compared to generic teams. Even elite power hitters like Michael Busch
        # (34 HR, .523 SLG) only get ~68k AAC, but need 75-85k for realistic HR production.
        #
        # Solution: Apply aggressive boost based on power level + home run rate indicators
        stored_aac = record.get('attack_angle_control')
        
        # Get HR rate indicators from the record
        hr_count = record.get('home_runs', 0) or 0
        ab_count = record.get('at_bats', 1) or 1  # Avoid division by zero
        slg = record.get('slugging_pct', 0.400) or 0.400
        
        # Determine hitter archetype based on ACTUAL production, not power rating
        is_elite_power = (hr_count >= 35) or (slg >= 0.550)  # Top ~10-15 hitters in MLB
        is_good_power = (hr_count >= 25) or (slg >= 0.480)   # Top 30-40 power hitters
        is_moderate_power = (hr_count >= 15) or (slg >= 0.420)
        
        # Calculate AAC based on actual production - conservative for realistic GB%
        if is_elite_power:
            min_aac = 80000  # Elite power: 80k for ~15.8° mean LA
        elif is_good_power:
            min_aac = 70000  # Good power: 70k for ~13.8° mean LA
        elif is_moderate_power:
            min_aac = 60000  # Moderate power: 60k for ~10.4° mean LA
        elif raw_power >= 40000:
            min_aac = 50000  # Average hitter: 50k for ~7° mean LA (MLB average)
        else:
            min_aac = 45000  # Contact/speed hitter: 45k for ~5° mean LA (more GBs)
        
        if stored_aac is None or stored_aac == 0:
            attack_angle_control = min_aac
        else:
            attack_angle_control = max(stored_aac, min_aac)

        # Create HitterAttributes with actual Statcast data if available
        hitter_attrs = HitterAttributes(
            BAT_SPEED=boosted_bat_speed,  # Rating (used if actual not available)
            BARREL_ACCURACY=adjusted_barrel_accuracy,  # Rating (used if actual not available)
            ZONE_DISCERNMENT=record['discipline'],  # Discipline maps to pitch recognition
            VISION=record.get('vision', 50000),  # Contact frequency, default to average
            ATTACK_ANGLE_CONTROL=attack_angle_control,  # Launch angle tendency
            # PHASE 3: Direct Statcast measurements (override derived values)
            actual_bat_speed_mph=true_bat_speed_mph,  # None if not available
            actual_barrel_accuracy_mm=actual_barrel_accuracy_mm,  # None if not available
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
