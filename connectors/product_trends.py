"""
PRODUCT / MARKET TREND connector.

Surfaces currently-trending PRODUCTS (not just topics) so the market engine can
recommend things people are actually buying right now. Real integrations:
  * Amazon Best Sellers / Movers & Shakers (PA-API or scrape)
  * Google Shopping / Trends rising queries
  * Product Hunt (new SaaS launches)

Configure a feed URL (PRODUCT_TREND_FEED_URL) returning JSON items, otherwise a
deterministic, niche-aware fallback keeps the engine running offline.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass

from connectors.http_client_utils import get_json
from core.logging_utils import get_logger

log = get_logger("product_trends")


@dataclass
class Product:
    title: str
    category: str = ""
    momentum: float = 0.0      # % rise / heat
    source: str = "fallback"


_FALLBACK = {
    "ai tools": ["ChatGPT Plus", "Claude Pro", "Perplexity Pro", "Jasper", "Notion AI"],
    "ai coding": ["GitHub Copilot", "Cursor", "Windsurf", "Tabnine", "Replit AI"],
    "ai automation": ["Make", "Zapier", "n8n", "Lindy", "Gumloop"],
    "ai image": ["Midjourney v7", "Google Veo 3", "Runway Gen-4", "Ideogram", "Flux"],
    "ai video": ["Google Veo 3", "Runway Gen-4", "Kling 2.0", "Pika", "Luma Dream Machine"],
    "generic": ["Trending AI tool", "Popular SaaS pick", "Best-seller gadget"],
}


def _bucket(query: str) -> str:
    q = query.lower()
    for key in _FALLBACK:
        if key != "generic" and all(w in q for w in key.split()):
            return key
    for key in _FALLBACK:
        if key != "generic" and any(w in q for w in key.split()):
            return key
    return "generic"


def trending_products(query: str, *, geo: str = "US", limit: int = 5) -> list[Product]:
    url = os.getenv("PRODUCT_TREND_FEED_URL")
    if url:
        try:
            data = get_json(f"{url}?q={query.replace(' ', '+')}&geo={geo}")
            items = data.get("items", data) if isinstance(data, dict) else data
            out = [Product(title=i.get("title", ""), category=i.get("category", ""),
                           momentum=float(i.get("momentum", 0)), source="feed")
                   for i in items[:limit] if i.get("title")]
            if out:
                return out
        except Exception as e:  # noqa: BLE001
            log.warning("product feed failed (%s) -> fallback", e)

    names = _FALLBACK[_bucket(query)]
    rnd = random.Random(query)
    return [Product(title=n, category=_bucket(query),
                    momentum=round(rnd.uniform(20, 260), 1)) for n in names[:limit]]
