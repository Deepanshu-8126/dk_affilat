#!/usr/bin/env python3
"""
MASTER ORCHESTRATOR.

Runs the 3 niche agents (optionally in parallel), each producing 1 post.
Adds a small random jitter per agent so publish times are never fixed.

Usage:
  python run.py                      # all niches
  python run.py --only agent_1_ai_tools
  python run.py --sequential         # one at a time
  python run.py --no-jitter          # skip random delay (CI/tests)

Env flags of interest (see .env.example):
  DRY_RUN=true            # simulate publish (default)
  REQUIRE_APPROVAL=true   # Telegram HITL gate
  AUTO_APPROVE=true       # bypass approval (unattended)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import os
import random
import time
import uuid

from core.agent import BaseNicheAgent
from core.config import load_config
from core.logging_utils import get_logger
from core.strategist import Strategist, save_plan

log = get_logger("orchestrator")


def _run_one(app, niche_id: str, run_id: str, jitter: bool):
    if jitter:
        delay = random.randint(0, 45)
        log.info("niche=%s jitter %ds (random publish timing)", niche_id, delay)
        time.sleep(delay)
    try:
        return BaseNicheAgent(app, niche_id, run_id).run()
    except Exception as e:  # noqa: BLE001
        log.exception("niche=%s crashed: %s", niche_id, e)
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="run a single niche id")
    ap.add_argument("--sequential", action="store_true")
    ap.add_argument("--no-jitter", action="store_true")
    ap.add_argument("--agentic", action="store_true",
                    help="let the strategist decide which niches to publish & order")
    ap.add_argument("--plan-only", action="store_true",
                    help="just print the strategist's daily plan and exit")
    args = ap.parse_args()

    app = load_config()
    run_id = time.strftime("%Y%m%d-") + uuid.uuid4().hex[:6]

    strat_cfg = app.defaults.get("strategy", {})
    use_agentic = (args.agentic or args.plan_only
                   or strat_cfg.get("mode") == "agentic") and not args.only

    if use_agentic:
        log.info("AGENTIC MODE — strategist planning the day…")
        strat = Strategist(app)
        plan = strat.plan_day(max_publish=strat_cfg.get("max_publish_per_day"))
        save_plan(plan, "data/daily_plan.json")
        for p in plan.plans:
            log.info("  #%d %-24s opp=%-5s publish=%s type=%s theme='%s' | %s",
                     p.priority, p.niche_id, p.opportunity, p.publish,
                     p.content_type, p.focus_theme, p.top_topic)
        if args.plan_only:
            return 0
        min_opp = strat_cfg.get("min_opportunity", 0)
        niches = [p.niche_id for p in plan.to_publish() if p.opportunity >= min_opp]
    else:
        niches = [args.only] if args.only else list(app.niches)

    log.info("run_id=%s | dry_run=%s | approval=%s | niches=%s",
             run_id, app.dry_run, app.require_approval, niches)

    results = []
    jitter = not args.no_jitter
    if args.sequential or len(niches) == 1:
        for n in niches:
            results.append(_run_one(app, n, run_id, jitter))
    else:
        with cf.ThreadPoolExecutor(max_workers=len(niches)) as ex:
            futs = {ex.submit(_run_one, app, n, run_id, jitter): n for n in niches}
            for fut in cf.as_completed(futs):
                results.append(fut.result())

    published = sum(1 for r in results if r and any(t.ok for t in r.published))
    log.info("=== SUMMARY run_id=%s | %d/%d agents published ===",
             run_id, published, len(niches))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
