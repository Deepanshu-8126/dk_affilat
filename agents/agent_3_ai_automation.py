"""
AGENT 3 — AI Automation Guides  (ai-automate.com)
Brain: Qwen3 (local Ollama) | Tone: Automation Expert | Author: Sarah Mitchell
"""
from __future__ import annotations

from core.agent import BaseNicheAgent
from core.config import AppConfig, load_config

NICHE_ID = "agent_3_ai_automation"


class Agent3AiAutomation(BaseNicheAgent):
    def __init__(self, app: AppConfig, run_id: str | None = None):
        super().__init__(app, NICHE_ID, run_id)


def run(run_id: str | None = None):
    return Agent3AiAutomation(load_config(), run_id).run()


if __name__ == "__main__":
    run()
