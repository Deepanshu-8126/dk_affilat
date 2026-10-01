"""
AUTO-NICHE / INDUSTRY DETECTION ENGINE.

The 4 built-in niches are just a starting point. This engine lets the system
discover a profitable niche in ANY industry automatically — gaming (GTA 6),
finance, crypto, health, tech, ... — by:

  1. scanning trends across every industry in knowledge/industries.yaml,
  2. scoring each by blended opportunity (trend heat × money potential),
  3. generating a ready-to-run NicheConfig on the fly (brain + author + monetization),

so a spike like "GTA 6" can be turned into a published, monetized article without
anyone hand-coding a niche for it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.config import AppConfig, BrainConfig, NicheConfig, ROOT
from core.logging_utils import get_logger
from core.models import ResearchBrief, TrendTopic
from pipeline import market_intel
from pipeline.trend_detect import TrendContext, detect

log = get_logger("industry")

INDUSTRIES_PATH = ROOT / "knowledge" / "industries.yaml"
_TREND_SOURCES = ["citedy", "fn_ignis", "deeptrend", "trends_checker", "github"]


@dataclass
class Industry:
    id: str
    name: str
    tags: list[str]
    seed_keywords: list[str]
    product_type: str
    rpm: float
    amazon: bool
    saas: list[str]
    author: dict
    brain: str


@dataclass
class Opportunity:
    industry: Industry
    top_topic: str
    trend_score: float
    money_score: float
    tier: str
    rpm: float
    best_platform: str
    opportunity: float          # blended 0-100
    keywords: list[str] = field(default_factory=list)


def load_industries() -> dict[str, Industry]:
    if not INDUSTRIES_PATH.exists():
        return {}
    data = yaml.safe_load(INDUSTRIES_PATH.read_text(encoding="utf-8")) or {}
    out: dict[str, Industry] = {}
    for iid, v in data.get("industries", {}).items():
        out[iid] = Industry(
            id=iid, name=v["name"], tags=v.get("tags", []),
            seed_keywords=v.get("seed_keywords", []), product_type=v.get("product_type", "mixed"),
            rpm=float(v.get("rpm", 8)), amazon=bool(v.get("amazon", False)),
            saas=v.get("saas", []), author=v.get("author", {"name": "Editor", "title": "Writer"}),
            brain=v.get("brain", ""),
        )
    return out


def _monetization(ind: Industry) -> dict:
    return {"adsense": True, "amazon_associates": ind.amazon, "saas_affiliate": ind.saas}


def _content_types(ind: Industry) -> list[str]:
    if ind.product_type in ("physical", "mixed"):
        return ["review", "comparison", "buyers_guide", "listicle"]
    if ind.product_type == "saas":
        return ["review", "comparison", "guide", "listicle"]
    return ["guide", "review", "comparison", "listicle"]


def score_industry(app: AppConfig, ind: Industry) -> Opportunity:
    topics = detect(TrendContext(niche_id=f"industry::{ind.id}",
                                 seed_keywords=ind.seed_keywords,
                                 sources=_TREND_SOURCES, n=3))
    top = topics[0] if topics else TrendTopic(title=ind.seed_keywords[0],
                                              source="seed", keywords=ind.seed_keywords)
    brief = ResearchBrief(topic=top, primary_keyword=(top.keywords[0] if top.keywords else top.title),
                          secondary_keywords=top.keywords[1:6], angle=f"best {ind.name}")
    strat = market_intel.build_strategy(
        brief, niche_monetization=_monetization(ind),
        market=app.defaults.get("market", {}),
        allowed_content_types=_content_types(ind), niche_name=ind.name)

    trend_score = top.score
    # blend trend heat, monetization money score and industry RPM
    opp = min(100.0, 0.4 * trend_score + 0.4 * strat.money_score + ind.rpm)
    return Opportunity(
        industry=ind, top_topic=top.title, trend_score=round(trend_score, 1),
        money_score=strat.money_score, tier=strat.tier, rpm=ind.rpm,
        best_platform=(strat.platforms[0].name if strat.platforms else "-"),
        opportunity=round(opp, 1), keywords=top.keywords[:5],
    )


def discover(app: AppConfig, *, limit: int | None = None) -> list[Opportunity]:
    industries = load_industries()
    opps = [score_industry(app, ind) for ind in industries.values()]
    opps.sort(key=lambda o: o.opportunity, reverse=True)
    log.info("discovered %d industries; top: %s (%.1f)",
             len(opps), opps[0].industry.name if opps else "-",
             opps[0].opportunity if opps else 0)
    return opps[:limit] if limit else opps


def make_niche_config(app: AppConfig, ind: Industry) -> NicheConfig:
    """Turn an industry into a runnable NicheConfig (dynamic niche)."""
    # pick brain: preferred if present, else rotate deterministically
    brain: BrainConfig
    if ind.brain in app.brains:
        brain = app.brains[ind.brain]
    else:
        keys = list(app.brains.values())
        brain = keys[hash(ind.id) % len(keys)]

    niche_id = f"auto_{ind.id}"
    domain = f"{ind.id.replace('_', '-')}-hub.com"
    tone_map = {
        "physical": "Product Reviewer, hands-on, verdict-first",
        "saas": "Pro Analyst, comparison-led, data-driven",
        "digital": "Expert Guide, practical, actionable",
        "mixed": "Reviewer + Guide, balanced and honest",
    }
    return NicheConfig(
        id=niche_id, name=ind.name,
        site={"domain": domain, "wordpress_base_url_env": "WP_AUTO_URL",
              "wordpress_user_env": "WP_AUTO_USER", "wordpress_app_password_env": "WP_AUTO_APP_PASSWORD"},
        brain=brain, tone=tone_map.get(ind.product_type, "Expert Reviewer"),
        author={"name": ind.author.get("name", "Editor"),
                "title": ind.author.get("title", "Writer"),
                "bio": f"{ind.author.get('name','Editor')} is a {ind.author.get('title','writer')} "
                       f"covering {ind.name.lower()} with hands-on testing and honest verdicts.",
                "avatar_prompt": f"professional headshot of a {ind.name.lower()} expert, studio background, photorealistic"},
        keywords_seed=ind.seed_keywords, trend_sources=_TREND_SOURCES,
        monetization=_monetization(ind), content_types=_content_types(ind),
        defaults=app.defaults,
    )


def register_dynamic_niche(app: AppConfig, industry_id: str) -> str:
    """Create + inject a dynamic niche into the app so an agent can run it."""
    industries = load_industries()
    if industry_id not in industries:
        raise KeyError(f"Unknown industry '{industry_id}'. Known: {list(industries)}")
    cfg = make_niche_config(app, industries[industry_id])
    app.niches[cfg.id] = cfg
    log.info("registered dynamic niche '%s' (%s) brain=%s", cfg.id, cfg.name, cfg.brain.id)
    return cfg.id
