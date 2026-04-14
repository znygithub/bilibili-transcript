#!/usr/bin/env python3
"""Backward-compat wrapper. Prefer: python -m bilibili_transcript export-html"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bilibili_transcript.export_html import export_morandi_html

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: export_morandi_html.py <成稿.md|目录>", file=sys.stderr)
        print("Prefer: python -m bilibili_transcript export-html <path>", file=sys.stderr)
        sys.exit(1)
    arg = Path(sys.argv[1])
    if arg.is_dir():
        mds = list(arg.glob("*_transcript_成稿.md"))
        if not mds:
            print("No *_transcript_成稿.md in directory", file=sys.stderr)
            sys.exit(1)
        md_path = mds[0]
    else:
        md_path = arg
    out = export_morandi_html(md_path)
    print(out)
