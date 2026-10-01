"""
IndexNow ping (Bing + Yandex) for near-instant indexing. Free.

Requires an IndexNow key hosted at https://<domain>/<key>.txt. Set INDEXNOW_KEY.
"""
from __future__ import annotations

import os

from connectors.http import post_json
from core.logging_utils import get_logger

log = get_logger("indexnow")

_ENDPOINT = "https://api.indexnow.org/indexnow"


def submit(domain: str, urls: list[str]) -> dict:
    key = os.getenv("INDEXNOW_KEY")
    dry = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
    urls = [u for u in urls if u]
    if not urls:
        return {"ok": False, "error": "no urls"}
    if dry or not key:
        log.info("[dry/unconfigured] IndexNow would ping %d url(s) for %s", len(urls), domain)
        return {"ok": True, "simulated": True, "count": len(urls)}
    payload = {
        "host": domain,
        "key": key,
        "keyLocation": f"https://{domain}/{key}.txt",
        "urlList": urls,
    }
    try:
        post_json(_ENDPOINT, payload)
        log.info("IndexNow pinged %d url(s) for %s", len(urls), domain)
        return {"ok": True, "count": len(urls)}
    except Exception as e:  # noqa: BLE001
        log.error("IndexNow failed: %s", e)
        return {"ok": False, "error": str(e)}
