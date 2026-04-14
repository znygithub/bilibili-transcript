"""Generate structured draft 成稿 Markdown from transcript JSON.

Content (summaries, headings, blurbs) comes from:
  - presets/{video_id}.json if available
  - generic placeholders otherwise

The verbatim transcript body is segments concatenated as-is.
Final polish (punctuation, paragraphing, de-filler, translation)
must be done by the AI assistant, not by this script.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from bilibili_transcript.text_post import sanitize_filename_title
from bilibili_transcript.utils import fmt_ts

PRESETS_DIR = Path(__file__).parent / "presets"
NUM_BUCKETS = 5


def load_preset(video_id: str) -> Optional[Dict[str, Any]]:
    """Load preset JSON for a specific video, or return None."""
    p = PRESETS_DIR / f"{video_id}.json"
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def split_segments_into_n_buckets(
    segments: Sequence[Dict[str, Any]],
    n: int,
) -> List[List[Dict[str, Any]]]:
    """Split segments evenly by list index, never cutting mid-segment."""
    segs = list(segments)
    if not segs or n < 1:
        return []
    per = (len(segs) + n - 1) // n
    buckets: List[List[Dict[str, Any]]] = []
    for i in range(0, len(segs), per):
        buckets.append(segs[i : i + per])
    return buckets[:n] if len(buckets) > n else buckets


def build_eval_markdown(
    *,
    title: str,
    full_summary: str,
    section_main_num: int,
    subsections: List[Tuple[str, str, str]],
) -> str:
    """Build the eval Markdown string.

    subsections: [(heading, blurb_multiline, body_verbatim), ...]
    """
    lines: List[str] = []
    lines.append(f"# {title.strip()}")
    lines.append("")
    lines.append("## 全文总结")
    lines.append("")
    for para in full_summary.strip().split("\n\n"):
        para = para.strip()
        if para:
            lines.append(para)
            lines.append("")
    lines.append(f"## {section_main_num}. 完整逐字稿")
    lines.append("")
    for h, blurb, body in subsections:
        lines.append(f"### {h}")
        lines.append("")
        for bl in blurb.strip().split("\n"):
            bl = bl.strip()
            if bl:
                lines.append(f"> {bl}")
        lines.append("")
        lines.append(body.strip())
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _resolve_content(
    video_id: str,
    num_buckets: int,
    full_text: str,
) -> Tuple[List[str], List[str], str]:
    """Return (headings, blurbs, full_summary) from preset or generic."""
    preset = load_preset(video_id)
    if preset:
        headings = preset.get("headings", [])
        blurbs = preset.get("blurbs", [])
        summary = preset.get("full_summary", "")
        # Pad if preset has fewer entries than buckets
        while len(headings) < num_buckets:
            headings.append(f"1.{len(headings)+1} 段落")
        while len(blurbs) < num_buckets:
            blurbs.append("")
        return headings, blurbs, summary

    headings = [f"1.{i+1} 第{i+1}部分" for i in range(num_buckets)]
    blurbs = [""] * num_buckets
    preview = full_text[:1500]
    summary = (
        "**【自动占位】以下为正文前约 1500 字摘抄，请替换为规范「全文总结」：**\n\n"
        + preview
        + ("\n……\n" if len(full_text) > 1500 else "\n")
    )
    return headings, blurbs, summary


def write_eval_markdown_from_json(
    json_path: Path,
    out_path: Optional[Path] = None,
) -> Path:
    """Generate structured draft 成稿.md from transcript JSON."""
    data = json.loads(json_path.read_text(encoding="utf-8"))
    title = data.get("title") or data.get("bvid") or "标题"
    segs = data.get("segments") or []
    if not segs:
        raise ValueError("No segments in JSON")

    video_id = data.get("video_id") or data.get("bvid") or "out"
    buckets = split_segments_into_n_buckets(segs, NUM_BUCKETS)
    full_text = data.get("text") or ""

    headings, blurbs, full_summary = _resolve_content(video_id, len(buckets), full_text)

    subsections: List[Tuple[str, str, str]] = []
    for i, b in enumerate(buckets):
        h = headings[i] if i < len(headings) else f"1.{i+1} 段落"
        t0, t1 = b[0]["start"], b[-1]["end"]
        extra = blurbs[i] if i < len(blurbs) else ""
        blurb = f"（时间参考：{fmt_ts(t0)}–{fmt_ts(t1)}）\n{extra.strip()}"
        body = "".join(s.get("text") or "" for s in b)
        subsections.append((h, blurb, body))

    md = build_eval_markdown(
        title=title,
        full_summary=full_summary,
        section_main_num=1,
        subsections=subsections,
    )

    slug = sanitize_filename_title(title)
    out = out_path or (json_path.parent / f"{slug}_{video_id}_transcript_成稿.md")
    out.write_text(md, encoding="utf-8")
    return out
