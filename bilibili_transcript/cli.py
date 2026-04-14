#!/usr/bin/env python3
"""CLI: video URL → (prefer subtitles → fallback ASR) → JSON + optional Markdown."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from bilibili_transcript.draft_md import build_draft_transcript_markdown
from bilibili_transcript.finalize_md import write_eval_markdown_from_json
from bilibili_transcript.providers import detect_provider
from bilibili_transcript.providers.base import SourceRecord, VideoMeta
from bilibili_transcript.transcribe import save_transcript_json, transcribe_mp3

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def resolve_device(device: str) -> str:
    if device != "auto":
        return device
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def resolve_compute_type(compute_type: str, device: str) -> str:
    if compute_type != "default":
        return compute_type
    return "float16" if device == "cuda" else "int8"


def merge_segment_lists(part_segments: List[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    merged: List[Dict[str, Any]] = []
    new_id = 0
    for part_idx, segs in enumerate(part_segments, start=1):
        for s in segs:
            merged.append({
                "id": new_id,
                "start": float(s.get("start", 0)),
                "end": float(s.get("end", 0)),
                "text": (s.get("text") or "").strip(),
                "words": s.get("words"),
                "part": part_idx,
                "text_source": s.get("source") or s.get("text_source"),
            })
            new_id += 1
    return merged


def obtain_part_segments(
    *,
    meta: VideoMeta,
    part_index: int,
    cid: int,
    out_dir: Path,
    args: argparse.Namespace,
    device: str,
    compute_type: str,
    provider,
) -> Tuple[List[Dict[str, Any]], str, SourceRecord]:
    """Return (segments, full_text, source_record)."""
    result = provider.fetch_segments(meta, part_index, cid, args=args)
    if result is not None:
        return result

    # ASR fallback
    mp3 = out_dir / f"{meta.video_id}_p{part_index}.mp3"
    if args.skip_download and mp3.exists():
        logger.info("Using existing %s", mp3)
    else:
        mp3 = provider.download_audio(meta, part_index, cid, out_dir, args=args)

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
    return segs, text, SourceRecord(
        part=part_index,
        mode="asr",
        extra={"whisper_model": args.whisper_model},
    )


def run_pipeline(args: argparse.Namespace) -> int:
    provider = detect_provider(args.input)
    logger.info("Source: %s", provider.name)

    video_id = provider.extract_id(args.input)
    out_dir = Path(args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        meta = provider.fetch_metadata(video_id)
    except Exception as e:
        logger.error("Failed to fetch metadata: %s", e)
        return 5

    if not meta.aid and provider.name == "bilibili":
        logger.error("无法获取 aid，字幕接口需要 aid。请稍后重试或检查网络。")
        return 5

    try:
        pages_sel, page_indices = provider.page_indices(meta, args.part)
    except ValueError as e:
        logger.error("%s", e)
        return 2

    device = resolve_device(args.device)
    compute_type = resolve_compute_type(args.compute_type, device)

    all_seg_lists: List[List[Dict[str, Any]]] = []
    combined_text_parts: List[str] = []
    sources: List[Dict[str, Any]] = []

    for pi, page in zip(page_indices, pages_sel):
        cid = int(page.get("cid", 0))
        segs, text, src = obtain_part_segments(
            meta=meta,
            part_index=pi,
            cid=cid,
            out_dir=out_dir,
            args=args,
            device=device,
            compute_type=compute_type,
            provider=provider,
        )
        all_seg_lists.append(segs)
        combined_text_parts.append(text)
        sources.append(src.to_dict())
        logger.info("Part %s: %s", pi, src.mode)

    merged_segments = merge_segment_lists(all_seg_lists)
    if not merged_segments:
        logger.error("No segments produced (subtitles and ASR both empty). Try --no-vad or check the video.")
        return 4

    full_text = "".join((s.get("text") or "") for s in merged_segments)
    transcript_json: Dict[str, Any] = {
        "source": provider.name,
        "video_id": video_id,
        "bvid": video_id,  # backward compat for bilibili
        "title": meta.title,
        "text": full_text,
        "segments": merged_segments,
        "part_sources": sources,
    }
    json_path = out_dir / f"{video_id}_transcript.json"
    save_transcript_json(transcript_json, json_path)
    logger.info("Wrote %s", json_path)

    if args.json_only:
        logger.info("JSON-only mode, skipping Markdown.")
        return 0

    md = build_draft_transcript_markdown(
        meta.title, merged_segments, max_span_seconds=args.chunk_span,
    )
    md_path = out_dir / f"{video_id}_transcript.md"
    md_path.write_text(md, encoding="utf-8")
    logger.info("Wrote %s (time-chunked draft)", md_path)

    try:
        ev_path = write_eval_markdown_from_json(json_path)
        logger.info("Wrote %s (structured draft for review)", ev_path)
    except Exception as e:
        logger.warning("Skipped eval markdown: %s", e)
    return 0


# ---------------------------------------------------------------------------
# export-html subcommand (formerly tools/export_morandi_html.py)
# ---------------------------------------------------------------------------

def run_export_html(args: argparse.Namespace) -> int:
    from bilibili_transcript.export_html import export_morandi_html

    target = Path(args.input)
    if target.is_dir():
        mds = list(target.glob("*_transcript_成稿.md"))
        if not mds:
            logger.error("No *_transcript_成稿.md found in %s", target)
            return 1
        target = mds[0]
    if not target.is_file():
        logger.error("Not found: %s", target)
        return 1

    out = export_morandi_html(target)
    logger.info("Wrote %s", out)

    if not args.no_open:
        import platform
        import subprocess
        opener = {"Darwin": "open", "Linux": "xdg-open", "Windows": "start"}.get(platform.system(), "open")
        try:
            subprocess.Popen([opener, str(out)])
        except Exception:
            pass
    return 0


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        description="Video transcript pipeline: subtitles-first, ASR-fallback, local-only.",
    )
    sub = root.add_subparsers(dest="command")

    # Default: transcript pipeline (also works without subcommand for backward compat)
    p = sub.add_parser("transcript", help="Fetch transcript from video URL")
    _add_transcript_args(p)

    # export-html subcommand
    h = sub.add_parser("export-html", help="Convert 成稿.md to Morandi HTML")
    h.add_argument("input", help="Path to *_transcript_成稿.md or a directory containing one")
    h.add_argument("--no-open", action="store_true", help="Don't auto-open in browser")

    return root


def _add_transcript_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("input", help="Video URL or ID (e.g. BV号, YouTube URL)")
    p.add_argument("-o", "--out-dir", default=".", help="Output directory (default: current)")
    p.add_argument("--part", type=int, default=None, help="Process only part N (1-based)")
    p.add_argument("--skip-download", action="store_true", help="Reuse existing MP3 (ASR path only)")
    p.add_argument("--ytdlp", action="store_true", help="Force yt-dlp for audio download")
    p.add_argument("--ytdlp-subs", action="store_true", help="Try yt-dlp for subtitles when official API has none")
    p.add_argument(
        "--cookies-from-browser", default=None, metavar="BROWSER",
        help="Read cookies from local browser for authenticated requests (e.g. chrome)",
    )
    p.add_argument(
        "--prefer-subtitles", action=argparse.BooleanOptionalAction, default=True,
        help="Prefer official subtitles over ASR (default: on)",
    )
    p.add_argument("--force-asr", action="store_true", help="Skip subtitle check, force local ASR")
    p.add_argument("--whisper-model", default="medium", help="faster-whisper model (small/medium/large-v3)")
    p.add_argument("--device", default="auto", help="cpu / cuda / auto")
    p.add_argument("--compute-type", default="default", help="default / int8 / float16 / float32")
    p.add_argument("--language", default="zh", help="Whisper language code (default: zh)")
    p.add_argument("--no-vad", action="store_true", help="Disable VAD filter (try for music/BGM)")
    p.add_argument("--json-only", action="store_true", help="Output JSON only, skip Markdown")
    p.add_argument("--chunk-span", type=float, default=300.0, metavar="SEC", help="Draft section span in seconds (default: 300)")


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args, remaining = parser.parse_known_args(argv)

    # Backward compat: `python -m bilibili_transcript "BV..."` without subcommand
    if args.command is None:
        if remaining:
            fallback = argparse.ArgumentParser()
            _add_transcript_args(fallback)
            args = fallback.parse_args(remaining)
            args.command = "transcript"
        else:
            parser.print_help()
            return 0

    try:
        if args.command == "export-html":
            return run_export_html(args)
        return run_pipeline(args)
    except KeyboardInterrupt:
        logger.error("Interrupted")
        return 130
    except Exception as e:
        logger.exception("%s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
