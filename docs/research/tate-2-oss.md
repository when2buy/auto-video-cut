# Tate 万能君 提到的两个 OSS — 识别记录

> Douyin post ~2026-05-28. All repo facts verified via `gh api repos/<owner>/<name>` on 2026-05-29.

## 1. "AI 一键生成视频，长视频科普类" → **NarratoAI**

- **Repo**: https://github.com/linyqh/NarratoAI
- **Stars**: 9,567 (active — last commit 2026-05-29)
- **Tagline (作者原文)**: 「一站式 AI 影视解说+自动化剪辑工具」"利用 AI 大模型，一键解说并剪辑视频"
- **谱系**: 直接 fork 自 `MoneyPrinterTurbo` + `MoneyPrinter`，但**重写为"解说现有视频"而不是"无中生有 stock-footage 视频"**。这是 v0.2 没有覆盖、且 MoneyPrinterTurbo 也没有覆盖的赛道。

### 它做什么（pipeline 全貌）
1. 上传**已有长视频**（纪录片/电影/B 站长片）
2. **逐帧抽帧 → 多模态 LLM 理解**（Qwen2-VL / Gemini-Vision）— `app/services/documentary/frame_analysis_service.py`，0.7.8 还专门重构了"纪录片逐帧分析链路"
3. **LLM 生成解说文案**（按场景对齐时间戳）— `generate_narration_script.py`
4. **TTS 配音**（Azure / 腾讯 / IndexTTS2 语音克隆）+ **Fun-ASR 字幕回写**
5. **自动剪辑**：根据解说节奏切原视频 → 配音轨 + 字幕轨 → 渲染
6. **导出剪映草稿**（jianying_task.py）—— 这是中国创作者实际工作流的关键

### 跟我们 v0.2 (whisper → Gemini → ffmpeg → reframe → captions) 的核心差异

| 维度 | auto-video-cut v0.2 | NarratoAI |
|------|----|----|
| **目标产物** | 短片（cut + reframe） | 长片解说（add narration to existing video） |
| **LLM 输入** | 纯文字 transcript | **逐帧画面 + transcript**（Vision LLM） |
| **配音** | 无 | TTS 全程，支持声纹克隆 |
| **导出** | mp4 | mp4 + **剪映草稿**（人工 last-mile 调整） |
| **垂直场景模板** | 通用 | 影视解说 / 短剧解说 / 纪录片 三套独立 prompt |

### 我们应该偷的具体特性

1. **Vision LLM 逐帧理解**（最有杀伤力）— 我们目前是文本-only，丢掉了画面信息。可以最低成本接 Gemini-Vision，让 LLM 看到画面再决定 cut。`frame_analysis_service.py` 的抽帧 + 缓存 + 并发逻辑直接借鉴。
2. **剪映草稿导出** — 中国创作者根本不会接受"黑盒一键出片"，他们要在剪映里二次调整。这是**比 reframe + captions 更刚需的本地化能力**，工作量小（剪映草稿就是一个 JSON schema）。
3. **垂直 prompt 套件**（`prompts/documentary/`, `prompts/short_drama_narration/`）— 把"通用 cut prompt"拆成场景专用模板，质量提升肉眼可见。
4. **Fun-ASR 字幕模式** — 比 whisper 更擅长中文标点和断句，0.7.9 新增。
5. **IndexTTS2 声纹克隆** — 解说类视频"作者声音"是品牌资产，克隆比 TTS 默认音色刚需。

> v0.2 应该考虑加一条 `narrate-mode` 子命令，专门做"长视频 → 解说短片"，复用 NarratoAI 的 prompt 模板和剪映导出。

## 2. "本地部署 AI 客服" → **Dify**

- **Repo**: https://github.com/langgenius/dify
- **Stars**: 143,057 (last commit 2026-05-29)
- **Tagline**: "Production-ready platform for agentic workflow development"
- **为什么是它**: 中文 AI 圈 2025–2026 年"本地部署 + 落地客服"几乎等于 Dify 同义词。Docker compose 一键起，自带 RAG / workflow / API / chat UI，企业客服是它官方 use-case 头条。FastGPT (28k) 和 AnythingLLM (60k) 是它的同位竞品，但 Tate 这种"落地实用"创作者大概率讲的就是 Dify——星数、热度、中文文档完整度都是天花板。

---
*Generated 2026-05-29. Repos verified via GitHub REST API.*
