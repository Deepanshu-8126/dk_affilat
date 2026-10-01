"""
STEP 7 — PUBLISH (WOPE + IndexNow).

Order:
  1. Publish canonical post to WordPress (primary site).
  2. Syndicate to DEV.to / Medium / Hashnode with rel=canonical -> primary.
  3. Ping IndexNow (Bing + Yandex) for the canonical URL.

Markdown is converted to lightweight HTML for WordPress; syndication platforms
receive Markdown directly.
"""
from __future__ import annotations

import re

from connectors import indexnow, syndicate
from connectors.wordpress import WordPressClient
from core import accounts
from core.logging_utils import get_logger
from core.models import Article, PublishTarget
from pipeline import monetize

log = get_logger("publish")


def _md_to_html(md: str) -> str:
    """Minimal, dependency-free Markdown -> HTML (headings, lists, bold, para)."""
    html_lines: list[str] = []
    in_list = False
    for line in md.splitlines():
        s = line.rstrip()
        if not s:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            continue
        h = re.match(r"^(#{1,6})\s+(.*)", s)
        if h:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            lvl = len(h.group(1))
            html_lines.append(f"<h{lvl}>{_inline(h.group(2))}</h{lvl}>")
            continue
        li = re.match(r"^\s*[-*]\s+(.*)", s)
        if li:
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{_inline(li.group(1))}</li>")
            continue
        if in_list:
            html_lines.append("</ul>")
            in_list = False
        html_lines.append(f"<p>{_inline(s)}</p>")
    if in_list:
        html_lines.append("</ul>")
    return "\n".join(html_lines)


def _inline(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
    # Links with optional attribute block: [text](url){: rel="..." target=... }
    text = re.sub(
        r"\[(.+?)\]\((.+?)\)(?:\{:\s*(.*?)\s*\})?",
        _render_link,
        text,
    )
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    return text


def _render_link(m: re.Match) -> str:
    label, url, attrs = m.group(1), m.group(2), (m.group(3) or "").strip()
    extra = ""
    rel = re.search(r'rel="([^"]+)"', attrs)
    if rel:
        extra += f' rel="{rel.group(1)}"'
    if "target=_blank" in attrs or 'target="_blank"' in attrs:
        extra += ' target="_blank"'
    return f'<a href="{url}"{extra}>{label}</a>'


def _author_box(article: Article) -> str:
    return (f'\n<hr>\n<div class="author-box"><strong>{article.author_name}</strong>'
            f'<p>{article.author_bio}</p></div>')


def _schema_block(article: Article) -> str:
    import json
    return f'\n<script type="application/ld+json">{json.dumps(article.seo.schema_jsonld)}</script>'


def publish(article: Article, wp: WordPressClient, *,
            platforms: list[str], index_now: bool, domain: str,
            mon: dict | None = None,
            accounts_cfg: dict | None = None) -> list[PublishTarget]:
    targets: list[PublishTarget] = []
    html = _md_to_html(article.body_markdown)

    # In-article AdSense units (only if configured + post long enough)
    if mon:
        ad_units = monetize.adsense_html(article.word_count, mon)
        html, n = monetize.inject_ads_into_html(html, ad_units)
        if n:
            article.meta.setdefault("monetization", {})["ad_units"] = n
            log.info("injected %d AdSense unit(s)", n)

    html = html + _author_box(article) + _schema_block(article)

    # 1) WordPress canonical
    wp_res = wp.create_post(
        title=article.seo.title_tag or article.title,
        content_html=html,
        excerpt=article.seo.meta_description or article.excerpt,
        slug=article.slug,
        tags=article.tags,
        domain=domain,
    )
    canonical_url = wp_res.get("url", f"https://{domain}/{article.slug}/")
    targets.append(PublishTarget(
        platform="wordpress", url=canonical_url,
        external_id=str(wp_res.get("id", "")), ok=wp_res.get("ok", False),
        canonical=True, error=wp_res.get("error", ""),
    ))
    log.info("WordPress -> %s (ok=%s)", canonical_url, wp_res.get("ok"))

    # 2) Syndicate
    for plat in platforms:
        if plat == "wordpress":
            continue
        fn = syndicate.DISPATCH.get(plat)
        if not fn:
            log.warning("no syndicator for '%s'", plat)
            continue
        token_env = None
        if accounts_cfg:
            token_env = accounts.pick_account(plat, accounts_cfg)
        res = fn(
            title=article.title,
            body_markdown=article.body_markdown,
            canonical_url=canonical_url,
            tags=article.tags or (article.brief.secondary_keywords if article.brief else []),
            slug=article.slug,
            token_env=token_env,
        )
        targets.append(PublishTarget(
            platform=plat, url=res.get("url", ""), ok=res.get("ok", False),
            error=res.get("error", ""),
        ))
        if token_env:
            article.meta.setdefault("accounts_used", {})[plat] = token_env

    # 3) IndexNow
    if index_now:
        urls = [t.url for t in targets if t.ok and t.url]
        indexnow.submit(domain, urls)

    return targets
