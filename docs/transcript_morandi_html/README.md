# 成稿 → 莫兰迪卡片 HTML

将 `*_transcript_成稿.md` 转为**单文件 HTML**：暖灰米底、白卡片、章节编号圆圈、可选时间胶囊。无外链、无 JavaScript，本地双击即可阅读。

| 文件 | 作用 |
|------|------|
| 本 README | 映射规则与注意事项 |
| [`morandi-template.html`](morandi-template.html) | 单页模板（内联 CSS、占位符） |

## 使用方式

### 方式一：CLI 子命令（推荐）

```bash
python -m bilibili_transcript export-html path/to/*_transcript_成稿.md
```

自动生成同名 `.html` 并在浏览器中打开。

### 方式二：AI 助手手写

读取本 README + `morandi-template.html`，手动填入内容。适合需要微调版式的个案。

## Markdown → HTML 映射

| Markdown | HTML |
|----------|------|
| `# 标题` | `<header><h1>` + `<div class="subtitle">` 写视频 ID 与来源 |
| `## 全文总结` 下正文 | `.summary-card` 内段落；`**词**` → `<strong>` |
| 斜体说明段 `*说明：…*` | `.summary-card .note` |
| `### 1.1 短标题` | `.section-header h3` |
| `> （时间参考：MM:SS–MM:SS）` | `<span class="time-tag">⏱ MM:SS – MM:SS</span>` |
| 引用块其余行 | `.section-intro` |
| 正文段落 | `.content-card` 内 `<p>` |
| `**主持人：**` / `**嘉宾：**` | `.speaker.a` / `.speaker.b` |
| 页脚 | `<footer>` |

## 设计规范

- 配色、字号、圆角、阴影：以 `morandi-template.html` 的 `:root` 为准
- 最大宽度 780px 居中；已有移动端 `@media`
- DOM 顺序：`header` → `.summary-card` → `.section` × N → `footer`
- 章节色由 `nth-child` 控制；若去掉总结卡片需调整序号

## 注意事项

- 单文件自包含，不引入外部 CSS/JS
- HTML 实体转义：`&` → `&amp;`，`<` → `&lt;`
- 不编造原视频中不存在的内容
