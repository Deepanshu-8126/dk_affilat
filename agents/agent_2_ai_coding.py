"""
AGENT 2 — AI Coding Tutorials  (ai-code-tutorial.com)
Brain: Groq Llama 70B | Tone: Senior Dev | Author: Alex Chen
"""
from __future__ import annotations

from core.agent import BaseNicheAgent
from core.config import AppConfig, load_config

NICHE_ID = "agent_2_ai_coding"


class Agent2AiCoding(BaseNicheAgent):
    def __init__(self, app: AppConfig, run_id: str | None = None):
        super().__init__(app, NICHE_ID, run_id)


def run(run_id: str | None = None):
    return Agent2AiCoding(load_config(), run_id).run()


if __name__ == "__main__":
    run()
