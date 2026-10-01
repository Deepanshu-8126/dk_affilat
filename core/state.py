"""
Lightweight JSON state store + feedback/learning memory.

Two responsibilities:
  1. Persist each run's articles under data/runs/<run_id>/ for auditing & HITL.
  2. Keep a per-niche performance memory (data/memory/<niche>.json) that the
     trend/write steps read to bias toward what performed well (the feedback
     loop described in the PRD's "Analytics + Learn" block).
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from core.config import DATA_DIR
from core.logging_utils import get_logger

log = get_logger("state")

RUNS_DIR = DATA_DIR / "runs"
MEMORY_DIR = DATA_DIR / "memory"
SEEN_DIR = DATA_DIR / "seen"


def _ensure() -> None:
    for d in (RUNS_DIR, MEMORY_DIR, SEEN_DIR):
        d.mkdir(parents=True, exist_ok=True)


def save_article(run_id: str, article_dict: dict[str, Any]) -> Path:
    _ensure()
    run_dir = RUNS_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    niche = article_dict.get("niche_id", "unknown")
    path = run_dir / f"{niche}.json"
    path.write_text(json.dumps(article_dict, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def load_article(run_id: str, niche_id: str) -> dict[str, Any] | None:
    path = RUNS_DIR / run_id / f"{niche_id}.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


# --- de-dup: never write the same topic twice ------------------------------
def _seen_path(niche_id: str) -> Path:
    _ensure()
    return SEEN_DIR / f"{niche_id}.json"


def already_covered(niche_id: str, topic_key: str) -> bool:
    p = _seen_path(niche_id)
    if not p.exists():
        return False
    return topic_key in set(json.loads(p.read_text(encoding="utf-8")))


def mark_covered(niche_id: str, topic_key: str) -> None:
    p = _seen_path(niche_id)
    seen = set(json.loads(p.read_text(encoding="utf-8"))) if p.exists() else set()
    seen.add(topic_key)
    p.write_text(json.dumps(sorted(seen)), encoding="utf-8")


# --- feedback / learning memory --------------------------------------------
def _memory_path(niche_id: str) -> Path:
    _ensure()
    return MEMORY_DIR / f"{niche_id}.json"


def load_memory(niche_id: str) -> dict[str, Any]:
    p = _memory_path(niche_id)
    if not p.exists():
        return {"niche_id": niche_id, "topics": {}, "keyword_boosts": {}, "updated": 0}
    return json.loads(p.read_text(encoding="utf-8"))


def save_memory(niche_id: str, memory: dict[str, Any]) -> None:
    memory["updated"] = time.time()
    _memory_path(niche_id).write_text(json.dumps(memory, indent=2), encoding="utf-8")


def record_performance(niche_id: str, topic_title: str, keywords: list[str],
                       clicks: int, ctr: float, position: float) -> None:
    """
    Feed GSC metrics back in. High-CTR / good-position topics raise the boost
    for their keywords so future trend scoring prefers similar directions.
    """
    mem = load_memory(niche_id)
    mem["topics"][topic_title] = {"clicks": clicks, "ctr": ctr, "position": position}
    # Reward keywords tied to strong performers
    reward = (ctr * 10) + max(0, (20 - position)) + (clicks / 50.0)
    for kw in keywords:
        mem["keyword_boosts"][kw.lower()] = round(
            mem["keyword_boosts"].get(kw.lower(), 0.0) + reward, 3)
    save_memory(niche_id, mem)
    log.info("recorded performance for %s (reward=%.2f)", topic_title, reward)


def keyword_boost(niche_id: str, keyword: str) -> float:
    return load_memory(niche_id)["keyword_boosts"].get(keyword.lower(), 0.0)
