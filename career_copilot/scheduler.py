"""Optional hand-off to a social scheduling API you already use.

Builds the request payload; sending is opt-in (--send) and always requires
an approved draft. LinkedIn itself is never automated by this project.
"""
from __future__ import annotations
import json
import urllib.request
from datetime import datetime, timedelta


def build_payload(caption: str, pdf_path: str, publish_at: datetime, channel: str) -> dict:
    return {"channel": channel, "text": caption, "document": pdf_path,
            "publish_at": publish_at.isoformat(), "status": "scheduled"}


def metrics_checkpoints(published_at: datetime) -> list[datetime]:
    """When to ask the human for an analytics screenshot (24h and 72h)."""
    return [published_at + timedelta(hours=24), published_at + timedelta(hours=72)]


def send(payload: dict, api_url: str, api_key: str, approved: bool) -> int:
    if not approved:
        raise PermissionError("draft not approved by a human")
    if not api_url or not api_key:
        raise RuntimeError("SCHEDULER_API_URL / SCHEDULER_API_KEY not set")
    req = urllib.request.Request(api_url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.status
