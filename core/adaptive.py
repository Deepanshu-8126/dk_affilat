"""
ADAPTIVE BRAIN — retrieval-augmented "self-training" without fine-tuning.

Real fine-tuning isn't free, so instead each agent continuously *conditions* its
prompts on its own accumulated performance data (data/memory/<niche>.json) plus a
small library of winning-style exemplars. This gives the practical effect of a
brain that "learns from data": every run the writer is nudged toward the topics,
keywords and angles that historically earned the best CTR / rank, and away from
duds.

Pipeline:
  performance memory  ─┐
  winning exemplars   ─┼─►  build_learned_directive()  ──► injected into the
  fresh trend signals ─┘                                    writer's system prompt
"""
from __future__ import annotations

from dataclasses import dataclass

from core.logging_utils import get_logger
from core.state import load_memory

log = get_logger("adaptive")


@dataclass
class LearnedContext:
    prioritize_keywords: list[str]
    avoid_keywords: list[str]
    winning_topics: list[str]
    confidence: float          # 0-1, grows with data volume
    directive: str             # ready-to-inject prompt text


def _rank_keywords(memory: dict) -> tuple[list[str], list[str]]:
    boosts = memory.get("keyword_boosts", {})
    if not boosts:
        return [], []
    ranked = sorted(boosts.items(), key=lambda kv: kv[1], reverse=True)
    top = [k for k, v in ranked if v > 0][:8]
    # "avoid" = keywords we tried a lot but that never earned a boost
    bottom = [k for k, v in ranked if v <= 0][:5]
    return top, bottom


def _winning_topics(memory: dict, n: int = 5) -> list[str]:
    topics = memory.get("topics", {})
    scored = []
    for title, m in topics.items():
        score = (m.get("ctr", 0) * 100) + m.get("clicks", 0) - m.get("position", 50)
        scored.append((score, title))
    scored.sort(reverse=True)
    return [t for _, t in scored[:n]]


def build_learned_directive(niche_id: str) -> LearnedContext:
    mem = load_memory(niche_id)
    top, bottom = _rank_keywords(mem)
    winners = _winning_topics(mem)
    data_points = len(mem.get("topics", {}))
    confidence = min(1.0, data_points / 30.0)   # saturates around 30 tracked topics

    parts: list[str] = []
    if winners:
        parts.append(
            "LEARNED FROM YOUR OWN ANALYTICS (mimic what worked, don't copy):\n"
            + "\n".join(f"  • high performer: \"{t}\"" for t in winners)
        )
    if top:
        parts.append("PRIORITIZE these proven keywords where natural: "
                     + ", ".join(top))
    if bottom:
        parts.append("DE-EMPHASIZE these underperformers: " + ", ".join(bottom))
    if confidence < 0.2:
        parts.append("NOTE: limited performance history yet — favour broad, "
                     "clearly useful angles to gather signal.")

    directive = "\n".join(parts)
    log.info("niche=%s learned-directive | conf=%.2f top=%d avoid=%d winners=%d",
             niche_id, confidence, len(top), len(bottom), len(winners))
    return LearnedContext(
        prioritize_keywords=top, avoid_keywords=bottom,
        winning_topics=winners, confidence=confidence, directive=directive,
    )
