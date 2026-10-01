"""
MARKET STRATEGY ENGINE  (STEP 2b — runs after research, before write).

This is the "how do I actually make money" brain. For every topic it:

  1. Scores COMMERCIAL / BUYER INTENT (transactional vs commercial vs info).
  2. Picks the HIGHEST-PAYING affiliate platform that matches the niche
     (Amazon US, Meesho, Impact, ShareASale, PartnerStack, ClickBank, ...).
  3. Estimates RPM + commission and an expected-value "money score".
  4. Chooses the best money content type (review/comparison/buyer's guide).
  5. Emits a MARKET DIRECTIVE injected into the writer so the article naturally
     includes buyer-intent sections + CTAs that convert clicks and ad views —
     without turning into spam (CTA count is capped).

It also conditions the writer on live market context (trending products +
seasonal signals) via connectors.product_trends, giving the practical effect of
an LLM "trained on what's happening in the market right now".
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

from connectors.product_trends import trending_products
from core.logging_utils import get_logger
from core.models import ResearchBrief

log = get_logger("market")


@dataclass
class AffiliateMatch:
    platform_id: str
    name: str
    geo: str
    commission_low: float
    commission_high: float
    cookie_days: int
    reason: str = ""


@dataclass
class MarketStrategy:
    tier: str                        # transactional | commercial | informational
    commercial_score: float          # 0-100
    money_score: float               # 0-100 expected-value blend
    rpm_estimate: float              # USD per 1000 views (target geo)
    content_type: str
    platforms: list[AffiliateMatch] = field(default_factory=list)
    buyer_keywords: list[str] = field(default_factory=list)
    trending_products: list[str] = field(default_factory=list)
    ctas: list[str] = field(default_factory=list)
    directive: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


def _niche_tags(niche_monetization: dict) -> list[str]:
    """Infer product/category tags from a niche's monetization config."""
    tags: list[str] = ["saas", "software", "digital"]
    if niche_monetization.get("amazon_associates"):
        tags += ["physical", "gadgets", "accessories"]
    return tags


def _commercial_score(text: str, market: dict) -> tuple[float, list[str], str]:
    t = text.lower()
    bik = market.get("buyer_intent_keywords", {})
    high = [k for k in bik.get("high", []) if re.search(rf"\b{re.escape(k)}\b", t)]
    med = [k for k in bik.get("medium", []) if re.search(rf"\b{re.escape(k)}\b", t)]
    score = min(100.0, len(high) * 22 + len(med) * 8)
    if score >= 66:
        tier = "transactional"
    elif score >= market.get("min_commercial_score", 45):
        tier = "commercial"
    else:
        tier = "informational"
    return score, high + med, tier


def _match_platforms(tags: list[str], market: dict, target_geo: str,
                     limit: int = 3) -> list[AffiliateMatch]:
    reg = market.get("affiliate_platforms", {})
    scored: list[tuple[float, AffiliateMatch]] = []
    for pid, p in reg.items():
        overlap = len(set(tags) & set(p.get("best_for", [])))
        if overlap == 0:
            continue
        lo, hi = p.get("commission", [0, 0])
        geo = p.get("geo", "GLOBAL")
        geo_bonus = 1.0 if geo in (target_geo, "GLOBAL") else 0.4
        # expected value ~ mid commission * geo fit * category fit * cookie length
        ev = ((lo + hi) / 2) * geo_bonus * (1 + overlap * 0.3) * (1 + p.get("cookie", 1) / 90)
        scored.append((ev, AffiliateMatch(
            platform_id=pid, name=p["name"], geo=geo,
            commission_low=lo, commission_high=hi, cookie_days=p.get("cookie", 1),
            reason=f"matches {overlap} category tag(s), {lo}-{hi}% comm, {p.get('cookie',1)}d cookie",
        )))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored[:limit]]


def _pick_content_type(brief: ResearchBrief, tier: str, market: dict,
                       allowed: list[str]) -> str:
    money_types = market.get("money_content_types", [])
    if tier in ("transactional", "commercial"):
        for mt in money_types:
            if mt in allowed:
                return mt
    return brief.content_type or (allowed[0] if allowed else "guide")


def _ctas(tier: str, platforms: list[AffiliateMatch], products: list[str],
          cap: int) -> list[str]:
    ctas: list[str] = []
    if platforms:
        top = platforms[0]
        ctas.append(f"Add a clear 'Check price / Try free' CTA linking via {top.name} near the first recommendation.")
    if tier == "transactional":
        ctas.append("Open with a quick verdict box (winner + runner-up) above the fold.")
        ctas.append("Include a comparison table with an affiliate button per row.")
    if products:
        ctas.append(f"Reference currently-trending picks: {', '.join(products[:3])}.")
    ctas.append("End with a single strong CTA; avoid stuffing links (keeps ad viewability high).")
    return ctas[:cap]


def build_strategy(brief: ResearchBrief, *, niche_monetization: dict,
                   market: dict, allowed_content_types: list[str],
                   niche_name: str = "") -> MarketStrategy:
    target_geo = market.get("target_geo", "US")
    text = f"{brief.topic.title} {' '.join(brief.secondary_keywords)} {brief.angle}"
    score, keywords, tier = _commercial_score(text, market)

    tags = _niche_tags(niche_monetization)
    platforms = _match_platforms(tags, market, target_geo)

    products = [p.title for p in trending_products(niche_name or brief.primary_keyword,
                                                   geo=target_geo, limit=5)]

    rpm = market.get("rpm_bands", {}).get(tier, 6)
    content_type = _pick_content_type(brief, tier, market, allowed_content_types)

    # money score = commercial intent + platform payout + rpm, normalised
    payout = (platforms[0].commission_high if platforms else 5)
    money_score = min(100.0, 0.45 * score + 0.35 * payout + rpm)

    cap = market.get("max_cta_per_post", 4)
    ctas = _ctas(tier, platforms, products, cap)

    directive = _make_directive(tier, score, platforms, keywords, products,
                                content_type, target_geo, cap)

    strat = MarketStrategy(
        tier=tier, commercial_score=round(score, 1), money_score=round(money_score, 1),
        rpm_estimate=float(rpm), content_type=content_type, platforms=platforms,
        buyer_keywords=keywords, trending_products=products, ctas=ctas,
        directive=directive,
    )
    log.info("market: tier=%s comm=%.0f money=%.0f rpm=$%s platform=%s type=%s",
             tier, score, money_score, rpm,
             platforms[0].platform_id if platforms else "none", content_type)
    return strat


def _make_directive(tier: str, score: float, platforms, keywords, products,
                    content_type: str, geo: str, cap: int) -> str:
    plat = platforms[0].name if platforms else "the best-fit affiliate program"
    lines = [
        "--- MONETIZATION STRATEGY (write to earn, stay genuinely helpful) ---",
        f"Audience geo: {geo} (optimise for {geo} readers/RPM).",
        f"Commercial tier: {tier.upper()} (buyer-intent score {score:.0f}/100).",
        f"Format: write this as a {content_type}.",
        f"Primary affiliate route: {plat}. Recommend real products/tools and link the top pick early.",
    ]
    if tier in ("transactional", "commercial"):
        lines.append("Include: a short verdict box up top, a comparison of 3-5 options, "
                     "pros/cons, price context, and a 'who should buy which' section.")
    if products:
        lines.append(f"Currently trending in this market (weave in where accurate): {', '.join(products[:5])}.")
    if keywords:
        lines.append(f"Buyer-intent phrases to cover naturally: {', '.join(keywords[:8])}.")
    lines.append(f"Use at most {cap} CTAs. Disclose affiliate links. Never fabricate prices or specs.")
    return "\n".join(lines)
