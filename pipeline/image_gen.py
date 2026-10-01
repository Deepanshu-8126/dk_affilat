"""
STEP 5 — IMAGE (hero + OG + author avatar).

Uses connectors.image_backends (Z-Image-Turbo -> Pollinations -> SVG placeholder).
Generates:
  * featured  800x450  (in-post hero)
  * og        1200x630 (social card)
  * author avatar (once per niche, cached)
"""
from __future__ import annotations

from pathlib import Path

from connectors import image_backends
from core.config import DATA_DIR
from core.logging_utils import get_logger
from core.models import Article, ImageAsset

log = get_logger("image_gen")

ASSETS = DATA_DIR / "assets"


def _hero_prompt(article: Article) -> str:
    kw = article.seo.focus_keyword or article.title
    return (f"clean modern blog hero illustration about '{kw}', flat vector style, "
            f"soft gradient background, tech theme, no text, high quality")


def generate_images(article: Article, author_avatar_prompt: str | None = None) -> list[ImageAsset]:
    niche_dir = ASSETS / article.niche_id / article.slug
    niche_dir.mkdir(parents=True, exist_ok=True)
    assets: list[ImageAsset] = []

    specs = [("featured", 800, 450), ("og", 1200, 630)]
    hp = _hero_prompt(article)
    for kind, w, h in specs:
        out = niche_dir / f"{kind}.png"
        ok = image_backends.generate(hp, out, width=w, height=h)
        final = out if out.exists() else out.with_suffix(".svg")
        assets.append(ImageAsset(
            path=str(final), kind=kind, width=w, height=h,
            alt=f"{article.title} — {kind} image", prompt=hp, generated=ok,
        ))

    # Author avatar (cached per niche)
    if author_avatar_prompt:
        avatar = ASSETS / article.niche_id / "author_avatar.png"
        if not avatar.exists() and not avatar.with_suffix(".svg").exists():
            ok = image_backends.generate(author_avatar_prompt, avatar,
                                         width=512, height=512)
        final = avatar if avatar.exists() else avatar.with_suffix(".svg")
        assets.append(ImageAsset(
            path=str(final), kind="author_avatar", width=512, height=512,
            alt=f"{article.author_name} avatar", prompt=author_avatar_prompt,
            generated=avatar.exists(),
        ))

    log.info("generated %d image asset(s) for '%s'", len(assets), article.title)
    return assets
