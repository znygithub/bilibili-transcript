"""ASR with faster-whisper; emit segments JSON for downstream structuring."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def transcribe_mp3(
    mp3_path: Path,
    model_size: str = "medium",
    device: str = "auto",
    compute_type: str = "default",
    language: Optional[str] = "zh",
    vad_filter: bool = True,
) -> Dict[str, Any]:
    """
    Returns dict with keys: text, segments, language, info.
    segments: [{id, start, end, text, words?}, ...]
    """
    from faster_whisper import WhisperModel

    if compute_type == "default":
        compute_type = "float16" if device == "cuda" else "int8"

    logger.info("Loading WhisperModel %s (%s)…", model_size, device)
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    logger.info("Transcribing %s…", mp3_path)
    segments_iter, info = model.transcribe(
        str(mp3_path),
        language=language,
        word_timestamps=True,
        vad_filter=vad_filter,
    )

    segments: List[Dict[str, Any]] = []
    full_text_parts: List[str] = []
    for i, seg in enumerate(segments_iter):
        words_out: Optional[List[Dict[str, Any]]] = None
        if seg.words:
            words_out = [
                {"start": w.start, "end": w.end, "word": w.word}
                for w in seg.words
            ]
        segments.append(
            {
                "id": i,
                "start": seg.start,
                "end": seg.end,
                "text": seg.text.strip(),
                "words": words_out,
            }
        )
        full_text_parts.append(seg.text.strip())

    text = "".join(full_text_parts)

    out: Dict[str, Any] = {
        "text": text,
        "segments": segments,
        "language": getattr(info, "language", None),
        "duration": getattr(info, "duration", None),
    }
    return out


def save_transcript_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
