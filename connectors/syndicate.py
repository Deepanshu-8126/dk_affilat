"""
WOPE syndication: push the canonical WordPress post to DEV.to / Medium / Hashnode
with a rel=canonical back to the primary site (backlinks + no duplicate-content
penalty).

Each platform is a thin function. Missing token => simulated result so the
pipeline still completes. Modelled after a-vip/automated-syndicator behaviour.
"""
from __future__ import annotations

import os
import re

from connectors.http import get_json, post_json
from core.logging_utils import get_logger

log = get_logger("syndicate")


def _sim(platform: str, slug: str) -> dict:
    handle = os.getenv("SYNDICATE_HANDLE", "anitadevi23736")
    fake = {
        "devto": f"https://dev.to/{handle}/{slug}",
        "medium": f"https://medium.com/@{handle}/{slug}",
        "hashnode": f"https://{handle}.hashnode.dev/{slug}",
    }.get(platform, f"https://{platform}.example/{slug}")
    log.info("[sim] %s syndication -> %s", platform, fake)
    return {"ok": True, "url": fake, "simulated": True}


def to_devto(*, title: str, body_markdown: str, canonical_url: str,
             tags: list[str], slug: str, token_env: str | None = None) -> dict:
    key = os.getenv(token_env or "DEVTO_API_KEY")
    dry = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
    if dry or not key:
        return _sim("devto", slug)
    payload = {"article": {
        "title": title,
        "body_markdown": body_markdown,
        "published": True,
        "canonical_url": canonical_url,
        "tags": [t.replace(" ", "")[:20] for t in tags[:4]],
    }}
    try:
        data = post_json("https://dev.to/api/articles", payload,
                         headers={"api-key": key})
        return {"ok": True, "url": data.get("url", "")}
    except Exception as e:  # noqa: BLE001
        log.error("devto failed: %s", e)
        return {"ok": False, "error": str(e), "url": ""}


def to_hashnode(*, title: str, body_markdown: str, canonical_url: str,
                tags: list[str], slug: str, token_env: str | None = None) -> dict:
    token = os.getenv(token_env or "HASHNODE_TOKEN")
    pub_id = os.getenv("HASHNODE_PUBLICATION_ID")
    dry = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
    if dry or not (token and pub_id):
        return _sim("hashnode", slug)
    query = """
    mutation Publish($input: PublishPostInput!) {
      publishPost(input: $input) { post { url } }
    }"""
    variables = {"input": {
        "title": title,
        "contentMarkdown": body_markdown,
        "publicationId": pub_id,
        "originalArticleURL": canonical_url,
        "tags": [{"slug": t.lower().replace(" ", "-"), "name": t} for t in tags[:5]],
    }}
    try:
        data = post_json("https://gql.hashnode.com/",
                         {"query": query, "variables": variables},
                         headers={"Authorization": token})
        url = data["data"]["publishPost"]["post"]["url"]
        return {"ok": True, "url": url}
    except Exception as e:  # noqa: BLE001
        log.error("hashnode failed: %s", e)
        return {"ok": False, "error": str(e), "url": ""}


def to_medium(*, title: str, body_markdown: str, canonical_url: str,
              tags: list[str], slug: str, token_env: str | None = None) -> dict:
    token = os.getenv(token_env or "MEDIUM_TOKEN")
    dry = os.getenv("DRY_RUN", "true").lower() in ("1", "true", "yes")
    if dry or not token:
        return _sim("medium", slug)
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        user_info = get_json("https://api.medium.com/v1/me", headers=headers)
        user_id = (user_info.get("data") or {}).get("id")
        if not user_id:
            return {"ok": False, "error": f"Failed to retrieve Medium user profile: {user_info}", "url": ""}

        clean_tags = [re.sub(r"[^a-zA-Z0-9-]", "", t.replace(" ", "-"))[:25] for t in tags[:5] if t.strip()]
        payload = {
            "title": title,
            "contentFormat": "markdown",
            "content": body_markdown,
            "canonicalUrl": canonical_url,
            "tags": clean_tags,
            "publishStatus": "public",
        }
        res = post_json(f"https://api.medium.com/v1/users/{user_id}/posts", payload, headers=headers)
        url = (res.get("data") or {}).get("url", "")
        return {"ok": True, "url": url}
    except Exception as e:  # noqa: BLE001
        log.error("medium failed: %s", e)
        return {"ok": False, "error": str(e), "url": ""}


DISPATCH = {"devto": to_devto, "medium": to_medium, "hashnode": to_hashnode}
