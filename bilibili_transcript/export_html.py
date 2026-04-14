"""Convert *_transcript_成稿.md to single-file Morandi HTML.

Only structural mapping + HTML escaping; does not alter transcript content.
"""

from __future__ import annotations

import html
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "docs/transcript_morandi_html/morandi-template.html"


def _style_block() -> str:
    m = re.search(r"<style>.*?</style>", TEMPLATE.read_text(encoding="utf-8"), re.DOTALL)
    return m.group(0) if m else "<style></style>"


def _inline_md(s: str) -> str:
    """Convert **bold** to <strong>; escape HTML entities."""
    if not s:
        return ""
    parts = re.split(r"(\*\*[^*]+\*\*)", s)
    out: list[str] = []
    for p in parts:
        if p.startswith("**") and p.endswith("**") and len(p) > 4:
            out.append(f"<strong>{html.escape(p[2:-2])}</strong>")
        else:
            out.append(html.escape(p))
    return "".join(out)


def _parse_md(path: Path) -> Tuple[str, List[str], str, List[Dict]]:
    """Parse 成稿 Markdown into (title, summary_paras, note, sections)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    title = lines[0][2:].strip() if lines and lines[0].startswith("# ") else ""

    i = 0
    while i < len(lines) and not lines[i].startswith("## 全文总结"):
        i += 1
    i += 1

    summary_paras: list[str] = []
    note = ""
    while i < len(lines):
        line = lines[i]
        if line.startswith("## 1."):
            break
        if line.startswith("*说明：") and line.endswith("*"):
            note = line.strip("*").replace("说明：", "").strip()
            i += 1
            continue
        if not line.strip():
            i += 1
            continue
        summary_paras.append(line)
        i += 1

    rest = "\n".join(lines[i:])
    sections: list[dict] = []
    for ch in re.split(r"\n(?=### )", rest):
        ch = ch.strip()
        if not ch.startswith("###"):
            continue
        cl = ch.split("\n")
        mh = re.match(r"###\s+(\d+\.\d+)\s+(.*)", cl[0])
        sec_title = mh.group(2).strip() if mh else cl[0]

        j = 1
        time_range = ""
        intro_lines: list[str] = []
        body_lines: list[str] = []
        in_q = False
        while j < len(cl):
            line = cl[j]
            if line.startswith("> "):
                in_q = True
                c = line[2:]
                tm = re.search(r"（时间参考：(\d{2}:\d{2}[–-]\d{2}:\d{2})）", c)
                if tm:
                    time_range = tm.group(1).replace("-", "–")
                    r = c.replace(tm.group(0), "").strip()
                    if r:
                        intro_lines.append(r)
                else:
                    intro_lines.append(c)
                j += 1
                continue
            if in_q and not line.strip():
                j += 1
                continue
            if not line.startswith(">") and in_q:
                in_q = False
            if not in_q:
                body_lines.append(line)
            j += 1

        paras = [p.strip() for p in re.split(r"\n\s*\n", "\n".join(body_lines).strip()) if p.strip()]
        sections.append({
            "title": sec_title,
            "time": time_range,
            "intro": " ".join(intro_lines),
            "paras": paras,
        })
    return title, summary_paras, note, sections


def _build_html(
    title: str,
    subtitle: str,
    summary_paras: list[str],
    note: str,
    sections: list[dict],
    footer_txt: str,
) -> str:
    style = _style_block()
    sum_ps = "".join(f"<p>{_inline_md(p)}</p>" for p in summary_paras)
    note_html = f'<div class="note">{_inline_md("说明：" + note)}</div>' if note else ""

    blocks: list[str] = []
    for idx, s in enumerate(sections, 1):
        intro = _inline_md(s["intro"]) if s["intro"] else ""
        tt = f'<span class="time-tag">⏱ {html.escape(s["time"])}</span>' if s["time"] else ""
        ph = "".join(f"<p>{_inline_md(p)}</p>" for p in s["paras"])
        blocks.append(
            f"""  <div class="section">
    <div class="section-header">
      <div class="section-number">{idx}</div>
      <h3>{html.escape(s["title"])}</h3>
    </div>
    {tt}
    <div class="section-intro">{intro}</div>
    <div class="content-card">
{ph}
    </div>
  </div>"""
        )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
{style}
</head>
<body>
<div class="container">
  <header>
    <h1>{html.escape(title)}</h1>
    <div class="subtitle">{html.escape(subtitle)}</div>
  </header>
  <div class="summary-card">
    <h2>全文总结</h2>
{sum_ps}
{note_html}
  </div>
{chr(10).join(blocks)}
  <footer>
    <p>{html.escape(footer_txt)}</p>
  </footer>
</div>
</body>
</html>
"""


def _guess_subtitle(md_path: Path) -> str:
    parent = md_path.parent.name
    if "_p1" in parent:
        return "上集（分 P1）"
    elif "_p2" in parent:
        return "下集（分 P2）"
    return ""


def export_morandi_html(md_path: Path, out_path: Optional[Path] = None) -> Path:
    """Top-level entry: MD → HTML, returns output path."""
    title, summary_paras, note, sections = _parse_md(md_path)

    parent = md_path.parent.name
    part_hint = _guess_subtitle(md_path)
    video_id = parent.split("_p")[0] if parent.startswith("BV") and "_p" in parent else (parent[:12] if parent.startswith("BV") else "")
    subtitle_parts = [p for p in [video_id, part_hint, "视频转写"] if p]
    subtitle = " · ".join(subtitle_parts)

    out = out_path or md_path.with_suffix(".html")
    out.write_text(
        _build_html(title, subtitle, summary_paras, note, sections, "由 bilibili_transcript 导出 · 仅供个人学习"),
        encoding="utf-8",
    )
    return out
