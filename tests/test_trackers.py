"""Tracker agents v1 and v2, driven with hand-made states."""

import unittest
from typing import Any

from agents.tracker_v1 import TrackerV1Agent
from agents.tracker_v2 import TrackerV2Agent

URI = "ws://localhost:8765/ws"
WEST = {"action": "move", "direction": "WEST"}
EAST = {"action": "move", "direction": "EAST"}


def paddle_state(ball_x: float, **extra: Any) -> dict[str, Any]:
    """Paddle at x 100..180 (centre 140, centre third 126.7..153.3)."""
    return {"paddle_x": 100.0, "paddle_width": 80.0, "ball_x": ball_x, "game_over": False, **extra}


class TestTrackerV1(unittest.IsolatedAsyncioTestCase):
    async def test_none_over_the_centre_third_else_towards_the_ball(self) -> None:
        agent = TrackerV1Agent(URI, "t", "a1")
        self.assertIsNone(await agent.deliberate())  # no state yet
        cases = ((140.0, None), (152.0, None), (128.0, None), (155.0, EAST), (125.0, WEST), (400.0, EAST), (10.0, WEST))
        for ball_x, expected in cases:
            agent.current_state = paddle_state(ball_x)
            self.assertEqual(await agent.deliberate(), expected, ball_x)
        agent.current_state = paddle_state(400.0, game_over=True)
        self.assertIsNone(await agent.deliberate())


class TestTrackerV2(unittest.IsolatedAsyncioTestCase):
    async def test_moves_towards_the_ball_and_rests_inside_the_dead_band(self) -> None:
        agent = TrackerV2Agent(URI, "t", "a1")
        self.assertIsNone(await agent.deliberate())  # no state yet
        agent.current_state = paddle_state(140.0)
        self.assertIsNone(await agent.deliberate())  # centred
        agent.current_state = paddle_state(10.0)
        self.assertEqual(await agent.deliberate(), WEST)
        agent.current_state = paddle_state(400.0)
        self.assertEqual(await agent.deliberate(), EAST)
        agent.current_state = paddle_state(400.0, game_over=True)
        self.assertIsNone(await agent.deliberate())


if __name__ == "__main__":
    unittest.main()
