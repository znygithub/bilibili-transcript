# 视频理解（B 站转写）

- **脚本**：只生成文字稿 `transcript.json`（字幕/ASR）。  
- **Cursor**：按 Skill 用**子 Agent** 做翻译、总结与成稿 md；见 [`.cursor/skills/bilibili-transcript-finalize/SKILL.md`](.cursor/skills/bilibili-transcript-finalize/SKILL.md)。**主触发**：发 B 站视频 URL。

- **交接说明与代码结构**：见 [`交接文档.md`](交接文档.md)
- **字幕优先顺序与参数**：见 [`TRANSCRIPT_STRATEGY.md`](TRANSCRIPT_STRATEGY.md)

```bash
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx
```
