# bilibili-transcript

本机把 B 站视频转成可核对的 **`transcript.json`**，成稿（总结、翻译、排版）由 **Cursor** 按项目 [Skill](.cursor/skills/bilibili-transcript-finalize/SKILL.md) 完成。

**仓库**：<https://github.com/znygithub/bilibili-transcript>（公开，无密钥）

```bash
pip install -r requirements.txt   # 建议使用 venv
python -m bilibili_transcript "BV1xxxxxxxxx" -o case_outputs/BV1xxxxxxxxx
```

**进一步阅读**（避免与下述文档重复，此处不展开）：

| 文档 | 内容 |
|------|------|
| [**交接文档.md**](交接文档.md) | 目标与分工、**代码结构表**、输出物、环境、Skill、案例、接手清单 |
| [**TRANSCRIPT_STRATEGY.md**](TRANSCRIPT_STRATEGY.md) | 字幕优先于 ASR 的决策顺序、常用 CLI 参数 |
