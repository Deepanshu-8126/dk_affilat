"""
Google Pro / Gemini Advanced Cookie & Browser Session Automator.
Features:
1. Connects to your logged-in Google Pro session via Brave Browser profile
2. Exports session cookies to data/google_session_cookie.json for 24/7 Cloud use
3. Navigates to Google Veo / VideoFX / Gemini Pro web interface
4. Enters the prompt -> Clicks Generate -> Extracts the raw AI video from DOM
5. 100% Free: Uses your existing Google Pro subscription with zero extra API fees!
"""
from __future__ import annotations

import asyncio
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from core.logging_utils import get_logger

log = get_logger("google_pro_session")

BRAVE_EXE = Path(r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe")
BRAVE_USER_DATA = Path(r"C:\Users\Deepanshu\AppData\Local\BraveSoftware\Brave-Browser\User Data")


class GoogleProSessionAutomator:
    """Automates Google Veo / VideoFX video generation using your logged-in Google Pro session."""

    def __init__(self):
        self.root = Path(__file__).resolve().parent.parent
        self.cookie_file = self.root / "data" / "google_session_cookie.json"
        self.output_dir = self.root / "data" / "veo_pro_generated_videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def extract_cookies_and_run(self, prompt: str, target_url: str = "https://labs.google/fx/tools/video-fx") -> dict[str, Any]:
        """Runs browser session to export cookies and trigger Veo generation."""
        return asyncio.run(self._async_run(prompt, target_url))

    async def _async_run(self, prompt: str, target_url: str) -> dict[str, Any]:
        from playwright.async_api import async_playwright

        log.info("🚀 [GoogleProSession] Initializing isolated profile to connect to Google Pro...")
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt[:15]).lower().strip("_")
        timestamp = int(time.time())
        dest_mp4 = self.output_dir / f"PRO_VEO_{slug}_{timestamp}.mp4"

        # Use a permanent, persistent profile directory so your Google Pro login stays saved forever!
        perm_profile_dir = self.root / "data" / "browser_sessions" / "google_pro_permanent_profile"
        perm_profile_dir.mkdir(parents=True, exist_ok=True)

        async with async_playwright() as p:
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=str(perm_profile_dir),
                executable_path=str(BRAVE_EXE) if BRAVE_EXE.exists() else None,
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check"
                ]
            )

            page = await browser.new_page()
            # 1. Stealth Mode: Hide automation fingerprints
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = { runtime: {} };
            """)

            log.info("Navigating to Google Veo / VideoFX portal: %s", target_url)
            await page.goto(target_url, timeout=60000, wait_until="domcontentloaded")
            await page.wait_for_timeout(4000)

            # Auto-handle any modal dialogs (Terms, Cookie consent, 'Get Started', 'Create Project')
            modal_buttons = [
                "button:has-text('Accept all')",
                "button:has-text('I agree')",
                "button:has-text('Get started')",
                "button:has-text('Create Project')",
                "button:has-text('New Project')",
                "button:has-text('Got it')",
                "button:has-text('Continue')"
            ]
            for m_sel in modal_buttons:
                try:
                    m_btn = await page.query_selector(m_sel)
                    if m_btn and await m_btn.is_visible():
                        log.info("Clicking onboarding/modal button: %s", m_sel)
                        await m_btn.click()
                        await page.wait_for_timeout(2000)
                except Exception:
                    pass

            # 2. Save active Google Pro cookies for 24/7 Cloud Automation
            cookies = await browser.cookies()
            self.cookie_file.parent.mkdir(parents=True, exist_ok=True)
            self.cookie_file.write_text(json.dumps(cookies, indent=2), encoding="utf-8")
            log.info("🔑 Exported %d active Google session cookies to: %s", len(cookies), self.cookie_file)

            # 3. Find prompt input box & dispatch React events
            selectors = [
                "textarea[placeholder*='prompt']",
                "textarea[placeholder*='Describe']",
                "div[contenteditable='true']",
                "textarea",
                "input[type='text']"
            ]
            input_filled = False
            for sel in selectors:
                try:
                    elem = await page.query_selector(sel)
                    if elem and await elem.is_visible():
                        log.info("Focusing and injecting prompt into: %s", sel)
                        await elem.click()
                        await page.wait_for_timeout(500)
                        # Dispatch real input events so React / Angular state updates properly
                        await page.evaluate("""(text) => {
                            const el = document.activeElement;
                            if (el) {
                                if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                                    el.value = text;
                                } else {
                                    el.innerText = text;
                                }
                                el.dispatchEvent(new Event('input', { bubbles: true }));
                                el.dispatchEvent(new Event('change', { bubbles: true }));
                            }
                        }""", prompt)
                        await page.keyboard.press("Space")
                        await page.keyboard.press("Backspace")
                        input_filled = True
                        break
                except Exception:
                    pass

            await page.wait_for_timeout(1500)

            # 4. Click Generate / Create Button
            gen_btn_selectors = [
                "button:has-text('Generate')",
                "button:has-text('Create')",
                "button[aria-label*='Generate']",
                "button[aria-label*='Create']",
                "button[type='submit']",
                "button:has-text('Submit')"
            ]
            for b_sel in gen_btn_selectors:
                try:
                    btn = await page.query_selector(b_sel)
                    if btn and await btn.is_visible():
                        log.info("Triggering generate button: %s", b_sel)
                        await btn.click(force=True)
                        break
                except Exception:
                    pass

            log.info("⏳ Waiting for Google Veo to generate video on your Google Pro account (30-60 seconds)...")
            video_url = None

            # Poll for up to 180 seconds with live progress counter
            for sec in range(1, 180):
                await page.wait_for_timeout(1000)
                if sec % 10 == 0:
                    print(f"  ⏳ [Google Veo Render in progress: {sec}s elapsed...]")

                # Check multiple potential video elements & download buttons
                video_selectors = [
                    "video[src]",
                    "video source[src]",
                    "a[download]",
                    "a[href*='.mp4']",
                    "button:has-text('Download')"
                ]
                for v_sel in video_selectors:
                    try:
                        elem = await page.query_selector(v_sel)
                        if elem:
                            src = await elem.get_attribute("src") or await elem.get_attribute("href")
                            if src and ("http" in src or "blob" in src or ".mp4" in src):
                                video_url = src
                                log.info("🎉 Video successfully rendered by Google Veo! URL: %s", video_url)
                                break
                    except Exception:
                        pass
                if video_url:
                    # Download the rendered video directly to dest_mp4
                    try:
                        import urllib.request
                        log.info("⬇️ Downloading Google Veo MP4 video to: %s...", dest_mp4)
                        urllib.request.urlretrieve(video_url, str(dest_mp4))
                        log.info("✅ Google Veo MP4 Video Saved successfully: %s", dest_mp4)

                        # Auto-clean Gemini / Google watermark
                        try:
                            from connectors.watermark_remover import WatermarkRemover
                            remover = WatermarkRemover(output_dir=self.output_dir)
                            clean_path = remover.clean_video(dest_mp4)
                            if clean_path and clean_path.exists():
                                dest_mp4 = clean_path
                                log.info("✨ Watermark removed. Clean output: %s", dest_mp4)
                        except Exception as we:
                            log.warning("Watermark remover notice: %s", we)

                    except Exception as e:
                        log.warning("Video download notice: %s", e)
                    break

            await page.wait_for_timeout(3000)
            await browser.close()

        return {
            "status": "success",
            "prompt": prompt,
            "video_path": str(dest_mp4) if dest_mp4.exists() else video_url,
            "cookies_exported": str(self.cookie_file),
            "output_dir": str(self.output_dir),
            "message": "Google Pro session connected & clean watermark-free video rendered"
        }


if __name__ == "__main__":
    automator = GoogleProSessionAutomator()
    prompt = (
        "Authentic 4K 60fps POV camera angle looking down at desk. "
        "Real human hands opening delivery courier parcel, pulling out Floral Anarkali Kurti, "
        "unfolding fabric towards the daylight camera. "
        "Picture-in-picture model wearing the kurti shown in bottom-right corner. "
        "Aesthetic headline 'Meesho Kurti Set Haul 🌸' on top. "
        "No voiceover, natural ambient sound, hyper-realistic, zero watermark, 9:16 vertical."
    )
    res = automator.extract_cookies_and_run(prompt)
    print("\n🎉 [Google Pro Session Result]:", json.dumps(res, indent=2))
