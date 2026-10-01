"""
STEP 3 — WRITE (the agent's hands).

Multi-agent writing chain (raghul-tech style) run through the niche's own brain:
    Planner -> Writer -> Editor -> Proofreader
Each stage is a focused LLM call with the niche persona/tone baked into the
system prompt, then the deterministic humanizer runs on top.

The result is a 1500-2500 word Markdown post written "in character".
"""
from __future__ import annotations

from dataclasses import dataclass

from core.llm import Brain
from core.logging_utils import get_logger
from core.models import ResearchBrief
from pipeline.humanize import humanize

log = get_logger("write")


@dataclass
class WriterPersona:
    author_name: str
    author_title: str
    tone: str
    niche_name: str


def _persona_system(p: WriterPersona, role: str, learned: str = "") -> str:
    base = (
        f"You are {p.author_name}, {p.author_title}, writing for a {p.niche_name} "
        f"blog. Voice/tone: {p.tone}.\n"
        f"Current role: {role}.\n"
        "Hard rules:\n"
        "- Write like a real, experienced human. Vary sentence length.\n"
        "- No filler intros ('In today's fast-paced world'), no 'In conclusion'.\n"
        "- Be specific and concrete; use real numbers, names and steps.\n"
        "- Second person where natural; opinionated but fair.\n"
        "- Markdown only. Use ## for sections, short paragraphs, lists where useful."
    )
    if learned:
        base += f"\n\n--- ADAPTIVE GUIDANCE (from this site's performance data) ---\n{learned}"
    return base


def _plan(brain: Brain, persona: WriterPersona, brief: ResearchBrief,
          learned: str = "") -> str:
    system = _persona_system(persona, "Planner", learned)
    facts = "\n".join(f"- {f}" for f in brief.key_facts) or "- (use source material)"
    outline = "\n".join(f"{i+1}. {s}" for i, s in enumerate(brief.outline)) or "(create one)"
    prompt = (
        f"TOPIC: {brief.topic.title}\n"
        f"ANGLE: {brief.angle}\n"
        f"CONTENT TYPE: {brief.content_type}\n"
        f"PRIMARY KEYWORD: {brief.primary_keyword}\n"
        f"SECONDARY: {', '.join(brief.secondary_keywords)}\n\n"
        f"KEY FACTS:\n{facts}\n\n"
        f"DRAFT OUTLINE:\n{outline}\n\n"
        "Refine this into a tight writing plan: final H2 list, the single most "
        "compelling hook for the intro, and one takeaway per section. Keep it short."
    )
    return brain.complete(system, prompt).text


def _write(brain: Brain, persona: WriterPersona, brief: ResearchBrief, plan: str,
           learned: str = "") -> str:
    system = _persona_system(persona, "Writer", learned)
    sources = "\n\n".join(
        f"SOURCE [{s.title or s.url}]:\n{s.text[:1200]}" for s in brief.sources
    ) or "(no external sources — rely on expertise, do not fabricate specifics)"
    prompt = (
        f"TITLE: {brief.topic.title}\n"
        f"PRIMARY KEYWORD (use naturally, ~1% density): {brief.primary_keyword}\n"
        f"SECONDARY KEYWORDS: {', '.join(brief.secondary_keywords)}\n\n"
        f"WRITING PLAN:\n{plan}\n\n"
        f"RESEARCH:\n{sources[:5000]}\n\n"
        "Write the FULL article in Markdown, 1500-2500 words. Start with a strong "
        "1-2 sentence hook (no throat-clearing). Use ## section headers from the "
        "plan. Include a short comparison or checklist where it fits. End with a "
        "clear verdict/next-step, NOT a section literally titled 'Conclusion'. "
        "Do not invent statistics that aren't supported by the research."
    )
    return brain.complete(system, prompt).text


def _edit(brain: Brain, persona: WriterPersona, draft: str) -> str:
    system = _persona_system(persona, "Editor")
    prompt = (
        "Edit this draft for flow, accuracy and punchiness. Cut fluff, tighten "
        "weak sentences, keep the author's voice, keep Markdown structure and "
        "length. Return only the edited article.\n\n"
        f"DRAFT:\n{draft[:12000]}"
    )
    return brain.complete(system, prompt).text


def write_article(brain: Brain, persona: WriterPersona, brief: ResearchBrief,
                  *, do_edit: bool = True, do_humanize: bool = True,
                  learned: str = "") -> str:
    plan = _plan(brain, persona, brief, learned)
    log.info("plan done (%d chars)", len(plan))
    draft = _write(brain, persona, brief, plan, learned)
    log.info("draft done (%d words)", len(draft.split()))
    if do_edit:
        draft = _edit(brain, persona, draft)
        log.info("edit pass done (%d words)", len(draft.split()))
    if do_humanize:
        draft = humanize(draft)
    return draft.strip()
