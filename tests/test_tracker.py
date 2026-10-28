import pytest
from career_copilot.tracker import CsvTracker, JOB_FIELDS


def test_upsert_dedupes_and_backs_up(tmp_path):
    p = tmp_path / "t.csv"
    t = CsvTracker(str(p), JOB_FIELDS, key="url")
    assert t.upsert([{"url": "a", "status": "awaiting-human"}]) == 1
    assert t.upsert([{"url": "a"}, {"url": "b", "status": "awaiting-human"}]) == 1
    assert [r["url"] for r in t.read()] == ["a", "b"]
    assert any(".bak-" in f.name for f in tmp_path.iterdir())


def test_set_status(tmp_path):
    t = CsvTracker(str(tmp_path / "t.csv"), JOB_FIELDS, key="url")
    t.upsert([{"url": "a", "status": "awaiting-human"}])
    assert t.set_status("a", "applied")
    assert t.read()[0]["status"] == "applied"
    assert not t.set_status("zzz", "applied")
    with pytest.raises(ValueError):
        t.set_status("a", "auto-posted")
