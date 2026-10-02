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

    # Check if article is a Comparison or Deal/Review post
    title_lower = article.title.lower()
    from connectors.photoshop_deal_banner import PhotoshopDealBannerEngine
    banner_engine = PhotoshopDealBannerEngine(output_dir=niche_dir)

    is_comparison = any(k in title_lower for k in [" vs ", " versus ", " compared to ", " alternative", " vs."])
    is_deal_or_review = any(k in title_lower for k in ["deal", "discount", "sale", "price", "review", "best "])

    if is_comparison:
        # Extract product names if possible
        parts = title_lower.split(" vs ") if " vs " in title_lower else title_lower.split(" versus ")
        prod_a = parts[0].strip().title() if len(parts) > 1 else article.title[:20]
        prod_b = parts[1].strip().title() if len(parts) > 1 else "Alternative"
        vs_banner = banner_engine.generate_vs_battle_banner(
            product_a=prod_a, product_b=prod_b, category=article.niche_id, out_filename="featured.png"
        )
        assets.append(ImageAsset(
            path=str(vs_banner), kind="featured", width=1200, height=630,
            alt=f"{article.title} — Comparison Battle Card", prompt=f"{prod_a} vs {prod_b}", generated=True,
        ))
    elif is_deal_or_review:
        deal_banner = banner_engine.generate_deal_discount_banner(
            product_name=article.title, discount_percent="40% OFF DEAL", out_filename="featured.png"
        )
        assets.append(ImageAsset(
            path=str(deal_banner), kind="featured", width=1200, height=630,
            alt=f"{article.title} — Deal & Discount Card", prompt=article.title, generated=True,
        ))
    else:
        # Standard featured & OG generation
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
