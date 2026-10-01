"""
LLM brain abstraction.

One uniform `.complete(system, prompt)` interface over multiple free providers:
  - gemini  -> Google Gemini (REST, free tier)
  - groq    -> Groq OpenAI-compatible API (free tier)
  - ollama  -> local Ollama server (Qwen3, unlimited)

If a provider is unavailable (no key / no network / DRY_RUN with no key), it
degrades to a deterministic offline generator so the whole pipeline still runs.
This keeps the scaffold runnable out-of-the-box, then becomes "real" the moment
you drop API keys into .env.
"""
from __future__ import annotations

import json
import os
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass

from core.config import BrainConfig
from core.logging_utils import get_logger

log = get_logger("llm")

_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "60"))


@dataclass
class LLMResult:
    text: str
    provider: str
    model: str
    ok: bool = True
    fallback: bool = False


def _http_post(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload).encode()
    hdrs = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    }
    hdrs.update(headers)
    req = urllib.request.Request(url, data=data, headers=hdrs, method="POST")
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


class Brain:
    """A bound LLM instance for a single niche agent."""

    def __init__(self, cfg: BrainConfig) -> None:
        self.cfg = cfg

    # -- public ------------------------------------------------------------
    def complete(self, system: str, prompt: str, *, json_mode: bool = False) -> LLMResult:
        provider = self.cfg.provider
        try:
            if provider == "gemini" and self.cfg.api_key:
                return self._gemini(system, prompt, json_mode)
            if provider == "groq" and self.cfg.api_key:
                return self._groq(system, prompt, json_mode)
            if provider == "ollama":
                return self._ollama(system, prompt, json_mode)
        except (urllib.error.URLError, TimeoutError, OSError, KeyError, ValueError) as e:
            log.warning("brain=%s provider=%s failed (%s) -> offline fallback",
                        self.cfg.id, provider, e)
        # No key or failure -> offline
        return self._offline(system, prompt, json_mode)

    # -- providers ---------------------------------------------------------
    def _gemini(self, system: str, prompt: str, json_mode: bool) -> LLMResult:
        model = os.getenv("GEMINI_MODEL", self.cfg.model)
        model_name = model if model.startswith("models/") else f"models/{model}"
        url = (f"https://generativelanguage.googleapis.com/v1beta/"
               f"{model_name}:generateContent?key={self.cfg.api_key}")
        gen: dict = {
            "temperature": self.cfg.temperature,
            "maxOutputTokens": self.cfg.max_output_tokens,
        }
        if json_mode:
            gen["responseMimeType"] = "application/json"
        payload = {
            "systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": gen,
        }
        data = _http_post(url, payload, {"Content-Type": "application/json"})
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return LLMResult(text=text, provider="gemini", model=model)

    def _groq(self, system: str, prompt: str, json_mode: bool) -> LLMResult:
        model = os.getenv("GROQ_MODEL", self.cfg.model)
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": model,
            "temperature": self.cfg.temperature,
            "max_tokens": self.cfg.max_output_tokens,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {self.cfg.api_key}"}
        data = _http_post(url, payload, headers)
        text = data["choices"][0]["message"]["content"]
        return LLMResult(text=text, provider="groq", model=model)

    def _ollama(self, system: str, prompt: str, json_mode: bool) -> LLMResult:
        base = self.cfg.base_url or "http://localhost:11434"
        url = f"{base}/api/chat"
        payload = {
            "model": self.cfg.model,
            "stream": False,
            "options": {"temperature": self.cfg.temperature},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        }
        if json_mode:
            payload["format"] = "json"
        data = _http_post(url, payload, {"Content-Type": "application/json"})
        text = data["message"]["content"]
        return LLMResult(text=text, provider="ollama", model=self.cfg.model)

    # -- offline deterministic fallback ------------------------------------
    def _offline(self, system: str, prompt: str, json_mode: bool) -> LLMResult:
        """
        Deterministic, dependency-free text so the pipeline is always runnable.
        Recognises the pipeline's own prompt markers to emit useful stubs.
        """
        topic = _extract(prompt, "TOPIC:") or _extract(prompt, "TITLE:") or "AI Trend"
        if json_mode:
            return LLMResult(
                text=json.dumps(_offline_json(prompt, topic)),
                provider=self.cfg.provider, model=self.cfg.model,
                fallback=True,
            )
        return LLMResult(text=_offline_markdown(topic, self.cfg),
                         provider=self.cfg.provider, model=self.cfg.model, fallback=True)


def _extract(text: str, marker: str) -> str:
    for line in text.splitlines():
        if marker in line:
            return line.split(marker, 1)[1].strip()
    return ""


def _offline_json(prompt: str, topic: str) -> dict:
    if "OUTLINE" in prompt.upper():
        return {
            "angle": f"A practical, up-to-date breakdown of {topic}",
            "primary_keyword": topic.lower(),
            "secondary_keywords": [f"{topic} guide", f"{topic} review", f"best {topic}"],
            "content_type": "guide",
            "outline": [
                f"What is {topic}?",
                f"Why {topic} matters right now",
                "Key features and how it works",
                "Step-by-step walkthrough",
                "Pros, cons and pricing",
                "Alternatives and comparison",
                "Verdict and recommendations",
            ],
            "key_facts": [
                f"{topic} is trending across multiple platforms.",
                "Adoption is accelerating among practitioners.",
            ],
        }
    return {"result": topic}


def _offline_markdown(topic: str, cfg: BrainConfig) -> str:
    return textwrap.dedent(f"""\
    ## Introduction

    {topic} has moved from niche curiosity to something worth a serious look.
    This piece breaks down what it is, how it works, and whether it deserves a
    place in your workflow — written from hands-on testing rather than hype.

    ## What is {topic}?

    At its core, {topic} solves a concrete problem. Below we unpack the moving
    parts and the tradeoffs that actually matter in day-to-day use.

    ## How it works

    1. Set up the basics.
    2. Configure the workflow to fit your stack.
    3. Iterate and measure results.

    ## Pros and cons

    **Pros:** fast setup, sensible defaults, good free tier.
    **Cons:** a learning curve, and edge cases still need manual review.

    ## Verdict

    For most people, {topic} is worth trying. Start with the free tier, run a
    small pilot, and scale only what demonstrably saves you time.

    *(Offline draft generated by the {cfg.provider} brain fallback — add an API
    key in .env to produce full model-written content.)*
    """)
