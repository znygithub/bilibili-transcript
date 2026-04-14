# bilibili-transcript

本地视频转写流水线：**优先字幕 → 否则本机 ASR → 结构化 JSON + Markdown + HTML**。

当前支持 **Bilibili**，架构已预留扩展接口（YouTube、小宇宙等可通过添加 Provider 接入）。Python 流水线**不调用外部 LLM API**——全文总结、翻译、润色由 AI 编程助手（Cursor、Claude Code 等）按 [Skill](.cursor/skills/bilibili-transcript-finalize/SKILL.md) 完成。

## 快速开始

```bash
pip install -e .                  # 或 pip install -r requirements.txt
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx
```

## 流程总览

```
视频 URL / ID
  → Provider 识别来源（Bilibili / ...）
  → 拉取元数据（标题、分 P、cid、aid）
  → 每个分 P：优先字幕（WBI / yt-dlp）→ 否则下载音轨 + faster-whisper ASR
  → 合并分段 → *_transcript.json
  → 可选：生成草稿 Markdown
  → AI 助手：润色成稿 → *_transcript_成稿.md
  → 导出 HTML → *_transcript_成稿.html
```

## 三阶段分工


| 阶段          | 执行者                                         | 产出                                 |
| ----------- | ------------------------------------------- | ---------------------------------- |
| **① 脚本**    | `python -m bilibili_transcript`             | `*_transcript.json`（分段时间轴 + 原文）    |
| **② AI 助手** | Cursor / Claude Code / 其他                   | `*_transcript_成稿.md`（总结 + 润色 + 翻译） |
| **③ 导出**    | `python -m bilibili_transcript export-html` | `*_transcript_成稿.html`（莫兰迪卡片）      |


脚本只管拉稿和结构化。去口癖、标点、分段、翻译等终稿处理由 AI 助手完成。

## 代码结构

```
bilibili_transcript/
  cli.py              主入口 + export-html 子命令
  providers/
    base.py            Provider 抽象接口（扩展新来源时实现此接口）
    bilibili.py        Bilibili Provider
  bvid.py              BV 号解析
  meta.py              B 站元数据 API
  download.py          音轨下载（API + yt-dlp 兜底）+ ffmpeg 转码
  wbi.py               B 站 WBI 签名
  subtitles.py         官方字幕抓取 + SRT 解析
  transcribe.py        faster-whisper ASR
  draft_md.py          按时间分块的草稿 Markdown
  finalize_md.py       结构化成稿 Markdown（从 presets/ 加载配置）
  export_html.py       成稿 Markdown → 莫兰迪 HTML
  text_post.py         文件名清理
  utils.py             公共工具函数
  presets/             按视频 ID 的预设内容（标题、摘要、总结）
```

## 字幕策略（每个分 P 独立判断）

1. **B 站官方 CC**（推荐）— WBI 签名请求 `x/player/wbi/v2`
2. **yt-dlp 字幕文件** — 需 `--cookies-from-browser` 或 `--ytdlp-subs`
3. **本机 faster-whisper ASR** — 以上均不可用时的兜底

部分稿件的字幕**仅在登录态返回**。未登录时接口返回空列表属正常现象，不是 bug。

## 常用参数


| 场景               | 参数                                                        |
| ---------------- | --------------------------------------------------------- |
| 默认（能抓字幕就不 ASR）   | 无额外参数                                                     |
| 登录字幕在网页有、接口无     | `--cookies-from-browser chrome`                           |
| 强制 ASR           | `--force-asr`                                             |
| 仅输出 JSON         | `--json-only`                                             |
| 官方无 CC 时试 yt-dlp | `--ytdlp-subs`                                            |
| 指定分 P            | `--part N`                                                |
| 导出 HTML          | `python -m bilibili_transcript export-html path/to/成稿.md` |


## 输出物


| 文件                     | 说明                                                 |
| ---------------------- | -------------------------------------------------- |
| `*_transcript.json`    | 事实源：`video_id`、`title`、`segments[]`、`part_sources` |
| `{bvid}_transcript.md` | 按时间分块的草稿（总结留空）                                     |
| `*_transcript_成稿.md`   | 结构化成稿（初版由脚本生成，终稿由 AI 覆盖）                           |
| `*_transcript_成稿.html` | 莫兰迪卡片单页 HTML                                       |


## 扩展新的视频来源

1. 在 `bilibili_transcript/providers/` 下创建新模块（如 `youtube.py`）
2. 实现 `TranscriptProvider` 接口：`match()`、`extract_id()`、`fetch_metadata()`、`fetch_segments()`、`download_audio()`
3. 在 `providers/__init__.py` 的 `PROVIDERS` 列表中注册
4. 下游流程（JSON → MD → HTML）无需改动

```python
# providers/youtube.py 示例骨架
class YouTubeProvider(TranscriptProvider):
    name = "youtube"

    def match(self, url_or_id: str) -> bool:
        return "youtube.com" in url_or_id or "youtu.be" in url_or_id
    # ... 实现其余方法
```

## 环境要求

- Python ≥ 3.10
- `ffmpeg` on PATH
- 依赖：`pip install -e .` 或 `pip install -r requirements.txt`
- ASR 可选 CUDA（`--device cuda`）

## AI 助手集成

本项目的 Skill 文件（`.cursor/skills/bilibili-transcript-finalize/SKILL.md`）定义了 AI 助手的执行流程。它不绑定特定工具——任何能读写文件、执行 shell 命令的 AI 编程助手都可以按此流程工作。

## 已知案例

- `case_outputs/BV1f3DYBDE9h/` — 中文评述
- `case_outputs/BV1ijE4zwEHP/` — 英文 ASR
- `case_outputs/BV1728bzzEwA/` — 多 P 视频

