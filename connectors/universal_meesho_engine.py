"""
Universal Meesho & Affiliate Video Production Engine.
Works universally for ANY product category across Meesho & Indian E-commerce:
- Ethnic Wear (Sarees, Lehengas, Kurtis - 15% Commission)
- Western Wear (Tops, Dresses, Jeans, Y2K Baby Tees - 12% Commission)
- Men's Fashion & Gym Activewear (Shirts, T-shirts, Compression - 12% Commission)
- Jewelry & Accessories (Rings, Necklaces, Jhumkas - 18% Commission)
- Beauty & Skincare (Serums, Illuminators, Perfume - 18% Commission)
- Footwear & Bags (Sneakers, Heels, Tote Bags - 14% Commission)
- Home Decor & Smart Gadgets (Bedsheets, Thermal Printers - 10-12% Commission)

Supports:
- Direct Meesho URL input
- Keyword / Title input
- Image path input
- Automatic Commission & Savings calculation (>5% to 18%)
- 100% Watermark-Free 1080x1920 60fps MP4 Reel Generation
"""
from __future__ import annotations

import json
import os
import re
import sys
import subprocess
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageFont

# Ensure root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger
from connectors.gemini_vision_director import GeminiVisionDirector
from connectors.watermark_remover import WatermarkRemover
from connectors.ugc_fashion_unboxer import _get_font

log = get_logger("universal_meesho_engine")

UNIVERSAL_COMMISSION_RATES = {
    "jewelry": 18.0,
    "beauty_skincare": 18.0,
    "saree_ethnic": 15.0,
    "bags_wallets": 15.0,
    "footwear": 14.0,
    "kurtis_suits": 14.0,
    "western_tops": 12.0,
    "mens_wear": 12.0,
    "home_decor": 12.0,
    "electronics": 9.0,
    "general": 10.0
}


class UniversalMeeshoEngine:
    def __init__(self, output_dir: Path | str | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent / "data" / "universal_meesho_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vision = GeminiVisionDirector()
        self.cleaner = WatermarkRemover(output_dir=self.output_dir)

    def process_universal_product(
        self,
        target_input: str,
        image_path: str | Path | None = None
    ) -> dict[str, Any]:
        """Processes ANY Meesho URL, keyword, or image and returns clean 60fps MP4 Reel."""
        target = target_input.strip()
        log.info("🌐 [Universal Meesho Engine] Processing: '%s'", target)

        # 1. Parse product title & determine category
        clean_title = self._extract_clean_title(target)
        cat_key, commission_pct = self._detect_category_and_commission(clean_title)

        # 2. Locate or select reference image
        ref_image = self._resolve_product_image(clean_title, image_path)

        # 3. Analyze with Gemini Multimodal Vision / LLM
        vision_data = self.vision.analyze_image_for_ugc(ref_image, product_title=clean_title)

        price = vision_data.get("sale_price", "₹399")
        mrp = vision_data.get("mrp", "₹1,499")
        discount = vision_data.get("discount", "70% OFF")
        headline = vision_data.get("headline", f"{clean_title[:16]} Haul ✨")
        fabric_info = vision_data.get("fabric_and_color", "High quality verified material")
        hook = vision_data.get("hook", f"Viral Meesho find under {price}! Quality is 10/10 ✨")

        # Calculate estimated affiliate profit
        price_num = float(re.sub(r'[^0-9]', '', price) or "399")
        est_commission = round(price_num * (commission_pct / 100.0), 2)

        # 4. Render Luxury 1080x1920 Frame
        frame_path = self._render_luxury_frame(
            title=vision_data.get("product_name", clean_title),
            price=price,
            mrp=mrp,
            discount=discount,
            headline=headline,
            fabric_info=fabric_info,
            category_tag=cat_key.replace("_", " ").title(),
            img_path=ref_image
        )

        # 5. Compile into 60fps MP4
        slug = re.sub(r'[^a-zA-Z0-9]', '_', clean_title[:16]).lower()
        raw_mp4 = self.output_dir / f"RAW_UNIVERSAL_{slug.upper()}.mp4"

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(frame_path),
            "-t", "8",
            "-vf", "scale=1080:1920,fps=60",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(raw_mp4)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 6. Watermark Clean
        clean_mp4 = self.cleaner.clean_video(raw_mp4)

        # 7. Wishlink & Reels Caption
        wishlink_code = f"WL-{slug[:8].upper()}-{int(price_num)}"
        caption = (
            f"✨ {hook}\n\n"
            f"📦 Product: {vision_data.get('product_name', clean_title)}\n"
            f"💰 Price: {price} (MRP {mrp} - {discount}!)\n"
            f"⭐ Rating: 4.8/5.0 | Free Delivery & Cash on Delivery\n"
            f"🧵 Details: {fabric_info[:80]}...\n\n"
            f"👉 How to get the link:\n"
            f"1️⃣ Comment 'LINK' below & I'll DM you the direct Wishlink / Meesho link!\n"
            f"2️⃣ Link also in my Bio!\n\n"
            f"🛍️ Wishlink Code: {wishlink_code}\n"
            f"💰 Commission Margin: {commission_pct}% (~₹{est_commission}/sale)\n"
            f"#meeshofinds #viralproducts #meeshohaul #wishlinkhaul #trendingonline #under500"
        )

        log.info("🎉 Universal Video Ready: %s", clean_mp4)
        return {
            "status": "success",
            "title": vision_data.get("product_name", clean_title),
            "video_path": str(clean_mp4),
            "price": price,
            "commission_rate": f"{commission_pct}%",
            "est_commission": f"₹{est_commission}",
            "caption": caption,
            "wishlink_code": wishlink_code
        }

    def _extract_clean_title(self, target: str) -> str:
        if "meesho.com" in target:
            # Extract slug from URL e.g. meesho.com/saree-xyz/p/123 -> Saree Xyz
            match = re.search(r"meesho\.com/([^/?#]+)", target)
            if match:
                slug = match.group(1).replace("-", " ").title()
                if "Search" not in slug and "P" != slug:
                    return slug[:35]
        # Remove slash commands if sent from Telegram
        target = re.sub(r"^/(video|haul|deal)\s*", "", target, flags=re.IGNORECASE)
        return target[:35] or "Meesho Viral Trending Product"

    def _detect_category_and_commission(self, title: str) -> tuple[str, float]:
        t = title.lower()
        if any(w in t for w in ["ring", "necklace", "jhumka", "earring", "jewelry", "jewellery", "bangle", "chain"]):
            return "jewelry", UNIVERSAL_COMMISSION_RATES["jewelry"]
        elif any(w in t for w in ["serum", "cream", "lipstick", "makeup", "beauty", "skincare", "illuminator", "perfume"]):
            return "beauty_skincare", UNIVERSAL_COMMISSION_RATES["beauty_skincare"]
        elif any(w in t for w in ["saree", "lehenga", "silk", "chanderi", "banarasi", "chiffon saree"]):
            return "saree_ethnic", UNIVERSAL_COMMISSION_RATES["saree_ethnic"]
        elif any(w in t for w in ["kurti", "anarkali", "suit", "dupatta", "chikankari"]):
            return "kurtis_suits", UNIVERSAL_COMMISSION_RATES["kurtis_suits"]
        elif any(w in t for w in ["bag", "handbag", "tote", "wallet", "sling"]):
            return "bags_wallets", UNIVERSAL_COMMISSION_RATES["bags_wallets"]
        elif any(w in t for w in ["shoe", "sneaker", "heel", "sandal", "footwear", "loafer"]):
            return "footwear", UNIVERSAL_COMMISSION_RATES["footwear"]
        elif any(w in t for w in ["gym", "activewear", "compression", "tshirt", "t-shirt", "shirt men", "men"]):
            return "mens_wear", UNIVERSAL_COMMISSION_RATES["mens_wear"]
        elif any(w in t for w in ["sweater", "cardigan", "top", "tee", "dress", "skirt"]):
            return "western_tops", UNIVERSAL_COMMISSION_RATES["western_tops"]
        elif any(w in t for w in ["bedsheet", "curtain", "decor", "kitchen", "lamp", "bottle"]):
            return "home_decor", UNIVERSAL_COMMISSION_RATES["home_decor"]
        return "general", UNIVERSAL_COMMISSION_RATES["general"]

    def _resolve_product_image(self, clean_title: str, image_path: str | Path | None) -> Path:
        if image_path and Path(image_path).exists():
            return Path(image_path)
        # Check if we have cropped images matching title
        scraped_dir = Path(__file__).resolve().parent.parent / "data" / "scraped_products"
        t = clean_title.lower()
        if "sweater" in t and (scraped_dir / "meesho_flame_sweater_purple.jpg").exists():
            return scraped_dir / "meesho_flame_sweater_purple.jpg"
        elif ("baby tee" in t or "raglan" in t or "top" in t) and (scraped_dir / "meesho_raglan_baby_tee.jpg").exists():
            return scraped_dir / "meesho_raglan_baby_tee.jpg"
        elif "ring" in t and (scraped_dir / "meesho_chunky_rings.jpg").exists():
            return scraped_dir / "meesho_chunky_rings.jpg"
        elif "striped" in t and (scraped_dir / "meesho_striped_baby_tee.jpg").exists():
            return scraped_dir / "meesho_striped_baby_tee.jpg"
        
        # Default high-res fallback
        fallback = Path(__file__).resolve().parent.parent / "data" / "ref_frame1.jpg"
        return fallback if fallback.exists() else (scraped_dir / "meesho_flame_sweater_purple.jpg")

    def _render_luxury_frame(
        self,
        title: str,
        price: str,
        mrp: str,
        discount: str,
        headline: str,
        fabric_info: str,
        category_tag: str,
        img_path: Path
    ) -> Path:
        """Renders 1080x1920 luxury UGC frame applicable to ANY product."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (18, 16, 22, 255))
        draw = ImageDraw.Draw(canvas)

        # Ambient backdrop gradient
        for y in range(0, h, 6):
            ratio = y / h
            r = int(95 - 20 * ratio)
            g = int(90 - 18 * ratio)
            b = int(105 - 15 * ratio)
            draw.rectangle([0, y, w, y + 6], fill=(r, g, b, 255))

        # Main Real Product Showcase
        try:
            raw_img = Image.open(img_path).convert("RGBA")
            tw, th = 900, 1080
            aspect = tw / th
            img_aspect = raw_img.width / raw_img.height
            if img_aspect > aspect:
                nw = int(raw_img.height * aspect)
                left = (raw_img.width - nw) // 2
                raw_img = raw_img.crop((left, 0, left + nw, raw_img.height))
            else:
                nh = int(raw_img.width / aspect)
                top = (raw_img.height - nh) // 2
                raw_img = raw_img.crop((0, top, raw_img.width, top + nh))

            raw_img = raw_img.resize((tw, th), Image.Resampling.LANCZOS)
            mask = Image.new("L", (tw, th), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw, th], radius=28, fill=255)

            draw.rounded_rectangle([86, 426, 86 + tw + 8, 426 + th + 8], radius=32, fill=(0, 0, 0, 140))
            canvas.paste(raw_img, (90, 430), mask)
            draw.rounded_rectangle([90, 430, 90 + tw, 430 + th], radius=28, outline=(255, 255, 255, 220), width=3)
        except Exception as e:
            log.warning("Universal frame image notice: %s", e)

        # Top Pill: Category Tag
        draw.rounded_rectangle([300, 120, 780, 190], radius=18, fill=(244, 63, 94, 255))
        draw.text((540, 155), f"🔥 {category_tag.upper()} • MEESHO FIND", fill=(255, 255, 255, 255), font=_get_font(26, bold=True), anchor="mm")

        # Aesthetic Headline
        font_h = _get_font(52, bold=True)
        draw.text((542, 262), headline, fill=(0, 0, 0, 220), font=font_h, anchor="mm")
        draw.text((540, 260), headline, fill=(255, 255, 255, 255), font=font_h, anchor="mm")

        # Subtitle Product Title
        draw.rounded_rectangle([180, 320, 900, 375], radius=16, fill=(25, 20, 30, 220), outline=(255, 255, 255, 140), width=2)
        draw.text((540, 347), title[:35], fill=(240, 230, 245, 255), font=_get_font(24, bold=True), anchor="mm")

        # Bottom Price Card
        draw.rounded_rectangle([90, 1540, 990, 1750], radius=26, fill=(15, 12, 18, 235), outline=(255, 255, 255, 180), width=2)
        price_text = f"💰 {price}  (MRP {mrp} • {discount})"
        draw.text((540, 1600), price_text, fill=(255, 230, 100, 255), font=_get_font(34, bold=True), anchor="mm")

        draw.text((540, 1665), f"🧵 {fabric_info[:52]}...", fill=(220, 215, 230, 255), font=_get_font(22), anchor="mm")
        draw.text((540, 1715), "👉 Comment 'LINK' for direct Wishlink DM!", fill=(244, 63, 94, 255), font=_get_font(22, bold=True), anchor="mm")

        slug = re.sub(r'[^a-zA-Z0-9]', '_', title[:15]).lower()
        out_f = self.output_dir / f"universal_frame_{slug}.png"
        canvas.convert("RGB").save(out_f, format="PNG", quality=95)
        return out_f


if __name__ == "__main__":
    engine = UniversalMeeshoEngine()
    # Test with saree / jewelry / men
    test_queries = [
        "Banarasi Soft Silk Saree with Gold Zari Border",
        "Men Slim Fit Compression Activewear Tshirt",
        "Vintage Chunky Silver Bohemian Rings"
    ]
    for q in test_queries:
        res = engine.process_universal_product(q)
        print(f"\n🎉 Generated for '{q}':")
        print("  • Video:", res["video_path"])
        print("  • Commission:", res["commission_rate"], f"({res['est_commission']})")
        print("  • Caption Preview:\n", res["caption"][:150] + "...")
