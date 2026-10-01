#!/usr/bin/env python3
"""
ANALYTICS + LEARN (feedback loop).

Pulls Search Console performance per site and feeds it into per-niche memory
(core.state). High-CTR / well-ranked keywords get boosted so the next trend
run prefers similar directions — "yeh topic 3x CTR de raha hai -> aur banao".

Run this on its own schedule (e.g. daily/weekly) via GitHub Actions.
"""
from __future__ import annotations

import glob
import json

from connectors.gsc import fetch_performance
from core.config import DATA_DIR, load_config
from core.knowledge import load_kb
from core.logging_utils import get_logger
from core.state import record_performance

log = get_logger("learn")


def _reinforce_knowledge(app) -> None:
    """
    Tie real performance back to the expert knowledge cards that produced it.
    For each niche's latest article we reward the cards it used, scaled by that
    niche's best measured CTR — so advice that correlates with clicks gains weight.
    """
    kb = load_kb(force=True)
    kb.decay()  # gently pull all weights toward 1.0 so winners must keep earning
    for niche_id, niche in app.niches.items():
        rows = fetch_performance(f"https://{niche.domain}")
        best_ctr = max((r["ctr"] for r in rows), default=0.0)
        latest = sorted(glob.glob(str(DATA_DIR / "runs" / "*" / f"{niche_id}.json")))
        if not latest:
            continue
        data = json.loads(open(latest[-1]).read())
        cards = data.get("meta", {}).get("knowledge_cards", [])
        if cards and best_ctr > 0:
            kb.reinforce(cards, reward=round(best_ctr * 5, 4))
    log.info("knowledge reinforcement complete | %s", kb.stats()["top_weighted"][:4])


def main() -> int:
    app = load_config()
    for niche_id, niche in app.niches.items():
        site = f"https://{niche.domain}"
        rows = fetch_performance(site)
        log.info("niche=%s | %d GSC rows", niche_id, len(rows))
        for r in rows:
            record_performance(
                niche_id=niche_id,
                topic_title=r["query"],
                keywords=[r["query"]],
                clicks=r["clicks"],
                ctr=r["ctr"],
                position=r["position"],
            )
    _reinforce_knowledge(app)
    log.info("learning loop complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
