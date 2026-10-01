#!/usr/bin/env python3
"""
BRAIN TRAINER — inspect, test, feed and train the knowledge engine.

The brain is "trained" by (a) the expert playbooks in knowledge/*.yaml and
(b) reinforcement weights learned from real performance. This CLI lets you drive
all of it.

Commands:
  python brain_train.py status
      Show how much the brain knows + which rules are weighted highest.

  python brain_train.py show "best ai video generator vs alternatives" [--niche agent_4_ai_visual]
      Show the exact expert briefing the writer would receive for a topic
      (proof of intelligent, context-aware reasoning).

  python brain_train.py add --file custom --id my_rule --title "My rule" \
      --tags "affiliate,cta" --applies-to all --rule "Do X because Y."
      Feed the brain a new piece of knowledge (persisted to knowledge/custom.yaml).

  python brain_train.py train
      Run a reinforcement cycle from current performance data.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from core.knowledge import KB_DIR, load_kb
from core.logging_utils import get_logger

log = get_logger("brain_train")


def cmd_status(_args) -> int:
    kb = load_kb(force=True)
    s = kb.stats()
    print(f"\n🧠 BRAIN KNOWLEDGE STATUS")
    print(f"   cards loaded : {s['cards']}")
    print(f"   sources      : {', '.join(s['files'])}")
    print(f"\n   top-weighted rules (most reinforced by results):")
    for cid, w in s["top_weighted"]:
        bar = "█" * int((w) * 8)
        print(f"     {w:5.2f} {bar:<20} {cid}")
    print()
    return 0


def cmd_show(args) -> int:
    kb = load_kb(force=True)
    brief, ids = kb.briefing(args.query, niche_id=args.niche, tier=args.tier, k=args.k)
    print(f"\n🔎 Query: {args.query!r} | niche={args.niche} tier={args.tier}")
    print(f"   retrieved cards: {ids}\n")
    print(brief or "   (no relevant knowledge found)")
    print()
    return 0


def cmd_add(args) -> int:
    path = KB_DIR / f"{args.file}.yaml"
    KB_DIR.mkdir(exist_ok=True)
    data = {"cards": []}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {"cards": []}
        data.setdefault("cards", [])
    card = {
        "id": args.id,
        "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
        "applies_to": [t.strip() for t in args.applies_to.split(",") if t.strip()],
        "title": args.title,
        "rule": args.rule,
    }
    # replace if id exists
    data["cards"] = [c for c in data["cards"] if c.get("id") != args.id] + [card]
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    kb = load_kb(force=True)
    print(f"✅ Added/updated card '{args.id}' in {path.name}. "
          f"Brain now knows {len(kb.cards)} rules.")
    return 0


def cmd_train(_args) -> int:
    from core.config import load_config
    from learn import _reinforce_knowledge
    app = load_config()
    print("🏋️  Running reinforcement cycle from performance data…")
    _reinforce_knowledge(app)
    return cmd_status(_args)


def main() -> int:
    ap = argparse.ArgumentParser(description="Train / inspect the knowledge brain")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status").set_defaults(func=cmd_status)

    p_show = sub.add_parser("show")
    p_show.add_argument("query")
    p_show.add_argument("--niche", default="all")
    p_show.add_argument("--tier", default="all")
    p_show.add_argument("--k", type=int, default=6)
    p_show.set_defaults(func=cmd_show)

    p_add = sub.add_parser("add")
    p_add.add_argument("--file", default="custom")
    p_add.add_argument("--id", required=True)
    p_add.add_argument("--title", required=True)
    p_add.add_argument("--tags", required=True)
    p_add.add_argument("--applies-to", default="all", dest="applies_to")
    p_add.add_argument("--rule", required=True)
    p_add.set_defaults(func=cmd_add)

    sub.add_parser("train").set_defaults(func=cmd_train)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
