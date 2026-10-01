#!/usr/bin/env python3
"""
AUTO-NICHE DISCOVERY CLI.

  python discover.py
      Scan EVERY industry, rank by opportunity (trend × money), print + save an
      HTML report (data/discovery_report.html).

  python discover.py --run gaming
      Auto-generate a dynamic niche for that industry and run the full pipeline
      (e.g. a "GTA 6 / best gaming PC" article), published like any other niche.

  python discover.py --top 3 --run-top
      Run the pipeline on the top N discovered industries automatically.
"""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from core.agent import BaseNicheAgent
from core.config import DATA_DIR, load_config
from core.industry import discover, register_dynamic_niche
from core.logging_utils import get_logger

log = get_logger("discover")
REPORT = DATA_DIR / "discovery_report.html"

TIER_COLOR = {"transactional": "#00b894", "commercial": "#0984e3", "informational": "#b2bec3"}


def _report(opps) -> Path:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = ""
    for i, o in enumerate(opps, 1):
        color = TIER_COLOR.get(o.tier, "#888")
        w = int(o.opportunity)
        rows += f"""
        <tr>
          <td><b>#{i}</b></td>
          <td><b>{o.industry.name}</b><br><span class="muted">{o.industry.id} · ${o.rpm:.0f} RPM</span></td>
          <td>🎯 {o.top_topic}</td>
          <td><span class="tier" style="background:{color}">{o.tier}</span></td>
          <td>{o.money_score:.0f}</td>
          <td><div class="barwrap"><div class="bar" style="width:{w}%"></div></div><b>{o.opportunity:.0f}</b></td>
          <td>{o.best_platform}</td>
        </tr>"""
    html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Auto-Niche Discovery</title>
<style>
 body{{margin:0;font-family:system-ui,Segoe UI,Arial;background:linear-gradient(180deg,#0b132b,#1c2541);color:#1a1d29}}
 .wrap{{max-width:1000px;margin:0 auto;padding:28px 18px 60px}}
 header{{color:#fff;margin-bottom:16px}} header h1{{margin:0;font-size:26px}} header p{{color:#9fb3d1;margin:4px 0 0}}
 table{{width:100%;border-collapse:collapse;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 8px 24px rgba(0,0,0,.3)}}
 th,td{{padding:12px 14px;text-align:left;font-size:13px;border-bottom:1px solid #eef1f6;vertical-align:top}}
 th{{background:#f5f7fb;color:#666;font-size:11px;text-transform:uppercase;letter-spacing:.4px}}
 .muted{{color:#999;font-size:11px}}
 .tier{{color:#fff;font-size:10px;font-weight:700;padding:3px 8px;border-radius:20px;text-transform:uppercase}}
 .barwrap{{background:#eef1f6;border-radius:6px;height:10px;width:110px;display:inline-block;overflow:hidden;vertical-align:middle;margin-right:6px}}
 .bar{{height:10px;background:linear-gradient(90deg,#6c5ce7,#00b894)}}
</style></head><body><div class="wrap">
<header><h1>🧭 Auto-Niche Discovery</h1>
<p>System scanned {len(opps)} industries and ranked them by opportunity (trend heat × money potential) · {now}</p></header>
<table>
<tr><th>#</th><th>Industry</th><th>Top opportunity</th><th>Tier</th><th>Money</th><th>Opportunity</th><th>Best platform</th></tr>
{rows}
</table>
</div></body></html>"""
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(html, encoding="utf-8")
    return REPORT


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="industry id to generate a niche for and run")
    ap.add_argument("--run-top", action="store_true", help="run the top --top industries")
    ap.add_argument("--top", type=int, default=5)
    ap.add_argument("--no-jitter", action="store_true")
    args = ap.parse_args()

    app = load_config()
    opps = discover(app)

    print("\n🧭 AUTO-DETECTED NICHE OPPORTUNITIES (any industry)\n")
    print(f"  {'#':<3}{'INDUSTRY':<26}{'TIER':<14}{'MONEY':<7}{'OPP':<6}TOP TOPIC")
    for i, o in enumerate(opps, 1):
        print(f"  {i:<3}{o.industry.name:<26}{o.tier:<14}{o.money_score:<7.0f}{o.opportunity:<6.0f}{o.top_topic}")
    p = _report(opps)
    print(f"\n  report -> {p}")

    to_run: list[str] = []
    if args.run:
        to_run = [args.run]
    elif args.run_top:
        to_run = [o.industry.id for o in opps[: args.top]]

    for iid in to_run:
        nid = register_dynamic_niche(app, iid)
        print(f"\n▶ Running dynamic niche '{nid}' …")
        art = BaseNicheAgent(app, nid).run()
        live = [t.url for t in art.published if t.ok]
        print(f"  ✅ {art.title}  (SEO {art.seo.score:.0f}, QC {art.qc.score:.0f}, {len(live)} url(s))")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
