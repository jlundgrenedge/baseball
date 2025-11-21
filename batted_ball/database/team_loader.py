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
        max_hitters: int = 9
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
            Maximum number of pitchers to include (top N by innings)
        max_hitters : int
            Maximum number of hitters to include (by batting order)

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
        pitcher_records = team_data['pitchers'][:max_pitchers]
        hitter_records = team_data['hitters'][:max_hitters]

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

        # Generate realistic pitch arsenal based on velocity/movement
        arsenal = generate_pitch_arsenal(
            attrs,
            role="starter" if record.get('games_pitched', 0) > 15 else "reliever"
        )

        # Create Pitcher
        pitcher = Pitcher(
            name=record['player_name'],
            attributes=attrs,
            pitch_arsenal=arsenal
        )

        return pitcher

    def _create_hitter_from_record(self, record: Dict) -> Optional[Hitter]:
        """
        Create a Hitter object from database record (v2: includes VISION + defensive attributes).

        Parameters
        ----------
        record : dict
            Database record with hitter stats and attributes

        Returns
        -------
        Hitter or None
        """
        # Create HitterAttributes from stored ratings (v1 + v2)
        # NOTE: Generic teams apply large boosts to BAT_SPEED to produce realistic exit velocities.
        # Generic power hitters: 88k-98k BAT_SPEED → 85-93 mph bat speed → 95-105 mph EV
        # Without boost, DB teams were getting ~85-90 mph EV (not enough for HRs)
        #
        # Variable boost based on power level:
        # - Low power (<50k): +10k (contact hitters still need reasonable EV)
        # - Medium power (50k-70k): +15k (balanced hitters)
        # - High power (>70k): +20k (power hitters need 85k+ for HR capability)
        raw_power = record['power']
        if raw_power >= 70000:
            bat_speed_boost = 20000  # Power hitters need to reach 85k+ for HRs
        elif raw_power >= 50000:
            bat_speed_boost = 15000  # Balanced hitters
        else:
            bat_speed_boost = 10000  # Contact hitters

        boosted_bat_speed = min(raw_power + bat_speed_boost, 100000)

        hitter_attrs = HitterAttributes(
            BAT_SPEED=boosted_bat_speed,  # Power + boost for realistic exit velo
            BARREL_ACCURACY=record['contact'],  # Contact maps to barrel accuracy
            ZONE_DISCERNMENT=record['discipline'],  # Discipline maps to pitch recognition
            # v2 attributes (Phase 2A/2C additions)
            VISION=record.get('vision', 50000),  # Contact frequency, default to average if missing
            # ATTACK_ANGLE_CONTROL is CRITICAL for HR generation (Phase 2C fix)
            # Without this, DB teams default to 50k which is much lower than generic teams (72k-88k for power)
            ATTACK_ANGLE_CONTROL=record.get('attack_angle_control', 60000),  # Launch angle tendency
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
