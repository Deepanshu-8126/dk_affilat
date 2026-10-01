"""
AGENT 1 — AI Tools Reviews  (ai-tools-review.com)
Brain: Gemini 2.0 Flash | Tone: Pro Reviewer | Author: James Carter
"""
from __future__ import annotations

from core.agent import BaseNicheAgent
from core.config import AppConfig, load_config

NICHE_ID = "agent_1_ai_tools"


class Agent1AiTools(BaseNicheAgent):
    def __init__(self, app: AppConfig, run_id: str | None = None):
        super().__init__(app, NICHE_ID, run_id)


def run(run_id: str | None = None):
    return Agent1AiTools(load_config(), run_id).run()


if __name__ == "__main__":
    run()
