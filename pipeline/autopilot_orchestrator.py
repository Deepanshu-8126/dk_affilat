"""
Unified Master Affiliate & Multi-Stream Earning Orchestrator.
Automates 4 High-Income Streams with Zero Manual Work:
1. Meesho & Wishlink High-Commission Viral Reels & Post Pipeline
2. Amazon / Tech Gadget Comparison Reviews & Deal Banners
3. Etsy / Gumroad High-Margin Digital Products & eBooks
4. 24/7 Cloud Auto-Pilot Scheduler
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from connectors.meesho_wishlink_crawler import MeeshoWishlinkCrawler
from connectors.reels_ai_generator import ProductReelsGenerator
from connectors.photoshop_deal_banner import PhotoshopDealBannerEngine
from connectors.digital_products_engine import DigitalProductsEngine
from core.logging_utils import get_logger

log = get_logger("orchestrator")


class MultiStreamEarningOrchestrator:
    """Master controller that autonomously manages all affiliate and digital income pipelines."""

    def __init__(self, affiliate_id: str = "earn_master_01"):
        self.affiliate_id = affiliate_id
        self.crawler = MeeshoWishlinkCrawler(affiliate_tag=affiliate_id)
        self.reels_gen = ProductReelsGenerator()
        self.banner_gen = PhotoshopDealBannerEngine()
        self.digital_gen = DigitalProductsEngine()
        self.output_manifest = Path(__file__).resolve().parent.parent / "data" / "autopilot_manifest.json"

    def run_daily_profit_cycle(self, target_stream: str = "all") -> dict[str, Any]:
        """Executes full daily cycle generating Reels, Banners, Product Reviews and eBooks."""
        results: dict[str, Any] = {
            "reels_produced": [],
            "digital_products": [],
            "deal_banners": [],
        }

        # Stream 1: Meesho & Wishlink Viral Reels
        if target_stream in ("all", "meesho_reels"):
            print("\n🛍️ [Stream 1] Crawling Meesho & Wishlink for 12%-18% High-Commission Deals...")
            deals = self.crawler.fetch_top_trending_deals(limit=2)
            for d in deals:
                print(f"  🎬 Rendering 9:16 Viral Reel for: '{d.title}' (Profit: ₹{d.est_profit_per_sale:.2f}/sale)...")
                reel_res = self.reels_gen.generate_affiliate_reel(d)
                results["reels_produced"].append(reel_res)

        # Stream 2: Etsy & Gumroad Digital Products
        if target_stream in ("all", "digital_products"):
            print("\n📚 [Stream 2] Generating High-Ticket Etsy / Gumroad Digital Product Bundle...")
            prod_res = self.digital_gen.build_complete_digital_product(
                title="2026 AI Prompt Engineering & Side Hustle Playbook",
                subtitle="Over 1,000+ Copy-Paste Prompts for Passive Income",
                price="$19.99"
            )
            print(f"  ✅ Product Package Created: {prod_res['title']} (Platforms: {', '.join(prod_res['platforms'])})")
            results["digital_products"].append(prod_res)

        # Stream 3: Photoshop High-CTR Comparison & Deal Cards
        if target_stream in ("all", "deal_banners"):
            print("\n🎨 [Stream 3] Rendering Photoshop-Grade Comparison & Flash Sale Banners...")
            b1 = self.banner_gen.generate_vs_battle_banner("iPhone 16 Pro", "Samsung S24 Ultra", "SMARTPHONE SHOWDOWN")
            b2 = self.banner_gen.generate_deal_discount_banner("Mini Pocket Wireless Thermal Printer", "70% OFF", "₹1,999", "₹599")
            results["deal_banners"].extend([str(b1), str(b2)])

        # Save manifest
        self.output_manifest.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"\n🎉 [Autopilot Cycle Complete] All Assets Ready! Manifest -> {self.output_manifest}")
        return results


if __name__ == "__main__":
    orchestrator = MultiStreamEarningOrchestrator()
    orchestrator.run_daily_profit_cycle(target_stream="all")
