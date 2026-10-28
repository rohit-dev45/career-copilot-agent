"""Content pipeline: news items -> fact-check gate -> caption + slide outline.

Drafting is template-based on purpose. Plug in any LLM by implementing `Drafter`;
the fact-check gate still runs on whatever it returns.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Protocol

LINKEDIN_CAPTION_LIMIT = 3000
CONNECTION_NOTE_LIMIT = 200


@dataclass
class Source:
    title: str
    url: str
    published: str  # ISO date


@dataclass
class Claim:
    text: str
    sources: list[Source] = field(default_factory=list)

    @property
    def verified(self) -> bool:
        # A claim needs two independent sources (distinct domains) or one primary source.
        domains = {re.sub(r"^https?://(www\.)?", "", s.url).split("/")[0] for s in self.sources}
        return len(domains) >= 2 or any("primary" in s.title.lower() for s in self.sources)


@dataclass
class Draft:
    hook: str
    claims: list[Claim]
    takeaways: list[str]
    question: str
    hashtags: list[str]


def fact_check(draft: Draft) -> list[str]:
    """Return problems; empty list means the draft may go to a human for approval."""
    problems = [f"unverified claim: {c.text}" for c in draft.claims if not c.verified]
    if len(draft.hashtags) > 5:
        problems.append("more than 5 hashtags")
    if len(render_caption(draft)) > LINKEDIN_CAPTION_LIMIT:
        problems.append("caption over LinkedIn limit")
    return problems


def render_caption(draft: Draft) -> str:
    lines = [draft.hook, ""]
    lines += [f"- {c.text}" for c in draft.claims]
    lines += ["", "What I take from it:"]
    lines += [f"{i}. {t}" for i, t in enumerate(draft.takeaways, 1)]
    lines += ["", draft.question, "", "Sources:"]
    seen = []
    for c in draft.claims:
        for s in c.sources:
            if s.url not in seen:
                seen.append(s.url)
    lines += seen
    lines += ["", " ".join(f"#{h.lstrip('#')}" for h in draft.hashtags)]
    return "\n".join(lines)


def slide_outline(draft: Draft) -> list[dict]:
    slides = [{"title": draft.hook, "body": ""}]
    slides += [{"title": f"Fact {i}", "body": c.text} for i, c in enumerate(draft.claims, 1)]
    slides += [{"title": "Takeaways", "body": "\n".join(draft.takeaways)}]
    slides += [{"title": "Your turn", "body": draft.question}]
    return slides


def check_note_length(text: str, limit: int = CONNECTION_NOTE_LIMIT) -> bool:
    return len(text) <= limit


class Drafter(Protocol):
    def draft(self, topic: str, sources: list[Source]) -> Draft: ...
