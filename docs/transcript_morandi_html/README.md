# 成稿 → 网页（莫兰迪卡片）指引

本目录是**仓库里的普通文档**（Markdown + HTML 模板），**不是** Cursor 的 Agent Skill：不放在 `.cursor/skills/`、不占用全局 Skill 数量。主流程里由 **[`bilibili-transcript-finalize`](../../.cursor/skills/bilibili-transcript-finalize/SKILL.md)** 在阶段③ 要求子 Agent **按本指引执行**，效果上等同于「多一段规范」，但无需单独注册 Skill。

| 文件 | 作用 |
|------|------|
| **本 README** | 映射规则、步骤、注意事项 |
| [`morandi-template.html`](morandi-template.html) | 单页 HTML 模板（内联 CSS、占位符） |

把 **Markdown 成稿**（尤其 `*_transcript_成稿.md`）转为**单文件 HTML**，风格为暖灰米底、白卡片、章节编号圆圈与可选时间胶囊标签。**无外链、无 JavaScript**，本地双击即可阅读。

## 分工（谁跑）

- **推荐（稳定产出）**：成稿 `.md` 定稿后，运行 **`tools/export_morandi_html.py`**（仓库根目录，**仅**把 Markdown 映射到 `morandi-template.html` 的结构并做 HTML 转义，**不参与**去口癖、标点等正文处理）。示例：  
  `python tools/export_morandi_html.py case_outputs/BV1xxxx_p1/段永平…_transcript_成稿.md`
- **备选**：由 **Cursor 子 Agent** 阅读 **本 README** 与 **`morandi-template.html`** 手写写入 `.html`（适合需微调版式的个案）。
- 子 Agent 与「翻译/总结成稿」子 Agent **分开**：避免单条对话塞超长 HTML；HTML 专由本子任务负责。
- **B 站链接主流程**：`bilibili-transcript-finalize` 规定 **默认**在 ② 完成后**总是**再跑阶段③（除非用户明确只要 md）。
- 阶段 **②** 成稿 `.md` 的正文润色（去口癖、标点、分段、换行等）由 **Cursor 子 Agent** 完成，见同一 Skill；**不用** Python 脚本对逐字稿做语义级处理。

## 在项目中的位置

| 阶段 | 产出 |
|------|------|
| ① `bilibili_transcript` | `*_transcript.json` |
| ② `bilibili-transcript-finalize`（Cursor Skill） | `*_transcript_成稿.md` |
| **③ 本指引（默认随主流程，子 Agent）** | **`*_transcript_成稿.html`** |

## 何时需要本指引

- **默认**：`bilibili-transcript-finalize` 跑完 成稿 `.md` 后，主 Agent **应再开子 Agent**，按本目录与模板生成 HTML（见该 Skill 阶段③）。
- 用户说：**莫兰迪卡片**、**成稿转网页**、**生成 HTML**、**单页阅读版**、**转写稿网页**。
- 用户 `@` 某份 `*_transcript_成稿.md` 或粘贴其内容。
- 任意 Markdown 长文需要「好看单页」呈现（读书笔记、访谈整理等）。

## 执行步骤

1. **读模板**：打开本目录 **[`morandi-template.html`](morandi-template.html)**，复制为工作基础（保持 `<style>` 不动，除非修错别字）。
2. **定输出路径**：与源 Markdown 同目录、同主文件名，扩展名改为 `.html`：  
   `{sanitize_title}_{bvid}_transcript_成稿.html`（与成稿 `.md` 对齐）。
3. **从 Markdown 抽结构**（见下节「成稿映射」）。
4. **填模板**：替换 `{{占位符}}`；删除不需要的块（如无备注则去掉 `.note` 整块或清空）。
5. **章节**：每个逻辑章节对应一个 `.section`；**圆圈数字**与章节顺序一致（1, 2, 3…）。
6. **高亮**：关键句保持或改为 `<strong>`，样式已做渐变底纹。
7. **交付**：写入 **`*_transcript_成稿.html`** 后，**立刻在终端用系统默认浏览器打开**，无需用户手动找文件：
   - **macOS**：`open "/绝对路径/…_transcript_成稿.html"`
   - **Linux**：`xdg-open "/绝对路径/…"`
   - **Windows（cmd）**：`start "" "C:\绝对路径\…"`
   （路径含空格时务必加引号。）
8. **回复用户**：说明 `.html` 已生成并已自动打开；若删了「全文总结」卡片，须同步调整 CSS 中章节 `nth-child` 序号（见模板注释）。

## 成稿 Markdown → HTML 映射（本仓库版式）

典型结构见 `TRANSCRIPT_STRATEGY.md` / `bilibili-transcript-finalize`：

| Markdown | HTML |
|----------|------|
| `# 标题` | `<header><h1>`；`subtitle` 可写 `BVxxxx · B 站转写` 或英文来源说明 |
| `## 全文总结` 下正文 | `.summary-card` 内段落；`**词**` → `<strong>` |
| `## 全文总结` 后的斜体/说明段（如 `*说明：…*`） | `.summary-card .note` |
| `## 1. 完整逐字稿` | 一般不单独渲染为标题块，**小节用下面的 `###` 拆成多个 `.section`** |
| `### 1.1 短标题` | `.section-header h3`（可去掉前缀 `1.1`，或保留，二选一全篇统一） |
| 小节下引用块首行 `> （时间参考：MM:SS–MM:SS）` | `<span class="time-tag">⏱ MM:SS – MM:SS</span>`（去掉「时间参考」等套话，保留时间） |
| 引用块其余行 `> …` | 合并为 `.section-intro` 一段或多段 |
| 正文段落 | `.content-card` 内 `<p>`；保持分段 |
| `**主持人：**` / `**嘉宾：**` / `**巴菲特：**` 等 | 第一处用 `.speaker.a`，第二角色用 `.speaker.b`，第三人可再嵌 `<span class="speaker a">` 轮换或统一 `.speaker.a`（全篇一致即可） |
| 页脚说明 | `<footer><p>`，如「由 bilibili_transcript 成稿导出 · 仅供个人学习」 |

**发言人**：若无法区分身份，不要用假标签，仅用正文 `<p>` 即可。

**时间标签**：若某节无时间引用块，省略 `.time-tag` 即可。

## 设计规范（必须与模板一致）

- **配色、字号、圆角、阴影、间距**：以 `morandi-template.html` 内 `:root` 与现有规则为准，勿随意改色破坏统一。
- **字体**：正文 `-apple-system, …, "PingFang SC", sans-serif`；时间戳 `SF Mono`, `Fira Code`, monospace。
- **布局**：最大宽度 780px 居中；移动端已有 `@media`。
- **章节色**：模板用 `.container > .section:nth-child(3)` 起算；**必须**保持 DOM 顺序为：`header` → `.summary-card` → 若干 `.section` → `footer`。若去掉总结卡片，需把模板里相关 `nth-child` 全部减 1 或给 `.section` 加显式 `accent` 类并改 CSS（任选一种，避免圆圈颜色错）。

## 注意事项

- 单文件自包含；**不要**引入外部 CSS/JS/CDN（除非用户明确要求）。
- 长文注意实体转义：`&` → `&amp;`，`<` → `&lt;` 仅在正文需要时（一般中文稿很少）。
- 不编造音视频里不存在的事实；HTML 仅改变呈现，不改变成稿语义。

## 与仓库示例

- 根目录若存在 `视觉效果案例.html`，可作为已填内容的版式参考；**规范模板以本目录 [`morandi-template.html`](morandi-template.html) 为准**。
