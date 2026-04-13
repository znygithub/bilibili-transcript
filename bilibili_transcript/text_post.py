"""逐字稿后处理：标点、分段（不依赖大模型）。"""

from __future__ import annotations

import re
from typing import List


def sanitize_filename_title(title: str, max_len: int = 48) -> str:
    """用于成稿文件名：视频标题精简 + 合法字符。"""
    s = title.strip()
    # 弯引号、书名号等易在文件名中造成怪异或非法表现，统一去掉
    for ch in "\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f":
        s = s.replace(ch, "")
    s = re.sub(r'[\\/:*?"<>|#\s]+', "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s or "untitled"


def format_english_body(text: str) -> str:
    """英文口语：句间空格 + 按长度与衔接词拆段。"""
    if not text.strip():
        return text
    t = text.replace("\n", " ")
    t = re.sub(r" +", " ", t)
    t = re.sub(r"([.!?])([A-Za-z\"'])", r"\1 \2", t)
    t = re.sub(r"([.!?])([A-Za-z\"'])", r"\1 \2", t)
    # 在明显话轮处换段（保守列表）
    for kw in (
        "OK, ",
        "OK.",
        "So ",
        "And ",
        "But ",
        "Well, ",
        "I mean",
        "Right?",
        "Come on",
        "Okay",
        "Now ",
        "Anyway",
        "However",
    ):
        t = t.replace(kw, "\n\n" + kw)
    t = re.sub(r"\n{3,}", "\n\n", t)
    parts = [p.strip() for p in t.split("\n\n") if p.strip()]
    out: List[str] = []
    for p in parts:
        if len(p) > 600:
            for i in range(0, len(p), 500):
                chunk = p[i : i + 500].strip()
                if chunk:
                    if chunk[-1] not in ".!?":
                        chunk += "."
                    out.append(chunk)
        else:
            if p[-1] not in ".!?":
                p += "."
            out.append(p)
    return "\n\n".join(out)


def format_chinese_body(text: str, line_max: int = 38, para_chars: int = 220) -> str:
    """
    中文连写：按字数折行、按块分段，并在块末补「。」（启发式）。
    """
    if not text.strip():
        return text
    t = re.sub(r"\s+", "", text.replace("\n", ""))
    paragraphs: List[str] = []
    for i in range(0, len(t), para_chars):
        block = t[i : i + para_chars]
        lines = [block[j : j + line_max] for j in range(0, len(block), line_max)]
        para = "\n".join(lines)
        if para and para[-1] not in "。！？…;,.!?":
            para += "。"
        paragraphs.append(para)
    return "\n\n".join(paragraphs)


def format_body(text: str, *, lang_hint: str = "auto") -> str:
    """lang_hint: zh / en / auto（按拉丁字母比例猜）。"""
    if not text.strip():
        return text
    if lang_hint == "auto":
        latin = sum(1 for c in text if c.isascii() and c.isalpha())
        lang_hint = "en" if latin / max(len(text), 1) > 0.22 else "zh"
    if lang_hint == "en":
        return format_english_body(text)
    return format_chinese_body(text)
