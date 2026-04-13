---
name: bilibili-transcript-finalize
description: >-
  After bilibili_transcript script outputs transcript JSON only, Cursor spawns sub-agents to
  translate and summarize into 成稿 Markdown. Primary trigger: user sends a Bilibili video URL.
  Script does 文字稿; Cursor does 翻译与总结 via sub-agents. Also when user @ json or mentions 成稿.
---

# B 站：脚本出文字稿，Cursor 子 Agent 做翻译与总结

## 分工（必须遵守）

| 阶段 | 谁做 | 产出 |
|------|------|------|
| **① 脚本** | `python -m bilibili_transcript`（本仓库 CLI） | **只生成文字稿**：`*_transcript.json`（含 `segments` 时间轴与口播文本）。可选 `{bvid}_transcript.md` 粗分块草稿。脚本**不写**全文总结、不做翻译、不把终稿成稿当唯一目标。 |
| **② Cursor** | **主 Agent 编排 + 若干子 Agent** | 基于 JSON 做 **翻译**（英文 ASR→中文）、**总结**（全文总结 + 每节摘要）、标点与分段，输出 **`*_transcript_成稿.md`**。 |
| **③ 可选** | **另一个 Cursor 子 Agent**（非脚本） | 在 **`*_transcript_成稿.md` 已生成** 之后，由主 Agent **单独启动子 Agent**，让其阅读 skill **`bilibili-morandi-html`**（含 `morandi-template.html`），把成稿转为单页 **`*_transcript_成稿.html`**。 |

- 主 Agent：跑完 ① 后，**不要**自己在一条回复里塞下全文翻译+总结；应 **启动子 Agent**（若可用 `Task` 工具则并行）分工完成 ②，再合并写入文件。
- 子 Agent 职责示例：子 Agent 1 = 仅「全文总结」；子 Agent 2～6 = 各管 1/5 节的标题+摘要+译/润色正文。
- **③**：成稿 `.md` 落盘且用户要网页版时，主 Agent **不要**自己在对话里贴整页 HTML；应 **再启动一个子 Agent**，指令中写明：读 `bilibili-morandi-html` skill、输入为刚写好的成稿路径（或 `@` 文件）。**仓库不提供** `md→html` 的 Python 脚本，HTML 由该子 Agent 按 skill 写出文件即可。

## 何时触发

1. **主触发**：用户发来 **B 站视频链接**（`bilibili.com`、`b23.tv` 或含 `BV`+10 位）。→ 先执行 ①，再执行 ②。
2. **次触发**：已有 `*_transcript.json`（用户 `@` 文件或提到 `case_outputs` / 成稿）。

### 收到 URL 时的顺序

1. 跑脚本（若尚无 json）：  
   `python -m bilibili_transcript "<URL或BV>" -o case_outputs/<BV号>`
2. 确认 `case_outputs/<BV号>/<BV>_transcript.json` 存在。
3. **用子 Agent** 按下文「交付物」生成终稿，**不是**让主对话一次性生成万字画稿。

## 输入（子 Agent 共用）

- `*_transcript.json` 中的 `title`、`bvid`、`segments`（`start` / `end` / `text`）。

## 交付物（子 Agent 合并结果）

- 路径：`<sanitize(标题)>_<bvid>_transcript_成稿.md`（规则同 `bilibili_transcript/text_post.sanitize_filename_title`）。
- 版式与结构见下节 **「文稿要求」**。

## 文稿要求（终稿必须满足，与仓库 `TRANSCRIPT_STRATEGY.md` 成稿版式对齐）

### 文档结构

1. **一级标题** `#`：使用 JSON 的 `title`（B 站视频标题），勿用纯 BV 号当标题。
2. **`## 全文总结`**：简体中文，**尽量详细**——背景、说话人/博主、主线论点、关键数据与案例、结论；可用加粗突出重点；**不编造**音视频里不存在的事实；ASR 明显同音错误可在总结中括号注明「口播作 xxx」。
3. **`## 1. 完整逐字稿`**：其下固定 **5 个小节** `### 1.1` … `### 1.5`（与 `finalize_md.split_segments_into_n_buckets(..., 5)` 分桶一致）。
4. **小节标题**：必须是**话题短标题**（如「开场：xxx」「案例：xxx」），**禁止**单独使用「时间片段 1（00:00–05:00）」类作为唯一标题；时间只允许出现在下方引用摘要里。
5. **每节开头（引用块）**  
   - 第一行：`> （时间参考：MM:SS–MM:SS）`（由该节首尾 segment 的 `start`/`end` 推算）。  
   - 第二行起：`> ` 接 **2～4 句**本节中文摘要，只概括本节，不剧透其他节。
6. **正文**：简体中文为主；口播为英文时译为通顺口语化中文；**公司/产品/人名**用通用中文译名或保留英文并在首次出现必要时括注，全书专名统一。
7. **多说话人**（访谈/对谈）：若从文本可区分，可用 **`主持人：`** / **`嘉宾：`** 等加粗标签分行；**无法判断时不要编造身份**。
8. **标点与分段**：中文全角标点；按语义分段，禁止把正文压成无标点长串，也禁止机械按固定字数折行冒充排版。

### 语言与忠实度

- 终稿主体为**简体中文**；原文英文须译出，勿整段英文堆在终稿（专名、固定产品名可保留或括注）。
- 逐字部分以 JSON 为据，可纠错标点与同音字，**不得虚构观点、案例、数字**。

### 文件名

- `{sanitize_filename_title(title)}_{bvid}_transcript_成稿.md`；非法路径字符与过长标题按 `text_post.sanitize_filename_title` 处理。

## 分桶规则（与代码一致）

- 按 `segments` **列表顺序**均分成 **5 桶**（与 `finalize_md.split_segments_into_n_buckets(segments, 5)` 一致），勿在单个 segment 中间切断。

## 与 `finalize_md.py` 的关系

- Python 可能生成一版初稿成稿，**以本子 Agent 流程产出的终稿为准**覆盖或替换。

## 完成后

- 回复用户：成稿路径、是否经子 Agent 并行、译/润色说明。
- 若用户还要求 **HTML 阅读版**：**启动子 Agent**，使其遵循 **`bilibili-morandi-html`**，产出与成稿同路径、同主文件名的 **`*_transcript_成稿.html`**。
