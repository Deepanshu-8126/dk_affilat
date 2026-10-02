"""
WordPress REST API publisher (primary/canonical target).

Auth via Application Passwords (free, built into WP 5.6+). In DRY_RUN or when
credentials are missing, it simulates a successful publish and returns a fake URL
so the pipeline can be exercised end-to-end.
"""
from __future__ import annotations

import base64
import os

from connectors.http_client_utils import post_json
from core.logging_utils import get_logger

log = get_logger("wordpress")


class WordPressClient:
    def __init__(self, base_url: str | None, user: str | None, app_password: str | None):
        self.base_url = (base_url or "").rstrip("/")
        self.user = user
        self.app_password = app_password

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.user and self.app_password)

    def _auth_header(self) -> dict:
        token = base64.b64encode(f"{self.user}:{self.app_password}".encode()).decode()
        return {"Authorization": f"Basic {token}"}

    def create_post(self, *, title: str, content_html: str, excerpt: str,
                    slug: str, status: str = "publish",
                    tags: list[str] | None = None,
                    meta: dict | None = None,
                    domain: str | None = None) -> dict:
        dry = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
        if dry or not self.configured:
            host = _domain(self.base_url) if self.base_url else (domain or "example.com")
            fake = f"https://{host}/{slug}/"
            log.info("[dry/unconfigured] WP publish simulated -> %s", fake)
            return {"ok": True, "url": fake, "id": "dry-run", "simulated": True}
        url = f"{self.base_url}/wp-json/wp/v2/posts"
        payload = {
            "title": title,
            "content": content_html,
            "excerpt": excerpt,
            "slug": slug,
            "status": status,
        }
        if meta:
            payload["meta"] = meta
        try:
            data = post_json(url, payload, headers=self._auth_header())
            return {"ok": True, "url": data.get("link", ""), "id": data.get("id", "")}
        except Exception as e:  # noqa: BLE001
            log.error("WP publish failed: %s", e)
            return {"ok": False, "error": str(e), "url": ""}


def _domain(base_url: str) -> str:
    return base_url.replace("https://", "").replace("http://", "").split("/")[0] or "example.com"
