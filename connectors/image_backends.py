"""
Image generation backends for hero / OG / author-avatar images.

Priority:
  1. Z-Image-Turbo via a local/remote endpoint (Z_IMAGE_URL) — the PRD's choice.
  2. Pollinations free text-to-image (no key) as a hosted fallback.
  3. Deterministic local SVG placeholder (always works, zero deps/network) so
     the pipeline never breaks on the image step.
"""
from __future__ import annotations

import hashlib
import os
import urllib.parse
import urllib.request
from pathlib import Path

from connectors.http_client_utils import request
from core.logging_utils import get_logger

log = get_logger("image")


def generate(prompt: str, out_path: Path, *, width: int, height: int) -> bool:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    dry = os.getenv("DRY_RUN", "false").lower() in ("1", "true", "yes")

    if not dry and os.getenv("Z_IMAGE_URL"):
        if _z_image(prompt, out_path, width, height):
            return True
    
    # Always enable Pollinations free AI image generator as active backend
    if not dry or os.getenv("ENABLE_POLLINATIONS", "true").lower() in ("1", "true", "yes"):
        if _pollinations(prompt, out_path, width, height):
            return True

    _placeholder_svg(prompt, out_path.with_suffix(".svg"), width, height)
    return False


def _z_image(prompt: str, out_path: Path, w: int, h: int) -> bool:
    try:
        url = os.getenv("Z_IMAGE_URL", "").rstrip("/") + "/generate"
        status, raw = request("POST", url, json_body={
            "prompt": prompt, "width": w, "height": h, "steps": 8,
        }, timeout=90)
        if status < 400 and raw[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1"):
            out_path.write_bytes(raw)
            log.info("Z-Image-Turbo generated %s", out_path.name)
            return True
        log.warning("Z-Image endpoint returned non-image (status=%s)", status)
    except Exception as e:  # noqa: BLE001
        log.warning("Z-Image failed: %s", e)
    return False


def _pollinations(prompt: str, out_path: Path, w: int, h: int) -> bool:
    try:
        q = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{q}?width={w}&height={h}&nologo=true"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=90) as resp:
            raw = resp.read()
        out_path.write_bytes(raw)
        log.info("Pollinations generated %s", out_path.name)
        return True
    except Exception as e:  # noqa: BLE001
        log.warning("Pollinations failed: %s", e)
        return False


def _placeholder_svg(prompt: str, out_path: Path, w: int, h: int) -> None:
    seed = hashlib.md5(prompt.encode()).hexdigest()
    c1, c2 = f"#{seed[:6]}", f"#{seed[6:12]}"
    label = (prompt[:48] + "…") if len(prompt) > 48 else prompt
    label = label.replace("&", "&amp;").replace("<", "&lt;")
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/>
  </linearGradient></defs>
  <rect width="{w}" height="{h}" fill="url(#g)"/>
  <rect x="24" y="{h-96}" width="{w-48}" height="72" rx="10" fill="rgba(0,0,0,0.35)"/>
  <text x="40" y="{h-50}" font-family="Segoe UI,Arial,sans-serif" font-size="26"
        fill="#fff" font-weight="700">{label}</text>
</svg>"""
    out_path.write_text(svg, encoding="utf-8")
    log.info("placeholder image -> %s", out_path.name)
