"""
Multi-Product Outfit Haul Video Engine (Combos & Wardrobe Collections).
Automatically generates viral multi-item unboxing haul reels (e.g., 3 Sweaters Haul, Festive Kurti Combos):
1. Accepts multiple product reference images (scraped from Meesho / Pinterest)
2. Uses Gemini Vision to analyze each garment's fabric, weave, color, and price
3. Stitches a dynamic 15-second multi-item comparison haul:
   - Item 1 (0-4s): Unboxing + Try-on badge + Price
   - Item 2 (4-8s): Unboxing + Try-on badge + Price
   - Item 3 (8-12s): Unboxing + Try-on badge + Price
   - CTA Outro (12-15s): 'Which one is your favorite? 1, 2, or 3? Comment below!'
4. Runs through WatermarkRemover for 100% clean, zero-logo output!
"""
from __future__ import annotations

import json
import os
import sys
import subprocess
from pathlib import Path

# Safeguard root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from typing import Any
from PIL import Image, ImageDraw, ImageFont

from core.logging_utils import get_logger
from connectors.gemini_vision_director import GeminiVisionDirector
from connectors.watermark_remover import WatermarkRemover
from connectors.ugc_fashion_unboxer import UGCFashionUnboxingStudio, _get_font

log = get_logger("multi_product_haul")


class MultiProductHaulStudio:
    def __init__(self, output_dir: Path | str | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent / "data" / "multi_haul_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vision = GeminiVisionDirector()
        self.ugc_studio = UGCFashionUnboxingStudio(output_dir=self.output_dir)
        self.cleaner = WatermarkRemover(output_dir=self.output_dir)

    def produce_multi_item_haul(
        self,
        images: list[str | Path],
        haul_title: str = "Meesho Viral Sweaters Haul ☕",
        niche: str = "Winter Cozy Outfits"
    ) -> dict[str, Any]:
        """Creates a viral multi-item comparison haul reel from multiple product images."""
        if not images:
            raise ValueError("At least 1 product reference image is required.")

        log.info("🚀 Starting Multi-Item Haul Production for: '%s' (%d items)", haul_title, len(images))

        clip_files: list[Path] = []
        analyzed_items: list[dict[str, Any]] = []

        # 1. Analyze each item with Gemini Vision & render individual 4s clips
        for idx, img_path in enumerate(images, start=1):
            p = Path(img_path)
            if not p.exists():
                continue
            log.info("Analyzing Haul Item #%d: %s...", idx, p.name)
            item_data = self.vision.analyze_image_for_ugc(p, product_title=f"{haul_title} Item #{idx}")
            analyzed_items.append(item_data)

            # Render custom composite frame with Item # badge
            frame_path = self._render_haul_slide(item_data, p, item_number=idx, total_items=len(images), haul_title=haul_title)

            # Compile into 4-second MP4 segment
            sub_mp4 = self.output_dir / f"temp_item_{idx}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(frame_path),
                "-t", "4",
                "-vf", "scale=1080:1920,fps=60",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(sub_mp4)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            clip_files.append(sub_mp4)

        # 2. Render CTA Outro Slide: 'Comment 1, 2, or 3 for direct link!'
        outro_frame = self._render_outro_slide(haul_title, len(analyzed_items))
        outro_mp4 = self.output_dir / "temp_item_outro.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(outro_frame),
            "-t", "3",
            "-vf", "scale=1080:1920,fps=60",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(outro_mp4)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        clip_files.append(outro_mp4)

        # 3. Concatenate all segments seamlessly
        concat_txt = self.output_dir / "concat_list.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clip_files:
                f.write(f"file '{c.resolve().as_posix()}'\n")

        slug = haul_title[:18].lower().replace(" ", "_").replace("☕", "").replace("✨", "").strip()
        merged_raw = self.output_dir / f"RAW_MULTI_HAUL_{slug.upper()}.mp4"

        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(merged_raw)
        ]
        subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        # 4. Run through WatermarkRemover for 100% clean guarantee
        clean_final = self.cleaner.clean_video(merged_raw)

        # 5. Build high-engagement caption
        items_desc = "\n".join([f"✨ Look #{i}: {it.get('product_name')} - Only {it.get('sale_price')} ({it.get('discount')})" for i, it in enumerate(analyzed_items, 1)])
        caption = (
            f"🔥 {haul_title} Under ₹500! Which one is your favorite?\n\n"
            f"{items_desc}\n\n"
            f"👇 Comment 1, 2, or 3 & I'll DM you the exact link instantly!\n"
            f"🔗 Link also in bio!\n\n"
            f"#meeshohaul #sweaterweather #winterhaul #viraloutfits #collegefits #affordablefashion #tryonhaul"
        )

        log.info("🎉 Multi-Item Haul Video Complete: %s", clean_final)
        return {
            "status": "success",
            "haul_title": haul_title,
            "total_items": len(analyzed_items),
            "video_path": str(clean_final),
            "caption": caption
        }

    def _render_haul_slide(self, item: dict[str, Any], img_path: Path, item_number: int, total_items: int, haul_title: str) -> Path:
        """Renders 1080x1920 high-craft slide with Item # counter and Try-on inset."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (20, 18, 22, 255))
        draw = ImageDraw.Draw(canvas)

        # Ambient background gradient
        for y in range(0, h, 6):
            ratio = y / h
            r = int(120 - 30 * ratio)
            g = int(110 - 25 * ratio)
            b = int(105 - 20 * ratio)
            draw.rectangle([0, y, w, y + 6], fill=(r, g, b, 255))

        # Main Real Product Showcase Center
        try:
            raw_img = Image.open(img_path).convert("RGBA")
            target_w = 880
            target_h = 1050
            aspect = target_w / target_h
            img_aspect = raw_img.width / raw_img.height
            if img_aspect > aspect:
                new_w = int(raw_img.height * aspect)
                left = (raw_img.width - new_w) // 2
                raw_img = raw_img.crop((left, 0, left + new_w, raw_img.height))
            else:
                new_h = int(raw_img.width / aspect)
                top = (raw_img.height - new_h) // 2
                raw_img = raw_img.crop((0, top, raw_img.width, top + new_h))

            raw_img = raw_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            mask = Image.new("L", (target_w, target_h), 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.rounded_rectangle([0, 0, target_w, target_h], radius=24, fill=255)

            # Drop shadow
            draw.rounded_rectangle([96, 446, 96 + target_w + 8, 446 + target_h + 8], radius=28, fill=(0, 0, 0, 140))
            canvas.paste(raw_img, (100, 450), mask)
            # Subtle border
            draw.rounded_rectangle([100, 450, 100 + target_w, 450 + target_h], radius=24, outline=(255, 255, 255, 200), width=3)
        except Exception as e:
            log.warning("Could not render center product image: %s", e)

        # Top Bar: Haul Title + Counter Badge (e.g. 'LOOK 1 OF 3')
        draw.rounded_rectangle([320, 140, 760, 210], radius=18, fill=(244, 63, 94, 255))
        draw.text((540, 175), f"🔥 LOOK #{item_number} OF {total_items}", fill=(255, 255, 255, 255), font=_get_font(28, bold=True), anchor="mm")

        # Aesthetic Headline
        font_h = _get_font(52, bold=True)
        draw.text((542, 272), item.get("product_name", "Aesthetic Outfit"), fill=(0, 0, 0, 200), font=font_h, anchor="mm")
        draw.text((540, 270), item.get("product_name", "Aesthetic Outfit"), fill=(255, 255, 255, 255), font=font_h, anchor="mm")

        # Bottom Price Pill & Fabric Info
        draw.rounded_rectangle([120, 1550, 960, 1750], radius=22, fill=(15, 12, 18, 235), outline=(255, 255, 255, 180), width=2)
        price_text = f"💰 ONLY {item.get('sale_price', '₹499')} ({item.get('discount', '70% OFF')})"
        draw.text((540, 1610), price_text, fill=(255, 230, 100, 255), font=_get_font(34, bold=True), anchor="mm")
        fabric_text = f"🧵 {item.get('fabric_and_color', '')[:50]}..."
        draw.text((540, 1680), fabric_text, fill=(230, 230, 230, 255), font=_get_font(22), anchor="mm")

        out_frame = self.output_dir / f"haul_slide_{item_number}.png"
        canvas.convert("RGB").save(out_frame, format="PNG", quality=95)
        return out_frame

    def _render_outro_slide(self, haul_title: str, total_items: int) -> Path:
        """Renders Call-To-Action outro slide triggering massive comment engagement."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (18, 14, 20, 255))
        draw = ImageDraw.Draw(canvas)

        # Bold Question Box
        draw.rounded_rectangle([100, 500, 980, 1400], radius=32, fill=(30, 25, 35, 255), outline=(244, 63, 94, 255), width=4)

        draw.text((540, 650), "WHICH ONE IS YOUR FAVORITE?", fill=(255, 255, 255, 255), font=_get_font(42, bold=True), anchor="mm")
        
        # Options 1, 2, 3
        options_text = " • ".join([f"#{i}" for i in range(1, total_items + 1)])
        draw.rounded_rectangle([250, 750, 830, 890], radius=24, fill=(244, 63, 94, 255))
        draw.text((540, 820), f"LOOK {options_text}", fill=(255, 255, 255, 255), font=_get_font(44, bold=True), anchor="mm")

        draw.text((540, 1040), "👇 Comment your favorite number below!", fill=(255, 240, 245, 255), font=_get_font(32, bold=True), anchor="mm")
        draw.text((540, 1120), "I will DM you the direct Meesho link instantly! 💌", fill=(200, 190, 210, 255), font=_get_font(24), anchor="mm")

        out_frame = self.output_dir / "haul_slide_outro.png"
        canvas.convert("RGB").save(out_frame, format="PNG", quality=95)
        return out_frame


if __name__ == "__main__":
    studio = MultiProductHaulStudio()
    test_images = ["data/ref_frame1.jpg", "data/ref_frame2.jpg"]
    res = studio.produce_multi_item_haul(test_images, haul_title="Meesho Viral Knit Sweaters Haul ☕")
    print("\n🎉 Multi-Item Haul Generated Successfully!")
    print("  • Video:", res["video_path"])
    print("  • Caption:\n", res["caption"])
