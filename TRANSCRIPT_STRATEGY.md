# 转写策略速查

> 详细说明见 [README.md](README.md)。本文件仅作 CLI 操作的快速参考。

## 字幕优先级（每个分 P 独立）

1. **B 站官方 CC** — `x/player/wbi/v2`（需 `bvid` + `cid` + `aid`）
2. **yt-dlp 字幕** — `--cookies-from-browser` 或 `--ytdlp-subs` 时启用
3. **本机 ASR** — faster-whisper，以上均不可用时兜底

## 典型命令

```bash
# 默认：字幕优先
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx

# 登录态字幕
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx \
  --cookies-from-browser chrome

# 强制 ASR
python -m bilibili_transcript "BV1xxxxxxxxx" -o out --force-asr

# 仅 JSON
python -m bilibili_transcript "BV1xxxxxxxxx" -o out --json-only

# 导出 HTML
python -m bilibili_transcript export-html case_outputs/BV1xxxxxxxxx/
```

## JSON 中的 `part_sources`

| `mode` 值 | 含义 |
|-----------|------|
| `official_cc` | B 站官方字幕 |
| `ytdlp_subtitle_file` | yt-dlp 拉取的字幕文件 |
| `asr` | 本机 faster-whisper 转写 |

## 成稿版式

终稿结构与要求见 [SKILL.md](.cursor/skills/bilibili-transcript-finalize/SKILL.md) 的 **② 成稿 Markdown** 一节。
