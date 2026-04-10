# jsx-to-video

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Claude Code Plugin](https://img.shields.io/badge/Claude_Code-Plugin-blueviolet)](https://claude.ai)

Convert JSX/React animations into GIF and MP4 videos — ready for social media.

将 Claude 生成的 JSX/React 动画转换为 GIF 和 MP4 视频，可直接用于社交媒体发布。

---

## Why / 为什么需要

Claude can generate beautiful animated JSX components, but social media platforms only accept standard image/video formats. This plugin converts JSX animations to GIF/MP4 directly within Claude Code — no manual workflow needed.

Claude 能生成精美的 JSX 动画组件，但社交媒体平台只接受标准图片/视频格式。本插件在 Claude Code 中直接完成 JSX 到 GIF/MP4 的转换，无需手动操作。

## How it works / 工作原理

```
JSX → Analyze → Rewrite to vanilla HTML/JS (zero CDN) → Test screenshot → Capture frames → Encode GIF/MP4
```

The plugin rewrites React/JSX code into self-contained vanilla HTML (replacing Tailwind, lucide-react, Google Fonts, etc.), renders it with Playwright + Chromium, captures frames, and encodes with ffmpeg.

---

## Skills / 包含的技能

| Skill | Output | Use Case / 使用场景 |
|-------|--------|---------------------|
| `jsx-to-gif-separate` | One GIF per step | Each animation step as individual GIF / 每个步骤单独导出 GIF |
| `jsx-to-gif-all` | One combined GIF | All steps in one looping GIF / 全部步骤合并为一个 GIF |
| `jsx-to-mp4-separate` | One MP4 per step | Each step as individual video clip / 每个步骤单独导出视频 |
| `jsx-to-mp4-all` | One combined MP4 | All steps in one video / 全部步骤合并为一个视频 |

---

## Installation / 安装

```bash
claude plugin add github:BradLeon/jsx-to-video-skill
```

### Prerequisites / 前置要求

These are pre-installed in Claude's sandbox environment. For local use:

- Python 3.8+
- [Playwright](https://playwright.dev/python/) — `pip install playwright && playwright install chromium`
- [ffmpeg](https://ffmpeg.org/) — `brew install ffmpeg` (macOS) / `apt install ffmpeg` (Linux)
- xvfb (Linux only) — `apt install xvfb`

---

## Usage / 使用方法

After installing the plugin, the skills are triggered automatically when you describe what you want. You can also invoke them directly:

安装插件后，技能会根据描述自动触发。也可以直接调用：

### Trigger phrases / 触发短语

**English:**
- "Convert this JSX to GIF"
- "Export each step as a separate MP4"
- "Make one video of the whole animation"
- "Save this animation as GIF for Twitter"

**中文：**
- "把这个 JSX 转成 GIF"
- "每一页导出一个 MP4"
- "合成一个完整视频"
- "动画转 GIF 发小红书"

### Direct invocation / 直接调用

```
/jsx-to-video:jsx-to-gif-all
/jsx-to-video:jsx-to-mp4-separate
```

### Example workflow / 示例流程

1. Ask Claude to create an animated JSX component (e.g., a step-by-step tutorial animation)
2. Say "convert this to MP4" or "把这个转成 GIF"
3. The skill will:
   - Analyze the JSX and identify steps/dependencies
   - Rewrite to self-contained vanilla HTML/JS
   - Render with Playwright and capture frames
   - Encode to GIF or MP4 with ffmpeg
4. Download the output files

---

## Project Structure / 项目结构

```
jsx-to-video-skill/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── scripts/
│   └── capture.py           # Shared Playwright + ffmpeg capture script
├── skills/
│   ├── jsx-to-gif-separate/
│   │   └── SKILL.md
│   ├── jsx-to-gif-all/
│   │   └── SKILL.md
│   ├── jsx-to-mp4-separate/
│   │   └── SKILL.md
│   └── jsx-to-mp4-all/
│       └── SKILL.md
├── .gitignore
├── LICENSE
└── README.md
```

---

## Contributing / 贡献

Contributions are welcome! Please open an issue or submit a PR.

欢迎贡献！请提交 Issue 或 Pull Request。

## License / 许可

[MIT](LICENSE)
