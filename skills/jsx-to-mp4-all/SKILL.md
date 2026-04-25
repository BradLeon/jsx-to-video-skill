---
name: jsx-to-mp4-all
description: Convert JSX/React animation into ONE combined MP4 video containing all steps playing in sequence. Use when the user wants a single video with all animation steps. Trigger keywords: 'JSX转MP4', '完整视频', '合并MP4', 'combined MP4', 'one video', '整体视频', '全部步骤一个视频', '动画转视频'. Also trigger when user says 'make one video of everything' or '合成一个视频'.
---

# jsx-to-mp4-all

**Output: One single MP4 file** containing all steps playing in sequence with auto-advance.


## MANDATORY: Environment Setup (run FIRST)

```bash
playwright install chromium 2>&1 | tail -3
which ffmpeg xvfb-run && python3 -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

**CRITICAL:** ALWAYS use Playwright + Chromium. NEVER fall back to sharp, puppeteer-core, node-canvas, or SVG-only rendering. ALWAYS prefix scripts with `xvfb-run -a`.

---

## Pipeline

```
JSX → Analyze → Rewrite to vanilla HTML/JS (zero CDN) → Test screenshot → Capture frames → Encode
```

---

## Step 1: Analyze JSX

Identify:
- Number of steps/pages
- Dependencies to replace (see table below)
- Animation type (JS frame loop vs CSS one-shot vs CSS infinite)
- Timing per step

### Dependency Replacement Table

| Dependency | Detection | Replacement |
|-----------|-----------|-------------|
| React/JSX | `import React`, JSX syntax | Vanilla JS + `innerHTML` |
| Tailwind CSS | `className="flex items-center..."` | Inline `style=""` |
| lucide-react | `import { Zap } from 'lucide-react'` | Emoji (⚡💿📦◎▽🌧🔌📌) or inline SVG |
| Google Fonts | `@import url(fonts.googleapis.com)` | System fonts: `-apple-system, 'Segoe UI', sans-serif` |
| recharts/d3 | `import { LineChart }` | Inline SVG or canvas |

### Animation Type → Capture Strategy

| Type | Detection | Strategy |
|------|----------|---------|
| JS frame loop | `setInterval(() => { frame++; render() }, 80)` | Continuous capture |
| CSS one-shot | `@keyframes` + `forwards` | Reset innerHTML on step switch to restart |
| CSS infinite | `@keyframes` + `infinite` | Continuous capture |

---

## Step 2: Rewrite to Vanilla HTML/JS

### Template

```html
<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>/* ALL CSS inline, @keyframes if needed */</style>
</head><body>
<div id="app"><!-- skeleton --></div>
<script>
var STEPS = [ /* step data */ ];
var currentStep = 0, frame = 0;

function render() {
  var step = STEPS[currentStep];
  // Update DOM; for CSS one-shot: replace innerHTML to restart animations
}

setInterval(function(){ frame++; render(); }, 80);

window.autoAdvance = false;
setInterval(function(){
  if (window.autoAdvance && currentStep < STEPS.length - 1) { currentStep++; render(); }
}, 5000);

render();
</script></body></html>
```

**Rules:** `currentStep`, `render()`, `window.autoAdvance` MUST be global. `autoAdvance` defaults to `false`.

### Tailwind Quick Reference

```
flex→display:flex  items-center→align-items:center  gap-3→gap:12px
w-full→width:100%  h-8→height:32px  p-4→padding:16px
text-xl→font-size:20px  font-bold→font-weight:700
rounded-xl→border-radius:12px  bg-slate-900→background:#0f172a
text-blue-400→color:#60a5fa  border-slate-800→border-color:#1e293b
```

Slate: `400:#94a3b8 500:#64748b 700:#334155 800:#1e293b 900:#0f172a 950:#020617`

### Layout: Convert desktop sidebar layouts to single-column portrait (540×960 logical).

---

## Step 3: Test Screenshot

```python
# Run with: xvfb-run -a python test.py
import asyncio
from playwright.async_api import async_playwright
async def test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width":540,"height":960}, device_scale_factor=2)
        await page.goto("file:///home/claude/animation.html")
        await page.wait_for_timeout(3000)
        await page.screenshot(path="/home/claude/test.png", clip={"x":0,"y":0,"width":540,"height":960})
        await browser.close()
asyncio.run(test())
```

**Check:** PNG > 50KB = OK. If ~2-3KB = blank page = JS error.


---

## Step 4: Capture Frames

**Output: One single MP4 file** containing all steps playing in sequence with auto-advance.

Enable auto-advance and capture all steps in one continuous recording:

```python
# Run with: xvfb-run -a python capture.py
# Enable auto-advance for combined mode
await page.evaluate("window.autoAdvance = true; currentStep = 0; render();")

total_frames = FPS * DURATION_PER_STEP * num_steps
for i in range(total_frames):
    await page.screenshot(path=f"/home/claude/frames/frame_{i:05d}.png",
        type="png", clip={"x":0,"y":0,"width":540,"height":960})
    await page.wait_for_timeout(1000 // FPS)

# Encode ONE MP4 from all frames
# ... (see encoding command below)
```

### Using bundled capture.py

```bash
xvfb-run -a python ${CLAUDE_PLUGIN_ROOT}/scripts/capture.py --html animation.html --output ./output --combined --mp4-only
```

### Parameters

| Parameter | Value |
|-----------|-------|
| Logical size | 540×960 (1080×1920 at 2x) |
| device_scale_factor | 2 |
| FPS | 12 (JS anim) / 15 (CSS anim) |
| Duration per step | Match original auto-advance |

---

## Step 5: Encode MP4

```bash
ffmpeg -y -framerate {FPS} -i frame_%05d.png \
  -c:v libx264 -pix_fmt yuv420p -preset medium -crf 20 \
  -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" output.mp4
```

---

## Platform Guide

| Platform | Notes |
|----------|-------|
| 微信公众号 | 编辑器'插入视频' |
| 小红书 | 视频笔记直接上传 |
| X/Twitter | MP4画质更好，推荐 |

---

## DO NOT

- ❌ NEVER use sharp, puppeteer-core, node-canvas, or SVG-only rendering
- ❌ NEVER run Playwright without `xvfb-run -a`
- ❌ NEVER forget `playwright install chromium` at start
- ❌ NEVER rely on CDN (React, Tailwind, Babel, fonts)
- ❌ NEVER skip the test screenshot step
- ❌ NEVER output separate files — this skill produces ONE combined file
