"""文件名与正文占位：终稿级标点、分段、去口癖等必须由 Cursor 子 Agent 完成，本模块不对口播正文做启发式改写。"""

from __future__ import annotations

import re


def sanitize_filename_title(title: str, max_len: int = 48) -> str:
    """用于成稿文件名：视频标题精简 + 合法字符。"""
    s = title.strip()
    for ch in "\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f":
        s = s.replace(ch, "")
    s = re.sub(r'[\\/:*?"<>|#\s]+', "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s or "untitled"


def format_body(text: str, *, lang_hint: str = "auto") -> str:
    """
    原样返回正文，不做标点、分段、去口癖或语言相关的启发式处理。

    项目约定：`*_transcript_成稿.md` 的可读终稿由 **Cursor 子 Agent**
   （见 `.cursor/skills/bilibili-transcript-finalize/SKILL.md`）基于 JSON 人工编排完成；
    Python 流水线不得用语义级规则替代子 Agent。

    `lang_hint` 保留仅为兼容旧调用，已忽略。
    """
    del lang_hint
    return text
