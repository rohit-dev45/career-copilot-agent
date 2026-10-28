"""Check that a listing URL is still reachable. Plain HTTP GET on official pages only; no scraping of logged-in sites."""
from __future__ import annotations
import urllib.request

CLOSED_MARKERS = ("no longer accepting", "position has been filled", "job not found", "this job is closed")


def classify_page(status: int, body: str) -> bool:
    if status >= 400:
        return False
    low = body.lower()
    return not any(m in low for m in CLOSED_MARKERS)


def is_listing_live(url: str, timeout: float = 10.0) -> bool | None:
    """True/False when determinable, None on network error (treat as unverified)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "career-copilot-agent/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return classify_page(resp.status, resp.read(200_000).decode("utf-8", "ignore"))
    except urllib.error.HTTPError as e:
        return classify_page(e.code, "")
    except Exception:
        return None
