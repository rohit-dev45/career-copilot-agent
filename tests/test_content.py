from datetime import datetime
import pytest
from career_copilot.content import Claim, Draft, Source, fact_check, render_caption, slide_outline, check_note_length
from career_copilot.scheduler import metrics_checkpoints, send
from career_copilot.verify import classify_page
from career_copilot.slides import render_carousel


def make(claims):
    return Draft("Hook", claims, ["t1"], "Q?", ["AI"])


def test_single_secondary_source_fails():
    d = make([Claim("x", [Source("blog", "https://a.com/1", "2026-01-01")])])
    assert fact_check(d)


def test_two_domains_pass_and_caption_lists_sources():
    d = make([Claim("x", [Source("a", "https://a.com/1", "d"), Source("b", "https://www.b.org/2", "d")])])
    assert fact_check(d) == []
    cap = render_caption(d)
    assert "https://a.com/1" in cap and cap.endswith("#AI")


def test_same_domain_twice_fails():
    d = make([Claim("x", [Source("a", "https://a.com/1", "d"), Source("a2", "https://www.a.com/2", "d")])])
    assert fact_check(d)


def test_note_length():
    assert check_note_length("hi") and not check_note_length("x" * 201)


def test_checkpoints():
    t = datetime(2026, 1, 1, 8)
    assert [c.hour for c in metrics_checkpoints(t)] == [8, 8]
    assert (metrics_checkpoints(t)[1] - t).days == 3


def test_send_requires_approval():
    with pytest.raises(PermissionError):
        send({}, "u", "k", approved=False)


def test_classify_page():
    assert classify_page(200, "Apply now")
    assert not classify_page(200, "This job is closed")
    assert not classify_page(404, "")


def test_render_carousel(tmp_path):
    d = make([Claim("x", [Source("Primary docs", "https://a.com", "d")])])
    pngs, pdf = render_carousel(slide_outline(d), str(tmp_path))
    assert len(pngs) == 4
    assert open(pdf, "rb").read(4) == b"%PDF"
