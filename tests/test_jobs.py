from career_copilot.jobs import Job, score_job, rank_jobs

SK = ["c#", ".net", "asp.net core", "sql", "git", "python"]


def job(**kw):
    base = dict(company="X", title="Dev", location="Remote", url="u", requirements=["C#", ".NET"], min_years=0)
    base.update(kw)
    return Job(**base)


def test_perfect_match_needs_live_listing():
    r = score_job(job(), SK, ["remote"], 2)
    assert r.score == 100 and r.decision == "verify-listing"
    r = score_job(job(is_live=True), SK, ["remote"], 2)
    assert r.decision == "prepare-application"


def test_closed_listing_skipped():
    assert score_job(job(is_live=False), SK, ["remote"], 2).decision == "skip-closed"


def test_experience_and_location_penalties():
    r = score_job(job(min_years=3, location="Onsite"), SK, ["remote"], 2)
    assert r.score == 70 and r.decision == "human-review"
    assert score_job(job(min_years=5, location="Onsite"), SK, ["remote"], 2).score == 60


def test_missing_skills_reported():
    r = score_job(job(requirements=["C#", "Azure"]), SK, ["remote"], 2)
    assert r.missing == ["azure"] and r.score == 70


def test_rank_order():
    ranked = rank_jobs([job(requirements=["Java"]), job()], skills=SK, locations=["remote"], max_years=2)
    assert ranked[0][1].score > ranked[1][1].score
