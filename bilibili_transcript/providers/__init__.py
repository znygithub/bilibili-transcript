"""Provider registry.

To add a new source, append an instance to PROVIDERS.
The first provider whose match() returns True wins.
"""

from __future__ import annotations

from typing import List

from bilibili_transcript.providers.base import TranscriptProvider, VideoMeta, SourceRecord
from bilibili_transcript.providers.bilibili import BilibiliProvider

PROVIDERS: List[TranscriptProvider] = [
    BilibiliProvider(),
]


def detect_provider(url_or_id: str) -> TranscriptProvider:
    """Return the first provider that matches, or raise ValueError."""
    for p in PROVIDERS:
        if p.match(url_or_id):
            return p
    supported = ", ".join(p.name for p in PROVIDERS)
    raise ValueError(
        f"No provider matched input: {url_or_id!r}\n"
        f"Supported sources: {supported}"
    )


__all__ = [
    "PROVIDERS",
    "TranscriptProvider",
    "VideoMeta",
    "SourceRecord",
    "detect_provider",
]
