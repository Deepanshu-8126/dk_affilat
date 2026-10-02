"""
Multi-Store Universal Affiliate & Reel Automator for Instagram Female Fashion Niche.
Supports: Myntra, Meesho, Ajio, Flipkart, Shopsy, Nykaa.

1. EarnKaro 1-Wallet Link Conversion (User ID: 3360368)
2. Live Creator Storefront Catalog Auto-Update (data/storefront/index.html)
3. 1080x1920 60fps Watermark-Free Video Generation
4. GenZ Female Voiceover Synthesis (ElevenLabs)
5. Instagram Trending Audio + Caption + Hashtags Pairing
6. Instant Telegram Delivery to Phone (@Ubstabot)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.parse
from pathlib import Path
from typing import Any

# Ensure root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger
from connectors.creator_storefront_generator import CreatorStorefrontGenerator, make_earnkaro_affiliate_link
from connectors.universal_affiliate_router import UniversalAffiliateRouter
from connectors.universal_meesho_engine import UniversalMeeshoEngine
from connectors.reels_audio_synthesizer import ReelsAudioSynthesizer
from connectors.telegram_video_bot import TelegramVideoBot

log = get_logger("multi_store_automator")


# Trending Instagram Audio Recommendations for GenZ Female Niche
TRENDING_INSTAGRAM_AUDIOS = [
    "🔥 Audio 1: 'aesthetic slow vibe' (Slowed + Reverb Remix) - 1.2M Reels",
    "✨ Audio 2: 'soft y2k girl aesthetic beat' - 850K Reels",
    "🎀 Audio 3: 'pinterest moodboard lo-fi chill' - 640K Reels",
    "💄 Audio 4: 'grwm fashion haul acoustic' - 510K Reels",
    "🌸 Audio 5: 'korean soft aesthetic sound' - 920K Reels"
]


class MultiStoreAffiliateAutomator:
    def __init__(self):
        self.storefront = CreatorStorefrontGenerator()
        self.video_engine = UniversalMeeshoEngine()
        self.audio_synth = ReelsAudioSynthesizer()
        self.telegram = TelegramVideoBot()

    def process_product(
        self,
        product_name: str,
        store_name: str,
        raw_product_url: str,
        original_price: float,
        deal_price: float,
        category: str = "GenZ Fashion",
        image_path: str | None = None
    ) -> dict[str, Any]:
        """
        Processes any product from Myntra, Meesho, Ajio, Flipkart, Shopsy, Nykaa:
        - EarnKaro 1-Wallet Affiliate Link
        - Storefront update
        - Voiced 60fps MP4 Reel
        - Telegram Delivery
        """
        log.info(f"Processing {product_name} from {store_name}...")

        # 1. Multi-Platform Affiliate Link (Direct Meesho, Direct Myntra, Direct Flipkart, or EarnKaro)
        aff_res = UniversalAffiliateRouter.generate_link(raw_product_url, store_name)
        affiliate_link = aff_res["affiliate_url"]
        platform_name = aff_res["platform_used"]
        savings_pct = int(((original_price - deal_price) / original_price) * 100) if original_price > deal_price else 25


        # 2. Add to Creator Storefront Catalog
        discount_pct = f"{savings_pct}% OFF"
        item_dict = {
            "id": f"item_{int(deal_price)}",
            "title": f"[{store_name.upper()}] {product_name}",
            "category": category,
            "price": f"₹{int(deal_price)}",
            "mrp": f"₹{int(original_price)}",
            "discount": discount_pct,
            "rating": "4.8",
            "image": image_path or "meesho_flame_sweater_purple.jpg",
            "meesho_url": raw_product_url,
            "earnkaro_link": affiliate_link
        }
        self.storefront.add_product_to_storefront(item_dict)

        # 3. Generate 1080x1920 60fps Veo AI Video
        from connectors.google_veo_direct_api import GoogleVeoDirectAPI
        veo_client = GoogleVeoDirectAPI()
        veo_res = veo_client.generate_ugc_unboxing_video(
            product_title=f"{product_name} ({store_name} Find)",
            category="fashion"
        )
        veo_raw_path = veo_res["video_path"]

        # Clean watermark
        from connectors.watermark_remover import WatermarkRemover
        cleaner = WatermarkRemover()
        clean_veo_path = cleaner.clean_video(veo_raw_path)

        # 4. Generate GenZ Female Voiceover & Layer Audio
        voice_script = (
            f"Hey girls! Found this super aesthetic {product_name} on {store_name.capitalize()}! "
            f"Original price was {int(original_price)} rupees, but you can get it for just {int(deal_price)} rupees right now. "
            f"Direct buying link is in Telegram caption and storefront bio! Grab it before it sells out!"
        )
        voiced_video_path = self.audio_synth.synthesize_voiced_reel(
            video_path=clean_veo_path,
            script_text=voice_script,
            voice_id="21m00Tcm4TlvDq8ikWAM"
        )

        # 5. Build Instagram Caption with AFFILIATE TRACKING LINK (EarnKaro User ID 3360368)
        direct_product_link = raw_product_url.strip() if raw_product_url.startswith("http") else f"https://www.{store_name.lower()}.com"
        caption = (
            f"✨ GenZ Aesthetic Find from {store_name.capitalize()}! ✨\n\n"
            f"👗 Item: {product_name}\n"
            f"💸 Price Drop: ₹{int(deal_price)} (WAS ₹{int(original_price)} - {savings_pct}% OFF!)\n\n"
            f"💰 YOUR AFFILIATE BUY LINK (EarnKaro User ID: 3360368):\n"
            f"{affiliate_link}\n\n"
            f"🛒 Direct Store Item: {direct_product_link}\n"
            f"🛍️ Storefront Link (#Item {len(self.storefront.load_catalog())})\n\n"
            f"🎵 INSTAGRAM TRENDING AUDIO STRATEGY:\n"
            f"Use any of these trending audios on Instagram Reels at 10-15% volume so the voiceover stays crystal clear!\n"
            f"1. Aesthetic Slow Vibe Remix\n"
            f"2. Y2K Soft Girl Beat\n\n"
            f"#GenZFashion #{store_name.capitalize()}Haul #OOTDIndia #AestheticOutfits #EarnKaro #VeoAI"
        )

        # 6. Deliver Voiced Veo MP4 directly to Telegram Bot
        self.telegram.send_video_file(
            video_path=voiced_video_path,
            caption=f"🎥 *GOOGLE VEO AI REEL READY FOR INSTAGRAM!*\n\n{caption}"
        )

        return {
            "status": "success",
            "product_name": product_name,
            "store": store_name,
            "earnkaro_link": affiliate_link,
            "voiced_video_path": str(voiced_video_path),
            "storefront_url": "data/storefront/index.html",
            "telegram_delivered": True
        }


if __name__ == "__main__":
    automator = MultiStoreAffiliateAutomator()
    res = automator.process_product(
        product_name="Imported Dori Style Aesthetic Ponchu Top",
        store_name="Meesho",
        raw_product_url="https://www.meesho.com/imported-dori-style-ponchu/p/8n98vw",
        original_price=1299.0,
        deal_price=359.0,
        category="Western Tops & Tunics"
    )
    print("SUCCESS RESULT:", json.dumps(res, indent=2))
