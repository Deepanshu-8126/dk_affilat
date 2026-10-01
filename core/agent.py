"""
BaseNicheAgent — runs the shared 7-step pipeline with a niche-specific brain,
tone and author persona. The three concrete agents (agent_1/2/3) are thin
subclasses that only differ by config id.
"""
from __future__ import annotations

import time
import uuid

from connectors import openmontage, telegram
from connectors.wordpress import WordPressClient
from core.adaptive import build_learned_directive
from core.config import AppConfig, NicheConfig
from core.knowledge import load_kb
from core.llm import Brain
from core.logging_utils import get_logger
from core.models import Article, ApprovalDecision, Stage
from core.state import mark_covered, save_article
from pipeline import (geo_aeo, image_gen, market_intel, monetize, publish, qc,
                      research, seo_optimize, write)
from pipeline.trend_detect import TrendContext, detect
from pipeline.write import WriterPersona


class BaseNicheAgent:
    def __init__(self, app: AppConfig, niche_id: str, run_id: str | None = None):
        self.app = app
        self.cfg: NicheConfig = app.niche(niche_id)
        self.brain = Brain(self.cfg.brain)
        self.run_id = run_id or time.strftime("%Y%m%d-") + uuid.uuid4().hex[:6]
        self.log = get_logger(f"agent:{niche_id}")

    # -- helpers -----------------------------------------------------------
    def _persona(self) -> WriterPersona:
        a = self.cfg.author
        return WriterPersona(
            author_name=a["name"], author_title=a["title"],
            tone=self.cfg.tone, niche_name=self.cfg.name,
        )

    def _new_article(self) -> Article:
        art = Article(niche_id=self.cfg.id, run_id=self.run_id)
        art.author_name = self.cfg.author["name"]
        art.author_bio = self.cfg.author["bio"]
        art.meta["domain"] = self.cfg.domain
        art.meta["brain"] = self.cfg.brain.id
        art.meta["tone"] = self.cfg.tone
        return art

    def _checkpoint(self, art: Article) -> None:
        save_article(self.run_id, art.to_dict())

    # -- main pipeline -----------------------------------------------------
    def run(self) -> Article:
        d = self.cfg.defaults
        art = self._new_article()
        self.log.info("=== RUN %s | niche=%s | brain=%s ===",
                      self.run_id, self.cfg.id, self.cfg.brain.id)

        # STEP 1: TREND
        art.stage = Stage.TREND
        topics = detect(TrendContext(
            niche_id=self.cfg.id,
            seed_keywords=self.cfg.keywords_seed,
            sources=self.cfg.trend_sources,
            n=d.get("trends_per_run", 3),
        ))
        if not topics:
            self.log.warning("no fresh topics -> abort")
            art.stage = Stage.FAILED
            self._checkpoint(art)
            return art
        art.topic = topics[0]
        art.title = art.topic.title
        self._checkpoint(art)

        # STEP 2: RESEARCH
        art.stage = Stage.RESEARCH
        art.brief = research.build_brief(
            self.brain, art.topic,
            sources_limit=d.get("research_sources", 5),
            content_types=self.cfg.content_types,
        )
        art.title = art.brief.topic.title
        art.tags = art.brief.secondary_keywords[:5]
        self._checkpoint(art)

        # STEP 2b: MARKET STRATEGY (commercial intent + best affiliate platform)
        strategy = market_intel.build_strategy(
            art.brief,
            niche_monetization=self.cfg.monetization,
            market=d.get("market", {}),
            allowed_content_types=self.cfg.content_types,
            niche_name=self.cfg.name,
        )
        art.brief.content_type = strategy.content_type
        art.meta["market"] = strategy.to_dict()
        self._checkpoint(art)

        # STEP 3: WRITE (conditioned on: expert knowledge + learned data + market)
        art.stage = Stage.WRITE
        learned = build_learned_directive(self.cfg.id)
        art.meta["learning_confidence"] = round(learned.confidence, 3)
        kb = load_kb()
        kb_query = f"{art.title} {' '.join(art.brief.secondary_keywords)} {strategy.tier}"
        expert_brief, used_cards = kb.briefing(
            kb_query, niche_id=self.cfg.id, tier=strategy.tier, k=6)
        art.meta["knowledge_cards"] = used_cards
        combined_directive = "\n\n".join(
            x for x in (expert_brief, learned.directive, strategy.directive) if x)
        art.body_markdown = write.write_article(
            self.brain, self._persona(), art.brief,
            do_humanize=d.get("humanize", True),
            learned=combined_directive,
        )
        art.excerpt = " ".join(art.body_markdown.split()[:40])
        self._checkpoint(art)

        # STEP 3b: MONETIZE (affiliate links + FTC/Amazon disclosure)
        mon = d.get("monetization", {})
        m = self.cfg.monetization
        art.body_markdown, mon_res = monetize.apply_content_monetization(
            art.body_markdown,
            saas_slugs=m.get("saas_affiliate", []),
            amazon_enabled=m.get("amazon_associates", False),
            mon=mon,
        )
        art.meta["monetization"] = {
            "links_added": mon_res.links_added,
            "tools_linked": mon_res.tools_linked,
            "disclosure_added": mon_res.disclosure_added,
            "amazon_disclosure_added": mon_res.amazon_disclosure_added,
        }
        self._checkpoint(art)

        # STEP 4: SEO
        art.stage = Stage.SEO
        art.seo = seo_optimize.optimize(self.brain, art)
        # STEP 4b: GEO/AEO — future-safe optimisation for AI answer engines
        art.meta["geo_aeo"] = geo_aeo.apply(self.brain, art)
        self._checkpoint(art)

        # STEP 4c: VIDEO-FOR-SEO (OpenMontage repurpose logic)
        # YouTube is the 2nd-largest search engine and an embedded video lifts
        # dwell time. Build a VideoObject schema + a YouTube pack + a free
        # OpenMontage render manifest so the post ranks in a second channel.
        vcfg = d.get("video_seo", {})
        if vcfg.get("enabled", True):
            pack = openmontage.video_seo_pack(
                art.title, art.brief.primary_keyword,
                secondary_keywords=art.brief.secondary_keywords,
                outline=art.brief.outline,
                page_url=f"https://{self.cfg.domain}/{art.slug}",
                author=art.author_name,
                length=vcfg.get("length", "long"),
            )
            saved = openmontage.save_video_brief(pack, art.slug)
            art.meta["video_seo"] = {**pack.to_dict(), **saved}
            # Merge the VideoObject into the page's JSON-LD graph for real
            # video rich-result eligibility.
            base = art.seo.schema_jsonld or {}
            if base.get("@graph"):
                base["@graph"].append(pack.video_object)
            elif base:
                art.seo.schema_jsonld = {"@context": "https://schema.org",
                                         "@graph": [base, pack.video_object]}
            else:
                art.seo.schema_jsonld = pack.video_object
            self.log.info("video-for-SEO ready | schema=VideoObject | "
                          "manifest=%s | renderable=%s",
                          saved["manifest"], pack.renderable)
            self._checkpoint(art)

        # STEP 5: IMAGE
        art.stage = Stage.IMAGE
        art.images = image_gen.generate_images(
            art, author_avatar_prompt=self.cfg.author.get("avatar_prompt"))
        self._checkpoint(art)

        # STEP 6: QC
        art.stage = Stage.QC
        art.qc = qc.run_qc(art, min_score=d.get("qc_min_score", 80))
        self._checkpoint(art)
        if not art.qc.passed:
            self.log.warning("QC failed (%.1f) — needs review: %s",
                             art.qc.score, art.qc.notes[:3])
            telegram.notify(f"⚠️ QC failed for *{art.title}* "
                            f"({art.qc.score:.0f}/100) on {self.cfg.id}")

        # STEP 6b: APPROVAL (HITL)
        art.stage = Stage.APPROVAL
        art.approval = self._approve(art)
        self._checkpoint(art)
        if art.approval in (ApprovalDecision.REJECT, ApprovalDecision.REWRITE):
            self.log.info("decision=%s -> not publishing", art.approval.value)
            art.stage = Stage.DONE
            self._checkpoint(art)
            return art

        # STEP 7: PUBLISH
        art.stage = Stage.PUBLISH
        creds = self.cfg.wp_credentials()
        wp = WordPressClient(creds["base_url"], creds["user"], creds["app_password"])
        art.published = publish.publish(
            art, wp,
            platforms=d.get("publish_platforms", ["wordpress"]),
            index_now=d.get("index_now", True),
            domain=self.cfg.domain,
            mon=d.get("monetization", {}),
            accounts_cfg=d.get("accounts", {}),
        )
        mark_covered(self.cfg.id, art.topic.key)

        # SELF-TRAINING: reward the expert knowledge used, proportional to quality.
        reward = max(0.0, (art.qc.score - 75) / 50.0)   # QC 85 -> +0.2
        if reward and art.meta.get("knowledge_cards"):
            kb.reinforce(art.meta["knowledge_cards"], reward)

        art.stage = Stage.DONE
        self._checkpoint(art)

        live = [t.url for t in art.published if t.ok]
        telegram.notify(f"✅ Published *{art.title}* on {len(live)} platform(s)\n"
                        f"{chr(10).join(live)}")
        self.log.info("=== DONE %s | %d live url(s) ===", self.run_id, len(live))
        return art

    # -- approval ----------------------------------------------------------
    def _approve(self, art: Article) -> ApprovalDecision:
        if not self.app.require_approval:
            return ApprovalDecision.AUTO
        card = telegram.send_card(art)
        if card.get("auto"):
            return ApprovalDecision.AUTO
        self.log.info("waiting for Telegram approval…")
        decision = telegram.poll_decision(self.run_id, self.cfg.id)
        return {
            "approve": ApprovalDecision.APPROVE,
            "reject": ApprovalDecision.REJECT,
            "rewrite": ApprovalDecision.REWRITE,
            "timeout": ApprovalDecision.REJECT,
        }.get(decision, ApprovalDecision.REJECT)
