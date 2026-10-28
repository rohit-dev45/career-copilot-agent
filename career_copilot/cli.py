"""Command line entry point: `python -m career_copilot <command>`."""
from __future__ import annotations
import argparse
import json
from datetime import date

from .config import Settings
from .content import Claim, Draft, Source, fact_check, render_caption, slide_outline
from .jobs import Job, rank_jobs
from .slides import render_carousel
from .tracker import JOB_FIELDS, CsvTracker
from .verify import is_listing_live


def cmd_shortlist(args, st: Settings) -> None:
    jobs = [Job(**j) for j in json.load(open(args.jobs, encoding="utf-8"))]
    if args.verify:
        for j in jobs:
            j.is_live = is_listing_live(j.url)
    ranked = rank_jobs(jobs, skills=st.candidate_skills, locations=st.preferred_locations,
                       max_years=st.max_years_experience, apply_threshold=st.apply_threshold,
                       review_threshold=st.review_threshold)
    rows = []
    print(f"# Shortlist {date.today()}  (apply threshold {st.apply_threshold})\n")
    for job, r in ranked:
        print(f"- {r.score:3d}  {r.decision:20s} {job.company} - {job.title} ({job.location})")
        print(f"       missing: {', '.join(r.missing) or 'none'}")
        rows.append({"date_discovered": date.today().isoformat(), "company": job.company, "title": job.title,
                     "url": job.url, "score": r.score, "decision": r.decision,
                     "status": "awaiting-human", "next_action": "human decides"})
    added = CsvTracker(args.tracker, JOB_FIELDS, key="url").upsert(rows)
    print(f"\n{added} new row(s) written to {args.tracker}")


def cmd_post(args, st: Settings) -> None:
    raw = json.load(open(args.draft, encoding="utf-8"))
    draft = Draft(hook=raw["hook"],
                  claims=[Claim(c["text"], [Source(**s) for s in c["sources"]]) for c in raw["claims"]],
                  takeaways=raw["takeaways"], question=raw["question"], hashtags=raw["hashtags"])
    problems = fact_check(draft)
    if problems:
        print("Fact-check failed:")
        for p in problems:
            print(" -", p)
        raise SystemExit(1)
    caption = render_caption(draft)
    pngs, pdf = render_carousel(slide_outline(draft), args.out, footer=raw.get("footer", ""))
    open(f"{args.out}/caption.txt", "w", encoding="utf-8").write(caption)
    print(caption)
    print(f"\nRendered {len(pngs)} slides -> {pdf}. Review, then post or schedule it yourself.")


def main() -> None:
    p = argparse.ArgumentParser(prog="career_copilot")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("shortlist", help="score jobs from a JSON file")
    s.add_argument("--jobs", default="data/sample_jobs.json")
    s.add_argument("--tracker", default="output/job-tracker.csv")
    s.add_argument("--verify", action="store_true", help="HTTP-check each listing URL")
    c = sub.add_parser("post", help="fact-check a draft and render caption + carousel")
    c.add_argument("--draft", default="data/sample_post.json")
    c.add_argument("--out", default="output/post")
    args = p.parse_args()
    st = Settings.from_env()
    import os
    os.makedirs("output", exist_ok=True)
    {"shortlist": cmd_shortlist, "post": cmd_post}[args.cmd](args, st)


if __name__ == "__main__":
    main()
