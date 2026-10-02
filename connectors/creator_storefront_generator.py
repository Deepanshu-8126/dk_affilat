"""
Automated Wishlink-Style Creator Storefront Engine.
Creates a unified, mobile-responsive aesthetic wardrobe storefront (like Wishlink / Linktree)
where ALL products ever scraped or generated are listed in one place:
- Wired directly to EarnKaro User ID: 3360368
- Every 'Buy on Meesho' button routes through your EarnKaro affiliate tracking link
- Categories: Y2K Tops, Sweaters, Ethnic Wear, Jewelry & Combos
- Beautiful Pinterest / Instagram creator aesthetic
"""
from __future__ import annotations

import json
import os
import urllib.parse
from pathlib import Path
from typing import Any

from core.logging_utils import get_logger

log = get_logger("creator_storefront")

EARNKARO_USER_ID = os.getenv("EARNKARO_USER_ID", "3360368")
MEESHO_DIRECT_CODE = os.getenv("MEESHO_DIRECT_CODE", "")  # Direct Meesho Creator/Affiliate Code if available
CREATOR_NAME = os.getenv("CREATOR_NAME", "Aesthetic Fashion Closet")


def make_earnkaro_affiliate_link(product_url: str, user_id: str = EARNKARO_USER_ID) -> str:
    """
    Smart Dual Affiliate Link Generator:
    1. If product_url is already a Direct Meesho Affiliate Share Link (e.g., meesho.com/s/...), retains it 100% directly.
    2. If MEESHO_DIRECT_CODE is configured and it's a Meesho link, attaches direct Meesho affiliate tracking.
    3. Otherwise, converts Meesho, Myntra, Ajio, Flipkart, Shopsy, Nykaa into EarnKaro 1-wallet tracking link.
    """
    clean_url = product_url.strip()
    if not clean_url.startswith("http"):
        clean_url = "https://www.meesho.com"
    
    # Check if already a Direct Meesho Share / Affiliate link (e.g., https://www.meesho.com/s/p/...)
    if "meesho.com/s/" in clean_url or "referral=" in clean_url:
        return clean_url
    
    # Direct Meesho Affiliate Code Override (if user has direct Meesho Creator Account)
    if "meesho.com" in clean_url and MEESHO_DIRECT_CODE:
        separator = "&" if "?" in clean_url else "?"
        return f"{clean_url}{separator}referral={MEESHO_DIRECT_CODE}"
    
    # Default: Universal EarnKaro Affiliate Link (1-Wallet Pooling)
    encoded = urllib.parse.quote_plus(clean_url)
    return f"https://ekaro.in/enkr?r={user_id}&url={encoded}"



class CreatorStorefrontGenerator:
    def __init__(self, output_dir: Path | str | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent / "data" / "storefront"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.catalog_file = self.output_dir / "catalog.json"
        self._init_catalog()

    def _init_catalog(self):
        if not self.catalog_file.exists():
            default_items = [
                {
                    "id": "item_1",
                    "title": "Classic Lavender Flame Hem Knit Sweater",
                    "category": "Sweaters",
                    "price": "₹577",
                    "mrp": "₹1,499",
                    "discount": "62% OFF",
                    "rating": "4.8",
                    "image": "meesho_flame_sweater_purple.jpg",
                    "meesho_url": "https://www.meesho.com/classic-fabulous-women-sweaters/p/flame-knit",
                    "earnkaro_link": make_earnkaro_affiliate_link("https://www.meesho.com/classic-fabulous-women-sweaters/p/flame-knit")
                },
                {
                    "id": "item_2",
                    "title": "Trendy Y2K Contrast Raglan Baby Tee",
                    "category": "Y2K Tops",
                    "price": "₹187",
                    "mrp": "₹699",
                    "discount": "73% OFF",
                    "rating": "4.6",
                    "image": "meesho_raglan_baby_tee.jpg",
                    "meesho_url": "https://www.meesho.com/trendy-graceful-women-tops/p/raglan-tee",
                    "earnkaro_link": make_earnkaro_affiliate_link("https://www.meesho.com/trendy-graceful-women-tops/p/raglan-tee")
                },
                {
                    "id": "item_3",
                    "title": "Pretty 90s Striped Ribbed Knit Top",
                    "category": "Y2K Tops",
                    "price": "₹138",
                    "mrp": "₹599",
                    "discount": "77% OFF",
                    "rating": "4.7",
                    "image": "meesho_striped_baby_tee.jpg",
                    "meesho_url": "https://www.meesho.com/pretty-modern-women-tops/p/striped-tee",
                    "earnkaro_link": make_earnkaro_affiliate_link("https://www.meesho.com/pretty-modern-women-tops/p/striped-tee")
                },
                {
                    "id": "item_4",
                    "title": "Allure Bohemian Chunky Silver Rings Set",
                    "category": "Jewelry",
                    "price": "₹117",
                    "mrp": "₹499",
                    "discount": "76% OFF",
                    "rating": "4.9",
                    "image": "meesho_chunky_rings.jpg",
                    "meesho_url": "https://www.meesho.com/allure-chunky-rings/p/silver-rings",
                    "earnkaro_link": make_earnkaro_affiliate_link("https://www.meesho.com/allure-chunky-rings/p/silver-rings")
                }
            ]
            self.catalog_file.write_text(json.dumps(default_items, indent=2), encoding="utf-8")

    def load_catalog(self) -> list[dict[str, Any]]:
        """Loads all catalog items currently in the storefront."""
        if not self.catalog_file.exists():
            return []
        return json.loads(self.catalog_file.read_text(encoding="utf-8"))

    def add_product_to_storefront(self, item_dict: dict[str, Any]):
        """Adds a newly scraped/generated product into the permanent storefront catalog."""
        catalog = json.loads(self.catalog_file.read_text(encoding="utf-8"))
        meesho_url = item_dict.get("meesho_url", "https://www.meesho.com")
        item_dict["earnkaro_link"] = make_earnkaro_affiliate_link(meesho_url)
        # Avoid duplicate URLs
        existing_urls = [x.get("meesho_url") for x in catalog]
        if meesho_url not in existing_urls:
            catalog.insert(0, item_dict)
            self.catalog_file.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
            log.info("Added product to storefront: '%s'", item_dict.get("title"))
        self.render_html_storefront()

    def render_html_storefront(self) -> Path:
        """Generates self-contained Wishlink-style mobile-first creator shop HTML."""
        catalog = json.loads(self.catalog_file.read_text(encoding="utf-8"))

        cards_html = ""
        for it in catalog:
            cards_html += f"""
            <div class="product-card">
                <div class="img-wrapper">
                    <img src="../scraped_products/{it.get('image', 'meesho_flame_sweater_purple.jpg')}" alt="{it.get('title')}" loading="lazy" />
                    <span class="discount-badge">{it.get('discount', '70% OFF')}</span>
                </div>
                <div class="card-info">
                    <span class="category-tag">{it.get('category', 'Fashion')}</span>
                    <h3 class="product-title">{it.get('title')}</h3>
                    <div class="price-row">
                        <span class="sale-price">{it.get('price')}</span>
                        <span class="mrp">{it.get('mrp', '')}</span>
                    </div>
                    <a href="{it.get('earnkaro_link')}" target="_blank" class="buy-btn">
                        🛒 Buy on Meesho
                    </a>
                </div>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{CREATOR_NAME} | Curated Fashion Wardrobe</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-primary: #0f0d13;
            --card-bg: #1a1622;
            --accent: #f43f5e;
            --accent-glow: rgba(244, 63, 94, 0.35);
            --text-main: #f9fafb;
            --text-muted: #9ca3af;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-main);
            min-height: 100vh;
            padding-bottom: 60px;
        }}
        .header {{
            text-align: center;
            padding: 40px 20px 24px;
            background: linear-gradient(180deg, #1e172a 0%, var(--bg-primary) 100%);
            border-bottom: 1px solid rgba(255,255,255,0.06);
        }}
        .avatar {{
            width: 88px;
            height: 88px;
            border-radius: 50%;
            background: linear-gradient(135deg, #f43f5e, #fb7185);
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            font-weight: 800;
            color: white;
            box-shadow: 0 8px 24px var(--accent-glow);
            margin-bottom: 14px;
            border: 3px solid rgba(255,255,255,0.2);
        }}
        .creator-title {{
            font-size: 24px;
            font-weight: 800;
            letter-spacing: -0.5px;
            margin-bottom: 6px;
        }}
        .bio {{
            color: var(--text-muted);
            font-size: 14px;
            max-width: 420px;
            margin: 0 auto 18px;
        }}
        .container {{
            max-width: 900px;
            margin: 28px auto 0;
            padding: 0 16px;
        }}
        .section-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: 700;
        }}
        .product-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
            gap: 20px;
        }}
        @media (max-width: 580px) {{
            .product-grid {{
                grid-template-columns: repeat(2, 1fr);
                gap: 12px;
            }}
        }}
        .product-card {{
            background: var(--card-bg);
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.08);
            transition: transform 0.2s, box-shadow 0.2s;
            display: flex;
            flex-direction: column;
        }}
        .product-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 28px rgba(0,0,0,0.5);
            border-color: rgba(244, 63, 94, 0.4);
        }}
        .img-wrapper {{
            position: relative;
            width: 100%;
            aspect-ratio: 1 / 1.15;
            background: #231f2d;
            overflow: hidden;
        }}
        .img-wrapper img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}
        .product-card:hover .img-wrapper img {{
            transform: scale(1.04);
        }}
        .discount-badge {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: var(--accent);
            color: white;
            font-size: 11px;
            font-weight: 800;
            padding: 4px 8px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }}
        .card-info {{
            padding: 14px;
            display: flex;
            flex-direction: column;
            flex: 1;
        }}
        .category-tag {{
            font-size: 11px;
            color: var(--accent);
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .product-title {{
            font-size: 14px;
            font-weight: 600;
            line-height: 1.35;
            color: var(--text-main);
            margin-bottom: 10px;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            overflow: hidden;
        }}
        .price-row {{
            margin-top: auto;
            display: flex;
            align-items: baseline;
            gap: 8px;
            margin-bottom: 12px;
        }}
        .sale-price {{
            font-size: 18px;
            font-weight: 800;
            color: #fde047;
        }}
        .mrp {{
            font-size: 13px;
            color: var(--text-muted);
            text-decoration: line-through;
        }}
        .buy-btn {{
            display: block;
            text-align: center;
            background: linear-gradient(135deg, #f43f5e, #e11d48);
            color: white;
            text-decoration: none;
            font-size: 13px;
            font-weight: 700;
            padding: 10px;
            border-radius: 12px;
            transition: opacity 0.2s;
            box-shadow: 0 4px 14px var(--accent-glow);
        }}
        .buy-btn:hover {{
            opacity: 0.92;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="avatar">P</div>
        <h1 class="creator-title">{CREATOR_NAME}</h1>
        <p class="bio">Affordable Meesho Outfits, Y2K Finds & Aesthetic Hauls ✨ Tap to shop!</p>
    </div>

    <div class="container">
        <div class="section-header">
            <h2 class="section-title">✨ Trending Meesho Outfits ({len(catalog)} Items)</h2>
        </div>
        <div class="product-grid">
            {cards_html}
        </div>
    </div>
</body>
</html>
"""
        out_html = self.output_dir / "index.html"
        out_html.write_text(html_content, encoding="utf-8")
        log.info("✅ Rendered Wishlink-Style Storefront: %s", out_html)
        return out_html


if __name__ == "__main__":
    storefront = CreatorStorefrontGenerator()
    html_path = storefront.render_html_storefront()
    print("\n🎉 [Storefront Created Successfully!]")
    print("  • Storefront HTML:", html_path)
    print("  • EarnKaro User ID:", EARNKARO_USER_ID)
    print("  • Creator Name:", CREATOR_NAME)
