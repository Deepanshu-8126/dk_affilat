"""
Typed data models that flow through the 7-step pipeline.

Every step consumes and enriches an `Article` object (plus its sub-models),
so the pipeline is just a chain of pure-ish transforms over these dataclasses.
"""
from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional


def _slug(text: str) -> str:
    keep = "".join(c.lower() if c.isalnum() else "-" for c in text)
    while "--" in keep:
        keep = keep.replace("--", "-")
    return keep.strip("-")[:80]


class Stage(str, Enum):
    TREND = "trend_detect"
    RESEARCH = "research"
    WRITE = "write"
    SEO = "seo_optimize"
    IMAGE = "image_gen"
    QC = "quality_check"
    APPROVAL = "approval"
    PUBLISH = "publish"
    DONE = "done"
    FAILED = "failed"


class ApprovalDecision(str, Enum):
    PENDING = "pending"
    APPROVE = "approve"
    REJECT = "reject"
    REWRITE = "rewrite"
    AUTO = "auto"  # auto-approved (no HITL configured)


@dataclass
class TrendTopic:
    """A single trending topic surfaced by the trend-detection layer."""
    title: str
    source: str                       # citedy | fn_ignis | trends_checker | deeptrend | reddit
    score: float = 0.0                # normalised 0-100 opportunity/heat score
    momentum: float = 0.0             # % change signal if available
    keywords: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)  # urls / snippets backing the trend
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def key(self) -> str:
        return hashlib.sha1(self.title.lower().encode()).hexdigest()[:12]


@dataclass
class SourceDoc:
    url: str
    title: str = ""
    text: str = ""
    word_count: int = 0


@dataclass
class ResearchBrief:
    topic: TrendTopic
    angle: str = ""
    primary_keyword: str = ""
    secondary_keywords: list[str] = field(default_factory=list)
    keyword_difficulty: Optional[int] = None
    search_volume: Optional[int] = None
    outline: list[str] = field(default_factory=list)
    key_facts: list[str] = field(default_factory=list)
    sources: list[SourceDoc] = field(default_factory=list)
    content_type: str = "guide"


@dataclass
class SeoReport:
    score: float = 0.0
    title_tag: str = ""
    meta_description: str = ""
    slug: str = ""
    focus_keyword: str = ""
    keyword_density: float = 0.0
    readability: float = 0.0
    internal_links: list[str] = field(default_factory=list)
    schema_jsonld: dict[str, Any] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)


@dataclass
class QcResult:
    score: float = 0.0
    passed: bool = False
    checklist: dict[str, bool] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)


@dataclass
class ImageAsset:
    path: str = ""
    kind: str = "hero"          # hero | og | featured | author_avatar
    width: int = 0
    height: int = 0
    alt: str = ""
    prompt: str = ""
    generated: bool = False     # True if a real model produced it


@dataclass
class PublishTarget:
    platform: str
    url: str = ""
    external_id: str = ""
    ok: bool = False
    canonical: bool = False
    error: str = ""


@dataclass
class Article:
    """The unit of work carried through the whole pipeline."""
    niche_id: str
    run_id: str
    topic: Optional[TrendTopic] = None
    brief: Optional[ResearchBrief] = None

    title: str = ""
    body_markdown: str = ""
    excerpt: str = ""
    tags: list[str] = field(default_factory=list)

    author_name: str = ""
    author_bio: str = ""

    seo: SeoReport = field(default_factory=SeoReport)
    qc: QcResult = field(default_factory=QcResult)
    images: list[ImageAsset] = field(default_factory=list)

    approval: ApprovalDecision = ApprovalDecision.PENDING
    stage: Stage = Stage.TREND
    published: list[PublishTarget] = field(default_factory=list)

    created_at: float = field(default_factory=time.time)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def slug(self) -> str:
        return self.seo.slug or _slug(self.title)

    @property
    def word_count(self) -> int:
        return len(self.body_markdown.split())

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # enums -> values
        d["approval"] = self.approval.value
        d["stage"] = self.stage.value
        return d
