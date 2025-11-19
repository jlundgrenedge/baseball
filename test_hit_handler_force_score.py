
import unittest
from unittest.mock import MagicMock, patch
from batted_ball.hit_handler import HitHandler
from batted_ball.play_outcome import PlayResult, PlayOutcome
from batted_ball.baserunning import BaseRunner

class TestHitHandler(unittest.TestCase):
    @patch('batted_ball.hit_handler.decide_runner_advancement')
    def test_handle_hit_baserunning_scores_run(self, mock_decide):
        # Setup
        field_layout = MagicMock()
        baserunning_sim = MagicMock()
        
        # Mock runner on third
        runner_on_3rd = BaseRunner("Runner", sprint_speed=27.0)
        runner_on_3rd.current_base = "third"
        
        # Mock baserunning simulator to return this runner
        baserunning_sim.runners = {"third": runner_on_3rd}
        baserunning_sim.get_runner_at_base.side_effect = lambda base: runner_on_3rd if base == "third" else None
        
        # Mock decide_runner_advancement to return "home"
        mock_decide.return_value = {
            "target_base": "home",
            "risk_level": "low",
            "advancement_bases": 1
        }
        
        handler = HitHandler(baserunning_sim)
        
        # Create result
        result = PlayResult()
        result.outcome = PlayOutcome.SINGLE
        result.runs_scored = 0
        
        # Run
        handler.handle_hit_baserunning(result, current_outs=0)
        
        # Verify
        print(f"Runs Scored: {result.runs_scored}")
        print(f"Events: {[e.description for e in result.events]}")
        
        self.assertEqual(result.runs_scored, 1)
        self.assertTrue(any("scores" in e.description for e in result.events))

if __name__ == "__main__":
    unittest.main()
