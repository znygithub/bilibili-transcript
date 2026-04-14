from bilibili_transcript.draft_md import chunk_segments_by_span, build_draft_transcript_markdown


def _seg(start, end, text="hello"):
    return {"start": start, "end": end, "text": text}


class TestChunkSegments:
    def test_empty(self):
        assert chunk_segments_by_span([]) == []

    def test_single_chunk(self):
        segs = [_seg(0, 10), _seg(10, 20), _seg(20, 30)]
        chunks = chunk_segments_by_span(segs, max_span_seconds=300)
        assert len(chunks) == 1
        assert len(chunks[0]) == 3

    def test_split_by_span(self):
        segs = [_seg(0, 50), _seg(50, 100), _seg(100, 200), _seg(200, 350)]
        chunks = chunk_segments_by_span(segs, max_span_seconds=100)
        assert len(chunks) >= 2


class TestBuildDraft:
    def test_basic_structure(self):
        segs = [_seg(0, 60, "测试"), _seg(60, 120, "内容")]
        md = build_draft_transcript_markdown("测试视频", segs, max_span_seconds=300)
        assert "# 测试视频" in md
        assert "## 全文总结" in md
        assert "## 1. 完整逐字稿" in md
        assert "测试" in md
        assert "内容" in md
