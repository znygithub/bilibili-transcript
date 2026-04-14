"""Filename sanitization for transcript output files."""

from __future__ import annotations

import re


def sanitize_filename_title(title: str, max_len: int = 48) -> str:
    """Sanitize video title for use in filenames."""
    s = title.strip()
    for ch in "\u201c\u201d\u2018\u2019\u300c\u300d\u300e\u300f":
        s = s.replace(ch, "")
    s = re.sub(r'[\\/:*?"<>|#\s]+', "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    if len(s) > max_len:
        s = s[:max_len].rstrip("_")
    return s or "untitled"
