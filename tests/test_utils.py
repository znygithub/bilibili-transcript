from bilibili_transcript.utils import fmt_ts


def test_zero():
    assert fmt_ts(0) == "00:00"


def test_negative_clamps():
    assert fmt_ts(-5) == "00:00"


def test_seconds():
    assert fmt_ts(65.7) == "01:05"


def test_large():
    assert fmt_ts(3661) == "61:01"
