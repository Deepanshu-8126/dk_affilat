"""
STEP 6 — QUALITY CONTROL (25-point checklist, publish gate).

Deterministic checks across structure, SEO, originality signals, humanness,
media and compliance. Article must score >= niche qc_min_score to proceed to
approval/publish.
"""
from __future__ import annotations

import re

from core.logging_utils import get_logger
from core.models import Article, QcResult
from pipeline.humanize import ai_speak_score

log = get_logger("qc")


def _has_heading(md: str) -> bool:
    return bool(re.search(r"(?m)^##\s", md))


def run_qc(article: Article, *, min_score: float = 80) -> QcResult:
    md = article.body_markdown
    seo = article.seo
    checks: dict[str, bool] = {}

    # --- Structure (6) -----------------------------------------------------
    checks["has_title"] = bool(article.title.strip())
    checks["word_count_ok"] = 1500 <= article.word_count <= 2600
    checks["has_h2_sections"] = len(re.findall(r"(?m)^##\s", md)) >= 4
    checks["has_intro_hook"] = len(md.split("\n\n")[0].split()) <= 60 if md else False
    checks["has_list_or_table"] = bool(re.search(r"(?m)^\s*[-*]\s|\n\d+\.\s|\|", md))
    checks["no_conclusion_header"] = not re.search(r"(?mi)^##\s*conclusion\b", md)

    # --- SEO (8) -----------------------------------------------------------
    checks["seo_score_ok"] = seo.score >= min_score
    checks["title_len_ok"] = 0 < len(seo.title_tag) <= 60
    checks["meta_len_ok"] = 120 <= len(seo.meta_description) <= 160
    checks["slug_ok"] = bool(re.fullmatch(r"[a-z0-9-]+", seo.slug or ""))
    checks["keyword_in_title"] = seo.focus_keyword.lower() in seo.title_tag.lower() if seo.focus_keyword else False
    checks["keyword_density_ok"] = 0.5 <= seo.keyword_density <= 2.5
    checks["readability_ok"] = seo.readability >= 55
    checks["has_schema"] = bool(seo.schema_jsonld)
    checks["has_internal_links"] = len(seo.internal_links) >= 2

    # --- Humanness / originality (4) --------------------------------------
    ai_score = ai_speak_score(md)
    checks["low_ai_speak"] = ai_score < 5.0
    checks["no_banned_intro"] = not re.search(r"(?i)in today'?s fast[- ]paced world", md)
    checks["varied_sentences"] = _sentence_variety(md)
    checks["not_repetitive"] = _repetition_ok(md)

    # --- Media (3) ---------------------------------------------------------
    kinds = {img.kind for img in article.images}
    checks["has_featured_image"] = "featured" in kinds
    checks["has_og_image"] = "og" in kinds
    checks["images_have_alt"] = all(img.alt for img in article.images) if article.images else False

    # --- Compliance / trust (4) -------------------------------------------
    checks["has_author"] = bool(article.author_name)
    checks["has_sources"] = bool(article.brief and article.brief.sources)
    checks["no_placeholder_text"] = "lorem ipsum" not in md.lower()
    checks["no_fabrication_flag"] = "(offline draft generated" not in md.lower()
    # FTC compliance: if affiliate links were injected, a disclosure must exist.
    _mon = article.meta.get("monetization", {})
    if _mon.get("links_added", 0) > 0:
        checks["affiliate_disclosure_present"] = bool(_mon.get("disclosure_added"))
    else:
        checks["affiliate_disclosure_present"] = True  # n/a -> pass

    total = len(checks)
    passed = sum(1 for v in checks.values() if v)
    score = round((passed / total) * 100, 1)

    notes = [f"failed: {k}" for k, v in checks.items() if not v]
    notes.append(f"ai_speak_index={ai_score:.2f}")
    result = QcResult(score=score, passed=score >= min_score,
                      checklist=checks, notes=notes)
    log.info("QC %d/%d checks (%.1f%%) -> %s",
             passed, total, score, "PASS" if result.passed else "FAIL")
    return result


def _sentence_variety(md: str) -> bool:
    sents = re.split(r"[.!?]+", re.sub(r"[#*\-|]", "", md))
    lengths = [len(s.split()) for s in sents if s.strip()]
    if len(lengths) < 8:
        return False
    mean = sum(lengths) / len(lengths)
    var = sum((x - mean) ** 2 for x in lengths) / len(lengths)
    return var > 20  # some spread in sentence length


def _repetition_ok(md: str) -> bool:
    paras = [p.strip()[:40] for p in md.split("\n\n") if p.strip()]
    return len(paras) == len(set(paras))
