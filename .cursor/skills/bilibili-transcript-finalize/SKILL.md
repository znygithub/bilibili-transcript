---
name: bilibili-transcript-finalize
description: >-
  Bilibili URL → bilibili_transcript (subtitle-first, no ASR when CC exists) → 成稿.md → 必生成 成稿.html
  (Morandi). Do not ask whether to build HTML. macOS: Full Disk Access for Terminal + Cursor if using
  browser cookies. See repo docs/transcript_morandi_html/.
---

# B 站：脚本出文字稿，Cursor 做成稿 + **必生成**莫兰迪 HTML

> 文内 `docs/…`、`TRANSCRIPT_STRATEGY.md` 均相对**本仓库根目录**。

## Gotcha（常见翻车点）

- **`finalize_md` / CLI 写出来的 md 不是终稿**：只是分桶 + 原文拼接；**无标点、字墙**＝② 还没做，别当交付物。  
- **多 P / 上下集**：`BV*_p1`、`BV*_p2` **各自**要做完 ②→③；只润一集或只润 1.1，另一集/节仍是字幕。  
- **子 Agent 不会自动跑**：跑完 Python **不会**自动再起一轮润色；必须在对话里**显式**完成 ②（再 ③）。  
- **③ 不能救 ②**：用未润色 md 生成的 HTML，只是**排版好的字墙**；先定稿 md，再 `export_morandi_html` 或手写 HTML。

## 收到 B 站视频链接时的铁律

1. **必跑完整链路**：① `bilibili_transcript` → ② 成稿 `*_transcript_成稿.md` → ③ **`*_transcript_成稿.html`**。  
2. **不要问**「要不要生成网页 / HTML」——**默认就做**，除非用户**明确**说只要 Markdown、不要 HTML。  
3. ③ 完成后按 [`docs/transcript_morandi_html/README.md`](docs/transcript_morandi_html/README.md) 用系统默认浏览器 **自动打开** 该 HTML（`open` / `xdg-open` / `start`）。

## 字幕已有 → 不要自己转写（判定规则）

流水线**优先字幕**，**不是**一上来 Whisper。主 Agent 跑 ① 时必须遵守：

| 判定依据 | 怎么做 |
|----------|--------|
| **目标** | 只要站方字幕能拉到（官方 CC / yt-dlp 字幕文件），**就不要**走本机 ASR（`faster-whisper`）。 |
| **默认参数** | 使用 **`--cookies-from-browser <浏览器>`**（例如 `chrome`），与网页登录态一致；详见 [`TRANSCRIPT_STRATEGY.md`](TRANSCRIPT_STRATEGY.md)。匿名请求时 `wbi/v2` 可能对「需登录字幕」返回空列表，**不等于**没有字幕。 |
| **如何确认已走字幕、未走 ASR** | 读 `*_transcript.json` 里的 **`part_sources`**：若某项 **`mode` 为 `official_cc` 或 `ytdlp_subtitle_file`**，该分 P 即为字幕轨，**禁止**再对该稿 **`--force-asr`** 重跑覆盖。 |
| **只有**当 `part_sources` 里对应分 P 为 **`asr`**（或无任何分段且已排除网络/权限问题）时，才视为「只能转写」。 |
| **多 P / 上下集** | 用户要第几 P 就加 **`--part N`**；多集分别输出到不同目录，各自再做 ②③。 |

**小结**：先按「字幕优先 + 浏览器 Cookie」跑脚本 → 用 **`part_sources.mode`** 判定来源；**已有字幕则不要重复提取（不要强制 ASR）**。

### macOS：读浏览器 Cookie 时的系统权限

使用 **`--cookies-from-browser`** 时，本机会用 **`browser-cookie3`** 读取浏览器内 `bilibili.com` 的 Cookie。若系统多次弹窗要求输入**登录密码**或授权：

- 在 **系统设置 → 隐私与安全性 → 完全磁盘访问权限** 中，为 **「终端」** 与 **Cursor**（以及你实际用来执行 Python 的终端类 App）**勾选授权**。  
- 授权后**退出并重新打开**对应 App，再跑脚本；一般可明显减少重复弹窗。  
- 这与「业务逻辑」无关，是 macOS 对浏览器敏感数据的保护。

## 成稿转网页（莫兰迪）— 仓库文档，不是第二个 Skill

- **位置**：[`docs/transcript_morandi_html/README.md`](docs/transcript_morandi_html/README.md) 与 [`morandi-template.html`](docs/transcript_morandi_html/morandi-template.html)。  
- **怎么用**：② 完成后 **必须**再启子 Agent，按 README + 模板写入 **`*_transcript_成稿.html`**，并 **自动打开**；主 Agent **不要**在对话里贴整页 HTML。

## 分工（必须遵守）

| 阶段 | 谁做 | 产出 |
|------|------|------|
| **① 脚本** | `python -m bilibili_transcript`（本仓库 CLI） | **只生成文字稿**：`*_transcript.json`（含 `segments` 与 **`part_sources`**）。可选草稿 `.md`、可选 `finalize_md` 初版结构 md。脚本**不写**终稿级全文总结，**不对口播正文做**去口癖、标点、分段、换行等处理。 |
| **② Cursor** | **主 Agent 编排 + 若干子 Agent** | 基于 JSON 做 **翻译**（英文→中文）、**全文总结**、**去口癖**、**标点与分段/换行**、小节标题与段前摘要，输出并覆盖 **`*_transcript_成稿.md`**。 |
| **③ 必跑** | **子 Agent** | 在成稿 `.md` 落盘后，按 **`docs/transcript_morandi_html/`** 生成 **`*_transcript_成稿.html`**。 |

- 主 Agent：跑完 ① 后，**不要**在单条回复里塞万字成稿；应 **启动子 Agent** 完成 ②。  
- **③ 推荐**：成稿 md 定稿后，用 **`tools/export_morandi_html.py`** 生成 HTML（**仅**结构与转义，不改写正文）；亦可按 [`docs/transcript_morandi_html/`](docs/transcript_morandi_html/) 手写单页。禁止用语义脚本替代 ② 的润色。

### 禁止：用 Python 脚本处理终稿正文

- **不允许**使用仓库内或自写脚本对逐字稿做 **去口癖、整理语序、加标点、分段、换行** 等语义/可读性处理（含已移除的 `format_body` 类启发式）。  
- **`finalize_md` / CLI 若写出 `*_transcript_成稿.md`**，其中逐字部分仅为 **原文拼接 + 分桶结构**，**必须**由子 Agent 按上文要求 **覆盖为终稿**。  
- **`text_post.format_body`** 为兼容保留，**原样透传**，不参与终稿质量；终稿可读性 **只认子 Agent 产出**。

## 何时触发

1. **主触发**：用户发来 **B 站视频链接**（`bilibili.com`、`b23.tv` 或含 `BV`+10 位）。→ **① → ② → ③**，**含 HTML**。  
2. **次触发**：已有 `*_transcript.json` 或成稿 `.md`。→ 从缺的那步补；若仅缺 HTML，只跑 **③**。

### 收到 URL 时的建议命令形态

```bash
python -m bilibili_transcript "<URL或BV>" -o case_outputs/<BV号或子目录> \
  --cookies-from-browser chrome
```

按需加 `--part N`、`--ytdlp-subs`（官方仍空时再试 yt-dlp）。**不要**默认加 `--force-asr`。

确认 `*_transcript.json` 存在后，再做 ②、③。

## 输入（子 Agent 共用）

- `*_transcript.json` 中的 `title`、`bvid`、`segments`、`part_sources`。

## 交付物

- **必交**：`<sanitize(标题)>_<bvid>_transcript_成稿.md`（规则同 `bilibili_transcript/text_post.sanitize_filename_title`）。  
- **必交**：同路径 **`<sanitize(标题)>_<bvid>_transcript_成稿.html`**；**仅当用户明确不要网页时**可省略 HTML。

## 文稿要求（终稿必须满足，与仓库 `TRANSCRIPT_STRATEGY.md` 成稿版式对齐）

### 文档结构

1. **一级标题** `#`：使用 JSON 的 `title`（B 站视频标题），勿用纯 BV 号当标题。  
2. **`## 全文总结`**：简体中文，**尽量详细**——背景、说话人/博主、主线论点、关键数据与案例、结论；可用加粗突出重点；**不编造**事实；字幕/ASR 明显错误可在总结中括号注明。  
3. **`## 1. 完整逐字稿`**：其下固定 **5 个小节** `### 1.1` … `### 1.5`（与 `finalize_md.split_segments_into_n_buckets(..., 5)` 分桶一致）。  
4. **小节标题**：**话题短标题**；**禁止**仅以「时间片段 1（00:00–05:00）」为唯一标题。  
5. **每节开头（引用块）**：首行 `> （时间参考：MM:SS–MM:SS）`；后续 2～4 句本节摘要。  
6. **正文**：简体中文为主；英文口播译成通顺中文；专名统一。  
7. **多说话人**：可 **`主持人：`** / **`嘉宾：`** 等；**无法判断时不要编造**。  
8. **标点与分段**：中文全角标点；按语义分段。

### 语言与忠实度

- 终稿主体为**简体中文**；逐字以 JSON 为据，**不得虚构**观点、案例、数字。

### 文件名

- `{sanitize_filename_title(title)}_{bvid}_transcript_成稿.md` / `.html`。

## 分桶规则（与代码一致）

- 按 `segments` **列表顺序**均分成 **5 桶**（与 `finalize_md.split_segments_into_n_buckets(segments, 5)` 一致），勿在单个 segment 中间切断。

## 与 `finalize_md.py` 的关系

- Python 可能生成一版**仅含结构与原文拼接**的 md，**以本子 Agent 流程产出的终稿为准**覆盖或替换；**不得**依赖脚本完成润色。

## 完成后

- 回复用户：**`.md` 与 `.html` 路径**、**`part_sources` 来源**（字幕 / ASR）、是否已自动打开 HTML。  
- 若用户事先声明只要 md，在回复里说明**未生成 HTML**的原因。
