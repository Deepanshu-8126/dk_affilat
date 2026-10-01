"""
AGENTIC STRATEGIST — the autonomous "brain of brains".

Before any content is written, the strategist looks across ALL niches and
decides the day's plan:
  * which niches to publish today (and in what priority order),
  * the best content_type for each (based on what the niche's data rewards),
  * a focus theme drawn from the strongest fresh trend,
  * and a short rationale.

It reasons with an LLM when a key is available, and always has a deterministic
opportunity-scoring fallback so it runs offline. Output is a DailyPlan that
run.py can act on — this is what makes the system agentic rather than a fixed
cron of 3 jobs.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict

from core.adaptive import build_learned_directive
from core.config import AppConfig
from core.llm import Brain
from core.logging_utils import get_logger
from pipeline.trend_detect import TrendContext, detect

log = get_logger("strategist")


@dataclass
class NichePlan:
    niche_id: str
    publish: bool
    priority: int                 # 1 = highest
    opportunity: float            # 0-100 blended score
    content_type: str
    focus_theme: str
    top_topic: str
    rationale: str = ""


@dataclass
class DailyPlan:
    plans: list[NichePlan] = field(default_factory=list)
    summary: str = ""

    def to_publish(self) -> list[NichePlan]:
        return sorted([p for p in self.plans if p.publish], key=lambda p: p.priority)

    def to_dict(self) -> dict:
        return {"summary": self.summary, "plans": [asdict(p) for p in self.plans]}


class Strategist:
    def __init__(self, app: AppConfig):
        self.app = app
        # Use the first configured brain that has a key, else any (offline ok).
        self.brain = self._pick_brain()

    def _pick_brain(self) -> Brain:
        for b in self.app.brains.values():
            if b.api_key:
                return Brain(b)
        return Brain(next(iter(self.app.brains.values())))

    # -- opportunity scoring ------------------------------------------------
    def _score_niche(self, niche_id: str) -> tuple[float, list, "object"]:
        niche = self.app.niche(niche_id)
        topics = detect(TrendContext(
            niche_id=niche_id,
            seed_keywords=niche.keywords_seed,
            sources=niche.trend_sources,
            n=self.app.defaults.get("trends_per_run", 3),
        ))
        learned = build_learned_directive(niche_id)
        trend_heat = topics[0].score if topics else 0.0
        # blend: fresh trend heat + learning confidence + momentum
        momentum = max((t.momentum for t in topics), default=0.0)
        opportunity = min(100.0, 0.5 * trend_heat + 25 * learned.confidence
                          + 0.1 * momentum)
        return round(opportunity, 1), topics, learned

    def _best_content_type(self, niche_id: str, learned) -> str:
        niche = self.app.niche(niche_id)
        types = niche.content_types or ["guide"]
        # If we've learned winners, bias toward "review"/"comparison" style that
        # tends to monetize; else first configured type.
        if learned.confidence > 0.3 and any("review" in t for t in types):
            return next(t for t in types if "review" in t)
        return types[0]

    # -- planning -----------------------------------------------------------
    def plan_day(self, *, max_publish: int | None = None) -> DailyPlan:
        max_publish = max_publish or len(self.app.niches)
        scored: list[NichePlan] = []
        for niche_id in self.app.niches:
            opp, topics, learned = self._score_niche(niche_id)
            top = topics[0] if topics else None
            scored.append(NichePlan(
                niche_id=niche_id,
                publish=False,
                priority=99,
                opportunity=opp,
                content_type=self._best_content_type(niche_id, learned),
                focus_theme=(top.keywords[0] if top and top.keywords else ""),
                top_topic=(top.title if top else "(no fresh topic)"),
                rationale=(f"trend heat + learning conf {learned.confidence:.2f}"),
            ))

        scored.sort(key=lambda p: p.opportunity, reverse=True)
        for i, p in enumerate(scored):
            p.priority = i + 1
            p.publish = (i < max_publish) and p.top_topic != "(no fresh topic)"

        plan = DailyPlan(plans=scored)
        plan.summary = self._narrate(scored)
        log.info("DAILY PLAN: %s", plan.summary)
        return plan

    def _narrate(self, scored: list[NichePlan]) -> str:
        ranked = ", ".join(f"{p.niche_id}({p.opportunity})" for p in scored)
        # Optional LLM one-liner rationale (falls back to deterministic).
        system = ("You are a content strategist. In ONE sentence, justify the "
                  "publishing priority. Be concrete, no fluff.")
        prompt = ("TOPIC: daily publishing plan\n"
                  "Niches ranked by opportunity: " + ranked + "\n"
                  "Give a one-line rationale.")
        try:
            r = self.brain.complete(system, prompt)
            if not r.fallback:
                return r.text.strip().splitlines()[0]
        except Exception:  # noqa: BLE001
            pass
        top = scored[0]
        return (f"Lead with {top.niche_id} (opportunity {top.opportunity}) — "
                f"'{top.top_topic}'. Order by opportunity: {ranked}.")


def save_plan(plan: DailyPlan, path: str) -> None:
    from pathlib import Path
    Path(path).write_text(json.dumps(plan.to_dict(), indent=2), encoding="utf-8")
