import pytest

from bilibili_transcript.providers import detect_provider
from bilibili_transcript.providers.bilibili import BilibiliProvider


class TestBilibiliProviderMatch:
    def test_bvid(self):
        p = BilibiliProvider()
        assert p.match("BV1f3DYBDE9h")

    def test_url(self):
        p = BilibiliProvider()
        assert p.match("https://www.bilibili.com/video/BV1f3DYBDE9h")

    def test_b23(self):
        p = BilibiliProvider()
        assert p.match("https://b23.tv/abc123")

    def test_no_match(self):
        p = BilibiliProvider()
        assert not p.match("https://youtube.com/watch?v=abc")


class TestDetectProvider:
    def test_bilibili(self):
        p = detect_provider("BV1f3DYBDE9h")
        assert p.name == "bilibili"

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="No provider matched"):
            detect_provider("https://youtube.com/watch?v=abc")
