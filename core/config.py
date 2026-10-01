"""
Configuration loader.

Merges `config/niches.yaml` with environment variables (.env supported).
Everything the pipeline needs is resolved here so no other module reads env
directly for niche config.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "niches.yaml"
DATA_DIR = ROOT / "data"


def _load_dotenv() -> None:
    """Minimal .env loader (no dependency). Real env always wins."""
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k = k.strip()
        v = v.strip()
        if not (v.startswith('"') and v.endswith('"')) and not (v.startswith("'") and v.endswith("'")):
            v = v.split("#", 1)[0].strip()
        else:
            v = v[1:-1]
        if v or k not in os.environ:
            os.environ[k] = v


@dataclass
class BrainConfig:
    id: str
    provider: str
    model: str
    api_key_env: str | None = None
    base_url_env: str | None = None
    temperature: float = 0.7
    max_output_tokens: int = 8000
    free_tier: str = ""

    @property
    def api_key(self) -> str | None:
        return os.getenv(self.api_key_env) if self.api_key_env else None

    @property
    def base_url(self) -> str | None:
        if not self.base_url_env:
            return None
        return os.getenv(self.base_url_env, "http://localhost:11434")


@dataclass
class NicheConfig:
    id: str
    name: str
    site: dict[str, Any]
    brain: BrainConfig
    tone: str
    author: dict[str, Any]
    keywords_seed: list[str]
    trend_sources: list[str]
    monetization: dict[str, Any]
    content_types: list[str]
    defaults: dict[str, Any]

    # ---- convenience accessors -------------------------------------------
    @property
    def domain(self) -> str:
        return self.site.get("domain", "")

    def wp_credentials(self) -> dict[str, str | None]:
        return {
            "base_url": os.getenv(self.site.get("wordpress_base_url_env", "")),
            "user": os.getenv(self.site.get("wordpress_user_env", "")),
            "app_password": os.getenv(self.site.get("wordpress_app_password_env", "")),
        }


@dataclass
class AppConfig:
    defaults: dict[str, Any]
    brains: dict[str, BrainConfig] = field(default_factory=dict)
    niches: dict[str, NicheConfig] = field(default_factory=dict)

    def niche(self, niche_id: str) -> NicheConfig:
        if niche_id not in self.niches:
            raise KeyError(f"Unknown niche '{niche_id}'. Known: {list(self.niches)}")
        return self.niches[niche_id]

    @property
    def dry_run(self) -> bool:
        return os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")

    @property
    def require_approval(self) -> bool:
        return os.getenv("REQUIRE_APPROVAL", "true").lower() in ("1", "true", "yes")


def load_config(path: Path | str = CONFIG_PATH) -> AppConfig:
    _load_dotenv()
    DATA_DIR.mkdir(exist_ok=True)
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {})

    brains: dict[str, BrainConfig] = {}
    for bid, b in raw.get("brains", {}).items():
        brains[bid] = BrainConfig(
            id=bid,
            provider=b["provider"],
            model=b["model"],
            api_key_env=b.get("api_key_env"),
            base_url_env=b.get("base_url_env"),
            temperature=b.get("temperature", 0.7),
            max_output_tokens=b.get("max_output_tokens", 8000),
            free_tier=b.get("free_tier", ""),
        )

    niches: dict[str, NicheConfig] = {}
    for n in raw.get("niches", []):
        brain_id = n["brain"]
        if brain_id not in brains:
            raise ValueError(f"Niche '{n['id']}' references unknown brain '{brain_id}'")
        niches[n["id"]] = NicheConfig(
            id=n["id"],
            name=n["name"],
            site=n["site"],
            brain=brains[brain_id],
            tone=n["tone"],
            author=n["author"],
            keywords_seed=n.get("keywords_seed", []),
            trend_sources=n.get("trend_sources", []),
            monetization=n.get("monetization", {}),
            content_types=n.get("content_types", []),
            defaults=defaults,
        )

    return AppConfig(defaults=defaults, brains=brains, niches=niches)
