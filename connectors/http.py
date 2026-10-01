"""Tiny HTTP helper (stdlib) shared by connectors."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

DEFAULT_TIMEOUT = 45


def request(method: str, url: str, *, headers: dict | None = None,
            json_body: Any = None, data: bytes | None = None,
            timeout: int = DEFAULT_TIMEOUT) -> tuple[int, bytes]:
    headers = dict(headers or {})
    body = data
    if json_body is not None:
        body = json.dumps(json_body).encode()
        headers.setdefault("Content-Type", "application/json")
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def get_json(url: str, headers: dict | None = None, timeout: int = DEFAULT_TIMEOUT) -> Any:
    status, raw = request("GET", url, headers=headers, timeout=timeout)
    if status >= 400:
        raise RuntimeError(f"GET {url} -> {status}: {raw[:200]!r}")
    return json.loads(raw.decode())


def post_json(url: str, payload: Any, headers: dict | None = None,
              timeout: int = DEFAULT_TIMEOUT) -> Any:
    status, raw = request("POST", url, headers=headers, json_body=payload, timeout=timeout)
    if status >= 400:
        raise RuntimeError(f"POST {url} -> {status}: {raw[:200]!r}")
    return json.loads(raw.decode()) if raw else {}
