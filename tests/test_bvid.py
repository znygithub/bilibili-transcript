from bilibili_transcript.bvid import extract_bvid, video_page_url, video_page_url_part
import pytest


class TestExtractBvid:
    def test_raw_bvid(self):
        assert extract_bvid("BV1f3DYBDE9h") == "BV1f3DYBDE9h"

    def test_from_url(self):
        assert extract_bvid("https://www.bilibili.com/video/BV1f3DYBDE9h") == "BV1f3DYBDE9h"

    def test_from_url_with_query(self):
        assert extract_bvid("https://www.bilibili.com/video/BV1f3DYBDE9h?p=2") == "BV1f3DYBDE9h"

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            extract_bvid("not-a-bvid")

    def test_short_bv_raises(self):
        with pytest.raises(ValueError):
            extract_bvid("BV123")


class TestVideoPageUrl:
    def test_basic(self):
        assert video_page_url("BV1f3DYBDE9h") == "https://www.bilibili.com/video/BV1f3DYBDE9h"

    def test_part_1(self):
        assert video_page_url_part("BV1f3DYBDE9h", 1) == "https://www.bilibili.com/video/BV1f3DYBDE9h"

    def test_part_2(self):
        assert video_page_url_part("BV1f3DYBDE9h", 2) == "https://www.bilibili.com/video/BV1f3DYBDE9h?p=2"
