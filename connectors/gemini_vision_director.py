"""
Gemini Vision Multimodal UGC Director.
Powered by UniversalLLMVisualTrainer with deep multi-domain few-shot corpus and anti-AI optical physics.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from core.logging_utils import get_logger
from connectors.universal_llm_visual_trainer import UniversalLLMVisualTrainer

log = get_logger("gemini_vision_director")


class GeminiVisionDirector:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.trainer = UniversalLLMVisualTrainer()

    def analyze_image_for_ugc(self, image_path: str | Path, product_title: str = "") -> dict[str, Any]:
        """Deeply analyzes image using universal few-shot physical ontology."""
        return self.trainer.deep_analyze_product(image_path, product_title=product_title)
