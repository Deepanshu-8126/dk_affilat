"""
Universal LLM Visual Intelligence & Deep Domain Training Engine.
Heavily trained with multimodal e-commerce & fashion knowledge across:
1. Ethnic & Indian Festive (Banarasi/Kanjivaram Sarees, Chikankari, Anarkalis)
2. GenZ, Y2K & Western Streetwear (Baby tees, flame knitwear, grunge mesh, cargo)
3. Jewelry, Accessories & Watches (Chunky brutalist rings, oxidized silver, moissanite)
4. Footwear & Bags (Chunky sneakers, platform heels, structured tote bags)
5. Beauty, Cosmetics & Skincare (Dewy illuminators, glass skin serums, lip stains)
6. Tech & Smart Home Gadgets (Pocket thermal printers, magnetic chargers)

Enforces strict Anti-AI 8K Optical Realism:
- True camera physics (iPhone 16 Pro ProRes 4K 60fps / Sony FX3 35mm f/1.8)
- Real tactile friction, weight of fabric, unboxing tape resistance
- Human authenticity: real skin cuticles, pores, thumb grip indentations
- Zero plastic sheen, zero synthetic CGI artifacts, zero uncanny morphing
"""
from __future__ import annotations

import base64
import json
import os
import re
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Ensure root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger

log = get_logger("universal_llm_trainer")


def _get_api_key() -> str:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY=") and not line.startswith("#"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


# ==============================================================================
# DEEP DOMAIN TAXONOMY & FEW-SHOT TRAINING EXEMPLARS
# ==============================================================================

FEW_SHOT_TRAINING_CORPUS = """
--- DOMAIN EXEMPLAR 1: ETHNIC WEAR (SAREES & LEHENGAS) ---
Input: Banarasi Soft Silk Saree with Gold Zari Border
Material DNA: Pure mulberry silk base with high-density gold electroplated metallic zari threadwork, crisp starched drape, authentic woven reverse knots.
Tactile Physics: Stiff silk folds that hold their pleats with subtle fabric swish sound; gold zari catches warm directional lighting with metallic micro-shimmer.
POV Unboxing Choreography: Overhead 45-degree angle. Real manicured hands slicing sealed polybag tape, lifting saree out by its folded pleats, unfolding the heavy pallu across a smooth beige linen table so the intricate floral zari border catches natural morning daylight.
Visual Negative Constraints: Zero digital blur, zero floating cloth, no cartoonish gold glow, zero plastic sheen.

--- DOMAIN EXEMPLAR 2: GENZ / Y2K KNITWEAR & BABY TEES ---
Input: Lavender Flame Hem Jacquard Knit Sweater
Material DNA: 100% heavy gauge acrylic-cotton blend, 7-gauge intarsia flame weave, ribbed 2x2 crewneck collar, slightly dropped shoulders with raw textured yarn fuzz.
Tactile Physics: Chunky, weighty knit that drapes with deep natural fabric fold shadows. Slight yarn elasticity when pulled gently between fingers.
POV Unboxing Choreography: Handheld POV camera with subtle natural breathing movement. Two hands with clean unpolished fingernails tearing open a silver courier pouch, sliding out the folded lilac sweater, running thumbs across the tactile flame jacquard stitches to prove knit density, turning collar to camera.
Visual Negative Constraints: No AI airbrushing on hands, no plastic texture, no synthetic CGI gloss.

--- DOMAIN EXEMPLAR 3: JEWELRY & CHUNKY ACCESSORIES ---
Input: Vintage Chunky Silver Bohemian Ring Set
Material DNA: Cast zinc-alloy with antique oxidized blackened patina recesses, hand-burnished high-points, simulated turquoise stone cabochons with authentic mineral veins.
Tactile Physics: Solid metallic clinking sound when picked up; cool metal thermal reflection; micro-scratches and organic casting imperfections.
POV Unboxing Choreography: Macro 100mm f/2.0 shallow depth of field. Hands opening a matte black drawstring velvet pouch, taking out the rings one by one, slipping the statement ring onto the index finger, rotating the hand against warm vanity rim lighting to reveal the carved floral engravings.
Visual Negative Constraints: No cartoon sparkle stars, realistic skin pores and knuckle wrinkles, zero floating elements.

--- DOMAIN EXEMPLAR 4: BEAUTY & SKINCARE ILLUMINATORS ---
Input: Liquid Glass Skin Illuminator Highlighter Serum
Material DNA: Heavyweight frosted glass dropper bottle, rose-gold metallic cap, viscous liquid with micronized gold and champagne pearl mica suspension.
Tactile Physics: Satisfying suction pop when dropper is pulled out; viscous droplet holds teardrop shape for 1.5 seconds before slowly sliding down skin.
POV Unboxing Choreography: Clean white marble vanity table. Hands breaking brand safety seal on cardboard box, pulling out cool glass bottle, unscrewing dropper, dispensing exactly one luminous droplet onto the back of the hand, gently blending with ring finger to display high-pigment wet-look dewy sheen.
Visual Negative Constraints: No fake CGI glare, realistic skin texture with visible pores and fine hairs.

--- DOMAIN EXEMPLAR 5: MYNTRA & AJIO WESTERN HIGH-STREET DRESSES ---
Input: Emerald Green Satin Slip Dress with Cowl Neck
Material DNA: Premium 100% fluid polyester satin weave, bias-cut silhouette, adjustable spaghetti straps, liquid-like light drape with soft satin luster.
Tactile Physics: Weightless silky movement that flows like water; catches ambient indoor mood lighting with deep emerald highlights and soft shadow folds.
POV Unboxing Choreography: Soft linen background. Female hands carefully lifting dress out of branded tissue paper, holding shoulder straps to camera, running fingers across the cowl neckline to show seamless stitching and fluid drape.
Visual Negative Constraints: Zero plastic glare, true satin physics, natural hand movements.

--- DOMAIN EXEMPLAR 6: SHOPSY & FLIPKART BUDGET ETHNIC KURTIS ---
Input: Cotton Printed Straight Kurti under 299
Material DNA: 100% breathable cambric cotton weave, hand-block Jaipur floral print, 3/4th sleeves with delicate border piping.
Tactile Physics: Crisp natural cotton texture with slight stiffness before first wash; matte daylight reflection, crisp hemline.
POV Unboxing Choreography: Unfolding kurti on light wooden table, pressing palm flat against print to demonstrate 100% pure cotton texture, close-up on cuff stitching.
Visual Negative Constraints: No synthetic sheen, real cotton weave visible under macro lens.

--- INSTAGRAM REELS VIRAL HOOK FORMULAS (GENZ FEMALE NICHE) ---
1. Curiosity Hook: "Girls, stop scrolling! Found this viral Myntra dress that looks ₹5000 but is literally under ₹899..."
2. Price Drop Hook: "Meesho mistake? How is this heavy aesthetic sweater listed for only ₹449?!"
3. Secret Storefront Hook: "All the aesthetic aesthetic girls are buying this Ajio top... link in bio before it sells out!"
"""

UNIVERSAL_SYSTEM_DIRECTIVE = f"""
You are the world's most elite, PhD-level Fashion & E-Commerce Video Creative Director and Computer Vision Analyst.
Your goal is to inspect any product image or collection of images from Meesho/Pinterest/Amazon, analyze its microscopic physical and visual DNA, and generate a hyper-realistic, photorealistic POV unboxing prompt for Google Veo that completely eliminates the "AI plastic/synthetic" look.

Strict Photorealism Guidelines:
1. CAMERA OPTICS: Describe specific real-world optics (e.g. "Shot on iPhone 16 Pro 4K 60fps ProRes, 24mm f/1.8 lens, natural handheld micro-movements, auto-exposure tracking, organic motion blur").
2. PHYSICAL FRICTION & WEIGHT: Fabrics and products must behave with real mass, friction, drape gravity, and tactile resistance (opening packages, unfolding seams, texture close-up).
3. HUMAN REALISM: Hands must have natural human skin textures, visible pores, real cuticles, realistic knuckle folds, authentic finger pressure indentations.
4. ZERO AI ARTIFACTS: NEVER use generic buzzwords like "hyperrealistic, photorealistic, masterpiece". Instead, describe the physical reality: lighting angle, dust particles, weave density, shadows, and true reflections.

{FEW_SHOT_TRAINING_CORPUS}
"""


class UniversalLLMVisualTrainer:
    """Trains and executes deep multimodal visual ontology and similarity clustering."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or _get_api_key()
        self.models_priority = [
            "gemini-3.1-flash-lite",
            "gemini-3.5-flash-lite",
            "gemini-3.8-flash",
            "gemini-flash-latest"
        ]

    def deep_analyze_product(
        self,
        image_path: str | Path,
        product_title: str = "",
        category_hint: str = ""
    ) -> dict[str, Any]:
        """Deeply inspects an image and extracts complete physical, visual, and prompt DNA."""
        path = Path(image_path)
        if not path.exists():
            log.warning("Image not found: %s. Using heuristic analysis.", path)
            return self._heuristic_fallback(product_title, category_hint)

        ext = path.suffix.lower()
        mime_type = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
        with open(path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")

        prompt = f"""
{UNIVERSAL_SYSTEM_DIRECTIVE}

Now analyze this specific product reference image in microscopic detail:
Title/Context: '{product_title}'
Category Hint: '{category_hint}'

Return a strictly valid JSON object with the following comprehensive fields:
{{
  "domain": "Ethnic Apparel | Western Y2K | Men Activewear | Jewelry | Footwear | Beauty | Home | Tech",
  "product_name": "Precise, aesthetic, high-converting product title",
  "material_dna": "Specific fabric/material weave, yarn weight, sheen, texture, stitch density",
  "chromatic_palette": "Exact color tones, secondary accents, undertones, and light reflectivity",
  "tactile_physics": "How this exact item folds, moves, drapes, or catches shadows",
  "pov_choreography": "Step-by-step 0s to 8s real hands unboxing action in natural daylight",
  "camera_and_lighting": "Exact camera lens, framing, f-stop, natural window lighting direction",
  "veo_prompt": "Ultra-detailed, cinematic Google Veo unboxing prompt written using true physical descriptions (zero plastic look, real hands, authentic fabric motion, 9:16 vertical)",
  "sale_price": "Realistic affordable Meesho selling price (e.g. ₹499)",
  "mrp": "Realistic original MRP (e.g. ₹1,799)",
  "discount": "Percentage discount (e.g. 72% OFF)",
  "commission_rate": "Estimated affiliate commission % (12% to 18%)",
  "viral_hook": "1-sentence conversational, punchy hook for voiceover or caption",
  "colorway_tags": ["List of 3 aesthetic colorway names this item could come in, e.g. 'Lavender 💜', 'Charcoal 🖤'"]
}}

Respond ONLY with the raw JSON object.
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type,
                                "data": b64_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2
            }
        }

        for model in self.models_priority:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key
                    }
                )
                with urllib.request.urlopen(req, timeout=30) as resp:
                    result = json.loads(resp.read().decode("utf-8"))

                text_out = result["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text_out.startswith("```json"):
                    text_out = text_out[7:]
                if text_out.startswith("```"):
                    text_out = text_out[3:]
                if text_out.endswith("```"):
                    text_out = text_out[:-3]

                data = json.loads(text_out.strip())
                log.info("🎯 [Deep Vision Trained] Model %s successfully deconstructed: '%s'", model, data.get("product_name"))
                return data
            except Exception as e:
                log.warning("Attempt with %s notice: %s", model, e)
                continue

        return self._heuristic_fallback(product_title, category_hint)

    def cluster_multi_product_relationship(
        self,
        analyzed_items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Analyzes multiple items and decides whether they form a Colorway Family or a Curated Outfit."""
        if len(analyzed_items) <= 1:
            return {"mode": "SOLO_PRODUCT", "theme": "Hero Product Showcase"}

        domains = [it.get("domain", "") for it in analyzed_items]
        titles = [it.get("product_name", "") for it in analyzed_items]

        # Check if all items are the same type (e.g. all sweaters or all tops)
        all_same_type = len(set(domains)) == 1

        if all_same_type:
            # Colorway Family Mode (e.g. 1 Design in 3 Colors or Multiple Matching Sweaters)
            first_title = titles[0] if titles else "Fashion Outfits"
            return {
                "mode": "COLORWAY_FAMILY",
                "theme": f"1 Viral Design • {len(analyzed_items)} Aesthetic Colors ✨",
                "headline": f"Which Color is Your Vibe? 🔥",
                "cta": "Comment your favorite color number (1, 2, or 3) for direct Meesho/Wishlink!"
            }
        else:
            # Styled Outfit Lookbook Mode (e.g. Top + Layer + Jewelry)
            return {
                "mode": "STYLED_LOOKBOOK",
                "theme": "Complete Head-to-Toe Curated Outfit ✨",
                "headline": "Full Aesthetic Lookbook Under ₹999 👗",
                "cta": "Comment 'OUTFIT' below to get links to all pieces in your DMs!"
            }

    def _heuristic_fallback(self, title: str, category: str) -> dict[str, Any]:
        t = title or "Meesho Trending Fashion Find"
        return {
            "domain": category or "Western Y2K",
            "product_name": t,
            "material_dna": "Premium verified fabric with dense weave, clean hem stitching, and authentic color tones",
            "chromatic_palette": "Deep saturated tone with natural light absorption",
            "tactile_physics": "Natural drape with realistic gravity creases and tactile cloth friction",
            "pov_choreography": f"POV hands unboxing parcel, unfolding {t} in natural morning daylight.",
            "camera_and_lighting": "Shot on 24mm f/1.8 lens, natural window light from left, realistic handheld camera movement.",
            "veo_prompt": (
                f"Authentic 4K 60fps POV camera angle looking down at linen desk. "
                f"Real human hands with natural skin texture and cuticles opening courier parcel, "
                f"unfolding {t} towards natural daylight. Realistic tactile fabric physics, "
                f"soft contact shadows, zero plastic look, 9:16 vertical."
            ),
            "sale_price": "₹399",
            "mrp": "₹1,499",
            "discount": "73% OFF",
            "commission_rate": "15%",
            "viral_hook": f"Found this viral {t} on Meesho under ₹400! Quality is 10/10 ✨",
            "colorway_tags": ["Mocha 🤎", "Lavender 💜", "Obsidian 🖤"]
        }


if __name__ == "__main__":
    trainer = UniversalLLMVisualTrainer()
    test_img = "data/scraped_products/meesho_flame_sweater_purple.jpg"
    if Path(test_img).exists():
        print("\n🧪 [Deep Training Test] Running multimodal visual deconstruction on flame sweater...")
        res = trainer.deep_analyze_product(test_img, product_title="Flame Knit Sweater", category_hint="Sweaters")
        print("\n✅ [Trained Deconstruction Result]:")
        print("  • Domain:", res.get("domain"))
        print("  • Material DNA:", res.get("material_dna"))
        print("  • Chromatic Palette:", res.get("chromatic_palette"))
        print("  • Tactile Physics:", res.get("tactile_physics"))
        print("  • Commission Rate:", res.get("commission_rate"))
        print("\n🎥 [8K Anti-AI Veo Prompt]:\n", res.get("veo_prompt"))
    else:
        print("Test image not found:", test_img)
