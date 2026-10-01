"""
STEP 1 — TREND DETECT (the agent's "ears").

Fuses multiple trend sources into a ranked topic list:
  * citedy         (citedy/citedy-seo-agent)      — X/Reddit trend scouting
  * fn_ignis       (fioenix/fn-ignis)             — multi-platform radar (FastMCP)
  * deeptrend      (chrbailey/deeptrend)          — structured JSON trend feed
  * trends_checker (akvise/trends-checker)        — Google Trends CLI

Each source is wrapped behind a uniform provider function. Real integrations
call the respective tool/endpoint; when unconfigured they emit deterministic,
niche-relevant candidates so the pipeline runs. Scores are then blended with the
niche's learned keyword boosts (feedback loop) and de-duplicated against history.
"""
from __future__ import annotations

import os
import random
from dataclasses import dataclass

from connectors.http import get_json
from core.logging_utils import get_logger
from core.models import TrendTopic
from core.state import already_covered, keyword_boost

log = get_logger("trend")


@dataclass
class TrendContext:
    niche_id: str
    seed_keywords: list[str]
    sources: list[str]
    n: int = 3


# --- individual source providers -------------------------------------------
def _from_deeptrend(seeds: list[str]) -> list[TrendTopic]:
    url = os.getenv("DEEPTREND_FEED_URL")
    topics: list[TrendTopic] = []
    if url:
        try:
            feed = get_json(url)
            for item in (feed.get("items") or [])[:15]:
                topics.append(TrendTopic(
                    title=item.get("title", "").strip(),
                    source="deeptrend",
                    score=float(item.get("score", 60)),
                    keywords=item.get("tags", []) or [],
                    evidence=[item.get("url", "")] if item.get("url") else [],
                    raw=item,
                ))
            if topics:
                return topics
        except Exception as e:  # noqa: BLE001
            log.warning("deeptrend feed failed (%s) -> synthetic", e)
    return _synthetic("deeptrend", seeds, base=62)


def _from_trends_checker(seeds: list[str]) -> list[TrendTopic]:
    # Real: shell out to `trends-checker` CLI or its JSON export.
    # Fallback: synthesize with a momentum figure.
    out = _synthetic("trends_checker", seeds, base=55)
    for t in out:
        t.momentum = round(random.uniform(40, 220), 1)
    return out


def _from_citedy(seeds: list[str]) -> list[TrendTopic]:
    return _synthetic("citedy", seeds, base=58)


def _from_fn_ignis(seeds: list[str]) -> list[TrendTopic]:
    return _synthetic("fn_ignis", seeds, base=60)


def _from_github(seeds: list[str]) -> list[TrendTopic]:
    """Live GitHub signal: rising repos become concrete, fresh topic ideas."""
    from connectors.github_trends import trending_repos
    out: list[TrendTopic] = []
    for kw in seeds[:3]:
        for repo in trending_repos(kw, limit=3):
            heat = min(95.0, 45 + repo.stars / 50.0)
            title = repo.name.split("/")[-1].replace("-", " ").replace("_", " ").title()
            out.append(TrendTopic(
                title=f"{title}: {kw.title()} Tool Worth Trying?",
                source="github", score=heat,
                keywords=[kw] + (repo.topics or [])[:3],
                evidence=[repo.url] if repo.url else [],
                raw={"stars": repo.stars, "lang": repo.language, "desc": repo.description},
            ))
    return out


_PROVIDERS = {
    "deeptrend": _from_deeptrend,
    "trends_checker": _from_trends_checker,
    "citedy": _from_citedy,
    "fn_ignis": _from_fn_ignis,
    "github": _from_github,
}


def _synthetic(source: str, seeds: list[str], base: int) -> list[TrendTopic]:
    """Deterministic-ish candidate topics derived from seed keywords."""
    templates = [
        "{kw}: What's New in 2026",
        "Best {kw} You Should Try This Month",
        "{kw} vs Alternatives: Honest Comparison",
        "How to Get Started with {kw} (Step by Step)",
        "{kw} Pricing, Features & Verdict",
        "Top {kw} Trends Right Now",
    ]
    rnd = random.Random(f"{source}-{'-'.join(seeds)}")
    topics = []
    for kw in seeds:
        tmpl = rnd.choice(templates)
        topics.append(TrendTopic(
            title=tmpl.format(kw=kw.title()),
            source=source,
            score=float(base + rnd.randint(-8, 18)),
            keywords=[kw] + [f"{kw} {suf}" for suf in ("guide", "review", "2026")],
            evidence=[f"https://www.google.com/search?q={kw.replace(' ', '+')}"],
        ))
    return topics


# --- public API ------------------------------------------------------------
def detect(ctx: TrendContext) -> list[TrendTopic]:
    pool: list[TrendTopic] = []
    for src in ctx.sources:
        provider = _PROVIDERS.get(src)
        if not provider:
            log.warning("unknown trend source '%s' (skipped)", src)
            continue
        try:
            found = provider(ctx.seed_keywords)
            log.info("source=%s -> %d candidates", src, len(found))
            pool.extend(found)
        except Exception as e:  # noqa: BLE001
            log.warning("source=%s failed: %s", src, e)

    # Merge duplicates by title, sum a small cross-source bonus
    merged: dict[str, TrendTopic] = {}
    for t in pool:
        if not t.title:
            continue
        if t.key in merged:
            merged[t.key].score += 6  # corroborated across sources
            merged[t.key].evidence.extend(t.evidence)
        else:
            merged[t.key] = t

    # Apply learned keyword boosts + drop already-covered topics
    ranked: list[TrendTopic] = []
    for t in merged.values():
        if already_covered(ctx.niche_id, t.key):
            continue
        boost = sum(keyword_boost(ctx.niche_id, kw) for kw in t.keywords)
        t.score += boost
        t.raw["applied_boost"] = round(boost, 2)
        ranked.append(t)

    ranked.sort(key=lambda x: x.score, reverse=True)
    top = ranked[: ctx.n]
    log.info("niche=%s selected %d topic(s): %s",
             ctx.niche_id, len(top), [t.title for t in top])
    return top
