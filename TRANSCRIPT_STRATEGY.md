# 转写策略：官方字幕优先，否则本机 ASR

本仓库流水线**不调用外部 LLM API**。全文总结、英文译中文、话题标题等**不在代码里生成**，由你在编辑器里自行撰写，或打开本项目的 AI 对话（如 Cursor）把 `*_transcript.json` 贴进去让模型辅助整理——**那是人工/对话侧操作，不是本仓库的函数调用**。

## 决策顺序（每个分 P 独立）

1. **B 站官方 CC（推荐）**
  - 调用 `GET https://api.bilibili.com/x/player/wbi/v2`（**WBI 签名**，需 `bvid` + `cid` + `aid`）。  
  - 若 `data.subtitle.subtitles` 中存在带 `subtitle_url` 的轨道，则按语言优先级选取（如 `zh-Hans`、`zh-CN`、`ai-zh` 等），下载 JSON。  
  - 字幕正文取自 JSON 的 `body[].from` / `to` / `content`，与站内播放器字幕一致。  
  - **说明**：部分稿件的 CC **仅在登录态**返回；未登录时接口可能返回空列表，与「是否有字幕」的肉眼判断不一致，属正常现象。
2. **yt-dlp 字幕文件（可选）**
  - 当第 1 步无可用轨道，且你传了 `--cookies-from-browser` 或显式 `--ytdlp-subs` 时，用 `yt-dlp --write-subs --write-auto-subs` 拉取本地 `.srt` 再解析。  
  - 仍失败时，进入第 3 步。
3. **本机 faster-whisper ASR**
  - 下载音轨（`pagelist` + `playurl` 或 `--ytdlp`），转 MP3，再转写。  
  - 适用于无字幕、字幕需登录但不愿带 Cookie、或只有自动语音场景。

## 常用参数


| 场景                     | 建议参数                                                 |
| ---------------------- | ---------------------------------------------------- |
| 默认（能抓 CC 就不 ASR）       | 无额外参数                                                |
| 只要 ASR、不尝试字幕           | `--force-asr`                                        |
| 完全不要字幕尝试               | `--no-prefer-subtitles`（与 `--force-asr` 类似，仍走下载+ASR） |
| 登录用户字幕在网页有、接口无         | `--cookies-from-browser chrome`（注入官方 `wbi/v2` + yt-dlp；需 `pip install browser-cookie3`） |
| 官方无 CC 时仍尝试 yt-dlp 拉文件 | `--ytdlp-subs`（常需配合 Cookie 才有真 CC）                   |


## 输出中的 `part_sources`

`*_transcript.json` 里的 `part_sources` 记录每一分 P 的来源：`official_cc`、`ytdlp_subtitle_file` 或 `asr`，便于核对可靠性。

## 成稿版式（与「硅谷 101」类对谈稿对齐）

**终稿完整文稿要求**（含子 Agent 执行清单）以项目 Skill 为准： [`.cursor/skills/bilibili-transcript-finalize/SKILL.md`](.cursor/skills/bilibili-transcript-finalize/SKILL.md) 中的 **「文稿要求」** 一节。

**分工**：去口癖、标点、分段、换行、翻译等**一律由 Cursor 子 Agent** 在成稿阶段完成；Python 流水线**不得**用语义规则或脚本替代（见该 Skill **「禁止：用 Python 脚本处理终稿正文」** 与 **Gotcha**）。

流水线生成的 `*_transcript.md` 是**占位草稿**，结构约定为：

1. `#` 视频标题
2. `## 全文总结`（须补写详细中文总结）
3. `## 1. 完整逐字稿`
4. 其下为 `### 1.1`、`### 1.2` … —— 小节标题应为**话题**（如「开场介绍」），**不要**以「时间片段」作为终稿标题；时间仅可放在 `>` 摘要里作参考。
5. 每节前 `>` 写 2～4 句本节摘要。
6. 多说话人时可用 **主持人：** / **嘉宾：** 等分行（仅当文本可支持时，勿编造）。
7. **英文须译为简体中文**：流水线**不调用**任何翻译 API。请基于 `*_transcript.json` 在本地编辑终稿，或使用编辑器 AI 辅助翻译；统一专名与说话人分段。

## 实测（Case）

在本机 **未登录 B 站账号**、无 Cookie 条件下：


| 稿件                               | 预期                 | 实际                                                                                                              |
| -------------------------------- | ------------------ | --------------------------------------------------------------------------------------------------------------- |
| `BV1f3DYBDE9h`（约 5 分钟，标题含「一人公司」） | 若网页有 CC，理想情况应走官方字幕 | `wbi/v2` 返回 `subtitles: []`，与 yt-dlp 提示「字幕需登录」一致，**回退 ASR**；流水线成功产出 `*_transcript.json`，`part_sources.mode=asr` |
| `BV1ijE4zwEHP`（约 20 分钟，李录相关）     | 无官方 CC 时走 ASR      | `wbi/v2` 无轨道，**应走 ASR**（与 Case1 同一套逻辑；长视频 ASR 耗时显著增加）                                                           |


**可靠性结论**：

1. **官方字幕检测**依赖 `wbi/v2`；与旧版未签名 `v2` 相比更稳定。若你能在浏览器里看到 CC 但脚本抓不到，优先尝试 `--cookies-from-browser chrome`。
2. **未登录**时，「有字幕的稿件」在接口层仍可能表现为空，**不属于脚本逻辑错误**，而是平台鉴权策略。
3. **ASR** 为兜底路径；`tiny` 模型速度快但繁体/专名错误更多，正式使用建议 `medium` 或 `large-v3`。
4. 部分音轨可能出现 faster-whisper 的 `mel_spec` 数值警告，一般不影响整段转写；若 ASR 结果为空，可试 `--no-vad`。

