#!/usr/bin/env python3
"""
MARKET OPPORTUNITY REPORT.

Analyses every niche through the market engine and renders a single HTML report:
for each niche it shows the top trend, its commercial tier + money score,
the best-matched affiliate platforms (Amazon / Meesho / Impact / ...),
estimated RPM, and currently-trending products to feature.

Usage:  python market_report.py   ->   data/market_report.html
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from core.config import DATA_DIR, load_config
from core.logging_utils import get_logger
from core.models import ResearchBrief, TrendTopic
from pipeline import market_intel
from pipeline.trend_detect import TrendContext, detect

log = get_logger("market_report")
OUT = DATA_DIR / "market_report.html"

TIER_COLOR = {"transactional": "#00b894", "commercial": "#0984e3", "informational": "#b2bec3"}


def _brief_for(niche) -> ResearchBrief:
    topics = detect(TrendContext(niche_id=niche.id, seed_keywords=niche.keywords_seed,
                                 sources=niche.trend_sources, n=3))
    top = topics[0] if topics else TrendTopic(title=niche.keywords_seed[0], source="seed",
                                              keywords=niche.keywords_seed)
    return ResearchBrief(topic=top, primary_keyword=(top.keywords[0] if top.keywords else top.title),
                         secondary_keywords=top.keywords[1:6], angle=f"best {niche.name}")


def build() -> Path:
    app = load_config()
    market = app.defaults.get("market", {})
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    cards = ""
    total_rpm = 0.0
    for nid, niche in app.niches.items():
        brief = _brief_for(niche)
        strat = market_intel.build_strategy(
            brief, niche_monetization=niche.monetization, market=market,
            allowed_content_types=niche.content_types, niche_name=niche.name)
        total_rpm += strat.rpm_estimate
        color = TIER_COLOR.get(strat.tier, "#888")

        plats = "".join(
            f'<tr><td><b>{p.name}</b></td><td>{p.geo}</td>'
            f'<td>{p.commission_low:.0f}-{p.commission_high:.0f}%</td>'
            f'<td>{p.cookie_days}d</td></tr>' for p in strat.platforms) \
            or '<tr><td colspan=4 class="muted">no platform match</td></tr>'
        products = "".join(f'<span class="chip">{p}</span>' for p in strat.trending_products)
        ctas = "".join(f"<li>{c}</li>" for c in strat.ctas)

        cards += f"""
        <div class="card">
          <div class="ch">
            <div><h3>{niche.name}</h3><span class="muted">{nid} · {niche.domain}</span></div>
            <span class="tier" style="background:{color}">{strat.tier.upper()}</span>
          </div>
          <div class="metrics">
            <div><b>{strat.money_score:.0f}</b><span>money score</span></div>
            <div><b>{strat.commercial_score:.0f}</b><span>buyer intent</span></div>
            <div><b>${strat.rpm_estimate:.0f}</b><span>est. RPM</span></div>
            <div><b>{strat.content_type}</b><span>best format</span></div>
          </div>
          <div class="topic">🎯 Top opportunity: <b>{brief.topic.title}</b></div>
          <h4>Best affiliate platforms</h4>
          <table><tr><th>Platform</th><th>Geo</th><th>Commission</th><th>Cookie</th></tr>{plats}</table>
          <h4>Trending products to feature</h4><div class="chips">{products}</div>
          <h4>Conversion playbook</h4><ul class="ctas">{ctas}</ul>
        </div>"""

    avg_rpm = total_rpm / max(1, len(app.niches))
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<title>Market Opportunity Report</title><style>
 body{{margin:0;font-family:system-ui,Segoe UI,Arial;background:linear-gradient(180deg,#0b132b,#1c2541);color:#1a1d29}}
 .wrap{{max-width:1080px;margin:0 auto;padding:28px 18px 60px}}
 header{{color:#fff;margin-bottom:8px}} header h1{{margin:0;font-size:26px}}
 header p{{color:#9fb3d1;margin:4px 0 0}}
 .sum{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:20px 0}}
 .sum div{{background:#fff;border-radius:12px;padding:16px;text-align:center;box-shadow:0 6px 18px rgba(0,0,0,.25)}}
 .sum b{{display:block;font-size:24px;color:#0b8457}} .sum span{{font-size:12px;color:#777}}
 .grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
 .card{{background:#fff;border-radius:14px;padding:18px;box-shadow:0 6px 18px rgba(0,0,0,.2)}}
 .ch{{display:flex;justify-content:space-between;align-items:flex-start}}
 .card h3{{margin:0;font-size:16px}} .card h4{{margin:16px 0 6px;font-size:12px;color:#555;text-transform:uppercase;letter-spacing:.4px}}
 .tier{{color:#fff;font-size:11px;font-weight:700;padding:4px 10px;border-radius:20px}}
 .muted{{color:#999;font-size:12px}}
 .metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin:14px 0}}
 .metrics div{{text-align:center;background:#f6f8fc;border-radius:8px;padding:8px 4px}}
 .metrics b{{display:block;font-size:16px;color:#4834d4}} .metrics span{{font-size:10px;color:#888}}
 .topic{{background:#eefaf3;border-left:3px solid #00b894;padding:8px 12px;border-radius:6px;font-size:13px}}
 table{{width:100%;border-collapse:collapse;font-size:12px}} th,td{{padding:6px 8px;text-align:left;border-bottom:1px solid #eef1f6}} th{{color:#888;font-size:10px;text-transform:uppercase}}
 .chips .chip,.chips{{display:inline-block}} .chip{{background:#eef0ff;color:#4834d4;font-size:11px;padding:4px 9px;border-radius:20px;margin:3px 4px 0 0}}
 .ctas{{margin:6px 0 0;padding-left:18px;font-size:12px;color:#444;line-height:1.6}}
</style></head><body><div class="wrap">
<header><h1>💸 Market Opportunity Report</h1>
<p>Affiliate + ad monetization analysis across all niches · target geo {market.get('target_geo','US')} · {now}</p></header>
<div class="sum">
 <div><b>{len(app.niches)}</b><span>NICHES ANALYSED</span></div>
 <div><b>${avg_rpm:.0f}</b><span>AVG EST. RPM (US)</span></div>
 <div><b>{len(market.get('affiliate_platforms',{}))}</b><span>AFFILIATE PLATFORMS</span></div>
</div>
<div class="grid">{cards}</div>
</div></body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


if __name__ == "__main__":
    p = build()
    print(f"market report -> {p}")
