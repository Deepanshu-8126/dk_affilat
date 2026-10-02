"""
Master Veo Haul & UGC Video Director (Google Veo + FireCrawler + Gemini Pro).
Supports:
1. Single Product POV Unboxing Reel (Real hands opening courier pack + try-on inset)
2. Multi-Item Aesthetic Haul (Multiple outfits laid on bed / desk, hands picking & reviewing each)
3. Self-Healing Violation Bypass (Auto-rephrases prompts if safety filter flags terms)
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any

from connectors.firecrawl_agent import FireCrawlNode
from connectors.google_veo_api_client import GoogleVeoApiClient
from core.logging_utils import get_logger

log = get_logger("veo_director")

HAUL_SCENARIOS = [
    {
        "type": "single_unboxing",
        "title": "Gothic Chic Spiderweb Mesh Top",
        "platform": "Meesho",
        "price": "₹349",
        "mrp": "₹1,299",
        "headline": "Gothic Chic Unboxing ✨",
        "fabric": "Sheer black stretchable spiderweb mesh",
        "packaging": "Silver metallic shipping parcel",
        "scene": "POV hands with clean manicured nails opening parcel, unfolding mesh top against warm daylight, with try-on model inset in bottom right."
    },
    {
        "type": "multi_haul",
        "title": "Aesthetic Y2K College Outfit Haul (3-Piece Set)",
        "platform": "Meesho / Wishlink",
        "price": "₹999 (Bundle)",
        "mrp": "₹3,499",
        "headline": "Y2K College Haul Under ₹999 🌸",
        "fabric": "Pastel knit cardigan, pleated tennis skirt, and sheer mesh layer",
        "packaging": "Multi-package haul laid out on white aesthetic duvet",
        "scene": "Top-down POV video of 3 cute matching outfits spread across bed in sunlight, hands picking up each piece, showcasing soft knit texture, and trying each one."
    },
    {
        "type": "single_unboxing",
        "title": "Pastel Pink Anarkali Festive Kurti Set",
        "platform": "Meesho",
        "price": "₹699",
        "mrp": "₹2,499",
        "headline": "Meesho Festive Kurti Haul 🌸",
        "fabric": "Pure cotton with gold lace border and matching dupatta",
        "packaging": "Sealed transparent brand polybag",
        "scene": "POV hands gently sliding out folded floral kurti, unfolding flare to show rich printed dupatta in bright aesthetic room."
    }
]


class VeoHaulDirector:
    """Orchestrates end-to-end full-motion unboxing and haul video generation."""

    def __init__(self):
        self.firecrawl = FireCrawlNode()
        self.veo_client = GoogleVeoApiClient()
        self.output_dir = Path(__file__).resolve().parent.parent / "data" / "veo_master_productions"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def produce_veo_master_video(self, scenario_idx: int | None = None) -> dict[str, Any]:
        """Runs full autonomous loop: Trend Select -> Prompt Craft -> Veo Render -> Final MP4."""
        if scenario_idx is not None and 0 <= scenario_idx < len(HAUL_SCENARIOS):
            item = HAUL_SCENARIOS[scenario_idx]
        else:
            item = random.choice(HAUL_SCENARIOS)

        log.info("🎬 [VeoDirector] Producing Full-Motion Veo Video for: '%s' (Mode: %s)", item['title'], item['type'])

        # 1. Craft bulletproof Veo prompt
        prompt, neg_prompt = self.veo_client.craft_bulletproof_veo_prompt(
            item_name=item['title'],
            mode=item['type'],
            details=item
        )

        # 2. Submit to Google Veo & Render Full 60fps MP4
        job = self.veo_client.submit_veo_generation_job(prompt, neg_prompt)

        # 3. Formulate Viral Instagram / Pinterest Caption
        caption = (
            f"✨ {item['headline']}\n\n"
            f"📦 Items: {item['title']}\n"
            f"💰 Deal Price: {item['price']} (MRP {item['mrp']} - Huge Discount!)\n"
            f"🧵 Quality & Texture: {item['fabric']}\n\n"
            f"👉 How to order:\n"
            f"1️⃣ Comment 'LINK' below & I'll send you the direct Meesho/Wishlink links!\n"
            f"2️⃣ Direct link also in my Bio.\n\n"
            f"#meeshohaul #unboxingvideo #outfithaul #pinterestoutfits #meeshofinds #under500 #aestheticunboxing"
        )

        return {
            "status": "success",
            "title": item['title'],
            "mode": item['type'],
            "headline": item['headline'],
            "video_path": job.local_mp4_path,
            "veo_prompt": prompt,
            "caption": caption
        }


if __name__ == "__main__":
    director = VeoHaulDirector()
    res = director.produce_veo_master_video()
    print("\n🎉 [Google Veo Master Video Ready!]")
    print(f"  • Title: {res['title']} (Mode: {res['mode']})")
    print(f"  • Video: {res['video_path']}")
    print(f"\n🎥 [Veo Prompt]:\n{res['veo_prompt']}")
    print(f"\n📱 [Caption]:\n{res['caption']}")
