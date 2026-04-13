"""Bilibili WBI 签名（与站方算法一致，参考 yt-dlp bilibili extractor）。"""

from __future__ import annotations

import hashlib
import time
import urllib.parse
from typing import Any, Dict, Optional

import requests

from bilibili_transcript.download import DEFAULT_UA

_WBI_KEY: Optional[str] = None
_WBI_TS: float = 0.0
_WBI_TTL = 300.0

_MIXIN_TAB = [
    46, 47, 18, 2, 53, 8, 23, 32, 15, 50, 10, 31, 58, 3, 45, 35, 27, 43, 5, 49,
    33, 9, 42, 19, 29, 28, 14, 39, 12, 38, 41, 13, 37, 48, 7, 16, 24, 55, 40,
    61, 26, 17, 0, 1, 60, 51, 30, 4, 22, 25, 54, 21, 56, 59, 6, 63, 57, 62, 11,
    36, 20, 34, 44, 52,
]


def _fetch_mixin_key(session: requests.Session) -> str:
    r = session.get(
        "https://api.bilibili.com/x/web-interface/nav",
        timeout=30.0,
    )
    r.raise_for_status()
    j = r.json()
    data = j.get("data") or {}
    wbi = data.get("wbi_img") or {}
    img = (wbi.get("img_url") or "").rsplit("/", 1)[-1].partition(".")[0]
    sub = (wbi.get("sub_url") or "").rsplit("/", 1)[-1].partition(".")[0]
    lookup = f"{img}{sub}"
    if len(lookup) < 64:
        raise RuntimeError("Unexpected wbi_img format from /nav")
    return "".join(lookup[i] for i in _MIXIN_TAB)[:32]


def get_wbi_key(session: requests.Session) -> str:
    global _WBI_KEY, _WBI_TS
    now = time.time()
    if _WBI_KEY and now - _WBI_TS < _WBI_TTL:
        return _WBI_KEY
    _WBI_KEY = _fetch_mixin_key(session)
    _WBI_TS = now
    return _WBI_KEY


def sign_wbi(params: Dict[str, Any], session: requests.Session) -> Dict[str, Any]:
    p = dict(params)
    p["wts"] = int(time.time())
    p = {
        k: "".join(c for c in str(v) if c not in "!'()*")
        for k, v in sorted(p.items())
    }
    query = urllib.parse.urlencode(p)
    w_rid = hashlib.md5((query + get_wbi_key(session)).encode()).hexdigest()
    p["w_rid"] = w_rid
    return p


def session_with_headers(bvid: str) -> requests.Session:
    s = requests.Session()
    s.headers.update(
        {
            "User-Agent": DEFAULT_UA,
            "Referer": f"https://www.bilibili.com/video/{bvid}",
        }
    )
    return s
