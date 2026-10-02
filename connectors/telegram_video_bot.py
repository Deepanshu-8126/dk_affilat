"""
n8n-Grade Autonomous Telegram Video Dispatcher & Phone Controller.
Allows user to control the entire video production pipeline directly from their Phone via Telegram:
1. User sends any Meesho product link or name -> Bot scrapes & creates 1080x1920 60fps clean video -> sends it back to phone!
2. Supports /video <product>, /haul <title>, /trending (picks 12-18% high-commission viral deals)
3. True multipart binary video file upload directly to Telegram chat.
"""
from __future__ import annotations

import io
import json
import mimetypes
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

# Ensure root in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger

log = get_logger("telegram_bot")


def _load_env_telegram() -> tuple[str, str]:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").split("#")[0].strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").split("#")[0].strip()
    if token and chat_id:
        return token, chat_id
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TELEGRAM_BOT_TOKEN=") and not line.startswith("#"):
                token = line.split("=", 1)[1].split("#")[0].strip().strip('"').strip("'")
            elif line.startswith("TELEGRAM_CHAT_ID=") and not line.startswith("#"):
                chat_id = line.split("=", 1)[1].split("#")[0].strip().strip('"').strip("'")
    return token, chat_id


class TelegramVideoBot:
    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        t, c = _load_env_telegram()
        self.bot_token = bot_token or t
        self.chat_id = chat_id or c

    def send_message(self, text: str) -> bool:
        """Sends text message to Telegram chat."""
        if not self.bot_token or not self.chat_id:
            log.warning("Telegram Bot Token or Chat ID missing.")
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = json.dumps({"chat_id": self.chat_id, "text": text, "parse_mode": "Markdown"}).encode("utf-8")
        try:
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status == 200
        except Exception as e:
            log.warning("Telegram sendMessage error: %s", e)
            return False

    def send_video_file(self, video_path: Path | str, caption: str = "") -> bool:
        """Uploads real 1080x1920 MP4 video directly to Telegram chat via multipart binary upload."""
        path = Path(video_path)
        if not path.exists():
            log.warning("Video file not found: %s", path)
            return False

        if not self.bot_token or not self.chat_id:
            log.info("Telegram not configured in .env. Video saved locally: %s", path)
            return False

        log.info("🚀 Uploading video (%d KB) to Telegram chat: %s...", path.stat().st_size // 1024, self.chat_id)

        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        body = io.BytesIO()

        # chat_id field
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(b'Content-Disposition: form-data; name="chat_id"\r\n\r\n')
        body.write(f"{self.chat_id}\r\n".encode("utf-8"))

        # supports_streaming field
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(b'Content-Disposition: form-data; name="supports_streaming"\r\n\r\n')
        body.write(b"true\r\n")

        # caption field
        if caption:
            body.write(f"--{boundary}\r\n".encode("utf-8"))
            body.write(b'Content-Disposition: form-data; name="caption"\r\n\r\n')
            body.write(f"{caption}\r\n".encode("utf-8"))

        # reply_markup field (Interactive Phone Buttons)
        reply_markup = json.dumps({
            "inline_keyboard": [
                [
                    {"text": "📸 POST TO INSTAGRAM NOW", "callback_data": "post_insta"},
                    {"text": "🛍️ OPEN STOREFRONT", "url": "https://earnkaro.com/top-selling-products"}
                ]
            ]
        })
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(b'Content-Disposition: form-data; name="reply_markup"\r\n\r\n')
        body.write(f"{reply_markup}\r\n".encode("utf-8"))

        # video file field
        body.write(f"--{boundary}\r\n".encode("utf-8"))
        body.write(f'Content-Disposition: form-data; name="video"; filename="{path.name}"\r\n'.encode("utf-8"))
        body.write(b"Content-Type: video/mp4\r\n\r\n")
        with open(path, "rb") as f:
            body.write(f.read())
        body.write(b"\r\n")

        body.write(f"--{boundary}--\r\n".encode("utf-8"))
        content_bytes = body.getvalue()

        url = f"https://api.telegram.org/bot{self.bot_token}/sendVideo"
        req = urllib.request.Request(
            url,
            data=content_bytes,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(content_bytes))
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                if res_data.get("ok"):
                    log.info("✅ Video successfully delivered to Telegram chat!")
                    return True
                else:
                    log.warning("Telegram API rejected video: %s", res_data)
                    return False
        except Exception as e:
            log.warning("Telegram video upload failed: %s", e)
            return False

    def start_polling_loop(self):
        """Listens for commands from the user's phone on Telegram."""
        if not self.bot_token:
            log.error("Cannot poll: TELEGRAM_BOT_TOKEN is empty in .env.")
            return

        log.info("🤖 Telegram Video Bot is now ONLINE and listening for commands from your phone...")
        print("\n📱 [Telegram Phone Controller Active!]")
        print("  • Send any Meesho link: https://www.meesho.com/...")
        print("  • Or type: /video <product name>")
        print("  • Or type: /haul <category>")
        print("  • Or type: /trending (auto-picks highest commission deals)\n")

        last_update_id = 0
        while True:
            try:
                poll_url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates?offset={last_update_id + 1}&timeout=25"
                with urllib.request.urlopen(poll_url, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))

                for update in data.get("result", []):
                    last_update_id = update["update_id"]
                    msg = update.get("message", {})
                    text = msg.get("text", "").strip()
                    chat_id = msg.get("chat", {}).get("id")

                    if not text or not chat_id:
                        continue

                    # Set active chat id
                    self.chat_id = str(chat_id)
                    log.info("Received command from phone: '%s'", text)

                    self.send_message(f"⏳ *Processing request from your phone:* `{text}`\n\nCreating EarnKaro 1-Wallet Link + 1080x1920 60fps Voiced Reel + Updating Storefront...")

                    # Process request via MultiStoreAffiliateAutomator
                    from connectors.multi_store_affiliate_automator import MultiStoreAffiliateAutomator
                    automator = MultiStoreAffiliateAutomator()

                    # Handle Meesho Affiliate Collection URLs (affiliate.meesho.com/collection/...)
                    if "affiliate.meesho.com/collection/" in low_text or "meesho.com/collection/" in low_text:
                        from connectors.meesho_affiliate_collection_parser import MeeshoAffiliateCollectionParser
                        self.send_message(f"🔍 *Detected Meesho Affiliate Collection!*\nParsing products & direct affiliate tracking links...")
                        collection_items = MeeshoAffiliateCollectionParser.fetch_collection_products(text)
                        
                        if not collection_items:
                            self.send_message("⚠️ Could not extract products from Meesho collection link. Please check if collection link is public.")
                            continue

                        self.send_message(f"✨ *Found {len(collection_items)} curated products in collection!*\nGenerating 60fps Veo AI Reels & Storefront listings...")
                        for idx, item in enumerate(collection_items, 1):
                            self.send_message(f"🎬 Processing Product {idx}/{len(collection_items)}: `{item['title']}` (₹{item['price']})...")
                            automator.process_product(
                                product_name=item["title"],
                                store_name="Meesho",
                                raw_product_url=item["affiliate_link"],
                                original_price=item["mrp"],
                                deal_price=item["price"],
                                category="Meesho Collection Find",
                                image_path=item["main_image"]
                            )
                        log.info("✅ Finished processing all %d collection items!", len(collection_items))
                        continue

                    # Detect store from link or text
                    if "myntra.com" in low_text or "/myntra" in low_text:
                        store_name = "Myntra"
                    elif "ajio.com" in low_text or "/ajio" in low_text:
                        store_name = "Ajio"
                    elif "flipkart.com" in low_text or "/flipkart" in low_text:
                        store_name = "Flipkart"
                    elif "shopsy.in" in low_text or "/shopsy" in low_text:
                        store_name = "Shopsy"
                    elif "nykaa.com" in low_text or "/nykaa" in low_text:
                        store_name = "Nykaa"
                    else:
                        store_name = "Meesho"

                    clean_title = text.replace("/video", "").replace("/myntra", "").replace("/ajio", "").replace("/meesho", "").strip()
                    if not clean_title:
                        clean_title = "Trending Aesthetic GenZ Outfit Find"

                    res = automator.process_product(
                        product_name=clean_title[:40],
                        store_name=store_name,
                        raw_product_url=text if text.startswith("http") else f"https://www.{store_name.lower()}.com",
                        original_price=1999.0,
                        deal_price=699.0,
                        category="GenZ Aesthetic Fashion"
                    )

                    log.info("✅ Telegram auto-processed item for: %s", clean_title)


            except Exception as e:
                log.warning("Telegram polling iteration notice: %s", e)
                time.sleep(3)


if __name__ == "__main__":
    bot = TelegramVideoBot()
    if bot.bot_token:
        bot.start_polling_loop()
    else:
        print("Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env")
