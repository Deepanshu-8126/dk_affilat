"""
Telegram HITL (human-in-the-loop) approval bridge.

Two modes:
  * send_for_approval(): posts the article card with inline buttons
    [APPROVE] [REJECT] [REWRITE] and returns immediately (async approval), OR
  * poll_decision(): blocks briefly waiting for a callback/reply (used by the
    long-poll approval script).

When TELEGRAM_BOT_TOKEN is missing or AUTO_APPROVE=true, it auto-approves so the
pipeline can run unattended (CI smoke tests, first-time setup).
"""
from __future__ import annotations

import os
import time

from connectors.http_client_utils import get_json, post_json
from core.logging_utils import get_logger

log = get_logger("telegram")


def _cfg() -> tuple[str | None, str | None]:
    return os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")


def _api(token: str, method: str) -> str:
    return f"https://api.telegram.org/bot{token}/{method}"


def enabled() -> bool:
    token, chat = _cfg()
    auto = os.getenv("AUTO_APPROVE", "false").lower() in ("1", "true", "yes")
    return bool(token and chat) and not auto


def send_card(article) -> dict:
    """Send an approval card. Returns {'message_id'} or auto-approval marker."""
    token, chat = _cfg()
    if not enabled():
        log.info("Telegram disabled/auto -> auto-approving '%s'", article.title)
        return {"auto": True}

    seo = article.seo.score
    kw = article.seo.focus_keyword or (article.brief.primary_keyword if article.brief else "")
    text = (
        f"📝 *Post Ready* — {article.niche_id}\n\n"
        f"*{_md(article.title)}*\n\n"
        f"👤 {article.author_name}\n"
        f"📊 SEO: {seo:.0f}/100   ✅ QC: {article.qc.score:.0f}/100\n"
        f"🔑 Keyword: `{_md(kw)}`\n"
        f"📄 {article.word_count} words   🖼️ {len(article.images)} images\n\n"
        f"_{_md(article.excerpt[:220])}_"
    )
    kb = {"inline_keyboard": [[
        {"text": "✅ APPROVE", "callback_data": f"approve:{article.run_id}:{article.niche_id}"},
        {"text": "❌ REJECT", "callback_data": f"reject:{article.run_id}:{article.niche_id}"},
        {"text": "🔄 REWRITE", "callback_data": f"rewrite:{article.run_id}:{article.niche_id}"},
    ]]}
    try:
        data = post_json(_api(token, "sendMessage"), {
            "chat_id": chat, "text": text, "parse_mode": "Markdown",
            "reply_markup": kb,
        })
        return {"message_id": data["result"]["message_id"]}
    except Exception as e:  # noqa: BLE001
        log.error("telegram send failed (%s) -> auto-approve", e)
        return {"auto": True}


def poll_decision(run_id: str, niche_id: str, *, timeout: int = 900,
                  interval: int = 5) -> str:
    """
    Long-poll getUpdates for a callback matching this article.
    Returns one of: approve | reject | rewrite | timeout.
    """
    token, chat = _cfg()
    if not enabled():
        return "approve"
    deadline = time.time() + timeout
    offset = 0
    while time.time() < deadline:
        try:
            data = get_json(_api(token, f"getUpdates?timeout={interval}&offset={offset}"))
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                cb = upd.get("callback_query")
                if not cb:
                    continue
                payload = cb.get("data", "")
                action, _, rest = payload.partition(":")
                if rest == f"{run_id}:{niche_id}":
                    _answer(token, cb["id"], f"Got it: {action}")
                    return action
        except Exception as e:  # noqa: BLE001
            log.warning("poll error: %s", e)
        time.sleep(interval)
    return "timeout"


def _answer(token: str, callback_id: str, text: str) -> None:
    try:
        post_json(_api(token, "answerCallbackQuery"),
                  {"callback_query_id": callback_id, "text": text})
    except Exception:  # noqa: BLE001
        pass


def notify(text: str) -> None:
    token, chat = _cfg()
    if not (token and chat):
        log.info("[telegram] %s", text)
        return
    try:
        post_json(_api(token, "sendMessage"),
                  {"chat_id": chat, "text": text, "parse_mode": "Markdown"})
    except Exception as e:  # noqa: BLE001
        log.warning("notify failed: %s", e)


def _md(s: str) -> str:
    for ch in "_*[]()~`>#+-=|{}.!":
        s = s.replace(ch, f"\\{ch}") if ch in "`_*[" else s
    return s
