"""Tracker v1: moves towards the ball x; when the ball is over the centre third of the paddle it does nothing."""

import argparse
import asyncio
from typing import Any

from agents.base_agent import BaseAgent

AGENT_ID: str | None = None  # your id (e.g. "a12345"); --id overrides it; None = random
CENTER_RATIO = 0.3333  # share of the paddle width counted as aligned (the centre region of the 3-region paddle)


class TrackerV1Agent(BaseAgent):
    """Moves the paddle west or east, towards the ball x; no message while the ball is inside the centre third."""

    def __init__(
        self, server_uri: str, name: str, agent_id: str | None = None, center_ratio: float = CENTER_RATIO
    ) -> None:
        super().__init__(server_uri, name, agent_id)
        self.center_ratio = center_ratio

    async def deliberate(self) -> dict[str, Any] | None:
        s = self.current_state
        if not s or s.get("game_over"):
            return None
        centre = s["paddle_x"] + s["paddle_width"] / 2.0
        half = self.center_ratio * s["paddle_width"] / 2.0
        dx = s["ball_x"] - centre
        if dx < -half:
            return {"action": "move", "direction": "WEST"}
        if dx > half:
            return {"action": "move", "direction": "EAST"}
        return None


def main() -> None:
    """Run the tracker v1 agent against a game server."""
    parser = argparse.ArgumentParser(description="Arkanoid tracker agent v1 (ball over the centre third: no move)")
    parser.add_argument("--server", default="ws://localhost:8765/ws", help="WebSocket URI")
    parser.add_argument("--name", default="Tracker v1 Agent", help="Agent name shown in the high score table")
    parser.add_argument("--id", default=None, help="Agent id, used to rank it (default: AGENT_ID, else random)")
    parser.add_argument("--center-ratio", type=float, default=CENTER_RATIO, help="paddle share counted as aligned")
    args = parser.parse_args()
    agent = TrackerV1Agent(args.server, args.name, args.id or AGENT_ID, args.center_ratio)
    asyncio.run(agent.run())


if __name__ == "__main__":
    main()
