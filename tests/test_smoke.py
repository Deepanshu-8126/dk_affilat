"""
Smoke tests — verify each agent runs the full pipeline end-to-end in
offline/dry-run mode (no keys, no network required).

Run:  DRY_RUN=true AUTO_APPROVE=true python -m pytest -q
  or: python tests/test_smoke.py
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("DRY_RUN", "true")
os.environ.setdefault("AUTO_APPROVE", "true")
os.environ.setdefault("REQUIRE_APPROVAL", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")

from core.agent import BaseNicheAgent          # noqa: E402
from core.config import load_config            # noqa: E402
from core.models import Stage                  # noqa: E402
from pipeline.humanize import humanize         # noqa: E402
from pipeline.seo_optimize import _slugify, _keyword_density  # noqa: E402


def test_config_loads_niches():
    app = load_config()
    assert {"agent_1_ai_tools", "agent_2_ai_coding",
            "agent_3_ai_automation", "agent_4_ai_visual"} <= set(app.niches)
    assert app.niche("agent_1_ai_tools").brain.provider == "gemini"
    assert app.niche("agent_2_ai_coding").brain.provider == "groq"
    assert app.niche("agent_3_ai_automation").brain.provider == "ollama"
    assert app.niche("agent_4_ai_visual").brain.provider == "groq"


def test_humanizer_removes_ai_speak():
    txt = "In today's fast-paced world, we leverage cutting-edge tools. In conclusion, it works."
    out = humanize(txt)
    assert "fast-paced world" not in out.lower()
    assert "leverage" not in out.lower()
    assert "in conclusion" not in out.lower()


def test_slug_and_density():
    assert _slugify("Best AI Tools 2026!") == "best-ai-tools-2026"
    d = _keyword_density("ai tools are great ai tools rock", "ai tools")
    assert d > 0


def test_monetization_injects_links_and_disclosure():
    from pipeline.monetize import apply_content_monetization, adsense_html, inject_ads_into_html
    mon = {
        "max_affiliate_links": 6,
        "link_rel": "sponsored nofollow noopener",
        "disclosure": {"affiliate": "Disclosure: affiliate links.",
                       "amazon": "As an Amazon Associate we earn."},
        "affiliate_registry": {
            "jasper": {"name": "Jasper", "url": "https://jasper.ai/?fpr={tag}", "tag_env": "JASPER_AFFILIATE_ID"},
            "cursor": {"name": "Cursor", "url": "https://cursor.com/", "tag_env": None},
        },
    }
    md = ("Here is the hook paragraph.\n\n"
          "I tested Jasper and Cursor for weeks. Jasper is great; Cursor too.")
    out, res = apply_content_monetization(
        md, saas_slugs=["jasper", "cursor"], amazon_enabled=True, mon=mon)
    assert res.links_added == 2
    assert "](https://cursor.com/)" in out            # no tag -> plain url
    assert "jasper.ai" in out
    assert "Disclosure:" in out                        # FTC disclosure present
    assert "Amazon Associate" in out
    # only the FIRST mention of each tool is linked (idempotent-ish)
    assert out.count("](https://cursor.com/)") == 1

    # adsense: needs publisher/slot envs -> without them, no units
    assert adsense_html(1500, {"adsense": {"enabled": True, "min_words_for_ads": 900,
                               "publisher_id_env": "X", "slot_id_env": "Y"}}) == []
    # short post -> no ads even if configured
    os.environ["ADP"] = "ca-pub-1"; os.environ["ADS"] = "123"
    units = adsense_html(500, {"adsense": {"enabled": True, "min_words_for_ads": 900,
                               "publisher_id_env": "ADP", "slot_id_env": "ADS", "max_units": 2}})
    assert units == []
    # long post + configured -> units, injected between h2s
    units = adsense_html(1500, {"adsense": {"enabled": True, "min_words_for_ads": 900,
                               "publisher_id_env": "ADP", "slot_id_env": "ADS", "max_units": 2}})
    assert len(units) == 2
    html = "<h2>A</h2><p>x</p><h2>B</h2><p>y</p><h2>C</h2><p>z</p>"
    injected, n = inject_ads_into_html(html, units)
    assert n >= 1 and "adsbygoogle" in injected


def test_market_strategy_engine():
    from core.config import load_config
    from core.models import ResearchBrief, TrendTopic
    from pipeline import market_intel
    app = load_config()
    market = app.defaults["market"]
    niche = app.niche("agent_1_ai_tools")
    topic = TrendTopic(title="Best AI Writing Tools Review 2026 vs Alternatives",
                       source="t", keywords=["best ai writing tools", "review"])
    brief = ResearchBrief(topic=topic, primary_keyword="best ai writing tools",
                          secondary_keywords=["review", "vs", "price"], angle="best tools")
    strat = market_intel.build_strategy(
        brief, niche_monetization=niche.monetization, market=market,
        allowed_content_types=niche.content_types, niche_name=niche.name)
    assert strat.tier in ("transactional", "commercial")   # buyer-intent title
    assert strat.commercial_score > 0
    assert strat.platforms, "should match at least one affiliate platform"
    assert strat.rpm_estimate >= market["rpm_bands"]["commercial"]
    assert strat.directive and "MONETIZATION STRATEGY" in strat.directive
    assert strat.content_type in market["money_content_types"]


def test_knowledge_engine_retrieval_and_training():
    from core.knowledge import load_kb
    kb = load_kb(force=True)
    assert len(kb.cards) >= 20, "expected a substantial knowledge base"
    # retrieval is context-aware: a transactional AI-video query should surface
    # the visual playbook + a conversion rule
    brief, ids = kb.briefing("best ai video generator vs runway review price",
                             niche_id="agent_4_ai_visual", tier="transactional", k=6)
    assert brief and "EXPERT PLAYBOOK" in brief
    assert "pb_ai_visual" in ids
    # reinforcement raises weight (self-training)
    before = next(c.weight for c in kb.cards if c.id == "intent_ladder")
    kb.reinforce(["intent_ladder"], reward=0.5)
    after = next(c.weight for c in kb.cards if c.id == "intent_ladder")
    assert after > before


def test_auto_industry_discovery():
    from core.config import load_config
    from core.industry import discover, load_industries, register_dynamic_niche, make_niche_config
    app = load_config()
    inds = load_industries()
    assert "gaming" in inds and "finance" in inds
    opps = discover(app)
    assert len(opps) >= 8
    assert all(0 <= o.opportunity <= 100 for o in opps)
    # dynamic niche generation for any industry
    cfg = make_niche_config(app, inds["gaming"])
    assert cfg.id == "auto_gaming" and cfg.author["name"]
    nid = register_dynamic_niche(app, "gaming")
    assert nid in app.niches


def test_openmontage_seo_logic():
    from connectors import openmontage
    # 1) deep research fan-out (OpenMontage "research first, many angles")
    plan = openmontage.research_query_plan(
        "Best VPN for streaming", ["best vpn", "vpn for netflix"], n=8)
    assert len(plan.queries) == 8
    assert len(set(plan.angles)) >= 4          # many distinct angles
    urls = openmontage.deep_research_urls("Best VPN", ["best vpn"], n=6)
    assert all(u.startswith("http") for u in urls) and len(urls) == 6
    # 2) video-for-SEO pack + VideoObject schema + free render manifest
    pack = openmontage.video_seo_pack(
        "Best VPN for Streaming in 2026", "best vpn",
        secondary_keywords=["vpn for netflix", "cheap vpn"],
        outline=["What to look for", "Top picks", "How we tested"],
        page_url="https://example.com/best-vpn", author="Ryan Cooper")
    assert pack.video_object["@type"] == "VideoObject"
    assert pack.yt_title and pack.yt_tags and pack.chapters
    assert "pipeline:" in pack.manifest and "budget_usd: 0" in pack.manifest
    saved = openmontage.save_video_brief(pack, "best-vpn-streaming")
    assert saved["manifest"].endswith(".openmontage.yaml")


def test_each_agent_runs_end_to_end():
    app = load_config()
    for niche_id in app.niches:
        art = BaseNicheAgent(app, niche_id).run()
        assert art.stage in (Stage.DONE,), f"{niche_id} ended at {art.stage}"
        assert art.title
        assert art.body_markdown
        assert art.seo.slug
        assert any(t.platform == "wordpress" for t in art.published)
        print(f"OK {niche_id}: '{art.title}' "
              f"(SEO {art.seo.score}, QC {art.qc.score}, "
              f"{len(art.published)} targets)")


if __name__ == "__main__":
    test_config_loads_niches()
    test_humanizer_removes_ai_speak()
    test_slug_and_density()
    test_monetization_injects_links_and_disclosure()
    test_market_strategy_engine()
    test_knowledge_engine_retrieval_and_training()
    test_auto_industry_discovery()
    test_openmontage_seo_logic()
    test_each_agent_runs_end_to_end()
    print("\nALL SMOKE TESTS PASSED")
