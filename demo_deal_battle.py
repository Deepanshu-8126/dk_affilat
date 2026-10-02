#!/usr/bin/env python3
"""
Affiliate Product Comparison & Deal Battle Demo.
Generates an in-depth, high-converting product review & comparison post with:
- Photoshop-grade 2-column 'Product A vs Product B' VS Battle Banner
- Interactive comparison specs matrix
- Pros, Cons, and Key Highlights
- High-CTR Affiliate CTA Buttons
- Schema.org Product & Review JSON-LD structured data for Google Search rich snippets
"""
from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("DRY_RUN", "true")

from connectors.photoshop_deal_banner import PhotoshopDealBannerEngine
from core.config import DATA_DIR, load_config
from core.models import Article, SeoReport, ImageAsset, TrendTopic, ResearchBrief
from pipeline import geo_aeo, monetize, publish, qc, seo_optimize

SAMPLE_VS_ARTICLE = """\
If you are a developer writing code in 2026, you've likely faced the burning dilemma: should you stick with the familiar **GitHub Copilot**, or make the leap to the AI-native powerhouse **Cursor AI**?

Over the past 30 days, our engineering team ran extensive benchmark tests across five real-world full-stack repositories. We measured raw speed, contextual codebase indexing, refactoring accuracy, multi-file edits, and daily developer productivity. Here is our completely unbiased, head-to-head breakdown.

---

## ⚡ The Quick Verdict: Which One Should You Buy?

If you want an AI that understands your **entire multi-repo codebase**, can edit 10 files simultaneously with one prompt, and feels like a senior pair-programmer inside VS Code — **Cursor AI is the undisputed champion**. 

However, if your company strictly enforces standard VS Code / JetBrains environments with enterprise SAML SSO and you only need basic inline autocompletion, **GitHub Copilot** remains the safe standard.

---

## 📊 Quick Comparison Matrix: Cursor AI vs GitHub Copilot

| Feature Benchmark | Cursor AI (Winner) 🏆 | GitHub Copilot |
| :--- | :--- | :--- |
| **Primary AI Engine** | Claude 3.5 Sonnet / GPT-4o / Custom | GPT-4o / Claude 3.5 |
| **Codebase Indexing** | Full Semantic Vector Indexing (`@codebase`) | Limited Local Context |
| **Multi-File Editing** | Native Composer (Multi-file diff apply) | Single file chat |
| **Speed & Latency** | Instant (~180ms tab completion) | Fast (~250ms) |
| **Terminal Integration** | Native Terminal Command Gen (`Cmd+K`) | Chat terminal commands |
| **Free Tier** | 14-Day Pro Trial + 50 Fast Requests/mo | Free for Students/OSS |
| **Starting Price** | $20/month | $10/month (Individual) / $19 (Biz) |
| **Our Rating** | ⭐⭐⭐⭐⭐ **4.9 / 5.0** | ⭐⭐⭐⭐ **4.6 / 5.0** |

---

## 🏆 Deep Dive 1: Cursor AI (The Developer's Superpower)

Cursor is a dedicated fork of VS Code engineered from the ground up for LLM-assisted programming.

### 🌟 Key Highlights & Superpowers:
- **`Composer` Multi-File Editing:** You can literally tell Cursor *"Refactor our authentication middleware to use JWT and update all 8 route handlers"* — and it will open all 8 files, show clean green/red diffs, and apply them with one click.
- **Deep Codebase Awareness:** By typing `@codebase` or `@docs`, Cursor embeds your whole project in real-time. It knows your utility functions, database schemas, and typing patterns.

### ❌ Cursor Drawbacks:
- Requires using the Cursor IDE (fork of VS Code) rather than vanilla VS Code extension.

---

## 🥊 Deep Dive 2: GitHub Copilot (The Established Standard)

GitHub Copilot was the pioneer of AI pair-programming and remains backed by Microsoft and OpenAI.

### 🌟 Key Highlights:
- Seamlessly installs as an extension inside VS Code, Visual Studio, JetBrains (IntelliJ, PyCharm), and Neovim.
- Enterprise-grade compliance, IP indemnification, and GitHub repository integration.

### ❌ Copilot Drawbacks:
- Struggles with complex multi-file architectural refactoring.
- Inline suggestions can sometimes feel repetitive or outdated on newer frameworks.

---

## 💰 Pricing & Exclusive Discount Deals

- **Cursor AI Deal:** Start with the Free Tier or unlock the **Pro Plan at $20/mo** with unlimited completions and 500 fast Claude 3.5 requests.
- **GitHub Copilot Deal:** $10/month for individuals, or **Free for verified students and open-source maintainers**.

---

## 🎯 Final Recommendation

For solo developers, startup teams, and fast-moving engineers, **Cursor AI delivers a massive 3x to 5x productivity boost** that easily pays for its $20 monthly price tag on day one.
"""


def run_deal_battle_demo():
    print("🚀 [DealBattleDemo] Generating High-Converting Product Comparison Article...")

    # 1. Generate Photoshop Battle Banner
    banner_engine = PhotoshopDealBannerEngine()
    banner_path = banner_engine.generate_vs_battle_banner(
        product_a="Cursor AI",
        product_b="GitHub Copilot",
        category="AI CODING ASSISTANTS",
        rating_a="4.9",
        rating_b="4.6",
        winner="A",
        out_filename="VS_BATTLE_cursor_vs_copilot.png"
    )
    print(f"🎨 [PhotoshopEngine] Generated 1200x630 Battle Card: {banner_path}")

    # 2. Build Article Object
    article = Article(
        niche_id="ai_coding",
        run_id="deal_battle_01",
        title="Cursor AI vs GitHub Copilot: The Ultimate 2026 Developer Showdown",
        body_markdown=SAMPLE_VS_ARTICLE,
        author_name="Alex Chen",
        author_bio="Senior Full-Stack Architect & AI Tooling Specialist",
        images=[
            ImageAsset(
                path=str(banner_path),
                kind="featured",
                width=1200,
                height=630,
                alt="Cursor AI vs GitHub Copilot Comparison Battle Card",
                prompt="Cursor vs Copilot",
                generated=True,
            )
        ]
    )

    app = load_config()
    niche = app.niche("agent_2_ai_coding")
    mon = app.defaults["monetization"]

    # 3. Monetization Injection (Affiliate Links + FTC Disclosures + CTA Buttons)
    from demo_live_post import ScriptedBrain
    brain = ScriptedBrain()

    topic = TrendTopic(title="Cursor AI vs GitHub Copilot 2026", source="deal_radar",
                       keywords=["Cursor AI", "GitHub Copilot", "AI coding"])
    brief = ResearchBrief(topic=topic, angle="hands-on benchmark comparison",
                          primary_keyword="Cursor AI vs GitHub Copilot",
                          secondary_keywords=["Cursor AI review", "Copilot vs Cursor", "AI code editor"],
                          content_type="comparison")
    article.brief = brief
    article.tags = brief.secondary_keywords

    article.body_markdown, mon_res = monetize.apply_content_monetization(
        article.body_markdown,
        saas_slugs=niche.monetization.get("saas_affiliate", []),
        amazon_enabled=niche.monetization.get("amazon_associates", True),
        mon=mon
    )
    article.meta["monetization"] = {
        "links_added": mon_res.links_added,
        "tools_linked": mon_res.tools_linked,
        "disclosure_added": mon_res.disclosure_added
    }
    print(f"💰 [Monetize] Injected {mon_res.links_added} affiliate links | Disclosure: {mon_res.disclosure_added}")

    # 4. SEO & Schema Optimization
    article.seo = seo_optimize.optimize(brain, article)
    print(f"📈 [SEO] Focus Keyword Score: {article.seo.score:.1f}/100 | Density: {article.seo.keyword_density:.2f}%")

    # 5. GEO/AEO & Rich Schema (Key Takeaways + Product FAQ)
    article.meta["geo_aeo"] = geo_aeo.apply(brain, article)
    print(f"🤖 [AEO] Attached {article.meta['geo_aeo'].get('faqs', 0)} FAQ Schema entries & {article.meta['geo_aeo'].get('takeaways', 0)} Key Takeaways")

    # 6. QC Gate
    article.qc = qc.run_qc(article, min_score=80)
    print(f"✅ [QC Gate] Score: {article.qc.score:.1f}% -> {'PASSED' if article.qc.passed else 'FAILED'}")

    # 7. Render Production HTML with Photoshop Banner
    html_body = publish._md_to_html(article.body_markdown)
    ad_units = monetize.adsense_html(article.word_count, mon)
    html_body, _ = monetize.inject_ads_into_html(html_body, ad_units)

    import json as _json
    schema = _json.dumps(article.seo.schema_jsonld)
    banner_rel_path = f"assets/deal_banners/{banner_path.name}"

    final_html = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="description" content="{article.seo.meta_description}">
<title>{article.title}</title>
<script type="application/ld+json">{schema}</script>
<style>
 body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #1e293b; line-height: 1.8; margin: 0; background: #0f172a; }}
 .top-bar {{ background: #020617; border-bottom: 1px solid #1e293b; padding: 12px 20px; color: #94a3b8; font-size: 13px; }}
 .top-bar .wrap {{ max-width: 860px; margin: 0 auto; display: flex; justify-content: space-between; }}
 .top-bar b {{ color: #38bdf8; }}
 article {{ max-width: 860px; margin: 24px auto 60px; padding: 40px; background: #ffffff; border-radius: 16px; box-shadow: 0 20px 40px rgba(0,0,0,0.5); }}
 h1 {{ font-size: 34px; line-height: 1.25; color: #0f172a; margin: 10px 0 16px; font-weight: 800; }}
 h2 {{ font-size: 24px; color: #0f172a; margin: 36px 0 12px; border-left: 4px solid #2563eb; padding-left: 12px; }}
 h3 {{ font-size: 18px; color: #334155; margin: 20px 0 8px; }}
 .byline {{ color: #64748b; font-size: 14px; border-bottom: 1px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
 .badge {{ display: inline-block; background: #e0f2fe; color: #0284c7; padding: 4px 12px; border-radius: 999px; font-weight: 600; font-size: 12px; margin-right: 8px; }}
 .hero-banner {{ width: 100%; border-radius: 14px; margin: 16px 0 28px; box-shadow: 0 10px 25px rgba(0,0,0,0.25); display: block; }}
 table {{ width: 100%; border-collapse: collapse; margin: 24px 0; font-size: 15px; }}
 th, td {{ padding: 12px 16px; border: 1px solid #cbd5e1; text-align: left; }}
 th {{ background: #f1f5f9; color: #0f172a; font-weight: 700; }}
 tr:nth-child(even) {{ background: #f8fafc; }}
 blockquote {{ background: #fffbeb; border-left: 4px solid #f59e0b; padding: 12px 18px; color: #92400e; font-size: 14px; margin: 20px 0; border-radius: 6px; }}
 a {{ color: #2563eb; text-decoration: none; font-weight: 600; }}
 a:hover {{ text-decoration: underline; }}
 .author-card {{ margin-top: 40px; padding: 20px; background: #f8fafc; border-radius: 12px; display: flex; gap: 16px; align-items: center; border: 1px solid #e2e8f0; }}
 .avatar {{ width: 56px; height: 56px; border-radius: 50%; background: linear-gradient(135deg, #2563eb, #7c3aed); flex-shrink: 0; }}
</style>
</head>
<body>
<div class="top-bar">
 <div class="wrap">
   <span>⚡ <b>AI CODING HUB</b> • LIVE AFFILIATE SYSTEM</span>
   <span>SEO: <b>{article.seo.score}</b> | QC: <b>{article.qc.score}%</b> | {article.word_count} Words</span>
 </div>
</div>
<article>
 <div class="badge">🔥 2026 BENCHMARK REVIEW</div>
 <h1>{article.title}</h1>
 <div class="byline">By <strong>{article.author_name}</strong> · 7 min read · Verified Engineering Review</div>
 <img src="{banner_path.as_uri()}" class="hero-banner" alt="Cursor vs Copilot Battle Banner" />
 {html_body}
 <div class="author-card">
   <div class="avatar"></div>
   <div>
     <strong>{article.author_name}</strong><br>
     <span style="font-size: 13px; color: #64748b;">{article.author_bio}</span>
   </div>
 </div>
</article>
</body>
</html>"""

    out_preview = DATA_DIR / "deal_battle_preview.html"
    out_preview.write_text(final_html, encoding="utf-8")
    print(f"\n🎉 [Complete] Deal Battle Article Generated -> {out_preview}")


if __name__ == "__main__":
    run_deal_battle_demo()
