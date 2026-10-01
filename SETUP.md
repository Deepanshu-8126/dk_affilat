# 🛠️ SETUP GUIDE — Zero se Earning tak (Hinglish)

Ye guide tujhe **exactly** batati hai kahan click karna hai, kya paste karna hai,
aur kis order mein. Sab **free** se shuru hota hai. Har step ke saamne ⏱️ time
aur 💸 cost likha hai.

> **Rule #1:** Pehle sab kuch `DRY_RUN=true` (simulation) pe test karo. Jab sab
> theek chale, tab `DRY_RUN=false` karke asli publish karo.

---

## 📍 Roadmap (ek nazar mein)

| Phase | Kaam | Time | Cost |
|---|---|---|---|
| 0 | Local test (bina kisi key ke) | 5 min | ₹0 |
| 1 | LLM brain keys (Gemini + Groq) | 15 min | ₹0 |
| 2 | 4 WordPress sites | 1-2 ghante | ₹0 |
| 3 | Affiliate accounts (market strategy) | ~1 din (approval time) | ₹0 |
| 4 | AdSense (50+ posts baad) | 10 min apply | ₹0 |
| 5 | Telegram approval bot | 10 min | ₹0 |
| 6 | GitHub Actions auto-pilot | 20 min | ₹0 |

---

## PHASE 0 — Local test (abhi kar sakta hai) ⏱️5 min

```bash
cd trend-earning-system
pip install -r requirements.txt

# Sab kuch simulation mode mein chalao (koi key ki zarurat nahi)
DRY_RUN=true AUTO_APPROVE=true REQUIRE_APPROVAL=false python run.py --agentic --no-jitter

# Reports dekho
python dashboard.py         # data/dashboard.html
python market_report.py     # data/market_report.html
python demo_live_post.py    # data/live_post_preview.html (sample published post)
```
Agar ye chal gaya → engine perfect hai. Ab isme "petrol" (keys + accounts) daalna hai.

---

## PHASE 1 — LLM Brains (dimag) ⏱️15 min · 💸₹0

Ye teen agents ke "writers" hain. Sab free tier hain.

1. **Gemini** (Agent 1 + strategist): https://aistudio.google.com/apikey → "Create API key" → copy
2. **Groq** (Agent 2 + Agent 4): https://console.groq.com/keys → "Create API Key" → copy
3. **Qwen3 local** (Agent 3, optional): laptop pe Ollama install karo →
   `ollama pull qwen3:8b` → `ollama serve`. (Agar skip kare toh Agent 3 offline
   fallback pe chalega.)

Ab `.env` banao (`.env.example` copy karke):
```bash
cp .env.example .env
```
`.env` mein bhar:
```
GEMINI_API_KEY=AIza...tera_key
GROQ_API_KEY=gsk_...tera_key
OLLAMA_BASE_URL=http://localhost:11434
```

Test:
```bash
DRY_RUN=true AUTO_APPROVE=true python run.py --only agent_1_ai_tools --no-jitter
```
Ab log mein `brain=gemini` real content likhega (offline fallback nahi).

---

## PHASE 2 — 4 WordPress Sites (ghar) ⏱️1-2 ghante · 💸₹0

Har niche ki apni site:
| Site | Niche | Env prefix |
|---|---|---|
| ai-tools-review.com | AI Tools Reviews | WP1 |
| ai-code-tutorial.com | AI Coding | WP2 |
| ai-automate.com | AI Automation | WP3 |
| ai-visual-lab.com | AI Image/Video | WP4 |

**Free tareeka:**
1. Free WordPress host lo (e.g. **WordPress.com free**, ya **InfinityFree**, ya
   apne PC pe LocalWP → baad mein migrate). Domain baad mein khareed sakte ho;
   shuru mein free subdomain chalega.
2. WordPress admin → **Users → Profile → Application Passwords** → naam do
   ("bot") → **Add** → jo password mile use copy karo (space ke saath).
3. `.env` mein bhar (har site ke liye):
```
WP1_URL=https://ai-tools-review.com
WP1_USER=admin
WP1_APP_PASSWORD=xxxx xxxx xxxx xxxx
# WP2_..., WP3_..., WP4_... same tarah
```

Test (abhi bhi DRY_RUN=true rakh — nakli publish):
```bash
DRY_RUN=true python run.py --only agent_1_ai_tools --no-jitter
```

---

## PHASE 3 — 💸 MARKET STRATEGY: Affiliate accounts (asli kamayi yahan se)

Ye system ka **naya Market Strategy Engine** khud decide karta hai har post ke
liye **best platform + best product + kitna commission**. Tere ko sirf un
platforms pe account banana hai jinke links post mein daalne hain.

### 2026/2027 mein kahan paisa hai (priority order):

| Platform | Kis niche ke liye | Commission | Kyun |
|---|---|---|---|
| **ClickBank / Digistore24** | AI courses, digital products, info | **30-75%** | Sabse zyada commission, digital = instant |
| **Impact.com** | SaaS, AI tools, brands | 10-50% | Jasper/Notion type tools, recurring |
| **PartnerStack** | B2B SaaS (recurring) | 20-50% | Har mahine repeat commission |
| **ShareASale / Awin** | Tools, digital | 10-40% | Bada network, easy approval |
| **Amazon Associates (US)** | Gadgets, physical (cameras, mics) | 1-10% | USA traffic = high RPM, trust zyada |
| **Meesho Affiliate** | India audience, physical | 4-12% | India ke liye |
| **Lemon Squeezy / Gumroad** | Indie SaaS, templates | 20-50% | Chhote tools, easy |

**Kaise join karo:**
1. Amazon Associates: https://affiliate-program.amazon.com → sign up → tag milega (`yourtag-20`)
2. Impact / ShareASale / PartnerStack: site pe "Publishers/Affiliates" → apply →
   approve hone pe har brand ka apna link milta hai
3. ClickBank: https://clickbank.com → account → nickname milega

`.env` mein bhar (jo-jo join kiya):
```
AMAZON_ASSOCIATE_TAG=yourtag-20
IMPACT_AFFILIATE_ID=...
CLICKBANK_AFFILIATE_ID=...
SHAREASALE_AFFILIATE_ID=...
# aur SaaS tools ke individual ids (JASPER_AFFILIATE_ID, MAKE_AFFILIATE_ID, ...)
```

> System khud match karega: transactional post ("best X", "X vs Y") → high-commission
> platform + verdict box + comparison table + CTA. Informational post → sirf ads.
> `python market_report.py` chala ke dekho har niche ke liye kaunsa platform best hai.

---

## PHASE 4 — Google AdSense (clicks se paisa) ⏱️10 min apply · 💸₹0

- **Kab apply karo:** har site pe ~30-50 quality posts ho jayein, tab.
- https://adsense.google.com → site add karo → approve hone pe do id milengi:
```
ADSENSE_PUBLISHER_ID=ca-pub-XXXXXXXXXXXXXXXX
ADSENSE_SLOT_IN_ARTICLE=1234567890
```
- System khud in-article ad slots daalta hai (sirf 900+ word posts pe — policy-safe).
- USA/UK/CA traffic pe RPM sabse zyada, isliye content English + US-focused hai.

---

## PHASE 5 — Telegram Approval (tera 5 min/day) ⏱️10 min · 💸₹0

1. Telegram pe **@BotFather** → `/newbot` → naam do → **token** milega
2. Apna chat id: **@userinfobot** ko message karo → id milegi
3. `.env`:
```
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=987654321
REQUIRE_APPROVAL=true
AUTO_APPROVE=false
```
Ab har post se pehle phone pe card aayega: **[✅ Approve] [❌ Reject] [🔄 Rewrite]**.
Bas ek button dabana — yahi tera daily kaam hai.

---

## PHASE 6 — GitHub Actions Auto-Pilot ⏱️20 min · 💸₹0

1. GitHub pe **public repo** banao (public = unlimited free Actions minutes)
2. Code push karo:
```bash
git init && git add . && git commit -m "earning system"
git remote add origin https://github.com/<tu>/<repo>.git
git push -u origin main
```
3. GitHub → **Settings → Secrets and variables → Actions** → har `.env` wali key
   ko **New repository secret** ke roop mein daal do (GEMINI_API_KEY, WP1_URL, ...)
4. **Settings → Pages** → Source: "GitHub Actions" (dashboard auto-deploy ke liye)
5. **Actions** tab → "Daily Content" → "Run workflow" → test karo

Ab roz 3 cron times pe apne aap chalega. Dashboard bhi auto-deploy hoga (public URL).

---

## PHASE 7 — GO LIVE 🚀

Jab sab test ho jaye:
```
# .env mein:
DRY_RUN=false
```
Bas. Ab asli posts jaayenge, IndexNow ping hoga, affiliate + ads live honge.

---

## 🧠 Niche / Product strategy (kaise sochna hai)

Ye system already ye karta hai, par samajh le:

1. **USA-based, English content** → highest RPM (US > UK > CA > baaki).
2. **Buyer-intent topics** ("best", "vs", "review", "price") → transactional →
   affiliate + high ad RPM. System inhe auto-detect karke money-format mein likhta hai.
3. **Digital products (courses/SaaS)** → highest commission (ClickBank 30-75%,
   PartnerStack recurring). Physical (Amazon) → trust zyada par commission kam.
4. **Trending products feature karo** → system `product_trends` se current picks
   laata hai (ChatGPT, Veo 3, Cursor, etc.) aur article mein weave karta hai.
5. **Quality > quantity** → 90 ghatiya posts se Google demote karega. QC gate
   (27-point, 80+) + humanizer + real research isi liye hai.

Rozana: `python market_report.py` khol ke dekho kaunsi niche ka **money score**
sabse zyada hai — usi pe zyada dhyan do.

---

## ⚡ Commands Cheat Sheet

```bash
python run.py --plan-only            # aaj ka agentic plan dekho
python run.py --agentic              # strategist decide karke chalaye
python run.py --only agent_4_ai_visual   # ek niche
python learn.py                      # GSC data se seekho (feedback loop)
python dashboard.py --serve --port 8080  # live dashboard
python market_report.py              # money/affiliate analysis
python demo_live_post.py             # sample published post
python tests/test_smoke.py           # sab kuch test karo
```

---

## ✅ Setup checklist

- [ ] Phase 0: local dry-run chala
- [ ] Phase 1: GEMINI + GROQ keys .env mein
- [ ] Phase 2: 4 WordPress sites + app passwords
- [ ] Phase 3: kam se kam 2 affiliate accounts (Amazon + ek digital network)
- [ ] Phase 4: AdSense apply (50 posts baad)
- [ ] Phase 5: Telegram bot on
- [ ] Phase 6: GitHub secrets + Actions test
- [ ] Phase 7: DRY_RUN=false → LIVE

Setup ho gaya? Roz sirf Telegram pe approve dabana. Baaki system khud sambhalta hai. 🚀
