"""Bilibili video metadata (title, etc.)."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from bilibili_transcript.bvid import video_page_url
from bilibili_transcript.download import DEFAULT_UA

logger = logging.getLogger(__name__)

VIEW_URL = "https://api.bilibili.com/x/web-interface/view"


def fetch_video_meta(bvid: str, timeout: float = 30.0) -> Dict[str, Any]:
    r = requests.get(
        VIEW_URL,
        params={"bvid": bvid},
        headers={
            "User-Agent": DEFAULT_UA,
            "Referer": video_page_url(bvid),
        },
        timeout=timeout,
    )
    r.raise_for_status()
    j = r.json()
    if j.get("code") != 0:
        raise RuntimeError(f"view API failed: {j}")
    return j.get("data") or {}


def video_title(bvid: str) -> Optional[str]:
    try:
        data = fetch_video_meta(bvid)
        return data.get("title")
    except Exception as e:
        logger.warning("Could not fetch video title: %s", e)
        return None
