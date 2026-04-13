# 视频理解（B 站转写）

公开仓库：<https://github.com/znygithub/bilibili-transcript>（B 站转写流水线 + Cursor 成稿 Skill；无密钥，仅依赖本机环境与可选 Cookie。）

- **脚本**：只生成文字稿 `transcript.json`（字幕/ASR）。  
- **Cursor**：按 Skill 用**子 Agent** 做翻译、总结与成稿 md；见 [`.cursor/skills/bilibili-transcript-finalize/SKILL.md`](.cursor/skills/bilibili-transcript-finalize/SKILL.md)。**主触发**：发 B 站视频 URL。

- **交接说明与代码结构**：见 [`交接文档.md`](交接文档.md)
- **字幕优先顺序与参数**：见 [`TRANSCRIPT_STRATEGY.md`](TRANSCRIPT_STRATEGY.md)

```bash
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx
```

**Skill 全局使用**：将 `.cursor/skills/bilibili-transcript-finalize/` 复制到 `~/.cursor/skills/bilibili-transcript-finalize/` 后，任意项目均可加载（本机已可复制一份到用户目录）。
