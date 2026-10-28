"""Rule-based job fit scoring (0-100) with transparent reasons."""
from __future__ import annotations
import re
from dataclasses import dataclass, field


@dataclass
class Job:
    company: str
    title: str
    location: str
    url: str
    requirements: list[str]
    min_years: int = 0
    is_live: bool | None = None  # None = not verified yet


@dataclass
class ScoreResult:
    score: int
    decision: str
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def score_job(job: Job, skills: list[str], locations: list[str], max_years: int,
              apply_threshold: int = 85, review_threshold: int = 70) -> ScoreResult:
    """Weights: skills 60, experience 20, location 20. Unverified/closed listings never auto-qualify."""
    skillset = {_norm(s) for s in skills}
    reqs = [_norm(r) for r in job.requirements] or ["(none listed)"]
    matched = [r for r in reqs if r in skillset]
    missing = [r for r in reqs if r not in skillset]
    reasons = []
    skill_pts = round(60 * len(matched) / len(reqs))
    reasons.append(f"skills {len(matched)}/{len(reqs)} -> {skill_pts}/60")

    if job.min_years <= max_years:
        exp_pts = 20
    elif job.min_years == max_years + 1:
        exp_pts = 10
    else:
        exp_pts = 0
    reasons.append(f"experience {job.min_years}+ yrs -> {exp_pts}/20")

    loc = _norm(job.location)
    loc_pts = 20 if any(_norm(p) in loc for p in locations) else 0
    reasons.append(f"location '{job.location}' -> {loc_pts}/20")

    score = max(0, min(100, skill_pts + exp_pts + loc_pts))
    if job.is_live is False:
        decision = "skip-closed"
    elif score >= apply_threshold and job.is_live:
        decision = "prepare-application"
    elif score >= apply_threshold:
        decision = "verify-listing"
    elif score >= review_threshold:
        decision = "human-review"
    else:
        decision = "skip"
    return ScoreResult(score, decision, matched, missing, reasons)


def rank_jobs(jobs: list[Job], **kw) -> list[tuple[Job, ScoreResult]]:
    scored = [(j, score_job(j, **kw)) for j in jobs]
    return sorted(scored, key=lambda p: p[1].score, reverse=True)
