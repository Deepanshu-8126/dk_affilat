"""
OPENMONTAGE bridge — reuse the useful *logic* from calesthio/OpenMontage for SEO.

We don't run a video studio here. We borrow two ideas that make our written
content rank better and open a second (video) search channel — for FREE:

  1. DEEP RESEARCH FAN-OUT
     OpenMontage does 15-25 live web searches before it produces anything. That
     "research first, across many angles" pattern is exactly what strong SEO
     content needs. `research_query_plan()` fans a topic out into buyer,
     comparison, how-to, freshness, complaint and question angles, and
     `deep_research_urls()` turns that into extra candidate sources for the
     scraper — wider, more authoritative briefs.

  2. VIDEO-FOR-SEO REPURPOSE
     YouTube is the world's 2nd-largest search engine and an embedded video
     lifts on-page dwell time (a ranking signal). `video_seo_pack()` turns any
     finished post into: a YouTube title/description/tags/chapters, a Shorts
     hook, a VideoObject JSON-LD block (for video rich results), and an
     OpenMontage-compatible pipeline manifest so the clip can be rendered later
     with the free stack (Piper TTS + FFmpeg + Remotion) at ₹0.

Everything degrades gracefully: no network, no OpenMontage install -> still
returns useful deterministic output so the pipeline never breaks.
"""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from core.logging_utils import get_logger

log = get_logger("openmontage")

# Reference to the upstream project (kept for docs / manifests).
UPSTREAM = "https://github.com/calesthio/OpenMontage"


# ---------------------------------------------------------------------------
# 1) DEEP RESEARCH FAN-OUT  (OpenMontage "research first, many angles" logic)
# ---------------------------------------------------------------------------
# Each angle is a query template. {kw} = primary keyword. These mirror the way
# a research agent probes a topic from every commercially useful direction.
_RESEARCH_ANGLES: list[tuple[str, str]] = [
    ("definition",   "what is {kw}"),
    ("best",         "best {kw}"),
    ("comparison",   "{kw} vs alternatives"),
    ("how_to",       "how to use {kw}"),
    ("review",       "{kw} review pros and cons"),
    ("pricing",      "{kw} price cost worth it"),
    ("latest",       "{kw} 2026 latest update"),
    ("complaints",   "{kw} problems complaints reddit"),
    ("alternatives", "{kw} alternatives"),
    ("questions",    "{kw} faq questions"),
    ("statistics",   "{kw} statistics data"),
    ("examples",     "{kw} examples"),
]


@dataclass
class ResearchPlan:
    primary: str
    queries: list[str] = field(default_factory=list)
    angles: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {"primary": self.primary, "queries": self.queries,
                "angles": self.angles}


def research_query_plan(topic_title: str, keywords: list[str] | None = None,
                        *, n: int = 8) -> ResearchPlan:
    """Fan a topic out into `n` distinct, high-value research queries."""
    keywords = keywords or []
    primary = (keywords[0] if keywords else topic_title).strip()
    queries: list[str] = []
    angles: list[str] = []

    for angle, tpl in _RESEARCH_ANGLES:
        if len(queries) >= n:
            break
        q = tpl.format(kw=primary)
        queries.append(q)
        angles.append(angle)

    # Mix in the extra seed keywords verbatim (real long-tails from trend step).
    for kw in keywords[1:]:
        if len(queries) >= n:
            break
        if kw and kw.lower() != primary.lower():
            queries.append(kw)
            angles.append("seed")

    log.info("research plan | primary='%s' | %d queries across %d angles",
             primary, len(queries), len(set(angles)))
    return ResearchPlan(primary=primary, queries=queries[:n], angles=angles[:n])


def deep_research_urls(topic_title: str, keywords: list[str] | None = None,
                       *, n: int = 8) -> list[str]:
    """Turn the research plan into candidate search-result URLs to scrape."""
    plan = research_query_plan(topic_title, keywords, n=n)
    urls = []
    for q in plan.queries:
        urls.append(f"https://duckduckgo.com/html/?q={q.replace(' ', '+')}")
    return urls


# ---------------------------------------------------------------------------
# 2) VIDEO-FOR-SEO REPURPOSE  (OpenMontage pipeline manifest + video schema)
# ---------------------------------------------------------------------------
@dataclass
class VideoSeoPack:
    yt_title: str
    yt_description: str
    yt_tags: list[str]
    chapters: list[dict]           # [{"time": "00:00", "label": "..."}]
    shorts_hook: str
    thumbnail_text: str
    video_object: dict             # VideoObject JSON-LD (for the blog page)
    manifest: str                  # OpenMontage-compatible YAML brief
    renderable: bool               # is a local OpenMontage install present?

    def to_dict(self) -> dict:
        return {
            "yt_title": self.yt_title,
            "yt_description": self.yt_description,
            "yt_tags": self.yt_tags,
            "chapters": self.chapters,
            "shorts_hook": self.shorts_hook,
            "thumbnail_text": self.thumbnail_text,
            "video_object": self.video_object,
            "renderable": self.renderable,
        }


def is_available() -> bool:
    """True if a local OpenMontage checkout is configured (OPENMONTAGE_DIR)."""
    d = os.getenv("OPENMONTAGE_DIR")
    return bool(d and Path(d).expanduser().is_dir())


def _clip(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _chapters_from_outline(outline: list[str]) -> list[dict]:
    """Even, deterministic chapter timestamps from the article's H2 outline."""
    outline = [o for o in (outline or []) if o][:8] or ["Introduction"]
    step = max(20, 480 // max(1, len(outline)))  # ~fit inside ~8 min
    chapters = []
    for i, label in enumerate(outline):
        secs = i * step
        chapters.append({"time": f"{secs // 60:02d}:{secs % 60:02d}",
                         "label": _clip(label, 60)})
    return chapters


def video_seo_pack(title: str, primary_keyword: str,
                   secondary_keywords: list[str] | None = None,
                   outline: list[str] | None = None,
                   *, page_url: str = "", author: str = "",
                   duration_s: int = 480, length: str = "long") -> VideoSeoPack:
    """Build all video-SEO artefacts for one article (long-form or shorts)."""
    secondary_keywords = secondary_keywords or []
    outline = outline or []
    kw = primary_keyword or title

    yt_title = _clip(f"{title} ({'#Shorts' if length == 'shorts' else '2026 Guide'})", 100)
    chapters = _chapters_from_outline(outline)
    chapter_lines = "\n".join(f"{c['time']} {c['label']}" for c in chapters)
    desc = (
        f"{_clip(title, 120)}\n\n"
        f"In this video we break down {kw} — what matters, how it works, and how "
        f"to choose. Full written guide: {page_url or '(link in description)'}\n\n"
        f"⏱️ Chapters:\n{chapter_lines}\n\n"
        f"#"
        + " #".join((kw.split() + secondary_keywords[:4]))
    )
    tags = list(dict.fromkeys(
        [kw] + secondary_keywords[:8]
        + [f"{kw} 2026", f"best {kw}", f"{kw} review", f"how to {kw}"]))[:15]

    shorts_hook = _clip(
        f"Stop scrolling — here's what nobody tells you about {kw}.", 90)
    thumbnail_text = _clip(kw.upper() if len(kw) <= 22 else kw.title(), 24)

    video_object = {
        "@context": "https://schema.org",
        "@type": "VideoObject",
        "name": _clip(title, 110),
        "description": _clip(desc, 300),
        "thumbnailUrl": (page_url.rstrip("/") + "/thumb.jpg") if page_url else "",
        "uploadDate": "",  # filled at publish time
        "duration": f"PT{duration_s // 60}M{duration_s % 60}S",
        "contentUrl": "",
        "embedUrl": "",
        "publisher": {"@type": "Organization", "name": author or "Editorial team"},
    }

    manifest = _openmontage_manifest(
        title=title, kw=kw, outline=outline, page_url=page_url,
        length=length, author=author)

    return VideoSeoPack(
        yt_title=yt_title, yt_description=desc, yt_tags=tags,
        chapters=chapters, shorts_hook=shorts_hook,
        thumbnail_text=thumbnail_text, video_object=video_object,
        manifest=manifest, renderable=is_available())


def _openmontage_manifest(*, title: str, kw: str, outline: list[str],
                          page_url: str, length: str, author: str) -> str:
    """Emit a YAML brief OpenMontage's agent can consume to render the video.

    Uses the FREE provider path (Piper TTS + FFmpeg + Remotion) so cost = ₹0.
    See {UPSTREAM} for the pipeline/skill contract.
    """
    pipeline = "shorts" if length == "shorts" else "animated_explainer"
    scenes = "\n".join(
        f"    - beat: {_clip(sec, 70)!r}" for sec in (outline or [title])[:8])
    return (
        f"# OpenMontage brief — auto-generated for SEO repurpose\n"
        f"# upstream: {UPSTREAM}  (free stack: Piper TTS + FFmpeg + Remotion)\n"
        f"pipeline: {pipeline}\n"
        f"budget_usd: 0            # free providers only\n"
        f"tts: piper               # offline, no API key\n"
        f"topic: {title!r}\n"
        f"primary_keyword: {kw!r}\n"
        f"target_platform: {'shorts' if length == 'shorts' else 'youtube'}\n"
        f"cta_url: {page_url or '(blog url)'!r}\n"
        f"narrator: {author or 'Editorial'!r}\n"
        f"scenes:\n{scenes or '    - beat: Introduction'}\n"
    )


def save_video_brief(pack: VideoSeoPack, slug: str,
                     out_dir: str = "data/video_briefs") -> dict:
    """Persist the manifest + SEO pack so a clip can be rendered on demand."""
    d = Path(out_dir)
    d.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r"[^a-z0-9-]+", "-", (slug or "video").lower()).strip("-") or "video"
    manifest_path = d / f"{slug}.openmontage.yaml"
    pack_path = d / f"{slug}.videoseo.json"
    manifest_path.write_text(pack.manifest, encoding="utf-8")
    pack_path.write_text(json.dumps(pack.to_dict(), indent=2), encoding="utf-8")
    log.info("video brief saved | %s (renderable=%s)", manifest_path, pack.renderable)
    return {"manifest": str(manifest_path), "seo_pack": str(pack_path),
            "renderable": pack.renderable}
