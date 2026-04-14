import json
import tempfile
from pathlib import Path

from bilibili_transcript.finalize_md import (
    split_segments_into_n_buckets,
    load_preset,
    write_eval_markdown_from_json,
)


def _seg(i, text="hello"):
    return {"id": i, "start": i * 10.0, "end": (i + 1) * 10.0, "text": text}


class TestSplitBuckets:
    def test_empty(self):
        assert split_segments_into_n_buckets([], 5) == []

    def test_fewer_than_n(self):
        segs = [_seg(0), _seg(1), _seg(2)]
        buckets = split_segments_into_n_buckets(segs, 5)
        assert len(buckets) == 3

    def test_exact_split(self):
        segs = [_seg(i) for i in range(10)]
        buckets = split_segments_into_n_buckets(segs, 5)
        assert len(buckets) == 5
        assert all(len(b) == 2 for b in buckets)


class TestLoadPreset:
    def test_known_preset(self):
        preset = load_preset("BV1f3DYBDE9h")
        assert preset is not None
        assert len(preset["headings"]) == 5

    def test_unknown_returns_none(self):
        assert load_preset("BV_nonexistent") is None


class TestWriteEvalMarkdown:
    def test_generic_video(self):
        segs = [_seg(i, f"text{i}") for i in range(10)]
        data = {
            "video_id": "BV_test12345",
            "bvid": "BV_test12345",
            "title": "Test Video Title",
            "text": "".join(s["text"] for s in segs),
            "segments": segs,
        }
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "BV_test12345_transcript.json"
            json_path.write_text(json.dumps(data), encoding="utf-8")
            out = write_eval_markdown_from_json(json_path)
            assert out.exists()
            content = out.read_text(encoding="utf-8")
            assert "# Test Video Title" in content
            assert "## 全文总结" in content
            assert "### 1.1" in content
