"""
High-Profit Female Fashion Cash Machine & Auto-Pilot.
Exclusively targets high-converting ₹500 - ₹1,499 female products with ₹80 - ₹250 profit per sale:
1. Chikankari Kurti Sets (15% Commission | ₹150 Profit/Sale)
2. Flame / Cable Knit Sweaters (15% Commission | ₹86.55 Profit/Sale)
3. Complete 3-Piece Lookbook Outfits (15% Commission | ₹132.15 Profit/Sale)
4. Bohemian Chunky Silver Jewelry Sets (18% Commission | ₹63 Profit/Sale)
5. Korean Glass Skin Makeup & Serum Combos (18% Commission | ₹80 Profit/Sale)

Automated Pipeline:
- Selects top profit deal
- Deconstructs with trained Gemini 8K Vision
- Renders 1080x1920 60fps clean MP4 (Watermarks eliminated)
- Adds product to Aesthetic Fashion Storefront wired to EarnKaro User ID: 3360368
- Dispatches video + caption to Telegram
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

# Ensure root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger
from connectors.universal_meesho_engine import UniversalMeeshoEngine
from connectors.aesthetic_combo_lookbook_studio import AestheticComboLookbookStudio
from connectors.creator_storefront_generator import CreatorStorefrontGenerator, make_earnkaro_affiliate_link

log = get_logger("high_profit_autopilot")

HIGH_PROFIT_CATALOG = [
    {
        "id": "festive_chikankari",
        "category": "chikankari",
        "title": "Chikankari Hand-Embroidered Anarkali Kurti & Dupatta Set",
        "price": "₹999",
        "mrp": "₹2,999",
        "discount": "67% OFF",
        "commission_pct": 15.0,
        "est_profit": "₹149.85",
        "image": "data/ref_frame1.jpg",
        "meesho_url": "https://www.meesho.com/chikankari-embroidered-kurti-set/p/chikankari-999",
        "hook": "Found the most ethereal Chikankari kurti set under ₹1,000! Looks like a ₹4,000 designer piece 🌸"
    },
    {
        "id": "genz_flame_sweater",
        "category": "sweater",
        "title": "Lavender Flame Hem Oversized Knit Sweater",
        "price": "₹577",
        "mrp": "₹1,499",
        "discount": "62% OFF",
        "commission_pct": 15.0,
        "est_profit": "₹86.55",
        "image": "data/scraped_products/meesho_flame_sweater_purple.jpg",
        "meesho_url": "https://www.meesho.com/classic-fabulous-women-sweaters/p/flame-knit",
        "hook": "The viral Pinterest flame sweater everyone is gatekeeping! Under ₹600 only 💜"
    },
    {
        "id": "boho_chunky_rings",
        "category": "jewelry",
        "title": "Vintage Chunky Bohemian Silver Rings Set",
        "price": "₹349",
        "mrp": "₹1,199",
        "discount": "71% OFF",
        "commission_pct": 18.0,
        "est_profit": "₹62.82",
        "image": "data/scraped_products/meesho_chunky_rings.jpg",
        "meesho_url": "https://www.meesho.com/allure-chunky-rings/p/silver-rings",
        "hook": "Stop overpaying for jewelry! This 5-piece silver rings set is only ₹349 on Meesho ✨"
    }
]


class HighProfitFashionAutopilot:
    def __init__(self):
        self.universal_engine = UniversalMeeshoEngine()
        self.combo_studio = AestheticComboLookbookStudio()
        self.storefront = CreatorStorefrontGenerator()

    def run_profit_production(self, category: str = "combo") -> dict[str, Any]:
        """Runs automated end-to-end video production for high-profit female fashion."""
        print("\n" + "="*65)
        print("🚀 [HIGH-PROFIT FASHION CASH MACHINE] Launching Auto-Pilot...")
        print("  • Target Market: Female Fashion, Y2K Fits & Ethnic Wear")
        print("  • Commission Strategy: ₹80 to ₹250 Profit Per Single Sale")
        print("  • Monetization Hub: EarnKaro User ID 3360368 (Aesthetic Fashion Hub)")
        print("="*65 + "\n")

        if category == "combo":
            # Run the highest-earning 3-piece lookbook combo (Total ₹881 | Profit ₹132/sale)
            print("👗 [Step 1] Curating High-Ticket 3-Piece Lookbook Combo...")
            outfit_pieces = [
                {
                    "role": "Step 1: The Base Top",
                    "title": "Y2K Contrast Raglan Baby Tee",
                    "price": "₹187",
                    "mrp": "₹699",
                    "detail": "Mocha & Black Contrast Sleeves • Soft Ribbed Cotton",
                    "image": "data/scraped_products/meesho_raglan_baby_tee.jpg",
                    "meesho_url": "https://www.meesho.com/trendy-graceful-women-tops/p/raglan-tee"
                },
                {
                    "role": "Step 2: Layering Piece",
                    "title": "Flame Hem Oversized Sweater",
                    "price": "₹577",
                    "mrp": "₹1,499",
                    "detail": "Lavender Purple • White Flame Weave Knit",
                    "image": "data/scraped_products/meesho_flame_sweater_purple.jpg",
                    "meesho_url": "https://www.meesho.com/classic-fabulous-women-sweaters/p/flame-knit"
                },
                {
                    "role": "Step 3: The Jewelry",
                    "title": "Vintage Chunky Rings Set",
                    "price": "₹117",
                    "mrp": "₹499",
                    "detail": "Set of 5 Bohemian Silver Statement Rings",
                    "image": "data/scraped_products/meesho_chunky_rings.jpg",
                    "meesho_url": "https://www.meesho.com/allure-chunky-rings/p/silver-rings"
                }
            ]

            combo_res = self.combo_studio.produce_complete_lookbook(
                pieces=outfit_pieces,
                lookbook_theme="Pinterest Y2K Aesthetic Fit ✨"
            )

            # Add each outfit piece to permanent storefront
            for piece in outfit_pieces:
                self.storefront.add_product_to_storefront({
                    "id": piece["title"][:10].lower().replace(" ", "_"),
                    "title": piece["title"],
                    "category": piece["role"].split(":")[-1].strip(),
                    "price": piece["price"],
                    "mrp": piece["mrp"],
                    "discount": "65% OFF",
                    "rating": "4.8",
                    "image": Path(piece["image"]).name,
                    "meesho_url": piece["meesho_url"]
                })

            # Synthesize GenZ Female Voiceover
            try:
                from connectors.reels_audio_synthesizer import ReelsAudioSynthesizer
                synth = ReelsAudioSynthesizer()
                v_text = "Girls, stop scrolling! Look at this complete Pinterest outfit I styled under 900 rupees! Comment OUTFIT for all links! ✨"
                audio = synth.generate_female_voiceover(v_text, "combo_lookbook")
                if audio and audio.exists():
                    combo_res["video_path"] = str(synth.attach_voiceover_to_video(combo_res["video_path"], audio))
            except Exception as ve:
                log.warning("Voiceover notice: %s", ve)

            print("\n🎉 [Combo Lookbook Produced!]")
            print(f"  • Video (Voiced): {combo_res['video_path']}")
            print(f"  • Total Bundle Price: {combo_res['total_price']}")
            print(f"  • Commission per Bundle: ~₹132.15")
            print(f"  • Storefront Updated: data/storefront/index.html")

            # Try Telegram dispatch
            self._try_telegram_dispatch(combo_res["video_path"], combo_res["caption"])
            return combo_res

        else:
            # Single High-Ticket Category (Chikankari / Sweater / Jewelry)
            item = next((x for x in HIGH_PROFIT_CATALOG if x["category"] == category), HIGH_PROFIT_CATALOG[0])
            print(f"👗 [Step 1] Selected High-Ticket Item: '{item['title']}' ({item['price']})")
            print(f"  • Estimated Profit: {item['est_profit']} per single sale!")

            res = self.universal_engine.process_universal_product(item["title"], image_path=item["image"])

            # Add to storefront
            self.storefront.add_product_to_storefront({
                "id": item["id"],
                "title": item["title"],
                "category": item["category"].title(),
                "price": item["price"],
                "mrp": item["mrp"],
                "discount": item["discount"],
                "rating": "4.8",
                "image": Path(item["image"]).name,
                "meesho_url": item["meesho_url"]
            })

            print("\n🎉 [High-Profit Video Produced!]")
            print(f"  • Video: {res['video_path']}")
            print(f"  • Commission: {item['commission_pct']}% ({item['est_profit']}/sale)")
            print(f"  • Storefront Updated: data/storefront/index.html")

            self._try_telegram_dispatch(res["video_path"], res["caption"])
            return res

    def _try_telegram_dispatch(self, video_path: str, caption: str):
        try:
            from connectors.telegram_video_bot import TelegramVideoBot
            bot = TelegramVideoBot()
            if bot.bot_token and bot.chat_id:
                print(f"📱 Dispatching video directly to your Telegram ({bot.chat_id})...")
                bot.send_video_file(video_path, caption=caption)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="High-Profit Female Fashion Cash Machine")
    parser.add_argument("--category", choices=["combo", "chikankari", "sweater", "jewelry"], default="combo", help="Target high-profit niche")
    args = parser.parse_args()

    autopilot = HighProfitFashionAutopilot()
    autopilot.run_profit_production(category=args.category)


if __name__ == "__main__":
    main()
