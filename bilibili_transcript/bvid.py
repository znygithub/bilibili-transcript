import re
from typing import Optional

BV_RE = re.compile(r"(BV[0-9A-Za-z]{10})")


def extract_bvid(url_or_bvid: str) -> str:
    """Extract BV id from a full URL or raw bvid string."""
    s = url_or_bvid.strip()
    m = BV_RE.search(s)
    if not m:
        raise ValueError(f"Could not find BV id in: {url_or_bvid!r}")
    return m.group(1)


def video_page_url(bvid: str) -> str:
    return f"https://www.bilibili.com/video/{bvid}"


def video_page_url_part(bvid: str, part: int) -> str:
    """part 为 1-based 分 P。"""
    if part <= 1:
        return video_page_url(bvid)
    return f"{video_page_url(bvid)}?p={part}"
