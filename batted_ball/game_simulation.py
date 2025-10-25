"""
Game Simulation Module

This module provides a complete baseball game simulation system that integrates
all the physics-based mechanics (pitching, hitting, fielding, baserunning) into
a full 9-inning game with detailed tracking and output.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum
import random

from .player import Pitcher, Hitter
from .fielding import Fielder
from .baserunning import BaseRunner, create_average_runner, create_speed_runner, create_slow_runner
from .play_simulation import PlaySimulator, PlayResult, PlayOutcome, create_standard_defense
from .at_bat import AtBatSimulator


class BaseState(Enum):
    """Represents which bases have runners"""
    EMPTY = "empty"
    FIRST = "1st"
    SECOND = "2nd"
    THIRD = "3rd"
    FIRST_SECOND = "1st_2nd"
    FIRST_THIRD = "1st_3rd"
    SECOND_THIRD = "2nd_3rd"
    LOADED = "loaded"


@dataclass
class GameState:
    """Tracks the complete state of a baseball game"""
    inning: int = 1
    is_top: bool = True  # True = top of inning (away team batting)
    outs: int = 0
    away_score: int = 0
    home_score: int = 0

    # Runners on base (None if empty, Hitter object if occupied)
    runner_on_first: Optional[Hitter] = None
    runner_on_second: Optional[Hitter] = None
    runner_on_third: Optional[Hitter] = None

    # Game statistics
    total_pitches: int = 0
    total_hits: int = 0
    total_home_runs: int = 0

    def get_batting_team(self) -> str:
        """Returns which team is currently batting"""
        return "Away" if self.is_top else "Home"

    def get_pitching_team(self) -> str:
        """Returns which team is currently pitching"""
        return "Home" if self.is_top else "Away"

    def get_base_state(self) -> BaseState:
        """Returns the current base/runner situation"""
        first = self.runner_on_first is not None
        second = self.runner_on_second is not None
        third = self.runner_on_third is not None

        if not any([first, second, third]):
            return BaseState.EMPTY
        elif first and second and third:
            return BaseState.LOADED
        elif first and second:
            return BaseState.FIRST_SECOND
        elif first and third:
            return BaseState.FIRST_THIRD
        elif second and third:
            return BaseState.SECOND_THIRD
        elif first:
            return BaseState.FIRST
        elif second:
            return BaseState.SECOND
        elif third:
            return BaseState.THIRD

    def clear_bases(self):
        """Clear all runners from bases"""
        self.runner_on_first = None
        self.runner_on_second = None
        self.runner_on_third = None

    def add_out(self):
        """Add an out"""
        self.outs += 1

    def end_half_inning(self):
        """End the current half inning"""
        self.outs = 0
        self.clear_bases()

        if self.is_top:
            # Switch to bottom of inning
            self.is_top = False
        else:
            # Move to next inning
            self.is_top = True
            self.inning += 1

    def score_run(self, for_away_team: bool):
        """Add a run to the appropriate team"""
        if for_away_team:
            self.away_score += 1
        else:
            self.home_score += 1

    def __str__(self) -> str:
        """String representation of game state"""
        half = "Top" if self.is_top else "Bot"
        base_state = self.get_base_state().value
        return (f"{half} {self.inning} | {self.away_score}-{self.home_score} | "
                f"{self.outs} out | Runners: {base_state}")


@dataclass
class Team:
    """Represents a baseball team with players"""
    name: str
    pitchers: List[Pitcher]
    hitters: List[Hitter]  # Batting lineup (9 players)
    fielders: Dict[str, Fielder]  # Defensive positions dict keyed by position name

    current_pitcher_index: int = 0
    current_batter_index: int = 0

    def get_current_pitcher(self) -> Pitcher:
        """Get the current pitcher"""
        return self.pitchers[self.current_pitcher_index]

    def get_next_batter(self) -> Hitter:
        """Get the next batter in the lineup and advance"""
        batter = self.hitters[self.current_batter_index]
        self.current_batter_index = (self.current_batter_index + 1) % len(self.hitters)
        return batter

    def switch_pitcher(self, index: int):
        """Switch to a different pitcher"""
        if 0 <= index < len(self.pitchers):
            self.current_pitcher_index = index


@dataclass
class PlayByPlayEvent:
    """A single play-by-play event in the game"""
    inning: int
    is_top: bool
    batter_name: str
    pitcher_name: str
    outcome: str
    description: str
    physics_data: Dict
    game_state_after: str


class GameSimulator:
    """Simulates a complete baseball game"""

    def __init__(self, away_team: Team, home_team: Team, verbose: bool = True):
        self.away_team = away_team
        self.home_team = home_team
        self.verbose = verbose
        self.game_state = GameState()
        self.play_by_play: List[PlayByPlayEvent] = []

        # Simulator (we'll create at-bat simulators per at-bat)
        self.play_simulator = PlaySimulator()

    def simulate_game(self, num_innings: int = 9) -> GameState:
        """Simulate a complete baseball game"""
        if self.verbose:
            print(f"\n{'='*80}")
            print(f"GAME START: {self.away_team.name} @ {self.home_team.name}")
            print(f"{'='*80}\n")

        while self.game_state.inning <= num_innings:
            self.simulate_half_inning()

            # Check for mercy rule or if we're past 9 innings with a tie
            if self.game_state.inning > num_innings:
                if self.game_state.away_score != self.game_state.home_score:
                    break  # Game over
                # Continue extra innings if tied

        if self.verbose:
            self.print_final_summary()

        return self.game_state

    def simulate_half_inning(self):
        """Simulate a half inning (until 3 outs)"""
        batting_team = self.away_team if self.game_state.is_top else self.home_team
        pitching_team = self.home_team if self.game_state.is_top else self.away_team

        if self.verbose:
            print(f"\n{'='*60}")
            print(f"{self.game_state}")
            print(f"{'='*60}")

        # Safety limit to prevent infinite loops
        at_bats = 0
        max_at_bats = 50

        while self.game_state.outs < 3 and at_bats < max_at_bats:
            self.simulate_at_bat(batting_team, pitching_team)
            at_bats += 1
            
            # Check if inning should end after processing the at-bat
            if self.game_state.outs >= 3:
                break

        if at_bats >= max_at_bats:
            print(f"  WARNING: Hit max at-bats limit ({max_at_bats}), ending inning")

        # End of half inning
        self.game_state.end_half_inning()

    def simulate_at_bat(self, batting_team: Team, pitching_team: Team):
        """Simulate a single at-bat"""
        batter = batting_team.get_next_batter()
        pitcher = pitching_team.get_current_pitcher()

        if self.verbose:
            print(f"\n{batter.name} batting against {pitcher.name}")
            print(f"  Situation: {self.game_state.get_base_state().value}, {self.game_state.outs} out(s)")

        # Create at-bat simulator for this matchup
        at_bat_sim = AtBatSimulator(pitcher, batter)

        # Simulate the at-bat to get batted ball
        at_bat_result = at_bat_sim.simulate_at_bat()
        num_pitches = len(at_bat_result.pitches)
        self.game_state.total_pitches += num_pitches

        if at_bat_result.outcome in ["strikeout", "walk"]:
            # Handle strikeout or walk
            self.handle_strikeout_or_walk(at_bat_result.outcome, batter)

            # Log the event
            balls, strikes = at_bat_result.final_count
            self.log_play_by_play(
                batter_name=batter.name,
                pitcher_name=pitcher.name,
                outcome=at_bat_result.outcome,
                description=f"{at_bat_result.outcome.upper()} on {num_pitches} pitches",
                physics_data={
                    "pitches_thrown": num_pitches,
                    "final_count": f"{balls}-{strikes}"
                }
            )
        else:
            # Ball was put in play - simulate the complete play

            # Setup defense (fielders is already a dict)
            self.play_simulator.setup_defense(pitching_team.fielders)

            # Setup existing baserunners (not including batter)
            runners_dict = {}
            if self.game_state.runner_on_first:
                runners_dict["first"] = self.create_runner_from_hitter(
                    self.game_state.runner_on_first, "first"
                )
            if self.game_state.runner_on_second:
                runners_dict["second"] = self.create_runner_from_hitter(
                    self.game_state.runner_on_second, "second"
                )
            if self.game_state.runner_on_third:
                runners_dict["third"] = self.create_runner_from_hitter(
                    self.game_state.runner_on_third, "third"
                )

            self.play_simulator.setup_baserunners(runners_dict)

            # Create batter as runner
            batter_runner = self.create_runner_from_hitter(batter, "home")

            # Extract the actual trajectory result from the dict
            trajectory = at_bat_result.batted_ball_result['trajectory']

            # Simulate the play
            play_result = self.play_simulator.simulate_complete_play(
                batted_ball_result=trajectory,
                batter_runner=batter_runner
            )

            # Process the play result with enhanced physics data
            self.process_play_result(play_result, batter, pitcher, at_bat_result)

            # Reset play simulator for next play
            self.play_simulator.reset_simulation()

    def handle_strikeout_or_walk(self, outcome: str, batter: Hitter):
        """Handle a strikeout or walk"""
        if outcome == "strikeout":
            self.game_state.add_out()
            if self.verbose:
                print(f"  ⚾ STRIKEOUT! {self.game_state.outs} out(s)")

        elif outcome == "walk":
            # Batter walks to first, runners advance if forced
            if self.verbose:
                print(f"  🚶 WALK!")

            # Check for force plays and advance runners
            if self.game_state.runner_on_first is not None:
                if self.game_state.runner_on_second is not None:
                    if self.game_state.runner_on_third is not None:
                        # Bases loaded - runner scores from third
                        self.game_state.score_run(self.game_state.is_top)
                        if self.verbose:
                            print(f"  🏃 Runner scores from third! (RBI Walk)")

                    # Move third to home handled above
                    self.game_state.runner_on_third = self.game_state.runner_on_second

                # Move second to third
                self.game_state.runner_on_second = self.game_state.runner_on_first

            # Batter goes to first
            self.game_state.runner_on_first = batter

    def get_current_runners(self, batter: Hitter) -> List[BaseRunner]:
        """Get current runners on base for play simulation"""
        runners = []

        # Add existing runners
        if self.game_state.runner_on_first:
            runners.append(self.create_runner_from_hitter(
                self.game_state.runner_on_first, "first"
            ))

        if self.game_state.runner_on_second:
            runners.append(self.create_runner_from_hitter(
                self.game_state.runner_on_second, "second"
            ))

        if self.game_state.runner_on_third:
            runners.append(self.create_runner_from_hitter(
                self.game_state.runner_on_third, "third"
            ))

        # Add batter as runner
        runners.append(self.create_runner_from_hitter(batter, "home"))

        return runners

    def create_runner_from_hitter(self, hitter: Hitter, starting_base: str) -> BaseRunner:
        """Create a BaseRunner from a Hitter with some randomness"""
        # Use hitter attributes to influence runner speed
        # This is a simple mapping - you might want to add speed attributes to Hitter later
        speed_types = [create_slow_runner, create_average_runner, create_speed_runner]
        runner_factory = random.choice(speed_types)

        runner = runner_factory(hitter.name)
        runner.current_base = starting_base
        return runner

    def process_play_result(self, play_result: PlayResult, batter: Hitter, pitcher: Pitcher,
                           at_bat_result=None):
        """Process the result of a play and update game state"""
        outcome = play_result.outcome

        # Count hits
        if outcome in [PlayOutcome.SINGLE, PlayOutcome.DOUBLE, PlayOutcome.TRIPLE, PlayOutcome.HOME_RUN]:
            self.game_state.total_hits += 1
            if outcome == PlayOutcome.HOME_RUN:
                self.game_state.total_home_runs += 1

        # Enhanced physics data collection from at_bat_result
        last_pitch = {}  # Initialize to avoid scope issues
        
        if at_bat_result and at_bat_result.batted_ball_result:
            batted_ball_dict = at_bat_result.batted_ball_result
            physics_data = {
                "exit_velocity_mph": round(batted_ball_dict['exit_velocity'], 1),
                "launch_angle_deg": round(batted_ball_dict['launch_angle'], 1), 
                "distance_ft": round(batted_ball_dict['distance'], 1),
                "hang_time_sec": round(batted_ball_dict['hang_time'], 2),
                "contact_quality": batted_ball_dict.get('contact_quality', 'unknown'),
                "peak_height_ft": round(batted_ball_dict['peak_height'], 1),
            }
            
            # Get the last pitch (the one that was hit)
            last_pitch = at_bat_result.pitches[-1] if at_bat_result.pitches else {}
        else:
            # Fallback to trajectory object (though we always have dict now)
            bb_result = play_result.batted_ball_result
            physics_data = {
                "exit_velocity_mph": 0,
                "launch_angle_deg": 0,
                "distance_ft": round(bb_result.distance, 1),
                "hang_time_sec": round(bb_result.flight_time, 2),
                "peak_height_ft": round(bb_result.peak_height, 1),
                "spin_rpm": 0,
            }

        # Build description
        description = self.build_play_description(play_result, physics_data)

        if self.verbose:
            print(f"  {description}")
            
            # Enhanced physics display
            physics_line = (f"    Physics: EV={physics_data['exit_velocity_mph']} mph, "
                          f"LA={physics_data['launch_angle_deg']}°, "
                          f"Dist={physics_data['distance_ft']} ft")
            
            # Add contact quality if available
            if 'contact_quality' in physics_data:
                physics_line += f", Contact: {physics_data['contact_quality']}"
                
            print(physics_line)
            
            # Add pitch information if available  
            if last_pitch:
                pitch_type = last_pitch.get('pitch_type', 'fastball')
                pitch_velocity = last_pitch.get('velocity_plate', 0)
                pitch_location = last_pitch.get('final_location', (0, 0))
                pitch_line = f"    Pitch: {pitch_type} {pitch_velocity:.1f} mph"
                if pitch_location and len(pitch_location) >= 2:
                    zone_x = pitch_location[0] / 12.0  # Convert inches to feet for display
                    zone_z = pitch_location[1] / 12.0  
                    pitch_line += f" at zone ({zone_x:.1f}', {zone_z:.1f}')"
                print(pitch_line)

        # Update game state based on outcome
        self.update_game_state_from_play(play_result, batter)

        # Log play by play
        self.log_play_by_play(
            batter_name=batter.name,
            pitcher_name=pitcher.name,
            outcome=outcome.value,
            description=description,
            physics_data=physics_data
        )

    def build_play_description(self, play_result: PlayResult, physics_data: Dict) -> str:
        """Build a descriptive string for the play"""
        outcome = play_result.outcome

        if outcome == PlayOutcome.HOME_RUN:
            return f"💥 HOME RUN! {physics_data['distance_ft']} ft shot!"
        elif outcome == PlayOutcome.TRIPLE:
            return f"🔥 TRIPLE! Ball goes to the gap"
        elif outcome == PlayOutcome.DOUBLE:
            return f"⚡ DOUBLE! Extra base hit"
        elif outcome == PlayOutcome.SINGLE:
            return f"✓ SINGLE"
        elif outcome == PlayOutcome.GROUND_OUT:
            fielder_pos = play_result.primary_fielder.position if play_result.primary_fielder else "infield"
            return f"⚾ Ground out to {fielder_pos}"
        elif outcome == PlayOutcome.FLY_OUT:
            fielder_pos = play_result.primary_fielder.position if play_result.primary_fielder else "outfield"
            return f"⚾ Fly out to {fielder_pos}"
        elif outcome == PlayOutcome.LINE_OUT:
            return f"⚾ Line out"
        elif outcome == PlayOutcome.DOUBLE_PLAY:
            return f"⚾⚾ DOUBLE PLAY!"
        else:
            return f"{outcome.value}"

    def update_game_state_from_play(self, play_result: PlayResult, batter: Hitter):
        """Update game state based on play result"""
        outcome = play_result.outcome

        # Use the outs_made and runs_scored from play result
        for _ in range(play_result.outs_made):
            self.game_state.add_out()

        # Score runs
        for _ in range(play_result.runs_scored):
            self.game_state.score_run(self.game_state.is_top)
            if self.verbose:
                print(f"    🏃 Run scores!")

        # Clear bases first
        self.game_state.clear_bases()

        # DEBUG: Print what's in final_runner_positions
        if self.verbose and len(play_result.final_runner_positions) > 0:
            print(f"    DEBUG: Final runner positions: {list(play_result.final_runner_positions.keys())}")

        # Update base runners from final positions
        for base, runner in play_result.final_runner_positions.items():
            if base == "first":
                self.game_state.runner_on_first = batter  # Simplified - should track actual hitter
            elif base == "second":
                self.game_state.runner_on_second = batter
            elif base == "third":
                self.game_state.runner_on_third = batter

        # If it was a hit and no runners in final positions, at least put batter on appropriate base
        if outcome in [PlayOutcome.SINGLE, PlayOutcome.DOUBLE, PlayOutcome.TRIPLE] and len(play_result.final_runner_positions) == 0:
            if outcome == PlayOutcome.SINGLE:
                self.game_state.runner_on_first = batter
            elif outcome == PlayOutcome.DOUBLE:
                self.game_state.runner_on_second = batter
            elif outcome == PlayOutcome.TRIPLE:
                self.game_state.runner_on_third = batter

    def log_play_by_play(self, batter_name: str, pitcher_name: str,
                         outcome: str, description: str, physics_data: Dict):
        """Log a play-by-play event"""
        event = PlayByPlayEvent(
            inning=self.game_state.inning,
            is_top=self.game_state.is_top,
            batter_name=batter_name,
            pitcher_name=pitcher_name,
            outcome=outcome,
            description=description,
            physics_data=physics_data,
            game_state_after=str(self.game_state)
        )
        self.play_by_play.append(event)

    def print_final_summary(self):
        """Print final game summary"""
        print(f"\n{'='*80}")
        print(f"FINAL SCORE")
        print(f"{'='*80}")
        print(f"{self.away_team.name}: {self.game_state.away_score}")
        print(f"{self.home_team.name}: {self.game_state.home_score}")
        print(f"\nGame Statistics:")
        print(f"  Total Pitches: {self.game_state.total_pitches}")
        print(f"  Total Hits: {self.game_state.total_hits}")
        print(f"  Home Runs: {self.game_state.total_home_runs}")
        print(f"{'='*80}\n")


def create_test_team(name: str, team_quality: str = "average") -> Team:
    """
    Create a test team with randomized but realistic players

    Args:
        name: Team name
        team_quality: "poor", "average", "good", or "elite"

    Returns:
        Complete Team object
    """
    # Quality determines attribute ranges
    quality_ranges = {
        "poor": (30, 50),
        "average": (45, 65),
        "good": (55, 75),
        "elite": (65, 85)
    }

    min_attr, max_attr = quality_ranges.get(team_quality, (45, 65))

    # Create pitchers (starting pitcher + some relievers)
    pitchers = []
    for i in range(3):
        role = "Starter" if i == 0 else "Reliever"
        pitcher = Pitcher(
            name=f"{name} Pitcher {i+1} ({role})",
            velocity=random.randint(min_attr, max_attr),
            spin_rate=random.randint(min_attr, max_attr),
            spin_efficiency=random.randint(min_attr, max_attr),
            command=random.randint(min_attr, max_attr),
            control=random.randint(min_attr, max_attr),
            pitch_tunneling=random.randint(min_attr, max_attr),
            deception=random.randint(min_attr, max_attr),
            stamina=random.randint(min_attr + 10, max_attr + 10) if i == 0 else random.randint(min_attr, max_attr),
            fatigue_resistance=random.randint(min_attr, max_attr)
        )
        pitchers.append(pitcher)

    # Create hitters (9-player lineup)
    hitters = []
    position_names = ["C", "1B", "2B", "3B", "SS", "LF", "CF", "RF", "DH"]
    for i, pos in enumerate(position_names):
        hitter = Hitter(
            name=f"{name} {pos}",
            bat_speed=random.randint(min_attr, max_attr),
            barrel_accuracy=random.randint(min_attr, max_attr),
            swing_path_angle=float(random.randint(10, 20)),
            swing_timing_precision=random.randint(min_attr, max_attr),
            bat_control=random.randint(min_attr, max_attr),
            exit_velocity_ceiling=random.randint(min_attr, max_attr),
            launch_angle_tendency=float(random.randint(10, 25)),
            pitch_recognition_speed=random.randint(min_attr, max_attr),
            zone_discipline=random.randint(min_attr, max_attr),
            swing_decision_aggressiveness=random.randint(min_attr, max_attr)
        )
        hitters.append(hitter)

    # Create fielders using standard defense
    fielders = create_standard_defense()

    return Team(
        name=name,
        pitchers=pitchers,
        hitters=hitters,
        fielders=fielders
    )
