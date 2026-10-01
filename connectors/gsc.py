"""
Google Search Console analytics reader (feedback loop input).

Full OAuth/service-account wiring is left as a config step; this module provides
the interface and a deterministic sample generator so the learning loop
(core.state.record_performance) can be exercised immediately.
"""
from __future__ import annotations

import hashlib
import os

from core.logging_utils import get_logger

log = get_logger("gsc")


def fetch_performance(site_url: str, days: int = 28) -> list[dict]:
    """
    Return rows: [{'query','page','clicks','impressions','ctr','position'}, ...]

    Wire the real GSC Search Analytics API here (searchconsole.googleapis.com,
    v1 searchanalytics.query) using a service account JSON in GSC_CREDENTIALS.
    Until then, returns deterministic sample rows for the learning loop demo.
    """
    if os.getenv("GSC_CREDENTIALS"):
        # TODO: implement real searchanalytics.query call
        log.info("GSC credentials present — implement real query for %s", site_url)
    seed = int(hashlib.md5(site_url.encode()).hexdigest(), 16)
    rows = []
    samples = [
        "best ai tools 2026", "ai video editing", "wan 2.2 tutorial",
        "ai automation workflow", "copilot vs cursor",
    ]
    for i, q in enumerate(samples):
        clicks = (seed >> (i * 3)) % 120
        impr = clicks * 20 + 50
        rows.append({
            "query": q,
            "page": f"{site_url}/{q.replace(' ', '-')}/",
            "clicks": clicks,
            "impressions": impr,
            "ctr": round(clicks / impr, 4) if impr else 0.0,
            "position": round(3 + (seed >> i) % 25, 1),
        })
    return rows
