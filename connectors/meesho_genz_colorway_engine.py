"""
Meesho GenZ & Multi-Colorway Fashion Studio (Wishlink & Telegram Ready).
Features:
1. Multi-Colorway Showcase: 1 Product in multiple colors ('+5 More' / '+3 More' as seen on Meesho)
   - e.g. Flame Sweater in 3 Colors: Lavender Flame 💜, Obsidian Flame 🖤, Baby Pink Flame 🌸
2. GenZ Aesthetic Auto-Classifier:
   - Y2K / Grunge Baby Tees
   - Fire / Flame Knitwear & Oversized Cardigans
   - Chunky Gothic Rings & Silver Jewelry
   - Men Compression & Gym Activewear
3. Wishlink Deep Link Integration (Automated 'Comment LINK' format)
4. 100% Watermark-Free 1080x1920 60fps MP4 Reel + Telegram Dispatch
"""
from __future__ import annotations

import json
import os
import sys
import subprocess
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw, ImageEnhance, ImageOps

# Ensure root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger
from connectors.gemini_vision_director import GeminiVisionDirector
from connectors.watermark_remover import WatermarkRemover
from connectors.ugc_fashion_unboxer import _get_font

log = get_logger("meesho_genz_colorways")


GENZ_VIRAL_CATEGORIES = {
    "y2k_baby_tees": {
        "tag": "Y2K Grunge & Baby Tees",
        "hook": "Meesho Y2K baby tees under ₹200 that look straight off Pinterest ✨",
        "sample_colors": [("Mocha & Black", (90, 60, 50)), ("Baby Blue & White", (60, 100, 140)), ("Olive & Charcoal", (70, 80, 50))]
    },
    "flame_knit_sweaters": {
        "tag": "Flame & Graphic Knitwear",
        "hook": "The viral flame knit sweater everyone is gatekeeping on Instagram! Under ₹600 💜",
        "sample_colors": [("Pastel Lavender Flame 💜", (160, 130, 210)), ("Obsidian Black Flame 🖤", (35, 35, 45)), ("Cyber Pink Flame 🌸", (220, 120, 160))]
    },
    "striped_90s_crop": {
        "tag": "90s Striped Ribbed Tops",
        "hook": "Found the cutest 90s striped ribbed top on Meesho for literally ₹138! 🍭",
        "sample_colors": [("Retro Rainbow", (180, 80, 80)), ("Ocean Blue Stripe", (50, 120, 170)), ("Mocha Latte Stripe", (120, 90, 70))]
    },
    "chunky_rings_jewelry": {
        "tag": "GenZ Aesthetic Jewelry",
        "hook": "Vintage chunky silver rings set under ₹120! Quality is unreal ✨",
        "sample_colors": [("Vintage Silver", (190, 195, 205)), ("Antiqued Gunmetal", (100, 105, 115))]
    }
}


class MeeshoGenZColorwayStudio:
    def __init__(self, output_dir: Path | str | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent / "data" / "genz_colorways_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vision = GeminiVisionDirector()
        self.cleaner = WatermarkRemover(output_dir=self.output_dir)

    def produce_colorways_reel(
        self,
        base_image: str | Path,
        product_title: str = "Flame Hem Knit Sweater",
        price: str = "₹577",
        mrp: str = "₹1,499",
        discount: str = "62% OFF",
        wishlink_code: str = "WL-MEESHO-789",
        color_variants: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        """Creates a viral '1 Product, Multiple Colors' reel showcasing all color variations."""
        base_p = Path(base_image)
        if not base_p.exists():
            raise FileNotFoundError(f"Base product image not found: {base_p}")

        log.info("🚀 Generating Multi-Colorway Reel for: '%s' (%s)", product_title, price)

        # Default 3 high-converting colorways if not specified
        if not color_variants:
            color_variants = [
                {"name": "Lavender Flame 💜", "tint": (155, 120, 210, 80)},
                {"name": "Obsidian Black Flame 🖤", "tint": (20, 20, 30, 140)},
                {"name": "Cyber Pink Flame 🌸", "tint": (220, 90, 150, 80)},
            ]

        clip_files: list[Path] = []
        variant_images: list[Path] = []

        # 1. Generate / Prepare variant images & individual 3.5s video clips
        for idx, variant in enumerate(color_variants, start=1):
            var_name = variant["name"]
            # Create tinted variant image or load existing
            var_img_path = self.output_dir / f"variant_{idx}_{base_p.name}"
            self._create_colorway_image(base_p, var_img_path, variant.get("tint"))
            variant_images.append(var_img_path)

            # Render 1080x1920 Frame with Colorway Badge
            frame_path = self._render_colorway_frame(
                img_path=var_img_path,
                title=product_title,
                price=price,
                mrp=mrp,
                discount=discount,
                color_name=var_name,
                color_index=idx,
                total_colors=len(color_variants)
            )

            # Compile into 3.5-second clip with subtle zoom
            sub_mp4 = self.output_dir / f"clip_color_{idx}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(frame_path),
                "-t", "3.5",
                "-vf", "scale=1080:1920,fps=60",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(sub_mp4)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            clip_files.append(sub_mp4)

        # 2. Render All-Colors Comparison & CTA Outro (3.5s)
        outro_frame = self._render_all_colors_cta_frame(
            variant_images=variant_images,
            color_variants=color_variants,
            title=product_title,
            price=price
        )
        outro_mp4 = self.output_dir / "clip_color_outro.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(outro_frame),
            "-t", "4",
            "-vf", "scale=1080:1920,fps=60",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(outro_mp4)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        clip_files.append(outro_mp4)

        # 3. Concatenate all colorway clips
        concat_txt = self.output_dir / "color_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clip_files:
                f.write(f"file '{c.resolve().as_posix()}'\n")

        slug = product_title[:16].lower().replace(" ", "_").strip()
        merged_raw = self.output_dir / f"RAW_COLORWAYS_{slug.upper()}.mp4"

        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(merged_raw)
        ]
        subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 4. Clean watermark with WatermarkRemover
        final_video = self.cleaner.clean_video(merged_raw)

        # 5. Build Wishlink Automated Comment Hook
        color_list_text = "\n".join([f"✨ Color {i}: {v['name']}" for i, v in enumerate(color_variants, 1)])
        caption = (
            f"🔥 Meesho {product_title} in 3 VIRAL COLORS! Only {price} ({discount})\n\n"
            f"{color_list_text}\n\n"
            f"👇 WHICH COLOR WOULD YOU WEAR? Comment 1, 2, or 3 below!\n"
            f"💌 Direct Wishlink / Meesho link will be sent to your DMs automatically!\n\n"
            f"🛍️ Wishlink Code: {wishlink_code}\n"
            f"#meeshofinds #y2koutfits #colorwayhaul #pinterestoutfits #sweaterweather #under600 #wishlinkhaul"
        )

        log.info("🎉 Multi-Colorway Reel Ready: %s", final_video)
        return {
            "status": "success",
            "title": product_title,
            "video_path": str(final_video),
            "colors_count": len(color_variants),
            "caption": caption,
            "wishlink_code": wishlink_code
        }

    def _create_colorway_image(self, src: Path, dest: Path, tint: tuple[int, int, int, int] | None):
        """Creates authentic color variations of the base product using PIL tint overlay."""
        img = Image.open(src).convert("RGBA")
        if tint:
            # Create semi-transparent color overlay
            overlay = Image.new("RGBA", img.size, tint)
            img = Image.alpha_composite(img, overlay)
        img.convert("RGB").save(dest, format="JPEG", quality=95)

    def _render_colorway_frame(
        self,
        img_path: Path,
        title: str,
        price: str,
        mrp: str,
        discount: str,
        color_name: str,
        color_index: int,
        total_colors: int
    ) -> Path:
        """Renders 1080x1920 luxury vertical frame with Colorway highlight."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (18, 16, 20, 255))
        draw = ImageDraw.Draw(canvas)

        # Aesthetic mood gradient
        for y in range(0, h, 6):
            ratio = y / h
            r = int(100 - 25 * ratio)
            g = int(95 - 20 * ratio)
            b = int(110 - 15 * ratio)
            draw.rectangle([0, y, w, y + 6], fill=(r, g, b, 255))

        # Big Center Product Image
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
            mdraw = ImageDraw.Draw(mask)
            mdraw.rounded_rectangle([0, 0, tw, th], radius=28, fill=255)

            # Shadow + Image paste
            draw.rounded_rectangle([86, 436, 86 + tw + 8, 436 + th + 8], radius=32, fill=(0, 0, 0, 140))
            canvas.paste(raw_img, (90, 440), mask)
            draw.rounded_rectangle([90, 440, 90 + tw, 440 + th], radius=28, outline=(255, 255, 255, 220), width=3)
        except Exception as e:
            log.warning("Colorway image render notice: %s", e)

        # Top Bar: 1 Product, 3 Colors
        draw.rounded_rectangle([280, 130, 800, 200], radius=18, fill=(244, 63, 94, 255))
        draw.text((540, 165), f"✨ 1 PRODUCT • {total_colors} VIRAL COLORS", fill=(255, 255, 255, 255), font=_get_font(28, bold=True), anchor="mm")

        # Color Name Badge
        font_c = _get_font(52, bold=True)
        draw.text((542, 272), color_name, fill=(0, 0, 0, 220), font=font_c, anchor="mm")
        draw.text((540, 270), color_name, fill=(255, 255, 255, 255), font=font_c, anchor="mm")

        # Subtitle Color Counter Pill
        draw.rounded_rectangle([380, 330, 700, 385], radius=16, fill=(30, 26, 35, 220), outline=(255, 255, 255, 160), width=2)
        draw.text((540, 357), f"COLORWAY {color_index} OF {total_colors}", fill=(240, 230, 245, 255), font=_get_font(22, bold=True), anchor="mm")

        # Bottom Price Card
        draw.rounded_rectangle([100, 1560, 980, 1750], radius=24, fill=(15, 12, 18, 235), outline=(255, 255, 255, 180), width=2)
        price_text = f"💰 {price}  (MRP {mrp} - {discount})"
        draw.text((540, 1620), price_text, fill=(255, 230, 100, 255), font=_get_font(34, bold=True), anchor="mm")
        draw.text((540, 1690), "👉 Wishlink Code: WL-MEESHO-789 • Free Delivery", fill=(220, 215, 230, 255), font=_get_font(24), anchor="mm")

        out_f = self.output_dir / f"colorway_frame_{color_index}.png"
        canvas.convert("RGB").save(out_f, format="PNG", quality=95)
        return out_f

    def _render_all_colors_cta_frame(
        self,
        variant_images: list[Path],
        color_variants: list[dict[str, Any]],
        title: str,
        price: str
    ) -> Path:
        """Renders finale comparison screen where all colors are shown side-by-side to trigger comments."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (18, 14, 22, 255))
        draw = ImageDraw.Draw(canvas)

        # Question Header
        draw.rounded_rectangle([100, 140, 980, 280], radius=24, fill=(244, 63, 94, 255))
        draw.text((540, 210), "WHICH COLOR IS YOUR FAVORITE?", fill=(255, 255, 255, 255), font=_get_font(38, bold=True), anchor="mm")

        # Grid of the 3 color variants side-by-side
        cols = len(variant_images)
        card_w = int((880 - (cols - 1) * 20) / cols)
        card_h = 750

        for i, (p, v) in enumerate(zip(variant_images, color_variants)):
            x = 100 + i * (card_w + 20)
            y = 360
            try:
                c_img = Image.open(p).convert("RGBA")
                c_img = c_img.resize((card_w, card_h), Image.Resampling.LANCZOS)
                c_mask = Image.new("L", (card_w, card_h), 0)
                ImageDraw.Draw(c_mask).rounded_rectangle([0, 0, card_w, card_h], radius=20, fill=255)

                canvas.paste(c_img, (x, y), c_mask)
                draw.rounded_rectangle([x, y, x + card_w, y + card_h], radius=20, outline=(255, 255, 255, 220), width=3)

                # Number Badge over each card
                draw.rounded_rectangle([x + 15, y + card_h - 75, x + card_w - 15, y + card_h - 15], radius=14, fill=(0, 0, 0, 220))
                draw.text((x + card_w // 2, y + card_h - 45), f"#{i+1}", fill=(255, 255, 255, 255), font=_get_font(32, bold=True), anchor="mm")
            except Exception as e:
                log.warning("All-colors card error: %s", e)

        # Big CTA Box
        draw.rounded_rectangle([100, 1200, 980, 1680], radius=32, fill=(26, 22, 32, 255), outline=(244, 63, 94, 255), width=3)
        draw.text((540, 1310), f"🔥 ONLY {price} ON MEESHO", fill=(255, 230, 100, 255), font=_get_font(38, bold=True), anchor="mm")
        draw.text((540, 1420), "👇 Comment #1, #2, or #3 below!", fill=(255, 255, 255, 255), font=_get_font(34, bold=True), anchor="mm")
        draw.text((540, 1520), "Direct Wishlink will be sent to your DMs! 💌", fill=(220, 210, 230, 255), font=_get_font(26), anchor="mm")

        out_f = self.output_dir / "colorway_all_cta_frame.png"
        canvas.convert("RGB").save(out_f, format="PNG", quality=95)
        return out_f


if __name__ == "__main__":
    studio = MeeshoGenZColorwayStudio()
    # Test on the Flame Sweater extracted from user screenshot
    test_img = "data/scraped_products/meesho_flame_sweater_purple.jpg"
    res = studio.produce_colorways_reel(
        base_image=test_img,
        product_title="Flame Hem Knit Sweater",
        price="₹577",
        mrp="₹1,499",
        discount="62% OFF",
        wishlink_code="WL-FLAME-577"
    )
    print("\n🎉 Multi-Colorway Reel Generated Successfully!")
    print("  • Video Path:", res["video_path"])
    print("  • Caption:\n", res["caption"])
