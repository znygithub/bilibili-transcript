# bilibili-transcript

## 这个项目在做什么

在**本机**把 B 站视频转成可核对的 **`{BV号}_transcript.json`**（分段时间轴、可选词级时间戳），再生成可检阅的 **`{标题slug}_{BV号}_transcript_成稿.md`**（全文总结、分话题小节、段前摘要、逐字正文）。**Python 流水线只负责文字稿与初版成稿结构，不调用大模型 HTTP API**；成稿的总结、翻译与润色由 **Cursor** 按项目内 [Skill](.cursor/skills/bilibili-transcript-finalize/SKILL.md)（子 Agent）完成。

**仓库**：<https://github.com/znygithub/bilibili-transcript>（公开，无密钥）

```bash
pip install -r requirements.txt   # 建议使用 venv
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx
```

「字幕 / ASR 先后的决策树」与常用 CLI 参数见 [**TRANSCRIPT_STRATEGY.md**](TRANSCRIPT_STRATEGY.md)。

---

## 1. 项目目标

在**本机**完成 B 站视频的**可核对转写**与**本地文稿产物**，用于：

- 优先使用 **B 站官方 CC 字幕**（与播放器一致），若无则 **yt-dlp 拉字幕**，再不行则 **faster-whisper ASR**；
- 输出结构化 **`{BV号}_transcript.json`**（含分段时间轴、可选词级时间戳）；
- 生成 **`{标题slug}_{BV号}_transcript_成稿.md`**：含「全文总结 + 分话题小节 + 段前摘要 + 逐字正文」（部分 BV 在 `finalize_md.py` 里写死了总结/分节模板）；
- **Python 流水线不调用大模型 HTTP API**；成稿的总结与翻译由 **Cursor Agent** 按项目内 **Skill** 执行（见下），无需用户在对话里手动复制 JSON。

**非目标**：在 Python 内封装「调用 OpenAI / 公司网关」的总结服务（若需要可另加模块）。

---

## 2. 分工：脚本 = 文字稿，Cursor 子 Agent = 翻译与总结

| 层级 | 做什么 |
|------|--------|
| **脚本**（`bilibili_transcript`） | **只生成文字稿**：`*_transcript.json`（含分段时间与口播文本）。不写终稿总结、不做翻译终稿。 |
| **Cursor** | 按 Skill **[`.cursor/skills/bilibili-transcript-finalize/SKILL.md`](.cursor/skills/bilibili-transcript-finalize/SKILL.md)**：主 Agent 跑完脚本后，**用子 Agent** 分工完成 **全文总结、翻译、分节摘要、润色**，写入 `*_transcript_成稿.md`（勿用单条回复硬塞万字）。 |

**用户操作**：发 **B 站链接** 或 `@` 已有 `*_transcript.json` 即可；**不要求**手抄 JSON。

仓库内**没有** Python 调用 Cursor；子 Agent 是 Cursor 侧能力，不是脚本里的函数。

---

## 3. 总体流程（数据流）

```
B 站 URL 或 BV 号
    → 拉取稿件元数据（标题、分 P、cid、aid）
    → 每一分 P：优先官方字幕（WBI）→ 可选 yt-dlp 字幕 → 否则下载音轨 + faster-whisper ASR
    → 合并分 P 分段 → 写入 *_transcript.json
    →（可选）finalize：生成初版成稿 md
    →（Cursor 子 Agent）按 Skill 终稿：翻译 + 总结 + 润色 → *_transcript_成稿.md
```

---

## 4. 代码结构（`bilibili_transcript/`）

| 文件 | 职责 |
|------|------|
| [`cli.py`](bilibili_transcript/cli.py) | **主入口**：下载 / 字幕 / ASR、写 JSON、调用成稿与草稿。 |
| [`__main__.py`](bilibili_transcript/__main__.py) | `python -m bilibili_transcript` 时转调 `cli.main()`。 |
| [`draft_md.py`](bilibili_transcript/draft_md.py) | 生成 `{bvid}_transcript.md`：按时间跨度分块的**纯草稿**（总结处留空），不含任何 LLM 调用。 |
| [`download.py`](bilibili_transcript/download.py) | `pagelist`、`playurl` 下载音轨；`ffmpeg` 转 MP3；可选 `yt-dlp` 兜底。 |
| [`meta.py`](bilibili_transcript/meta.py) | 拉取视频标题等元数据。 |
| [`bvid.py`](bilibili_transcript/bvid.py) | 从 URL 解析 BV 号、构造分 P 页面 URL。 |
| [`wbi.py`](bilibili_transcript/wbi.py) | B 站 **WBI 签名**。 |
| [`subtitles.py`](bilibili_transcript/subtitles.py) | 官方 CC 解析；可选 `yt-dlp` 字幕文件解析。 |
| [`transcribe.py`](bilibili_transcript/transcribe.py) | **faster-whisper** 转写、`save_transcript_json`。 |
| [`finalize_md.py`](bilibili_transcript/finalize_md.py) | 从 JSON 生成 **成稿 Markdown**；特定 BV 的内嵌总结/分节；`format_body` 仅做排版启发式。 |
| [`text_post.py`](bilibili_transcript/text_post.py) | `sanitize_filename_title`、`format_body`（中/英）。 |

已删除、不再维护的文件（避免误以为「还有机翻/LLM 模块」）：~~`translate.py`~~、~~`llm_md.py`~~、~~`cursor_export.py`~~（曾生成易误解的 `*_cursor_prompt.md`）。

---

## 5. 输出物说明

| 产物 | 说明 |
|------|------|
| `*_transcript.json` | **事实源**：`bvid`、`title`、`text`、`segments[]`、`part_sources`。 |
| `{bvid}_transcript.md` | 按时间分块的草稿；总结与话题标题为空或占位，需自行编辑（`--json-only` 时不生成）。 |
| `{标题slug}_{BV号}_transcript_成稿.md` | **检阅用成稿**：Python 可出初版；终稿由 **Cursor Skill** 润色/翻译后覆盖（见上）。 |
| `case_outputs/` | 示例输出目录；可含 `*_p1.mp3` 等。 |

重新跑流水线会**覆盖**上述 md（手润稿请先备份）。

---

## 6. 环境与运行

- **依赖**：[`requirements.txt`](requirements.txt)（`requests`、`faster-whisper`、`yt-dlp` 等）。
- **系统工具**：`ffmpeg`；ASR 可选 CUDA。建议用项目 `venv` 的 `python`，避免系统 Python 缺依赖。

```bash
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx
```

常用参数见 [`TRANSCRIPT_STRATEGY.md`](TRANSCRIPT_STRATEGY.md)。

**Skill 全局使用（可选）**：将 `.cursor/skills/bilibili-transcript-finalize/` 复制到 `~/.cursor/skills/bilibili-transcript-finalize/`，便于在其他仓库复用同一套成稿指引。

---

## 7. 成稿逻辑与定制点（`finalize_md.py`）

- 对特定 `bvid` 可配置：分节标题、段前摘要、全文总结（如 `_full_summary_bv1f3()`）。
- 英文 ASR：`format_body(..., lang_hint="en")` 仅为初版排版；**中文终稿**由 Skill `bilibili-transcript-finalize` 在 Cursor 侧完成翻译与成稿。
- 中文 ASR 初版：`format_body(..., lang_hint="zh")`；可读性终稿由同一 Skill 润色。

---

## 8. 已知案例

- `case_outputs/BV1f3DYBDE9h/`：中文评述，成稿有手润版。
- `case_outputs/BV1ijE4zwEHP/`：英文 ASR，成稿中文为对话助手翻译示例。

---

## 9. 接手检查清单

1. 能成功跑通命令并生成 JSON。
2. 阅读 `TRANSCRIPT_STRATEGY.md`，理解无登录时 CC 可能为空。
3. 重要成稿改完后做备份，避免被流水线覆盖。
4. 若需自动调用公司模型 API，应**新开模块**评审后再接，本仓库默认不包含。

---

## 10. 版本与维护

- 包版本见 [`bilibili_transcript/__init__.py`](bilibili_transcript/__init__.py) 中的 `__version__`。
