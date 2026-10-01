#!/usr/bin/env python3
"""
Standalone Telegram approval listener (HITL).

Two ways approval works in this system:

1) Inline (default): each agent calls telegram.send_card() then
   telegram.poll_decision() and blocks until you tap a button. Good for a
   single interactive run.

2) This listener: run it separately to review any articles saved in
   data/runs/ that are still PENDING. It shows a card per article and applies
   your decision (approve -> publish, reject/rewrite -> mark & skip).

Usage:
  python telegram_approval.py                 # review latest run
  python telegram_approval.py --run 20260930-abc123
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from connectors import telegram
from connectors.wordpress import WordPressClient
from core.config import DATA_DIR, load_config
from core.logging_utils import get_logger
from core.models import ApprovalDecision
from pipeline import publish

log = get_logger("approval")
RUNS = DATA_DIR / "runs"


def _latest_run() -> str | None:
    if not RUNS.exists():
        return None
    runs = sorted([p.name for p in RUNS.iterdir() if p.is_dir()])
    return runs[-1] if runs else None


def review_run(run_id: str) -> None:
    app = load_config()
    run_dir = RUNS / run_id
    if not run_dir.exists():
        log.error("run %s not found", run_id)
        return
    for f in sorted(run_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        if data.get("approval") not in (ApprovalDecision.PENDING.value, None):
            continue
        title = data.get("title", "(untitled)")
        niche_id = data.get("niche_id")
        seo = data.get("seo", {}).get("score", 0)
        qc = data.get("qc", {}).get("score", 0)
        print(f"\n=== {niche_id} | {title} ===")
        print(f"SEO {seo} | QC {qc} | words {len(data.get('body_markdown','').split())}")

        decision = telegram.poll_decision(run_id, niche_id, timeout=600)
        log.info("decision for %s: %s", niche_id, decision)
        if decision != "approve":
            data["approval"] = decision
            f.write_text(json.dumps(data, indent=2), encoding="utf-8")
            continue

        # publish
        niche = app.niche(niche_id)
        creds = niche.wp_credentials()
        wp = WordPressClient(creds["base_url"], creds["user"], creds["app_password"])
        # rebuild a minimal object surface publish.publish needs
        from core.models import Article, SeoReport
        art = Article(niche_id=niche_id, run_id=run_id,
                      title=title, body_markdown=data.get("body_markdown", ""),
                      author_name=data.get("author_name", ""),
                      author_bio=data.get("author_bio", ""),
                      tags=data.get("tags", []))
        s = data.get("seo", {})
        art.seo = SeoReport(**{k: s.get(k) for k in SeoReport().__dict__ if k in s})
        art.meta = data.get("meta", {})
        art.meta.setdefault("monetization", data.get("meta", {}).get("monetization", {}))
        targets = publish.publish(
            art, wp,
            platforms=niche.defaults.get("publish_platforms", ["wordpress"]),
            index_now=niche.defaults.get("index_now", True),
            domain=niche.domain,
            mon=niche.defaults.get("monetization", {}),
        )
        data["approval"] = "approve"
        data["published"] = [t.__dict__ for t in targets]
        f.write_text(json.dumps(data, indent=2), encoding="utf-8")
        log.info("published %s", title)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", help="run id (default: latest)")
    args = ap.parse_args()
    run_id = args.run or _latest_run()
    if not run_id:
        log.error("no runs found in %s", RUNS)
        return 1
    review_run(run_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
