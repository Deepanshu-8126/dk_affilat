#!/usr/bin/env python3
"""
1-Click Google Pro / Gemini Advanced Veo Video Generator with Reference Image Support.
Zero Extra API Cost:
- Uses your active Google Pro subscription via your logged-in Brave profile
- Gemini Multimodal Vision reads product reference image (from Meesho, Pinterest, or local upload)
- Auto-extracts exact fabric weave, color hex, embroidery, neckline, and unboxing script
- Renders 1080x1920 60fps UGC Video + Triggers Google Veo VideoFX!
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from connectors.google_pro_cookie_session import GoogleProSessionAutomator
from connectors.gemini_vision_director import GeminiVisionDirector
from connectors.ugc_fashion_unboxer import UGCFashionUnboxingStudio


def main():
    parser = argparse.ArgumentParser(description="Google Pro Cookie-Based Veo Video Generator with Reference Image")
    parser.add_argument("product_name", nargs="?", default="Meesho Floral Anarkali Printed Kurti Set", help="Product name to unbox")
    parser.add_argument("--image", "-i", default=None, help="Path to real product reference image (JPEG/PNG/WEBP)")
    parser.add_argument("--haul", default=None, help="Haul title for multi-item comparison video (e.g. 'Meesho Sweaters Haul ☕')")
    parser.add_argument("--images", default=None, help="Comma-separated image paths for multi-item haul (e.g. 'img1.jpg,img2.jpg')")
    parser.add_argument("--colorways", action="store_true", help="Generate '1 Product in Multi-Colors' Reel (+3 More / +5 More)")
    parser.add_argument("--lookbook", action="store_true", help="Generate Complete Styled Lookbook Combo (Top + Layer + Jewelry)")
    parser.add_argument("--price", default="₹577", help="Display selling price")

    args = parser.parse_args()

    # Check if Complete Lookbook Combo is requested
    if args.lookbook:
        from connectors.aesthetic_combo_lookbook_studio import AestheticComboLookbookStudio
        theme = args.product_name or "Pinterest Y2K Aesthetic Fit ✨"
        print(f"\n👗 [Combo Lookbook Studio] Styling complete outfit for: '{theme}'...")
        studio = AestheticComboLookbookStudio()
        outfit_pieces = [
            {
                "role": "Step 1: The Base Top",
                "title": "Y2K Contrast Raglan Baby Tee",
                "price": "₹187",
                "mrp": "₹699",
                "detail": "Mocha & Black Contrast Sleeves • Soft Ribbed Cotton",
                "image": "data/scraped_products/meesho_raglan_baby_tee.jpg"
            },
            {
                "role": "Step 2: Layering Piece",
                "title": "Flame Hem Oversized Sweater",
                "price": "₹577",
                "mrp": "₹1,499",
                "detail": "Lavender Purple • White Flame Weave Knit",
                "image": "data/scraped_products/meesho_flame_sweater_purple.jpg"
            },
            {
                "role": "Step 3: The Jewelry",
                "title": "Vintage Chunky Rings Set",
                "price": "₹117",
                "mrp": "₹499",
                "detail": "Set of 5 Bohemian Silver Statement Rings",
                "image": "data/scraped_products/meesho_chunky_rings.jpg"
            }
        ]
        res = studio.produce_complete_lookbook(pieces=outfit_pieces, lookbook_theme=theme)
        print("\n🎉 [Complete Combination Lookbook Ready!]")
        print(f"  • Total Look Price: {res['total_price']}")
        print(f"  • Bundle Discount: {res['bundle_discount']}")
        print(f"  • Video: {res['video_path']}")
        print(f"\n📱 [Viral Caption]:\n{res['caption']}")
        return

    # Check if Multi-Colorway mode is requested
    if args.colorways:
        from connectors.meesho_genz_colorway_engine import MeeshoGenZColorwayStudio
        base_img = args.image or "data/scraped_products/meesho_flame_sweater_purple.jpg"
        print(f"\n🎨 [Multi-Colorway Studio] Producing viral color comparison for: '{args.product_name}'...")
        studio = MeeshoGenZColorwayStudio()
        res = studio.produce_colorways_reel(base_image=base_img, product_title=args.product_name, price=args.price)
        print("\n🎉 [Multi-Colorway Reel Ready!]")
        print(f"  • Video: {res['video_path']}")
        print(f"  • Wishlink Code: {res['wishlink_code']}")
        print(f"\n📱 [Viral Caption]:\n{res['caption']}")
        return

    # Check if Multi-Item Haul mode is requested
    if args.haul:
        from connectors.multi_product_haul_studio import MultiProductHaulStudio
        haul_title = args.haul.strip()
        img_list = [p.strip() for p in args.images.split(",")] if args.images else ["data/ref_frame1.jpg", "data/ref_frame2.jpg"]
        print(f"\n🛍️ [Multi-Item Haul Studio] Producing viral haul for: '{haul_title}' ({len(img_list)} items)...")
        studio = MultiProductHaulStudio()
        res = studio.produce_multi_item_haul(img_list, haul_title=haul_title)
        print("\n🎉 [Multi-Item Haul Generated Successfully!]")
        print(f"  • Video: {res['video_path']}")
        print(f"  • Status: 100% Watermark-Free 1080x1920 60fps MP4")
        print(f"\n📱 [Engagement Caption]:\n{res['caption']}")
        return

    product = args.product_name.strip()
    image_path = args.image.strip() if args.image else None

    print(f"\n🌟 [Google Pro Veo Studio] Starting generation for: '{product}'...")
    print("  • Using your logged-in Google Pro session from Brave Browser")
    print("  • Zero API fees & 100% Free Video Generation!")

    # Check if reference image is provided
    if image_path and Path(image_path).exists():
        print(f"\n📸 [Vision Director] Analyzing Reference Image: {image_path}...")
        director = GeminiVisionDirector()
        vision_data = director.analyze_image_for_ugc(image_path, product_title=product)

        print(f"  • Detected Outfit: {vision_data.get('product_name')}")
        print(f"  • Fabric & Texture: {vision_data.get('fabric_and_color')}")
        print(f"  • Viral Headline: {vision_data.get('headline')}")
        print(f"  • Price Hook: {vision_data.get('sale_price')} ({vision_data.get('discount')})")

        prompt = vision_data.get("veo_prompt")

        # Also render UGC composite reel with the real reference image inside Try-on inset
        print("\n🎬 [UGC Studio] Rendering UGC Try-on frame with your reference image...")
        studio = UGCFashionUnboxingStudio()
        ugc_res = studio.produce_ugc_fashion_reel(image_path=image_path)
        print(f"  • UGC 60fps Video Created: {ugc_res['video_path']}")
    else:
        prompt = (
            f"Authentic 4K 60fps POV camera angle looking down at desk. "
            f"Real human hands opening delivery courier parcel, pulling out {product}, "
            f"unfolding fabric towards the daylight camera. "
            f"Picture-in-picture model wearing the {product} shown in bottom-right corner. "
            f"Aesthetic headline '{product[:20]} Unboxing ✨' on top. "
            f"No voiceover, natural ambient sound, hyper-realistic, zero watermark, 9:16 vertical."
        )

    print("\n🚀 [Google Veo Automation] Injecting detailed prompt into Google Pro session...")
    automator = GoogleProSessionAutomator()
    res = automator.extract_cookies_and_run(prompt)
    print("\n✅ [Google Pro Generation Complete!]")
    print(f"  • Cookies Saved to: {res['cookies_exported']}")
    print(f"  • Output Folder: {res['output_dir']}")
    print(f"  • Status: {res['message']}")

    # Auto-dispatch to Telegram if configured
    try:
        from connectors.telegram_video_bot import TelegramVideoBot
        tbot = TelegramVideoBot()
        if tbot.bot_token and tbot.chat_id:
            vid = res.get("video_path")
            if vid and Path(vid).exists():
                print(f"📱 [Telegram] Dispatching video directly to your phone: {tbot.chat_id}...")
                tbot.send_video_file(vid, caption=f"🎬 Video Ready: {product}\n\n👉 Wishlink/Meesho Link in Bio! ✨")
    except Exception as te:
        pass


if __name__ == "__main__":
    main()
