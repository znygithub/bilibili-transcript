#!/usr/bin/env python3
"""
将 *_transcript_成稿.md 转为莫兰迪单页 HTML（仅结构与转义，不改写正文语义）。

用法:
  python tools/export_morandi_html.py path/to/*_transcript_成稿.md
  python tools/export_morandi_html.py path/to/dir   # 目录内首个 *_transcript_成稿.md

终稿润色须由 Cursor Agent 在 .md 中完成；本脚本不参与标点、去口癖等处理。
"""
from __future__ import annotations

import html
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
TEMPLATE = REPO / "docs/transcript_morandi_html/morandi-template.html"


def _style_block() -> str:
    m = re.search(r"<style>.*?</style>", TEMPLATE.read_text(encoding="utf-8"), re.DOTALL)
    return m.group(0) if m else "<style></style>"


def inline_md(s: str) -> str:
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


def parse_md(path: Path):
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
        sections.append(
            {
                "title": sec_title,
                "time": time_range,
                "intro": " ".join(intro_lines),
                "paras": paras,
            }
        )
    return title, summary_paras, note, sections


def build_html(
    title: str,
    subtitle: str,
    summary_paras: list[str],
    note: str,
    sections: list[dict],
    footer_txt: str,
) -> str:
    style = _style_block()
    sum_ps = "".join(f"<p>{inline_md(p)}</p>" for p in summary_paras)
    note_html = f'<div class="note">{inline_md("说明：" + note)}</div>' if note else ""
    blocks: list[str] = []
    for idx, s in enumerate(sections, 1):
        intro = inline_md(s["intro"]) if s["intro"] else ""
        tt = f'<span class="time-tag">⏱ {html.escape(s["time"])}</span>' if s["time"] else ""
        ph = "".join(f"<p>{inline_md(p)}</p>" for p in s["paras"])
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


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: export_morandi_html.py <成稿.md|目录>", file=sys.stderr)
        sys.exit(1)
    arg = Path(sys.argv[1])
    if arg.is_dir():
        mds = list(arg.glob("*_transcript_成稿.md"))
        if not mds:
            print("No *_transcript_成稿.md in directory", file=sys.stderr)
            sys.exit(1)
        md_path = mds[0]
    else:
        md_path = arg
    if not md_path.is_file():
        print(f"Not found: {md_path}", file=sys.stderr)
        sys.exit(1)

    title, summary_paras, note, sections = parse_md(md_path)
    parent = md_path.parent.name
    if "_p1" in parent:
        sub = "上集（分 P1）· B 站转写"
    elif "_p2" in parent:
        sub = "下集（分 P2）· B 站转写"
    else:
        sub = "B 站转写"
    bvid = parent.split("_p")[0] if parent.startswith("BV") and "_p" in parent else (parent[:12] if parent.startswith("BV") else "BV")
    subtitle = f"{bvid} · {sub}"

    out = md_path.with_suffix(".html")
    out.write_text(
        build_html(
            title,
            subtitle,
            summary_paras,
            note,
            sections,
            "由 bilibili_transcript 成稿导出 · 仅供个人学习",
        ),
        encoding="utf-8",
    )
    print(out)


if __name__ == "__main__":
    main()
