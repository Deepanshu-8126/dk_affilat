#!/usr/bin/env python3
"""
Single-Command Launcher for FireCrawler + Google Veo + Telegram Automation Suite.
Usage:
  1. Generate direct video:
     python run_veo_telegram.py "Meesho viral thermal printer"
     python run_veo_telegram.py "https://meesho.com/p/some-viral-product"

  2. Run 24/7 Telegram Listener (Send commands from your phone):
     python run_veo_telegram.py --listen
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from connectors.telegram_video_bot import TelegramVideoBot


def main():
    parser = argparse.ArgumentParser(description="FireCrawler + Google Veo + Telegram AI Video Suite")
    parser.add_argument("query_or_url", nargs="?", default="Meesho viral thermal printer", help="Product URL or search query")
    parser.add_argument("--listen", action="store_true", help="Start continuous 24/7 Telegram Listener")

    args = parser.parse_args()
    bot = TelegramVideoBot()

    if args.listen:
        print("🤖 [Telegram Listener Active] Send /video <product> on Telegram to auto-generate videos 24/7...")
    else:
        target = args.query_or_url.strip()
        print(f"🎬 [Starting Pipeline] Scrape '{target}' ➔ Google Veo ➔ Render MP4 ➔ Telegram...")
        res = bot.process_video_request(target)
        print("\n✅ [Finished!]")
        print(f"  • Product: {res['product']}")
        print(f"  • Video Output: {res['video_path']}")
        print(f"  • Veo Prompt: {res['veo_prompt']}")


if __name__ == "__main__":
    main()
