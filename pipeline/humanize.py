"""
Humanizer — strips common "AI-speak" and mechanical patterns so drafts read like
a real person wrote them. Deterministic regex/heuristic layer applied after the
LLM draft (cheap, offline, always-on).
"""
from __future__ import annotations

import re

# Phrases to remove or soften (case-insensitive)
_BANNED = [
    r"in today'?s fast[- ]paced world[,]?",
    r"in the ever[- ]evolving (world|landscape) of [^.,]+[,.]?",
    r"in the digital age[,]?",
    r"in conclusion[,]?",
    r"it'?s important to note that",
    r"it is worth noting that",
    r"when it comes to",
    r"at the end of the day[,]?",
    r"needless to say[,]?",
    r"in the realm of [^.,]+[,]?",
    r"unlock (the|your) (full )?potential",
    r"take your [^.]+ to the next level",
    r"game[- ]changer",
    r"revolutioni[sz]e",
    r"delve into",
    r"navigate the complexities of",
    r"a testament to",
]

# Word-level de-clichéing
_REPLACE = {
    r"\bleverage\b": "use",
    r"\bleverages\b": "uses",
    r"\bleveraging\b": "using",
    r"\butilize\b": "use",
    r"\butilizes\b": "uses",
    r"\bfacilitate\b": "help",
    r"\bplethora of\b": "lots of",
    r"\bmyriad of\b": "many",
    r"\bfurthermore\b": "also",
    r"\bmoreover\b": "and",
    r"\badditionally\b": "also",
    r"\bcommenced\b": "started",
    r"\bendeavor\b": "try",
    r"\bseamlessly\b": "easily",
    r"\bcutting[- ]edge\b": "modern",
    r"\bstate[- ]of[- ]the[- ]art\b": "modern",
    r"\brobust\b": "solid",
    r"\bdive deep\b": "look closely",
}


def humanize(text: str) -> str:
    out = text
    for pat in _BANNED:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    for pat, repl in _REPLACE.items():
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)

    # Collapse artefacts from removals
    out = re.sub(r"[ \t]{2,}", " ", out)
    out = re.sub(r" +([.,!?;:])", r"\1", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    # Fix leading lowercase after we chopped an intro phrase
    out = re.sub(r"(^|\n)([a-z])",
                 lambda m: m.group(1) + m.group(2).upper(), out)
    return out.strip()


def ai_speak_score(text: str) -> float:
    """0-100 where lower is more human. Used by QC."""
    hits = 0
    for pat in _BANNED:
        hits += len(re.findall(pat, text, flags=re.IGNORECASE))
    for pat in _REPLACE:
        hits += len(re.findall(pat, text, flags=re.IGNORECASE))
    words = max(1, len(text.split()))
    return min(100.0, (hits / words) * 10000)
