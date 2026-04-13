#!/usr/bin/env python3
"""CLI: Bilibili →（优先官方字幕）→ 否则 ASR → JSON + 可选草稿 Markdown + 成稿。"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bilibili_transcript.bvid import extract_bvid, video_page_url_part
from bilibili_transcript.draft_md import build_draft_transcript_markdown
from bilibili_transcript.download import download_part_mp3, fetch_pagelist
from bilibili_transcript.meta import fetch_video_meta
from bilibili_transcript.subtitles import (
    try_fetch_official_segments,
    try_fetch_subtitles_ytdlp,
)
from bilibili_transcript.transcribe import save_transcript_json, transcribe_mp3
from bilibili_transcript.finalize_md import write_eval_markdown_from_json

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)


def resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def merge_segment_lists(part_segments: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    new_id = 0
    for part_idx, segs in enumerate(part_segments, start=1):
        for s in segs:
            merged.append(
                {
                    "id": new_id,
                    "start": float(s.get("start", 0)),
                    "end": float(s.get("end", 0)),
                    "text": (s.get("text") or "").strip(),
                    "words": s.get("words"),
                    "part": part_idx,
                    "text_source": s.get("source") or s.get("text_source"),
                }
            )
            new_id += 1
    return merged


def obtain_part_segments(
    *,
    bvid: str,
    part_index: int,
    cid: int,
    aid: int,
    out_dir: Path,
    args: argparse.Namespace,
    device: str,
    compute_type: str,
) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
    """
    返回 (segments_for_part, text_for_part, source_record)。
    source_record 至少含 mode: official_cc | ytdlp | asr
    """
    page_url = video_page_url_part(bvid, part_index)

    if not args.force_asr and args.prefer_subtitles:
        off = try_fetch_official_segments(bvid, cid, aid)
        if off:
            segs, full, meta = off
            return segs, full, {
                "part": part_index,
                "mode": "official_cc",
                "lan": meta.get("lan"),
                "subtitle_url": meta.get("subtitle_url"),
            }

        if args.cookies_from_browser or args.ytdlp_subs:
            yd = try_fetch_subtitles_ytdlp(
                page_url,
                cookies_from_browser=args.cookies_from_browser,
            )
            if yd:
                segs, full = yd
                return segs, full, {"part": part_index, "mode": "ytdlp_subtitle_file"}

    mp3 = out_dir / f"{bvid}_p{part_index}.mp3"
    if args.skip_download and mp3.exists():
        logger.info("Using existing %s", mp3)
    else:
        mp3 = download_part_mp3(
            bvid,
            page=part_index,
            cid=cid,
            out_dir=out_dir,
            prefer_ytdlp=args.ytdlp,
            cookies_from_browser=args.cookies_from_browser,
        )

    tr = transcribe_mp3(
        mp3,
        model_size=args.whisper_model,
        device=device,
        compute_type=compute_type,
        language=args.language,
        vad_filter=not args.no_vad,
    )
    segs = tr.get("segments") or []
    text = tr.get("text") or ""
    return segs, text, {
        "part": part_index,
        "mode": "asr",
        "whisper_model": args.whisper_model,
    }


def run_pipeline(args: argparse.Namespace) -> int:
    bvid = extract_bvid(args.input)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = fetch_pagelist(bvid)
    if args.part is not None:
        p = args.part
        if p < 1 or p > len(pages):
            logger.error("part %s out of range 1..%s", p, len(pages))
            return 2
        pages_sel = [pages[p - 1]]
        page_indices = [p]
    else:
        pages_sel = pages
        page_indices = list(range(1, len(pages) + 1))

    try:
        meta = fetch_video_meta(bvid)
        vtitle = meta.get("title") or bvid
        aid = int(meta.get("aid") or 0)
    except Exception:
        vtitle = bvid
        aid = 0

    if not aid:
        logger.error("无法从 view 接口获取 aid，字幕接口需要 aid。请稍后重试或检查网络。")
        return 5

    device = resolve_device(args.device)
    compute_type = args.compute_type
    if compute_type == "default":
        compute_type = "float16" if device == "cuda" else "int8"

    all_seg_lists: List[List[Dict[str, Any]]] = []
    combined_text_parts: List[str] = []
    sources: List[Dict[str, Any]] = []

    for pi, page in zip(page_indices, pages_sel):
        cid = int(page["cid"])
        segs, text, src = obtain_part_segments(
            bvid=bvid,
            part_index=pi,
            cid=cid,
            aid=aid,
            out_dir=out_dir,
            args=args,
            device=device,
            compute_type=compute_type,
        )
        all_seg_lists.append(segs)
        combined_text_parts.append(text)
        sources.append(src)
        logger.info("分P %s：%s", pi, src.get("mode"))

    merged_segments = merge_segment_lists(all_seg_lists)
    if not merged_segments:
        logger.error("未得到任何文本分段（字幕与 ASR 均为空）。可尝试 --no-vad 或检查稿件。")
        return 4

    full_text = "".join((s.get("text") or "") for s in merged_segments)
    transcript_json: Dict[str, Any] = {
        "bvid": bvid,
        "title": vtitle,
        "text": full_text,
        "segments": merged_segments,
        "part_sources": sources,
        "transcript_strategy": (
            "优先使用 B 站官方 CC（WBI /player/wbi/v2 + subtitle_url）；"
            "若无则可在提供浏览器 Cookie 时用 yt-dlp 拉取字幕文件；"
            "仍无则本机 faster-whisper ASR。详见 TRANSCRIPT_STRATEGY.md。"
        ),
    }
    json_path = out_dir / f"{bvid}_transcript.json"
    save_transcript_json(transcript_json, json_path)
    logger.info("Wrote %s", json_path)

    if args.json_only:
        logger.info("仅输出 JSON（--json-only）。")
        return 0

    md = build_draft_transcript_markdown(
        vtitle,
        merged_segments,
        max_span_seconds=args.chunk_span,
    )
    md_path = out_dir / f"{bvid}_transcript.md"
    md_path.write_text(md, encoding="utf-8")
    logger.info("Wrote %s（按时间分块的草稿，总结与标题需自行编辑）", md_path)

    try:
        ev_path = write_eval_markdown_from_json(json_path)
        logger.info("Wrote %s（成稿：含全文总结与话题摘要，供直接检阅）", ev_path)
    except Exception as e:
        logger.warning("未生成 transcript_成稿.md：%s", e)
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Bilibili → 优先官方字幕 / 否则 ASR → transcript.json + 草稿 md + 成稿 md（不调用外部 API）",
    )
    p.add_argument("input", help="B 站视频 URL 或 BV 号")
    p.add_argument(
        "-o",
        "--out-dir",
        default=".",
        help="输出目录（默认当前目录）",
    )
    p.add_argument(
        "--part",
        type=int,
        default=None,
        help="仅处理第几 P（1-based）；默认处理全部分 P",
    )
    p.add_argument("--skip-download", action="store_true", help="若已存在 MP3 则跳过下载（仅 ASR 分支）")
    p.add_argument("--ytdlp", action="store_true", help="下载音轨时强制使用 yt-dlp（跳过 API 直链）")
    p.add_argument(
        "--ytdlp-subs",
        action="store_true",
        help="官方接口无字幕时，仍尝试用 yt-dlp 拉字幕（无需浏览器时通常仅弹幕/XML）",
    )
    p.add_argument(
        "--cookies-from-browser",
        default=None,
        metavar="BROWSER",
        help="传给 yt-dlp：下载音轨或**拉取需登录的字幕**时使用，例如 chrome",
    )
    p.add_argument(
        "--prefer-subtitles",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="优先使用可抓取的官方字幕（默认开启）；关闭等价于仅 ASR",
    )
    p.add_argument(
        "--force-asr",
        action="store_true",
        help="忽略字幕，强制走本机 ASR（仍下载音轨）",
    )
    p.add_argument("--whisper-model", default="medium", help="faster-whisper 模型，如 small/medium/large-v3")
    p.add_argument("--device", default="auto", help="cpu / cuda / auto")
    p.add_argument("--compute-type", default="default", help="default 或 int8/float16 float32 等")
    p.add_argument("--language", default="zh", help="Whisper language code，默认 zh")
    p.add_argument(
        "--no-vad",
        action="store_true",
        help="关闭 faster-whisper 的 VAD 过滤（音乐/纯 BGM 稿件可试）",
    )
    p.add_argument(
        "--json-only",
        action="store_true",
        help="仅输出 *_transcript.json，不生成 Markdown 草稿",
    )
    p.add_argument(
        "--skip-llm",
        action="store_true",
        help="已弃用：等同于 --json-only",
    )
    p.add_argument(
        "--chunk-span",
        type=float,
        default=300.0,
        metavar="SEC",
        help="草稿中按时间粗分的小节最大跨度（秒），默认 300",
    )
    return p


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.skip_llm:
        args.json_only = True
        logger.warning("--skip-llm 已弃用，请改用 --json-only")
    try:
        return run_pipeline(args)
    except KeyboardInterrupt:
        logger.error("Interrupted")
        return 130
    except Exception as e:
        logger.exception("%s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
