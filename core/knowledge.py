"""
KNOWLEDGE ENGINE — the "training" layer.

Loads the expert playbooks in knowledge/*.yaml and, for any topic + niche +
commercial tier, retrieves the most relevant rules and compiles them into an
"expert briefing" that is injected into the writer, strategist and market brains.

This is retrieval-augmented conditioning ("feed it data") plus a self-training
loop: cards that appear in high-performing posts get their weight raised
(reinforcement), so over time the system leans on the advice that actually earns.
No paid fine-tuning, no external deps — but the practical effect is a brain that
reasons like a seasoned SEO + affiliate expert and keeps getting sharper.

    knowledge/*.yaml ─► load cards ─► retrieve(topic,niche,tier) ─► briefing
                                          ▲                              │
                          weights (reinforced) ◄── record_performance ──┘
"""
from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from core.config import DATA_DIR, ROOT
from core.logging_utils import get_logger

log = get_logger("knowledge")

KB_DIR = ROOT / "knowledge"
WEIGHTS_PATH = DATA_DIR / "knowledge_weights.json"

_STOP = set("a an the and or of to in on for with at by from is are be this that "
            "you your how what why best vs it its as if not no".split())


def _tokenize(text: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in _STOP and len(t) > 1]


@dataclass
class Card:
    id: str
    tags: list[str]
    applies_to: list[str]
    title: str
    rule: str
    source: str = ""
    weight: float = 1.0
    _terms: set[str] = field(default_factory=set)

    def matches_scope(self, niche_id: str, tier: str) -> bool:
        scope = set(self.applies_to)
        return ("all" in scope or niche_id in scope or tier in scope)


class KnowledgeBase:
    def __init__(self, cards: list[Card]):
        self.cards = cards
        self._by_id = {c.id: c for c in cards}

    # -- retrieval ---------------------------------------------------------
    def retrieve(self, query: str, *, niche_id: str = "all", tier: str = "all",
                 k: int = 5) -> list[Card]:
        q_terms = set(_tokenize(query))
        scored: list[tuple[float, Card]] = []
        for c in self.cards:
            if not c.matches_scope(niche_id, tier):
                continue
            tag_terms = set(_tokenize(" ".join(c.tags)))
            overlap_tags = len(q_terms & tag_terms)
            overlap_body = len(q_terms & c._terms)
            scope_bonus = 2.0 if (niche_id in c.applies_to or tier in c.applies_to) else 0.0
            base = overlap_tags * 3 + overlap_body * 0.5 + scope_bonus
            # everything relevant gets at least a small base so weight matters
            score = (base + 0.5) * c.weight
            scored.append((score, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored[:k]]

    def briefing(self, query: str, *, niche_id: str = "all", tier: str = "all",
                 k: int = 5) -> tuple[str, list[str]]:
        cards = self.retrieve(query, niche_id=niche_id, tier=tier, k=k)
        if not cards:
            return "", []
        lines = ["--- EXPERT PLAYBOOK (apply these proven rules) ---"]
        for c in cards:
            rule = " ".join(c.rule.split())
            lines.append(f"• {c.title}: {rule}")
        return "\n".join(lines), [c.id for c in cards]

    # -- self-training / reinforcement -------------------------------------
    def reinforce(self, card_ids: list[str], reward: float) -> None:
        """Raise weights of cards tied to a good outcome; mild decay on others."""
        weights = _load_weights()
        for cid in card_ids:
            if cid in self._by_id:
                weights[cid] = round(weights.get(cid, 1.0) + reward, 4)
        _save_weights(weights)
        self._apply_weights(weights)
        log.info("reinforced %d card(s) reward=%.3f", len(card_ids), reward)

    def decay(self, factor: float = 0.995) -> None:
        weights = _load_weights()
        for c in self.cards:
            w = weights.get(c.id, 1.0)
            weights[c.id] = round(1.0 + (w - 1.0) * factor, 4)  # pull toward 1.0
        _save_weights(weights)
        self._apply_weights(weights)

    def _apply_weights(self, weights: dict) -> None:
        for c in self.cards:
            c.weight = max(0.2, weights.get(c.id, 1.0))

    def stats(self) -> dict:
        return {
            "cards": len(self.cards),
            "files": sorted({c.source for c in self.cards}),
            "top_weighted": sorted(
                [(c.id, round(c.weight, 3)) for c in self.cards],
                key=lambda x: x[1], reverse=True)[:8],
        }


# --- module-level helpers --------------------------------------------------
def _load_weights() -> dict:
    if WEIGHTS_PATH.exists():
        return json.loads(WEIGHTS_PATH.read_text(encoding="utf-8"))
    return {}


def _save_weights(weights: dict) -> None:
    WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    WEIGHTS_PATH.write_text(json.dumps(weights, indent=2), encoding="utf-8")


_CACHE: KnowledgeBase | None = None


def load_kb(force: bool = False) -> KnowledgeBase:
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    cards: list[Card] = []
    weights = _load_weights()
    if KB_DIR.exists():
        for f in sorted(KB_DIR.glob("*.yaml")):
            data = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
            for raw in data.get("cards", []):
                c = Card(
                    id=raw["id"], tags=[str(t) for t in raw.get("tags", [])],
                    applies_to=[str(a) for a in raw.get("applies_to", ["all"])],
                    title=raw.get("title", raw["id"]), rule=raw.get("rule", ""),
                    source=f.stem, weight=max(0.2, weights.get(raw["id"], 1.0)),
                )
                c._terms = set(_tokenize(c.title + " " + c.rule + " " + " ".join(c.tags)))
                cards.append(c)
    log.info("loaded %d knowledge cards from %d file(s)",
             len(cards), len({c.source for c in cards}))
    _CACHE = KnowledgeBase(cards)
    return _CACHE
