"""Shared utilities used across multiple modules."""

from __future__ import annotations


def fmt_ts(seconds: float) -> str:
    """Format seconds as MM:SS."""
    s = max(0.0, float(seconds))
    m = int(s // 60)
    sec = int(s % 60)
    return f"{m:02d}:{sec:02d}"
