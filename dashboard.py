#!/usr/bin/env python3
"""
ANALYZE-ALL DASHBOARD.

Scans data/runs + data/memory + config + account state and renders a single
self-contained HTML control center (inline CSS + SVG charts, no external assets
so it previews anywhere). Shows per-niche output, SEO/QC trends, learned keyword
boosts, multi-account health, GEO/AEO coverage, monetization and an earnings
projection.

Usage:  python dashboard.py   ->   data/dashboard.html
"""
from __future__ import annotations

import glob
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from core.accounts import account_summary
from core.config import DATA_DIR, load_config

OUT = DATA_DIR / "dashboard.html"

# earnings model (aligned with the PRD timeline, per site)
PROJECTION = [
    (1, 90, 500, 0, 20), (2, 180, 2000, 50, 50), (3, 270, 8000, 200, 200),
    (6, 540, 30000, 800, 800), (12, 1080, 100000, 2500, 3000),
]


def _load_runs() -> list[dict]:
    arts = []
    for f in sorted(glob.glob(str(DATA_DIR / "runs" / "*" / "*.json"))):
        try:
            arts.append(json.load(open(f)))
        except Exception:  # noqa: BLE001
            pass
    return arts


def _bar(value: float, maxv: float, color: str, w: int = 180) -> str:
    pct = 0 if maxv == 0 else max(2, int(w * value / maxv))
    return (f'<svg width="{w}" height="14">'
            f'<rect width="{w}" height="14" rx="3" fill="#eef1f6"/>'
            f'<rect width="{pct}" height="14" rx="3" fill="{color}"/></svg>')


def _spark(values: list[float], color: str, w: int = 160, h: int = 34) -> str:
    if not values:
        return ""
    lo, hi = min(values), max(values)
    rng = (hi - lo) or 1
    step = w / max(1, len(values) - 1)
    pts = " ".join(f"{i*step:.1f},{h-2-(v-lo)/rng*(h-6):.1f}" for i, v in enumerate(values))
    return (f'<svg width="{w}" height="{h}">'
            f'<polyline fill="none" stroke="{color}" stroke-width="2" points="{pts}"/></svg>')


def build(auto_refresh: int = 0) -> Path:
    app = load_config()
    arts = _load_runs()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    by_niche: dict[str, list[dict]] = defaultdict(list)
    for a in arts:
        by_niche[a.get("niche_id", "?")].append(a)

    total_posts = len(arts)
    published = sum(1 for a in arts if any(t.get("ok") for t in a.get("published", [])))
    avg_seo = round(sum(a.get("seo", {}).get("score", 0) for a in arts) / max(1, total_posts), 1)
    avg_qc = round(sum(a.get("qc", {}).get("score", 0) for a in arts) / max(1, total_posts), 1)

    # per-niche cards
    niche_rows = ""
    for nid, ncfg in app.niches.items():
        posts = by_niche.get(nid, [])
        seo_vals = [p.get("seo", {}).get("score", 0) for p in posts]
        qc_vals = [p.get("qc", {}).get("score", 0) for p in posts]
        mem = json.loads((DATA_DIR / "memory" / f"{nid}.json").read_text(encoding="utf-8")) \
            if (DATA_DIR / "memory" / f"{nid}.json").exists() else {"keyword_boosts": {}, "topics": {}}
        conf = min(1.0, len(mem.get("topics", {})) / 30.0)
        top_kw = sorted(mem.get("keyword_boosts", {}).items(), key=lambda kv: kv[1], reverse=True)[:5]
        kw_html = "".join(
            f'<div class="kw"><span>{k}</span>{_bar(v, max((x[1] for x in top_kw), default=1), "#6c5ce7", 120)}<b>{v:.1f}</b></div>'
            for k, v in top_kw) or '<div class="muted">no learning data yet — run learn.py</div>'
        links = sum(p.get("meta", {}).get("monetization", {}).get("links_added", 0) for p in posts)
        niche_rows += f"""
        <div class="card">
          <div class="card-h">
            <div><h3>{ncfg.name}</h3><span class="muted">{nid} · {ncfg.brain.provider}/{ncfg.brain.model}</span></div>
            <div class="badge">{ncfg.author['name']}</div>
          </div>
          <div class="stats">
            <div><b>{len(posts)}</b><span>posts</span></div>
            <div><b>{round(sum(seo_vals)/max(1,len(seo_vals)),1)}</b><span>avg SEO</span></div>
            <div><b>{round(sum(qc_vals)/max(1,len(qc_vals)),1)}</b><span>avg QC</span></div>
            <div><b>{int(conf*100)}%</b><span>learning</span></div>
            <div><b>{links}</b><span>aff. links</span></div>
          </div>
          <div class="spark-row">
            <div>SEO {_spark(seo_vals, "#0984e3")}</div>
            <div>QC {_spark(qc_vals, "#00b894")}</div>
          </div>
          <div class="kw-block"><h4>Learned keyword boosts</h4>{kw_html}</div>
        </div>"""

    # accounts
    acc = account_summary(app.defaults.get("accounts", {}))
    acc_html = "".join(
        f'<tr><td>{p}</td><td>{v["configured"]}</td><td>{v["healthy"]}</td>'
        f'<td>{_bar(v["healthy"], max(v["configured"],1), "#e17055", 120)}</td></tr>'
        for p, v in acc.items()) or '<tr><td colspan=4 class="muted">no pools configured</td></tr>'

    # earnings projection (× number of sites)
    n_sites = len(app.niches)
    proj_html = "".join(
        f'<tr><td>M{m}</td><td>{posts*n_sites}</td><td>{traffic*n_sites:,}</td>'
        f'<td>${ad*n_sites}</td><td>${aff*n_sites}</td><td><b>${(ad+aff)*n_sites}</b></td></tr>'
        for m, posts, traffic, ad, aff in PROJECTION)

    # geo/aeo coverage
    geo = sum(1 for a in arts if a.get("meta", {}).get("geo_aeo"))

    # brain intelligence (knowledge engine)
    from core.knowledge import load_kb
    kb = load_kb(force=True)
    ks = kb.stats()
    max_w = max((w for _, w in ks["top_weighted"]), default=1)
    brain_rows = "".join(
        f'<div class="kw"><span>{cid}</span>{_bar(w, max_w, "#e84393", 130)}<b>{w:.2f}</b></div>'
        for cid, w in ks["top_weighted"])
    brain_html = f"""
    <div class="card" style="grid-column:1/-1">
      <div class="card-h"><div><h3>🧠 Brain intelligence</h3>
      <span class="muted">{ks['cards']} expert rules across {len(ks['files'])} playbooks · reinforced by results</span></div>
      <div class="badge">self-training</div></div>
      <div class="kw-block"><h4>Most effective rules (weight ↑ = earns more)</h4>{brain_rows}</div>
    </div>"""

    refresh_tag = f'<meta http-equiv="refresh" content="{auto_refresh}">' if auto_refresh else ""
    html = f"""<!doctype html><html><head><meta charset="utf-8">
{refresh_tag}
<title>Earning System — Control Center</title>
<style>
  :root{{--bg:#0f1220;--card:#fff;--ink:#1a1d29;--muted:#8a91a5}}
  *{{box-sizing:border-box}}
  body{{margin:0;font-family:system-ui,Segoe UI,Arial;background:linear-gradient(180deg,#0f1220,#1a1f36);color:var(--ink)}}
  .wrap{{max-width:1080px;margin:0 auto;padding:28px 18px 60px}}
  header{{color:#fff;margin-bottom:22px}}
  header h1{{margin:0 0 4px;font-size:26px}}
  header p{{margin:0;color:#aab2cc}}
  .kpis{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:18px 0 26px}}
  .kpi{{background:var(--card);border-radius:14px;padding:16px;text-align:center;box-shadow:0 6px 20px rgba(0,0,0,.25)}}
  .kpi b{{display:block;font-size:26px;color:#4834d4}}
  .kpi span{{color:var(--muted);font-size:12px}}
  h2{{color:#fff;font-size:16px;margin:26px 0 12px;border-left:3px solid #6c5ce7;padding-left:10px}}
  .grid{{display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px}}
  .card{{background:var(--card);border-radius:14px;padding:16px;box-shadow:0 6px 20px rgba(0,0,0,.2)}}
  .card-h{{display:flex;justify-content:space-between;align-items:flex-start}}
  .card h3{{margin:0;font-size:15px}}
  .badge{{background:#eef0ff;color:#4834d4;font-size:11px;padding:3px 8px;border-radius:20px;font-weight:600}}
  .muted{{color:var(--muted);font-size:12px}}
  .stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;margin:14px 0}}
  .stats div{{text-align:center}}
  .stats b{{display:block;font-size:18px;color:#1a1d29}}
  .stats span{{font-size:10px;color:var(--muted)}}
  .spark-row{{display:flex;gap:16px;font-size:11px;color:var(--muted);align-items:center;margin-bottom:10px}}
  .kw-block h4{{margin:8px 0 6px;font-size:12px;color:#555}}
  .kw{{display:flex;align-items:center;gap:8px;font-size:11px;margin:3px 0}}
  .kw span{{width:110px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
  .kw b{{color:#6c5ce7}}
  table{{width:100%;border-collapse:collapse;background:var(--card);border-radius:14px;overflow:hidden;box-shadow:0 6px 20px rgba(0,0,0,.2)}}
  th,td{{padding:9px 12px;text-align:left;font-size:13px;border-bottom:1px solid #eef1f6}}
  th{{background:#f7f8fc;color:#555;font-size:11px;text-transform:uppercase;letter-spacing:.4px}}
  .two{{display:grid;grid-template-columns:1fr 1fr;gap:14px;align-items:start}}
</style></head><body><div class="wrap">
<header>
  <h1>🚀 Trend-Driven Earning System — Control Center</h1>
  <p>Agentic · adaptive · multi-account · GEO/AEO · generated {now}</p>
</header>

<div class="kpis">
  <div class="kpi"><b>{total_posts}</b><span>ARTICLES</span></div>
  <div class="kpi"><b>{published}</b><span>PUBLISHED</span></div>
  <div class="kpi"><b>{avg_seo}</b><span>AVG SEO</span></div>
  <div class="kpi"><b>{avg_qc}</b><span>AVG QC</span></div>
  <div class="kpi"><b>{geo}/{total_posts}</b><span>GEO/AEO</span></div>
</div>

<h2>Niche agents</h2>
<div class="grid">{niche_rows}</div>

<h2>Brain training</h2>
<div class="grid">{brain_html}</div>

<div class="two">
  <div>
    <h2>Multi-account health</h2>
    <table><tr><th>Platform</th><th>Configured</th><th>Healthy</th><th>Coverage</th></tr>{acc_html}</table>
  </div>
  <div>
    <h2>Earnings projection ({n_sites} sites)</h2>
    <table><tr><th>Month</th><th>Posts</th><th>Traffic</th><th>AdSense</th><th>Affiliate</th><th>Total</th></tr>{proj_html}</table>
  </div>
</div>

<h2>System capabilities</h2>
<div class="card">
  <p class="muted" style="line-height:1.7">
  ✅ 4 niche agents · distinct LLM brains (Gemini / Groq / Qwen3)<br>
  ✅ 9-step pipeline: trend → research → market → write → SEO → GEO/AEO → image → QC → publish<br>
  ✅ Knowledge engine — 31+ expert rules (trending + earning + SEO/GEO + 2030 future) fed to every brain, self-reinforced by results<br>
  ✅ Adaptive brain — writers conditioned on each site's own performance data<br>
  ✅ Market strategy — buyer-intent scoring + best affiliate platform + trending products<br>
  ✅ Agentic strategist — daily plan by opportunity score<br>
  ✅ Multi-account rotation — spread syndication risk across account pools<br>
  ✅ Monetization — affiliate injection + FTC/Amazon disclosure + AdSense slots<br>
  ✅ Future-safe — FAQ schema, key-takeaways, llms.txt for AI answer engines<br>
  ✅ Feedback loop — GSC metrics raise keyword boosts for the next run
  </p>
</div>
</div></body></html>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(html, encoding="utf-8")
    return OUT


def serve(port: int, refresh: int) -> None:
    """Live mode: rebuild on each request + auto-refresh the page."""
    import http.server
    import socketserver

    class Handler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            build(auto_refresh=refresh)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(OUT.read_bytes())

        def log_message(self, *a):  # silence
            pass

    with socketserver.TCPServer(("0.0.0.0", port), Handler) as httpd:
        print(f"live dashboard on http://0.0.0.0:{port} (rebuilds each load)")
        httpd.serve_forever()


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="run a live auto-refreshing server")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--refresh", type=int, default=0, help="auto-refresh seconds")
    args = ap.parse_args()
    if args.serve:
        serve(args.port, args.refresh or 15)
    else:
        p = build(auto_refresh=args.refresh)
        print(f"dashboard -> {p}")
