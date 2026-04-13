"""按时间跨度生成 transcript 草稿 Markdown（不含任何「自动总结/翻译」逻辑）。"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence


def _fmt_ts(seconds: float) -> str:
    s = max(0.0, float(seconds))
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m:02d}:{sec:02d}"


def chunk_segments_by_span(
    segments: Sequence[Dict[str, Any]],
    max_span_seconds: float = 300.0,
) -> List[List[Dict[str, Any]]]:
    """按时间跨度把分段合并为若干大块。"""
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
    """生成按时间分块的草稿：正文为 segments 拼接，总结与话题标题留空待填。"""
    chunks = chunk_segments_by_span(segments, max_span_seconds=max_span_seconds)
    lines: List[str] = []
    lines.append(f"# {video_title}")
    lines.append("")
    lines.append("## 全文总结")
    lines.append("")
    lines.append("（在此撰写或粘贴整期总结。）")
    lines.append("")
    lines.append(f"## {main_section_num}. 完整逐字稿")
    lines.append("")

    for idx, ch in enumerate(chunks, start=1):
        t0 = float(ch[0].get("start", 0))
        t1 = float(ch[-1].get("end", 0))
        sub_id = f"{main_section_num}.{idx}"
        body = "".join((s.get("text") or "").strip() for s in ch)
        lines.append(f"### {sub_id} （时间 {_fmt_ts(t0)}–{_fmt_ts(t1)}）")
        lines.append("")
        lines.append("> （本节摘要，可选）")
        lines.append("")
        lines.append(body)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
