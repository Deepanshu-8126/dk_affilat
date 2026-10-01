"""
STEP 2 — RESEARCH (the agent's homework).

  * Scrape top sources with Firecrawl (connectors.firecrawl).
  * Pull keyword difficulty / volume from an SEO data source (open-seo style).
  * Ask the niche brain to synthesize an angle + outline + key facts as JSON.

Produces a ResearchBrief that the writer turns into a full article.
"""
from __future__ import annotations

import json
import os

from connectors.firecrawl import scrape_many
from connectors.http import get_json
from connectors.openmontage import deep_research_urls
from core.llm import Brain
from core.logging_utils import get_logger
from core.models import ResearchBrief, SourceDoc, TrendTopic

log = get_logger("research")


def _candidate_urls(topic: TrendTopic, limit: int) -> list[str]:
    # Real evidence URLs from the trend step come first.
    urls = [e for e in topic.evidence if e.startswith("http")]
    # OpenMontage-style deep research fan-out: probe the topic from many angles
    # (buyer, comparison, how-to, freshness, complaints, questions...) so the
    # brief is built on a wide, authoritative source base — not one search.
    if len(urls) < limit:
        for u in deep_research_urls(topic.title, topic.keywords, n=limit * 2):
            if u not in urls:
                urls.append(u)
            if len(urls) >= limit:
                break
    return urls[:limit]


def _seo_metrics(keyword: str) -> dict:
    """open-seo / All-In-One-Free-SEO-Tool style lookup with fallback."""
    base = os.getenv("OPEN_SEO_URL")
    if base:
        try:
            return get_json(f"{base.rstrip('/')}/keyword?q={keyword.replace(' ', '+')}")
        except Exception as e:  # noqa: BLE001
            log.warning("open-seo lookup failed (%s)", e)
    # deterministic fallback
    diff = 15 + (sum(map(ord, keyword)) % 40)
    vol = 300 + (sum(map(ord, keyword)) % 20) * 220
    return {"difficulty": diff, "volume": vol}


def build_brief(brain: Brain, topic: TrendTopic, *, sources_limit: int = 5,
                content_types: list[str] | None = None) -> ResearchBrief:
    docs = scrape_many(_candidate_urls(topic, sources_limit), limit=sources_limit)
    log.info("scraped %d source(s) for '%s'", len(docs), topic.title)

    primary = topic.keywords[0] if topic.keywords else topic.title.lower()
    metrics = _seo_metrics(primary)

    corpus = "\n\n".join(f"[{d['title']}]\n{d['text'][:1500]}" for d in docs) or "(no sources)"
    system = ("You are a meticulous research editor. Return STRICT JSON only. "
              "No prose outside the JSON object.")
    prompt = (
        f"TOPIC: {topic.title}\n"
        f"SEED KEYWORDS: {', '.join(topic.keywords)}\n"
        f"ALLOWED CONTENT TYPES: {', '.join(content_types or ['guide'])}\n\n"
        f"SOURCE MATERIAL:\n{corpus[:6000]}\n\n"
        "Produce JSON with keys: angle (string), primary_keyword (string), "
        "secondary_keywords (array of 4-6 strings), content_type (one of the "
        "allowed types), outline (array of 6-8 H2 section titles), key_facts "
        "(array of 4-6 concrete, source-grounded facts). OUTLINE must be logical."
    )
    result = brain.complete(system, prompt, json_mode=True)
    data = _parse_json(result.text)

    brief = ResearchBrief(
        topic=topic,
        angle=data.get("angle", f"A practical breakdown of {topic.title}"),
        primary_keyword=data.get("primary_keyword", primary),
        secondary_keywords=data.get("secondary_keywords", topic.keywords[1:5]),
        keyword_difficulty=metrics.get("difficulty"),
        search_volume=metrics.get("volume"),
        outline=data.get("outline", []),
        key_facts=data.get("key_facts", []),
        sources=[SourceDoc(url=d["url"], title=d["title"], text=d["text"],
                           word_count=len(d["text"].split())) for d in docs],
        content_type=data.get("content_type",
                              (content_types or ["guide"])[0]),
    )
    log.info("brief ready | kw='%s' diff=%s vol=%s sections=%d",
             brief.primary_keyword, brief.keyword_difficulty,
             brief.search_volume, len(brief.outline))
    return brief


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        text = text[text.find("{"):] if "{" in text else text
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    log.warning("could not parse research JSON -> using defaults")
    return {}
