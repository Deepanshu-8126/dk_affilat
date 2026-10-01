# 🚀 Trend-Driven Multi-Niche Website Earning System

**Har niche = 1 agent.** Each agent runs the same 7-step pipeline
(**Trend → Research → Write → SEO → Image → QC → Publish**) but with a
**different LLM brain, tone and author persona** — so 3 sites read like 3
different human writers.

Built to run **100% free**: GitHub Actions orchestrator, free LLM tiers
(Gemini / Groq / local Qwen3), free trend + SEO sources, WordPress + WOPE
syndication, IndexNow. Your i5 laptop does **0% of the work** — it's all cloud
(except optional local Qwen3/Z-Image).

> ✅ The scaffold runs **out of the box with zero API keys** thanks to
> offline/simulated fallbacks on every external step. Drop keys into `.env` to
> turn each piece "real" incrementally.

---

## 🏗️ Architecture

```
Master Orchestrator (run.py / GitHub Actions cron, random times)
      │  runs 3 agents in parallel, each = 1 post
      ▼
┌──────────────┬──────────────┬───────────────┐
│ Agent 1      │ Agent 2      │ Agent 3       │
│ AI Tools     │ AI Coding    │ AI Automation │
│ Gemini 2.0   │ Groq Llama70 │ Qwen3 (local) │
│ James Carter │ Alex Chen    │ Sarah Mitchell│
└──────┬───────┴──────┬───────┴──────┬────────┘
       │  same 7-step pipeline, different brain
       ▼
1 TREND  → citedy + fn-ignis + deeptrend + trends-checker (+ learned boosts)
2 RESEARCH → Firecrawl scrape + open-seo metrics → brief (angle/outline/facts)
3 WRITE  → Planner→Writer→Editor chain (in persona) + humanizer
4 SEO    → title/meta/slug/schema/density/readability score (claude-seo style)
5 IMAGE  → Z-Image-Turbo → Pollinations → SVG placeholder (featured/og/avatar)
6 QC     → 25-point checklist gate (>= 80 to pass)
6b APPROVE → Telegram HITL (✅/❌/🔄) — or auto in CI
7 PUBLISH → WordPress (canonical) → DEV.to/Medium/Hashnode (rel=canonical) → IndexNow
       ▼
Analytics + Learn (learn.py) → GSC metrics feed back into keyword boosts
```

---

## 📁 Project layout

```
trend-earning-system/
├── run.py                     # master orchestrator (parallel, random jitter)
├── learn.py                   # feedback loop: GSC → keyword boosts
├── telegram_approval.py       # standalone HITL listener
├── config/niches.yaml         # 3 niches × 3 brains × 3 authors
├── core/
│   ├── config.py              # yaml + env loader
│   ├── models.py              # typed pipeline data models
│   ├── llm.py                 # Gemini/Groq/Ollama brain + offline fallback
│   ├── agent.py               # BaseNicheAgent: runs the 7 steps
│   ├── state.py               # run store + de-dup + learning memory
│   └── logging_utils.py
├── pipeline/
│   ├── trend_detect.py        # step 1
│   ├── research.py            # step 2
│   ├── write.py               # step 3 (multi-agent chain)
│   ├── humanize.py            #   AI-speak remover
│   ├── seo_optimize.py        # step 4
│   ├── image_gen.py           # step 5
│   ├── qc.py                  # step 6 (25-point)
│   └── publish.py             # step 7 (WOPE + IndexNow)
├── connectors/                # firecrawl, wordpress, syndicate, indexnow,
│                              #   telegram, image_backends, gsc, http
├── agents/                    # agent_1/2/3 (thin subclasses)
├── tests/test_smoke.py        # full end-to-end offline test
├── requirements.txt           # just PyYAML (stdlib does the rest)
├── .env.example
└── .github/workflows/daily-content.yml
```

---

## ⚡ Quick start (60 seconds, no keys)

```bash
cd trend-earning-system
pip install -r requirements.txt

# run all 3 agents once, simulated publish, no waiting
DRY_RUN=true AUTO_APPROVE=true REQUIRE_APPROVAL=false python run.py --no-jitter

# inspect the generated posts
ls data/runs/            # one folder per run
cat data/runs/*/agent_1_ai_tools.json
```

Run the test suite:

```bash
python tests/test_smoke.py         # or: python -m pytest -q
```

---

## 🔑 Going live (drop keys as you get them)

Copy `.env.example` → `.env` and fill what you have. **Every key is optional** —
missing ones keep that step simulated.

| To enable | Set | Free source |
|---|---|---|
| Real writing (Agent 1) | `GEMINI_API_KEY` | aistudio.google.com/apikey — 1500 req/day |
| Real writing (Agent 2) | `GROQ_API_KEY` | console.groq.com/keys — 30 req/min |
| Real writing (Agent 3) | run Ollama + `ollama pull qwen3:8b` | local, unlimited |
| Source scraping | `FIRECRAWL_API_KEY` | firecrawl.dev free tier |
| Real images | `Z_IMAGE_URL` or `ENABLE_POLLINATIONS=true` | self-host / pollinations.ai |
| Publish (per site) | `WP{1,2,3}_URL/USER/APP_PASSWORD` | WordPress Application Passwords |
| Syndication | `DEVTO_API_KEY`, `HASHNODE_TOKEN` + `..._PUBLICATION_ID` | free accounts |
| Instant indexing | `INDEXNOW_KEY` (host `<key>.txt` at each domain) | free |
| Approvals | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | @BotFather |
| Learning loop | `GSC_CREDENTIALS` (service-account JSON) | Search Console API |

Then flip `DRY_RUN=false` when you're ready to actually publish.

---

## 🤖 GitHub Actions (the $0 orchestrator)

1. Push this repo to a **public** GitHub repo (unlimited Actions minutes).
2. Add every key from `.env` as a **Repository Secret**
   (Settings → Secrets and variables → Actions).
3. The workflow `.github/workflows/daily-content.yml` runs on 3 daily cron
   windows (UTC → ~08:07 / 14:23 / 20:41 IST). It also adds random in-process
   jitter so publish times are never fixed.
4. Trigger manually anytime: **Actions → Daily Content → Run workflow**
   (optionally set `only` to one niche, or `dry_run=true`).

CI defaults to `AUTO_APPROVE=true`. For human approval, set
`REQUIRE_APPROVAL=true`, `AUTO_APPROVE=false`, and run `telegram_approval.py`
(e.g. on your phone-triggered dispatch or a separate always-on runner).

---

## ✍️ How the "3 different writers" effect works

- **3 different LLMs** (Gemini, Groq Llama, Qwen3) → genuinely different phrasing.
- **Per-niche system prompt**: name, title, tone baked into every LLM call
  (`pipeline/write.py::_persona_system`).
- **Humanizer** (`pipeline/humanize.py`) strips ~40 tell-tale AI phrases and
  clichés, then QC scores an `ai_speak_index`.
- **Random publish windows + jitter** so cadence looks organic.
- **Author box + AI-generated avatar** per site for E-E-A-T.

---

## 🧠 Advanced / agentic layer

| Upgrade | Module | What it does |
|---|---|---|
| **Adaptive brain** | `core/adaptive.py` | Conditions each writer's prompt on that site's own performance data (RAG-lite "self-training" — no paid fine-tuning). Winners get amplified, duds de-emphasised. |
| **Agentic strategist** | `core/strategist.py` | Meta-brain that scores every niche (trend heat + learning confidence + momentum) and decides the daily plan: who publishes, priority order, content type, focus theme. |
| **Multi-account rotation** | `core/accounts.py` | Round-robin / least-recent / random rotation across account pools per platform to spread risk and scale reach. Works with 1 account, scales as you add more. |
| **Future-safe GEO/AEO** | `pipeline/geo_aeo.py` | TL;DR key-takeaways + FAQ section + FAQPage JSON-LD + per-domain `llms.txt` so content is quotable by ChatGPT / Perplexity / Google AI Overviews. |
| **Analyze-all dashboard** | `dashboard.py` | Self-contained HTML control center: per-niche stats, SEO/QC sparklines, learned keyword boosts, account health, GEO/AEO coverage, earnings projection. |
| **Market strategy engine** | `pipeline/market_intel.py` | Scores buyer/commercial intent, matches each topic to the highest-paying affiliate platform (Amazon US, Meesho, Impact, ShareASale, PartnerStack, ClickBank, Lemon Squeezy), estimates RPM, picks money content types and injects a conversion-focused directive + trending products into the writer. |
| **Market report** | `market_report.py` | `python market_report.py` → HTML analysis of every niche's money score, best platforms, est. RPM and trending products to feature. |
| **Knowledge engine (self-training)** | `core/knowledge.py`, `knowledge/*.yaml`, `brain_train.py` | 31+ expert rules (how trending works, how earning works, SEO/GEO, per-niche playbooks, 2026→2030 future) retrieved into every brain and reinforced by real results. `python brain_train.py status/show/add/train`. |
| **Auto-niche / industry detection** | `core/industry.py`, `knowledge/industries.yaml`, `discover.py` | Detects a profitable niche in ANY industry (gaming/GTA 6, finance, crypto, health, ...) and generates a runnable niche on the fly. `python discover.py` (rank all), `python discover.py --run gaming` (build + publish). |

> 📖 Full step-by-step onboarding (keys, WordPress, affiliate networks, AdSense,
> Telegram, GitHub deploy, 2026/2027 earning strategy) is in **[SETUP.md](SETUP.md)**.

Run them:

```bash
python run.py --plan-only     # see the strategist's daily plan
python run.py --agentic       # let the strategist pick & order the niches
python dashboard.py           # rebuild data/dashboard.html
```

`strategy.mode: agentic` in `config/niches.yaml` makes `run.py` agentic by default.

## 🔁 The learning loop

`learn.py` reads Search Console performance per site and calls
`state.record_performance()`, which raises `keyword_boosts` for keywords tied to
high-CTR / well-ranked pages. On the next run, `trend_detect.py` adds those
boosts to topic scores → the agent leans into what's working.

---

## 🧩 Mapping to the source repos in the PRD

| PRD repo | Where it lives here |
|---|---|
| citedy-seo-agent, fn-ignis, deeptrend, trends-checker | `pipeline/trend_detect.py` providers |
| Firecrawl, open-seo, All-In-One-Free-SEO-Tool | `connectors/firecrawl.py`, `pipeline/research.py` |
| modamaan/Blog_Automation, raghul-tech multi-agent, vipulawl, mohitjoer | `pipeline/write.py` chain + `core/agent.py` HITL flow |
| claude-seo, pseo-ai-kit | `pipeline/seo_optimize.py` (score, schema, interlinks) |
| Z-Image-Turbo | `connectors/image_backends.py` |
| automated-syndicator (WOPE) + IndexNow | `pipeline/publish.py`, `connectors/syndicate.py`, `connectors/indexnow.py` |

The trend/SEO/syndication connectors are written as thin adapters: swap the
fallback body for the real repo's API/CLI call without touching the pipeline.

---

## 💰 Monetization hooks

Configured per niche in `config/niches.yaml` (`monetization:`): AdSense (after
~50 posts/site), Amazon Associates (reviews), and SaaS affiliate lists
(Jasper, Cursor, Make, etc.). Wire affiliate link injection into
`pipeline/write.py` or a post-processing step.

---

## ⚠️ Before you scale — read this

Auto-publishing AI content at volume touches real policies:

- **AdSense / Search**: Google rewards *helpful, original* content and can
  demote mass-produced pages. The QC gate + humanizer + real research help, but
  quality > quantity. 90 thin posts/month can hurt more than help.
- **Medium / DEV.to ToS**: bulk auto-posting can get accounts flagged. Use
  `rel=canonical`, keep it modest, and treat these as backlinks, not spam.
- **Affiliate disclosure**: FTC/Amazon require visible disclosure — add it to
  the author box / template.
- **Revenue timelines** in the PRD are optimistic; treat them as an upside
  scenario, not a forecast.

This scaffold gives you the machine; sustainable earnings still depend on niche
quality, genuine usefulness, and staying inside each platform's rules.
```
