"""Generate time-chunked draft Markdown from transcript segments.

No summarization or translation logic — just structural scaffolding.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence

from bilibili_transcript.utils import fmt_ts


def chunk_segments_by_span(
    segments: Sequence[Dict[str, Any]],
    max_span_seconds: float = 300.0,
) -> List[List[Dict[str, Any]]]:
    """Group segments into chunks by time span."""
    if not segments:
        return []
    chunks: List[List[Dict[str, Any]]] = []
    cur: List[Dict[str, Any]] = []
    chunk_start = float(segments[0].get("start", 0))
    for seg in segments:
        t0 = float(seg.get("start", 0))
        t1 = float(seg.get("end", 0))
        if not cur:
            cur.append(seg)
            chunk_start = t0
            continue
        if t1 - chunk_start <= max_span_seconds:
            cur.append(seg)
        else:
            chunks.append(cur)
            cur = [seg]
            chunk_start = t0
    if cur:
        chunks.append(cur)
    return chunks


def build_draft_transcript_markdown(
    video_title: str,
    segments: List[Dict[str, Any]],
    max_span_seconds: float = 300.0,
    main_section_num: int = 1,
) -> str:
    """Build time-chunked draft with placeholder summary and topic headings."""
    chunks = chunk_segments_by_span(segments, max_span_seconds=max_span_seconds)
    lines: List[str] = [
        f"# {video_title}",
        "",
        "## 全文总结",
        "",
        "（在此撰写或粘贴整期总结。）",
        "",
        f"## {main_section_num}. 完整逐字稿",
        "",
    ]

    for idx, ch in enumerate(chunks, start=1):
        t0 = float(ch[0].get("start", 0))
        t1 = float(ch[-1].get("end", 0))
        sub_id = f"{main_section_num}.{idx}"
        body = "".join((s.get("text") or "").strip() for s in ch)
        lines.append(f"### {sub_id} （时间 {fmt_ts(t0)}–{fmt_ts(t1)}）")
        lines.append("")
        lines.append("> （本节摘要，可选）")
        lines.append("")
        lines.append(body)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
