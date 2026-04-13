# 视频理解（B 站转写）

私有仓库：<https://github.com/znygithub/video-understanding>（GitHub 仓库名仅支持 ASCII，故为 `video-understanding`；中文名「视频理解」见仓库描述。）

- **脚本**：只生成文字稿 `transcript.json`（字幕/ASR）。  
- **Cursor**：按 Skill 用**子 Agent** 做翻译、总结与成稿 md；见 [`.cursor/skills/bilibili-transcript-finalize/SKILL.md`](.cursor/skills/bilibili-transcript-finalize/SKILL.md)。**主触发**：发 B 站视频 URL。

- **交接说明与代码结构**：见 [`交接文档.md`](交接文档.md)
- **字幕优先顺序与参数**：见 [`TRANSCRIPT_STRATEGY.md`](TRANSCRIPT_STRATEGY.md)

```bash
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx
```

**Skill 全局使用**：将 `.cursor/skills/bilibili-transcript-finalize/` 复制到 `~/.cursor/skills/bilibili-transcript-finalize/` 后，任意项目均可加载（本机已可复制一份到用户目录）。
