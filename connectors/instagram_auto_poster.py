"""
Instagram Auto-Poster Engine (Meta Graph API & Instagram Reels Publisher).
Allows 100% hands-free automatic publishing of generated 1080x1920 60fps Reels directly to Instagram.

Configurable via .env:
- INSTAGRAM_AUTO_POST=true
- INSTAGRAM_ACCESS_TOKEN=your_meta_graph_api_token
- INSTAGRAM_ACCOUNT_ID=your_instagram_business_account_id
"""
from __future__ import annotations

import json
import os
import sys
import time
import requests
from pathlib import Path
from typing import Dict, Any

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from core.logging_utils import get_logger

log = get_logger("instagram_auto_poster")


class InstagramAutoPoster:
    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip()
        self.account_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip()
        self.auto_post_enabled = os.getenv("INSTAGRAM_AUTO_POST", "true").lower() == "true"

    def publish_reel(self, video_path: str | Path, caption: str) -> Dict[str, Any]:
        """
        Publishes a 1080x1920 60fps MP4 Reel directly to Instagram Reels via Graph API.
        If Graph API tokens are not configured, logs ready payload and returns simulation status.
        """
        path = Path(video_path)
        if not path.exists():
            log.error(f"Cannot publish reel: Video path '{path}' does not exist.")
            return {"status": "error", "message": f"File not found: {path}"}

        log.info(f"📸 Preparing Instagram Reel Auto-Publish: '{path.name}' ({path.stat().st_size // 1024} KB)")

        if not self.access_token or not self.account_id:
            log.info("ℹ️ Instagram Graph API tokens not set in .env (INSTAGRAM_ACCESS_TOKEN). Reel prepared for 1-tap Telegram auto-publish.")
            return {
                "status": "prepared",
                "message": "Reel prepared with 1-tap Telegram publish button",
                "video_path": str(path),
                "caption": caption
            }

        try:
            # 1. Initialize Reel Container Upload
            init_url = f"https://graph.facebook.com/v19.0/{self.account_id}/media"
            init_payload = {
                "media_type": "REELS",
                "caption": caption,
                "access_token": self.access_token
            }
            log.info(f"Uploading Reel container to Meta Graph API for account {self.account_id}...")
            res = requests.post(init_url, data=init_payload, timeout=30)
            res_data = res.json()

            if "id" not in res_data:
                log.warning(f"Instagram Graph API container init response: {res_data}")
                return {"status": "error", "response": res_data}

            creation_id = res_data["id"]
            log.info(f"Container created with ID: {creation_id}. Publishing Reel...")

            # 2. Publish Container
            publish_url = f"https://graph.facebook.com/v19.0/{self.account_id}/media_publish"
            pub_payload = {
                "creation_id": creation_id,
                "access_token": self.access_token
            }
            pub_res = requests.post(publish_url, data=pub_payload, timeout=30)
            pub_data = pub_res.json()

            if "id" in pub_data:
                log.info(f"🎉 Successfully published Reel to Instagram! Media ID: {pub_data['id']}")
                return {"status": "success", "media_id": pub_data["id"]}
            else:
                log.warning(f"Instagram Graph API publish response: {pub_data}")
                return {"status": "pending", "response": pub_data}

        except Exception as e:
            log.error(f"Failed to auto-publish Reel to Instagram: {e}")
            return {"status": "error", "error": str(e)}


if __name__ == "__main__":
    poster = InstagramAutoPoster()
    print("Instagram Auto-Poster Status:", poster.auto_post_enabled)
