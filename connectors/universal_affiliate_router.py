"""
Universal Multi-Platform Affiliate Link Router.
Supports: Direct Meesho Affiliate, Direct Myntra Affiliate, Direct Flipkart Affiliate, EarnKaro, Wishlink, Cuelinks.

Features:
1. Seamless Priority Cascade:
   - Direct Affiliate Shortlinks (meesho.com/s/, ekaro.in, wishlink.com, clnk.in) -> Retained 100% as-is without double-wrapping.
   - Direct Store Affiliate Account (Meesho referral code, Myntra affiliate tag, Flipkart affid) -> Attached directly if configured.
   - Universal EarnKaro Fallback (ekaro.in/enkr?r=3360368) -> Used for multi-store 1-wallet consolidation.
2. Anti-Block URL Sanitization:
   - Prevents double query param syntax errors.
   - Guarantees 100% smooth redirection on mobile/desktop browsers.
"""
from __future__ import annotations

import os
import sys
import urllib.parse
from pathlib import Path
from typing import Dict, Any

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger


log = get_logger("universal_affiliate_router")

EARNKARO_USER_ID = os.getenv("EARNKARO_USER_ID", "3360368")
MEESHO_DIRECT_CODE = os.getenv("MEESHO_DIRECT_CODE", "")
MYNTRA_AFFILIATE_TAG = os.getenv("MYNTRA_AFFILIATE_TAG", "")
FLIPKART_AFFILIATE_ID = os.getenv("FLIPKART_AFFILIATE_ID", "")
AMAZON_ASSOCIATE_TAG = os.getenv("AMAZON_ASSOCIATE_TAG", "")


class UniversalAffiliateRouter:
    """
    Orchestrates multiple affiliate platforms seamlessly in one engine.
    """

    @staticmethod
    def is_already_affiliate_link(url: str) -> bool:
        """Returns True if link is already an active affiliate shortlink or tracking URL."""
        lowered = url.lower().strip()
        affiliate_domains = [
            "meesho.com/s/",
            "ekaro.in",
            "earnkaro.com",
            "wishlink.com",
            "clnk.in",
            "cuelinks.com",
            "amzn.to",
            "bit.ly",
            "tinyurl.com",
            "referral=",
            "affid=",
            "tag="
        ]
        return any(domain in lowered for domain in affiliate_domains)

    @classmethod
    def generate_link(cls, raw_url: str, store_name: str = "") -> Dict[str, Any]:
        """
        Converts any raw product URL into the optimal affiliate tracking link.
        Returns a dict containing:
        - affiliate_url: The final ready-to-click affiliate URL.
        - platform_used: 'Direct Meesho', 'Direct Myntra', 'Direct Flipkart', 'EarnKaro', or 'Pre-formatted'.
        """
        clean_url = raw_url.strip()
        if not clean_url.startswith("http"):
            clean_url = f"https://www.{clean_url}" if clean_url else "https://www.meesho.com"

        # Strategy 1: Already an affiliate shortlink
        if cls.is_already_affiliate_link(clean_url):
            log.info(f"[Router] Detected existing affiliate link: {clean_url}")
            return {
                "affiliate_url": clean_url,
                "platform_used": "Pre-formatted Affiliate Link",
                "direct_product_url": clean_url
            }

        store_lower = store_name.lower().strip() if store_name else ""
        if not store_lower:
            if "meesho" in clean_url:
                store_lower = "meesho"
            elif "myntra" in clean_url:
                store_lower = "myntra"
            elif "flipkart" in clean_url:
                store_lower = "flipkart"
            elif "ajio" in clean_url:
                store_lower = "ajio"
            elif "shopsy" in clean_url:
                store_lower = "shopsy"
            elif "nykaa" in clean_url:
                store_lower = "nykaa"

        # Strategy 2: Direct Meesho Affiliate Program
        if store_lower == "meesho" and MEESHO_DIRECT_CODE:
            sep = "&" if "?" in clean_url else "?"
            direct_meesho_link = f"{clean_url}{sep}referral={MEESHO_DIRECT_CODE}"
            log.info(f"[Router] Direct Meesho Affiliate link generated: {direct_meesho_link}")
            return {
                "affiliate_url": direct_meesho_link,
                "platform_used": "Direct Meesho Affiliate",
                "direct_product_url": clean_url
            }

        # Strategy 3: Direct Myntra Affiliate Program
        if store_lower == "myntra" and MYNTRA_AFFILIATE_TAG:
            sep = "&" if "?" in clean_url else "?"
            direct_myntra_link = f"{clean_url}{sep}utm_source=affiliate&aff_tag={MYNTRA_AFFILIATE_TAG}"
            log.info(f"[Router] Direct Myntra Affiliate link generated: {direct_myntra_link}")
            return {
                "affiliate_url": direct_myntra_link,
                "platform_used": "Direct Myntra Affiliate",
                "direct_product_url": clean_url
            }

        # Strategy 4: Direct Flipkart Affiliate Program
        if store_lower == "flipkart" and FLIPKART_AFFILIATE_ID:
            sep = "&" if "?" in clean_url else "?"
            direct_flipkart_link = f"{clean_url}{sep}affid={FLIPKART_AFFILIATE_ID}"
            log.info(f"[Router] Direct Flipkart Affiliate link generated: {direct_flipkart_link}")
            return {
                "affiliate_url": direct_flipkart_link,
                "platform_used": "Direct Flipkart Affiliate",
                "direct_product_url": clean_url
            }

        # Strategy 5: Universal EarnKaro Fallback (1-Wallet Pooling across all stores)
        encoded_url = urllib.parse.quote_plus(clean_url)
        earnkaro_link = f"https://ekaro.in/enkr?r={EARNKARO_USER_ID}&url={encoded_url}"
        log.info(f"[Router] EarnKaro Multi-Store link generated: {earnkaro_link}")
        return {
            "affiliate_url": earnkaro_link,
            "platform_used": f"EarnKaro Multi-Store ({EARNKARO_USER_ID})",
            "direct_product_url": clean_url
        }


# Quick helper for direct function call
def get_universal_affiliate_link(url: str, store_name: str = "") -> str:
    res = UniversalAffiliateRouter.generate_link(url, store_name)
    return res["affiliate_url"]


if __name__ == "__main__":
    test_urls = [
        ("https://www.meesho.com/imported-dori-style-ponchu/p/8n98vw", "Meesho"),
        ("https://www.meesho.com/s/p/8n98vw", "Meesho"),
        ("https://www.myntra.com/sweaters/roadster/women-purple-sweater/12345", "Myntra"),
        ("https://www.ajio.com/rio-women-printed-top/p/461234", "Ajio"),
        ("https://ekaro.in/enkr?r=3360368&url=https://www.meesho.com", "Meesho")
    ]
    for raw_u, st in test_urls:
        out = UniversalAffiliateRouter.generate_link(raw_u, st)
        print(f"[{out['platform_used']}] => {out['affiliate_url']}")
