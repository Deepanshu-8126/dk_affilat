"""
MULTI-ACCOUNT ROTATOR.

Spreads syndication across multiple accounts per platform to scale reach and
reduce the chance any single account gets rate-limited/flagged. Rotation state
is persisted so it survives across runs (round-robin actually rotates).

Only accounts whose env var is set are considered "healthy"; everything else is
skipped, so the system works with 1 account and scales as you add more.
"""
from __future__ import annotations

import json
import os
import random
from pathlib import Path

from core.config import DATA_DIR
from core.logging_utils import get_logger

log = get_logger("accounts")

_STATE = DATA_DIR / "accounts_state.json"


def _load_state() -> dict:
    if _STATE.exists():
        return json.loads(_STATE.read_text(encoding="utf-8"))
    return {}


def _save_state(state: dict) -> None:
    _STATE.parent.mkdir(parents=True, exist_ok=True)
    _STATE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def healthy_accounts(platform: str, pools: dict) -> list[str]:
    """Return env-var names for the platform that actually have a value set."""
    return [env for env in pools.get(platform, []) if os.getenv(env)]


def pick_account(platform: str, cfg: dict) -> str | None:
    """
    Return the env var NAME of the account token to use for this platform,
    honouring the configured rotation policy. None => no configured account
    (caller should simulate / skip).
    """
    pools = cfg.get("pools", {})
    rotation = cfg.get("rotation", "round_robin")
    healthy = healthy_accounts(platform, pools)
    if not healthy:
        # fall back to the first declared env even if empty (simulated mode)
        declared = pools.get(platform, [])
        return declared[0] if declared else None

    state = _load_state()
    if rotation == "random":
        choice = random.choice(healthy)
    elif rotation == "least_recent":
        counts = state.get("counts", {})
        choice = min(healthy, key=lambda e: counts.get(e, 0))
    else:  # round_robin
        idx = state.get("rr", {}).get(platform, -1) + 1
        choice = healthy[idx % len(healthy)]
        state.setdefault("rr", {})[platform] = idx

    state.setdefault("counts", {})
    state["counts"][choice] = state["counts"].get(choice, 0) + 1
    _save_state(state)
    log.info("platform=%s -> account env '%s' (%d healthy)",
             platform, choice, len(healthy))
    return choice


def account_summary(cfg: dict) -> dict:
    pools = cfg.get("pools", {})
    return {p: {"configured": len(envs), "healthy": len(healthy_accounts(p, pools))}
            for p, envs in pools.items()}
