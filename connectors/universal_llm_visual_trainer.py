"""
Universal LLM Visual Prompt & Aesthetic Trainer for Pinterest Meesho Outfits.
Trained on top Pinterest aesthetic collages, Wishlink outfits, and @derosa_finds collage structures.

Prompt Library Patterns:
1. COLLAGE_CARD_SPLIT: Main model try-on pose + floating product cards (Top card + Jeans card) with prices and pointer lines.
2. PRICE_TAG_PIECE: Total Outfit Price badge ("Total Outfit Price ₹932 | Style + Comfort = You ❤️").
3. DEROSA_MANNEQUIN_WALL: Mannequin in room with aesthetic frames (VOGUE, The Weeknd) + hanging ivy + Meesho badge.
4. PINTEREST_4PIECE_FLATLAY: Top + Jeans + Retro Sneakers + Y2K Shoulder Bag on linen background.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger

from connectors.model_face_identity_trainer import ModelFaceIdentityTrainer

log = get_logger("llm_visual_trainer")


class UniversalLLMVisualTrainer:
    """
    Prompt library manager for training Gemini Vision and Veo AI engines on viral Pinterest Meesho layouts.
    Now includes user's trained model face identity.
    """

    BLUEPRINT_LIBRARY = {
        "PINTEREST_COLLAGE_CARD_SPLIT": {
            "description": "Full-body model try-on with floating product cards, white pointer lines, price badges",
            "veo_prompt_template": (
                "Hyper-realistic 4K 60fps vertical 9:16 Pinterest aesthetic outfit reel. "
                "Model: {model_face}. "
                "Center: Model wearing {top_name} and {bottom_name} in an aesthetic warm daylight bedroom with Kinfolk books on table. "
                "Top-Left Card: Rounded product card of {top_name} showing price '₹{top_price}'. "
                "Bottom-Right Card: Rounded product card of {bottom_name} showing price '₹{bottom_price}'. "
                "Bottom-Left Badge: Rounded white badge 'Total Outfit Price ₹{total_price} | Style + Comfort = You ❤️'. "
                "White pointer lines connecting cards to model outfit. Zero AI logo, photorealistic fabric, 60fps."
            ),
            "insta_post_layout": {
                "top_card_pos": (40, 40),
                "bottom_card_pos": (700, 750),
                "total_badge_pos": (40, 1100),
                "pointer_lines": True
            }
        },

        "PINTEREST_4PIECE_FLATLAY": {
            "description": "4-item aesthetic flatlay combo (Tee + Pants + Retro Sneakers + Y2K Bag) on white linen",
            "veo_prompt_template": (
                "Hyper-realistic 4K 60fps vertical 9:16 flatlay video shot from top POV angle. "
                "Laid out neatly on white linen sheet: {top_name}, {bottom_name}, retro sneakers, and Y2K shoulder bag. "
                "Small purple Meesho logo badge in top-left corner. Clean daylight studio lighting, soft shadows, 60fps."
            ),
            "insta_post_layout": {
                "meesho_badge": True,
                "badge_pos": "top_left",
                "aspect_ratio": "4:5"
            }
        },
        "MANNEQUIN_VOGUE_POSTER_WALL": {
            "description": "White mannequin with VOGUE/The Weeknd posters and hanging ivy vines",
            "veo_prompt_template": (
                "Hyper-realistic 4K 60fps vertical 9:16 outfit showcase. "
                "Clean white mannequin wearing {top_name} and {bottom_name}. "
                "Background: White wall with aesthetic VOGUE poster frames and hanging green ivy leaf vines on top-left. "
                "Small purple Meesho logo badge top-left. Photorealistic studio daylight, zero watermark."
            ),
            "insta_post_layout": {
                "meesho_badge": True,
                "badge_pos": "top_left",
                "aspect_ratio": "4:5"
            }
        }
    }

    @classmethod
    def get_trained_prompt(
        cls,
        blueprint_key: str,
        top_name: str,
        bottom_name: str,
        top_price: int,
        bottom_price: int
    ) -> Dict[str, Any]:
        """Generates trained prompt for Google Veo AI and Instagram Post generators."""
        blueprint = cls.BLUEPRINT_LIBRARY.get(blueprint_key, cls.BLUEPRINT_LIBRARY["PINTEREST_COLLAGE_CARD_SPLIT"])
        total_price = top_price + bottom_price

        model_face = ModelFaceIdentityTrainer.MODEL_PROMPT_TOKENS["facial_features"]
        prompt_str = blueprint["veo_prompt_template"].format(
            model_face=model_face,
            top_name=top_name,
            bottom_name=bottom_name,
            top_price=top_price,
            bottom_price=bottom_price,
            total_price=total_price
        )


        return {
            "blueprint_used": blueprint_key,
            "veo_prompt": prompt_str,
            "total_price": total_price,
            "layout_config": blueprint["insta_post_layout"]
        }


if __name__ == "__main__":
    trainer = UniversalLLMVisualTrainer()
    res = trainer.get_trained_prompt(
        blueprint_key="PINTEREST_COLLAGE_CARD_SPLIT",
        top_name="Ribbed Olive Polo Neck Top",
        bottom_name="Black Wide Leg Denim Jeans",
        top_price=242,
        bottom_price=690
    )
    print("\n[Trained Prompt Output]:")
    print("Blueprint:", res["blueprint_used"])
    print("Total Outfit Price: ₹", res["total_price"])
    print("Generated Veo Prompt:\n", res["veo_prompt"])
