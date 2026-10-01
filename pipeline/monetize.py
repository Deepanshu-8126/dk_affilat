"""
MONETIZATION — runs after WRITE, before SEO.

Three jobs, all policy-aware and idempotent:
  1. inject_affiliate_links()  — turn the FIRST plain mention of a known tool
     into an affiliate link (rel=sponsored), capped to avoid over-linking.
  2. add_disclosures()         — prepend an FTC affiliate disclosure (+ Amazon
     Associates line if enabled) whenever affiliate links exist. Required by law.
  3. adsense_html()            — build in-article <ins> ad units for the HTML
     render step, only on posts long enough to be policy-safe.

Everything degrades gracefully: no tool mentioned -> no links; no publisher id
-> no ad markup; no affiliate links -> no disclosure. Nothing ever breaks.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

from core.logging_utils import get_logger

log = get_logger("monetize")


@dataclass
class MonetizeResult:
    links_added: int = 0
    tools_linked: list[str] | None = None
    disclosure_added: bool = False
    amazon_disclosure_added: bool = False
    ad_units: int = 0

    def __post_init__(self):
        if self.tools_linked is None:
            self.tools_linked = []


# --- 1. affiliate links ----------------------------------------------------
def _resolve_url(entry: dict) -> str | None:
    url = entry.get("url", "")
    tag_env = entry.get("tag_env")
    if "{tag}" in url:
        tag = os.getenv(tag_env) if tag_env else None
        if not tag:
            # No tag configured -> strip the tagged query so we still link out.
            return re.sub(r"[?&][^=]+=\{tag\}", "", url).rstrip("?&") or None
        return url.replace("{tag}", tag)
    return url or None


def _link_markup(text: str, url: str, mon: dict) -> str:
    rel = mon.get("link_rel", "sponsored nofollow noopener")
    target = ' target="_blank"' if mon.get("open_in_new_tab", True) else ""
    # Markdown link with an HTML title carrying rel/target hints for the renderer.
    return f'[{text}]({url}){{: rel="{rel}"{target} }}'


def inject_affiliate_links(markdown: str, saas_slugs: list[str],
                           registry: dict, mon: dict) -> tuple[str, list[str]]:
    """Link the first plain-text mention of each configured tool, once."""
    cap = mon.get("max_affiliate_links", 6)
    linked: list[str] = []
    out = markdown

    # Skip anything already inside a link or code span.
    def already_linked(name: str, s: str) -> bool:
        return bool(re.search(r"\]\([^)]*\)\s*" + re.escape(name), s)) or \
               bool(re.search(r"\[" + re.escape(name) + r"\]\(", s))

    for slug in saas_slugs:
        if len(linked) >= cap:
            break
        entry = registry.get(slug)
        if not entry:
            continue
        name = entry.get("name", slug)
        url = _resolve_url(entry)
        if not url:
            continue
        if already_linked(name, out):
            continue
        # Match the whole-word first occurrence not already in a markdown link/code.
        pattern = re.compile(rf"(?<![\[`/\w]){re.escape(name)}(?![\w\]`])")
        m = pattern.search(out)
        if not m:
            continue
        out = out[:m.start()] + _link_markup(name, url, mon) + out[m.end():]
        linked.append(name)

    return out, linked


# --- 2. disclosures --------------------------------------------------------
def add_disclosures(markdown: str, mon: dict, *, has_affiliate: bool,
                    amazon_enabled: bool) -> tuple[str, bool, bool]:
    if not has_affiliate:
        return markdown, False, False
    disc = mon.get("disclosure", {})
    lines = []
    aff = (disc.get("affiliate") or "").strip()
    if aff and aff.lower() not in markdown.lower():
        lines.append(f"> {aff}")
    amazon_added = False
    if amazon_enabled:
        amz = (disc.get("amazon") or "").strip()
        if amz and amz.lower() not in markdown.lower():
            lines.append(f"> {amz}")
            amazon_added = True
    if not lines:
        return markdown, False, amazon_added

    block = "\n".join(lines)
    # Insert after the first paragraph (the hook), so it's visible "near the top".
    parts = markdown.split("\n\n", 1)
    if len(parts) == 2:
        new_md = f"{parts[0]}\n\n{block}\n\n{parts[1]}"
    else:
        new_md = f"{block}\n\n{markdown}"
    return new_md, True, amazon_added


# --- 3. adsense ------------------------------------------------------------
def adsense_html(word_count: int, mon: dict) -> list[str]:
    """Return a list of in-article ad-unit HTML strings (may be empty)."""
    ad = mon.get("adsense", {})
    if not ad.get("enabled", False):
        return []
    if word_count < ad.get("min_words_for_ads", 900):
        log.info("post too short (%d words) for ads -> skipping", word_count)
        return []
    pub = os.getenv(ad.get("publisher_id_env", ""))
    slot = os.getenv(ad.get("slot_id_env", ""))
    if not (pub and slot):
        return []
    unit = (
        '<ins class="adsbygoogle" style="display:block; text-align:center;" '
        'data-ad-layout="in-article" data-ad-format="fluid" '
        f'data-ad-client="{pub}" data-ad-slot="{slot}"></ins>'
        '<script>(adsbygoogle = window.adsbygoogle || []).push({});</script>'
    )
    return [unit] * max(1, min(ad.get("max_units", 2), 3))


def inject_ads_into_html(html: str, ad_units: list[str]) -> tuple[str, int]:
    """Distribute ad units evenly between <h2> section boundaries."""
    if not ad_units:
        return html, 0
    boundaries = [m.start() for m in re.finditer(r"<h2[ >]", html)]
    if len(boundaries) < 2:
        return html, 0
    # pick evenly spaced boundaries (skip the very first section)
    picks = []
    step = max(1, len(boundaries) // (len(ad_units) + 1))
    idx = step
    while idx < len(boundaries) and len(picks) < len(ad_units):
        picks.append(boundaries[idx])
        idx += step
    # insert from the end so offsets stay valid
    out = html
    inserted = 0
    for pos, unit in zip(reversed(picks), ad_units):
        out = out[:pos] + f"\n{unit}\n" + out[pos:]
        inserted += 1
    return out, inserted


# --- orchestration ---------------------------------------------------------
def apply_content_monetization(markdown: str, *, saas_slugs: list[str],
                               amazon_enabled: bool, mon: dict) -> tuple[str, MonetizeResult]:
    registry = mon.get("affiliate_registry", {})
    md, linked = inject_affiliate_links(markdown, saas_slugs, registry, mon)
    md, disc, amz = add_disclosures(
        md, mon, has_affiliate=bool(linked), amazon_enabled=amazon_enabled)
    res = MonetizeResult(links_added=len(linked), tools_linked=linked,
                         disclosure_added=disc, amazon_disclosure_added=amz)
    log.info("monetize: %d affiliate link(s) %s | disclosure=%s amazon=%s",
             res.links_added, linked, disc, amz)
    return md, res
