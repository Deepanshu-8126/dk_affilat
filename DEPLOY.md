# 🚀 DEPLOY GUIDE — Arena se VS Code se GitHub se LIVE (Hinglish)

> Ye guide batati hai: is workspace ko apne PC par le jaana → VS Code mein
> kholna → locally test → GitHub par push → GitHub Actions se **auto-pilot**
> chalu karna. **Server ki zaroorat nahi.** Sab kuch **₹0** (free tier) par.

---

## 🧠 Pehle samajh le: "Deploy" ka matlab yahan kya hai?

Is system ko koi 24/7 server nahi chahiye. Ye **GitHub Actions** (free) par
cron schedule pe khud chalta hai — din mein 3 baar uthta hai, content banata
hai, publish karta hai, so jaata hai. Matlab:

```
Tera kaam = code GitHub par push karna + secrets daalna + Actions ON karna.
Baaki = GitHub khud roz auto chalayega. Bas.
```

---

## ✅ STEP 0 — Kya-kya chahiye (checklist)

| Cheez | Free? | Zaroori? |
|---|---|---|
| GitHub account | ✅ | **Haan** (deploy yahin hoga) |
| VS Code (PC par) | ✅ | Haan (edit + push ke liye) |
| Git installed | ✅ | Haan |
| Python 3.12+ (local test ke liye) | ✅ | Optional (test ke liye) |
| 1 LLM key (Gemini ya Groq — free tier) | ✅ | **Haan** (content likhne ke liye) |
| 1 WordPress site (WordPress.com free ya apna) | ✅ | Live post ke liye |

> **Minimum to start:** GitHub + 1 LLM key + 1 WordPress site. Baaki sab optional.

---

## 📥 STEP 1 — Workspace apne PC par le aao

Arena workspace ke file explorer se poora `trend-earning-system/` folder
**download** kar le (ya zip export). Apne PC par kisi folder mein rakh de, jaise:

```
C:\Users\<tu>\projects\trend-earning-system     (Windows)
~/projects/trend-earning-system                 (Mac/Linux)
```

---

## 🖥️ STEP 2 — VS Code mein kholo

1. VS Code kholo → **File → Open Folder** → `trend-earning-system` chuno.
2. Left panel mein saara code dikhega (`run.py`, `core/`, `pipeline/`, etc).
3. Recommended extensions (VS Code khud suggest karega): **Python**, **GitLens**.

---

## 🧪 STEP 3 — Local test (optional par recommended)

VS Code mein **Terminal → New Terminal** kholo, phir:

```bash
# 1) virtual environment banao
python -m venv .venv

# 2) activate karo
#   Windows:
.venv\Scripts\activate
#   Mac/Linux:
source .venv/bin/activate

# 3) dependencies install (bas PyYAML — ekdum halka)
pip install -r requirements.txt

# 4) apni keys ka file banao
cp .env.example .env          # Windows PowerShell: copy .env.example .env
#   ab .env kholo aur apni keys bharo (neeche STEP 5 dekho konsi)

# 5) SAFE test — kuch publish nahi hoga, sirf simulate
#   .env mein DRY_RUN=true rakho, phir:
python run.py --no-jitter

# 6) sab pass ho raha hai check karo
python tests/test_smoke.py
```

`ALL SMOKE TESTS PASSED` aa gaya = sab sahi hai. ✅

> **DRY_RUN=true** rehte hue kuch bhi live publish nahi hota — bindaas test kar.

---

## 🐙 STEP 4 — GitHub par push (2 tareeke)

### Aasaan tareeka — VS Code se (GUI)
1. Left bar mein **Source Control** icon (branch jaisa) click karo.
2. **Publish to GitHub** button dabao.
3. **Private** repository chuno (recommended — code private rahega).
4. VS Code khud repo bana ke push kar dega. Bas. 🎉

### Ya command line se
```bash
git init
git add .
git commit -m "Trend earning system — initial deploy"
# GitHub par ek naya EMPTY repo banao (github.com/new), phir:
git branch -M main
git remote add origin https://github.com/<tera-username>/<repo-name>.git
git push -u origin main
```

> `.gitignore` already set hai — teri `.env` (secrets) kabhi push nahi hogi. Safe. 🔒

---

## 🔑 STEP 5 — GitHub Secrets daalo (yahan keys jaati hain, .env nahi)

GitHub par apne repo mein jaao:
**Settings → Secrets and variables → Actions → New repository secret**

Har key ek-ek karke add karo (Name + Value). **Minimum to go live:**

| Secret Name | Kahan se milega | Zaroori? |
|---|---|---|
| `GEMINI_API_KEY` | aistudio.google.com/apikey (free) | ✅ (ya Groq) |
| `GROQ_API_KEY` | console.groq.com/keys (free, fast) | ✅ (ya Gemini) |
| `WP1_URL` | teri site ka URL, e.g. `https://mysite.com` | ✅ publish ke liye |
| `WP1_USER` | WordPress username | ✅ |
| `WP1_APP_PASSWORD` | WP → Users → Profile → **Application Passwords** | ✅ |

**Paise kamane ke liye (jab ready ho):**

| Secret | Kaam |
|---|---|
| `AMAZON_ASSOCIATE_TAG` | Amazon affiliate links |
| `ADSENSE_PUBLISHER_ID` + `ADSENSE_SLOT_IN_ARTICLE` | Display ads |
| `IMPACT_AFFILIATE_ID`, `SHAREASALE_AFFILIATE_ID`, ... | High-commission networks |
| `TELEGRAM_BOT_TOKEN` + `TELEGRAM_CHAT_ID` | Approval + notifications |
| `FIRECRAWL_API_KEY` | Behtar research scraping (free tier) |

> **`GITHUB_TOKEN` add karne ki zaroorat NAHI** — GitHub Actions khud provide
> karta hai (live GitHub trend data usi se chalega). ✅
> Baaki jo secret naa daalo, wo feature bas skip ho jaata hai — kuch crash nahi hota.

---

## ⚙️ STEP 6 — Actions ON + pehla test run

1. Repo mein **Actions** tab kholo → agar poochhe to **"I understand, enable"**.
2. Left se **"Daily Content"** workflow chuno.
3. **Run workflow** button → input `dry_run` = **true** rakho → **Run**.
4. Run par click karke live logs dekho. Green ✅ = sab kaam kar raha.

> Cron already set hai: roz **~8AM, ~2PM, ~8PM IST** (jitter ke saath) auto chalega.

---

## 🟢 STEP 7 — LIVE jao (asli publish)

Jab dry-run se khush ho jao:

- Workflow ko `dry_run = false` ke saath chalao (ya schedule ko chhod do — wo
  default `false` par hi live publish karta hai).
- Bas! Ab har din 3 posts khud ban ke publish honge. 🎯

---

## 🎬 (Optional) Video-for-SEO render chalu karna

Abhi har post ke saath VideoObject schema + YouTube pack + OpenMontage
**manifest** ban raha hai (`data/video_briefs/`). Actual video render tab hoga
jab tu OpenMontage locally set kare:

```bash
git clone https://github.com/calesthio/OpenMontage.git
cd OpenMontage && make setup      # free stack: Piper TTS + FFmpeg + Remotion
# phir .env / secret mein:
OPENMONTAGE_DIR=/path/to/OpenMontage
```

Ye 100% optional hai — bina iske bhi video ka SEO fayda (schema + wider research) mil raha hai.

---

## 🆘 Troubleshooting

| Problem | Fix |
|---|---|
| Actions run fail — "no API key" | Us feature ka secret missing. LLM key zaroori. |
| Kuch publish nahi hua | `DRY_RUN` true tha ya WP secrets missing/galat. |
| WordPress 401 error | App Password use karo (normal login password nahi). |
| GitHub trend data 403 | Rate limit — GitHub Actions ke andar auto-token se theek chalta hai. |
| `.env` galti se push? | `.gitignore` rok deta hai; phir bhi tab keys turant rotate kar de. |
| Local run slow | Sandbox/offline network ke timeouts — CI (GitHub) par fast chalega. |

---

## 📁 Kaunsi file kya karti hai (quick map)

| File | Kaam |
|---|---|
| `run.py` | Master orchestrator — sab niche agents chalata hai |
| `discover.py` | 28 industries rank + kisi ko bhi auto-run karo |
| `brain_train.py` | Knowledge base dekho / train karo |
| `dashboard.py` | Local dashboard (`--serve`) |
| `config/niches.yaml` | Saari settings — niches, market, video_seo, accounts |
| `.env` | Teri keys (local only, kabhi push nahi) |
| `.github/workflows/daily-content.yml` | Auto cron — roz 3 baar |

---

### TL;DR (3 line)
1. Folder → VS Code → **Publish to GitHub** (private).
2. **Settings → Secrets** mein LLM key + WordPress key daalo.
3. **Actions → Run workflow** (dry_run true → phir false). Ho gaya, ab auto-pilot. 🚀
