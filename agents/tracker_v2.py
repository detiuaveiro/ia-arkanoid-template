"""Tracker v2: keeps the paddle centre within a dead band (half a paddle step) of the ball x (no bricks)."""

import argparse
import asyncio
from typing import Any

from agents.base_agent import BaseAgent

AGENT_ID: str | None = None  # your id (e.g. "a12345"); --id overrides it; None = random
DEAD_BAND = 14.0  # px: half a paddle step (28 px), so the paddle settles instead of dithering around the ball


class TrackerV2Agent(BaseAgent):
    """Moves the paddle towards the ball x until the paddle centre is within the dead band."""

    def __init__(self, server_uri: str, name: str, agent_id: str | None = None, dead_band: float = DEAD_BAND) -> None:
        super().__init__(server_uri, name, agent_id)
        self.dead_band = dead_band

    async def deliberate(self) -> dict[str, Any] | None:
        s = self.current_state
        if not s or s.get("game_over"):
            return None
        dx = s["ball_x"] - (s["paddle_x"] + s["paddle_width"] / 2.0)
        if dx < -self.dead_band:
            return {"action": "move", "direction": "WEST"}
        if dx > self.dead_band:
            return {"action": "move", "direction": "EAST"}
        return None


def main() -> None:
    """Run the tracker v2 agent against a game server."""
    parser = argparse.ArgumentParser(description="Arkanoid tracker agent v2 (dead band of half a paddle step)")
    parser.add_argument("--server", default="ws://localhost:8765/ws", help="WebSocket URI")
    parser.add_argument("--name", default="Tracker v2 Agent", help="Agent name shown in the high score table")
    parser.add_argument("--id", default=None, help="Agent id, used to rank it (default: AGENT_ID, else random)")
    parser.add_argument("--dead-band", type=float, default=DEAD_BAND, help="px of ball/paddle-centre offset tolerated")
    args = parser.parse_args()
    asyncio.run(TrackerV2Agent(args.server, args.name, args.id or AGENT_ID, args.dead_band).run())


if __name__ == "__main__":
    main()
