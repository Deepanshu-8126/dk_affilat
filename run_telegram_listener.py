#!/usr/bin/env python3
"""
1-Click Phone Controller for Meesho / Veo AI Video Generator.
Run this script, then lock your PC or control everything from your Phone on Telegram:
- Send any Meesho URL -> Bot scrapes & sends back 1080x1920 60fps MP4 video
- Type: /video <product name>
- Type: /haul <category> (e.g. /haul sarees)
- Type: /trending (auto-picks high commission deals)
"""
from __future__ import annotations

import sys
from pathlib import Path
from connectors.telegram_video_bot import TelegramVideoBot

if __name__ == "__main__":
    bot = TelegramVideoBot()
    if not bot.bot_token:
        print("\n⚠️ [Telegram Not Configured Yet]")
        print("To control video generation from your phone:")
        print("1. Open Telegram and search @BotFather -> create bot and get Token")
        print("2. Search @userinfobot -> get your Chat ID")
        print("3. Add them in D:/affi;ate/trend-earning-system/.env:")
        print("   TELEGRAM_BOT_TOKEN=your_token")
        print("   TELEGRAM_CHAT_ID=your_chat_id\n")
    else:
        bot.start_polling_loop()
