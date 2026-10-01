"""
GITHUB LIVE DATA source.

Pulls fast-rising GitHub repositories as a real trend/market signal. Developer
and AI trends surface on GitHub before they hit mainstream search, so this gives
the agent an early-warning radar and fresh, concrete things to write about.

Uses the public GitHub Search API (higher limits with GITHUB_TOKEN). Falls back
to a deterministic sample so the pipeline never breaks offline.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date, timedelta

from connectors.http import get_json
from core.logging_utils import get_logger

log = get_logger("github")


@dataclass
class Repo:
    name: str
    description: str
    stars: int
    url: str
    language: str = ""
    topics: list[str] | None = None


def _headers() -> dict:
    h = {"Accept": "application/vnd.github+json", "User-Agent": "trend-agent"}
    tok = os.getenv("GITHUB_TOKEN")
    if tok:
        h["Authorization"] = f"Bearer {tok}"
    return h


def trending_repos(query: str, *, days: int = 60, limit: int = 6) -> list[Repo]:
    """Recently-created repos matching `query`, ranked by stars (rising signal)."""
    since = (date.today() - timedelta(days=days)).isoformat()
    q = f"{query} created:>{since}"
    url = ("https://api.github.com/search/repositories"
           f"?q={q.replace(' ', '+')}&sort=stars&order=desc&per_page={limit}")
    try:
        data = get_json(url, headers=_headers(), timeout=20)
        items = data.get("items", [])
        out = [Repo(name=i["full_name"], description=(i.get("description") or "")[:200],
                    stars=i.get("stargazers_count", 0), url=i.get("html_url", ""),
                    language=i.get("language") or "", topics=i.get("topics", []))
               for i in items]
        if out:
            log.info("github: %d repo(s) for '%s'", len(out), query)
            return out
    except Exception as e:  # noqa: BLE001
        log.warning("github search failed for '%s' (%s) -> fallback", query, e)

    # deterministic fallback
    base = query.strip().title().replace(" ", "-") or "Trending"
    return [Repo(name=f"awesome/{base}-{i}", description=f"Trending project related to {query}",
                 stars=1000 - i * 120, url=f"https://github.com/search?q={query.replace(' ', '+')}",
                 language="Python", topics=[query.split()[0] if query.split() else "ai"])
            for i in range(min(limit, 3))]
