---
name: bilibili-transcript-finalize
description: >-
  Video URL → transcript pipeline → 成稿.md → 成稿.html (Morandi).
  Always generate HTML unless user explicitly opts out.
  macOS: grant Full Disk Access to Terminal app if using --cookies-from-browser.
---

# 视频转写成稿流程

> 所有路径相对仓库根目录。本流程适用于任何支持读写文件的 AI 编程助手（Cursor、Claude Code 等）。

## 三阶段流程

| 阶段 | 执行者 | 产出 |
|------|--------|------|
| **① 脚本** | `python -m bilibili_transcript` | `*_transcript.json` + 可选草稿 `.md` |
| **② AI 助手** | 你（读 JSON → 润色成稿） | `*_transcript_成稿.md` |
| **③ 导出 HTML** | `python -m bilibili_transcript export-html` 或你手写 | `*_transcript_成稿.html` |

## 触发条件

1. 用户发来**视频链接**（`bilibili.com`、`b23.tv`、含 `BV` 号）→ 执行 ①②③
2. 已有 `*_transcript.json` 或 `成稿.md` → 从缺失的阶段开始补

## ① 运行脚本

```bash
python -m bilibili_transcript "<URL或BV号>" \
  -o case_outputs/<视频ID> \
  --cookies-from-browser chrome
```

- 按需加 `--part N`（多 P 视频指定分 P）
- **不要**加 `--force-asr`（流水线优先拉字幕，只在字幕不可用时才 ASR）
- 确认 JSON 产出后，检查 `part_sources` 中的 `mode`：
  - `official_cc` / `ytdlp_subtitle_file` → 字幕，不要重跑 ASR 覆盖
  - `asr` → 转写，正常

### macOS 权限提示

`--cookies-from-browser` 需要在 **系统设置 → 隐私与安全性 → 完全磁盘访问权限** 中授权终端 App。

## ② 成稿 Markdown

基于 `*_transcript.json` 完成以下工作，写入 `*_transcript_成稿.md`：

### 文档结构（必须满足）

1. `# {视频标题}`（来自 JSON `title`，不要用纯 ID）
2. `## 全文总结` — 详细中文总结：背景、说话人、主线论点、关键数据、结论；可用 **加粗** 突出重点；不编造
3. `## 1. 完整逐字稿` — 其下固定 **5 个小节** `### 1.1` … `### 1.5`
4. 小节标题 = **话题短标题**（不要用纯时间段做标题）
5. 每节开头引用块：首行 `> （时间参考：MM:SS–MM:SS）`，后续 2–4 句摘要
6. 正文：简体中文；英文口播译中文；专名统一；中文全角标点；按语义分段
7. 多说话人时可用 `**主持人：**` / `**嘉宾：**` 分行（无法判断时不要编造）

### 关键规则

- 脚本产出的 `finalize_md` 只是分桶原文拼接 → **必须覆盖为终稿**
- 分桶规则：`segments` 按列表顺序均分 5 桶（同 `split_segments_into_n_buckets(segments, 5)`）
- 不得虚构观点、案例、数字

### 文件名

`{sanitize_filename_title(title)}_{video_id}_transcript_成稿.md`

## ③ 导出 HTML

成稿 `.md` 定稿后：

```bash
python -m bilibili_transcript export-html path/to/成稿.md
```

或按 `docs/transcript_morandi_html/README.md` + `morandi-template.html` 手写。

- **默认必做**，除非用户明确说只要 Markdown
- 多 P 视频每个 P 各自走完 ②→③

## 完成后回复

告知用户：
- `.md` 与 `.html` 的路径
- `part_sources` 来源（字幕/ASR）
- HTML 是否已自动打开
