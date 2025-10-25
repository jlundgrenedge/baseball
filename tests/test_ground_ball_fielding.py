import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest

from batted_ball.play_simulation import PlaySimulator, PlayResult, PlayOutcome
from batted_ball.fielding import Fielder
from batted_ball.field_layout import FieldPosition
from batted_ball.baserunning import BaseRunner
from batted_ball.ground_ball_physics import GroundBallResult


class TestGroundBallFielding(unittest.TestCase):
    """Behavioral tests for the simplified ground ball fielding helper."""

    def _create_ground_ball_result(self, total_time: float) -> GroundBallResult:
        result = GroundBallResult()
        result.total_time = total_time
        return result

    def _create_infielder(self, fielding_range: int, arm_strength: int,
                          transfer_quickness: int = 65) -> Fielder:
        return Fielder(
            name="Infielder",
            position="infield",
            sprint_speed=65,
            acceleration=65,
            reaction_time=65,
            arm_strength=arm_strength,
            throwing_accuracy=65,
            transfer_quickness=transfer_quickness,
            fielding_range=fielding_range,
            current_position=FieldPosition(68.0, 18.0, 0.0),
        )

    def _create_runner(self, sprint_speed: int) -> BaseRunner:
        return BaseRunner(
            name="Runner",
            sprint_speed=sprint_speed,
            acceleration=sprint_speed,
            base_running_iq=60,
            current_base="home",
        )

    def test_range_and_throw_strength_affect_outcome(self):
        ball_position = FieldPosition(72.0, 20.0, 0.0)
        ball_time = 1.2
        ground_ball_result = self._create_ground_ball_result(total_time=0.55)

        # Elite defender should retire an average runner.
        elite_sim = PlaySimulator()
        elite_fielder = self._create_infielder(fielding_range=85, arm_strength=80)
        elite_sim.fielding_simulator.add_fielder("shortstop", elite_fielder)
        elite_runner = self._create_runner(sprint_speed=55)
        elite_sim.baserunning_simulator.add_runner("home", elite_runner)
        elite_result = PlayResult()

        elite_sim._simulate_ground_ball_fielding(
            elite_fielder,
            ball_position,
            ball_time,
            elite_result,
            ground_ball_result,
        )

        self.assertEqual(elite_result.outcome, PlayOutcome.GROUND_OUT)

        # Below-average defender should allow a faster runner to reach.
        limited_sim = PlaySimulator()
        limited_fielder = self._create_infielder(
            fielding_range=5,
            arm_strength=10,
            transfer_quickness=5,
        )
        limited_sim.fielding_simulator.add_fielder("shortstop", limited_fielder)
        limited_runner = self._create_runner(sprint_speed=95)
        limited_sim.baserunning_simulator.add_runner("home", limited_runner)
        limited_result = PlayResult()

        limited_sim._simulate_ground_ball_fielding(
            limited_fielder,
            ball_position,
            ball_time,
            limited_result,
            ground_ball_result,
        )

        self.assertEqual(limited_result.outcome, PlayOutcome.SINGLE)


if __name__ == "__main__":
    unittest.main()
