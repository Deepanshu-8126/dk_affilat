"""
Firecrawl connector for scraping the top research sources.

Uses the Firecrawl API when FIRECRAWL_API_KEY is set; otherwise falls back to a
plain stdlib fetch + naive HTML-to-text so research still runs offline-ish.
"""
from __future__ import annotations

import os
import re
import urllib.request

from connectors.http import post_json
from core.logging_utils import get_logger

log = get_logger("firecrawl")

_API = "https://api.firecrawl.dev/v1/scrape"


def _strip_html(html: str) -> str:
    html = re.sub(r"(?is)<(script|style|nav|footer|header)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def scrape(url: str, *, max_chars: int = 6000) -> dict:
    """Return {'url','title','text'} for a single URL."""
    key = os.getenv("FIRECRAWL_API_KEY")
    if key:
        try:
            data = post_json(
                _API,
                {"url": url, "formats": ["markdown"], "onlyMainContent": True},
                headers={"Authorization": f"Bearer {key}"},
            )
            doc = data.get("data", data)
            md = doc.get("markdown") or doc.get("content") or ""
            title = (doc.get("metadata") or {}).get("title", "")
            return {"url": url, "title": title, "text": md[:max_chars]}
        except Exception as e:  # noqa: BLE001
            log.warning("firecrawl api failed for %s (%s) -> plain fetch", url, e)

    # plain fallback
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research-bot)"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            html = resp.read().decode("utf-8", "ignore")
        m = re.search(r"(?is)<title[^>]*>(.*?)</title>", html)
        title = _strip_html(m.group(1)) if m else url
        return {"url": url, "title": title, "text": _strip_html(html)[:max_chars]}
    except Exception as e:  # noqa: BLE001
        log.warning("plain fetch failed for %s (%s)", url, e)
        return {"url": url, "title": "", "text": ""}


def scrape_many(urls: list[str], *, limit: int = 5) -> list[dict]:
    out = []
    for u in urls[:limit]:
        doc = scrape(u)
        if doc["text"]:
            out.append(doc)
    return out
