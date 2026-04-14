"""Abstract base for transcript source providers.

To add a new source (YouTube, 小宇宙, etc.):
1. Create a new module in this package (e.g. youtube.py)
2. Subclass TranscriptProvider
3. Register it in __init__.py via PROVIDERS list

The pipeline (JSON → Markdown → HTML) is source-agnostic;
only fetching metadata / subtitles / audio is provider-specific.
"""

from __future__ import annotations

import argparse
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class VideoMeta:
    video_id: str
    title: str
    aid: int = 0
    pages: List[Dict[str, Any]] = field(default_factory=list)
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceRecord:
    """Provenance info for one part's transcript."""
    part: int
    mode: str  # e.g. "official_cc", "ytdlp_subtitle_file", "asr"
    extra: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"part": self.part, "mode": self.mode}
        d.update(self.extra)
        return d


# segments: list of {id, start, end, text, ...}
Segments = List[Dict[str, Any]]


class TranscriptProvider(ABC):
    """Interface that each source (Bilibili, YouTube, ...) must implement."""

    name: str = "base"

    @abstractmethod
    def match(self, url_or_id: str) -> bool:
        """Return True if this provider can handle the input."""

    @abstractmethod
    def extract_id(self, url_or_id: str) -> str:
        """Extract the canonical video ID from a URL or raw ID string."""

    @abstractmethod
    def fetch_metadata(self, video_id: str, **kwargs: Any) -> VideoMeta:
        """Fetch video title, page list, and any extra metadata."""

    @abstractmethod
    def fetch_segments(
        self,
        meta: VideoMeta,
        part_index: int,
        cid: int,
        *,
        args: argparse.Namespace,
    ) -> Optional[Tuple[Segments, str, SourceRecord]]:
        """Try to get transcript segments without ASR (subtitles, CC, etc.).

        Returns (segments, full_text, source_record) or None if unavailable.
        """

    @abstractmethod
    def download_audio(
        self,
        meta: VideoMeta,
        part_index: int,
        cid: int,
        out_dir: Path,
        *,
        args: argparse.Namespace,
    ) -> Path:
        """Download audio file (e.g. MP3) for ASR fallback.

        Returns path to the downloaded audio file.
        """

    def page_indices(
        self, meta: VideoMeta, part: Optional[int]
    ) -> Tuple[List[Dict[str, Any]], List[int]]:
        """Select which pages/parts to process. Override for non-Bilibili sources."""
        pages = meta.pages
        if part is not None:
            if part < 1 or part > len(pages):
                raise ValueError(f"part {part} out of range 1..{len(pages)}")
            return [pages[part - 1]], [part]
        return pages, list(range(1, len(pages) + 1))
