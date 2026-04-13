"""抓取 B 站官方字幕（WBI player/v2）；失败时可由 yt-dlp + cookies 兜底。"""

from __future__ import annotations

import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests

from bilibili_transcript.wbi import session_with_headers, sign_wbi

logger = logging.getLogger(__name__)

WBI_V2_URL = "https://api.bilibili.com/x/player/wbi/v2"

# 优先：简中 / 繁中 / 英文；其余按接口顺序
_LANG_PRIORITY = (
    "zh-Hans",
    "zh-CN",
    "ai-zh",
    "zh-Hant",
    "zh-TW",
    "en",
    "en-US",
)


def fetch_player_wbi_v2(
    bvid: str,
    cid: int,
    aid: int,
    session: requests.Session,
) -> Dict[str, Any]:
    params = sign_wbi({"bvid": bvid, "cid": cid, "aid": aid}, session)
    r = session.get(WBI_V2_URL, params=params, timeout=30.0)
    r.raise_for_status()
    j = r.json()
    if j.get("code") != 0:
        raise RuntimeError(f"wbi/v2 error: {j}")
    return j.get("data") or {}


def list_official_subtitle_tracks(
    bvid: str,
    cid: int,
    aid: int,
    session: requests.Session,
) -> List[Dict[str, Any]]:
    data = fetch_player_wbi_v2(bvid, cid, aid, session)
    sub = data.get("subtitle") or {}
    tracks = sub.get("subtitles") or []
    if sub.get("need_login_subtitle"):
        logger.info("稿件字幕需登录后可见（need_login_subtitle）。")
    return tracks


def pick_subtitle_track(tracks: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not tracks:
        return None
    by_lan = {t.get("lan"): t for t in tracks if t.get("lan")}
    for lan in _LANG_PRIORITY:
        if lan in by_lan and by_lan[lan].get("subtitle_url"):
            return by_lan[lan]
    for t in tracks:
        if t.get("subtitle_url"):
            return t
    return None


def download_subtitle_json(subtitle_url: str, session: requests.Session) -> Dict[str, Any]:
    r = session.get(subtitle_url, timeout=60.0)
    r.raise_for_status()
    return r.json()


def subtitle_json_to_segments(
    doc: Dict[str, Any],
    source: str = "bilibili_cc",
) -> Tuple[List[Dict[str, Any]], str]:
    """返回 (segments, full_text)。"""
    body = doc.get("body") or []
    segments: List[Dict[str, Any]] = []
    parts: List[str] = []
    for i, line in enumerate(body):
        t0 = float(line.get("from", 0))
        t1 = float(line.get("to", t0))
        text = (line.get("content") or "").strip()
        segments.append(
            {
                "id": i,
                "start": t0,
                "end": t1,
                "text": text,
                "source": source,
            }
        )
        parts.append(text)
    full = "".join(parts)
    return segments, full


def try_fetch_official_segments(
    bvid: str,
    cid: int,
    aid: int,
) -> Optional[Tuple[List[Dict[str, Any]], str, Dict[str, Any]]]:
    """
    若存在可下载的官方字幕，返回 (segments, full_text, meta)。
    meta 含 lan, subtitle_url 等；否则 None。
    """
    session = session_with_headers(bvid)
    tracks = list_official_subtitle_tracks(bvid, cid, aid, session)
    track = pick_subtitle_track(tracks)
    if not track:
        return None
    url = track.get("subtitle_url")
    if not url:
        return None
    logger.info("使用官方字幕 track: %s", track.get("lan"))
    doc = download_subtitle_json(url, session)
    segs, full = subtitle_json_to_segments(doc)
    if not segs:
        logger.warning("官方字幕 JSON 无有效 body，将回退 ASR。")
        return None
    meta = {"lan": track.get("lan"), "subtitle_url": url, "track": track}
    return segs, full, meta


# --- SRT 解析（yt-dlp 落地文件） ---

_TIME_RANGE = re.compile(
    r"^(\d+:\d+:\d+[,.]\d+)\s+-->\s+(\d+:\d+:\d+[,.]\d+)"
)


def _ts_to_sec(ts: str) -> float:
    ts = ts.strip().replace(",", ".")
    parts = ts.split(":")
    if len(parts) == 3:
        h, m, s = int(parts[0]), int(parts[1]), float(parts[2])
        return h * 3600 + m * 60 + s
    if len(parts) == 2:
        m, s = int(parts[0]), float(parts[1])
        return m * 60 + s
    return float(ts)


def parse_srt(text: str) -> List[Dict[str, Any]]:
    segments: List[Dict[str, Any]] = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if len(lines) < 2:
            continue
        # 可选：首行序号
        if re.match(r"^\d+$", lines[0]):
            lines = lines[1:]
        if not lines:
            continue
        m = _TIME_RANGE.match(lines[0])
        if not m:
            continue
        t0 = _ts_to_sec(m.group(1))
        t1 = _ts_to_sec(m.group(2))
        content = "".join(lines[1:]).replace("\n", "")
        segments.append(
            {
                "id": len(segments),
                "start": t0,
                "end": t1,
                "text": content,
                "source": "srt",
            }
        )
    for i, s in enumerate(segments):
        s["id"] = i
    return segments


def try_fetch_subtitles_ytdlp(
    page_url: str,
    cookies_from_browser: Optional[str] = None,
) -> Optional[Tuple[List[Dict[str, Any]], str]]:
    """无官方接口字幕时，用 yt-dlp 写本地字幕文件再解析。"""
    import sys

    tmp = Path(tempfile.mkdtemp(prefix="bili_sub_"))
    out_template = str(tmp / "v.%(ext)s")
    cmd: List[str] = [sys.executable, "-m", "yt_dlp"]
    if cookies_from_browser:
        cmd.extend(["--cookies-from-browser", cookies_from_browser])
    cmd.extend(
        [
            "--write-subs",
            "--write-auto-subs",
            "--sub-langs",
            "zh-Hans,zh-CN,zh-Hant,zh-TW,en,all",
            "--skip-download",
            "-o",
            out_template,
            page_url,
        ]
    )
    logger.info("尝试 yt-dlp 拉取字幕…")
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=180,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        logger.warning("yt-dlp 字幕失败: %s", e)
        return None

    srt_files = sorted(tmp.glob("*.srt"))
    if not srt_files:
        logger.warning("yt-dlp 未产生 srt 字幕文件（可能需要登录或稿件无字幕）。")
        return None

    best = srt_files[0]
    for f in srt_files:
        name = f.name.lower()
        if "zh" in name or "zh-hans" in name or "chi" in name:
            best = f
            break
    raw = best.read_text(encoding="utf-8", errors="replace")
    segs = parse_srt(raw)
    if not segs:
        return None
    full = "".join(s["text"] for s in segs)
    return segs, full
