#!/usr/bin/env python3
"""
LIVE-STYLE FULL POST DEMO.

Runs a genuine ~1600-word article through the REAL pipeline transforms:
  monetize -> SEO -> GEO/AEO (FAQ + takeaways + schema) -> QC -> HTML render.

The prose is authored here (no live API key in this environment); with a real
GEMINI_API_KEY / GROQ_API_KEY the identical steps run on model output. Produces
data/live_post_preview.html styled like a published blog post.
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("DRY_RUN", "true")

from core.config import DATA_DIR, load_config           # noqa: E402
from core.llm import LLMResult                          # noqa: E402
from core.models import Article, SeoReport, TrendTopic, ResearchBrief, SourceDoc  # noqa: E402
from pipeline import geo_aeo, monetize, publish, qc, seo_optimize  # noqa: E402


class ScriptedBrain:
    """Stands in for a real LLM: returns tailored output per pipeline role."""

    @staticmethod
    def _r(text: str) -> LLMResult:
        return LLMResult(text=text, provider="scripted", model="demo")

    def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> LLMResult:
        s, p = system.lower(), prompt.lower()
        if json_mode and "takeaway" in p:
            import json
            return self._r(json.dumps([
                "Jasper leads on polished long-form; Copy.ai wins on speed and a generous free tier.",
                "Writesonic is the best value for SEO teams shipping high volume.",
                "Notion AI is worth it only if your team already lives in Notion.",
                "Start on free tiers, measure words-kept-per-hour, then pay for the one you actually use.",
            ]))
        if json_mode and ("faq" in p or "question" in s):
            import json
            return self._r(json.dumps([
                {"question": "What is the best AI writing tool in 2026?",
                 "answer": "For long-form, Jasper is the most polished; Copy.ai is faster for short marketing copy. The 'best' depends on whether you optimise for quality or speed."},
                {"question": "Are AI writing tools worth paying for?",
                 "answer": "Yes if you write daily — the time saved usually covers the ~$40/month cost within a week. Casual users should stay on free tiers."},
                {"question": "Do AI writing tools hurt SEO?",
                 "answer": "Not if you edit and add first-hand experience. Google rewards helpful, original content regardless of how the first draft was produced."},
                {"question": "Which AI writing tool has the best free plan?",
                 "answer": "Copy.ai has the most generous ongoing free tier; Writesonic offers a solid monthly word allowance for testing."},
            ]))
        if "meta description" in s:
            return self._r("Compared Jasper, Copy.ai, Writesonic and Notion AI head-to-head for 2026 — real tests on quality, speed, pricing and SEO to find the best AI writing tool for you.")
        return self._r("")


ARTICLE_MD = """\
Picking an AI writing assistant in 2026 is less about "which one is smartest" and more about which one fits how you actually work. I spent two weeks running the same twelve briefs through the four tools most people ask me about — Jasper, Copy.ai, Writesonic and Notion AI — and scored each on draft quality, speed, editing effort and price. Here's what held up.

## How I tested them

Every tool got the identical inputs: four long-form blog briefs, four batches of short marketing copy, and four "rewrite this clunky paragraph" tasks. I measured three things that matter in real work — how usable the first draft was, how many minutes of editing it needed, and how often I hit a paywall or rate limit. No cherry-picked prompts, no vendor demos.

## Jasper: the polished long-form pick

Jasper produced the cleanest long-form drafts of the group. On a 1,500-word "how to migrate to a headless CMS" brief, it kept a consistent voice across sections and rarely contradicted itself — the failure mode that usually eats your editing time. Its brand-voice feature genuinely works once you feed it three or four samples.

The catch is price. Jasper is the most expensive option here, and the value only makes sense if long-form is your bread and butter. For a content team shipping pillar pages weekly, it pays for itself in edit-time saved. For occasional blog posts, it's overkill.

## Copy.ai: fastest for short marketing copy

Copy.ai flips the tradeoff. Its long-form drafts needed more cleanup, but for short copy — ad variations, product descriptions, cold email openers — it was the quickest to a usable result and had the most generous ongoing free tier. If your day is "give me twenty subject lines, now," this is the one you'll keep open.

Where it struggles is depth. Ask for a technical explainer and you'll get confident but shallow output that needs a subject-matter pass. That's fine if you're the expert doing the editing; risky if you're not.

## Writesonic: best value for SEO volume

Writesonic sits in the middle on quality but wins on value for teams publishing at volume. Its article workflow — outline, draft, then a built-in optimisation pass — mapped closely to how SEO writers actually work, and the monthly word allowance stretched further than I expected. If you're shipping dozens of posts a month on a budget, it's the pragmatic choice.

## Notion AI: only if you already live in Notion

Notion AI is the odd one out. As a standalone writer it's merely fine, but that misses the point — its value is being one keystroke away inside docs you're already writing. For summarising meeting notes, expanding bullet points into prose, and cleaning up drafts in place, it removes the copy-paste tax entirely. If your team already runs on Notion, it's a no-brainer add-on. If not, it isn't a reason to switch.

## Side-by-side: what actually differs

- **Draft quality (long-form):** Jasper > Writesonic > Copy.ai > Notion AI
- **Speed (short copy):** Copy.ai > Writesonic > Jasper > Notion AI
- **Value per dollar at volume:** Writesonic > Copy.ai > Notion AI > Jasper
- **Free tier for testing:** Copy.ai > Writesonic > Notion AI > Jasper
- **Fits existing workflow:** Notion AI (if you use Notion) > the rest

## Pricing, honestly

All four cluster in the $30–60/month range for the plans most people actually need, with annual billing knocking off roughly 20%. The free tiers are real but capped: enough to judge quality, not enough to run a content operation. My advice is to spend a week on free plans, track how many words you keep versus throw away, and only then pull out a card.

## The verdict

There's no single winner, and anyone who tells you otherwise is selling something. If you write long-form for a living, Jasper earns its premium. If you live in short marketing copy, Copy.ai is the fastest path. Publishing at volume on a budget? Writesonic. Already all-in on Notion? Add Notion AI and stop shopping.

Whatever you pick, the tool is a first-draft engine, not a replacement for your judgement. The people getting real leverage from these aren't publishing raw output — they're using it to skip the blank page, then adding the experience and specifics that make writing worth reading.

## Who each tool is really for

After two weeks I stopped thinking about the best AI writing tools as competitors and started thinking of them as different jobs. Jasper is for the content lead who answers to a traffic number. Copy.ai is for the marketer who ships ten small things a day. Writesonic is for the SEO operator scaling output without scaling headcount. Notion AI is for the team that already treats Notion as its second brain and just wants writing help where the work already lives.

That framing matters because most buyer's remorse I hear about comes from picking a tool built for a different job. A solo blogger who buys the top Jasper tier rarely uses half of it. A ten-person content team on Copy.ai's cheapest plan constantly hits limits. Match the tool to the volume and the format you produce most, not to the flashiest demo.

## What surprised me during testing

Two things stood out. First, the gap between tools on raw quality is narrower than it was a year ago — the real differences now are workflow, speed and price, not "which model is smarter." Second, the editing time is where the money actually is. A tool that gives you a slightly worse draft you can fix in five minutes beats a "better" draft that needs a full rewrite because it invented a statistic.

I also noticed that every tool did better when I gave it real inputs — a rough outline, three example paragraphs in my voice, and the specific audience. Feeding thin prompts and blaming the tool for generic output is the single most common mistake I see. Garbage in, generic out.

## Common mistakes to avoid

- **Publishing raw drafts.** Search engines and readers both punish it. Always add first-hand experience and specifics.
- **Buying the biggest plan first.** Start small, measure, then upgrade the one tool you reach for daily.
- **Ignoring fact-checking.** These tools state wrong things confidently. Verify names, numbers and dates.
- **Skipping brand voice setup.** Ten minutes of samples turns generic output into something that sounds like you.
- **Chasing word count.** Longer isn't better; useful is better. Cut ruthlessly after the draft.

## My actual workflow with these tools

Here's the loop that saves me the most time. I write the outline and the hook myself — that's where judgement lives. I hand the tool the outline plus a few voice samples and let it draft the middle sections. Then I do a hard editing pass: cut clichés, add real examples, verify every claim, and rewrite the intro and conclusion by hand. The tool does maybe 60% of the typing and none of the thinking.

That split is why I'm comfortable recommending any of the best AI writing tools here to the right person. They compress the boring part — turning a blank page into a rough middle — so you can spend your energy on the parts that actually differentiate your writing.

## Bottom line

Don't overthink the choice. Spend a week on free tiers, track words-kept-per-hour, and commit to the one tool that fits your dominant format. Long-form: Jasper. Fast short copy: Copy.ai. Volume on a budget: Writesonic. Notion-native team: Notion AI. Then stop tool-shopping and go write something worth reading.
"""


def main() -> Path:
    app = load_config()
    niche = app.niche("agent_1_ai_tools")
    mon = app.defaults["monetization"]
    brain = ScriptedBrain()

    topic = TrendTopic(title="Best AI Writing Tools in 2026", source="demo",
                       keywords=["best AI writing tools", "AI writing software"])
    brief = ResearchBrief(topic=topic, angle="hands-on comparison",
                          primary_keyword="best AI writing tools",
                          secondary_keywords=["AI writing software", "Jasper vs Copy.ai",
                                              "AI content tools", "AI copywriting"],
                          content_type="comparison",
                          sources=[SourceDoc(url="https://example.com/test", title="Test notes", text="x"*400, word_count=80)])

    art = Article(niche_id=niche.id, run_id="demo",
                  title="Best AI Writing Tools in 2026: Jasper vs Copy.ai vs Writesonic vs Notion AI",
                  body_markdown=ARTICLE_MD, brief=brief,
                  author_name=niche.author["name"], author_bio=niche.author["bio"])
    art.tags = brief.secondary_keywords[:5]
    art.meta["domain"] = niche.domain

    # --- REAL pipeline transforms ---
    art.body_markdown, mon_res = monetize.apply_content_monetization(
        art.body_markdown, saas_slugs=niche.monetization["saas_affiliate"],
        amazon_enabled=niche.monetization["amazon_associates"], mon=mon)
    art.meta["monetization"] = {"links_added": mon_res.links_added,
                                "tools_linked": mon_res.tools_linked,
                                "disclosure_added": mon_res.disclosure_added}
    art.excerpt = " ".join(art.body_markdown.split()[:40])
    art.seo = seo_optimize.optimize(brain, art)
    art.meta["geo_aeo"] = geo_aeo.apply(brain, art)
    art.qc = qc.run_qc(art, min_score=80)

    # Force real AdSense placeholders so the preview shows ad slots visually
    os.environ["ADSENSE_PUBLISHER_ID"] = "ca-pub-DEMO"
    os.environ["ADSENSE_SLOT_IN_ARTICLE"] = "0000000000"
    html_body = publish._md_to_html(art.body_markdown)
    ad_units = monetize.adsense_html(art.word_count, mon)
    html_body, _ = monetize.inject_ads_into_html(html_body, ad_units)

    import json as _json
    schema = _json.dumps(art.seo.schema_jsonld)
    out = DATA_DIR / "live_post_preview.html"
    out.write_text(_PAGE.format(
        title=art.title, meta=art.seo.meta_description, author=art.author_name,
        author_title=niche.author["title"], bio=art.author_bio, body=html_body,
        seo=art.seo.score, qc=art.qc.score, words=art.word_count,
        links=mon_res.links_added, kw=art.seo.focus_keyword,
        density=art.seo.keyword_density, read=art.seo.readability,
        faqs=art.meta["geo_aeo"]["faqs"], schema=schema), encoding="utf-8")
    print(f"SEO={art.seo.score} QC={art.qc.score} words={art.word_count} "
          f"affiliate_links={mon_res.links_added} faqs={art.meta['geo_aeo']['faqs']}")
    print(f"preview -> {out}")
    return out


_PAGE = """<!doctype html><html><head><meta charset="utf-8">
<meta name="description" content="{meta}">
<title>{title}</title>
<script type="application/ld+json">{schema}</script>
<style>
 body{{font-family:Georgia,'Times New Roman',serif;color:#1a1a1a;line-height:1.7;margin:0;background:#fafafa}}
 .top{{background:#111827;color:#fff;padding:10px 0;font-family:system-ui;font-size:13px}}
 .top .wrap{{max-width:760px;margin:0 auto;padding:0 20px;display:flex;justify-content:space-between}}
 .top b{{color:#a5b4fc}}
 article{{max-width:760px;margin:0 auto;padding:32px 20px 60px;background:#fff}}
 h1{{font-size:34px;line-height:1.2;margin:6px 0 14px}}
 h2{{font-size:24px;margin:34px 0 10px;font-family:system-ui}}
 .byline{{font-family:system-ui;color:#666;font-size:14px;border-bottom:1px solid #eee;padding-bottom:16px;margin-bottom:24px}}
 .badges{{font-family:system-ui;font-size:12px;color:#444;margin:4px 0 0}}
 .badges span{{display:inline-block;background:#eef2ff;color:#4338ca;padding:3px 9px;border-radius:20px;margin-right:6px}}
 blockquote{{background:#fff8e1;border-left:4px solid #f0b400;padding:10px 16px;color:#6a5400;font-family:system-ui;font-size:14px;margin:18px 0;border-radius:4px}}
 a{{color:#1d4ed8;text-decoration:underline}}
 ul{{padding-left:22px}}
 .adsbygoogle{{display:block;background:#eef3ff;border:1px dashed #90a4d4;padding:18px;text-align:center;color:#5566aa;font-family:system-ui;font-size:13px;margin:22px 0;border-radius:6px}}
 .adsbygoogle::before{{content:"▮ AdSense in-article unit"}}
 .author{{margin-top:36px;padding:18px;background:#f6f7f9;border-radius:10px;font-family:system-ui;font-size:14px;display:flex;gap:14px;align-items:flex-start}}
 .avatar{{width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,#6366f1,#a855f7);flex:none}}
</style></head><body>
<div class="top"><div class="wrap"><span>ai-tools-review.com</span>
<span>REAL pipeline output — SEO <b>{seo}</b> · QC <b>{qc}</b> · {words} words · {links} affiliate links · {faqs} FAQ</span></div></div>
<article>
 <h1>{title}</h1>
 <div class="byline">By <strong>{author}</strong>, {author_title} · 8 min read
 <div class="badges"><span>focus: {kw}</span><span>density {density}%</span><span>readability {read}</span></div></div>
 {body}
 <div class="author"><div class="avatar"></div><div><strong>{author}</strong> — {author_title}<br>{bio}</div></div>
</article></body></html>"""


if __name__ == "__main__":
    main()
