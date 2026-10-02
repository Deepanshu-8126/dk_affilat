#!/usr/bin/env python3
"""
Zero-Input Autonomous Gen Z & Pinterest Aesthetic Unboxer.
No URLs or keywords required!
1-Click Command:
  python run_autonomous_unboxer.py
"""
from __future__ import annotations

import json
from connectors.genz_pinterest_unboxer import GenZUnboxingStudio


def main():
    print("🌸 [GenZ Unboxing Studio] Auto-Discovering Viral Aesthetic Trends (No URL needed)...")
    studio = GenZUnboxingStudio()
    result = studio.produce_unboxing_production()

    print("\n🎉 [Production Complete!]")
    print(f"  • Product: {result['product_name']}")
    print(f"  • Niche: {result['niche']}")
    print(f"  • Unboxing Reel: {result['video_reel']}")
    print(f"  • Pinterest Card: {result['cover_card']}")
    print(f"\n🎥 [Hyper-Realistic Veo UGC Prompt]:\n{result['ugc_veo_prompt']}")
    print(f"\n📱 [Viral Caption Ready]:\n{result['caption']}")


if __name__ == "__main__":
    main()
