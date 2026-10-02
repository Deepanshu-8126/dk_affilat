"""
Aesthetic Complete Outfit Lookbook & Combination Studio.
Curates real multi-product aesthetic bundles from Meesho (Top + Layer + Jewelry/Accessories):
1. Combines disparate items into a unified Pinterest viral styling lookbook:
   - Piece 1: Base Top (e.g. Y2K Contrast Raglan Baby Tee • ₹187)
   - Piece 2: Layering Piece (e.g. Lavender Flame Knit Sweater • ₹577)
   - Piece 3: Bling & Accessories (e.g. Chunky Silver Bohemian Rings • ₹117)
2. Calculates Total Bundle Price (e.g. Full Look Under ₹900)
3. Renders a cinematic 14-second 1080x1920 60fps Lookbook Reel:
   - Scene 1 (0-3s): The Base Top
   - Scene 2 (3-6s): The Layering Sweater
   - Scene 3 (6-9s): The Chunky Rings Bling
   - Scene 4 (9-14s): Master Pinterest Flatlay Moodboard of ALL 3 items styled together!
4. Zero Watermarks & Wishlink Collection DM Trigger ('Comment OUTFIT').
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

log = get_logger("combo_lookbook_studio")


class AestheticComboLookbookStudio:
    def __init__(self, output_dir: Path | str | None = None):
        if output_dir:
            self.output_dir = Path(output_dir)
        else:
            self.output_dir = Path(__file__).resolve().parent.parent / "data" / "combo_lookbook_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.vision = GeminiVisionDirector()
        self.cleaner = WatermarkRemover(output_dir=self.output_dir)

    def produce_complete_lookbook(
        self,
        pieces: list[dict[str, Any]],
        lookbook_theme: str = "Pinterest Y2K Aesthetic Fit ✨"
    ) -> dict[str, Any]:
        """Creates an ultra-aesthetic 14-second complete outfit combination video."""
        if not pieces:
            raise ValueError("At least 2 outfit pieces are required to create a combination lookbook.")

        log.info("👗 [Combo Lookbook] Producing styled combination reel: '%s' (%d pieces)", lookbook_theme, len(pieces))

        # 1. Calculate Total Bundle Price & Savings
        total_price = 0
        total_mrp = 0
        for p in pieces:
            price_val = int(re.sub(r'[^0-9]', '', str(p.get("price", "399"))) or "399")
            mrp_val = int(re.sub(r'[^0-9]', '', str(p.get("mrp", "1299"))) or str(price_val * 3))
            p["price_clean"] = f"₹{price_val}"
            p["price_int"] = price_val
            p["mrp_int"] = mrp_val
            total_price += price_val
            total_mrp += mrp_val

        bundle_discount = int((1 - total_price / max(total_mrp, 1)) * 100)

        clip_files: list[Path] = []

        # 2. Render individual piece slides (3s each)
        for idx, piece in enumerate(pieces, start=1):
            role = piece.get("role", f"Piece #{idx}")
            title = piece.get("title", "Aesthetic Piece")
            img_path = Path(piece["image"])

            frame = self._render_piece_slide(
                piece=piece,
                img_path=img_path,
                step_idx=idx,
                total_steps=len(pieces),
                theme=lookbook_theme
            )

            clip_mp4 = self.output_dir / f"clip_step_{idx}.mp4"
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1", "-i", str(frame),
                "-t", "3",
                "-vf", "scale=1080:1920,fps=60",
                "-c:v", "libx264", "-pix_fmt", "yuv420p",
                str(clip_mp4)
            ]
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            clip_files.append(clip_mp4)

        # 3. Render Master Styled Flatlay Moodboard Finale (5s)
        board_frame = self._render_master_flatlay_board(
            pieces=pieces,
            total_price=total_price,
            total_mrp=total_mrp,
            bundle_discount=bundle_discount,
            theme=lookbook_theme
        )
        board_mp4 = self.output_dir / "clip_master_board.mp4"
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1", "-i", str(board_frame),
            "-t", "5",
            "-vf", "scale=1080:1920,fps=60",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            str(board_mp4)
        ]
        subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        clip_files.append(board_mp4)

        # 4. Concatenate & Clean
        concat_txt = self.output_dir / "combo_concat.txt"
        with open(concat_txt, "w", encoding="utf-8") as f:
            for c in clip_files:
                f.write(f"file '{c.resolve().as_posix()}'\n")

        slug = re.sub(r'[^a-zA-Z0-9]', '_', lookbook_theme[:16]).lower()
        merged_raw = self.output_dir / f"RAW_COMBO_{slug.upper()}.mp4"

        cmd_concat = [
            "ffmpeg", "-y",
            "-f", "concat", "-safe", "0",
            "-i", str(concat_txt),
            "-c", "copy",
            str(merged_raw)
        ]
        subprocess.run(cmd_concat, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

        final_video = self.cleaner.clean_video(merged_raw)

        # 5. Build High-Converting Wishlink Multi-Bundle Caption
        pieces_breakdown = "\n".join([f"✨ {p.get('role', 'Item')}: {p.get('title')} • {p.get('price_clean')}" for p in pieces])
        caption = (
            f"🔥 FULL {lookbook_theme.upper()} UNDER ₹{total_price + 100}!\n\n"
            f"{pieces_breakdown}\n"
            f"━━━━━━━━━━━━━━━━━━━\n"
            f"💰 TOTAL OUTFIT: ONLY ₹{total_price} (MRP ₹{total_mrp} - {bundle_discount}% OFF!)\n\n"
            f"👇 Comment 'OUTFIT' below & I'll DM you the direct Wishlink collection for all 3 items!\n"
            f"🔗 Collection link also in Bio!\n\n"
            f"#outfitinspo #y2kfits #meeshohaul #pinterestfashion #affordablefits #under1000 #stylingvideo #lookbook"
        )

        log.info("🎉 Complete Lookbook Combo Reel Ready: %s", final_video)
        return {
            "status": "success",
            "theme": lookbook_theme,
            "total_price": f"₹{total_price}",
            "bundle_discount": f"{bundle_discount}% OFF",
            "video_path": str(final_video),
            "caption": caption
        }

    def _render_piece_slide(
        self,
        piece: dict[str, Any],
        img_path: Path,
        step_idx: int,
        total_steps: int,
        theme: str
    ) -> Path:
        """Renders 1080x1920 luxury styling piece spotlight slide."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (16, 14, 18, 255))
        draw = ImageDraw.Draw(canvas)

        # Editorial warm gradient
        for y in range(0, h, 6):
            ratio = y / h
            r = int(90 - 20 * ratio)
            g = int(85 - 18 * ratio)
            b = int(100 - 15 * ratio)
            draw.rectangle([0, y, w, y + 6], fill=(r, g, b, 255))

        # Main Real Product Showcase
        try:
            raw_img = Image.open(img_path).convert("RGBA")
            tw, th = 880, 1050
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

            draw.rounded_rectangle([96, 426, 96 + tw + 8, 426 + th + 8], radius=32, fill=(0, 0, 0, 140))
            canvas.paste(raw_img, (100, 430), mask)
            draw.rounded_rectangle([100, 430, 100 + tw, 430 + th], radius=28, outline=(255, 255, 255, 220), width=3)
        except Exception as e:
            log.warning("Piece render notice: %s", e)

        # Step Pill (e.g. 'STEP 1: THE BASE TOP')
        draw.rounded_rectangle([260, 130, 820, 200], radius=18, fill=(244, 63, 94, 255))
        role_label = piece.get("role", f"STEP #{step_idx}").upper()
        draw.text((540, 165), f"✨ {role_label}", fill=(255, 255, 255, 255), font=_get_font(28, bold=True), anchor="mm")

        # Piece Title
        font_t = _get_font(48, bold=True)
        draw.text((542, 272), piece.get("title", ""), fill=(0, 0, 0, 220), font=font_t, anchor="mm")
        draw.text((540, 270), piece.get("title", ""), fill=(255, 255, 255, 255), font=font_t, anchor="mm")

        # Step Counter Pill
        draw.rounded_rectangle([390, 330, 690, 385], radius=16, fill=(25, 20, 30, 220), outline=(255, 255, 255, 140), width=2)
        draw.text((540, 357), f"PIECE {step_idx} OF {total_steps}", fill=(240, 230, 245, 255), font=_get_font(22, bold=True), anchor="mm")

        # Bottom Price Card
        draw.rounded_rectangle([100, 1550, 980, 1750], radius=24, fill=(15, 12, 18, 235), outline=(255, 255, 255, 180), width=2)
        draw.text((540, 1610), f"💰 ONLY {piece.get('price_clean', '₹399')} ON MEESHO", fill=(255, 230, 100, 255), font=_get_font(34, bold=True), anchor="mm")
        draw.text((540, 1680), f"🧵 {piece.get('detail', 'Aesthetic verified styling piece')}", fill=(220, 215, 230, 255), font=_get_font(22), anchor="mm")

        out_f = self.output_dir / f"step_frame_{step_idx}.png"
        canvas.convert("RGB").save(out_f, format="PNG", quality=95)
        return out_f

    def _render_master_flatlay_board(
        self,
        pieces: list[dict[str, Any]],
        total_price: int,
        total_mrp: int,
        bundle_discount: int,
        theme: str
    ) -> Path:
        """Renders the master Pinterest aesthetic moodboard styling all 3 pieces together."""
        w, h = 1080, 1920
        canvas = Image.new("RGBA", (w, h), (14, 12, 16, 255))
        draw = ImageDraw.Draw(canvas)

        # Luxury aesthetic header
        draw.rounded_rectangle([100, 120, 980, 240], radius=24, fill=(244, 63, 94, 255))
        draw.text((540, 180), "✨ COMPLETE CURATED OUTFIT ✨", fill=(255, 255, 255, 255), font=_get_font(38, bold=True), anchor="mm")

        # Styled Grid of the 3 Pieces (Editorial Collage Layout)
        # Top half: 2 vertical cards (Top + Sweater)
        # Bottom half: 1 horizontal banner card (Chunky Rings / Accessories)
        p1 = pieces[0] if len(pieces) > 0 else {}
        p2 = pieces[1] if len(pieces) > 1 else {}
        p3 = pieces[2] if len(pieces) > 2 else {}

        # Piece 1: Left Card (e.g. Baby Tee)
        card1_w, card1_h = 420, 560
        self._paste_flatlay_thumb(canvas, draw, Path(p1.get("image", "")), 100, 290, card1_w, card1_h, p1.get("role", "Base Top"), p1.get("price_clean", ""))

        # Piece 2: Right Card (e.g. Flame Sweater)
        self._paste_flatlay_thumb(canvas, draw, Path(p2.get("image", "")), 560, 290, card1_w, card1_h, p2.get("role", "Layer"), p2.get("price_clean", ""))

        # Piece 3: Center Bottom Card (e.g. Chunky Rings)
        card3_w, card3_h = 880, 400
        self._paste_flatlay_thumb(canvas, draw, Path(p3.get("image", "")), 100, 890, card3_w, card3_h, p3.get("role", "Accessories / Rings"), p3.get("price_clean", ""))

        # Huge Finale Total Deal Card
        draw.rounded_rectangle([100, 1340, 980, 1780], radius=32, fill=(24, 20, 28, 255), outline=(244, 63, 94, 255), width=3)

        draw.text((540, 1420), "TOTAL OUTFIT PRICE", fill=(200, 190, 210, 255), font=_get_font(26, bold=True), anchor="mm")
        draw.text((540, 1500), f"🔥 ONLY ₹{total_price}", fill=(255, 230, 100, 255), font=_get_font(64, bold=True), anchor="mm")
        draw.text((540, 1580), f"(MRP ₹{total_mrp} • Save {bundle_discount}% OFF!)", fill=(180, 175, 195, 255), font=_get_font(24), anchor="mm")

        # Animated DM Call To Action
        draw.rounded_rectangle([180, 1630, 900, 1720], radius=20, fill=(244, 63, 94, 255))
        draw.text((540, 1675), "👇 Comment 'OUTFIT' for All 3 Links! 💌", fill=(255, 255, 255, 255), font=_get_font(28, bold=True), anchor="mm")

        out_f = self.output_dir / "master_flatlay_board.png"
        canvas.convert("RGB").save(out_f, format="PNG", quality=95)
        return out_f

    def _paste_flatlay_thumb(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        img_path: Path,
        x: int,
        y: int,
        w: int,
        h: int,
        label: str,
        price: str
    ):
        """Helper to crop and paste an aesthetic thumbnail onto the flatlay moodboard."""
        if not img_path.exists():
            return
        try:
            raw = Image.open(img_path).convert("RGBA")
            aspect = w / h
            img_aspect = raw.width / raw.height
            if img_aspect > aspect:
                nw = int(raw.height * aspect)
                left = (raw.width - nw) // 2
                raw = raw.crop((left, 0, left + nw, raw.height))
            else:
                nh = int(raw.width / aspect)
                top = (raw.height - nh) // 2
                raw = raw.crop((0, top, raw.width, top + nh))

            raw = raw.resize((w, h), Image.Resampling.LANCZOS)
            mask = Image.new("L", (w, h), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=20, fill=255)

            canvas.paste(raw, (x, y), mask)
            draw.rounded_rectangle([x, y, x + w, y + h], radius=20, outline=(255, 255, 255, 200), width=2)

            # Price Tag Pill on Thumbnail
            pill_h = 44
            draw.rounded_rectangle([x + 10, y + h - pill_h - 10, x + w - 10, y + h - 10], radius=12, fill=(0, 0, 0, 220))
            draw.text((x + w // 2, y + h - pill_h // 2 - 10), f"{label}: {price}", fill=(255, 255, 255, 255), font=_get_font(20, bold=True), anchor="mm")
        except Exception as e:
            log.warning("Flatlay thumb notice: %s", e)


if __name__ == "__main__":
    studio = AestheticComboLookbookStudio()
    # Build complete aesthetic combo from screenshot items!
    outfit_pieces = [
        {
            "role": "Step 1: The Base Top",
            "title": "Y2K Contrast Raglan Baby Tee",
            "price": "₹187",
            "mrp": "₹699",
            "detail": "Mocha & Black Contrast Sleeves • 95% Soft Ribbed Cotton",
            "image": "data/scraped_products/meesho_raglan_baby_tee.jpg"
        },
        {
            "role": "Step 2: Layering Piece",
            "title": "Flame Hem Oversized Sweater",
            "price": "₹577",
            "mrp": "₹1,499",
            "detail": "Lavender Purple • White Jacquard Flame Weave Knit",
            "image": "data/scraped_products/meesho_flame_sweater_purple.jpg"
        },
        {
            "role": "Step 3: The Jewelry",
            "title": "Vintage Chunky Rings Set",
            "price": "₹117",
            "mrp": "₹499",
            "detail": "Set of 5 Bohemian Silver & Turquoise Statement Rings",
            "image": "data/scraped_products/meesho_chunky_rings.jpg"
        }
    ]

    res = studio.produce_complete_lookbook(
        pieces=outfit_pieces,
        lookbook_theme="Pinterest Y2K Aesthetic Fit ✨"
    )
    print("\n🎉 Complete Combination Lookbook Generated Successfully!")
    print("  • Total Look Price:", res["total_price"])
    print("  • Bundle Discount:", res["bundle_discount"])
    print("  • Video Path:", res["video_path"])
    print("  • Caption:\n", res["caption"])
