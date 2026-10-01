"""
STEP 4b — GEO / AEO (future-safe optimisation for AI answer engines).

Classic SEO ranks pages; GEO/AEO makes content the *quoted source* inside
ChatGPT, Perplexity, Gemini and Google AI Overviews. This step adds the
structures those systems reward:

  * a "Key takeaways" TL;DR block at the top (extractable, citable)
  * a FAQ section + FAQPage JSON-LD (rich results + AI Q&A grounding)
  * an llms.txt entry per site (the emerging standard for AI crawlers)

All generated via the niche brain, with deterministic fallbacks.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from core.config import DATA_DIR
from core.llm import Brain
from core.logging_utils import get_logger
from core.models import Article

log = get_logger("geo_aeo")

LLMS_DIR = DATA_DIR / "llms"


def _parse_json(text: str) -> dict | list | None:
    text = text.strip().strip("`")
    for lo, hi in (("{", "}"), ("[", "]")):
        s, e = text.find(lo), text.rfind(hi)
        if s != -1 and e != -1:
            try:
                return json.loads(text[s:e + 1])
            except json.JSONDecodeError:
                continue
    return None


def key_takeaways(brain: Brain, article: Article, n: int = 4) -> list[str]:
    system = ("Extract crisp, standalone key takeaways an AI could quote. "
              "Return a JSON array of short strings. No markdown.")
    prompt = (f"TITLE: {article.title}\n\nARTICLE:\n{article.body_markdown[:5000]}\n\n"
              f"Give {n} key takeaways as a JSON array.")
    data = _parse_json(brain.complete(system, prompt, json_mode=True).text)
    if isinstance(data, list) and data:
        return [str(x).strip() for x in data[:n]]
    # fallback: first sentence of first few sections
    sents = re.split(r"(?<=[.!?])\s+", re.sub(r"[#*>-]", "", article.body_markdown))
    return [s.strip() for s in sents if len(s.split()) > 6][:n]


def faq(brain: Brain, article: Article, n: int = 4) -> list[dict]:
    system = ("Write a helpful FAQ that answers real questions people ask about "
              "this topic. Return JSON array of {question, answer}. Answers 1-2 "
              "sentences, specific, no fluff.")
    prompt = (f"TOPIC: {article.title}\nKEYWORD: {article.seo.focus_keyword}\n\n"
              f"CONTEXT:\n{article.body_markdown[:4000]}\n\nGive {n} FAQ items as JSON.")
    data = _parse_json(brain.complete(system, prompt, json_mode=True).text)
    out = []
    if isinstance(data, list):
        for item in data[:n]:
            if isinstance(item, dict) and item.get("question") and item.get("answer"):
                out.append({"question": str(item["question"]).strip(),
                            "answer": str(item["answer"]).strip()})
    if not out:
        kw = article.seo.focus_keyword or article.title
        out = [
            {"question": f"What is {kw}?",
             "answer": f"{kw} is covered in detail in this guide, including how it works and when to use it."},
            {"question": f"Is {kw} worth it?",
             "answer": "For most users the free tier is enough to evaluate it before committing."},
        ]
    return out


def apply(brain: Brain, article: Article) -> dict:
    """Mutates article.body_markdown + article.seo.schema_jsonld; returns stats."""
    takeaways = key_takeaways(brain, article)
    faqs = faq(brain, article)

    # 1) TL;DR block at the very top (after title-less body start)
    tl = "**Key takeaways**\n\n" + "\n".join(f"- {t}" for t in takeaways)
    article.body_markdown = f"{tl}\n\n{article.body_markdown}"

    # 2) FAQ section at the end
    faq_md = "\n\n## Frequently asked questions\n\n" + "\n\n".join(
        f"**{q['question']}**\n\n{q['answer']}" for q in faqs)
    article.body_markdown += faq_md

    # 3) FAQPage schema -> attach as an additional graph node
    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q["question"],
             "acceptedAnswer": {"@type": "Answer", "text": q["answer"]}}
            for q in faqs
        ],
    }
    base = article.seo.schema_jsonld or {}
    article.seo.schema_jsonld = {"@context": "https://schema.org",
                                 "@graph": [base, faq_schema]} if base else faq_schema

    # 4) llms.txt entry (append per-domain)
    _append_llms_txt(article, takeaways)

    log.info("GEO/AEO: %d takeaways, %d FAQ, FAQPage schema attached",
             len(takeaways), len(faqs))
    return {"takeaways": len(takeaways), "faqs": len(faqs)}


def _append_llms_txt(article: Article, takeaways: list[str]) -> None:
    LLMS_DIR.mkdir(parents=True, exist_ok=True)
    domain = article.meta.get("domain", "site")
    path = LLMS_DIR / f"{domain}.llms.txt"
    header = f"# {domain}\n\n> AI-readable index of high-signal content.\n\n"
    entry = (f"## {article.title}\n"
             f"- URL: https://{domain}/{article.slug}/\n"
             f"- Summary: {takeaways[0] if takeaways else article.excerpt[:160]}\n\n")
    if not path.exists():
        path.write_text(header + entry, encoding="utf-8")
    else:
        path.write_text(path.read_text(encoding="utf-8") + entry, encoding="utf-8")
