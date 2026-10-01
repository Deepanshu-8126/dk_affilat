"""
STEP 4 — SEO OPTIMIZE (the agent's brain).

Combines:
  * claude-seo style on-page optimisation (title tag, meta, slug, headings)
  * programmatic schema (JSON-LD Article) — pseo-ai-kit style
  * open-seo style density/readability metrics
Produces a SeoReport and updates the article's title/excerpt if better options
are found. Deterministic + one optional LLM polish for the meta description.
"""
from __future__ import annotations

import re

from core.llm import Brain
from core.logging_utils import get_logger
from core.models import Article, SeoReport

log = get_logger("seo")

_STOP = set("a an the and or but of to in on for with at by from is are was were "
            "be this that your you how what why best vs 2026".split())


def _slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:70]


def _keyword_density(text: str, keyword: str) -> float:
    words = re.findall(r"[a-zA-Z']+", text.lower())
    if not words:
        return 0.0
    kw = keyword.lower().split()
    joined = " ".join(words)
    count = joined.count(keyword.lower())
    return round((count * len(kw) / len(words)) * 100, 2)


def _flesch_reading_ease(text: str) -> float:
    sentences = max(1, len(re.findall(r"[.!?]+", text)))
    words = re.findall(r"[a-zA-Z]+", text)
    if not words:
        return 0.0
    syllables = sum(_syllables(w) for w in words)
    wc = len(words)
    score = 206.835 - 1.015 * (wc / sentences) - 84.6 * (syllables / wc)
    return round(max(0.0, min(100.0, score)), 1)


def _syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    n = len(groups)
    if word.endswith("e"):
        n = max(1, n - 1)
    return max(1, n)


def _internal_link_targets(article: Article) -> list[str]:
    """Suggest internal links from learned/seed keywords (interlink graph)."""
    seeds = []
    if article.brief:
        seeds = [article.brief.primary_keyword] + article.brief.secondary_keywords
    domain = article.meta.get("domain", "example.com")
    return [f"https://{domain}/{_slugify(s)}/" for s in seeds[:4]]


def optimize(brain: Brain, article: Article) -> SeoReport:
    body = article.body_markdown
    kw = (article.brief.primary_keyword if article.brief else "") or article.title
    slug = _slugify(article.title)

    # Title tag: <= 60 chars, keyword near front
    title_tag = article.title
    if len(title_tag) > 60:
        title_tag = title_tag[:57].rsplit(" ", 1)[0] + "…"

    # Meta description (LLM polish, deterministic fallback)
    meta = _meta_description(brain, article, kw)

    density = _keyword_density(body, kw)
    readability = _flesch_reading_ease(body)
    links = _internal_link_targets(article)

    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": article.title,
        "description": meta,
        "author": {"@type": "Person", "name": article.author_name},
        "keywords": kw,
        "articleSection": article.brief.content_type if article.brief else "guide",
        "inLanguage": "en",
    }

    # --- scoring (claude-seo inspired weighting) ---------------------------
    issues: list[str] = []
    score = 0.0
    # title
    if kw.lower() in title_tag.lower():
        score += 15
    else:
        issues.append("focus keyword missing from title")
    if len(title_tag) <= 60:
        score += 10
    else:
        issues.append("title tag > 60 chars")
    # meta
    if 120 <= len(meta) <= 160:
        score += 12
    else:
        issues.append("meta description not 120-160 chars")
    if kw.lower() in meta.lower():
        score += 8
    else:
        issues.append("focus keyword missing from meta")
    # density
    if 0.5 <= density <= 2.5:
        score += 15
    else:
        issues.append(f"keyword density {density}% out of 0.5-2.5 range")
    # readability
    if readability >= 55:
        score += 12
    else:
        issues.append(f"low readability ({readability})")
    # structure
    h2 = len(re.findall(r"(?m)^##\s", body))
    if h2 >= 4:
        score += 10
    else:
        issues.append(f"only {h2} H2 sections")
    if re.search(r"(?m)^\s*[-*]\s|\n\d+\.\s", body):
        score += 6
    else:
        issues.append("no lists")
    # length
    if 1500 <= article.word_count <= 2600:
        score += 12
    else:
        issues.append(f"word count {article.word_count} outside 1500-2600")

    report = SeoReport(
        score=round(min(100.0, score), 1),
        title_tag=title_tag,
        meta_description=meta,
        slug=slug,
        focus_keyword=kw,
        keyword_density=density,
        readability=readability,
        internal_links=links,
        schema_jsonld=schema,
        issues=issues,
    )
    log.info("SEO score=%.1f density=%.2f%% readability=%.1f issues=%d",
             report.score, density, readability, len(issues))
    return report


def _meta_description(brain: Brain, article: Article, kw: str) -> str:
    system = ("You write concise SEO meta descriptions. Output ONE line, "
              "120-160 characters, includes the keyword naturally, no quotes.")
    prompt = (f"TITLE: {article.title}\nKEYWORD: {kw}\n"
              f"EXCERPT: {article.excerpt or article.body_markdown[:300]}\n"
              "Write the meta description.")
    text = brain.complete(system, prompt).text.strip().splitlines()[0].strip().strip('"')
    if not (120 <= len(text) <= 160):
        # deterministic fallback
        base = f"{article.title}. A practical, up-to-date guide covering {kw}, key features, pros and cons, and a clear verdict."
        text = base[:157].rsplit(" ", 1)[0] + "…" if len(base) > 160 else base
    return text
