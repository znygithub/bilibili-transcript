"""Download Bilibili audio via pagelist + playurl, transcode to MP3; yt-dlp fallback."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from bilibili_transcript.bvid import video_page_url

logger = logging.getLogger(__name__)

DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

PAGELIST_URL = "https://api.bilibili.com/x/player/pagelist"
PLAYURL_URL = "https://api.bilibili.com/x/player/playurl"


def _session_headers(bvid: str) -> Dict[str, str]:
    return {
        "User-Agent": DEFAULT_UA,
        "Referer": video_page_url(bvid),
        "Origin": "https://www.bilibili.com",
    }


def fetch_pagelist(bvid: str, timeout: float = 30.0) -> List[Dict[str, Any]]:
    r = requests.get(
        PAGELIST_URL,
        params={"bvid": bvid},
        headers=_session_headers(bvid),
        timeout=timeout,
    )
    r.raise_for_status()
    data = r.json()
    if data.get("code") != 0:
        raise RuntimeError(f"pagelist error: {data}")
    pages = data.get("data") or []
    if not pages:
        raise RuntimeError("pagelist returned no pages")
    return pages


def _pick_audio_url(playurl_json: Dict[str, Any]) -> Optional[str]:
    d = playurl_json.get("data") or {}
    dash = d.get("dash")
    if not dash:
        return None
    audios = dash.get("audio") or []
    if not audios:
        return None
    # Prefer highest bandwidth
    audios = sorted(audios, key=lambda x: int(x.get("bandwidth") or 0), reverse=True)
    base = audios[0].get("baseUrl") or audios[0].get("base_url")
    if base:
        return base
    backups = audios[0].get("backupUrl") or audios[0].get("backup_url") or []
    if backups:
        return backups[0]
    return None


def fetch_playurl(
    bvid: str,
    cid: int,
    timeout: float = 30.0,
) -> Tuple[Dict[str, Any], Optional[str]]:
    """Return (raw_json, audio_url_or_none). Tries fnval values for DASH."""
    fnvals = (4048, 16, 80)
    last: Optional[Dict[str, Any]] = None
    for fnval in fnvals:
        r = requests.get(
            PLAYURL_URL,
            params={
                "bvid": bvid,
                "cid": cid,
                "qn": 80,
                "fnval": fnval,
                "fourk": 1,
            },
            headers=_session_headers(bvid),
            timeout=timeout,
        )
        r.raise_for_status()
        j = r.json()
        last = j
        if j.get("code") != 0:
            logger.warning("playurl code=%s message=%s fnval=%s", j.get("code"), j.get("message"), fnval)
            continue
        url = _pick_audio_url(j)
        if url:
            return j, url
    return last or {}, None


def download_url_to_file(url: str, dest: Path, bvid: str, timeout: float = 600.0) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(
        url,
        headers=_session_headers(bvid),
        stream=True,
        timeout=timeout,
    ) as resp:
        resp.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in resp.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)


def transcode_to_mp3(src: Path, dst: Path, bitrate: str = "192k") -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(src),
        "-acodec",
        "libmp3lame",
        "-b:a",
        bitrate,
        str(dst),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def download_audio_via_api(
    bvid: str,
    cid: int,
    work_dir: Path,
    basename: str,
    bitrate: str = "192k",
) -> Path:
    _, audio_url = fetch_playurl(bvid, cid)
    if not audio_url:
        raise RuntimeError("playurl did not return DASH audio URL")

    suffix = _guess_suffix(audio_url)
    raw_path = work_dir / f"{basename}_raw{suffix}"
    mp3_path = work_dir / f"{basename}.mp3"

    logger.info("Downloading audio from DASH…")
    download_url_to_file(audio_url, raw_path, bvid)
    logger.info("Transcoding to MP3…")
    transcode_to_mp3(raw_path, mp3_path, bitrate=bitrate)
    try:
        raw_path.unlink(missing_ok=True)
    except OSError:
        pass
    return mp3_path


def _guess_suffix(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in (".m4a", ".mp4", ".aac", ".opus", ".mp3"):
        if path.endswith(ext):
            return ext
    return ".bin"


def download_audio_via_ytdlp(
    bvid: str,
    page: int,
    out_mp3: Path,
    cookies_from_browser: Optional[str] = None,
) -> None:
    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    url = f"{video_page_url(bvid)}?p={page}"
    cmd = [
        "yt-dlp",
        "-x",
        "--audio-format",
        "mp3",
        "--audio-quality",
        "0",
        "-o",
        str(out_mp3.with_suffix(".%(ext)s")),
        url,
    ]
    if cookies_from_browser:
        cmd[1:1] = ["--cookies-from-browser", cookies_from_browser]
    logger.info("Running yt-dlp fallback…")
    subprocess.run(cmd, check=True)


def resolve_mp3_after_ytdlp(out_mp3: Path) -> Path:
    """yt-dlp may name file .mp3 directly; if template was used, pick newest mp3 in dir."""
    if out_mp3.exists():
        return out_mp3
    parent = out_mp3.parent
    pattern = out_mp3.stem + "*"
    candidates = sorted(parent.glob(pattern + ".mp3"), key=lambda p: p.stat().st_mtime, reverse=True)
    if candidates:
        return candidates[0]
    # any mp3 in parent matching stem
    for p in sorted(parent.glob("*.mp3"), key=lambda p: p.stat().st_mtime, reverse=True):
        return p
    raise FileNotFoundError(f"No mp3 produced next to {out_mp3}")


def download_part_mp3(
    bvid: str,
    page: int,
    cid: int,
    out_dir: Path,
    prefer_ytdlp: bool = False,
    cookies_from_browser: Optional[str] = None,
) -> Path:
    """
    page: 1-based index.
    Writes ``{bvid}_p{page}.mp3`` into out_dir.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{bvid}_p{page}"
    out_mp3 = out_dir / f"{base}.mp3"

    if prefer_ytdlp:
        download_audio_via_ytdlp(bvid, page, out_mp3, cookies_from_browser=cookies_from_browser)
        return resolve_mp3_after_ytdlp(out_mp3)

    try:
        return download_audio_via_api(bvid, cid, out_dir, basename=base)
    except Exception as e:
        logger.warning("API download failed (%s), trying yt-dlp…", e)
        download_audio_via_ytdlp(bvid, page, out_mp3, cookies_from_browser=cookies_from_browser)
        return resolve_mp3_after_ytdlp(out_mp3)
